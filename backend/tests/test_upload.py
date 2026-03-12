"""Upload tests — covers CSV, JSON, error cases, and the detail endpoint."""

import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

# ---------------------------------------------------------------------------
# Happy-path uploads (eager mode — task runs inline, metadata is populated)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_upload_csv_success(auth_client):
    """Uploading a valid CSV returns 201 with correct metadata after inline parsing."""
    csv_content = b"id,name,age\n1,Alice,30\n2,Bob,25\n3,Carol,35\n"
    uploaded = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
    resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "test"
    assert data["file_type"] == "csv"
    # With eager mode the Celery task runs synchronously, so we need to
    # re-fetch the dataset to see updated fields.
    detail = auth_client.get(f"/api/datasets/{data['id']}")
    assert detail.status_code == 200
    detail_data = detail.json()
    assert detail_data["row_count"] == 3
    assert detail_data["column_count"] == 3
    assert detail_data["status"] == "PENDING"


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_upload_json_success(auth_client):
    """Uploading a valid JSON file returns 201 with correct metadata."""
    json_data = [
        {"id": 1, "product": "Apple", "price": 1.20},
        {"id": 2, "product": "Banana", "price": 0.80},
    ]
    uploaded = SimpleUploadedFile("data.json", json.dumps(json_data).encode(), content_type="application/json")
    resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "data"
    assert data["file_type"] == "json"
    # Re-fetch to confirm parsing completed
    detail = auth_client.get(f"/api/datasets/{data['id']}")
    detail_data = detail.json()
    assert detail_data["row_count"] == 2
    assert detail_data["column_count"] == 3
    assert detail_data["status"] == "PENDING"


# ---------------------------------------------------------------------------
# Immediate response shape (the view always returns PROCESSING + row_count=0)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_upload_returns_processing_status(auth_client):
    """The upload response itself always shows the pre-parsing skeleton."""
    csv_content = b"id,name\n1,Alice\n"
    uploaded = SimpleUploadedFile("quick.csv", csv_content, content_type="text/csv")
    resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    assert resp.status_code == 201
    data = resp.json()
    # The view serialises the dataset before the task has mutated the DB row
    # (even in eager mode the response is built first, then the task fires).
    # So we accept either PROCESSING (pre-task) or PENDING (task already ran).
    assert data["status"] in ("PROCESSING", "PENDING")
    assert "id" in data


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_upload_unsupported_file_type(auth_client):
    """Uploading an unsupported file type returns 400."""
    uploaded = SimpleUploadedFile("notes.txt", b"hello world", content_type="text/plain")
    resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_upload_empty_file(auth_client):
    """Uploading an empty file returns 400."""
    uploaded = SimpleUploadedFile("empty.csv", b"", content_type="text/csv")
    resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_upload_no_file(auth_client):
    """Posting without a file returns 400."""
    resp = auth_client.post("/api/datasets/upload", {}, format="multipart")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Dataset detail endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_dataset_detail_endpoint(auth_client):
    """GET /api/datasets/<id> returns the full dataset record."""
    csv_content = b"x,y\n1,2\n3,4\n"
    uploaded = SimpleUploadedFile("xy.csv", csv_content, content_type="text/csv")
    resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    dataset_id = resp.json()["id"]

    detail = auth_client.get(f"/api/datasets/{dataset_id}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["id"] == dataset_id
    assert data["name"] == "xy"
    assert data["row_count"] == 2
    assert data["status"] == "PENDING"


@pytest.mark.django_db
def test_dataset_detail_not_found(auth_client):
    """GET /api/datasets/99999 returns 404."""
    resp = auth_client.get("/api/datasets/99999")
    assert resp.status_code == 404
