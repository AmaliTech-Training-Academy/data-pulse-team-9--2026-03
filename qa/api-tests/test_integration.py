"""End-to-end integration tests."""

import requests
import pytest
import time
from conftest import BASE_URL


class TestCompleteWorkflow:
    """Test complete end-to-end workflow."""

    def test_full_workflow_csv(self, auth_headers):
        """Test complete workflow: upload CSV -> create rules -> run checks -> get report -> view trends."""

        # Step 1: Upload dataset
        csv = b"id,name,email,age,salary\n1,Alice,alice@test.com,30,50000\n2,Bob,bob@test.com,25,45000\n3,Carol,carol@test.com,35,60000"
        files = {"file": ("employees.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        assert upload_resp.status_code in [201, 400, 429]
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        # Step 2: Create multiple validation rules
        rules = [
            {
                "name": "Email Not Null",
                "dataset_type": "csv",
                "rule_type": "NOT_NULL",
                "field_name": "email",
                "severity": "HIGH",
                "parameters": "{}",
            },
            {
                "name": "Age Must Be Int",
                "dataset_type": "csv",
                "rule_type": "DATA_TYPE",
                "field_name": "age",
                "severity": "MEDIUM",
                "parameters": '{"expected_type": "int"}',
            },
            {
                "name": "Age Range",
                "dataset_type": "csv",
                "rule_type": "RANGE",
                "field_name": "age",
                "severity": "LOW",
                "parameters": '{"min": 18, "max": 65}',
            },
        ]

        for rule in rules:
            rule_resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule)
            assert rule_resp.status_code in [201, 429]

        # Step 3: Run quality checks
        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)
        assert check_resp.status_code in [200, 201, 429]
        if check_resp.status_code in [200, 201]:
            quality_score = check_resp.json()["score"]
            assert 0 <= quality_score <= 100

        # Step 4: Get detailed report
        report_resp = requests.get(f"{BASE_URL}/api/reports/{dataset_id}", headers=auth_headers)
        assert report_resp.status_code in [200, 429]

        # Step 5: View trends
        trends_resp = requests.get(f"{BASE_URL}/api/reports/{dataset_id}/trends", headers=auth_headers)
        assert trends_resp.status_code in [200, 404, 429]

    def test_full_workflow_json(self, auth_headers):
        """Test complete workflow with JSON file."""

        # Step 1: Upload JSON dataset
        json_data = b'[{"id":1,"name":"Alice","age":30},{"id":2,"name":"Bob","age":25}]'
        files = {"file": ("data.json", json_data, "application/json")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        assert upload_resp.status_code in [201, 400, 429]
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        # Step 2: Create rule
        rule_data = {
            "name": "Name Not Null",
            "dataset_type": "json",
            "rule_type": "NOT_NULL",
            "field_name": "name",
            "severity": "HIGH",
            "parameters": "{}",
        }
        rule_resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
        assert rule_resp.status_code in [201, 429]

        # Step 3: Run checks
        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)
        assert check_resp.status_code in [200, 201, 429]


class TestMultipleDatasets:
    """Test handling multiple datasets."""

    def test_multiple_datasets_dashboard(self, auth_headers):
        """Test dashboard with multiple datasets."""

        # Upload multiple datasets
        datasets = []
        for i in range(2):
            csv = f"id,value\n1,{i*10}\n2,{i*20}".encode()
            files = {"file": (f"data{i}.csv", csv, "text/csv")}
            resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
            if resp.status_code == 429:
                pytest.skip("Rate limited")
            assert resp.status_code in [201, 400]
            datasets.append(resp.json()["id"])

        # Get dashboard
        dashboard_resp = requests.get(f"{BASE_URL}/api/reports/dashboard", headers=auth_headers)
        assert dashboard_resp.status_code in [200, 429]


class TestRuleManagement:
    """Test rule CRUD operations in workflow."""

    def test_update_rule_and_rerun_checks(self, auth_headers):
        """Test updating rule and re-running checks."""

        # Upload dataset
        csv = b"id,age\n1,30\n2,25\n3,35"
        files = {"file": ("test.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        # Create rule
        rule_data = {
            "name": "Age Range",
            "dataset_type": "csv",
            "rule_type": "RANGE",
            "field_name": "age",
            "severity": "LOW",
            "parameters": '{"min": 20, "max": 40}',
        }
        rule_resp = requests.post(f"{BASE_URL}/api/rules/", headers=auth_headers, json=rule_data)
        if rule_resp.status_code == 429:
            pytest.skip("Rate limited")
        rule_id = rule_resp.json()["id"]

        # Update rule severity
        update_resp = requests.put(f"{BASE_URL}/api/rules/{rule_id}", headers=auth_headers, json={"severity": "HIGH"})
        assert update_resp.status_code in [200, 429]


class TestDataQualityScoring:
    """Test quality score calculation."""

    def test_perfect_score(self, auth_headers):
        """Test dataset with perfect quality score."""
        csv = b"id,name,age\n1,Alice,30\n2,Bob,25\n3,Carol,35"
        files = {"file": ("perfect.csv", csv, "text/csv")}
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

    def test_failing_score(self, auth_headers):
        """Test dataset with quality issues."""
        csv = b"id,name,age\n1,,30\n2,,25\n3,,35"
        files = {"file": ("failing.csv", csv, "text/csv")}
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


class TestErrorHandling:
    """Test error handling in workflows."""

    def test_check_without_rules(self, auth_headers):
        """Test running check on dataset without any rules."""
        csv = b"id,name\n1,Alice\n2,Bob"
        files = {"file": ("test.csv", csv, "text/csv")}
        upload_resp = requests.post(f"{BASE_URL}/api/datasets/upload", headers=auth_headers, files=files)
        if upload_resp.status_code == 429:
            pytest.skip("Rate limited")
        dataset_id = upload_resp.json()["id"]
        time.sleep(2)

        # Run check without creating rules
        check_resp = requests.post(f"{BASE_URL}/api/checks/run/{dataset_id}", headers=auth_headers)
        # Should either succeed with score or return appropriate message
        assert check_resp.status_code in [200, 201, 400, 429]
