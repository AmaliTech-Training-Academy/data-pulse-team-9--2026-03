import pytest
from rest_framework import status


@pytest.mark.django_db
def test_datasets_protected(client):
    """Verify that /api/datasets/ requires authentication."""
    response = client.get("/api/datasets/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_rules_protected(client):
    """Verify that /api/rules/ requires authentication."""
    response = client.get("/api/rules/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
