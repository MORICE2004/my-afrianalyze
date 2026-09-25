# Observability

Rewritten 2026-09-25. The previous version described telemetry in the legacy `agents/` layer, which the
live API does not load. This is what exists for the v1 code path.

| Signal | Where | Status |
|---|---|---|
| Is the API up and able to serve? | `GET /ready`: 200 `APP_HEALTHY` or `DEGRADED` (with the stale sources listed); 503 `DATABASE_UNAVAILABLE` or `DATABASE_NOT_SEEDED`. Render's health check points here | REAL, tested |
| How fresh is each data source? | `GET /health` and the `/health` page: every source with its last success, age and limit | REAL, tested |
| Server errors | Python logging to stdout (Render collects it). Database failures are logged with the traceback there, never returned to the caller | REAL |
| Error reporting to Sentry (backend) | `sentry_sdk.init` in `apps/api/main.py` when `SENTRY_DSN` is set: errors only, no tracing, `send_default_pii=False`, request bodies never sent | **wired, not connected**: no Sentry project exists. Status `BLOCKED` on the owner creating one |
| Error reporting to Sentry (frontend) | none | MISSING. Needs `@sentry/nextjs` and a project |
| Product analytics (PostHog) | none | MISSING. Needs a project and a decision on which events to send. Any events must not carry portfolio amounts or document contents (CLAUDE.md rule 10) |
| CI | GitHub Actions on every push (`.github/workflows/ci.yml`) | REAL; first run 2026-09-25 |

## To connect Sentry (owner, about five minutes)

1. Create a project at sentry.io (platform: Python → FastAPI).
2. Copy the DSN into Render's `SENTRY_DSN`. Not into git.
3. Check it: a deliberate error must appear in Sentry without request bodies, cookies or IP addresses.
   The API has no endpoint that raises on purpose; the check is to stop Neon briefly and watch `/ready`
   report `DATABASE_UNAVAILABLE` while the logged exception reaches Sentry.

Until that is done, "Sentry works" is not a claim this project can make.
