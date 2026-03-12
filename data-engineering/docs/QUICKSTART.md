# DataPulse Data Engineering - Quick Start

This guide walks through setting up and running the data engineering component
of DataPulse from scratch. Follow the steps in order.

---

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 14 or higher running locally (or via Docker)
- The backend service started at least once so its tables exist (the ETL reads
  from the same database)

---

## Step 1 — Navigate to the data-engineering directory

All commands in this guide must be run from inside `data-engineering/`.

```
cd data-engineering
```

---

## Step 2 — Create and activate a virtual environment

```
python -m venv venv
```

Windows:
```
venv\Scripts\activate
```

macOS / Linux:
```
source venv/bin/activate
```

---

## Step 3 — Install dependencies

```
pip install -r requirements.txt
```

Key packages installed:
- streamlit 1.28.1 — dashboard UI
- pandas 2.1.3 — data manipulation
- plotly 5.17.0 — charting
- sqlalchemy 2.0.23 — database ORM
- psycopg2-binary 2.9.9 — PostgreSQL driver
- python-dotenv 1.0.0 — environment variable loading

---

## Step 4 — Configure environment variables

Copy the example environment file:

```
cp .env.example .env
```

Open `.env` and set the two database connection strings.
Both currently point to the shared PostgreSQL instance:

```
DATABASE_URL=postgresql://datapulse:datapulse@localhost:5432/datapulse  # pragma: allowlist secret
TARGET_DB_URL=postgresql://datapulse:datapulse@localhost:5432/datapulse  # pragma: allowlist secret
```

`DATABASE_URL` is the source database (written to by the Django backend).
`TARGET_DB_URL` is the analytics database where the ETL writes its star schema
tables. In the current setup both are the same PostgreSQL instance.

Other variables you may need to adjust:

```
LOG_LEVEL=INFO        # DEBUG | INFO | WARNING | ERROR | CRITICAL
BATCH_SIZE=1000       # rows per bulk insert
```

---

## Step 5 — Run the analytics schema migrations

The migrations create the star schema and supporting tables in the target
database. They are idempotent and safe to re-run.

```
python migrations/migrate.py migrate
```

Expected output:

```
Applying V001_create_analytics_schema ... OK
Applying V002_add_performance_indexes ... OK
Applying V003_add_etl_run_tracking    ... OK
Applying V004_add_aggregation_tables  ... OK
```

Verify all four migrations are applied:

```
python migrations/migrate.py status
```

Expected output:

```
Migration Status
----------------------------------------
Applied: 4
  [x] V001_create_analytics_schema
  [x] V002_add_performance_indexes
  [x] V003_add_etl_run_tracking
  [x] V004_add_aggregation_tables
Pending: 0
```

---

## Step 6 — Seed source data (development only)

If the backend database is empty, populate it with representative mock data
before running the pipeline:

```
python -m seed.seed_analytics
```

This script is idempotent — running it more than once will not duplicate
records. Skip this step if the backend team has already populated the database.

To verify source data is present before continuing:

```python
# quick check — run from a Python shell inside the venv
from config import settings
from sqlalchemy import create_engine, text
engine = create_engine(settings["database"]["source_url"])
with engine.connect() as conn:
    for t in ["datasets", "check_results", "validation_rules"]:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(t, n)
```

Expected: each table should have at least 1 row before proceeding.

---

## Step 7 — Run the ETL pipeline

### Full run (recommended first time)

Extracts all source data, transforms it, loads it into the star schema, and
runs validation.

```
python main.py --mode full
```

### Incremental run

Extracts only records added since the last recorded watermark. Use this for
scheduled runs after the initial full load.

```
python main.py --mode incremental
```

### Dry run

Validates the pipeline logic without writing anything to the target database.
Useful for testing configuration changes.

```
python main.py --dry-run
```

### Strict mode

Fails the pipeline immediately if any validation warning is raised (instead of
continuing with warnings).

```
python main.py --mode full --strict
```

### Disable watermark (force full re-load on incremental)

```
python main.py --mode incremental --no-watermark
```

All pipeline output is written to:
- `logs/etl.log` — full log at the configured level
- `logs/etl_errors.log` — errors only

After a successful run the following tables in the target database will be
populated: `dim_datasets`, `dim_rules`, `dim_date`, `fact_quality_checks`,
`agg_daily_quality`, `etl_run_log`.

---

## Step 8 — Start the quality dashboard

```
streamlit run dashboards/quality_dashboard.py
```

Open http://localhost:8501 in your browser. Use the sidebar to select datasets,
a date range, and severity levels, then navigate between sections:

- Overview — KPI snapshot and combined trend sparkline
- Quality Trends — score over time per dataset
- Failure Analysis — failure rates by rule type and severity
- Dataset Comparison — side-by-side dataset scores
- Field-Level Issues — treemap and scrollable pill list of problem fields
- Day Patterns — average score by day of week
- Export Report — download data as CSV, Excel, or JSON

The dashboard requires the pipeline to have run at least once (Step 7).

---

## Running the tests

```
pytest tests/ -v
```

---

## Project structure

```
data-engineering/
    config/
        __init__.py         # Config loader (reads config.yaml + .env)
        config.yaml         # Application settings
    dashboards/
        quality_dashboard.py  # Streamlit dashboard
        queries.py            # SQL query templates used by the dashboard
    docs/
        DATA_DICTIONARY.md
        ETL_ARCHITECTURE.md
        QUICKSTART.md
    infrastructure/
        db.py               # Database connection helpers
        models.py           # SQLAlchemy ORM models
    migrations/
        migrate.py          # Migration runner
        V001_create_analytics_schema.py
        V002_add_performance_indexes.py
        V003_add_etl_run_tracking.py
        V004_add_aggregation_tables.py
    pipeline/
        etl/
            extract.py
            transform.py
            load.py
            validate.py
        orchestration/
            run_pipeline.py
        utils/
            logging.py
    seed/
        seed_analytics.py   # Mock data seeder for development
    tests/
    logs/                   # Created automatically on first run
    main.py                 # CLI entry point
    requirements.txt
    .env.example
```

---

## Troubleshooting

**Connection refused or OperationalError**
- Confirm PostgreSQL is running: `pg_isready -h localhost -p 5432`
- Check `DATABASE_URL` and `TARGET_DB_URL` in `.env` match your PostgreSQL
  credentials

**No data appears in the dashboard**
- Run the pipeline first: `python main.py --mode full`
- Check `logs/etl.log` for errors
- Confirm the source tables have rows (see Step 6 verification query)

**Migration failed or partially applied**
- Inspect state: `python migrations/migrate.py status`
- Check `migrations/.migration_state.json` for the last applied version

**Dashboard import error for queries module**
- Ensure you are running Streamlit from the `data-engineering/` directory, not
  from a parent folder

---

## Contact

Data Engineering Team - DataPulse Project
