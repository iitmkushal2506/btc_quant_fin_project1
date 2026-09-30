"""
Crypto Sentiment Collector: Alternative.me Fear & Greed Index & Momentum
"""

import time
import logging
from typing import Dict, Any, List
import httpx

from app.config import FEAR_GREED_API, CACHE_TTL

logger = logging.getLogger(__name__)

class SentimentCollector:
    def __init__(self):
        self._cache: Dict[str, Any] = {"data": None, "timestamp": 0}
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def get_sentiment_data(self) -> Dict[str, Any]:
        """Fetch Crypto Fear & Greed Index and calculate sentiment momentum."""
        now = time.time()
        if self._cache["data"] and (now - self._cache["timestamp"]) < CACHE_TTL["sentiment"]:
            return self._cache["data"]

        try:
            resp = await self.client.get(FEAR_GREED_API)
            if resp.status_code == 200:
                raw = resp.json()
                items = raw.get("data", [])
                if items:
                    current_item = items[0]
                    score = int(current_item.get("value", 50))
                    label = current_item.get("value_classification", "Neutral")
                    
                    history = []
                    for it in items[:14]:
                        history.append({
                            "score": int(it.get("value", 50)),
                            "label": it.get("value_classification", "Neutral"),
                            "timestamp": int(it.get("timestamp", 0))
                        })

                    # Calculate momentum
                    prev_day_score = int(items[1].get("value", score)) if len(items) > 1 else score
                    prev_week_score = int(items[7].get("value", score)) if len(items) > 7 else score
                    
                    momentum_1d = score - prev_day_score
                    momentum_7d = score - prev_week_score

                    # Contrarian / Overcrowded indicator
                    # Extreme Greed (>75) -> increased pullback risk; Extreme Fear (<25) -> oversold / accumulation zone
                    sentiment_bias = "CONTRARIAN_LONG_FAVORED" if score < 25 else (
                        "OVERHEATED_RISK_HIGH" if score > 75 else "BALANCED_TREND_CONTINUATION"
                    )

                    result = {
                        "score": score,
                        "label": label,
                        "previous_day_score": prev_day_score,
                        "previous_week_score": prev_week_score,
                        "momentum_1d": momentum_1d,
                        "momentum_7d": momentum_7d,
                        "sentiment_bias": sentiment_bias,
                        "history": history,
                        "status": "LIVE",
                        "timestamp": int(now * 1000)
                    }
                    self._cache = {"data": result, "timestamp": now}
                    return result

        except Exception as e:
            logger.warning(f"Error fetching Fear & Greed index: {e}. Generating fallback.")

        return self._generate_fallback_sentiment()

    def _generate_fallback_sentiment(self) -> Dict[str, Any]:
        """Fallback mock for Fear & Greed sentiment."""
        return {
            "score": 62,
            "label": "Greed",
            "previous_day_score": 58,
            "previous_week_score": 52,
            "momentum_1d": 4,
            "momentum_7d": 10,
            "sentiment_bias": "BALANCED_TREND_CONTINUATION",
            "history": [
                {"score": 62 - i, "label": "Greed" if (62-i) > 55 else "Neutral", "timestamp": int(time.time()) - i*86400}
                for i in range(14)
            ],
            "status": "SIMULATED_FALLBACK",
            "timestamp": int(time.time() * 1000)
        }
