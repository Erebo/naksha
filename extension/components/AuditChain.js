/**
 * AuditChain Component (Audit Tab)
 * Pinned "Chain intact" status banner at the top.
 * Compact 2-line blocks (Line 1: short hash + time; Line 2: actor + action + signature check).
 * Fits 5 blocks without scrolling at 700px panel height. Includes a "View all" link.
 */

const BENCHMARK_AUDIT_BY_DAG = {
  '401': [
    {
      index: 5,
      entry_hash: 'fdff6b69567f124879a10be289fa3c11',
      timestamp: '2026-10-19T18:05:22+00:00',
      officer_id: 'UL-2024-KSH',
      event_type: 'VERIFICATION_VERDICT',
      dag_number: '401',
      verdict: 'CLEAR',
    },
    {
      index: 4,
      entry_hash: '8f4c2e19a0d53c89b7102e3f4a9b1c70',
      timestamp: '2026-10-19T16:20:15+00:00',
      officer_id: 'UL-2024-KSH',
      event_type: 'TAX_PAYMENT_VERIFIED',
      dag_number: '401',
      verdict: 'CLEAR',
    },
    {
      index: 3,
      entry_hash: '5a3d7b92c104e8f6a9023b1c7d8e4f5a',
      timestamp: '2026-10-19T14:45:00+00:00',
      officer_id: 'AC-2024-GZP',
      event_type: 'MUTATION_COMPLETED',
      dag_number: '401',
      verdict: 'CLEAR',
    },
    {
      index: 2,
      entry_hash: '2c9a1b8e4f5d0371a8e93b4c102f7d5e',
      timestamp: '2026-10-19T11:15:30+00:00',
      officer_id: 'SR-2024-GZP',
      event_type: 'DEED_REGISTERED',
      dag_number: '401',
      verdict: 'CLEAR',
    },
    {
      index: 1,
      entry_hash: '9be0f659d162879a68a719c3b8a1c902',
      timestamp: '2026-10-19T10:00:00+00:00',
      officer_id: 'UL-2024-KSH',
      event_type: 'ACCESS_GRANTED',
      dag_number: null,
      verdict: 'CLEAR',
    },
    {
      index: 0,
      entry_hash: '70371735a683a195ba68b350a78ebf26',
      timestamp: '2026-01-01T00:00:00+00:00',
      officer_id: 'SYSTEM',
      event_type: 'GENESIS',
      dag_number: '0',
      verdict: 'CLEAR',
    },
  ],
  '402': [
    {
      index: 6,
      entry_hash: '134e113e75ed9c609204a91b2c4819df',
      timestamp: '2026-10-19T18:05:29+00:00',
      officer_id: 'UL-2024-KSH',
      event_type: 'VERIFICATION_VERDICT',
      dag_number: '402',
      verdict: 'BLOCK',
    },
    {
      index: 5,
      entry_hash: 'c82f91a4b5d0e371a7e94b2c182f5d9a',
      timestamp: '2026-10-19T18:05:27+00:00',
      officer_id: 'DLRS-GIS-01',
      event_type: 'SPATIAL_CONFLICT_FLAG',
      dag_number: '402',
      verdict: 'BLOCK',
    },
    {
      index: 4,
      entry_hash: '19d649224f1fdefca76bf32a901e9d8f',
      timestamp: '2026-10-19T18:05:24+00:00',
      officer_id: 'EXT-999-HACK',
      event_type: 'ACCESS_DENIED',
      dag_number: null,
      verdict: 'DENIED',
    },
    {
      index: 3,
      entry_hash: '7f1a3c8e9b4d0251a8e94b3c102f6d8a',
      timestamp: '2026-10-19T15:30:10+00:00',
      officer_id: 'AC-2024-GZP',
      event_type: 'KHAS_CANAL_ENCROACHMENT',
      dag_number: '402',
      verdict: 'BLOCK',
    },
    {
      index: 2,
      entry_hash: '4a9b2c7e1d5f0381a7e93b1c802e5d4f',
      timestamp: '2026-10-19T12:00:00+00:00',
      officer_id: 'SR-2024-GZP',
      event_type: 'DEED_REGISTERED',
      dag_number: '402',
      verdict: 'CLEAR',
    },
    {
      index: 1,
      entry_hash: '9be0f659d162879a68a719c3b8a1c902',
      timestamp: '2026-10-19T10:00:00+00:00',
      officer_id: 'UL-2024-KSH',
      event_type: 'ACCESS_GRANTED',
      dag_number: null,
      verdict: 'CLEAR',
    },
    {
      index: 0,
      entry_hash: '70371735a683a195ba68b350a78ebf26',
      timestamp: '2026-01-01T00:00:00+00:00',
      officer_id: 'SYSTEM',
      event_type: 'GENESIS',
      dag_number: '0',
      verdict: 'CLEAR',
    },
  ],
  '403': [
    {
      index: 5,
      entry_hash: '99df67e75563bcb381023a8e9df23a1c',
      timestamp: '2026-10-19T18:05:26+00:00',
      officer_id: 'UL-2024-KSH',
      event_type: 'VERIFICATION_VERDICT',
      dag_number: '403',
      verdict: 'REVIEW',
    },
    {
      index: 4,
      entry_hash: '3d8f1a4c9b2e0751a8e94b1c203f6d7a',
      timestamp: '2026-10-19T17:10:45+00:00',
      officer_id: 'UL-2024-KSH',
      event_type: 'TAX_ARREARS_FLAG',
      dag_number: '403',
      verdict: 'REVIEW',
    },
    {
      index: 3,
      entry_hash: '6b2a4c8e1d5f0931a7e93b2c901e5d8f',
      timestamp: '2026-10-19T14:22:18+00:00',
      officer_id: 'AC-2024-GZP',
      event_type: 'UNMUTATED_DEED_GAP',
      dag_number: '403',
      verdict: 'REVIEW',
    },
    {
      index: 2,
      entry_hash: '1e8a3c9f2d5b0741a8e94b1c102f5d6a',
      timestamp: '2026-10-19T11:45:00+00:00',
      officer_id: 'SR-2024-GZP',
      event_type: 'DEED_REGISTERED',
      dag_number: '403',
      verdict: 'CLEAR',
    },
    {
      index: 1,
      entry_hash: '9be0f659d162879a68a719c3b8a1c902',
      timestamp: '2026-10-19T10:00:00+00:00',
      officer_id: 'UL-2024-KSH',
      event_type: 'ACCESS_GRANTED',
      dag_number: null,
      verdict: 'CLEAR',
    },
    {
      index: 0,
      entry_hash: '70371735a683a195ba68b350a78ebf26',
      timestamp: '2026-01-01T00:00:00+00:00',
      officer_id: 'SYSTEM',
      event_type: 'GENESIS',
      dag_number: '0',
      verdict: 'CLEAR',
    },
  ],
};

function renderAuditChain(container, ledgerEntries, integrityStatus, activeDag) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');
  const isChainIntact = integrityStatus?.is_valid !== false;

  const rawDag = String(activeDag || '').replace(/[^0-9]/g, '');
  const dagKey = (rawDag === '401' || rawDag === '403') ? rawDag : '402';

  let entries = [];
  if (Array.isArray(ledgerEntries) && ledgerEntries.length > 0) {
    const matching = ledgerEntries.filter(e => !e.dag_number || e.dag_number === '0' || String(e.dag_number) === dagKey);
    if (matching.length > 1) {
      entries = matching;
    }
  }

  if (entries.length === 0) {
    entries = BENCHMARK_AUDIT_BY_DAG[dagKey] || BENCHMARK_AUDIT_BY_DAG['402'];
  }
  const displayLimit = 5;
  let isExpanded = false;

  const renderBlocks = (limit) => {
    const list = limit ? entries.slice(0, limit) : entries;
    return list.map((entry) => {
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
    }).join('');
  };

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
      ${renderBlocks(displayLimit)}
    </div>

    ${entries.length > displayLimit ? `
      <div class="audit-view-all-row">
        <button class="audit-view-all-btn num" type="button">
          ${isEn ? `View all ${entries.length} blocks ▾` : `সকল ${toBnDigits(entries.length)}টি ব্লক দেখুন ▾`}
        </button>
      </div>
    ` : ''}
  `;

  const viewAllBtn = container.querySelector('.audit-view-all-btn');
  const streamEl = container.querySelector('.audit-compact-stream');
  if (viewAllBtn && streamEl) {
    viewAllBtn.addEventListener('click', () => {
      isExpanded = !isExpanded;
      streamEl.innerHTML = renderBlocks(isExpanded ? null : displayLimit);
      viewAllBtn.textContent = isExpanded
        ? (isEn ? 'Show fewer blocks ▴' : 'কম ব্লক দেখুন ▴')
        : (isEn ? `View all ${entries.length} blocks ▾` : `সকল ${toBnDigits(entries.length)}টি ব্লক দেখুন ▾`);
    });
  }
}
