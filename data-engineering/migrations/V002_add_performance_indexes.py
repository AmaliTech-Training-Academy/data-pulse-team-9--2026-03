from sqlalchemy import text

DESCRIPTION = "Add performance indexes for common query patterns"


def upgrade(conn):
    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_facts_passed
        ON fact_quality_checks(passed)
        WHERE passed = FALSE
    """
        )
    )

    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_facts_score_range
        ON fact_quality_checks(score)
        WHERE score < 70
    """
        )
    )

    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_datasets_status
        ON dim_datasets(status)
    """
        )
    )


def downgrade(conn):
    conn.execute(text("DROP INDEX IF EXISTS idx_facts_passed"))
    conn.execute(text("DROP INDEX IF EXISTS idx_facts_score_range"))
    conn.execute(text("DROP INDEX IF EXISTS idx_datasets_status"))
