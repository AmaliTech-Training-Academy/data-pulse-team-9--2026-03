"""
SQL query templates used by quality_dashboard.py.

All templates that filter by dataset / date / severity use placeholder tokens
{id_list} and {sev_list} which are expanded into named bind-parameters by
build_parameterized_query().  Simple static queries are plain strings.
"""

# ---------------------------------------------------------------------------
# Common filter clause (reused across queries)
# ---------------------------------------------------------------------------

_BASE_FILTER = """
    f.dataset_id IN ({id_list})
    AND d.full_date BETWEEN :start AND :end
    AND r.severity IN ({sev_list})
"""

# ---------------------------------------------------------------------------
# Bootstrap / sidebar
# ---------------------------------------------------------------------------

GET_DATASETS = "SELECT DISTINCT id, name FROM dim_datasets ORDER BY name"

GET_DATE_RANGE = "SELECT MIN(full_date) AS min_d, MAX(full_date) AS max_d FROM dim_date"

# ---------------------------------------------------------------------------
# Overview section
# ---------------------------------------------------------------------------

KPI_OVERVIEW = f"""
    SELECT
        COUNT(*) AS total_checks,
        SUM(CASE WHEN passed THEN 1 ELSE 0 END) AS passed_checks,
        AVG(score) AS avg_score,
        MIN(score) AS min_score,
        MAX(score) AS max_score
    FROM fact_quality_checks f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_rules r ON f.rule_id = r.id
    WHERE {_BASE_FILTER}
"""

OVERVIEW_SPARK = f"""
    SELECT d.full_date, ROUND(AVG(f.score)::numeric, 1) AS avg_score
    FROM fact_quality_checks f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_rules r ON f.rule_id = r.id
    WHERE {_BASE_FILTER}
    GROUP BY d.full_date
    ORDER BY d.full_date
"""

# ---------------------------------------------------------------------------
# Quality Trends section
# ---------------------------------------------------------------------------

QUALITY_TRENDS = f"""
    SELECT d.full_date, ds.name AS dataset_name, AVG(f.score) AS avg_score,
           COUNT(*) AS check_count
    FROM fact_quality_checks f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_datasets ds ON f.dataset_id = ds.id
    JOIN dim_rules r ON f.rule_id = r.id
    WHERE ds.id IN ({{id_list}})
      AND d.full_date BETWEEN :start AND :end
      AND r.severity IN ({{sev_list}})
    GROUP BY d.full_date, ds.name
    ORDER BY d.full_date
"""

# ---------------------------------------------------------------------------
# Failure Analysis section
# ---------------------------------------------------------------------------

FAILURE_BY_RULETYPE = f"""
    SELECT r.rule_type,
           COUNT(*) AS total,
           SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failed,
           ROUND(AVG(CASE WHEN NOT f.passed THEN 1.0 ELSE 0.0 END) * 100, 1) AS failure_rate
    FROM fact_quality_checks f
    JOIN dim_rules r ON f.rule_id = r.id
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE {_BASE_FILTER}
    GROUP BY r.rule_type
    ORDER BY failure_rate DESC
"""

FAILURE_BY_SEVERITY = f"""
    SELECT r.severity,
           COUNT(*) AS total,
           SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failed
    FROM fact_quality_checks f
    JOIN dim_rules r ON f.rule_id = r.id
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE {_BASE_FILTER}
    GROUP BY r.severity
"""

# ---------------------------------------------------------------------------
# Dataset Comparison section
# ---------------------------------------------------------------------------

DATASET_COMPARISON = f"""
    SELECT ds.name AS dataset,
           ROUND(AVG(f.score)::numeric, 1) AS avg_score,
           COUNT(*) AS total_checks,
           SUM(CASE WHEN f.passed THEN 1 ELSE 0 END) AS passed,
           SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failed,
           ROUND(STDDEV(f.score)::numeric, 2) AS score_std
    FROM fact_quality_checks f
    JOIN dim_datasets ds ON f.dataset_id = ds.id
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_rules r ON f.rule_id = r.id
    WHERE ds.id IN ({{id_list}})
      AND d.full_date BETWEEN :start AND :end
      AND r.severity IN ({{sev_list}})
    GROUP BY ds.name
    ORDER BY avg_score ASC
"""

# ---------------------------------------------------------------------------
# Field-Level Issues section
# ---------------------------------------------------------------------------

FIELD_QUALITY_ISSUES = f"""
    SELECT r.field_name, r.rule_type, r.severity,
           COUNT(*) AS total_checks,
           SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failures,
           ROUND(AVG(CASE WHEN NOT f.passed THEN 1.0 ELSE 0.0 END) * 100, 1) AS failure_rate
    FROM fact_quality_checks f
    JOIN dim_rules r ON f.rule_id = r.id
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE {_BASE_FILTER}
      AND NOT f.passed
    GROUP BY r.field_name, r.rule_type, r.severity
    ORDER BY failures DESC
    LIMIT 10
"""

# ---------------------------------------------------------------------------
# Day-of-Week Patterns section
# ---------------------------------------------------------------------------

QUALITY_BY_DOW = f"""
    SELECT d.day_of_week,
           ROUND(AVG(f.score)::numeric, 1) AS avg_score,
           COUNT(*) AS check_count
    FROM fact_quality_checks f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_rules r ON f.rule_id = r.id
    WHERE {_BASE_FILTER}
    GROUP BY d.day_of_week
    ORDER BY d.day_of_week
"""
