/**
 * RuleGrid Component (Bento Grid)
 * Shows ONLY failed rules expanded.
 * Mini value-vs-limit bar (e.g. "124 d / 30 d limit").
 * Collapses passed rules into one clean line ("3 rules passed").
 * Record IDs appear with 1-click copy buttons.
 */

function renderRuleGrid(container, data) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');

  const allRules = [
    {
      id: 'rule_khas',
      name: isEn ? 'Khas Canal Encroachment' : 'সরকারি খাস বা খাল দখল',
      failed: !!data.hasKhasOverlap,
      statusColor: 'var(--status-block)',
      valText: isEn ? '0.90 dec overlap' : '০.৯০ শতক দখল',
      limitText: isEn ? '0.00 dec allowed' : '০.০০ শতক অনুমোদিত',
      barPct: 90,
      evidence: isEn 
        ? 'DLRS Sheet 04, Kashimpur Public Drainage Canal. Non-transferable under State Acquisition Act §86.' 
        : 'ডিএলআরএস শিট ০৪, কাশিমপুর নিষ্কাশন খাল। রাষ্ট্রীয় অধিগ্রহণ আইন ধারা ৮৬ মোতাবেক হস্তান্তর অযোগ্য।',
      records: ['DLRS-BS-402', 'KHAS-CANAL-04'],
    },
    {
      id: 'rule_area',
      name: isEn ? 'Area Tolerance Limit' : 'আয়তন সংবিধিবদ্ধ সীমা',
      failed: !!data.hasAreaMismatch,
      statusColor: 'var(--status-block)',
      valText: isEn ? '0.90 dec deficit' : '০.৯০ শতক ঘাটতি',
      limitText: isEn ? '±0.20 dec limit' : '±০.২০ শতক সংবিধিবদ্ধ সীমা',
      barPct: 85,
      evidence: isEn 
        ? 'Deed claims 6.00 dec vs DLRS ground truth 5.10 dec. Deficit exceeds statutory ±0.20 dec threshold.' 
        : 'দলিলে ৬.০০ শতক কিন্তু ডিএলআরএস জরিপে ৫.১০ শতক। ঘাটতি ±০.২০ শতক সংবিধিবদ্ধ সীমা অতিক্রম করেছে।',
      records: ['DEED-2024-DH-402', 'DLRS-BS-402'],
    },
    {
      id: 'rule_mutation',
      name: isEn ? 'Deed Mutation Gap' : 'নামজারিহীন দলিল নোটিশ',
      failed: !!data.hasUnmutated,
      statusColor: 'var(--status-review)',
      valText: isEn ? '124 days unmutated' : '১২৪ দিন নামজারিহীন',
      limitText: isEn ? '30 days limit' : '৩০ দিন আইনগত সময়সীমা',
      barPct: 80,
      evidence: isEn 
        ? 'Sub-Registry deed registered 124 days ago; no AC Land e-Mutation record opened.' 
        : 'সাব-রেজিস্ট্রি দলিল সম্পাদনের ১২৪ দিন অতিক্রান্ত; এসি ল্যান্ড অফিসে নামজারি আবেদন করা হয়নি।',
      records: ['DEED-2023-DH-403'],
    },
    {
      id: 'rule_owner',
      name: isEn ? 'Khatian vs Tax Payer' : 'খতিয়ান বনাম করদাতা অমিল',
      failed: !!data.hasOwnerMismatch,
      statusColor: 'var(--status-review)',
      valText: isEn ? '64% match' : '৬৪% ধ্বনিগত মিল',
      limitText: isEn ? '80% threshold' : '৮০% আবশ্যক',
      barPct: 64,
      evidence: isEn 
        ? 'Title owner differs from land tax payer on record.' 
        : 'খতিয়ানভুক্ত মালিক ও ভূমি উন্নয়ন কর প্রদানকারী ভিন্ন ব্যক্তি।',
      records: ['KHAT-BS-120', 'TAX-2024-KSH-403'],
    },
    {
      id: 'rule_class',
      name: isEn ? 'Land Classification Mismatch' : 'জমির শ্রেণি অসংগতি',
      failed: !!data.hasClassConflict,
      statusColor: 'var(--status-review)',
      valText: isEn ? 'Nal vs Viti' : 'নাল বনাম ভিটি',
      limitText: isEn ? 'Exact match required' : 'অভিন্ন শ্রেণি আবশ্যক',
      barPct: 70,
      evidence: isEn 
        ? 'Deed assessed as agricultural Nal; tax classified as residential Viti.' 
        : 'দলিলে নাল (কৃষি) হিসেবে কর প্রদান কিন্তু রসিদে ভিটি (আবাসিক) শ্রেণিভুক্ত।',
      records: ['DEED-2023-DH-403', 'TAX-2024-KSH-403'],
    },
  ];

  const failedRules = allRules.filter(r => r.failed);
  const passedRules = allRules.filter(r => !r.failed);

  const passedCountStr = isEn ? String(passedRules.length) : toBnDigits(passedRules.length);

  container.innerHTML = `
    <div class="bento-rules-box">
      <div class="bento-header">
        <span class="bento-title">${isEn ? 'Rule Checks & Compliance' : 'সংবিধিবদ্ধ বিধি পরীক্ষণ'}</span>
        <span class="bento-subtitle num">${isEn ? `${passedRules.length} of 5 passed` : `৫টির মধ্যে ${passedCountStr}টি উত্তীর্ণ`}</span>
      </div>

      <!-- Failed Rules (Expanded by default) -->
      ${failedRules.length > 0 ? `
        <div class="rules-failed-list">
          ${failedRules.map(r => `
            <div class="rule-fail-card" style="border-left: 2px solid ${r.statusColor};">
              <div class="rf-top">
                <span class="rf-name font-bold">${r.name}</span>
                <span class="rf-val num" style="color: ${r.statusColor};">${r.valText}</span>
              </div>
              <div class="rf-bar-track">
                <div class="rf-bar-fill" style="width: ${r.barPct}%; background-color: ${r.statusColor};"></div>
              </div>
              <div class="rf-meta-row">
                <span class="rf-limit num">${r.limitText}</span>
                <span class="rf-cite-toggle" onclick="this.nextElementSibling.classList.toggle('hidden')">
                  ${isEn ? 'Evidence' : 'প্রমাণ'} ▾
                </span>
                <div class="rf-evidence-panel hidden">
                  <div class="rf-ev-desc">${r.evidence}</div>
                  <div class="rf-ev-chips">
                    ${r.records.map(id => `
                      <span class="rf-chip-code" onclick="navigator.clipboard.writeText('${id}')" title="${isEn ? 'Copy' : 'কপি করুন'}">
                        <code>${id}</code>
                        ${ICONS.copy}
                      </span>
                    `).join('')}
                  </div>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}

      <!-- Passed Rules (Collapsed Summary Line) -->
      <div class="rules-passed-summary">
        <span class="rp-icon" style="color: var(--status-clear);">${ICONS.check}</span>
        <span class="rp-text">
          ${failedRules.length === 0 
            ? (isEn ? 'All 5 statutory rules passed without discrepancies.' : 'সকল ৫টি সংবিধিবদ্ধ নিয়ম সম্পূর্ণ নির্ভুলভাবে উত্তীর্ণ হয়েছে।')
            : (isEn ? `${passedCountStr} rules passed successfully.` : `${passedCountStr}টি নিয়ম সফলভাবে উত্তীর্ণ হয়েছে।`)}
        </span>
      </div>
    </div>
  `;
}
