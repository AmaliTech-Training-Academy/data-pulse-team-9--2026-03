# DataPulse Django — Project Structure & Migration Guide

This document explains the structure of the Django version of DataPulse, what each app and module does, and how it maps to the original FastAPI starter code.

---

## High-Level Directory Layout

```
datapulse-django/
├── backend/                 # Django application (replaces backend/ from FastAPI)
│   ├── manage.py            # Django CLI entry point (replaces uvicorn)
│   ├── Dockerfile           # Container build (same pattern, different CMD)
│   ├── requirements.txt     # Python dependencies (Django stack)
│   ├── pytest.ini           # Test runner configuration
│   │
│   ├── datapulse/           # Django project settings (replaces app/config.py + app/main.py)
│   │   ├── settings.py      # All configuration (DB, JWT, CORS, installed apps)
│   │   ├── urls.py          # Root URL routing (replaces FastAPI router includes)
│   │   └── wsgi.py          # WSGI entry point
│   │
│   ├── authentication/      # 🔐 Auth app (replaces app/routers/auth.py + app/services/auth_service.py)
│   ├── datasets/            # 📁 Datasets app (replaces app/routers/upload.py + app/services/file_parser.py)
│   ├── rules/               # 📏 Rules app (replaces app/routers/rules.py)
│   ├── checks/              # ✅ Checks app (replaces app/routers/checks.py + services/)
│   ├── reports/             # 📊 Reports app (replaces app/routers/reports.py + services/)
│   │
│   ├── tests/               # Unit tests (replaces backend/tests/)
│   └── uploads/             # File upload storage (same as original)
│
├── devops/                  # DevOps configs (copied, CI updated for Django)
├── qa/                      # QA test plans & external API tests (copied as-is)
├── data-engineering/        # ETL pipeline & analytics (copied as-is)
├── docker-compose.yml       # Docker orchestration (same structure)
├── .gitignore
└── README.md
```

---

## Technology Mapping

| Concern | FastAPI (Original) | Django (New) |
|---|---|---|
| Web framework | `fastapi` | `django` + `djangorestframework` |
| Server | `uvicorn` | `manage.py runserver` / `gunicorn` |
| ORM | `sqlalchemy` | Django ORM (built-in) |
| Schemas / Serialization | `pydantic` models | DRF serializers |
| JWT Authentication | `python-jose` | `djangorestframework-simplejwt` |
| Password Hashing | `passlib[bcrypt]` | Django's `BCryptSHA256PasswordHasher` |
| CORS | `CORSMiddleware` (FastAPI) | `django-cors-headers` |
| File Uploads | `UploadFile` (FastAPI) | `request.FILES` (Django) |
| Config / Env Vars | `pydantic-settings` | `os.getenv()` in `settings.py` |
| Testing | `pytest` + `TestClient` | `pytest-django` + DRF `APIClient` |
| Database | PostgreSQL via SQLAlchemy | PostgreSQL via Django ORM |
| Data Processing | `pandas` | `pandas` (unchanged) |

---

## App-by-App Breakdown

### 1. `datapulse/` — Project Configuration

**Replaces:** `app/main.py` + `app/config.py` + `app/database.py`

| File | Purpose | FastAPI Equivalent |
|------|---------|-------------------|
| `settings.py` | DB config, JWT config, CORS, installed apps | `config.py` (Settings class) + `database.py` |
| `urls.py` | Root URL routing + `/` and `/health` endpoints | `main.py` (app.include_router + root/health routes) |
| `wsgi.py` | WSGI server entry | N/A (uvicorn handled this) |

**Key difference:** Django uses `settings.py` for everything — database connection, JWT lifetime, secret key, CORS. In FastAPI, these were split across `config.py`, `database.py`, and `main.py`.

---

### 2. `authentication/` — User Registration & Login 🔐

**Replaces:** `app/routers/auth.py` + `app/schemas/auth.py` + `app/services/auth_service.py` + `app/models/user.py` + `app/utils/jwt_handler.py` + `app/utils/dependencies.py`

| File | Purpose | FastAPI Equivalent |
|------|---------|-------------------|
| `models.py` | `User` model (email-based, custom manager) | `app/models/user.py` |
| `serializers.py` | `UserCreateSerializer`, `LoginSerializer`, `TokenSerializer` | `app/schemas/auth.py` |
| `services.py` | `create_user()`, `authenticate_user()` | `app/services/auth_service.py` |
| `views.py` | `POST /register`, `POST /login` | `app/routers/auth.py` |
| `urls.py` | Route definitions | Part of `main.py` |

**Endpoints (both ✅ implemented):**
| Method | URL | What it does |
|--------|-----|-------------|
| POST | `/api/auth/register` | Creates user, returns JWT (201) |
| POST | `/api/auth/login` | Authenticates user, returns JWT (200) |

**Key difference:** JWT tokens are generated via `SimpleJWT`'s `AccessToken.for_user()` instead of manually calling `jose.jwt.encode()`. The token format is identical (`{"access_token": "...", "token_type": "bearer"}`).

---

### 3. `datasets/` — File Upload & Dataset Management 📁

**Replaces:** `app/routers/upload.py` + `app/schemas/dataset.py` + `app/models/dataset.py` + `app/services/file_parser.py`

| File | Purpose | FastAPI Equivalent |
|------|---------|-------------------|
| `models.py` | `Dataset`, `DatasetFile` models | `app/models/dataset.py` |
| `serializers.py` | `DatasetResponseSerializer`, `DatasetListSerializer` | `app/schemas/dataset.py` |
| `services/file_parser.py` | `parse_csv()`, `parse_json()` using Pandas | `app/services/file_parser.py` (identical) |
| `views.py` | Upload and list endpoints | `app/routers/upload.py` |
| `urls.py` | Route definitions | Part of `main.py` |

**Endpoints (both ✅ implemented):**
| Method | URL | What it does |
|--------|-----|-------------|
| POST | `/api/datasets/upload` | Upload CSV/JSON, store metadata (201) |
| GET | `/api/datasets` | List datasets with skip/limit pagination (200) |

**Key difference:** File upload uses Django's `request.FILES` and `MultiPartParser` instead of FastAPI's `UploadFile = File(...)`. The `file_parser.py` is identical — it's pure Pandas with no framework dependency.

---

### 4. `rules/` — Validation Rule Management 📏

**Replaces:** `app/routers/rules.py` + `app/schemas/rule.py` + `app/models/rule.py`

| File | Purpose | FastAPI Equivalent |
|------|---------|-------------------|
| `models.py` | `ValidationRule` model | `app/models/rule.py` |
| `serializers.py` | `RuleCreateSerializer`, `RuleResponseSerializer`, `RuleUpdateSerializer` | `app/schemas/rule.py` |
| `views.py` | CRUD endpoints (create/list done, update/delete TODO) | `app/routers/rules.py` |
| `urls.py` | Route definitions | Part of `main.py` |

**Endpoints:**
| Method | URL | Status |
|--------|-----|--------|
| POST | `/api/rules` | ✅ Create rule (201) |
| GET | `/api/rules` | ✅ List rules with optional `dataset_type` filter (200) |
| PUT | `/api/rules/{id}` | ⚠️ TODO — returns 501 |
| DELETE | `/api/rules/{id}` | ⚠️ TODO — returns 501 |

**Key difference:** Django can't natively bind multiple HTTP methods to the same URL path with separate function views. We use `@api_view(["POST", "GET"])` on a single `rules_root` view to handle both, and `@api_view(["PUT", "DELETE"])` on `rule_detail`. The TODO stubs have the exact same docstrings with implementation steps.

---

### 5. `checks/` — Quality Check Execution ✅

**Replaces:** `app/routers/checks.py` + `app/schemas/report.py` (partial) + `app/models/check_result.py` + `app/services/validation_engine.py` + `app/services/scoring_service.py`

| File | Purpose | FastAPI Equivalent |
|------|---------|-------------------|
| `models.py` | `CheckResult`, `QualityScore` models | `app/models/check_result.py` |
| `serializers.py` | `CheckResultResponseSerializer`, `QualityScoreResponseSerializer` | `app/schemas/report.py` (partial) |
| `services/validation_engine.py` | `ValidationEngine` class with check methods | `app/services/validation_engine.py` (identical) |
| `services/scoring_service.py` | `calculate_quality_score()` | `app/services/scoring_service.py` (identical) |
| `views.py` | Run checks and get results endpoints | `app/routers/checks.py` |
| `urls.py` | Route definitions | Part of `main.py` |

**Endpoints (all ⚠️ TODO stubs):**
| Method | URL | Status |
|--------|-----|--------|
| POST | `/api/checks/run/{dataset_id}` | ⚠️ TODO — 10-step implementation guide in docstring |
| GET | `/api/checks/results/{dataset_id}` | ⚠️ TODO — 3-step implementation guide in docstring |

**Validation Engine Status:**
| Check Type | Status |
|-----------|--------|
| `null_check` | ✅ Implemented |
| `type_check` | ⚠️ TODO stub |
| `range_check` | ⚠️ TODO stub |
| `unique_check` | ⚠️ TODO stub |
| `regex_check` | ⚠️ TODO stub |

---

### 6. `reports/` — Quality Reports & Trends 📊

**Replaces:** `app/routers/reports.py` + `app/schemas/report.py` (partial) + `app/services/report_service.py`

| File | Purpose | FastAPI Equivalent |
|------|---------|-------------------|
| `serializers.py` | `QualityReportSerializer` | `app/schemas/report.py` (QualityReport) |
| `services/report_service.py` | `generate_report()`, `get_trend_data()` | `app/services/report_service.py` (identical stubs) |
| `views.py` | Report and trends endpoints | `app/routers/reports.py` |
| `urls.py` | Route definitions | Part of `main.py` |

**Endpoints (all ⚠️ TODO stubs):**
| Method | URL | Status |
|--------|-----|--------|
| GET | `/api/reports/{dataset_id}` | ⚠️ TODO — 5-step implementation guide in docstring |
| GET | `/api/reports/trends` | ⚠️ TODO — 4-step implementation guide in docstring |

---

## Non-Backend Folders (Unchanged)

### `devops/`
- `.github/workflows/ci.yml` — GitHub Actions CI (lint → test → docker build). Updated to run `pytest` with Django.
- `Dockerfile.pipeline` — Container for the ETL pipeline (unchanged)
- `scripts/setup.sh` — Quick setup script (unchanged)

### `qa/`
- `api-tests/` — External API tests using `requests` library (framework-agnostic, test against `http://localhost:8000`)
- `test-data/` — `valid_test.csv` and `invalid_test.csv` sample files
- `test-plan/` — Test plan checklist template

### `data-engineering/`
- `pipeline/etl_pipeline.py` — ETL class with extract (✅), transform (TODO), load (TODO)
- `pipeline/data_models.py` — SQLAlchemy models for analytics dimension/fact tables
- `dashboards/quality_dashboard.py` — Streamlit dashboard stub
- `sql/analytics_schema.sql` — DDL for analytics tables
- `sample_data/` — CSV test datasets

---

## Database Table Mapping

All table names are **identical** between FastAPI and Django versions:

| Table | Django App | Model |
|-------|-----------|-------|
| `users` | `authentication` | `User` |
| `datasets` | `datasets` | `Dataset` |
| `dataset_files` | `datasets` | `DatasetFile` |
| `validation_rules` | `rules` | `ValidationRule` |
| `check_results` | `checks` | `CheckResult` |
| `quality_scores` | `checks` | `QualityScore` |

---

## Environment Variables

Same variables, same defaults as the original:

| Variable | Default | Used In |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql://<user>:<password>@db:5432/<dbname>` | `settings.py` |
| `SECRET_KEY` | `change-me-in-production` | `settings.py`, JWT signing |
| `ALGORITHM` | `HS256` | `settings.py`, JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | `settings.py`, JWT lifetime |
| `UPLOAD_DIR` | `uploads/` | `settings.py`, file storage |
