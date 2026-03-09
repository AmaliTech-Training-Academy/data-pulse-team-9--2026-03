"""Test fixtures for pytest-django."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    """Return a DRF APIClient for making test requests."""
    return APIClient()


@pytest.fixture
def sample_user(client):
    """Register a test user and return the response data."""
    resp = client.post(
        "/api/auth/register",
        {"email": "test@example.com", "password": "TestPass1!", "full_name": "Test User"},
        format="json",
    )
    if resp.status_code != 201:
        print(f"REGISTRATION FAILED: {resp.status_code} {resp.content}")
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def auth_token(sample_user):
    """Return the access token from sample_user registration."""
    return sample_user["access_token"]


@pytest.fixture
def auth_client(client, auth_token):
    """Return an APIClient with authorization headers."""
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_token}")
    return client


@pytest.fixture
def sample_csv_content():
    """Return a sample CSV byte string."""
    return (
        b"id,name,age,email\n"
        b"1,Alice,30,alice@test.com\n"
        b"2,Bob,25,bob@test.com\n"
        b"3,Charlie,35,charlie@test.com\n"
    )


@pytest.fixture
def sample_json_content():
    """Return a sample JSON byte string."""
    import json

    data = [
        {"id": 1, "name": "Apple", "price": 1.2},
        {"id": 2, "name": "Banana", "price": 0.8},
    ]
    return json.dumps(data).encode()
