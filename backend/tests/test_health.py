from unittest.mock import patch

import pytest
from django.db.utils import OperationalError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_health_check_healthy(client):
    """Test that the health endpoint returns 200 OK when DB and Redis are up."""
    # Mocking redis ping since we don't want to actually connect to a real reddis cache during normal tests
    with patch("redis.Redis.ping", return_value=True):
        url = reverse("health")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
        assert response.data["database"] == "up"
        assert response.data["redis"] == "up"


@pytest.mark.django_db
def test_health_check_redis_down(client):
    """Test that the health endpoint returns 503 when Redis is down."""
    with patch("redis.Redis.ping", return_value=False):
        url = reverse("health")
        response = client.get(url)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data["status"] == "unhealthy"
        assert response.data["redis"] == "down"
        assert response.data["database"] == "up"


@pytest.mark.django_db
def test_health_check_db_down(client):
    """Test that the health endpoint returns 503 when DB is down."""
    with patch("django.db.backends.utils.CursorWrapper.execute", side_effect=OperationalError("DB is down")):
        with patch("redis.Redis.ping", return_value=True):
            url = reverse("health")
            response = client.get(url)
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert response.data["status"] == "unhealthy"
            assert response.data["database"] == "down"
            assert response.data["redis"] == "up"
