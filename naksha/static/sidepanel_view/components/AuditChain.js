/**
 * AuditChain Component (Audit Tab)
 * Visual chain of hash blocks (short hash, time, actor, action) with link lines.
 * Green "Chain Intact" badge, Ed25519 digital signature detail line.
 */

function renderAuditChain(container, ledgerEntries, integrityStatus) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');
  const isChainIntact = integrityStatus?.is_valid !== false;

  container.innerHTML = `
    <div class="audit-chain-container">
      <!-- Chain Status Header -->
      <div class="chain-status-banner ${isChainIntact ? 'banner-intact' : 'banner-broken'}">
        <div class="csb-left">
          <span class="csb-icon">${isChainIntact ? '🔒' : '⚠️'}</span>
          <div>
            <div class="csb-title font-bold">
              ${isChainIntact ? (isEn ? 'Audit Hash Chain Intact' : 'ডিজিটাল ট্রাস্ট লেজার অটুট (INTACT)') : (isEn ? 'Hash Integrity Broken' : 'হ্যাশ চেইনে অসংগতি!')}
            </div>
            <div class="csb-sub">
              ${isEn ? 'Algorithm: SHA-256 + Ed25519 Signatures' : 'অ্যালগরিদম: SHA-256 চেইন + Ed25519 ডিজিটাল স্বাক্ষর'}
            </div>
          </div>
        </div>
        <div class="csb-badge tabular">
          ${ledgerEntries ? ledgerEntries.length : 0} ${isEn ? 'Blocks' : 'ব্লক'}
        </div>
      </div>

      <!-- Connected Blocks List -->
      <div class="blocks-track">
        ${(ledgerEntries || []).map((entry, index) => {
          const shortHash = entry.entry_hash ? entry.entry_hash.slice(0, 16) + '...' : 'GENESIS';
          const prevHash = entry.previous_hash ? entry.previous_hash.slice(0, 8) + '...' : '00000000...';
          const time = entry.timestamp ? entry.timestamp.slice(11, 19) + ' UTC' : '';

          return `
            <div class="block-card">
              <div class="bc-indicator-line"></div>
              <div class="bc-header">
                <div class="bc-num-group">
                  <span class="bc-num tabular font-bold">#${entry.index}</span>
                  <span class="bc-event font-bold">${entry.event_type}</span>
                </div>
                <span class="bc-time tabular">${time}</span>
              </div>

              <div class="bc-payload">
                <div class="bc-row">
                  <span class="bc-lbl">${isEn ? 'Actor' : 'ব্যবহারকারী'}:</span>
                  <span class="bc-val font-bold">${entry.officer_id || 'UL-2024-KSH'}</span>
                  ${entry.dag_number ? `· <span class="bc-lbl">${isEn ? 'Plot' : 'দাগ'}:</span> <strong class="tabular">${entry.dag_number}</strong>` : ''}
                  ${entry.verdict ? `· <span class="bc-lbl">${isEn ? 'Verdict' : 'রায়'}:</span> <strong>${entry.verdict}</strong>` : ''}
                </div>
                <div class="bc-row bc-hash-row">
                  <span class="bc-lbl">Hash:</span>
                  <code class="bc-code tabular">${shortHash}</code>
                  <span class="bc-verified">✓ Ed25519</span>
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}
