import pytest
from authentication.models import User
from datasets.models import Dataset
from django.urls import reverse
from django_celery_beat.models import PeriodicTask
from rest_framework import status
from rest_framework.test import APIClient
from schedule.models import Schedule


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestScheduleAPI:
    def test_create_schedule_success(self, api_client):
        user = User.objects.create_user(email="test@example.com", full_name="Test User", password="password")
        api_client.force_authenticate(user=user)

        dataset = Dataset.objects.create(name="Test Dataset", uploaded_by=user)
        url = reverse("schedule-create")
        data = {"dataset_id": dataset.id, "cron_expression": "0 0 * * *"}  # Every day at midnight

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Schedule.objects.filter(dataset=dataset).exists()
        assert PeriodicTask.objects.filter(name=f"Data Quality Check - Dataset {dataset.id}").exists()

    def test_create_schedule_invalid_cron(self, api_client):
        user = User.objects.create_user(email="test2@example.com", full_name="Test User 2", password="password")
        api_client.force_authenticate(user=user)

        dataset = Dataset.objects.create(name="Test Dataset 2", uploaded_by=user)
        url = reverse("schedule-create")
        data = {"dataset_id": dataset.id, "cron_expression": "invalid cron"}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.data["code"] == "validation_error"

    def test_create_schedule_wrong_parts_count(self, api_client):
        user = User.objects.create_user(email="test3@example.com", full_name="Test User 3", password="password")
        api_client.force_authenticate(user=user)

        dataset = Dataset.objects.create(name="Test Dataset 3", uploaded_by=user)
        url = reverse("schedule-create")
        data = {"dataset_id": dataset.id, "cron_expression": "* * * *"}  # Only 4 parts

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
