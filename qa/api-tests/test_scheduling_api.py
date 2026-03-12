"""Scheduling API tests."""

import requests
import pytest
from conftest import BASE_URL


def test_create_schedule(auth_headers, uploaded_dataset):
    """Test creating a new schedule."""
    schedule_data = {"dataset_id": uploaded_dataset, "cron_expression": "0 9 * * 1"}
    resp = requests.post(f"{BASE_URL}/api/schedules/", headers=auth_headers, json=schedule_data)
    assert resp.status_code in [200, 201]
    data = resp.json()
    assert "id" in data
    return data["id"]


def test_create_schedule_without_auth(uploaded_dataset):
    """Test creating schedule without authentication."""
    schedule_data = {"dataset_id": uploaded_dataset, "cron_expression": "0 9 * * 1"}
    resp = requests.post(f"{BASE_URL}/api/schedules/", json=schedule_data)
    assert resp.status_code == 401


def test_create_schedule_invalid_cron(auth_headers, uploaded_dataset):
    """Test creating schedule with invalid cron expression."""
    schedule_data = {"dataset_id": uploaded_dataset, "cron_expression": "invalid-cron"}
    resp = requests.post(f"{BASE_URL}/api/schedules/", headers=auth_headers, json=schedule_data)
    assert resp.status_code in [400, 422]


def test_list_schedules(auth_headers):
    """Test listing all schedules."""
    resp = requests.get(f"{BASE_URL}/api/schedules/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Response can be list or paginated object
    if isinstance(data, dict):
        assert "results" in data or "total" in data
    else:
        assert isinstance(data, list)


def test_list_schedules_without_auth():
    """Test listing schedules without authentication."""
    resp = requests.get(f"{BASE_URL}/api/schedules/")
    assert resp.status_code == 401


def test_pause_schedule(auth_headers, uploaded_dataset):
    """Test pausing a schedule."""
    # Create schedule first
    schedule_data = {"dataset_id": uploaded_dataset, "cron_expression": "0 10 * * 1"}
    create_resp = requests.post(f"{BASE_URL}/api/schedules/", headers=auth_headers, json=schedule_data)
    if create_resp.status_code not in [200, 201]:
        pytest.skip("Scheduling endpoints not working")
    schedule_id = create_resp.json()["id"]

    # Pause it
    resp = requests.patch(f"{BASE_URL}/api/schedules/{schedule_id}/pause/", headers=auth_headers)
    assert resp.status_code in [200, 204]


def test_pause_nonexistent_schedule(auth_headers):
    """Test pausing non-existent schedule."""
    resp = requests.patch(f"{BASE_URL}/api/schedules/99999/pause/", headers=auth_headers)
    assert resp.status_code == 404


def test_resume_schedule(auth_headers, uploaded_dataset):
    """Test resuming a paused schedule."""
    # Create and pause schedule first
    schedule_data = {"dataset_id": uploaded_dataset, "cron_expression": "0 11 * * 1"}
    create_resp = requests.post(f"{BASE_URL}/api/schedules/", headers=auth_headers, json=schedule_data)
    if create_resp.status_code not in [200, 201]:
        pytest.skip("Scheduling endpoints not working")
    schedule_id = create_resp.json()["id"]

    # Pause it first
    requests.patch(f"{BASE_URL}/api/schedules/{schedule_id}/pause/", headers=auth_headers)

    # Resume it
    resp = requests.patch(f"{BASE_URL}/api/schedules/{schedule_id}/resume/", headers=auth_headers)
    assert resp.status_code in [200, 204]


def test_resume_nonexistent_schedule(auth_headers):
    """Test resuming non-existent schedule."""
    resp = requests.patch(f"{BASE_URL}/api/schedules/99999/resume/", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_schedule(auth_headers, uploaded_dataset):
    """Test deleting a schedule."""
    # Create schedule first
    schedule_data = {"dataset_id": uploaded_dataset, "cron_expression": "0 12 * * 1"}
    create_resp = requests.post(f"{BASE_URL}/api/schedules/", headers=auth_headers, json=schedule_data)
    if create_resp.status_code not in [200, 201]:
        pytest.skip("Scheduling endpoints not working")
    schedule_id = create_resp.json()["id"]

    # Delete it
    resp = requests.delete(f"{BASE_URL}/api/schedules/{schedule_id}/", headers=auth_headers)
    assert resp.status_code in [200, 204]


def test_delete_nonexistent_schedule(auth_headers):
    """Test deleting non-existent schedule."""
    resp = requests.delete(f"{BASE_URL}/api/schedules/99999/", headers=auth_headers)
    assert resp.status_code == 404


def test_set_alert_threshold(auth_headers, uploaded_dataset):
    """Test setting alert threshold for a dataset."""
    alert_data = {"threshold": 75}
    resp = requests.post(f"{BASE_URL}/api/schedules/alerts/{uploaded_dataset}/", headers=auth_headers, json=alert_data)
    assert resp.status_code in [200, 201]
    data = resp.json()
    assert data["threshold"] == 75


def test_set_alert_invalid_threshold(auth_headers, uploaded_dataset):
    """Test setting invalid alert threshold."""
    alert_data = {"threshold": 150}  # Invalid: > 100
    resp = requests.post(f"{BASE_URL}/api/schedules/alerts/{uploaded_dataset}/", headers=auth_headers, json=alert_data)
    assert resp.status_code in [400, 422]


def test_set_alert_without_auth(uploaded_dataset):
    """Test setting alert without authentication."""
    alert_data = {"threshold": 75}
    resp = requests.post(f"{BASE_URL}/api/schedules/alerts/{uploaded_dataset}/", json=alert_data)
    assert resp.status_code == 401


def test_set_alert_nonexistent_dataset(auth_headers):
    """Test setting alert for non-existent dataset."""
    alert_data = {"threshold": 75}
    resp = requests.post(f"{BASE_URL}/api/schedules/alerts/99999/", headers=auth_headers, json=alert_data)
    assert resp.status_code == 404
