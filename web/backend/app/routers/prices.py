from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()

@router.get("/crypto/{symbol}")
async def get_crypto_price(symbol: str, timeframe: str = "1h", limit: int = 100):
    try:
        from data.crypto_data import CryptoDataFetcher
        from features.technical_indicators import FeatureEngineer
        
        fetcher = CryptoDataFetcher()
        df = fetcher.fetch_ohlcv(symbol, timeframe, limit)
        
        if df.empty:
            return {"symbol": symbol, "data": [], "error": "Veri yok"}
        
        fe = FeatureEngineer()
        df = fe.add_all_indicators(df)
        
        data = []
        for idx, row in df.iterrows():
            data.append({
                "timestamp": idx.isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
                "rsi": float(row.get("rsi", 0)),
                "macd": float(row.get("macd", 0)),
                "macd_signal": float(row.get("macd_signal", 0)),
                "bb_high": float(row.get("bb_high", 0)),
                "bb_low": float(row.get("bb_low", 0)),
            })
        
        return {"symbol": symbol, "timeframe": timeframe, "data": data}
    except Exception as e:
        return {"symbol": symbol, "data": [], "error": str(e)}

@router.get("/forex/{symbol}")
async def get_forex_price(symbol: str, timeframe: str = "H1", limit: int = 100):
    try:
        from data.forex_data import ForexDataFetcher
        from features.technical_indicators import FeatureEngineer
        
        fetcher = ForexDataFetcher()
        if not fetcher.connect():
            return {"symbol": symbol, "data": [], "error": "MT5 baglantisi basarisiz"}
        
        df = fetcher.fetch_ohlcv(symbol, timeframe, limit)
        fetcher.disconnect()
        
        if df.empty:
            return {"symbol": symbol, "data": [], "error": "Veri yok"}
        
        fe = FeatureEngineer()
        df = fe.add_all_indicators(df)
        
        data = []
        for idx, row in df.iterrows():
            data.append({
                "timestamp": idx.isoformat(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
                "rsi": float(row.get("rsi", 0)),
                "macd": float(row.get("macd", 0)),
                "macd_signal": float(row.get("macd_signal", 0)),
            })
        
        return {"symbol": symbol, "timeframe": timeframe, "data": data}
    except Exception as e:
        return {"symbol": symbol, "data": [], "error": str(e)}

@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str, source: str = "crypto"):
    try:
        if source == "crypto":
            from data.crypto_data import CryptoDataFetcher
            fetcher = CryptoDataFetcher()
            ticker = fetcher.fetch_ticker(symbol)
            return {"symbol": symbol, "ticker": ticker}
        else:
            return {"symbol": symbol, "ticker": {}, "error": "Forex ticker desteklenmiyor"}
    except Exception as e:
        return {"symbol": symbol, "ticker": {}, "error": str(e)}

@router.get("/orderbook/{symbol}")
async def get_orderbook(symbol: str, limit: int = 20):
    try:
        from data.crypto_data import CryptoDataFetcher
        fetcher = CryptoDataFetcher()
        ob = fetcher.fetch_orderbook(symbol, limit)
        return {"symbol": symbol, "orderbook": ob}
    except Exception as e:
        return {"symbol": symbol, "orderbook": {}, "error": str(e)}
