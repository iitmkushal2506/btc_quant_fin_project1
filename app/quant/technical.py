"""
Quantitative Technical Analysis: Indicators, Multi-Timeframe Signals, Divergences & Patterns
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

class TechnicalAnalyzer:
    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators on OHLCV DataFrame."""
        if df.empty or len(df) < 20:
            return df

        df = df.copy()

        # 1. Exponential Moving Averages (EMA)
        for period in [9, 20, 50, 100, 200]:
            df[f"ema_{period}"] = df["close"].ewm(span=period, adjust=False).mean()

        # 2. Relative Strength Index (RSI 14)
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss.replace(0, 1e-9))
        df["rsi_14"] = 100 - (100 / (1 + rs))

        # 3. MACD (12, 26, 9)
        ema_12 = df["close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd_line"] = ema_12 - ema_26
        df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd_line"] - df["macd_signal"]

        # 4. Bollinger Bands (20, 2.0)
        df["bb_middle"] = df["close"].rolling(window=20).mean()
        bb_std = df["close"].rolling(window=20).std()
        df["bb_upper"] = df["bb_middle"] + 2.0 * bb_std
        df["bb_lower"] = df["bb_middle"] - 2.0 * bb_std
        df["bb_bandwidth"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
        df["bb_pct_b"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"]).replace(0, 1e-9)

        # 5. Average True Range (ATR 14)
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift(1)).abs()
        tr3 = (df["low"] - df["close"].shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr_14"] = tr.rolling(window=14).mean()
        df["atr_pct"] = (df["atr_14"] / df["close"]) * 100

        # 6. Volume-Weighted Average Price (VWAP)
        typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
        df["cum_vol_price"] = (typical_price * df["volume"]).cumsum()
        df["cum_vol"] = df["volume"].cumsum()
        df["vwap"] = df["cum_vol_price"] / df["cum_vol"].replace(0, 1e-9)

        # 7. Supertrend (Period 10, Multiplier 3.0)
        df = TechnicalAnalyzer._calculate_supertrend(df, period=10, multiplier=3.0)

        # 8. Candlestick Patterns
        df = TechnicalAnalyzer._detect_candlestick_patterns(df)

        return df

    @staticmethod
    def _calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        high = df["high"]
        low = df["low"]
        close = df["close"]
        
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        hl2 = (high + low) / 2
        basic_upper = hl2 + (multiplier * atr)
        basic_lower = hl2 - (multiplier * atr)

        final_upper = pd.Series(0.0, index=df.index)
        final_lower = pd.Series(0.0, index=df.index)
        supertrend = pd.Series(0.0, index=df.index)
        direction = pd.Series(1, index=df.index)

        for i in range(1, len(df)):
            if basic_upper.iloc[i] < final_upper.iloc[i-1] or close.iloc[i-1] > final_upper.iloc[i-1]:
                final_upper.iloc[i] = basic_upper.iloc[i]
            else:
                final_upper.iloc[i] = final_upper.iloc[i-1]

            if basic_lower.iloc[i] > final_lower.iloc[i-1] or close.iloc[i-1] < final_lower.iloc[i-1]:
                final_lower.iloc[i] = basic_lower.iloc[i]
            else:
                final_lower.iloc[i] = final_lower.iloc[i-1]

            if close.iloc[i] > final_upper.iloc[i-1]:
                direction.iloc[i] = 1
            elif close.iloc[i] < final_lower.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1]

            supertrend.iloc[i] = final_lower.iloc[i] if direction.iloc[i] == 1 else final_upper.iloc[i]

        df["supertrend"] = supertrend
        df["supertrend_dir"] = direction
        return df

    @staticmethod
    def _detect_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
        df["pattern"] = "NONE"
        body = (df["close"] - df["open"]).abs()
        candle_range = (df["high"] - df["low"]).replace(0, 1e-9)
        upper_wick = df["high"] - df[["open", "close"]].max(axis=1)
        lower_wick = df[["open", "close"]].min(axis=1) - df["low"]

        # Bullish Pinbar / Hammer
        bull_pin = (lower_wick >= 2.0 * body) & (upper_wick <= 0.25 * body) & (df["close"] > df["open"])
        # Bearish Pinbar / Shooting Star
        bear_pin = (upper_wick >= 2.0 * body) & (lower_wick <= 0.25 * body) & (df["close"] < df["open"])
        # Bullish Engulfing
        bull_engulf = (df["close"] > df["open"].shift(1)) & (df["open"] < df["close"].shift(1)) & (df["close"].shift(1) < df["open"].shift(1))
        # Bearish Engulfing
        bear_engulf = (df["close"] < df["open"].shift(1)) & (df["open"] > df["close"].shift(1)) & (df["close"].shift(1) > df["open"].shift(1))

        df.loc[bull_pin, "pattern"] = "BULLISH_PINBAR"
        df.loc[bear_pin, "pattern"] = "BEARISH_PINBAR"
        df.loc[bull_engulf, "pattern"] = "BULLISH_ENGULFING"
        df.loc[bear_engulf, "pattern"] = "BEARISH_ENGULFING"
        return df

    @classmethod
    def evaluate_signals(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate quantitative technical score (-100 to +100) and rationale."""
        if df.empty or len(df) < 50:
            return {"score": 0.0, "signals": [], "trend": "NEUTRAL"}

        last = df.iloc[-1]
        prev = df.iloc[-2]
        close = last["close"]

        score = 0.0
        signals = []

        # 1. EMA Alignment & Trend
        ema20 = last.get("ema_20", close)
        ema50 = last.get("ema_50", close)
        ema200 = last.get("ema_200", close)

        if close > ema20 > ema50 > ema200:
            score += 25.0
            signals.append({"name": "EMA Bullish Stack", "type": "BULLISH", "weight": "+25"})
        elif close < ema20 < ema50 < ema200:
            score -= 25.0
            signals.append({"name": "EMA Bearish Stack", "type": "BEARISH", "weight": "-25"})
        elif close > ema200:
            score += 10.0
            signals.append({"name": "Above 200 EMA (Macro Bullish)", "type": "BULLISH", "weight": "+10"})
        elif close < ema200:
            score -= 10.0
            signals.append({"name": "Below 200 EMA (Macro Bearish)", "type": "BEARISH", "weight": "-10"})

        # 2. RSI Condition & Divergence
        rsi = last.get("rsi_14", 50.0)
        if 40 <= rsi <= 60:
            signals.append({"name": f"RSI Neutral ({round(rsi, 1)})", "type": "NEUTRAL", "weight": "0"})
        elif rsi > 70:
            score -= 10.0 # Overbought caution
            signals.append({"name": f"RSI Overbought ({round(rsi, 1)})", "type": "BEARISH_CAUTION", "weight": "-10"})
        elif rsi < 30:
            score += 15.0 # Oversold bounce potential
            signals.append({"name": f"RSI Oversold ({round(rsi, 1)})", "type": "BULLISH_OPPORTUNITY", "weight": "+15"})
        elif 60 < rsi <= 70:
            score += 12.0 # Bullish momentum
            signals.append({"name": f"RSI Bullish Momentum ({round(rsi, 1)})", "type": "BULLISH", "weight": "+12"})
        elif 30 <= rsi < 40:
            score -= 12.0 # Bearish momentum
            signals.append({"name": f"RSI Bearish Momentum ({round(rsi, 1)})", "type": "BEARISH", "weight": "-12"})

        # 3. MACD Momentum
        macd_hist = last.get("macd_hist", 0.0)
        prev_hist = prev.get("macd_hist", 0.0)
        if macd_hist > 0 and macd_hist > prev_hist:
            score += 15.0
            signals.append({"name": "MACD Histogram Expanding Bullish", "type": "BULLISH", "weight": "+15"})
        elif macd_hist > 0 and macd_hist <= prev_hist:
            score += 5.0
            signals.append({"name": "MACD Bullish Weakening", "type": "NEUTRAL_BULLISH", "weight": "+5"})
        elif macd_hist < 0 and macd_hist < prev_hist:
            score -= 15.0
            signals.append({"name": "MACD Histogram Expanding Bearish", "type": "BEARISH", "weight": "-15"})
        elif macd_hist < 0 and macd_hist >= prev_hist:
            score -= 5.0
            signals.append({"name": "MACD Bearish Weakening", "type": "NEUTRAL_BEARISH", "weight": "-5"})

        # 4. Supertrend
        st_dir = last.get("supertrend_dir", 1)
        if st_dir == 1:
            score += 15.0
            signals.append({"name": "Supertrend Bullish Confirmation", "type": "BULLISH", "weight": "+15"})
        else:
            score -= 15.0
            signals.append({"name": "Supertrend Bearish Confirmation", "type": "BEARISH", "weight": "-15"})

        # 5. VWAP Relationship
        vwap = last.get("vwap", close)
        if close > vwap * 1.002:
            score += 10.0
            signals.append({"name": "Trading Above VWAP", "type": "BULLISH", "weight": "+10"})
        elif close < vwap * 0.998:
            score -= 10.0
            signals.append({"name": "Trading Below VWAP", "type": "BEARISH", "weight": "-10"})

        # 6. Candlestick Pattern
        pattern = last.get("pattern", "NONE")
        if pattern == "BULLISH_PINBAR" or pattern == "BULLISH_ENGULFING":
            score += 15.0
            signals.append({"name": f"Candlestick: {pattern.replace('_', ' ')}", "type": "BULLISH", "weight": "+15"})
        elif pattern == "BEARISH_PINBAR" or pattern == "BEARISH_ENGULFING":
            score -= 15.0
            signals.append({"name": f"Candlestick: {pattern.replace('_', ' ')}", "type": "BEARISH", "weight": "-15"})

        final_score = max(-100.0, min(100.0, score))
        trend = "BULLISH" if final_score > 25 else ("BEARISH" if final_score < -25 else "NEUTRAL_RANGING")

        return {
            "score": round(final_score, 1),
            "trend": trend,
            "signals": signals,
            "rsi": round(rsi, 2),
            "macd_hist": round(macd_hist, 2),
            "close": round(close, 2),
            "ema_20": round(ema20, 2),
            "ema_50": round(ema50, 2),
            "ema_200": round(ema200, 2),
            "atr": round(last.get("atr_14", 500.0), 2),
            "bb_bandwidth": round(last.get("bb_bandwidth", 0.05), 4)
        }
