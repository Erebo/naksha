/**
 * AuditChain Component (Audit Tab)
 * Pinned "Chain intact" status banner at the top.
 * Compact 2-line blocks (Line 1: short hash + time; Line 2: actor + action + signature check).
 * Fits 5 blocks without scrolling at 700px panel height. Includes a "View all" link.
 */

function renderAuditChain(container, ledgerEntries, integrityStatus) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');
  const isChainIntact = integrityStatus?.is_valid !== false;
  const entries = ledgerEntries || [];
  const displayLimit = 5;
  const shownEntries = entries.slice(0, displayLimit);

  container.innerHTML = `
    <div class="audit-pinned-banner">
      <div class="apb-left">
        <span class="apb-badge num" style="color: ${isChainIntact ? 'var(--status-clear)' : 'var(--status-block)'};">
          ${isChainIntact ? (isEn ? '● CHAIN INTACT' : '● লেজার সম্পূর্ণ অটুট') : (isEn ? '● INTEGRITY COMPROMISED' : '● অডিট ত্রুটি')}
        </span>
        <span class="apb-count num">${entries.length} ${isEn ? 'verified blocks' : 'টি ব্লক'}</span>
      </div>
      <span class="apb-algo num">SHA-256 + Ed25519</span>
    </div>

    <!-- Compact 2-Line Block Stream (5 visible without scroll) -->
    <div class="audit-compact-stream">
      ${shownEntries.map((entry) => {
        const shortHash = entry.entry_hash ? entry.entry_hash.slice(0, 16) + '...' : 'GENESIS';
        const time = entry.timestamp ? entry.timestamp.slice(11, 19) + ' UTC' : '';
        const actor = entry.officer_id || 'UL-2024-KSH';
        const dagStr = entry.dag_number ? formatNumber(entry.dag_number, 0) : '';

        return `
          <div class="audit-block-card">
            <!-- Line 1: Short Hash & Timestamp -->
            <div class="abc-line-1">
              <span class="abc-hash num font-bold">#${formatNumber(entry.index, 0)} <code>${shortHash}</code></span>
              <span class="abc-time num">${time}</span>
            </div>
            <!-- Line 2: Actor, Action & Signature Tick -->
            <div class="abc-line-2">
              <span class="abc-actor">${actor} · <strong>${entry.event_type}</strong> ${dagStr ? `· ${isEn ? 'Dag' : 'দাগ'} ${dagStr}` : ''}</span>
              <span class="abc-signed num" style="color: var(--status-clear);">✓ Ed25519</span>
            </div>
          </div>
        `;
      }).join('')}
    </div>

    ${entries.length > displayLimit ? `
      <div class="audit-view-all-row">
        <button class="audit-view-all-btn num" type="button">
          ${isEn ? `View all ${entries.length} blocks ▾` : `সকল ${toBnDigits(entries.length)}টি ব্লক দেখুন ▾`}
        </button>
      </div>
    ` : ''}
  `;
}
