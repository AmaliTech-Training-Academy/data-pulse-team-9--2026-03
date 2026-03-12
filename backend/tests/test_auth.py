"""Authentication tests - IMPLEMENTED."""

import pytest


@pytest.mark.django_db
def test_register_success(client):
    resp = client.post(
        "/api/auth/register",
        {"email": "new@example.com", "password": "TestPass1!", "full_name": "New User"},
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.django_db
def test_login_success(client):
    # Register first
    client.post(
        "/api/auth/register",
        {"email": "login@example.com", "password": "TestPass1!", "full_name": "Login User"},
        format="json",
    )
    # Then login
    resp = client.post(
        "/api/auth/login",
        {"email": "login@example.com", "password": "TestPass1!"},
        format="json",
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.django_db
def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        {"email": "wrong@example.com", "password": "TestPass1!", "full_name": "Wrong User"},
        format="json",
    )
    resp = client.post(
        "/api/auth/login",
        {"email": "wrong@example.com", "password": "badpass"},
        format="json",
    )
    assert resp.status_code == 401
