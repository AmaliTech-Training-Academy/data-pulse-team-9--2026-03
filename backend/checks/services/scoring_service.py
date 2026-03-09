"""Scoring service - STUB: Needs implementation."""


def calculate_quality_score(results: list, rules: list) -> dict:
    """Calculate weighted quality score - IMPLEMENTED."""
    if not rules:
        return {"score": 100.0, "total_rules": 0, "passed_rules": 0, "failed_rules": 0}

    severity_weights = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    
    total_weight = 0
    total_passed_weight = 0
    passed_count = 0
    failed_count = 0
    
    # Map results to rules by rule_id
    results_map = {r["rule_id"]: r for r in results}
    
    for rule in rules:
        weight = severity_weights.get(rule.severity, 1)
        total_weight += weight
        
        result = results_map.get(rule.id)
        if result:
            total_rows = result.get("total_rows", 0)
            failed_rows = result.get("failed_rows", 0)
            
            if total_rows > 0:
                pass_rate = (total_rows - failed_rows) / total_rows
            else:
                pass_rate = 1.0 if result.get("passed", False) else 0.0
                
            total_passed_weight += weight * pass_rate
            
            if result.get("passed", False):
                passed_count += 1
            else:
                failed_count += 1
        else:
            # Rule not run, counts as failed with 0% pass rate
            failed_count += 1
            
    score = (total_passed_weight / total_weight) * 100 if total_weight > 0 else 100.0
    
    return {
        "score": round(score, 2),
        "total_rules": len(rules),
        "passed_rules": passed_count,
        "failed_rules": failed_count,
    }
