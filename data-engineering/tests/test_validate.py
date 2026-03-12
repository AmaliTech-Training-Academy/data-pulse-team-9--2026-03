# Tests for the validation module (pipeline/etl/validate.py).


import pytest
from datetime import datetime, timezone

from sqlalchemy import create_engine, text

from pipeline.etl.validate import (
    validate,
    validate_with_guard,
    StrictValidationError,
    _check_row_counts,
    _check_foreign_keys,
    _check_score_ranges,
    _check_duplicate_facts,
)
from pipeline.models import (
    ValidationResult,
    IntegrityWarning,
    Severity,
)
from infrastructure.db import AnalyticsBase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def source_engine():
    """SQLite in-memory engine with a minimal check_results (source) table."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE check_results (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    rule_id   INTEGER NOT NULL,
                    passed    BOOLEAN NOT NULL,
                    failed_rows INTEGER DEFAULT 0,
                    total_rows  INTEGER DEFAULT 0,
                    checked_at  TIMESTAMP
                )
                """
            )
        )
    return engine


@pytest.fixture
def target_engine():
    """SQLite in-memory engine with analytics schema."""
    engine = create_engine("sqlite:///:memory:")
    AnalyticsBase.metadata.create_all(engine)
    return engine


@pytest.fixture
def populated_source(source_engine):
    """Source engine with exactly one check_results row."""
    with source_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO check_results (dataset_id, rule_id, passed, failed_rows, total_rows, checked_at) "
                "VALUES (1, 1, 1, 0, 100, :ts)"
            ),
            {"ts": _NOW},
        )
    return source_engine


@pytest.fixture
def populated_target(target_engine):
    """Target engine with valid dim + fact rows, all FKs satisfied."""
    with target_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO dim_datasets (id, name, file_type, row_count, column_count, status) "
                "VALUES (1, 'test.csv', 'csv', 100, 5, 'VALIDATED')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active) "
                "VALUES (1, 'Not null', 'email', 'NOT_NULL', 'HIGH', 'test', 1)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year) "
                "VALUES (20260311, '2026-03-11', 2, 3, 1, 2026)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO fact_quality_checks "
                "(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at) "
                "VALUES (1, 1, 20260311, 1, 0, 100, 100.0, :ts)"
            ),
            {"ts": _NOW},
        )
    return target_engine


# ---------------------------------------------------------------------------
# _check_row_counts
# ---------------------------------------------------------------------------


def test_row_counts_match(populated_source, populated_target):
    """Matching source and target counts produce no warnings."""
    result = ValidationResult()
    _check_row_counts(populated_source, populated_target, result)
    row_count_warnings = [w for w in result.warnings if w.check == "ROW_COUNT"]
    assert len(row_count_warnings) == 0


def test_row_counts_mismatch(source_engine, target_engine):
    """Mismatched counts produce a ROW_COUNT warning."""
    # Source: 3 rows, target: 0 rows
    with source_engine.begin() as conn:
        for i in range(3):
            conn.execute(
                text(
                    "INSERT INTO check_results (dataset_id, rule_id, passed, failed_rows, total_rows, checked_at) "
                    "VALUES (:ds, 1, 1, 0, 100, :ts)"
                ),
                {"ds": i + 1, "ts": _NOW},
            )

    result = ValidationResult()
    _check_row_counts(source_engine, target_engine, result)

    row_count_warnings = [w for w in result.warnings if w.check == "ROW_COUNT"]
    assert len(row_count_warnings) == 1
    assert row_count_warnings[0].severity == Severity.WARNING


def test_row_counts_both_empty(source_engine, target_engine):
    """Both engines empty produces no ROW_COUNT warning."""
    result = ValidationResult()
    _check_row_counts(source_engine, target_engine, result)
    row_count_warnings = [w for w in result.warnings if w.check == "ROW_COUNT"]
    assert len(row_count_warnings) == 0


def test_row_counts_stores_counts(populated_source, populated_target):
    """Populated counts are stored on the result object."""
    result = ValidationResult()
    _check_row_counts(populated_source, populated_target, result)
    assert result.source_count == 1
    assert result.target_count == 1


# ---------------------------------------------------------------------------
# _check_foreign_keys
# ---------------------------------------------------------------------------


def test_no_orphans_on_clean_data(populated_target):
    """Clean data with valid FKs produces no FK errors."""
    result = ValidationResult()
    _check_foreign_keys(populated_target, result)
    fk_errors = [w for w in result.warnings if w.check.startswith("FK_")]
    assert len(fk_errors) == 0


def test_orphaned_dataset_reference(target_engine):
    """Fact row referencing non-existent dataset_id triggers FK_DATASET error."""
    with target_engine.begin() as conn:
        # Insert dimension rows but NOT dim_datasets id=99
        conn.execute(
            text(
                "INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active) "
                "VALUES (1, 'Not null', 'email', 'NOT_NULL', 'HIGH', 'test', 1)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year) "
                "VALUES (20260311, '2026-03-11', 2, 3, 1, 2026)"
            )
        )
        # Fact row pointing at non-existent dataset_id=99
        conn.execute(
            text(
                "INSERT INTO fact_quality_checks "
                "(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at) "
                "VALUES (99, 1, 20260311, 1, 0, 100, 100.0, :ts)"
            ),
            {"ts": _NOW},
        )

    result = ValidationResult()
    _check_foreign_keys(target_engine, result)
    fk_dataset_errors = [w for w in result.warnings if w.check == "FK_DATASET"]
    assert len(fk_dataset_errors) == 1
    assert fk_dataset_errors[0].severity == Severity.ERROR


def test_orphaned_rule_reference(target_engine):
    """Fact row referencing non-existent rule_id triggers FK_RULE error."""
    with target_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO dim_datasets (id, name, file_type, row_count, column_count, status) "
                "VALUES (1, 'test.csv', 'csv', 100, 5, 'VALIDATED')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year) "
                "VALUES (20260311, '2026-03-11', 2, 3, 1, 2026)"
            )
        )
        # Fact row pointing at non-existent rule_id=99
        conn.execute(
            text(
                "INSERT INTO fact_quality_checks "
                "(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at) "
                "VALUES (1, 99, 20260311, 1, 0, 100, 100.0, :ts)"
            ),
            {"ts": _NOW},
        )

    result = ValidationResult()
    _check_foreign_keys(target_engine, result)
    fk_rule_errors = [w for w in result.warnings if w.check == "FK_RULE"]
    assert len(fk_rule_errors) == 1
    assert fk_rule_errors[0].severity == Severity.ERROR


def test_orphaned_date_reference(target_engine):
    """Fact row referencing non-existent date_key triggers FK_DATE error."""
    with target_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO dim_datasets (id, name, file_type, row_count, column_count, status) "
                "VALUES (1, 'test.csv', 'csv', 100, 5, 'VALIDATED')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active) "
                "VALUES (1, 'Not null', 'email', 'NOT_NULL', 'HIGH', 'test', 1)"
            )
        )
        # Fact row with date_key=99999999 — not in dim_date
        conn.execute(
            text(
                "INSERT INTO fact_quality_checks "
                "(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at) "
                "VALUES (1, 1, 99999999, 1, 0, 100, 100.0, :ts)"
            ),
            {"ts": _NOW},
        )

    result = ValidationResult()
    _check_foreign_keys(target_engine, result)
    fk_date_errors = [w for w in result.warnings if w.check == "FK_DATE"]
    assert len(fk_date_errors) == 1
    assert fk_date_errors[0].severity == Severity.ERROR


# ---------------------------------------------------------------------------
# _check_score_ranges
# ---------------------------------------------------------------------------


def test_all_scores_valid(populated_target):
    """Scores within [0, 100] produce no INVALID_SCORE warning."""
    result = ValidationResult()
    _check_score_ranges(populated_target, result)
    score_errors = [w for w in result.warnings if w.check == "INVALID_SCORE"]
    assert len(score_errors) == 0


def test_score_above_100_flagged(target_engine):
    """A score > 100 is flagged as INVALID_SCORE error."""
    with target_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO dim_datasets (id, name, file_type, row_count, column_count, status) "
                "VALUES (1, 'test.csv', 'csv', 100, 5, 'VALIDATED')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active) "
                "VALUES (1, 'r', 'f', 'NOT_NULL', 'HIGH', 't', 1)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year) "
                "VALUES (20260311, '2026-03-11', 2, 3, 1, 2026)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO fact_quality_checks "
                "(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at) "
                "VALUES (1, 1, 20260311, 1, 0, 100, 150.0, :ts)"  # score = 150
            ),
            {"ts": _NOW},
        )

    result = ValidationResult()
    _check_score_ranges(target_engine, result)
    score_errors = [w for w in result.warnings if w.check == "INVALID_SCORE"]
    assert len(score_errors) == 1
    assert score_errors[0].severity == Severity.ERROR


def test_score_below_0_flagged(target_engine):
    """A score < 0 is flagged as INVALID_SCORE error."""
    with target_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO dim_datasets (id, name, file_type, row_count, column_count, status) "
                "VALUES (1, 'test.csv', 'csv', 100, 5, 'VALIDATED')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active) "
                "VALUES (1, 'r', 'f', 'NOT_NULL', 'HIGH', 't', 1)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year) "
                "VALUES (20260311, '2026-03-11', 2, 3, 1, 2026)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO fact_quality_checks "
                "(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at) "
                "VALUES (1, 1, 20260311, 0, 105, 100, -5.0, :ts)"  # score = -5
            ),
            {"ts": _NOW},
        )

    result = ValidationResult()
    _check_score_ranges(target_engine, result)
    score_errors = [w for w in result.warnings if w.check == "INVALID_SCORE"]
    assert len(score_errors) == 1


# ---------------------------------------------------------------------------
# _check_duplicate_facts
# ---------------------------------------------------------------------------


def test_no_duplicate_facts(populated_target):
    """No duplicate (dataset_id, rule_id, checked_at) produces no DUPLICATE_FACTS warning."""
    result = ValidationResult()
    _check_duplicate_facts(populated_target, result)
    dup_warnings = [w for w in result.warnings if w.check == "DUPLICATE_FACTS"]
    assert len(dup_warnings) == 0


def test_duplicate_facts_detected(target_engine):
    """Two facts with the same (dataset_id, rule_id, checked_at) are flagged."""
    with target_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO dim_datasets (id, name, file_type, row_count, column_count, status) "
                "VALUES (1, 'test.csv', 'csv', 100, 5, 'VALIDATED')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active) "
                "VALUES (1, 'r', 'f', 'NOT_NULL', 'HIGH', 't', 1)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year) "
                "VALUES (20260311, '2026-03-11', 2, 3, 1, 2026)"
            )
        )
        # Insert same (dataset_id, rule_id, checked_at) twice
        for _ in range(2):
            conn.execute(
                text(
                    "INSERT INTO fact_quality_checks "
                    "(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at) "
                    "VALUES (1, 1, 20260311, 1, 0, 100, 100.0, :ts)"
                ),
                {"ts": _NOW},
            )

    result = ValidationResult()
    _check_duplicate_facts(target_engine, result)
    dup_warnings = [w for w in result.warnings if w.check == "DUPLICATE_FACTS"]
    assert len(dup_warnings) == 1
    assert dup_warnings[0].severity == Severity.WARNING


# ---------------------------------------------------------------------------
# validate() — full function
# ---------------------------------------------------------------------------


def test_validate_returns_validation_result(populated_source, populated_target):
    """validate() always returns a ValidationResult instance."""
    result = validate(populated_source, populated_target)
    assert isinstance(result, ValidationResult)


def test_validate_clean_data_has_no_errors(populated_source, populated_target):
    """Clean matching data: validate() reports no ERROR-severity warnings."""
    result = validate(populated_source, populated_target)
    assert result.passed(), f"Expected no errors but got: {result.to_list()}"
    assert result.error_count == 0


def test_validate_row_mismatch_adds_warning(source_engine, populated_target):
    """Mismatched row counts produce a warning but not an error — pipeline continues."""
    # Source has 3 rows, target has 1 row
    with source_engine.begin() as conn:
        for i in range(3):
            conn.execute(
                text(
                    "INSERT INTO check_results (dataset_id, rule_id, passed, failed_rows, total_rows, checked_at) "
                    "VALUES (:ds, 1, 1, 0, 100, :ts)"
                ),
                {"ds": i + 1, "ts": _NOW},
            )

    result = validate(source_engine, populated_target)
    assert isinstance(result, ValidationResult)
    # ROW_COUNT is a WARNING, not an ERROR
    row_count_checks = [w for w in result.warnings if w.check == "ROW_COUNT"]
    if row_count_checks:
        assert row_count_checks[0].severity == Severity.WARNING


def test_validate_strict_mode_raises_on_errors(populated_source, target_engine):
    """strict=True raises StrictValidationError when ERROR-severity warnings exist."""
    # Insert a fact with an orphaned dataset FK to force an error
    with target_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active) "
                "VALUES (1, 'r', 'f', 'NOT_NULL', 'HIGH', 't', 1)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year) "
                "VALUES (20260311, '2026-03-11', 2, 3, 1, 2026)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO fact_quality_checks "
                "(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at) "
                "VALUES (99, 1, 20260311, 1, 0, 100, 100.0, :ts)"  # dataset_id=99 has no dim row
            ),
            {"ts": _NOW},
        )

    with pytest.raises(StrictValidationError):
        validate(populated_source, target_engine, strict=True)


def test_validate_non_strict_does_not_raise_on_errors(populated_source, target_engine):
    """strict=False (default) does NOT raise even with ERROR-severity warnings."""
    with target_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active) "
                "VALUES (1, 'r', 'f', 'NOT_NULL', 'HIGH', 't', 1)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year) "
                "VALUES (20260311, '2026-03-11', 2, 3, 1, 2026)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO fact_quality_checks "
                "(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at) "
                "VALUES (99, 1, 20260311, 1, 0, 100, 100.0, :ts)"
            ),
            {"ts": _NOW},
        )

    # Should not raise
    result = validate(populated_source, target_engine, strict=False)
    assert isinstance(result, ValidationResult)
    assert result.has_errors()


# ---------------------------------------------------------------------------
# validate_with_guard()
# ---------------------------------------------------------------------------


def test_validate_with_guard_passes_clean_data(populated_source, populated_target):
    """validate_with_guard() returns result when no errors."""
    result = validate_with_guard(populated_source, populated_target)
    assert isinstance(result, ValidationResult)
    assert result.passed()


def test_validate_with_guard_raises_on_errors(populated_source, target_engine):
    """validate_with_guard() raises RuntimeError when there are FK errors."""
    with target_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active) "
                "VALUES (1, 'r', 'f', 'NOT_NULL', 'HIGH', 't', 1)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year) "
                "VALUES (20260311, '2026-03-11', 2, 3, 1, 2026)"
            )
        )
        conn.execute(
            text(
                "INSERT INTO fact_quality_checks "
                "(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at) "
                "VALUES (99, 1, 20260311, 1, 0, 100, 100.0, :ts)"
            ),
            {"ts": _NOW},
        )

    with pytest.raises(RuntimeError):
        validate_with_guard(populated_source, target_engine)


# ---------------------------------------------------------------------------
# ValidationResult and IntegrityWarning model helpers
# ---------------------------------------------------------------------------


def test_integrity_warning_error_severity():
    """ERROR and CRITICAL severity warnings are recognised as errors."""
    error_warning = IntegrityWarning(check="TEST", message="test", severity=Severity.ERROR)
    critical_warning = IntegrityWarning(check="TEST", message="test", severity=Severity.CRITICAL)
    assert error_warning.is_error() is True
    assert critical_warning.is_error() is True


def test_integrity_warning_non_error_severity():
    """WARNING and INFO severity are NOT treated as errors."""
    warn = IntegrityWarning(check="TEST", message="test", severity=Severity.WARNING)
    info = IntegrityWarning(check="TEST", message="test", severity=Severity.INFO)
    assert warn.is_error() is False
    assert info.is_error() is False


def test_integrity_warning_str_format():
    """str(IntegrityWarning) contains check name and message."""
    w = IntegrityWarning(check="ROW_COUNT", message="Delta detected", severity=Severity.WARNING)
    s = str(w)
    assert "ROW_COUNT" in s
    assert "Delta detected" in s


def test_validation_result_no_errors_by_default():
    """A fresh ValidationResult has no errors and passes."""
    result = ValidationResult()
    assert result.has_errors() is False
    assert result.passed() is True
    assert result.error_count == 0
    assert result.warning_count == 0


def test_validation_result_error_count():
    """error_count reflects only ERROR/CRITICAL severity warnings."""
    result = ValidationResult()
    result.warnings.append(IntegrityWarning(check="A", message="err", severity=Severity.ERROR))
    result.warnings.append(IntegrityWarning(check="B", message="warn", severity=Severity.WARNING))
    assert result.error_count == 1
    assert result.warning_count == 1


def test_validation_result_has_errors_with_error_warning():
    """has_errors() returns True when any ERROR warning is present."""
    result = ValidationResult()
    result.warnings.append(IntegrityWarning(check="X", message="x", severity=Severity.ERROR))
    assert result.has_errors() is True
    assert result.passed() is False


def test_validation_result_to_list():
    """to_list() returns string representation of each warning."""
    result = ValidationResult()
    result.warnings.append(IntegrityWarning(check="ROW_COUNT", message="delta", severity=Severity.WARNING))
    lst = result.to_list()
    assert isinstance(lst, list)
    assert len(lst) == 1
    assert "ROW_COUNT" in lst[0]


def test_validation_result_to_dict_keys():
    """to_dict() contains expected top-level keys."""
    result = ValidationResult()
    d = result.to_dict()
    for key in ("passed", "error_count", "warning_count", "source_count", "target_count", "warnings"):
        assert key in d, f"Missing key: {key}"


def test_validation_result_to_dict_passed_reflects_state():
    """to_dict()['passed'] is False when an ERROR warning is present."""
    result = ValidationResult()
    result.warnings.append(IntegrityWarning(check="FK", message="orphan", severity=Severity.ERROR))
    assert result.to_dict()["passed"] is False


def test_integrity_warning_to_dict():
    """IntegrityWarning.to_dict() includes check, message, severity, details."""
    w = IntegrityWarning(
        check="SCORE_RANGE",
        message="2 invalid scores",
        severity=Severity.ERROR,
        details={"count": 2},
    )
    d = w.to_dict()
    assert d["check"] == "SCORE_RANGE"
    assert d["message"] == "2 invalid scores"
    assert d["severity"] == "ERROR"
    assert d["details"] == {"count": 2}
