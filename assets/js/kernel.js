(() => {
    'use strict';

    const $ = (id) => document.getElementById(id);

    const searchInput   = $('search-input');
    const modelsContainer = $('models-container');
    const loadingSpinner  = $('loading-spinner');
    const generatedAtSpan = $('generated-at');
    const tabsNav         = $('tabs-nav');
    const resultCount     = $('result-count');
    const toastContainer  = $('toast-container');

    let globalData    = null;   // api/models.json full payload
    let activeTab     = 'all'; // current provider tab key
    let maxScore      = 0;     // global max intelligence score (for bar scale)

    // ── Fetch ───────────────────────────────────────────────────────────────
    // Menggunakan parameter cache-buster agar selalu mendapat data terbaru dari GitHub Pages
    fetch('api/models.json?t=' + Date.now())
        .then(r => {
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            return r.json();
        })
        .then(data => {
            globalData = data;

            // compute global max score for scaling bars
            for (const p of Object.values(data.providers)) {
                for (const m of (p.models || [])) {
                    if (m.intelligence_score != null && m.intelligence_score > maxScore)
                        maxScore = m.intelligence_score;
                }
            }

            // format sync date
            generatedAtSpan.innerHTML = `Last Sync: <strong>${new Date(data.generated_at).toLocaleString()}</strong>`;

            // Build tabs
            buildTabs(data.providers);

            loadingSpinner.style.display = 'none';
            renderView();
        })
        .catch(err => {
            loadingSpinner.innerHTML = `
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <p style="color:#EF4444">Failed to load api/models.json.<br><small>Open this page via a web server (not directly as a file).</small></p>
            `;
            console.error('Fetch error:', err);
        });

    // ── Build provider tabs dynamically ─────────────────────────────────────
    function buildTabs(providers) {
        // Clear existing injected tabs (keep "All")
        tabsNav.querySelectorAll('.tab-btn:not([data-tab="all"])').forEach(el => el.remove());

        for (const [key, data] of Object.entries(providers)) {
            const count = (data.models || []).length;
            if (count === 0) continue;

            const btn = document.createElement('button');
            btn.className = 'tab-btn';
            btn.dataset.tab = key;
            btn.innerHTML = `${capitalize(key)} <span class="tab-count">${count}</span>`;
            btn.addEventListener('click', () => setTab(key));
            tabsNav.appendChild(btn);
        }

        // Update "All" count
        const allCount = Object.values(providers).reduce((s, p) => s + (p.models||[]).length, 0);
        $('tabs-nav').querySelector('[data-tab="all"]').innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
            All <span class="tab-count">${allCount}</span>
        `;
    }

    function setTab(key) {
        activeTab = key;
        tabsNav.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === key);
        });
        renderView();
    }

    // Bind "All" tab manually (it's already in HTML)
    tabsNav.querySelector('[data-tab="all"]').addEventListener('click', () => setTab('all'));

    // ── Search real-time ─────────────────────────────────────────────────────
    searchInput.addEventListener('input', renderView);

    // ── Render ───────────────────────────────────────────────────────────────
    function renderView() {
        if (!globalData) return;

        const query = searchInput.value.toLowerCase().trim();
        const providers = globalData.providers;
        const fragment = document.createDocumentFragment();
        let totalShown = 0;

        const providerKeys = activeTab === 'all'
            ? Object.keys(providers)
            : [activeTab];

        for (const key of providerKeys) {
            const provData = providers[key];
            if (!provData) continue;

            const models = provData.models || [];
            const filtered = query
                ? models.filter(m =>
                    (m.id   || '').toLowerCase().includes(query) ||
                    (m.name || '').toLowerCase().includes(query))
                : models;

            if (filtered.length === 0) continue;
            totalShown += filtered.length;

            fragment.appendChild(buildProviderSection(key, provData.tier, filtered, provData.website));
        }

        modelsContainer.innerHTML = '';

        if (totalShown === 0) {
            modelsContainer.innerHTML = `
                <div class="no-results">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="opacity:.4;margin-bottom:.75rem"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                    <p>No models found for <strong>"${escHtml(query)}"</strong></p>
                </div>`;
            resultCount.textContent = '0 results';
        } else {
            modelsContainer.appendChild(fragment);
            resultCount.textContent = `${totalShown} model${totalShown !== 1 ? 's' : ''}`;
        }
    }

    function buildProviderSection(key, tier, models, website) {
        const section = document.createElement('div');
        section.className = 'provider-section';

        // Header
        const header = document.createElement('div');
        header.className = 'provider-header';
        
        let websiteBtn = '';
        if (website) {
            websiteBtn = `<a href="${escAttr(website)}" target="_blank" rel="noopener noreferrer" class="provider-action-btn">🔑 Get API Key</a>`;
        }

        header.innerHTML = `
            <div class="provider-header-left">
                <h2 class="provider-name">${capitalize(key)}</h2>
                <span class="tier-badge">${tier} tier</span>
                <span class="provider-model-count">${models.length} model${models.length !== 1 ? 's' : ''}</span>
            </div>
            ${websiteBtn}
        `;
        section.appendChild(header);

        // Grid
        const grid = document.createElement('div');
        grid.className = 'models-grid';

        models.forEach((m, idx) => {
            grid.appendChild(buildCard(m, idx + 1));
        });

        section.appendChild(grid);
        return section;
    }

    function buildCard(m, rank) {
        const card = document.createElement('div');
        card.className = 'model-card';

        const score  = m.intelligence_score;
        const hasScore = score != null;

        // Rank badge
        const rankBadge = hasScore
            ? `<span class="rank-badge ranked">#${rank}</span>`
            : `<span class="rank-badge unranked">#${rank}</span>`;

        // Intelligence bar
        let intelBar = '';
        if (hasScore && maxScore > 0) {
            const pct = ((score / maxScore) * 100).toFixed(1);
            intelBar = `
                <div class="intel-bar-row">
                    <span class="intel-label">IQ</span>
                    <div class="intel-bar-track"><div class="intel-bar-fill" style="width:${pct}%"></div></div>
                    <span class="intel-score-val">${score.toFixed(1)}</span>
                </div>`;
        }

        // Limits badges
        const limitsHtml = buildLimits(m);

        card.innerHTML = `
            ${rankBadge}
            <div class="model-name">${escHtml(m.name || m.id)}</div>
            ${intelBar}
            <button class="model-id" data-copy="${escAttr(m.id)}" title="Click to copy">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                ${escHtml(m.id)}
            </button>
            ${limitsHtml ? `<div class="card-limits">${limitsHtml}</div>` : ''}
        `;

        return card;
    }

    function buildLimits(m) {
        let parts = [];
        if (m.context_length) parts.push(`Ctx: <strong>${m.context_length.toLocaleString()}</strong>`);
        if (m.limits && Object.keys(m.limits).length) {
            for (const [k, v] of Object.entries(m.limits)) {
                if (v != null) parts.push(`${k}: <strong>${v}</strong>`);
            }
        }
        return parts.map(p => `<span class="limit-badge">${p}</span>`).join('');
    }

    // ── Copy to clipboard (event delegation) ────────────────────────────────
    modelsContainer.addEventListener('click', e => {
        const btn = e.target.closest('.model-id');
        if (!btn) return;
        const text = btn.dataset.copy;
        navigator.clipboard.writeText(text)
            .then(() => showToast(`Copied <strong>${escHtml(text)}</strong>`))
            .catch(() => showToast('Failed to copy (no HTTPS/permissions)'));
    });

    // ── Toast ────────────────────────────────────────────────────────────────
    function showToast(html) {
        const el = document.createElement('div');
        el.className = 'toast';
        el.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
            <span>${html}</span>
        `;
        toastContainer.appendChild(el);
        void el.offsetWidth;  // reflow
        el.classList.add('show');
        setTimeout(() => {
            el.classList.remove('show');
            setTimeout(() => el.remove(), 350);
        }, 3000);
    }

    // ── Utils ────────────────────────────────────────────────────────────────
    function capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    function escHtml(s = '') {
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
    function escAttr(s = '') {
        return String(s).replace(/"/g,'&quot;');
    }
})();
