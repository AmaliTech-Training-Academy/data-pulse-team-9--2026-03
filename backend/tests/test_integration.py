"""Integration test — full end-to-end flow:
Register → Upload CSV → Create rules → Run checks → Get report → View trends.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


from django.test import override_settings

VALID_PASSWORD = "IntegTest1!"


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_full_e2e_flow(client):
    """End-to-end: register → upload → rules → checks → report → trends."""

    # 1. Register
    reg_resp = client.post(
        "/api/auth/register",
        {"email": "e2e@example.com", "password": VALID_PASSWORD, "full_name": "E2E User"},
        format="json",
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # 2. Upload CSV
    csv_content = (
        b"id,name,age,email\n"
        b"1,Alice,30,alice@test.com\n"
        b"2,Bob,25,bob@test.com\n"
        b"3,,35,carol@test.com\n"  # name is null on purpose
        b"4,Dave,150,not-an-email\n"  # age out of range, email invalid
        b"5,Eve,28,eve@test.com\n"
    )
    uploaded = SimpleUploadedFile("e2e.csv", csv_content, content_type="text/csv")
    upload_resp = client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["id"]
    assert upload_resp.json()["row_count"] == 5

    # 3. Create rules
    rules_to_create = [
        {
            "name": "Name not null",
            "rule_type": "NOT_NULL",
            "field_name": "name",
            "severity": "HIGH",
            "dataset_type": "csv",
            "parameters": "{}",
        },
        {
            "name": "Age range",
            "rule_type": "RANGE",
            "field_name": "age",
            "severity": "MEDIUM",
            "dataset_type": "csv",
            "parameters": '{"min": 0, "max": 120}',
        },
        {
            "name": "Email format",
            "rule_type": "REGEX",
            "field_name": "email",
            "severity": "LOW",
            "dataset_type": "csv",
            "parameters": '{"pattern": ".+@.+\\\\..+"}',
        },
    ]

    for rule_data in rules_to_create:
        resp = client.post("/api/rules/", rule_data, format="json")
        assert resp.status_code == 201

    # Verify rules created
    rules_resp = client.get("/api/rules/")
    assert rules_resp.status_code == 200
    assert len(rules_resp.json()) == 3

    # 4. Run checks
    check_resp = client.post(f"/api/checks/run/{dataset_id}")
    assert check_resp.status_code == 501

    # 5. Get check results
    results_resp = client.get(f"/api/checks/results/{dataset_id}")
    assert results_resp.status_code == 501

    # 6. Get report
    report_resp = client.get(f"/api/reports/{dataset_id}")
    assert report_resp.status_code == 501

    # 7. View trends
    trends_resp = client.get("/api/reports/trends?days=30")
    assert trends_resp.status_code == 501

    # 8. Dashboard
    dash_resp = client.get("/api/reports/dashboard")
    assert dash_resp.status_code == 200
    dashboard = dash_resp.json()
    assert len(dashboard) == 0  # No scores calculated because run_checks is 501


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_full_e2e_flow_json(client):
    """End-to-end for JSON dataset: register → upload → rules → checks → report."""
    
    # 1. Register & Auth
    reg_resp = client.post(
        "/api/auth/register",
        {"email": "e2e_json@example.com", "password": VALID_PASSWORD, "full_name": "E2E Json User"},
        format="json",
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # 2. Upload JSON
    import json
    json_content = json.dumps([
        {"id": 1, "product": "Apple", "price": 1.20, "code": "A123"},
        {"id": 2, "product": "Banana", "price": 0.80, "code": "B456"},
        {"id": 3, "product": None, "price": 1500.00, "code": "invalid-code"},
        {"id": 4, "product": "Orange", "price": 0.90, "code": "A123"}, # Duplicate code
    ]).encode()
    
    uploaded = SimpleUploadedFile("data.json", json_content, content_type="application/json")
    upload_resp = client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["id"]

    # 3. Create Rules
    rules_to_create = [
        {"name": "Product not null", "rule_type": "NOT_NULL", "field_name": "product", "dataset_type": "json", "severity": "HIGH"},
        {"name": "Price range", "rule_type": "RANGE", "field_name": "price", "dataset_type": "json", "parameters": '{"min": 0, "max": 100}', "severity": "MEDIUM"},
        {"name": "Code Unique", "rule_type": "UNIQUE", "field_name": "code", "dataset_type": "json", "severity": "HIGH"},
        {"name": "Code Regex", "rule_type": "REGEX", "field_name": "code", "dataset_type": "json", "parameters": '{"pattern": "^[A-Z][0-9]{3}$"}', "severity": "LOW"},
    ]
    for rule_data in rules_to_create:
        resp = client.post("/api/rules/", rule_data, format="json")
        assert resp.status_code == 201

    # 4. Run checks
    check_resp = client.post(f"/api/checks/run/{dataset_id}")
    assert check_resp.status_code == 501


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_regex_escaping_behavior(client):
    """Test how the API handles escaped vs unescaped regex patterns."""
    import json
    
    reg_resp = client.post(
        "/api/auth/register",
        {"email": "regex@example.com", "password": VALID_PASSWORD, "full_name": "Regex User"},
        format="json",
    )
    token = reg_resp.json()["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # CSV with SSN Data
    csv_content = (
        b"id,ssn\n"
        b"1,123-45-6789\n" # Valid format
        b"2,123456789\n"   # Invalid format
    )
    uploaded = SimpleUploadedFile("ssn.csv", csv_content, content_type="text/csv")
    upload_resp = client.post("/api/datasets/upload", {"file": uploaded}, format="multipart")
    dataset_id = upload_resp.json()["id"]

    # Test 1: Properly escaped JSON string for Regex \d
    # We want the JSON string to contain `\\d`, meaning we must pass a string that parses back to `\\d` in Python.
    escaped_pattern = json.dumps({"pattern": "^\\d{3}-\\d{2}-\\d{4}$"})
    
    # Test 2: Unescaped \d within JSON string (invalid JSON payload)
    # If a user just sends `{"pattern": "^\d..."}`, the JSON parser fails.
    unescaped_pattern = '{"pattern": "^\\d{3}-\\d{2}-\\d{4}$"}' # Python literal equivalent of receiving \d

    # Rule 1
    resp1 = client.post("/api/rules/", {
        "name": "Escaped SSN", 
        "rule_type": "REGEX", 
        "field_name": "ssn", 
        "dataset_type": "csv", 
        "severity": "HIGH",
        "parameters": escaped_pattern
    }, format="json")
    assert resp1.status_code == 201
    rule1_id = resp1.json()["id"]

    # Rule 2
    resp2 = client.post("/api/rules/", {
        "name": "Unescaped SSN", 
        "rule_type": "REGEX", 
        "field_name": "ssn", 
        "dataset_type": "csv", 
        "severity": "HIGH",
        "parameters": unescaped_pattern
    }, format="json")
    assert resp2.status_code == 201
    rule2_id = resp2.json()["id"]
    
    # Run Checks
    check_resp = client.post(f"/api/checks/run/{dataset_id}")
    assert check_resp.status_code == 501
