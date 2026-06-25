from fastapi import APIRouter
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()

@router.get("/history")
async def get_trade_history(limit: int = 50):
    try:
        return {
            "trades": [],
            "count": 0,
            "message": "Trade gecmisi suan bos. Canli trade baslatildiginda islemler burada gorunecek."
        }
    except Exception as e:
        return {"trades": [], "error": str(e)}

@router.get("/open-positions")
async def get_open_positions():
    try:
        from data.crypto_data import CryptoDataFetcher
        fetcher = CryptoDataFetcher()
        
        balance = fetcher.get_balance()
        
        positions = []
        for symbol, amount in balance.items():
            if symbol != "USDT" and amount > 0:
                try:
                    ticker = fetcher.fetch_ticker(f"{symbol}/USDT")
                    if ticker:
                        positions.append({
                            "symbol": f"{symbol}/USDT",
                            "amount": amount,
                            "current_price": ticker.get("last", 0),
                            "value": amount * ticker.get("last", 0),
                            "change_24h": ticker.get("percentage", 0),
                        })
                except:
                    pass
        
        return {"positions": positions, "count": len(positions)}
    except Exception as e:
        return {"positions": [], "error": str(e)}

@router.get("/performance")
async def get_performance():
    try:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "message": "Henuz trade gecmisi yok"
        }
    except Exception as e:
        return {"error": str(e)}
