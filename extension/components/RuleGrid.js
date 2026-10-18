/**
 * RuleGrid Component
 * 5 statutory rule cards in a compact grid:
 * 1. Deed vs Mutation Gap (Unmutated days vs 30d threshold)
 * 2. Khatian vs Tax Payer (Owner match %)
 * 3. Land Class Consistency (Agriculture/Nal vs Homestead/Viti)
 * 4. Area Statutory Limit (Paper claim vs DLRS survey ±0.20 dec)
 * 5. Public Khas Canal Overlap (0.90 dec overlap)
 *
 * Each card shows rule name, pass/fail status, one key number, and expands on tap for evidence.
 */

function renderRuleGrid(container, rulesData) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');

  const defaultRules = [
    {
      id: 'rule_khas',
      name: isEn ? 'Khas Canal Overlap' : 'সরকারি খাস বা খাল দখল',
      passed: !rulesData.hasKhasOverlap,
      status: rulesData.hasKhasOverlap ? 'BLOCK' : 'PASS',
      keyNumber: rulesData.hasKhasOverlap ? '0.90 dec' : '0.00 dec',
      subText: rulesData.hasKhasOverlap ? (isEn ? 'Public canal encroachment' : 'সরকারি নিষ্কাশন খাল দখল') : (isEn ? 'No encroachment' : 'কোনো দখল নেই'),
      evidence: rulesData.khasEvidence || 'DLRS Sheet 04, Kashimpur Public Drainage Canal (Khas Plot 405). Non-transferable under State Acquisition Act §86.',
      recordIds: ['DLRS-BS-402', 'KHAS-CANAL-04'],
    },
    {
      id: 'rule_area',
      name: isEn ? 'Area Statutory Limit' : 'আয়তন সংবিধিবদ্ধ সীমা',
      passed: !rulesData.hasAreaMismatch,
      status: rulesData.hasAreaMismatch ? 'BLOCK' : 'PASS',
      keyNumber: rulesData.areaDeficit ? `${rulesData.areaDeficit} dec` : '±0.05 dec',
      subText: isEn ? 'Limit: ±0.20 dec' : 'সংবিধিবদ্ধ সীমা: ±০.২০ শতক',
      evidence: rulesData.areaEvidence || 'Sub-Registry Deed claims 6.00 dec vs DLRS field polygon 5.10 dec. Deficit exceeds statutory tolerance.',
      recordIds: ['DEED-2024-DH-402', 'DLRS-BS-402'],
    },
    {
      id: 'rule_mutation',
      name: isEn ? 'Deed vs Mutation Gap' : 'নামজারিহীন দলিল নোটিশ',
      passed: !rulesData.hasUnmutated,
      status: rulesData.hasUnmutated ? 'REVIEW' : 'PASS',
      keyNumber: rulesData.unmutatedDays ? `${rulesData.unmutatedDays} days` : '0 days',
      subText: isEn ? 'Statutory limit: 30 days' : 'আইনগত সময়সীমা: ৩০ দিন',
      evidence: rulesData.mutationEvidence || 'Deed registered 124 days ago; no corresponding e-Mutation docket opened at AC Land office.',
      recordIds: ['DEED-2023-DH-403'],
    },
    {
      id: 'rule_owner',
      name: isEn ? 'Khatian vs Tax Payer' : 'খতিয়ান বনাম করদাতা',
      passed: !rulesData.hasOwnerMismatch,
      status: rulesData.hasOwnerMismatch ? 'REVIEW' : 'PASS',
      keyNumber: rulesData.ownerScore ? `${rulesData.ownerScore}%` : '100%',
      subText: isEn ? 'Phonetic match score' : 'নামের ধ্বনিগত মিল',
      evidence: rulesData.ownerEvidence || 'Khatian owner matches tax assessment records across Land Revenue Database.',
      recordIds: ['KHAT-BS-120', 'TAX-2024-KSH-402'],
    },
    {
      id: 'rule_class',
      name: isEn ? 'Land Classification' : 'জমির শ্রেণি সামঞ্জস্য',
      passed: !rulesData.hasClassConflict,
      status: rulesData.hasClassConflict ? 'REVIEW' : 'PASS',
      keyNumber: rulesData.classConflict ? (isEn ? 'Nal vs Viti' : 'নাল বনাম ভিটি') : (isEn ? 'Nal (Agri)' : 'নাল (কৃষি)'),
      subText: isEn ? 'Assessment category' : 'নির্ধারিত ভূমি রাজস্ব শ্রেণি',
      evidence: rulesData.classEvidence || 'Sub-Registry Deed assessed as agricultural (Nal) vs Union Land Tax classified as Homestead (Viti).',
      recordIds: ['DEED-2023-DH-403', 'TAX-2024-KSH-403'],
    },
  ];

  container.innerHTML = `
    <div class="rule-grid-header">
      <h4>${isEn ? 'Statutory Rules Checked' : '৫টি সংবিধিবদ্ধ বিধি পরীক্ষণ'}</h4>
      <span class="rule-grid-sub">${isEn ? 'Tap card for cited records' : 'রেকর্ড প্রমাণের জন্য ট্যাপ করুন'}</span>
    </div>
    <div class="rule-grid">
      ${defaultRules.map(rule => {
        let badgeColor = 'var(--status-clear)';
        let badgeBg = 'var(--status-clear-bg)';
        let badgeIcon = '✓';
        if (rule.status === 'BLOCK') {
          badgeColor = 'var(--status-block)';
          badgeBg = 'var(--status-block-bg)';
          badgeIcon = '✕';
        } else if (rule.status === 'REVIEW') {
          badgeColor = 'var(--status-review)';
          badgeBg = 'var(--status-review-bg)';
          badgeIcon = '⚠';
        }

        return `
          <div class="rule-card" data-rule-id="${rule.id}">
            <div class="rc-header">
              <span class="rc-name">${rule.name}</span>
              <span class="rc-badge" style="color: ${badgeColor}; background: ${badgeBg};">
                ${badgeIcon} ${rule.status}
              </span>
            </div>
            <div class="rc-metric-row">
              <span class="rc-key-number tabular" style="color: ${rule.passed ? 'var(--text-main)' : badgeColor}">
                ${rule.keyNumber}
              </span>
              <span class="rc-subtext">${rule.subText}</span>
            </div>
            
            <!-- Expandable Evidence (collapsed by default) -->
            <div class="rc-evidence hidden">
              <p class="rc-ev-desc">${rule.evidence}</p>
              <div class="rc-ev-records">
                ${rule.recordIds.map(id => `
                  <span class="rc-chip-id" title="কপি করুন" onclick="navigator.clipboard.writeText('${id}')">
                    <code>${id}</code>
                    <span class="rc-copy-icon">⎘</span>
                  </span>
                `).join('')}
              </div>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;

  // Attach tap-to-expand accordion
  container.querySelectorAll('.rule-card').forEach(card => {
    card.addEventListener('click', () => {
      const ev = card.querySelector('.rc-evidence');
      if (ev) {
        const isHidden = ev.classList.contains('hidden');
        // Toggle this evidence
        ev.classList.toggle('hidden');
        card.classList.toggle('expanded', isHidden);
      }
    });
  });
}
