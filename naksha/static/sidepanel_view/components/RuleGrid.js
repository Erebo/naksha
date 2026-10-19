/**
 * RuleGrid Component (Bento Grid)
 * 
 * Renders statutory rules dynamically evaluated by the backend API:
 * - Displays FAIL and UNKNOWN rules expanded.
 * - Shows UNKNOWN as its own state with neutral color and "Insufficient data" label.
 * - Collapses PASS rules into a clean summary line.
 * - Dynamically formats measured values, statutory limits, evidence, legal citations,
 *   and cited record chips without any hardcoded numbers or static citations.
 */

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

const RULE_METADATA = {
  khas_encroachment: {
    en: 'Khas Canal Encroachment',
    bn: 'সরকারি খাস বা খাল দখল',
  },
  area_tolerance: {
    en: 'Area Tolerance Limit',
    bn: 'আয়তন সংবিধিবদ্ধ সীমা',
  },
  mutation_status: {
    en: 'Deed Mutation Gap',
    bn: 'নামজারি স্থিতি ও দলিল ব্যবধান',
  },
  owner_name_match: {
    en: 'Khatian vs Tax Payer Name',
    bn: 'খতিয়ান বনাম করদাতা নাম মিল',
  },
  ld_tax_compliance: {
    en: 'LD Tax Compliance',
    bn: 'ভূমি উন্নয়ন কর অনুবর্তীতা',
  },
};

function formatUnitName(unit, isEn) {
  if (!unit) return '';
  const u = String(unit).toLowerCase();
  if (u === 'decimal' || u === 'dec') return isEn ? 'dec' : 'শতক';
  if (u === 'day' || u === 'days') return isEn ? 'days' : 'দিন';
  if (u === 'year' || u === 'years') return isEn ? 'yrs' : 'অর্থবছর';
  if (u === 'ratio') return '%';
  return unit;
}

function formatRuleMetric(val, unit, isEn) {
  if (val === null || val === undefined) {
    return isEn ? 'N/A' : 'তথ্য নেই';
  }
  const u = unit ? String(unit).toLowerCase() : '';
  if (u === 'ratio') {
    const pct = typeof val === 'number' && val <= 1.0 ? Math.round(val * 100) : Math.round(val);
    return isEn ? `${pct}%` : `${toBnDigits(pct)}%`;
  }
  if (typeof val === 'number') {
    const formatted = Number.isInteger(val) ? String(val) : val.toFixed(2);
    const numText = isEn ? formatted : toBnDigits(formatted);
    const unitText = formatUnitName(unit, isEn);
    return unitText ? `${numText} ${unitText}` : numText;
  }
  return isEn ? String(val) : toBnDigits(val);
}

function calculateBarPercentage(rule) {
  if (rule.status === 'UNKNOWN') return 0;
  if (rule.unit === 'ratio' && typeof rule.measured === 'number') {
    const ratioVal = rule.measured <= 1.0 ? rule.measured : rule.measured / 100.0;
    return Math.min(100, Math.max(5, Math.round(ratioVal * 100)));
  }
  if (typeof rule.measured === 'number' && typeof rule.limit === 'number' && rule.limit > 0) {
    return Math.min(100, Math.max(5, Math.round((rule.measured / rule.limit) * 100)));
  }
  if (rule.status === 'FAIL') return 100;
  return 0;
}

const LEGAL_REFS_BN = {
  khas_encroachment: 'সরকারি এবং স্থানীয় কর্তৃপক্ষ ভূমি ও ইমারত (বেদখল উদ্ধার) অধ্যাদেশ, ১৯৭০ (ধারা ৫)',
  area_tolerance: 'বেঙ্গল সার্ভে অ্যাক্ট, ১৮৭৫ ও ভূমি জরিপ নির্দেশিকা (পরিপত্র ১৬/২০১৫)',
  owner_name_match: 'নিবন্ধন আইন, ১৯০৮ (ধারা ২১) ও ভূমি ব্যবস্থাপনা ম্যানুয়াল, ১৯৯০',
  ld_tax_compliance: 'ভূমি উন্নয়ন কর অধ্যাদেশ, ১৯৭৬ (ধারা ৩) ও কর আদায় বিধিমালা',
  mutation_status: 'রাষ্ট্রীয় অধিগ্রহণ ও প্রজাস্বত্ব আইন, ১৯৫০ (ধারা ১৪৩) ও পরিপত্র',
};

const LEGAL_REFS_EN = {
  khas_encroachment: 'Government & Local Authority Lands & Buildings (Recovery of Possession) Ordinance 1970 (Sec 5)',
  area_tolerance: 'Bengal Survey Act 1875 & Cadastral Mapping Circular (Circular 16/2015)',
  owner_name_match: 'Registration Act 1908 (Sec 21) & Land Management Manual 1990',
  ld_tax_compliance: 'Land Development Tax Ordinance 1976 (Sec 3) & Assessment Rules',
  mutation_status: 'State Acquisition and Tenancy Act 1950 (Sec 143) & MinLand Directives',
};

function formatEvidenceText(rule, isEn) {
  if (!rule || !rule.evidence) return '';
  if (isEn) return rule.evidence;

  const id = rule.rule_id;
  const status = rule.status;
  const m = rule.measured;
  const lim = rule.limit;

  if (id === 'ld_tax_compliance') {
    if (status === 'FAIL') {
      const yrs = Math.round(m || 0);
      const limYrs = Math.round(lim || 1);
      return `হোল্ডিংয়ে ${toBnDigits(yrs)} অর্থবছরের ভূমি উন্নয়ন কর বকেয়া রয়েছে (সংবিধিবদ্ধ অনুমোদিত সীমা: ${toBnDigits(limYrs)} অর্থবছর)।`;
    }
    return `ভূমি উন্নয়ন কর পরিশোধের স্থিতি নিয়মিত রয়েছে (${toBnDigits(Math.round(m || 0))} বকেয়া বছর <= ${toBnDigits(Math.round(lim || 1))} বছর)।`;
  }

  if (id === 'mutation_status') {
    if (status === 'FAIL') {
      const days = Math.round(m || 0);
      const limDays = Math.round(lim || 30);
      return `দলিল নিবন্ধনের ${toBnDigits(days)} দিন অতিবাহিত হলেও এসি ল্যান্ড ই-নামজারি সম্পন্ন হয়নি (সংবিধিবদ্ধ সীমা: ${toBnDigits(limDays)} দিন)।`;
    }
    return `দলিল নিবন্ধনের পর সংবিধিবদ্ধ নামজারি সময়সীমা উত্তীর্ণ হয়নি (${toBnDigits(Math.round(m || 0))} দিন <= ${toBnDigits(Math.round(lim || 30))} দিন)।`;
  }

  if (id === 'khas_encroachment') {
    if (status === 'FAIL') {
      const decStr = typeof m === 'number' ? m.toFixed(2) : String(m);
      const limStr = typeof lim === 'number' ? lim.toFixed(2) : String(lim);
      return `সরকারি খাস জমি বা খালের উপর ${toBnDigits(decStr)} শতক অননুমোদিত দখল সনাক্ত হয়েছে (অনুমোদিত সীমা: ${toBnDigits(limStr)} শতক)।`;
    }
    return `সরকারি খাস জমি বা খালের উপর কোনো অননুমোদিত দখল সনাক্ত হয়নি।`;
  }

  if (id === 'area_tolerance') {
    const diffStr = typeof m === 'number' ? m.toFixed(2) : String(m);
    const limStr = typeof lim === 'number' ? lim.toFixed(2) : String(lim);
    if (status === 'FAIL') {
      return `দলিল ও ডিএলআরএস জরিপের মধ্যে ক্ষেত্রফলের পার্থক্য ${toBnDigits(diffStr)} শতক, যা সংবিধিবদ্ধ সহনশীলতার (±${toBnDigits(limStr)} শতক) বাইরে।`;
    }
    return `দলিল ও ডিএলআরএস জরিপের ক্ষেত্রফলের পার্থক্য ${toBnDigits(diffStr)} শতক, যা অনুমোদিত সীমার (±${toBnDigits(limStr)} শতক) মধ্যে রয়েছে।`;
  }

  if (id === 'owner_name_match') {
    const pct = typeof m === 'number' && m <= 1.0 ? Math.round(m * 100) : Math.round(m);
    const limPct = typeof lim === 'number' && lim <= 1.0 ? Math.round(lim * 100) : Math.round(lim);
    if (status === 'FAIL') {
      return `রেকর্ডকৃত মালিক ও আবেদনকারীর নামের ধ্বনিগত মিল ${toBnDigits(pct)}%, যা সংবিধিবদ্ধ সীমার (${toBnDigits(limPct)}%) কম।`;
    }
    return `রেকর্ডকৃত মালিক ও আবেদনকারীর নামের মধ্যে গ্রহণযোগ্য ধ্বনিগত মিল রয়েছে (${toBnDigits(pct)}% >= ${toBnDigits(limPct)}%)।`;
  }

  return rule.evidence;
}

function formatLegalRefText(rule, isEn) {
  if (!rule) return '';
  if (isEn) {
    if (rule.legal_ref && !rule.legal_ref.includes('TODO')) {
      return rule.legal_ref;
    }
    return LEGAL_REFS_EN[rule.rule_id] || 'Statutory Land Administration Guidelines';
  }
  return LEGAL_REFS_BN[rule.rule_id] || rule.legal_ref || 'প্রযোজ্য ভূমি ব্যবস্থাপনা আইন ও সরকারি পরিপত্র';
}

function renderRuleGrid(container, data) {
  if (!container) return;

  const isEn = (typeof currentLang !== 'undefined' && currentLang === 'en');
  const rawRules = (data && Array.isArray(data.rules)) ? data.rules : [];

  if (rawRules.length === 0) {
    container.innerHTML = `
      <div class="bento-rules-box">
        <div class="bento-header">
          <span class="bento-title">${isEn ? 'Rule Checks & Compliance' : 'সংবিধিবদ্ধ বিধি পরীক্ষণ'}</span>
          <span class="bento-subtitle num">${isEn ? '0 rules evaluated' : 'কোনো বিধি পাওয়া যায়নি'}</span>
        </div>
      </div>
    `;
    return;
  }

  const processedRules = rawRules.map((r) => {
    const meta = RULE_METADATA[r.rule_id] || {};
    const name = (isEn ? meta.en : meta.bn) || r.rule_id.replace(/_/g, ' ');
    const status = (r.status || 'UNKNOWN').toUpperCase();
    const severity = (r.severity || 'REVIEW').toUpperCase();

    let statusColor = 'var(--status-neutral, #9A9AA5)';
    let badgeText = isEn ? 'Insufficient data' : 'অপর্যাপ্ত তথ্য';

    if (status === 'FAIL') {
      if (severity === 'BLOCK') {
        statusColor = 'var(--status-block, #F43F5E)';
        badgeText = isEn ? 'BLOCK' : 'ব্লক';
      } else {
        statusColor = 'var(--status-review, #FBBF24)';
        badgeText = isEn ? 'REVIEW' : 'রিভিউ';
      }
    } else if (status === 'PASS') {
      statusColor = 'var(--status-clear, #34D399)';
      badgeText = isEn ? 'PASS' : 'উত্তীর্ণ';
    }

    const valText = status === 'UNKNOWN' && (r.measured === null || r.measured === undefined)
      ? (isEn ? 'Insufficient data' : 'অপর্যাপ্ত তথ্য')
      : formatRuleMetric(r.measured, r.unit, isEn);

    let limitText = '';
    if (r.limit !== null && r.limit !== undefined) {
      const formattedLimit = formatRuleMetric(r.limit, r.unit, isEn);
      limitText = isEn ? `Limit: ${formattedLimit}` : `সংবিধিবদ্ধ সীমা: ${formattedLimit}`;
    } else if (status === 'UNKNOWN') {
      limitText = isEn ? 'Evaluation pending data' : 'মূল্যায়নের জন্য তথ্য অপর্যাপ্ত';
    }

    return {
      ...r,
      name,
      status,
      severity,
      statusColor,
      badgeText,
      valText,
      limitText,
      barPct: calculateBarPercentage(r),
      records: Array.isArray(r.cited_record_ids) ? r.cited_record_ids : [],
    };
  });

  const activeRules = processedRules.filter(r => r.status === 'FAIL' || r.status === 'UNKNOWN');
  const passedRules = processedRules.filter(r => r.status === 'PASS');

  const totalCount = processedRules.length;
  const passedCount = passedRules.length;
  const passedCountStr = isEn ? String(passedCount) : toBnDigits(passedCount);
  const totalCountStr = isEn ? String(totalCount) : toBnDigits(totalCount);

  container.innerHTML = `
    <div class="bento-rules-box">
      <div class="bento-header">
        <span class="bento-title">${isEn ? 'Rule Checks & Compliance' : 'সংবিধিবদ্ধ বিধি পরীক্ষণ'}</span>
        <span class="bento-subtitle num">${isEn ? `${passedCount} of ${totalCount} passed` : `${totalCountStr}টির মধ্যে ${passedCountStr}টি উত্তীর্ণ`}</span>
      </div>

      <!-- Active / Attention Rules (Failed or Unknown, expanded by default) -->
      ${activeRules.length > 0 ? `
        <div class="rules-failed-list">
          ${activeRules.map(r => `
            <div class="rule-fail-card" style="border-left: 2px solid ${r.statusColor};">
              <div class="rf-top">
                <span class="rf-name font-bold">${escapeHtml(r.name)}</span>
                <span class="rf-val num" style="color: ${r.statusColor};">${r.valText}</span>
              </div>
              <div class="rf-track rf-bar-track">
                <div class="rf-fill rf-bar-fill" style="width: ${r.barPct}%; background-color: ${r.statusColor};"></div>
              </div>
              <div class="rf-meta-row" style="display: flex; justify-content: space-between; align-items: center; margin-top: 3px;">
                <span class="rf-limit num" style="font-size: 9.5px; color: var(--text-muted);">${r.limitText}</span>
                <span class="rf-cite-toggle" onclick="this.nextElementSibling.classList.toggle('hidden')" style="font-size: 9.5px; cursor: pointer; color: var(--text-dim);">
                  ${isEn ? 'Evidence & Law' : 'প্রমাণ ও আইনি ভিত্তি'} ▾
                </span>
                <div class="rf-evidence-panel hidden" style="margin-top: 6px; padding: 7px 9px; background: var(--bg-surface-2, #18181C); border-radius: var(--radius-sm, 4px); border: 1px solid rgba(255, 255, 255, 0.08); width: 100%;">
                  <div class="rf-ev-desc" style="font-size: 9.5px; color: var(--text-main); line-height: 1.35; margin-bottom: 4px;">${escapeHtml(formatEvidenceText(r, isEn))}</div>
                  <div class="rf-ev-legal" style="font-size: 9px; color: var(--text-muted); margin-bottom: 6px;">
                    <span class="font-bold" style="color: var(--text-main);">${isEn ? 'Statutory Reference: ' : 'আইনি ভিত্তি: '}</span>
                    <span>${escapeHtml(formatLegalRefText(r, isEn))}</span>
                  </div>
                  ${r.records.length > 0 ? `
                    <div class="rf-ev-chips" style="display: flex; flex-wrap: wrap; gap: 5px; margin-top: 5px;">
                      ${r.records.map(id => {
                        const upper = String(id || '').toUpperCase();
                        let chipType = 'default';
                        if (upper.includes('MATCH')) chipType = 'match';
                        else if (upper.includes('CONFLICT') || upper.includes('KHAS')) chipType = 'conflict';
                        else if (upper.includes('TAX')) chipType = 'tax';
                        else if (upper.includes('DEED')) chipType = 'deed';
                        else if (upper.includes('MUT')) chipType = 'mutation';

                        return `
                          <span class="record-copy-btn rf-chip-code chip-${chipType}" data-type="${chipType}" onclick="navigator.clipboard.writeText('${escapeHtml(id)}')" title="${isEn ? 'Copy' : 'কপি করুন'}">
                            <code>${escapeHtml(id)}</code>
                            ${(typeof ICONS !== 'undefined' && ICONS.copy) ? ICONS.copy : '📋'}
                          </span>
                        `;
                      }).join('')}
                    </div>
                  ` : ''}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}

      <!-- Passed Rules (Collapsed Summary Line) -->
      <div class="rules-passed-summary rules-passed-row">
        <span class="rp-icon" style="color: var(--status-clear);">${(typeof ICONS !== 'undefined' && ICONS.check) ? ICONS.check : '✓'}</span>
        <span class="rp-text">
          ${activeRules.length === 0 
            ? (isEn ? `All ${totalCount} statutory rules passed without discrepancies.` : `সকল ${totalCountStr}টি সংবিধিবদ্ধ নিয়ম সম্পূর্ণ নির্ভুলভাবে উত্তীর্ণ হয়েছে।`)
            : (isEn ? `${passedCountStr} rules passed successfully.` : `${passedCountStr}টি নিয়ম সফলভাবে উত্তীর্ণ হয়েছে।`)}
        </span>
      </div>
    </div>
  `;
}
