# DataPulse Development Environment — Architecture

This document describes the **development (dev)** AWS architecture for DataPulse. The environment is defined in Terraform under `terraform/environments/dev/` and runs the full application stack on a **single EC2 instance** using **Docker Compose**, with an **Application Load Balancer (ALB)** providing a single entry point and path-based routing.

---

## Diagram

An architectural diagram is available as a draw.io file:

| File | Description |
|------|-------------|
| **`docs/devops/datapulse-dev-architecture.drawio`** | Dev environment: VPC, ALB, EC2, SSM, Scheduler, application services |

**How to use:** Open the file in [draw.io](https://app.diagrams.net/) or in VS Code with a draw.io extension to view or edit.

The diagram shows:

- AWS Cloud and VPC layout (two AZs, public and private subnets)
- Internet Gateway, ALB, Elastic IP, and EC2 instance
- Security groups (EC2, ALB; ECS/RDS/Redis SGs exist in the shared module but are unused in dev)
- SSM Parameter Store for config and secrets
- Scheduler (EventBridge + Lambda) for EC2 start/stop
- Application services running on EC2 (Docker Compose): Frontend, Backend, Streamlit, Grafana, Prometheus, Loki, Tempo, PostgreSQL

---

## Overview

| Aspect | Development |
|--------|-------------|
| **Region** | `eu-west-1` |
| **VPC CIDR** | `10.1.0.0/16` (separate from prod `10.0.0.0/16`) |
| **Availability Zones** | `eu-west-1a`, `eu-west-1b` |
| **Compute** | Single EC2 instance (e.g. `t3.small`), Amazon Linux 2023 |
| **Storage** | 30 GB gp3 EBS (encrypted) |
| **Application runtime** | Docker Compose on EC2 (all services on one host) |
| **Databases** | PostgreSQL and Redis run as containers on the same EC2 |
| **Ingress** | Application Load Balancer (HTTP :80) + optional direct access via Elastic IP |
| **Secrets & config** | SSM Parameter Store (`/datapulse/dev/*`) |
| **Cost optimization** | Scheduler stops EC2 at 8pm, starts at 7am (weekdays) |

---

## Network

### Subnets

- **Public subnets**
  - `10.1.0.0/24` (eu-west-1a), `10.1.1.0/24` (eu-west-1b)
  - Used for: Internet Gateway, ALB, and the **EC2 instance** (dev runs in public subnet for simplicity).
- **Private subnets**
  - `10.1.10.0/24`, `10.1.11.0/24`
  - Present for VPC module consistency; in dev no application workloads run here.
  - VPC interface endpoints (ecr.api, ecr.dkr, secretsmanager, logs, ssm) and S3 gateway endpoint exist in the private subnets for potential future use or shared module reuse.

### Traffic flow

1. **Via ALB (recommended for app traffic)**
   Internet → IGW → ALB (HTTP :80) → path-based routing → EC2 (ports 3001, 8000, 8501, 3000).

2. **Direct to EC2**
   Internet → IGW → Elastic IP → EC2 (SSH :22 or direct app ports if allowed by `allowed_cidr`).
   Use for SSH, debugging, or when ALB is not in use.

---

## Core Components

### Application Load Balancer (ALB)

- **Name:** `datapulse-dev`
- **Listeners:** HTTP on port 80 (no HTTPS in dev by default).
- **Target type:** Instance (single EC2 registered with multiple target groups, one per service port).
- **Path-based routing:**

| Path pattern(s) | Target group | EC2 port | Service |
|----------------|-------------|----------|---------|
| Default `/` | Frontend | 3001 | Next.js frontend |
| `/api`, `/api/*`, `/health/*`, `/admin`, `/admin/*` | Backend | 8000 | Django API |
| `/streamlit`, `/streamlit/`, `/streamlit/*` | Streamlit | 8501 | Streamlit app |
| `/grafana`, `/grafana/`, `/grafana/*` | Grafana | 3000 | Grafana |

- **Health checks:** Backend `/health/`, Frontend `/`, Streamlit `/_stcore/health`, Grafana `/api/health`.
- **Deletion protection:** Disabled for dev.

### EC2 instance

- **Name / tags:** `datapulse-dev`, `ScheduleStop=true`.
- **Role:** Runs Docker Compose; pulls code (e.g. from GitHub), builds/pulls images, and starts services.
- **User data:** Installs Docker, configures env from SSM (via `refresh-env.sh`), clones repo, and runs deploy logic.
- **IAM:** Instance profile with SSM read (Parameter Store) so the instance can load config and secrets at boot and during deploy.
- **Key pair:** Stored in Secrets Manager for SSH access; Terraform keypair module manages it.

### Application services (Docker Compose on EC2)

All run on the same EC2; ports are mapped to the host and targeted by the ALB:

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 3001 | Next.js app; default ALB route `/`. |
| **Backend** | 8000 | Django API, admin; ALB paths `/api/*`, `/health/*`, `/admin/*`. |
| **Streamlit** | 8501 | Streamlit dashboards; ALB path `/streamlit/*`. |
| **Grafana** | 3000 | Grafana UI; ALB path `/grafana/*`. |
| **Prometheus** | 9090 | Metrics (direct or internal). |
| **Loki** | 3100 | Logs (internal). |
| **Tempo** | 3200 | Traces (internal). |
| **PostgreSQL** | 5432 | Main DB (container). |
| **Redis** | 6379 | Cache/Celery broker (container). |

Other containers (e.g. Celery worker, Celery beat, ETL, db-seed) also run on the same host as needed by `docker-compose.yml`.

---

## Secrets and configuration

- **SSM Parameter Store** prefix: `/datapulse/dev/`
  - **String parameters:** `postgres_user`, `postgres_db`, `analytics_user`, `analytics_db`, `django_settings_module`, `grafana_user`.
  - **SecureString parameters:** `postgres_password`, `analytics_password`, `secret_key`, `grafana_password`.
- **Scheduler:** Lambda reads EC2 instance ID from SSM (e.g. `scheduler/instance_id`) to start/stop the instance.
- **On EC2:** A `.env` file is generated/refreshed from SSM (and optionally Secrets Manager) via `scripts/refresh-env.sh` so Docker Compose and apps get the same values.

---

## CI/CD and deployment

- **GitHub Actions:** Workflow (e.g. `cd-dev.yml`) deploys to the dev EC2 on push to the develop branch.
- **Deploy steps:** SSH to EC2, refresh `.env` from SSM, pull code, `docker compose` build/up, health checks.
- **Health checks:** Backend `/health/`, frontend `:3001/`, Streamlit `:8501/` (see `scripts/deploy-dev.sh` and workflow).

---

## Scheduler (cost optimization)

- **EventBridge rules:** e.g. start at 7am, stop at 8pm (weekdays).
- **Lambda:** Start/stop the EC2 instance; reads instance ID from SSM.
- **IAM:** Role for Lambda with EC2 start/stop/describe and SSM GetParameter.

---

## Security

- **ALB security group:** Ingress 80 from `0.0.0.0/0`; egress all. No deletion protection in dev.
- **EC2 security group:**
  - Ingress: SSH (22), Backend (8000), Frontend (3001), Streamlit (8501), Grafana (3000), Prometheus (9090), Loki (3100), Tempo (3200) from `allowed_cidr`; plus same app ports from ALB security group.
  - Egress: all.
- **ECS/RDS/Redis/endpoints SGs:** Created by the shared security module; not used by any dev resources (dev has no ECS, RDS, or ElastiCache).
- **Tags:** `Project=datapulse`, `Environment=dev`, `ManagedBy=terraform`.

---

## Terraform state and outputs

- **Backend:** S3 bucket `datapulse-team9-terraform-state`, key `dev/terraform.tfstate`, region `eu-west-1`, encryption and locking enabled.

**Useful outputs:**

| Output | Description |
|--------|-------------|
| `instance_id` | EC2 instance ID |
| `public_ip` | Elastic IP (direct EC2 access) |
| `service_urls` | Direct URLs by service (e.g. backend :8000, frontend :3001) |
| `alb_dns_name` | ALB DNS name |
| `alb_url` | Base URL via ALB (e.g. `http://<alb_dns>`) |
| `alb_service_paths` | Full URLs for frontend, backend, streamlit, grafana via ALB |

Set `NEXT_PUBLIC_API_URL` (e.g. to `alb_url`) so the frontend calls the backend through the ALB.

---

## Related documentation

- [Production architecture](PRODUCTION-ARCHITECTURE.md) — ECS Fargate, RDS, ElastiCache, blue/green.
- [Monitoring](MONITORING.md) — Grafana, analytics, ETL.
- [Changelog](CHANGELOG.md) — DevOps and infrastructure changes.
