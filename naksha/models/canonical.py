"""Canonical Land Data Model for NAKSHA (Pydantic v2).

Defines the normalized data structures used across all agency adapters and
reconciliation engines.
"""
from datetime import datetime, timezone
from typing import Generic, Optional, TypeVar, Any
from pydantic import BaseModel, Field, ConfigDict

from naksha.models.enums import (
    AgencyType,
    LandAreaUnit,
    SurveyEra,
    LandClass,
    VerificationVerdict,
    DiscrepancyType,
    DiscrepancySeverity,
)

T = TypeVar("T")


class ExtractedField(BaseModel, Generic[T]):
    """Encapsulates an extracted piece of data, preserving the raw input alongside

    its normalized comparison value, extraction confidence, and document citation.
    """
    raw_value: Optional[str] = Field(
        default=None,
        description="Original text/value exactly as extracted from the source document.",
    )
    normalized_value: Optional[T] = Field(
        default=None,
        description="Cleaned, standardized value used for deterministic comparisons.",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score (0.0 to 1.0).",
    )
    source_citation: Optional[str] = Field(
        default=None,
        description="Specific clause, column, or sheet coordinate where this field was found.",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SourceReference(BaseModel):
    """Metadata regarding the originating agency, document type, and authority."""
    agency: AgencyType = Field(
        description="Originating government body or financial institution.",
    )
    document_type: str = Field(
        description="Legal instrument or record type (e.g., Deed, Khatian BS, Dakhila).",
    )
    source_record_id: str = Field(
        description="Primary identifier within the source agency (e.g. Deed No., Case ID, Holding No.).",
    )
    volume_or_sheet: Optional[str] = Field(
        default=None,
        description="Volume, book, or map sheet number.",
    )
    issuing_office: Optional[str] = Field(
        default=None,
        description="Specific office or SRO branch (e.g., 'Sadar SRO, Dhaka').",
    )
    issue_date: Optional[str] = Field(
        default=None,
        description="Date of record issuance in ISO format (YYYY-MM-DD) or raw date.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional contextual notes from the source archive.",
    )


class LandRecord(BaseModel):
    """Canonical representation of a single land record from any agency.

    Fields are optional to accommodate fragmented, damaged, or legacy records.
    Original raw values are preserved within ExtractedField objects.
    """
    id: str = Field(
        description="Unique internal record identifier (e.g. 'rec-subreg-001' or UUIDv7).",
    )
    canonical_parcel_id: Optional[str] = Field(
        default=None,
        description="Resolved persistent canonical parcel UUID (UUIDv7) if matched.",
    )
    source: SourceReference = Field(
        description="Provenance and originating system reference.",
    )

    # Administrative Jurisdiction
    district: Optional[ExtractedField[str]] = Field(
        default=None,
        description="District (জেলা) name.",
    )
    upazila: Optional[ExtractedField[str]] = Field(
        default=None,
        description="Upazila / Thana (উপজেলা / থানা) name.",
    )
    mouza: Optional[ExtractedField[str]] = Field(
        default=None,
        description="Revenue village / Mouza (মৌজা) name.",
    )
    jl_number: Optional[ExtractedField[str]] = Field(
        default=None,
        description="Jurisdiction List (জে. এল. নং) identifier.",
    )

    # Land Plot & Title Identifiers
    survey_era: Optional[SurveyEra] = Field(
        default=None,
        description="Survey operation era (CS, SA, RS, BS, DIARA).",
    )
    khatian_number: Optional[ExtractedField[str]] = Field(
        default=None,
        description="Record-of-Rights / Khatian (খতিয়ান) number.",
    )
    dag_number: Optional[ExtractedField[str]] = Field(
        default=None,
        description="Survey plot / Dag (দাগ) number.",
    )
    holding_number: Optional[ExtractedField[str]] = Field(
        default=None,
        description="Union land revenue holding (হোল্ডিং) number.",
    )

    # Ownership & Parties
    owner_name: Optional[ExtractedField[str]] = Field(
        default=None,
        description="Recorded owner or claimant name.",
    )
    owner_nid_hmac: Optional[str] = Field(
        default=None,
        description="Salted cryptographic HMAC of the National ID (no plaintext PII).",
    )
    ownership_share: Optional[ExtractedField[float]] = Field(
        default=None,
        description="Fractional share of plot ownership (e.g. 0.50 for 50%, 1.0 for sole owner).",
    )

    # Land Area Measurements
    recorded_area: Optional[float] = Field(
        default=None,
        description="Original numeric area as stated in the source document.",
    )
    recorded_unit: Optional[LandAreaUnit] = Field(
        default=None,
        description="Original measurement unit (decimal, acre, bigha, katha, etc.).",
    )
    area_in_decimals: Optional[float] = Field(
        default=None,
        description="Standardized area converted to Bangladesh revenue decimals (শতক).",
    )
    area_in_sq_meters: Optional[float] = Field(
        default=None,
        description="Standardized area converted to metric square meters.",
    )
    land_class: Optional[LandClass] = Field(
        default=None,
        description="Revenue land classification (e.g. Nal, Viti, Pukur, Khas).",
    )

    # Encumbrances & Locks
    is_encumbered: bool = Field(
        default=False,
        description="Whether an active mortgage lien or acquisition notice is attached.",
    )
    encumbrance_details: Optional[str] = Field(
        default=None,
        description="Details of active lien or corridor acquisition lock.",
    )

    # Synthetic Dataset Guardrails
    is_synthetic: bool = Field(
        default=True,
        description="Safety flag declaring this record as synthetic benchmark data.",
    )
    synthetic_disclaimer: str = Field(
        default="SYNTHETIC BENCHMARK RECORD: NOT AN OFFICIAL GOVERNMENT DOCUMENT",
        description="Audit notice verifying no real citizen PII is present.",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when record was ingested into NAKSHA.",
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when record was normalized and validated.",
    )


class RecordMatch(BaseModel):
    """Describes a positive cross-agency match between two records."""
    target_record_id: str = Field(description="Internal ID of the record being verified.")
    matched_record_id: str = Field(description="Internal ID of the matching agency record.")
    match_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall match confidence score (1.0 = exact match).",
    )
    matched_fields: list[str] = Field(
        default_factory=list,
        description="List of fields that agreed between the records (e.g. ['dag', 'khatian', 'mouza']).",
    )
    match_type: str = Field(
        default="CANONICAL_EXACT",
        description="Type of match: CANONICAL_EXACT, PHONETIC_EQUIVALENT, or JURISDICTION_OVERLAP.",
    )
    explanation: str = Field(
        description="Human-readable explanation of why the match was established.",
    )


class Discrepancy(BaseModel):
    """Details a specific discrepancy or anomaly detected between records."""
    discrepancy_type: DiscrepancyType = Field(
        description="Type of conflict or divergence detected.",
    )
    severity: DiscrepancySeverity = Field(
        default=DiscrepancySeverity.WARNING,
        description="Severity level: INFO, WARNING, or BLOCKING.",
    )
    field_name: str = Field(
        description="The field where discrepancy arose (e.g. 'dag_number', 'area_in_decimals').",
    )
    record_a_id: str = Field(
        description="ID of the first record involved.",
    )
    record_b_id: Optional[str] = Field(
        default=None,
        description="ID of the second record involved in the conflict (if applicable).",
    )
    value_a: Optional[str] = Field(
        default=None,
        description="Recorded value in record A.",
    )
    value_b: Optional[str] = Field(
        default=None,
        description="Recorded value in record B.",
    )
    difference_description: str = Field(
        description="Explicit, explainable statement describing the difference.",
    )


class VerificationResult(BaseModel):
    """Consolidated outcome of verifying and cross-referencing land records."""
    canonical_parcel_id: Optional[str] = Field(
        default=None,
        description="Resolved canonical parcel UUID (UUIDv7) if determined.",
    )
    primary_record_id: str = Field(
        description="ID of the record subjected to verification.",
    )
    compared_record_ids: list[str] = Field(
        default_factory=list,
        description="IDs of all agency records evaluated against the primary record.",
    )
    verdict: VerificationVerdict = Field(
        description="Decision outcome: CLEAR, REVIEW, or BLOCK.",
    )
    summary: str = Field(
        description="Concise, explainable summary of the clearance verdict.",
    )
    matches: list[RecordMatch] = Field(
        default_factory=list,
        description="Positive matches identified across records.",
    )
    discrepancies: list[Discrepancy] = Field(
        default_factory=list,
        description="List of all detected discrepancies or anomalies.",
    )
    is_synthetic: bool = Field(
        default=True,
        description="Safety flag confirming synthetic benchmark execution.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of verification execution.",
    )
