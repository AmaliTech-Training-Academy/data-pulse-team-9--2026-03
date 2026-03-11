from datetime import timedelta

import pytest
from audit.models import AuditLog
from datasets.models import Dataset
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com", password="password123", full_name="Test User"  # pragma: allowlist secret
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def dataset(db):
    return Dataset.objects.create(name="Test Dataset", file_type="csv")


@pytest.fixture
def audit_logs(dataset):
    logs = []
    for i in range(5):
        logs.append(
            AuditLog.objects.create(
                dataset=dataset,
                triggered_by=f"user_{i}@example.com",
                trigger_type="manual",
                score=0.8 + (i * 0.01),
            )
        )
    return logs


@pytest.mark.django_db
class TestAuditLogModel:
    def test_audit_log_creation(self, dataset):
        log = AuditLog.objects.create(dataset=dataset, triggered_by="system", trigger_type="scheduled", score=0.95)
        assert log.id is not None
        assert log.trigger_type == "scheduled"
        assert log.triggered_by == "system"

    def test_append_only_update_prevention(self, dataset):
        log = AuditLog.objects.create(
            dataset=dataset, triggered_by="admin@example.com", trigger_type="manual", score=0.9
        )
        with pytest.raises(RuntimeError, match="AuditLog entries are append-only and cannot be updated."):
            log.score = 1.0
            log.save()

    def test_append_only_delete_prevention(self, dataset):
        log = AuditLog.objects.create(
            dataset=dataset, triggered_by="admin@example.com", trigger_type="manual", score=0.9
        )
        with pytest.raises(RuntimeError, match="AuditLog entries are append-only and cannot be deleted."):
            log.delete()


@pytest.mark.django_db
class TestAuditLogAPI:
    def test_list_audit_logs_unauthorized(self, api_client, audit_logs):
        url = reverse("audit-log-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_audit_logs_authorized(self, authenticated_client, audit_logs):
        url = reverse("audit-log-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5

    def test_filter_by_dataset(self, authenticated_client, dataset, audit_logs):
        other_dataset = Dataset.objects.create(name="Other", file_type="json")
        AuditLog.objects.create(
            dataset=other_dataset, triggered_by="other@example.com", trigger_type="manual", score=0.5
        )

        url = reverse("audit-log-list")
        response = authenticated_client.get(url, {"dataset_id": dataset.id})
        assert response.status_code == status.HTTP_200_OK
        assert all(item["dataset"] == dataset.id for item in response.data["results"])
        assert len(response.data["results"]) == 5

    def test_filter_by_date_range(self, authenticated_client, audit_logs):
        url = reverse("audit-log-list")
        now = timezone.now()

        start_date = (now - timedelta(minutes=1)).isoformat()
        response = authenticated_client.get(url, {"start_date": start_date})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5

        future_date = (now + timedelta(days=1)).isoformat()
        response = authenticated_client.get(url, {"start_date": future_date})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0
