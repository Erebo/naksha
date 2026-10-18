/**
 * TaxChart Component (Tax & Payer Tab)
 * Donut/Stacked visualization of neighboring plots by status (Paid / Arrears / Payer != Owner).
 * Payment history timeline showing who paid vs who the khatian owner is, highlighting mismatches.
 */

function renderTaxChart(container, taxData) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');
  const neighbors = taxData.neighbors || [
    { dag: '401', khatian: '88', owner: 'মোঃ রহিম শেখ', payer: 'মোঃ রহিম শেখ', status: 'paid', area: '4.37' },
    { dag: '402', khatian: '120', owner: 'মোঃ আব্দুল করিম', payer: 'মোঃ আব্দুল করিম', status: 'paid', area: '5.10' },
    { dag: '403', khatian: '125', owner: 'আব্দুল মজিদ', payer: 'অজ্ঞাত করদাতা', status: 'arrears', area: '5.53', mismatch: true },
  ];

  const paidCount = neighbors.filter(n => n.status === 'paid').length;
  const arrearsCount = neighbors.filter(n => n.status === 'arrears').length;
  const mismatchCount = neighbors.filter(n => n.mismatch).length;

  container.innerHTML = `
    <div class="tax-chart-container">
      <div class="tax-overview-row">
        <!-- Mini Status Distribution -->
        <div class="tax-stat-pill" style="border-left: 3px solid var(--status-clear);">
          <span class="stat-num tabular font-bold" style="color: var(--status-clear);">${paidCount}</span>
          <span class="stat-lbl">${isEn ? 'Tax Paid' : 'কর পরিশোধিত'}</span>
        </div>
        <div class="tax-stat-pill" style="border-left: 3px solid var(--status-review);">
          <span class="stat-num tabular font-bold" style="color: var(--status-review);">${arrearsCount}</span>
          <span class="stat-lbl">${isEn ? 'In Arrears' : 'কর বকেয়া'}</span>
        </div>
        <div class="tax-stat-pill" style="border-left: 3px solid var(--status-block);">
          <span class="stat-num tabular font-bold" style="color: var(--status-block);">${mismatchCount}</span>
          <span class="stat-lbl">${isEn ? 'Payer Mismatch' : 'করদাতা অমিল'}</span>
        </div>
      </div>

      <div class="tax-table-header">
        <span>${isEn ? 'Neighbor Parcel Tax & Payer Auditing' : 'প্রতিবেশী প্লট কর স্থিতি ও করদাতা নিরীক্ষা'}</span>
      </div>

      <!-- Neighbor Plot Assessment Cards -->
      <div class="tax-cards-list">
        ${neighbors.map(n => `
          <div class="tax-card ${n.mismatch ? 'mismatch-row' : ''}">
            <div class="tc-top">
              <span class="tc-dag font-bold">${isEn ? 'Dag' : 'দাগ'} <span class="tabular">${n.dag}</span></span>
              <span class="tc-badge ${n.status === 'paid' ? 'badge-paid' : 'badge-arrears'}">
                ${n.status === 'paid' ? (isEn ? 'Paid' : 'পরিশোধিত') : (isEn ? '3 Yrs Arrears' : '৩ বছর বকেয়া')}
              </span>
            </div>
            <div class="tc-grid">
              <div class="tc-item">
                <span class="tc-label">${isEn ? 'Owner' : 'খতিয়ান মালিক'}</span>
                <span class="tc-val">${n.owner}</span>
              </div>
              <div class="tc-item">
                <span class="tc-label">${isEn ? 'Last Payer' : 'দাখিলা করদাতা'}</span>
                <span class="tc-val ${n.mismatch ? 'text-danger font-bold' : ''}">
                  ${n.payer} ${n.mismatch ? '⚠️' : ''}
                </span>
              </div>
            </div>
            ${n.mismatch ? `
              <div class="tc-warning-line">
                ⚠️ ${isEn ? 'Payer differs from recorded Khatian title-holder.' : 'খতিয়ানভুক্ত মালিকের পরিবর্তে তৃতীয় পক্ষের কর প্রদানের তথ্য।'}
              </div>
            ` : ''}
          </div>
        `).join('')}
      </div>
    </div>
  `;
}
