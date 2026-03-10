## Description
Added comprehensive monitoring and analytics infrastructure to DataPulse with Grafana dashboards, analytics database, and ETL pipeline for data quality insights.

### Key Changes:
- **Analytics Database**: Added separate PostgreSQL instance for analytics data isolation
- **Grafana Integration**: Configured Grafana service with custom dashboards for data quality monitoring
- **ETL Pipeline**: Implemented data transformation service to move operational data to analytics warehouse
- **Docker Orchestration**: Extended docker-compose with monitoring services and proper service dependencies
- **Environment Configuration**: Added analytics and monitoring environment variables

## Type of Change
- [x] `feat` - New feature
- [x] `devops` - Infrastructure/CI/CD

## Related Issue
Closes #27

## Testing
- [x] Tests added/updated
- [x] All tests pass locally
- [x] Tested with Docker Compose
- [x] Manual testing completed
- [x] Grafana dashboards accessible at http://localhost:3000
- [x] Analytics database connectivity verified
- [x] ETL pipeline data flow tested

## Checklist
- [x] Branch follows `type/description` format
- [x] PR title follows `type(scope): description` format
- [x] No secrets or `.env` files committed
- [x] Pre-commit hooks passed
- [x] Documentation updated (if needed)
- [x] Ready for review

## Additional Notes
- Grafana admin credentials configured via environment variables
- Analytics database runs on port 5433 to avoid conflicts
- ETL pipeline scheduled for every 6 hours (configurable)
- All monitoring services properly health-checked and dependency-managed
