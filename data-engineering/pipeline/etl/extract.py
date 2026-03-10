"""
Extract Module - ETL Pipeline

Handles data extraction from source database with:
- High watermark tracking for incremental loads
- Query timeout protection
- Exponential backoff retry logic
- Chunked extraction for memory efficiency
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Generator, Optional
import random
import time

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError, TimeoutError as SATimeoutError

from pipeline.utils.logging import get_logger
from pipeline.sql_queries import ExtractQueries
from config import settings

logger = get_logger("extract")

# Configuration with defaults
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 5.0
DEFAULT_RETRY_MAX_DELAY = 60.0
DEFAULT_RETRY_MULTIPLIER = 2.0
DEFAULT_QUERY_TIMEOUT = 300  # 5 minutes
DEFAULT_BATCH_SIZE = 1000


class ExtractionError(Exception):
    """Raised when extraction fails after all retry attempts."""

    pass


class ExtractionConfig:
    """Configuration for extraction operations."""

    def __init__(self):
        etl_config = settings.get("etl", {})
        self.retry_attempts: int = etl_config.get("retry_attempts", DEFAULT_RETRY_ATTEMPTS)
        self.retry_delay: float = etl_config.get("retry_delay_seconds", DEFAULT_RETRY_DELAY)
        self.retry_max_delay: float = etl_config.get("retry_max_delay_seconds", DEFAULT_RETRY_MAX_DELAY)
        self.retry_multiplier: float = etl_config.get("retry_multiplier", DEFAULT_RETRY_MULTIPLIER)
        self.query_timeout: int = etl_config.get("query_timeout_seconds", DEFAULT_QUERY_TIMEOUT)
        self.batch_size: int = etl_config.get("batch_size", DEFAULT_BATCH_SIZE)
        # Random seed for reproducibility in tests
        self.random_seed: Optional[int] = etl_config.get("random_seed")


def _get_config() -> ExtractionConfig:
    """Get extraction configuration with defaults."""
    return ExtractionConfig()


def _build_query(mode: str, last_run: Optional[datetime]) -> tuple[str, dict]:
    # Build extraction query based on mode.

    if mode == "incremental" and last_run is not None:
        query = ExtractQueries.BASE_QUERY + ExtractQueries.INCREMENTAL_FILTER
        return query, {"last_run": last_run}
    return ExtractQueries.BASE_QUERY, {}


def _calculate_backoff_delay(
    attempt: int, base_delay: float, max_delay: float, multiplier: float, seed: Optional[int] = None
) -> float:
    # Calculate exponential backoff delay with jitter.

    if seed is not None:
        random.seed(seed + attempt)

    # Exponential backoff: delay = base * (multiplier ^ (attempt - 1))
    delay = base_delay * (multiplier ** (attempt - 1))

    # Add jitter (±25%)
    jitter = delay * 0.25 * (2 * random.random() - 1)
    delay = delay + jitter

    # Cap at max delay
    return min(delay, max_delay)


def _retry_with_backoff(func, config: ExtractionConfig, operation_name: str = "operation"):
    # Execute function with exponential backoff retry.

    last_error: Optional[Exception] = None

    for attempt in range(1, config.retry_attempts + 1):
        try:
            return func()
        except (OperationalError, SATimeoutError, ConnectionError) as e:
            last_error = e

            if attempt < config.retry_attempts:
                delay = _calculate_backoff_delay(
                    attempt=attempt,
                    base_delay=config.retry_delay,
                    max_delay=config.retry_max_delay,
                    multiplier=config.retry_multiplier,
                    seed=config.random_seed,
                )
                logger.warning(
                    "%s attempt %d/%d failed, retrying in %.2fs: %s",
                    operation_name,
                    attempt,
                    config.retry_attempts,
                    delay,
                    e,
                )
                time.sleep(delay)
            else:
                logger.error("%s failed after %d attempts: %s", operation_name, config.retry_attempts, e)

    raise ExtractionError(
        f"{operation_name} failed after {config.retry_attempts} attempts: {last_error}"
    ) from last_error


def get_high_watermark(engine: Engine) -> Optional[datetime]:
    """
    Get the high watermark (latest checked_at) from source table.

    Used for incremental load tracking.
    """

    config = _get_config()

    def do_query():
        with engine.connect() as conn:
            result = conn.execute(
                text(ExtractQueries.WATERMARK).execution_options(timeout=config.query_timeout)
            ).scalar_one_or_none()

            if result is not None:
                # Ensure timezone-aware
                if isinstance(result, datetime) and result.tzinfo is None:
                    result = result.replace(tzinfo=timezone.utc)
            return result

    try:
        watermark = _retry_with_backoff(do_query, config, "Watermark query")
        logger.info("High watermark: %s", watermark)
        return watermark
    except ExtractionError:
        logger.warning("Could not retrieve high watermark, defaulting to None")
        return None


def get_record_count(engine: Engine, mode: str = "full", last_run: Optional[datetime] = None) -> int:
    # Get record count for extraction planning.

    config = _get_config()

    if mode == "incremental" and last_run is not None:
        count_query = ExtractQueries.COUNT_INCREMENTAL
        params: dict = {"last_run": last_run}
    else:
        count_query = ExtractQueries.COUNT_FULL
        params = {}

    def do_count():
        with engine.connect() as conn:
            result = conn.execute(
                text(count_query).execution_options(timeout=config.query_timeout), params
            ).scalar_one_or_none()
            return result or 0

    try:
        count: int = _retry_with_backoff(do_count, config, "Count query")
        return count
    except ExtractionError:
        logger.warning("Could not get record count, returning 0")
        return 0


def extract(engine: Engine, mode: str = "full", last_run: Optional[datetime] = None) -> pd.DataFrame:
    """
    Full extraction - loads all records into memory.

    Use extract_chunked() for large datasets to avoid memory issues.
    """

    config = _get_config()

    logger.info("Extracting all data into memory - Mode: %s", mode)

    query_str, params = _build_query(mode, last_run)

    def do_extract():
        with engine.connect() as conn:
            # Set statement timeout for query protection
            return pd.read_sql(text(query_str).execution_options(timeout=config.query_timeout), conn, params=params)

    try:
        df: pd.DataFrame = _retry_with_backoff(do_extract, config, "Full extraction")
        logger.info("Extracted %d records (full load)", len(df))
        return df

    except SQLAlchemyError as e:
        logger.error("Query execution failed: %s", e)
        raise ExtractionError(f"Extraction query failed: {e}") from e


def extract_chunked(
    engine: Engine, mode: str = "full", last_run: Optional[datetime] = None, chunk_size: Optional[int] = None
) -> Generator[pd.DataFrame, None, None]:
    # Chunked extraction - yields DataFrames in batches for memory efficiency.

    config = _get_config()
    chunk_size = chunk_size or config.batch_size

    # Get expected count for progress logging
    expected_count = get_record_count(engine, mode, last_run)
    expected_chunks = (expected_count + chunk_size - 1) // chunk_size if expected_count > 0 else 0

    logger.info(
        "Starting chunked extraction - ~%d records in ~%d chunks of %d", expected_count, expected_chunks, chunk_size
    )

    query_str, params = _build_query(mode, last_run)

    def get_chunk_iterator():
        with engine.connect() as conn:
            return pd.read_sql(
                text(query_str).execution_options(timeout=config.query_timeout),
                conn,
                params=params,
                chunksize=chunk_size,
            )

    try:
        chunk_iter = _retry_with_backoff(get_chunk_iterator, config, "Chunk iterator creation")

        total_records: int = 0
        chunk_num: int = 0

        for chunk in chunk_iter:
            chunk_num += 1
            total_records += len(chunk)
            logger.info(
                "Yielding chunk %d/%d (%d records, %d total)", chunk_num, expected_chunks, len(chunk), total_records
            )
            yield chunk

        logger.info("Chunked extraction complete - %d chunks, %d total records", chunk_num, total_records)

    except SQLAlchemyError as e:
        logger.error("Chunked extraction failed: %s", e)
        raise ExtractionError(f"Chunked extraction failed: {e}") from e


def extract_with_watermark(
    engine: Engine, stored_watermark: Optional[datetime] = None, chunk_size: Optional[int] = None
) -> tuple[Generator[pd.DataFrame, None, None], Optional[datetime]]:
    # Extract with automatic watermark tracking.

    current_watermark = get_high_watermark(engine)

    # Recovery path: if stored watermark is ahead of source max timestamp,
    # fall back to a full extraction to avoid permanently skipping data.
    if stored_watermark is not None and current_watermark is not None and stored_watermark > current_watermark:
        logger.warning(
            "Stored watermark (%s) is ahead of source watermark (%s). " "Resetting to full extraction.",
            stored_watermark,
            current_watermark,
        )
        stored_watermark = None

    mode = "incremental" if stored_watermark else "full"

    logger.info("Watermark extraction - Mode: %s, Stored: %s, Current: %s", mode, stored_watermark, current_watermark)

    generator = extract_chunked(engine=engine, mode=mode, last_run=stored_watermark, chunk_size=chunk_size)

    return generator, current_watermark
