"""Unit tests for scoring_service — weighted quality score calculation."""

import pytest
from checks.services.scoring_service import calculate_quality_score


class MockRule:
    def __init__(self, id, severity):
        self.id = id
        self.severity = severity


class TestCalculateQualityScore:
    def test_perfect_score(self):
        rules = [MockRule(1, "HIGH"), MockRule(2, "MEDIUM"), MockRule(3, "LOW")]
        results = [
            {"rule_id": 1, "passed": True},
            {"rule_id": 2, "passed": True},
            {"rule_id": 3, "passed": True},
        ]
        score = calculate_quality_score(results, rules)
        assert score["score"] == 100.0
        assert score["passed_rules"] == 3
        assert score["failed_rules"] == 0

    def test_zero_score(self):
        rules = [MockRule(1, "HIGH"), MockRule(2, "MEDIUM")]
        results = [
            {"rule_id": 1, "passed": False},
            {"rule_id": 2, "passed": False},
        ]
        score = calculate_quality_score(results, rules)
        assert score["score"] == 0.0
        assert score["failed_rules"] == 2

    def test_weighted_scoring(self):
        """HIGH rule passes (weight 3), LOW rule fails (weight 1) → 3/4 = 75%."""
        rules = [MockRule(1, "HIGH"), MockRule(2, "LOW")]
        results = [
            {"rule_id": 1, "passed": True},
            {"rule_id": 2, "passed": False},
        ]
        score = calculate_quality_score(results, rules)
        assert score["score"] == 75.0

    def test_no_rules_returns_perfect(self):
        score = calculate_quality_score([], [])
        assert score["score"] == 100.0
        assert score["total_rules"] == 0

    def test_mixed_severities(self):
        """HIGH=3 fail, MEDIUM=2 pass, LOW=1 pass → 3/6 = 50%."""
        rules = [MockRule(1, "HIGH"), MockRule(2, "MEDIUM"), MockRule(3, "LOW")]
        results = [
            {"rule_id": 1, "passed": False},
            {"rule_id": 2, "passed": True},
            {"rule_id": 3, "passed": True},
        ]
        score = calculate_quality_score(results, rules)
        assert score["score"] == 50.0
        assert score["passed_rules"] == 2
        assert score["failed_rules"] == 1

    def test_proportional_scoring(self):
        """HIGH rule fails 2 out of 10 rows (80% pass). Weight 3.
        Total weight 3. Passed weight 3 * 0.8 = 2.4. Score = 80.0"""
        rules = [MockRule(1, "HIGH")]
        results = [
            {"rule_id": 1, "passed": False, "total_rows": 10, "failed_rows": 2},
        ]
        score = calculate_quality_score(results, rules)
        assert score["score"] == 80.0
        assert score["failed_rules"] == 1
