"""Pytest configuration and shared fixtures for API tests."""

import os
import pytest
import requests
import time
import random

BASE_URL = os.getenv("API_URL", "http://localhost:8000")

# Test credentials as defined in backend/authentication/management/commands/seed_users.py
TEST_USERS = [
    ("admin@amalitech.com", "password123"),  # pragma: allowlist secret
    ("user@amalitech.com", "password123"),  # pragma: allowlist secret
]


def login_with_retry(email, password, max_retries=3):
    """Login with retry mechanism."""
    for attempt in range(max_retries):
        try:
            resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})

            if resp.status_code == 200:
                data = resp.json()
                # SimpleJWT returns 'access' and 'refresh'
                return data.get("access_token") or data.get("access")
            elif resp.status_code == 429:
                wait_time = (2**attempt) + random.uniform(0, 1)
                print(f"Rate limited, waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}")
                time.sleep(wait_time)
                continue
            else:
                raise AssertionError(f"Login failed for {email} with status {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise AssertionError(f"Login request failed for {email}: {e}")
            time.sleep(1)

    raise pytest.skip(f"Login failed for {email} after all retries")


@pytest.fixture(scope="session")
def admin_token():
    """Get admin JWT token for tests."""
    return login_with_retry(TEST_USERS[0][0], TEST_USERS[0][1])


@pytest.fixture(scope="session")
def user_token():
    """Get regular user JWT token for tests."""
    return login_with_retry(TEST_USERS[1][0], TEST_USERS[1][1])


@pytest.fixture
def auth_headers(user_token):
    """Return authorization headers with user token."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Return authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_csv_file():
    """Return a valid CSV file for testing."""
    csv_content = """id,name,email,age,salary
1,Alice,alice@test.com,30,50000
2,Bob,bob@test.com,25,45000
3,Carol,carol@test.com,35,60000
4,David,david@test.com,28,48000
5,Eve,eve@test.com,32,55000"""
    return ("test.csv", csv_content.encode(), "text/csv")


@pytest.fixture
def sample_json_file():
    """Return a valid JSON file for testing."""
    json_content = """[
    {"id": 1, "name": "Alice", "email": "alice@test.com", "age": 30, "salary": 50000},
    {"id": 2, "name": "Bob", "email": "bob@test.com", "age": 25, "salary": 45000},
    {"id": 3, "name": "Carol", "email": "carol@test.com", "age": 35, "salary": 60000}
]"""
    return ("test.json", json_content.encode(), "application/json")


@pytest.fixture
def uploaded_dataset(auth_headers, sample_csv_file):
    """Upload a dataset and return its ID."""
    resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files={"file": sample_csv_file})
    assert resp.status_code == 201, f"Dataset upload failed: {resp.text}"
    return resp.json()["id"]


@pytest.fixture
def created_rule(auth_headers, uploaded_dataset):
    """Create a validation rule and return its ID."""
    rule_data = {
        "name": "Test Age Not Null",
        "dataset_type": "csv",
        "rule_type": "NOT_NULL",
        "field_name": "age",
        "severity": "HIGH",
        "parameters": "{}",
    }
    resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
    assert resp.status_code == 201, f"Rule creation failed: {resp.text}"
    return resp.json()["id"]
