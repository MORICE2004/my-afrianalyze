# Phase 13 Production Readiness Audit

## 1. Mocks & Stubs Discovered
A codebase scan revealed the following remaining mocks:
- agents/llm_provider.py: Mock paths exist when APP_ENV=TEST.
- agents/orchestrator.py: Stub for financial data gate check (and False).
- agents/sector_agent.py: Hardcoded FX test rates.
- agents/synthesis.py: Placeholder for LLM output.
- apps/web/src/app/report/[symbol]/page.tsx & FinancialMetrics.tsx: UI mocks.
- apps/web/src/lib/posthog.ts: Mocked PostHog logger.
- connectors/dse/connector.py: Mocked schema parsing for testing.

## 2. Component Classifications
| Component | Status | Notes |
| :--- | :--- | :--- |
| DSE Connector | PARTIAL | Uses real source registry but parse_documents retains a mock. |
| NSE / USE Connectors | VERIFIED_LOCAL | Implemented, test-passing. |
| Document Ingestion | VERIFIED_LOCAL | Real pipeline exists. |
| LLM Providers | PARTIAL | Litellm is connected, but synthesis.py retains a placeholder string. |
| Technical Analysis | VERIFIED_LOCAL | Pandas indicators work. |
| Financial/Valuation Engine | VERIFIED_LOCAL | Deterministic engines pass 60+ tests. |
| Adversarial Auditor | VERIFIED_LOCAL | Cross-market currency logic implemented. |
| Research Orchestrator | PARTIAL | Retains a disabled gate check. |
| PostHog | MOCKED | Uses a console.log abstraction. |
| Sentry | MOCKED / UNKNOWN | Not visibly implemented. |
| Database (Postgres) | VERIFIED_LOCAL | Migrations work. |
| Redis / Celery | VERIFIED_LOCAL | Works via Docker-compose. |
| Next.js Frontend | PARTIAL | Contains hardcoded mock strings in report views. |

## 3. Production Firewall Requirement
To enforce PRODUCTION_DATA_VIOLATION, we must create a global exception ProductionDataViolation and ensure that if APP_ENV=PRODUCTION is set, any attempt to use these mock fallbacks throws this exception instead of silently returning mock data.
