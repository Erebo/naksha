"""API Route Definitions for NAKSHA Canonical & Spatial Engine."""
from typing import Optional, List, Dict, Any
import threading
import time
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from naksha.core.config import settings
from naksha.models.canonical import (
    LandRecord,
    VerificationResult,
    GeoJSONGeometry,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    SpatialConflictZone,
    SurveyLayerSnapshot,
)
from naksha.models.enums import AgencyType
from naksha.repository.base import BaseRecordRepository
from naksha.repository.memory import InMemoryRecordRepository
from naksha.data.synthetic import generate_synthetic_records
from naksha.data.synthetic_spatial import (
    get_synthetic_parcel_layers,
    get_synthetic_neighbor_parcels,
    get_synthetic_all_parcels_geojson,
    get_synthetic_conflict_zone,
    normalize_parcel_key,
)
from naksha.services.verification import verify_record_against_cohort
from naksha.services.ledger import audit_ledger, LedgerEntry
from naksha.spatial.engine import (
    calculate_polygon_area,
    calculate_overlap,
    validate_geometry,
)
from naksha.models.auth import OfficerContext, OfficerRole
from naksha.core.auth import get_current_officer, require_role, create_officer_token
from naksha.core.policy import check_jurisdiction_permission

router = APIRouter()

from naksha.database.repository import SQLAlchemyRecordRepository
from naksha.database.init_db import init_database

# Ensure database tables and seed data exist
try:
    init_database()
    _persistent_repo = SQLAlchemyRecordRepository()
except Exception as e:
    print(f"[NAKSHA API] Persistent database fallback notice: {e}")
    _persistent_repo = InMemoryRecordRepository(initial_records=generate_synthetic_records())


def get_repository() -> BaseRecordRepository:
    """Dependency provider for the repository layer."""
    return _persistent_repo


# ==============================================================================
# Request / Response Schemas
# ==============================================================================

class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "naksha-api"
    version: str = "0.2.0"
    spatial_engine_ready: bool = True
    synthetic_mode: bool = True


class RecordListResponse(BaseModel):
    total: int = Field(description="Total number of records matching query.")
    limit: int = Field(description="Page size limit.")
    offset: int = Field(description="Pagination offset.")
    records: List[LandRecord] = Field(description="List of canonical LandRecords.")
    is_synthetic: bool = True


class DemoResponse(BaseModel):
    description: str
    benchmark_scenarios: List[str]
    verification_results: List[VerificationResult]
    is_synthetic: bool = True
    notice: str


class AreaCalculationRequest(BaseModel):
    geometry: GeoJSONGeometry = Field(description="WGS 84 (EPSG:4326) Polygon GeoJSON")


class AreaCalculationResponse(BaseModel):
    area_in_decimals: float = Field(description="Calculated area in standard Bangladesh decimals (শতক).")
    area_in_sq_meters: float = Field(description="Calculated area in metric square meters.")
    is_valid: bool = True
    notice: str = "CALCULATED IN UTM ZONE 46N (EPSG:32646)"


class OverlapCalculationRequest(BaseModel):
    geometry_a: GeoJSONGeometry = Field(description="Primary Polygon GeoJSON")
    geometry_b: GeoJSONGeometry = Field(description="Secondary Polygon GeoJSON")


class OverlapCalculationResponse(BaseModel):
    overlap_in_decimals: float = Field(description="Area of intersection in decimals.")
    overlap_in_sq_meters: float = Field(description="Area of intersection in metric square meters.")
    intersection_geometry: Optional[GeoJSONGeometry] = Field(
        default=None,
        description="GeoJSON geometry of the intersection polygon.",
    )
    has_overlap: bool


# ==============================================================================
# System & Record Endpoints
# ==============================================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health and Readiness Check",
    tags=["System"],
)
def get_health() -> HealthResponse:
    """Returns the operational status of the NAKSHA canonical API and Spatial Engine."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        spatial_engine_ready=True,
        synthetic_mode=settings.synthetic_mode,
    )


@router.get(
    f"{settings.api_prefix}/records",
    response_model=RecordListResponse,
    summary="List and Filter Land Records",
    tags=["Land Records"],
)
def list_records(
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Offset index for pagination"),
    agency: Optional[AgencyType] = Query(default=None, description="Filter by originating agency"),
    mouza: Optional[str] = Query(default=None, description="Filter by mouza name"),
    dag: Optional[str] = Query(default=None, description="Filter by dag / plot number"),
    repo: BaseRecordRepository = Depends(get_repository),
    officer: OfficerContext = Depends(require_role("records")),
) -> RecordListResponse:
    """Retrieves normalized canonical land records with optional agency, mouza, or dag filters."""
    if mouza and not check_jurisdiction_permission(officer, mouza):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Officer jurisdiction '{officer.jurisdiction}' does not permit access to mouza '{mouza}'.",
        )
    total_count = repo.count()
    records = repo.list_records(
        limit=limit,
        offset=offset,
        agency=agency,
        mouza=mouza,
        dag=dag,
    )
    return RecordListResponse(
        total=total_count,
        limit=limit,
        offset=offset,
        records=records,
        is_synthetic=True,
    )


@router.get(
    f"{settings.api_prefix}/records/demo",
    response_model=DemoResponse,
    summary="Demonstration of Cross-Agency Record Reconciliation",
    tags=["Demonstration"],
)
def get_demo_reconciliation(
    repo: BaseRecordRepository = Depends(get_repository),
    officer: OfficerContext = Depends(require_role("records")),
) -> DemoResponse:
    """Executes reconciliation across the synthetic benchmark cohort, demonstrating:

    1. Matching records (Sub-Registry deed vs. AC Land e-Mutation).
    2. Conflicting identifiers (Tax dakhila citing Dag 403 vs 402).
    3. Conflicting area (Deed 6.0 dec vs. DLRS 5.1 dec polygon).
    4. Duplicate deed registration on the same plot.
    5. Incomplete damaged historical CS record.
    """
    all_records = repo.list_records(limit=100)
    primary_records = [
        r for r in all_records
        if r.id in ("SYN-MATCH-01", "SYN-CONFLICT-ID-01", "SYN-CONFLICT-AREA-01", "SYN-DUPLICATE-01", "SYN-INCOMPLETE-01")
    ]

    results: List[VerificationResult] = []
    for prim in primary_records:
        res = verify_record_against_cohort(primary=prim, cohort=all_records)
        results.append(res)

    return DemoResponse(
        description="NAKSHA Canonical Land Data Model Reconciliation Demo (Stage 2 + Spatial Engine)",
        benchmark_scenarios=[
            "Scenario 1: Matching Records (Sub-Registry Deed & AC Land Mutation) -> CLEAR",
            "Scenario 2: Identifier Conflict (Tax Receipt citing Dag 403 vs Dag 402) -> BLOCK",
            "Scenario 3: Area Discrepancy (Deed 6.0 dec vs DLRS 5.1 dec polygon) -> BLOCK",
            "Scenario 4: Duplicate Concurrent Deed on Same Plot -> BLOCK",
            "Scenario 5: Damaged / Incomplete Historical CS Record -> REVIEW",
        ],
        verification_results=results,
        is_synthetic=True,
        notice="ALL BENCHMARK RECORDS ARE SYNTHETIC. NO LIVE GOVERNMENT OR PRIVATE DATA IS USED.",
    )


@router.get(
    f"{settings.api_prefix}/records/{{record_id}}",
    response_model=LandRecord,
    summary="Get Single Land Record by ID",
    tags=["Land Records"],
)
def get_record_by_id(
    record_id: str,
    repo: BaseRecordRepository = Depends(get_repository),
    officer: OfficerContext = Depends(require_role("records")),
) -> LandRecord:
    """Fetches a specific normalized canonical LandRecord by its unique ID."""
    record = repo.get_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Land record '{record_id}' not found.",
        )
    mouza = record.mouza.normalized_value if record.mouza else "Unknown"
    if not check_jurisdiction_permission(officer, mouza):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Officer jurisdiction '{officer.jurisdiction}' does not permit access to mouza '{mouza}'.",
        )
    return record


@router.get(
    f"{settings.api_prefix}/records/{{record_id}}/verify",
    response_model=VerificationResult,
    summary="Verify Single Record Against Entire Repository Cohort",
    tags=["Verification Engine"],
)
def verify_single_record(
    record_id: str,
    repo: BaseRecordRepository = Depends(get_repository),
    officer: OfficerContext = Depends(require_role("records")),
) -> VerificationResult:
    """Performs deterministic cross-agency verification of a target record against the cohort,
    sealing the finding into the Ed25519-signed SHA-256 Trust Ledger.
    """
    record = repo.get_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Land record '{record_id}' not found.",
        )
    mouza = record.mouza.normalized_value if record.mouza else "Unknown"
    if not check_jurisdiction_permission(officer, mouza):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Officer jurisdiction '{officer.jurisdiction}' does not permit access to mouza '{mouza}'.",
        )
    cohort = repo.list_records(limit=100)
    result = verify_record_against_cohort(primary=record, cohort=cohort)

    # Record into cryptographic Trust Ledger
    audit_ledger.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id=result.canonical_parcel_id,
        dag_number=record.dag_number.normalized_value if record.dag_number else None,
        mouza=mouza,
        verdict=result.verdict.value,
        cited_records=result.compared_record_ids,
        officer_id=officer.officer_id,
    )
    return result


@router.get(
    f"{settings.api_prefix}/ledger",
    response_model=List[LedgerEntry],
    summary="Get Append-Only Cryptographic Trust Ledger Entries",
    tags=["Trust Ledger"],
)
def get_ledger_entries(
    limit: int = Query(default=20, ge=1, le=100),
    officer: OfficerContext = Depends(require_role("ledger")),
) -> List[LedgerEntry]:
    """Retrieves recent signed audit entries from the append-only SHA-256 hash-chain."""
    return audit_ledger.get_entries(limit=limit)


@router.get(
    f"{settings.api_prefix}/ledger/verify",
    summary="Verify Cryptographic Integrity of Trust Ledger Chain",
    tags=["Trust Ledger"],
)
def verify_ledger_chain(
    officer: OfficerContext = Depends(require_role("ledger")),
) -> Dict[str, Any]:
    """Verifies that all blocks in the ledger hash chain are intact and signed by Ed25519."""
    is_valid, reason = audit_ledger.verify_integrity()
    return {
        "is_valid": is_valid,
        "total_blocks": len(audit_ledger._chain),
        "latest_block_hash": audit_ledger.latest_entry.entry_hash,
        "reason": reason,
        "algorithm": "SHA-256 Hash Chain + Ed25519 Digital Signatures",
    }


# ==============================================================================
# 2D GIS & Spatial Engine Endpoints
# ==============================================================================

@router.get(
    f"{settings.api_prefix}/spatial/parcels",
    response_model=GeoJSONFeatureCollection,
    summary="Get All Parcel Boundaries in GeoJSON",
    tags=["Spatial Engine"],
)
def get_all_parcels_geojson(
    officer: OfficerContext = Depends(require_role("spatial")),
) -> GeoJSONFeatureCollection:
    """Returns a GeoJSON FeatureCollection containing all cadastral parcel geometries

    with Dag, Khatian, area, and LD Tax payment status attributes.
    """
    return get_synthetic_all_parcels_geojson()


@router.get(
    f"{settings.api_prefix}/spatial/parcels/{{parcel_id}}/layers",
    response_model=List[SurveyLayerSnapshot],
    summary="Get 4-Layer Multi-Era 2D GIS Stack for Side Panel",
    tags=["Spatial Engine"],
)
def get_parcel_survey_layers(
    parcel_id: str,
    officer: OfficerContext = Depends(require_role("spatial")),
) -> List[SurveyLayerSnapshot]:
    """Returns the multi-era survey visual layer stack for the interactive 2D GIS side panel:

    - Layer 1: Ancestral CS Dag 88 footprint (historical root)
    - Layer 2: Deed claim boundary (6.0 dec claim)
    - Layer 3: DLRS surveyed ground truth (5.1 dec polygon)
    - Layer 4: Computed conflict zone (0.9 dec Khas canal overlap)
    - Layer 5: Public Khas canal boundary
    """
    key = normalize_parcel_key(parcel_id)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No survey layers found for parcel '{parcel_id}'.",
        )
    mouza = "কাশিমপুর"
    if not check_jurisdiction_permission(officer, mouza):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Officer jurisdiction '{officer.jurisdiction}' does not permit access to mouza '{mouza}'.",
        )
    layers = get_synthetic_parcel_layers(parcel_id)
    if not layers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No survey layers found for parcel '{parcel_id}'.",
        )
    return layers


@router.get(
    f"{settings.api_prefix}/spatial/parcels/{{parcel_id}}/neighbors",
    response_model=GeoJSONFeatureCollection,
    summary="Get Neighboring Plots and Tax Status for Tax Map",
    tags=["Spatial Engine"],
)
def get_parcel_neighbors(
    parcel_id: str,
    officer: OfficerContext = Depends(require_role("spatial")),
) -> GeoJSONFeatureCollection:
    """Returns the target parcel and adjacent plots with LD Tax payment statuses

    (paid, arrears, payer mismatch) for rendering the Tax Map in the side panel.
    """
    key = normalize_parcel_key(parcel_id)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel '{parcel_id}' not found.",
        )
    mouza = "কাশিমপুর"
    if not check_jurisdiction_permission(officer, mouza):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Officer jurisdiction '{officer.jurisdiction}' does not permit access to mouza '{mouza}'.",
        )
    return get_synthetic_neighbor_parcels(parcel_id)


@router.get(
    f"{settings.api_prefix}/spatial/parcels/{{parcel_id}}/conflicts",
    response_model=Optional[SpatialConflictZone],
    summary="Get Computed Spatial Conflict Zone",
    tags=["Spatial Engine"],
)
def get_parcel_conflict_zone(
    parcel_id: str,
    officer: OfficerContext = Depends(require_role("spatial")),
) -> Optional[SpatialConflictZone]:
    """Returns geometric details of any public Khas encroachment or boundary conflict."""
    key = normalize_parcel_key(parcel_id)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No spatial conflict detected on parcel '{parcel_id}'.",
        )
    mouza = "কাশিমপুর"
    if not check_jurisdiction_permission(officer, mouza):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Officer jurisdiction '{officer.jurisdiction}' does not permit access to mouza '{mouza}'.",
        )
    conflict = get_synthetic_conflict_zone(parcel_id)
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No spatial conflict detected on parcel '{parcel_id}'.",
        )
    return conflict


@router.get(
    f"{settings.api_prefix}/spatial/parcels/{{parcel_id}}/verification",
    response_model=VerificationResult,
    summary="Get Dynamic Cross-Agency Verification for Parcel",
    tags=["Spatial Engine", "Verification Engine"],
)
def get_parcel_verification(
    parcel_id: str,
    repo: BaseRecordRepository = Depends(get_repository),
    officer: OfficerContext = Depends(require_role("spatial")),
) -> VerificationResult:
    """Performs dynamic cross-agency record verification for the target parcel cohort,
    sealing the verdict and cited records into the append-only SHA-256 + Ed25519 Trust Ledger.
    """
    from naksha.services.verification import verify_parcel_by_id

    key = normalize_parcel_key(parcel_id)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parcel '{parcel_id}' not found.",
        )

    mouza = "কাশিমপুর"
    if repo:
        recs = repo.list_records(dag=key)
        for r in recs:
            if r.mouza and r.mouza.normalized_value:
                mouza = r.mouza.normalized_value
                break

    if not check_jurisdiction_permission(officer, mouza):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Officer jurisdiction '{officer.jurisdiction}' does not permit access to mouza '{mouza}'.",
        )

    result = verify_parcel_by_id(parcel_id, repo)

    # Record into cryptographic Trust Ledger
    audit_ledger.record_verification(
        event_type="VERIFICATION_VERDICT",
        canonical_parcel_id=result.canonical_parcel_id,
        dag_number=key,
        mouza=mouza,
        verdict=result.verdict.value,
        cited_records=result.compared_record_ids,
        officer_id=officer.officer_id,
    )
    return result


@router.post(
    f"{settings.api_prefix}/spatial/calculate-area",
    response_model=AreaCalculationResponse,
    summary="Calculate Deterministic Metric Area in UTM 46N",
    tags=["Spatial Engine"],
)
def api_calculate_area(
    req: AreaCalculationRequest,
    officer: OfficerContext = Depends(get_current_officer),
) -> AreaCalculationResponse:
    """Calculates ground area deterministically in metric square meters (UTM 46N)

    and converts to standard Bangladesh decimals (শতক).
    """
    try:
        dec, sqm = calculate_polygon_area(req.geometry)
        return AreaCalculationResponse(
            area_in_decimals=dec,
            area_in_sq_meters=sqm,
            is_valid=True,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post(
    f"{settings.api_prefix}/spatial/calculate-overlap",
    response_model=OverlapCalculationResponse,
    summary="Calculate Spatial Overlap & Conflict Polygon",
    tags=["Spatial Engine"],
)
def api_calculate_overlap(
    req: OverlapCalculationRequest,
    officer: OfficerContext = Depends(get_current_officer),
) -> OverlapCalculationResponse:
    """Computes geometric intersection between two polygons in UTM 46N."""
    try:
        ov_dec, ov_sqm, inter_geom = calculate_overlap(req.geometry_a, req.geometry_b)
        return OverlapCalculationResponse(
            overlap_in_decimals=ov_dec,
            overlap_in_sq_meters=ov_sqm,
            intersection_geometry=inter_geom,
            has_overlap=(ov_dec > 0.0),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


# ==============================================================================
# Officer Verification & Session Security
# ==============================================================================

class VerifyOfficerRequest(BaseModel):
    portal_origin: Optional[str] = Field(default="", description="Origin or URL of calling government portal")
    officer_id: str = Field(description="Synthetic officer identifier, e.g. UL-2024-KSH")
    name: Optional[str] = Field(default=None, description="Officer display name")
    designation: Optional[str] = Field(default=None, description="Official job title")
    office: Optional[str] = Field(default=None, description="Jurisdiction or office location")


class VerifyOfficerResponse(BaseModel):
    status: str = Field(description="'verified' or 'denied'")
    token: Optional[str] = Field(default=None, description="15-minute HS256 signed JWT session token")
    officer: Optional[Dict[str, Any]] = Field(default=None, description="Verified officer profile")
    reason: Optional[str] = Field(default=None, description="Denial reason if verification failed")


SEEDED_OFFICER_REGISTRY: Dict[str, Dict[str, Any]] = {
    "UL-2024-KSH": {
        "officer_id": "UL-2024-KSH",
        "name": "মোঃ ফজলুর রহমান",
        "designation": "ইউনিয়ন ভূমি সহকারী কর্মকর্তা",
        "office": "কাশিমপুর, গাজীপুর সদর",
        "role": "union_land_officer",
        "jurisdiction": "কাশিমপুর",
        "trusted": True,
    },
    "AC-2024-GZP": {
        "officer_id": "AC-2024-GZP",
        "name": "তানিয়া সুলতানা",
        "designation": "সহকারী কমিশনার (ভূমি)",
        "office": "গাজীপুর সদর",
        "role": "ac_land",
        "jurisdiction": "গাজীপুর সদর",
        "trusted": True,
    },
    "KN-2024-KSH": {
        "officer_id": "KN-2024-KSH",
        "name": "মোঃ রফিকুল ইসলাম",
        "designation": "কানুনগো",
        "office": "কাশিমপুর, গাজীপুর সদর",
        "role": "kanungo",
        "jurisdiction": "কাশিমপুর",
        "trusted": True,
    },
    "ACL-GZ-04": {
        "officer_id": "ACL-GZ-04",
        "name": "তানিয়া সুলতানা",
        "designation": "সহকারী কমিশনার (ভূমি)",
        "office": "সদর উপজেলা, গাজীপুর",
        "role": "ac_land",
        "jurisdiction": "গাজীপুর সদর",
        "trusted": True,
    },
}

_rate_limit_lock = threading.Lock()
_ip_request_timestamps: Dict[str, List[float]] = {}


def reset_auth_rate_limits() -> None:
    """Helper to clear rate limit timestamps (used for test isolation)."""
    with _rate_limit_lock:
        _ip_request_timestamps.clear()


@router.post(
    "/auth/verify-officer",
    response_model=VerifyOfficerResponse,
    summary="Verify Officer Portal Session and Issue 15-Minute Token",
    tags=["Authentication & Security"],
)
@router.post(
    f"{settings.api_prefix}/auth/verify-officer",
    response_model=VerifyOfficerResponse,
    summary="Verify Officer Portal Session and Issue 15-Minute Token (Prefixed)",
    tags=["Authentication & Security"],
)
def verify_officer_session(req: VerifyOfficerRequest, request: Request) -> VerifyOfficerResponse:
    """Verifies that the officer is currently logged into an approved government portal
    and matches our authorized officer registry. Emits ACCESS_GRANTED or ACCESS_DENIED
    audit ledger events.
    """
    # 0. In-memory sliding-window rate limit per client IP
    client_ip = "unknown"
    if request.client and request.client.host:
        client_ip = request.client.host

    now = time.time()
    with _rate_limit_lock:
        timestamps = _ip_request_timestamps.setdefault(client_ip, [])
        window_start = now - settings.auth_rate_limit_window_seconds
        _ip_request_timestamps[client_ip] = [t for t in timestamps if t > window_start]
        if len(_ip_request_timestamps[client_ip]) >= settings.auth_rate_limit_max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many authentication requests. Please try again later.",
            )
        _ip_request_timestamps[client_ip].append(now)

    # 1. Verify exact-match origin allowlist (empty or missing origin is denied)
    if not req.portal_origin or req.portal_origin.strip() not in settings.allowed_origins:
        audit_ledger.record_verification(
            event_type="ACCESS_DENIED",
            canonical_parcel_id=None,
            dag_number=None,
            mouza=req.office or "Unknown",
            verdict="DENIED",
            cited_records=["DISALLOWED_ORIGIN"],
            officer_id=req.officer_id or "UNKNOWN",
        )
        return VerifyOfficerResponse(
            status="denied",
            reason="অননুমোদিত পোর্টাল উৎস (Disallowed portal origin)",
        )

    # 2. Match against seeded registry
    officer_profile = SEEDED_OFFICER_REGISTRY.get(req.officer_id)
    if not officer_profile or not officer_profile.get("trusted", False):
        audit_ledger.record_verification(
            event_type="ACCESS_DENIED",
            canonical_parcel_id=None,
            dag_number=None,
            mouza=req.office or "Unknown",
            verdict="DENIED",
            cited_records=["UNKNOWN_OFFICER"],
            officer_id=req.officer_id or "UNKNOWN",
        )
        return VerifyOfficerResponse(
            status="denied",
            reason="কর্মকর্তার পরিচয় নিবন্ধনে পাওয়া যায়নি বা অননুমোদিত (Officer not found or unauthorized)",
        )

    # 3. Match officer name and designation
    if not req.name or req.name.strip() != officer_profile.get("name"):
        audit_ledger.record_verification(
            event_type="ACCESS_DENIED",
            canonical_parcel_id=None,
            dag_number=None,
            mouza=req.office or officer_profile.get("jurisdiction", "Unknown"),
            verdict="DENIED",
            cited_records=["NAME_MISMATCH"],
            officer_id=req.officer_id or "UNKNOWN",
        )
        return VerifyOfficerResponse(
            status="denied",
            reason="কর্মকর্তার নাম নিবন্ধনের তথ্যের সাথে মেলেনি (Officer name mismatch)",
        )

    if not req.designation or req.designation.strip() != officer_profile.get("designation"):
        audit_ledger.record_verification(
            event_type="ACCESS_DENIED",
            canonical_parcel_id=None,
            dag_number=None,
            mouza=req.office or officer_profile.get("jurisdiction", "Unknown"),
            verdict="DENIED",
            cited_records=["DESIGNATION_MISMATCH"],
            officer_id=req.officer_id or "UNKNOWN",
        )
        return VerifyOfficerResponse(
            status="denied",
            reason="কর্মকর্তার পদবী নিবন্ধনের তথ্যের সাথে মেলেনি (Officer designation mismatch)",
        )

    # 4. Generate signed session token using centralized create_officer_token
    context = OfficerContext(
        officer_id=officer_profile["officer_id"],
        name=officer_profile["name"],
        role=OfficerRole(officer_profile["role"]),
        designation=officer_profile["designation"],
        office=officer_profile["office"],
        jurisdiction=officer_profile["jurisdiction"],
    )
    token = create_officer_token(context)

    # 5. Record ACCESS_GRANTED in audit ledger
    audit_ledger.record_verification(
        event_type="ACCESS_GRANTED",
        canonical_parcel_id=None,
        dag_number=None,
        mouza=officer_profile["jurisdiction"],
        verdict="CLEAR",
        cited_records=[f"REGISTRY-MATCH:{officer_profile['officer_id']}"],
        officer_id=officer_profile["officer_id"],
    )

    return VerifyOfficerResponse(
        status="verified",
        token=token,
        officer=officer_profile,
    )

