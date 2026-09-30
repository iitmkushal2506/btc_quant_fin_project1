/**
 * Institutional Risk Management & Interactive Position Sizing Engine
 */

class RiskCalculator {
    constructor(onUpdateCallback) {
        this.onUpdateCallback = onUpdateCallback;
        this.accountEquityInput = document.getElementById('input-account-equity');
        this.riskPctInput = document.getElementById('input-risk-pct');
        this.lblRiskPct = document.getElementById('lbl-risk-pct');
        this.lblRiskUsd = document.getElementById('lbl-risk-usd');
        this.directionButtons = document.querySelectorAll('#direction-toggle-group .dir-btn');

        this.calcPosBtc = document.getElementById('calc-pos-btc');
        this.calcPosUsd = document.getElementById('calc-pos-usd');
        this.calcLev = document.getElementById('calc-effective-lev');
        this.calcLiq = document.getElementById('calc-liq-price');
        this.calcKelly = document.getElementById('calc-kelly-pct');
        this.levelsTbody = document.getElementById('risk-levels-tbody');
        this.thesisText = document.getElementById('thesis-invalidation-text');

        this.currentDirection = 'LONG';
        this.currentRiskData = null;

        this.initEvents();
    }

    initEvents() {
        if (this.accountEquityInput) {
            this.accountEquityInput.addEventListener('input', () => this.triggerRecalculate());
        }
        if (this.riskPctInput) {
            this.riskPctInput.addEventListener('input', (e) => {
                const val = parseFloat(e.target.value);
                if (this.lblRiskPct) this.lblRiskPct.textContent = `${val.toFixed(2)}%`;
                const equity = parseFloat(this.accountEquityInput?.value || 10000);
                if (this.lblRiskUsd) this.lblRiskUsd.textContent = `$${((equity * val) / 100).toFixed(2)}`;
                this.triggerRecalculate();
            });
        }
        this.directionButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.directionButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentDirection = btn.dataset.dir;
                this.triggerRecalculate();
            });
        });
    }

    async triggerRecalculate() {
        const equity = parseFloat(this.accountEquityInput?.value || 10000);
        const riskPct = parseFloat(this.riskPctInput?.value || 1.0);

        try {
            const resp = await fetch('/api/risk/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    account_equity: equity,
                    risk_percentage: riskPct,
                    direction: this.currentDirection
                })
            });

            if (!resp.ok) return;
            const updatedRisk = await resp.json();
            this.renderRiskProfile(updatedRisk);

            if (this.onUpdateCallback) {
                this.onUpdateCallback(updatedRisk);
            }
        } catch (e) {
            console.debug('Risk calc note:', e);
        }
    }

    renderRiskProfile(riskSetup, thesis) {
        if (!riskSetup) return;
        this.currentRiskData = riskSetup;

        const pos = riskSetup.position_sizing || {};
        if (this.calcPosBtc) this.calcPosBtc.textContent = `${(pos.position_size_btc || 0).toFixed(4)} BTC`;
        if (this.calcPosUsd) this.calcPosUsd.textContent = `$${(pos.position_notional_usd || 0).toLocaleString()}`;
        if (this.calcLev) this.calcLev.textContent = `${(pos.effective_leverage || 1.0).toFixed(2)}x`;
        if (this.calcLiq) this.calcLiq.textContent = `$${(pos.est_liquidation_price || 0).toLocaleString()}`;
        if (this.calcKelly) this.calcKelly.textContent = `${(pos.half_kelly_recommended_risk_pct || 1.0).toFixed(2)}%`;

        // Render Levels Table
        if (this.levelsTbody) {
            const entry = riskSetup.entry_zone?.optimal || 0;
            const sl = riskSetup.stop_loss || 0;
            const tps = riskSetup.take_profit_levels || [];
            const riskUsd = pos.max_risk_usd || 0;

            let rowsHtml = `
                <tr>
                    <td><b class="text-cyan">OPTIMAL ENTRY</b></td>
                    <td><b>$${entry.toLocaleString()}</b></td>
                    <td>Baseline (0R)</td>
                    <td>Initial Entry</td>
                    <td>$0.00</td>
                </tr>
                <tr>
                    <td><b class="text-red">HARD STOP LOSS</b></td>
                    <td class="text-red"><b>$${sl.toLocaleString()}</b></td>
                    <td class="text-red">-1.00R</td>
                    <td>100% Invalidation</td>
                    <td class="text-red">-$${riskUsd.toFixed(2)}</td>
                </tr>
            `;

            tps.forEach(tp => {
                rowsHtml += `
                    <tr>
                        <td><b class="text-green">${tp.tier}</b></td>
                        <td class="text-green"><b>$${tp.price.toLocaleString()}</b></td>
                        <td class="text-green">+${tp.rr}R</td>
                        <td>Take Profit Scale</td>
                        <td class="text-green">+$${tp.profit_usd?.toFixed(2) || '0.00'}</td>
                    </tr>
                `;
            });

            this.levelsTbody.innerHTML = rowsHtml;
        }

        if (this.thesisText && thesis) {
            this.thesisText.textContent = thesis.invalidation_condition || 'A 4-hour close beyond structural swing pivots immediately invalidates the trade thesis.';
        }
    }
}
