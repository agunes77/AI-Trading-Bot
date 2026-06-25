from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()

class BacktestRequest(BaseModel):
    source: str
    symbol: str
    strategy: str
    timeframe: str = "1h"
    days: int = 365
    initial_balance: float = 10000.0
    stop_loss: float = 0.02
    take_profit: float = 0.04

class StrategyCompareRequest(BaseModel):
    source: str
    symbol: str
    timeframe: str = "1h"
    days: int = 365
    initial_balance: float = 10000.0
    stop_loss: float = 0.02
    take_profit: float = 0.04

@router.get("/list")
async def list_strategies():
    try:
        from strategies.classic_strategies import ALL_STRATEGIES
        
        strategies = []
        for key, cls in ALL_STRATEGIES.items():
            s = cls()
            strategies.append({
                "key": key,
                "name": s.name,
                "description": s.describe(),
                "params": s.params,
            })
        
        return {"strategies": strategies, "count": len(strategies)}
    except Exception as e:
        return {"strategies": [], "error": str(e)}

@router.post("/backtest")
async def run_strategy_backtest(request: BacktestRequest):
    try:
        from data.data_manager import DataManager
        from backtesting.strategy_backtester import StrategyBacktester
        
        dm = DataManager()
        if request.source == "crypto":
            df = dm.get_crypto_data(request.symbol, request.timeframe, request.days)
        else:
            df = dm.get_forex_data(request.symbol, request.timeframe, request.days)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Veri bulunamadi")
        
        sb = StrategyBacktester()
        result = sb.run_single(
            df, request.strategy, request.symbol,
            initial_balance=request.initial_balance,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
        )
        
        result.pop("equity_curve", None)
        result.pop("trades", None)
        
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_strategies(request: StrategyCompareRequest):
    try:
        from data.data_manager import DataManager
        from backtesting.strategy_backtester import StrategyBacktester
        
        dm = DataManager()
        if request.source == "crypto":
            df = dm.get_crypto_data(request.symbol, request.timeframe, request.days)
        else:
            df = dm.get_forex_data(request.symbol, request.timeframe, request.days)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Veri bulunamadi")
        
        sb = StrategyBacktester()
        comparison = sb.run_comparison(
            df, request.symbol,
            initial_balance=request.initial_balance,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
        )
        
        return {"success": True, "comparison": comparison.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/top")
async def get_top_strategies(request: StrategyCompareRequest):
    try:
        from data.data_manager import DataManager
        from backtesting.strategy_backtester import StrategyBacktester
        
        dm = DataManager()
        if request.source == "crypto":
            df = dm.get_crypto_data(request.symbol, request.timeframe, request.days)
        else:
            df = dm.get_forex_data(request.symbol, request.timeframe, request.days)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Veri bulunamadi")
        
        sb = StrategyBacktester()
        top = sb.run_top_strategies(df, request.symbol, top_n=5)
        
        for r in top:
            r.pop("equity_curve", None)
            r.pop("trades", None)
        
        return {"success": True, "top_strategies": top}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
