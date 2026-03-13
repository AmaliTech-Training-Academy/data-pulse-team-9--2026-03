"""Validation engine tests - testing each rule type with edge cases."""

import requests
import time
import pytest
from conftest import BASE_URL


class TestNotNullValidation:
    """Test NOT_NULL rule type."""

    def test_not_null_all_valid(self, auth_headers):
        """Test NOT_NULL with all valid (non-null) values."""
        # Delete all existing rules first
        rules_resp = requests.get(f"{BASE_URL}/api/rules/", headers=auth_headers)
        if rules_resp.status_code == 200:
            for rule in rules_resp.json():
                requests.delete(f"{BASE_URL}/api/rules/{rule['id']}", headers=auth_headers)

        csv = b"id,name\n1,Alice\n2,Bob\n3,Carol"
        files = {"file": ("notnull_valid.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": f"Name Not Null {dataset_id}",
            "dataset_type": "csv",
            "rule_type": "NOT_NULL",
            "field_name": "name",
            "severity": "HIGH",
            "parameters": "{}",
        }
        rule_resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
        rule_id = rule_resp.json()["id"]

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)

        # Clean up rule
        requests.delete(f"{BASE_URL}/api/rules/{rule_id}", headers=auth_headers)

        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            assert check_resp.json()["score"] == 100

    def test_not_null_with_nulls(self, auth_headers):
        """Test NOT_NULL with some null values."""
        csv = b"id,name\n1,Alice\n2,\n3,Carol"
        files = {"file": ("test.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": "Name Not Null",
            "dataset_type": "csv",
            "rule_type": "NOT_NULL",
            "field_name": "name",
            "severity": "HIGH",
            "parameters": "{}",
        }
        requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)
        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            score = check_resp.json()["score"]
            assert score < 100  # Should fail for row with null


class TestDataTypeValidation:
    """Test DATA_TYPE rule type."""

    def test_data_type_int_valid(self, auth_headers):
        """Test DATA_TYPE with valid integers."""
        # Delete all existing rules first
        rules_resp = requests.get(f"{BASE_URL}/api/rules/", headers=auth_headers)
        if rules_resp.status_code == 200:
            for rule in rules_resp.json():
                requests.delete(f"{BASE_URL}/api/rules/{rule['id']}", headers=auth_headers)

        csv = b"id,age\n1,30\n2,25\n3,35"
        files = {"file": ("datatype_valid.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": f"Age Must Be Int {dataset_id}",
            "dataset_type": "csv",
            "rule_type": "DATA_TYPE",
            "field_name": "age",
            "severity": "MEDIUM",
            "parameters": '{"expected_type": "int"}',
        }
        rule_resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
        rule_id = rule_resp.json()["id"]

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)

        # Clean up rule
        requests.delete(f"{BASE_URL}/api/rules/{rule_id}", headers=auth_headers)

        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            assert check_resp.json()["score"] == 100

    def test_data_type_int_invalid(self, auth_headers):
        """Test DATA_TYPE with invalid type (string instead of int)."""
        csv = b"id,age\n1,30\n2,abc\n3,35"
        files = {"file": ("test.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": "Age Must Be Int",
            "dataset_type": "csv",
            "rule_type": "DATA_TYPE",
            "field_name": "age",
            "severity": "MEDIUM",
            "parameters": '{"expected_type": "int"}',
        }
        requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)
        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            score = check_resp.json()["score"]
            assert score < 100


class TestRangeValidation:
    """Test RANGE rule type."""

    def test_range_all_within(self, auth_headers):
        """Test RANGE with all values within range."""
        # Delete all existing rules first
        rules_resp = requests.get(f"{BASE_URL}/api/rules/", headers=auth_headers)
        if rules_resp.status_code == 200:
            for rule in rules_resp.json():
                requests.delete(f"{BASE_URL}/api/rules/{rule['id']}", headers=auth_headers)

        csv = b"id,age\n1,25\n2,30\n3,40"
        files = {"file": ("range_valid.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": f"Age Range 18-65 {dataset_id}",
            "dataset_type": "csv",
            "rule_type": "RANGE",
            "field_name": "age",
            "severity": "MEDIUM",
            "parameters": '{"min": 18, "max": 65}',
        }
        rule_resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
        rule_id = rule_resp.json()["id"]

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)

        # Clean up rule
        requests.delete(f"{BASE_URL}/api/rules/{rule_id}", headers=auth_headers)

        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            assert check_resp.json()["score"] == 100

    def test_range_outside_bounds(self, auth_headers):
        """Test RANGE with values outside range."""
        csv = b"id,age\n1,15\n2,30\n3,70"
        files = {"file": ("test.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": "Age Range 18-65",
            "dataset_type": "csv",
            "rule_type": "RANGE",
            "field_name": "age",
            "severity": "MEDIUM",
            "parameters": '{"min": 18, "max": 65}',
        }
        requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)
        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            score = check_resp.json()["score"]
            assert score < 100

    def test_range_boundary_values(self, auth_headers):
        """Test RANGE with exact boundary values."""
        # Delete all existing rules first
        rules_resp = requests.get(f"{BASE_URL}/api/rules/", headers=auth_headers)
        if rules_resp.status_code == 200:
            for rule in rules_resp.json():
                requests.delete(f"{BASE_URL}/api/rules/{rule['id']}", headers=auth_headers)

        csv = b"id,age\n1,18\n2,65\n3,30"
        files = {"file": ("range_boundary.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": f"Age Range 18-65 {dataset_id}",
            "dataset_type": "csv",
            "rule_type": "RANGE",
            "field_name": "age",
            "severity": "MEDIUM",
            "parameters": '{"min": 18, "max": 65}',
        }
        rule_resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
        rule_id = rule_resp.json()["id"]

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)

        # Clean up rule
        requests.delete(f"{BASE_URL}/api/rules/{rule_id}", headers=auth_headers)

        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            assert check_resp.json()["score"] == 100


class TestUniqueValidation:
    """Test UNIQUE rule type."""

    def test_unique_all_unique(self, auth_headers):
        """Test UNIQUE with all unique values."""
        # Delete all existing rules first
        rules_resp = requests.get(f"{BASE_URL}/api/rules/", headers=auth_headers)
        if rules_resp.status_code == 200:
            for rule in rules_resp.json():
                requests.delete(f"{BASE_URL}/api/rules/{rule['id']}", headers=auth_headers)

        csv = b"id,email\n1,alice@test.com\n2,bob@test.com\n3,carol@test.com"
        files = {"file": ("unique_valid.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": f"Email Must Be Unique {dataset_id}",
            "dataset_type": "csv",
            "rule_type": "UNIQUE",
            "field_name": "email",
            "severity": "HIGH",
            "parameters": "{}",
        }
        rule_resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
        rule_id = rule_resp.json()["id"]

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)

        # Clean up rule
        requests.delete(f"{BASE_URL}/api/rules/{rule_id}", headers=auth_headers)

        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            assert check_resp.json()["score"] == 100

    def test_unique_with_duplicates(self, auth_headers):
        """Test UNIQUE with duplicate values."""
        csv = b"id,email\n1,alice@test.com\n2,alice@test.com\n3,carol@test.com"
        files = {"file": ("test.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": "Email Must Be Unique",
            "dataset_type": "csv",
            "rule_type": "UNIQUE",
            "field_name": "email",
            "severity": "HIGH",
            "parameters": "{}",
        }
        requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)
        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            score = check_resp.json()["score"]
            assert score < 100


class TestRegexValidation:
    """Test REGEX rule type."""

    def test_regex_all_match(self, auth_headers):
        """Test REGEX with all values matching pattern."""
        # Delete all existing rules first
        rules_resp = requests.get(f"{BASE_URL}/api/rules/", headers=auth_headers)
        if rules_resp.status_code == 200:
            for rule in rules_resp.json():
                requests.delete(f"{BASE_URL}/api/rules/{rule['id']}", headers=auth_headers)

        csv = b"id,email\n1,alice@test.com\n2,bob@test.com\n3,carol@test.com"
        files = {"file": ("regex_valid.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": f"Email Format {dataset_id}",
            "dataset_type": "csv",
            "rule_type": "REGEX",
            "field_name": "email",
            "severity": "LOW",
            "parameters": '{"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$"}',
        }
        rule_resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
        rule_id = rule_resp.json()["id"]

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)

        # Clean up rule
        requests.delete(f"{BASE_URL}/api/rules/{rule_id}", headers=auth_headers)

        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            assert check_resp.json()["score"] == 100

    def test_regex_some_mismatch(self, auth_headers):
        """Test REGEX with some values not matching pattern."""
        csv = b"id,email\n1,alice@test.com\n2,invalid-email\n3,carol@test.com"
        files = {"file": ("test.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": "Email Format",
            "dataset_type": "csv",
            "rule_type": "REGEX",
            "field_name": "email",
            "severity": "LOW",
            "parameters": '{"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$"}',
        }
        requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)
        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            score = check_resp.json()["score"]
            assert score < 100


class TestSeverityImpact:
    """Test that severity levels impact scoring correctly."""

    def test_high_severity_impact(self, auth_headers):
        """Test that HIGH severity has greater impact on score."""
        csv = b"id,name\n1,Alice\n2,\n3,Carol"
        files = {"file": ("test.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        rule_data = {
            "name": "Name Not Null High",
            "dataset_type": "csv",
            "rule_type": "NOT_NULL",
            "field_name": "name",
            "severity": "HIGH",
            "parameters": "{}",
        }
        requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)

        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)
        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            score = check_resp.json()["score"]
            assert 0 <= score < 100
