# Production certification

Date: 2026-09-25. Branch `m3-crdb-report`. Findings behind each row: `docs/AFRIEDGE_PRODUCTION_AUDIT.md`.
This replaces nothing on `master`, whose certification of the same date is contradicted by the evidence
(audit findings M-2 to M-5).

## Overall: `BLOCKED`

The code on this branch is in good order for what it does, and CI proves the parts that can be proved
without accounts. It is not a production system yet, for three reasons outside the repository:

1. No API host or database exists (the owner's accounts).
2. Both research reports are unapproved drafts, so production has nothing to show (the owner's review).
3. Showing DSE figures and hosting the banks' PDFs publicly are open licensing questions.

Statuses: `READY`, `READY_WITH_LIMITATIONS`, `BLOCKED` (needs something outside the repo),
`INCONCLUSIVE`, `REJECTED` (not built, or fails the bar), `INSUFFICIENT_DATA`.
Columns: **Real** = works on real data, not fixtures. **Deployed** = running on production infrastructure.

CI evidence below is run #36139810755 (all 5 jobs passed): unit tests 152 passed, 74 skipped (integration
tests that need the downloaded reports); Postgres job 17 passed. Local: 222 passed, 4 skipped.

| Capability | Implemented | Real | Tested | Deployed | Evidence | Status | Limitation |
|---|---|---|---|---|---|---|---|
| Frontend | yes | yes | tsc, eslint, build (local and CI); Playwright 28 checks at 1440/375 px (local, 2026-09-20) | preview only, protected | Vercel `web-1u7t6cvbb…` Ready | READY_WITH_LIMITATIONS | Playwright not in CI; no production deployment |
| API | yes | yes | 222 local tests; CI serves it in PRODUCTION mode on Postgres | no | CI job "Postgres from zero" | BLOCKED | No host yet (O-1) |
| PostgreSQL | yes | yes (CI Postgres 16) | migrations up/down/up; money round trip; image migrates on start | no | CI jobs "Postgres", "API image" | BLOCKED | Neon not created; full data load never run on Postgres |
| Redis | no | n/a | n/a | n/a | Not needed by v1 (`PRODUCTION_ARCHITECTURE.md`) | READY_WITH_LIMITATIONS | Deliberately absent |
| Background workers | no | n/a | n/a | n/a | Pipelines are commands; legacy Celery unused | READY_WITH_LIMITATIONS | No scheduled refresh: prices STALE (O-4) |
| Authentication | no | n/a | n/a | n/a | No per-user data exists; saved portfolios 401 | REJECTED | Must precede any per-user feature |
| Authorization | partial | yes | review gate 403 tested | no | `tests/v1/test_api.py` (APP_ENV=PRODUCTION monkeypatch) | READY_WITH_LIMITATIONS | Only the publish gate; no users |
| DSE | yes (prices, index) | yes | 13 importer tests; reconciliation | no | 2,473 days NMB/CRDB; 2,460 DSEI | READY_WITH_LIMITATIONS | STALE; `LICENSE_REVIEW_REQUIRED` for public display |
| NSE | no (v1) | reachable | probe | n/a | `DATA_SOURCE_MATRIX.md` | REJECTED | Outside v1 scope |
| USE | no (v1) | reachable | probe | n/a | as above | REJECTED | Outside v1 scope |
| BoT | yes (bond yields); CBR broken | yes | indirectly (`test_fixed_income_points_carry_sources`); no loader test | no | 2Y-25Y yields, dated per auction | READY_WITH_LIMITATIONS | CBR loader fails (O-5); no T-bills |
| CBK | no | reachable | probe | n/a | as above | REJECTED | Outside v1 scope |
| BoU | no | reachable | probe | n/a | as above | REJECTED | Outside v1 scope |
| NBS | yes (CPI) | yes | range check in the loader; no loader test | no | August 2026 CPI | READY_WITH_LIMITATIONS | The loader has no test of its own |
| KNBS | no | certificate fails | probe | n/a | as above | BLOCKED | Their TLS certificate |
| UBOS | no | certificate fails | probe | n/a | as above | BLOCKED | Their TLS certificate |
| IMF | no loader | API works | probe | n/a | Tanzania GDP growth parsed | REJECTED | No loader |
| World Bank | no loader | API works | probe | n/a | Tanzania GDP parsed | REJECTED | No loader |
| Company documents | yes | yes | SHA-256 manifests; integration tests | no | 10 annual reports (NMB, CRDB FY2021-25) | READY_WITH_LIMITATIONS | Two banks; PDF hosting rights open (O-7) |
| PDF extraction | yes | yes | two-reader agreement; every figure on its page | workstation | 295 + 297 facts | READY_WITH_LIMITATIONS | Runs offline, not on the server |
| Financial normalization | yes | yes | tie checks 41/42, 42/42 | no | `DATA_QUALITY.md` | READY | |
| Financial calculations | yes | yes | hand-checked tests | no | `tests/v1/test_bank_ratios.py` etc. | READY | Banks only |
| Valuation | yes | yes | hand-checked tests; sensitivity | no | Residual income, justified P/B, DDM; every input sourced | INCONCLUSIVE | Cost-of-equity treatment and CRDB growth unsettled; the view flips on the beta (O-3) |
| Technical analysis | engine only (legacy) | no | legacy tests | no | Not on the v1 report | REJECTED | Not wired in v1 |
| Market analysis | partial | yes | `test_markets_and_portfolios_do_not_invent_numbers` | no | DSEI level and movers from stored prices | READY_WITH_LIMITATIONS | Two securities priced; no breadth or sector view |
| Fixed income | partial | yes | fixed-income test | no | BoT bond curve, real yield, 2y-10y spread | READY_WITH_LIMITATIONS | No T-bills, no duration/convexity |
| Mutual funds | no | n/a | n/a | n/a | | REJECTED | Not built |
| Portfolios | no | n/a | proposal answers "not available" honestly | no | `/api/v1/portfolio/proposals` | REJECTED | Not built |
| Optimization | legacy only | no | n/a | n/a | | REJECTED | Not built in v1 |
| Stress testing | legacy only | no | n/a | n/a | | REJECTED | Not built in v1 |
| Evidence lineage | yes | yes | every figure has source, page, status | no | `test_every_shown_figure_has_status_source_and_units` | READY_WITH_LIMITATIONS | Source links need the PDFs hosted (O-7) |
| AI copilot | no | n/a | n/a | n/a | No LLM calls in v1 | REJECTED | Not built; needs sign-in and rate limits first |
| Sentry | backend wired | no | inert without DSN | no | `apps/api/main.py` | BLOCKED | No Sentry project; frontend not wired |
| PostHog | no | n/a | n/a | n/a | | REJECTED | Not built |
| CI/CD | yes | yes | 5 jobs green | GitHub Actions | run #36139810755 | READY_WITH_LIMITATIONS | Render deploy gate (`checksPass`) configured, not yet exercised |
| Security | yes | yes | tests + gitleaks + pip-audit + npm audit | n/a | `SECURITY_MODEL.md` | READY_WITH_LIMITATIONS | No CSP; no second-tool review yet |
| Backups | documented | no | not tested | n/a | `DATABASE_RUNBOOK.md` | REJECTED | Dump/restore never run; `data/` not backed up |
| Browser verification | yes | yes | Playwright local | preview only | 28 checks (2026-09-20) | INCONCLUSIVE | Not run against a deployed API; not rerun since today's changes except `/ready` and `/health` in the browser |

## The directive's end-to-end journey

Of the 24 steps in the directive's final user journey, the following work today (locally, against real
data): search a listed company; open it; real company information; real financial statements; open a line
item and see its source and page; ratios; valuation with assumptions and sensitivity; risks; the
recommendation with its uncertainty and the rule behind it; source lineage; data quality and research
status. Not built: sign-in, the copilot, technical analysis on the report, creating, analysing,
stress-testing and saving a portfolio. None of it runs in production yet.
