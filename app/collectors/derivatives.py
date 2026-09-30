"""
Derivatives Collector: Open Interest, Funding Rates, Long/Short Ratios, Liquidations
"""

import time
import logging
from typing import Dict, Any, List
import httpx
import numpy as np

from app.config import (
    BINANCE_FUTURES_API,
    BINANCE_DATA_API,
    PRIMARY_SYMBOL,
    CACHE_TTL
)

logger = logging.getLogger(__name__)

class DerivativesCollector:
    def __init__(self, symbol: str = PRIMARY_SYMBOL):
        self.symbol = symbol
        self._cache: Dict[str, Any] = {"data": None, "timestamp": 0}
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def get_derivatives_data(self) -> Dict[str, Any]:
        """Fetch comprehensive derivatives metrics for BTCUSDT."""
        now = time.time()
        if self._cache["data"] and (now - self._cache["timestamp"]) < CACHE_TTL["derivatives"]:
            return self._cache["data"]

        try:
            # Concurrent requests for derivatives metrics
            oi_task = self.client.get(f"{BINANCE_FUTURES_API}/openInterest", params={"symbol": self.symbol})
            prem_task = self.client.get(f"{BINANCE_FUTURES_API}/premiumIndex", params={"symbol": self.symbol})
            funding_hist_task = self.client.get(f"{BINANCE_FUTURES_API}/fundingRate", params={"symbol": self.symbol, "limit": 10})
            ls_ratio_task = self.client.get(f"{BINANCE_DATA_API}/globalLongShortAccountRatio", params={"symbol": self.symbol, "period": "15m", "limit": 15})
            taker_ratio_task = self.client.get(f"{BINANCE_DATA_API}/takerlongshortRatio", params={"symbol": self.symbol, "period": "15m", "limit": 15})

            responses = await httpx.AsyncClient().get(f"{BINANCE_FUTURES_API}/openInterest", params={"symbol": self.symbol})
            
            # Using self.client with gather
            import asyncio
            oi_resp, prem_resp, funding_resp, ls_resp, taker_resp = await asyncio.gather(
                oi_task, prem_task, funding_hist_task, ls_ratio_task, taker_ratio_task,
                return_exceptions=True
            )

            # 1. Open Interest
            open_interest_btc = 0.0
            if not isinstance(oi_resp, Exception) and oi_resp.status_code == 200:
                oi_data = oi_resp.json()
                open_interest_btc = float(oi_data.get("openInterest", 0.0))

            # 2. Funding Rate & Mark Price
            current_funding_rate = 0.0001
            mark_price = 0.0
            index_price = 0.0
            next_funding_time = 0
            if not isinstance(prem_resp, Exception) and prem_resp.status_code == 200:
                p_data = prem_resp.json()
                current_funding_rate = float(p_data.get("lastFundingRate", 0.0001))
                mark_price = float(p_data.get("markPrice", 0.0))
                index_price = float(p_data.get("indexPrice", 0.0))
                next_funding_time = int(p_data.get("nextFundingTime", 0))

            # 3. Funding Rate History & Trend
            funding_history = []
            if not isinstance(funding_resp, Exception) and funding_resp.status_code == 200:
                for item in funding_resp.json():
                    funding_history.append({
                        "fundingRate": float(item["fundingRate"]),
                        "fundingTime": int(item["fundingTime"])
                    })

            # 4. Long / Short Account Ratio
            long_short_ratio = 1.0
            long_account_pct = 50.0
            short_account_pct = 50.0
            ls_trend = "NEUTRAL"
            if not isinstance(ls_resp, Exception) and ls_resp.status_code == 200:
                ls_data = ls_resp.json()
                if ls_data:
                    latest_ls = ls_data[-1]
                    long_short_ratio = float(latest_ls.get("longShortRatio", 1.0))
                    long_account_pct = float(latest_ls.get("longAccount", 0.5)) * 100
                    short_account_pct = float(latest_ls.get("shortAccount", 0.5)) * 100
                    if len(ls_data) >= 3:
                        prev_ls = float(ls_data[0].get("longShortRatio", 1.0))
                        if long_short_ratio > prev_ls * 1.05:
                            ls_trend = "LONGS_INCREASING"
                        elif long_short_ratio < prev_ls * 0.95:
                            ls_trend = "SHORTS_INCREASING"

            # 5. Taker Buy/Sell Volume Ratio
            buy_vol_ratio = 1.0
            buy_vol_pct = 50.0
            sell_vol_pct = 50.0
            if not isinstance(taker_resp, Exception) and taker_resp.status_code == 200:
                t_data = taker_resp.json()
                if t_data:
                    latest_taker = t_data[-1]
                    buy_vol_ratio = float(latest_taker.get("buySellRatio", 1.0))
                    buy_vol_pct = float(latest_taker.get("buyVol", 50.0))
                    sell_vol_pct = float(latest_taker.get("sellVol", 50.0))

            # Derived Metrics & Risk Interpretations
            annualized_funding_pct = current_funding_rate * 3 * 365 * 100
            oi_usdt = open_interest_btc * (mark_price if mark_price > 0 else 64000.0)

            # Liquidation squeeze risk gauge (-100 heavy short squeeze risk to +100 heavy long liquidation cascade risk)
            squeeze_risk_score = 0.0
            if current_funding_rate > 0.0003: # > 0.03% per 8h is elevated
                squeeze_risk_score += 40
            elif current_funding_rate < -0.0002: # Negative funding = shorts crowded
                squeeze_risk_score -= 40

            if long_short_ratio > 2.0:
                squeeze_risk_score += 35 # Retail heavily long, vulnerable to long squeeze
            elif long_short_ratio < 0.7:
                squeeze_risk_score -= 35 # Retail heavily short, fuel for short squeeze

            result = {
                "symbol": self.symbol,
                "mark_price": mark_price,
                "index_price": index_price,
                "open_interest_btc": round(open_interest_btc, 2),
                "open_interest_usdt": round(oi_usdt, 2),
                "current_funding_rate": current_funding_rate,
                "annualized_funding_pct": round(annualized_funding_pct, 2),
                "next_funding_time": next_funding_time,
                "funding_history": funding_history,
                "long_short_ratio": round(long_short_ratio, 3),
                "long_account_pct": round(long_account_pct, 1),
                "short_account_pct": round(short_account_pct, 1),
                "ls_trend": ls_trend,
                "taker_buy_sell_ratio": round(buy_vol_ratio, 3),
                "squeeze_risk_score": round(squeeze_risk_score, 1),
                "sentiment_bias": "OVERHEATED_BULLISH" if annualized_funding_pct > 25 and long_short_ratio > 1.8 else ("EXTREME_BEARISH_CROWDED" if annualized_funding_pct < -5 else "HEALTHY_BALANCED"),
                "timestamp": int(now * 1000),
                "status": "LIVE"
            }
            self._cache = {"data": result, "timestamp": now}
            return result

        except Exception as e:
            logger.warning(f"Error fetching derivatives data: {e}. Using fallback.")
            return self._generate_fallback_derivatives()

    def _generate_fallback_derivatives(self) -> Dict[str, Any]:
        """Realistic fallback for derivatives metrics."""
        return {
            "symbol": self.symbol,
            "mark_price": 64520.0,
            "index_price": 64510.0,
            "open_interest_btc": 78450.0,
            "open_interest_usdt": 5061594000.0,
            "current_funding_rate": 0.000100,
            "annualized_funding_pct": 10.95,
            "next_funding_time": int(time.time() * 1000) + 14400000,
            "funding_history": [{"fundingRate": 0.0001, "fundingTime": int(time.time()*1000) - i*28800000} for i in range(5)],
            "long_short_ratio": 1.25,
            "long_account_pct": 55.6,
            "short_account_pct": 44.4,
            "ls_trend": "NEUTRAL",
            "taker_buy_sell_ratio": 1.08,
            "squeeze_risk_score": 10.0,
            "sentiment_bias": "HEALTHY_BALANCED",
            "timestamp": int(time.time() * 1000),
            "status": "SIMULATED_FALLBACK"
        }
