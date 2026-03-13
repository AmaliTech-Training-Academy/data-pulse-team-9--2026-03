# DataPulse — DevOps & Infrastructure

Documentation for deployment, infrastructure, and operations.

## Architecture

| Document | Diagram | Description |
|----------|---------|-------------|
| [**Dev architecture**](DEV-ARCHITECTURE.md) | [datapulse-dev-architecture.drawio](datapulse-dev-architecture.drawio) | Development: single EC2, Docker Compose, ALB path-based routing, SSM, scheduler |
| [**Production architecture**](PRODUCTION-ARCHITECTURE.md) | [datapulse-prod-architecture.drawio](datapulse-prod-architecture.drawio) | Production: ECS Fargate, RDS, ElastiCache, ALB blue/green, CodeDeploy, Amplify |

Open the `.drawio` files in [draw.io](https://app.diagrams.net/) or a draw.io-compatible editor to view or edit the diagrams.

## Other docs

- [**Monitoring**](MONITORING.md) — Grafana, analytics DB, ETL pipeline
- [**Changelog**](CHANGELOG.md) — DevOps and infrastructure changes
