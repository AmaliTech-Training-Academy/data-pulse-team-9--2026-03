# Transform Module - ETL Pipeline

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import numpy as np
import pandas as pd

from pipeline.utils.logging import get_logger
from pipeline.models import (
    TransformResult,
    DIM_DATASET_MAPPING,
    DIM_RULE_MAPPING,
    REQUIRED_COLUMNS,
    DIM_DATASET,
    DIM_RULE,
    DIM_DATE,
    FACT_QUALITY_CHECK,
)

logger = get_logger("transform")


class ValidationError(Exception):
    """Raised when data validation fails during transformation."""

    pass


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""

    pass


def _validate_schema(df: pd.DataFrame, expected_columns: list[str], name: str) -> list[str]:
    #  Validate DataFrame schema against expected columns.

    warnings: list[str] = []

    missing = set(expected_columns) - set(df.columns)
    if missing:
        raise SchemaValidationError(f"{name}: Missing required columns: {missing}")

    # Check for extra columns (informational)
    extra = set(df.columns) - set(expected_columns)
    if extra:
        warnings.append(f"{name}: Extra columns present (will be ignored): {extra}")

    return warnings


def _validate_raw_data(df: pd.DataFrame) -> list[str]:
    # Validate raw extraction data before transformation.

    warnings: list[str] = []

    if df is None or df.empty:
        raise ValidationError("Input DataFrame is empty")

    # Check required columns
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise SchemaValidationError(f"Missing required columns: {missing}")

    # Check for null values in required columns
    for col in REQUIRED_COLUMNS:
        null_count: int = df[col].isnull().sum()
        if null_count > 0:
            warnings.append(f"Column '{col}' has {null_count} null values")
            logger.warning("Column '%s' has %d null values", col, null_count)

    # Check for invalid total_rows values
    invalid_count: int = (df["total_rows"] <= 0).sum()
    if invalid_count > 0:
        warnings.append(f"{invalid_count} records have total_rows <= 0")
        logger.warning("%d records have total_rows <= 0", invalid_count)

    # Check for duplicate check results
    dup_count: int = df.duplicated(subset=["dataset_id", "rule_id", "checked_at"]).sum()
    if dup_count > 0:
        warnings.append(f"{dup_count} duplicate check results found")
        logger.warning("%d duplicate check results (same dataset_id, rule_id, checked_at)", dup_count)

    return warnings


def _ensure_timezone_aware(series: pd.Series) -> pd.Series:
    # Ensure datetime series is timezone-aware (UTC).

    if series.dt.tz is None:
        return series.dt.tz_localize(timezone.utc)
    return series.dt.tz_convert(timezone.utc)


def transform(raw_data: pd.DataFrame) -> Optional[TransformResult]:
    # Transform raw extraction data into dimensional model.

    if raw_data is None or raw_data.empty:
        logger.warning("No data to transform")
        return None

    # Validate input data
    all_warnings: list[str] = _validate_raw_data(raw_data)

    logger.info("Transforming %d raw records", len(raw_data))

    # Parse checked_at once for reuse (fix computed twice issue)
    checked_at_parsed: pd.Series = pd.to_datetime(raw_data["checked_at"], errors="coerce")
    checked_at_parsed = _ensure_timezone_aware(checked_at_parsed)

    # Build dimensions and facts
    dim_datasets: pd.DataFrame = _build_dim_datasets(raw_data)
    dim_rules: pd.DataFrame = _build_dim_rules(raw_data)
    dim_date: pd.DataFrame = _build_dim_date(checked_at_parsed)
    facts: pd.DataFrame = _build_facts(raw_data, checked_at_parsed)

    # Validate fact date_key against dim_date
    date_key_warnings = _validate_date_keys(facts, dim_date)
    all_warnings.extend(date_key_warnings)

    result = TransformResult(
        dim_datasets=dim_datasets,
        dim_rules=dim_rules,
        dim_date=dim_date,
        facts=facts,
        warnings=all_warnings,
    )

    logger.info("Transform complete - %s", result)

    if all_warnings:
        logger.warning("Transform completed with %d warnings", len(all_warnings))

    return result


def _build_dim_datasets(df: pd.DataFrame) -> pd.DataFrame:
    # Build dataset dimension table.

    cols: list[str] = list(DIM_DATASET_MAPPING.keys())
    dim: pd.DataFrame = df[cols].drop_duplicates(subset=["dataset_id"]).copy()
    dim.rename(columns=DIM_DATASET_MAPPING, inplace=True)

    # Ensure timezone-aware uploaded_at
    if "uploaded_at" in dim.columns:
        dim["uploaded_at"] = pd.to_datetime(dim["uploaded_at"], errors="coerce")
        if dim["uploaded_at"].dt.tz is None:
            dim["uploaded_at"] = dim["uploaded_at"].dt.tz_localize(timezone.utc)

    return dim.reset_index(drop=True)


def _build_dim_rules(df: pd.DataFrame) -> pd.DataFrame:
    # Build rule dimension table.

    cols: list[str] = list(DIM_RULE_MAPPING.keys())
    dim: pd.DataFrame = df[cols].drop_duplicates(subset=["rule_id"]).copy()
    dim.rename(columns=DIM_RULE_MAPPING, inplace=True)
    # Convert SQLite integer (0/1) to Python boolean for Postgres compatibility
    if "is_active" in dim.columns:
        dim["is_active"] = dim["is_active"].astype(bool)
    return dim.reset_index(drop=True)


def _build_dim_date(checked_at: pd.Series) -> pd.DataFrame:
    # Build date dimension table.

    try:
        valid_dates: pd.Series = checked_at.dropna()

        if valid_dates.empty:
            logger.warning("No valid dates found in checked_at column")
            return pd.DataFrame(columns=DIM_DATE.columns)

        min_date: datetime = valid_dates.min()
        max_date: datetime = valid_dates.max()

        # Normalize to date boundaries
        date_range: pd.DatetimeIndex = pd.date_range(
            start=min_date.normalize(), end=max_date.normalize(), freq="D", tz=timezone.utc
        )

        dim: pd.DataFrame = pd.DataFrame(
            {
                DIM_DATE.date_key: (date_range.year * 10000 + date_range.month * 100 + date_range.day).astype(int),
                DIM_DATE.full_date: date_range.date,
                DIM_DATE.day_of_week: date_range.dayofweek.astype(int),
                DIM_DATE.month: date_range.month.astype(int),
                DIM_DATE.quarter: date_range.quarter.astype(int),
                DIM_DATE.year: date_range.year.astype(int),
            }
        )

        return dim

    except Exception as e:
        logger.error("Failed to build date dimension: %s", e)
        raise ValidationError(f"Date dimension build failed: {e}") from e


def _build_facts(df: pd.DataFrame, checked_at: pd.Series) -> pd.DataFrame:
    # Build fact table with quality check results.

    facts: pd.DataFrame = df[
        ["id", "dataset_id", "rule_id", "passed", "failed_rows", "total_rows", "checked_at"]
    ].copy()

    # Convert SQLite integer (0/1) to Python boolean for Postgres compatibility
    facts["passed"] = facts["passed"].astype(bool)

    # Calculate quality score
    total_rows: np.ndarray = facts["total_rows"].values
    failed_rows: np.ndarray = facts["failed_rows"].values

    with np.errstate(divide="ignore", invalid="ignore"):
        score: np.ndarray = np.where(total_rows > 0, np.round((total_rows - failed_rows) / total_rows * 100, 2), 0.0)
    facts["score"] = score

    # Calculate date_key from pre-parsed checked_at (no double computation)
    facts["date_key"] = (
        (checked_at.dt.year * 10000 + checked_at.dt.month * 100 + checked_at.dt.day).fillna(0).astype(int)
    )

    # Store timezone-aware checked_at
    facts["checked_at"] = checked_at

    # Deduplicate facts (same dataset_id, rule_id, checked_at)
    initial_count: int = len(facts)
    facts = facts.drop_duplicates(
        subset=["dataset_id", "rule_id", "checked_at"], keep="last"  # Keep most recent in case of duplicates
    )
    dedup_count: int = initial_count - len(facts)

    if dedup_count > 0:
        logger.info("Removed %d duplicate facts during transformation", dedup_count)

    return facts.reset_index(drop=True)


def _validate_date_keys(facts: pd.DataFrame, dim_date: pd.DataFrame) -> list[str]:
    # Validate that all fact date_keys exist in dim_date.

    warnings: list[str] = []

    if dim_date.empty:
        return warnings

    fact_keys: set = set(facts["date_key"].unique())
    dim_keys: set = set(dim_date["date_key"].unique())

    # Check for invalid date_keys (0 indicates NULL date)
    invalid_keys: int = (facts["date_key"] == 0).sum()
    if invalid_keys > 0:
        warnings.append(f"{invalid_keys} facts have invalid date_key (NULL checked_at)")
        logger.warning("%d facts have invalid date_key (NULL checked_at)", invalid_keys)

    # Check for orphaned date_keys (excluding 0)
    orphaned: set = (fact_keys - dim_keys) - {0}
    if orphaned:
        warnings.append(f"{len(orphaned)} date_keys in facts not found in dim_date: {orphaned}")
        logger.warning("%d date_keys in facts not found in dim_date", len(orphaned))

    return warnings
