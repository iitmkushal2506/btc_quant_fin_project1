"""
Macroeconomics & Cross-Asset Collector: DXY, S&P 500, Nasdaq, Gold, 10Y Treasury Yield
"""

import time
import logging
import asyncio
from typing import Dict, Any
import pandas as pd
import numpy as np
try:
    import yfinance as yf
except ImportError:
    yf = None

from app.config import MACRO_TICKERS, CACHE_TTL

logger = logging.getLogger(__name__)

class MacroCollector:
    def __init__(self):
        self._cache: Dict[str, Any] = {"data": None, "timestamp": 0}

    async def get_macro_data(self) -> Dict[str, Any]:
        """Fetch macro asset prices, returns, and cross-asset correlations."""
        now = time.time()
        if self._cache["data"] and (now - self._cache["timestamp"]) < CACHE_TTL["macro"]:
            return self._cache["data"]

        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(None, self._fetch_macro_sync)
            self._cache = {"data": data, "timestamp": now}
            return data
        except Exception as e:
            logger.warning(f"Error fetching macro data from yfinance: {e}. Generating fallback.")
            return self._generate_fallback_macro()

    def _fetch_macro_sync(self) -> Dict[str, Any]:
        if yf is None:
            return self._generate_fallback_macro()
        tickers = list(MACRO_TICKERS.values())
        # Add BTC-USD to calculate correlations
        all_tickers = tickers + ["BTC-USD"]
        
        # Download 1mo history
        df = yf.download(all_tickers, period="1mo", interval="1d", progress=False, auto_adjust=True)
        if df.empty or "Close" not in df:
            return self._generate_fallback_macro()

        close_df = df["Close"].copy().ffill().bfill()

        # Extract current prices and 1d percentage changes
        assets_data = {}
        for name, ticker in MACRO_TICKERS.items():
            if ticker in close_df.columns:
                series = close_df[ticker].dropna()
                if len(series) >= 2:
                    current = float(series.iloc[-1])
                    prev = float(series.iloc[-2])
                    chg_pct = ((current - prev) / prev) * 100
                    assets_data[name] = {
                        "ticker": ticker,
                        "price": round(current, 2),
                        "change_pct_24h": round(chg_pct, 2),
                        "trend_7d": "UP" if current > series.iloc[-min(7, len(series))] else "DOWN"
                    }

        # Calculate Rolling 30d Correlations with BTC
        correlations = {}
        if "BTC-USD" in close_df.columns:
            btc_returns = close_df["BTC-USD"].pct_change().dropna()
            for name, ticker in MACRO_TICKERS.items():
                if ticker in close_df.columns:
                    asset_returns = close_df[ticker].pct_change().dropna()
                    combined = pd.concat([btc_returns, asset_returns], axis=1).dropna()
                    if len(combined) >= 5:
                        corr = float(combined.iloc[:, 0].corr(combined.iloc[:, 1]))
                        correlations[f"BTC_{name}_corr"] = round(corr, 3)
                    else:
                        correlations[f"BTC_{name}_corr"] = 0.0

        # Determine Macro Regime
        dxy_chg = assets_data.get("DXY", {}).get("change_pct_24h", 0.0)
        spx_chg = assets_data.get("SP500", {}).get("change_pct_24h", 0.0)
        us10y_val = assets_data.get("US10Y", {}).get("price", 4.0)

        if spx_chg > 0.3 and dxy_chg <= 0.1:
            macro_regime = "RISK_ON_EXPANSION"
            macro_bias = "BULLISH_CRYPTO"
            macro_score = 65.0
        elif spx_chg < -0.5 or dxy_chg > 0.4:
            macro_regime = "RISK_OFF_CONTRACTION"
            macro_bias = "BEARISH_CRYPTO"
            macro_score = -60.0
        elif dxy_chg < -0.3:
            macro_regime = "DOLLAR_WEAKNESS_TAILWIND"
            macro_bias = "BULLISH_CRYPTO"
            macro_score = 55.0
        else:
            macro_regime = "NEUTRAL_CONSOLIDATION"
            macro_bias = "NEUTRAL"
            macro_score = 5.0

        return {
            "assets": assets_data,
            "correlations": correlations,
            "macro_regime": macro_regime,
            "macro_bias": macro_bias,
            "macro_score": macro_score,
            "status": "LIVE",
            "timestamp": int(time.time() * 1000)
        }

    def _generate_fallback_macro(self) -> Dict[str, Any]:
        """Fallback mock for macro cross-asset data."""
        return {
            "assets": {
                "DXY": {"ticker": "DX-Y.NYB", "price": 101.45, "change_pct_24h": -0.22, "trend_7d": "DOWN"},
                "SP500": {"ticker": "^GSPC", "price": 5740.20, "change_pct_24h": 0.45, "trend_7d": "UP"},
                "NASDAQ": {"ticker": "^IXIC", "price": 18120.50, "change_pct_24h": 0.62, "trend_7d": "UP"},
                "GOLD": {"ticker": "GC=F", "price": 2655.80, "change_pct_24h": 0.35, "trend_7d": "UP"},
                "US10Y": {"ticker": "^TNX", "price": 3.78, "change_pct_24h": -0.85, "trend_7d": "DOWN"},
                "ETH": {"ticker": "ETH-USD", "price": 2640.50, "change_pct_24h": 2.15, "trend_7d": "UP"}
            },
            "correlations": {
                "BTC_DXY_corr": -0.62,
                "BTC_SP500_corr": 0.68,
                "BTC_NASDAQ_corr": 0.74,
                "BTC_GOLD_corr": 0.31,
                "BTC_US10Y_corr": -0.45,
                "BTC_ETH_corr": 0.91
            },
            "macro_regime": "RISK_ON_EXPANSION",
            "macro_bias": "BULLISH_CRYPTO",
            "macro_score": 60.0,
            "status": "SIMULATED_FALLBACK",
            "timestamp": int(time.time() * 1000)
        }
