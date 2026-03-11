import pytest
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from infrastructure.db import AnalyticsBase
from infrastructure import models  # noqa: F401


@pytest.fixture
def sample_raw_data():
    """Mock DataFrame mimicking the extract query output."""
    now = datetime.now()
    return pd.DataFrame(
        [
            {
                "id": 1,
                "dataset_id": 10,
                "rule_id": 100,
                "passed": True,
                "failed_rows": 0,
                "total_rows": 500,
                "checked_at": now - timedelta(days=2),
                "rule_name": "Name not null",
                "rule_type": "NOT_NULL",
                "severity": "HIGH",
                "field_name": "name",
                "dataset_type": "employee",
                "is_active": True,
                "dataset_name": "employees.csv",
                "file_type": "csv",
                "dataset_row_count": 500,
                "column_count": 7,
                "uploaded_at": now - timedelta(days=10),
                "dataset_status": "VALIDATED",
            },
            {
                "id": 2,
                "dataset_id": 10,
                "rule_id": 101,
                "passed": False,
                "failed_rows": 25,
                "total_rows": 500,
                "checked_at": now - timedelta(days=2),
                "rule_name": "Age range",
                "rule_type": "RANGE",
                "severity": "HIGH",
                "field_name": "age",
                "dataset_type": "employee",
                "is_active": True,
                "dataset_name": "employees.csv",
                "file_type": "csv",
                "dataset_row_count": 500,
                "column_count": 7,
                "uploaded_at": now - timedelta(days=10),
                "dataset_status": "VALIDATED",
            },
            {
                "id": 3,
                "dataset_id": 20,
                "rule_id": 102,
                "passed": True,
                "failed_rows": 0,
                "total_rows": 300,
                "checked_at": now - timedelta(days=1),
                "rule_name": "Rating range",
                "rule_type": "RANGE",
                "severity": "MEDIUM",
                "field_name": "rating",
                "dataset_type": "feedback",
                "is_active": True,
                "dataset_name": "feedback.json",
                "file_type": "json",
                "dataset_row_count": 300,
                "column_count": 5,
                "uploaded_at": now - timedelta(days=5),
                "dataset_status": "VALIDATED",
            },
        ]
    )


@pytest.fixture
def in_memory_engine():
    """SQLite in-memory engine with analytics tables created."""
    engine = create_engine("sqlite:///:memory:")
    AnalyticsBase.metadata.create_all(engine)
    return engine
