"""Quality reports and trends API tests."""

import time
import requests
import pytest
from conftest import BASE_URL


def test_get_quality_report(auth_headers, uploaded_dataset, created_rule):
    """Test generating quality report for a dataset."""
    # Run check first
    requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}", headers=auth_headers)

    # Get report
    resp = requests.get(f"{BASE_URL}/api/reports/{uploaded_dataset}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "quality_score" in data or "score" in data
    assert "rules" in data or "findings" in data or "results" in data


def test_get_report_without_auth(uploaded_dataset):
    """Test getting report without authentication."""
    resp = requests.get(f"{BASE_URL}/api/reports/{uploaded_dataset}")
    assert resp.status_code == 401


def test_get_report_nonexistent_dataset(auth_headers):
    """Test getting report for non-existent dataset."""
    resp = requests.get(f"{BASE_URL}/api/reports/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_get_quality_trends(auth_headers, uploaded_dataset, created_rule):
    """Test retrieving quality trends over time."""
    # Run multiple checks
    for _ in range(2):
        requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}", headers=auth_headers)
        time.sleep(1)

    # Get trends
    resp = requests.get(f"{BASE_URL}/api/reports/{uploaded_dataset}/trends", headers=auth_headers)
    assert resp.status_code in [200, 404]
    if resp.status_code == 200:
        data = resp.json()
        # Response can be list or paginated object with 'trends' key
        if isinstance(data, dict):
            assert "trends" in data or "results" in data
        else:
            assert isinstance(data, list)


def test_get_trends_with_date_filter(auth_headers, uploaded_dataset, created_rule):
    """Test getting trends with date range filter."""
    # Run check
    requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}", headers=auth_headers)

    # Get trends with date filter
    params = {"start_date": "2024-01-01", "end_date": "2025-12-31"}
    resp = requests.get(f"{BASE_URL}/api/reports/{uploaded_dataset}/trends", headers=auth_headers, params=params)
    assert resp.status_code == 200


def test_get_trends_with_pagination(auth_headers, uploaded_dataset, created_rule):
    """Test trends endpoint with pagination."""
    # Run check
    requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}", headers=auth_headers)

    params = {"limit": 5, "page": 1}
    resp = requests.get(f"{BASE_URL}/api/reports/{uploaded_dataset}/trends", headers=auth_headers, params=params)
    assert resp.status_code == 200


def test_get_dashboard_summary(auth_headers, uploaded_dataset, created_rule):
    """Test getting dashboard with aggregated scores."""
    # Run check
    requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}", headers=auth_headers)

    resp = requests.get(f"{BASE_URL}/api/reports/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_dashboard_without_auth():
    """Test accessing dashboard without authentication."""
    resp = requests.get(f"{BASE_URL}/api/reports/dashboard")
    assert resp.status_code == 401


def test_report_contains_rule_breakdown(auth_headers, uploaded_dataset, created_rule):
    """Test that report contains per-rule breakdown."""
    # Run check
    requests.post(f"{BASE_URL}/api/checks/run/{uploaded_dataset}", headers=auth_headers)

    # Get report
    resp = requests.get(f"{BASE_URL}/api/reports/{uploaded_dataset}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    # Check for rule-level details
    has_rule_info = "rules" in data or "findings" in data or "rule_results" in data or "results" in data
    assert has_rule_info
