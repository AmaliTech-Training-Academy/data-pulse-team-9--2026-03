# Load Module - ETL Pipeline

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Union
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from pipeline.utils.logging import get_logger
from pipeline.models import TransformResult, LoadSummary
from pipeline.sql_queries import LoadQueries
from infrastructure.db import AnalyticsBase
from infrastructure import models  # noqa: F401 - Required for table creation
from config import settings

logger = get_logger("load")

# Configuration
BATCH_SIZE: int = settings.get("etl", {}).get("batch_size", 1000)


class LoadError(Exception):
    """Raised when load operation fails."""

    pass


def _to_native(row: dict[str, Any]) -> dict[str, Any]:
    # Convert numpy/pandas types to native Python types for database insertion.

    result: dict[str, Any] = {}
    for k, v in row.items():
        if hasattr(v, "item"):
            # numpy scalar
            result[k] = v.item()
        elif isinstance(v, pd.Timestamp):
            # Ensure timezone-aware
            dt = v.to_pydatetime()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            result[k] = dt
        elif pd.isna(v):
            result[k] = None
        else:
            result[k] = v
    return result


def _validate_dataframe(df: Optional[pd.DataFrame], name: str) -> bool:
    # Validate DataFrame is non-empty before loading.

    if df is None or df.empty:
        logger.warning("Empty DataFrame for %s - skipping", name)
        return False
    return True


def _prepare_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    # Prepare DataFrame records for batch insertion.

    return [_to_native(row) for row in df.to_dict(orient="records")]


def _batch_execute(conn: Connection, stmt: Any, records: list[dict[str, Any]], batch_size: int, table_name: str) -> int:
    # Execute batch inserts efficiently.

    total: int = len(records)
    if total == 0:
        return 0

    batch_count: int = 0

    for i in range(0, total, batch_size):
        batch: list[dict] = records[i : i + batch_size]

        # Use executemany for batch execution (much faster than row-by-row)
        conn.execute(stmt, batch)

        batch_count += 1

        if batch_count % 10 == 0 or i + batch_size >= total:
            logger.debug(
                "Batch %d: inserted %d/%d records into %s", batch_count, min(i + batch_size, total), total, table_name
            )

    logger.info("Inserted %d rows into %s in %d batches", total, table_name, batch_count)
    return total


def _upsert_dim_datasets(conn: Connection, df: pd.DataFrame, is_sqlite: bool) -> int:
    # Upsert dataset dimension records.

    if not _validate_dataframe(df, "dim_datasets"):
        return 0

    sql = LoadQueries.upsert_dim_datasets(is_sqlite)
    stmt = text(sql)
    records = _prepare_records(df)

    return _batch_execute(conn, stmt, records, BATCH_SIZE, "dim_datasets")


def _upsert_dim_rules(conn: Connection, df: pd.DataFrame, is_sqlite: bool) -> int:
    # Upsert rule dimension records.

    if not _validate_dataframe(df, "dim_rules"):
        return 0

    sql = LoadQueries.upsert_dim_rules(is_sqlite)
    stmt = text(sql)
    records = _prepare_records(df)

    return _batch_execute(conn, stmt, records, BATCH_SIZE, "dim_rules")


def _upsert_dim_date(conn: Connection, df: pd.DataFrame, is_sqlite: bool) -> int:
    # Upsert date dimension records.

    if not _validate_dataframe(df, "dim_date"):
        return 0

    sql = LoadQueries.upsert_dim_date(is_sqlite)
    stmt = text(sql)
    records = _prepare_records(df)

    return _batch_execute(conn, stmt, records, BATCH_SIZE, "dim_date")


def _deduplicate_existing_facts(conn: Connection, is_sqlite: bool) -> int:
    # Remove duplicate facts from the fact table.
    # First count duplicates
    count_query = text(
        """
        SELECT COUNT(*) FROM (
            SELECT dataset_id, rule_id, checked_at
            FROM fact_quality_checks
            GROUP BY dataset_id, rule_id, checked_at
            HAVING COUNT(*) > 1
        ) dups
    """
    )

    dup_groups: int = conn.execute(count_query).scalar_one_or_none() or 0

    if dup_groups == 0:
        return 0

    # Perform deduplication
    dedup_sql = LoadQueries.deduplicate_facts(is_sqlite)
    result = conn.execute(text(dedup_sql))

    removed: int = result.rowcount if hasattr(result, "rowcount") else 0
    logger.info("Removed %d duplicate fact records", removed)

    return removed


def _insert_facts_with_dedup(conn: Connection, df: pd.DataFrame, is_sqlite: bool) -> tuple[int, int]:
    # Insert facts with deduplication check.

    if not _validate_dataframe(df, "fact_quality_checks"):
        return 0, 0

    # Prepare records (exclude 'id' column - auto-generated)
    fact_cols = ["dataset_id", "rule_id", "date_key", "passed", "failed_rows", "total_rows", "score", "checked_at"]

    df_insert = df[fact_cols].copy()
    records = _prepare_records(df_insert)

    stmt = text(LoadQueries.INSERT_FACT)

    inserted = _batch_execute(conn, stmt, records, BATCH_SIZE, "fact_quality_checks")

    # Post-load deduplication for idempotency
    duplicates_removed = _deduplicate_existing_facts(conn, is_sqlite)

    return inserted, duplicates_removed


def load(engine: Engine, transformed_data: Optional[Union[TransformResult, dict]]) -> LoadSummary:
    # Load transformed data into target database.

    if transformed_data is None:
        logger.warning("No transformed data to load")
        return LoadSummary()

    # Handle both TransformResult and dict (backward compatibility)
    if isinstance(transformed_data, TransformResult):
        dim_datasets = transformed_data.dim_datasets
        dim_rules = transformed_data.dim_rules
        dim_date = transformed_data.dim_date
        facts = transformed_data.facts
    else:
        # Dict access with .get() - legacy support
        dim_datasets = transformed_data.get("dim_datasets")
        dim_rules = transformed_data.get("dim_rules")
        dim_date = transformed_data.get("dim_date")
        facts = transformed_data.get("facts")

    # Ensure tables exist
    AnalyticsBase.metadata.create_all(engine)

    is_sqlite: bool = "sqlite" in engine.dialect.name

    summary = LoadSummary()

    with engine.begin() as conn:
        # Load dimensions first (foreign key targets)
        summary.dim_datasets = _upsert_dim_datasets(conn, dim_datasets, is_sqlite)
        summary.dim_rules = _upsert_dim_rules(conn, dim_rules, is_sqlite)
        summary.dim_date = _upsert_dim_date(conn, dim_date, is_sqlite)

        # Load facts with deduplication
        inserted, deduped = _insert_facts_with_dedup(conn, facts, is_sqlite)
        summary.fact_quality_checks = inserted
        summary.duplicates_removed = deduped

    logger.info("Load complete - %s", summary.to_dict())
    return summary


def load_incremental(
    engine: Engine, transformed_data: Optional[TransformResult], check_existing: bool = True
) -> LoadSummary:
    # Load data with stronger idempotency checking.

    if transformed_data is None:
        logger.warning("No transformed data to load")
        return LoadSummary()

    AnalyticsBase.metadata.create_all(engine)
    is_sqlite: bool = "sqlite" in engine.dialect.name

    summary = LoadSummary()

    with engine.begin() as conn:
        # Load dimensions
        summary.dim_datasets = _upsert_dim_datasets(conn, transformed_data.dim_datasets, is_sqlite)
        summary.dim_rules = _upsert_dim_rules(conn, transformed_data.dim_rules, is_sqlite)
        summary.dim_date = _upsert_dim_date(conn, transformed_data.dim_date, is_sqlite)

        # Load facts with existence check
        if check_existing:
            new_facts, skipped = _insert_new_facts_only(conn, transformed_data.facts, is_sqlite)
            summary.fact_quality_checks = new_facts
            if skipped > 0:
                logger.info("Skipped %d existing facts", skipped)
        else:
            inserted, deduped = _insert_facts_with_dedup(conn, transformed_data.facts, is_sqlite)
            summary.fact_quality_checks = inserted
            summary.duplicates_removed = deduped

    logger.info("Incremental load complete - %s", summary.to_dict())
    return summary


def _insert_new_facts_only(conn: Connection, df: pd.DataFrame, is_sqlite: bool) -> tuple[int, int]:
    # Insert only new facts (not already existing).

    if not _validate_dataframe(df, "fact_quality_checks"):
        return 0, 0

    fact_cols = ["dataset_id", "rule_id", "date_key", "passed", "failed_rows", "total_rows", "score", "checked_at"]

    check_stmt = text(LoadQueries.CHECK_FACT_EXISTS)
    insert_stmt = text(LoadQueries.INSERT_FACT)

    df_insert = df[fact_cols].copy()
    records = _prepare_records(df_insert)

    inserted: int = 0
    skipped: int = 0

    # Batch the existence checks
    for record in records:
        check_params = {
            "dataset_id": record["dataset_id"],
            "rule_id": record["rule_id"],
            "checked_at": record["checked_at"],
        }

        exists = conn.execute(check_stmt, check_params).scalar_one_or_none()

        if exists:
            skipped += 1
        else:
            conn.execute(insert_stmt, record)
            inserted += 1

    logger.info("Inserted %d new facts, skipped %d existing", inserted, skipped)

    return inserted, skipped
