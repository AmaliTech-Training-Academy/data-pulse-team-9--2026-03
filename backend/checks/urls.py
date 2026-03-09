"""Checks URL configuration."""

from checks.views import CheckResultsView, RunChecksView
from django.urls import path

urlpatterns = [
    path("run/<int:dataset_id>", RunChecksView.as_view(), name="checks-run"),
    path("results/<int:dataset_id>", CheckResultsView.as_view(), name="checks-results"),
]
