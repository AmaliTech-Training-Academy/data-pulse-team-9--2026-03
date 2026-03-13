"""Validation rules API tests."""

import requests
import pytest
from conftest import BASE_URL


def test_create_not_null_rule(auth_headers):
    """Test creating a NOT_NULL validation rule."""
    rule_data = {
        "name": "Email Not Null",
        "dataset_type": "csv",
        "rule_type": "NOT_NULL",
        "field_name": "email",
        "severity": "HIGH",
        "parameters": "{}",
    }
    resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == rule_data["name"]
    assert data["rule_type"] == "NOT_NULL"


def test_create_data_type_rule(auth_headers):
    """Test creating a DATA_TYPE validation rule."""
    rule_data = {
        "name": "Age Must Be Integer",
        "dataset_type": "csv",
        "rule_type": "DATA_TYPE",
        "field_name": "age",
        "severity": "MEDIUM",
        "parameters": '{"expected_type": "int"}',
    }
    resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rule_type"] == "DATA_TYPE"


def test_create_range_rule(auth_headers):
    """Test creating a RANGE validation rule."""
    rule_data = {
        "name": "Age Range 18-65",
        "dataset_type": "csv",
        "rule_type": "RANGE",
        "field_name": "age",
        "severity": "MEDIUM",
        "parameters": '{"min": 18, "max": 65}',
    }
    resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rule_type"] == "RANGE"


def test_create_unique_rule(auth_headers):
    """Test creating a UNIQUE validation rule."""
    rule_data = {
        "name": "ID Must Be Unique",
        "dataset_type": "csv",
        "rule_type": "UNIQUE",
        "field_name": "id",
        "severity": "HIGH",
        "parameters": "{}",
    }
    resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rule_type"] == "UNIQUE"


def test_create_regex_rule(auth_headers):
    """Test creating a REGEX validation rule."""
    rule_data = {
        "name": "Email Format Check",
        "dataset_type": "csv",
        "rule_type": "REGEX",
        "field_name": "email",
        "severity": "LOW",
        "parameters": '{"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$"}',
    }
    resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rule_type"] == "REGEX"


def test_create_rule_without_auth():
    """Test creating rule without authentication."""
    rule_data = {
        "name": "Test Rule",
        "rule_type": "NOT_NULL",
        "field_name": "test",
        "severity": "LOW",
        "parameters": "{}",
    }
    resp = requests.post(f"{BASE_URL}/api/rules/", json=rule_data)
    assert resp.status_code == 401


def test_create_rule_invalid_type(auth_headers):
    """Test creating rule with invalid rule_type."""
    rule_data = {
        "name": "Invalid Rule",
        "rule_type": "INVALID_TYPE",
        "field_name": "test",
        "severity": "LOW",
        "parameters": "{}",
    }
    resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
    # Backend returns 400 for validation errors instead of 422
    assert resp.status_code == 400


def test_create_rule_invalid_severity(auth_headers):
    """Test creating rule with invalid severity."""
    rule_data = {
        "name": "Invalid Severity",
        "rule_type": "NOT_NULL",
        "field_name": "test",
        "severity": "CRITICAL",
        "parameters": "{}",
    }
    resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
    # Backend returns 400 for validation errors instead of 422
    assert resp.status_code == 400


def test_list_rules(auth_headers, created_rule):
    """Test listing validation rules."""
    resp = requests.get(f"{BASE_URL}/api/rules/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(r["id"] == created_rule for r in data)


def test_update_rule(auth_headers, created_rule):
    """Test updating an existing rule."""
    update_data = {"name": "Updated Rule Name", "severity": "LOW"}
    resp = requests.put(f"{BASE_URL}/api/rules/{created_rule}", headers=auth_headers, json=update_data)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Rule Name"


def test_update_nonexistent_rule(auth_headers):
    """Test updating non-existent rule."""
    resp = requests.put(f"{BASE_URL}/api/rules/99999", headers=auth_headers, json={"name": "Updated"})
    assert resp.status_code == 404


def test_delete_rule(auth_headers):
    """Test deleting a rule."""
    # Create a rule to delete
    rule_data = {
        "name": "Rule To Delete",
        "dataset_type": "csv",
        "rule_type": "NOT_NULL",
        "field_name": "test",
        "severity": "LOW",
        "parameters": "{}",
    }
    create_resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
    assert create_resp.status_code == 201
    rule_id = create_resp.json()["id"]

    # Delete it
    resp = requests.delete(f"{BASE_URL}/api/rules/{rule_id}", headers=auth_headers)
    assert resp.status_code == 204


def test_delete_nonexistent_rule(auth_headers):
    """Test deleting non-existent rule."""
    resp = requests.delete(f"{BASE_URL}/api/rules/99999", headers=auth_headers)
    assert resp.status_code == 404
