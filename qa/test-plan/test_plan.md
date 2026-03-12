# Test Plan: DataPulse

## 1. INTRODUCTION

### 1.1 INTRODUCTION AND PURPOSE
A Test Plan is a formal document that outlines the objectives, scope, approach, resources, and schedule of intended testing activities for a software project. It serves as a roadmap for the QA team and stakeholders, ensuring that the system is thoroughly validated and that all functional and non-functional requirements are met.

The DataPulse project is a data quality monitoring tool designed to help organizations maintain high-quality datasets by allowing users to upload CSV and JSON files, define validation rules including null checks, data type checks, range checks, and uniqueness checks, run quality checks that produce a quality score from 0 to 100, generate detailed per-rule quality reports, and track quality trends over time via a dashboard.

The system exposes all operations through a REST API and is built using **Python 3.11+, Django, Django Rest Framework (DRF), and PostgreSQL**, with data processing handled by **Pandas**, testing implemented via **pytest**, and deployment managed using **Docker, Docker Compose, and GitHub Actions for CI/CD**.

The purpose of this test plan is to define the objectives, scope, and approach for QA activities, ensuring that all MVP features are tested and validated, including file uploads, validation rules, quality score computation, report generation, dashboard trends, and API endpoints. Testing will focus on verifying functionality, data integrity, reliability, and accuracy, while logging and tracking defects to prepare the system for deployment. The QA approach includes a combination of manual exploratory testing via Postman and Swagger (drf-spectacular), automated testing using pytest with coverage reporting, and regression testing after fixes or new features.

### 1.2 OBJECTIVES OF TESTING
The objectives of this test plan define what the testing activities aim to achieve during the development of the DataPulse system. They guide the QA process by ensuring that all critical features of the application are validated, potential defects are identified early, and the system meets the required functional and reliability standards before deployment.

The main objectives of testing are:
*   **Validate core functionality**: Ensure that all main features of DataPulse work as expected, including uploading CSV and JSON files, defining validation rules, running quality checks, and generating reports.
*   **Verify data validation rules**: Confirm that validation rules such as null checks, data type checks, range checks, and uniqueness checks are applied correctly and detect invalid data accurately.
*   **Ensure accuracy of quality score calculation**: Verify that the system correctly computes the quality score (0–100) based on the percentage of rows that pass all defined validation rules.
*   **Test REST API functionality**: Ensure that all API endpoints operate correctly, return appropriate responses, handle errors properly, and enforce authentication and authorization where required using JWT.
*   **Validate report generation and dashboard data**: Confirm that detailed quality reports and trend data are generated correctly and reflect the actual validation results for each dataset.
*   **Identify and document defects**: Detect bugs during testing and document them with clear steps, severity levels, and expected versus actual results to support efficient resolution.
*   **Verify end-to-end workflow**: Ensure that the complete process—from uploading datasets to applying validation rules, generating reports, and viewing trends—works seamlessly without failures.
*   **Support system reliability and deployment readiness**: Ensure the system is stable, well-tested, and ready for integration into the CI/CD pipeline and eventual deployment.

## 2. SCOPE OF TESTING
The scope of testing defines the components, features, and quality attributes of the system that will be validated during testing. Testing will focus on ensuring that the system correctly processes uploaded datasets, applies validation rules accurately, generates reliable quality reports, and provides secure and responsive APIs.

### 2.1 In Scope:
*   **API Endpoint Testing**: Testing all available API endpoints to ensure they respond correctly to different types of requests (GET, POST, PUT, PATCH, DELETE).
*   **Data Validation Accuracy**: Verifying that the system correctly validates incoming data against required fields, data types, and acceptable ranges.
*   **File Upload Handling**: Testing the system’s ability to accept, validate, and process uploaded files (CSV/JSON) and handle size limits or corrupted files.
*   **Security Testing**: Verifying authentication enforcement (JWT), secure handling of uploaded files, and protection against common API security issues.
*   **Frontend Functional Testing**: Testing the user interface to ensure that features such as dataset upload, rule configuration, and dashboards function correctly.
*   **Accessibility Testing**: Ensuring the frontend interface is usable by people with disabilities (keyboard navigation, color contrast, etc.).
*   **Performance and Response Testing**: Evaluating the responsiveness of APIs for file uploads and validation checks.
*   **Quality Score and Reporting Validation**: Testing the correctness of the quality score calculation and generated reports.

### 2.2 Out of Scope:
*   **Third-Party Service Reliability**: Failures or downtime caused by external third-party services integrated with the system.

## 3. TEST CATEGORIES

### 3.1 AUTHENTICATION TESTS
*   **Register with valid data**: Verify new user registration with unique email and valid password.
*   **Register duplicate email**: Verify system prevents registration with an existing email.
*   **Login with valid credentials**: Ensure users can log in and receive a valid JWT.
*   **Login with invalid credentials**: Verify system denies access with incorrect credentials.

### 3.2 UPLOAD TESTS
*   **Upload valid CSV**: Verify successful processing of formatted CSV files.
*   **Upload valid JSON**: Confirm successful processing of structured JSON files.
*   **Upload unsupported file type**: Verify rejection of non-CSV/JSON files.
*   **Upload empty file**: Ensure system rejects files with no data.
*   **Upload large file**: Verify handling of datasets within acceptable limits.

### 3.3 RULES TESTS
*   **Create rule**: Verify successful rule creation with valid parameters.
*   **List rules**: Ensure system returns all existing rules with full details.
*   **Filter by dataset_type**: Confirm rules can be filtered by type (CSV/JSON).
*   **Update rule**: Verify existing rules can be modified successfully.
*   **Delete rule**: Ensure rules can be removed effectively.

### 3.4 REPORTS TESTS
*   **Get dataset report**: Verify generation of detailed quality reports (passed/failed counts, score).
*   **Get quality trends**: Ensure retrieval of historical quality scores over time.

## 4. TEST DATA
*   **valid_test.csv – Clean data**: Used to verify successful processing of clean data and perfect scores.
*   **invalid_test.csv – Data with issues**: Used to confirm detection of quality issues and lower scores.

## 5. TEST ENVIRONMENT
*   **Base URL**: `http://localhost:8000`
*   **Stack**: Django / DRF / PostgreSQL / Docker.

## 6. TEST RESOURCES
*   **Testing Tools**: pytest, Postman, Swagger (drf-spectacular), Docker.

## 7. TEST ENTRY AND EXIT CRITERIA
*   **Entry**: Application deployed, APIs implemented, DB running, Test data available.
*   **Exit**: All test cases executed, major bugs fixed, end-to-end workflow successful, scoring accurate.

## 8. TEST DESIGN TECHNIQUES
*   Equivalence partitioning, Boundary Value Analysis, and End-to-End Workflow Testing.

## 9. RISK AND MITIGATION
*   Incomplete API implementation -> Regular developer coordination.
*   Performance bottlenecks -> Performance testing with large datasets.
*   Integration issues -> End-to-end integration testing.

## 10. TEST SCHEDULE
*   Testing is conducted within 1-week sprints using an Agile methodology.

## 11. DEFECT MANAGEMENT
*   Defects are logged with steps to reproduce, expected vs. actual results, and severity levels (Critical, High, Medium, Low).
