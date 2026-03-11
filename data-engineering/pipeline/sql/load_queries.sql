-- Load Queries for ETL Pipeline
-- These queries are used during the load phase

-- UPSERT_DIM_DATASETS_POSTGRES
INSERT INTO dim_datasets (id, name, file_type, row_count, column_count, status, uploaded_at)
VALUES (:id, :name, :file_type, :row_count, :column_count, :status, :uploaded_at)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    file_type = EXCLUDED.file_type,
    row_count = EXCLUDED.row_count,
    column_count = EXCLUDED.column_count,
    status = EXCLUDED.status,
    uploaded_at = EXCLUDED.uploaded_at

-- UPSERT_DIM_DATASETS_SQLITE
INSERT OR REPLACE INTO dim_datasets (id, name, file_type, row_count, column_count, status, uploaded_at)
VALUES (:id, :name, :file_type, :row_count, :column_count, :status, :uploaded_at)

-- UPSERT_DIM_RULES_POSTGRES
INSERT INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active)
VALUES (:id, :name, :field_name, :rule_type, :severity, :dataset_type, :is_active)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    field_name = EXCLUDED.field_name,
    rule_type = EXCLUDED.rule_type,
    severity = EXCLUDED.severity,
    dataset_type = EXCLUDED.dataset_type,
    is_active = EXCLUDED.is_active

-- UPSERT_DIM_RULES_SQLITE
INSERT OR REPLACE INTO dim_rules (id, name, field_name, rule_type, severity, dataset_type, is_active)
VALUES (:id, :name, :field_name, :rule_type, :severity, :dataset_type, :is_active)

-- UPSERT_DIM_DATE_POSTGRES
INSERT INTO dim_date (date_key, full_date, day_of_week, month, quarter, year)
VALUES (:date_key, :full_date, :day_of_week, :month, :quarter, :year)
ON CONFLICT (date_key) DO NOTHING

-- UPSERT_DIM_DATE_SQLITE
INSERT OR IGNORE INTO dim_date (date_key, full_date, day_of_week, month, quarter, year)
VALUES (:date_key, :full_date, :day_of_week, :month, :quarter, :year)

-- INSERT_FACT_SINGLE
INSERT INTO fact_quality_checks
(dataset_id, rule_id, date_key, passed, failed_rows, total_rows, score, checked_at)
VALUES (:dataset_id, :rule_id, :date_key, :passed, :failed_rows, :total_rows, :score, :checked_at)

-- CHECK_FACT_EXISTS_POSTGRES
SELECT 1 FROM fact_quality_checks
WHERE dataset_id = :dataset_id AND rule_id = :rule_id AND checked_at = :checked_at
LIMIT 1

-- DELETE_EXISTING_FACTS
DELETE FROM fact_quality_checks
WHERE dataset_id = :dataset_id AND rule_id = :rule_id AND checked_at = :checked_at

-- DEDUPLICATE_FACTS_POSTGRES
DELETE FROM fact_quality_checks f1
USING fact_quality_checks f2
WHERE f1.id > f2.id
  AND f1.dataset_id = f2.dataset_id
  AND f1.rule_id = f2.rule_id
  AND f1.checked_at = f2.checked_at

-- DEDUPLICATE_FACTS_SQLITE
DELETE FROM fact_quality_checks
WHERE id NOT IN (
    SELECT MIN(id)
    FROM fact_quality_checks
    GROUP BY dataset_id, rule_id, checked_at
)
