"""SQLAlchemy ORM for analytics tables."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base

AnalyticsBase = declarative_base()


class DimDataset(AnalyticsBase):
    __tablename__ = "dim_datasets"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    file_type = Column(String(10))
    row_count = Column(Integer)
    uploaded_at = Column(DateTime)


class DimRule(AnalyticsBase):
    __tablename__ = "dim_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    field_name = Column(String(255))
    rule_type = Column(String(20))
    severity = Column(String(10))


class DimDate(AnalyticsBase):
    __tablename__ = "dim_date"
    date_key = Column(Integer, primary_key=True)
    full_date = Column(Date)
    day_of_week = Column(Integer)
    month = Column(Integer)
    year = Column(Integer)


class FactQualityCheck(AnalyticsBase):
    __tablename__ = "fact_quality_checks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("dim_datasets.id"))
    rule_id = Column(Integer, ForeignKey("dim_rules.id"))
    rule_type = Column(String(20))
    passed = Column(Boolean)
    failed_rows = Column(Integer)
    total_rows = Column(Integer)
    score = Column(Float)
    severity = Column(String(10))
    checked_at = Column(DateTime)
