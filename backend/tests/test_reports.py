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
    assert len(data) > 0  # Score is calculated since run_checks works


@pytest.mark.django_db
def test_reports_unauthenticated(client):
    resp = client.get("/api/reports/99/trends")
    assert resp.status_code == 401


'''
@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_get_dashboard_with_unchecked_dataset(auth_client, sample_csv_content):
    """Verify dashboard includes datasets without checks (null score)."""
    uploaded = SimpleUploadedFile("dash2.csv", sample_csv_content, content_type="text/csv")
    upload_resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    dataset_id = upload_resp.json()["id"]

    resp = auth_client.get("/api/reports/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

    # Check that our dataset is right there with null score
    dataset_summary = next(item for item in data if item["dataset_id"] == dataset_id)
    assert dataset_summary["score"] is None
    assert dataset_summary["checked_at"] is None

'''


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_get_trends_date_filters(auth_client, sample_csv_content):
    """Verify trends endpoint supports start_date and end_date filters."""
    from datetime import date, timedelta

    uploaded = SimpleUploadedFile("trend_filter.csv", sample_csv_content, content_type="text/csv")
    upload_resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    dataset_id = upload_resp.json()["id"]

    # Run check
    auth_client.post(f"/api/checks/run/{dataset_id}")

    # Test filtering (should match since we just ran it today)
    today = date.today()
    start_date = (today - timedelta(days=1)).isoformat()
    end_date = (today + timedelta(days=1)).isoformat()

    resp = auth_client.get(f"/api/reports/{dataset_id}/trends?start_date={start_date}&end_date={end_date}")

    assert resp.status_code == 200
    assert len(resp.json()["trends"]) == 1 if "trends" in resp.json() else len(resp.json()) == 1

    # Test filtering out of range
    future_date = (today + timedelta(days=10)).isoformat()
    resp_future = auth_client.get(f"/api/reports/{dataset_id}/trends?start_date={future_date}")
    assert resp_future.status_code == 200
    assert len(resp_future.json()["trends"]) == 0 if "trends" in resp_future.json() else len(resp_future.json()) == 0


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_get_trends_invalid_date_format(auth_client, sample_csv_content):
    """Verify trends endpoint rejects invalid date format with 400 Bad Request."""
    uploaded = SimpleUploadedFile("trend_invalid.csv", sample_csv_content, content_type="text/csv")
    upload_resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    dataset_id = upload_resp.json()["id"]

    resp = auth_client.get(f"/api/reports/{dataset_id}/trends?start_date=invalid-date")
    assert resp.status_code == 400
    assert "Expected YYYY-MM-DD" in resp.json()["detail"]
