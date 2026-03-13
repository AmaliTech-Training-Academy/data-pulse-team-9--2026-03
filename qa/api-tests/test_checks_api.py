"""Quality checks execution API tests."""

import requests
import pytest
import time
from conftest import BASE_URL


def test_run_check_on_dataset(auth_headers, uploaded_dataset, created_rule):
    """Test running quality checks on a dataset."""
    resp = requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}", headers=auth_headers)
    assert resp.status_code in [200, 201, 404]
    data = resp.json()
    assert "score" in data
    assert 0 <= data["score"] <= 100


def test_run_check_without_auth(uploaded_dataset):
    """Test running check without authentication."""
    resp = requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}")
    assert resp.status_code == 401


def test_run_check_nonexistent_dataset(auth_headers):
    """Test running check on non-existent dataset."""
    resp = requests.post(f"{BASE_URL}/api/checks/run/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_get_check_results(auth_headers, uploaded_dataset, created_rule):
    """Test retrieving check results."""
    # Run check first
    run_resp = requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}", headers=auth_headers)
    assert run_resp.status_code in [200, 201]

    # Get results
    resp = requests.get(f"{BASE_URL}/api/checks/results/{uploaded_dataset}", headers=auth_headers)
    assert resp.status_code in [200, 404]
    data = resp.json()
    assert isinstance(data, (list, dict))


def test_get_results_without_auth(uploaded_dataset):
    """Test getting results without authentication."""
    resp = requests.get(f"{BASE_URL}/api/checks/results/{uploaded_dataset}")
    assert resp.status_code == 401


def test_get_results_nonexistent_dataset(auth_headers):
    """Test getting results for non-existent dataset."""
    resp = requests.get(f"{BASE_URL}/api/checks/results/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_batch_check_execution(auth_headers, uploaded_dataset):
    """Test batch check execution."""
    batch_data = {"dataset_ids": [uploaded_dataset]}
    resp = requests.post(f"{BASE_URL}/api/scheduling/batch", headers=auth_headers, json=batch_data)
    assert resp.status_code in [200, 201, 202, 404]


def test_multiple_checks_same_dataset(auth_headers, uploaded_dataset, created_rule):
    """Test running multiple checks on same dataset."""
    # Run first check
    resp1 = requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}", headers=auth_headers)
    assert resp1.status_code in [200, 201]
    score1 = resp1.json()["score"]

    time.sleep(1)

    # Run second check
    resp2 = requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}", headers=auth_headers)
    assert resp2.status_code in [200, 201]
    score2 = resp2.json()["score"]

    # Scores should be consistent
    assert score1 == score2
