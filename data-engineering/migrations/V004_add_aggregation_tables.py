from sqlalchemy import text

DESCRIPTION = "Add data quality metrics aggregation table for faster dashboard queries"


def upgrade(conn):
    conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS agg_daily_quality (
            date_key INTEGER NOT NULL,
            dataset_id INTEGER NOT NULL,
            total_checks INTEGER NOT NULL,
            passed_checks INTEGER NOT NULL,
            failed_checks INTEGER NOT NULL,
            avg_score FLOAT NOT NULL,
            min_score FLOAT NOT NULL,
            max_score FLOAT NOT NULL,
            high_severity_failures INTEGER DEFAULT 0,
            medium_severity_failures INTEGER DEFAULT 0,
            low_severity_failures INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (date_key, dataset_id)
        )
    """
        )
    )

    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_agg_daily_date ON agg_daily_quality(date_key)
    """
        )
    )

    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_agg_daily_dataset ON agg_daily_quality(dataset_id)
    """
        )
    )


def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS agg_daily_quality CASCADE"))
