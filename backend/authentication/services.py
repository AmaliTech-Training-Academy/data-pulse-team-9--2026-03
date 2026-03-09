"""Authentication service - IMPLEMENTED."""

from django.contrib.auth.hashers import make_password, check_password
from authentication.models import User


def create_user(email, password, full_name):
    """Create a new user. Returns None if email exists."""
    if User.objects.filter(email=email).exists():
        return None
    user = User.objects.create(
        email=email,
        password=make_password(password),
        full_name=full_name,
    )
    return user


def authenticate_user(email, password):
    """Authenticate user by email and password."""
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None
    if not check_password(password, user.password):
        return None
    return user
