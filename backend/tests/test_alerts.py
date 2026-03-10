import os

import pandas as pd
import pytest
from authentication.models import User
from datasets.models import Dataset, DatasetFile
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rules.models import ValidationRule
from schedule.models import AlertConfig
from schedule.tasks import run_scheduled_checks


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestAlertSystem:
    def test_set_alert_threshold(self, api_client):
        user = User.objects.create_user(
            email="alert@example.com", full_name="Alert User", password="password"  # pragma: allowlist secret
        )
        api_client.force_authenticate(user=user)
        dataset = Dataset.objects.create(name="Alert Dataset", uploaded_by=user)

        url = reverse("alert-threshold", kwargs={"dataset_id": dataset.id})
        data = {"threshold": 75}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert AlertConfig.objects.filter(dataset=dataset, threshold=75).exists()

    def test_update_alert_threshold(self, api_client):
        user = User.objects.create_user(
            email="update_alert@example.com",
            full_name="Update Alert User",
            password="password",  # pragma: allowlist secret
        )
        api_client.force_authenticate(user=user)
        dataset = Dataset.objects.create(name="Update Alert Dataset", uploaded_by=user)
        AlertConfig.objects.create(dataset=dataset, threshold=50)

        url = reverse("alert-threshold", kwargs={"dataset_id": dataset.id})
        data = {"threshold": 85}

        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert AlertConfig.objects.get(dataset=dataset).threshold == 85

    def test_alert_email_sent_below_threshold(self, api_client):
        user = User.objects.create_user(
            email="sender@example.com", full_name="Sender User", password="password"  # pragma: allowlist secret
        )
        dataset = Dataset.objects.create(name="Email Alert Dataset", uploaded_by=user, file_type="csv")
        AlertConfig.objects.create(dataset=dataset, threshold=90)

        # Create a CSV that will fail a rule (score will be 0)
        csv_file_path = "test_alert_data.csv"
        df = pd.DataFrame({"id": [1], "value": [None]})
        df.to_csv(csv_file_path, index=False)
        DatasetFile.objects.create(dataset=dataset, file_path=csv_file_path, original_filename="test_alert_data.csv")

        ValidationRule.objects.create(
            name="Check nulls", dataset_type="csv", field_name="value", rule_type="NOT_NULL", severity="HIGH"
        )

        # Clear outbox
        mail.outbox = []

        # Run task
        run_scheduled_checks(dataset.id)

        # Verify email sent
        assert len(mail.outbox) == 1
        assert "Data Quality Alert" in mail.outbox[0].subject
        assert dataset.name in mail.outbox[0].body

        # Verify suppression active
        alert_config = AlertConfig.objects.get(dataset=dataset)
        assert alert_config.is_alert_active is True

        # Run again, should NOT send another email (suppression)
        mail.outbox = []
        run_scheduled_checks(dataset.id)
        assert len(mail.outbox) == 0

        # Cleanup
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)

    def test_alert_recovery_and_resend(self, api_client):
        user = User.objects.create_user(
            email="recovery@example.com", full_name="Recovery User", password="password"  # pragma: allowlist secret
        )
        dataset = Dataset.objects.create(name="Recovery Dataset", uploaded_by=user, file_type="csv")
        alert_config = AlertConfig.objects.create(dataset=dataset, threshold=90, is_alert_active=True)

        # Create a CSV that will pass all rules (score will be 100)
        csv_file_path = "test_recovery_data.csv"
        df = pd.DataFrame({"id": [1], "value": [10]})
        df.to_csv(csv_file_path, index=False)
        DatasetFile.objects.create(dataset=dataset, file_path=csv_file_path, original_filename="test_recovery_data.csv")

        ValidationRule.objects.create(
            name="Check nulls", dataset_type="csv", field_name="value", rule_type="NOT_NULL", severity="HIGH"
        )

        # Run task - should recover
        run_scheduled_checks(dataset.id)

        alert_config.refresh_from_db()
        assert alert_config.is_alert_active is False

        # Now fail it again, should send a new email
        mail.outbox = []
        df_fail = pd.DataFrame({"id": [1], "value": [None]})
        df_fail.to_csv(csv_file_path, index=False)

        run_scheduled_checks(dataset.id)
        assert len(mail.outbox) == 1

        # Cleanup
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
