"""Data models for NAKSHA statutory rules (domain layer)."""
from enum import Enum
from typing import Optional, Union, List
from pydantic import BaseModel, Field


class RuleStatus(str, Enum):
    """Execution status of a statutory business rule."""
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class RuleSeverity(str, Enum):
    """Enforced severity when a statutory business rule fails."""
    BLOCK = "BLOCK"
    REVIEW = "REVIEW"


class RuleResult(BaseModel):
    """Outcome of evaluating an explicit statutory business rule."""
    rule_id: str = Field(description="Unique rule identifier (e.g. 'khas_encroachment').")
    status: RuleStatus = Field(description="Status of rule: PASS, FAIL, or UNKNOWN.")
    severity: RuleSeverity = Field(description="Action severity if failed: BLOCK or REVIEW.")
    measured: Optional[Union[float, int, str]] = Field(
        default=None,
        description="Measured value from the record/geometry (None if missing/unknown).",
    )
    limit: Optional[Union[float, int, str]] = Field(
        default=None,
        description="Statutory threshold or permitted boundary limit from config.",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Measurement unit (e.g. 'decimal', 'ratio', 'year', 'day').",
    )
    evidence: str = Field(description="Human-readable explainable evidence string.")
    cited_record_ids: List[str] = Field(
        default_factory=list,
        description="Identifiers of records evaluated in this rule.",
    )
    legal_ref: str = Field(description="Statutory legal citation or unverified notice.")
