# AfriEdge Production Deployment Runbook

## 1. Prerequisites
- Docker Engine >= 24.0
- Node.js >= 20.x
- Python >= 3.11
- Managed PostgreSQL connection (`DATABASE_URL`)
- Managed Redis connection (`REDIS_URL`)
- LiteLLM Provider API Key (`LLM_API_KEY`)

## 2. Target Platforms
- **Frontend Workstation:** Vercel (Next.js 16 App Router)
- **API Engine:** GCP Cloud Run or Render Web Service (FastAPI)
- **Background Worker:** Celery container on Cloud Run Jobs or Render Background Worker
- **Database:** Managed Cloud PostgreSQL (Neon / Supabase / Cloud SQL)
- **Cache/Queue:** Managed Redis (Upstash / Redis Cloud)

## 3. Deployment Steps

### Step 1: Database Migration
Before directing traffic to new container versions:
```bash
alembic upgrade head
```

### Step 2: Build & Deploy Backend Container
```bash
docker build -t afriedge-api:latest -f Dockerfile.api .
# Deploy to cloud container registry and update service
```

### Step 3: Frontend Deployment on Vercel
1. Set Environment Variables in Vercel Dashboard:
   - `NEXT_PUBLIC_API_URL`: `https://api.afriedge.com` (or staging endpoint)
   - `API_URL_INTERNAL`: `https://api.afriedge.com`
2. Trigger Deployment from `master` branch.
3. Verify live probes:
   - `GET https://api.afriedge.com/health` -> `{"status": "ok"}`
   - `GET https://api.afriedge.com/ready` -> `{"status": "APP_HEALTHY", "database": "CONNECTED", "redis": "CONNECTED"}`

## 4. Rollback Procedure
If a production defect is discovered:
1. Re-deploy previous known good Git commit on Vercel and API host.
2. If database schema rollback is required:
   ```bash
   alembic downgrade -1
   ```
