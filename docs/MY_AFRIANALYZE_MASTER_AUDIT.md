# My AfriAnalyze: Master Audit

Last updated: 2026-09-20 (production readiness: see `docs/AFRIEDGE_PRODUCTION_AUDIT.md` and `docs/PRODUCTION_CERTIFICATION.md`, 2026-09-25). Branch `m3-crdb-report`.
This file is the current truth about the repository (CLAUDE.md, PRODUCT_CONTEXT.md section 66).
Status words: `REAL`, `MOCKED`, `PARTIAL`, `BLOCKED`, `UNTESTED`, `BROKEN`, `MISSING`.
Proof for every claim below is in `docs/PROGRESS.md`. Open items are in `docs/KNOWN_GAPS.md`.

Nothing here is "production ready". The certification matrix at the end shows why.

## Current state

- **The earlier "complete" and "production ready" claims were false.** The baseline audit (17 September 2026,
  table at the end of this file) confirmed every issue in PRODUCT_CONTEXT.md section 70. The report page
  returned HTTP 500 for every ticker. Every number in the UI was hardcoded. `/health` always said "ok". The
  frontend source was never on GitHub (only a gitlink).
- **What works now (REAL, tested, checked in the browser).**
  - Reports for NMB Bank Plc (`/report/DSE:NMB`, 295 figures) and CRDB Bank Plc (`/report/DSE:CRDB`,
    297 figures), each from that bank's five annual reports (FY2020 to FY2025), built by one shared pipeline
    with a short profile per bank.
  - Each figure was read by independent readers (Camelot, Docling and the PDF text lines) and is stored only
    when at least two agree. Every figure is tie-checked and linked to its PDF page, and stored as an exact
    decimal.
  - Bank ratios, line-item analysis, rule-based notes, TZS cost-of-equity inputs, cited risks, PDF export, and
    a draft/review lifecycle.
  - A verified security master and search, a real health status, Bank of Tanzania bond yields, CBR and NBS
    inflation.
- **What is blocked.** DSE share prices are licensed data, so price, beta, cost of equity, valuation, target
  price, fair value range and the model view are shown as `BLOCKED` with the reason. There are no numbers in
  their place.
- **What is not built.** The rest of the DSE, T-bills, unit trusts, scheduled ingestion, the admin console,
  accounts, plans, Swahili and the copilot.
- **Tests.**
  - 179 Python tests pass, 3 are skipped (each with a stated reason), 0 fail. The v1 suite (`tests/v1`,
    110 tests) is hand-checked.
  - Playwright: 24 checks pass at 1440px and 375px, and 10 backend-stopped checks pass.

## Real

| Capability | Where | Evidence |
|---|---|---|
| Security master (5 securities, each verified on its exchange listing page) | `config/securities.json`, `pipelines/load_security_master.py`, `/api/v1/securities` | `tests/v1/test_api.py::test_search_ranks_exact_ticker_first` |
| Search with typeahead, keyboard support and a "no results" state | `apps/web/src/components/SecuritySearch.tsx` | Playwright "search finds NMB and opens its report" |
| Health endpoint: online, degraded (stale or blocked sources listed) or offline | `apps/api/main.py:46`, `components/layout/SystemStatus.tsx` | `test_health_reports_blocked_prices_honestly`; offline screenshot `docs/screenshots/desktop-1440-offline-report.png` |
| NMB and CRDB annual reports 2021 to 2025, downloaded from each bank's investor relations page with SHA-256 | `pipelines/banks/download_reports.py`, `data/raw/<bank>/manifest.json` | `test_raw_files_match_their_recorded_hash`, `test_documents_and_risks` |
| Independent readers (Camelot, Docling, PDF text lines). A value is stored only when at least two agree; an outvoted reader is recorded | `pipelines/banks/extract.py`, `resolve.py` | NMB: 295 facts, 0 disagreements. CRDB: 297 facts, 4 disagreements and 10 single-reader lines, none used |
| Every stored figure appears on the page it cites | `tests/v1/test_nmb_integration.py`, `test_crdb_integration.py` | 295 of 295 (NMB) and 297 of 297 (CRDB); 18 and 21 figures hand-checked |
| Tie checks: balance sheet (every year), income statement arithmetic, net loans | `pipelines/banks/resolve.py`, per-bank rules in `profiles.py` | NMB 41 of 42 (the failure is inside NMB's own 2021 report, see Data issues); CRDB 42 of 42 |
| Publication date of each report (board approval date, with the quote) | `pipelines/banks/load.py` | `test_documents_have_hash_publication_date_and_terms_note` |
| Exact money: `Decimal` in Python, `NUMERIC` on Postgres, text on SQLite; floats refused | `packages/database/types.py` | `tests/v1/test_exact_decimal.py` |
| Bank ratios: NIM, C/I, CoR, NPL, coverage, LDR, ROE, ROA, CAR, payout | `packages/analysis/bank_ratios.py` | `tests/v1/test_bank_ratios.py` (hand-worked values) |
| Line items: YoY, CAGR, common size, and rule-based notes that never contradict the numbers | `packages/analysis/line_items.py`, `notes.py` | `tests/v1/test_notes.py` |
| Status on every figure (VERIFIED, PARTIALLY_VERIFIED, CONFLICTING_SOURCE, INSUFFICIENT_DATA, BLOCKED, STALE) | `packages/report/builder.py`, `components/ui/StatusBadge.tsx` | `test_every_shown_figure_has_status_source_and_units`; Playwright report check |
| Figures that don't add up in the source are left out of every calculation | `config/source_issues.json`, `builder.py` | `test_figure_that_does_not_add_up_in_the_source_is_not_used` |
| TZS cost-of-equity inputs: BoT 10Y bond, Damodaran default spread, mature ERP, CRP (each dated and sourced) | `pipelines/macro.py`, `packages/analysis/cost_of_equity.py` | `tests/v1/test_cost_of_equity.py`; `test_stale_inputs_are_flagged` |
| Beta engine: raw daily, weekly, monthly, Dimson, Scholes-Williams, bottom-up, Blume, selection rule | `packages/analysis/beta.py` | `tests/v1/test_beta.py`. The engine is REAL; its output is BLOCKED (no prices) |
| Valuation engine: residual income, justified P/B, multi-stage DDM, bear/base/bull, probability-weighted target | `packages/analysis/bank_valuation.py` | `tests/v1/test_valuation.py`; `test_valuation_runs_on_real_facts_with_a_given_cost_of_equity`. The engine is REAL; its output is BLOCKED |
| Model view (Undervalued / Fairly valued / Overvalued), with BUY/HOLD/SELL behind `SHOW_TRADE_LABELS` (on since the owner's decision of 2026-09-19) | `packages/analysis/recommendation.py`, `packages/core/config.py` | `tests/v1/test_recommendation.py`; `test_no_view_and_no_trade_label_without_prices` |
| Confidence score (completeness, conflicts, beta quality, stale inputs) | `recommendation.py:confidence` | `test_confidence_score` |
| Cited risks: 9 verbatim quotes per bank, each found on its page, or the load stops | `pipelines/banks/profiles.py` | Report "Risks" tab; `test_documents_and_risks` |
| PDF export: draft warning, model view, statements, ratios, CoE, risks, sources, disclaimer | `packages/report/pdf.py` | `test_pdf_says_draft_and_model_view_not_buy_sell` |
| Review lifecycle: draft, in_review, published, superseded. Named reviewer; every action logged; production hides unpublished reports | `pipelines/review.py`, `apps/api/main.py:132` | `test_production_hides_unreviewed_reports`; run `RA-20260919-001` is `draft` |
| Tanzania fixed income: BoT auction yields by tenor, CBR, NBS CPI, real yield, 2Y to 10Y spread | `/api/v1/fixed-income/TZ`, `apps/web/src/app/fixed-income/page.tsx` | `test_fixed_income_points_carry_sources`; screenshots |
| No page shows a figure when the backend is down | all routes | `apps/web/e2e/offline.spec.ts` (10 pass) |
| Mobile menu, per-route titles, no sideways scrolling at 375px | `components/layout/AppLayout.tsx`, route metadata | Playwright smoke (24 pass) |

## Mocked

No data in the v1 code path (the API, `packages/analysis`, `packages/report`, `pipelines`, the web pages) is
mocked. The one exception in the web app is the NextAuth mock below, which no page uses. The other modules
listed still contain invented values. The v1 API does not import them. They stay in the repo until the owner
decides (see `KNOWN_GAPS.md`).

| Module | What is fake | Evidence |
|---|---|---|
| `connectors/dse`, `connectors/nse`, `connectors/cbk` | Hard-coded companies and prices in parts of each connector. Kept because they also contain real download code that Kenya and Uganda work may reuse | `connectors/dse/connector.py:60-142`, `connectors/nse/connector.py` |
| `packages/asset_universe/engine.py` | `_mock_dse_adapter`, `_mock_cmsa_adapter`, `_mock_bot_adapter`, `_mock_use_adapter`, `_mock_bou_adapter` | `engine.py:8-160` |
| `apps/api/tasks/research_tasks.py` | Celery task with `LLMClient(provider="dummy", api_key="dummy_key")` | `research_tasks.py:10-13`; not mounted |
| `apps/api/core/telemetry.py` | "Dummy" Sentry/PostHog init | baseline audit |

## Partial

| Capability | What is missing | Where |
|---|---|---|
| Source registry | Kept as `docs/SOURCE_REGISTRY.md` plus the `data_source_status` table. There is no registry table with terms fields and no admin view | `apps/api/main.py:46` |
| Freshness | Each input has an as-of date and a STALE flag. There is no alerting and no admin dashboard | `builder.py:258`, `/health` |
| Bank of Tanzania CBR | Reads a fixed April 2026 MPC statement URL. Newer statements are not discovered, so the value is flagged STALE | `pipelines/macro.py:36,126` |
| Validation | Balance sheet, income statement arithmetic and net-loan checks exist. The cash-flow check (cash movement) and full subtotal checks do not | `pipelines/nmb/resolve.py` |
| Review lifecycle | Command line only (`pipelines.review`). No admin console, no overrides with a logged reason, no automatic re-review on new results | `pipelines/review.py` |
| Portfolio wizard | Market first, then capital in TZS. It refuses to size positions without licensed prices and names the checks that will apply. No optimiser | `apps/web/src/app/portfolio/page.tsx`, `apps/api/main.py:239` |
| Markets page | Shows the securities in the master and why index levels and movers are missing | `apps/web/src/app/markets/page.tsx` |
| Plans and entitlements | Tables exist (`plans`, `entitlements`, `users.plan_id`). No logic (payments are out of scope until the owner says so) | `packages/database/models.py` |
| Shares outstanding | Derived as profit ÷ EPS (weighted average), not a dated share count (section 79) | `bank_valuation.py:31` |

## Blocked

| What | Why | What would unblock it |
|---|---|---|
| DSE end-of-day prices, history and indices | Licensed data: DSE Data Vending Policy clauses 16.3.3 and 23.1 restrict reuse. We do not scrape it | A DSE data licence, the academic route (clauses 17.1 and 17.7), or a commercial vendor. Importer ready: `pipelines/dse/import_prices.py` (needs a licence reference) |
| Share price, market cap, zero-volume days | as above | as above |
| Beta (all methods). Bottom-up also needs regional peer prices | as above | as above |
| Cost of equity, valuation, target price, fair value range, model view | Need a measured beta | as above. Meanwhile a beta sensitivity grid (0.6 to 1.2) is shown, labelled as a sensitivity |
| Peer P/E and P/B cross-check | Needs sourced peer prices | as above |

## Untested

| What | Why |
|---|---|
| `docker compose up` (`docker-compose.yml`, `Dockerfile.api`, `apps/web/Dockerfile`) | Docker is not installed on the dev machine. The files were corrected (web context `./apps/web`, API module `apps.api.main:app`, Node 22, standalone build, migrations on start) but never run |
| PostgreSQL | Migrations and all tests ran on SQLite only |
| GitHub Actions CI (`.github/workflows/ci.yml`) | Retargeted from `main` (does not exist) to `master` and Node 22. It has not run on GitHub yet |
| Terraform (`infra/`) | Never applied |
| Legacy `agents/` layer | `litellm` is not installed; its tests are skipped |

## Broken

Nothing in the v1 code path is known to be broken (all checks above pass). Legacy code that is broken if used:

| What | Problem | Evidence |
|---|---|---|
| `packages/market_data/beta.py` | Returns beta 1.0 when data is insufficient | baseline audit, lines 69-80 and 88-91 |
| `models/banks/valuation.py` | Returns fair value 0.0 instead of failing when CoE ≤ g | baseline audit, lines 7-9 and 61-65 |
| `apps/api/routers/portfolios.py` | Not mounted; `get_db` yields `None`; `DummyUser` | baseline audit |
| `packages/document_parser/pipeline.py` | Raises on the first extraction disagreement instead of recording it | baseline audit, lines 60-83 |

## Missing

- CRDB Bank report (v1 flagship), and a report or "limited coverage" page for every other DSE company.
- Bank of Tanzania T-bills; unit trust funds (v1 scope, section 77).
- Scheduled ingestion (Celery beat) with retries and failure alerts. Today the pipelines are commands.
- Admin console: review queue, conflicts, overrides with reasons, freshness dashboard.
- Report history and the public track record (section 76).
- Accounts, roles, plans and gating (payments wait for the owner, section 54).
- Grounded copilot (switched off: the old page showed invented NMB figures).
- Methodology page, legal pages (drafts marked FOR LAWYER REVIEW), cookie consent.
- Swahili, beginner mode, screener, compare, watchlist and alerts.
- Observability (Sentry, structured logs, uptime checks), backups, staging.

## Technical debt

- About 15 legacy packages, `agents/`, `connectors/`, `models/`, `apps/api/routers|tasks|core` and three
  `run_*_acceptance.py` scripts are not used by v1. Several contain invented data (see Mocked). Deleting them
  needs the owner's approval.
- 30 older docs in `docs/` (`PHASE*`, `PRODUCTION_READINESS_SCORECARD.md`, `MOCK_AUDIT.md`,
  `UI_UX_*`) contain claims that were found false. `docs/README.md` marks them as historical.
- SQLite stores exact decimals as text, so SQL-side numeric comparisons on those columns would be wrong. The
  code never does that. Postgres uses `NUMERIC`.
- The API sends decimals as JSON numbers, which the browser reads as floating point. This is for display
  only; every calculation happens server-side in `Decimal`.
- `pyproject.toml` dependencies disagree with `requirements.txt` (which now lists what v1 actually imports).
- Report building is synchronous (about 1 second per request). There is no caching.
- The Next.js dev indicator ("N" badge) shows in dev screenshots only.

## Security issues

1. **Mock credentials auth: fixed.** The file that accepted any email and password was deleted on
   2026-09-19 with the owner's approval, along with the unused `next-auth` package. There is no sign-in at
   all now; real accounts come with Milestone 6.
2. Serving source PDFs (`/api/v1/sources/{id}/file`) redistributes NMB's annual reports. The path is checked
   against the repo root, and licensed files return 403. Whether hosting (rather than linking) is allowed is
   a terms question (`COMPLIANCE_NOTES.md`).
3. There is no rate limiting and no security headers. CORS is locked to localhost ports (fine for dev; needs
   the real domain in production).
4. `docker-compose.yml` has a local-only default Postgres password (overridable with `POSTGRES_PASSWORD`).
   A pattern scan for API keys, tokens and passwords found no other secrets in the repository (2026-09-19).
5. No PII is collected anywhere yet. PostHog and Sentry stubs were removed from the frontend.

## Data issues

1. **NMB 2021 annual report, note 20(a), p.324, 2020 comparative does not add up.**
   - Gross loans 4,308,206 − allowance 204,809 = 4,103,397, but the stated net figure is 4,108,891.
   - The six loan categories sum to 4,313,598, not the stated gross.
   - Net loans agree with the balance sheet (p.226) and with the maturity analysis on the same page.
   - Treatment: FY2020 gross loans and allowance are `CONFLICTING_SOURCE` and are not used. Cost of risk for
     FY2021 is therefore not shown (`config/source_issues.json`; needs a person to confirm).
2. Ten restated comparatives: the later report is the source of record. The first-reported value is kept and
   shown with an asterisk.
   - Cash-flow restatements for 2021 and 2022 are large (e.g. FY2021 operating cash flow 453,290 first
     reported, 759,134 restated).
   - Cash-flow figures should be read with that in mind.
3. The dividend per share is read from report text by one method, so it is `PARTIALLY_VERIFIED`.
4. Damodaran inputs are dated 2026-01-05 and are STALE under the 200-day rule. The CBR (April 2026) is
   STALE. The 7-year bond was last auctioned in 2022.
5. Terms of use for NMB, BoT, NBS and Damodaran data in a paid product have not been reviewed (section 73).

## UX issues

- Header cards for blocked values repeat the licensing reason several times. It is honest but wordy.
- Wide statement tables scroll sideways inside their box on phones (the page itself does not).
- The homepage lists only the 5 verified securities. There is no landing page yet.
- There is no beginner mode, and no Swahili.
- The "Download PDF" button downloads a draft, which says so on the first page.

## Production blockers

1. DSE price data licence (or an approved alternative). Without it there is no price, beta, valuation or
   model view.
2. Legal review: whether publishing a model view, target price or BUY/HOLD/SELL requires a licence, and the
   terms of use for every source (`COMPLIANCE_NOTES.md`).
3. A named reviewer approves each research run before it is shown in production.
4. Remove or replace the mock auth provider. Real accounts are needed before any paid plan.
5. Verify Docker and PostgreSQL, CI green on GitHub, backups, monitoring.
6. CRDB and the rest of the DSE (or "limited coverage" pages), plus T-bills and unit trusts for the v1 scope.

## Priorities (section 67), mapped to the roadmap

| Priority | Items | Roadmap milestone |
|---|---|---|
| P0 production blockers | DSE price licence decision; source terms review; remove mock auth; Docker + Postgres verified; CI green; named reviewer | M0, M2, M6, M7, M9 |
| P1 core research reliability | CRDB report; scheduled ingestion with retries and alerts; CBR discovery; Damodaran refresh; cash-flow tie checks; dated share counts; admin review console and overrides | M2, M3, M4 |
| P2 user experience | Landing page, beginner mode, Swahili, screener, compare, watchlist, rebuilt wizard with prices | M5 |
| P3 expansion | All DSE companies; T-bills and unit trusts; then Kenya and Uganda after v1 certification | M4, v1 scope |
| P4 future intelligence | Grounded copilot with a numeric guard; public track record; Black-Litterman; backtesting | M8, section 76 |

## Certification matrix (section 64)

| Capability | Implementation | Real / Mocked | Tested | Live | Evidence | Known limitations |
|---|---|---|---|---|---|---|
| Security master and search | `securities` table, `/api/v1/securities`, `SecuritySearch.tsx` | REAL | Yes | Local only | `test_api.py`, Playwright | 5 securities; full DSE list missing |
| NMB statements | shared bank pipeline, 2 readers | REAL | Yes | Local only | `test_nmb_integration.py` | FY2020 loans CONFLICTING_SOURCE |
| CRDB statements | shared bank pipeline, 3 readers | REAL | Yes | Local only | `test_crdb_integration.py` | Loan impairment FY2022-23 unresolved; NPL basis to confirm |
| Bank ratios and notes | `bank_ratios.py`, `notes.py` | REAL | Yes | Local only | `test_bank_ratios.py`, `test_notes.py` | CoR FY2021 not shown |
| Beta | `beta.py` | REAL engine, BLOCKED output | Yes | No | `test_beta.py` | Needs licensed prices |
| Cost of equity | `cost_of_equity.py` | REAL inputs, BLOCKED output | Yes | No | `test_cost_of_equity.py` | Inputs partly STALE |
| Valuation and scenarios | `bank_valuation.py` | REAL engine, BLOCKED output | Yes | No | `test_valuation.py` | Terminal growth 5% is a placeholder assumption |
| Model view | `recommendation.py` | REAL rule, BLOCKED output | Yes | No | `test_recommendation.py` | Legal position on labels open |
| PDF export | `pdf.py` | REAL | Yes | Local only | `test_api.py` | Draft only |
| Review lifecycle | `pipelines/review.py` | PARTIAL (CLI) | Yes | No | `test_api.py` | No admin console |
| Fixed income (TZ) | `pipelines/macro.py` | REAL | Yes | Local only | `test_api.py`, screenshots | CBR stale; no T-bills |
| Markets | `/api/v1/markets/overview` | REAL (says what is missing) | Yes | Local only | `test_api.py` | Index data BLOCKED |
| Portfolio wizard | `/portfolio`, proposals API | PARTIAL | Yes | No | Playwright | No sizing without prices |
| Auth | none (mock deleted) | MISSING | No | No | this file | Real accounts are Milestone 6 |
| Copilot | switched off | MISSING | No | No | `/research-chat` | — |
| Docker stack | compose files | UNTESTED | No | No | — | Docker not installed |
| CI | `.github/workflows/ci.yml` | UNTESTED | No | No | — | Not yet run on GitHub |
| Payments | none | MISSING | No | No | — | Waits for the owner |

---

## Baseline (17 September 2026, before this branch)

Method: read every route, component, the API, the database layer, the connectors and the calculation
packages. Searched for `mock|sample|dummy|placeholder|TODO|fake|simulat`. Loaded every route of the running app
in a browser. Ran the pytest suite.

| Feature | What the summary claimed | What actually existed | Evidence |
|---|---|---|---|
| Deployment | "Staging ready via docker-compose up" | Compose built `./frontend` (missing); API module path wrong; Docker not installed | `docker-compose.yml:6`, `Dockerfile.api:24` |
| Frontend source control | Monorepo with `apps/web` | Gitlink only; no frontend files on GitHub | `git ls-tree 193c2ba apps/` → `160000 commit`. Fixed in `716dfae` |
| Database | "PostgreSQL 15, Migration v1.0" | Migration and models disagreed; Alembic saw no tables | `alembic/versions/1a2b3c4d5e6f_initial_migration.py:23` |
| Health endpoint | Monitoring | `GET /health` returned `{"status":"ok"}` unconditionally | old `apps/api/main.py:21-23` |
| Header status | Live system status | Static "SYS: ONLINE" while the backend was down | old `AppLayout.tsx:20-23` |
| Company report | Evidence-backed report | HTTP 500 for every ticker (`params` not awaited); hardcoded Safaricom figures and a fake citation | old `report/[symbol]/page.tsx:3-6,27,45,146-156,197` |
| Homepage search | Company search | No handler | old `page.tsx:17-22` |
| Ticker formats | Canonical master | `SFA.KE` vs `SCOM.NR`, `MTNN.NG` vs `MTNN.LG`, "MTN" under USE | old `page.tsx:31-34`, `dashboard/page.tsx:37-49` |
| Markets | Live data | Hardcoded index levels, `Math.random()` sparklines, unsourced commentary | old `markets/page.tsx:8-58,176-192` |
| Fixed income | Sovereign yield analytics | Hardcoded curve, CBR 6.00%, inflation 3.20% | old `fixed-income/page.tsx:8-34` |
| Dashboard | Saved portfolios | `mockData` with two invented portfolios | old `dashboard/page.tsx:26-55` |
| Portfolio wizard | Multi-currency optimisation | Capital in `$` before market; 3 fixed portfolios | old `portfolio/page.tsx:9-10` |
| Research copilot | "Deterministic RAG confirmed" | Scripted answer with invented NMB figures and a non-existent PDF | old `research-chat/page.tsx:37-41,123-153` |
| Analytics | "PostHog/Sentry scrubbing verified" | `console.log` stubs | old `lib/posthog.ts:1-8` |
| `/macro` | Macro module | 404 | browser |
| Mobile nav | Responsive | No menu below 768px | old `AppLayout.tsx:13` |
| Metadata | Branded | "Create Next App" | old `layout.tsx:16-19` |
| Test suite | "76 passing tests" | 71 pass, 2 fail, 3 files fail to import | pytest output |
