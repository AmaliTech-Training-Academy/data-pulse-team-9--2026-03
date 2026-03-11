"""Tests for the load module (uses SQLite in-memory for portability)."""

from sqlalchemy import text
from pipeline.etl.transform import transform
from pipeline.etl.load import load


def test_load_creates_dimension_rows(sample_raw_data, in_memory_engine):
    """load() should insert dimension rows into the analytics tables."""
    transformed = transform(sample_raw_data)
    summary = load(in_memory_engine, transformed)

    assert summary.dim_datasets == 2
    assert summary.dim_rules == 3
    assert summary.dim_date >= 2
    assert summary.fact_quality_checks == 3


def test_load_idempotent_dimensions(sample_raw_data, in_memory_engine):
    """Running load twice should not duplicate dimension rows.

    Note: SQLite uses INSERT OR REPLACE instead of ON CONFLICT DO UPDATE,
    so this test verifies the concept. Full upsert tested against PostgreSQL.
    """
    transformed = transform(sample_raw_data)

    # First load
    load(in_memory_engine, transformed)

    # Second load — dimensions should not grow.
    load(in_memory_engine, transformed)

    with in_memory_engine.connect() as conn:
        ds_count = conn.execute(text("SELECT COUNT(*) FROM dim_datasets")).scalar()
        rule_count = conn.execute(text("SELECT COUNT(*) FROM dim_rules")).scalar()

    # Dimensions should stay the same (upsert/replace)
    assert ds_count == 2
    assert rule_count == 3


def test_load_facts_append(sample_raw_data, in_memory_engine):
    """Facts should remain idempotent across repeated loads."""
    transformed = transform(sample_raw_data)

    load(in_memory_engine, transformed)
    load(in_memory_engine, transformed)

    with in_memory_engine.connect() as conn:
        fact_count = conn.execute(text("SELECT COUNT(*) FROM fact_quality_checks")).scalar()

    # Dedup key is (dataset_id, rule_id, checked_at), so count remains stable.
    assert fact_count == 3


def test_load_none_input(in_memory_engine):
    """load() should handle None input gracefully and return zero counts."""
    result = load(in_memory_engine, None)
    assert result.to_dict() == {
        "dim_datasets": 0,
        "dim_date": 0,
        "dim_rules": 0,
        "fact_quality_checks": 0,
        "duplicates_removed": 0,
    }
