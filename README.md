# ⚡ Bitcoin AI Quantitative Trading & Market Intelligence System

A data-science-driven institutional Bitcoin quantitative intelligence and rapid scalping platform with an executive **White Financial Dashboard Theme**, **5-Minute Scalper Engine**, **Non-Trader (NN) Beginner Guide**, **Forensic Post-Mortem Trade Book**, and custom **Trade Music Player (`songs_trade/` folder)**.

https://btc-quant-fin-project1.onrender.com/

---


## 🏛 Core Architectural Philosophy

The system prioritizes **evidence, confluence, statistical validation, and capital preservation over trade frequency**. 

Rather than relying on basic technical indicators, the system continuously aggregates **7 independent market dimensions** into a single transparent, evidence-based trading assessment:

```
LIVE MARKET DATA + TECHNICAL ANALYSIS (SMC) + QUANTITATIVE DATA SCIENCE + MACHINE LEARNING + 
DERIVATIVES & POSITIONING + ON-CHAIN & MEMPOOL + MACROECONOMICS + GLOBAL NEWS NLP + SENTIMENT + RISK MANAGEMENT
```

### Authoritative Decision States

* 🟢 **`TRADE SETUP VALID (LONG / SHORT)`**: All independent pillars align with statistical edge, low conflict index, and asymmetric Risk/Reward $\ge 2.0\text{R}$.
* 🟡 **`WAIT — SETUP DEVELOPING`**: Directional bias is emerging, but important confirmation (e.g. funding reset, range breakout, news cooling) is pending.
* 🔴 **`NO TRADE`**: Evidence is insufficient, contradictory, market conditions are in chop/ranging regimes, or risk is excessive. *No Trade is treated as an active and critical capital preservation result.*

---

## 🌐 7 Independent Confluence Pillars & Data Sources

| Pillar | Dimension | Weight | Public & Free Data Sources |
| :--- | :--- | :---: | :--- |
| **1** | **Technical & SMC Market Structure** | **22%** | Binance Public Spot Klines (15m, 1h, 4h, 1D), EMA stacks (20, 50, 200), RSI 14, MACD, Bollinger Bands, ATR, Supertrend, Order Blocks (OB), Fair Value Gaps (FVG), Swing Highs/Lows, BOS & CHoCH. |
| **2** | **Order Flow & Liquidity Depth** | **14%** | Binance Spot Orderbook Depth (L2), Order Book Imbalance (OBI), Bid-Ask Spread bps, Support & Resistance Liquidity Wall Detection. |
| **3** | **Derivatives & Open Interest** | **18%** | Binance Futures Open Interest, 8h Funding Rate, Annualized Funding %, Top Trader Long/Short Ratio, Taker Buy/Sell Volume Ratio, Squeeze Risk Index. |
| **4** | **On-Chain & Mempool Health** | **10%** | Mempool.space recommended fee rates (fastest, half-hour, hour), Mempool transaction backlog & vsize, Bitcoin market capitalization & distance from ATH. |
| **5** | **Macroeconomics & Cross-Asset** | **12%** | Yahoo Finance tickers: US Dollar Index (DXY), S&P 500 (`^GSPC`), Nasdaq 100 (`^IXIC`), Gold Futures (`GC=F`), US 10-Year Treasury Yield (`^TNX`). 30-day rolling correlation matrices and Risk-On/Risk-Off regime index. |
| **6** | **Sentiment & Global Breaking News NLP** | **10%** | Alternative.me Fear & Greed Index (historical momentum) + RSS Breaking News feeds (CoinDesk, CoinTelegraph, Decrypt, Bitcoin Magazine) processed through an entity extraction and crypto-domain NLP sentiment & factuality classifier. |
| **7** | **Quantitative Data Science & Machine Learning** | **14%** | Gaussian Mixture & Volatility Regime Clustering (`TRENDING_BULL`, `TRENDING_BEAR`, `RANGING`, `LOW_VOL_SQUEEZE`, `VOLATILITY_SHOCK`), Hurst Exponent ($H$), RandomForest + GradientBoosting ensemble predicting forward directional probabilities $P(\text{Bull})$, $P(\text{Neutral})$, $P(\text{Bear})$ with feature importance ranking, and 1,000-Path Monte Carlo Jump Diffusion simulation. |

---

## 🛡 Institutional Financial Risk Management

Every valid setup provides:
* **Optimal Entry Zone** (Pullback to Order Block / Fair Value Gap)
* **Structural Hard Stop Loss** (Swing pivot + 1.75x ATR buffer)
* **Multi-Tier Take Profit Targets**:
  * **TP1**: $1.85\text{R}$ (Scale out 50% and immediately move stop to Breakeven)
  * **TP2**: $3.00\text{R}$ (Scale out 30%)
  * **TP3**: $4.80\text{R}$ (Runner 20%)
* **Position Sizing Engine**:
  * Fixed Fractional Portfolio Risk ($0.5\% - 2.0\%$ max risk per trade)
  * Fractional Kelly Criterion calculation
  * Effective Leverage calculation & Estimated Liquidation Price verification
* **Explicit Structural Invalidation Rules** & Major Thesis Risks

---

## 🚀 Quickstart & Local Execution

### 1. Dual-Terminal Modes Available

* 🏛 **Macro Institutional Terminal**: Comprehensive 7-pillar multi-timeframe analysis prioritizing high conviction and capital preservation.
  👉 **`http://localhost:8000/`**
* ⚡ **5-Minute Scalper AI Terminal**: High-frequency intraday momentum scalping engine generating active trade setups **every 5 minutes** with real-time trade stream.
  👉 **`http://localhost:8000/scalp`** (or `http://localhost:8000/5m`)

---

## 📡 REST API & WebSocket Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/scalp` or `/5m` | `GET` | Specialized 5-minute Scalper Web Terminal interface. |
| `/api/scalp/overview` | `GET` | Active 5-minute trade, timer countdown, and micro-confluence metrics. |
| `/api/scalp/history` | `GET` | Continuous live stream of 5-minute AI scalp trades with Win/Loss PnL. |
| `/api/scalp/force-generate`| `POST` | Force immediate on-demand generation of a fresh 5-minute trade setup. |
| `/api/overview` | `GET` | Complete holistic market intelligence payload with master decision, 7 pillars, and risk sizing. |
| `/api/market/klines` | `GET` | Multi-timeframe OHLCV data with EMA 20/50/200, Bollinger Bands, Order Blocks, and FVGs. |
| `/api/market/orderbook` | `GET` | Orderbook depth, bid-ask spread bps, imbalance ratio, and liquidity walls. |
| `/api/derivatives` | `GET` | Futures open interest, funding rate, long/short ratio, and squeeze risk score. |
| `/api/onchain` | `GET` | Mempool backlog, priority fee recommendations, and network stats. |
| `/api/macro` | `GET` | Macro asset prices (DXY, SPX, Gold, 10Y Yield) and rolling BTC correlations. |
| `/api/news` | `GET` | Breaking crypto news with NLP sentiment labels, factuality classification, and entity tags. |
| `/api/quant/monte-carlo`| `GET` | 1,000-path Monte Carlo price projection, 95% Confidence Cone, and VaR. |
| `/api/quant/backtest` | `GET` | Walk-forward strategy backtest results, Sharpe/Sortino ratios, and equity curve. |
| `/api/risk/calculate` | `POST` | Custom interactive position sizing calculator based on custom equity and risk %. |
| `/ws/live` | `WS` | Real-time WebSocket streaming live price ticks and signal updates. |

---

## ⚠️ Risk Disclaimer
This system is an evidence-based quantitative market intelligence tool built for data science analysis and risk evaluation. It does not guarantee future market behavior. Always manage capital prudently.
