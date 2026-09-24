# AfriEdge Production Deployment Architecture

## 1. System Overview

AfriEdge is architected as an institutional-grade African investment research terminal. It decouples the user presentation layer (Next.js Edge on Vercel) from the deterministic financial compute engine and asynchronous research pipelines (FastAPI + Celery + PostgreSQL + Redis).

```
                         +-----------------------------------+
                         |           CLIENT BROWSER          |
                         +-----------------------------------+
                                         |
                                         | HTTPS
                                         v
                         +-----------------------------------+
                         |      VERCEL EDGE NETWORK          |
                         |      (Next.js App Router)         |
                         +-----------------------------------+
                                         |
                                         | HTTPS (JSON API)
                                         v
                         +-----------------------------------+
                         |     API GATEWAY (FastAPI)         |
                         |      Cloud Run / Docker           |
                         +-----------------------------------+
                            /            |             \
                           /             |              \
             SQLAlchemy   /              | Sync Redis    \ Enqueue Task
                         v               v                v
                 +------------+   +-------------+   +-------------------+
                 | PostgreSQL |   | Redis Cache |   | Celery Worker(s)  |
                 | Managed DB |   |  & Broker   |   |   (Research &     |
                 +------------+   +-------------+   |   Data Pipelines) |
                                                    +-------------------+
                                                      /        |        \
                                                     /         |         \
                                                    v          v          v
                                                [Firecrawl] [Central]  [Listed]
                                                [Scraper]   [Banks]    [Exchanges]
```

## 2. Infrastructure Components

| Layer | Provider / Runtime | Purpose | Health Monitoring |
|---|---|---|---|
| **Frontend** | Vercel (Next.js 16 App Router) | Interactive analyst workstation, charts, evidence graphs | Vercel Analytics / Sentry Web |
| **API Backend** | GCP Cloud Run / Container | Deterministic REST API, Auth, Portfolio CRUD | `/health`, `/ready` |
| **Database** | Managed PostgreSQL (Cloud SQL / Neon) | Relational store for users, portfolios, evidence, companies | Connection pool telemetry |
| **Worker Queue** | Redis (Memorystore / Upstash) | Asynchronous task queue for long-running research jobs | Redis heartbeat ping |
| **Background Workers** | Celery on Container Service | Asynchronous PDF ingestion, dual-extraction, report synthesis | Celery event monitor |
| **Telemetry & Observability** | Sentry & PostHog | Error tracking, LLM token cost telemetry, product metrics | Sentry DSN / PostHog SDK |

## 3. Communication Contracts

1. **Client -> API:** HTTPS with JWT Bearer authentication. All endpoints versioned under `/api/v1/`.
2. **Deterministic Computing:** Pure Python execution for ratios, metrics, portfolio optimization (SciPy), and fixed income. The LLM is never on the critical arithmetic path.
3. **Evidence Lineage:** Every extracted number links back to an immutable `Evidence` record containing source URL, document hash, page, and table coordinates.
