import requests
import re
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from utils.logger import logger


@dataclass
class NewsItem:
    title: str
    source: str
    timestamp: datetime
    url: str
    sentiment: float = 0.0
    keywords: list = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class NewsSentiment:
    def __init__(self):
        self.positive_words = {
            "bullish", "surge", "rally", "gain", "rise", "growth", "profit", "strong",
            "breakout", "optimism", "recovery", "upgrade", "buy", "higher", "momentum",
            "positive", "success", "improvement", "boost", "advance", "uptrend",
        }
        self.negative_words = {
            "bearish", "crash", "drop", "fall", "decline", "loss", "weak", "plunge",
            "sell-off", "pessimism", "downgrade", "sell", "lower", "correction",
            "negative", "failure", "deterioration", "risk", "downtrend", "fear",
        }
        self.high_impact_keywords = {
            "fed", "fomc", "interest rate", "inflation", "cpi", "gdp", "employment",
            "nfp", "nonfarm", "powell", "ecb", "boe", "boj", "recession", "default",
        }

    def analyze_text(self, text: str) -> float:
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        positive_count = len(words & self.positive_words)
        negative_count = len(words & self.negative_words)
        total = positive_count + negative_count

        if total == 0:
            return 0.0

        sentiment = (positive_count - negative_count) / total
        return max(-1.0, min(1.0, sentiment))

    def is_high_impact(self, text: str) -> bool:
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.high_impact_keywords)

    def get_crypto_news(self, limit: int = 20) -> list[NewsItem]:
        try:
            url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            news_items = []
            for item in data.get("Data", [])[:limit]:
                title = item.get("title", "")
                body = item.get("body", "")
                full_text = f"{title} {body}"

                sentiment = self.analyze_text(full_text)
                is_high = self.is_high_impact(full_text)

                news_items.append(NewsItem(
                    title=title,
                    source=item.get("source", ""),
                    timestamp=datetime.fromtimestamp(item.get("published_on", 0)),
                    url=item.get("url", ""),
                    sentiment=sentiment,
                    keywords=list(self.high_impact_keywords & set(full_text.lower().split())) if is_high else [],
                ))

            logger.info(f"{len(news_items)} kripto haberi yuklendi")
            return news_items

        except Exception as e:
            logger.error(f"Kripto haberleri alinamadi: {e}")
            return []

    def get_overall_sentiment(self, news_items: list[NewsItem]) -> dict:
        if not news_items:
            return {
                "average_sentiment": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "high_impact_count": 0,
                "market_mood": "neutral",
            }

        sentiments = [n.sentiment for n in news_items]
        avg_sentiment = sum(sentiments) / len(sentiments)

        positive = sum(1 for s in sentiments if s > 0.2)
        negative = sum(1 for s in sentiments if s < -0.2)
        neutral = len(sentiments) - positive - negative

        high_impact = sum(1 for n in news_items if n.keywords)

        if avg_sentiment > 0.3:
            mood = "bullish"
        elif avg_sentiment < -0.3:
            mood = "bearish"
        elif positive > negative * 1.5:
            mood = "slightly_bullish"
        elif negative > positive * 1.5:
            mood = "slightly_bearish"
        else:
            mood = "neutral"

        return {
            "average_sentiment": avg_sentiment,
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "high_impact_count": high_impact,
            "market_mood": mood,
        }

    def should_pause_trading(self, news_items: list[NewsItem], threshold: float = -0.5) -> tuple[bool, str]:
        sentiment_data = self.get_overall_sentiment(news_items)

        if sentiment_data["average_sentiment"] < threshold:
            return True, f"Piyasa cok negatif (sentiment: {sentiment_data['average_sentiment']:.2f})"

        if sentiment_data["high_impact_count"] >= 3:
            return True, f"Cok fazla yuksek etkili haber ({sentiment_data['high_impact_count']} adet)"

        recent_news = [n for n in news_items if (datetime.utcnow() - n.timestamp).total_seconds() < 3600]
        negative_recent = sum(1 for n in recent_news if n.sentiment < -0.5)

        if negative_recent >= 2:
            return True, f"Son 1 saatte {negative_recent} negatif haber"

        return False, ""
