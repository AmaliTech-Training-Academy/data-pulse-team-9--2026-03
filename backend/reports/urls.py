"""Reports URL configuration."""

from django.urls import path
from reports.views import QualityTrendsView, DatasetReportView, DashboardView

urlpatterns = [
    path("trends", QualityTrendsView.as_view(), name="reports-trends"),
    path("dashboard", DashboardView.as_view(), name="reports-dashboard"),
    path("<int:dataset_id>", DatasetReportView.as_view(), name="reports-detail"),
]
