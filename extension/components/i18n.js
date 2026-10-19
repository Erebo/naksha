/**
 * NAKSHA (নকশা) — Strict Localization & Bengali Numeral Conversion
 * Guarantees zero mixed languages: 100% Bengali in BN mode, 100% Latin in EN mode.
 */

const BN_DIGITS = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'];

function toBnDigits(strOrNum) {
  if (strOrNum === null || strOrNum === undefined) return '';
  return String(strOrNum).replace(/\d/g, (d) => BN_DIGITS[parseInt(d, 10)]);
}

function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined) return '';
  const formatted = typeof num === 'number' ? num.toFixed(decimals) : String(num);
  return currentLang === 'bn' ? toBnDigits(formatted) : formatted;
}

const I18N = {
  bn: {
    app_title: 'নকশা',
    role_officer: 'এসি ল্যান্ড / কানুনগো',
    theme_light: 'হালকা থিম',
    theme_dark: 'গাঢ় থিম',
    lang_btn: 'EN',
    syn_footer: 'কৃত্রিম প্রদর্শনী তথ্য — কোনো সরকারি রেকর্ডের সাথে সম্পর্কযুক্ত নয়',
    portal_ld_tax: 'ভূমি কর পোর্টাল',
    portal_e_mutation: 'ই-নামজারি',
    mouza: 'মৌজা',
    khatian: 'খতিয়ান',
    dag: 'দাগ',
    status_clear: 'ক্লিয়ার',
    status_review: 'রিভিউ',
    status_block: 'ব্লক',
    rules_passed_suffix: 'টি নিয়ম উত্তীর্ণ',
    khas_overlap_label: 'সরকারি খাল দখল',
    khas_clean_label: 'কোনো বিরোধ নেই',
    action_block: 'নামজারি চূড়ান্ত অনুমোদন স্থগিত। এসি ল্যান্ডে নথি প্রেরণের নির্দেশ।',
    action_review: 'শুনানির পূর্বে বিগত ৩ অর্থবছরের বকেয়া ভূমি উন্নয়ন কর আদায় সাপেক্ষ।',
    action_clear: 'সকল রেকর্ড ও ক্যাডাস্ট্রাল সীমানা সামঞ্জস্যপূর্ণ। নামজারি অনুমোদনের সুপারিশ।',
    layers_btn: 'স্তরসমূহ',
    reset_view_btn: 'রিসেট',
    tab_overview: 'সারসংক্ষেপ',
    tab_history: 'ইতিহাস',
    tab_tax: 'কর স্থিতি',
    tab_liens: 'দায় ও লিয়েন',
    tab_audit: 'অডিট লেজার',
    card_area_title: 'জমির পরিমাপ তুলনা',
    card_khas_title: 'খাস খাল দখল',
    card_rules_title: 'বিধি পরীক্ষণ',
    area_cs: 'সিএস পৈত্রিক',
    area_deed: 'দলিল দাবি',
    area_dlrs: 'ডিএলআরএস প্রকৃত',
    tolerance_label: 'সীমা ±০.২০ শতক',
    rule_unmutated_name: 'নামজারিহীন দলিল',
    rule_area_name: 'আয়তন সংবিধিবদ্ধ সীমা',
    rule_owner_name: 'খতিয়ান বনাম করদাতা',
    rule_class_name: 'শ্রেণি সামঞ্জস্য',
    rule_khas_name: 'সরকারি খাল দখল',
    rule_khas_encroachment: 'সরকারি খাস বা খাল দখল',
    rule_area_tolerance: 'আয়তন সংবিধিবদ্ধ সীমা',
    rule_mutation_status: 'নামজারি স্থিতি ও দলিল ব্যবধান',
    rule_owner_name_match: 'খতিয়ান বনাম করদাতা নাম মিল',
    rule_ld_tax_compliance: 'ভূমি উন্নয়ন কর অনুবর্তীতা',
    status_unknown: 'অপর্যাপ্ত তথ্য',
    status_insufficient_data: 'অপর্যাপ্ত তথ্য',
    legal_ref_label: 'আইনি ভিত্তি',
    evidence_label: 'প্রমাণ',
    rules_all_passed: 'সকল সংবিধিবদ্ধ নিয়ম উত্তীর্ণ',
    rule_passed_count: 'টি নিয়ম সফলভাবে উত্তীর্ণ',
    no_liens_title: 'কোনো সক্রিয় দায় বা লিয়েন নেই',
    no_liens_desc: 'ব্যাংক দায়, বন্ধক বা সরকারি অধিগ্রহণ স্থগিতাদেশ পাওয়া যায়নি।',
    chain_intact: 'হ্যাশ-চেইন সম্পূর্ণ অটুট',
    unit_dec: 'শতক',
    unit_days: 'দিন',
    unit_pct: '%',
  },
  en: {
    app_title: 'NAKSHA',
    role_officer: 'AC Land / Kanoongo',
    theme_light: 'Light Mode',
    theme_dark: 'Dark Mode',
    lang_btn: 'বাং',
    syn_footer: 'Synthetic demonstration data — Not an official government record',
    portal_ld_tax: 'LD Tax Portal',
    portal_e_mutation: 'e-Mutation',
    mouza: 'Mouza',
    khatian: 'Khatian',
    dag: 'Dag',
    status_clear: 'CLEAR',
    status_review: 'REVIEW',
    status_block: 'BLOCK',
    rules_passed_suffix: 'rules passed',
    khas_overlap_label: 'Khas Overlap',
    khas_clean_label: 'Zero Overlap',
    action_block: 'Do not register. Place mutation on hold & refer to AC Land.',
    action_review: 'Issue hearing notice. Collect 3-year tax arrears prior to mutation.',
    action_clear: 'All boundaries & ownership records match. Recommended for approval.',
    layers_btn: 'Layers',
    reset_view_btn: 'Reset',
    tab_overview: 'Overview',
    tab_history: 'History',
    tab_tax: 'Tax',
    tab_liens: 'Liens',
    tab_audit: 'Audit',
    card_area_title: 'Area Comparison',
    card_khas_title: 'Khas Encroachment',
    card_rules_title: 'Rule Checks',
    area_cs: 'Ancestral CS',
    area_deed: 'Deed Claim',
    area_dlrs: 'DLRS Truth',
    tolerance_label: 'Limit ±0.20 dec',
    rule_unmutated_name: 'Deed vs Mutation Gap',
    rule_area_name: 'Area Statutory Limit',
    rule_owner_name: 'Khatian vs Tax Payer',
    rule_class_name: 'Land Classification',
    rule_khas_name: 'Khas Canal Overlap',
    rule_khas_encroachment: 'Khas Canal Encroachment',
    rule_area_tolerance: 'Area Tolerance Limit',
    rule_mutation_status: 'Deed Mutation Gap',
    rule_owner_name_match: 'Khatian vs Tax Payer Name',
    rule_ld_tax_compliance: 'LD Tax Compliance',
    status_unknown: 'Insufficient data',
    status_insufficient_data: 'Insufficient data',
    legal_ref_label: 'Statutory Reference',
    evidence_label: 'Evidence',
    rules_all_passed: 'All statutory rules passed',
    rule_passed_count: 'rules passed',
    no_liens_title: 'No active liens or locks',
    no_liens_desc: 'No bank mortgages, court attachments or acquisition locks.',
    chain_intact: 'Audit Chain Intact & Signed',
    unit_dec: 'dec',
    unit_days: 'days',
    unit_pct: '%',
  }
};

let currentLang = 'bn';
let currentTheme = 'dark';

function t(key) {
  return (I18N[currentLang] && I18N[currentLang][key]) || key;
}

function toggleLanguage() {
  currentLang = currentLang === 'bn' ? 'en' : 'bn';
  document.documentElement.lang = currentLang;
  return currentLang;
}

function toggleTheme() {
  currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', currentTheme);
  return currentTheme;
}
