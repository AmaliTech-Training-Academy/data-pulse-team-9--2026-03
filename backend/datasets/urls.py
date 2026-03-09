"""Datasets URL configuration."""

from django.urls import path
from datasets.views import DatasetUploadView, DatasetListView

urlpatterns = [
    path("upload", DatasetUploadView.as_view(), name="dataset-upload"),
    path("", DatasetListView.as_view(), name="dataset-list"),
]
