from datetime import datetime, timedelta
from typing import Optional
from news.economic_calendar import EconomicCalendar, ImpactLevel
from news.news_sentiment import NewsSentiment
from utils.logger import logger


class NewsFilter:
    def __init__(self):
        self.calendar = EconomicCalendar()
        self.sentiment = NewsSentiment()
        self._last_check = None
        self._cached_news = []
        self._cache_duration = timedelta(minutes=15)

    def should_trade(self, symbol: str = None, currencies: list = None) -> tuple[bool, str]:
        symbol_currencies = currencies or self._extract_currencies(symbol)

        is_event_near, event = self.calendar.is_high_impact_event_near(minutes_threshold=30, currencies=symbol_currencies)
        if is_event_near:
            return False, f"Yuksek etkili etkinlik yakinda: {event.event} ({event.timestamp})"

        news_items = self._get_cached_news()
        should_pause, reason = self.sentiment.should_pause_trading(news_items)
        if should_pause:
            return False, f"Haber filtresi: {reason}"

        sentiment_data = self.sentiment.get_overall_sentiment(news_items)
        if sentiment_data["market_mood"] in ("bearish", "slightly_bearish"):
            logger.warning(f"Piyasa havasi negatif: {sentiment_data['market_mood']}")

        return True, ""

    def _get_cached_news(self) -> list:
        now = datetime.utcnow()
        if self._last_check and (now - self._last_check) < self._cache_duration and self._cached_news:
            return self._cached_news

        self._cached_news = self.sentiment.get_crypto_news(limit=30)
        self._last_check = now
        return self._cached_news

    def _extract_currencies(self, symbol: Optional[str]) -> Optional[list]:
        if not symbol:
            return None

        symbol_upper = symbol.upper()

        forex_map = {
            "EURUSD": ["EUR", "USD"], "GBPUSD": ["GBP", "USD"],
            "USDJPY": ["USD", "JPY"], "AUDUSD": ["AUD", "USD"],
            "USDCAD": ["USD", "CAD"], "USDCHF": ["USD", "CHF"],
            "NZDUSD": ["NZD", "USD"],
        }

        if symbol_upper in forex_map:
            return forex_map[symbol_upper]

        if "/" in symbol:
            base, quote = symbol.split("/")
            return [base, quote]

        return None

    def get_market_condition(self, symbol: str = None) -> dict:
        symbol_currencies = self._extract_currencies(symbol)

        calendar_sentiment = self.calendar.get_market_sentiment_from_calendar(currencies=symbol_currencies)
        news_items = self._get_cached_news()
        news_sentiment = self.sentiment.get_overall_sentiment(news_items)

        overall_score = 0
        overall_score += calendar_sentiment["sentiment_score"] * 0.4
        overall_score += news_sentiment["average_sentiment"] * 100 * 0.6

        if overall_score > 20:
            condition = "bullish"
        elif overall_score < -20:
            condition = "bearish"
        else:
            condition = "neutral"

        return {
            "calendar": calendar_sentiment,
            "news": news_sentiment,
            "overall_score": overall_score,
            "market_condition": condition,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_upcoming_events(self, hours_ahead: int = 24, currencies: list = None) -> list:
        events = self.calendar.get_upcoming_high_impact(hours_ahead=hours_ahead, currencies=currencies)
        return [
            {
                "time": e.timestamp.isoformat(),
                "currency": e.currency,
                "event": e.event,
                "impact": e.impact.value,
                "forecast": e.forecast,
                "previous": e.previous,
            }
            for e in events
        ]

    def get_latest_news(self, limit: int = 10) -> list:
        news_items = self._get_cached_news()[:limit]
        return [
            {
                "title": n.title,
                "source": n.source,
                "time": n.timestamp.isoformat(),
                "sentiment": n.sentiment,
                "url": n.url,
                "high_impact": bool(n.keywords),
            }
            for n in news_items
        ]
