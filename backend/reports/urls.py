"""Reports URL configuration."""

from django.urls import path
from reports.views import DashboardView, DatasetReportView, QualityTrendsView

urlpatterns = [
    path("<int:dataset_id>/trends", QualityTrendsView.as_view(), name="reports-trends"),
    path("dashboard", DashboardView.as_view(), name="reports-dashboard"),
    path("<int:dataset_id>", DatasetReportView.as_view(), name="reports-detail"),
]
