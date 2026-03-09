"""Checks URL configuration."""

from django.urls import path
from checks.views import RunChecksView, CheckResultsView

urlpatterns = [
    path("run/<int:dataset_id>", RunChecksView.as_view(), name="checks-run"),
    path("results/<int:dataset_id>", CheckResultsView.as_view(), name="checks-results"),
]
