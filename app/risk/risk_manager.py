"""
Institutional Financial Risk Management & Position Sizing Engine:
Entry Zones, Structural Stop-Loss, Multi-Tier Targets, Kelly Criterion, and Prudent Leverage
"""

from typing import Dict, Any, Optional
import numpy as np

from app.config import DEFAULT_RISK_PARAMS, DECISION_THRESHOLDS

class RiskManager:
    def __init__(self, risk_params: Optional[Dict[str, Any]] = None):
        self.params = risk_params or DEFAULT_RISK_PARAMS

    def calculate_trade_setup(
        self,
        direction: str,
        current_price: float,
        atr: float,
        structure_data: Dict[str, Any],
        account_equity: float = 10000.0,
        risk_pct: float = 1.0
    ) -> Dict[str, Any]:
        """Compute institutional trade setup with exact entry, stop loss, targets, and position sizing."""
        if direction not in ["LONG", "SHORT"] or current_price <= 0:
            return self._generate_no_trade_risk_profile(current_price, account_equity)

        atr_buffer = atr * self.params.get("atr_stop_multiplier", 1.75)
        nearest_support = structure_data.get("nearest_support", current_price * 0.97)
        nearest_resistance = structure_data.get("nearest_resistance", current_price * 1.03)

        if direction == "LONG":
            # Entry Zone: near current price or pullback to nearest order block
            entry_optimal = current_price
            entry_min = round(current_price * 0.997, 2)
            entry_max = round(current_price * 1.002, 2)

            # Stop Loss below nearest swing low or structural support - ATR buffer
            structural_sl = min(nearest_support, current_price - atr_buffer)
            stop_loss = round(structural_sl - (atr * 0.5), 2)
            risk_per_unit = entry_optimal - stop_loss

            if risk_per_unit <= 0 or (risk_per_unit / entry_optimal) > 0.08:
                stop_loss = round(entry_optimal * 0.975, 2) # Fallback 2.5% max risk
                risk_per_unit = entry_optimal - stop_loss

            # Multi-tier Take Profits
            tp1 = round(entry_optimal + (risk_per_unit * 1.85), 2)
            tp2 = round(entry_optimal + (risk_per_unit * 3.0), 2)
            tp3 = round(entry_optimal + (risk_per_unit * 4.8), 2)

            rr_ratio = (tp1 - entry_optimal) / risk_per_unit

        else: # SHORT
            entry_optimal = current_price
            entry_min = round(current_price * 0.998, 2)
            entry_max = round(current_price * 1.003, 2)

            structural_sl = max(nearest_resistance, current_price + atr_buffer)
            stop_loss = round(structural_sl + (atr * 0.5), 2)
            risk_per_unit = stop_loss - entry_optimal

            if risk_per_unit <= 0 or (risk_per_unit / entry_optimal) > 0.08:
                stop_loss = round(entry_optimal * 1.025, 2)
                risk_per_unit = stop_loss - entry_optimal

            tp1 = round(entry_optimal - (risk_per_unit * 1.85), 2)
            tp2 = round(entry_optimal - (risk_per_unit * 3.0), 2)
            tp3 = round(entry_optimal - (risk_per_unit * 4.8), 2)

            rr_ratio = (entry_optimal - tp1) / risk_per_unit

        # Capital Preservation & Position Sizing
        risk_pct_clamped = max(0.25, min(3.0, risk_pct))
        risk_dollars = account_equity * (risk_pct_clamped / 100.0)

        # Position Size (BTC)
        pos_size_btc = risk_dollars / risk_per_unit if risk_per_unit > 0 else 0.01
        notional_usd = pos_size_btc * entry_optimal
        effective_leverage = notional_usd / account_equity if account_equity > 0 else 1.0

        # Estimated Liquidation Price under isolated margin
        if direction == "LONG":
            est_liquidation = entry_optimal * (1.0 - (1.0 / max(1.0, effective_leverage)) * 0.9)
        else:
            est_liquidation = entry_optimal * (1.0 + (1.0 / max(1.0, effective_leverage)) * 0.9)

        # Fractional Kelly Criterion calculation
        # f* = (p * b - q) / b where p = 0.55 win rate, b = 2.0 R:R, q = 0.45 loss rate
        win_prob = 0.55
        b_ratio = rr_ratio
        kelly_fraction = (win_prob * b_ratio - (1 - win_prob)) / b_ratio if b_ratio > 0 else 0.05
        half_kelly_pct = max(0.5, min(2.5, kelly_fraction * 0.5 * 100))

        # Expected Value (EV) per $1 risked: EV = (Win_Prob * TP1_R) - (Loss_Prob * 1.0)
        expected_value_r = (win_prob * rr_ratio) - ((1.0 - win_prob) * 1.0)

        is_rr_valid = bool(rr_ratio >= DECISION_THRESHOLDS["MIN_RISK_REWARD_RATIO"])

        return {
            "direction": direction,
            "entry_zone": {
                "optimal": round(float(entry_optimal), 2),
                "min_entry": round(float(entry_min), 2),
                "max_entry": round(float(entry_max), 2)
            },
            "stop_loss": round(float(stop_loss), 2),
            "stop_loss_distance_usd": round(float(risk_per_unit), 2),
            "stop_loss_distance_pct": round(float((risk_per_unit / entry_optimal) * 100), 2),
            "take_profit_levels": [
                {"tier": "TP1 (50% scale out + BE stop)", "price": round(float(tp1), 2), "rr": 1.85, "profit_usd": round(float(risk_dollars * 1.85 * 0.5), 2)},
                {"tier": "TP2 (30% scale out)", "price": round(float(tp2), 2), "rr": 3.0, "profit_usd": round(float(risk_dollars * 3.0 * 0.3), 2)},
                {"tier": "TP3 (20% runner)", "price": round(float(tp3), 2), "rr": 4.8, "profit_usd": round(float(risk_dollars * 4.8 * 0.2), 2)},
            ],
            "risk_reward_ratio": round(float(rr_ratio), 2),
            "is_rr_valid": is_rr_valid,
            "position_sizing": {
                "account_equity_usd": float(account_equity),
                "risk_percentage": float(risk_pct_clamped),
                "max_risk_usd": round(float(risk_dollars), 2),
                "position_size_btc": round(float(pos_size_btc), 4),
                "position_notional_usd": round(float(notional_usd), 2),
                "effective_leverage": round(float(effective_leverage), 2),
                "recommended_max_leverage": float(self.params.get("max_recommended_leverage", 5.0)),
                "est_liquidation_price": round(float(est_liquidation), 2),
                "half_kelly_recommended_risk_pct": round(float(half_kelly_pct), 2),
                "expected_value_per_trade_r": round(float(expected_value_r), 2)
            }
        }

    def _generate_no_trade_risk_profile(self, current_price: float, account_equity: float) -> Dict[str, Any]:
        """Default defensive risk payload when no trade is active."""
        return {
            "direction": "NO_TRADE",
            "entry_zone": {"optimal": round(current_price, 2), "min_entry": 0.0, "max_entry": 0.0},
            "stop_loss": 0.0,
            "stop_loss_distance_usd": 0.0,
            "stop_loss_distance_pct": 0.0,
            "take_profit_levels": [],
            "risk_reward_ratio": 0.0,
            "is_rr_valid": False,
            "position_sizing": {
                "account_equity_usd": account_equity,
                "risk_percentage": 0.0,
                "max_risk_usd": 0.0,
                "position_size_btc": 0.0,
                "position_notional_usd": 0.0,
                "effective_leverage": 0.0,
                "recommended_max_leverage": 5.0,
                "est_liquidation_price": 0.0,
                "half_kelly_recommended_risk_pct": 1.0,
                "expected_value_per_trade_r": 0.0
            }
        }
