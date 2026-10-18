"""Unit tests for NAKSHA canonical Pydantic models."""
import pytest
from pydantic import ValidationError

from naksha.models.canonical import (
    ExtractedField,
    SourceReference,
    LandRecord,
    RecordMatch,
    Discrepancy,
    VerificationResult,
)
from naksha.models.enums import (
    AgencyType,
    LandAreaUnit,
    SurveyEra,
    LandClass,
    VerificationVerdict,
    DiscrepancyType,
    DiscrepancySeverity,
)


def test_extracted_field_generic_types():
    """Verify ExtractedField properly handles generic types and default confidence."""
    # String field
    str_field = ExtractedField[str](
        raw_value="দাগ নং ৪০২",
        normalized_value="402",
        confidence=0.98,
        source_citation="Column 3",
    )
    assert str_field.raw_value == "দাগ নং ৪০২"
    assert str_field.normalized_value == "402"
    assert str_field.confidence == 0.98

    # Float field
    float_field = ExtractedField[float](
        raw_value="0.50",
        normalized_value=0.50,
    )
    assert float_field.normalized_value == 0.50
    assert float_field.confidence == 1.0  # default


def test_extracted_field_confidence_bounds():
    """Confidence score must be constrained between 0.0 and 1.0."""
    with pytest.raises(ValidationError):
        ExtractedField[str](confidence=1.5)

    with pytest.raises(ValidationError):
        ExtractedField[str](confidence=-0.1)


def test_source_reference_valid():
    """SourceReference requires valid AgencyType and required fields."""
    src = SourceReference(
        agency=AgencyType.SUB_REGISTRY,
        document_type="Deed",
        source_record_id="DEED-1234",
    )
    assert src.agency == AgencyType.SUB_REGISTRY
    assert src.document_type == "Deed"
    assert src.source_record_id == "DEED-1234"


def test_land_record_minimal_required_fields():
    """LandRecord must instantiate with only minimal required fields, leaving optional fields as None."""
    src = SourceReference(
        agency=AgencyType.DLRS,
        document_type="Fragment",
        source_record_id="FRAG-001",
    )
    rec = LandRecord(
        id="REC-TEST-MINIMAL",
        source=src,
    )
    assert rec.id == "REC-TEST-MINIMAL"
    assert rec.source.agency == AgencyType.DLRS
    assert rec.dag_number is None
    assert rec.khatian_number is None
    assert rec.recorded_area is None
    assert rec.area_in_decimals is None
    assert rec.owner_name is None
    assert rec.is_synthetic is True
    assert "SYNTHETIC" in rec.synthetic_disclaimer


def test_land_record_full_serialization():
    """Verify serialization to and from dictionary / JSON."""
    src = SourceReference(
        agency=AgencyType.AC_LAND,
        document_type="e-Mutation",
        source_record_id="MUT-998",
        issuing_office="Gazipur Sadar",
    )
    rec = LandRecord(
        id="REC-TEST-FULL",
        source=src,
        dag_number=ExtractedField(raw_value="402", normalized_value="402"),
        khatian_number=ExtractedField(raw_value="120", normalized_value="120"),
        recorded_area=6.0,
        recorded_unit=LandAreaUnit.DECIMAL,
        area_in_decimals=6.0,
        area_in_sq_meters=242.81,
        land_class=LandClass.NAL,
    )

    dumped = rec.model_dump()
    assert dumped["id"] == "REC-TEST-FULL"
    assert dumped["dag_number"]["normalized_value"] == "402"
    assert dumped["area_in_decimals"] == 6.0

    # Test JSON round-trip
    json_str = rec.model_dump_json()
    reconstructed = LandRecord.model_validate_json(json_str)
    assert reconstructed.id == rec.id
    assert reconstructed.dag_number.normalized_value == "402"


def test_discrepancy_and_verification_result():
    """Verify Discrepancy and VerificationResult data model constraints."""
    disc = Discrepancy(
        discrepancy_type=DiscrepancyType.AREA_MISMATCH,
        severity=DiscrepancySeverity.BLOCKING,
        field_name="area_in_decimals",
        record_a_id="REC-A",
        record_b_id="REC-B",
        value_a="6.0 dec",
        value_b="5.1 dec",
        difference_description="0.9 dec area discrepancy",
    )
    assert disc.severity == DiscrepancySeverity.BLOCKING

    match = RecordMatch(
        target_record_id="REC-A",
        matched_record_id="REC-B",
        match_score=0.95,
        matched_fields=["dag_number", "khatian_number"],
        explanation="Matched on plot and khatian",
    )

    res = VerificationResult(
        primary_record_id="REC-A",
        compared_record_ids=["REC-B"],
        verdict=VerificationVerdict.BLOCK,
        summary="BLOCK: area mismatch detected",
        matches=[match],
        discrepancies=[disc],
    )
    assert res.verdict == VerificationVerdict.BLOCK
    assert len(res.matches) == 1
    assert len(res.discrepancies) == 1
