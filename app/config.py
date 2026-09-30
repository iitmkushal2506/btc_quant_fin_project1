"""
Bitcoin AI Trading & Market Intelligence System - Configuration
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

# Base Settings
APP_NAME = "BTC AI Quantitative Trading & Market Intelligence System"
VERSION = "1.0.0"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# Market Symbol Settings
PRIMARY_SYMBOL = "BTCUSDT"
SUPPORTED_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]
DEFAULT_TIMEFRAME = "1h"
KLINE_LIMIT = 500

# Public & Free API Endpoints
BINANCE_SPOT_API = "https://api.binance.com/api/v3"
BINANCE_FUTURES_API = "https://fapi.binance.com/fapi/v1"
BINANCE_DATA_API = "https://fapi.binance.com/futures/data"
FEAR_GREED_API = "https://api.alternative.me/fng/?limit=30"
MEMPOOL_API = "https://mempool.space/api"
BLOCKCHAIN_INFO_API = "https://api.blockchain.info"
COINGECKO_API = "https://api.coingecko.com/api/v3"

# Macro Assets (Yahoo Finance Tickers)
MACRO_TICKERS: Dict[str, str] = {
    "DXY": "DX-Y.NYB",      # US Dollar Index
    "SP500": "^GSPC",       # S&P 500
    "NASDAQ": "^IXIC",      # Nasdaq Composite
    "GOLD": "GC=F",         # Gold Futures
    "US10Y": "^TNX",        # US 10-Year Treasury Yield
    "ETH": "ETH-USD",       # Ethereum / Crypto Beta
}

# Free Global Market & Crypto RSS News Feeds (Worldwide Coverage)
NEWS_RSS_FEEDS: List[Dict[str, str]] = [
    # Global Macro, Central Banks & World Markets
    {"source": "Yahoo Finance World", "category": "GLOBAL_MACRO", "region": "🌐 Global", "url": "https://finance.yahoo.com/news/rssindex"},
    {"source": "MarketWatch Global", "category": "STOCKS_COMMODITIES", "region": "🇺🇸 US", "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"},
    {"source": "CNBC World Markets", "category": "GLOBAL_MACRO", "region": "🇺🇸 US", "url": "https://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=markets&sort=date&output=rss"},
    {"source": "Investing.com World", "category": "GLOBAL_MACRO", "region": "🇪🇺 Europe", "url": "https://www.investing.com/rss/news.rss"},
    
    # Bitcoin & Global Crypto Intelligence
    {"source": "CoinDesk Global", "category": "BITCOIN_CRYPTO", "region": "🌐 Global", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"source": "CoinTelegraph Worldwide", "category": "BITCOIN_CRYPTO", "region": "🌐 Global", "url": "https://cointelegraph.com/rss"},
    {"source": "Decrypt Media", "category": "BITCOIN_CRYPTO", "region": "🇺🇸 US", "url": "https://decrypt.co/feed"},
    {"source": "Bitcoin Magazine", "category": "BITCOIN_CRYPTO", "region": "🌐 Global", "url": "https://bitcoinmagazine.com/.rss/full/"},
    {"source": "The Block Crypto", "category": "BITCOIN_CRYPTO", "region": "🇯🇵 Asia / Global", "url": "https://www.theblock.co/rss.xml"},
]


# Confluence Matrix Pillars & Weightings
CONFLUENCE_WEIGHTS: Dict[str, float] = {
    "technical_structure": 0.22,      # Multi-timeframe trend, EMA, RSI, MACD, SMC (BOS, CHoCH, Order Blocks, FVGs)
    "order_flow_liquidity": 0.14,     # Orderbook depth imbalance, bid/ask walls, spread, CVD proxy
    "derivatives_positioning": 0.18,  # Funding rate, Open Interest trend, Long/Short ratio, liquidations
    "onchain_fundamentals": 0.10,     # Mempool congestion, fee rates, active addresses, network health
    "macro_cross_asset": 0.12,        # DXY correlation, risk-on/risk-off regime, 10Y yield pressure
    "sentiment_news_nlp": 0.10,       # Fear & Greed index, breaking news sentiment, entity catalyst impact
    "quant_ml_regime": 0.14,          # Regime clustering (Bull, Bear, Range, Squeeze), ML ensemble probabilities
}

# Decision Thresholds
DECISION_THRESHOLDS = {
    "VALID_LONG_SCORE": 58.0,         # Minimum confluence score for LONG setup
    "VALID_SHORT_SCORE": -58.0,       # Maximum confluence score for SHORT setup
    "WAIT_UPPER_BOUND": 35.0,         # Developing setup upper threshold
    "WAIT_LOWER_BOUND": -35.0,        # Developing setup lower threshold
    "MAX_CONFLICT_PENALTY": 30.0,     # Penalty deducted when pillars strongly contradict
    "MIN_RISK_REWARD_RATIO": 2.0,     # Trade setup invalid if R:R is below 2.0
}

# Risk Management Defaults
DEFAULT_RISK_PARAMS = {
    "account_equity": 10000.0,        # Default USD capital for sizing calculator
    "risk_percentage": 1.0,           # 1.0% risk per trade
    "max_account_risk": 2.0,          # Maximum allowable portfolio risk %
    "atr_stop_multiplier": 1.75,      # ATR multiplier for stop loss buffer
    "tp1_rr_multiplier": 1.5,         # Target 1 (50% scale out + breakeven stop)
    "tp2_rr_multiplier": 2.75,        # Target 2 (30% scale out)
    "tp3_rr_multiplier": 4.5,         # Target 3 (20% runner)
    "max_recommended_leverage": 5.0,  # Max prudent leverage for BTC volatility
}

# Cache & Polling Intervals (seconds)
CACHE_TTL = {
    "ticker": 3,
    "klines": 10,
    "orderbook": 5,
    "derivatives": 30,
    "macro": 300,
    "onchain": 300,
    "sentiment": 300,
    "news": 180,
    "ml_regime": 30,
}
