"""NAKSHA Statutory Rules Engine Package.

Exports the 5 explicit statutory business rules and their result models:
1. khas_encroachment: Public Khas canal / waterbody encroachment (BLOCK)
2. area_tolerance: Registered deed claimed area vs DLRS surveyed area (BLOCK)
3. owner_name_match: Recorded owner vs claimant phonetic name match (REVIEW)
4. ld_tax_compliance: Land Development Tax clearance and arrears (REVIEW)
5. mutation_status: Sub-Registry deed e-Mutation timeliness (REVIEW)
"""
from typing import List, Tuple, Optional
from datetime import date

from naksha.models.enums import VerificationVerdict, DiscrepancySeverity
from naksha.models.canonical import Discrepancy
from naksha.services.rules.models import RuleResult, RuleStatus, RuleSeverity
from naksha.services.rules.khas_encroachment import evaluate_khas_encroachment
from naksha.services.rules.area_tolerance import evaluate_area_tolerance
from naksha.services.rules.owner_name_match import evaluate_owner_name_match
from naksha.services.rules.ld_tax_compliance import evaluate_ld_tax_compliance
from naksha.services.rules.mutation_status import evaluate_mutation_status


def compute_final_verdict(
    rule_results: List[RuleResult],
    discrepancies: Optional[List[Discrepancy]] = None,
) -> VerificationVerdict:
    """Computes final clearance verdict as worst-case across 5 rules and discrepancies.

    Hierarchy:
    - BLOCK if any rule fails with BLOCK or any discrepancy is BLOCKING (e.g. duplicate deed, dag mismatch).
    - REVIEW if any rule fails with REVIEW, any rule is UNKNOWN (missing data), or any discrepancy is WARNING.
    - CLEAR only if all rules PASS and no blocking/warning discrepancies exist.
    """
    discs = discrepancies or []

    # Check for blocking conditions
    has_blocking_rule = any(
        r.status == RuleStatus.FAIL and r.severity == RuleSeverity.BLOCK
        for r in rule_results
    )
    has_blocking_disc = any(
        d.severity == DiscrepancySeverity.BLOCKING
        for d in discs
    )
    if has_blocking_rule or has_blocking_disc:
        return VerificationVerdict.BLOCK

    # Check for review / warning / unknown conditions
    has_review_rule = any(
        r.status == RuleStatus.FAIL and r.severity == RuleSeverity.REVIEW
        for r in rule_results
    )
    has_unknown_rule = any(
        r.status == RuleStatus.UNKNOWN
        for r in rule_results
    )
    has_warning_disc = any(
        d.severity == DiscrepancySeverity.WARNING
        for d in discs
    )
    if has_review_rule or has_unknown_rule or has_warning_disc:
        return VerificationVerdict.REVIEW

    return VerificationVerdict.CLEAR


__all__ = [
    "RuleResult",
    "RuleStatus",
    "RuleSeverity",
    "evaluate_khas_encroachment",
    "evaluate_area_tolerance",
    "evaluate_owner_name_match",
    "evaluate_ld_tax_compliance",
    "evaluate_mutation_status",
    "compute_final_verdict",
]
