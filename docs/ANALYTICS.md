# Product Analytics (Sentry + PostHog)

## Abstraction Layers
To prevent vendor lock-in and respect privacy mandates for financial data:
- **Backend API**: Uses `BackendTelemetry` (`apps/api/core/telemetry.py`)
- **Frontend App**: Uses wrapper methods (`apps/web/src/lib/telemetry.ts`)

## Environmental Controls
Both services are purely opt-in using `.env` values:
- `POSTHOG_ENABLED=true` / `NEXT_PUBLIC_POSTHOG_ENABLED=true`
- `SENTRY_ENABLED=true` / `NEXT_PUBLIC_SENTRY_ENABLED=true`

## Data Privacy (Scrubbing)
All contexts routed to Sentry/PostHog pass through a `scrubData()` sanitizer. The following patterns are scrubbed replacing values with `[SCRUBBED]`:
- `password`
- `api_key`
- `secret`
- `financial_data`
- `source_doc`
