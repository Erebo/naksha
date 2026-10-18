/**
 * NAKSHA (নকশা) — Internationalization Dictionary (BN / EN)
 * Concise labels and plain-language summaries for land officers.
 */

const I18N = {
  bn: {
    app_title: 'নকশা',
    role_officer: 'এসি ল্যান্ড / কানুনগো',
    session_prefix: 'সেশন',
    lang_btn: 'EN',
    syn_badge: 'কৃত্রিম ডেমো ডেটা',
    portal_ld_tax: 'ভূমি কর পোর্টাল',
    portal_e_mutation: 'ই-নামজারি',
    mouza: 'মৌজা',
    khatian: 'খতিয়ান',
    dag: 'দাগ',
    rules_passed: 'টি নিয়ম উত্তীর্ণ',
    recenter: 'কেন্দ্রীভূত',
    reset_view: 'রিসেট',
    layers_title: 'ক্যাডাস্ট্রাল স্তরসমূহ',
    tab_overview: 'সারসংক্ষেপ',
    tab_history: 'ইতিহাস',
    tab_tax: 'কর স্থিতি',
    tab_liens: 'দায় ও লিয়েন',
    tab_audit: 'অডিট লেজার',
    verdict_clear: 'ক্লিয়ার (CLEAR)',
    verdict_review: 'রিভিউ (REVIEW)',
    verdict_block: 'ব্লক (BLOCK)',
    area_chart_title: 'জমির পরিমাপ তুলনা (শতক)',
    area_excess: 'অতিরিক্ত দাবি',
    area_cs: 'সিএস পৈত্রিক',
    area_deed: 'দলিল দাবি',
    area_dlrs: 'ডিএলআরএস জরিপ',
    tolerance_label: 'সংবিধিবদ্ধ সীমা: ±০.২০ শতক',
    khas_donut_title: 'সরকারি খাস নিষ্কাশন খাল দখল',
    khas_donut_sub: '৬.০০ শতকের মধ্যে ০.৯০ শতক (১৫%) খালের অন্তর্ভুক্ত',
    rules_header: 'স্বয়ংক্রিয় বিধিসমূহ ও পরীক্ষণ',
    rule_unmutated: 'নামজারিহীন দলিল',
    rule_owner_match: 'খতিয়ান বনাম করদাতা',
    rule_class_match: 'জমির শ্রেণি সামঞ্জস্য',
    rule_area_tol: 'আয়তন সংবিধিবদ্ধ সীমা',
    rule_khas_overlap: 'সরকারি খাস বা খাল দখল',
    evidence_btn: 'রেকর্ড সূত্র ও প্রমাণ',
    no_liens_title: 'কোনো সক্রিয় দায় বা লিয়েন নেই',
    no_liens_desc: 'ব্যাংক বন্ধক বা সরকারি অধিগ্রহণ সংক্রান্ত কোনো স্থগিতাদেশ পাওয়া যায়নি।',
    chain_intact: 'হ্যাশ-চেইন অটুট (INTACT)',
    chain_broken: 'হ্যাশ-চেইনে ত্রুটি!',
    algorithm: 'অ্যালগরিদম: SHA-256 Chain + Ed25519 স্বাক্ষর',
    unit_dec: 'শতক',
    unit_days: 'দিন',
  },
  en: {
    app_title: 'NAKSHA',
    role_officer: 'AC Land / Kanoongo',
    session_prefix: 'Session',
    lang_btn: 'বাং',
    syn_badge: 'Synthetic Data',
    portal_ld_tax: 'LD Tax Portal',
    portal_e_mutation: 'e-Mutation',
    mouza: 'Mouza',
    khatian: 'Khatian',
    dag: 'Plot / Dag',
    rules_passed: 'rules passed',
    recenter: 'Recenter',
    reset_view: 'Reset',
    layers_title: 'Cadastral Layers',
    tab_overview: 'Overview',
    tab_history: 'Lineage',
    tab_tax: 'Tax & Payer',
    tab_liens: 'Liens & Locks',
    tab_audit: 'Audit Chain',
    verdict_clear: 'CLEAR',
    verdict_review: 'REVIEW',
    verdict_block: 'BLOCK',
    area_chart_title: 'Area Comparison (Decimals)',
    area_excess: 'Excess claim',
    area_cs: 'Ancestral CS',
    area_deed: 'Deed Claim',
    area_dlrs: 'DLRS Survey',
    tolerance_label: 'Statutory Tolerance: ±0.20 dec',
    khas_donut_title: 'Public Khas Canal Encroachment',
    khas_donut_sub: '0.90 dec of 6.00 dec (15%) inside canal',
    rules_header: 'Automated Rule Checks',
    rule_unmutated: 'Deed vs Mutation Gap',
    rule_owner_match: 'Khatian vs Tax Payer',
    rule_class_match: 'Land Classification',
    rule_area_tol: 'Area Statutory Limit',
    rule_khas_overlap: 'Khas Canal Overlap',
    evidence_btn: 'Citations & Evidence',
    no_liens_title: 'No Active Liens or Locks',
    no_liens_desc: 'No bank mortgages or acquisition injunctions found on record.',
    chain_intact: 'Chain Intact & Signed',
    chain_broken: 'Integrity Failure!',
    algorithm: 'Algorithm: SHA-256 Chain + Ed25519',
    unit_dec: 'dec',
    unit_days: 'days',
  }
};

let currentLang = 'bn';

function t(key) {
  return (I18N[currentLang] && I18N[currentLang][key]) || key;
}

function toggleLanguage() {
  currentLang = currentLang === 'bn' ? 'en' : 'bn';
  document.documentElement.lang = currentLang;
  return currentLang;
}
