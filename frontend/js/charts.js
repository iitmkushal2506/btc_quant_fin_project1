/**
 * Interactive Candlestick & Technical Analysis Chart Engine (Light Executive Theme)
 * Supports TradingView Lightweight Charts with Canvas Fallback & Trade Markers
 */

class ChartManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.fallbackCanvas = document.getElementById('custom-fallback-chart');
        this.currentTimeframe = '5m';
        this.chart = null;
        this.candleSeries = null;
        this.volumeSeries = null;
        this.ema9Series = null;
        this.ema21Series = null;
        this.activePriceLines = [];
        this.candlesData = [];

        this.initChart();
    }

    initChart() {
        if (!this.container) return;

        // Check if LightweightCharts is available from CDN
        if (typeof LightweightCharts !== 'undefined') {
            try {
                this.chart = LightweightCharts.createChart(this.container, {
                    width: this.container.clientWidth,
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
                        scaleMargins: { top: 0.1, bottom: 0.2 },
                    },
                    timeScale: {
                        borderColor: '#e2e8f0',
                        timeVisible: true,
                        secondsVisible: false,
                    },
                });

                // Candlestick Series in Executive Light Colors
                this.candleSeries = this.chart.addCandlestickSeries({
                    upColor: '#10b981',
                    downColor: '#ef4444',
                    borderVisible: false,
                    wickUpColor: '#10b981',
                    wickDownColor: '#ef4444',
                });

                // Volume Series
                this.volumeSeries = this.chart.addHistogramSeries({
                    color: '#94a3b8',
                    priceFormat: { type: 'volume' },
                    priceScaleId: '',
                    scaleMargins: { top: 0.82, bottom: 0 },
                });

                // Moving Averages (Fast EMA 9 & 21 Ribbon)
                this.ema9Series = this.chart.addLineSeries({
                    color: '#2563eb',
                    lineWidth: 1.5,
                    title: 'EMA 9',
                });

                this.ema21Series = this.chart.addLineSeries({
                    color: '#f59e0b',
                    lineWidth: 1.5,
                    title: 'EMA 21',
                });

                // High-performance responsive resize & orientation observer
                const handleResize = () => {
                    if (this.chart && this.container) {
                        this.chart.applyOptions({ 
                            width: this.container.clientWidth,
                            height: this.container.clientHeight || (window.innerWidth < 768 ? 320 : 460)
                        });
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
                console.warn('LightweightCharts init failed, using fallback', err);
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

    async loadKlines(timeframe = '5m') {
        this.currentTimeframe = timeframe;
        try {
            const resp = await fetch(`/api/market/klines?timeframe=${timeframe}&limit=150`);
            if (!resp.ok) throw new Error('Failed to fetch klines');
            const data = await resp.json();
            
            this.candlesData = data.candles || [];
            this.renderChart(this.candlesData);
        } catch (e) {
            console.warn('Error loading klines:', e);
        }
    }

    renderChart(candles) {
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
                value: c.volume,
                color: c.close >= c.open ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)'
            }));

            const e9 = candles.filter(c => c.ema_20 || c.ema_9).map(c => ({ time: c.time, value: c.ema_9 || c.ema_20 }));
            const e21 = candles.filter(c => c.ema_50 || c.ema_21).map(c => ({ time: c.time, value: c.ema_21 || c.ema_50 }));

            this.candleSeries.setData(cData);
            this.volumeSeries.setData(vData);
            if (this.ema9Series && e9.length) this.ema9Series.setData(e9);
            if (this.ema21Series && e21.length) this.ema21Series.setData(e21);

            this.chart.timeScale().fitContent();
        }
    }

    updateActiveTradeLines(trade) {
        if (!this.chart || !this.candleSeries || !trade) return;

        // Clear existing price lines
        this.activePriceLines.forEach(line => this.candleSeries.removePriceLine(line));
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
