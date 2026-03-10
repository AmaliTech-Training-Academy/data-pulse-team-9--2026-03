"""Scoring service - IMPLEMENTED."""

from typing import Any, Dict, List, Optional, TypedDict


class QualityScoreResult(TypedDict):
    """Structured response for quality score calculations."""

    score: float
    total_rules: int
    passed_rules: int
    failed_rules: int


# Constant mapping of rule severities to their calculation weights
SEVERITY_WEIGHTS = {
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


def _evaluate_rule_performance(rule: Any, result: Optional[Dict[str, Any]]) -> tuple[float, bool]:
    """Helper method to determine the weight contribution and pass status for a single rule."""
    if not result:
        # Rule wasn't run for some reason; counts as completely failed (0% pass rate)
        return 0.0, False

    total_rows = result.get("total_rows", 0)
    failed_rows = result.get("failed_rows", 0)
    passed_status = result.get("passed", False)

    # Calculate the row-level pass percentage for this rule
    if total_rows > 0:
        pass_rate = (total_rows - failed_rows) / total_rows
    else:
        pass_rate = 1.0 if passed_status else 0.0

    return pass_rate, passed_status


def calculate_quality_score(results: List[Dict[str, Any]], rules: List[Any]) -> QualityScoreResult:
    """Calculate weighted quality score based on individual rule pass rates and severities."""

    if not rules:
        return {"score": 100.0, "total_rules": 0, "passed_rules": 0, "failed_rules": 0}

    total_weight = 0
    total_passed_weight = 0
    passed_count = 0
    failed_count = 0

    # Index results by rule id for O(1) lookups
    results_map = {r.get("rule_id"): r for r in results if r.get("rule_id") is not None}

    for rule in rules:
        # 1. Determine base weight from severity
        weight = SEVERITY_WEIGHTS.get(getattr(rule, "severity", "LOW"), 1)
        total_weight += weight

        # 2. Evaluate physical rule performance
        result_data = results_map.get(getattr(rule, "id", None))
        pass_rate, passed_status = _evaluate_rule_performance(rule, result_data)

        # 3. Accumulate weighted contributions
        total_passed_weight += weight * pass_rate

        if passed_status:
            passed_count += 1
        else:
            failed_count += 1

    # Final calculation: weighted average of row-level pass rates scaled to 0-100
    final_score = (total_passed_weight / total_weight) * 100 if total_weight > 0 else 100.0

    return {
        "score": round(final_score, 2),
        "total_rules": len(rules),
        "passed_rules": passed_count,
        "failed_rules": failed_count,
    }
