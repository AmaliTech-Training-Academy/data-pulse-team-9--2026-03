from typing import Any, List, Optional

from checks.models import QualityScore
from datasets.models import Dataset
from django.db.models import QuerySet


def get_latest_report(dataset: Dataset) -> Optional[QualityScore]:
    """Fetch the most recent quality score for a dataset."""
    return QualityScore.objects.filter(dataset=dataset).order_by("-checked_at").first()


def get_report_by_id(report_id: int) -> Optional[QualityScore]:
    """Fetch a specific quality report by its ID."""
    return QualityScore.objects.select_related("dataset").filter(id=report_id).first()


def get_dataset_trends(dataset: Dataset, start_date: Optional[str] = None, end_date: Optional[str] = None) -> QuerySet:
    """Fetch historical quality scores for a dataset, optionally filtered by date."""
    queryset = QualityScore.objects.filter(dataset=dataset)
    if start_date:
        queryset = queryset.filter(checked_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(checked_at__date__lte=end_date)
    return queryset.order_by("-checked_at")


def get_dashboard_summary(user: Any) -> List[QualityScore]:
    """Fetch the latest score for each dataset the user can access."""
    if getattr(user, "role", "USER") == "ADMIN":
        dataset_qs = Dataset.objects.all()
    else:
        dataset_qs = Dataset.objects.filter(uploaded_by=user)

    latest_scores = []
    for dataset in dataset_qs:
        qs = get_latest_report(dataset)
        if qs:
            latest_scores.append(qs)

    return latest_scores
