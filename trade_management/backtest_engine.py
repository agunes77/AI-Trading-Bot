"""
Backtesting altyapısı: OCO Engine ve Sinyal Motorunu birlikte çalıştırır.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from trade_management.oco_engine import (
    TradeManagementEngine, TradeState, OCOOrderSet,
    OrderSide, OrderSetStatus, TrailingMode
)
from strategy_builder.executor import StrategyExecutor
from utils.logger import logger


class BacktestEngine:
    """Strateji + OCO Motorunu birleştiren tam backtest sistemi"""
    
    def __init__(self, initial_balance: float = 10000.0, commission: float = 0.001):
        self.initial_balance = initial_balance
        self.commission = commission

    def run(
        self, 
        strategy: Dict, 
        data: pd.DataFrame,
        risk_pct: float = 0.02,
        sl_atr_mult: float = 1.5,
        tp_atr_mult: float = 3.0,
        trailing_mode: str = "atr",
        trailing_atr_mult: float = 2.0,
    ) -> Dict:
        """Tam backtest çalıştır"""
        # 1. Sinyalleri üret
        executor = StrategyExecutor()
        result = executor.execute(strategy, data)
        
        if "error" in result:
            return result
            
        buy_signals = result.get("signals", {}).get("buy", pd.Series(False, index=data.index))
        sell_signals = result.get("signals", {}).get("sell", pd.Series(False, index=data.index))
        
        # 2. ATR hesapla (OCO için)
        atr_period = 14
        tr = pd.concat([
            data["high"] - data["low"],
            abs(data["high"] - data["close"].shift()),
            abs(data["low"] - data["close"].shift())
        ], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_period).mean()
        
        # 3. Backtest event loop
        balance = self.initial_balance
        position = 0.0
        entry_price = 0.0
        entry_time = None
        active_trade: Optional[TradeState] = None
        equity_curve = [balance]
        trades = []
        
        for i in range(len(data)):
            price = data.iloc[i]["close"]
            current_atr = atr.iloc[i] if not np.isnan(atr.iloc[i]) else 0.01
            
            # Aktif trade varsa trailing stop güncelle
            if active_trade:
                oco_engine = TradeManagementEngine()
                oco_engine.update_trailing_stops(price, current_atr, active_trade)
                
                # Exit kontrolü
                triggered = oco_engine.check_exits(price, active_trade)
                if triggered:
                    for t in triggered:
                        if "SL" in t:
                            pnl_pct = (price - entry_price) / entry_price if active_trade.side == OrderSide.LONG else (entry_price - price) / entry_price
                            equity = balance + (position * price * pnl_pct)
                            balance += (position * price * pnl_pct) * (1 - self.commission)
                            trades.append({"type": "exit_sl", "price": price, "pnl_pct": pnl_pct * 100, "reason": t})
                        elif "TP" in t:
                            pnl_pct = (price - entry_price) / entry_price if active_trade.side == OrderSide.LONG else (entry_price - price) / entry_price
                            balance += (position * price * pnl_pct) * (1 - self.commission)
                            trades.append({"type": "exit_tp", "price": price, "pnl_pct": pnl_pct * 100, "reason": t})
                        
                        position = 0.0
                        entry_price = 0.0
                        active_trade = None
            
            # Yeni ALIŞ sinyali
            if buy_signals.iloc[i] and position == 0:
                entry_price = price
                entry_time = data.index[i]
                risk_amount = balance * risk_pct
                position = risk_amount / (current_atr * sl_atr_mult) # Dinamik pozisyon büyüklüğü
                
                sl = price - (sl_atr_mult * current_atr)
                tp = price + (tp_atr_mult * current_atr)
                
                sl_dist = abs(price - sl)
                position = risk_amount / sl_dist if sl_dist > 0 else 0
                
                oco = OCOOrderSet(
                    name="Main", side=OrderSide.LONG, entry_price=price, stop_loss=sl, take_profit=tp,
                    position_pct=1.0, status=OrderSetStatus.ACTIVE,
                    trailing_mode=TrailingMode(trailing_mode), trailing_atr_mult=trailing_atr_mult
                )
                active_trade = TradeState(
                    entry_price=price, side=OrderSide.LONG, size=position, entry_time=entry_time,
                    stop_loss=sl, take_profit=tp, max_favorable_price=price, max_adverse_price=price,
                    order_sets=[oco]
                )
                balance -= position * price * self.commission
                trades.append({"type": "entry_long", "price": price, "size": position})
            
            # Yeni SATIŞ sinyali
            elif sell_signals.iloc[i] and position == 0:
                entry_price = price
                entry_time = data.index[i]
                risk_amount = balance * risk_pct
                sl = price + (sl_atr_mult * current_atr)
                tp = price - (tp_atr_mult * current_atr)
                sl_dist = abs(price - sl)
                position = risk_amount / sl_dist if sl_dist > 0 else 0
                
                oco = OCOOrderSet(
                    name="Main", side=OrderSide.SHORT, entry_price=price, stop_loss=sl, take_profit=tp,
                    position_pct=1.0, status=OrderSetStatus.ACTIVE,
                    trailing_mode=TrailingMode(trailing_mode), trailing_atr_mult=trailing_atr_mult
                )
                active_trade = TradeState(
                    entry_price=price, side=OrderSide.SHORT, size=position, entry_time=entry_time,
                    stop_loss=sl, take_profit=tp, max_favorable_price=price, max_adverse_price=price,
                    order_sets=[oco]
                )
                balance -= position * price * self.commission
                trades.append({"type": "entry_short", "price": price, "size": position})
            
            equity_curve.append(balance + (position * price if position > 0 else 0))
        
        # Açık pozisyonu kapat
        if position > 0 and active_trade:
            price = data.iloc[-1]["close"]
            if active_trade.side == OrderSide.LONG:
                pnl_pct = (price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - price) / entry_price
            balance += position * price * pnl_pct * (1 - self.commission)
            trades.append({"type": "close_end", "price": price, "pnl_pct": pnl_pct * 100})
        
        # Performans hesapla
        equity_arr = np.array(equity_curve)
        total_return = (balance - self.initial_balance) / self.initial_balance * 100
        max_dd = (1 - equity_arr / np.maximum.accumulate(equity_arr)).max() * 100
        exit_trades = [t for t in trades if "exit" in t["type"] or t["type"] == "close_end"]
        winning = [t for t in exit_trades if t.get("pnl_pct", 0) > 0]
        
        return {
            "total_return_pct": total_return,
            "max_drawdown_pct": max_dd,
            "total_trades": len(exit_trades),
            "winning_trades": len(winning),
            "losing_trades": len(exit_trades) - len(winning),
            "win_rate": len(winning) / len(exit_trades) * 100 if exit_trades else 0,
            "final_balance": balance,
            "trades": trades,
            "equity_curve": equity_curve,
            "chart_data": result.get("chart_data"),
        }