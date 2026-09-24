# AfriEdge Environment Variable Contract

This document specifies all environment variables used across the AfriEdge ecosystem, classified according to sensitivity, execution boundary, and production criticality.

| Variable Name | Classification | Boundary | Required in Production | Description |
|---|---|---|---|---|
| `APP_ENV` | PUBLIC | SERVER_ONLY | YES | Operating environment: `TEST`, `DEVELOPMENT`, or `PRODUCTION`. |
| `DATABASE_URL` | SECRET | SERVER_ONLY | YES | PostgreSQL connection URI (`postgresql://...`). Never exposed to browser. |
| `REDIS_URL` | SECRET | SERVER_ONLY | YES | Redis broker and cache URI (`redis://...`). |
| `SECRET_KEY` | SECRET | SERVER_ONLY | YES | Cryptographic signing key for sessions and tokens. Minimum 32 chars. |
| `LLM_API_KEY` | SECRET | SERVER_ONLY | YES | API key for LiteLLM inference gateway (Anthropic, Gemini, OpenAI). |
| `LLM_PROVIDER` | PUBLIC | SERVER_ONLY | NO | Default provider (default: `google` or `anthropic`). |
| `LLM_MODEL` | PUBLIC | SERVER_ONLY | NO | Target model name (default: `gemini-1.5-flash` or `claude-3-5-sonnet`). |
| `FIRECRAWL_API_KEY`| SECRET | SERVER_ONLY | OPTIONAL | Cloud Firecrawl API key when not routing to local docker endpoint. |
| `FIRECRAWL_API_URL`| PUBLIC | SERVER_ONLY | NO | Scraper gateway URL (default: `http://localhost:3002/v1`). |
| `SENTRY_DSN` | SECRET | SERVER_ONLY | YES | Sentry backend crash reporting DSN. |
| `POSTHOG_API_KEY` | SECRET | SERVER_ONLY | OPTIONAL | PostHog product telemetry key. |
| `POSTHOG_HOST` | PUBLIC | SERVER_ONLY | NO | PostHog host endpoint. |
| `S3_BUCKET` | PUBLIC | SERVER_ONLY | OPTIONAL | Bucket name for raw PDF storage and processed table artifacts. |
| `NEXT_PUBLIC_API_URL`| PUBLIC | BROWSER_SAFE | YES | Browser-accessible base URL for the FastAPI backend. |
| `API_URL_INTERNAL` | PUBLIC | SERVER_ONLY | OPTIONAL | Next.js server-to-FastAPI internal network URL (e.g. for SSR/API routes). |
| `NEXT_PUBLIC_POSTHOG_KEY`| PUBLIC | BROWSER_SAFE | OPTIONAL | Client-side event tracking key. |
| `NEXT_PUBLIC_POSTHOG_HOST`| PUBLIC | BROWSER_SAFE | OPTIONAL | Client-side analytics host. |
