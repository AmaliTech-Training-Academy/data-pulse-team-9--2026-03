"""Tests for the transform module."""

import pandas as pd
import pytest
from pipeline.etl.transform import transform, ValidationError


def test_transform_returns_all_keys(sample_raw_data):
    """transform() should return TransformResult containing all tables."""
    result = transform(sample_raw_data)
    assert result is not None
    assert set(result.to_dict().keys()) == {"dim_datasets", "dim_rules", "dim_date", "facts"}


def test_transform_dim_datasets_no_duplicates(sample_raw_data):
    """Each dataset should appear exactly once in dim_datasets."""
    result = transform(sample_raw_data)
    dim = result.dim_datasets
    assert len(dim) == 2  # dataset_id 10 and 20
    assert "id" in dim.columns
    assert "name" in dim.columns
    assert dim["id"].is_unique


def test_transform_dim_rules_no_duplicates(sample_raw_data):
    """Each rule should appear exactly once in dim_rules."""
    result = transform(sample_raw_data)
    dim = result.dim_rules
    assert len(dim) == 3  # rule_id 100, 101, 102
    assert dim["id"].is_unique


def test_transform_dim_rules_has_required_columns(sample_raw_data):
    """dim_rules should have all columns from the corrected schema."""
    result = transform(sample_raw_data)
    dim = result.dim_rules
    for col in ["id", "name", "field_name", "rule_type", "severity", "dataset_type", "is_active"]:
        assert col in dim.columns, f"Missing column: {col}"


def test_transform_dim_date_covers_range(sample_raw_data):
    """dim_date should cover all dates between min and max checked_at."""
    result = transform(sample_raw_data)
    dim = result.dim_date
    assert len(dim) >= 2  # at least 2 days in the sample data
    assert "date_key" in dim.columns
    assert "quarter" in dim.columns


def test_transform_facts_score_computation(sample_raw_data):
    """score should be (total_rows - failed_rows) / total_rows * 100."""
    result = transform(sample_raw_data)
    facts = result.facts
    # Row with 0 failed out of 500 → 100.0
    row_passed = facts[facts["passed"] == True].iloc[0]
    assert row_passed["score"] == 100.0
    # Row with 25 failed out of 500 → 95.0
    row_failed = facts[facts["passed"] == False].iloc[0]
    assert row_failed["score"] == 95.0


def test_transform_facts_date_key(sample_raw_data):
    """date_key should be an integer in YYYYMMDD format."""
    result = transform(sample_raw_data)
    facts = result.facts
    for dk in facts["date_key"]:
        assert isinstance(dk, int)
        s = str(dk)
        assert len(s) == 8  # YYYYMMDD


def test_transform_empty_input():
    """transform() should return None for empty input."""
    assert transform(pd.DataFrame()) is None
    assert transform(None) is None


def test_transform_validation_error_missing_columns():
    """transform() should raise ValidationError if required columns missing."""
    bad_df = pd.DataFrame({"foo": [1, 2]})
    with pytest.raises(ValidationError):
        transform(bad_df)
