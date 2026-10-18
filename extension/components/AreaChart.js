/**
 * AreaChart Component (Bento Grid Card A & Card B)
 * Card A: Area comparison bars (CS, Deed claim 6.0, DLRS 5.1) with tolerance band ±0.20 dec and excess in red.
 * Card B: Khas overlap donut (0.90 of 6.00 dec = 15%).
 * Tabular numerals, strict language formatting, max 2 lines of text per card.
 */

function renderAreaChart(container, areaData) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');

  const csArea = areaData.csArea || 18.0;
  const deedArea = areaData.deedArea || 6.00;
  const dlrsArea = areaData.dlrsArea || 5.10;
  const conflictArea = areaData.conflictArea || 0.0;
  const isEncroachment = conflictArea >= 0.20;

  const maxVal = Math.max(deedArea, dlrsArea, 7.0);
  const deedPct = Math.min(100, Math.round((deedArea / maxVal) * 100));
  const dlrsPct = Math.min(100, Math.round((dlrsArea / maxVal) * 100));
  const tolerancePct = Math.min(100, Math.round(((dlrsArea + 0.20) / maxVal) * 100));

  const khasPct = Math.min(100, Math.round((conflictArea / (deedArea || 1)) * 100));
  const strokeDash = Math.round((khasPct / 100) * 125);

  const deedAreaStr = formatNumber(deedArea) + ' ' + (isEn ? 'dec' : 'শতক');
  const dlrsAreaStr = formatNumber(dlrsArea) + ' ' + (isEn ? 'dec' : 'শতক');
  const conflictAreaStr = formatNumber(conflictArea) + ' ' + (isEn ? 'dec' : 'শতক');
  const khasPctStr = (isEn ? String(khasPct) : toBnDigits(khasPct)) + '%';

  container.innerHTML = `
    <div class="bento-row-cards">
      <!-- Card A: Area Comparison Horizontal Bars -->
      <div class="bento-card card-area-comparison">
        <div class="bento-card-header">
          <span class="bento-title">${isEn ? 'Area Tolerance Comparison' : 'জমির পরিমাপ ও সংবিধিবদ্ধ সীমা'}</span>
          <span class="bento-badge num">${isEn ? '±0.20 dec limit' : 'সীমা ±০.২০ শতক'}</span>
        </div>

        <div class="bento-bars-list">
          <!-- Deed Claim -->
          <div class="b-bar-item">
            <div class="b-bar-meta">
              <span class="b-bar-lbl">${isEn ? 'Deed Claim' : 'দলিলে দাবি'}</span>
              <span class="b-bar-num num" style="color: var(--layer-deed);">${deedAreaStr}</span>
            </div>
            <div class="b-track">
              <div class="b-fill" style="width: ${deedPct}%; background-color: var(--layer-deed);"></div>
              ${isEncroachment ? `
                <div class="b-excess" style="left: ${dlrsPct}%; width: ${deedPct - dlrsPct}%;" title="${isEn ? 'Excess' : 'অতিরিক্ত'}: ${conflictAreaStr}"></div>
              ` : ''}
            </div>
          </div>

          <!-- DLRS Survey -->
          <div class="b-bar-item">
            <div class="b-bar-meta">
              <span class="b-bar-lbl">${isEn ? 'DLRS Survey' : 'ডিএলআরএস জরিপ'}</span>
              <span class="b-bar-num num" style="color: var(--layer-dlrs);">${dlrsAreaStr}</span>
            </div>
            <div class="b-track">
              <div class="b-fill" style="width: ${dlrsPct}%; background-color: var(--layer-dlrs);"></div>
              <div class="b-tolerance-band" style="left: ${dlrsPct}%; width: ${Math.max(4, tolerancePct - dlrsPct)}%;"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Card B: Khas Canal Overlap Donut -->
      <div class="bento-card card-khas-overlap">
        <div class="bento-card-header">
          <span class="bento-title">${isEn ? 'Khas Canal Overlap' : 'সরকারি খাল দখল'}</span>
          <span class="bento-badge num" style="color: ${isEncroachment ? 'var(--status-block)' : 'var(--status-clear)'};">
            ${isEncroachment ? (isEn ? 'Encroached' : 'দখল শনাক্ত') : (isEn ? 'Clean' : 'বিরোধমুক্ত')}
          </span>
        </div>

        ${isEncroachment ? `
          <div class="bento-donut-row">
            <div class="donut-ring-wrap">
              <svg viewBox="0 0 48 48" class="donut-svg">
                <circle cx="24" cy="24" r="20" class="donut-bg" />
                <circle cx="24" cy="24" r="20" class="donut-val" 
                        style="stroke: var(--status-block); stroke-dasharray: ${strokeDash} 126;" />
              </svg>
              <span class="donut-center-pct num">${khasPctStr}</span>
            </div>
            <div class="donut-legend-info">
              <div class="donut-headline font-bold num" style="color: var(--status-block);">${conflictAreaStr}</div>
              <div class="donut-subline">
                ${isEn 
                  ? `${conflictAreaStr} of ${deedAreaStr} inside public drainage canal.` 
                  : `${deedAreaStr} দলিলের মধ্যে ${conflictAreaStr} খালের অন্তর্ভুক্ত।`}
              </div>
            </div>
          </div>
        ` : `
          <div class="bento-clean-state">
            <span class="clean-check-icon" style="color: var(--status-clear);">${ICONS.check}</span>
            <div class="clean-state-text">
              ${isEn 
                ? 'Zero overlap with public khas land or waterbody.' 
                : 'সরকারি খাস ভূমি বা জলমহালের কোনো সীমানা দখল নেই।'}
            </div>
          </div>
        `}
      </div>
    </div>
  `;
}
