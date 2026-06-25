import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.logger import logger
from config.settings import BINANCE_CONFIG, DATA_DIR


class CryptoDataFetcher:
    def __init__(self, config=None):
        self.config = config or BINANCE_CONFIG
        self.exchange = self._init_exchange()

    def _init_exchange(self):
        exchange = ccxt.binance({
            "apiKey": self.config["api_key"],
            "secret": self.config["api_secret"],
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })
        if self.config["sandbox"]:
            exchange.set_sandbox_mode(True)
            logger.info("Binance sandbox (testnet) modu aktif")
        return exchange

    def fetch_ohlcv(self, symbol: str, timeframe: str = None, limit: int = 1000, since=None) -> pd.DataFrame:
        timeframe = timeframe or self.config["default_timeframe"]
        try:
            raw = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            df = df.astype(np.float64)
            logger.debug(f"{symbol} | {timeframe} | {len(df)} mum verisi yuklendi")
            return df
        except Exception as e:
            logger.error(f"OHLCV cekilemedi {symbol}: {e}")
            return pd.DataFrame()

    def fetch_historical(self, symbol: str, timeframe: str = "1h", days: int = 365) -> pd.DataFrame:
        since = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
        all_data = []
        while since < int(datetime.utcnow().timestamp() * 1000):
            batch = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            if not batch:
                break
            all_data.extend(batch)
            since = batch[-1][0] + 1
        df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df = df[~df.index.duplicated(keep="first")]
        df = df.astype(np.float64)
        logger.info(f"{symbol} | {timeframe} | {len(df)} mum ({days} gun)")
        return df

    def fetch_orderbook(self, symbol: str, limit: int = 20) -> dict:
        try:
            ob = self.exchange.fetch_order_book(symbol, limit=limit)
            return {
                "bids": ob["bids"],
                "asks": ob["asks"],
                "spread": ob["asks"][0][0] - ob["bids"][0][0] if ob["asks"] and ob["bids"] else None,
                "mid_price": (ob["asks"][0][0] + ob["bids"][0][0]) / 2 if ob["asks"] and ob["bids"] else None,
            }
        except Exception as e:
            logger.error(f"Orderbook cekilemedi {symbol}: {e}")
            return {}

    def fetch_ticker(self, symbol: str) -> dict:
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"Ticker cekilemedi {symbol}: {e}")
            return {}

    def get_balance(self) -> dict:
        try:
            balance = self.exchange.fetch_balance()
            return {k: v for k, v in balance["total"].items() if v > 0}
        except Exception as e:
            logger.error(f"Bakiye cekilemedi: {e}")
            return {}
