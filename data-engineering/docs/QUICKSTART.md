# DataPulse Data Engineering - Quick Start

## Installation

```bash
cd data-engineering
pip install -r requirements.txt
```

## Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Set database URLs:


## Database Setup

Run migrations:
```bash
python migrations/migrate.py migrate
```

Check migration status:
```bash
python migrations/migrate.py status
```

## Running the Pipeline

Full extraction:
```bash
python main.py --mode full
```

Incremental extraction:
```bash
python main.py --mode incremental
```

Dry run (no writes):
```bash
python main.py --dry-run
```

## Dashboard

Start the Streamlit dashboard:
```bash
streamlit run dashboards/quality_dashboard.py
```

Access at: http://localhost:8501

## Development

### Project Structure

```
data-engineering/
|-- config/
|   |-- __init__.py       # Config loader
|   |-- config.yaml       # Settings
|-- dashboards/
|   |-- quality_dashboard.py
|-- docs/
|   |-- DATA_DICTIONARY.md
|   |-- ETL_ARCHITECTURE.md
|-- infrastructure/
|   |-- db.py             # Database connections
|   |-- models.py         # ORM models
|-- migrations/
|   |-- migrate.py        # Migration runner
|   |-- V001_*.py         # Migration scripts
|-- pipeline/
|   |-- etl/
|   |   |-- extract.py
|   |   |-- transform.py
|   |   |-- load.py
|   |   |-- validate.py
|   |-- orchestration/
|   |   |-- run_pipeline.py
|   |-- utils/
|       |-- logging.py
|-- tests/
|-- logs/
|-- main.py               # Entry point
```

### Running Tests

```bash
pytest tests/ -v
```

### Seeding Test Data

```bash
python -m seed.seed_analytics
```

## Troubleshooting

### Common Issues

**Connection refused**
- Verify PostgreSQL is running
- Check DATABASE_URL in .env

**No data in dashboard**
- Run pipeline first: `python main.py`
- Check logs/etl.log for errors

**Migration failed**
- Check migrations/.migration_state.json
- Run `python migrations/migrate.py status`

### Logs

- All logs: `logs/etl.log`
- Errors only: `logs/etl_errors.log`

## Contact

Data Engineering Team - DataPulse Project
