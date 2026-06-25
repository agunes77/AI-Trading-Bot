from fastapi import APIRouter, Query
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()


@router.get("/check")
async def check_trade_eligibility(symbol: Optional[str] = None):
    try:
        from news.news_filter import NewsFilter
        nf = NewsFilter()
        can_trade, reason = nf.should_trade(symbol=symbol)
        return {
            "can_trade": can_trade,
            "reason": reason,
        }
    except Exception as e:
        return {"can_trade": True, "reason": "", "warning": str(e)}


@router.get("/sentiment")
async def get_market_sentiment(symbol: Optional[str] = None):
    try:
        from news.news_filter import NewsFilter
        nf = NewsFilter()
        condition = nf.get_market_condition(symbol=symbol)
        return condition
    except Exception as e:
        return {"error": str(e)}


@router.get("/events")
async def get_upcoming_events(
    hours_ahead: int = 24,
    currencies: Optional[str] = None,
):
    try:
        from news.news_filter import NewsFilter
        nf = NewsFilter()
        currency_list = currencies.split(",") if currencies else None
        events = nf.get_upcoming_events(hours_ahead=hours_ahead, currencies=currency_list)
        return {"events": events, "count": len(events)}
    except Exception as e:
        return {"events": [], "error": str(e)}


@router.get("/headlines")
async def get_latest_headlines(limit: int = 10):
    try:
        from news.news_filter import NewsFilter
        nf = NewsFilter()
        news = nf.get_latest_news(limit=limit)
        return {"news": news, "count": len(news)}
    except Exception as e:
        return {"news": [], "error": str(e)}
