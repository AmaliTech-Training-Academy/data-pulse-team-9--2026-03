# DataPulse

## Overview

Upload datasets, define rules, run checks, track trends.
Built with FastAPI + PostgreSQL + Pandas + Docker.

## Quick Start

docker-compose up --build
API: http://localhost:8000

## API Endpoints

| Method | Endpoint                 | Status |
| ------ | ------------------------ | ------ |
| POST   | /api/auth/register       | Done   |
| POST   | /api/auth/login          | Done   |
| POST   | /api/datasets/upload     | Done   |
| GET    | /api/datasets            | Done   |
| POST   | /api/rules               | Done   |
| GET    | /api/rules               | Done   |
| PUT    | /api/rules/{id}          | TODO   |
| DELETE | /api/rules/{id}          | TODO   |
| POST   | /api/checks/run/{id}     | TODO   |
| GET    | /api/checks/results/{id} | TODO   |
| GET    | /api/reports/{id}        | TODO   |
| GET    | /api/reports/trends      | TODO   |

## Team Roles

### Backend (2-3 people)

- Complete checks.py and reports.py routers
- Implement validation_engine.py checks
- Implement scoring and report services
- Add PUT/DELETE for rules

### Data Engineers (1-2 people)

- Complete ETL pipeline transform/load
- Build analytics schema
- Create Streamlit dashboard

### QA (1 person)

- Expand API tests
- Execute test plans
- Create edge case test data

### DevOps (1 person)

- Maintain CI/CD
- Optimize Docker
- Set up monitoring

## Env Vars

- DATABASE_URL (default: postgresql://datapulse:datapulse@db:5432/datapulse)
- SECRET_KEY (default: change-me-in-production)
- ALGORITHM (default: HS256)
- ACCESS_TOKEN_EXPIRE_MINUTES (default: 1440)
