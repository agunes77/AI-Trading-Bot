import time
import numpy as np
from data.crypto_data import CryptoDataFetcher
from features.technical_indicators import FeatureEngineer
from agent.rl_agent import RLAgent
from execution.risk_manager import RiskManager
from utils.logger import logger
from config.settings import BINANCE_CONFIG


class CryptoExecutor:
    def __init__(self, agent: RLAgent, risk_manager: RiskManager):
        self.agent = agent
        self.risk = risk_manager
        self.fetcher = CryptoDataFetcher()
        self.fe = FeatureEngineer()
        self.feature_cols = self.fe.get_feature_columns()
        self.position = None
        self.entry_price = 0.0

    def run_cycle(self, symbol: str):
        try:
            df = self.fetcher.fetch_ohlcv(symbol, limit=300)
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
            logger.error(f"Trade dongusu hatasi {symbol}: {e}")

    def _build_observation(self, row, available_cols):
        features = np.array([row.get(c, 0) for c in available_cols], dtype=np.float64)
        position_val = 1.0 if self.position == "long" else 0.0
        extra = np.array([position_val, 1.0, 1.0, 0.0], dtype=np.float64)
        return np.concatenate([features, extra])

    def _execute_buy(self, symbol: str, price: float):
        balance_info = self.fetcher.get_balance()
        usdt_balance = balance_info.get("USDT", 0)
        if usdt_balance <= 0:
            logger.warning("USDT bakiye yok")
            return
        if not self.risk.can_open_trade(usdt_balance):
            return
        logger.info(f"ALIS | {symbol} @ ${price:,.2f}")
        self.position = "long"
        self.entry_price = price
        self.risk.record_trade_open()

    def _execute_sell(self, symbol: str, price: float):
        pnl_pct = (price - self.entry_price) / self.entry_price if self.entry_price > 0 else 0
        logger.info(f"SATIS | {symbol} @ ${price:,.2f} | PnL: {pnl_pct:.2%}")
        self.position = None
        self.entry_price = 0.0
        self.risk.record_trade_close(pnl_pct)

    def _check_exits(self, symbol: str, price: float):
        if self.position != "long":
            return
        stop_loss = self.risk.get_stop_loss(self.entry_price)
        take_profit = self.risk.get_take_profit(self.entry_price)
        if price <= stop_loss:
            logger.warning(f"STOP LOSS | {symbol} @ ${price:,.2f}")
            self._execute_sell(symbol, price)
        elif price >= take_profit:
            logger.info(f"TAKE PROFIT | {symbol} @ ${price:,.2f}")
            self._execute_sell(symbol, price)
