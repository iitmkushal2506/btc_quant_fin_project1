"""
Market Data Collector: Binance Spot & Multi-Timeframe Klines
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
import httpx
import pandas as pd
import numpy as np

from app.config import (
    BINANCE_SPOT_API,
    PRIMARY_SYMBOL,
    SUPPORTED_TIMEFRAMES,
    DEFAULT_TIMEFRAME,
    KLINE_LIMIT,
    CACHE_TTL
)

logger = logging.getLogger(__name__)

class MarketDataCollector:
    def __init__(self, symbol: str = PRIMARY_SYMBOL):
        self.symbol = symbol
        self._kline_cache: Dict[str, Dict[str, Any]] = {}
        self._ticker_cache: Dict[str, Any] = {"data": None, "timestamp": 0}
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def get_live_ticker(self) -> Dict[str, Any]:
        """Fetch current 24hr ticker data including price, change, volume, high, low."""
        now = time.time()
        if self._ticker_cache["data"] and (now - self._ticker_cache["timestamp"]) < CACHE_TTL["ticker"]:
            return self._ticker_cache["data"]

        url = f"{BINANCE_SPOT_API}/ticker/24hr"
        params = {"symbol": self.symbol}
        try:
            resp = await self.client.get(url, params=params)
            if resp.status_code == 200:
                raw = resp.json()
                ticker = {
                    "symbol": self.symbol,
                    "last_price": float(raw["lastPrice"]),
                    "price_change": float(raw["priceChange"]),
                    "price_change_percent": float(raw["priceChangePercent"]),
                    "high_24h": float(raw["highPrice"]),
                    "low_24h": float(raw["lowPrice"]),
                    "volume_btc_24h": float(raw["volume"]),
                    "volume_usdt_24h": float(raw["quoteVolume"]),
                    "bid_price": float(raw["bidPrice"]),
                    "ask_price": float(raw["askPrice"]),
                    "weighted_avg_price": float(raw["weightedAvgPrice"]),
                    "timestamp": int(raw["closeTime"]),
                    "status": "LIVE"
                }
                self._ticker_cache = {"data": ticker, "timestamp": now}
                return ticker
        except Exception as e:
            logger.warning(f"Error fetching 24hr ticker for {self.symbol}: {e}. Generating fallback.")

        # Fallback if live network fails
        return self._generate_fallback_ticker()

    async def get_klines(self, timeframe: str = DEFAULT_TIMEFRAME, limit: int = KLINE_LIMIT) -> pd.DataFrame:
        """
        Fetch OHLCV candlestick data for given timeframe.
        Supports multi-batch retrieval up to 7+ days (2016+ candles).
        Returns pandas DataFrame with datetime index and typed float columns.
        """
        now = time.time()
        cache_key = f"{timeframe}_{limit}"
        if cache_key in self._kline_cache:
            cache_entry = self._kline_cache[cache_key]
            if (now - cache_entry["timestamp"]) < CACHE_TTL["klines"]:
                return cache_entry["data"].copy()

        url = f"{BINANCE_SPOT_API}/klines"
        try:
            if limit <= 1000:
                params = {"symbol": self.symbol, "interval": timeframe, "limit": limit}
                resp = await self.client.get(url, params=params)
                if resp.status_code == 200:
                    raw_data = resp.json()
                    df = self._parse_kline_data(raw_data)
                    self._kline_cache[cache_key] = {"data": df, "timestamp": now}
                    return df.copy()
            else:
                # Multi-batch chunking to get 7 full days of history (e.g., 2016 candles for 5m)
                all_raw_data = []
                remaining = limit
                end_time = None

                while remaining > 0:
                    batch_size = min(1000, remaining)
                    params = {"symbol": self.symbol, "interval": timeframe, "limit": batch_size}
                    if end_time:
                        params["endTime"] = end_time

                    resp = await self.client.get(url, params=params)
                    if resp.status_code != 200:
                        break

                    batch = resp.json()
                    if not batch:
                        break

                    all_raw_data = batch + all_raw_data
                    remaining -= len(batch)
                    end_time = batch[0][0] - 1  # 1 ms before oldest candle in this batch

                    if len(batch) < batch_size:
                        break

                if all_raw_data:
                    df = self._parse_kline_data(all_raw_data)
                    self._kline_cache[cache_key] = {"data": df, "timestamp": now}
                    return df.copy()

        except Exception as e:
            logger.warning(f"Error fetching klines {timeframe} for {self.symbol}: {e}. Generating fallback.")

        fallback_df = self._generate_fallback_klines(timeframe, limit)
        return fallback_df

    async def get_multi_timeframe_klines(self, timeframes: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """Fetch klines across multiple timeframes concurrently."""
        tfs = timeframes or SUPPORTED_TIMEFRAMES
        tasks = [self.get_klines(tf) for tf in tfs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        mtf_dict = {}
        for tf, res in zip(tfs, results):
            if isinstance(res, pd.DataFrame) and not res.empty:
                mtf_dict[tf] = res
            else:
                mtf_dict[tf] = self._generate_fallback_klines(tf, KLINE_LIMIT)
        return mtf_dict

    def _parse_kline_data(self, raw_data: List[List[Any]]) -> pd.DataFrame:
        """Parse Binance raw kline array to clean DataFrame."""
        columns = [
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ]
        df = pd.DataFrame(raw_data, columns=columns)
        numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base", "taker_buy_quote"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
        df["timestamp"] = df["open_time"].astype(np.int64) // 10**6
        
        # Deduplicate and ensure strict chronological order
        df.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
        df.sort_values(by="timestamp", ascending=True, inplace=True)
        df.set_index("open_time", inplace=True)
        return df

    def _generate_fallback_ticker(self) -> Dict[str, Any]:
        """Generate a realistic fallback ticker when offline."""
        base_price = 64500.0
        return {
            "symbol": self.symbol,
            "last_price": base_price,
            "price_change": 1250.0,
            "price_change_percent": 1.97,
            "high_24h": 65200.0,
            "low_24h": 63100.0,
            "volume_btc_24h": 28540.5,
            "volume_usdt_24h": 1845000000.0,
            "bid_price": base_price - 0.5,
            "ask_price": base_price + 0.5,
            "weighted_avg_price": 64320.0,
            "timestamp": int(time.time() * 1000),
            "status": "SIMULATED_FALLBACK"
        }

    def _generate_fallback_klines(self, timeframe: str, limit: int) -> pd.DataFrame:
        """Synthesize realistic BTC price action data for testing/offline support."""
        now_ms = int(time.time() * 1000)
        tf_minutes = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}.get(timeframe, 60)
        interval_ms = tf_minutes * 60 * 1000

        np.random.seed(42)
        timestamps = [now_ms - (limit - i) * interval_ms for i in range(limit)]
        
        # Realistic random walk with slight upward drift
        returns = np.random.normal(0.0003, 0.006, limit)
        price = 60000.0 * np.exp(np.cumsum(returns))
        
        high = price * (1 + np.abs(np.random.normal(0.003, 0.002, limit)))
        low = price * (1 - np.abs(np.random.normal(0.003, 0.002, limit)))
        open_p = np.roll(price, 1)
        open_p[0] = price[0] * 0.998
        volume = np.random.uniform(500, 3500, limit)
        quote_vol = volume * price

        data = {
            "timestamp": timestamps,
            "open": open_p,
            "high": high,
            "low": low,
            "close": price,
            "volume": volume,
            "quote_volume": quote_vol,
            "trades": np.random.randint(1000, 15000, limit),
            "taker_buy_base": volume * np.random.uniform(0.45, 0.55, limit),
            "taker_buy_quote": quote_vol * np.random.uniform(0.45, 0.55, limit),
        }
        df = pd.DataFrame(data)
        df["open_time"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("open_time", inplace=True)
        return df
