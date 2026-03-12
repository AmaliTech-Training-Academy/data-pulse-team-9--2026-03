# DataPulse Backend

The **DataPulse** backend is a robust RESTful API built with **Django**, **Django REST Framework (DRF)**, **PostgreSQL**, **Pandas**, and **Celery**. It handles file uploads, complex rule-based dataset validation, comprehensive scoring, background task scheduling, and quality trend reporting.

---

## 1. Backend API Server

### How to start the server locally?

The easiest and recommended way to run the entire backend stack (API, PostgreSQL Database, Redis, Celery Worker, Celery Beat) is via Docker.

1. **Install Docker Desktop**: If you don't have it installed already, download and install it from [docker.com](https://www.docker.com/products/docker-desktop/).
2. Navigate to the root repository folder (where `docker-compose.yml` is located) and run:

```bash
docker-compose up --build
```

### What port does it run on?

- The backend API runs and binds to port **8000**.
- **Important**: We highly recommend using the interactive Swagger UI to explore and test the endpoints directly from your browser!
- **Swagger Documentation URL**: `http://localhost:8000/docs/`
- Base API URL: `http://localhost:8000`

### Any environment setup needed?

- If using Docker, **no env setup is required**. `docker-compose.yml` automatically passes all necessary environment variables (including database connection strings and Redis URLs) into the containers.
- If you wish to run the project natively (without Docker), you should:
  1. Copy `backend/.env.example` to `backend/.env`
  2. Start a local PostgreSQL and Redis server
  3. Update `DATABASE_URL`, `CELERY_BROKER_URL`, etc. inside the `.env` file
  4. Run `python manage.py migrate` and `python manage.py runserver`

---

## 2. API Documentation

Authentication is required for all endpoints except `register` and `login`.

- **Authentication Mechanism**: JWT (JSON Web Token) with Access & Refresh tokens
- **Token Type**: Bearer
- **Header Format**: `Authorization: Bearer <your_access_token>`
- **Role-Based Access Control (RBAC)**: Certain endpoints require specific roles (e.g., Admin vs User). Roles determine viewing/editing permissions for datasets and users.

### List of Endpoints

| Method | Endpoint | Description & Request Format | Status |
|--------|----------|------------------------------|--------|
| **POST** | `/api/auth/register` | Register user. Body: `{"email": "...", "password": "...", "full_name": "..."}` | ✅ Done |
| **POST** | `/api/auth/login` | Authenticate user. Body: `{"email": "...", "password": "..."}`. Returns JWT access and refresh token. | ✅ Done |
| **GET**  | `/api/auth/me` | Retrieve current authenticated user profile and roles. Requires Bearer Token. | ✅ Done |
| **POST** | `/api/auth/token/refresh` | Refresh the JWT access token using the refresh token. | ✅ Done |
| **POST** | `/api/datasets/upload` | Upload CSV/JSON file. | ✅ Done |
| **GET**  | `/api/datasets/` | List datasets uploaded by the user. | ✅ Done |
| **POST** | `/api/rules/` | Create a rule. | ✅ Done |
| **GET**  | `/api/rules/` | List active validation rules. | ✅ Done |
| **PUT**  | `/api/rules/{id}` | Update an existing rule. | ✅ Done |
| **DELETE** | `/api/rules/{id}` | Soft-delete a rule. | ✅ Done |
| **POST** | `/api/checks/run/{id}` | Run validation checks on a dataset. | ✅ Done |
| **GET**  | `/api/checks/results/{id}` | Get row-level check results. | ✅ Done |
| **POST** | `/api/scheduling/batch` | Run checks asynchronously for datasets. | ✅ Done |
| **GET**  | `/api/reports/{id}` | Generate dataset quality report. | ✅ Done |
| **GET**  | `/api/reports/{dataset_id}/trends` | Timeline of quality scores. | ✅ Done |
| **GET**  | `/api/reports/dashboard` | Aggregated dataset scores. | ✅ Done |
| **POST** | `/api/schedule/` | Create/update a schedule. | ✅ Done |
| **GET**  | `/api/schedule/` | List schedules. | ✅ Done |
| **PATCH** | `/api/schedule/{id}/pause/` | Pause schedule. | ✅ Done |
| **PATCH** | `/api/schedule/{id}/resume/` | Resume schedule. | ✅ Done |
| **DELETE** | `/api/schedule/{id}/` | Delete schedule. | ✅ Done |
| **POST** | `/api/schedule/alerts/{id}/` | Set alert threshold. | ✅ Done |
| **GET** | `/metrics/` | Prometheus metrics endpoint. | ✅ Done |

> **Note:** For exact JSON schemas and models, please view the auto-generated **Swagger Documentation** by starting the server and navigating to `http://localhost:8000/docs/`.

---

## 3. How to Test the Reporting & Trends API

1. Start the server (e.g., `python manage.py runserver` or via Docker).
2. Go to `http://localhost:8000/docs/` and **Authorize** with a JWT Token (use `/api/auth/login`).
3. Upload a dataset via `POST /api/datasets/upload`.
4. Run checks via `POST /api/checks/run/{dataset_id}`. Take note of the dataset ID.
5. **Get Report**: Use `GET /api/reports/{dataset_id}` to see rules broken down by pass/fail + sample failing rows.
6. **Get Trends**: Call `GET /api/reports/{dataset_id}/trends` to see historical runs for that dataset. You can also filter by `start_date` and `end_date` (YYYY-MM-DD format) and use `limit`/`page` for pagination.
7. **Get Dashboard**: Call `GET /api/reports/dashboard` to get an overview of the latest scores for all your datasets.

---

## 4. Test Environment Setup

We use `pytest` along with `pytest-django` for our automated test suite, covering both unit tests and e2e integration tests.

- **Test Database**: `pytest-django` automatically spins up a clean, isolated SQLite or PostgreSQL database solely for testing purposes and tears it down afterwards.
- **Environment Variables (.env)**: When running tests inside Docker, it inherits the test configuration automatically.
- **Running Tests**:
  To execute all 60+ tests locally, run:
  ```bash
  docker-compose exec backend pytest -v
  ```
  To run specific tests (like the new role-based protection tests), run:
  ```bash
  docker-compose exec backend pytest backend/tests/test_protection.py -v
  ```

---

## 4. Data Schema

When uploading data, the engine parses `.csv` or `.json` (array of objects) files into Pandas DataFrames.
When creating Validation Rules via API (`POST /api/rules/`), the backend expects the following structured payload:

| Field          | Type   | Required | Description                                                                                         |
| -------------- | ------ | -------- | --------------------------------------------------------------------------------------------------- |
| `name`         | string | **Yes**  | Human readable name for the rule                                                                    |
| `dataset_type` | string | No       | Filter rule execution by file extension (e.g. `csv` or `json`). If blank, it acts as a global rule. |
| `rule_type`    | string | **Yes**  | Must be one of: `NOT_NULL`, `DATA_TYPE`, `RANGE`, `UNIQUE`, `REGEX`                                 |
| `field_name`   | string | **Yes**  | The exact name of the column/attribute to validate in the dataset.                                  |
| `severity`     | string | **Yes**  | Impacts scoring weight. Must be one of: `HIGH` (3x), `MEDIUM` (2x), `LOW` (1x)                      |
| `parameters`   | string | No       | Stringified JSON object detailing the check configurations. See below.                              |

### Parameters by `rule_type`:

- **`NOT_NULL`** / **`UNIQUE`**: _No parameters needed._ (Send `"{}"` or `""`)
- **`DATA_TYPE`**: Requires `{"expected_type": "int"}`. Valid expected types: `int`, `float`, `numeric`, `str`, `datetime`, `bool`.
- **`RANGE`**: Requires `{"min": 0, "max": 100}`. Both min and max are optional, but at least one must be provided.
- **`REGEX`**: Requires `{"pattern": "^[A-Z]+$"}`.

#### Validation Engine Scoring Rules:

The engine applies "partial credit" (proportional scoring). For example, if a dataset has 100 rows, and 80 rows pass a highly severe rule, the rule awards 80% of its total potential weight (weight=3) to the final dataset score. Total dataset score is scaled 0-100.

---

## 5. Test User Accounts

When you bring up the database for the first time using `docker-compose up --build`, an `entrypoint.sh` script automatically runs migrations and seeds the database with the following default test accounts.

You do **not** need to register these to start using the API immediately.

| Role             | Email                 | Password      |
| ---------------- | --------------------- | ------------- |
| **Admin**        | `admin@amalitech.com` | `password123` |
| **Regular User** | `user@amalitech.com`  | `password123` |
