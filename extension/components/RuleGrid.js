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
                <div class="rf-evidence-panel hidden" style="margin-top: 5px; padding: 5px; background: var(--bg-surface); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); width: 100%;">
                  ${r.evidence ? `<div class="rf-ev-desc" style="font-size: 9.5px; color: var(--text-main); line-height: 1.35; margin-bottom: 4px;">${escapeHtml(r.evidence)}</div>` : ''}
                  ${r.legal_ref ? `
                    <div class="rf-ev-legal" style="font-size: 9px; color: var(--text-muted); margin-bottom: 4px;">
                      <span class="font-bold" style="color: var(--text-main);">${isEn ? 'Statutory Reference: ' : 'আইনি ভিত্তি: '}</span>
                      <span>${escapeHtml(r.legal_ref)}</span>
                    </div>
                  ` : ''}
                  ${r.records.length > 0 ? `
                    <div class="rf-ev-chips" style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px;">
                      ${r.records.map(id => `
                        <span class="record-copy-btn rf-chip-code" onclick="navigator.clipboard.writeText('${escapeHtml(id)}')" title="${isEn ? 'Copy' : 'কপি করুন'}">
                          <code>${escapeHtml(id)}</code>
                          ${(typeof ICONS !== 'undefined' && ICONS.copy) ? ICONS.copy : ''}
                        </span>
                      `).join('')}
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
