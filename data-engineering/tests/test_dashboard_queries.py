"""
Tests for the dashboard SQL query constants (dashboards/queries.py).

Covers:
  - Every constant is a non-empty string
  - Parameterised queries contain the {id_list} and {sev_list} placeholders
  - Parameterised queries contain :start and :end date bind parameters
  - Static queries (GET_DATASETS, GET_DATE_RANGE) have no placeholders
  - Every query begins with SELECT and references at least one FROM clause
  - Analytical queries reference fact_quality_checks (the central fact table)
  - Static queries execute successfully against a SQLite in-memory analytics DB
"""

import pytest
from datetime import date

from sqlalchemy import create_engine, text

from infrastructure.db import AnalyticsBase
from infrastructure import models  # noqa: F401 — registers ORM tables
import dashboards.queries as Q


# ---------------------------------------------------------------------------
# Query groups
# ---------------------------------------------------------------------------

PARAMETERISED = [
    ("KPI_OVERVIEW", Q.KPI_OVERVIEW),
    ("OVERVIEW_SPARK", Q.OVERVIEW_SPARK),
    ("QUALITY_TRENDS", Q.QUALITY_TRENDS),
    ("FAILURE_BY_RULETYPE", Q.FAILURE_BY_RULETYPE),
    ("FAILURE_BY_SEVERITY", Q.FAILURE_BY_SEVERITY),
    ("DATASET_COMPARISON", Q.DATASET_COMPARISON),
    ("FIELD_QUALITY_ISSUES", Q.FIELD_QUALITY_ISSUES),
    ("QUALITY_BY_DOW", Q.QUALITY_BY_DOW),
]

STATIC = [
    ("GET_DATASETS", Q.GET_DATASETS),
    ("GET_DATE_RANGE", Q.GET_DATE_RANGE),
]

ALL_QUERIES = PARAMETERISED + STATIC


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def empty_analytics_engine():
    """SQLite in-memory engine with analytics schema but no data."""
    engine = create_engine("sqlite:///:memory:")
    AnalyticsBase.metadata.create_all(engine)
    return engine


@pytest.fixture
def seeded_analytics_engine(empty_analytics_engine):
    """SQLite in-memory engine populated with one row in each analytics table."""
    engine = empty_analytics_engine
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO dim_datasets (id, name, file_type, row_count, column_count, status) "
                "VALUES (1, 'sales.csv', 'csv', 500, 6, 'VALIDATED')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active) "
                "VALUES (1, 'Not null', 'amount', 'NOT_NULL', 'HIGH', 'sales', 1)"
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
                "VALUES (1, 1, 20260311, 1, 0, 500, 100.0, '2026-03-11 12:00:00')"
            )
        )
    return engine


# ---------------------------------------------------------------------------
# 1.  All constants are non-empty strings
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name, query", ALL_QUERIES)
def test_query_is_non_empty_string(name, query):
    """Every query constant must be a non-empty string."""
    assert isinstance(query, str), f"{name} should be a str"
    assert query.strip(), f"{name} should not be empty"


# ---------------------------------------------------------------------------
# 2.  Parameterised queries have required placeholders
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name, query", PARAMETERISED)
def test_parameterised_queries_have_id_list(name, query):
    """{id_list} placeholder must appear in every parameterised query."""
    assert "{id_list}" in query, f"{name} is missing {{id_list}} placeholder"


@pytest.mark.parametrize("name, query", PARAMETERISED)
def test_parameterised_queries_have_sev_list(name, query):
    """{sev_list} placeholder must appear in every parameterised query."""
    assert "{sev_list}" in query, f"{name} is missing {{sev_list}} placeholder"


@pytest.mark.parametrize("name, query", PARAMETERISED)
def test_parameterised_queries_have_date_bind_params(name, query):
    """All parameterised queries must use :start and :end date bind-params."""
    assert ":start" in query, f"{name} is missing :start date bind-param"
    assert ":end" in query, f"{name} is missing :end date bind-param"


# ---------------------------------------------------------------------------
# 3.  Static queries do NOT contain dynamic placeholders
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name, query", STATIC)
def test_static_queries_have_no_id_list(name, query):
    """Static queries must not contain {id_list} — they need no dataset filter."""
    assert "{id_list}" not in query, f"{name} unexpectedly contains {{id_list}}"


@pytest.mark.parametrize("name, query", STATIC)
def test_static_queries_have_no_sev_list(name, query):
    """Static queries must not contain {sev_list}."""
    assert "{sev_list}" not in query, f"{name} unexpectedly contains {{sev_list}}"


# ---------------------------------------------------------------------------
# 4.  Basic SQL structure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name, query", ALL_QUERIES)
def test_query_starts_with_select(name, query):
    """Every query must be a SELECT statement."""
    normalised = query.strip().upper()
    assert normalised.startswith("SELECT"), f"{name} does not start with SELECT"


@pytest.mark.parametrize("name, query", ALL_QUERIES)
def test_query_has_from_clause(name, query):
    """Every query must reference at least one table via FROM."""
    assert "FROM" in query.upper(), f"{name} has no FROM clause"


@pytest.mark.parametrize("name, query", PARAMETERISED)
def test_parameterised_queries_reference_fact_table(name, query):
    """Analytical queries must read from fact_quality_checks."""
    assert "fact_quality_checks" in query.lower(), f"{name} does not reference fact_quality_checks"


@pytest.mark.parametrize("name, query", PARAMETERISED)
def test_parameterised_queries_join_dim_date(name, query):
    """Analytical queries must join dim_date to enable date filtering."""
    assert "dim_date" in query.lower(), f"{name} does not join dim_date"


@pytest.mark.parametrize("name, query", PARAMETERISED)
def test_parameterised_queries_join_dim_rules(name, query):
    """Analytical queries must join dim_rules to enable severity filtering."""
    assert "dim_rules" in query.lower(), f"{name} does not join dim_rules"


# ---------------------------------------------------------------------------
# 5.  Static queries execute cleanly against SQLite
# ---------------------------------------------------------------------------


def test_get_datasets_executes_on_empty_db(empty_analytics_engine):
    """GET_DATASETS runs without error on an empty analytics schema."""
    with empty_analytics_engine.connect() as conn:
        result = conn.execute(text(Q.GET_DATASETS)).fetchall()
    assert result == []


def test_get_date_range_executes_on_empty_db(empty_analytics_engine):
    """GET_DATE_RANGE runs without error on an empty date dimension."""
    with empty_analytics_engine.connect() as conn:
        row = conn.execute(text(Q.GET_DATE_RANGE)).fetchone()
    # Both min and max are NULL when the table is empty
    assert row is not None
    assert row[0] is None  # min_d
    assert row[1] is None  # max_d


def test_get_datasets_returns_rows_when_populated(seeded_analytics_engine):
    """GET_DATASETS returns dataset id and name when data exists."""
    with seeded_analytics_engine.connect() as conn:
        rows = conn.execute(text(Q.GET_DATASETS)).fetchall()
    assert len(rows) == 1
    row = rows[0]
    assert row[0] == 1  # id
    assert row[1] == "sales.csv"  # name


def test_get_date_range_returns_dates_when_populated(seeded_analytics_engine):
    """GET_DATE_RANGE returns min and max dates when dim_date is populated."""
    with seeded_analytics_engine.connect() as conn:
        row = conn.execute(text(Q.GET_DATE_RANGE)).fetchone()
    assert row is not None
    assert row[0] is not None  # min_d
    assert row[1] is not None  # max_d


# ---------------------------------------------------------------------------
# 6.  Placeholder expansion (simulates what the dashboard helper does)
# ---------------------------------------------------------------------------


def test_id_list_placeholder_can_be_expanded():
    """After replacing {id_list} with a bind-param list the query is valid SQL text."""
    expanded = Q.KPI_OVERVIEW.format(
        id_list=":id0, :id1",
        sev_list=":sev0, :sev1",
    )
    assert ":id0" in expanded
    assert ":id1" in expanded
    assert "{id_list}" not in expanded
    assert "{sev_list}" not in expanded


def test_single_id_expansion_works():
    """Single-element expansion produces valid SQL (no trailing comma)."""
    expanded = Q.QUALITY_TRENDS.format(id_list=":id0", sev_list=":sev0")
    assert expanded.count(":id0") >= 1
    # The expanded string must not have the raw placeholder tokens
    assert "{id_list}" not in expanded


def test_multi_severity_expansion_works():
    """Multiple severity values can be expanded into the sev_list slot."""
    expanded = Q.FAILURE_BY_SEVERITY.format(
        id_list=":id0",
        sev_list=":sev0, :sev1, :sev2",
    )
    assert ":sev0" in expanded
    assert ":sev2" in expanded
    assert "{sev_list}" not in expanded


# ---------------------------------------------------------------------------
# 7.  No hardcoded test data in SQL constants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name, query", ALL_QUERIES)
def test_no_hardcoded_dataset_ids(name, query):
    """SQL constants must not hardcode specific dataset IDs."""
    # Legitimate integer literals like date_key comparisons are fine,
    # but "dataset_id = 1" would indicate a hard-coded filter.
    assert "dataset_id = 1" not in query, f"{name} appears to have a hardcoded dataset_id filter"


@pytest.mark.parametrize("name, query", ALL_QUERIES)
def test_no_hardcoded_severity_values(name, query):
    """SQL constants must not hardcode severity string literals like 'HIGH'."""
    # Severity filtering uses the {sev_list} placeholder, not literals
    assert "'HIGH'" not in query, f"{name} has a hardcoded severity literal 'HIGH'"
    assert "'LOW'" not in query, f"{name} has a hardcoded severity literal 'LOW'"
