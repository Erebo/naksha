"""API Route Definitions for NAKSHA Stage 2."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from naksha.core.config import settings
from naksha.models.canonical import LandRecord, VerificationResult
from naksha.models.enums import AgencyType
from naksha.repository.base import BaseRecordRepository
from naksha.repository.memory import InMemoryRecordRepository
from naksha.data.synthetic import generate_synthetic_records
from naksha.services.verification import verify_record_against_cohort

router = APIRouter()

# Default singleton repository pre-populated with synthetic records
_default_repo = InMemoryRecordRepository(initial_records=generate_synthetic_records())


def get_repository() -> BaseRecordRepository:
    """Dependency provider for the repository layer."""
    return _default_repo


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "naksha-api"
    version: str = "0.2.0"
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


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health and Readiness Check",
    tags=["System"],
)
def get_health() -> HealthResponse:
    """Returns the operational status of the NAKSHA canonical API."""
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
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
        description="NAKSHA Canonical Land Data Model Reconciliation Demo (Stage 2)",
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
