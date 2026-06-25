import pandas as pd
import numpy as np
from strategies.base_strategy import BaseStrategy, Signal
from strategies.classic_strategies import ALL_STRATEGIES
from features.technical_indicators import FeatureEngineer
from utils.logger import logger
from config.settings import BACKTEST_CONFIG


class StrategyEngine:
    def __init__(self, feature_engineer: FeatureEngineer = None):
        self.fe = feature_engineer or FeatureEngineer()

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = self.fe.add_all_indicators(df)
        return df

    def run_strategy(self, df: pd.DataFrame, strategy: BaseStrategy) -> pd.DataFrame:
        df = self.prepare_data(df)
        df["signal"] = strategy.generate_signals(df)
        return df

    def run_all_strategies(self, df: pd.DataFrame) -> dict:
        df = self.prepare_data(df)
        results = {}
        for name, strategy_cls in ALL_STRATEGIES.items():
            strategy = strategy_cls()
            signals = strategy.generate_signals(df)
            results[name] = {
                "strategy": strategy,
                "signals": signals,
                "buy_count": int((signals == Signal.BUY).sum()),
                "sell_count": int((signals == Signal.SELL).sum()),
            }
        return results

    def backtest_strategy(
        self,
        df: pd.DataFrame,
        strategy: BaseStrategy,
        initial_balance: float = None,
        commission: float = None,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.04,
    ) -> dict:
        initial_balance = initial_balance or BACKTEST_CONFIG["initial_balance"]
        commission = commission or BACKTEST_CONFIG["commission_pct"]

        df = self.prepare_data(df)
        signals = strategy.generate_signals(df)

        balance = initial_balance
        position = 0
        entry_price = 0.0
        shares = 0.0
        equity_curve = [initial_balance]
        trades = []
        max_equity = initial_balance

        for i in range(len(df)):
            price = df.iloc[i]["close"]
            signal = signals.iloc[i] if i < len(signals) else Signal.HOLD

            if position == 1:
                pnl_pct = (price - entry_price) / entry_price
                if pnl_pct <= -stop_loss_pct:
                    revenue = shares * price * (1 - commission)
                    balance += revenue
                    trades.append({"step": i, "action": "sell_sl", "price": price, "pnl_pct": pnl_pct})
                    position = 0
                    shares = 0.0
                    entry_price = 0.0
                elif pnl_pct >= take_profit_pct:
                    revenue = shares * price * (1 - commission)
                    balance += revenue
                    trades.append({"step": i, "action": "sell_tp", "price": price, "pnl_pct": pnl_pct})
                    position = 0
                    shares = 0.0
                    entry_price = 0.0

            if signal == Signal.BUY and position == 0:
                invest = balance * 0.95
                exec_price = price * 1.0005
                shares = invest / exec_price
                balance -= invest
                entry_price = exec_price
                position = 1
                trades.append({"step": i, "action": "buy", "price": exec_price, "pnl_pct": 0})

            elif signal == Signal.SELL and position == 1:
                revenue = shares * price * (1 - commission)
                balance += revenue
                pnl_pct = (price - entry_price) / entry_price
                trades.append({"step": i, "action": "sell", "price": price, "pnl_pct": pnl_pct})
                position = 0
                shares = 0.0
                entry_price = 0.0

            total = balance + shares * price
            equity_curve.append(total)
            if total > max_equity:
                max_equity = total

        if position == 1:
            final_price = df.iloc[-1]["close"]
            balance += shares * final_price * (1 - commission)
            shares = 0.0
            position = 0

        final_balance = balance
        equity = np.array(equity_curve)
        returns = np.diff(equity) / (equity[:-1] + 1e-10)

        sell_trades = [t for t in trades if t["action"] in ("sell", "sell_sl", "sell_tp")]
        winning = [t for t in sell_trades if t["pnl_pct"] > 0]
        losing = [t for t in sell_trades if t["pnl_pct"] <= 0]

        total_return = (final_balance - initial_balance) / initial_balance * 100
        max_dd = (1 - equity / np.maximum.accumulate(equity)).max() * 100
        sharpe = np.sqrt(252) * returns.mean() / (returns.std() + 1e-10) if len(returns) > 0 else 0
        total_trades = len(sell_trades)
        win_rate = (len(winning) / total_trades * 100) if total_trades > 0 else 0
        avg_win = np.mean([t["pnl_pct"] for t in winning]) * 100 if winning else 0
        avg_loss = np.mean([t["pnl_pct"] for t in losing]) * 100 if losing else 0
        profit_factor = abs(sum(t["pnl_pct"] for t in winning) / sum(t["pnl_pct"] for t in losing)) if losing and sum(t["pnl_pct"] for t in losing) != 0 else float("inf")

        return {
            "strategy_name": strategy.describe(),
            "initial_balance": initial_balance,
            "final_balance": final_balance,
            "total_return_pct": total_return,
            "max_drawdown_pct": max_dd,
            "sharpe_ratio": sharpe,
            "total_trades": total_trades,
            "win_rate_pct": win_rate,
            "avg_win_pct": avg_win,
            "avg_loss_pct": avg_loss,
            "profit_factor": profit_factor,
            "buy_signals": int((signals == Signal.BUY).sum()),
            "sell_signals": int((signals == Signal.SELL).sum()),
            "equity_curve": equity_curve,
            "trades": trades,
        }

    def compare_all_strategies(
        self,
        df: pd.DataFrame,
        initial_balance: float = None,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.04,
    ) -> pd.DataFrame:
        df = self.prepare_data(df)
        comparison = []
        for name, strategy_cls in ALL_STRATEGIES.items():
            strategy = strategy_cls()
            result = self.backtest_strategy(df, strategy, initial_balance=initial_balance,
                                            stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct)
            comparison.append({
                "Strateji": strategy.describe(),
                "Getiri %": f"{result['total_return_pct']:.2f}",
                "Max DD %": f"{result['max_drawdown_pct']:.2f}",
                "Sharpe": f"{result['sharpe_ratio']:.3f}",
                "Islem": result["total_trades"],
                "Kazanma %": f"{result['win_rate_pct']:.1f}",
                "Ort Kazanc %": f"{result['avg_win_pct']:.2f}",
                "Ort Kayip %": f"{result['avg_loss_pct']:.2f}",
                "Profit Factor": f"{result['profit_factor']:.2f}" if result['profit_factor'] != float('inf') else "inf",
                "Son Bakiye": f"${result['final_balance']:,.2f}",
            })
        return pd.DataFrame(comparison)

    def get_best_strategies(self, df: pd.DataFrame, top_n: int = 5, sort_by: str = "sharpe_ratio") -> list:
        df = self.prepare_data(df)
        results = []
        for name, strategy_cls in ALL_STRATEGIES.items():
            strategy = strategy_cls()
            result = self.backtest_strategy(df, strategy)
            result["key"] = name
            results.append(result)

        reverse = sort_by != "max_drawdown_pct"
        results.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        return results[:top_n]

    def ensemble_signal(self, df: pd.DataFrame, strategy_weights: dict = None) -> Signal:
        df = self.prepare_data(df)
        total_weight = 0
        weighted_signal = 0

        for name, strategy_cls in ALL_STRATEGIES.items():
            strategy = strategy_cls()
            signals = strategy.generate_signals(df)
            latest_signal = signals.iloc[-1] if len(signals) > 0 else Signal.HOLD

            weight = 1.0
            if strategy_weights and name in strategy_weights:
                weight = strategy_weights[name]

            weighted_signal += latest_signal * weight
            total_weight += weight

        if total_weight == 0:
            return Signal.HOLD

        avg = weighted_signal / total_weight
        if avg > 0.3:
            return Signal.BUY
        elif avg < -0.3:
            return Signal.SELL
        return Signal.HOLD
