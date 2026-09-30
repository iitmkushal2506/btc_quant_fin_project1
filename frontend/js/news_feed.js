/**
 * Global Crypto Intelligence & NLP News Feed Manager
 */

class NewsFeedManager {
    constructor() {
        this.newsContainer = document.getElementById('news-feed-list');
        this.filterButtons = document.querySelectorAll('#news-filter-group .n-filter-btn');
        this.currentFilter = 'ALL';
        this.articles = [];

        this.initEvents();
    }

    initEvents() {
        this.filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                this.filterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentFilter = btn.dataset.category;
                this.renderArticles();
            });
        });
    }

    update(newsPayload) {
        if (!newsPayload || !newsPayload.articles) return;
        this.articles = newsPayload.articles;
        this.renderArticles();
    }

    renderArticles() {
        if (!this.newsContainer) return;

        let filtered = this.articles;
        if (this.currentFilter !== 'ALL') {
            filtered = this.articles.filter(art => (art.entities || []).includes(this.currentFilter));
        }

        if (filtered.length === 0) {
            this.newsContainer.innerHTML = '<div style="color: var(--text-muted); padding: 16px; font-family: var(--font-mono); font-size: 11px;">No breaking articles currently matching category filter.</div>';
            return;
        }

        const cardsHtml = filtered.map(art => {
            const sentClass = (art.sentiment_label || 'NEUTRAL').toLowerCase();
            const factualityFormatted = (art.factuality || 'DEVELOPING_REPORT').replace(/_/g, ' ');
            const entitiesStr = (art.entities || []).slice(0, 2).map(e => e.replace(/_/g, ' ')).join(', ');

            return `
                <div class="news-card-item">
                    <div class="n-top">
                        <span class="n-source">${art.source || 'Crypto'} • ${art.published || 'Recent'}</span>
                        <div class="n-tags">
                            <span class="n-tag ${sentClass}">${art.sentiment_label || 'NEUTRAL'}</span>
                            <span class="n-tag" style="background: rgba(255,255,255,0.05); color: var(--text-secondary);">${art.impact_level || 'MED'} IMPACT</span>
                        </div>
                    </div>
                    <a href="${art.link || '#'}" target="_blank" rel="noopener" class="n-title">${art.title}</a>
                    <p class="n-summary">${art.summary || ''}</p>
                    <div class="n-footer">
                        <span>🏷 ${entitiesStr || 'General'}</span>
                        <span>🔍 ${factualityFormatted}</span>
                    </div>
                </div>
            `;
        }).join('');

        this.newsContainer.innerHTML = cardsHtml;
    }
}
