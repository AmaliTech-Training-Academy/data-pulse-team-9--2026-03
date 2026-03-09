"""Rules API tests - STUB."""

import os
import requests
import pytest

BASE_URL = os.getenv("API_URL", "http://localhost:8000")


def test_create_rule():
    """Create a validation rule - STUB."""
    # TODO: Implement
    # POST /api/rules with valid rule data
    # Assert 201 and correct response fields
    pass


def test_list_rules():
    """List validation rules - STUB."""
    # TODO: Implement
    # GET /api/rules
    # Assert 200 and response is a list
    pass
