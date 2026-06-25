from fastapi import APIRouter
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()


@router.get("/status")
async def get_risk_status():
    try:
        from execution.risk_manager import RiskManager
        risk = RiskManager()
        return risk.get_status()
    except Exception as e:
        return {"error": str(e)}


@router.get("/report")
async def get_risk_report():
    try:
        from execution.risk_manager import RiskManager
        risk = RiskManager()
        return risk.get_risk_report()
    except Exception as e:
        return {"error": str(e)}


@router.get("/config")
async def get_risk_config():
    try:
        from config.settings import RISK_CONFIG
        return {
            "max_position_pct": RISK_CONFIG["max_position_pct"],
            "max_daily_loss_pct": RISK_CONFIG["max_daily_loss_pct"],
            "max_weekly_loss_pct": RISK_CONFIG["max_weekly_loss_pct"],
            "max_open_trades": RISK_CONFIG["max_open_trades"],
            "stop_loss_pct": RISK_CONFIG["stop_loss_pct"],
            "take_profit_pct": RISK_CONFIG["take_profit_pct"],
            "trailing_stop_pct": RISK_CONFIG["trailing_stop_pct"],
            "max_correlation": RISK_CONFIG["max_correlation"],
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/correlation-check")
async def check_correlation(symbol: str):
    try:
        from execution.risk_manager import RiskManager
        risk = RiskManager()
        is_correlated, reason = risk.check_correlation(symbol, {})
        return {
            "symbol": symbol,
            "is_correlated": is_correlated,
            "reason": reason,
        }
    except Exception as e:
        return {"symbol": symbol, "is_correlated": False, "reason": str(e)}
