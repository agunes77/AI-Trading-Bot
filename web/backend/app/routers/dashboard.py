from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()

class PortfolioSummary(BaseModel):
    total_balance: float
    total_pnl: float
    total_pnl_pct: float
    open_positions: int
    today_pnl: float
    today_pnl_pct: float
    assets: list

class DashboardData(BaseModel):
    portfolio: PortfolioSummary
    market_overview: dict
    recent_trades: list
    top_performers: list

@router.get("/summary", response_model=DashboardData)
async def get_dashboard_summary():
    try:
        from data.crypto_data import CryptoDataFetcher
        from execution.risk_manager import RiskManager
        
        fetcher = CryptoDataFetcher()
        balance = fetcher.get_balance()
        
        total_balance = sum(balance.values()) if balance else 10000.0
        
        portfolio = PortfolioSummary(
            total_balance=total_balance,
            total_pnl=total_balance - 10000.0,
            total_pnl_pct=((total_balance - 10000.0) / 10000.0) * 100,
            open_positions=0,
            today_pnl=0.0,
            today_pnl_pct=0.0,
            assets=[{"symbol": k, "amount": v} for k, v in balance.items()] if balance else []
        )
        
        market_overview = {
            "btc_price": 0.0,
            "eth_price": 0.0,
            "btc_change_24h": 0.0,
            "eth_change_24h": 0.0,
        }
        
        try:
            btc_ticker = fetcher.fetch_ticker("BTC/USDT")
            eth_ticker = fetcher.fetch_ticker("ETH/USDT")
            if btc_ticker:
                market_overview["btc_price"] = btc_ticker.get("last", 0)
                market_overview["btc_change_24h"] = btc_ticker.get("percentage", 0)
            if eth_ticker:
                market_overview["eth_price"] = eth_ticker.get("last", 0)
                market_overview["eth_change_24h"] = eth_ticker.get("percentage", 0)
        except:
            pass
        
        return DashboardData(
            portfolio=portfolio,
            market_overview=market_overview,
            recent_trades=[],
            top_performers=[]
        )
    except Exception as e:
        return DashboardData(
            portfolio=PortfolioSummary(
                total_balance=10000.0,
                total_pnl=0.0,
                total_pnl_pct=0.0,
                open_positions=0,
                today_pnl=0.0,
                today_pnl_pct=0.0,
                assets=[]
            ),
            market_overview={"btc_price": 0, "eth_price": 0, "btc_change_24h": 0, "eth_change_24h": 0},
            recent_trades=[],
            top_performers=[]
        )

@router.get("/portfolio")
async def get_portfolio():
    try:
        from data.crypto_data import CryptoDataFetcher
        fetcher = CryptoDataFetcher()
        balance = fetcher.get_balance()
        return {"balance": balance, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"balance": {}, "error": str(e)}

@router.get("/market-overview")
async def get_market_overview():
    try:
        from data.crypto_data import CryptoDataFetcher
        fetcher = CryptoDataFetcher()
        
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"]
        overview = []
        
        for symbol in symbols:
            try:
                ticker = fetcher.fetch_ticker(symbol)
                if ticker:
                    overview.append({
                        "symbol": symbol,
                        "price": ticker.get("last", 0),
                        "change_24h": ticker.get("percentage", 0),
                        "volume_24h": ticker.get("quoteVolume", 0),
                        "high_24h": ticker.get("high", 0),
                        "low_24h": ticker.get("low", 0),
                    })
            except:
                pass
        
        return {"markets": overview}
    except Exception as e:
        return {"markets": [], "error": str(e)}
