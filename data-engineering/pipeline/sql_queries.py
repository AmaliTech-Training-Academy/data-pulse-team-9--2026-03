# SQL Query Loader Module

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional
import re

_SQL_DIR = Path(__file__).parent / "sql"


class QueryNotFoundError(Exception):
    """Raised when a SQL query cannot be found."""

    pass


@lru_cache(maxsize=32)
def _load_sql_file(filename: str) -> str:
    """Load and cache SQL file content."""
    filepath = _SQL_DIR / filename
    if not filepath.exists():
        raise QueryNotFoundError(f"SQL file not found: {filepath}")
    return filepath.read_text(encoding="utf-8")


def _parse_queries(content: str) -> dict[str, str]:
    """
    Parse SQL file content into named queries.

    Queries are denoted by comment headers like:
    -- QUERY_NAME
    SELECT ...
    """
    queries: dict[str, str] = {}
    current_name: Optional[str] = None
    current_lines: list[str] = []

    for line in content.split("\n"):
        # Check for query header comment
        header_match = re.match(r"^--\s*([A-Z][A-Z0-9_]+)\s*$", line.strip())

        if header_match:
            # Save previous query if exists
            if current_name and current_lines:
                query = "\n".join(current_lines).strip()
                if query:
                    queries[current_name] = query
            # Start new query
            current_name = header_match.group(1)
            current_lines = []
        elif current_name:
            # Skip descriptive comments but include query lines
            if not line.strip().startswith("--"):
                current_lines.append(line)

    # Save last query
    if current_name and current_lines:
        query = "\n".join(current_lines).strip()
        if query:
            queries[current_name] = query

    return queries


@lru_cache(maxsize=32)
def get_queries(filename: str) -> dict[str, str]:
    # Load all named queries from a SQL file.

    content = _load_sql_file(filename)
    return _parse_queries(content)


def get_query(filename: str, query_name: str) -> str:
    # Get a specific named query from a SQL file.

    queries = get_queries(filename)
    if query_name not in queries:
        raise QueryNotFoundError(f"Query '{query_name}' not found in {filename}. " f"Available: {list(queries.keys())}")
    return queries[query_name]


# Pre-defined query getters for common modules
class ExtractQueries:
    """Extract phase SQL queries."""

    _FILE = "extract_queries.sql"

    # Base query is special - it's the main unnamed query in the file
    BASE_QUERY = """
        SELECT cr.id, cr.dataset_id, cr.rule_id, cr.passed,
               cr.failed_rows, cr.total_rows, cr.checked_at,
               vr.name AS rule_name, vr.rule_type, vr.severity,
               vr.field_name, vr.dataset_type, vr.is_active,
               d.name AS dataset_name, d.file_type,
               d.row_count AS dataset_row_count, d.column_count,
               d.uploaded_at, d.status AS dataset_status
        FROM check_results cr
        JOIN validation_rules vr ON cr.rule_id = vr.id
        JOIN datasets d ON cr.dataset_id = d.id
    """

    # Use >= to avoid missing late-arriving rows with identical timestamps;
    # downstream fact deduplication handles re-reads safely.
    INCREMENTAL_FILTER = " WHERE cr.checked_at >= :last_run ORDER BY cr.checked_at"

    COUNT_FULL = "SELECT COUNT(*) FROM check_results"
    COUNT_INCREMENTAL = "SELECT COUNT(*) FROM check_results WHERE checked_at >= :last_run"

    WATERMARK = "SELECT MAX(checked_at) FROM check_results"


class ValidationQueries:
    """Validation phase SQL queries."""

    _FILE = "validation_queries.sql"

    SOURCE_COUNT = "SELECT COUNT(*) FROM check_results"
    TARGET_FACT_COUNT = "SELECT COUNT(*) FROM fact_quality_checks"

    ORPHANED_DATASETS = """
        SELECT COUNT(*) FROM fact_quality_checks f
        LEFT JOIN dim_datasets d ON f.dataset_id = d.id
        WHERE d.id IS NULL
    """

    ORPHANED_RULES = """
        SELECT COUNT(*) FROM fact_quality_checks f
        LEFT JOIN dim_rules r ON f.rule_id = r.id
        WHERE r.id IS NULL
    """

    ORPHANED_DATES = """
        SELECT COUNT(*) FROM fact_quality_checks f
        LEFT JOIN dim_date d ON f.date_key = d.date_key
        WHERE d.date_key IS NULL
    """

    INVALID_SCORES = """
        SELECT COUNT(*) FROM fact_quality_checks
        WHERE score < :min_score OR score > :max_score
    """

    DUPLICATE_FACTS = """
        SELECT COUNT(*) FROM (
            SELECT dataset_id, rule_id, checked_at, COUNT(*) as cnt
            FROM fact_quality_checks
            GROUP BY dataset_id, rule_id, checked_at
            HAVING COUNT(*) > 1
        ) dups
    """

    SUMMARY_STATISTICS = """
       SELECT
        COUNT(*) AS total_records,
        SUM(CASE WHEN passed THEN 1 ELSE 0 END) AS passed_count,
        SUM(CASE WHEN NOT passed THEN 1 ELSE 0 END) AS failed_count,
        ROUND(
          SUM(CASE WHEN passed THEN 1 ELSE 0 END)::numeric * 100.0
          / NULLIF(COUNT(*), 0),
          2
        ) AS success_rate,
        ROUND(AVG(score)::numeric, 2) AS avg_score,
        ROUND(MIN(score)::numeric, 2) AS min_score,
        ROUND(MAX(score)::numeric, 2) AS max_score
      FROM fact_quality_checks
    """

    DATASET_SUMMARY = """
        SELECT
            d.id AS dataset_id,
            d.name AS dataset_name,
            COUNT(f.id) AS total_checks,
            SUM(CASE WHEN f.passed THEN 1 ELSE 0 END) AS passed_checks,
            SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failed_checks,
            AVG(f.score) AS avg_score,
            MIN(f.score) AS min_score,
            MAX(f.score) AS max_score
        FROM fact_quality_checks f
        JOIN dim_datasets d ON f.dataset_id = d.id
        GROUP BY d.id, d.name
    """

    RULE_FAILURE_SUMMARY = """
        SELECT
            r.id AS rule_id,
            r.name AS rule_name,
            r.severity,
            COUNT(f.id) AS total_checks,
            SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failure_count
        FROM fact_quality_checks f
        JOIN dim_rules r ON f.rule_id = r.id
        GROUP BY r.id, r.name, r.severity
    """


class LoadQueries:
    """Load phase SQL queries."""

    _FILE = "load_queries.sql"

    @staticmethod
    def upsert_dim_datasets(is_sqlite: bool) -> str:
        if is_sqlite:
            return """
                INSERT OR REPLACE INTO dim_datasets
                (id, name, file_type, row_count, column_count, status, uploaded_at)
                VALUES (:id, :name, :file_type, :row_count, :column_count, :status, :uploaded_at)
            """
        return """
            INSERT INTO dim_datasets (id, name, file_type, row_count, column_count, status, uploaded_at)
            VALUES (:id, :name, :file_type, :row_count, :column_count, :status, :uploaded_at)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                file_type = EXCLUDED.file_type,
                row_count = EXCLUDED.row_count,
                column_count = EXCLUDED.column_count,
                status = EXCLUDED.status,
                uploaded_at = EXCLUDED.uploaded_at
        """

    @staticmethod
    def upsert_dim_rules(is_sqlite: bool) -> str:
        if is_sqlite:
            return """
                INSERT OR REPLACE INTO dim_rules
                (id, name, field_name, rule_type, severity, dataset_type, is_active)
                VALUES (:id, :name, :field_name, :rule_type, :severity, :dataset_type, :is_active)
            """
        return """
            INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active)
            VALUES (:id, :name, :field_name, :rule_type, :severity, :dataset_type, :is_active)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                field_name = EXCLUDED.field_name,
                rule_type = EXCLUDED.rule_type,
                severity = EXCLUDED.severity,
                dataset_type = EXCLUDED.dataset_type,
                is_active = EXCLUDED.is_active
        """

    @staticmethod
    def upsert_dim_date(is_sqlite: bool) -> str:
        if is_sqlite:
            return """
                INSERT OR IGNORE INTO dim_date
                (date_key, full_date, day_of_week, month, quarter, year)
                VALUES (:date_key, :full_date, :day_of_week, :month, :quarter, :year)
            """
        return """
            INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year)
            VALUES (:date_key, :full_date, :day_of_week, :month, :quarter, :year)
            ON CONFLICT (date_key) DO NOTHING
        """

    INSERT_FACT = """
        INSERT INTO fact_quality_checks
        (dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at)
        VALUES (:dataset_id, :rule_id, :date_key, :passed, :failed_rows, :total_rows, :score, :checked_at)
    """

    CHECK_FACT_EXISTS = """
        SELECT 1 FROM fact_quality_checks
        WHERE dataset_id = :dataset_id AND rule_id = :rule_id AND checked_at = :checked_at
        LIMIT 1
    """

    @staticmethod
    def deduplicate_facts(is_sqlite: bool) -> str:
        if is_sqlite:
            return """
                DELETE FROM fact_quality_checks
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM fact_quality_checks
                    GROUP BY dataset_id, rule_id, checked_at
                )
            """
        return """
            DELETE FROM fact_quality_checks f1
            USING fact_quality_checks f2
            WHERE f1.id > f2.id
              AND f1.dataset_id = f2.dataset_id
              AND f1.rule_id = f2.rule_id
              AND f1.checked_at = f2.checked_at
        """
