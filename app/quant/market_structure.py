"""
Smart Money Concepts (SMC) & Market Structure Analyzer:
Swing Highs/Lows, BOS, CHoCH, Order Blocks, FVGs, and Liquidity Pools
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

class MarketStructureAnalyzer:
    @staticmethod
    def analyze_structure(df: pd.DataFrame) -> Dict[str, Any]:
        """Perform institutional market structure & SMC analysis on OHLCV klines."""
        if df.empty or len(df) < 30:
            return {
                "structure": "NEUTRAL",
                "structure_score": 0.0,
                "order_blocks": [],
                "fair_value_gaps": [],
                "swing_highs": [],
                "swing_lows": [],
                "bos_events": [],
                "choch_events": []
            }

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values
        opens = df["open"].values
        timestamps = df["timestamp"].values if "timestamp" in df else np.arange(len(df))
        n = len(df)

        # 1. Identify Fractal Swing Highs and Swing Lows (5-bar fractal window)
        swing_highs = []
        swing_lows = []

        for i in range(2, n - 2):
            # Swing High: Highest among 2 preceding and 2 succeeding bars
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append({"index": i, "price": round(float(highs[i]), 2), "timestamp": int(timestamps[i])})
            # Swing Low: Lowest among 2 preceding and 2 succeeding bars
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append({"index": i, "price": round(float(lows[i]), 2), "timestamp": int(timestamps[i])})

        # 2. Identify Break of Structure (BOS) and Change of Character (CHoCH)
        bos_events = []
        choch_events = []
        current_trend = "NEUTRAL"

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            last_sh = swing_highs[-1]["price"]
            prev_sh = swing_highs[-2]["price"]
            last_sl = swing_lows[-1]["price"]
            prev_sl = swing_lows[-2]["price"]
            current_price = closes[-1]

            # Bullish trend: Higher Highs (HH) & Higher Lows (HL)
            if last_sh > prev_sh and last_sl > prev_sl:
                current_trend = "BULLISH_STRUCTURE"
                if current_price > last_sh:
                    bos_events.append({"type": "BULLISH_BOS", "level": last_sh, "desc": "Price broke above previous Swing High"})
            # Bearish trend: Lower Highs (LH) & Lower Lows (LL)
            elif last_sh < prev_sh and last_sl < prev_sl:
                current_trend = "BEARISH_STRUCTURE"
                if current_price < last_sl:
                    bos_events.append({"type": "BEARISH_BOS", "level": last_sl, "desc": "Price broke below previous Swing Low"})
            # Potential CHoCH Reversals
            elif last_sh > prev_sh and current_price < last_sl:
                current_trend = "CHOCH_BEARISH_REVERSAL"
                choch_events.append({"type": "BEARISH_CHOCH", "level": last_sl, "desc": "Bullish trend broken by break below Swing Low"})
            elif last_sl < prev_sl and current_price > last_sh:
                current_trend = "CHOCH_BULLISH_REVERSAL"
                choch_events.append({"type": "BULLISH_CHOCH", "level": last_sh, "desc": "Bearish trend broken by break above Swing High"})
            else:
                current_trend = "RANGE_CONSOLIDATION"

        # 3. Detect Order Blocks (OB)
        # Bullish OB: The last down-close candle before a strong impulsive upward move
        # Bearish OB: The last up-close candle before a strong impulsive downward move
        order_blocks = []
        for i in range(max(0, n - 40), n - 2):
            # Bullish OB: red candle followed by strong 2-bar green expansion
            if closes[i] < opens[i] and (closes[i+1] > opens[i+1]) and (closes[i+2] > highs[i]):
                ob_high = float(highs[i])
                ob_low = float(lows[i])
                # Check if mitigated
                is_mitigated = any(lows[k] <= ob_high for k in range(i+1, n))
                order_blocks.append({
                    "type": "BULLISH_OB",
                    "top": round(ob_high, 2),
                    "bottom": round(ob_low, 2),
                    "mitigated": is_mitigated,
                    "bar_index": i,
                    "timestamp": int(timestamps[i])
                })

            # Bearish OB: green candle followed by strong 2-bar red drop
            elif closes[i] > opens[i] and (closes[i+1] < opens[i+1]) and (closes[i+2] < lows[i]):
                ob_high = float(highs[i])
                ob_low = float(lows[i])
                is_mitigated = any(highs[k] >= ob_low for k in range(i+1, n))
                order_blocks.append({
                    "type": "BEARISH_OB",
                    "top": round(ob_high, 2),
                    "bottom": round(ob_low, 2),
                    "mitigated": is_mitigated,
                    "bar_index": i,
                    "timestamp": int(timestamps[i])
                })

        # Keep latest unmitigated order blocks prioritized
        unmitigated_obs = [ob for ob in order_blocks if not ob["mitigated"]][-6:]

        # 4. Detect Fair Value Gaps (FVG / Imbalances)
        # Bullish FVG: Low of candle[i+2] > High of candle[i] (3-candle pattern)
        # Bearish FVG: High of candle[i+2] < Low of candle[i]
        fvgs = []
        for i in range(max(0, n - 30), n - 2):
            if lows[i+2] > highs[i]: # Bullish FVG
                gap_size = lows[i+2] - highs[i]
                if gap_size > (closes[i] * 0.001): # At least 0.1% gap
                    is_filled = any(lows[k] <= highs[i] for k in range(i+3, n))
                    fvgs.append({
                        "type": "BULLISH_FVG",
                        "top": round(float(lows[i+2]), 2),
                        "bottom": round(float(highs[i]), 2),
                        "gap_size": round(float(gap_size), 2),
                        "filled": is_filled,
                        "timestamp": int(timestamps[i+1])
                    })
            elif highs[i+2] < lows[i]: # Bearish FVG
                gap_size = lows[i] - highs[i+2]
                if gap_size > (closes[i] * 0.001):
                    is_filled = any(highs[k] >= lows[i] for k in range(i+3, n))
                    fvgs.append({
                        "type": "BEARISH_FVG",
                        "top": round(float(lows[i]), 2),
                        "bottom": round(float(highs[i+2]), 2),
                        "gap_size": round(float(gap_size), 2),
                        "filled": is_filled,
                        "timestamp": int(timestamps[i+1])
                    })

        active_fvgs = [f for f in fvgs if not f["filled"]][-5:]

        # 5. Structure Score Calculation
        structure_score = 0.0
        if current_trend == "BULLISH_STRUCTURE":
            structure_score += 45.0
        elif current_trend == "CHOCH_BULLISH_REVERSAL":
            structure_score += 65.0
        elif current_trend == "BEARISH_STRUCTURE":
            structure_score -= 45.0
        elif current_trend == "CHOCH_BEARISH_REVERSAL":
            structure_score -= 65.0

        if bos_events:
            for b in bos_events:
                if b["type"] == "BULLISH_BOS":
                    structure_score += 20.0
                elif b["type"] == "BEARISH_BOS":
                    structure_score -= 20.0

        # Nearby Order Block Support / Resistance alignment
        current_p = closes[-1]
        for ob in unmitigated_obs:
            if ob["type"] == "BULLISH_OB" and ob["bottom"] <= current_p <= ob["top"] * 1.01:
                structure_score += 15.0 # Tested bullish demand zone
            elif ob["type"] == "BEARISH_OB" and ob["bottom"] * 0.99 <= current_p <= ob["top"]:
                structure_score -= 15.0 # Tested bearish supply zone

        structure_score = max(-100.0, min(100.0, structure_score))

        return {
            "structure": current_trend,
            "structure_score": round(structure_score, 1),
            "order_blocks": unmitigated_obs,
            "fair_value_gaps": active_fvgs,
            "swing_highs": swing_highs[-4:],
            "swing_lows": swing_lows[-4:],
            "bos_events": bos_events[-2:],
            "choch_events": choch_events[-2:],
            "nearest_support": swing_lows[-1]["price"] if swing_lows else round(current_p * 0.97, 2),
            "nearest_resistance": swing_highs[-1]["price"] if swing_highs else round(current_p * 1.03, 2),
        }
