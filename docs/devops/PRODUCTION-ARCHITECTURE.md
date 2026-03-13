# DataPulse Production Environment — Architecture

This document describes the **production (prod)** AWS architecture for DataPulse. The environment is defined in Terraform under `terraform/environments/prod/` and uses **ECS Fargate**, **RDS**, **ElastiCache**, and an **Application Load Balancer** with blue/green deployments.

## Diagram

An architectural diagram is available as a draw.io file:

- **Path:** `docs/devops/datapulse-prod-architecture.drawio`
- **Usage:** Open in [draw.io](https://app.diagrams.net/) or VS Code with a draw.io extension to view or edit.

The diagram shows VPC layout, subnets, ALB, ECS tasks, RDS, ElastiCache, VPC endpoints, and supporting services (Secrets Manager, SSM, ECR, CodeDeploy, Scheduler, Amplify, GitHub OIDC).

---

## Overview

| Aspect | Production |
|--------|-------------|
| **Region** | `eu-west-1` |
| **VPC CIDR** | `10.0.0.0/16` |
| **Availability Zones** | `eu-west-1a`, `eu-west-1b` |
| **Compute** | ECS Fargate (no EC2 for app workloads) |
| **Databases** | RDS PostgreSQL (2 instances: operational + analytics) |
| **Cache** | ElastiCache Redis |
| **Ingress** | Application Load Balancer (HTTP/HTTPS) |
| **Frontend** | AWS Amplify (Next.js), optional |
| **Outbound** | No NAT Gateway; private subnets use VPC endpoints |

---

## Network

- **Public subnets** (`10.0.0.0/24`, `10.0.1.0/24`): Internet Gateway, ALB.
- **Private subnets** (`10.0.10.0/24`, `10.0.11.0/24`): ECS Fargate tasks, RDS, ElastiCache.
- **VPC endpoints** (interface): `ecr.api`, `ecr.dkr`, `secretsmanager`, `logs`, `ssm` (and S3 gateway). Used so tasks can pull images and secrets without NAT.

---

## Core Components

### Application Load Balancer (ALB)

- **Name:** `datapulse-prod`
- **Subnets:** Public (both AZs).
- **Listeners:** HTTP (80), optionally HTTPS (443) if `domain_name` is set (ACM certificate).
- **Path-based routing:**
  - `/api/*`, `/health/*`, `/admin/*` → Backend (Django).
  - `/streamlit/*` → Streamlit.
  - `/grafana/*` → Grafana.
  - Default → Frontend or backend, depending on config.
- **Blue/Green:** Separate target groups (blue/green) per service for CodeDeploy canary deployments; test listener on port 8080.

### ECS Fargate

- **Cluster:** `datapulse-prod`.
- **Capacity:** Fargate + Fargate Spot.
- **Services:**
  - **Backend** (Django): API, admin; registered to ALB backend target group.
  - **Celery worker** and **Celery beat**: async and scheduled tasks.
  - **Streamlit**: dashboards; registered to Streamlit target group.
  - **Grafana**: metrics UI; registered to Grafana target group.
- **Secrets:** From Secrets Manager (`datapulse/prod/*`) and SSM Parameter Store (`/datapulse/prod/*`). No long-lived credentials in task definitions.
- **Logs:** CloudWatch Logs; 14-day retention.

### RDS PostgreSQL

- **Two instances** (same subnet group, private subnets):
  - **Operational:** `datapulse-prod-operational` — main app DB.
  - **Analytics:** `datapulse-prod-analytics` — analytics warehouse.
- **Class:** `db.t4g.micro` (Graviton).
- **Engine:** PostgreSQL 15; storage encrypted.
- **Schedule:** Start/stop via Scheduler Lambda (e.g. start 7am, stop 8pm weekdays) to reduce cost.

### ElastiCache Redis

- **Node type:** `cache.t4g.micro`.
- **Subnets:** Private.
- **Usage:** Celery broker, cache, sessions.

### ECR

- Repositories: `datapulse-backend`, `datapulse-etl`, `datapulse-streamlit`, `datapulse-grafana`.
- Image scan on push; lifecycle policy keeps last 5 images per repo.

---

## Secrets and Config

- **Secrets Manager** (`datapulse/prod/*`): Passwords, `database_url`, `target_db_url`, `redis_url`, `secret_key`, `grafana_password`, etc. 7-day recovery window on delete.
- **SSM Parameter Store** (`/datapulse/prod/*`): Non-sensitive config (e.g. `postgres_user`, `postgres_db`, `django_settings_module`, `grafana_user`).
- **Terraform:** Sensitive values (e.g. passwords) come from `terraform.tfvars` (gitignored); Terraform writes them into Secrets Manager/SSM.

---

## CI/CD and Deployments

- **GitHub Actions OIDC:** IAM role `datapulse-prod-github-actions`; no long-lived GitHub secrets. Trust policy scoped to `repo:<github_repo>:ref:refs/heads/main`.
- **Permissions:** ECR push, ECS update/describe, CodeDeploy create/get/stop, SSM GetParameter for `/datapulse/prod/*`.
- **CodeDeploy:** Blue/green ECS deployments; canary with test listener (e.g. 8080). Lambda hooks can run pre/post traffic shift.

---

## Scheduler (Cost Optimization)

- **EventBridge rules:** e.g. start 7am, stop 8pm (weekdays).
- **Lambda:** Start/stop ECS services and RDS instances; reads instance/cluster identifiers from SSM.
- **Affected:** ECS services (backend, celery-worker, celery-beat, streamlit, grafana); RDS operational and analytics instances.

---

## Optional: Frontend (Amplify)

- **Module:** `terraform/modules/amplify`.
- **App:** Next.js frontend; connected to GitHub repo; optional custom domain via `domain_name`.
- **API URL:** Prod API base URL is ALB DNS (or custom domain if set). Frontend calls backend via this URL.

---

## Monitoring

- **Managed Prometheus:** Workspace alias `datapulse-prod`.
- **Grafana:** Workspace `datapulse-prod`; data sources include Prometheus, CloudWatch, X-Ray. IAM role for CloudWatch access.
- **Container Insights:** Enabled on the ECS cluster.

---

## Security

- **ALB:** Deletion protection enabled; security group allows 80/443 from internet (and 8080 from VPC if used for test listener).
- **ECS tasks:** Only in private subnets; no public IPs; pull images via VPC endpoints; secrets from Secrets Manager/SSM.
- **RDS / ElastiCache:** Private subnets only; security groups restrict access to ECS and required ports (5432, 6379).
- **Tags:** `Project=datapulse`, `Environment=prod`, `ManagedBy=terraform` on resources.

---

## Terraform State

- **Backend:** S3 bucket `datapulse-team9-terraform-state`, key `prod/terraform.tfstate`, region `eu-west-1`, encryption and locking enabled.

---

## Related Docs

- [Monitoring](MONITORING.md) — Grafana, analytics, ETL.
- [Changelog](CHANGELOG.md) — DevOps and infra changes.
- **Dev architecture:** See [Dev architecture](DEV-ARCHITECTURE.md) and `docs/devops/datapulse-dev-architecture.drawio` for the dev (EC2-based) setup.
