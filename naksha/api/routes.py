"""API Route Definitions for NAKSHA Canonical & Spatial Engine."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
)
from naksha.services.verification import verify_record_against_cohort
from naksha.spatial.engine import (
    calculate_polygon_area,
    calculate_overlap,
    validate_geometry,
)

router = APIRouter()

# Default singleton repository pre-populated with synthetic records
_default_repo = InMemoryRecordRepository(initial_records=generate_synthetic_records())


def get_repository() -> BaseRecordRepository:
    """Dependency provider for the repository layer."""
    return _default_repo


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
) -> RecordListResponse:
    """Retrieves normalized canonical land records with optional agency, mouza, or dag filters."""
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
) -> LandRecord:
    """Fetches a specific normalized canonical LandRecord by its unique ID."""
    record = repo.get_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Land record '{record_id}' not found.",
        )
    return record


# ==============================================================================
# 2D GIS & Spatial Engine Endpoints
# ==============================================================================

@router.get(
    f"{settings.api_prefix}/spatial/parcels",
    response_model=GeoJSONFeatureCollection,
    summary="Get All Parcel Boundaries in GeoJSON",
    tags=["Spatial Engine"],
)
def get_all_parcels_geojson() -> GeoJSONFeatureCollection:
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
def get_parcel_survey_layers(parcel_id: str) -> List[SurveyLayerSnapshot]:
    """Returns the multi-era survey visual layer stack for the interactive 2D GIS side panel:

    - Layer 1: Ancestral CS Dag 88 footprint (historical root)
    - Layer 2: Deed claim boundary (6.0 dec claim)
    - Layer 3: DLRS surveyed ground truth (5.1 dec polygon)
    - Layer 4: Computed conflict zone (0.9 dec Khas canal overlap)
    - Layer 5: Public Khas canal boundary
    """
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
def get_parcel_neighbors(parcel_id: str) -> GeoJSONFeatureCollection:
    """Returns the target parcel and adjacent plots with LD Tax payment statuses

    (paid, arrears, payer mismatch) for rendering the Tax Map in the side panel.
    """
    return get_synthetic_neighbor_parcels(parcel_id)


@router.get(
    f"{settings.api_prefix}/spatial/parcels/{{parcel_id}}/conflicts",
    response_model=Optional[SpatialConflictZone],
    summary="Get Computed Spatial Conflict Zone",
    tags=["Spatial Engine"],
)
def get_parcel_conflict_zone(parcel_id: str) -> Optional[SpatialConflictZone]:
    """Returns geometric details of any public Khas encroachment or boundary conflict."""
    conflict = get_synthetic_conflict_zone(parcel_id)
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No spatial conflict detected on parcel '{parcel_id}'.",
        )
    return conflict


@router.post(
    f"{settings.api_prefix}/spatial/calculate-area",
    response_model=AreaCalculationResponse,
    summary="Calculate Deterministic Metric Area in UTM 46N",
    tags=["Spatial Engine"],
)
def api_calculate_area(req: AreaCalculationRequest) -> AreaCalculationResponse:
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
def api_calculate_overlap(req: OverlapCalculationRequest) -> OverlapCalculationResponse:
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
