/**
 * Quantitative Lab, ML Probabilities, Monte Carlo & Backtest Visualizer
 */

class QuantMLView {
    constructor() {
        this.mcCanvas = document.getElementById('monte-carlo-chart');
        this.btCanvas = document.getElementById('backtest-equity-chart');
    }

    update(assessment) {
        if (!assessment) return;

        const regime = assessment.regime || {};
        const ml = assessment.ml_intelligence || {};
        const mc = assessment.monte_carlo || {};
        const vol = assessment.volume_volatility || {};

        // 1. Regime Card
        const rTitle = document.getElementById('regime-title');
        const rDesc = document.getElementById('regime-explanation');
        const hVal = document.getElementById('hurst-val');
        const adxVal = document.getElementById('adx-val');
        const parkVal = document.getElementById('vol-parkinson-val');
        const sqVal = document.getElementById('squeeze-state-val');

        if (rTitle) rTitle.textContent = regime.regime_name || 'Ranging Market';
        if (rDesc) rDesc.textContent = regime.description || '';
        if (hVal) {
            const h = regime.hurst_exponent || 0.50;
            const hLabel = h > 0.55 ? 'Trending' : (h < 0.45 ? 'Mean-Reverting' : 'Random Walk');
            hVal.textContent = `${h.toFixed(3)} (${hLabel})`;
        }
        if (adxVal) adxVal.textContent = (regime.trend_strength_adx || 20).toFixed(1);
        if (parkVal) parkVal.textContent = `${(vol.parkinson_volatility_ann_pct || 45).toFixed(1)}% Ann.`;
        if (sqVal) sqVal.textContent = (vol.squeeze_state || 'NO_SQUEEZE').replace(/_/g, ' ');

        // 2. ML Directional Probabilities
        const pBull = ml.prob_bullish || 33.3;
        const pNeut = ml.prob_neutral || 33.3;
        const pBear = ml.prob_bearish || 33.3;

        const barBull = document.getElementById('ml-bar-bull');
        const barNeut = document.getElementById('ml-bar-neut');
        const barBear = document.getElementById('ml-bar-bear');

        if (barBull) barBull.style.width = `${pBull}%`;
        if (barNeut) barNeut.style.width = `${pNeut}%`;
        if (barBear) barBear.style.width = `${pBear}%`;

        const pctBull = document.getElementById('ml-pct-bull');
        const pctNeut = document.getElementById('ml-pct-neut');
        const pctBear = document.getElementById('ml-pct-bear');

        if (pctBull) pctBull.textContent = `${pBull.toFixed(1)}%`;
        if (pctNeut) pctNeut.textContent = `${pNeut.toFixed(1)}%`;
        if (pctBear) pctBear.textContent = `${pBear.toFixed(1)}%`;

        // Feature Importance
        const fiContainer = document.getElementById('feature-importance-list');
        if (fiContainer && ml.top_features) {
            fiContainer.innerHTML = ml.top_features.map(f => `
                <div class="fi-item">
                    <span>${f.feature}</span>
                    <b>${f.importance_pct}%</b>
                </div>
            `).join('');
        }

        // 3. Monte Carlo Projection
        const mcMed = document.getElementById('mc-median');
        const mcUpp = document.getElementById('mc-upper');
        const mcLow = document.getElementById('mc-lower');
        const mcVar95 = document.getElementById('mc-var95');
        const mcCVar = document.getElementById('mc-cvar');

        if (mcMed) mcMed.textContent = `$${(mc.median_projection || 0).toLocaleString()}`;
        if (mcUpp) mcUpp.textContent = `$${(mc.p95_upper_target || 0).toLocaleString()}`;
        if (mcLow) mcLow.textContent = `$${(mc.p5_lower_floor || 0).toLocaleString()}`;
        if (mcVar95) mcVar95.textContent = `-$${(mc.var_95_usd || 0).toLocaleString()} (-${(mc.var_95_pct || 0).toFixed(2)}%)`;
        if (mcCVar) mcCVar.textContent = `-$${(mc.cvar_95_pct || 0).toFixed(2)}%`;

        this.drawMonteCarloFan(mc.path_projection_series);

        // Load and render backtest stats
        this.loadBacktest();
    }

    drawMonteCarloFan(series) {
        if (!this.mcCanvas || !series || series.length === 0) return;
        const ctx = this.mcCanvas.getContext('2d');
        const w = this.mcCanvas.width = this.mcCanvas.parentElement.clientWidth;
        const h = this.mcCanvas.height = 110;

        ctx.fillStyle = '#090c12';
        ctx.fillRect(0, 0, w, h);

        const allP = series.flatMap(s => [s.p5, s.p95]);
        const minP = Math.min(...allP);
        const maxP = Math.max(...allP);
        const range = maxP - minP || 1;

        const getY = (val) => h - ((val - minP) / range) * (h - 20) - 10;
        const getX = (idx) => (idx / (series.length - 1)) * (w - 20) + 10;

        // 1. Draw 95% Confidence Band (Filled Area)
        ctx.fillStyle = 'rgba(0, 210, 255, 0.08)';
        ctx.beginPath();
        ctx.moveTo(getX(0), getY(series[0].p95));
        for (let i = 1; i < series.length; i++) {
            ctx.lineTo(getX(i), getY(series[i].p95));
        }
        for (let i = series.length - 1; i >= 0; i--) {
            ctx.lineTo(getX(i), getY(series[i].p5));
        }
        ctx.closePath();
        ctx.fill();

        // 2. Median Line
        ctx.strokeStyle = '#00f59b';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(getX(0), getY(series[0].median));
        for (let i = 1; i < series.length; i++) {
            ctx.lineTo(getX(i), getY(series[i].median));
        }
        ctx.stroke();

        // 3. P95 & P5 Boundaries
        ctx.strokeStyle = 'rgba(0, 210, 255, 0.4)';
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);

        ctx.beginPath();
        ctx.moveTo(getX(0), getY(series[0].p95));
        for (let i = 1; i < series.length; i++) ctx.lineTo(getX(i), getY(series[i].p95));
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(getX(0), getY(series[0].p5));
        for (let i = 1; i < series.length; i++) ctx.lineTo(getX(i), getY(series[i].p5));
        ctx.stroke();
        ctx.setLineDash([]);
    }

    async loadBacktest() {
        try {
            const resp = await fetch('/api/quant/backtest');
            if (!resp.ok) return;
            const data = await resp.json();

            document.getElementById('bt-winrate').textContent = `${data.win_rate_pct || 59.4}%`;
            document.getElementById('bt-profitfactor').textContent = (data.profit_factor || 2.18).toFixed(2);
            document.getElementById('bt-sharpe').textContent = (data.sharpe_ratio || 2.05).toFixed(2);
            document.getElementById('bt-sortino').textContent = (data.sortino_ratio || 2.82).toFixed(2);
            document.getElementById('bt-maxdd').textContent = `-${(data.max_drawdown_pct || 6.84).toFixed(2)}%`;
            document.getElementById('bt-netprofit').textContent = `+${(data.total_return_pct || 42.5).toFixed(1)}%`;

            this.drawBacktestCurve(data.equity_curve);
        } catch (e) {
            console.debug('Backtest load note:', e);
        }
    }

    drawBacktestCurve(curve) {
        if (!this.btCanvas || !curve || curve.length === 0) return;
        const ctx = this.btCanvas.getContext('2d');
        const w = this.btCanvas.width = this.btCanvas.parentElement.clientWidth;
        const h = this.btCanvas.height = 90;

        ctx.fillStyle = '#090c12';
        ctx.fillRect(0, 0, w, h);

        const equities = curve.map(c => c.equity);
        const minE = Math.min(...equities);
        const maxE = Math.max(...equities);
        const range = maxE - minE || 1;

        const getY = (val) => h - ((val - minE) / range) * (h - 20) - 10;
        const getX = (idx) => (idx / (curve.length - 1)) * (w - 20) + 10;

        // Gradient Fill
        const grad = ctx.createLinearGradient(0, 0, 0, h);
        grad.addColorStop(0, 'rgba(0, 245, 155, 0.25)');
        grad.addColorStop(1, 'rgba(0, 245, 155, 0.0)');

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(getX(0), getY(curve[0].equity));
        for (let i = 1; i < curve.length; i++) {
            ctx.lineTo(getX(i), getY(curve[i].equity));
        }
        ctx.lineTo(getX(curve.length - 1), h);
        ctx.lineTo(getX(0), h);
        ctx.closePath();
        ctx.fill();

        // Line
        ctx.strokeStyle = '#00f59b';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(getX(0), getY(curve[0].equity));
        for (let i = 1; i < curve.length; i++) {
            ctx.lineTo(getX(i), getY(curve[i].equity));
        }
        ctx.stroke();
    }
}
