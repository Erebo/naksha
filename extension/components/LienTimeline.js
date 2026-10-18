/**
 * LienTimeline Component (Liens & Locks Tab)
 * Vertical timeline of mortgages and acquisition locks with bank, date, status badge.
 * Friendly empty state: "No active liens" with a green check icon.
 */

function renderLienTimeline(container, lienData) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');
  const liens = (lienData && lienData.liens) ? lienData.liens : [];

  if (liens.length === 0) {
    container.innerHTML = `
      <div class="empty-lien-state">
        <div class="empty-icon-circle">✓</div>
        <div class="empty-title">${isEn ? 'No Active Liens or Mortgages' : 'কোনো সক্রিয় দায় বা লিয়েন নেই'}</div>
        <div class="empty-desc">
          ${isEn 
            ? 'No bank mortgage, court attachment, or government acquisition lock registered against this parcel.'
            : 'ব্যাংক দায়, আদালত ক্রোকাদেশ বা সরকারি অধিগ্রহণ সংক্রান্ত কোনো বিধিনিষেধ এই দাগে পাওয়া যায়নি।'}
        </div>
        <div class="empty-chip tabular">CIB / AC Land Clean Record</div>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="lien-timeline-container">
      <div class="lien-header">
        <span>${isEn ? 'Encumbrances & Injunctions' : 'আর্থিক দায় ও আইনি স্থগিতাদেশ'}</span>
      </div>
      <div class="lien-list">
        ${liens.map(l => `
          <div class="lien-card">
            <div class="lc-header">
              <span class="lc-bank font-bold">${l.institution}</span>
              <span class="lc-badge ${l.status === 'active' ? 'badge-block' : 'badge-clear'}">
                ${l.status.toUpperCase()}
              </span>
            </div>
            <div class="lc-details">
              <span>${isEn ? 'Amount' : 'দায়ের পরিমাণ'}: <strong class="tabular">${l.amount}</strong></span> ·
              <span>${isEn ? 'Date' : 'তারিখ'}: <strong class="tabular">${l.date}</strong></span>
            </div>
            <p class="lc-desc">${l.description}</p>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}
