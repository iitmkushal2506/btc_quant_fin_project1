"""
Volume & Volatility Quantitative Engine:
OBV, CMF, Parkinson Volatility, Garman-Klass Volatility, and Squeeze Detection
"""

from typing import Dict, Any
import pandas as pd
import numpy as np

class VolumeVolatilityAnalyzer:
    @staticmethod
    def analyze(df: pd.DataFrame) -> Dict[str, Any]:
        """Compute volume flow and statistical volatility metrics."""
        if df.empty or len(df) < 25:
            return {
                "score": 0.0,
                "obv_trend": "NEUTRAL",
                "cmf": 0.0,
                "parkinson_volatility": 0.0,
                "garman_klass_volatility": 0.0,
                "squeeze_state": "NO_SQUEEZE",
                "volume_ratio_20": 1.0
            }

        df = df.copy()
        close = df["close"]
        high = df["high"]
        low = df["low"]
        open_p = df["open"]
        vol = df["volume"]

        # 1. On-Balance Volume (OBV) & Trend
        obv = np.where(close > close.shift(1), vol, np.where(close < close.shift(1), -vol, 0)).cumsum()
        df["obv"] = obv
        df["obv_ema"] = df["obv"].ewm(span=20, adjust=False).mean()
        obv_trend = "BULLISH_EXPANSION" if df["obv"].iloc[-1] > df["obv_ema"].iloc[-1] else "BEARISH_CONTRACTION"

        # 2. Chaikin Money Flow (CMF 20)
        mf_multiplier = ((close - low) - (high - close)) / (high - low).replace(0, 1e-9)
        mf_volume = mf_multiplier * vol
        cmf_20 = mf_volume.rolling(window=20).sum() / vol.rolling(window=20).sum().replace(0, 1e-9)
        current_cmf = float(cmf_20.iloc[-1])

        # 3. Parkinson Volatility (High-Low estimator - much more efficient than close-to-close)
        # Parkinson = sqrt( 1 / (4 * ln(2) * N) * sum( (ln(H_i / L_i))^2 ) )
        hl_ratio = np.log(high / low.replace(0, 1e-9))
        parkinson = np.sqrt((1.0 / (4.0 * np.log(2))) * (hl_ratio**2).rolling(window=20).mean()) * np.sqrt(365 * 24) * 100
        current_parkinson = float(parkinson.iloc[-1]) if not np.isnan(parkinson.iloc[-1]) else 45.0

        # 4. Garman-Klass Volatility (combines Open, High, Low, Close)
        gk = 0.5 * (np.log(high / low.replace(0, 1e-9)))**2 - (2.0 * np.log(2) - 1.0) * (np.log(close / open_p.replace(0, 1e-9)))**2
        gk_vol = np.sqrt(gk.rolling(window=20).mean()) * np.sqrt(365 * 24) * 100
        current_gk = float(gk_vol.iloc[-1]) if not np.isnan(gk_vol.iloc[-1]) else 48.0

        # 5. Volatility Squeeze Detection (Bollinger Bands vs Keltner Channels)
        # 20 SMA & 20 ATR
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        bb_upper = sma20 + 2.0 * std20
        bb_lower = sma20 - 2.0 * std20

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr20 = tr.rolling(window=20).mean()
        kc_upper = sma20 + 1.5 * atr20
        kc_lower = sma20 - 1.5 * atr20

        # Squeeze is ON when BB is completely inside KC (ultra low volatility before explosion)
        is_squeeze = (bb_lower.iloc[-1] > kc_lower.iloc[-1]) and (bb_upper.iloc[-1] < kc_upper.iloc[-1])
        was_squeeze = (bb_lower.iloc[-2] > kc_lower.iloc[-2]) and (bb_upper.iloc[-2] < kc_upper.iloc[-2])

        if is_squeeze:
            squeeze_state = "SQUEEZE_ACTIVE_EXPANSION_IMMINENT"
        elif was_squeeze and not is_squeeze:
            squeeze_state = "SQUEEZE_FIRED_BREAKOUT"
        else:
            squeeze_state = "NO_SQUEEZE_NORMAL_VOL"

        # 6. Volume Ratio (Current bar vs 20-period average)
        vol_sma20 = vol.rolling(window=20).mean()
        vol_ratio = float(vol.iloc[-1] / vol_sma20.iloc[-1]) if vol_sma20.iloc[-1] > 0 else 1.0

        # 7. Volume & Volatility Confluence Score (-100 to +100)
        score = 0.0
        if current_cmf > 0.10:
            score += 35.0
        elif current_cmf > 0.02:
            score += 18.0
        elif current_cmf < -0.10:
            score -= 35.0
        elif current_cmf < -0.02:
            score -= 18.0

        if obv_trend == "BULLISH_EXPANSION":
            score += 25.0
        else:
            score -= 25.0

        if vol_ratio > 1.8 and close.iloc[-1] > open_p.iloc[-1]:
            score += 20.0 # Heavy buying volume expansion
        elif vol_ratio > 1.8 and close.iloc[-1] < open_p.iloc[-1]:
            score -= 20.0 # Heavy selling volume dump

        score = max(-100.0, min(100.0, score))

        return {
            "score": round(score, 1),
            "obv_trend": obv_trend,
            "cmf": round(current_cmf, 3),
            "cmf_signal": "STRONG_ACCUMULATION" if current_cmf > 0.10 else ("STRONG_DISTRIBUTION" if current_cmf < -0.10 else "NEUTRAL_FLOW"),
            "parkinson_volatility_ann_pct": round(current_parkinson, 2),
            "garman_klass_volatility_ann_pct": round(current_gk, 2),
            "squeeze_state": squeeze_state,
            "volume_ratio_20": round(vol_ratio, 2),
            "volatility_regime": "HIGH_EXPANSION" if current_parkinson > 65 else ("LOW_COMPRESSION" if current_parkinson < 35 else "MODERATE")
        }
