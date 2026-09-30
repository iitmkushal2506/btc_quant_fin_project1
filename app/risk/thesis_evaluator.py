"""
Thesis Evaluator & Thesis Invalidation Monitor:
Formulates institutional invalidation criteria, macro catalysts, and black swan risk factors
"""

from typing import Dict, Any, List

class ThesisEvaluator:
    @staticmethod
    def evaluate_thesis(
        direction: str,
        current_price: float,
        structure_data: Dict[str, Any],
        derivatives_data: Dict[str, Any],
        macro_data: Dict[str, Any],
        news_data: Dict[str, Any],
        regime_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Formulate explicit trade thesis, invalidation rules, and key market risk factors."""
        if direction == "NO_TRADE" or direction == "WAIT":
            return {
                "invalidation_condition": "System is currently in capital preservation / monitoring mode. No active trade thesis to invalidate.",
                "major_risks": [
                    "Market structure lacks clean institutional order block alignment.",
                    "Derivatives funding rate or cross-asset macro signals are conflicting.",
                    "High probability of chop / liquidity sweeps within current trading range."
                ],
                "capital_preservation_priority": "MAXIMUM",
                "actionable_triggers_to_watch": [
                    f"Watch for 4h candle close outside the range boundary (${structure_data.get('nearest_support', current_price*0.97):,.0f} - ${structure_data.get('nearest_resistance', current_price*1.03):,.0f}).",
                    "Wait for derivatives funding rate to normalize towards baseline (0.01% / 8h).",
                    "Monitor for confirmed Break of Structure (BOS) on the 1h timeframe."
                ]
            }

        major_risks = []
        invalidation_condition = ""
        actionable_triggers = []

        # Invalidation Conditions
        support_lvl = structure_data.get("nearest_support", current_price * 0.98)
        resist_lvl = structure_data.get("nearest_resistance", current_price * 1.02)

        if direction == "LONG":
            invalidation_condition = (
                f"A 4-hour candle close below ${support_lvl:,.0f} or an aggressive volume breakdown below the swing low "
                f"immediately invalidates the bullish market structure and converts bias to NEUTRAL/BEARISH."
            )
            actionable_triggers.append(f"Wait for limit fill within entry zone around ${current_price:,.0f}.")
            actionable_triggers.append(f"Scale out 50% at TP1 (${current_price * 1.02:,.0f}) and immediately move hard stop to Breakeven.")

            # Assess potential risks to LONG
            funding = derivatives_data.get("current_funding_rate", 0.0001)
            if funding > 0.00025:
                major_risks.append("Elevated futures funding rate indicates crowded retail long positioning, creating vulnerability to a liquidation flush.")

            ls_ratio = derivatives_data.get("long_short_ratio", 1.0)
            if ls_ratio > 1.8:
                major_risks.append("Retail Long/Short account ratio is heavily skewed bullish (> 1.8), increasing odds of a contrarian trap.")

            dxy_chg = macro_data.get("assets", {}).get("DXY", {}).get("change_pct_24h", 0.0)
            if dxy_chg > 0.2:
                major_risks.append("US Dollar Index (DXY) is showing intraday strength, which historically exerts downward pressure on BTC.")

        elif direction == "SHORT":
            invalidation_condition = (
                f"A 4-hour candle close above ${resist_lvl:,.0f} or an aggressive impulsive breakout above previous swing high "
                f"immediately invalidates the bearish market structure and invalidates the short thesis."
            )
            actionable_triggers.append(f"Wait for limit fill within entry zone around ${current_price:,.0f}.")
            actionable_triggers.append(f"Scale out 50% at TP1 (${current_price * 0.98:,.0f}) and move stop to Breakeven.")

            # Assess potential risks to SHORT
            funding = derivatives_data.get("current_funding_rate", 0.0001)
            if funding < -0.0001:
                major_risks.append("Negative funding rate indicates crowded short sellers; vulnerable to an explosive short squeeze cascade.")

            if macro_data.get("macro_regime") == "RISK_ON_EXPANSION":
                major_risks.append("Broader equity markets (S&P 500, Nasdaq) are rallying strongly in Risk-On mode, creating upside drag on crypto.")

        # Common market risks
        if regime_data.get("regime") == "HIGH_VOLATILITY_EXPANSION":
            major_risks.append("Market is currently exhibiting High Volatility Expansion; wider spread and slippage expected.")

        news_uncertainty = news_data.get("summary", {}).get("uncertainty_level", "LOW")
        if news_uncertainty == "HIGH":
            major_risks.append("Breaking global news sentiment reflects elevated speculation and policy uncertainty.")

        if not major_risks:
            major_risks.append("Standard market execution risk; ensure strict hard stop loss enforcement without emotional intervention.")

        return {
            "invalidation_condition": invalidation_condition,
            "major_risks": major_risks,
            "capital_preservation_priority": "HIGH",
            "actionable_triggers_to_watch": actionable_triggers
        }
