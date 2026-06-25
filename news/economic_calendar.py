import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from utils.logger import logger


class ImpactLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class EconomicEvent:
    timestamp: datetime
    currency: str
    event: str
    impact: ImpactLevel
    forecast: Optional[str] = None
    previous: Optional[str] = None
    actual: Optional[str] = None
    url: Optional[str] = None


class EconomicCalendar:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        self._cache = {}
        self._cache_time = None
        self._cache_duration = timedelta(hours=1)

    def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        currencies: Optional[list] = None,
        impact: Optional[ImpactLevel] = None,
    ) -> list[EconomicEvent]:
        now = datetime.utcnow()

        if self._cache_time and (now - self._cache_time) < self._cache_duration and self._cache:
            logger.debug("Ekonomik takvim cache'den yuklendi")
            events = self._cache.get("events", [])
        else:
            events = self._fetch_events()
            self._cache = {"events": events}
            self._cache_time = now

        if start_date:
            events = [e for e in events if e.timestamp >= start_date]
        if end_date:
            events = [e for e in events if e.timestamp <= end_date]
        if currencies:
            events = [e for e in events if e.currency in currencies]
        if impact:
            events = [e for e in events if e.impact == impact]

        return events

    def _fetch_events(self) -> list[EconomicEvent]:
        try:
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            events = []
            for item in data:
                impact_str = item.get("impact", "low").lower()
                if impact_str == "holiday":
                    continue

                impact = ImpactLevel.LOW
                if impact_str in ("high", "red"):
                    impact = ImpactLevel.HIGH
                elif impact_str in ("medium", "orange"):
                    impact = ImpactLevel.MEDIUM

                date_str = item.get("date", "")
                try:
                    timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.utcnow()

                events.append(EconomicEvent(
                    timestamp=timestamp,
                    currency=item.get("currency", ""),
                    event=item.get("title", ""),
                    impact=impact,
                    forecast=item.get("forecast", ""),
                    previous=item.get("previous", ""),
                    actual=item.get("actual", ""),
                    url=item.get("url", ""),
                ))

            events.sort(key=lambda x: x.timestamp)
            logger.info(f"{len(events)} ekonomik etkinlik yuklendi")
            return events

        except Exception as e:
            logger.error(f"Ekonomik takvim verisi alinamadi: {e}")
            return []

    def get_upcoming_high_impact(self, hours_ahead: int = 24, currencies: Optional[list] = None) -> list[EconomicEvent]:
        now = datetime.utcnow()
        future = now + timedelta(hours=hours_ahead)
        events = self.get_events(start_date=now, end_date=future, impact=ImpactLevel.HIGH, currencies=currencies)
        return events

    def is_high_impact_event_near(self, minutes_threshold: int = 30, currencies: Optional[list] = None) -> tuple[bool, Optional[EconomicEvent]]:
        now = datetime.utcnow()
        threshold_time = now + timedelta(minutes=minutes_threshold)

        events = self.get_events(start_date=now, end_date=threshold_time, impact=ImpactLevel.HIGH, currencies=currencies)

        if events:
            return True, events[0]
        return False, None

    def get_market_sentiment_from_calendar(self, currencies: Optional[list] = None) -> dict:
        events = self.get_events(currencies=currencies)

        high_impact = [e for e in events if e.impact == ImpactLevel.HIGH]
        medium_impact = [e for e in events if e.impact == ImpactLevel.MEDIUM]

        now = datetime.utcnow()
        upcoming = [e for e in events if e.timestamp > now]

        sentiment_score = 0
        if len(high_impact) > 3:
            sentiment_score -= 20
        elif len(high_impact) > 1:
            sentiment_score -= 10

        if len(upcoming) > 5:
            sentiment_score -= 5

        return {
            "high_impact_count": len(high_impact),
            "medium_impact_count": len(medium_impact),
            "upcoming_count": len(upcoming),
            "sentiment_score": max(-100, min(100, sentiment_score)),
            "risk_level": "high" if len(high_impact) > 2 else "medium" if len(high_impact) > 0 else "low",
        }
