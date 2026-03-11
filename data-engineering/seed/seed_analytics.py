# Seed the app database with mock data for ETL development.

import argparse
import random
import time
from datetime import datetime, timedelta
from sqlalchemy import text

from infrastructure.db import get_source_engine
from pipeline.utils.logging import get_logger

logger = get_logger("seed")

# Sample datasets to create
DATASETS = [
    ("employee_records.csv", "csv", 500, 7, "VALIDATED"),
    ("sales_q1.csv", "csv", 1200, 10, "VALIDATED"),
    ("customer_feedback.json", "json", 300, 5, "VALIDATED"),
    ("inventory_report.csv", "csv", 800, 8, "VALIDATED"),
    ("marketing_leads.csv", "csv", 250, 6, "PENDING"),
]

# Sample validation rules
RULES = [
    ("Name not null", "employee", "name", "NOT_NULL", None, "HIGH"),
    ("Email format", "employee", "email", "REGEX", '{"pattern": "^[\\\\w.+-]+@[\\\\w-]+\\\\.\\\\w+$"}', "MEDIUM"),
    ("Age range", "employee", "age", "RANGE", '{"min": 18, "max": 100}', "HIGH"),
    ("Unique ID", "employee", "id", "UNIQUE", None, "HIGH"),
    ("Salary type", "employee", "salary", "DATA_TYPE", '{"expected_type": "int"}', "MEDIUM"),
    ("Department not null", "employee", "department", "NOT_NULL", None, "LOW"),
    ("Date format", "employee", "hire_date", "REGEX", '{"pattern": "^\\\\d{4}-\\\\d{2}-\\\\d{2}$"}', "MEDIUM"),
    ("Sales amount range", "sales", "amount", "RANGE", '{"min": 0, "max": 999999}', "HIGH"),
    ("Customer ID not null", "sales", "customer_id", "NOT_NULL", None, "HIGH"),
    ("Product code format", "sales", "product_code", "REGEX", '{"pattern": "^PRD-\\\\d{4}$"}', "LOW"),
    ("Feedback not null", "feedback", "comment", "NOT_NULL", None, "MEDIUM"),
    ("Rating range", "feedback", "rating", "RANGE", '{"min": 1, "max": 5}', "MEDIUM"),
    ("SKU unique", "inventory", "sku", "UNIQUE", None, "HIGH"),
    ("Quantity type", "inventory", "quantity", "DATA_TYPE", '{"expected_type": "int"}', "LOW"),
    ("Lead email format", "marketing", "email", "REGEX", '{"pattern": "^[\\\\w.+-]+@[\\\\w-]+\\\\.\\\\w+$"}', "MEDIUM"),
]


def seed():
    """Insert mock data into the app database.

    Idempotent: Checks if data exists before inserting.
    Creates: 5 datasets, 15 rules, 100 check results.
    """
    engine = get_source_engine()

    with engine.begin() as conn:
        # Check if data already exists
        count = conn.execute(text("SELECT COUNT(*) FROM datasets")).scalar()
        if count > 0:
            logger.info("App DB already has %d datasets — skipping seed", count)
            return {"status": "skipped", "reason": "Data already exists"}

        # Seed datasets
        for name, file_type, row_count, col_count, status in DATASETS:
            days_ago = random.randint(5, 30)
            uploaded_at = datetime.now() - timedelta(days=days_ago)
            conn.execute(
                text(
                    """
                INSERT INTO datasets (name, file_type, row_count, column_count, uploaded_at, status)
                VALUES (:name, :file_type, :row_count, :column_count, :uploaded_at, :status)
            """
                ),
                {
                    "name": name,
                    "file_type": file_type,
                    "row_count": row_count,
                    "column_count": col_count,
                    "uploaded_at": uploaded_at,
                    "status": status,
                },
            )
        logger.info("Seeded %d datasets", len(DATASETS))

        # Seed validation rules
        for name, ds_type, field, rule_type, params, severity in RULES:
            created_at = datetime.now()
            conn.execute(
                text(
                    """
                INSERT INTO validation_rules (
                    name, dataset_type, field_name, rule_type, parameters, severity, is_active, created_at
                )
                VALUES (
                    :name, :dataset_type, :field_name, :rule_type, :parameters, :severity, :is_active, :created_at
                )
            """
                ),
                {
                    "name": name,
                    "dataset_type": ds_type,
                    "field_name": field,
                    "rule_type": rule_type,
                    "parameters": params,
                    "severity": severity,
                    "is_active": True,
                    "created_at": created_at,
                },
            )
        logger.info("Seeded %d validation rules", len(RULES))

        # Get inserted IDs
        dataset_ids = [r[0] for r in conn.execute(text("SELECT id FROM datasets")).fetchall()]
        rule_ids = [r[0] for r in conn.execute(text("SELECT id FROM validation_rules")).fetchall()]

        # Seed check results (~100 records spread over 30 days)
        check_count = 0
        for _ in range(100):
            ds_id = random.choice(dataset_ids)
            rule_id = random.choice(rule_ids)
            total_rows = random.choice([250, 300, 500, 800, 1200])
            passed = random.random() > 0.25  # 75% pass rate
            failed_rows = 0 if passed else random.randint(1, total_rows // 5)
            days_ago = random.randint(0, 29)
            checked_at = datetime.now() - timedelta(
                days=days_ago,
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )

            conn.execute(
                text(
                    """
                INSERT INTO check_results (dataset_id, rule_id, passed, failed_rows, total_rows, checked_at)
                VALUES (:dataset_id, :rule_id, :passed, :failed_rows, :total_rows, :checked_at)
            """
                ),
                {
                    "dataset_id": ds_id,
                    "rule_id": rule_id,
                    "passed": passed,
                    "failed_rows": failed_rows,
                    "total_rows": total_rows,
                    "checked_at": checked_at,
                },
            )
            check_count += 1

        logger.info("Seeded %d check results", check_count)

        # Seed quality scores (aggregates over time)
        score_count = 0
        for days_back in range(30):
            calc_date = datetime.now() - timedelta(days=days_back)
            for ds_id in dataset_ids:
                avg_score = round(75 + random.uniform(-10, 20), 2)
                total_rules = random.randint(5, 15)
                passed_rules = random.randint(3, total_rules)
                failed_rules = total_rules - passed_rules
                conn.execute(
                    text(
                        """
                    INSERT INTO quality_scores (
                        dataset_id, score, total_rules, passed_rules, failed_rules, checked_at
                    )
                    VALUES (
                        :dataset_id, :score, :total_rules, :passed_rules, :failed_rules, :checked_at
                    )
                """
                    ),
                    {
                        "dataset_id": ds_id,
                        "score": avg_score,
                        "total_rules": total_rules,
                        "passed_rules": passed_rules,
                        "failed_rules": failed_rules,
                        "checked_at": calc_date,
                    },
                )
                score_count += 1

        logger.info("Seeded %d quality scores", score_count)

    logger.info("Seeding complete!")
    return {
        "status": "success",
        "datasets": len(DATASETS),
        "rules": len(RULES),
        "check_results": check_count,
        "quality_scores": score_count,
    }


def append_check_results(rows: int = 50):
    """
    Append new check_results records without duplicate fact keys.

    Dedup key downstream is (dataset_id, rule_id, checked_at), so this function
    guarantees unique tuples for inserted rows.
    """
    if rows <= 0:
        return {"status": "skipped", "reason": "rows must be > 0"}

    engine = get_source_engine()

    with engine.begin() as conn:
        dataset_ids = [r[0] for r in conn.execute(text("SELECT id FROM datasets")).fetchall()]
        rule_ids = [r[0] for r in conn.execute(text("SELECT id FROM validation_rules")).fetchall()]

        if not dataset_ids or not rule_ids:
            return {
                "status": "skipped",
                "reason": "datasets/validation_rules are missing; run base seed first",
            }

        max_checked_at = conn.execute(text("SELECT MAX(checked_at) FROM check_results")).scalar_one_or_none()
        if isinstance(max_checked_at, str):
            try:
                max_checked_at = datetime.fromisoformat(max_checked_at)
            except ValueError:
                max_checked_at = datetime.now() - timedelta(minutes=rows + 1)
        if max_checked_at is None:
            max_checked_at = datetime.now() - timedelta(minutes=rows + 1)

        # Ensure all new rows are strictly newer than current max timestamp.
        base_time = max_checked_at + timedelta(seconds=1)

        inserted = 0
        used_keys: set[tuple[int, int, datetime]] = set()

        for i in range(rows):
            # Try multiple times to avoid accidental tuple collisions.
            for _ in range(20):
                ds_id = random.choice(dataset_ids)
                rule_id = random.choice(rule_ids)
                checked_at = base_time + timedelta(seconds=i)
                key = (ds_id, rule_id, checked_at)
                if key not in used_keys:
                    used_keys.add(key)
                    break

            total_rows = random.choice([250, 300, 500, 800, 1200])
            passed = random.random() > 0.25
            failed_rows = 0 if passed else random.randint(1, max(1, total_rows // 5))

            conn.execute(
                text(
                    """
                INSERT INTO check_results (dataset_id, rule_id, passed, failed_rows, total_rows, checked_at)
                VALUES (:dataset_id, :rule_id, :passed, :failed_rows, :total_rows, :checked_at)
            """
                ),
                {
                    "dataset_id": ds_id,
                    "rule_id": rule_id,
                    "passed": passed,
                    "failed_rows": failed_rows,
                    "total_rows": total_rows,
                    "checked_at": checked_at,
                },
            )
            inserted += 1

    logger.info("Appended %d new check_results rows", inserted)
    return {
        "status": "success",
        "appended_check_results": inserted,
        "start_checked_at": base_time.isoformat(),
    }


def stream_check_results(
    rows_per_cycle: int = 10,
    interval_seconds: int = 15,
    iterations: int = 0,
    run_incremental_etl: bool = True,
):
    # Continuously append check_results in cycles.

    if rows_per_cycle <= 0:
        return {"status": "skipped", "reason": "rows_per_cycle must be > 0"}

    if interval_seconds < 1:
        interval_seconds = 1

    logger.info(
        "Starting stream mode: rows_per_cycle=%d, interval_seconds=%d, iterations=%s, run_incremental_etl=%s",
        rows_per_cycle,
        interval_seconds,
        "infinite" if iterations == 0 else iterations,
        run_incremental_etl,
    )

    cycle = 0
    total_appended = 0

    try:
        while iterations == 0 or cycle < iterations:
            cycle += 1
            append_result = append_check_results(rows_per_cycle)
            appended_now = int(append_result.get("appended_check_results", 0))
            total_appended += appended_now

            logger.info(
                "Cycle %d: appended %d rows (total=%d)",
                cycle,
                appended_now,
                total_appended,
            )

            if run_incremental_etl:
                # Local import avoids startup overhead when only seeding.
                from pipeline.orchestration.run_pipeline import run

                result = run(mode="incremental", dry_run=False, strict=False, use_watermark=True)
                logger.info(
                    "Cycle %d: incremental ETL success=%s loaded=%d",
                    cycle,
                    result.success,
                    result.metrics.records_loaded,
                )

            if iterations != 0 and cycle >= iterations:
                break

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        logger.info("Stream mode stopped by user")

    return {
        "status": "success",
        "cycles": cycle,
        "total_appended_check_results": total_appended,
    }


def _parse_args():
    parser = argparse.ArgumentParser(description="Seed/append analytics source data")
    parser.add_argument(
        "--append-check-results",
        type=int,
        default=0,
        help="Append N new check_results rows (no duplicate fact keys)",
    )
    parser.add_argument(
        "--stream-check-results",
        type=int,
        default=0,
        help="Continuously append N check_results rows per cycle",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=15,
        help="Seconds between stream cycles (default: 15)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=0,
        help="Number of stream cycles (0 = infinite)",
    )
    parser.add_argument(
        "--no-etl",
        action="store_true",
        help="In stream mode, skip running incremental ETL after append",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.stream_check_results > 0:
        result = stream_check_results(
            rows_per_cycle=args.stream_check_results,
            interval_seconds=args.interval_seconds,
            iterations=args.iterations,
            run_incremental_etl=not args.no_etl,
        )
    elif args.append_check_results > 0:
        result = append_check_results(args.append_check_results)
    else:
        result = seed()
    print(f"Seed result: {result}")
