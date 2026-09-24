# AfriEdge Observability & Telemetry Framework

## 1. Sentry Error Tracking
- **Backend:** `sentry-sdk[fastapi]` initialized in `apps/api/core/telemetry.py` with automatic exception capture, trace sampling, and sensitive PII scrubbed from stack traces.
- **Frontend:** Sentry Next.js integration for capturing uncaught client-side rendering exceptions.

## 2. PostHog Product & Research Telemetry
- Captures business events without logging sensitive portfolio holdings or financial secrets:
  - `research_started`: `ticker`, `exchange`
  - `research_completed`: `ticker`, `run_duration_ms`, `confidence`
  - `portfolio_analyzed`: `asset_count`, `base_currency`
  - `valuation_viewed`: `symbol`, `model_type`

## 3. LLM Token & Cost Telemetry
- Every LLM inference call records token usage, latency, and estimated cost via `agents.telemetry.telemetry.log_llm_cost()`.
- Production rate limits prevent runaway agent cycles.
