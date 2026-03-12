"""
ETL Pipeline Models and Type Definitions

This module contains all the dataclasses and type definitions used throughout
the ETL pipeline for type safety and better architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Mapping, Optional
import pandas as pd

# =============================================================================
# Enums
# =============================================================================


class Severity(Enum):
    """Severity levels for validation warnings/errors."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def __str__(self) -> str:
        return self.value


class ExtractionMode(Enum):
    """Extraction modes for the ETL pipeline."""

    FULL = "full"
    INCREMENTAL = "incremental"


# =============================================================================
# Schema Definitions
# =============================================================================


@dataclass(frozen=True)
class DimDatasetSchema:
    """Schema definition for dataset dimension."""

    id: str = "id"
    name: str = "name"
    file_type: str = "file_type"
    row_count: str = "row_count"
    column_count: str = "column_count"
    status: str = "status"
    uploaded_at: str = "uploaded_at"

    @property
    def columns(self) -> list[str]:
        return [self.id, self.name, self.file_type, self.row_count, self.column_count, self.status, self.uploaded_at]


@dataclass(frozen=True)
class DimRuleSchema:
    """Schema definition for rule dimension."""

    id: str = "id"
    name: str = "name"
    field_name: str = "field_name"
    rule_type: str = "rule_type"
    severity: str = "severity"
    dataset_type: str = "dataset_type"
    is_active: str = "is_active"

    @property
    def columns(self) -> list[str]:
        return [self.id, self.name, self.field_name, self.rule_type, self.severity, self.dataset_type, self.is_active]


@dataclass(frozen=True)
class DimDateSchema:
    """Schema definition for date dimension."""

    date_key: str = "date_key"
    full_date: str = "full_date"
    day_of_week: str = "day_of_week"
    month: str = "month"
    quarter: str = "quarter"
    year: str = "year"

    @property
    def columns(self) -> list[str]:
        return [self.date_key, self.full_date, self.day_of_week, self.month, self.quarter, self.year]


@dataclass(frozen=True)
class FactQualityCheckSchema:
    """Schema definition for quality check facts."""

    id: str = "id"
    dataset_id: str = "dataset_id"
    rule_id: str = "rule_id"
    date_key: str = "date_key"
    passed: str = "passed"
    failed_rows: str = "failed_rows"
    total_rows: str = "total_rows"
    score: str = "score"
    checked_at: str = "checked_at"

    @property
    def columns(self) -> list[str]:
        return [
            self.dataset_id,
            self.rule_id,
            self.date_key,
            self.passed,
            self.failed_rows,
            self.total_rows,
            self.score,
            self.checked_at,
        ]

    @property
    def dedup_columns(self) -> list[str]:
        """Columns used for deduplication."""
        return [self.dataset_id, self.rule_id, self.checked_at]


# Default schema instances
DIM_DATASET = DimDatasetSchema()
DIM_RULE = DimRuleSchema()
DIM_DATE = DimDateSchema()
FACT_QUALITY_CHECK = FactQualityCheckSchema()


# Column mappings from source to target
DIM_DATASET_MAPPING: dict[str, str] = {
    "dataset_id": "id",
    "dataset_name": "name",
    "file_type": "file_type",
    "dataset_row_count": "row_count",
    "column_count": "column_count",
    "dataset_status": "status",
    "uploaded_at": "uploaded_at",
}

DIM_RULE_MAPPING: dict[str, str] = {
    "rule_id": "id",
    "rule_name": "name",
    "field_name": "field_name",
    "rule_type": "rule_type",
    "severity": "severity",
    "dataset_type": "dataset_type",
    "is_active": "is_active",
}

REQUIRED_COLUMNS: list[str] = [
    "dataset_id",
    "rule_id",
    "total_rows",
    "checked_at",
]


# =============================================================================
# Transform Result Types
# =============================================================================


@dataclass
class TransformResult:
    """
    Container for all transformed DataFrames ready for loading.

    Provides type-safe access to dimension and fact tables.
    """

    dim_datasets: pd.DataFrame
    dim_rules: pd.DataFrame
    dim_date: pd.DataFrame
    facts: pd.DataFrame
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate all required DataFrames are present."""
        for name in ["dim_datasets", "dim_rules", "dim_date", "facts"]:
            df = getattr(self, name)
            if df is None:
                raise ValueError(f"TransformResult.{name} cannot be None")

    @property
    def total_records(self) -> int:
        """Total number of fact records."""
        return len(self.facts)

    @property
    def has_warnings(self) -> bool:
        """Check if there are any transformation warnings."""
        return len(self.warnings) > 0

    def to_dict(self) -> dict[str, pd.DataFrame]:
        """Legacy compatibility - convert to dictionary format."""
        return {
            "dim_datasets": self.dim_datasets,
            "dim_rules": self.dim_rules,
            "dim_date": self.dim_date,
            "facts": self.facts,
        }

    def __repr__(self) -> str:
        return (
            f"TransformResult(datasets={len(self.dim_datasets)}, "
            f"rules={len(self.dim_rules)}, dates={len(self.dim_date)}, "
            f"facts={len(self.facts)}, warnings={len(self.warnings)})"
        )


# =============================================================================
# Validation Types
# =============================================================================


@dataclass
class IntegrityWarning:
    """
    Represents a data integrity warning or error found during validation.
    """

    check: str
    message: str
    severity: Severity = Severity.WARNING
    details: Optional[dict[str, Any]] = field(default=None)

    def __str__(self) -> str:
        return f"[{self.severity}] [{self.check}] {self.message}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "message": self.message,
            "severity": self.severity.value,
            "details": self.details,
        }

    def is_error(self) -> bool:
        return self.severity in (Severity.ERROR, Severity.CRITICAL)


@dataclass
class DatasetValidationSummary:
    """Validation summary for a single dataset."""

    dataset_id: int
    dataset_name: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    avg_score: float
    min_score: float
    max_score: float

    @property
    def pass_rate(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return round(self.passed_checks / self.total_checks * 100, 2)


@dataclass
class RuleFailureSummary:
    """Failure summary for a single rule."""

    rule_id: int
    rule_name: str
    severity: str
    total_checks: int
    failure_count: int

    @property
    def failure_rate(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return round(self.failure_count / self.total_checks * 100, 2)


@dataclass
class SummaryStatistics:
    """Overall summary statistics for the ETL run."""

    total_records: int = 0
    passed_count: int = 0
    failed_count: int = 0
    success_rate: float = 0.0
    avg_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_records": self.total_records,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "success_rate": self.success_rate,
            "avg_score": self.avg_score,
            "min_score": self.min_score,
            "max_score": self.max_score,
        }


@dataclass
class ValidationResult:
    """
    Complete validation result including all warnings and summary statistics.
    """

    warnings: list[IntegrityWarning] = field(default_factory=list)
    source_count: int = 0
    target_count: int = 0
    statistics: Optional[SummaryStatistics] = None
    dataset_summaries: list[DatasetValidationSummary] = field(default_factory=list)
    rule_summaries: list[RuleFailureSummary] = field(default_factory=list)

    def has_errors(self) -> bool:
        """Check if any warnings are errors."""
        return any(w.is_error() for w in self.warnings)

    def passed(self) -> bool:
        """Check if validation passed (no errors)."""
        return not self.has_errors()

    @property
    def error_count(self) -> int:
        return sum(1 for w in self.warnings if w.is_error())

    @property
    def warning_count(self) -> int:
        return len(self.warnings) - self.error_count

    def to_list(self) -> list[str]:
        """Convert warnings to string list for backward compatibility."""
        return [str(w) for w in self.warnings]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed(),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "source_count": self.source_count,
            "target_count": self.target_count,
            "warnings": [w.to_dict() for w in self.warnings],
            "statistics": self.statistics.to_dict() if self.statistics else None,
        }


# =============================================================================
# Load Types
# =============================================================================


@dataclass
class LoadSummary:
    """Summary of records loaded during the ETL process."""

    dim_datasets: int = 0
    dim_rules: int = 0
    dim_date: int = 0
    fact_quality_checks: int = 0
    duplicates_removed: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "dim_datasets": self.dim_datasets,
            "dim_rules": self.dim_rules,
            "dim_date": self.dim_date,
            "fact_quality_checks": self.fact_quality_checks,
            "duplicates_removed": self.duplicates_removed,
        }

    @property
    def total_loaded(self) -> int:
        return self.dim_datasets + self.dim_rules + self.dim_date + self.fact_quality_checks


@dataclass
class UpsertConfig:
    """Configuration for upsert operations."""

    table: str
    columns: list[str]
    conflict_column: str
    update_on_conflict: bool = True


# =============================================================================
# Pipeline Result Types
# =============================================================================


@dataclass
class PipelineMetrics:
    """Detailed metrics from pipeline execution."""

    records_extracted: int = 0
    records_transformed: int = 0
    records_loaded: int = 0
    dimensions_loaded: dict[str, int] = field(default_factory=dict)
    extraction_duration: Optional[timedelta] = None
    transform_duration: Optional[timedelta] = None
    load_duration: Optional[timedelta] = None
    validate_duration: Optional[timedelta] = None
    duplicates_removed: int = 0


@dataclass
class PipelineResult:
    """Complete result from pipeline execution."""

    success: bool = False
    run_id: str = ""
    mode: str = "full"
    dry_run: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None
    metrics: PipelineMetrics = field(default_factory=PipelineMetrics)
    transform_warnings: list[str] = field(default_factory=list)
    validation_result: Optional[ValidationResult] = None
    error: Optional[str] = None

    @property
    def validation_passed(self) -> bool:
        if self.validation_result is None:
            return True
        return self.validation_result.passed()

    @property
    def warnings(self) -> list[str]:
        """Combined warnings from transform and validation."""
        result = list(self.transform_warnings)
        if self.validation_result:
            result.extend(self.validation_result.to_list())
        return result

    @property
    def summary(self) -> dict[str, int]:
        return self.metrics.dimensions_loaded

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "run_id": self.run_id,
            "mode": self.mode,
            "dry_run": self.dry_run,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": str(self.duration) if self.duration else None,
            "metrics": {
                "records_extracted": self.metrics.records_extracted,
                "records_transformed": self.metrics.records_transformed,
                "records_loaded": self.metrics.records_loaded,
                "duplicates_removed": self.metrics.duplicates_removed,
            },
            "validation_passed": self.validation_passed,
            "error": self.error,
        }


# =============================================================================
# Utility Functions
# =============================================================================


def utc_now() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def ensure_timezone_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware (defaults to UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
