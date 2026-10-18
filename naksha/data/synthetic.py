"""Predefined Synthetic Benchmark Records for NAKSHA Stage 2.

All records in this module are strictly SYNTHETIC and generated exclusively
for automated testing, algorithm calibration, and demonstration of the
LandTech 2026 hackathon prototype.
NO REAL CITIZEN NAMES, REAL NIDS, OR ACTUAL GOVERNMENT RECORD NUMBERS ARE INCLUDED.
"""
from datetime import datetime, timezone
from typing import List

from naksha.models.canonical import ExtractedField, GeoJSONGeometry, LandRecord, SourceReference
from naksha.models.enums import AgencyType, LandAreaUnit, LandClass, SurveyEra
from naksha.normalization.area import standardize_area
from naksha.normalization.text import normalize_identifier, normalize_text, strip_bangla_honorifics
from naksha.spatial.engine import calculate_polygon_area
from naksha.data.synthetic_spatial import DEED_CLAIM_402_COORDS, DLRS_BS_402_COORDS


def _create_record(
    record_id: str,
    agency: AgencyType,
    doc_type: str,
    source_ref_id: str,
    mouza: str,
    upazila: str,
    district: str,
    jl_no: str,
    survey_era: SurveyEra,
    raw_dag: str | None,
    raw_khatian: str | None,
    raw_owner: str | None,
    raw_area: float | None,
    area_unit: LandAreaUnit | None,
    land_class: LandClass | None,
    canonical_parcel_id: str | None = None,
    holding_no: str | None = None,
    geometry: GeoJSONGeometry | None = None,
    survey_layer_ref: str | None = None,
    is_encumbered: bool = False,
    encumbrance_details: str | None = None,
    owner_confidence: float = 1.0,
    area_confidence: float = 1.0,
    dag_confidence: float = 1.0,
    khatian_confidence: float = 1.0,
    notes: str | None = None,
) -> LandRecord:
    """Helper to construct a verified LandRecord with populated ExtractedFields."""
    norm_mouza = normalize_text(mouza)
    norm_upazila = normalize_text(upazila)
    norm_district = normalize_text(district)
    norm_jl = normalize_identifier(jl_no)

    norm_dag = normalize_identifier(raw_dag) if raw_dag else None
    norm_khatian = normalize_identifier(raw_khatian) if raw_khatian else None
    norm_holding = normalize_identifier(holding_no) if holding_no else None

    norm_owner = normalize_text(raw_owner) if raw_owner else None

    # Compute standardized area
    area_dec, area_sqm = None, None
    if raw_area is not None and area_unit is not None:
        area_dec, area_sqm = standardize_area(raw_area, area_unit)

    # Compute deterministic polygon area if geometry is attached
    calc_poly_dec, calc_poly_sqm = None, None
    if geometry is not None:
        calc_poly_dec, calc_poly_sqm = calculate_polygon_area(geometry)

    return LandRecord(
        id=record_id,
        canonical_parcel_id=canonical_parcel_id,
        source=SourceReference(
            agency=agency,
            document_type=doc_type,
            source_record_id=source_ref_id,
            issuing_office=f"{upazila} {agency.value.replace('_', ' ').title()} Office",
            issue_date="2024-05-12",
            notes=notes,
        ),
        district=ExtractedField(
            raw_value=district,
            normalized_value=norm_district,
            confidence=1.0,
        ),
        upazila=ExtractedField(
            raw_value=upazila,
            normalized_value=norm_upazila,
            confidence=1.0,
        ),
        mouza=ExtractedField(
            raw_value=mouza,
            normalized_value=norm_mouza,
            confidence=1.0,
        ),
        jl_number=ExtractedField(
            raw_value=jl_no,
            normalized_value=norm_jl,
            confidence=1.0,
        ),
        survey_era=survey_era,
        dag_number=ExtractedField(
            raw_value=raw_dag,
            normalized_value=norm_dag,
            confidence=dag_confidence,
        ) if raw_dag is not None else None,
        khatian_number=ExtractedField(
            raw_value=raw_khatian,
            normalized_value=norm_khatian,
            confidence=khatian_confidence,
        ) if raw_khatian is not None else None,
        holding_number=ExtractedField(
            raw_value=holding_no,
            normalized_value=norm_holding,
            confidence=1.0,
        ) if holding_no is not None else None,
        owner_name=ExtractedField(
            raw_value=raw_owner,
            normalized_value=norm_owner,
            confidence=owner_confidence,
        ) if raw_owner is not None else None,
        ownership_share=ExtractedField(raw_value="1.00", normalized_value=1.0, confidence=1.0),
        recorded_area=raw_area,
        recorded_unit=area_unit,
        area_in_decimals=area_dec,
        area_in_sq_meters=area_sqm,
        land_class=land_class,
        geometry=geometry,
        survey_layer_reference=survey_layer_ref,
        calculated_polygon_area_decimals=calc_poly_dec,
        calculated_polygon_area_sqm=calc_poly_sqm,
        is_encumbered=is_encumbered,
        encumbrance_details=encumbrance_details,
        is_synthetic=True,
        synthetic_disclaimer="SYNTHETIC BENCHMARK RECORD: NOT AN OFFICIAL GOVERNMENT DOCUMENT",
        created_at=datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        processed_at=datetime(2024, 6, 1, 10, 15, 0, tzinfo=timezone.utc),
    )


def generate_synthetic_records() -> List[LandRecord]:
    """Generates the required synthetic test dataset satisfying all Stage 2 criteria:

    1. Two records that appear to match (Sub-Registry deed and AC Land e-mutation).
    2. A record with conflicting Dag and Khatian identifiers (LD Tax dakhila).
    3. A record with conflicting area (DLRS surveyed polygon vs. registered deed).
    4. A duplicate/concurrent deed registration on the same plot.
    5. An incomplete historical record missing key fields and low extraction confidence.
    """
    records: List[LandRecord] = []

    # 1. Matching Record A: Sub-Registry Registered Deed
    rec_match_a = _create_record(
        record_id="SYN-MATCH-01",
        agency=AgencyType.SUB_REGISTRY,
        doc_type="Deed of Transfer (দলিল)",
        source_ref_id="DEED-2024-DH-402",
        mouza="Kashimpur",
        upazila="Gazipur Sadar",
        district="Gazipur",
        jl_no="২৮",  # JL 28 in Bangla numerals
        survey_era=SurveyEra.BS,
        raw_dag="দাগ নং ৪০২",  # Bangla prefix
        raw_khatian="খতিয়ান ১২০",
        raw_owner="মোঃ আব্দুল করিম",  # With honorific
        raw_area=6.0,
        area_unit=LandAreaUnit.DECIMAL,
        land_class=LandClass.NAL,
        canonical_parcel_id="par-8f92-bd04-syn",
        geometry=GeoJSONGeometry(type="Polygon", coordinates=DEED_CLAIM_402_COORDS),
        survey_layer_ref="DEED-CLAIM-BS402",
        notes="Clean registered sale deed.",
    )
    records.append(rec_match_a)

    # 1. Matching Record B: AC Land e-Mutation approval (matches Record A)
    rec_match_b = _create_record(
        record_id="SYN-MATCH-02",
        agency=AgencyType.AC_LAND,
        doc_type="Mutation Khatian (e-Mutation)",
        source_ref_id="MUT-2024-GZ-884",
        mouza="Kashimpur",
        upazila="Gazipur Sadar",
        district="Gazipur",
        jl_no="28",
        survey_era=SurveyEra.BS,
        raw_dag="402",
        raw_khatian="120",
        raw_owner="Md. Abdul Karim",
        raw_area=6.0,
        area_unit=LandAreaUnit.DECIMAL,
        land_class=LandClass.NAL,
        canonical_parcel_id="par-8f92-bd04-syn",
        geometry=GeoJSONGeometry(type="Polygon", coordinates=DLRS_BS_402_COORDS),
        survey_layer_ref="DLRS-SURVEY-BS402",
        notes="Mutated khatian matching Deed DEED-2024-DH-402.",
    )
    records.append(rec_match_b)

    # 2. Conflicting Identifiers: Union Land Office LD Tax receipt citing Dag 403 & Khatian 125
    rec_conflict_id = _create_record(
        record_id="SYN-CONFLICT-ID-01",
        agency=AgencyType.UNION_LAND_OFFICE,
        doc_type="LD Tax Dakhila (দাখিলা)",
        source_ref_id="TAX-2024-5541",
        mouza="Kashimpur",
        upazila="Gazipur Sadar",
        district="Gazipur",
        jl_no="28",
        survey_era=SurveyEra.BS,
        raw_dag="দাগ নং ৪০৩",  # Conflict: 403 instead of 402!
        raw_khatian="খতিয়ান ১২৫",  # Conflict: 125 instead of 120!
        raw_owner="Mohammad Abdul Karim",
        raw_area=6.0,
        area_unit=LandAreaUnit.DECIMAL,
        land_class=LandClass.VITI,  # Also has class conflict (Viti vs Nal)
        holding_no="H-5541",
        notes="Tax receipt with divergent dag/khatian numbers.",
    )
    records.append(rec_conflict_id)

    # 3. Conflicting Area: DLRS Cadastral Survey records 5.1 decimals (vs 6.0 deed decimals)
    rec_conflict_area = _create_record(
        record_id="SYN-CONFLICT-AREA-01",
        agency=AgencyType.DLRS,
        doc_type="Cadastral Plot Sheet (BS Ground Truth)",
        source_ref_id="DLRS-BS-PLOT-402",
        mouza="Kashimpur",
        upazila="Gazipur Sadar",
        district="Gazipur",
        jl_no="28",
        survey_era=SurveyEra.BS,
        raw_dag="402",
        raw_khatian="120",
        raw_owner="Abdul Karim",
        raw_area=5.10,  # Conflict: 5.10 vs 6.00 decimals (0.90 dec deficit)
        area_unit=LandAreaUnit.DECIMAL,
        land_class=LandClass.NAL,
        canonical_parcel_id="par-8f92-bd04-syn",
        geometry=GeoJSONGeometry(type="Polygon", coordinates=DLRS_BS_402_COORDS),
        survey_layer_ref="DLRS-SURVEY-BS402",
        notes="DLRS ground-truth survey polygon is 5.10 decimals; deed claims 6.00 decimals.",
    )
    records.append(rec_conflict_area)

    # 4. Duplicate Record: Second Deed entered for the same Dag 402 within 14 days
    rec_duplicate = _create_record(
        record_id="SYN-DUPLICATE-01",
        agency=AgencyType.SUB_REGISTRY,
        doc_type="Deed of Transfer (দলিল)",
        source_ref_id="DEED-2024-DH-9912",  # Duplicate sale attempt
        mouza="Kashimpur",
        upazila="Gazipur Sadar",
        district="Gazipur",
        jl_no="28",
        survey_era=SurveyEra.BS,
        raw_dag="402",
        raw_khatian="120",
        raw_owner="Tariqul Islam (Buyer)",  # Unverified subsequent buyer
        raw_area=6.0,
        area_unit=LandAreaUnit.DECIMAL,
        land_class=LandClass.NAL,
        canonical_parcel_id="par-8f92-bd04-syn",
        notes="Concurrent unmutated deed registered on the same plot; double-sale hazard.",
    )
    records.append(rec_duplicate)

    # 5. Incomplete Record: Damaged historical CS record missing identifiers
    rec_incomplete = _create_record(
        record_id="SYN-INCOMPLETE-01",
        agency=AgencyType.DLRS,
        doc_type="Damaged Historical Survey Fragment (CS)",
        source_ref_id="CS-ARCHIVE-TORN-08",
        mouza="Kashimpur",
        upazila="Gazipur Sadar",
        district="Gazipur",
        jl_no="28",
        survey_era=SurveyEra.CS,
        raw_dag=None,  # Missing plot number due to ink fade
        raw_khatian=None,  # Missing khatian
        raw_owner="...করিম...",  # Fragmented text with low extraction confidence
        raw_area=None,  # Missing area
        area_unit=None,
        land_class=None,
        owner_confidence=0.35,  # Low confidence extraction
        notes="Water-damaged CS record page with illegible dag and khatian figures.",
    )
    records.append(rec_incomplete)

    # 6. West Neighbor Record: BS Dag 401 (Paid Tax, Clean Ownership)
    rec_401 = _create_record(
        record_id="SYN-401-TAX-01",
        agency=AgencyType.UNION_LAND_OFFICE,
        doc_type="LD Tax Dakhila (দাখিলা)",
        source_ref_id="TAX-2024-KSH-401",
        mouza="Kashimpur",
        upazila="Gazipur Sadar",
        district="Gazipur",
        jl_no="28",
        survey_era=SurveyEra.BS,
        raw_dag="401",
        raw_khatian="88",
        raw_owner="মোঃ রহিম শেখ (Md. Rahim Sheikh)",
        raw_area=4.37,
        area_unit=LandAreaUnit.DECIMAL,
        land_class=LandClass.NAL,
        canonical_parcel_id="par-401-west-syn",
        holding_no="H-401",
        notes="West neighbor plot BS 401; tax paid and in order.",
    )
    records.append(rec_401)

    # 7. South Neighbor Record: BS Dag 403 (Arrears & Payer Mismatch Hazard)
    rec_403 = _create_record(
        record_id="SYN-403-TAX-01",
        agency=AgencyType.UNION_LAND_OFFICE,
        doc_type="LD Tax Assessment (কর দাবি নোটিশ)",
        source_ref_id="TAX-2024-KSH-403",
        mouza="Kashimpur",
        upazila="Gazipur Sadar",
        district="Gazipur",
        jl_no="28",
        survey_era=SurveyEra.BS,
        raw_dag="403",
        raw_khatian="125",
        raw_owner="আব্দুল মজিদ (Abdul Majid)",
        raw_area=5.53,
        area_unit=LandAreaUnit.DECIMAL,
        land_class=LandClass.NAL,
        canonical_parcel_id="par-403-south-syn",
        holding_no="H-403",
        notes="South neighbor plot BS 403; land development tax in arrears for 3 fiscal years.",
    )
    records.append(rec_403)

    return records
