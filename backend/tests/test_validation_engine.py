"""Unit tests for ValidationEngine — all 5 check types + edge cases."""

import pytest
import pandas as pd

from checks.services.validation_engine import ValidationEngine


@pytest.fixture
def engine():
    return ValidationEngine()


# ---------- null_check ----------

class TestNullCheck:
    def test_no_nulls(self, engine):
        df = pd.DataFrame({"name": ["Alice", "Bob", "Carol"]})
        result = engine.null_check(df, "name")
        assert result["passed"] is True
        assert result["failed_rows"] == 0
        assert result["total_rows"] == 3

    def test_with_nulls(self, engine):
        df = pd.DataFrame({"name": ["Alice", None, "Carol"]})
        result = engine.null_check(df, "name")
        assert result["passed"] is False
        assert result["failed_rows"] == 1

    def test_missing_field(self, engine):
        df = pd.DataFrame({"name": ["Alice"]})
        result = engine.null_check(df, "nonexistent")
        assert result["passed"] is False
        assert result["failed_rows"] == 1


# ---------- type_check ----------

class TestTypeCheck:
    def test_int_valid(self, engine):
        df = pd.DataFrame({"age": [25, 30, 35]})
        result = engine.type_check(df, "age", "int")
        assert result["passed"] is True
        assert result["failed_rows"] == 0

    def test_int_with_float_values(self, engine):
        df = pd.DataFrame({"val": [1.5, 2.5, 3.5]})
        result = engine.type_check(df, "val", "int")
        assert result["passed"] is False
        assert result["failed_rows"] == 3

    def test_float_valid(self, engine):
        df = pd.DataFrame({"price": [1.5, 2.0, 3.99]})
        result = engine.type_check(df, "price", "float")
        assert result["passed"] is True

    def test_numeric_with_strings(self, engine):
        df = pd.DataFrame({"val": ["abc", "def", "ghi"]})
        result = engine.type_check(df, "val", "numeric")
        assert result["passed"] is False
        assert result["failed_rows"] == 3

    def test_datetime_valid(self, engine):
        df = pd.DataFrame({"date": ["2024-01-01", "2024-02-15", "2024-12-31"]})
        result = engine.type_check(df, "date", "datetime")
        assert result["passed"] is True

    def test_datetime_invalid(self, engine):
        df = pd.DataFrame({"date": ["not-a-date", "also-not"]})
        result = engine.type_check(df, "date", "datetime")
        assert result["passed"] is False
        assert result["failed_rows"] == 2

    def test_str_always_passes(self, engine):
        df = pd.DataFrame({"val": [1, 2.5, "hello"]})
        result = engine.type_check(df, "val", "str")
        assert result["passed"] is True
        assert result["failed_rows"] == 0

    def test_missing_field(self, engine):
        df = pd.DataFrame({"a": [1]})
        result = engine.type_check(df, "nonexistent", "int")
        assert result["passed"] is False

    def test_unsupported_type(self, engine):
        df = pd.DataFrame({"a": [1]})
        result = engine.type_check(df, "a", "custom_type")
        assert result["passed"] is False


# ---------- range_check ----------

class TestRangeCheck:
    def test_in_range(self, engine):
        df = pd.DataFrame({"age": [20, 30, 40]})
        result = engine.range_check(df, "age", 18, 65)
        assert result["passed"] is True
        assert result["failed_rows"] == 0

    def test_out_of_range(self, engine):
        df = pd.DataFrame({"age": [10, 30, 100]})
        result = engine.range_check(df, "age", 18, 65)
        assert result["passed"] is False
        assert result["failed_rows"] == 2  # 10 < 18 and 100 > 65

    def test_min_only(self, engine):
        df = pd.DataFrame({"val": [5, 15, 25]})
        result = engine.range_check(df, "val", 10, None)
        assert result["passed"] is False
        assert result["failed_rows"] == 1  # 5 < 10

    def test_max_only(self, engine):
        df = pd.DataFrame({"val": [5, 15, 25]})
        result = engine.range_check(df, "val", None, 20)
        assert result["passed"] is False
        assert result["failed_rows"] == 1  # 25 > 20

    def test_non_numeric_values(self, engine):
        df = pd.DataFrame({"val": ["abc", 10, 20]})
        result = engine.range_check(df, "val", 0, 100)
        assert result["passed"] is False
        assert result["failed_rows"] >= 1

    def test_missing_field(self, engine):
        df = pd.DataFrame({"a": [1]})
        result = engine.range_check(df, "nonexistent", 0, 100)
        assert result["passed"] is False


# ---------- unique_check ----------

class TestUniqueCheck:
    def test_all_unique(self, engine):
        df = pd.DataFrame({"id": [1, 2, 3, 4, 5]})
        result = engine.unique_check(df, "id")
        assert result["passed"] is True
        assert result["failed_rows"] == 0

    def test_with_duplicates(self, engine):
        df = pd.DataFrame({"id": [1, 2, 2, 3, 3]})
        result = engine.unique_check(df, "id")
        assert result["passed"] is False
        assert result["failed_rows"] == 4  # duplicated(keep=False) marks all duplicates

    def test_missing_field(self, engine):
        df = pd.DataFrame({"a": [1]})
        result = engine.unique_check(df, "nonexistent")
        assert result["passed"] is False


# ---------- regex_check ----------

class TestRegexCheck:
    def test_all_match(self, engine):
        df = pd.DataFrame({"email": ["a@b.com", "c@d.org", "e@f.net"]})
        result = engine.regex_check(df, "email", r".+@.+\..+")
        assert result["passed"] is True
        assert result["failed_rows"] == 0

    def test_some_fail(self, engine):
        df = pd.DataFrame({"email": ["a@b.com", "not-an-email", "e@f.net"]})
        result = engine.regex_check(df, "email", r".+@.+\..+")
        assert result["passed"] is False
        assert result["failed_rows"] == 1

    def test_empty_pattern(self, engine):
        df = pd.DataFrame({"val": ["abc"]})
        result = engine.regex_check(df, "val", "")
        assert result["passed"] is False

    def test_missing_field(self, engine):
        df = pd.DataFrame({"a": [1]})
        result = engine.regex_check(df, "nonexistent", r"\d+")
        assert result["passed"] is False


# ---------- run_all_checks ----------

class TestRunAllChecks:
    def test_runs_multiple_rules(self, engine):
        """Create mock rules and verify all checks are dispatched."""
        df = pd.DataFrame({"name": ["Alice", "Bob", None], "age": [25, 30, 35]})

        class MockRule:
            def __init__(self, id, rule_type, field_name, parameters=None):
                self.id = id
                self.rule_type = rule_type
                self.field_name = field_name
                self.parameters = parameters

        rules = [
            MockRule(1, "NOT_NULL", "name"),
            MockRule(2, "RANGE", "age", '{"min": 0, "max": 100}'),
        ]

        results = engine.run_all_checks(df, rules)
        assert len(results) == 2
        assert results[0]["rule_id"] == 1
        assert results[0]["passed"] is False  # has a null
        assert results[1]["rule_id"] == 2
        assert results[1]["passed"] is True   # all in range
