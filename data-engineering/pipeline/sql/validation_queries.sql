-- Validation Queries for ETL Pipeline
-- These queries are used during the post-load validation phase

-- SOURCE_COUNT_QUERY
-- Count of records in source check_results table
SELECT COUNT(*) FROM check_results

-- TARGET_FACT_COUNT_QUERY
-- Count of records in target fact table
SELECT COUNT(*) FROM fact_quality_checks

-- ORPHANED_DATASETS_QUERY
-- Count of fact records with missing dataset dimension
SELECT COUNT(*) FROM fact_quality_checks f
LEFT JOIN dim_datasets d ON f.dataset_id = d.id
WHERE d.id IS NULL

-- ORPHANED_RULES_QUERY
-- Count of fact records with missing rule dimension
SELECT COUNT(*) FROM fact_quality_checks f
LEFT JOIN dim_rules r ON f.rule_id = r.id
WHERE r.id IS NULL

-- ORPHANED_DATES_QUERY
-- Count of fact records with missing date dimension
SELECT COUNT(*) FROM fact_quality_checks f
LEFT JOIN dim_date d ON f.date_key = d.date_key
WHERE d.date_key IS NULL

-- INVALID_SCORES_QUERY
-- Count of records with scores outside valid range
SELECT COUNT(*) FROM fact_quality_checks
WHERE score < :min_score OR score > :max_score

-- DUPLICATE_FACTS_QUERY
-- Count of duplicate facts (same dataset_id, rule_id, checked_at)
SELECT COUNT(*) - COUNT(DISTINCT (dataset_id, rule_id, checked_at))
FROM fact_quality_checks

-- DATASET_VALIDATION_SUMMARY
-- Aggregated validation summary by dataset
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

-- RULE_FAILURE_SUMMARY
-- Aggregated failure summary by rule
SELECT
    r.id AS rule_id,
    r.name AS rule_name,
    r.severity,
    COUNT(f.id) AS total_checks,
    SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failure_count,
    ROUND(SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(f.id), 0), 2) AS failure_rate
FROM fact_quality_checks f
JOIN dim_rules r ON f.rule_id = r.id
GROUP BY r.id, r.name, r.severity

-- SUMMARY_STATISTICS
-- Overall pipeline summary statistics
SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN passed THEN 1 ELSE 0 END) AS passed_count,
    SUM(CASE WHEN NOT passed THEN 1 ELSE 0 END) AS failed_count,
    ROUND(SUM(CASE WHEN passed THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS success_rate,
    ROUND(AVG(score), 2) AS avg_score,
    ROUND(MIN(score), 2) AS min_score,
    ROUND(MAX(score), 2) AS max_score
FROM fact_quality_checks
