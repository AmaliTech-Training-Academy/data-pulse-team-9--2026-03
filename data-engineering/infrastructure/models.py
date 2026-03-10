from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey

from infrastructure.db import AnalyticsBase


class DimDataset(AnalyticsBase):
    __tablename__ = "dim_datasets"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    file_type = Column(String(10))
    row_count = Column(Integer)
    column_count = Column(Integer)
    status = Column(String(20))
    uploaded_at = Column(DateTime)


class DimRule(AnalyticsBase):
    __tablename__ = "dim_rules"

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    field_name = Column(String(255))
    rule_type = Column(String(20))
    severity = Column(String(10))
    dataset_type = Column(String(100))
    is_active = Column(Boolean)


class DimDate(AnalyticsBase):
    __tablename__ = "dim_date"

    date_key = Column(Integer, primary_key=True)
    full_date = Column(Date)
    day_of_week = Column(Integer)
    month = Column(Integer)
    quarter = Column(Integer)
    year = Column(Integer)


class FactQualityCheck(AnalyticsBase):
    __tablename__ = "fact_quality_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("dim_datasets.id"))
    rule_id = Column(Integer, ForeignKey("dim_rules.id"))
    date_key = Column(Integer, ForeignKey("dim_date.date_key"))
    passed = Column(Boolean)
    failed_rows = Column(Integer)
    total_rows = Column(Integer)
    score = Column(Float)
    checked_at = Column(DateTime)
