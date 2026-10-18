/**
 * VerdictHero Component (Minimalist Bento + Auto-Collapsing Strip)
 * - Expanded by default (~110px) on Overview tab.
 * - Auto-collapses to a compact 38px bar on other tabs or upon scrolling:
 *   [Status Dot] [STATUS WORD] · [Headline Metric] [Chevron]
 * - Tap chevron to expand/collapse.
 * - Zero emojis, monochrome chips with small status-colored dots.
 */

function renderVerdictHero(container, data, onChipClick) {
  if (!container) return;

  const verdict = data.verdict || 'BLOCK';
  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');

  let statusText = isEn ? 'BLOCK' : 'ব্লক';
  let statusColor = 'var(--status-block)';
  let headlineMetric = isEn ? '0.90 dec' : '০.৯০ শতক';
  let headlineLabel = isEn ? 'Khas overlap' : 'খাস খাল দখল';
  let recommendedAction = isEn
    ? 'Do not register. Place mutation on hold & refer to AC Land.'
    : 'নামজারি অনুমোদন স্থগিত। সহকারী কমিশনার (ভূমি) বরাবর প্রেরণের নির্দেশ।';

  if (verdict === 'CLEAR') {
    statusText = isEn ? 'CLEAR' : 'ক্লিয়ার';
    statusColor = 'var(--status-clear)';
    headlineMetric = isEn ? '0.00 dec' : '০.০০ শতক';
    headlineLabel = isEn ? 'Zero conflict' : 'বিরোধমুক্ত';
    recommendedAction = isEn
      ? 'All titles & boundaries align. Recommended for approval.'
      : 'সকল সংস্থার রেকর্ড ও সীমানা সামঞ্জস্যপূর্ণ। নামজারি অনুমোদনের সুপারিশ।';
  } else if (verdict === 'REVIEW') {
    statusText = isEn ? 'REVIEW' : 'রিভিউ';
    statusColor = 'var(--status-review)';
    headlineMetric = isEn ? '3 years' : '৩ অর্থবছর';
    headlineLabel = isEn ? 'Tax arrears' : 'কর বকেয়া';
    recommendedAction = isEn
      ? 'Issue hearing notice. Collect arrears prior to mutation.'
      : 'শুনানির নোটিশ জারি করুন। নামজারির পূর্বে বকেয়া কর আদায় প্রযোজ্য।';
  }

  // 5 Statutory Rules
  const rules = data.rules || [
    { id: 'rule_khas', passed: verdict !== 'BLOCK' && !data.hasKhasOverlap },
    { id: 'rule_area', passed: verdict !== 'BLOCK' && !data.hasAreaMismatch },
    { id: 'rule_mutation', passed: verdict !== 'REVIEW' && !data.hasUnmutated },
    { id: 'rule_owner', passed: !data.hasOwnerMismatch },
    { id: 'rule_class', passed: !data.hasClassConflict },
  ];
  const passedCount = rules.filter(r => r.passed).length;
  const passedCountStr = isEn ? String(passedCount) : toBnDigits(passedCount);
  const totalCountStr = isEn ? '5' : '৫';

  const chips = (data.chips || []).slice(0, 3);
  const isCollapsed = container.classList.contains('collapsed');

  container.innerHTML = `
    <!-- Expanded State (~110px) -->
    <div class="vh-expanded-box ${isCollapsed ? 'hidden' : ''}" style="border-left: 3px solid ${statusColor};">
      <div class="vh-main-row">
        <div class="vh-left-col">
          <div class="vh-status-word" style="color: ${statusColor};">${statusText}</div>
          <div class="vh-rule-segments" title="${passedCount} of 5 rules passed">
            ${rules.map(r => `
              <span class="vh-seg-bar" style="background-color: ${r.passed ? 'var(--status-clear)' : (verdict === 'REVIEW' ? 'var(--status-review)' : 'var(--status-block)')};"></span>
            `).join('')}
            <span class="vh-seg-text num">${passedCountStr}/${totalCountStr} ${isEn ? 'passed' : 'উত্তীর্ণ'}</span>
          </div>
        </div>

        <div class="vh-right-col">
          <div class="vh-metric-val num" style="color: ${verdict === 'CLEAR' ? 'var(--status-clear)' : (verdict === 'REVIEW' ? 'var(--status-review)' : 'var(--status-block)')};">
            ${headlineMetric}
          </div>
          <div class="vh-metric-lbl">${headlineLabel}</div>
        </div>
      </div>

      ${chips.length > 0 ? `
        <div class="vh-chips-row">
          ${chips.map(chip => `
            <button class="vh-chip-btn" data-target="${chip.target || ''}" type="button">
              <span class="vh-chip-dot" style="background-color: ${chip.color || statusColor};"></span>
              <span>${chip.label}</span>
            </button>
          `).join('')}
        </div>
      ` : ''}

      <div class="vh-action-line">
        <span class="vh-action-tag">${isEn ? 'ACTION' : 'করণীয়'}:</span>
        <span class="vh-action-desc">${recommendedAction}</span>
      </div>
    </div>

    <!-- Collapsed Slim Bar (~38px) -->
    <div class="vh-collapsed-bar ${isCollapsed ? '' : 'hidden'}" style="border-left: 3px solid ${statusColor};">
      <div class="vh-col-left">
        <span class="vh-status-dot" style="background-color: ${statusColor};"></span>
        <span class="vh-col-status font-bold" style="color: ${statusColor};">${statusText}</span>
        <span class="vh-col-divider">·</span>
        <span class="vh-col-metric num font-bold">${headlineMetric}</span>
        <span class="vh-col-label">${headlineLabel}</span>
      </div>
      <button class="vh-toggle-btn" id="vh-toggle-expand" type="button" title="${isEn ? 'Expand Verdict' : 'বিস্তারিত দেখুন'}">
        <span class="vh-chevron">▾</span>
      </button>
    </div>
  `;

  // Attach chip clicks
  container.querySelectorAll('.vh-chip-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (onChipClick) onChipClick(btn.dataset.target);
    });
  });

  // Toggle button
  const toggleBtn = container.querySelector('#vh-toggle-expand');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      container.classList.remove('collapsed');
      const exp = container.querySelector('.vh-expanded-box');
      const col = container.querySelector('.vh-collapsed-bar');
      if (exp) exp.classList.remove('hidden');
      if (col) col.classList.add('hidden');
    });
  }
}
