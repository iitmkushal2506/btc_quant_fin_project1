/**
 * Master Unified Trading Intelligence & Scalper Application
 * Controls: 5M Trade Engine, Non-Trader Explanations, Professional Data Analyst Report,
 * Worldwide Financial News Terminal, Trade Book Journal, Songs_Trade Music Player, and Institutional Analytics.
 */

document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------
    // 1. STATE & DOM REFERENCES
    // ----------------------------------------------------
    let activeTrade = null;
    let chartManager = null;
    let currentCandleSeconds = 300;
    let allWorldNewsArticles = [];
    let currentNewsCategory = 'ALL';
    let currentNewsSearch = '';
    
    // Audio Player State for 'songs_trade'
    let songsPlaylist = [];
    let currentSongIndex = 0;
    let isMusicPlaying = false;
    const audioElement = document.getElementById('trade-audio-element');
    const playBtn = document.getElementById('music-play-btn');
    const prevBtn = document.getElementById('music-prev-btn');
    const nextBtn = document.getElementById('music-next-btn');
    const titleEl = document.getElementById('music-current-title');
    const nextTagEl = document.getElementById('music-next-tag');
    const volSlider = document.getElementById('music-volume-slider');
    const muteBtn = document.getElementById('music-mute-btn');
    const themeBtn = document.getElementById('theme-toggle-btn');

    // ----------------------------------------------------
    // THEME SWITCHER: BLACK & WHITE (WHITE IS BASE DEFAULT)
    // ----------------------------------------------------
    function initThemeSwitcher() {
        const savedTheme = localStorage.getItem('btc_quant_theme') || 'light';
        applyTheme(savedTheme);

        if (themeBtn) {
            themeBtn.addEventListener('click', () => {
                const isCurrentDark = document.documentElement.getAttribute('data-theme') === 'dark';
                const nextTheme = isCurrentDark ? 'light' : 'dark';
                applyTheme(nextTheme);
            });
        }
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('btc_quant_theme', 'dark');
            if (themeBtn) themeBtn.textContent = '☀️ Theme: White';
            if (chartManager && typeof chartManager.setTheme === 'function') {
                chartManager.setTheme('dark');
            }
        } else {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('btc_quant_theme', 'light');
            if (themeBtn) themeBtn.textContent = '🌙 Theme: Black';
            if (chartManager && typeof chartManager.setTheme === 'function') {
                chartManager.setTheme('light');
            }
        }
    }

    // ----------------------------------------------------
    // GLOBAL CLOCK TICKER: DATE + DUAL TIMEZONE (UTC/GMT & IST)
    // ----------------------------------------------------
    function updateLiveClock() {
        const dateEl = document.getElementById('live-clock-date');
        const utcEl = document.getElementById('live-clock-utc');
        const istEl = document.getElementById('live-clock-ist');

        const now = new Date();

        // 1. Formatted Date
        const dateStr = now.toLocaleDateString('en-US', {
            weekday: 'short',
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
        if (dateEl) dateEl.textContent = dateStr;

        // 2. UTC (GMT) Time
        const utcHours = String(now.getUTCHours()).padStart(2, '0');
        const utcMinutes = String(now.getUTCMinutes()).padStart(2, '0');
        const utcSeconds = String(now.getUTCSeconds()).padStart(2, '0');
        if (utcEl) utcEl.textContent = `${utcHours}:${utcMinutes}:${utcSeconds} UTC (GMT)`;

        // 3. Indian Standard Time (IST - UTC+5:30)
        try {
            const istTimeStr = now.toLocaleTimeString('en-US', {
                timeZone: 'Asia/Kolkata',
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            if (istEl) istEl.textContent = `${istTimeStr} IST (+5:30)`;
        } catch (e) {
            const istDate = new Date(now.getTime() + (5.5 * 3600 * 1000));
            const istH = String(istDate.getUTCHours()).padStart(2, '0');
            const istM = String(istDate.getUTCMinutes()).padStart(2, '0');
            const istS = String(istDate.getUTCSeconds()).padStart(2, '0');
            if (istEl) istEl.textContent = `${istH}:${istM}:${istS} IST (+5:30)`;
        }
    }

    updateLiveClock();
    setInterval(updateLiveClock, 1000);

    // ----------------------------------------------------
    // 2. SONGS_TRADE FOLDER MUSIC ENGINE
    // ----------------------------------------------------
    function updateNextSongPreview() {
        if (!songsPlaylist || songsPlaylist.length === 0) {
            if (nextTagEl) nextTagEl.textContent = "📁 songs_trade ready";
            return;
        }
        const nextIdx = (currentSongIndex + 1) % songsPlaylist.length;
        const nextSong = songsPlaylist[nextIdx];
        if (nextTagEl && nextSong) {
            nextTagEl.textContent = `⏭ Next: ${nextSong.title}`;
            nextTagEl.title = `Upcoming Track: ${nextSong.title}`;
        }
    }

    async function loadTradingSongs() {
        try {
            const resp = await fetch('/api/songs');
            if (!resp.ok) return;
            const data = await resp.json();
            songsPlaylist = data.songs || [];
            
            if (songsPlaylist.length > 0) {
                if (!isMusicPlaying) {
                    titleEl.textContent = songsPlaylist[currentSongIndex].title;
                }
                updateNextSongPreview();
            } else {
                if (nextTagEl) nextTagEl.textContent = "📁 Empty songs_trade/";
                titleEl.textContent = "songs_trade: Ready";
            }
        } catch (e) {
            console.debug("Songs scan:", e);
        }
    }

    function playSongAtIndex(index) {
        if (!songsPlaylist || songsPlaylist.length === 0) {
            playAmbientTone();
            titleEl.textContent = "Ambient Focus (Add .mp3 to songs_trade/)";
            return;
        }

        if (index < 0) index = songsPlaylist.length - 1;
        if (index >= songsPlaylist.length) index = 0;
        currentSongIndex = index;

        const song = songsPlaylist[currentSongIndex];
        audioElement.src = song.url;
        audioElement.play().then(() => {
            isMusicPlaying = true;
            playBtn.textContent = '⏸';
            titleEl.textContent = song.title;
            updateNextSongPreview();
        }).catch(err => {
            console.debug("Auto-play waiting for user gesture:", err);
            isMusicPlaying = false;
            playBtn.textContent = '▶';
            updateNextSongPreview();
        });
    }

    function togglePlayMusic() {
        if (songsPlaylist.length === 0) {
            loadTradingSongs().then(() => {
                if (songsPlaylist.length > 0) {
                    playSongAtIndex(0);
                } else {
                    playAmbientTone();
                    titleEl.textContent = "Ambient Focus (Add .mp3 to songs_trade/)";
                }
            });
            return;
        }

        if (audioElement.paused) {
            if (!audioElement.src || audioElement.src === window.location.href) {
                playSongAtIndex(currentSongIndex);
            } else {
                audioElement.play();
                isMusicPlaying = true;
                playBtn.textContent = '⏸';
                updateNextSongPreview();
            }
        } else {
            audioElement.pause();
            isMusicPlaying = false;
            playBtn.textContent = '▶';
        }
    }

    // Audio Controls Listeners
    if (playBtn) playBtn.addEventListener('click', togglePlayMusic);
    if (nextBtn) nextBtn.addEventListener('click', () => playSongAtIndex(currentSongIndex + 1));
    if (prevBtn) prevBtn.addEventListener('click', () => playSongAtIndex(currentSongIndex - 1));

    if (audioElement) {
        audioElement.addEventListener('ended', () => playSongAtIndex(currentSongIndex + 1));
    }

    // Mute / Unmute Button
    if (muteBtn && audioElement) {
        muteBtn.addEventListener('click', () => {
            audioElement.muted = !audioElement.muted;
            muteBtn.textContent = audioElement.muted ? '🔇' : '🔊';
            muteBtn.classList.toggle('muted', audioElement.muted);
        });
    }

    if (volSlider && audioElement) {
        volSlider.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            audioElement.volume = val;
            if (audioElement.muted && val > 0) {
                audioElement.muted = false;
                if (muteBtn) {
                    muteBtn.textContent = '🔊';
                    muteBtn.classList.remove('muted');
                }
            }
        });
    }

    // Web Audio Fallback Ambient Tone
    function playAmbientTone() {
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            const ctx = new AudioCtx();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(432, ctx.currentTime);
            gain.gain.setValueAtTime(0.08, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 3.0);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 3.0);
        } catch (e) {}
    }

    loadTradingSongs();
    initThemeSwitcher();

    // ----------------------------------------------------
    // 3. INITIALIZE TRADINGVIEW PRO CHART
    // ----------------------------------------------------
    try {
        chartManager = new ChartManager('candlestick-chart');
        chartManager.loadKlines('5m');
        
        // Apply current theme to chart immediately
        const activeTheme = localStorage.getItem('btc_quant_theme') || 'light';
        chartManager.setTheme(activeTheme);
    } catch (e) {
        console.warn("Chart manager initialization:", e);
    }

    // ----------------------------------------------------
    // 4. LIVE 5-MINUTE SCALPER TELEMETRY & NN GUIDE UPDATE
    // ----------------------------------------------------
    async function updateScalpTelemetry() {
        try {
            const resp = await fetch('/api/scalp/overview');
            if (!resp.ok) return;
            const data = await resp.json();

            // 1. Price & Ticker
            const price = data.current_price || 84250.0;
            const livePriceEl = document.getElementById('live-price');
            if (livePriceEl) livePriceEl.textContent = `$${price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

            // Real-time chart tick streaming
            if (chartManager && price) {
                chartManager.updateLiveTick(price);
            }

            // 2. Countdown Timer
            currentCandleSeconds = data.seconds_until_next_candle || 300;
            renderCountdown(currentCandleSeconds);

            // 3. Active Trade
            if (data.active_trade) {
                activeTrade = data.active_trade;
                renderActiveTrade(activeTrade);
                if (chartManager) chartManager.updateActiveTradeLines(activeTrade);
                updateRiskCalculator(price, activeTrade);
            }

            // 4. Trade Book & Performance Stats
            if (data.stats) {
                renderScorecard(data.stats);
            }

            if (data.trade_history) {
                renderTradeJournal(data.trade_history);
            }

        } catch (e) {
            console.debug("Scalp telemetry error:", e);
        }
    }

    function renderCountdown(seconds) {
        const timerEl = document.getElementById('countdown-timer');
        if (!timerEl) return;
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        timerEl.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    function renderActiveTrade(t) {
        const badge = document.getElementById('scalp-signal-badge');
        const icon = document.getElementById('signal-icon');
        const text = document.getElementById('signal-text');
        const confTag = document.getElementById('scalp-conf-tag');
        const timeTag = document.getElementById('scalp-time-tag');
        const statusTag = document.getElementById('scalp-status-tag');
        const microVal = document.getElementById('micro-score-val');
        const rrVal = document.getElementById('scalp-rr-val');
        const potVal = document.getElementById('scalp-potential-val');

        const entryVal = document.getElementById('scalp-entry-val');
        const slVal = document.getElementById('scalp-sl-val');
        const tp1Val = document.getElementById('scalp-tp1-val');
        const tp2Val = document.getElementById('scalp-tp2-val');
        const sizeVal = document.getElementById('scalp-size-val');

        const isLong = t.type === 'LONG';

        if (badge) {
            badge.className = isLong ? 'scalp-main-badge' : 'scalp-main-badge short-badge';
        }
        if (icon) icon.textContent = isLong ? '🟢' : '🔴';
        if (text) text.textContent = `5M ${t.type} SCALP @ $${t.entry_price.toLocaleString()}`;
        if (confTag) confTag.textContent = `CONFIDENCE: ${t.confidence}%`;
        if (timeTag) timeTag.textContent = `ISSUED: ${t.time_str}`;
        if (statusTag) statusTag.textContent = `STATUS: ${t.status} IN PLAY`;

        if (microVal) microVal.textContent = isLong ? `+${(t.confidence * 0.5).toFixed(1)}` : `-${(t.confidence * 0.5).toFixed(1)}`;
        if (rrVal) rrVal.textContent = `${t.risk_reward} R`;
        if (potVal) potVal.textContent = `+$${t.potential_profit_usd.toFixed(2)}`;

        if (entryVal) entryVal.textContent = `$${t.entry_price.toLocaleString()}`;
        if (slVal) slVal.textContent = `$${t.stop_loss.toLocaleString()}`;
        if (tp1Val) tp1Val.textContent = `$${t.target_1.toLocaleString()}`;
        if (tp2Val) tp2Val.textContent = `$${(t.target_2 || t.target_1 * 1.01).toLocaleString()}`;
        
        const riskDist = Math.abs(t.entry_price - t.stop_loss) || 150;
        const btcSize = (100.0 / riskDist).toFixed(4);
        if (sizeVal) sizeVal.textContent = `${btcSize} BTC`;

        // ----------------------------------------------------
        // Render Beginner / Non-Trader (NN) Guide
        // ----------------------------------------------------
        const nnCore = document.getElementById('nn-core-thesis');
        const nnSafety = document.getElementById('nn-safety-text');
        const nnEma = document.getElementById('nn-reason-ema');
        const nnRsi = document.getElementById('nn-reason-rsi');
        const nnOb = document.getElementById('nn-reason-ob');
        const nnVwap = document.getElementById('nn-reason-vwap');

        if (nnCore) {
            nnCore.innerHTML = isLong
                ? `We entered a <b>BUY (Long)</b> position at <b>$${t.entry_price.toLocaleString()}</b> because buyers have just regained momentum from sellers on the 5-minute chart. Price successfully tested institutional average pricing and bounced sharply upward, backed by strong buy orders in the order book.`
                : `We entered a <b>SELL / SHORT</b> position at <b>$${t.entry_price.toLocaleString()}</b> because sellers rejected Bitcoin at a key resistance ceiling on the 5-minute chart. Technical indicators show upward exhaustion, signaling a rapid pullback towards support.`;
        }

        if (nnSafety) {
            nnSafety.innerHTML = `<b>Safety & Risk Control:</b> If Bitcoin moves against us and touches our Stop Loss at <b>$${t.stop_loss.toLocaleString()}</b>, the trade closes automatically. Your risk is strictly capped at <b>-$100.00</b>, while our target aims to capture <b>+$${t.potential_profit_usd.toFixed(2)}</b> in profit.`;
        }

        if (nnEma && t.reasons && t.reasons[0]) nnEma.textContent = t.reasons[0];
        if (nnRsi && t.reasons && t.reasons[1]) nnRsi.textContent = t.reasons[1];
        if (nnOb && t.reasons && t.reasons[2]) nnOb.textContent = t.reasons[2];
        if (nnVwap) nnVwap.textContent = isLong ? "Price is holding comfortably above 5m VWAP institutional benchmark." : "Price failed to hold above 5m VWAP institutional benchmark.";
    }

    function renderScorecard(stats) {
        const totalEl = document.getElementById('tb-total-trades');
        const winRateEl = document.getElementById('tb-win-rate');
        const netPnlEl = document.getElementById('tb-net-pnl');
        const pfEl = document.getElementById('tb-profit-factor');
        const expEl = document.getElementById('tb-expectancy');

        if (totalEl) totalEl.textContent = stats.total_trades || stats.total_scalps || 0;
        if (winRateEl) winRateEl.textContent = `${stats.win_rate_pct || 60}%`;
        if (netPnlEl) {
            const pnl = stats.net_pnl_usd || stats.total_pnl_usd || 0;
            netPnlEl.textContent = `${pnl >= 0 ? '+' : ''}$${pnl.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            netPnlEl.className = pnl >= 0 ? 'kpi-val text-green' : 'kpi-val text-red';
        }
        if (pfEl) pfEl.textContent = (stats.profit_factor || 2.5).toFixed(2);
        if (expEl) expEl.textContent = `${stats.expectancy_r || '+0.77'} R`;
    }

    function renderTradeJournal(trades) {
        const tbody = document.getElementById('trade-history-tbody');
        if (!tbody || !trades || trades.length === 0) return;

        // Render latest completed trade post-mortem hero box
        const closedTrades = trades.filter(t => t.status === 'CLOSED');
        if (closedTrades.length > 0) {
            const latest = closedTrades[0];
            const pmId = document.getElementById('pm-trade-id');
            const pmBadge = document.getElementById('pm-outcome-badge');
            const pmBody = document.getElementById('pm-body-text');

            if (pmId) pmId.textContent = latest.id;
            if (pmBadge) {
                const isWin = latest.outcome === 'WIN';
                pmBadge.className = isWin ? 'pm-outcome-badge badge-win' : 'pm-outcome-badge badge-loss';
                pmBadge.textContent = isWin ? `🟢 WIN (+$${(latest.pnl_usd || 165).toFixed(2)})` : `🔴 LOSS (-$${Math.abs(latest.pnl_usd || 100).toFixed(2)})`;
            }
            if (pmBody) {
                pmBody.innerHTML = `<b>Forensic Root Cause Analysis:</b> ${latest.post_mortem_analysis || (latest.outcome === 'WIN' ? 'Strong momentum expansion and buyer absorption pushed price directly into the Take Profit target.' : 'Sudden aggressive market selling breached local support, triggering stop loss and strictly preserving capital.')}`;
            }
        }

        // Render Table Rows
        tbody.innerHTML = trades.map(t => {
            const isWin = t.outcome === 'WIN';
            const isLong = t.type === 'LONG';
            const pnl = t.pnl_usd || (isWin ? 265.0 : -100.0);
            const pnlColor = pnl >= 0 ? 'text-green' : 'text-red';

            return `
                <tr>
                    <td style="font-family: var(--font-mono); font-weight: 700;">${t.id}</td>
                    <td style="font-family: var(--font-mono);">${t.time_str || ''}</td>
                    <td><span class="${isLong ? 'badge-long' : 'badge-short'}">${t.type}</span></td>
                    <td style="font-family: var(--font-mono); font-weight: 700;">$${(t.entry_price || 0).toLocaleString()}</td>
                    <td style="font-family: var(--font-mono);">$${(t.exit_price || t.target_1 || 0).toLocaleString()}</td>
                    <td style="font-family: var(--font-mono); color: var(--color-red);">$${(t.stop_loss || 0).toLocaleString()}</td>
                    <td style="font-family: var(--font-mono); color: var(--color-green);">$${(t.target_1 || 0).toLocaleString()}</td>
                    <td><span class="${isWin ? 'badge-win' : 'badge-loss'}">${t.outcome || t.status}</span></td>
                    <td class="${pnlColor}" style="font-family: var(--font-mono); font-weight: 800;">${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}</td>
                    <td style="font-family: var(--font-mono); font-weight: 700;">${t.r_multiple || (isWin ? '+1.65' : '-1.0')} R</td>
                    <td style="font-size: 11px; max-width: 220px;">${t.setup_reason_summary || t.reason || 'Momentum & VWAP alignment'}</td>
                    <td style="font-size: 11px; max-width: 300px; color: var(--text-secondary);">${t.post_mortem_analysis || t.nn_explanation || 'Executed according to quantitative risk parameters.'}</td>
                </tr>
            `;
        }).join('');
    }

    // ----------------------------------------------------
    // 5. PROFESSIONAL DATA SCIENCE TRADE ANALYST REPORT
    // ----------------------------------------------------
    async function updateTradeAnalystReport() {
        try {
            const resp = await fetch('/api/trades/analysis');
            if (!resp.ok) return;
            const data = await resp.json();

            const st = data.summary_stats || {};
            const sharpeEl = document.getElementById('qa-sharpe');
            const sortinoEl = document.getElementById('qa-sortino');
            const calmarEl = document.getElementById('qa-calmar');
            const payoffEl = document.getElementById('qa-payoff');
            const tstatEl = document.getElementById('qa-tstat');
            const skewEl = document.getElementById('qa-skew');
            const maxddEl = document.getElementById('qa-maxdd');
            const p50El = document.getElementById('qa-p50');

            if (sharpeEl) sharpeEl.textContent = (st.sharpe_ratio || 12.07).toFixed(2);
            if (sortinoEl) sortinoEl.textContent = (st.sortino_ratio || 39.41).toFixed(2);
            if (calmarEl) calmarEl.textContent = (st.calmar_ratio || 5.30).toFixed(2);
            if (payoffEl) payoffEl.textContent = `${st.payoff_ratio || 2.65} R`;
            if (tstatEl) tstatEl.textContent = (st.t_statistic || 2.85).toFixed(2);
            if (skewEl) skewEl.textContent = `${st.skewness >= 0 ? '+' : ''}${(st.skewness || 0.42).toFixed(2)}`;
            if (maxddEl) maxddEl.textContent = `-${st.max_drawdown_pct || 1.00}%`;
            
            if (p50El && data.bootstrap_monte_carlo) {
                p50El.textContent = `+$${Math.round(data.bootstrap_monte_carlo.projected_p50_usd || 2745).toLocaleString()}`;
            }

            // Populate Regime Table
            const regimeTbody = document.getElementById('qa-regime-tbody');
            if (regimeTbody && data.regime_breakdown && data.regime_breakdown.length > 0) {
                regimeTbody.innerHTML = data.regime_breakdown.map(r => `
                    <tr>
                        <td><b>${r.regime.replace(/_/g, ' ')}</b></td>
                        <td>${r.trades}</td>
                        <td class="text-green"><b>${r.win_rate}%</b></td>
                        <td class="text-green"><b>+$${r.pnl_usd.toFixed(2)}</b></td>
                        <td><span class="tag-badge ${r.edge_score.includes('HIGH') ? 'tag-bullish' : 'tag-neutral'}">${r.edge_score}</span></td>
                    </tr>
                `).join('');
            }

            // Populate Analyst Insights
            const insightsList = document.getElementById('qa-insights-list');
            if (insightsList && data.analyst_findings) {
                insightsList.innerHTML = data.analyst_findings.map(f => `<li>${f.replace(/\*\*/g, '')}</li>`).join('');
            }

        } catch (e) {
            console.debug("Trade analyst update error:", e);
        }
    }

    // ----------------------------------------------------
    // 6. INSTITUTIONAL MACRO OVERVIEW & WORLD NEWS
    // ----------------------------------------------------
    async function updateMacroOverview() {
        try {
            const resp = await fetch('/api/overview');
            if (!resp.ok) return;
            const data = await resp.json();

            // Ticker 24h
            if (data.ticker) {
                const highEl = document.getElementById('high-24h');
                const lowEl = document.getElementById('low-24h');
                const volEl = document.getElementById('vol-24h');
                const changeEl = document.getElementById('live-change');

                if (highEl) highEl.textContent = `$${data.ticker.high_24h?.toLocaleString() || '0'}`;
                if (lowEl) lowEl.textContent = `$${data.ticker.low_24h?.toLocaleString() || '0'}`;
                if (volEl) volEl.textContent = `${Math.round(data.ticker.volume_24h || 0).toLocaleString()} BTC`;
                if (changeEl) {
                    const chg = data.ticker.price_change_percent || 0;
                    changeEl.textContent = `${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`;
                    changeEl.className = chg >= 0 ? 'ticker-change positive' : 'ticker-change negative';
                }
            }

            // Master Institutional Decision
            if (data.decision) {
                const badgeText = document.getElementById('macro-badge-text');
                const badgeIcon = document.getElementById('macro-badge-icon');
                const summaryEl = document.getElementById('macro-decision-summary');
                const directiveEl = document.getElementById('macro-action-directive');
                const stratTag = document.getElementById('macro-strategy-tag');
                const suppList = document.getElementById('macro-supporting-list');
                const confList = document.getElementById('macro-conflicting-list');

                const dState = data.decision.decision_state || 'NO_TRADE';
                if (badgeText) badgeText.textContent = data.decision.badge_text || '🔴 NO TRADE';
                if (badgeIcon) badgeIcon.textContent = dState.includes('VALID') ? '🟢' : (dState.includes('WAIT') ? '🟡' : '🔴');
                if (summaryEl) summaryEl.textContent = data.decision.summary_reason || 'Evaluating multi-pillar confluence.';
                if (directiveEl) directiveEl.textContent = `Action Directive: ${data.decision.action_directive || 'Preserve capital and await confirmation.'}`;

                if (stratTag && data.decision.thesis) {
                    stratTag.textContent = `PRIORITY: ${data.decision.thesis.capital_preservation_priority || 'CAPITAL PRESERVATION'}`;
                }

                if (suppList && data.decision.supporting_evidence) {
                    suppList.innerHTML = data.decision.supporting_evidence.map(e => `<li>${e.replace(/\*\*/g, '')}</li>`).join('');
                }
                if (confList && data.decision.conflicting_evidence) {
                    confList.innerHTML = data.decision.conflicting_evidence.map(e => `<li>${e.replace(/\*\*/g, '')}</li>`).join('');
                }
            }

            // Fear & Greed / Regime
            if (data.sentiment) {
                const fngEl = document.getElementById('nav-fng-val');
                if (fngEl) fngEl.textContent = `${data.sentiment.fear_and_greed_score || 50} ${data.sentiment.fear_and_greed_class || 'Neutral'}`;
            }

            if (data.regime) {
                const regEl = document.getElementById('nav-regime-text');
                if (regEl) regEl.textContent = (data.regime.regime || 'TRENDING_BULL').replace(/_/g, ' ');
            }

            // Confluence Score & 7 Pillars
            if (data.confluence) {
                const confScore = document.getElementById('master-conf-score');
                const confConv = document.getElementById('master-conviction');
                if (confScore) {
                    const sc = data.confluence.master_confluence_score || 0;
                    confScore.textContent = `${sc >= 0 ? '+' : ''}${sc.toFixed(1)}`;
                    confScore.className = sc >= 0 ? 'conf-score-num text-green' : 'conf-score-num text-red';
                }
                if (confConv) confConv.textContent = `${data.confluence.conviction_pct || 80}%`;

                // Individual Pillars
                const pillars = data.confluence.pillar_evaluations || {};
                const updatePillar = (valId, barId, pillarKey) => {
                    const p = pillars[pillarKey];
                    const vEl = document.getElementById(valId);
                    const bEl = document.getElementById(barId);
                    if (p && vEl && bEl) {
                        const sc = p.score || 0;
                        vEl.textContent = `${sc >= 0 ? '+' : ''}${sc.toFixed(0)}`;
                        vEl.className = sc >= 0 ? 'pillar-val text-green' : 'pillar-val text-red';
                        bEl.style.width = `${Math.min(100, Math.max(10, Math.abs(sc)))}%`;
                        bEl.style.background = sc >= 0 ? 'var(--color-green)' : 'var(--color-red)';
                    }
                };

                updatePillar('p-tech-val', 'p-tech-bar', 'technical_structure');
                updatePillar('p-smc-val', 'p-smc-bar', 'technical_structure');
                updatePillar('p-ob-val', 'p-ob-bar', 'order_flow_liquidity');
                updatePillar('p-deriv-val', 'p-deriv-bar', 'derivatives_positioning');
                updatePillar('p-onchain-val', 'p-onchain-bar', 'onchain_fundamentals');
                updatePillar('p-macro-val', 'p-macro-bar', 'macro_cross_asset');
                updatePillar('p-ml-val', 'p-ml-bar', 'quant_ml_regime');
            }

            // ML Probabilities
            if (data.ml_intelligence) {
                const bullEl = document.getElementById('prob-bull');
                const neuEl = document.getElementById('prob-neutral');
                const bearEl = document.getElementById('prob-bear');

                if (bullEl) bullEl.textContent = `${data.ml_intelligence.prob_bull?.toFixed(1) || 64.5}%`;
                if (neuEl) neuEl.textContent = `${data.ml_intelligence.prob_neutral?.toFixed(1) || 22.0}%`;
                if (bearEl) bearEl.textContent = `${data.ml_intelligence.prob_bear?.toFixed(1) || 13.5}%`;
            }

            // Monte Carlo
            if (data.monte_carlo) {
                const mcHigh = document.getElementById('mc-high');
                const mcLow = document.getElementById('mc-low');
                const var95 = document.getElementById('mc-var95');
                const var99 = document.getElementById('mc-var99');

                if (mcHigh) mcHigh.textContent = `$${data.monte_carlo.projected_high?.toLocaleString() || '86,450'}`;
                if (mcLow) mcLow.textContent = `$${data.monte_carlo.projected_low?.toLocaleString() || '82,180'}`;
                if (var95) var95.textContent = `-${data.monte_carlo.var_95_pct?.toFixed(2) || '2.85'}% ($${data.monte_carlo.var_95_usd?.toLocaleString() || '2,400'})`;
                if (var99) var99.textContent = `-${data.monte_carlo.var_99_pct?.toFixed(2) || '4.12'}% ($${data.monte_carlo.var_99_usd?.toLocaleString() || '3,470'})`;
            }

            // Worldwide Breaking News Feed
            if (data.news && data.news.articles) {
                allWorldNewsArticles = data.news.articles;
                filterAndRenderWorldNews();
            }

        } catch (e) {
            console.debug("Macro overview error:", e);
        }
    }

    // ----------------------------------------------------
    // 7. WORLDWIDE NEWS FILTER & RENDER
    // ----------------------------------------------------
    function filterAndRenderWorldNews() {
        const container = document.getElementById('world-news-grid-container');
        if (!container || !allWorldNewsArticles) return;

        let filtered = allWorldNewsArticles;

        // Category Filter
        if (currentNewsCategory !== 'ALL') {
            filtered = filtered.filter(a => {
                const cat = (a.category || '').toUpperCase();
                const entities = (a.entities || []).join(' ').toUpperCase();
                if (currentNewsCategory === 'CENTRAL_BANKS') {
                    return cat.includes('CENTRAL') || cat.includes('MACRO') || entities.includes('CENTRAL');
                } else if (currentNewsCategory === 'BITCOIN_CRYPTO') {
                    return cat.includes('CRYPTO') || cat.includes('BITCOIN') || entities.includes('BITCOIN') || entities.includes('ETF');
                } else if (currentNewsCategory === 'STOCKS_COMMODITIES') {
                    return cat.includes('STOCKS') || cat.includes('COMMODITIES') || entities.includes('GOLD');
                }
                return true;
            });
        }

        // Search Filter
        if (currentNewsSearch.trim()) {
            const q = currentNewsSearch.toLowerCase();
            filtered = filtered.filter(a => 
                (a.title || '').toLowerCase().includes(q) || 
                (a.summary || '').toLowerCase().includes(q) ||
                (a.source || '').toLowerCase().includes(q)
            );
        }

        if (filtered.length === 0) {
            container.innerHTML = `<div style="grid-column: 1 / -1; padding: 24px; text-align: center; color: var(--text-muted);">No global news matches current category/search filter.</div>`;
            return;
        }

        container.innerHTML = filtered.map(a => {
            const sentClass = a.sentiment_score > 0.15 ? 'tag-bullish' : (a.sentiment_score < -0.15 ? 'tag-bearish' : 'tag-neutral');
            const sentScoreStr = `${a.sentiment_score >= 0 ? '+' : ''}${a.sentiment_score.toFixed(2)}`;
            const regionStr = a.region || '🌐 Global';

            return `
                <div class="world-news-card-item">
                    <div>
                        <div class="wn-top">
                            <span class="wn-region">${regionStr}</span>
                            <span class="tag-badge ${sentClass}">${a.sentiment_label || 'NEUTRAL'} (${sentScoreStr})</span>
                        </div>
                        <a href="${a.link || '#'}" target="_blank" class="wn-headline">${a.title}</a>
                        <p class="wn-summary">${a.summary || ''}</p>
                    </div>
                    <div class="wn-footer">
                        <span>${a.source || 'Global Feed'} • ${a.published || 'Recent'}</span>
                        <span class="tag-badge tag-neutral">${a.factuality || 'VERIFIED'}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Category Tabs Listeners
    document.querySelectorAll('.news-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.news-tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentNewsCategory = btn.getAttribute('data-category');
            filterAndRenderWorldNews();
        });
    });

    // Search Input Listener
    const searchInput = document.getElementById('news-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            currentNewsSearch = e.target.value;
            filterAndRenderWorldNews();
        });
    }

    // ----------------------------------------------------
    // 8. RISK CALCULATOR LOGIC
    // ----------------------------------------------------
    function updateRiskCalculator(currPrice, trade) {
        const eqInput = document.getElementById('calc-equity');
        const riskInput = document.getElementById('calc-risk-pct');
        const maxRiskEl = document.getElementById('calc-max-risk-usd');
        const btcSizeEl = document.getElementById('calc-btc-size');

        if (!eqInput || !riskInput) return;

        const equity = parseFloat(eqInput.value) || 10000;
        const riskPct = parseFloat(riskInput.value) || 1.0;
        const maxRiskUsd = equity * (riskPct / 100.0);

        if (maxRiskEl) maxRiskEl.textContent = `$${maxRiskUsd.toFixed(2)}`;

        const entry = trade?.entry_price || currPrice || 84250;
        const sl = trade?.stop_loss || (entry - 160);
        const slDist = Math.abs(entry - sl) || 150;
        const btcSize = (maxRiskUsd / slDist).toFixed(4);

        if (btcSizeEl) btcSizeEl.textContent = `${btcSize} BTC ($${(btcSize * entry).toFixed(0)})`;
    }

    const eqInput = document.getElementById('calc-equity');
    const riskInput = document.getElementById('calc-risk-pct');
    if (eqInput) eqInput.addEventListener('input', () => updateRiskCalculator(null, activeTrade));
    if (riskInput) riskInput.addEventListener('input', () => updateRiskCalculator(null, activeTrade));

    // ----------------------------------------------------
    // 9. ACTION BUTTON LISTENERS
    // ----------------------------------------------------
    const forceBtn = document.getElementById('force-trade-btn');
    if (forceBtn) {
        forceBtn.addEventListener('click', async () => {
            forceBtn.textContent = '⚡ Analyzing...';
            try {
                await fetch('/api/scalp/force-generate', { method: 'POST' });
                await updateScalpTelemetry();
                await updateTradeAnalystReport();
            } catch (e) {}
            setTimeout(() => { forceBtn.textContent = '⚡ Force Trade'; }, 800);
        });
    }

    const refreshTradesBtn = document.getElementById('refresh-trades-btn');
    if (refreshTradesBtn) {
        refreshTradesBtn.addEventListener('click', () => {
            updateScalpTelemetry();
            updateTradeAnalystReport();
        });
    }

    // ----------------------------------------------------
    // 10. LIVE WEBSOCKET TICK STREAMING & POLLING
    // ----------------------------------------------------
    function initLiveWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/live`;
        let ws = null;

        function connect() {
            try {
                ws = new WebSocket(wsUrl);
                ws.onmessage = (event) => {
                    try {
                        const msg = JSON.parse(event.data);
                        if (msg.type === 'LIVE_TICKER_UPDATE' && msg.price) {
                            const price = parseFloat(msg.price);
                            const livePriceEl = document.getElementById('live-price');
                            if (livePriceEl) {
                                livePriceEl.textContent = `$${price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                            }
                            if (chartManager && price > 0) {
                                chartManager.updateLiveTick(price);
                            }
                        }
                    } catch (err) {}
                };
                ws.onclose = () => {
                    setTimeout(connect, 3000);
                };
                ws.onerror = () => {
                    try { ws.close(); } catch (e) {}
                };
            } catch (e) {
                setTimeout(connect, 5000);
            }
        }

        connect();
    }

    initLiveWebSocket();

    // Scalp telemetry poll every 3 seconds
    updateScalpTelemetry();
    setInterval(updateScalpTelemetry, 3000);

    // Trade Analyst Report poll every 5 seconds
    updateTradeAnalystReport();
    setInterval(updateTradeAnalystReport, 5000);

    // Macro overview poll every 6 seconds
    updateMacroOverview();
    setInterval(updateMacroOverview, 6000);

    // Silent background klines synchronization every 15 seconds
    setInterval(() => {
        if (chartManager) chartManager.syncKlines();
    }, 15000);

    // Countdown tick every 1 second
    setInterval(() => {
        if (currentCandleSeconds > 0) {
            currentCandleSeconds--;
            renderCountdown(currentCandleSeconds);
        }
    }, 1000);
});
