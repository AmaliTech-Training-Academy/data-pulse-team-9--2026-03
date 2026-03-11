# Distributed Tracing Setup - Complete

##  What's Running

- **Tempo** (port 3200, 4317, 4318) - Trace storage
- **Grafana** (port 3000) - Visualization
- **Backend** - Instrumented with OpenTelemetry

##  View Traces in Grafana

1. **Open Grafana**: http://localhost:3000
   - Username: `<yourusername>`
   - Password: `<yourpassword>`

2. **Access Tempo Datasource**:
   - Go to **Explore** (compass icon in left sidebar)
   - Select **Tempo** from the datasource dropdown at the top

3. **Query Traces**:
   - Click "Search" tab
   - Select service: `datapulse-backend`
   - Click "Run query"
   - You'll see all traces from your Django backend

4. **View Trace Details**:
   - Click on any trace to see:
     - Request duration
     - Database queries
     - HTTP requests
     - Error details

##  Complete Observability Stack

| Component | Purpose | Port | URL |
|-----------|---------|------|-----|
| **Prometheus** | Metrics | 9090 | http://localhost:9090 |
| **Loki** | Logs | 3100 | http://localhost:3100 |
| **Tempo** | Traces | 3200 | http://localhost:3200 |
| **Grafana** | Visualization | 3000 | http://localhost:3000 |

##  Generate More Traces

Make requests to your backend:
```bash
curl http://localhost:8000/health/
curl http://localhost:8000/api/schema/
```

Each request creates a trace showing:
- HTTP request details
- Database queries (PostgreSQL)
- Response times
- Any errors

## 🔗 Correlate Logs & Traces

In Grafana Explore:
1. Query logs in Loki
2. Click on a log entry
3. If it has a trace ID, click "Tempo" to jump to the trace
