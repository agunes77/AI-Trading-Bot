import pandas as pd
from pathlib import Path
from data.crypto_data import CryptoDataFetcher
from data.forex_data import ForexDataFetcher
from utils.logger import logger
from config.settings import DATA_DIR


class DataManager:
    def __init__(self):
        self.crypto = CryptoDataFetcher()
        self.forex = ForexDataFetcher()
        self._cache_dir = DATA_DIR

    def get_crypto_data(self, symbol: str, timeframe: str = "1h", days: int = 365, use_cache: bool = True) -> pd.DataFrame:
        cache_file = self._cache_dir / f"crypto_{symbol.replace('/', '_')}_{timeframe}_{days}d.parquet"
        if use_cache and cache_file.exists():
            logger.info(f"Cache'den yukleniyor: {cache_file.name}")
            return pd.read_parquet(cache_file)
        df = self.crypto.fetch_historical(symbol, timeframe, days)
        if not df.empty and use_cache:
            df.to_parquet(cache_file)
            logger.info(f"Cache'e kaydedildi: {cache_file.name}")
        return df

    def get_forex_data(self, symbol: str, timeframe: str = "H1", days: int = 365, use_cache: bool = True) -> pd.DataFrame:
        cache_file = self._cache_dir / f"forex_{symbol}_{timeframe}_{days}d.parquet"
        if use_cache and cache_file.exists():
            logger.info(f"Cache'den yukleniyor: {cache_file.name}")
            return pd.read_parquet(cache_file)
        df = self.forex.fetch_historical(symbol, timeframe, days)
        if not df.empty and use_cache:
            df.to_parquet(cache_file)
            logger.info(f"Cache'e kaydedildi: {cache_file.name}")
        return df

    def get_latest(self, source: str, symbol: str, timeframe: str = None, limit: int = 100) -> pd.DataFrame:
        if source == "crypto":
            return self.crypto.fetch_ohlcv(symbol, timeframe, limit)
        elif source == "forex":
            return self.forex.fetch_ohlcv(symbol, timeframe, limit)
        return pd.DataFrame()
