-- DataPulse Analytics Schema

CREATE TABLE IF NOT EXISTS dim_datasets (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    file_type VARCHAR(10),
    row_count INTEGER,
    uploaded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_rules (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    field_name VARCHAR(255),
    rule_type VARCHAR(20),
    severity VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE,
    day_of_week INTEGER,
    month INTEGER,
    year INTEGER
);

CREATE TABLE IF NOT EXISTS fact_quality_checks (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES dim_datasets(id),
    rule_id INTEGER REFERENCES dim_rules(id),
    rule_type VARCHAR(20),
    passed BOOLEAN,
    failed_rows INTEGER,
    total_rows INTEGER,
    score FLOAT,
    severity VARCHAR(10),
    checked_at TIMESTAMP
);
