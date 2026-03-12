# Schedule System - Backend Technical Documentation

## Overview

The `schedule` app enables users to automate dataset quality checks on a recurring basis using cron expressions. It integrates with `django-celery-beat` to persist and manage schedules in the database, and with the `checks` app's `ValidationEngine` to ensure that scheduled checks produce results **identical** to manually triggered ones.

---

## Architecture

### 1. Data Models (`schedule/models.py`)

#### `Schedule`
The bridge between a `Dataset` and a Celery Beat `PeriodicTask`.

| Field | Type | Description |
|---|---|---|
| `dataset` | OneToOneField | The dataset being monitored |
| `cron_expression` | CharField | Standard 5-part cron string (e.g. `0 6 * * *`) |
| `periodic_task` | OneToOneField | Linked `django_celery_beat.PeriodicTask` |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-updated on save |

> **Note:** When a `Schedule` is deleted, the linked `PeriodicTask` is explicitly deleted first in `perform_destroy` to ensure no orphaned background jobs remain.

#### `AlertConfig`
Configures quality score thresholds for email notifications. See [alerts-technical.md](./alerts-technical.md).

---

### 2. API Endpoints (`schedule/views.py`)

#### `GET /api/schedules/` — List Schedules
Returns a paginated list of all schedules with real-time status.

**Response fields include:**
- `is_active`: `true` if the background task is currently enabled, `false` if paused.
- `last_run`: Timestamp of when the task last fired (sourced from `PeriodicTask.last_run_at`).

---

#### `POST /api/schedules/` — Create / Update Schedule

Creates a new schedule, or updates the existing one for the given dataset.

**Request Body:**
```json
{
  "dataset_id": 1,
  "cron_expression": "0 6 * * *"
}
```

**Cron Validation:**
- Must be a valid 5-part expression: `minute hour day_of_month month day_of_week`.
- Validated using Celery's `crontab` helper.
- Returns **422 Unprocessable Entity** on failure.

**Internal flow:**
1. Validates serializer data (including cron format).
2. Creates or updates a `CrontabSchedule` in `django-celery-beat`.
3. Creates or updates a `PeriodicTask` pointing to `schedule.tasks.run_scheduled_checks`.
4. Creates or updates the `Schedule` model record linking dataset to the task.

---

#### `DELETE /api/schedules/{id}/` — Delete Schedule

Removes the `Schedule` record and the associated `PeriodicTask` entirely.

---

#### `PATCH /api/schedules/{id}/pause/` — Pause Schedule

Sets `periodic_task.enabled = False`.

**Response:**
```json
{ "status": "paused", "schedule_id": 1 }
```

---

#### `PATCH /api/schedules/{id}/resume/` — Resume Schedule

Sets `periodic_task.enabled = True`.

**Response:**
```json
{ "status": "resumed", "schedule_id": 1 }
```

---

### 3. Background Task (`schedule/tasks.py`)

The Celery task `run_scheduled_checks(dataset_id)` runs the full data quality pipeline for a given dataset.

**Execution Flow:**

```
1. Fetch Dataset by ID
        ↓
2. Load the associated file (CSV or JSON)
        ↓
3. Fetch active ValidationRules matching the dataset's file type
        ↓
4. Run ValidationEngine.run_all_checks(df, rules)
        ↓
5. Persist CheckResult records (previous results are cleared first)
        ↓
6. Calculate quality score via calculate_quality_score()
        ↓
7. Persist QualityScore record (previous score is cleared first)
        ↓
8. Update Dataset.status → "VALIDATED" or "FAILED"
        ↓
9. Create AuditLog (triggered_by="system", trigger_type="scheduled")
        ↓
10. Run _handle_alerts() → send email if score < threshold
```

> **Result Parity:** Steps 4–8 use the exact same `ValidationEngine` and `scoring_service` as manual checks triggered via the API, guaranteeing identical results.

---

### 4. Infrastructure & Configuration

#### Celery Beat Scheduler

The scheduler must use `DatabaseScheduler` to pick up dynamically created tasks.

In `datapulse/settings/base.py`:
```python
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
```

#### Running Locally

```bash
# Celery Worker
celery -A datapulse worker --loglevel=info

# Celery Beat
celery -A datapulse beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

#### Running with Docker Compose

The `worker` and `beat` services are defined in `docker-compose.yml` and start automatically.

---

## Testing

Tests are located in `backend/schedule/tests.py` and cover:

- Successful schedule creation and update.
- Cron expression validation and 422 error response.
- Pause, Resume, and Delete lifecycle transitions.
- `GET /api/schedules/` listing with `is_active` and `last_run` fields.
- End-to-end `run_scheduled_checks` task execution (file parsing → results → score → status update).

```bash
pytest schedule/tests.py
```
