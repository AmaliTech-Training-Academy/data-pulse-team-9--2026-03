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
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Rule"
    assert data["severity"] == "HIGH"
    # Ensure other fields remained unchanged
    assert data["rule_type"] == "NOT_NULL"


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
    assert resp.status_code == 204

    # Verify rule is soft-deleted (no longer in list)
    list_resp = auth_client.get("/api/rules/")
    assert list_resp.status_code == 200
    rule_ids = [r["id"] for r in list_resp.json()]
    assert rule_id not in rule_ids


@pytest.mark.django_db
def test_update_nonexistent_rule(auth_client):
    resp = auth_client.put(
        "/api/rules/99999",
        {"name": "Ghost"},
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_delete_nonexistent_rule(auth_client):
    resp = auth_client.delete("/api/rules/99999")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_unauthenticated_rules_rejected(client):
    resp = client.get("/api/rules/")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Validation / Error Handling Tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_invalid_rule_type(auth_client):
    """Test that creating a rule with an unknown rule_type is rejected with 400."""
    resp = auth_client.post(
        "/api/rules/",
        {
            "name": "Bad Check",
            "rule_type": "UNKNOWN_TYPE",
            "field_name": "age",
            "severity": "HIGH",
            "dataset_type": "csv",
            "parameters": "{}",
        },
        format="json",
    )
    # The view rejects InvalidRuleException (maps to 400 Bad Request)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_create_invalid_severity(auth_client):
    """Test that creating a rule with an unknown severity is rejected."""
    resp = auth_client.post(
        "/api/rules/",
        {
            "name": "Bad Check",
            "rule_type": "NOT_NULL",
            "field_name": "age",
            "severity": "CRITICAL",  # Not in High/Medium/Low
            "dataset_type": "csv",
            "parameters": "{}",
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_create_missing_required_fields(auth_client):
    """Test that missing required fields (name, field_name, rule_type) returns 400."""
    # Missing name
    resp1 = auth_client.post(
        "/api/rules/",
        {
            "rule_type": "NOT_NULL",
            "field_name": "age",
            "severity": "HIGH",
        },
        format="json",
    )
    assert resp1.status_code == 400

    # Missing field_name
    resp2 = auth_client.post(
        "/api/rules/",
        {
            "name": "Missing field",
            "rule_type": "NOT_NULL",
            "severity": "HIGH",
        },
        format="json",
    )
    assert resp2.status_code == 400


@pytest.mark.django_db
def test_create_invalid_json_parameters(auth_client):
    """Test that malformed JSON in the parameters string is caught by the serializer."""
    resp = auth_client.post(
        "/api/rules/",
        {
            "name": "Bad Params",
            "rule_type": "RANGE",
            "field_name": "age",
            "severity": "HIGH",
            "dataset_type": "csv",
            "parameters": "{min: 0, max: 100",  # Invalid JSON
        },
        format="json",
    )
    # The RuleCreateSerializer has custom validate_parameters logic for this
    assert resp.status_code == 400


@pytest.mark.django_db
def test_update_invalid_rule_type(auth_client):
    """Test that updating an existing rule to an invalid type is rejected."""
    # Create valid rule
    create_resp = auth_client.post(
        "/api/rules/",
        {
            "name": "Valid Rule",
            "rule_type": "NOT_NULL",
            "field_name": "name",
            "severity": "LOW",
            "dataset_type": "csv",
        },
        format="json",
    )
    rule_id = create_resp.json()["id"]

    # Update to invalid type
    resp = auth_client.put(
        f"/api/rules/{rule_id}",
        {"rule_type": "FAKE_TYPE"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_partial_update_rule(auth_client):
    """Test that updating just a single field (like name) leaves others intact."""
    create_resp = auth_client.post(
        "/api/rules/",
        {
            "name": "To Rename",
            "rule_type": "UNIQUE",
            "field_name": "email",
            "severity": "HIGH",
            "dataset_type": "csv",
        },
        format="json",
    )
    rule_id = create_resp.json()["id"]

    resp = auth_client.put(
        f"/api/rules/{rule_id}",
        {"name": "Renamed"},
        format="json",
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Renamed"
    assert data["rule_type"] == "UNIQUE"
    assert data["field_name"] == "email"


@pytest.mark.django_db
def test_unauthenticated_cud_rejected(client):
    """Test that unauthenticated clients cannot Create, Update, or Delete."""
    # Create
    resp1 = client.post("/api/rules/", {"name": "Anon"}, format="json")
    assert resp1.status_code == 401

    # Update
    resp2 = client.put("/api/rules/1", {"name": "Anon"}, format="json")
    assert resp2.status_code == 401

    # Delete
    resp3 = client.delete("/api/rules/1")
    assert resp3.status_code == 401
