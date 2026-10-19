"""Rule: Area Tolerance Discrepancy Evaluation.

Compares registered deed claimed area against ground-truth surveyed area (DLRS).
Symmetric statutory tolerance of ±limit (default: ±0.20 decimals) is strictly enforced:
if abs(deed_area - survey_area) > limit, the rule produces a FAIL with severity BLOCK,
as area inflation directly harms cadastral boundary integrity.
"""
from decimal import Decimal
from typing import Optional, Union, List
from naksha.core.config import settings
from naksha.normalization.text import parse_numeric
from naksha.services.rules.models import RuleResult, RuleSeverity, RuleStatus


def evaluate_area_tolerance(
    deed_area: Optional[Union[float, int, str]],
    survey_area: Optional[Union[float, int, str]],
    record_ids: Optional[List[str]] = None,
    tolerance: Optional[float] = None,
    legal_ref: Optional[str] = None,
) -> RuleResult:
    """Evaluates deed claim vs. survey area against a symmetric ±tolerance threshold.

    Symmetric ±limit evaluation:
    - If abs(deed_area - survey_area) <= tolerance -> PASS
    - If abs(deed_area - survey_area) > tolerance -> FAIL (BLOCK)
    - If either area is missing or unparseable -> UNKNOWN

    Severity is BLOCK because paper area discrepancies beyond tolerance indicate
    either fraudulent paper inflation or unregistered boundary loss.
    """
    cited = list(record_ids or [])
    limit_val = settings.area_tolerance_decimals if tolerance is None else tolerance
    ref = settings.area_tolerance_legal_ref if legal_ref is None else legal_ref

    if deed_area is None or survey_area is None:
        return RuleResult(
            rule_id="area_tolerance",
            status=RuleStatus.UNKNOWN,
            severity=RuleSeverity.BLOCK,
            measured=None,
            limit=limit_val,
            unit="decimal",
            evidence="Deed area or surveyed ground-truth area is missing.",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    parsed_deed = parse_numeric(deed_area)
    parsed_survey = parse_numeric(survey_area)

    if parsed_deed is None or parsed_survey is None:
        return RuleResult(
            rule_id="area_tolerance",
            status=RuleStatus.UNKNOWN,
            severity=RuleSeverity.BLOCK,
            measured=None,
            limit=limit_val,
            unit="decimal",
            evidence=f"Invalid numeric area values: deed='{deed_area}', survey='{survey_area}'.",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    # Use Decimal for exact symmetric difference and threshold comparison
    d_deed = Decimal(str(parsed_deed))
    d_survey = Decimal(str(parsed_survey))
    d_limit = Decimal(str(limit_val))
    d_diff = abs(d_deed - d_survey)

    diff_float = float(d_diff)
    limit_float = float(d_limit)

    if d_diff > d_limit:
        return RuleResult(
            rule_id="area_tolerance",
            status=RuleStatus.FAIL,
            severity=RuleSeverity.BLOCK,
            measured=diff_float,
            limit=limit_float,
            unit="decimal",
            evidence=(
                f"Area divergence of {diff_float:.2f} dec (deed: {float(d_deed):.2f} dec, "
                f"survey: {float(d_survey):.2f} dec) exceeds symmetric statutory tolerance of ±{limit_float:.2f} dec."
            ),
            cited_record_ids=cited,
            legal_ref=ref,
        )

    return RuleResult(
        rule_id="area_tolerance",
        status=RuleStatus.PASS,
        severity=RuleSeverity.BLOCK,
        measured=diff_float,
        limit=limit_float,
        unit="decimal",
        evidence=(
            f"Area divergence of {diff_float:.2f} dec (deed: {float(d_deed):.2f} dec, "
            f"survey: {float(d_survey):.2f} dec) is within symmetric statutory tolerance of ±{limit_float:.2f} dec."
        ),
        cited_record_ids=cited,
        legal_ref=ref,
    )
