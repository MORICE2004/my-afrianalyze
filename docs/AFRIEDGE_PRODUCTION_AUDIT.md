# AfriEdge Comprehensive Production Readiness Audit

**Audit Date:** 2026-09-24  
**Auditor:** Principal Engineer / AfriEdge Systems Architect  
**Evaluation Standard:** Zero-Trust Independent Verification (Directive §3 & §4)  
**Overall Status:** NOT PRODUCTION READY (Multiple P0 & P1 Blockers Identified)

---

## 1. Executive Summary

An uncompromising line-by-line inspection of the AfriEdge codebase was conducted. While earlier phases established sound mathematical foundations (financial ratios, fixed income mechanics, portfolio optimization algorithms), the platform cannot operate in production due to fundamental gaps in:
1. Python dependencies and container execution specs.
2. Database schema synchronization (Alembic migrations vs SQLAlchemy models).
3. API routing, dependency injection (`get_db` yielding `None`), and missing CORS.
4. Mock firewall exception triggered on genuine LLM usage in `PRODUCTION`.
5. Hardcoded mock responses in the Next.js API chat route.
6. Real African market connector fallback to static dictionaries and stubs.

---

## 2. Production Gate Classification

- **P0 (Production Blocker):** Must be resolved before any deployment certification.
- **P1 (Core Reliability & Real Data):** Must be resolved for valid research and financial correctness.
- **P2 (Major Operational / UX):** Deployment, observability, and communication integrity.
- **P3 / P4 (Operational Enhancements & Advanced Intelligence):** Future polish.

---

## 3. Detailed Audit Findings Matrix

### Finding 1: Dependency Manifest Missing Core Backend Packages
- **File:** `requirements.txt` vs `pyproject.toml`
- **Component:** Python Runtime Dependencies
- **Severity:** P0 (Production Blocker)
- **Current Behavior:** `requirements.txt` only lists 8 packages (`docling`, `pydantic`, `pytest`, `pandas`, `litellm`, `tenacity`, `celery`, `redis`). It completely omits `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic-settings`, `scipy`, `numpy`, `bs4`, `requests`, `httpx`, `psycopg2-binary`, `alembic`, `sentry-sdk`, `posthog`.
- **Expected Behavior:** `requirements.txt` must contain all packages required to build and run the backend Docker image and application services.
- **Production Impact:** `Dockerfile.api` fails to build or crashes immediately with `ModuleNotFoundError: No module named 'fastapi'` upon container startup.
- **Fix:** Synchronize and pin all required dependencies in `requirements.txt`.
- **Verification Method:** Clean `pip install -r requirements.txt` in a fresh virtualenv and container build test.
- **Status:** OPEN (P0)

---

### Finding 2: Database Schema & SQLAlchemy Model Desynchronization
- **File:** `packages/database/models.py`, `packages/database/base.py`, `alembic/versions/1a2b3c4d5e6f_initial_migration.py`
- **Component:** Relational Data Layer
- **Severity:** P0 (Production Blocker)
- **Current Behavior:** The Alembic migration defines tables for `companies`, `documents`, `market_prices`, `research_runs`, and `evidence`. However, `packages/database/models.py` only defines `User`, `SavedPortfolio`, and `PortfolioHolding`. The initial migration completely lacks `users`, `saved_portfolios`, and `portfolio_holdings`, while Python code lacks ORM models for `Company`, `Document`, `Evidence`, etc.
- **Expected Behavior:** `packages/database/models.py` must define all database entities, and migrations must cleanly bootstrap the entire unified schema from zero on PostgreSQL.
- **Production Impact:** Running `alembic upgrade head` leaves the database in an inconsistent state where portfolio APIs fail because tables don't exist, and research runs cannot persist metadata.
- **Fix:** Unify all models into `packages/database/models.py` inheriting from the single shared `Base` in `packages/database/base.py`, create a complete clean migration script, and provide a database bootstrap runner.
- **Verification Method:** Run migration against clean PostgreSQL test instance and verify all tables and constraints.
- **Status:** OPEN (P0)

---

### Finding 3: Mock Database Dependency and Unregistered Portfolio Router in FastAPI
- **File:** `apps/api/routers/portfolios.py` & `apps/api/main.py`
- **Component:** API Endpoints & State Persistence
- **Severity:** P0 (Production Blocker)
- **Current Behavior:** In `portfolios.py`, `get_db()` is a stub that does `yield None`, and `get_current_user()` returns a dummy user. Furthermore, `apps/api/main.py` never includes `portfolio_router`, meaning the portfolio endpoints are not even exposed!
- **Expected Behavior:** Real database session generator wired to SQLAlchemy sessionmaker, real authentication dependency, and `app.include_router(portfolios.router, prefix="/api/v1")` added to `main.py`.
- **Production Impact:** Portfolio creation, reading, and updates fail to persist to PostgreSQL, returning empty data or 404s.
- **Fix:** Implement production `get_db()` session lifecycle in `packages/database/session.py`, implement JWT/session user validation, and register the router with CORS middleware.
- **Verification Method:** Test portfolio CRUD against real database session via FastAPI TestClient.
- **Status:** OPEN (P0)

---

### Finding 4: Production LLM Call Crash in `_estimate_cost`
- **File:** `agents/llm_provider.py` (Lines 31-38, 139)
- **Component:** AI Orchestration Layer
- **Severity:** P0 (Production Blocker)
- **Current Behavior:** When `APP_ENV == "PRODUCTION"`, `LLMClient.generate()` executes `self._estimate_cost(estimated_tokens)`. In `_estimate_cost()`, line 36 explicitly executes:
  `if settings.APP_ENV == "PRODUCTION": raise ProductionDataViolation("Mock reached in production")`.
- **Expected Behavior:** Real token cost estimation using LiteLLM model pricing, without raising exceptions.
- **Production Impact:** 100% of live AI research and copilot requests crash in production.
- **Fix:** Replace dummy exception with deterministic token price calculation based on the configured model.
- **Verification Method:** Execute `generate()` in production mode with mocked API key and verify exception is not raised.
- **Status:** OPEN (P0)

---

### Finding 5: Next.js Chat API Route Returns Static Simulated String
- **File:** `apps/web/src/app/api/chat/route.ts`
- **Component:** Frontend AI Research Copilot Route
- **Severity:** P0 (Production Blocker)
- **Current Behavior:** Line 12 explicitly notes: `// For now, returning a mock response simulating the AI agent's reply`. Line 22 returns a static string rather than querying the backend `PortfolioChatAgent`.
- **Expected Behavior:** Route forwards queries with user session to FastAPI `/api/v1/chat`, which invokes `PortfolioChatAgent` bound to deterministic Evidence Graph context.
- **Production Impact:** Violates the core principle that the AI copilot must provide grounded financial research from actual portfolio data.
- **Fix:** Implement backend chat endpoint and wire frontend route via fetch to backend with error handling.
- **Verification Method:** Send message through frontend chat route and verify response is dynamically generated from agent.
- **Status:** OPEN (P0)

---

### Finding 6: Integration Test Suite Failures
- **File:** `tests/test_integration.py` & `tests/test_connectors.py`
- **Component:** Automated Verification Suite
- **Severity:** P0 (Production Blocker)
- **Current Behavior:** 
  1. `test_integration.py` fails with `AttributeError: <module 'apps.api.main'> does not have attribute 'AsyncResult'` because `main.py` uses `celery_app.AsyncResult` rather than importing `AsyncResult` directly.
  2. `test_connectors.py` fails because `USEConnector` lacks MTNU profile and returns `30.50` instead of `31.50`.
- **Expected Behavior:** Clean test suite execution with 0 errors and 0 unhandled exceptions.
- **Production Impact:** CI/CD pipeline fails, preventing deployment gating.
- **Fix:** Import `AsyncResult` in `main.py` (or adjust mock target), add MTNU and correct pricing in `USEConnector`.
- **Verification Method:** `pytest tests/test_integration.py tests/test_connectors.py` passes cleanly.
- **Status:** OPEN (P0)

---

### Finding 7: Health Check Lacks Dependency Awareness & Readiness Probe Missing
- **File:** `apps/api/main.py`
- **Component:** Observability & Deployment Probes
- **Severity:** P1 (Core Reliability)
- **Current Behavior:** `@app.get("/health")` returns `{"status": "ok"}` blindly without checking PostgreSQL or Redis connectivity. No `/ready` endpoint exists.
- **Expected Behavior:** `/health` returns process liveness; `/ready` tests database query (`SELECT 1`) and Redis ping (`PING`), returning `APP_HEALTHY`, `DATABASE_UNAVAILABLE`, `REDIS_UNAVAILABLE`, or `DEGRADED`.
- **Production Impact:** Cloud Run or Kubernetes routes traffic to container instances before database or queue connections are established.
- **Fix:** Implement production `/health` and `/ready` probes with dependency checks and timeout protection.
- **Verification Method:** Call endpoints with DB/Redis online vs offline and verify appropriate HTTP status codes (200 vs 503).
- **Status:** OPEN (P1)

---

### Finding 8: Cross-Origin Resource Sharing (CORS) Missing in FastAPI
- **File:** `apps/api/main.py`
- **Component:** API Gateway Security
- **Severity:** P1 (Core Reliability)
- **Current Behavior:** FastAPI app has no `CORSMiddleware` installed.
- **Expected Behavior:** `CORSMiddleware` configured with allowed origins (Vercel production URL, preview URLs, local dev).
- **Production Impact:** Any browser-based client request from the deployed Vercel frontend is blocked by the browser's CORS policy.
- **Fix:** Add `CORSMiddleware` with configurable allowed origins.
- **Verification Method:** Test OPTIONS preflight requests using `httpx`.
- **Status:** OPEN (P1)

---

### Finding 9: African Exchange Connectors Rely on Static Fallbacks & Stubs
- **File:** `connectors/nse/connector.py`, `connectors/use/connector.py`, `connectors/cbk/connector.py`, `connectors/bou/connector.py`
- **Component:** Market Data Ingestion
- **Severity:** P1 (Real Data Integrity)
- **Current Behavior:** Several connectors return static dictionary values when network requests fail or URLs are unreachable. `cbk/connector.py` has commented-out scraping code and hardcoded yields (`10.5`, `11.2`, `12.1`). `bou/connector.py` returns dummy bond ISINs.
- **Expected Behavior:** Connectors must attempt real live retrieval, and if unavailable or blocked, return explicit status (`INSUFFICIENT_DATA` or `BLOCKED`), never silent dummy data.
- **Production Impact:** Users see synthetic rates masquerading as verified live central bank statistics.
- **Fix:** Strip out silent dummy data fallbacks; return structured `ConnectorResult` with explicit `DataQualityStatus`.
- **Verification Method:** Verify connector output schema and error state handling.
- **Status:** OPEN (P1)

---

### Finding 10: Missing Rate Limiting and Security Headers
- **File:** `apps/api/main.py`
- **Component:** API Security
- **Severity:** P2 (Operational Security)
- **Current Behavior:** No rate limiting on expensive research tasks or AI endpoints; no standard security headers (Content-Security-Policy, HSTS, X-Frame-Options).
- **Expected Behavior:** SlowAPI / Redis rate limiting on `/api/v1/research/start` and `/api/v1/chat`, and security header middleware.
- **Production Impact:** Vulnerable to denial-of-service and uncontrolled LLM API billing spikes.
- **Fix:** Implement rate limiting middleware and security headers.
- **Verification Method:** Test burst requests to verify 429 response.
- **Status:** OPEN (P2)
