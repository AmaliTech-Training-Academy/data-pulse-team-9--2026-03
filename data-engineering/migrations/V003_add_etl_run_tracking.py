from sqlalchemy import text

DESCRIPTION = "Add pipeline run tracking table for incremental loads"


def upgrade(conn):
    conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS etl_run_log (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(50) UNIQUE NOT NULL,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            status VARCHAR(20) NOT NULL,
            mode VARCHAR(20) NOT NULL,
            records_extracted INTEGER DEFAULT 0,
            records_loaded INTEGER DEFAULT 0,
            duration_seconds FLOAT,
            error_message TEXT
        )
    """
        )
    )

    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_etl_run_status ON etl_run_log(status)
    """
        )
    )

    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_etl_run_started ON etl_run_log(started_at DESC)
    """
        )
    )


def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS etl_run_log CASCADE"))
