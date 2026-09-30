"""
Master Institutional Decision Engine:
Synthesizes 7-Pillar Confluence, Risk/Reward validation, and Market Regime into:
🟢 TRADE SETUP VALID | 🟡 WAIT — SETUP DEVELOPING | 🔴 NO TRADE
"""

from typing import Dict, Any, List
from app.config import DECISION_THRESHOLDS

class DecisionMaker:
    @staticmethod
    def formulate_decision(
        confluence_payload: Dict[str, Any],
        risk_payload: Dict[str, Any],
        thesis_payload: Dict[str, Any],
        regime_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate authoritative quantitative trading decision and evidence report."""
        score = confluence_payload.get("master_confluence_score", 0.0)
        conflict_penalty = confluence_payload.get("conflict_penalty", 0.0)
        conviction_pct = confluence_payload.get("conviction_pct", 0.0)
        is_rr_valid = risk_payload.get("is_rr_valid", False)
        rr_ratio = risk_payload.get("risk_reward_ratio", 0.0)
        regime = regime_data.get("regime", "RANGING_MEAN_REVERTING")

        decision_state = "NO_TRADE"
        badge_text = "🔴 NO TRADE"
        badge_class = "no-trade"
        summary_reason = ""
        action_directive = ""

        # High-Conviction Long Conditions
        if score >= DECISION_THRESHOLDS["VALID_LONG_SCORE"] and conflict_penalty < 20.0 and is_rr_valid and regime != "HIGH_VOLATILITY_EXPANSION":
            decision_state = "TRADE_SETUP_VALID_LONG"
            badge_text = "🟢 TRADE SETUP VALID (LONG)"
            badge_class = "trade-valid-long"
            summary_reason = (
                f"Multi-dimensional confluence is strongly aligned bullish (+{score:.1f} score). "
                f"Technical structure, order flow imbalance, and quantitative regime confirm institutional demand "
                f"with an asymmetric Risk/Reward of {rr_ratio:.2f}R."
            )
            action_directive = "Execute limit order within specified entry zone. Set hard stop loss immediately."

        # High-Conviction Short Conditions
        elif score <= DECISION_THRESHOLDS["VALID_SHORT_SCORE"] and conflict_penalty < 20.0 and is_rr_valid and regime != "HIGH_VOLATILITY_EXPANSION":
            decision_state = "TRADE_SETUP_VALID_SHORT"
            badge_text = "🟢 TRADE SETUP VALID (SHORT)"
            badge_class = "trade-valid-short"
            summary_reason = (
                f"Multi-dimensional confluence is strongly aligned bearish ({score:.1f} score). "
                f"Break of structure, orderbook selling pressure, and macro headwind confirm downside momentum "
                f"with an asymmetric Risk/Reward of {rr_ratio:.2f}R."
            )
            action_directive = "Execute limit order within specified entry zone. Set hard stop loss immediately."

        # Developing / Wait Condition
        elif (DECISION_THRESHOLDS["WAIT_UPPER_BOUND"] <= abs(score) < DECISION_THRESHOLDS["VALID_LONG_SCORE"]) or (conflict_penalty >= 20.0 and abs(score) > 30.0) or regime == "LOW_VOLATILITY_COMPRESSION":
            decision_state = "WAIT_SETUP_DEVELOPING"
            badge_text = "🟡 WAIT — SETUP DEVELOPING"
            badge_class = "wait-developing"
            if conflict_penalty >= 20.0:
                summary_reason = (
                    f"A directional bias is emerging ({score:+.1f} score), but conflicting cross-asset or derivatives signals "
                    f"(Conflict Penalty: {conflict_penalty:.1f}) require patience until confirmation clears the divergence."
                )
            elif regime == "LOW_VOLATILITY_COMPRESSION":
                summary_reason = (
                    "Market is inside an energy coil / volatility compression squeeze. "
                    "Wait for a confirmed breakout candle close outside the consolidation range before entering."
                )
            else:
                summary_reason = (
                    f"Potential setup developing ({score:+.1f} score), but total conviction ({conviction_pct:.1f}%) "
                    "remains below the institutional execution threshold. Awaiting trigger confirmation."
                )
            action_directive = "Do not force entry. Monitor key structural levels and await volume confirmation."

        # No Trade / Choppy / Risky Condition
        else:
            decision_state = "NO_TRADE"
            badge_text = "🔴 NO TRADE"
            badge_class = "no-trade"
            if not is_rr_valid and abs(score) > 30.0:
                summary_reason = (
                    f"Current market structure does not offer the minimum acceptable Risk/Reward ratio (Required >= 2.0R, Current: {rr_ratio:.2f}R). "
                    "Capital preservation takes priority over low-quality setups."
                )
            elif regime == "HIGH_VOLATILITY_EXPANSION":
                summary_reason = (
                    "Market is in a High-Volatility Shock regime with excessive liquidation spikes and wide spreads. "
                    "Avoid entering during active price discovery."
                )
            else:
                summary_reason = (
                    "Market evidence is neutral, fragmented, or conflicting across key dimensions. "
                    "No statistical or fundamental edge is present. Capital preservation is the optimal strategy."
                )
            action_directive = "Stand aside. Preserve capital. Patiently await high-confluence alignment."

        # Catalysts and supporting factors
        supporting_evidence = []
        conflicting_evidence = []

        pillars = confluence_payload.get("pillars", {})
        for p_key, p_info in pillars.items():
            if (score > 0 and p_info["bias"] == "BULLISH") or (score < 0 and p_info["bias"] == "BEARISH"):
                supporting_evidence.append(f"**{p_info['name']}**: {', '.join(p_info['key_factors'][:2])}")
            elif (score > 0 and p_info["bias"] == "BEARISH") or (score < 0 and p_info["bias"] == "BULLISH"):
                conflicting_evidence.append(f"**{p_info['name']}**: {', '.join(p_info['key_factors'][:2])}")

        return {
            "decision_state": decision_state,
            "badge_text": badge_text,
            "badge_class": badge_class,
            "summary_reason": summary_reason,
            "action_directive": action_directive,
            "master_confluence_score": score,
            "conviction_pct": conviction_pct,
            "conflict_level": confluence_payload.get("conflict_level", "LOW_CONFLICT_HARMONY"),
            "supporting_evidence": supporting_evidence[:4],
            "conflicting_evidence": conflicting_evidence[:3],
            "risk_setup": risk_payload,
            "thesis": thesis_payload
        }
