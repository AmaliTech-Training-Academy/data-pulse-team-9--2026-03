"""Upload tests - IMPLEMENTED."""

import io
import pytest


@pytest.mark.django_db
def test_upload_csv_success(auth_client):
    """Test uploading a valid CSV file."""
    csv_content = b"id,name,age\n1,Alice,30\n2,Bob,25\n3,Carol,35\n"
    from django.core.files.uploadedfile import SimpleUploadedFile

    uploaded = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
    resp = auth_client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "test"
    assert data["file_type"] == "csv"
    assert data["row_count"] == 3
    assert data["column_count"] == 3
    assert data["status"] == "PENDING"
