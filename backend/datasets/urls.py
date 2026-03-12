"""Datasets URL configuration."""

from datasets.views import DatasetDetailView, DatasetListView, DatasetUploadView
from django.urls import path

urlpatterns = [
    path("upload", DatasetUploadView.as_view(), name="dataset-upload"),
    path("", DatasetListView.as_view(), name="dataset-list"),
    path("<int:pk>", DatasetDetailView.as_view(), name="dataset-detail"),
]
