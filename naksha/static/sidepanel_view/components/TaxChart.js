/**
 * TaxChart Component (Tax & Neighbor Tab)
 * Donut / status of neighboring plots (Paid / Arrears / Payer != Owner).
 * Payment history audit marking payer vs owner mismatches.
 */

function renderTaxChart(container, data) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');
  const neighbors = data.neighbors || [
    { dag: '401', khatian: '88', owner: isEn ? 'Rahim Sheikh' : 'মোঃ রহিম শেখ', payer: isEn ? 'Rahim Sheikh' : 'মোঃ রহিম শেখ', status: 'paid', area: '4.37' },
    { dag: '402', khatian: '120', owner: isEn ? 'Abdul Karim' : 'মোঃ আব্দুল করিম', payer: isEn ? 'Abdul Karim' : 'মোঃ আব্দুল করিম', status: 'paid', area: '5.10' },
    { dag: '403', khatian: '125', owner: isEn ? 'Abdul Majid' : 'আব্দুল মজিদ', payer: isEn ? 'Unknown Payer' : 'অজ্ঞাত করদাতা', status: 'arrears', area: '5.53', mismatch: true },
  ];

  const paidCount = neighbors.filter(n => n.status === 'paid').length;
  const arrearsCount = neighbors.filter(n => n.status === 'arrears').length;
  const mismatchCount = neighbors.filter(n => n.mismatch).length;

  container.innerHTML = `
    <div class="bento-card">
      <div class="bento-card-header">
        <span class="bento-title">${isEn ? 'Neighbor Plots Tax Audit' : 'প্রতিবেশী প্লট কর স্থিতি'}</span>
        <span class="bento-badge num">${isEn ? `${neighbors.length} plots verified` : `${formatNumber(neighbors.length, 0)}টি প্লট যাচাইকৃত`}</span>
      </div>

      <!-- Status Pills Summary -->
      <div class="tax-status-metric-row">
        <div class="tsm-item">
          <span class="tsm-val num font-bold" style="color: var(--status-clear);">${formatNumber(paidCount, 0)}</span>
          <span class="tsm-lbl">${isEn ? 'Paid' : 'পরিশোধিত'}</span>
        </div>
        <div class="tsm-item">
          <span class="tsm-val num font-bold" style="color: var(--status-review);">${formatNumber(arrearsCount, 0)}</span>
          <span class="tsm-lbl">${isEn ? 'In Arrears' : 'বকেয়া'}</span>
        </div>
        <div class="tsm-item">
          <span class="tsm-val num font-bold" style="color: var(--status-block);">${formatNumber(mismatchCount, 0)}</span>
          <span class="tsm-lbl">${isEn ? 'Payer Mismatch' : 'করদাতা অমিল'}</span>
        </div>
      </div>

      <!-- Neighbor Plot Cards List -->
      <div class="tax-parcel-rows">
        ${neighbors.map(n => `
          <div class="tax-parcel-card ${n.mismatch ? 'mismatch-flagged' : ''}">
            <div class="tpc-top">
              <span class="tpc-dag font-bold num">${isEn ? 'Dag' : 'দাগ'} ${formatNumber(n.dag, 0)}</span>
              <span class="tpc-badge num" style="color: ${n.status === 'paid' ? 'var(--status-clear)' : 'var(--status-review)'};">
                ${n.status === 'paid' ? (isEn ? 'Paid' : 'পরিশোধিত') : (isEn ? '3 Yrs Arrears' : '৩ বছর বকেয়া')}
              </span>
            </div>
            <div class="tpc-details">
              <span>${isEn ? 'Owner' : 'খতিয়ান'}: <strong>${n.owner}</strong></span>
              <span>${isEn ? 'Payer' : 'করদাতা'}: <strong style="${n.mismatch ? 'color: var(--status-review);' : ''}">${n.payer} ${n.mismatch ? '•' : ''}</strong></span>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}
