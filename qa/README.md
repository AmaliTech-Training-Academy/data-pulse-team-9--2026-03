# DataPulse QA Test Suite

## Setup

1. Install dependencies:
```bash
cd qa/api-tests
python -m pip install -r requirements.txt
```

2. Start backend:
```bash
docker-compose up -d --build
ping 127.0.0.1 -n 31 > nul
```

## Running Tests

**All tests:**
```bash
cd qa/api-tests
python -m pytest -v
```

**Integration tests only:**
```bash
python -m pytest test_integration.py -v
```

**Validation tests only:**
```bash
python -m pytest test_validation_rules.py -v
```

**Specific test:**
```bash
python -m pytest test_auth_api.py::test_login_valid_credentials -v
```

## HTML Report

After running tests, open: `qa/api-tests/report.html`

## Test Coverage

- **93 total tests**
- Authentication: 9 tests
- Datasets: 10 tests
- Rules: 13 tests
- Checks: 8 tests
- Reports: 9 tests
- Scheduling: 15 tests
- Metrics: 7 tests
- Upload: 3 tests
- Validation: 13 tests (all 5 rule types)
- Integration: 7 tests (end-to-end workflows)

## Endpoints Tested

- ✓ POST /api/auth/register
- ✓ POST /api/auth/login
- ✓ GET /api/auth/me
- ✓ POST /api/auth/token/refresh
- ✓ POST /api/datasets/upload
- ✓ GET /api/datasets
- ✓ GET /api/datasets/{id}
- ✓ POST /api/rules/
- ✓ GET /api/rules/
- ✓ PUT /api/rules/{id}
- ✓ DELETE /api/rules/{id}
- ✓ POST /api/checks/run/{id}
- ✓ GET /api/checks/results/{id}
- ✓ GET /api/reports/{id}
- ✓ GET /api/reports/{id}/trends
- ✓ GET /api/reports/dashboard
- ✓ POST /api/schedules/
- ✓ GET /api/schedules/
- ✓ GET /api/schedules/{id}/
- ✓ PATCH /api/schedules/{id}/pause/
- ✓ PATCH /api/schedules/{id}/resume/
- ✓ DELETE /api/schedules/{id}/
- ✓ POST /api/schedules/alerts/{dataset_id}/
- ✓ GET /metrics

## Validation Rules Tested

- ✓ NOT_NULL - Check for null/empty values
- ✓ DATA_TYPE - Validate data types (int, string, etc)
- ✓ RANGE - Check numeric ranges (min/max)
- ✓ UNIQUE - Ensure uniqueness
- ✓ REGEX - Pattern matching

**Troubleshooting:**
The environment has been configured to disable rate limiting in development mode. If you still see 429 errors, ensure that `REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]` is empty in `backend/datapulse/settings/dev.py`.

**Test Data:**
Location: `qa/test-data/`
- valid_test.csv - Clean CSV data
- valid_test.json - Clean JSON data
- invalid_test.csv - CSV with issues
- invalid_test.json - JSON with issues
- edge_cases.csv - Edge case scenarios
- edge_cases.json - Edge case scenarios

## Bug Reports

- Location: `qa/bug-reports/bugs.md`
- Template: `qa/bug-reports/bug_template.md`
