from datetime import datetime
from typing import Any, List, Optional

from checks.models import QualityScore
from datasets.models import Dataset
from django.db.models import Prefetch, QuerySet
from rest_framework.exceptions import ValidationError


def get_latest_report(dataset: Dataset) -> Optional[QualityScore]:
    """Fetch the most recent quality score for a dataset."""
    return QualityScore.objects.filter(dataset=dataset).order_by("-checked_at").first()


def get_report_by_id(report_id: int) -> Optional[QualityScore]:
    """Fetch a specific quality report by its ID."""
    return QualityScore.objects.select_related("dataset").filter(id=report_id).first()


def get_dataset_trends(dataset: Dataset, start_date: Optional[str] = None, end_date: Optional[str] = None) -> QuerySet:
    """Fetch historical quality scores for a dataset, optionally filtered by date."""

    def validate_date(date_str: str) -> None:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValidationError({"detail": f"Invalid date format for '{date_str}'. Expected YYYY-MM-DD."})

    queryset = QualityScore.objects.filter(dataset=dataset)
    if start_date:
        validate_date(start_date)
        queryset = queryset.filter(checked_at__date__gte=start_date)
    if end_date:
        validate_date(end_date)
        queryset = queryset.filter(checked_at__date__lte=end_date)
    return queryset.order_by("checked_at")


def get_dashboard_summary(user: Any) -> List[QualityScore]:
    """Fetch the latest score for each dataset the user can access."""
    prefetch = Prefetch(
        "qualityscore_set", queryset=QualityScore.objects.order_by("-checked_at"), to_attr="latest_scores"
    )

    if getattr(user, "role", "USER") == "ADMIN":
        dataset_qs = Dataset.objects.prefetch_related(prefetch).all()
    else:
        dataset_qs = Dataset.objects.prefetch_related(prefetch).filter(uploaded_by=user)

    latest_scores = []
    for dataset in dataset_qs:
        if dataset.latest_scores:
            latest_scores.append(dataset.latest_scores[0])
        else:
            latest_scores.append(
                QualityScore(
                    dataset=dataset,
                    score=None,
                    total_rules=None,
                    passed_rules=None,
                    failed_rules=None,
                    checked_at=None,
                )
            )

    return latest_scores
