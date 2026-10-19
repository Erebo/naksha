"""Rule: Land Development Tax (LD Tax) Compliance Evaluation.

Checks whether the plot's Land Development Tax is current and compliant.
Holding arrears exceeding the statutory threshold (default: 1 fiscal year)
produces a FAIL with severity REVIEW, mandating tax clearance prior to mutation approval.
"""
from decimal import Decimal
from typing import Optional, Union, List
from naksha.core.config import settings
from naksha.normalization.text import parse_numeric
from naksha.services.rules.models import RuleResult, RuleSeverity, RuleStatus


def evaluate_ld_tax_compliance(
    arrears_years: Optional[Union[float, int, str]],
    tax_record_present: bool = True,
    record_ids: Optional[List[str]] = None,
    max_arrears: Optional[int] = None,
    legal_ref: Optional[str] = None,
) -> RuleResult:
    """Evaluates Land Development Tax arrears status.

    Args:
        arrears_years: Number of unpaid fiscal years (supports int, float, or Bengali/English digit strings).
        tax_record_present: Whether a tax record was found for the parcel.
        record_ids: List of record IDs evaluated.
        max_arrears: Permitted arrears years threshold (loaded from config if None).
        legal_ref: Statutory citation (loaded from config if None).
    """
    cited = list(record_ids or [])
    limit_val = settings.max_tax_arrears_years if max_arrears is None else max_arrears
    ref = settings.ld_tax_compliance_legal_ref if legal_ref is None else legal_ref

    if not tax_record_present or arrears_years is None:
        return RuleResult(
            rule_id="ld_tax_compliance",
            status=RuleStatus.UNKNOWN,
            severity=RuleSeverity.REVIEW,
            measured=None,
            limit=limit_val,
            unit="year",
            evidence="Land Development Tax record or arrears status is missing.",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    parsed_arrears = parse_numeric(arrears_years)
    if parsed_arrears is None:
        return RuleResult(
            rule_id="ld_tax_compliance",
            status=RuleStatus.UNKNOWN,
            severity=RuleSeverity.REVIEW,
            measured=None,
            limit=limit_val,
            unit="year",
            evidence=f"Invalid numeric arrears value: '{arrears_years}'.",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    d_arrears = Decimal(str(parsed_arrears))
    d_limit = Decimal(str(limit_val))

    arrears_float = float(d_arrears)
    limit_float = float(d_limit)

    if d_arrears > d_limit:
        return RuleResult(
            rule_id="ld_tax_compliance",
            status=RuleStatus.FAIL,
            severity=RuleSeverity.REVIEW,
            measured=arrears_float,
            limit=limit_float,
            unit="year",
            evidence=f"Holding has {arrears_float:.0f} fiscal year(s) tax arrears (exceeds allowable limit of {limit_float:.0f} year).",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    return RuleResult(
        rule_id="ld_tax_compliance",
        status=RuleStatus.PASS,
        severity=RuleSeverity.REVIEW,
        measured=arrears_float,
        limit=limit_float,
        unit="year",
        evidence=f"Land Development Tax is compliant ({arrears_float:.0f} arrears year(s) <= {limit_float:.0f} allowable).",
        cited_record_ids=cited,
        legal_ref=ref,
    )
