/**
 * AreaChart Component
 * Visualizes:
 * a) Horizontal bar comparison: Ancestral CS area, Deed claim (6.0 dec), DLRS surveyed (5.1 dec),
 *    with a shaded tolerance band of ±0.20 dec and excess highlighted in red.
 * b) Khas overlap mini donut/bar: 0.90 dec of 6.00 dec (15%).
 */

function renderAreaChart(container, areaData) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');

  const csArea = areaData.csArea || 18.0;
  const deedArea = areaData.deedArea || 6.00;
  const dlrsArea = areaData.dlrsArea || 5.10;
  const conflictArea = areaData.conflictArea || (deedArea > dlrsArea ? +(deedArea - dlrsArea).toFixed(2) : 0.0);
  const maxVal = Math.max(deedArea, dlrsArea, 7.0);

  // Percentage calculations for bars
  const deedPct = Math.min(100, Math.round((deedArea / maxVal) * 100));
  const dlrsPct = Math.min(100, Math.round((dlrsArea / maxVal) * 100));
  const tolerancePct = Math.min(100, Math.round(((dlrsArea + 0.20) / maxVal) * 100));
  const hasExcess = conflictArea > 0.20;

  // Donut calculations for Khas overlap
  const khasPct = Math.min(100, Math.round((conflictArea / (deedArea || 1)) * 100));
  const strokeDash = Math.round((khasPct / 100) * 125); // circle radius 20 -> circumference ~125.6
  const isEncroachment = (conflictArea >= 0.20);

  container.innerHTML = `
    <div class="area-chart-container">
      <div class="chart-header">
        <span class="chart-title">${isEn ? 'Area Measurement Comparison' : 'জমির পরিমাপ ও বিরোধ বিশ্লেষণ'}</span>
        <span class="chart-unit tabular">±0.20 ${isEn ? 'dec limit' : 'শতক সীমা'}</span>
      </div>

      <!-- Horizontal Bar Chart -->
      <div class="bars-wrapper">
        <!-- Deed Claim Bar -->
        <div class="bar-row">
          <div class="bar-label-group">
            <span class="bar-name">${isEn ? 'Deed Claim' : 'দলিলে দাবি'}</span>
            <span class="bar-val tabular font-bold" style="color: var(--layer-deed);">${deedArea.toFixed(2)} ${isEn ? 'dec' : 'শতক'}</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width: ${deedPct}%; background-color: var(--layer-deed);"></div>
            ${hasExcess ? `
              <div class="bar-excess" style="left: ${dlrsPct}%; width: ${deedPct - dlrsPct}%;" title="অতিরিক্ত দাবি: ${conflictArea} শতক"></div>
            ` : ''}
          </div>
        </div>

        <!-- DLRS Ground Truth Bar -->
        <div class="bar-row">
          <div class="bar-label-group">
            <span class="bar-name">${isEn ? 'DLRS Surveyed' : 'ডিএলআরএস জরিপ'}</span>
            <span class="bar-val tabular font-bold" style="color: var(--layer-dlrs);">${dlrsArea.toFixed(2)} ${isEn ? 'dec' : 'শতক'}</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width: ${dlrsPct}%; background-color: var(--layer-dlrs);"></div>
            <!-- Shaded Tolerance Band -->
            <div class="bar-tolerance-band" style="left: ${dlrsPct}%; width: ${Math.max(4, tolerancePct - dlrsPct)}%;" title="±0.20 dec tolerance"></div>
          </div>
        </div>
      </div>

      <!-- Khas Overlap Mini Donut Card -->
      ${isEncroachment ? `
        <div class="khas-donut-card">
          <div class="donut-svg-wrapper">
            <svg viewBox="0 0 48 48" class="donut-svg">
              <circle cx="24" cy="24" r="20" class="donut-bg" />
              <circle cx="24" cy="24" r="20" class="donut-val" 
                      style="stroke: var(--status-block); stroke-dasharray: ${strokeDash} 126;" />
            </svg>
            <span class="donut-text tabular">${khasPct}%</span>
          </div>
          <div class="donut-info">
            <div class="donut-title" style="color: var(--status-block);">
              ${isEn ? 'Public Khas Canal Encroachment' : 'সরকারি খাস নিষ্কাশন খাল দখল'}
            </div>
            <div class="donut-desc">
              ${isEn 
                ? `<strong>${conflictArea.toFixed(2)} dec</strong> of ${deedArea.toFixed(2)} dec (${khasPct}%) is inside the public canal.`
                : `দাবিকৃত ${deedArea.toFixed(2)} শতকের মধ্যে <strong>${conflictArea.toFixed(2)} শতক (${khasPct}%)</strong> খালের ভেতরে ঢুকে পড়েছে।`}
            </div>
          </div>
        </div>
      ` : `
        <div class="khas-clean-card">
          <span class="clean-icon">✓</span>
          <span class="clean-text">
            ${isEn ? 'No government khas or waterbody overlap detected.' : 'কোনো সরকারি খাস ভূমি বা জলমহালের সীমানা দখল পাওয়া যায়নি।'}
          </span>
        </div>
      `}
    </div>
  `;
}
