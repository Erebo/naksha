/**
 * LienTimeline Component (Liens & Encumbrances Tab)
 * Vertical timeline of mortgages & locks with status badges.
 * Friendly, minimalist empty state when clean.
 */

function renderLienTimeline(container, data) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');
  const liens = data?.liens || [];

  if (liens.length === 0) {
    container.innerHTML = `
      <div class="bento-card bento-empty-center">
        <div class="empty-icon-ring" style="color: var(--status-clear);">
          ${ICONS.shield}
        </div>
        <div class="empty-headline font-bold">
          ${isEn ? 'No Active Liens or Locks' : 'কোনো সক্রিয় দায় বা লিয়েন নেই'}
        </div>
        <div class="empty-subtext">
          ${isEn 
            ? 'No bank mortgage, court attachment, or government acquisition lock registered against this parcel.' 
            : 'ব্যাংক দায়, বন্ধক, আদালত ক্রোকাদেশ বা সরকারি অধিগ্রহণ সংক্রান্ত কোনো বিধিনিষেধ পাওয়া যায়নি।'}
        </div>
        <div class="empty-tag num">CIB / AC Land Clean Record</div>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="bento-card">
      <div class="bento-card-header">
        <span class="bento-title">${isEn ? 'Active Encumbrances' : 'আর্থিক দায় ও আইনি স্থগিতাদেশ'}</span>
      </div>
      <div class="lien-items-list">
        ${liens.map(l => `
          <div class="lien-item-card">
            <div class="lic-top">
              <span class="lic-bank font-bold">${l.institution}</span>
              <span class="lic-badge num" style="color: var(--status-block);">${l.status}</span>
            </div>
            <div class="lic-meta num">${l.amount} · ${l.date}</div>
            <p class="lic-desc">${l.description}</p>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}
