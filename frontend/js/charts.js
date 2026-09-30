/**
 * Interactive Candlestick & Technical Analysis Chart Engine
 * Supports TradingView Lightweight Charts with Real-Time Price Streaming,
 * Multi-Day Historical Depth (7+ Days), EMA 9/21 Ribbons, and Dynamic Trade Execution Overlays.
 */

class ChartManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentTimeframe = '5m';
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.ema9Series = null;
        this.ema21Series = null;
        this.activePriceLines = [];
        this.candlesData = [];
        this.lastBar = null;
        this.lastVolume = 0;
        this.isLoading = false;

        this.initChart();
    }

    getTimeframeSeconds(tf) {
        switch (tf) {
            case '1m': return 60;
            case '5m': return 300;
            case '15m': return 900;
            case '1h': return 3600;
            case '4h': return 14400;
            case '1d': return 86400;
            default: return 300;
        }
    }

    getTimeframeCandleLimit(tf) {
        switch (tf) {
            case '1m': return 2000; // ~33.3 hours
            case '5m': return 2016; // Exactly 7.00 full days
            case '15m': return 1000; // 10.4 days
            case '1h': return 1000; // 41.6 days
            case '4h': return 1000; // 166.6 days
            case '1d': return 1000; // 1000 days
            default: return 2016;
        }
    }

    initChart() {
        if (!this.container) return;

        // Check if LightweightCharts is available from CDN
        if (typeof LightweightCharts !== 'undefined') {
            try {
                this.chart = LightweightCharts.createChart(this.container, {
                    width: this.container.clientWidth || 800,
                    height: this.container.clientHeight || 460,
                    layout: {
                        background: { color: '#ffffff' },
                        textColor: '#475569',
                        fontFamily: "'JetBrains Mono', monospace",
                    },
                    grid: {
                        vertLines: { color: '#f1f5f9' },
                        horzLines: { color: '#f1f5f9' },
                    },
                    crosshair: {
                        mode: LightweightCharts.CrosshairMode.Normal,
                    },
                    rightPriceScale: {
                        borderColor: '#e2e8f0',
                        scaleMargins: { top: 0.08, bottom: 0.18 },
                        autoScale: true,
                    },
                    timeScale: {
                        borderColor: '#e2e8f0',
                        timeVisible: true,
                        secondsVisible: false,
                        fixLeftEdge: false,
                        rightOffset: 5,
                        barSpacing: 6,
                        minBarSpacing: 2,
                    },
                });

                // Candlestick Series
                this.candleSeries = this.chart.addCandlestickSeries({
                    upColor: '#10b981',
                    downColor: '#ef4444',
                    borderVisible: false,
                    wickUpColor: '#10b981',
                    wickDownColor: '#ef4444',
                    priceLineVisible: true,
                    priceLineWidth: 1,
                    priceLineColor: '#2563eb',
                    priceLineStyle: LightweightCharts.LineStyle.Dotted,
                    priceFormat: {
                        type: 'price',
                        precision: 2,
                        minMove: 0.01,
                    },
                });

                // Volume Series (Bottom Sub-Scale)
                this.volumeSeries = this.chart.addHistogramSeries({
                    color: '#94a3b8',
                    priceFormat: { type: 'volume' },
                    priceScaleId: '',
                    scaleMargins: { top: 0.82, bottom: 0 },
                });

                // Fast EMA 9 (Blue) & EMA 21 (Amber) Moving Averages
                this.ema9Series = this.chart.addLineSeries({
                    color: '#2563eb',
                    lineWidth: 1.5,
                    title: 'EMA 9',
                    priceLineVisible: false,
                });

                this.ema21Series = this.chart.addLineSeries({
                    color: '#f59e0b',
                    lineWidth: 1.5,
                    title: 'EMA 21',
                    priceLineVisible: false,
                });

                // High-performance responsive resize & orientation observer
                const handleResize = () => {
                    if (this.chart && this.container) {
                        const newWidth = this.container.clientWidth;
                        const newHeight = this.container.clientHeight || (window.innerWidth < 768 ? 340 : 460);
                        if (newWidth > 0) {
                            this.chart.applyOptions({ width: newWidth, height: newHeight });
                        }
                    }
                };

                window.addEventListener('resize', handleResize);
                window.addEventListener('orientationchange', handleResize);

                if (window.ResizeObserver && this.container) {
                    const ro = new ResizeObserver(() => handleResize());
                    ro.observe(this.container);
                }

                return;
            } catch (err) {
                console.warn('LightweightCharts init error:', err);
            }
        }
    }

    setTheme(theme) {
        if (!this.chart) return;
        const isDark = theme === 'dark';
        this.chart.applyOptions({
            layout: {
                background: { color: isDark ? '#0e1526' : '#ffffff' },
                textColor: isDark ? '#94a3b8' : '#475569',
            },
            grid: {
                vertLines: { color: isDark ? '#1e293b' : '#f1f5f9' },
                horzLines: { color: isDark ? '#1e293b' : '#f1f5f9' },
            },
            rightPriceScale: {
                borderColor: isDark ? '#1e293b' : '#e2e8f0',
            },
            timeScale: {
                borderColor: isDark ? '#1e293b' : '#e2e8f0',
            }
        });
    }

    /**
     * Fetch complete historical candlestick series (up to 7+ days)
     */
    async loadKlines(timeframe = '5m', isInitial = true) {
        this.currentTimeframe = timeframe;
        this.isLoading = true;
        try {
            const limit = this.getTimeframeCandleLimit(timeframe);
            const resp = await fetch(`/api/market/klines?timeframe=${timeframe}&limit=${limit}`);
            if (!resp.ok) throw new Error(`Failed to fetch klines: HTTP ${resp.status}`);
            const data = await resp.json();
            
            this.candlesData = data.candles || [];
            this.renderChart(this.candlesData, isInitial);
        } catch (e) {
            console.warn('Error loading klines:', e);
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Silent background sync to refresh closed candles and indicators without resetting user view
     */
    async syncKlines() {
        if (this.isLoading) return;
        try {
            const limit = this.getTimeframeCandleLimit(this.currentTimeframe);
            const resp = await fetch(`/api/market/klines?timeframe=${this.currentTimeframe}&limit=${limit}`);
            if (!resp.ok) return;
            const data = await resp.json();
            
            if (data.candles && data.candles.length > 0) {
                this.candlesData = data.candles;
                this.renderChart(this.candlesData, false); // false = keep current scroll position
            }
        } catch (e) {
            console.debug('Silent kline sync error:', e);
        }
    }

    renderChart(candles, fitContent = true) {
        if (!candles || candles.length === 0) return;

        if (this.chart && this.candleSeries) {
            const cData = candles.map(c => ({
                time: c.time,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close
            }));

            const vData = candles.map(c => ({
                time: c.time,
                value: c.volume || 0,
                color: c.close >= c.open ? 'rgba(16, 185, 129, 0.28)' : 'rgba(239, 68, 68, 0.28)'
            }));

            const e9 = candles.filter(c => c.ema_9 !== undefined && c.ema_9 > 0).map(c => ({ time: c.time, value: c.ema_9 }));
            const e21 = candles.filter(c => (c.ema_21 || c.ema_20) !== undefined && (c.ema_21 || c.ema_20) > 0).map(c => ({ time: c.time, value: c.ema_21 || c.ema_20 }));

            this.candleSeries.setData(cData);
            if (this.volumeSeries) this.volumeSeries.setData(vData);
            if (this.ema9Series && e9.length) this.ema9Series.setData(e9);
            if (this.ema21Series && e21.length) this.ema21Series.setData(e21);

            // Record the active latest candle for live real-time tick streaming
            if (cData.length > 0) {
                const latest = cData[cData.length - 1];
                this.lastBar = { ...latest, volume: vData[vData.length - 1]?.value || 0 };
            }

            if (fitContent) {
                // Focus on the recent candles while allowing full 7-day scroll back
                const totalCandles = cData.length;
                if (totalCandles > 120) {
                    const fromIdx = Math.max(0, totalCandles - 120);
                    this.chart.timeScale().setVisibleLogicalRange({
                        from: fromIdx,
                        to: totalCandles + 5,
                    });
                } else {
                    this.chart.timeScale().fitContent();
                }
            }
        }
    }

    /**
     * Real-time intra-candle live tick updater.
     * Updates the currently open candle or initiates a new one instantly as prices arrive.
     */
    updateLiveTick(price, volumeDelta = 0) {
        if (!price || isNaN(price) || !this.candleSeries) return;

        const intervalSec = this.getTimeframeSeconds(this.currentTimeframe);
        const nowSec = Math.floor(Date.now() / 1000);
        const currentBarTime = Math.floor(nowSec / intervalSec) * intervalSec;

        if (this.lastBar) {
            if (currentBarTime === this.lastBar.time) {
                // Modify existing active candle
                this.lastBar.high = Math.max(this.lastBar.high, price);
                this.lastBar.low = Math.min(this.lastBar.low, price);
                this.lastBar.close = price;
                if (volumeDelta > 0) {
                    this.lastBar.volume = (this.lastBar.volume || 0) + volumeDelta;
                }

                this.candleSeries.update({
                    time: this.lastBar.time,
                    open: this.lastBar.open,
                    high: this.lastBar.high,
                    low: this.lastBar.low,
                    close: this.lastBar.close
                });

                if (this.volumeSeries) {
                    this.volumeSeries.update({
                        time: this.lastBar.time,
                        value: this.lastBar.volume || 10,
                        color: this.lastBar.close >= this.lastBar.open ? 'rgba(16, 185, 129, 0.28)' : 'rgba(239, 68, 68, 0.28)'
                    });
                }
            } else if (currentBarTime > this.lastBar.time) {
                // New candle period started
                this.lastBar = {
                    time: currentBarTime,
                    open: price,
                    high: price,
                    low: price,
                    close: price,
                    volume: volumeDelta || 10
                };

                this.candleSeries.update(this.lastBar);

                if (this.volumeSeries) {
                    this.volumeSeries.update({
                        time: this.lastBar.time,
                        value: this.lastBar.volume,
                        color: 'rgba(16, 185, 129, 0.28)'
                    });
                }
            }
        }
    }

    /**
     * Overlay active trade levels (Entry, Stop Loss, Take Profit) directly on the chart.
     */
    updateActiveTradeLines(trade) {
        if (!this.chart || !this.candleSeries || !trade) return;

        // Clear existing price lines
        this.activePriceLines.forEach(line => {
            try { this.candleSeries.removePriceLine(line); } catch (e) {}
        });
        this.activePriceLines = [];

        const entry = trade.entry_price;
        const sl = trade.stop_loss;
        const tp1 = trade.target_1;

        if (entry) {
            const entryLine = this.candleSeries.createPriceLine({
                price: entry,
                color: '#2563eb',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dotted,
                axisLabelVisible: true,
                title: `ENTRY: $${entry.toLocaleString()}`,
            });
            this.activePriceLines.push(entryLine);
        }

        if (sl) {
            const slLine = this.candleSeries.createPriceLine({
                price: sl,
                color: '#ef4444',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: `STOP: $${sl.toLocaleString()}`,
            });
            this.activePriceLines.push(slLine);
        }

        if (tp1) {
            const tpLine = this.candleSeries.createPriceLine({
                price: tp1,
                color: '#10b981',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: `TP1: $${tp1.toLocaleString()}`,
            });
            this.activePriceLines.push(tpLine);
        }
    }
}
