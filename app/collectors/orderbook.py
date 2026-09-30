"""
Orderbook & Liquidity Depth Collector: Walls, Spreads, and Imbalance Metrics
"""

import time
import logging
from typing import Dict, Any, List
import httpx
import numpy as np

from app.config import BINANCE_SPOT_API, PRIMARY_SYMBOL, CACHE_TTL

logger = logging.getLogger(__name__)

class OrderbookCollector:
    def __init__(self, symbol: str = PRIMARY_SYMBOL):
        self.symbol = symbol
        self._cache: Dict[str, Any] = {"data": None, "timestamp": 0}
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def get_orderbook_metrics(self, limit: int = 100) -> Dict[str, Any]:
        """Fetch depth and compute liquidity imbalance, walls, and spread."""
        now = time.time()
        if self._cache["data"] and (now - self._cache["timestamp"]) < CACHE_TTL["orderbook"]:
            return self._cache["data"]

        url = f"{BINANCE_SPOT_API}/depth"
        params = {"symbol": self.symbol, "limit": limit}

        try:
            resp = await self.client.get(url, params=params)
            if resp.status_code == 200:
                raw = resp.json()
                bids = [[float(p), float(q)] for p, q in raw.get("bids", [])]
                asks = [[float(p), float(q)] for p, q in raw.get("asks", [])]

                metrics = self._analyze_orderbook(bids, asks)
                metrics["status"] = "LIVE"
                metrics["timestamp"] = int(now * 1000)
                self._cache = {"data": metrics, "timestamp": now}
                return metrics
        except Exception as e:
            logger.warning(f"Error fetching orderbook for {self.symbol}: {e}. Generating fallback.")

        return self._generate_fallback_orderbook()

    def _analyze_orderbook(self, bids: List[List[float]], asks: List[List[float]]) -> Dict[str, Any]:
        if not bids or not asks:
            return self._generate_fallback_orderbook()

        best_bid = bids[0][0]
        best_ask = asks[0][0]
        mid_price = (best_bid + best_ask) / 2.0
        spread_usd = best_ask - best_bid
        spread_bps = (spread_usd / mid_price) * 10000

        total_bid_qty = sum(q for _, q in bids)
        total_ask_qty = sum(q for _, q in asks)
        total_bid_usd = sum(p * q for p, q in bids)
        total_ask_usd = sum(p * q for p, q in asks)

        # Order Book Imbalance (OBI) - range [-1.0, 1.0]
        imbalance = 0.0
        if (total_bid_qty + total_ask_qty) > 0:
            imbalance = (total_bid_qty - total_ask_qty) / (total_bid_qty + total_ask_qty)

        # Depth within 1% and 2% of mid price
        bid_depth_1pct = sum(p * q for p, q in bids if p >= mid_price * 0.99)
        ask_depth_1pct = sum(p * q for p, q in asks if p <= mid_price * 1.01)
        imbalance_1pct = 0.0
        if (bid_depth_1pct + ask_depth_1pct) > 0:
            imbalance_1pct = (bid_depth_1pct - ask_depth_1pct) / (bid_depth_1pct + ask_depth_1pct)

        # Detect Significant Liquidity Walls (>= 2.5x mean level volume)
        mean_bid_vol = np.mean([q for _, q in bids]) if bids else 1.0
        mean_ask_vol = np.mean([q for _, q in asks]) if asks else 1.0

        bid_walls = []
        for p, q in bids:
            if q >= mean_bid_vol * 2.5 and q >= 15.0: # Significant BTC wall
                bid_walls.append({
                    "price": p,
                    "quantity_btc": round(q, 2),
                    "value_usd": round(p * q, 2),
                    "distance_pct": round(((p - mid_price) / mid_price) * 100, 2)
                })

        ask_walls = []
        for p, q in asks:
            if q >= mean_ask_vol * 2.5 and q >= 15.0:
                ask_walls.append({
                    "price": p,
                    "quantity_btc": round(q, 2),
                    "value_usd": round(p * q, 2),
                    "distance_pct": round(((p - mid_price) / mid_price) * 100, 2)
                })

        # Top 5 Bids and Asks for visual depth chart
        ladder_bids = [{"price": p, "qty": q, "total": round(p * q, 2)} for p, q in bids[:8]]
        ladder_asks = [{"price": p, "qty": q, "total": round(p * q, 2)} for p, q in asks[:8]]

        return {
            "symbol": self.symbol,
            "mid_price": round(mid_price, 2),
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread_usd": round(spread_usd, 2),
            "spread_bps": round(spread_bps, 3),
            "total_bid_btc": round(total_bid_qty, 2),
            "total_ask_btc": round(total_ask_qty, 2),
            "total_bid_usd": round(total_bid_usd, 2),
            "total_ask_usd": round(total_ask_usd, 2),
            "orderbook_imbalance": round(imbalance, 3),
            "orderbook_imbalance_1pct": round(imbalance_1pct, 3),
            "imbalance_interpretation": "BUY_PRESSURE" if imbalance > 0.15 else ("SELL_PRESSURE" if imbalance < -0.15 else "BALANCED"),
            "bid_walls": bid_walls[:5],
            "ask_walls": ask_walls[:5],
            "ladder_bids": ladder_bids,
            "ladder_asks": ladder_asks,
        }

    def _generate_fallback_orderbook(self) -> Dict[str, Any]:
        """Fallback mock data for orderbook."""
        mid = 64500.0
        return {
            "symbol": self.symbol,
            "mid_price": mid,
            "best_bid": mid - 0.5,
            "best_ask": mid + 0.5,
            "spread_usd": 1.0,
            "spread_bps": 0.155,
            "total_bid_btc": 240.5,
            "total_ask_btc": 215.2,
            "total_bid_usd": 15512250.0,
            "total_ask_usd": 13880400.0,
            "orderbook_imbalance": 0.055,
            "orderbook_imbalance_1pct": 0.082,
            "imbalance_interpretation": "BALANCED",
            "bid_walls": [
                {"price": 64000.0, "quantity_btc": 45.2, "value_usd": 2892800.0, "distance_pct": -0.78},
                {"price": 63500.0, "quantity_btc": 62.8, "value_usd": 3987800.0, "distance_pct": -1.55}
            ],
            "ask_walls": [
                {"price": 65000.0, "quantity_btc": 51.4, "value_usd": 3341000.0, "distance_pct": 0.78},
                {"price": 65500.0, "quantity_btc": 70.1, "value_usd": 4591550.0, "distance_pct": 1.55}
            ],
            "ladder_bids": [{"price": mid - i*5, "qty": 10.0 + i*2, "total": (mid-i*5)*(10+i*2)} for i in range(1, 9)],
            "ladder_asks": [{"price": mid + i*5, "qty": 9.5 + i*2, "total": (mid+i*5)*(9.5+i*2)} for i in range(1, 9)],
            "timestamp": int(time.time() * 1000),
            "status": "SIMULATED_FALLBACK"
        }
