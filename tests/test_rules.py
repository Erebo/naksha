"""Comprehensive Unit and Integration Tests for NAKSHA Statutory 5-Rule Engine.

Covers:
- Boundary conditions for each of the 5 statutory rules (at, below, above limit)
- Floating point boundary sensitivity (e.g. 0.20 vs 0.2000001, 0.19, 0.21)
- Missing / unparseable data strictly producing UNKNOWN across all rules
- Exact parity between Bengali numerals (০-৯) and ASCII digits (0-9)
- Mutation timeliness with fixed `today` (29, 30, 31 days)
- compute_final_verdict resolution hierarchy (BLOCK > REVIEW > UNKNOWN > CLEAR)
- Blocking discrepancies (duplicate deed, dag mismatch) enforcing BLOCK even if all rules PASS
- Unseeded parcel "999" returning 404 across all 4 parcel endpoints
- Dynamic verification verdicts for Dag 401 (CLEAR), Dag 402 (BLOCK), Dag 403 (REVIEW) with populated `rules` list
- Strict token boundary normalization in normalize_parcel_key ("1401", "4010", "unknown", "")
"""
from datetime import date
import pytest
from fastapi.testclient import TestClient

from naksha.api.app import app
from naksha.data.synthetic_spatial import normalize_parcel_key
from naksha.models.canonical import Discrepancy
from naksha.models.enums import DiscrepancySeverity, DiscrepancyType, VerificationVerdict
from naksha.models.rules import RuleResult, RuleSeverity, RuleStatus
from naksha.services.rules import (
    compute_final_verdict,
    evaluate_area_tolerance,
    evaluate_khas_encroachment,
    evaluate_ld_tax_compliance,
    evaluate_mutation_status,
    evaluate_owner_name_match,
)

client = TestClient(app)


# ==============================================================================
# 1. Rule 1: khas_encroachment
# ==============================================================================

def test_khas_encroachment_boundary_conditions():
    """Khas limit is 0.0: <= 0.0 PASS, > 0.0 FAIL with severity BLOCK."""
    # Exactly at limit
    res_at = evaluate_khas_encroachment(0.0)
    assert res_at.status == RuleStatus.PASS
    assert res_at.severity == RuleSeverity.BLOCK
    assert res_at.measured == 0.0

    # Below limit (negative overlap or zero)
    res_below = evaluate_khas_encroachment(-0.01)
    assert res_below.status == RuleStatus.PASS
    assert res_below.measured == -0.01

    # Just above limit
    res_above = evaluate_khas_encroachment(0.01)
    assert res_above.status == RuleStatus.FAIL
    assert res_above.severity == RuleSeverity.BLOCK
    assert res_above.measured == 0.01


def test_khas_encroachment_float_boundary():
    """Float sensitivity around 0.0."""
    res_tiny_pos = evaluate_khas_encroachment(0.0000001)
    assert res_tiny_pos.status == RuleStatus.FAIL

    res_zero = evaluate_khas_encroachment(0.0000000)
    assert res_zero.status == RuleStatus.PASS


def test_khas_encroachment_bengali_digits():
    """Bengali digits must behave identically to ASCII digits."""
    res_bn_pass = evaluate_khas_encroachment("০.০")
    res_en_pass = evaluate_khas_encroachment("0.0")
    assert res_bn_pass.status == res_en_pass.status == RuleStatus.PASS
    assert res_bn_pass.measured == res_en_pass.measured == 0.0

    res_bn_fail = evaluate_khas_encroachment("০.০১")
    res_en_fail = evaluate_khas_encroachment("0.01")
    assert res_bn_fail.status == res_en_fail.status == RuleStatus.FAIL
    assert res_bn_fail.measured == res_en_fail.measured == 0.01


def test_khas_encroachment_missing_data():
    """None, empty, or unparseable input returns UNKNOWN (severity BLOCK)."""
    for val in (None, "", "   ", "unverified", "abc"):
        res = evaluate_khas_encroachment(val)
        assert res.status == RuleStatus.UNKNOWN
        assert res.severity == RuleSeverity.BLOCK
        assert res.measured is None


# ==============================================================================
# 2. Rule 2: area_tolerance
# ==============================================================================

def test_area_tolerance_boundary_conditions():
    """Symmetric ±0.20: abs(deed - survey) <= 0.20 PASS, > 0.20 FAIL (BLOCK)."""
    # Exactly at limit (+0.20)
    res_at_pos = evaluate_area_tolerance(deed_area=5.20, survey_area=5.00)
    assert res_at_pos.status == RuleStatus.PASS
    assert res_at_pos.severity == RuleSeverity.BLOCK
    assert res_at_pos.measured == pytest.approx(0.20)

    # Exactly at limit (-0.20 symmetric)
    res_at_neg = evaluate_area_tolerance(deed_area=4.80, survey_area=5.00)
    assert res_at_neg.status == RuleStatus.PASS
    assert res_at_neg.severity == RuleSeverity.BLOCK
    assert res_at_neg.measured == pytest.approx(0.20)

    # Just below limit (0.19)
    res_below = evaluate_area_tolerance(deed_area=5.19, survey_area=5.00)
    assert res_below.status == RuleStatus.PASS
    assert res_below.measured == pytest.approx(0.19)

    # Just above limit (0.21)
    res_above = evaluate_area_tolerance(deed_area=5.21, survey_area=5.00)
    assert res_above.status == RuleStatus.FAIL
    assert res_above.severity == RuleSeverity.BLOCK
    assert res_above.measured == pytest.approx(0.21)


def test_area_tolerance_float_boundary_cases():
    """Precision float boundary cases: 0.20 vs 0.2000001 vs 0.1999999."""
    # 0.20 is at limit -> PASS
    res_exact = evaluate_area_tolerance(deed_area=5.20, survey_area=5.00)
    assert res_exact.status == RuleStatus.PASS

    # 0.2000001 exceeds limit -> FAIL
    res_micro_over = evaluate_area_tolerance(deed_area=5.2000001, survey_area=5.00)
    assert res_micro_over.status == RuleStatus.FAIL

    # 0.1999999 is within limit -> PASS
    res_micro_under = evaluate_area_tolerance(deed_area=5.1999999, survey_area=5.00)
    assert res_micro_under.status == RuleStatus.PASS


def test_area_tolerance_bengali_digits():
    """Bengali numerals parse accurately and produce identical evaluations."""
    res_bn = evaluate_area_tolerance(deed_area="৫.২০", survey_area="৫.০০")
    res_en = evaluate_area_tolerance(deed_area="5.20", survey_area="5.00")
    assert res_bn.status == res_en.status == RuleStatus.PASS
    assert res_bn.measured == res_en.measured == pytest.approx(0.20)

    res_bn_fail = evaluate_area_tolerance(deed_area="৫.২১", survey_area="৫.০০")
    res_en_fail = evaluate_area_tolerance(deed_area="5.21", survey_area="5.00")
    assert res_bn_fail.status == res_en_fail.status == RuleStatus.FAIL
    assert res_bn_fail.measured == res_en_fail.measured == pytest.approx(0.21)


def test_area_tolerance_missing_data():
    """Missing or unparseable deed/survey area returns UNKNOWN."""
    cases = [
        (None, 5.0),
        (5.0, None),
        (None, None),
        ("", "5.0"),
        ("invalid", 5.0),
        (5.0, "অজানা"),
    ]
    for d, s in cases:
        res = evaluate_area_tolerance(d, s)
        assert res.status == RuleStatus.UNKNOWN
        assert res.severity == RuleSeverity.BLOCK
        assert res.measured is None


# ==============================================================================
# 3. Rule 3: owner_name_match
# ==============================================================================

def test_owner_name_match_boundary_conditions():
    """Phonetic threshold 0.80: >= 0.80 PASS, < 0.80 FAIL (severity REVIEW)."""
    # Identical names
    res_same = evaluate_owner_name_match("Md. Abdul Karim", "Md. Abdul Karim")
    assert res_same.status == RuleStatus.PASS
    assert res_same.severity == RuleSeverity.REVIEW
    assert res_same.measured == 1.0

    # Bengali honorific prefix stripped and phonetically matched
    res_phonetic = evaluate_owner_name_match("মোঃ আব্দুল করিম", "Md. Abdul Karim")
    assert res_phonetic.status == RuleStatus.PASS
    assert res_phonetic.severity == RuleSeverity.REVIEW
    assert res_phonetic.measured >= 0.80

    # Completely divergent names (subsequent buyer conflict)
    res_diff = evaluate_owner_name_match("Abdul Karim", "Tariqul Islam")
    assert res_diff.status == RuleStatus.FAIL
    assert res_diff.severity == RuleSeverity.REVIEW
    assert res_diff.measured < 0.80


def test_owner_name_match_missing_data():
    """Missing owner names return UNKNOWN with severity REVIEW."""
    for n_a, n_b in [(None, "Karim"), ("Karim", None), (None, None), ("", "Karim"), ("Karim", "   ")]:
        res = evaluate_owner_name_match(n_a, n_b)
        assert res.status == RuleStatus.UNKNOWN
        assert res.severity == RuleSeverity.REVIEW
        assert res.measured is None


# ==============================================================================
# 4. Rule 4: ld_tax_compliance
# ==============================================================================

def test_ld_tax_compliance_boundary_conditions():
    """Permitted arrears limit is 1 fiscal year: <= 1 PASS, > 1 FAIL (REVIEW)."""
    # Exactly at limit (1 year arrears)
    res_at = evaluate_ld_tax_compliance(arrears_years=1)
    assert res_at.status == RuleStatus.PASS
    assert res_at.severity == RuleSeverity.REVIEW
    assert res_at.measured == 1.0

    # Below limit (0 arrears, paid)
    res_below = evaluate_ld_tax_compliance(arrears_years=0)
    assert res_below.status == RuleStatus.PASS
    assert res_below.measured == 0.0

    # Above limit (2 years arrears)
    res_above = evaluate_ld_tax_compliance(arrears_years=2)
    assert res_above.status == RuleStatus.FAIL
    assert res_above.severity == RuleSeverity.REVIEW
    assert res_above.measured == 2.0


def test_ld_tax_compliance_bengali_digits():
    """Bengali numerals parse accurately into fiscal years."""
    res_bn_1 = evaluate_ld_tax_compliance("১")
    res_en_1 = evaluate_ld_tax_compliance("1")
    assert res_bn_1.status == res_en_1.status == RuleStatus.PASS
    assert res_bn_1.measured == res_en_1.measured == 1.0

    res_bn_0 = evaluate_ld_tax_compliance("০")
    res_en_0 = evaluate_ld_tax_compliance("0")
    assert res_bn_0.status == res_en_0.status == RuleStatus.PASS
    assert res_bn_0.measured == res_en_0.measured == 0.0

    res_bn_3 = evaluate_ld_tax_compliance("৩")
    res_en_3 = evaluate_ld_tax_compliance("3")
    assert res_bn_3.status == res_en_3.status == RuleStatus.FAIL
    assert res_bn_3.measured == res_en_3.measured == 3.0

    # Large numeral test: "১২৪" vs "124"
    res_bn_large = evaluate_ld_tax_compliance("১২৪")
    res_en_large = evaluate_ld_tax_compliance("124")
    assert res_bn_large.status == res_en_large.status == RuleStatus.FAIL
    assert res_bn_large.measured == res_en_large.measured == 124.0


def test_ld_tax_compliance_missing_data():
    """Missing tax record or unparseable arrears returns UNKNOWN."""
    for val in (None, "", "unknown", "invalid"):
        res = evaluate_ld_tax_compliance(val)
        assert res.status == RuleStatus.UNKNOWN
        assert res.severity == RuleSeverity.REVIEW
        assert res.measured is None

    # Missing tax record flag
    res_no_rec = evaluate_ld_tax_compliance(0, tax_record_present=False)
    assert res_no_rec.status == RuleStatus.UNKNOWN
    assert res_no_rec.severity == RuleSeverity.REVIEW


# ==============================================================================
# 5. Rule 5: mutation_status
# ==============================================================================

def test_mutation_status_with_fixed_today():
    """Mutation threshold 30 days: deed without mutation tested at 29, 30, 31 days."""
    fixed_today = date(2024, 6, 1)

    # 1. 29 days elapsed (2024-05-03) -> PASS
    res_29 = evaluate_mutation_status(
        deed_present=True,
        mutation_present=False,
        deed_date=date(2024, 5, 3),
        today=fixed_today,
    )
    assert res_29.status == RuleStatus.PASS
    assert res_29.severity == RuleSeverity.REVIEW
    assert res_29.measured == 29.0

    # 2. Exactly 30 days elapsed (2024-05-02) -> PASS
    res_30 = evaluate_mutation_status(
        deed_present=True,
        mutation_present=False,
        deed_date=date(2024, 5, 2),
        today=fixed_today,
    )
    assert res_30.status == RuleStatus.PASS
    assert res_30.severity == RuleSeverity.REVIEW
    assert res_30.measured == 30.0

    # 3. 31 days elapsed (2024-05-01) -> FAIL (REVIEW)
    res_31 = evaluate_mutation_status(
        deed_present=True,
        mutation_present=False,
        deed_date=date(2024, 5, 1),
        today=fixed_today,
    )
    assert res_31.status == RuleStatus.FAIL
    assert res_31.severity == RuleSeverity.REVIEW
    assert res_31.measured == 31.0


def test_mutation_status_days_unmutated_bengali_digits():
    """Bengali numerals for days_unmutated parameter."""
    res_bn_30 = evaluate_mutation_status(
        deed_present=True,
        mutation_present=False,
        days_unmutated="৩০",
    )
    res_en_30 = evaluate_mutation_status(
        deed_present=True,
        mutation_present=False,
        days_unmutated="30",
    )
    assert res_bn_30.status == res_en_30.status == RuleStatus.PASS
    assert res_bn_30.measured == res_en_30.measured == 30.0

    res_bn_31 = evaluate_mutation_status(
        deed_present=True,
        mutation_present=False,
        days_unmutated="৩১",
    )
    res_en_31 = evaluate_mutation_status(
        deed_present=True,
        mutation_present=False,
        days_unmutated="31",
    )
    assert res_bn_31.status == res_en_31.status == RuleStatus.FAIL
    assert res_bn_31.measured == res_en_31.measured == 31.0


def test_mutation_status_mutation_present():
    """Mutation approved record present produces PASS with 0 measured days."""
    res = evaluate_mutation_status(deed_present=True, mutation_present=True)
    assert res.status == RuleStatus.PASS
    assert res.severity == RuleSeverity.REVIEW
    assert res.measured == 0.0


def test_mutation_status_missing_data():
    """Neither deed nor mutation, or unparseable deed date returns UNKNOWN."""
    # Neither record exists
    res_none = evaluate_mutation_status(deed_present=False, mutation_present=False)
    assert res_none.status == RuleStatus.UNKNOWN
    assert res_none.severity == RuleSeverity.REVIEW

    # Deed present, but date missing/unparseable
    res_nodate = evaluate_mutation_status(
        deed_present=True,
        mutation_present=False,
        deed_date=None,
        days_unmutated=None,
    )
    assert res_nodate.status == RuleStatus.UNKNOWN


# ==============================================================================
# 6. compute_final_verdict Hierarchy and Discrepancy Escalation
# ==============================================================================

def test_compute_final_verdict_hierarchy():
    """Worst-case hierarchy: BLOCK > REVIEW > UNKNOWN > CLEAR."""
    pass_rule = RuleResult(
        rule_id="r1", status=RuleStatus.PASS, severity=RuleSeverity.BLOCK, evidence="pass", legal_ref="TODO",
    )
    review_rule = RuleResult(
        rule_id="r2", status=RuleStatus.FAIL, severity=RuleSeverity.REVIEW, evidence="review", legal_ref="TODO",
    )
    unknown_rule = RuleResult(
        rule_id="r3", status=RuleStatus.UNKNOWN, severity=RuleSeverity.REVIEW, evidence="unknown", legal_ref="TODO",
    )
    block_rule = RuleResult(
        rule_id="r4", status=RuleStatus.FAIL, severity=RuleSeverity.BLOCK, evidence="block", legal_ref="TODO",
    )

    # 1. All PASS -> CLEAR
    assert compute_final_verdict([pass_rule, pass_rule]) == VerificationVerdict.CLEAR

    # 2. PASS + UNKNOWN -> REVIEW
    assert compute_final_verdict([pass_rule, unknown_rule]) == VerificationVerdict.REVIEW

    # 3. PASS + REVIEW -> REVIEW
    assert compute_final_verdict([pass_rule, review_rule]) == VerificationVerdict.REVIEW

    # 4. REVIEW + UNKNOWN -> REVIEW
    assert compute_final_verdict([review_rule, unknown_rule]) == VerificationVerdict.REVIEW

    # 5. BLOCK overrides everything (even if other rules are PASS, REVIEW, or UNKNOWN)
    assert compute_final_verdict([pass_rule, block_rule]) == VerificationVerdict.BLOCK
    assert compute_final_verdict([review_rule, block_rule]) == VerificationVerdict.BLOCK
    assert compute_final_verdict([unknown_rule, block_rule]) == VerificationVerdict.BLOCK
    assert compute_final_verdict([pass_rule, review_rule, unknown_rule, block_rule]) == VerificationVerdict.BLOCK


def test_blocking_discrepancy_enforces_block_when_rules_pass():
    """Duplicate-deed or dag-mismatch discrepancy produces BLOCK even when all 5 rules PASS."""
    all_pass_rules = [
        RuleResult(rule_id=f"rule_{i}", status=RuleStatus.PASS, severity=RuleSeverity.BLOCK, evidence="ok", legal_ref="TODO")
        for i in range(5)
    ]

    # Duplicate deed blocking discrepancy
    dup_disc = Discrepancy(
        discrepancy_type=DiscrepancyType.DUPLICATE_RECORD,
        severity=DiscrepancySeverity.BLOCKING,
        field_name="source_record_id",
        record_a_id="rec-1",
        record_b_id="rec-2",
        difference_description="Duplicate sale deed registered on same dag.",
    )
    assert compute_final_verdict(all_pass_rules, discrepancies=[dup_disc]) == VerificationVerdict.BLOCK

    # Dag mismatch blocking discrepancy
    dag_disc = Discrepancy(
        discrepancy_type=DiscrepancyType.DAG_MISMATCH,
        severity=DiscrepancySeverity.BLOCKING,
        field_name="dag_number",
        record_a_id="rec-1",
        record_b_id="rec-2",
        difference_description="Dag mismatch conflict.",
    )
    assert compute_final_verdict(all_pass_rules, discrepancies=[dag_disc]) == VerificationVerdict.BLOCK

    # Warning discrepancy alone results in REVIEW
    warn_disc = Discrepancy(
        discrepancy_type=DiscrepancyType.KHATIAN_MISMATCH,
        severity=DiscrepancySeverity.WARNING,
        field_name="khatian_number",
        record_a_id="rec-1",
        record_b_id="rec-2",
        difference_description="Khatian mismatch notice.",
    )
    assert compute_final_verdict(all_pass_rules, discrepancies=[warn_disc]) == VerificationVerdict.REVIEW


# ==============================================================================
# 7. Unseeded Parcel "999" 404 Across Endpoints
# ==============================================================================

def test_unseeded_parcel_999_returns_404():
    """Unseeded parcel '999' returns 404 on all 4 parcel endpoints."""
    endpoints = [
        "/api/v1/spatial/parcels/999/verification",
        "/api/v1/spatial/parcels/999/layers",
        "/api/v1/spatial/parcels/999/neighbors",
        "/api/v1/spatial/parcels/999/conflicts",
    ]
    for url in endpoints:
        res = client.get(url)
        assert res.status_code == 404, f"Expected 404 for {url}, got {res.status_code}: {res.text}"


# ==============================================================================
# 8. Dynamic Verification Endpoints with Populated Rules List
# ==============================================================================

def test_api_verification_verdicts_and_rules_list():
    """Parcels 401 (CLEAR), 402 (BLOCK), 403 (REVIEW) include populated rules list."""
    # 1. Parcel 401 -> CLEAR
    res_401 = client.get("/api/v1/spatial/parcels/401/verification")
    assert res_401.status_code == 200
    body_401 = res_401.json()
    assert body_401["verdict"] == "CLEAR"
    assert "rules" in body_401
    assert len(body_401["rules"]) == 5
    rule_ids_401 = {r["rule_id"] for r in body_401["rules"]}
    assert rule_ids_401 == {
        "khas_encroachment", "area_tolerance", "owner_name_match", "ld_tax_compliance", "mutation_status",
    }
    for r in body_401["rules"]:
        assert r["status"] == "PASS", f"Rule {r['rule_id']} expected PASS, got {r['status']}"

    # 2. Parcel 402 -> BLOCK
    res_402 = client.get("/api/v1/spatial/parcels/402/verification")
    assert res_402.status_code == 200
    body_402 = res_402.json()
    assert body_402["verdict"] == "BLOCK"
    assert "rules" in body_402
    assert len(body_402["rules"]) == 5
    rules_by_id_402 = {r["rule_id"]: r for r in body_402["rules"]}
    assert rules_by_id_402["khas_encroachment"]["status"] == "FAIL"
    assert rules_by_id_402["khas_encroachment"]["severity"] == "BLOCK"
    assert rules_by_id_402["area_tolerance"]["status"] == "FAIL"
    assert rules_by_id_402["area_tolerance"]["severity"] == "BLOCK"

    # 3. Parcel 403 -> REVIEW
    res_403 = client.get("/api/v1/spatial/parcels/403/verification")
    assert res_403.status_code == 200
    body_403 = res_403.json()
    assert body_403["verdict"] == "REVIEW"
    assert "rules" in body_403
    assert len(body_403["rules"]) == 5
    rules_by_id_403 = {r["rule_id"]: r for r in body_403["rules"]}
    assert rules_by_id_403["ld_tax_compliance"]["status"] == "FAIL"
    assert rules_by_id_403["ld_tax_compliance"]["severity"] == "REVIEW"
    assert rules_by_id_403["mutation_status"]["status"] == "FAIL"
    assert rules_by_id_403["mutation_status"]["severity"] == "REVIEW"


# ==============================================================================
# 9. normalize_parcel_key Discrete Token Parsing
# ==============================================================================

def test_normalize_parcel_key_discrete_tokens():
    """Verify normalize_parcel_key parses discrete tokens and returns None for non-seeded strings."""
    # Substring edge cases must return None (no loose substring matching)
    assert normalize_parcel_key("1401") is None
    assert normalize_parcel_key("4010") is None
    assert normalize_parcel_key("4020") is None
    assert normalize_parcel_key("2402") is None
    assert normalize_parcel_key("unknown") is None
    assert normalize_parcel_key("") is None
    assert normalize_parcel_key(None) is None
    assert normalize_parcel_key("999") is None
    assert normalize_parcel_key("৯৯৯") is None

    # Valid discrete tokens (English & Bengali)
    assert normalize_parcel_key("401") == "401"
    assert normalize_parcel_key("৪০১") == "401"
    assert normalize_parcel_key("402") == "402"
    assert normalize_parcel_key("৪০২") == "402"
    assert normalize_parcel_key("403") == "403"
    assert normalize_parcel_key("৪০৩") == "403"

    # Prefixed identifier tokens
    assert normalize_parcel_key("BS-401") == "401"
    assert normalize_parcel_key("দাগ নং ৪০২") == "402"
    assert normalize_parcel_key("par-8f92-bd04-syn") == "402"
    assert normalize_parcel_key("par-401-west-syn") == "401"
    assert normalize_parcel_key("par-403-south-syn") == "403"
