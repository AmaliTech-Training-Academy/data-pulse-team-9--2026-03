# Alert System - Backend Technical Documentation

## Overview

The Alert System is integrated into the `schedule` app and triggered during the background task execution of quality checks.

## Architecture

### 1. Data Model (`schedule/models.py`)

- **`AlertConfig`**: One-to-one relationship with `Dataset`.
  - `threshold`: Integer (0-100).
  - `is_alert_active`: Boolean flag used for suppression. It is `True` if an alert has been sent and remains `True` until the score recovers.

### 2. API Endpoints

- **`POST /api/schedule/alerts/{dataset_id}/`**: Managed by `AlertConfigView`. Uses `update_or_create` to handle threshold settings.

### 3. Background Task Integration (`schedule/tasks.py`)

The `_handle_alerts` helper is called at the end of `run_scheduled_checks`.

**Flow:**

1. Fetch `AlertConfig` for the dataset.
2. If `current_score < threshold`:
   - If `not is_alert_active`:
     - Send email using `django.core.mail`.
     - Set `is_alert_active = True`.
3. Else (`current_score >= threshold`):
   - If `is_alert_active`:
     - Reset `is_alert_active = False` (Recovery).

### 4. Configuration

- **Settings**: Email backend and `FRONTEND_URL` are defined in `base.py`.
- **Environment**: Development uses the `Console` backend to output emails to logs.

## Testing

Tests are located in `backend/tests/test_alerts.py` and cover:

- CRUD for `AlertConfig`.
- Task execution with alert triggering.
- Suppression and recovery logic.
