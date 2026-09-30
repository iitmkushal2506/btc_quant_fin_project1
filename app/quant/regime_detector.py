"""
Market Regime Detector:
Statistical & Clustering Regime Classifier (Trending Bull, Trending Bear, Ranging, Squeeze, Vol Shock)
"""

from typing import Dict, Any
import numpy as np
import pandas as pd
from app.quant.statistical_analysis import StatisticalAnalyzer

class MarketRegimeDetector:
    @staticmethod
    def detect_regime(df: pd.DataFrame) -> Dict[str, Any]:
        """Detect current statistical market regime using volatility, momentum, and Hurst exponent."""
        if df.empty or len(df) < 35:
            return {
                "regime": "NEUTRAL_CONSOLIDATION",
                "regime_name": "Neutral Consolidation",
                "description": "Insufficient data to establish high-conviction regime.",
                "hurst_exponent": 0.50,
                "trend_strength_adx": 20.0,
                "favorable_strategy": "WAIT",
                "risk_multiplier": 1.0
            }

        close = df["close"].values
        high = df["high"].values
        low = df["low"].values

        # 1. Hurst Exponent
        hurst = StatisticalAnalyzer.calculate_hurst_exponent(close, max_lags=24)

        # 2. ADX (Average Directional Index) Calculation
        adx_val = MarketRegimeDetector._calculate_adx(high, low, close, period=14)

        # 3. 20-period Momentum and Volatility
        returns_20 = (close[-1] - close[-20]) / close[-20]
        returns_5 = (close[-1] - close[-5]) / close[-5]
        volatility_20 = np.std(np.diff(np.log(close[-20:]))) * np.sqrt(365 * 24) * 100

        # 4. Volatility compression / expansion
        atr_14 = df["atr_14"].iloc[-1] if "atr_14" in df else (high[-1] - low[-1])
        mean_atr_50 = df["atr_14"].iloc[-50:].mean() if "atr_14" in df and len(df) >= 50 else atr_14

        # Classification Logic
        if adx_val >= 28.0 and returns_20 > 0.03 and close[-1] > df["ema_50"].iloc[-1] if "ema_50" in df else close[-1] > close[-20]:
            regime = "TRENDING_BULL"
            regime_name = "Trending Bull Market"
            description = "Persistent upward momentum with strong directional trend strength. Trend-following pullbacks favored."
            favorable_strategy = "LONG_PULLBACKS_TREND_FOLLOWING"
            risk_multiplier = 1.0
        elif adx_val >= 28.0 and returns_20 < -0.03 and close[-1] < df["ema_50"].iloc[-1] if "ema_50" in df else close[-1] < close[-20]:
            regime = "TRENDING_BEAR"
            regime_name = "Trending Bear Market"
            description = "Persistent downward momentum with aggressive selling pressure. Short rallies & breakdown continuations favored."
            favorable_strategy = "SHORT_RALLIES_BREAKDOWN"
            risk_multiplier = 0.85
        elif volatility_20 > 75.0 or (atr_14 > mean_atr_50 * 2.2):
            regime = "HIGH_VOLATILITY_EXPANSION"
            regime_name = "High-Volatility Volatility Shock"
            description = "Erratic price expansion with large liquidation spikes. High slippage risk; reduced position sizing advised."
            favorable_strategy = "WAIT_FOR_SETTLE_OR_DEFENSIVE"
            risk_multiplier = 0.50
        elif atr_14 < mean_atr_50 * 0.65 or hurst < 0.40:
            regime = "LOW_VOLATILITY_COMPRESSION"
            regime_name = "Low-Volatility Squeeze"
            description = "Energy coil phase. Narrow trading range with volatility contraction preceding an explosive breakout."
            favorable_strategy = "PREPARE_BREAKOUT_STRADDLE"
            risk_multiplier = 0.75
        else:
            regime = "RANGING_MEAN_REVERTING"
            regime_name = "Ranging / Mean Reversion"
            description = "Market lacks strong directional trend. Price is bouncing within structural support & resistance bounds."
            favorable_strategy = "FADE_RANGE_BOUNDARIES_OR_WAIT"
            risk_multiplier = 0.70

        return {
            "regime": regime,
            "regime_name": regime_name,
            "description": description,
            "hurst_exponent": round(hurst, 3),
            "trend_strength_adx": round(adx_val, 1),
            "volatility_20_ann_pct": round(volatility_20, 1),
            "returns_20_pct": round(returns_20 * 100, 2),
            "favorable_strategy": favorable_strategy,
            "risk_multiplier": risk_multiplier
        }

    @staticmethod
    def _calculate_adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Calculate Average Directional Index (ADX)."""
        if len(close) < period * 2:
            return 22.0

        tr_list = []
        plus_dm_list = []
        minus_dm_list = []

        for i in range(1, len(close)):
            h_diff = high[i] - high[i-1]
            l_diff = low[i-1] - low[i]

            plus_dm = h_diff if (h_diff > l_diff and h_diff > 0) else 0.0
            minus_dm = l_diff if (l_diff > h_diff and l_diff > 0) else 0.0

            tr = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
            tr_list.append(tr)
            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)

        tr_s = pd.Series(tr_list).ewm(alpha=1/period, adjust=False).mean()
        plus_di = 100 * (pd.Series(plus_dm_list).ewm(alpha=1/period, adjust=False).mean() / tr_s.replace(0, 1e-9))
        minus_di = 100 * (pd.Series(minus_dm_list).ewm(alpha=1/period, adjust=False).mean() / tr_s.replace(0, 1e-9))

        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9))
        adx = dx.ewm(alpha=1/period, adjust=False).mean()

        return float(adx.iloc[-1]) if not np.isnan(adx.iloc[-1]) else 20.0
