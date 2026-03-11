# Pipeline Orchestration Module

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import json
import re
import uuid

import pandas as pd

from infrastructure.db import get_source_engine, get_target_engine
from pipeline.utils.logging import get_logger
from pipeline.models import (
    PipelineResult,
    PipelineMetrics,
    TransformResult,
    ValidationResult,
)
from pipeline.etl.extract import (
    extract_chunked,
    extract_with_watermark,
    ExtractionError,
)
from pipeline.etl.transform import transform, ValidationError
from pipeline.etl.load import load, LoadSummary
from pipeline.etl.validate import validate, validate_with_guard, StrictValidationError

logger = get_logger("pipeline")

STATE_FILE = Path(__file__).parent.parent.parent / "logs" / "pipeline_state.json"


def _generate_run_id() -> str:
    """Generate unique run ID."""
    return f"run-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


def _mask_connection_string(conn_str: str) -> str:
    """Mask password in DB connection string for safe logging."""
    pattern = r"(?P<pre>.*://)(?P<user>[^:@]+)(:(?P<pwd>[^@]+))?@(?P<post>.*)"
    match = re.match(pattern, conn_str)
    if not match:
        return conn_str
    groups = match.groupdict()
    masked = "***" if groups.get("pwd") else ""
    return f"{groups['pre']}{groups['user']}:{masked}@{groups['post']}"


def _utc_now() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def _load_state() -> dict:
    """Load pipeline state from file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Could not load state file: %s", e)
    return {}


def _save_state(state: dict) -> None:
    """Save pipeline state to file."""
    STATE_FILE.parent.mkdir(exist_ok=True)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)
    except IOError as e:
        logger.error("Could not save state file: %s", e)


def _parse_watermark(watermark_str: Optional[str]) -> Optional[datetime]:
    """Parse watermark string to timezone-aware datetime."""
    if not watermark_str:
        return None
    try:
        dt = datetime.fromisoformat(watermark_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def run(mode: str = "full", dry_run: bool = False, strict: bool = False, use_watermark: bool = True) -> PipelineResult:
    # Execute the ETL pipeline.

    run_id = _generate_run_id()
    start = _utc_now()

    result = PipelineResult(
        run_id=run_id,
        mode=mode,
        dry_run=dry_run,
        start_time=start,
        metrics=PipelineMetrics(),
    )

    logger.info("=" * 60)
    logger.info("ETL pipeline started - Run: %s, Mode: %s, Dry run: %s", run_id, mode, dry_run)
    logger.info("=" * 60)

    try:
        source = get_source_engine()
        target = get_target_engine()

        # Log connection info (masked)
        logger.debug("Source: %s", _mask_connection_string(str(source.url)))
        logger.debug("Target: %s", _mask_connection_string(str(target.url)))

        state = _load_state()

        # Determine watermark for incremental loads
        stored_watermark: Optional[datetime] = None
        new_watermark: Optional[datetime] = None

        if mode == "incremental" and use_watermark:
            stored_watermark = _parse_watermark(state.get("high_watermark"))
            logger.info("Stored watermark: %s", stored_watermark)

        # Step 1: Extract
        step_start = _utc_now()
        logger.info("Step 1/4: Extract (chunked)")

        if use_watermark:
            incremental_watermark = stored_watermark if mode == "incremental" else None
            chunk_gen, new_watermark = extract_with_watermark(
                source,
                stored_watermark=incremental_watermark,
            )
            chunks = list(chunk_gen)
        else:
            chunks = list(extract_chunked(source, mode=mode, last_run=stored_watermark))
            new_watermark = None

        result.metrics.extraction_duration = _utc_now() - step_start

        if not chunks:
            logger.warning("No data extracted - pipeline stopping")
            result.success = True
            result.transform_warnings.append("No data to process")
            return result

        raw: pd.DataFrame = pd.concat(chunks, ignore_index=True)
        result.metrics.records_extracted = len(raw)
        logger.info("Extracted %d records", len(raw))

        # Step 2: Transform
        step_start = _utc_now()
        logger.info("Step 2/4: Transform")

        transformed: Optional[TransformResult] = transform(raw)
        result.metrics.transform_duration = _utc_now() - step_start

        if transformed is None:
            logger.warning("No data transformed")
            result.success = True
            return result

        result.metrics.records_transformed = transformed.total_records

        # Collect transform warnings
        if transformed.has_warnings:
            result.transform_warnings.extend(transformed.warnings)
            logger.warning("Transform completed with %d warnings", len(transformed.warnings))

        # Dry run - skip load and validate
        if dry_run:
            logger.info("Dry run - skipping load and validate")
            result.success = True
            result.metrics.dimensions_loaded = {"dry_run": True}
            return result

        # Step 3: Load
        step_start = _utc_now()
        logger.info("Step 3/4: Load")

        load_summary: LoadSummary = load(target, transformed)
        result.metrics.load_duration = _utc_now() - step_start
        result.metrics.dimensions_loaded = load_summary.to_dict()
        result.metrics.records_loaded = load_summary.fact_quality_checks
        result.metrics.duplicates_removed = load_summary.duplicates_removed

        logger.info(
            "Loaded %d facts, removed %d duplicates", load_summary.fact_quality_checks, load_summary.duplicates_removed
        )

        # Step 4: Validate
        step_start = _utc_now()
        logger.info("Step 4/4: Validate")

        if strict:
            validation_result: ValidationResult = validate_with_guard(source, target, strict=True)
        else:
            validation_result = validate(source, target)

        result.metrics.validate_duration = _utc_now() - step_start
        result.validation_result = validation_result

        # Update state on successful validation
        if validation_result.passed():
            state["last_successful_run"] = start.isoformat()
            state["last_run_id"] = run_id
            if new_watermark:
                # Handle both datetime and string watermarks
                if isinstance(new_watermark, str):
                    state["high_watermark"] = new_watermark
                else:
                    state["high_watermark"] = new_watermark.isoformat()
            _save_state(state)
            logger.info("State saved - watermark: %s", new_watermark)
        else:
            logger.warning("Validation failed - state NOT saved")

        result.success = True

    except ExtractionError as e:
        logger.error("Pipeline failed during extraction: %s", e)
        result.error = f"Extraction failed: {e}"
        result.transform_warnings.append(result.error)

    except ValidationError as e:
        logger.error("Pipeline failed during transform: %s", e)
        result.error = f"Transform validation failed: {e}"
        result.transform_warnings.append(result.error)

    except StrictValidationError as e:
        logger.error("Pipeline failed strict validation: %s", e)
        result.error = f"Strict validation failed: {e}"
        # Re-raise for strict mode - this is a pipeline guard
        raise RuntimeError(str(e)) from e

    except Exception as e:
        logger.exception("Pipeline failed with unexpected error")
        result.error = f"Unexpected error: {e}"
        result.transform_warnings.append(result.error)

    finally:
        end = _utc_now()
        result.end_time = end
        result.duration = end - start

        logger.info("=" * 60)
        logger.info("Pipeline finished - Run: %s", run_id)
        logger.info("Duration: %s", result.duration)
        logger.info("Success: %s | Validation: %s", result.success, "PASSED" if result.validation_passed else "FAILED")
        logger.info(
            "Metrics: extracted=%d, transformed=%d, loaded=%d, duplicates=%d",
            result.metrics.records_extracted,
            result.metrics.records_transformed,
            result.metrics.records_loaded,
            result.metrics.duplicates_removed,
        )
        logger.info("=" * 60)

    return result


def run_with_guard(mode: str = "full", dry_run: bool = False) -> PipelineResult:
    # Execute pipeline with strict validation guard.

    return run(
        mode=mode,
        dry_run=dry_run,
        strict=True,
    )


if __name__ == "__main__":
    run()
