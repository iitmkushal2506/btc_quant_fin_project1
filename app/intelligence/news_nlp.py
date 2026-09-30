"""
News NLP & Entity Intelligence Engine:
Entity extraction, Crypto-domain Sentiment Analysis, and Factuality/Uncertainty Classification
"""

import re
from typing import Dict, Any, List, Tuple

# Entity Taxonomy Keywords
ENTITY_PATTERNS = {
    "ETF_FLOWS": [r"\betf\b", r"spot etf", r"blackrock", r"fidelity", r"inflows", r"outflows", r"ishares", r"grayscale", r"gbtc"],
    "REGULATION": [r"\bsec\b", r"cftc", r"gensler", r"regulation", r"lawsuit", r"compliance", r"senate", r"treasury", r"doj", r"subpoena", r"ban"],
    "INSTITUTIONAL": [r"microstrategy", r"saylor", r"institutional", r"hedge fund", r"custody", r"treasury reserve", r"sovereign", r"fidelity"],
    "CENTRAL_BANKS_MACRO": [r"fed\b", r"federal reserve", r"jerome powell", r"rate cut", r"rate hike", r"inflation", r"cpi", r"fomc", r"interest rate", r"liquidity"],
    "EXCHANGES": [r"binance", r"coinbase", r"kraken", r"bybit", r"okx", r"deribit", r"exchange reserve", r"outflow from exchange"],
    "HACKS_SECURITY": [r"hack", r"exploit", r"stolen", r"vulnerability", r"drainer", r"rug pull", r"breach", r"compromised", r"attack"],
    "MINING_HASHRATE": [r"mining", r"miner", r"hashrate", r"difficulty adjustment", r"halving", r"marathon", r"riot", r"cleanpark"],
    "STABLECOINS": [r"tether", r"usdt", r"circle", r"usdc", r"stablecoin", r"depeg", r"reserves", r"minted"],
    "BITCOIN_CORE": [r"bitcoin", r"\bbtc\b", r"satoshi", r"lightning network", r"taproot", r"node", r"ordinals", r"runes"]
}

# Domain-specific sentiment lexicons with crypto-adjusted weights
BULLISH_KEYWORDS = {
    "surge": 2.5, "soar": 2.5, "rally": 2.2, "breakout": 2.0, "all-time high": 3.0,
    "ath": 2.5, "inflow": 2.0, "accumulate": 2.0, "accumulation": 2.0, "adoption": 2.2,
    "approval": 2.8, "approved": 2.8, "bullish": 2.2, "rate cut": 2.0, "easing": 1.8,
    "stimulus": 2.2, "record": 1.8, "expansion": 1.5, "buying": 1.8, "outflow from exchange": 2.0,
    "partnership": 1.5, "upgrade": 1.4, "milestone": 1.6, "optimism": 1.5, "gain": 1.4,
    "green": 1.2, "rebound": 1.8, "recovery": 1.8, "boost": 1.6, "support": 1.2
}

BEARISH_KEYWORDS = {
    "crash": -3.0, "plunge": -2.8, "dump": -2.5, "selloff": -2.5, "collapse": -3.0,
    "lawsuit": -2.2, "ban": -2.8, "hack": -3.0, "stolen": -2.8, "exploit": -2.8,
    "sec charges": -3.0, "investigation": -2.0, "subpoena": -2.0, "outflow": -1.8,
    "liquidation": -2.0, "bearish": -2.2, "insolvency": -3.2, "bankrupt": -3.2,
    "rate hike": -2.2, "inflation rises": -2.0, "fear": -1.8, "panic": -2.5,
    "decline": -1.5, "drop": -1.5, "fall": -1.4, "loss": -1.5, "scam": -2.8,
    "fraud": -3.0, "warning": -1.8, "risk": -1.2, "fud": -1.5, "rejection": -2.0
}

# Factuality & Uncertainty patterns
VERIFIED_PATTERNS = [
    r"officially", r"announces", r"sec approves", r"filing reveals", r"confirmed",
    r"completed", r"statement shows", r"data shows", r"on-chain data confirms", r"passed"
]

UNCERTAINTY_PATTERNS = [
    r"could", r"might", r"may", r"rumor", r"speculates", r"analyst predicts",
    r"potential", r"expected to", r"unconfirmed", r"sources say", r"suggests", r"if"
]

class NewsNLPEngine:
    @staticmethod
    def analyze_article(title: str, summary: str = "", source: str = "") -> Dict[str, Any]:
        """Analyze title and summary for entities, sentiment, and factuality classification."""
        text = f"{title} {summary}".lower()

        # 1. Entity Extraction
        matched_entities = []
        for entity_type, patterns in ENTITY_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, text):
                    matched_entities.append(entity_type)
                    break

        if not matched_entities:
            matched_entities.append("GENERAL_CRYPTO")

        # 2. Crypto Sentiment Scoring
        bullish_score = 0.0
        bearish_score = 0.0

        for word, weight in BULLISH_KEYWORDS.items():
            count = len(re.findall(r"\b" + re.escape(word) + r"\b", text))
            if count > 0:
                bullish_score += weight * count

        for word, weight in BEARISH_KEYWORDS.items():
            count = len(re.findall(r"\b" + re.escape(word) + r"\b", text))
            if count > 0:
                bearish_score += abs(weight) * count

        net_raw = bullish_score - bearish_score
        # Normalize sentiment to range [-1.0, 1.0]
        denom = max(bullish_score + bearish_score, 1.0)
        sentiment_score = max(-1.0, min(1.0, net_raw / (denom * 1.5)))

        if sentiment_score > 0.18:
            sentiment_label = "BULLISH"
        elif sentiment_score < -0.18:
            sentiment_label = "BEARISH"
        else:
            sentiment_label = "NEUTRAL"

        # 3. Factuality & Uncertainty Classification
        is_verified = any(re.search(pat, text) for pat in VERIFIED_PATTERNS)
        is_uncertain = any(re.search(pat, text) for pat in UNCERTAINTY_PATTERNS)

        if "hack" in text or "exploit" in text or "lawsuit" in text:
            factuality = "DEVELOPING_REPORT"
        elif is_verified and not is_uncertain:
            factuality = "VERIFIED_EVENT"
        elif is_uncertain:
            factuality = "SPECULATION_UNCERTAINTY"
        elif "price" in text or "predict" in text or "target" in text:
            factuality = "MARKET_INTERPRETATION"
        else:
            factuality = "DEVELOPING_REPORT"

        # 4. Market Impact Assessment
        impact_weight = 1.0
        if "HACKS_SECURITY" in matched_entities or "REGULATION" in matched_entities or "CENTRAL_BANKS_MACRO" in matched_entities:
            impact_weight = 2.0
        elif "ETF_FLOWS" in matched_entities or "INSTITUTIONAL" in matched_entities:
            impact_weight = 1.6

        if (bullish_score + bearish_score) * impact_weight > 5.0:
            impact_level = "HIGH"
        elif (bullish_score + bearish_score) * impact_weight > 2.0:
            impact_level = "MEDIUM"
        else:
            impact_level = "LOW"

        return {
            "title": title,
            "summary": summary[:200] + "..." if len(summary) > 200 else summary,
            "source": source,
            "entities": matched_entities,
            "sentiment_score": round(sentiment_score, 3),
            "sentiment_label": sentiment_label,
            "factuality": factuality,
            "impact_level": impact_level,
            "confidence": round(min(1.0, (bullish_score + bearish_score) / 6.0 + 0.3), 2)
        }

    @classmethod
    def aggregate_news_sentiment(cls, analyzed_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize overall global news market bias & impact."""
        if not analyzed_articles:
            return {
                "overall_news_score": 0.0,
                "overall_news_sentiment": "NEUTRAL",
                "bullish_articles_count": 0,
                "bearish_articles_count": 0,
                "neutral_articles_count": 0,
                "top_themes": [],
                "uncertainty_level": "MODERATE"
            }

        total_weighted_score = 0.0
        total_weight = 0.0
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        entity_counts = {}
        factuality_counts = {}

        for art in analyzed_articles:
            w = 3.0 if art["impact_level"] == "HIGH" else (2.0 if art["impact_level"] == "MEDIUM" else 1.0)
            if art["factuality"] == "VERIFIED_EVENT":
                w *= 1.4
            elif art["factuality"] == "SPECULATION_UNCERTAINTY":
                w *= 0.6

            total_weighted_score += art["sentiment_score"] * w
            total_weight += w

            if art["sentiment_label"] == "BULLISH":
                bullish_count += 1
            elif art["sentiment_label"] == "BEARISH":
                bearish_count += 1
            else:
                neutral_count += 1

            for ent in art["entities"]:
                entity_counts[ent] = entity_counts.get(ent, 0) + 1

            f = art["factuality"]
            factuality_counts[f] = factuality_counts.get(f, 0) + 1

        overall_score = (total_weighted_score / total_weight) * 100 if total_weight > 0 else 0.0
        overall_score = max(-100.0, min(100.0, overall_score))

        top_themes = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:4]

        # Uncertainty calculation
        speculation_ratio = factuality_counts.get("SPECULATION_UNCERTAINTY", 0) / len(analyzed_articles)
        if speculation_ratio > 0.4:
            uncertainty = "HIGH"
        elif speculation_ratio > 0.2:
            uncertainty = "MODERATE"
        else:
            uncertainty = "LOW"

        return {
            "overall_news_score": round(overall_score, 1),
            "overall_news_sentiment": "BULLISH" if overall_score > 15 else ("BEARISH" if overall_score < -15 else "NEUTRAL"),
            "bullish_articles_count": bullish_count,
            "bearish_articles_count": bearish_count,
            "neutral_articles_count": neutral_count,
            "total_articles": len(analyzed_articles),
            "top_themes": [theme[0] for theme in top_themes],
            "uncertainty_level": uncertainty
        }
