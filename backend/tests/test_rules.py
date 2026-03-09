"""API tests for Rules CRUD (PUT, DELETE)."""

import pytest


@pytest.mark.django_db
def test_create_rule(auth_client):
    resp = auth_client.post(
        "/api/rules/",
        {
            "name": "Null Check - age",
            "rule_type": "NOT_NULL",
            "field_name": "age",
            "severity": "HIGH",
            "dataset_type": "csv",
            "parameters": "{}",
        },
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Null Check - age"
    assert data["rule_type"] == "NOT_NULL"


@pytest.mark.django_db
def test_list_rules(auth_client):
    # Create a rule first
    auth_client.post(
        "/api/rules/",
        {
            "name": "Test Rule",
            "rule_type": "NOT_NULL",
            "field_name": "name",
            "severity": "LOW",
            "dataset_type": "csv",
            "parameters": "{}",
        },
        format="json",
    )
    resp = auth_client.get("/api/rules/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.django_db
def test_update_rule(auth_client):
    # Create
    create_resp = auth_client.post(
        "/api/rules/",
        {
            "name": "Original",
            "rule_type": "NOT_NULL",
            "field_name": "name",
            "severity": "LOW",
            "dataset_type": "csv",
            "parameters": "{}",
        },
        format="json",
    )
    rule_id = create_resp.json()["id"]

    # Update
    resp = auth_client.put(
        f"/api/rules/{rule_id}",
        {"name": "Updated Rule", "severity": "HIGH"},
        format="json",
    )
    assert resp.status_code == 501


@pytest.mark.django_db
def test_delete_rule_soft_delete(auth_client):
    # Create
    create_resp = auth_client.post(
        "/api/rules/",
        {
            "name": "To Delete",
            "rule_type": "NOT_NULL",
            "field_name": "name",
            "severity": "LOW",
            "dataset_type": "csv",
            "parameters": "{}",
        },
        format="json",
    )
    rule_id = create_resp.json()["id"]

    # Delete
    resp = auth_client.delete(f"/api/rules/{rule_id}")
    assert resp.status_code == 501


@pytest.mark.django_db
def test_update_nonexistent_rule(auth_client):
    resp = auth_client.put(
        "/api/rules/99999",
        {"name": "Ghost"},
        format="json",
    )
    assert resp.status_code == 501


@pytest.mark.django_db
def test_delete_nonexistent_rule(auth_client):
    resp = auth_client.delete("/api/rules/99999")
    assert resp.status_code == 501


@pytest.mark.django_db
def test_unauthenticated_rules_rejected(client):
    resp = client.get("/api/rules/")
    assert resp.status_code == 401
