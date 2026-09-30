"""
Bitcoin AI Trading & Market Intelligence System - FastAPI Main Application Server
"""

import os
import time
import asyncio
import logging
import numpy as np
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.config import APP_NAME, VERSION, HOST, PORT, DEFAULT_TIMEFRAME, SUPPORTED_TIMEFRAMES
from app.collectors.market_data import MarketDataCollector
from app.collectors.derivatives import DerivativesCollector
from app.collectors.orderbook import OrderbookCollector
from app.collectors.onchain import OnChainCollector
from app.collectors.macro import MacroCollector
from app.collectors.sentiment import SentimentCollector
from app.collectors.news_collector import NewsCollector

from app.quant.technical import TechnicalAnalyzer
from app.quant.market_structure import MarketStructureAnalyzer
from app.quant.volume_volatility import VolumeVolatilityAnalyzer
from app.quant.regime_detector import MarketRegimeDetector
from app.quant.ml_predictor import MLPredictor
from app.quant.statistical_analysis import StatisticalAnalyzer
from app.quant.backtester import StrategyBacktester
from app.quant.scalp_engine import ScalpEngine

from app.intelligence.confluence_engine import ConfluenceEngine
from app.intelligence.decision_maker import DecisionMaker
from app.risk.risk_manager import RiskManager
from app.risk.thesis_evaluator import ThesisEvaluator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("BTC_AI_ENGINE")

# Global Engine Context
class IntelligenceSystem:
    def __init__(self):
        # Collectors
        self.market_collector = MarketDataCollector()
        self.derivatives_collector = DerivativesCollector()
        self.orderbook_collector = OrderbookCollector()
        self.onchain_collector = OnChainCollector()
        self.macro_collector = MacroCollector()
        self.sentiment_collector = SentimentCollector()
        self.news_collector = NewsCollector()

        # Quant & ML
        self.ml_predictor = MLPredictor()
        self.scalp_engine = ScalpEngine()

        # Intelligence & Risk
        self.confluence_engine = ConfluenceEngine()
        self.risk_manager = RiskManager()

        # Cache of holistic assessment
        self.latest_assessment: Dict[str, Any] = {}
        self.active_connections: List[WebSocket] = []
        self.is_running = False

    async def update_pipeline(self) -> Dict[str, Any]:
        """Execute full multi-dimensional quantitative intelligence pipeline."""
        start_t = time.time()
        try:
            # 1. Concurrent Market & Environment Data Ingestion
            ticker_task = self.market_collector.get_live_ticker()
            kline_1h_task = self.market_collector.get_klines("1h", limit=300)
            kline_4h_task = self.market_collector.get_klines("4h", limit=150)
            kline_15m_task = self.market_collector.get_klines("15m", limit=100)
            derivatives_task = self.derivatives_collector.get_derivatives_data()
            orderbook_task = self.orderbook_collector.get_orderbook_metrics()
            onchain_task = self.onchain_collector.get_onchain_metrics()
            macro_task = self.macro_collector.get_macro_data()
            sentiment_task = self.sentiment_collector.get_sentiment_data()
            news_task = self.news_collector.get_latest_news()

            (
                ticker, df_1h, df_4h, df_15m, derivatives,
                orderbook, onchain, macro, sentiment, news
            ) = await asyncio.gather(
                ticker_task, kline_1h_task, kline_4h_task, kline_15m_task, derivatives_task,
                orderbook_task, onchain_task, macro_task, sentiment_task, news_task,
                return_exceptions=True
            )

            # Safeguards if exceptions occurred
            if isinstance(ticker, Exception): ticker = self.market_collector._generate_fallback_ticker()
            if isinstance(df_1h, Exception): df_1h = self.market_collector._generate_fallback_klines("1h", 300)
            if isinstance(df_4h, Exception): df_4h = self.market_collector._generate_fallback_klines("4h", 150)
            if isinstance(df_15m, Exception): df_15m = self.market_collector._generate_fallback_klines("15m", 100)
            if isinstance(derivatives, Exception): derivatives = self.derivatives_collector._generate_fallback_derivatives()
            if isinstance(orderbook, Exception): orderbook = self.orderbook_collector._generate_fallback_orderbook()
            if isinstance(onchain, Exception): onchain = self.onchain_collector._generate_fallback_onchain()
            if isinstance(macro, Exception): macro = self.macro_collector._generate_fallback_macro()
            if isinstance(sentiment, Exception): sentiment = self.sentiment_collector._generate_fallback_sentiment()
            if isinstance(news, Exception): news = self.news_collector._get_fallback_payload()

            # 2. Quantitative & Technical Analytics
            df_1h_ind = TechnicalAnalyzer.calculate_indicators(df_1h)
            tech_eval = TechnicalAnalyzer.evaluate_signals(df_1h_ind)
            structure = MarketStructureAnalyzer.analyze_structure(df_1h_ind)
            vol_eval = VolumeVolatilityAnalyzer.analyze(df_1h_ind)
            regime = MarketRegimeDetector.detect_regime(df_1h_ind)
            anomalies = StatisticalAnalyzer.detect_anomalies(df_1h_ind)

            # 3. Machine Learning & Monte Carlo Projections
            ml_pred = self.ml_predictor.predict_probabilities(df_1h_ind)
            current_price = ticker.get("last_price", 64500.0)
            monte_carlo = StatisticalAnalyzer.run_monte_carlo_simulation(
                current_price=current_price,
                daily_volatility_pct=vol_eval.get("parkinson_volatility_ann_pct", 50.0) / np.sqrt(365),
                horizon_hours=24,
                num_simulations=1000
            )

            # 4. Multi-Timeframe Trend Matrix
            mtf_matrix = {
                "15m": "BULLISH" if df_15m["close"].iloc[-1] > df_15m["close"].ewm(span=20).mean().iloc[-1] else "BEARISH",
                "1h": tech_eval.get("trend", "NEUTRAL"),
                "4h": "BULLISH" if df_4h["close"].iloc[-1] > df_4h["close"].ewm(span=50).mean().iloc[-1] else "BEARISH",
            }

            # 5. 7-Pillar Confluence Synthesis
            confluence = self.confluence_engine.evaluate_confluence(
                technical_data=tech_eval,
                structure_data=structure,
                orderbook_data=orderbook,
                derivatives_data=derivatives,
                onchain_data=onchain,
                macro_data=macro,
                sentiment_data=sentiment,
                news_data=news,
                quant_ml_data=ml_pred,
                regime_data=regime
            )

            # 6. Direction & Financial Risk Management
            score = confluence.get("master_confluence_score", 0.0)
            trade_direction = "LONG" if score >= 40 else ("SHORT" if score <= -40 else "NO_TRADE")

            risk_setup = self.risk_manager.calculate_trade_setup(
                direction=trade_direction,
                current_price=current_price,
                atr=tech_eval.get("atr", current_price * 0.015),
                structure_data=structure,
                account_equity=10000.0,
                risk_pct=1.0
            )

            thesis = ThesisEvaluator.evaluate_thesis(
                direction=trade_direction,
                current_price=current_price,
                structure_data=structure,
                derivatives_data=derivatives,
                macro_data=macro,
                news_data=news,
                regime_data=regime
            )

            # 7. Master Trading Decision
            decision = DecisionMaker.formulate_decision(
                confluence_payload=confluence,
                risk_payload=risk_setup,
                thesis_payload=thesis,
                regime_data=regime
            )

            elapsed_ms = round((time.time() - start_t) * 1000, 1)

            assessment = {
                "system": {
                    "name": APP_NAME,
                    "version": VERSION,
                    "execution_time_ms": elapsed_ms,
                    "timestamp": int(time.time() * 1000)
                },
                "ticker": ticker,
                "decision": decision,
                "confluence": confluence,
                "risk_management": risk_setup,
                "thesis": thesis,
                "technical": tech_eval,
                "market_structure": structure,
                "volume_volatility": vol_eval,
                "regime": regime,
                "anomalies": anomalies,
                "ml_intelligence": ml_pred,
                "monte_carlo": monte_carlo,
                "mtf_matrix": mtf_matrix,
                "derivatives": derivatives,
                "orderbook": orderbook,
                "onchain": onchain,
                "macro": macro,
                "sentiment": sentiment,
                "news": news
            }

            self.latest_assessment = assessment
            return assessment

        except Exception as e:
            logger.error(f"Pipeline update error: {e}", exc_info=True)
            return self.latest_assessment

    async def broadcast_live_update(self):
        """Broadcast live ticker and mini-decision update to all connected WebSocket clients."""
        if not self.active_connections or not self.latest_assessment:
            return

        payload = {
            "type": "LIVE_TICKER_UPDATE",
            "price": self.latest_assessment.get("ticker", {}).get("last_price", 0.0),
            "change_pct": self.latest_assessment.get("ticker", {}).get("price_change_percent", 0.0),
            "confluence_score": self.latest_assessment.get("confluence", {}).get("master_confluence_score", 0.0),
            "decision_badge": self.latest_assessment.get("decision", {}).get("badge_text", "🔴 NO TRADE"),
            "decision_class": self.latest_assessment.get("decision", {}).get("badge_class", "no-trade"),
            "conviction": self.latest_assessment.get("confluence", {}).get("conviction_pct", 0.0),
            "timestamp": int(time.time() * 1000)
        }

        disconnected = []
        for ws in self.active_connections:
            try:
                await ws.send_json(payload)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            if ws in self.active_connections:
                self.active_connections.remove(ws)


system_engine = IntelligenceSystem()

# Background Loop
async def background_intelligence_loop():
    logger.info("Starting background market intelligence loop...")
    while system_engine.is_running:
        try:
            await system_engine.update_pipeline()
            await system_engine.broadcast_live_update()
        except Exception as e:
            logger.warning(f"Background loop iteration error: {e}")
        await asyncio.sleep(4.0) # Refresh every 4 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    system_engine.is_running = True
    # Initial pipeline run
    await system_engine.update_pipeline()
    # Start background task
    bg_task = asyncio.create_task(background_intelligence_loop())
    yield
    # Shutdown
    system_engine.is_running = False
    bg_task.cancel()
    await system_engine.market_collector.close()
    await system_engine.derivatives_collector.close()
    await system_engine.orderbook_collector.close()
    await system_engine.onchain_collector.close()
    await system_engine.sentiment_collector.close()


app = FastAPI(title=APP_NAME, version=VERSION, lifespan=lifespan)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API Endpoints
@app.get("/api/status")
async def get_status():
    return {"status": "ONLINE", "version": VERSION, "timestamp": int(time.time() * 1000)}

@app.get("/api/overview")
async def get_market_overview():
    """Get complete multi-dimensional quantitative market intelligence report."""
    if not system_engine.latest_assessment:
        await system_engine.update_pipeline()
    return system_engine.latest_assessment

def clean_float(val: Any, fallback: float = 0.0) -> float:
    try:
        f = float(val)
        return fallback if (np.isnan(f) or np.isinf(f)) else round(f, 2)
    except Exception:
        return fallback

@app.get("/api/market/klines")
async def get_klines(
    timeframe: str = Query(DEFAULT_TIMEFRAME, enum=SUPPORTED_TIMEFRAMES),
    limit: int = Query(2000, ge=30, le=2500)
):
    """Get candlestick OHLCV data with technical indicators and order blocks (up to 7+ days depth)."""
    df = await system_engine.market_collector.get_klines(timeframe, limit)
    df_ind = TechnicalAnalyzer.calculate_indicators(df)
    structure = MarketStructureAnalyzer.analyze_structure(df_ind)

    # Format klines for Lightweight Charts with strict NaN sanitization
    candles = []
    for idx, row in df_ind.iterrows():
        close_val = clean_float(row["close"], 0.0)
        candles.append({
            "time": int(row["timestamp"] // 1000), # Unix seconds for Lightweight Charts
            "open": clean_float(row["open"], close_val),
            "high": clean_float(row["high"], close_val),
            "low": clean_float(row["low"], close_val),
            "close": close_val,
            "volume": clean_float(row["volume"], 0.0),
            "ema_9": clean_float(row.get("ema_9"), close_val),
            "ema_20": clean_float(row.get("ema_20"), close_val),
            "ema_21": clean_float(row.get("ema_20"), close_val),
            "ema_50": clean_float(row.get("ema_50"), close_val),
            "ema_200": clean_float(row.get("ema_200"), close_val),
            "bb_upper": clean_float(row.get("bb_upper"), close_val),
            "bb_lower": clean_float(row.get("bb_lower"), close_val),
            "supertrend": clean_float(row.get("supertrend"), close_val),
        })

    return {
        "symbol": system_engine.market_collector.symbol,
        "timeframe": timeframe,
        "candles": candles,
        "order_blocks": structure.get("order_blocks", []),
        "fair_value_gaps": structure.get("fair_value_gaps", []),
        "swing_highs": structure.get("swing_highs", []),
        "swing_lows": structure.get("swing_lows", []),
    }

@app.get("/api/derivatives")
async def get_derivatives():
    return await system_engine.derivatives_collector.get_derivatives_data()

@app.get("/api/market/orderbook")
async def get_orderbook():
    return await system_engine.orderbook_collector.get_orderbook_metrics()

@app.get("/api/onchain")
async def get_onchain():
    return await system_engine.onchain_collector.get_onchain_metrics()

@app.get("/api/macro")
async def get_macro():
    return await system_engine.macro_collector.get_macro_data()

@app.get("/api/sentiment")
async def get_sentiment():
    return await system_engine.sentiment_collector.get_sentiment_data()

@app.get("/api/news")
async def get_news(limit: int = Query(25, ge=5, le=50)):
    return await system_engine.news_collector.get_latest_news(limit)

@app.get("/api/quant/monte-carlo")
async def get_monte_carlo(horizon: int = Query(24, ge=6, le=72), sims: int = Query(1000, ge=100, le=5000)):
    ticker = await system_engine.market_collector.get_live_ticker()
    price = ticker.get("last_price", 64500.0)
    return StatisticalAnalyzer.run_monte_carlo_simulation(current_price=price, daily_volatility_pct=3.2, horizon_hours=horizon, num_simulations=sims)

@app.get("/api/quant/backtest")
async def get_backtest(initial_capital: float = Query(10000.0), risk_pct: float = Query(1.0)):
    df = await system_engine.market_collector.get_klines("1h", limit=500)
    return StrategyBacktester.run_backtest(df, initial_capital=initial_capital, risk_per_trade_pct=risk_pct)

class RiskCalculationRequest(BaseModel):
    account_equity: float = 10000.0
    risk_percentage: float = 1.0
    direction: str = "LONG"
    custom_entry: Optional[float] = None
    custom_sl: Optional[float] = None
    custom_tp: Optional[float] = None

@app.post("/api/risk/calculate")
async def calculate_risk(req: RiskCalculationRequest):
    ticker = await system_engine.market_collector.get_live_ticker()
    curr_price = req.custom_entry or ticker.get("last_price", 64500.0)
    
    df = await system_engine.market_collector.get_klines("1h", limit=100)
    df_ind = TechnicalAnalyzer.calculate_indicators(df)
    structure = MarketStructureAnalyzer.analyze_structure(df_ind)
    atr = df_ind["atr_14"].iloc[-1] if "atr_14" in df_ind else curr_price * 0.015

    setup = system_engine.risk_manager.calculate_trade_setup(
        direction=req.direction,
        current_price=curr_price,
        atr=atr,
        structure_data=structure,
        account_equity=req.account_equity,
        risk_pct=req.risk_percentage
    )

    # If custom stop-loss or take-profit provided, recalculate
    if req.custom_sl and req.custom_sl > 0:
        setup["stop_loss"] = req.custom_sl
        risk_dist = abs(curr_price - req.custom_sl)
        setup["stop_loss_distance_usd"] = round(risk_dist, 2)
        setup["stop_loss_distance_pct"] = round((risk_dist / curr_price) * 100, 2)
        risk_usd = req.account_equity * (req.risk_percentage / 100.0)
        pos_btc = risk_usd / risk_dist if risk_dist > 0 else 0.01
        setup["position_sizing"]["position_size_btc"] = round(pos_btc, 4)
        setup["position_sizing"]["position_notional_usd"] = round(pos_btc * curr_price, 2)
        setup["position_sizing"]["effective_leverage"] = round((pos_btc * curr_price) / req.account_equity, 2)

    return setup

# WebSocket Streaming Endpoint
@app.websocket("/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    await websocket.accept()
    system_engine.active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(system_engine.active_connections)}")
    try:
        # Send initial snapshot immediately
        if system_engine.latest_assessment:
            await websocket.send_json({
                "type": "INITIAL_SNAPSHOT",
                "data": system_engine.latest_assessment
            })
        while True:
            # Keep connection alive & handle incoming client messages if any
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if websocket in system_engine.active_connections:
            system_engine.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        if websocket in system_engine.active_connections:
            system_engine.active_connections.remove(websocket)


# Mount Static Frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Health Check Endpoints (Render, Docker, Kubernetes)
@app.get("/healthz")
@app.get("/health")
@app.get("/api/status")
async def health_check():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": VERSION,
        "active_clients": len(system_engine.active_connections),
        "engine_running": system_engine.is_running
    }

# Mount Songs Folder
songs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "songs_trade")
os.makedirs(songs_dir, exist_ok=True)
app.mount("/songs_trade", StaticFiles(directory=songs_dir), name="songs_trade")

# Songs Playlist API
@app.get("/api/songs")
async def get_trading_songs():
    """Scan the 'songs_trade' folder for audio files."""
    import urllib.parse
    import re
    supported_exts = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".mp4"}
    songs_list = []
    
    if os.path.exists(songs_dir):
        for fname in sorted(os.listdir(songs_dir)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in supported_exts:
                fpath = os.path.join(songs_dir, fname)
                size_mb = round(os.path.getsize(fpath) / (1024 * 1024), 2)
                raw_title = os.path.splitext(fname)[0]
                # Clean up title for elegant UI display
                clean_title = re.sub(r'[\(\[\{].*?[\)\]\}]', '', raw_title)
                clean_title = clean_title.replace("｜", " - ").replace("：", ": ").replace("_", " ").strip()
                clean_title = re.sub(r'\s+', ' ', clean_title)
                encoded_name = urllib.parse.quote(fname)
                songs_list.append({
                    "filename": fname,
                    "title": clean_title or raw_title,
                    "url": f"/songs_trade/{encoded_name}",
                    "size_mb": size_mb
                })
    
    return {
        "folder": "songs_trade",
        "total_songs": len(songs_list),
        "songs": songs_list,
        "message": "Songs ready to play" if songs_list else "Folder 'songs_trade' is empty. Drop your .mp3 or .wav files into songs_trade/ to load custom music."
    }

# Trade Book & Excel Export Endpoints
@app.get("/api/trades/download-excel")
@app.get("/api/trades/export-excel")
async def download_trade_book_excel():
    """Export and download the Excel trade journal with beginner explanations and post-mortem analysis."""
    from app.services.trade_book import trade_book_service
    excel_path = trade_book_service.export_to_excel()
    if os.path.exists(excel_path):
        return FileResponse(
            excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="Bitcoin_AI_Trade_Book.xlsx"
        )
    raise HTTPException(status_code=404, detail="Trade book Excel file could not be generated.")

@app.get("/api/trades/journal")
async def get_trade_journal():
    """Get complete trade journal, non-trader analysis, post-mortems, and performance stats."""
    from app.services.trade_book import trade_book_service
    return {
        "trades": trade_book_service.trades,
        "stats": trade_book_service.get_performance_metrics()
    }

@app.get("/api/trades/analysis")
@app.get("/api/trades/analyst-report")
async def get_professional_trade_analysis():
    """Get executive-level Data Science & Quantitative Portfolio Analysis report for executed trades."""
    from app.services.trade_book import trade_book_service
    from app.services.trade_analyst import trade_analyst_service
    return trade_analyst_service.generate_professional_analysis(trade_book_service.trades)


# 5-Minute Scalp Endpoints
@app.get("/api/scalp/overview")
async def get_scalp_overview():
    """Get active 5-minute trade, timer countdown, and performance stats."""
    return await system_engine.scalp_engine.evaluate_5m_scalp()

@app.get("/api/scalp/history")
async def get_scalp_history():
    """Get recent 5-minute scalp trades stream."""
    return {
        "history": system_engine.scalp_engine.trade_book.trades,
        "stats": system_engine.scalp_engine.trade_book.get_performance_metrics()
    }

@app.post("/api/scalp/force-generate")
async def force_generate_scalp():
    """Force instant generation of a fresh 5-minute scalp setup."""
    system_engine.scalp_engine.last_signal_time = 0
    return await system_engine.scalp_engine.evaluate_5m_scalp()

@app.get("/scalp")
@app.get("/5m")
@app.get("/")
async def serve_unified_page():
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"status": "Frontend loading...", "api_docs": "/docs"})

