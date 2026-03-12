# Validation Module - ETL Pipeline

from __future__ import annotations

from typing import Any, Mapping, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from pipeline.utils.logging import get_logger
from pipeline.models import (
    Severity,
    IntegrityWarning,
    ValidationResult,
    SummaryStatistics,
    DatasetValidationSummary,
    RuleFailureSummary,
)
from pipeline.sql_queries import ValidationQueries
from config import settings

logger = get_logger("validate")

# Configuration
MIN_SCORE: float = settings.get("validation", {}).get("min_score", 0.0)
MAX_SCORE: float = settings.get("validation", {}).get("max_score", 100.0)


class ValidationError(Exception):
    """Raised when validation encounters a critical error."""

    pass


class StrictValidationError(Exception):
    """Raised in strict mode when validation warnings exist."""

    pass


# Helper Functions for Validation Checks


def _check_row_counts(source_engine: Engine, target_engine: Engine, result: ValidationResult) -> None:
    # Check that source and target row counts match or are explainable.

    try:
        with source_engine.connect() as conn:
            source_result = conn.execute(text(ValidationQueries.SOURCE_COUNT)).scalar_one_or_none()
            result.source_count = source_result or 0
    except SQLAlchemyError as e:
        logger.error("Failed to get source count: %s", e)
        result.warnings.append(
            IntegrityWarning(
                check="SOURCE_COUNT",
                message=f"Could not retrieve source count: {e}",
                severity=Severity.ERROR,
            )
        )
        return

    try:
        with target_engine.connect() as conn:
            target_result = conn.execute(text(ValidationQueries.TARGET_FACT_COUNT)).scalar_one_or_none()
            result.target_count = target_result or 0
    except SQLAlchemyError as e:
        logger.error("Failed to get target count: %s", e)
        result.warnings.append(
            IntegrityWarning(
                check="TARGET_COUNT",
                message=f"Could not retrieve target count: {e}",
                severity=Severity.ERROR,
            )
        )
        return

    if result.source_count != result.target_count:
        result.warnings.append(
            IntegrityWarning(
                check="ROW_COUNT",
                message=(
                    f"Source: {result.source_count}, Target: {result.target_count}. "
                    "Delta may indicate multiple ETL runs or deduplication."
                ),
                severity=Severity.WARNING,
                details={
                    "source": result.source_count,
                    "target": result.target_count,
                    "delta": result.target_count - result.source_count,
                },
            )
        )
    else:
        logger.info("Row counts match: %d", result.source_count)


def _check_foreign_keys(target_engine: Engine, result: ValidationResult) -> None:
    # Check for orphaned foreign key references in fact table.

    fk_checks = [
        ("FK_DATASET", ValidationQueries.ORPHANED_DATASETS, "dataset"),
        ("FK_RULE", ValidationQueries.ORPHANED_RULES, "rule"),
        ("FK_DATE", ValidationQueries.ORPHANED_DATES, "date"),
    ]

    for check_name, query, entity_name in fk_checks:
        try:
            with target_engine.connect() as conn:
                orphaned_count: int = conn.execute(text(query)).scalar_one_or_none() or 0

            if orphaned_count > 0:
                result.warnings.append(
                    IntegrityWarning(
                        check=check_name,
                        message=f"{orphaned_count} orphaned {entity_name} references",
                        severity=Severity.ERROR,
                        details={"count": orphaned_count, "entity": entity_name},
                    )
                )
        except SQLAlchemyError as e:
            logger.error("Failed to check %s foreign keys: %s", entity_name, e)
            result.warnings.append(
                IntegrityWarning(
                    check=check_name,
                    message=f"Could not check {entity_name} references: {e}",
                    severity=Severity.ERROR,
                )
            )


def _check_score_ranges(target_engine: Engine, result: ValidationResult) -> None:
    # Check for scores outside valid range.

    try:
        with target_engine.connect() as conn:
            invalid_count: int = (
                conn.execute(
                    text(ValidationQueries.INVALID_SCORES), {"min_score": MIN_SCORE, "max_score": MAX_SCORE}
                ).scalar_one_or_none()
                or 0
            )

        if invalid_count > 0:
            result.warnings.append(
                IntegrityWarning(
                    check="INVALID_SCORE",
                    message=f"{invalid_count} scores outside [{MIN_SCORE}, {MAX_SCORE}]",
                    severity=Severity.ERROR,
                    details={
                        "count": invalid_count,
                        "min_allowed": MIN_SCORE,
                        "max_allowed": MAX_SCORE,
                    },
                )
            )
        else:
            logger.info("All scores within valid range [%.1f, %.1f]", MIN_SCORE, MAX_SCORE)

    except SQLAlchemyError as e:
        logger.error("Failed to check score ranges: %s", e)
        result.warnings.append(
            IntegrityWarning(
                check="SCORE_RANGE",
                message=f"Could not check score ranges: {e}",
                severity=Severity.ERROR,
            )
        )


def _check_duplicate_facts(target_engine: Engine, result: ValidationResult) -> None:
    # Check for duplicate facts in target table.

    try:
        with target_engine.connect() as conn:
            dup_count: int = conn.execute(text(ValidationQueries.DUPLICATE_FACTS)).scalar_one_or_none() or 0

        if dup_count > 0:
            result.warnings.append(
                IntegrityWarning(
                    check="DUPLICATE_FACTS",
                    message=f"{dup_count} duplicate fact groups detected",
                    severity=Severity.WARNING,
                    details={"duplicate_groups": dup_count},
                )
            )
        else:
            logger.info("No duplicate facts detected")

    except SQLAlchemyError as e:
        logger.warning("Could not check for duplicates: %s", e)
        # Non-critical, just log


def _gather_summary_statistics(target_engine: Engine, result: ValidationResult) -> None:
    # Gather summary statistics from the fact table.

    try:
        with target_engine.connect() as conn:
            row: Optional[Mapping[str, Any]] = (
                conn.execute(text(ValidationQueries.SUMMARY_STATISTICS)).mappings().fetchone()
            )

        if row is None:
            logger.warning("No summary statistics available (empty fact table)")
            return

        result.statistics = SummaryStatistics(
            total_records=row.get("total_records") or 0,
            passed_count=row.get("passed_count") or 0,
            failed_count=row.get("failed_count") or 0,
            success_rate=row.get("success_rate") or 0.0,
            avg_score=row.get("avg_score") or 0.0,
            min_score=row.get("min_score") or 0.0,
            max_score=row.get("max_score") or 100.0,
        )

        logger.info(
            "Summary stats: %d total, %.1f%% success rate, avg score %.2f",
            result.statistics.total_records,
            result.statistics.success_rate,
            result.statistics.avg_score,
        )

    except SQLAlchemyError as e:
        logger.warning("Could not gather summary statistics: %s", e)


def _gather_dataset_summaries(target_engine: Engine, result: ValidationResult) -> None:
    # Gather validation summaries grouped by dataset.

    try:
        with target_engine.connect() as conn:
            rows = conn.execute(text(ValidationQueries.DATASET_SUMMARY)).mappings().fetchall()

        for row in rows:
            summary = DatasetValidationSummary(
                dataset_id=row.get("dataset_id"),
                dataset_name=row.get("dataset_name") or "Unknown",
                total_checks=row.get("total_checks") or 0,
                passed_checks=row.get("passed_checks") or 0,
                failed_checks=row.get("failed_checks") or 0,
                avg_score=row.get("avg_score") or 0.0,
                min_score=row.get("min_score") or 0.0,
                max_score=row.get("max_score") or 100.0,
            )
            result.dataset_summaries.append(summary)

        logger.info("Gathered validation summaries for %d datasets", len(result.dataset_summaries))

    except SQLAlchemyError as e:
        logger.warning("Could not gather dataset summaries: %s", e)


def _gather_rule_summaries(target_engine: Engine, result: ValidationResult) -> None:
    # Gather failure summaries grouped by rule.

    try:
        with target_engine.connect() as conn:
            rows = conn.execute(text(ValidationQueries.RULE_FAILURE_SUMMARY)).mappings().fetchall()

        for row in rows:
            summary = RuleFailureSummary(
                rule_id=row.get("rule_id"),
                rule_name=row.get("rule_name") or "Unknown",
                severity=row.get("severity") or "UNKNOWN",
                total_checks=row.get("total_checks") or 0,
                failure_count=row.get("failure_count") or 0,
            )
            result.rule_summaries.append(summary)

        # Log rules with high failure rates
        high_failure_rules = [r for r in result.rule_summaries if r.failure_rate > 50]
        if high_failure_rules:
            logger.warning("%d rules have failure rate > 50%%", len(high_failure_rules))

    except SQLAlchemyError as e:
        logger.warning("Could not gather rule summaries: %s", e)


# Main Validation Function


def validate(
    source_engine: Engine, target_engine: Engine, strict: bool = False, include_summaries: bool = True
) -> ValidationResult:
    # Perform post-load validation checks.

    logger.info("Starting post-load validation")

    result = ValidationResult()

    # Run all validation checks
    _check_row_counts(source_engine, target_engine, result)
    _check_foreign_keys(target_engine, result)
    _check_score_ranges(target_engine, result)
    _check_duplicate_facts(target_engine, result)

    # Gather statistics and summaries
    _gather_summary_statistics(target_engine, result)

    if include_summaries:
        _gather_dataset_summaries(target_engine, result)
        _gather_rule_summaries(target_engine, result)

    # Log results
    if result.warnings:
        for w in result.warnings:
            if w.is_error():
                logger.error(str(w))
            else:
                logger.warning(str(w))

        logger.warning(
            "Validation finished with %d error(s) and %d warning(s)",
            result.error_count,
            result.warning_count,
        )
    else:
        logger.info("Validation passed - no issues found")

    # Strict mode check
    if strict and result.has_errors():
        raise StrictValidationError(
            f"Validation failed with {result.error_count} error(s). "
            f"Errors: {[str(w) for w in result.warnings if w.is_error()]}"
        )

    return result


def validate_with_guard(source_engine: Engine, target_engine: Engine, strict: bool = False) -> ValidationResult:
    # Validate and raise RuntimeError if critical errors exist.

    result = validate(source_engine, target_engine, strict=strict)

    if result.has_errors():
        error_messages = [str(w) for w in result.warnings if w.is_error()]
        raise RuntimeError(
            f"Pipeline validation failed with {result.error_count} critical error(s): " f"{error_messages}"
        )

    return result
