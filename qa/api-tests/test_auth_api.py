"""Authentication API tests."""

import requests
import pytest
from conftest import BASE_URL


def test_register_new_user():
    """Test user registration with valid data."""
    user_data = {
        "email": f"testuser_{pytest.timestamp}@test.com",
        "password": "TestPass123!",  # pragma: allowlist secret
        "full_name": "Test User",
    }
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    assert resp.status_code == 201
    data = resp.json()
    # API returns tokens on registration, not user data
    assert "access_token" in data
    assert "refresh_token" in data


def test_register_duplicate_email():
    """Test registration with existing email fails."""
    user_data = {
        "email": "admin@amalitech.com",
        "password": "testpass123",  # pragma: allowlist secret
        "full_name": "Duplicate User",
    }  # pragma: allowlist secret
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    assert resp.status_code == 400


def test_register_invalid_email():
    """Test registration with invalid email format."""
    user_data = {
        "email": "not-an-email",
        "password": "TestPass123",  # pragma: allowlist secret
        "full_name": "Invalid Email",
    }  # pragma: allowlist secret
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    assert resp.status_code == 400  # Backend returns 400 for validation errors


def test_login_valid_credentials():
    """Test login with valid credentials."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "user@amalitech.com", "password": "password123"},  # pragma: allowlist secret
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_password():
    """Test login with wrong password."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "user@amalitech.com", "password": "wrongpassword"},  # pragma: allowlist secret
    )
    assert resp.status_code == 401


def test_login_nonexistent_user():
    """Test login with non-existent email."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "nonexistent@test.com", "password": "password123"},  # pragma: allowlist secret
    )
    assert resp.status_code == 401


def test_get_current_user(auth_headers):
    """Test retrieving current user profile."""
    resp = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "email" in data
    assert data["email"] == "user@amalitech.com"


def test_get_current_user_no_token():
    """Test accessing profile without token fails."""
    resp = requests.get(f"{BASE_URL}/api/auth/me")
    assert resp.status_code == 401


def test_refresh_token(user_token):
    """Test refreshing access token."""
    login_resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "user@amalitech.com", "password": "password123"},  # pragma: allowlist secret
    )
    refresh_token = login_resp.json()["refresh_token"]

    resp = requests.post(f"{BASE_URL}/api/auth/token/refresh", json={"refresh": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access" in data


# Add timestamp for unique test users
pytest.timestamp = __import__("time").time()
