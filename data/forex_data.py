import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.logger import logger
from config.settings import MT5_CONFIG

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None
    logger.warning("MetaTrader5 kutuphanesi bulunamadi. Sadece Windows'ta calisir.")

TIMEFRAME_MAP = {
    "M1": None, "M5": None, "M15": None, "M30": None,
    "H1": None, "H4": None, "D1": None, "W1": None,
}

def _get_tf(tf_str: str):
    if mt5 is None:
        return None
    mapping = {
        "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1,
    }
    return mapping.get(tf_str, mt5.TIMEFRAME_H1)


class ForexDataFetcher:
    def __init__(self, config=None):
        self.config = config or MT5_CONFIG
        self.connected = False

    def connect(self) -> bool:
        if mt5 is None:
            logger.error("MetaTrader5 kutuphanesi yuklu degil")
            return False
        if not mt5.initialize(
            path=self.config["path"],
            login=self.config["login"],
            password=self.config["password"],
            server=self.config["server"],
        ):
            logger.error(f"MT5 baglanti hatasi: {mt5.last_error()}")
            return False
        self.connected = True
        logger.info(f"MT5 baglandi: {self.config['server']}")
        return True

    def disconnect(self):
        if mt5 and self.connected:
            mt5.shutdown()
            self.connected = False

    def _ensure_symbols(self, symbols: list):
        for s in symbols:
            info = mt5.symbol_info(s)
            if info is None:
                logger.warning(f"Sembol bulunamadi: {s}")
                continue
            if not info.visible:
                mt5.symbol_select(s, True)

    def fetch_ohlcv(self, symbol: str, timeframe: str = None, count: int = 1000) -> pd.DataFrame:
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()
        tf = _get_tf(timeframe or self.config["default_timeframe"])
        self._ensure_symbols([symbol])
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        if rates is None or len(rates) == 0:
            logger.warning(f"MT5 veri yok: {symbol}")
            return pd.DataFrame()
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.rename(columns={"time": "timestamp", "tick_volume": "volume"}, inplace=True)
        df.set_index("timestamp", inplace=True)
        df = df[["open", "high", "low", "close", "volume"]].astype(np.float64)
        logger.debug(f"{symbol} | {timeframe} | {len(df)} mum")
        return df

    def fetch_historical(self, symbol: str, timeframe: str = "H1", days: int = 365) -> pd.DataFrame:
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()
        tf = _get_tf(timeframe)
        self._ensure_symbols([symbol])
        start = datetime.utcnow() - timedelta(days=days)
        rates = mt5.copy_rates_from(symbol, tf, start, days * 200)
        if rates is None or len(rates) == 0:
            return pd.DataFrame()
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.rename(columns={"time": "timestamp", "tick_volume": "volume"}, inplace=True)
        df.set_index("timestamp", inplace=True)
        df = df[["open", "high", "low", "close", "volume"]].astype(np.float64)
        df = df[~df.index.duplicated(keep="first")]
        logger.info(f"{symbol} | {timeframe} | {len(df)} mum ({days} gun)")
        return df

    def get_open_positions(self) -> pd.DataFrame:
        if not self.connected:
            return pd.DataFrame()
        positions = mt5.positions_get()
        if positions is None:
            return pd.DataFrame()
        return pd.DataFrame([p._asdict() for p in positions])

    def get_account_info(self) -> dict:
        if not self.connected:
            return {}
        info = mt5.account_info()
        return info._asdict() if info else {}
