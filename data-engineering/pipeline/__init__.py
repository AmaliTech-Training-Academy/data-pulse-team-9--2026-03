"""
DataPulse ETL Pipeline

Main entry points:
- run(): Execute the ETL pipeline
- run_with_guard(): Execute with strict validation
"""
from pipeline.orchestration.run_pipeline import run, run_with_guard
from pipeline.models import (
    TransformResult,
    ValidationResult,
    PipelineResult,
    LoadSummary,
    Severity,
    IntegrityWarning,
)

__all__ = [
    "run",
    "run_with_guard",
    "TransformResult",
    "ValidationResult",
    "PipelineResult",
    "LoadSummary",
    "Severity",
    "IntegrityWarning",
]
