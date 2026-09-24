# AfriEdge Codebase Audit Report
**Date:** 2026-09-24  
**Auditors:** Backend Auditor Agent, Frontend Auditor Agent  
**Status:** FIXES APPLIED — REMAINING ITEMS DOCUMENTED

---

## CRITICAL Issues — FIXED ✅

| # | File | Issue | Fix Applied |
|---|------|-------|-------------|
| 1 | `apps/web/src/app/layout.tsx` | `LayoutProps<"/">` type does not exist — **build blocker** | Replaced with `{ children: React.ReactNode }` |
| 2 | `Dockerfile.api` | CMD uses `api.main:app` but file is at `apps/api/main.py` | Changed to `apps.api.main:app` |
| 3 | `docker-compose.yml` (worker) | Celery command points to `core.tasks` which doesn't exist | Changed to `apps.api.core.celery_app` |
| 4 | `docker-compose.yml` (web) | Build context `./frontend` doesn't exist | Changed to `./apps/web` |
| 5 | `packages/core/config.py` | Settings missing `REDIS_URL`, `SECRET_KEY`, `LLM_API_KEY`, `SENTRY_DSN`, `POSTHOG_API_KEY`, `S3_BUCKET` | Added all missing fields |
| 6 | `packages/core/__init__.py` | Missing — breaks Python package imports | Created |
| 7 | `apps/api/core/__init__.py` | Missing — breaks Python package imports | Created |

## HIGH Issues — FIXED ✅

| # | File | Issue | Fix Applied |
|---|------|-------|-------------|
| 8 | `AppLayout.tsx` nav | `/macro` link → 404 (no such page exists) | Replaced with `/markets` |
| 9 | `AppLayout.tsx` nav | Missing links for `/portfolio` and `/research-chat` | Added both nav links |
| 10 | `tailwind.config.ts` | Missing Tremor content paths → Tremor classes purged in production | Added `./node_modules/@tremor/**/*.{js,ts,jsx,tsx}` |
| 11 | `alembic.ini` | Hardcoded DB connection string breaks non-local environments | Commented out; should load from env dynamically |
| 12 | `README.md` | Still says "My AfriAnalyze", outdated structure | Complete rewrite for AfriEdge rebrand |

## HIGH Issues — REMAINING ⚠️

| # | File | Issue | Action Required |
|---|------|-------|-----------------|
| 13 | `report/[symbol]/page.tsx` | Company name hardcoded to "Safaricom Plc" regardless of symbol | Needs dynamic data lookup or at minimum a symbol-to-name map |
| 14 | All components in `src/components/` | **17 orphaned components** never imported by any page: `AIValuations`, `AgentFindings`, `Dashboard`, `EvidenceViewer`, `FinancialMetrics`, `MultiMarketChart`, `PortfolioChat`, `RecommendationBadge`, `ReportTracker`, `ResearchTimeline`, `TechnicalChart`, `EvidenceLineage`, `FinancialStatements`, `TechnicalWorkspace`, `ValuationExplainer`, all 5 `ui/` components | Integrate into pages or remove dead code |
| 15 | `apps/api/*` | **Zero API tests** — FastAPI endpoints and Celery tasks entirely untested | Write test suite |
| 16 | `agents/orchestrator.py`, `auditor.py`, `research_director.py`, `synthesis.py` | Core orchestration agents have no unit tests | Write test suite |
| 17 | Tailwind v3 vs v4 | `package.json` has Tailwind v4 but config uses v3 patterns | Currently works via backward compat; may need migration |

## MEDIUM Issues — REMAINING ⚠️

| # | File | Issue |
|---|------|-------|
| 18 | `dashboard/page.tsx` | Hardcoded mock portfolio data |
| 19 | `research-chat/page.tsx` | Hardcoded NMB context; unused `ExternalLink` import |
| 20 | `fixed-income/page.tsx` | Unused `DollarSign` import |
| 21 | `health/page.tsx` | Hardcoded status/latency figures |
| 22 | `.github/workflows/ci.yml` | No service containers (Postgres/Redis), no linting, no coverage |
| 23 | `packages/database`, `packages/backtesting`, `packages/cache` | Zero test coverage |

## LOW Issues — REMAINING

| # | File | Issue |
|---|------|-------|
| 24 | `packages/backtesting/engine.py` | Dead code — never imported |
| 25 | `packages/cache/manager.py` | Dead code — never imported |
| 26 | `packages/security/pii_scrubber.py` | Dead code — never imported |
| 27 | `next-auth` | Installed with boilerplate but no actual auth flow wired |
| 28 | `clsx`, `tailwind-merge`, `class-variance-authority` | Only used by orphaned `ui/` components |

---

## Build Verification

```
✓ npm run build — PASSED (0 errors, 0 warnings)
✓ All 10 routes compiled successfully
✓ TypeScript type check passed
✓ Static pages generated (12/12)
```

## Commit

All fixes committed as `6ac6a3e` and pushed to `origin/master`.
