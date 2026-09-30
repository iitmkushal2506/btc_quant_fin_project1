"""
7-Pillar Multi-Dimensional Confluence Synthesis Engine:
Cross-dimensional synthesis, Conflict Penalty Matrix, and Conviction Scoring
"""

from typing import Dict, Any, List
import numpy as np

from app.config import CONFLUENCE_WEIGHTS

class ConfluenceEngine:
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or CONFLUENCE_WEIGHTS

    def evaluate_confluence(
        self,
        technical_data: Dict[str, Any],
        structure_data: Dict[str, Any],
        orderbook_data: Dict[str, Any],
        derivatives_data: Dict[str, Any],
        onchain_data: Dict[str, Any],
        macro_data: Dict[str, Any],
        sentiment_data: Dict[str, Any],
        news_data: Dict[str, Any],
        quant_ml_data: Dict[str, Any],
        regime_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize all 7 pillars into a master evidence-based confluence payload."""

        # 1. Technical & Structure Score (Combines indicators + SMC)
        tech_score = technical_data.get("score", 0.0)
        struct_score = structure_data.get("structure_score", 0.0)
        p1_score = max(-100.0, min(100.0, 0.55 * tech_score + 0.45 * struct_score))

        # 2. Order Flow & Liquidity Imbalance Score
        obi = orderbook_data.get("orderbook_imbalance", 0.0)
        spread_bps = orderbook_data.get("spread_bps", 0.2)
        p2_score = obi * 100.0 # -1.0 to 1.0 mapped to -100 to +100
        if spread_bps > 1.5:
            p2_score *= 0.7 # illiquid spread penalty
        p2_score = max(-100.0, min(100.0, p2_score))

        # 3. Derivatives & Positioning Score
        funding_rate = derivatives_data.get("current_funding_rate", 0.0001)
        ls_ratio = derivatives_data.get("long_short_ratio", 1.0)
        taker_ratio = derivatives_data.get("taker_buy_sell_ratio", 1.0)
        squeeze_risk = derivatives_data.get("squeeze_risk_score", 0.0)

        # High funding + crowded longs = contrarian bearish pressure (- score)
        # Negative funding + crowded shorts = contrarian bullish short squeeze fuel (+ score)
        p3_score = 0.0
        if funding_rate < -0.0001:
            p3_score += 45.0 # Shorts paying longs -> bullish squeeze fuel
        elif funding_rate > 0.0003:
            p3_score -= 45.0 # Longs overpaying -> long flush risk
        elif funding_rate > 0.00015:
            p3_score -= 15.0

        if taker_ratio > 1.15:
            p3_score += 35.0 # Aggressive taker market buying
        elif taker_ratio < 0.85:
            p3_score -= 35.0 # Aggressive taker market selling

        if ls_ratio < 0.85:
            p3_score += 20.0 # Retail crowded short
        elif ls_ratio > 1.8:
            p3_score -= 20.0 # Retail crowded long

        p3_score = max(-100.0, min(100.0, p3_score))

        # 4. On-Chain & Fundamentals Score
        congestion = onchain_data.get("congestion_level", "NORMAL")
        net_health = onchain_data.get("network_health_score", 85.0)
        p4_score = (net_health - 50.0) * 0.8
        if congestion == "HIGH_CONGESTION":
            p4_score += 15.0 # High fee demand indicates strong on-chain economic velocity
        p4_score = max(-100.0, min(100.0, p4_score))

        # 5. Macro & Cross-Asset Score
        p5_score = macro_data.get("macro_score", 0.0)
        dxy_chg = macro_data.get("assets", {}).get("DXY", {}).get("change_pct_24h", 0.0)
        if dxy_chg < -0.2:
            p5_score += 15.0
        elif dxy_chg > 0.3:
            p5_score -= 20.0
        p5_score = max(-100.0, min(100.0, p5_score))

        # 6. Sentiment & Global News NLP Score
        fng_score = sentiment_data.get("score", 50)
        news_score = news_data.get("summary", {}).get("overall_news_score", 0.0)
        
        # Fear & Greed normalized from [0, 100] to [-50, +50]
        fng_normalized = (fng_score - 50) * 1.0
        # If extreme greed (>80), contrarian risk reduces score
        if fng_score > 80:
            fng_normalized = 10.0 # Dampened
        elif fng_score < 20:
            fng_normalized = 25.0 # Contrarian accumulation bonus

        p6_score = 0.5 * fng_normalized + 0.5 * news_score
        p6_score = max(-100.0, min(100.0, p6_score))

        # 7. Quantitative & ML Regime Score
        ml_score = quant_ml_data.get("ml_score", 0.0)
        regime_mul = regime_data.get("risk_multiplier", 1.0)
        regime_type = regime_data.get("regime", "RANGING_MEAN_REVERTING")
        
        p7_score = ml_score * regime_mul
        if regime_type == "TRENDING_BULL" and p7_score > 0:
            p7_score += 15.0
        elif regime_type == "TRENDING_BEAR" and p7_score < 0:
            p7_score -= 15.0
        elif regime_type == "HIGH_VOLATILITY_EXPANSION":
            p7_score *= 0.6
        p7_score = max(-100.0, min(100.0, p7_score))

        # Assemble Pillar Scores
        pillars = {
            "technical_structure": {
                "name": "Technical & SMC Structure",
                "score": round(p1_score, 1),
                "weight": self.weights["technical_structure"],
                "bias": "BULLISH" if p1_score > 20 else ("BEARISH" if p1_score < -20 else "NEUTRAL"),
                "key_factors": [
                    f"Technical Score: {tech_score:+.1f}",
                    f"Structure State: {structure_data.get('structure', 'NEUTRAL')}",
                    f"RSI (14): {technical_data.get('rsi', 50.0)}",
                    f"Unmitigated Order Blocks: {len(structure_data.get('order_blocks', []))}"
                ]
            },
            "order_flow_liquidity": {
                "name": "Order Flow & Depth Imbalance",
                "score": round(p2_score, 1),
                "weight": self.weights["order_flow_liquidity"],
                "bias": "BULLISH" if p2_score > 15 else ("BEARISH" if p2_score < -15 else "NEUTRAL"),
                "key_factors": [
                    f"Orderbook Imbalance: {obi:+.3f}",
                    f"Spread: {spread_bps:.2f} bps",
                    f"Bid Walls: {len(orderbook_data.get('bid_walls', []))}",
                    f"Ask Walls: {len(orderbook_data.get('ask_walls', []))}"
                ]
            },
            "derivatives_positioning": {
                "name": "Derivatives & Liquidation Flow",
                "score": round(p3_score, 1),
                "weight": self.weights["derivatives_positioning"],
                "bias": "BULLISH" if p3_score > 15 else ("BEARISH" if p3_score < -15 else "NEUTRAL"),
                "key_factors": [
                    f"Funding Rate: {funding_rate * 100:+.4f}% / 8h",
                    f"Long/Short Ratio: {ls_ratio:.2f}",
                    f"Taker Buy/Sell: {taker_ratio:.2f}",
                    f"Squeeze Risk Score: {squeeze_risk:+.1f}"
                ]
            },
            "onchain_fundamentals": {
                "name": "On-Chain & Mempool Health",
                "score": round(p4_score, 1),
                "weight": self.weights["onchain_fundamentals"],
                "bias": "BULLISH" if p4_score > 15 else ("BEARISH" if p4_score < -15 else "NEUTRAL"),
                "key_factors": [
                    f"Fastest Fee: {onchain_data.get('fastest_fee_sat_vb', 15)} sat/vB",
                    f"Mempool Count: {onchain_data.get('mempool_tx_count', 40000):,} txs",
                    f"Network Health: {net_health:.1f}/100"
                ]
            },
            "macro_cross_asset": {
                "name": "Macroeconomics & Cross-Asset",
                "score": round(p5_score, 1),
                "weight": self.weights["macro_cross_asset"],
                "bias": "BULLISH" if p5_score > 15 else ("BEARISH" if p5_score < -15 else "NEUTRAL"),
                "key_factors": [
                    f"Macro Regime: {macro_data.get('macro_regime', 'NEUTRAL')}",
                    f"DXY 24h Change: {dxy_chg:+.2f}%",
                    f"BTC-SPX Correlation: {macro_data.get('correlations', {}).get('BTC_SP500_corr', 0.0):+.2f}"
                ]
            },
            "sentiment_news_nlp": {
                "name": "Sentiment & Breaking News NLP",
                "score": round(p6_score, 1),
                "weight": self.weights["sentiment_news_nlp"],
                "bias": "BULLISH" if p6_score > 15 else ("BEARISH" if p6_score < -15 else "NEUTRAL"),
                "key_factors": [
                    f"Fear & Greed Index: {fng_score} ({sentiment_data.get('label', 'Neutral')})",
                    f"News Sentiment: {news_data.get('summary', {}).get('overall_news_sentiment', 'NEUTRAL')}",
                    f"News Uncertainty: {news_data.get('summary', {}).get('uncertainty_level', 'MODERATE')}"
                ]
            },
            "quant_ml_regime": {
                "name": "Quantitative ML & Regime Model",
                "score": round(p7_score, 1),
                "weight": self.weights["quant_ml_regime"],
                "bias": "BULLISH" if p7_score > 15 else ("BEARISH" if p7_score < -15 else "NEUTRAL"),
                "key_factors": [
                    f"Market Regime: {regime_data.get('regime_name', 'Ranging')}",
                    f"ML Bullish Prob: {quant_ml_data.get('prob_bullish', 33.3):.1f}%",
                    f"ML Bearish Prob: {quant_ml_data.get('prob_bearish', 33.3):.1f}%",
                    f"Hurst Exponent: {regime_data.get('hurst_exponent', 0.50):.3f}"
                ]
            }
        }

        # Calculate Raw Weighted Confluence Score
        raw_weighted_score = sum(p["score"] * p["weight"] for p in pillars.values())

        # Cross-Dimensional Conflict Analysis
        positive_count = sum(1 for p in pillars.values() if p["score"] > 15.0)
        negative_count = sum(1 for p in pillars.values() if p["score"] < -15.0)
        total_active_pillars = len(pillars)
        agreement_ratio = max(positive_count, negative_count) / total_active_pillars

        # Conflict Penalty Calculation
        # If both strong positive and strong negative pillars exist, apply conflict dampening
        conflict_penalty = 0.0
        if positive_count >= 2 and negative_count >= 2:
            conflict_penalty = min(35.0, (positive_count * negative_count) * 4.0)

        # Apply Conflict Penalty to Master Score
        if raw_weighted_score > 0:
            final_confluence_score = max(0.0, raw_weighted_score - conflict_penalty)
        else:
            final_confluence_score = min(0.0, raw_weighted_score + conflict_penalty)

        # Conviction Percentage (0% to 100%)
        conviction_pct = min(100.0, abs(final_confluence_score) * 1.15 * (1.0 - (conflict_penalty / 100.0)))
        if regime_type == "HIGH_VOLATILITY_EXPANSION" or regime_type == "RANGING_MEAN_REVERTING":
            conviction_pct *= 0.80

        return {
            "master_confluence_score": round(final_confluence_score, 1),
            "raw_weighted_score": round(raw_weighted_score, 1),
            "conflict_penalty": round(conflict_penalty, 1),
            "conviction_pct": round(conviction_pct, 1),
            "pillars_in_agreement": f"{max(positive_count, negative_count)} of {total_active_pillars}",
            "agreement_ratio_pct": round(agreement_ratio * 100, 1),
            "conflict_level": "HIGH_CONFLICT" if conflict_penalty > 18 else ("MODERATE_CONFLICT" if conflict_penalty > 8 else "LOW_CONFLICT_HARMONY"),
            "pillars": pillars
        }
