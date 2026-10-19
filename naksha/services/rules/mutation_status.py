"""Rule: Deed e-Mutation Status and Timeliness Evaluation.

Checks whether registered Sub-Registry transfer deeds have a corresponding approved
or open e-Mutation record at the AC Land office within statutory timeframe (default: 30 days).
An unmutated deed exceeding the statutory day limit produces a FAIL with severity REVIEW,
alerting officers to potential title gaps or delayed mutation.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, Union, List
from naksha.core.config import settings
from naksha.normalization.text import parse_numeric
from naksha.services.rules.models import RuleResult, RuleSeverity, RuleStatus


def _parse_date(val: Union[date, datetime, str]) -> Optional[date]:
    """Helper to convert date, datetime, or date-string into datetime.date."""
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        cleaned = val.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(cleaned).date()
        except ValueError:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    return datetime.strptime(cleaned, fmt).date()
                except ValueError:
                    pass
    return None


def evaluate_mutation_status(
    deed_present: bool = False,
    mutation_present: bool = False,
    deed_date: Optional[Union[date, datetime, str]] = None,
    days_unmutated: Optional[Union[int, float, str]] = None,
    today: Optional[date] = None,
    record_ids: Optional[List[str]] = None,
    max_days: Optional[int] = None,
    legal_ref: Optional[str] = None,
) -> RuleResult:
    """Evaluates whether deeds have timely e-Mutation records at AC Land.

    Args:
        deed_present: Whether a Sub-Registry deed exists for the parcel.
        mutation_present: Whether an AC Land e-mutation record exists.
        deed_date: Date of the deed execution/registration.
        days_unmutated: Direct duration in days without mutation (supports digits/strings).
        today: Reference date for computing elapsed days (defaults to UTC today).
        record_ids: List of record IDs evaluated.
        max_days: Statutory unmutated day limit from config.
        legal_ref: Statutory citation from config.
    """
    cited = list(record_ids or [])
    limit_val = settings.max_unmutated_days if max_days is None else max_days
    ref = settings.mutation_status_legal_ref if legal_ref is None else legal_ref

    # If neither deed nor mutation records exist, status is unknown
    if not deed_present and not mutation_present:
        return RuleResult(
            rule_id="mutation_status",
            status=RuleStatus.UNKNOWN,
            severity=RuleSeverity.REVIEW,
            measured=None,
            limit=limit_val,
            unit="day",
            evidence="No deed or mutation records available to evaluate mutation status.",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    # Mutation record is present and active/approved
    if mutation_present:
        return RuleResult(
            rule_id="mutation_status",
            status=RuleStatus.PASS,
            severity=RuleSeverity.REVIEW,
            measured=0,
            limit=limit_val,
            unit="day",
            evidence="AC Land e-Mutation record is present and approved.",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    # Deed is present, but no mutation record exists
    elapsed_days: Optional[int] = None

    if deed_date is not None:
        parsed_d_date = _parse_date(deed_date)
        if parsed_d_date is not None:
            ref_today = today if today is not None else datetime.now(timezone.utc).date()
            elapsed_days = (ref_today - parsed_d_date).days

    if elapsed_days is None and days_unmutated is not None:
        num = parse_numeric(days_unmutated)
        if num is not None:
            elapsed_days = int(num)

    if elapsed_days is None:
        return RuleResult(
            rule_id="mutation_status",
            status=RuleStatus.UNKNOWN,
            severity=RuleSeverity.REVIEW,
            measured=None,
            limit=limit_val,
            unit="day",
            evidence="Sub-Registry deed exists without mutation, but registration date is missing or unparseable.",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    d_days = Decimal(str(elapsed_days))
    d_limit = Decimal(str(limit_val))

    days_float = float(d_days)
    limit_float = float(d_limit)

    if d_days > d_limit:
        return RuleResult(
            rule_id="mutation_status",
            status=RuleStatus.FAIL,
            severity=RuleSeverity.REVIEW,
            measured=days_float,
            limit=limit_float,
            unit="day",
            evidence=f"Deed registered {days_float:.0f} days ago without AC Land e-Mutation (exceeds {limit_float:.0f} day statutory threshold).",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    return RuleResult(
        rule_id="mutation_status",
        status=RuleStatus.PASS,
        severity=RuleSeverity.REVIEW,
        measured=days_float,
        limit=limit_float,
        unit="day",
        evidence=f"Deed is within permissible unmutated window ({days_float:.0f} days <= {limit_float:.0f} days).",
        cited_record_ids=cited,
        legal_ref=ref,
    )
