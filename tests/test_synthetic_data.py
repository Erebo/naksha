"""Unit tests verifying synthetic benchmark dataset integrity and scenarios."""
import pytest
from naksha.data.synthetic import generate_synthetic_records
from naksha.models.enums import AgencyType, DiscrepancySeverity, DiscrepancyType, VerificationVerdict
from naksha.services.verification import compare_records, verify_record_against_cohort


def test_synthetic_records_safety_markers():
    """All benchmark records MUST be explicitly labelled as synthetic with a disclaimer."""
    records = generate_synthetic_records()
    assert len(records) >= 5

    for rec in records:
        assert rec.is_synthetic is True
        assert "SYNTHETIC" in rec.synthetic_disclaimer
        assert rec.id.startswith("SYN-")


def test_matching_records_pair():
    """SYN-MATCH-01 (Deed) and SYN-MATCH-02 (e-Mutation) must match on core identifiers."""
    records = {r.id: r for r in generate_synthetic_records()}
    rec_a = records["SYN-MATCH-01"]
    rec_b = records["SYN-MATCH-02"]

    assert rec_a.source.agency == AgencyType.SUB_REGISTRY
    assert rec_b.source.agency == AgencyType.AC_LAND

    # Normalized fields should match
    assert rec_a.mouza.normalized_value.lower() == rec_b.mouza.normalized_value.lower()
    assert rec_a.dag_number.normalized_value == rec_b.dag_number.normalized_value == "402"
    assert rec_a.khatian_number.normalized_value == rec_b.khatian_number.normalized_value == "120"
    assert rec_a.area_in_decimals == rec_b.area_in_decimals == 6.0

    match, discrepancies = compare_records(rec_a, rec_b)
    assert match is not None
    assert match.match_score >= 0.75
    assert "dag_number" in match.matched_fields
    assert "khatian_number" in match.matched_fields
    assert "area_in_decimals" in match.matched_fields
    assert len(discrepancies) == 0


def test_conflicting_dag_and_khatian_record():
    """SYN-CONFLICT-ID-01 must trigger DAG_MISMATCH when compared with SYN-MATCH-01."""
    records = {r.id: r for r in generate_synthetic_records()}
    rec_a = records["SYN-MATCH-01"]  # Dag 402, Khatian 120
    rec_tax = records["SYN-CONFLICT-ID-01"]  # Dag 403, Khatian 125

    match, discrepancies = compare_records(rec_a, rec_tax)
    disc_types = [d.discrepancy_type for d in discrepancies]
    assert DiscrepancyType.DAG_MISMATCH in disc_types
    assert DiscrepancyType.KHATIAN_MISMATCH in disc_types


def test_conflicting_area_record():
    """SYN-CONFLICT-AREA-01 (DLRS 5.1 dec) vs SYN-MATCH-01 (Deed 6.0 dec) must trigger AREA_MISMATCH."""
    records = {r.id: r for r in generate_synthetic_records()}
    rec_deed = records["SYN-MATCH-01"]  # 6.0 dec
    rec_dlrs = records["SYN-CONFLICT-AREA-01"]  # 5.1 dec

    match, discrepancies = compare_records(rec_deed, rec_dlrs)
    disc_types = [d.discrepancy_type for d in discrepancies]
    assert DiscrepancyType.AREA_MISMATCH in disc_types

    area_disc = next(d for d in discrepancies if d.discrepancy_type == DiscrepancyType.AREA_MISMATCH)
    assert area_disc.severity == DiscrepancySeverity.BLOCKING
    assert "0.90" in area_disc.difference_description


def test_duplicate_deed_record():
    """SYN-DUPLICATE-01 against SYN-MATCH-01 must flag DUPLICATE_RECORD."""
    records = {r.id: r for r in generate_synthetic_records()}
    rec_deed_1 = records["SYN-MATCH-01"]
    rec_deed_2 = records["SYN-DUPLICATE-01"]

    match, discrepancies = compare_records(rec_deed_1, rec_deed_2)
    disc_types = [d.discrepancy_type for d in discrepancies]
    assert DiscrepancyType.DUPLICATE_RECORD in disc_types


def test_incomplete_damaged_record():
    """SYN-INCOMPLETE-01 must trigger INCOMPLETE_RECORD discrepancies."""
    records = {r.id: r for r in generate_synthetic_records()}
    rec_incomplete = records["SYN-INCOMPLETE-01"]

    assert rec_incomplete.dag_number is None
    assert rec_incomplete.khatian_number is None
    assert rec_incomplete.owner_name.confidence < 0.5

    result = verify_record_against_cohort(primary=rec_incomplete, cohort=list(records.values()))
    assert result.verdict in (VerificationVerdict.REVIEW, VerificationVerdict.BLOCK)
    disc_types = [d.discrepancy_type for d in result.discrepancies]
    assert DiscrepancyType.INCOMPLETE_RECORD in disc_types
