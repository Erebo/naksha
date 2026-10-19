"""Rule: Recorded Owner vs. Claimant Phonetic Name Match Evaluation.

Compares recorded owner names across legacy instruments (Khatian, Sub-Registry Deed)
using phonetic string similarity after stripping honorifics.
Phonetic similarity below the statutory threshold produces a FAIL with severity REVIEW,
requiring manual administrative hearing.
"""
from decimal import Decimal
from typing import Optional, List
from naksha.core.config import settings
from naksha.normalization.text import phonetic_name_similarity, normalize_text
from naksha.services.rules.models import RuleResult, RuleSeverity, RuleStatus


def evaluate_owner_name_match(
    name_a: Optional[str],
    name_b: Optional[str],
    record_ids: Optional[List[str]] = None,
    threshold: Optional[float] = None,
    legal_ref: Optional[str] = None,
) -> RuleResult:
    """Evaluates phonetic string match between two owner/claimant names.

    Args:
        name_a: Primary name from recorded instrument (e.g. Khatian).
        name_b: Counterpart name from transaction or tax dakhila.
        record_ids: List of record IDs evaluated.
        threshold: Minimum phonetic similarity ratio (loaded from config if None).
        legal_ref: Statutory citation (loaded from config if None).
    """
    cited = list(record_ids or [])
    limit_val = settings.owner_name_match_threshold if threshold is None else threshold
    ref = settings.owner_name_match_legal_ref if legal_ref is None else legal_ref

    norm_a = normalize_text(name_a) if name_a else None
    norm_b = normalize_text(name_b) if name_b else None

    if not norm_a or not norm_b:
        return RuleResult(
            rule_id="owner_name_match",
            status=RuleStatus.UNKNOWN,
            severity=RuleSeverity.REVIEW,
            measured=None,
            limit=limit_val,
            unit="ratio",
            evidence="Owner name is missing in one or more records being compared.",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    sim = round(phonetic_name_similarity(norm_a, norm_b), 4)
    d_sim = Decimal(str(sim))
    d_limit = Decimal(str(limit_val))

    sim_float = float(d_sim)
    limit_float = float(d_limit)

    if d_sim < d_limit:
        return RuleResult(
            rule_id="owner_name_match",
            status=RuleStatus.FAIL,
            severity=RuleSeverity.REVIEW,
            measured=sim_float,
            limit=limit_float,
            unit="ratio",
            evidence=f"Owner name divergence: '{norm_a}' vs '{norm_b}' (phonetic score: {sim_float:.2f} < {limit_float:.2f}).",
            cited_record_ids=cited,
            legal_ref=ref,
        )

    return RuleResult(
        rule_id="owner_name_match",
        status=RuleStatus.PASS,
        severity=RuleSeverity.REVIEW,
        measured=sim_float,
        limit=limit_float,
        unit="ratio",
        evidence=f"Owner names match phonetically: '{norm_a}' vs '{norm_b}' (score: {sim_float:.2f} >= {limit_float:.2f}).",
        cited_record_ids=cited,
        legal_ref=ref,
    )
