# DataPulse Logging Setup

## Overview
Centralized logging solution using Loki + Promtail + Grafana for log aggregation, collection, and visualization.

## Components

### 1. Loki (Log Aggregation)
- **Port**: 3100
- **Config**: `devops/loki/loki-config.yml`
- **Storage**: Filesystem-based with 31-day retention
- **Status**: http://localhost:3100/ready

### 2. Promtail (Log Collector)
- **Config**: `devops/promtail/promtail-config.yml`
- **Function**: Collects logs from all Docker containers
- **Labels**: Automatically adds container, service, and stream labels

### 3. Grafana (Visualization)
- **Port**: 3000
- **Credentials**: admin / datapulse123
- **Datasource**: `devops/grafana/provisioning/datasources/loki.yml`
- **Dashboard**: `devops/grafana/provisioning/dashboards/datapulse-logs.json`

## Access Points

- **Grafana**: http://localhost:3000
- **Loki API**: http://localhost:3100
- **Prometheus**: http://localhost:9090

## Verification

```bash
# Check Loki status
curl http://localhost:3100/ready

# Check available log labels
curl http://localhost:3100/loki/api/v1/label

# View all services
docker-compose ps
```

## Log Retention
- **Period**: 744 hours (31 days)
- **Rate Limit**: 16 MB/s ingestion
- **Burst Size**: 32 MB

## Troubleshooting

1. **Loki not starting**: Check logs with `docker logs datapulse-loki`
2. **No logs in Grafana**: Verify Promtail is running and connected to Loki
3. **Promtail errors**: Restart with `docker-compose restart promtail`
