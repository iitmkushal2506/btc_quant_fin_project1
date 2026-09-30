/**
 * 7-Pillar Confluence Radar & Master Decision Visualizer
 */

class ConfluenceRadar {
    constructor() {
        this.pillarsContainer = document.getElementById('pillars-container');
        this.decisionBadge = document.getElementById('master-decision-badge');
        this.summaryText = document.getElementById('decision-summary-text');
        this.directiveText = document.getElementById('action-directive-text');
        this.supportingList = document.getElementById('supporting-evidence-list');
        this.conflictingList = document.getElementById('conflicting-evidence-list');
        this.masterScoreVal = document.getElementById('master-score-val');
        this.convictionVal = document.getElementById('conviction-pct-val');
        this.convictionFill = document.getElementById('conviction-fill-bar');
        this.pillarAgreeVal = document.getElementById('pillar-agreement-val');
        this.conflictPenaltyVal = document.getElementById('conflict-penalty-val');
        this.tagConflict = document.getElementById('tag-conflict-level');
        this.tagStrategy = document.getElementById('tag-regime-strategy');
    }

    update(assessment) {
        if (!assessment) return;

        const decision = assessment.decision || {};
        const confluence = assessment.confluence || {};
        const pillars = confluence.pillars || {};
        const regime = assessment.regime || {};

        // 1. Update Decision Hero Banner
        if (this.decisionBadge) {
            this.decisionBadge.className = `decision-main-badge ${decision.badge_class || 'no-trade'}`;
            this.decisionBadge.innerHTML = `<span class="badge-icon">${decision.badge_text?.includes('VALID') ? '🟢' : (decision.badge_text?.includes('WAIT') ? '🟡' : '🔴')}</span><span class="badge-title">${decision.badge_text || '🔴 NO TRADE'}</span>`;
        }

        if (this.summaryText) this.summaryText.textContent = decision.summary_reason || '';
        if (this.directiveText) this.directiveText.textContent = decision.action_directive || '';

        if (this.tagConflict) this.tagConflict.textContent = `CONFLICT: ${(confluence.conflict_level || 'LOW').replace('_', ' ')}`;
        if (this.tagStrategy) this.tagStrategy.textContent = `STRATEGY: ${(regime.favorable_strategy || 'WAIT').replace(/_/g, ' ')}`;

        // 2. Gauges & Conviction
        const masterScore = confluence.master_confluence_score || 0;
        if (this.masterScoreVal) {
            this.masterScoreVal.textContent = (masterScore > 0 ? '+' : '') + masterScore.toFixed(1);
            this.masterScoreVal.style.color = masterScore > 20 ? 'var(--color-green)' : (masterScore < -20 ? 'var(--color-red)' : 'var(--color-yellow)');
        }

        const conviction = confluence.conviction_pct || 0;
        if (this.convictionVal) this.convictionVal.textContent = `${conviction.toFixed(0)}%`;
        if (this.convictionFill) this.convictionFill.style.width = `${Math.min(100, conviction)}%`;

        if (this.pillarAgreeVal) this.pillarAgreeVal.textContent = confluence.pillars_in_agreement || '0 / 7';
        if (this.conflictPenaltyVal) this.conflictPenaltyVal.textContent = `Penalty: -${(confluence.conflict_penalty || 0).toFixed(1)}`;

        // 3. Supporting and Conflicting Lists
        if (this.supportingList) {
            this.supportingList.innerHTML = (decision.supporting_evidence && decision.supporting_evidence.length > 0)
                ? decision.supporting_evidence.map(ev => `<li>${ev.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')}</li>`).join('')
                : '<li>No strong dimensional tailwinds identified.</li>';
        }

        if (this.conflictingList) {
            this.conflictingList.innerHTML = (decision.conflicting_evidence && decision.conflicting_evidence.length > 0)
                ? decision.conflicting_evidence.map(ev => `<li>${ev.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')}</li>`).join('')
                : '<li>No conflicting risk factors detected. Dimensions in harmony.</li>';
        }

        // 4. Render 7 Pillar Cards
        this.renderPillarCards(pillars);
    }

    renderPillarCards(pillars) {
        if (!this.pillarsContainer) return;

        const cardsHtml = Object.keys(pillars).map(key => {
            const p = pillars[key];
            const sc = p.score || 0;
            const bias = p.bias || 'NEUTRAL';
            const biasClass = bias.toLowerCase();
            const scoreFormatted = (sc > 0 ? '+' : '') + sc.toFixed(1);

            const factorsHtml = (p.key_factors || []).map(f => `<li>${f}</li>`).join('');

            return `
                <div class="pillar-card ${biasClass}">
                    <div class="p-header">
                        <span class="p-title">${p.name}</span>
                        <span class="p-weight">${(p.weight * 100).toFixed(0)}% Wgt</span>
                    </div>
                    <div class="p-score-row">
                        <span class="p-score ${biasClass}">${scoreFormatted}</span>
                        <span class="p-bias-badge ${biasClass}">${bias}</span>
                    </div>
                    <ul class="p-factors-list">
                        ${factorsHtml}
                    </ul>
                </div>
            `;
        }).join('');

        this.pillarsContainer.innerHTML = cardsHtml;
    }
}
