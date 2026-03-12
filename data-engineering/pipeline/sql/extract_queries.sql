-- Extract Queries for ETL Pipeline
-- These queries are used during the extraction phase

-- BASE_EXTRACT_QUERY
-- Main query for extracting check results with related datasets and rules
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

-- INCREMENTAL_FILTER
-- WHERE cr.checked_at > :last_run ORDER BY cr.checked_at

-- COUNT_QUERY_FULL
-- SELECT COUNT(*) FROM check_results

-- COUNT_QUERY_INCREMENTAL
-- SELECT COUNT(*) FROM check_results WHERE checked_at > :last_run

-- WATERMARK_QUERY
-- SELECT MAX(checked_at) FROM check_results
