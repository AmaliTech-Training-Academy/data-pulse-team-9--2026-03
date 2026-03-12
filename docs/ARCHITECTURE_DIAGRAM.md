# DataPulse Production Architecture (Without Custom Domain)

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                        │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌────────────────┐   ┌──────────────┐
│  AWS Amplify  │   │      ALB       │   │   Route53    │
│   (Frontend)  │   │  (HTTP:80)     │   │  (Optional)  │
│               │   │                │   │              │
│ Next.js App   │   │ datapulse-prod │   │ Custom Domain│
│               │   │ -XXXXX.elb...  │   │ (Future)     │
└───────────────┘   └────────┬───────┘   └──────────────┘
                             │
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌────────────────┐   ┌──────────────┐
│   Backend TG  │   │ Streamlit TG   │   │   Test TG    │
│   (Blue)      │   │   (Blue)       │   │   (Green)    │
│   Port 8000   │   │   Port 8501    │   │   Port 8080  │
└───────┬───────┘   └────────┬───────┘   └──────┬───────┘
        │                    │                   │
        │                    │                   │
        └────────────────────┼───────────────────┘
                             │
                             │
┌────────────────────────────┴────────────────────────────────────────────────┐
│                          ECS FARGATE CLUSTER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Backend    │  │Celery Worker │  │ Celery Beat  │  │  Streamlit   │   │
│  │   Service    │  │   Service    │  │   Service    │  │   Service    │   │
│  │              │  │              │  │              │  │              │   │
│  │ Django API   │  │ Task Queue   │  │  Scheduler   │  │  Dashboard   │   │
│  │ Gunicorn     │  │              │  │              │  │              │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │            │
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────────┘
          │                 │                 │                 │
          │                 │                 │                 │
          └─────────────────┼─────────────────┼─────────────────┘
                            │                 │
                            │                 │
        ┌───────────────────┼─────────────────┼───────────────────┐
        │                   │                 │                   │
        ▼                   ▼                 ▼                   ▼
┌───────────────┐   ┌────────────────┐   ┌──────────────┐   ┌──────────────┐
│  RDS Postgres │   │  RDS Postgres  │   │ ElastiCache  │   │   Secrets    │
│ (Operational) │   │  (Analytics)   │   │    Redis     │   │   Manager    │
│               │   │                │   │              │   │              │
│ db.t4g.micro  │   │ db.t4g.micro   │   │cache.t4g.micro│  │ Credentials  │
│ Port 5432     │   │ Port 5432      │   │ Port 6379    │   │              │
└───────────────┘   └────────────────┘   └──────────────┘   └──────────────┘
```

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VPC (10.0.0.0/16)                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      PUBLIC SUBNETS                                     │ │
│  │  ┌──────────────────────┐         ┌──────────────────────┐            │ │
│  │  │   eu-west-1a         │         │   eu-west-1b         │            │ │
│  │  │   10.0.1.0/24        │         │   10.0.2.0/24        │            │ │
│  │  │                      │         │                      │            │ │
│  │  │  ┌────────────────┐  │         │  ┌────────────────┐  │            │ │
│  │  │  │      ALB       │  │         │  │      ALB       │  │            │ │
│  │  │  │   (Primary)    │  │         │  │   (Standby)    │  │            │ │
│  │  │  └────────────────┘  │         │  └────────────────┘  │            │ │
│  │  └──────────────────────┘         └──────────────────────┘            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     PRIVATE SUBNETS                                     │ │
│  │  ┌──────────────────────┐         ┌──────────────────────┐            │ │
│  │  │   eu-west-1a         │         │   eu-west-1b         │            │ │
│  │  │   10.0.11.0/24       │         │   10.0.12.0/24       │            │ │
│  │  │                      │         │                      │            │ │
│  │  │  ┌────────────────┐  │         │  ┌────────────────┐  │            │ │
│  │  │  │  ECS Tasks     │  │         │  │  ECS Tasks     │  │            │ │
│  │  │  │  RDS Primary   │  │         │  │  RDS Standby   │  │            │ │
│  │  │  │  Redis Primary │  │         │  │  Redis Replica │  │            │ │
│  │  │  └────────────────┘  │         │  └────────────────┘  │            │ │
│  │  └──────────────────────┘         └──────────────────────┘            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      VPC ENDPOINTS                                      │ │
│  │  • ECR API  • ECR DKR  • S3  • Secrets Manager                         │ │
│  │  (No NAT Gateway needed - saves $32/month)                             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Security Groups

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SECURITY GROUP RULES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐                                                         │
│  │   ALB SG       │                                                         │
│  │                │                                                         │
│  │  Inbound:      │                                                         │
│  │  • 0.0.0.0/0   │  Port 80 (HTTP)                                        │
│  │  • 0.0.0.0/0   │  Port 443 (HTTPS) - if domain configured              │
│  │                │                                                         │
│  │  Outbound:     │                                                         │
│  │  • ECS SG      │  Port 8000, 8501                                       │
│  └────────┬───────┘                                                         │
│           │                                                                 │
│           ▼                                                                 │
│  ┌────────────────┐                                                         │
│  │   ECS SG       │                                                         │
│  │                │                                                         │
│  │  Inbound:      │                                                         │
│  │  • ALB SG      │  Port 8000 (Backend)                                   │
│  │  • ALB SG      │  Port 8501 (Streamlit)                                 │
│  │                │                                                         │
│  │  Outbound:     │                                                         │
│  │  • RDS SG      │  Port 5432                                             │
│  │  • Redis SG    │  Port 6379                                             │
│  │  • 0.0.0.0/0   │  Port 443 (AWS APIs via VPC endpoints)                │
│  └────────┬───────┘                                                         │
│           │                                                                 │
│           ├──────────────────┐                                             │
│           │                  │                                             │
│           ▼                  ▼                                             │
│  ┌────────────────┐  ┌────────────────┐                                   │
│  │   RDS SG       │  │   Redis SG     │                                   │
│  │                │  │                │                                   │
│  │  Inbound:      │  │  Inbound:      │                                   │
│  │  • ECS SG      │  │  • ECS SG      │                                   │
│  │    Port 5432   │  │    Port 6379   │                                   │
│  │                │  │                │                                   │
│  │  Outbound:     │  │  Outbound:     │                                   │
│  │  • None        │  │  • None        │                                   │
│  └────────────────┘  └────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REQUEST FLOW                                        │
└─────────────────────────────────────────────────────────────────────────────┘

1. USER REQUEST
   │
   ├─► Frontend Request
   │   │
   │   └─► AWS Amplify (Next.js)
   │       │
   │       └─► API Call to ALB DNS
   │
   └─► Direct API Request
       │
       └─► ALB (HTTP:80)
           │
           ├─► Path: /api/* ──► Backend Target Group ──► Django API
           │                                              │
           │                                              ├─► PostgreSQL (Operational)
           │                                              ├─► Redis (Cache/Queue)
           │                                              └─► Secrets Manager
           │
           └─► Path: /streamlit/* ──► Streamlit TG ──► Streamlit Dashboard
                                                         │
                                                         └─► PostgreSQL (Analytics)

2. BACKGROUND TASKS
   │
   ├─► Celery Beat (Scheduler)
   │   │
   │   └─► Schedules periodic tasks ──► Redis Queue
   │
   └─► Celery Worker
       │
       ├─► Reads from Redis Queue
       ├─► Processes tasks
       ├─► Writes to PostgreSQL
       └─► Sends results to Redis

3. ETL PIPELINE (Manual/Scheduled)
   │
   └─► ECS Task (Run once)
       │
       ├─► Reads from PostgreSQL (Operational)
       ├─► Transforms data
       └─► Writes to PostgreSQL (Analytics)
```

## Monitoring & Logging

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       OBSERVABILITY STACK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        APPLICATION LOGS                                 │ │
│  │                                                                         │ │
│  │  ECS Tasks ──► CloudWatch Logs ──► Log Groups                          │ │
│  │                                                                         │ │
│  │  • /ecs/datapulse-prod-backend                                         │ │
│  │  • /ecs/datapulse-prod-celery-worker                                   │ │
│  │  • /ecs/datapulse-prod-celery-beat                                     │ │
│  │  • /ecs/datapulse-prod-streamlit                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        METRICS                                          │ │
│  │                                                                         │ │
│  │  ECS Tasks ──► Amazon Managed Prometheus                               │ │
│  │                                                                         │ │
│  │  • CPU/Memory utilization                                              │ │
│  │  • Request rates                                                       │ │
│  │  • Error rates                                                         │ │
│  │  • Database connections                                                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        DASHBOARDS                                       │ │
│  │                                                                         │ │
│  │  Amazon Managed Grafana                                                │ │
│  │                                                                         │ │
│  │  • Application performance                                             │ │
│  │  • Infrastructure health                                               │ │
│  │  • Business metrics                                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Cost Optimization - Scheduler

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AUTOMATED SCHEDULER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  WEEKDAY SCHEDULE (Monday - Friday)                                         │
│  ════════════════════════════════════                                       │
│                                                                              │
│  07:00 UTC ──► EventBridge ──► Lambda (Start) ──► Start Services           │
│                                                    │                         │
│                                                    ├─► RDS Instances         │
│                                                    ├─► ECS Services          │
│                                                    └─► Wait for healthy      │
│                                                                              │
│  20:00 UTC ──► EventBridge ──► Lambda (Stop) ──► Stop Services             │
│                                                   │                          │
│                                                   ├─► ECS Services (scale 0) │
│                                                   └─► RDS Instances          │
│                                                                              │
│  WEEKEND (Saturday - Sunday)                                                │
│  ═══════════════════════════                                                │
│                                                                              │
│  All services STOPPED                                                       │
│                                                                              │
│  COST SAVINGS                                                               │
│  ════════════                                                               │
│                                                                              │
│  • Weekdays: 13 hours running (7am-8pm) = ~54% savings                     │
│  • Weekends: 0 hours running = 100% savings                                │
│  • Overall: ~60% reduction in compute costs                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Deployment Pipeline (Blue/Green)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CI/CD PIPELINE                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. CODE PUSH                                                               │
│     │                                                                        │
│     └─► GitHub (main branch)                                                │
│         │                                                                    │
│         └─► GitHub Actions Workflow                                         │
│             │                                                                │
│             ├─► Run Tests                                                   │
│             ├─► Build Docker Images                                         │
│             ├─► Push to ECR                                                 │
│             └─► Trigger CodeDeploy                                          │
│                                                                              │
│  2. BLUE/GREEN DEPLOYMENT                                                   │
│     │                                                                        │
│     └─► CodeDeploy                                                          │
│         │                                                                    │
│         ├─► Create GREEN task definition                                    │
│         ├─► Deploy GREEN tasks                                              │
│         ├─► Health check GREEN (test listener :8080)                        │
│         ├─► Shift 10% traffic to GREEN                                      │
│         ├─► Wait 5 minutes                                                  │
│         ├─► Shift 100% traffic to GREEN                                     │
│         └─► Terminate BLUE tasks                                            │
│                                                                              │
│  3. ROLLBACK (if health checks fail)                                        │
│     │                                                                        │
│     └─► Automatic rollback to BLUE                                          │
│         │                                                                    │
│         ├─► Shift traffic back to BLUE                                      │
│         ├─► Terminate GREEN tasks                                           │
│         └─► Alert team                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Access URLs

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       APPLICATION ENDPOINTS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BACKEND API                                                                │
│  ════════════                                                               │
│  http://datapulse-prod-XXXXX.eu-west-1.elb.amazonaws.com                   │
│                                                                              │
│  Endpoints:                                                                 │
│  • GET  /health/              - Health check                                │
│  • GET  /api/v1/...           - API endpoints                               │
│  • POST /api/v1/...           - API endpoints                               │
│                                                                              │
│  STREAMLIT DASHBOARD                                                        │
│  ════════════════════                                                       │
│  http://datapulse-prod-XXXXX.eu-west-1.elb.amazonaws.com/streamlit         │
│                                                                              │
│  FRONTEND (Next.js)                                                         │
│  ═══════════════════                                                        │
│  https://main.dXXXXXXXXXXXXXX.amplifyapp.com                                │
│                                                                              │
│  MONITORING                                                                 │
│  ══════════                                                                 │
│  • Grafana: AWS Console → Amazon Managed Grafana                            │
│  • Prometheus: AWS Console → Amazon Managed Service for Prometheus          │
│  • CloudWatch: AWS Console → CloudWatch → Log Groups                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Legend:**
- `───►` : Data flow direction
- `┌─┐` : Component boundary
- `│ │` : Vertical connection
- `└─┘` : Component boundary
