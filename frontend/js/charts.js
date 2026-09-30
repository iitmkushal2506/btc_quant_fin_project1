/**
 * TradingView Professional Candlestick & Technical Analysis Chart Engine
 * Features:
 * - Authentic TradingView Pine Green (#089981) & Crisp Red (#F23645) Palette
 * - Multi-Day Depth (7+ Days) with Instant Sub-Second Real-Time Candle Tick Streaming
 * - Interactive Chart Types (Candles, Line, Area Mountain)
 * - Multi-Timezone Formatter (UTC / GMT & Indian Standard Time IST)
 * - Dynamic Floating OHLCV Crosshair Legend
 * - Fast EMA 9 / 21 Moving Average Ribbons & Volume Sub-Scale
 * - Responsive Resize, Zoom Reset & Fullscreen Mode
 */

class ChartManager {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.cardElement = this.container ? this.container.closest('.tv-chart-card') : null;
        this.currentTimeframe = '5m';
        this.chartType = 'candle'; // 'candle' | 'line' | 'area'
        this.currentTimezone = 'UTC'; // 'UTC' | 'IST'
        this.currentTheme = localStorage.getItem('btc_quant_theme') || 'light';
        
        this.chart = null;
        this.candleSeries = null;
        this.lineSeries = null;
        this.areaSeries = null;
        this.volumeSeries = null;
        this.ema9Series = null;
        this.ema21Series = null;
        
        this.activePriceLines = [];
        this.candlesData = [];
        this.lastBar = null;
        this.isLoading = false;
        
        this.indicatorsVisible = {
            ema9: true,
            ema21: true,
            vol: true
        };

        this.initChart();
        this.bindToolbarEvents();
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
            case '1m': return 2000;
            case '5m': return 2016; // 7.00 full days
            case '15m': return 1000;
            case '1h': return 1000;
            case '4h': return 1000;
            case '1d': return 1000;
            default: return 2016;
        }
    }

    initChart() {
        if (!this.container || typeof LightweightCharts === 'undefined') return;

        try {
            const isDark = this.currentTheme === 'dark';
            const width = this.container.clientWidth || 800;
            const height = this.container.clientHeight || 480;

            this.chart = LightweightCharts.createChart(this.container, {
                width: width,
                height: height,
                layout: {
                    background: { color: isDark ? '#131722' : '#ffffff' },
                    textColor: '#787b86',
                    fontFamily: "'JetBrains Mono', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace",
                    fontSize: 11,
                },
                grid: {
                    vertLines: { color: isDark ? '#1e222d' : '#f0f3fa' },
                    horzLines: { color: isDark ? '#1e222d' : '#f0f3fa' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                    vertLine: {
                        color: '#758696',
                        width: 1,
                        style: LightweightCharts.LineStyle.Dashed,
                        labelBackgroundColor: '#2962ff',
                    },
                    horzLine: {
                        color: '#758696',
                        width: 1,
                        style: LightweightCharts.LineStyle.Dashed,
                        labelBackgroundColor: '#2962ff',
                    },
                },
                rightPriceScale: {
                    borderColor: isDark ? '#2a2e39' : '#e0e3eb',
                    scaleMargins: { top: 0.08, bottom: 0.20 },
                    autoScale: true,
                    alignLabels: true,
                    borderVisible: true,
                },
                timeScale: {
                    borderColor: isDark ? '#2a2e39' : '#e0e3eb',
                    timeVisible: true,
                    secondsVisible: false,
                    fixLeftEdge: false,
                    rightOffset: 6,
                    barSpacing: 9,
                    minBarSpacing: 3,
                    borderVisible: true,
                },
                handleScroll: {
                    mouseWheel: true,
                    pressedMouseMove: true,
                    horzTouchDrag: true,
                    vertTouchDrag: false,
                },
                handleScale: {
                    axisPressedMouseMove: true,
                    mouseWheel: true,
                    pinch: true,
                },
            });

            // 1. Candlestick Series (TradingView Colors)
            this.candleSeries = this.chart.addCandlestickSeries({
                upColor: '#089981',
                downColor: '#F23645',
                wickUpColor: '#089981',
                wickDownColor: '#F23645',
                borderUpColor: '#089981',
                borderDownColor: '#F23645',
                borderVisible: true,
                priceLineVisible: true,
                priceLineWidth: 1,
                priceLineColor: '#2962ff',
                priceLineStyle: LightweightCharts.LineStyle.Dotted,
            });

            // 2. Line Series (for Line view toggle)
            this.lineSeries = this.chart.addLineSeries({
                color: '#2962ff',
                lineWidth: 2,
                visible: false,
                priceLineVisible: true,
            });

            // 3. Area Series (for Area view toggle)
            this.areaSeries = this.chart.addAreaSeries({
                topColor: 'rgba(41, 98, 255, 0.40)',
                bottomColor: 'rgba(41, 98, 255, 0.02)',
                lineColor: '#2962ff',
                lineWidth: 2,
                visible: false,
                priceLineVisible: true,
            });

            // 4. Volume Sub-Scale (Bottom 15% Sub-Pane)
            this.volumeSeries = this.chart.addHistogramSeries({
                priceFormat: { type: 'volume' },
                priceScaleId: '',
                scaleMargins: { top: 0.84, bottom: 0 },
            });

            // 5. EMA 9 Moving Average (TradingView Blue)
            this.ema9Series = this.chart.addLineSeries({
                color: '#2962ff',
                lineWidth: 1.5,
                title: 'EMA 9',
                priceLineVisible: false,
                lastValueVisible: false,
            });

            // 6. EMA 21 Moving Average (TradingView Amber)
            this.ema21Series = this.chart.addLineSeries({
                color: '#ff6d00',
                lineWidth: 1.5,
                title: 'EMA 21',
                priceLineVisible: false,
                lastValueVisible: false,
            });

            // Crosshair move listener for interactive Legend Bar
            this.chart.subscribeCrosshairMove(param => this.handleCrosshairMove(param));

            // Responsive Window & Container Resize Observer
            const handleResize = () => {
                if (this.chart && this.container) {
                    const w = this.container.clientWidth;
                    const isFs = this.cardElement && this.cardElement.classList.contains('fullscreen');
                    const h = isFs ? window.innerHeight - 85 : (this.container.clientHeight || 480);
                    if (w > 0 && h > 0) {
                        this.chart.applyOptions({ width: w, height: h });
                    }
                }
            };

            window.addEventListener('resize', handleResize);
            window.addEventListener('orientationchange', handleResize);
            if (window.ResizeObserver && this.container) {
                const ro = new ResizeObserver(() => handleResize());
                ro.observe(this.container);
            }

        } catch (err) {
            console.error('TradingView chart initialization failed:', err);
        }
    }

    bindToolbarEvents() {
        // Timeframe selector buttons
        document.querySelectorAll('.tf-selector button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tf-selector button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const tf = btn.getAttribute('data-tf');
                const legTf = document.getElementById('leg-tf');
                if (legTf) legTf.textContent = tf;
                this.loadKlines(tf, true);
            });
        });

        // Chart Type Switcher
        const candleBtn = document.getElementById('tv-type-candle');
        const lineBtn = document.getElementById('tv-type-line');
        const areaBtn = document.getElementById('tv-type-area');

        const setType = (type, activeBtn) => {
            document.querySelectorAll('.tv-type-btn').forEach(b => b.classList.remove('active'));
            if (activeBtn) activeBtn.classList.add('active');
            this.setChartType(type);
        };

        if (candleBtn) candleBtn.addEventListener('click', () => setType('candle', candleBtn));
        if (lineBtn) lineBtn.addEventListener('click', () => setType('line', lineBtn));
        if (areaBtn) areaBtn.addEventListener('click', () => setType('area', areaBtn));

        // Indicator Visibility Toggles
        const tEma9 = document.getElementById('toggle-ema9-btn');
        const tEma21 = document.getElementById('toggle-ema21-btn');
        const tVol = document.getElementById('toggle-vol-btn');

        if (tEma9) {
            tEma9.addEventListener('click', () => {
                this.indicatorsVisible.ema9 = !this.indicatorsVisible.ema9;
                tEma9.classList.toggle('active', this.indicatorsVisible.ema9);
                if (this.ema9Series) this.ema9Series.applyOptions({ visible: this.indicatorsVisible.ema9 });
                const legBox = document.getElementById('leg-ema9-box');
                if (legBox) legBox.style.display = this.indicatorsVisible.ema9 ? 'flex' : 'none';
            });
        }

        if (tEma21) {
            tEma21.addEventListener('click', () => {
                this.indicatorsVisible.ema21 = !this.indicatorsVisible.ema21;
                tEma21.classList.toggle('active', this.indicatorsVisible.ema21);
                if (this.ema21Series) this.ema21Series.applyOptions({ visible: this.indicatorsVisible.ema21 });
                const legBox = document.getElementById('leg-ema21-box');
                if (legBox) legBox.style.display = this.indicatorsVisible.ema21 ? 'flex' : 'none';
            });
        }

        if (tVol) {
            tVol.addEventListener('click', () => {
                this.indicatorsVisible.vol = !this.indicatorsVisible.vol;
                tVol.classList.toggle('active', this.indicatorsVisible.vol);
                if (this.volumeSeries) this.volumeSeries.applyOptions({ visible: this.indicatorsVisible.vol });
            });
        }

        // Timezone Toggle Buttons (UTC vs IST)
        const btnUtc = document.getElementById('tv-tz-utc');
        const btnIst = document.getElementById('tv-tz-ist');

        if (btnUtc && btnIst) {
            btnUtc.addEventListener('click', () => {
                btnUtc.classList.add('active');
                btnIst.classList.remove('active');
                this.setTimezone('UTC');
            });

            btnIst.addEventListener('click', () => {
                btnIst.classList.add('active');
                btnUtc.classList.remove('active');
                this.setTimezone('IST');
            });
        }

        // Reset View / Fit Button
        const fitBtn = document.getElementById('tv-fit-btn');
        if (fitBtn) {
            fitBtn.addEventListener('click', () => this.fitRecentView());
        }

        // Fullscreen Toggle Button
        const fsBtn = document.getElementById('tv-fullscreen-btn');
        if (fsBtn && this.cardElement) {
            fsBtn.addEventListener('click', () => {
                this.cardElement.classList.toggle('fullscreen');
                const isFs = this.cardElement.classList.contains('fullscreen');
                fsBtn.textContent = isFs ? '✖' : '⛶';
                setTimeout(() => {
                    if (this.chart && this.container) {
                        const h = isFs ? window.innerHeight - 85 : 480;
                        this.chart.applyOptions({ width: this.container.clientWidth, height: h });
                        this.chart.timeScale().fitContent();
                    }
                }, 100);
            });
        }
    }

    setChartType(type) {
        this.chartType = type;
        if (!this.candleSeries || !this.lineSeries || !this.areaSeries) return;

        this.candleSeries.applyOptions({ visible: type === 'candle' });
        this.lineSeries.applyOptions({ visible: type === 'line' });
        this.areaSeries.applyOptions({ visible: type === 'area' });
    }

    setTimezone(tz) {
        if (this.currentTimezone === tz) return;
        this.currentTimezone = tz;
        // Re-render chart with timezone timestamp adjustment
        if (this.candlesData && this.candlesData.length > 0) {
            this.renderChart(this.candlesData, false);
        }
    }

    setTheme(theme) {
        this.currentTheme = theme;
        if (!this.chart) return;
        const isDark = theme === 'dark';
        this.chart.applyOptions({
            layout: {
                background: { color: isDark ? '#131722' : '#ffffff' },
                textColor: '#787b86',
            },
            grid: {
                vertLines: { color: isDark ? '#1e222d' : '#f0f3fa' },
                horzLines: { color: isDark ? '#1e222d' : '#f0f3fa' },
            },
            rightPriceScale: {
                borderColor: isDark ? '#2a2e39' : '#e0e3eb',
            },
            timeScale: {
                borderColor: isDark ? '#2a2e39' : '#e0e3eb',
            }
        });
    }

    /**
     * Load historical candles (7+ days depth)
     */
    async loadKlines(timeframe = '5m', isInitial = true) {
        this.currentTimeframe = timeframe;
        this.isLoading = true;
        try {
            const limit = this.getTimeframeCandleLimit(timeframe);
            const resp = await fetch(`/api/market/klines?timeframe=${timeframe}&limit=${limit}`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            
            this.candlesData = data.candles || [];
            this.renderChart(this.candlesData, isInitial);
            this.updateLegendFromLastBar();
        } catch (e) {
            console.warn('Error loading klines:', e);
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Silent background sync without resetting pan/zoom
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
                this.renderChart(this.candlesData, false);
            }
        } catch (e) {
            console.debug('Silent klines sync:', e);
        }
    }

    renderChart(candles, fitContent = true) {
        if (!candles || candles.length === 0 || !this.chart) return;

        // Apply timezone offset: IST is UTC+5:30 (+19,800 seconds)
        const tzOffset = this.currentTimezone === 'IST' ? 19800 : 0;

        const cData = candles.map(c => ({
            time: c.time + tzOffset,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close
        }));

        const lData = candles.map(c => ({
            time: c.time + tzOffset,
            value: c.close
        }));

        const vData = candles.map(c => ({
            time: c.time + tzOffset,
            value: c.volume || 0,
            color: c.close >= c.open ? 'rgba(8, 153, 129, 0.40)' : 'rgba(242, 54, 69, 0.40)'
        }));

        const e9 = candles.filter(c => c.ema_9 !== undefined && c.ema_9 > 0).map(c => ({
            time: c.time + tzOffset,
            value: c.ema_9
        }));

        const e21 = candles.filter(c => (c.ema_21 || c.ema_20) !== undefined && (c.ema_21 || c.ema_20) > 0).map(c => ({
            time: c.time + tzOffset,
            value: c.ema_21 || c.ema_20
        }));

        // Push data to all series
        if (this.candleSeries) this.candleSeries.setData(cData);
        if (this.lineSeries) this.lineSeries.setData(lData);
        if (this.areaSeries) this.areaSeries.setData(lData);
        if (this.volumeSeries) this.volumeSeries.setData(vData);
        if (this.ema9Series && e9.length) this.ema9Series.setData(e9);
        if (this.ema21Series && e21.length) this.ema21Series.setData(e21);

        if (cData.length > 0) {
            const rawLatest = candles[candles.length - 1];
            this.lastBar = {
                time: cData[cData.length - 1].time,
                rawTime: rawLatest.time,
                open: rawLatest.open,
                high: rawLatest.high,
                low: rawLatest.low,
                close: rawLatest.close,
                volume: rawLatest.volume || 0,
                ema9: rawLatest.ema_9 || 0,
                ema21: rawLatest.ema_21 || rawLatest.ema_20 || 0
            };
        }

        if (fitContent) {
            this.fitRecentView();
        }
    }

    fitRecentView() {
        if (!this.chart || !this.candlesData || this.candlesData.length === 0) return;
        const total = this.candlesData.length;
        if (total > 120) {
            this.chart.timeScale().setVisibleLogicalRange({
                from: total - 120,
                to: total + 6,
            });
        } else {
            this.chart.timeScale().fitContent();
        }
    }

    /**
     * Real-time intra-bar tick streaming.
     */
    updateLiveTick(price, volumeDelta = 0) {
        if (!price || isNaN(price) || !this.candleSeries) return;

        const intervalSec = this.getTimeframeSeconds(this.currentTimeframe);
        const nowSec = Math.floor(Date.now() / 1000);
        const rawBarTime = Math.floor(nowSec / intervalSec) * intervalSec;
        const tzOffset = this.currentTimezone === 'IST' ? 19800 : 0;
        const displayBarTime = rawBarTime + tzOffset;

        if (this.lastBar) {
            if (rawBarTime === this.lastBar.rawTime) {
                // Update existing active candle
                this.lastBar.high = Math.max(this.lastBar.high, price);
                this.lastBar.low = Math.min(this.lastBar.low, price);
                this.lastBar.close = price;
                if (volumeDelta > 0) {
                    this.lastBar.volume += volumeDelta;
                }

                const barPayload = {
                    time: displayBarTime,
                    open: this.lastBar.open,
                    high: this.lastBar.high,
                    low: this.lastBar.low,
                    close: this.lastBar.close
                };

                this.candleSeries.update(barPayload);
                if (this.lineSeries) this.lineSeries.update({ time: displayBarTime, value: price });
                if (this.areaSeries) this.areaSeries.update({ time: displayBarTime, value: price });

                if (this.volumeSeries) {
                    this.volumeSeries.update({
                        time: displayBarTime,
                        value: this.lastBar.volume,
                        color: this.lastBar.close >= this.lastBar.open ? 'rgba(8, 153, 129, 0.40)' : 'rgba(242, 54, 69, 0.40)'
                    });
                }
            } else if (rawBarTime > this.lastBar.rawTime) {
                // New candle period started
                this.lastBar = {
                    time: displayBarTime,
                    rawTime: rawBarTime,
                    open: price,
                    high: price,
                    low: price,
                    close: price,
                    volume: volumeDelta || 10,
                    ema9: this.lastBar.ema9,
                    ema21: this.lastBar.ema21
                };

                this.candleSeries.update({
                    time: displayBarTime,
                    open: price,
                    high: price,
                    low: price,
                    close: price
                });
                if (this.lineSeries) this.lineSeries.update({ time: displayBarTime, value: price });
                if (this.areaSeries) this.areaSeries.update({ time: displayBarTime, value: price });
                if (this.volumeSeries) this.volumeSeries.update({
                    time: displayBarTime,
                    value: this.lastBar.volume,
                    color: 'rgba(8, 153, 129, 0.40)'
                });
            }
        }

        this.updateLegendFromLastBar();
    }

    handleCrosshairMove(param) {
        if (!param || !param.time || !param.seriesData) {
            this.updateLegendFromLastBar();
            return;
        }

        const activeSeries = this.chartType === 'candle' ? this.candleSeries : (this.chartType === 'line' ? this.lineSeries : this.areaSeries);
        const barData = param.seriesData.get(activeSeries);
        const volData = param.seriesData.get(this.volumeSeries);
        const ema9Data = param.seriesData.get(this.ema9Series);
        const ema21Data = param.seriesData.get(this.ema21Series);

        if (barData) {
            const open = barData.open !== undefined ? barData.open : barData.value;
            const high = barData.high !== undefined ? barData.high : barData.value;
            const low = barData.low !== undefined ? barData.low : barData.value;
            const close = barData.close !== undefined ? barData.close : barData.value;
            const diff = close - open;
            const diffPct = open > 0 ? (diff / open) * 100 : 0;
            const vol = volData ? volData.value : 0;

            this.setLegendValues(open, high, low, close, diff, diffPct, vol, ema9Data?.value, ema21Data?.value);
        }
    }

    updateLegendFromLastBar() {
        if (!this.lastBar) return;
        const { open, high, low, close, volume, ema9, ema21 } = this.lastBar;
        const diff = close - open;
        const diffPct = open > 0 ? (diff / open) * 100 : 0;
        this.setLegendValues(open, high, low, close, diff, diffPct, volume, ema9, ema21);
    }

    setLegendValues(o, h, l, c, diff, diffPct, vol, e9, e21) {
        const fmt = val => (val !== undefined && val !== null && !isNaN(val)) ? val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '--';
        
        const openEl = document.getElementById('leg-open');
        const highEl = document.getElementById('leg-high');
        const lowEl = document.getElementById('leg-low');
        const closeEl = document.getElementById('leg-close');
        const changeEl = document.getElementById('leg-change');
        const volEl = document.getElementById('leg-vol');
        const ema9El = document.getElementById('leg-ema9');
        const ema21El = document.getElementById('leg-ema21');

        if (openEl) openEl.textContent = fmt(o);
        if (highEl) highEl.textContent = fmt(h);
        if (lowEl) lowEl.textContent = fmt(l);
        if (closeEl) closeEl.textContent = fmt(c);

        if (changeEl) {
            const sign = diff >= 0 ? '+' : '';
            changeEl.textContent = `${sign}${diff.toFixed(2)} (${sign}${diffPct.toFixed(2)}%)`;
            changeEl.className = diff >= 0 ? 'text-green' : 'text-red';
        }

        if (volEl) {
            volEl.textContent = vol ? `${Math.round(vol).toLocaleString()} BTC` : '--';
        }
        if (ema9El && e9) ema9El.textContent = fmt(e9);
        if (ema21El && e21) ema21El.textContent = fmt(e21);
    }

    /**
     * Overlay active trade execution levels directly on the chart.
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
                color: '#2962ff',
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
                color: '#F23645',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: `STOP LOSS: $${sl.toLocaleString()}`,
            });
            this.activePriceLines.push(slLine);
        }

        if (tp1) {
            const tpLine = this.candleSeries.createPriceLine({
                price: tp1,
                color: '#089981',
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: `TP1 TARGET: $${tp1.toLocaleString()}`,
            });
            this.activePriceLines.push(tpLine);
        }
    }
}
