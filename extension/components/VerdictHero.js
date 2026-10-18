/**
 * VerdictHero Component
 * Immediate 5-second decision hero: verdict badge, 5-segment rule ring, one-line summary,
 * and clickable finding chips that highlight evidence across tabs and the map.
 */

function renderVerdictHero(container, verdictData, onChipClick) {
  if (!container) return;

  const verdict = verdictData.verdict || 'BLOCK'; // 'CLEAR', 'REVIEW', 'BLOCK'
  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');
  
  let verdictClass = 'verdict-block';
  let verdictColor = 'var(--status-block)';
  let verdictBg = 'var(--status-block-bg)';
  let verdictBorder = 'var(--status-block-border)';
  let verdictText = isEn ? 'BLOCK' : 'ব্লক (BLOCK)';
  let verdictIcon = '🚨';

  if (verdict === 'CLEAR') {
    verdictClass = 'verdict-clear';
    verdictColor = 'var(--status-clear)';
    verdictBg = 'var(--status-clear-bg)';
    verdictBorder = 'var(--status-clear-border)';
    verdictText = isEn ? 'CLEAR' : 'ক্লিয়ার (CLEAR)';
    verdictIcon = '✅';
  } else if (verdict === 'REVIEW') {
    verdictClass = 'verdict-review';
    verdictColor = 'var(--status-review)';
    verdictBg = 'var(--status-review-bg)';
    verdictBorder = 'var(--status-review-border)';
    verdictText = isEn ? 'REVIEW' : 'রিভিউ (REVIEW)';
    verdictIcon = '⚠️';
  }

  // Calculate 5 statutory rules status
  const rules = verdictData.rules || [
    { id: 'rule_unmutated', passed: verdict !== 'REVIEW' && !verdictData.hasUnmutated, label: 'Mutation' },
    { id: 'rule_owner_match', passed: !verdictData.hasOwnerMismatch, label: 'Owner' },
    { id: 'rule_class_match', passed: !verdictData.hasClassConflict, label: 'Class' },
    { id: 'rule_area_tol', passed: verdict !== 'BLOCK' || !verdictData.hasAreaMismatch, label: 'Area' },
    { id: 'rule_khas_overlap', passed: verdict !== 'BLOCK' || !verdictData.hasKhasOverlap, label: 'Khas' },
  ];

  const passedCount = rules.filter(r => r.passed).length;
  const totalCount = rules.length;

  // Short 1-line summary max 90 chars
  let plainSummary = verdictData.summary || '';
  if (plainSummary.length > 90) {
    plainSummary = plainSummary.slice(0, 87) + '...';
  }

  // Finding chips
  const chips = verdictData.chips || [];

  container.innerHTML = `
    <div class="verdict-hero-card ${verdictClass}" style="border-left: 4px solid ${verdictColor};">
      <div class="vh-top">
        <div class="vh-badge-group">
          <span class="vh-status-pill" style="color: ${verdictColor}; background: ${verdictBg}; border: 1px solid ${verdictBorder};">
            <span class="vh-icon">${verdictIcon}</span>
            <span class="vh-title">${verdictText}</span>
          </span>
        </div>

        <!-- 5-Segment Rule Ring Indicator -->
        <div class="vh-rule-ring" title="${passedCount} of ${totalCount} rules passed">
          <div class="vh-segments">
            ${rules.map(r => `
              <span class="vh-seg ${r.passed ? 'passed' : 'failed'}" 
                    style="background-color: ${r.passed ? 'var(--status-clear)' : (verdict === 'REVIEW' ? 'var(--status-review)' : 'var(--status-block)')};"></span>
            `).join('')}
          </div>
          <span class="vh-ring-label tabular">${passedCount}/${totalCount} ${isEn ? 'Rules' : 'নিয়ম'}</span>
        </div>
      </div>

      <!-- Plain language 1-line summary -->
      <div class="vh-summary-line">${plainSummary}</div>

      <!-- Interactive Finding Chips -->
      ${chips.length > 0 ? `
        <div class="vh-chips-row">
          ${chips.map(chip => `
            <button class="vh-chip" data-chip-target="${chip.target || ''}" title="ক্লিক করে প্রমাণ দেখুন">
              <span class="vh-chip-dot" style="background-color: ${chip.color || verdictColor}"></span>
              <span>${chip.label}</span>
            </button>
          `).join('')}
        </div>
      ` : ''}
    </div>
  `;

  // Bind chip clicks to highlight matching feature / tab
  container.querySelectorAll('.vh-chip').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const target = btn.dataset.chipTarget;
      if (onChipClick) onChipClick(target);
    });
  });
}
