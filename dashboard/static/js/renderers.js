/**
 * renderers.js — Agent-specific result formatters.
 *
 * Each renderer receives (envelope, container):
 *   envelope  — the full server response { ok, result, saved_to, timestamp }
 *   container — the DOM element to render into
 *
 * To add a renderer for a new agent, add a function to the renderers
 * map inside dispatch(), keyed by agent slug (lowercase).
 */

const AgentRenderers = (() => {

    // ── Helpers ───────────────────────────────────────────────────────────

    function fmt(amount, currencyCode = 'GBP') {
        return new Intl.NumberFormat('en-GB', {
            style:                 'currency',
            currency:              currencyCode,
            minimumFractionDigits: 2,
        }).format(parseFloat(amount) || 0);
    }

    function blockLabel(text) {
        return `<div class="block-label">${text}</div>`;
    }

    // ── Recommendations renderer ──────────────────────────────────────────
    // Handles three formats the model may return:
    //   1. Array of plain strings  → styled <ul> list
    //   2. Array of objects        → card grid
    //   3. Plain string            → paragraph

    function renderRecs(recs) {
        if (!recs) return '';
        if (Array.isArray(recs)) {
            if (recs.length === 0) return '';

            // Plain string array (most common from 3b models)
            if (typeof recs[0] === 'string') {
                const items = recs.map(r => `<li>${r}</li>`).join('');
                return `<ul class="recs-list">${items}</ul>`;
            }

            // Object array { description, suggested_action }
            const cards = recs.map(r => {
                const title  = r.description || r.title || String(r);
                const detail = r.suggested_action || r.detail || '';
                return `
                    <div class="rec-card">
                        <div class="rec-title">${title}</div>
                        ${detail ? `<div class="rec-detail">${detail}</div>` : ''}
                    </div>`;
            }).join('');
            return `<div class="recs-grid">${cards}</div>`;
        }
        // Plain string
        return `<p class="recs-text">${recs}</p>`;
    }

    // ── Saved path + timestamp bar ────────────────────────────────────────

    function savedInfoBar(savedTo, timestamp) {
        if (!savedTo && !timestamp) return '';
        return `
            <div class="saved-info">
                ${savedTo ? `
                    <div>
                        <span class="saved-info-label">Saved to&nbsp;</span>
                        <span class="saved-info-path">${savedTo}</span>
                    </div>` : ''}
                ${timestamp ? `
                    <div>
                        <span class="saved-info-label">Timestamp&nbsp;</span>
                        <span class="saved-info-ts">${timestamp}</span>
                    </div>` : ''}
            </div>`;
    }

    // ── Download ──────────────────────────────────────────────────────────

    let _dlData = null;

    function prepareDownload(data) { _dlData = data; }

    function triggerDownload() {
        if (!_dlData) return;
        const ts   = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const slug = (
            _dlData.agent ||
            _dlData.result?.agent ||
            'result'
        ).toLowerCase();
        const blob = new Blob(
            [JSON.stringify(_dlData, null, 2)],
            { type: 'application/json' }
        );
        const url = URL.createObjectURL(blob);
        const a   = Object.assign(document.createElement('a'), {
            href:     url,
            download: `maestro_${slug}_${ts}.json`,
        });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // ── RATE renderer ─────────────────────────────────────────────────────

    function rate(envelope, container) {
        const result = envelope.result || envelope;
        const q      = result.quote;

        if (!q || q.parse_error) { _json(envelope, container); return; }

        prepareDownload(envelope);                // store full envelope for download

        const cur    = q.currency || 'GBP';
        const f      = n => fmt(n, cur);
        const vatPct = Math.round((q.vat_rate || 0) * 100);

        const rows = (q.line_items || []).map(item => `
            <tr>
                <td class="li-desc">${item.description}</td>
                <td class="li-num">${item.quantity}</td>
                <td class="li-unit">${item.unit}</td>
                <td class="li-num">${f(item.unit_price)}</td>
                <td class="li-num li-total">${f(item.total)}</td>
            </tr>`).join('');

        container.innerHTML = `

            ${savedInfoBar(envelope.saved_to, envelope.timestamp)}

            <div class="quote-card">

                <div class="quote-header">
                    <div>
                        <div class="quote-badge">Studio Quote</div>
                        <div class="quote-client">${q.client || '—'}</div>
                        <div class="quote-meta">
                            ${(q.project_type || '').toUpperCase()} &middot; ${cur}
                            &middot; Valid ${q.quote_valid_days || 30} days
                        </div>
                    </div>
                    <div class="quote-total-pill">
                        <div class="quote-total-label">Total</div>
                        <div class="quote-total-amount">${f(q.grand_total)}</div>
                        <button class="btn-download"
                                onclick="AgentRenderers.triggerDownload()">
                            ↓ Download JSON
                        </button>
                    </div>
                </div>

                <table class="line-items-table">
                    <thead>
                        <tr>
                            <th class="li-desc">Description</th>
                            <th class="li-num">Qty</th>
                            <th class="li-unit">Unit</th>
                            <th class="li-num">Unit Price</th>
                            <th class="li-num li-total">Line Total</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>

                <div class="totals-block">
                    <div class="totals-row">
                        <span>Subtotal</span>
                        <span>${f(q.subtotal)}</span>
                    </div>
                    <div class="totals-row">
                        <span>VAT (${vatPct}%)</span>
                        <span>${f(q.vat_amount)}</span>
                    </div>
                    <div class="totals-row grand-total">
                        <span>Grand Total</span>
                        <span>${f(q.grand_total)}</span>
                    </div>
                </div>

                <div class="payment-block">
                    ${blockLabel('Payment Terms')}
                    <div class="payment-row">
                        <span>Deposit required (50%)</span>
                        <span class="deposit-amount">${f(q.deposit_required)}</span>
                    </div>
                    <div class="payment-row">
                        <span>Balance due on delivery</span>
                        <span>${f(q.balance_due)}</span>
                    </div>
                    <div class="payment-terms">${q.payment_terms || ''}</div>
                </div>

                ${q.recommendations && q.recommendations.length ? `
                <div class="recs-block">
                    ${blockLabel('Recommendations')}
                    ${renderRecs(q.recommendations)}
                </div>` : ''}

            </div>`;
    }

    // ── JSON fallback (agents without a dedicated renderer) ───────────────

    function _json(envelope, container) {
        container.innerHTML =
            `<pre class="json-fallback">${JSON.stringify(envelope, null, 2)}</pre>`;
    }

    // ── Public API ────────────────────────────────────────────────────────

    function dispatch(agentSlug, envelope, container) {
        const renderers = {
            rate,
            // book:   book,
            // client: client,
        };
        const fn = renderers[(agentSlug || '').toLowerCase()];
        (typeof fn === 'function' ? fn : _json)(envelope, container);
    }

    return { dispatch, triggerDownload };

})();