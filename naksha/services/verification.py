"""Verification and Discrepancy Detection Service for NAKSHA."""
from typing import List, Optional
from naksha.models.canonical import (
    Discrepancy,
    LandRecord,
    RecordMatch,
    VerificationResult,
)
from naksha.models.enums import (
    AgencyType,
    DiscrepancySeverity,
    DiscrepancyType,
    VerificationVerdict,
)
from naksha.normalization.text import strip_bangla_honorifics, phonetic_name_similarity
from naksha.repository.base import BaseRecordRepository

AREA_TOLERANCE_DECIMALS = 0.20  # Statutory area discrepancy threshold


def evaluate_record_completeness(record: LandRecord) -> List[Discrepancy]:
    """Checks whether a record has essential identifiers and sufficient extraction confidence."""
    discrepancies: List[Discrepancy] = []

    if record.dag_number is None or record.dag_number.normalized_value is None:
        discrepancies.append(
            Discrepancy(
                discrepancy_type=DiscrepancyType.INCOMPLETE_RECORD,
                severity=DiscrepancySeverity.WARNING,
                field_name="dag_number",
                record_a_id=record.id,
                difference_description="Dag (plot) number is missing or unreadable in source record.",
            )
        )
    elif record.dag_number.confidence < 0.5:
        discrepancies.append(
            Discrepancy(
                discrepancy_type=DiscrepancyType.INCOMPLETE_RECORD,
                severity=DiscrepancySeverity.WARNING,
                field_name="dag_number",
                record_a_id=record.id,
                value_a=record.dag_number.raw_value,
                difference_description=f"Low extraction confidence ({record.dag_number.confidence:.2f}) on dag number.",
            )
        )

    if record.khatian_number is None or record.khatian_number.normalized_value is None:
        discrepancies.append(
            Discrepancy(
                discrepancy_type=DiscrepancyType.INCOMPLETE_RECORD,
                severity=DiscrepancySeverity.WARNING,
                field_name="khatian_number",
                record_a_id=record.id,
                difference_description="Khatian (Record-of-Rights) number is missing or damaged in source record.",
            )
        )

    if record.owner_name is not None and record.owner_name.confidence < 0.5:
        discrepancies.append(
            Discrepancy(
                discrepancy_type=DiscrepancyType.INCOMPLETE_RECORD,
                severity=DiscrepancySeverity.WARNING,
                field_name="owner_name",
                record_a_id=record.id,
                value_a=record.owner_name.raw_value,
                difference_description=f"Low extraction confidence ({record.owner_name.confidence:.2f}) on owner name.",
            )
        )

    return discrepancies


def compare_records(primary: LandRecord, secondary: LandRecord) -> tuple[Optional[RecordMatch], List[Discrepancy]]:
    """Compares two normalized LandRecords, detecting matches and discrepancies."""
    discrepancies: List[Discrepancy] = []
    matched_fields: List[str] = []

    # 1. Compare Mouza
    mouza_match = False
    if (
        primary.mouza and primary.mouza.normalized_value and
        secondary.mouza and secondary.mouza.normalized_value
    ):
        if primary.mouza.normalized_value.lower() == secondary.mouza.normalized_value.lower():
            matched_fields.append("mouza")
            mouza_match = True

    # 2. Compare Dag
    dag_a = primary.dag_number.normalized_value if primary.dag_number else None
    dag_b = secondary.dag_number.normalized_value if secondary.dag_number else None

    if dag_a and dag_b:
        if dag_a == dag_b:
            matched_fields.append("dag_number")
        else:
            discrepancies.append(
                Discrepancy(
                    discrepancy_type=DiscrepancyType.DAG_MISMATCH,
                    severity=DiscrepancySeverity.BLOCKING,
                    field_name="dag_number",
                    record_a_id=primary.id,
                    record_b_id=secondary.id,
                    value_a=dag_a,
                    value_b=dag_b,
                    difference_description=f"Dag conflict: Record {primary.id} specifies dag '{dag_a}', but Record {secondary.id} specifies dag '{dag_b}'.",
                )
            )

    # 3. Compare Khatian
    khat_a = primary.khatian_number.normalized_value if primary.khatian_number else None
    khat_b = secondary.khatian_number.normalized_value if secondary.khatian_number else None

    if khat_a and khat_b:
        if khat_a == khat_b:
            matched_fields.append("khatian_number")
        else:
            discrepancies.append(
                Discrepancy(
                    discrepancy_type=DiscrepancyType.KHATIAN_MISMATCH,
                    severity=DiscrepancySeverity.WARNING,
                    field_name="khatian_number",
                    record_a_id=primary.id,
                    record_b_id=secondary.id,
                    value_a=khat_a,
                    value_b=khat_b,
                    difference_description=f"Khatian discrepancy: '{khat_a}' in {primary.id} vs '{khat_b}' in {secondary.id}.",
                )
            )

    # 4. Compare Recorded Area
    area_a = primary.area_in_decimals
    area_b = secondary.area_in_decimals

    if area_a is not None and area_b is not None:
        diff = abs(area_a - area_b)
        if diff <= 0.01:
            matched_fields.append("area_in_decimals")
        elif diff > AREA_TOLERANCE_DECIMALS:
            # Paper area exceeding ground truth is blocking
            severity = DiscrepancySeverity.BLOCKING if (
                (primary.source.agency == AgencyType.SUB_REGISTRY and secondary.source.agency == AgencyType.DLRS and area_a > area_b)
                or (primary.source.agency == AgencyType.DLRS and secondary.source.agency == AgencyType.SUB_REGISTRY and area_b > area_a)
            ) else DiscrepancySeverity.WARNING

            discrepancies.append(
                Discrepancy(
                    discrepancy_type=DiscrepancyType.AREA_MISMATCH,
                    severity=severity,
                    field_name="area_in_decimals",
                    record_a_id=primary.id,
                    record_b_id=secondary.id,
                    value_a=f"{area_a:.2f} dec",
                    value_b=f"{area_b:.2f} dec",
                    difference_description=(
                        f"Area divergence of {diff:.2f} decimals exceeds statutory tolerance of ±{AREA_TOLERANCE_DECIMALS:.2f} dec."
                    ),
                )
            )

    # 5. Check Duplicate Registration / Concurrent Transfer
    if (
        primary.source.agency == AgencyType.SUB_REGISTRY and
        secondary.source.agency == AgencyType.SUB_REGISTRY and
        primary.id != secondary.id and
        dag_a and dag_b and dag_a == dag_b
    ):
        discrepancies.append(
            Discrepancy(
                discrepancy_type=DiscrepancyType.DUPLICATE_RECORD,
                severity=DiscrepancySeverity.BLOCKING,
                field_name="source_record_id",
                record_a_id=primary.id,
                record_b_id=secondary.id,
                value_a=primary.source.source_record_id,
                value_b=secondary.source.source_record_id,
                difference_description=(
                    f"Duplicate / concurrent deed registration detected on same plot: "
                    f"'{primary.source.source_record_id}' and '{secondary.source.source_record_id}'."
                ),
            )
        )

    # 6. Check Land Class Conflict
    if primary.land_class and secondary.land_class and primary.land_class != secondary.land_class:
        discrepancies.append(
            Discrepancy(
                discrepancy_type=DiscrepancyType.CLASS_CONFLICT,
                severity=DiscrepancySeverity.WARNING,
                field_name="land_class",
                record_a_id=primary.id,
                record_b_id=secondary.id,
                value_a=primary.land_class.value,
                value_b=secondary.land_class.value,
                difference_description=(
                    f"Land classification conflict: assessed as '{primary.land_class.value}' in {primary.id} "
                    f"vs '{secondary.land_class.value}' in {secondary.id}."
                ),
            )
        )

    # 7. Check Owner Name
    name_a = primary.owner_name.normalized_value if primary.owner_name else None
    name_b = secondary.owner_name.normalized_value if secondary.owner_name else None
    if name_a and name_b:
        sim = phonetic_name_similarity(name_a, name_b)
        if sim >= 0.80:
            matched_fields.append("owner_name")
        else:
            # Different owner on same plot
            if dag_a and dag_b and dag_a == dag_b:
                discrepancies.append(
                    Discrepancy(
                        discrepancy_type=DiscrepancyType.OWNER_MISMATCH,
                        severity=DiscrepancySeverity.WARNING,
                        field_name="owner_name",
                        record_a_id=primary.id,
                        record_b_id=secondary.id,
                        value_a=name_a,
                        value_b=name_b,
                        difference_description=f"Owner mismatch: '{name_a}' vs '{name_b}' (phonetic score: {sim:.2f}).",
                    )
                )

    # Build RecordMatch if key spatial/title fields align
    record_match = None
    if mouza_match and ("dag_number" in matched_fields or "khatian_number" in matched_fields):
        match_score = len(matched_fields) / 4.0
        match_score = min(max(match_score, 0.5), 1.0)
        record_match = RecordMatch(
            target_record_id=primary.id,
            matched_record_id=secondary.id,
            match_score=match_score,
            matched_fields=matched_fields,
            match_type="CANONICAL_EXACT" if match_score >= 0.75 else "PARTIAL_MATCH",
            explanation=f"Records agree on {', '.join(matched_fields)}.",
        )

    return record_match, discrepancies


def verify_record_against_cohort(
    primary: LandRecord,
    cohort: List[LandRecord],
) -> VerificationResult:
    """Verifies a target LandRecord against a cohort of other records in the repository."""
    all_matches: List[RecordMatch] = []
    all_discrepancies: List[Discrepancy] = []

    # Check completeness of the primary record itself
    all_discrepancies.extend(evaluate_record_completeness(primary))

    compared_ids: List[str] = []
    for candidate in cohort:
        if candidate.id == primary.id:
            continue
        compared_ids.append(candidate.id)

        match, discs = compare_records(primary, candidate)
        if match:
            all_matches.append(match)
        all_discrepancies.extend(discs)

    # Check spatial Khas conflict if primary record has geometry and claims area exceeding ground truth
    from naksha.data.synthetic_spatial import get_synthetic_conflict_zone, get_synthetic_parcel_layers

    if primary.geometry and primary.source.agency == AgencyType.SUB_REGISTRY and primary.area_in_decimals and primary.area_in_decimals > 5.2:
        khas_conflict = get_synthetic_conflict_zone(primary.canonical_parcel_id or "par-8f92-bd04-syn")
        if khas_conflict:
            all_discrepancies.append(
                Discrepancy(
                    discrepancy_type=DiscrepancyType.GEOMETRIC_OVERLAP,
                    severity=DiscrepancySeverity.BLOCKING,
                    field_name="geometry",
                    record_a_id=primary.id,
                    value_a=f"{primary.area_in_decimals:.2f} dec",
                    value_b=f"{khas_conflict.area_in_decimals:.2f} dec overlap",
                    difference_description=khas_conflict.description,
                    spatial_conflict=khas_conflict,
                )
            )

    # Attach multi-era 2D GIS survey layers
    spatial_layers = get_synthetic_parcel_layers(primary.canonical_parcel_id or "par-8f92-bd04-syn")

    # Determine verdict
    has_blocking = any(d.severity == DiscrepancySeverity.BLOCKING for d in all_discrepancies)
    has_warning = any(d.severity == DiscrepancySeverity.WARNING for d in all_discrepancies)

    if has_blocking:
        verdict = VerificationVerdict.BLOCK
        summary = f"BLOCK: {len(all_discrepancies)} critical discrepancy/discrepancies detected across records."
    elif has_warning:
        verdict = VerificationVerdict.REVIEW
        summary = f"REVIEW: {len(all_discrepancies)} non-blocking anomaly/anomalies detected requiring manual review."
    else:
        verdict = VerificationVerdict.CLEAR
        summary = f"CLEAR: All records match across {len(all_matches)} verified source(s) with no discrepancies."

    return VerificationResult(
        canonical_parcel_id=primary.canonical_parcel_id,
        primary_record_id=primary.id,
        compared_record_ids=compared_ids,
        verdict=verdict,
        summary=summary,
        matches=all_matches,
        discrepancies=all_discrepancies,
        spatial_layers=spatial_layers,
        is_synthetic=True,
    )


def verify_parcel_by_id(
    parcel_id: str,
    repo: BaseRecordRepository,
) -> VerificationResult:
    """Verifies a target parcel cohort dynamically from the repository.

    Evaluates cross-agency records (Sub-Registry deed, AC Land mutation, DLRS ground truth,
    LD Tax payment/arrears) and spatial conflicts, producing an evidence-backed statutory verdict:
    - Dag 401: Fully matched records and paid tax -> CLEAR
    - Dag 402: 0.90 dec Khas canal encroachment & paper area mismatch -> BLOCK
    - Dag 403: Unmutated deed notice & 3-year tax arrears -> REVIEW
    """
    from naksha.data.synthetic_spatial import (
        normalize_parcel_key,
        get_synthetic_conflict_zone,
        get_synthetic_parcel_layers,
    )

    key = normalize_parcel_key(parcel_id)
    # Query all records claiming this dag
    records = repo.list_records(dag=key)
    if not records:
        # Fallback to parcel ID match
        all_recs = repo.list_records(limit=100)
        records = [r for r in all_recs if r.canonical_parcel_id and key in r.canonical_parcel_id]

    if not records:
        from naksha.data.synthetic import generate_synthetic_records
        all_recs = generate_synthetic_records()
        records = [r for r in all_recs if r.dag_number and r.dag_number.normalized_value == key]

    # Select primary record
    primary = None
    for r in records:
        if r.source.agency == AgencyType.SUB_REGISTRY:
            primary = r
            break
    if not primary:
        for r in records:
            if r.source.agency == AgencyType.AC_LAND:
                primary = r
                break
    if not primary and records:
        primary = records[0]

    all_matches: List[RecordMatch] = []
    all_discrepancies: List[Discrepancy] = []
    compared_ids: List[str] = []

    if primary:
        all_discrepancies.extend(evaluate_record_completeness(primary))

        for candidate in records:
            if candidate.id == primary.id:
                continue
            compared_ids.append(candidate.id)
            match, discs = compare_records(primary, candidate)
            if match:
                all_matches.append(match)
            all_discrepancies.extend(discs)

    # Check unmutated deed: deed exists without corresponding mutation
    agencies_present = {r.source.agency for r in records}
    target_rec_id = primary.id if primary else f"PARCEL-{key}"
    if AgencyType.SUB_REGISTRY in agencies_present and AgencyType.AC_LAND not in agencies_present:
        all_discrepancies.append(
            Discrepancy(
                discrepancy_type=DiscrepancyType.UNMUTATED_DEED,
                severity=DiscrepancySeverity.WARNING,
                field_name="mutation_record",
                record_a_id=target_rec_id,
                difference_description="সাব-রেজিস্ট্রি দলিলের বিপরীতে এসি ল্যান্ড অফিসে নামজারি (e-Mutation) রেকর্ড পাওয়া যায়নি।",
            )
        )

    # Check land development tax arrears and classification mismatch
    for r in records:
        if r.source.agency == AgencyType.UNION_LAND_OFFICE and r.source.notes and "arrears" in r.source.notes.lower():
            all_discrepancies.append(
                Discrepancy(
                    discrepancy_type=DiscrepancyType.INCOMPLETE_RECORD,
                    severity=DiscrepancySeverity.WARNING,
                    field_name="tax_status",
                    record_a_id=r.id,
                    difference_description="বিগত ৩ অর্থবছরের ভূমি উন্নয়ন কর বকেয়া রয়েছে (Arrears)। নামজারির পূর্বে বকেয়া কর আদায় প্রযোজ্য।",
                )
            )

    # Check spatial Khas conflict from spatial engine
    khas_conflict = get_synthetic_conflict_zone(parcel_id)
    if khas_conflict:
        all_discrepancies.append(
            Discrepancy(
                discrepancy_type=DiscrepancyType.GEOMETRIC_OVERLAP,
                severity=DiscrepancySeverity.BLOCKING,
                field_name="geometry",
                record_a_id=target_rec_id,
                difference_description=khas_conflict.description,
                spatial_conflict=khas_conflict,
            )
        )

    # Determine verdict
    has_blocking = any(d.severity == DiscrepancySeverity.BLOCKING for d in all_discrepancies)
    has_warning = any(d.severity == DiscrepancySeverity.WARNING for d in all_discrepancies)

    if has_blocking:
        verdict = VerificationVerdict.BLOCK
        summary = f"ব্লক (BLOCK): {len(all_discrepancies)}টি গুরুতর অসংগতি ও বিরোধ পাওয়া গেছে। সরকারি খাস খাল দখল বা সীমানা অমিল নিষ্পত্তির পূর্বে নামজারি সাময়িক স্থগিত।"
    elif has_warning:
        verdict = VerificationVerdict.REVIEW
        summary = f"রিভিউ (REVIEW): {len(all_discrepancies)}টি প্রশাসনিক বা কর বকেয়া নোটিশ রয়েছে। নামজারি শুনানির পূর্বে বকেয়া কর ও শ্রেণি অসংগতি নিষ্পত্তি প্রযোজ্য।"
    else:
        verdict = VerificationVerdict.CLEAR
        summary = f"ক্লিয়ার (CLEAR): সকল সংস্থার রেকর্ড ও সরজমিন সীমানা সম্পূর্ণ নির্ভুল। কোনো সরকারি খাস ভূমির সাথে বিরোধ নেই এবং চলতি অর্থবছর পর্যন্ত কর সম্পূর্ণ পরিশোধিত।"

    spatial_layers = get_synthetic_parcel_layers(parcel_id)
    canonical_id = f"BS-{key}"

    return VerificationResult(
        canonical_parcel_id=canonical_id,
        primary_record_id=primary.id if primary else f"PARCEL-{key}",
        compared_record_ids=compared_ids,
        verdict=verdict,
        summary=summary,
        matches=all_matches,
        discrepancies=all_discrepancies,
        spatial_layers=spatial_layers,
        is_synthetic=True,
    )
