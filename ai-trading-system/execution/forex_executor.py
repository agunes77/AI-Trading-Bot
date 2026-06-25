import time
import numpy as np
from data.forex_data import ForexDataFetcher
from features.technical_indicators import FeatureEngineer
from agent.rl_agent import RLAgent
from execution.risk_manager import RiskManager
from utils.logger import logger
from config.settings import MT5_CONFIG

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None


class ForexExecutor:
    def __init__(self, agent: RLAgent, risk_manager: RiskManager):
        self.agent = agent
        self.risk = risk_manager
        self.fetcher = ForexDataFetcher()
        self.fe = FeatureEngineer()
        self.feature_cols = self.fe.get_feature_columns()
        self.position = None
        self.entry_price = 0.0
        self.ticket = None

    def connect(self) -> bool:
        return self.fetcher.connect()

    def disconnect(self):
        self.fetcher.disconnect()

    def run_cycle(self, symbol: str):
        if mt5 is None:
            logger.error("MT5 kutuphanesi yok")
            return
        try:
            df = self.fetcher.fetch_ohlcv(symbol, count=300)
            if df.empty or len(df) < 200:
                logger.warning(f"Yetersiz veri: {symbol}")
                return

            df_features = self.fe.add_all_indicators(df)
            available = [c for c in self.feature_cols if c in df_features.columns]
            latest = df_features.iloc[-1]
            obs = self._build_observation(latest, available)

            action = self.agent.predict(obs)
            current_price = latest["close"]

            if action == 1 and self.position is None:
                self._execute_buy(symbol, current_price)
            elif action == 2 and self.position == "long":
                self._execute_sell(symbol, current_price)

            self._check_exits(symbol, current_price)

        except Exception as e:
            logger.error(f"Forex trade dongusu hatasi {symbol}: {e}")

    def _build_observation(self, row, available_cols):
        features = np.array([row.get(c, 0) for c in available_cols], dtype=np.float64)
        position_val = 1.0 if self.position == "long" else 0.0
        extra = np.array([position_val, 1.0, 1.0, 0.0], dtype=np.float64)
        return np.concatenate([features, extra])

    def _execute_buy(self, symbol: str, price: float):
        account = self.fetcher.get_account_info()
        balance = account.get("balance", 0)
        if balance <= 0:
            return
        if not self.risk.can_open_trade(balance):
            return

        lot_size = self._calculate_lot_size(balance, price)
        sl = self.risk.get_stop_loss(price)
        tp = self.risk.get_take_profit(price)

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return
        point = symbol_info.point
        digits = symbol_info.digits

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": mt5.ORDER_TYPE_BUY,
            "price": mt5.symbol_info_tick(symbol).ask,
            "sl": round(sl, digits),
            "tp": round(tp, digits),
            "deviation": 20,
            "magic": 234000,
            "comment": "AI_Trader",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"MT5 alis hatasi: {result.comment}")
            return
        self.ticket = result.order
        self.position = "long"
        self.entry_price = price
        self.risk.record_trade_open()
        logger.info(f"FOREX ALIS | {symbol} @ {price:.5f} | Lot: {lot_size} | Ticket: {self.ticket}")

    def _execute_sell(self, symbol: str, price: float):
        if self.ticket is None:
            return
        pnl_pct = (price - self.entry_price) / self.entry_price if self.entry_price > 0 else 0
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": self._calculate_lot_size(self.fetcher.get_account_info().get("balance", 0), price),
            "type": mt5.ORDER_TYPE_SELL,
            "position": self.ticket,
            "price": mt5.symbol_info_tick(symbol).bid,
            "deviation": 20,
            "magic": 234000,
            "comment": "AI_Trader_Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"MT5 satis hatasi: {result.comment}")
            return
        self.position = None
        self.entry_price = 0.0
        self.ticket = None
        self.risk.record_trade_close(pnl_pct)
        logger.info(f"FOREX SATIS | {symbol} @ {price:.5f} | PnL: {pnl_pct:.2%}")

    def _check_exits(self, symbol: str, price: float):
        if self.position != "long":
            return
        stop_loss = self.risk.get_stop_loss(self.entry_price)
        take_profit = self.risk.get_take_profit(self.entry_price)
        if price <= stop_loss:
            logger.warning(f"FOREX STOP LOSS | {symbol} @ {price:.5f}")
            self._execute_sell(symbol, price)
        elif price >= take_profit:
            logger.info(f"FOREX TAKE PROFIT | {symbol} @ {price:.5f}")
            self._execute_sell(symbol, price)

    def _calculate_lot_size(self, balance: float, price: float) -> float:
        risk_amount = balance * self.risk.config["max_position_pct"]
        lot = risk_amount / (price * 100000)
        return round(max(0.01, min(lot, 1.0)), 2)
