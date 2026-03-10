"""API tests for Reports endpoints (report, trends, dashboard)."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_get_report(auth_client, sample_csv_content):
    """Upload, run checks, then fetch report."""
    uploaded = SimpleUploadedFile("report.csv", sample_csv_content, content_type="text/csv")
    upload_resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    dataset_id = upload_resp.json()["id"]

    # Run checks (no rules, so perfect score)
    auth_client.post(f"/api/checks/run/{dataset_id}")

    # Get report
    resp = auth_client.get(f"/api/reports/{dataset_id}")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_get_report_nonexistent_dataset(auth_client):
    resp = auth_client.get("/api/reports/99999")
    assert resp.status_code == 404


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_get_trends(auth_client, sample_csv_content):
    """Upload and run checks, then verify trends endpoint returns data."""
    uploaded = SimpleUploadedFile("trend.csv", sample_csv_content, content_type="text/csv")
    upload_resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    dataset_id = upload_resp.json()["id"]

    auth_client.post(f"/api/checks/run/{dataset_id}")

    resp = auth_client.get(f"/api/reports/{dataset_id}/trends?days=30")
    assert resp.status_code == 200


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_get_dashboard(auth_client, sample_csv_content):
    """Upload, run checks, verify dashboard shows latest score per dataset."""
    uploaded = SimpleUploadedFile("dash.csv", sample_csv_content, content_type="text/csv")
    upload_resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    dataset_id = upload_resp.json()["id"]

    auth_client.post(f"/api/checks/run/{dataset_id}")

    resp = auth_client.get("/api/reports/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1


@pytest.mark.django_db
def test_reports_unauthenticated(client):
    resp = client.get("/api/reports/99/trends")
    assert resp.status_code == 401
