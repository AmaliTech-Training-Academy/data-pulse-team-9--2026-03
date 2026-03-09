from sqlalchemy import text

DESCRIPTION = "Create initial analytics star schema tables"


def upgrade(conn):
    conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_datasets (
              id INTEGER PRIMARY KEY,
              name VARCHAR(255),
              file_type VARCHAR(10),
              row_count INTEGER,
              column_count INTEGER,
              status VARCHAR(20),
              uploaded_at TIMESTAMP
        )
    """))

    conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_rules (
              id INTEGER PRIMARY KEY,
              name VARCHAR(255),
              field_name VARCHAR(255),
              rule_type VARCHAR(20),
              severity VARCHAR(10),
              dataset_type VARCHAR(100),
              is_active BOOLEAN
        )
    """))

    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_rules_type ON dim_rules(rule_type)
    """))

    conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rules_severity ON dim_rules(severity)
    """))

    conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_date (
              date_key INTEGER PRIMARY KEY,
              full_date DATE,
              day_of_week INTEGER,
              month INTEGER,
              quarter INTEGER,
              year INTEGER
        )
    """))

    conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_date_year_month ON dim_date(year, month)
    """))

    conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_quality_checks (
              id SERIAL PRIMARY KEY,
              dataset_id INTEGER REFERENCES dim_datasets(id),
              rule_id INTEGER REFERENCES dim_rules(id),
              date_key INTEGER REFERENCES dim_date(date_key),
              passed BOOLEAN,
              failed_rows INTEGER,
              total_rows INTEGER,
              score FLOAT,
              checked_at TIMESTAMP
        )
    """))

    conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_facts_dataset_date ON fact_quality_checks(dataset_id, date_key)
    """))

    conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_facts_rule ON fact_quality_checks(rule_id)
    """))

    conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_facts_date ON fact_quality_checks(date_key)
    """))


def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS fact_quality_checks CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS dim_date CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS dim_rules CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS dim_datasets CASCADE"))
