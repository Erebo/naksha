"""Rule: Public Khas Land / Canal Encroachment Evaluation.

Evaluates whether a parcel's claimed boundaries intersect or overlap into
government-owned public drainage canals, rivers, or Khas land.
Any positive encroachment beyond the statutory threshold (default: 0.0 decimals)
triggers an absolute BLOCK.
"""
from decimal import Decimal
from typing import Optional, Union, List
from naksha.core.config import settings
from naksha.normalization.text import parse_numeric
from naksha.services.rules.models import RuleResult, RuleSeverity, RuleStatus


def evaluate_khas_encroachment(
    overlap_decimals: Optional[Union[float, int, str]],
    record_ids: Optional[List[str]] = None,
    threshold: Optional[float] = None,
    legal_ref: Optional[str] = None,
) -> RuleResult:
    """Evaluates Khas encroachment from measured overlap area in decimals.

    Args:
        overlap_decimals: Measured overlap area with public Khas land in decimals.
        record_ids: List of record IDs evaluated.
        threshold: Permitted overlap threshold in decimals (loaded from config if None).
        legal_ref: Statutory citation (loaded from config if None).
    """
    cited = list(record_ids or [])
    limit_val = settings.khas_overlap_limit_decimals if threshold is None else threshold
    ref = settings.khas_encroachment_legal_ref if legal_ref is None else legal_ref

    if overlap_decimals is None:
        return RuleResult(
            rule_id="khas_encroachment",
            status=RuleStatus.UNKNOWN,
            severity=RuleSeverity.BLOCK,
            measured=None,
            limit=limit_val,
            unit="decimal",
            evidence="Khas boundary overlap data is missing or unverified.",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    parsed_overlap = parse_numeric(overlap_decimals)
    if parsed_overlap is None:
        return RuleResult(
            rule_id="khas_encroachment",
            status=RuleStatus.UNKNOWN,
            severity=RuleSeverity.BLOCK,
            measured=None,
            limit=limit_val,
            unit="decimal",
            evidence=f"Invalid numeric overlap value: '{overlap_decimals}'.",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    # Use Decimal for exact threshold comparison without floating point inaccuracies
    dec_overlap = Decimal(str(parsed_overlap))
    dec_limit = Decimal(str(limit_val))

    if dec_overlap > dec_limit:
        return RuleResult(
            rule_id="khas_encroachment",
            status=RuleStatus.FAIL,
            severity=RuleSeverity.BLOCK,
            measured=float(dec_overlap),
            limit=float(dec_limit),
            unit="decimal",
            evidence=f"Encroachment detected on public Khas land/canal: {float(dec_overlap):.2f} dec overlap (limit: {float(dec_limit):.2f} dec).",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    return RuleResult(
        rule_id="khas_encroachment",
        status=RuleStatus.PASS,
        severity=RuleSeverity.BLOCK,
        measured=float(dec_overlap),
        limit=float(dec_limit),
        unit="decimal",
        evidence=f"No Khas canal or public land encroachment detected ({float(dec_overlap):.2f} dec <= {float(dec_limit):.2f} dec).",
        cited_record_ids=cited,
        legal_ref=ref,
    )
