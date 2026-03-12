"""Reports URL configuration."""

from django.urls import path
from reports.views import BulkQualityTrendsView, DashboardView, DatasetReportView, QualityTrendsView

urlpatterns = [
    path("<int:dataset_id>/trends", QualityTrendsView.as_view(), name="reports-trends"),
    path("bulk-trends", BulkQualityTrendsView.as_view(), name="reports-bulk-trends"),
    path("dashboard", DashboardView.as_view(), name="reports-dashboard"),
    path("<int:dataset_id>", DatasetReportView.as_view(), name="reports-detail"),
]
