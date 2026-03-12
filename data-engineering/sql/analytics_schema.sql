-- DataPulse Analytics Schema (Star Schema)

-- ---------------------------------------------------------------------------
-- DIMENSION: Datasets
-- Describes uploaded files that undergo quality checks.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_datasets (
    id INTEGER PRIMARY KEY,           -- Natural key from app DB (not surrogate)
    name VARCHAR(255),
    file_type VARCHAR(10),            -- csv, json, etc.
    row_count INTEGER,
    column_count INTEGER,
    status VARCHAR(20),               -- PENDING, VALIDATED, FAILED
    uploaded_at TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- DIMENSION: Validation Rules
-- Describes quality rules applied to datasets.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_rules (
    id INTEGER PRIMARY KEY,           -- Natural key from app DB
    name VARCHAR(255),
    field_name VARCHAR(255),
    rule_type VARCHAR(20),            -- NOT_NULL, RANGE, REGEX, etc.
    severity VARCHAR(10),             -- HIGH, MEDIUM, LOW
    dataset_type VARCHAR(100),        -- employee, sales, feedback, etc.
    is_active BOOLEAN
);

-- Index for filtering by rule_type/severity (common dashboard filters)
CREATE INDEX IF NOT EXISTS idx_rules_type ON dim_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_rules_severity ON dim_rules(severity);

-- ---------------------------------------------------------------------------
-- DIMENSION: Date
-- Calendar dimension for time-based analysis.
-- date_key is YYYYMMDD integer format for easy partitioning/filtering.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,     -- YYYYMMDD format (e.g., 20260306)
    full_date DATE,
    day_of_week INTEGER,              -- 0=Monday, 6=Sunday
    month INTEGER,
    quarter INTEGER,
    year INTEGER
);

-- Index for year/month filtering (time-series dashboards)
CREATE INDEX IF NOT EXISTS idx_date_year_month ON dim_date(year, month);

-- ---------------------------------------------------------------------------
-- FACT: Quality Checks
-- Records each quality check result (event/transaction grain).
-- One row per check_result from the app DB.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_quality_checks (
    id SERIAL PRIMARY KEY,            -- Surrogate key (analytics table)
    dataset_id INTEGER REFERENCES dim_datasets(id),
    rule_id INTEGER REFERENCES dim_rules(id),
    date_key INTEGER REFERENCES dim_date(date_key),
    passed BOOLEAN,
    failed_rows INTEGER,
    total_rows INTEGER,
    score FLOAT,                      -- Computed: (total-failed)/total * 100
    checked_at TIMESTAMP
);

-- Indexes for common query patterns:

-- 1. Time-series queries: "Score over time for dataset X"
CREATE INDEX IF NOT EXISTS idx_facts_dataset_date ON fact_quality_checks(dataset_id, date_key);

-- 2. Rule analysis: "Issues by rule type" (joins to dim_rules)
CREATE INDEX IF NOT EXISTS idx_facts_rule ON fact_quality_checks(rule_id);

-- 3. Date filtering: "All checks on date Y"
CREATE INDEX IF NOT EXISTS idx_facts_date ON fact_quality_checks(date_key);

-- 4. Failed checks: "Show me failures only"
CREATE INDEX IF NOT EXISTS idx_facts_passed ON fact_quality_checks(passed) WHERE passed = FALSE;
