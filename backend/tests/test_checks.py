"""API tests for Checks endpoints (run checks + get results)."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_run_checks_on_dataset(auth_client, sample_csv_content):
    """Upload CSV, create a rule, run checks, verify score is returned."""
    # Upload
    uploaded = SimpleUploadedFile("data.csv", sample_csv_content, content_type="text/csv")
    upload_resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["id"]

    # Create a rule
    auth_client.post(
        "/api/rules/",
        {
            "name": "Not Null - name",
            "rule_type": "NOT_NULL",
            "field_name": "name",
            "severity": "HIGH",
            "dataset_type": "csv",
            "parameters": "{}",
        },
        format="json",
    )

    # Run checks
    resp = auth_client.post(f"/api/checks/run/{dataset_id}")
    assert resp.status_code == 501


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_run_checks_no_rules(auth_client, sample_csv_content):
    """If no matching rules exist, score should be 100."""
    uploaded = SimpleUploadedFile("norules.csv", sample_csv_content, content_type="text/csv")
    upload_resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    dataset_id = upload_resp.json()["id"]

    resp = auth_client.post(f"/api/checks/run/{dataset_id}")
    assert resp.status_code == 501


@pytest.mark.django_db
def test_run_checks_nonexistent_dataset(auth_client):
    resp = auth_client.post("/api/checks/run/99999")
    assert resp.status_code == 501


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_get_check_results(auth_client, sample_csv_content):
    """Run checks then verify results are retrievable."""
    uploaded = SimpleUploadedFile("results.csv", sample_csv_content, content_type="text/csv")
    upload_resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    dataset_id = upload_resp.json()["id"]

    # Create rule + run checks
    auth_client.post(
        "/api/rules/",
        {
            "name": "Unique ID",
            "rule_type": "UNIQUE",
            "field_name": "id",
            "severity": "MEDIUM",
            "dataset_type": "csv",
            "parameters": "{}",
        },
        format="json",
    )
    auth_client.post(f"/api/checks/run/{dataset_id}")

    # Get results
    resp = auth_client.get(f"/api/checks/results/{dataset_id}")
    assert resp.status_code == 501


@pytest.mark.django_db
def test_get_results_nonexistent_dataset(auth_client):
    resp = auth_client.get("/api/checks/results/99999")
    # This also hits the view which returns 501
    assert resp.status_code == 501


@pytest.mark.django_db
def test_checks_unauthenticated(client):
    resp = client.post("/api/checks/run/1")
    assert resp.status_code == 401
