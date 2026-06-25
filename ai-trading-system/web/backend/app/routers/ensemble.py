from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()


class EnsembleBacktestRequest(BaseModel):
    source: str
    symbol: str
    timeframe: str = "1h"
    days: int = 365
    initial_balance: float = 10000.0
    lookahead: int = 5
    threshold: float = 0.005
    stop_loss: float = 0.02
    take_profit: float = 0.04


@router.post("/backtest")
async def run_ensemble_backtest(request: EnsembleBacktestRequest):
    try:
        from data.data_manager import DataManager
        from ensemble.ensemble_backtester import EnsembleBacktester

        dm = DataManager()
        if request.source == "crypto":
            df = dm.get_crypto_data(request.symbol, request.timeframe, request.days)
        else:
            df = dm.get_forex_data(request.symbol, request.timeframe, request.days)

        if df.empty:
            raise HTTPException(status_code=400, detail="Veri bulunamadi")

        eb = EnsembleBacktester()
        result = eb.run(
            df, symbol=request.symbol,
            initial_balance=request.initial_balance,
            lookahead=request.lookahead,
            threshold=request.threshold,
            stop_loss_pct=request.stop_loss,
            take_profit_pct=request.take_profit,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        result.pop("backtest", {}).pop("equity_curve", None)

        return {"success": True, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/availability")
async def check_model_availability():
    try:
        from ensemble.ensemble_ml import XGBOOST_AVAILABLE, LIGHTGBM_AVAILABLE, CATBOOST_AVAILABLE
        return {
            "xgboost": XGBOOST_AVAILABLE,
            "lightgbm": LIGHTGBM_AVAILABLE,
            "catboost": CATBOOST_AVAILABLE,
        }
    except Exception as e:
        return {"error": str(e)}
