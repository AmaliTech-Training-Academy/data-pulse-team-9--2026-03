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

    def test_pause_schedule(self, api_client):
        user = User.objects.create_user(email="pause@example.com", full_name="Pause User", password="password")
        api_client.force_authenticate(user=user)
        dataset = Dataset.objects.create(name="Pause Dataset", uploaded_by=user)

        # Create schedule first
        url = reverse("schedule-create")
        api_client.post(url, {"dataset_id": dataset.id, "cron_expression": "0 0 * * *"}, format="json")
        schedule = Schedule.objects.get(dataset=dataset)

        # Pause it
        pause_url = reverse("schedule-toggle", kwargs={"pk": schedule.id, "action": "pause"})
        response = api_client.patch(pause_url)

        assert response.status_code == status.HTTP_200_OK
        schedule.periodic_task.refresh_from_db()
        assert schedule.periodic_task.enabled is False

    def test_resume_schedule(self, api_client):
        user = User.objects.create_user(email="resume@example.com", full_name="Resume User", password="password")
        api_client.force_authenticate(user=user)
        dataset = Dataset.objects.create(name="Resume Dataset", uploaded_by=user)

        # Create schedule
        url = reverse("schedule-create")
        api_client.post(url, {"dataset_id": dataset.id, "cron_expression": "0 0 * * *"}, format="json")
        schedule = Schedule.objects.get(dataset=dataset)

        # Disable it manually first
        schedule.periodic_task.enabled = False
        schedule.periodic_task.save()

        # Resume it
        resume_url = reverse("schedule-toggle", kwargs={"pk": schedule.id, "action": "resume"})
        response = api_client.patch(resume_url)

        assert response.status_code == status.HTTP_200_OK
        schedule.periodic_task.refresh_from_db()
        assert schedule.periodic_task.enabled is True

    def test_delete_schedule(self, api_client):
        user = User.objects.create_user(email="delete@example.com", full_name="Delete User", password="password")
        api_client.force_authenticate(user=user)
        dataset = Dataset.objects.create(name="Delete Dataset", uploaded_by=user)

        # Create schedule
        url = reverse("schedule-create")
        api_client.post(url, {"dataset_id": dataset.id, "cron_expression": "0 0 * * *"}, format="json")
        schedule = Schedule.objects.get(dataset=dataset)
        periodic_task_id = schedule.periodic_task.id

        # Delete it
        delete_url = reverse("schedule-detail", kwargs={"pk": schedule.id})
        response = api_client.delete(delete_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Schedule.objects.filter(id=schedule.id).exists()
        assert not PeriodicTask.objects.filter(id=periodic_task_id).exists()

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
