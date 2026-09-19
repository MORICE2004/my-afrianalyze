# Known gaps

Last updated: 2026-09-19. Anything fake, partial, blocked or untested is listed here (ROADMAP rule 4).
Full detail and evidence: `docs/MY_AFRIANALYZE_MASTER_AUDIT.md`.

## Decisions needed from the owner

| # | Decision | Why it matters | Options |
|---|---|---|---|
| 1 | **DSE price data** | Without licensed prices there is no share price, beta, cost of equity, valuation, target price, fair value range, model view, peer multiples or portfolio sizing | (a) DSE data licence (Data Vending Policy cl. 16.3.3, 23.1); (b) academic route (cl. 17.1, 17.7), if this project qualifies; (c) a commercial African market-data vendor. `pipelines/dse/import_prices.py` is ready for a licensed file |
| 2 | **Terms of use** for NMB investor relations, Bank of Tanzania, NBS and Damodaran data in a paid product; hosting copies of annual reports | Section 73. Not reviewed yet | Lawyer review (questions in `COMPLIANCE_NOTES.md`) |
| 3 | **Trade labels** (BUY/HOLD/SELL) and publishing target prices | May need a CMSA investment adviser licence (section 71) | `SHOW_TRADE_LABELS` stays off until you confirm |
| 4 | **Terminal growth 5%** in `config/valuation.json` | Material to valuation. It is a placeholder analyst assumption, not sourced | Use the rate from the team's CFA Research Challenge model, or approve a documented method |
| 5 | Scenario shocks and probabilities (25/50/25), method weights (RI 50%, P/B 30%, DDM 20%), model-view margins (±2%) | Analyst assumptions shown on the page | Approve or replace |
| 6 | **A named reviewer** for publishing research runs | Section 72. Nothing is shown in production until someone approves it | Name the person(s) |
| 7 | **Mock auth** (`apps/web/src/pages/api/auth/[...nextauth].ts` accepts any password) | Security. Auth changes were out of scope | Remove now, or replace in Milestone 6 |
| 8 | **Legacy code** with invented data (`connectors/`, `packages/asset_universe`, `agents/`, `apps/api/routers|tasks|core`, `models/`) | Risk of someone wiring fake data back in | Delete (git history keeps it) or keep quarantined |
| 9 | **Install Docker Desktop** | Needed to test the Postgres/Docker stack | Install, or accept SQLite for local work |
| 10 | Pause at each milestone (ROADMAP rule 5) or keep going (section 82) | The two documents disagree | I have been following section 82 (PRODUCT_CONTEXT wins) |

## Blocked

- DSE end-of-day prices, history, indices and volumes (zero-volume days). They are licensed (decision 1).
  - Affects: price, market cap, all beta methods, cost of equity, valuation, target price, fair value range,
    model view, peer P/E and P/B, markets page index and movers, and portfolio sizing.
  - These are shown as `BLOCKED` with the reason. A beta sensitivity grid (0.6 to 1.2) is shown and labelled
    as a sensitivity, not a forecast.
- Bottom-up beta also needs sourced prices for regional listed banks (NSE, USE). Kenya and Uganda are outside
  the v1 scope anyway.

## Data gaps

- **NMB FY2020 loans.** The 2021 report (p.324) does not add up for the 2020 column, so gross loans and the
  allowance are `CONFLICTING_SOURCE`. Cost of risk for FY2021 is therefore not shown. Needs a person to
  confirm (`config/source_issues.json`, `confirmed_by: null`).
- **Bank of Tanzania CBR.** Read from the April 2026 MPC statement at a fixed URL; flagged STALE. Newer
  statements are not discovered automatically.
- **Damodaran** default spread, CRP and mature ERP are dated 2026-01-05. They are STALE under the 200-day rule
  and cost 15 confidence points. A mid-year update may exist; re-run `pipelines.macro` after checking.
- The 7-year TZS bond was last auctioned in 2022. It is shown on the curve with that date.
- Dividend per share comes from report text, read by one method, so it is `PARTIALLY_VERIFIED`.
- FVPL investment securities are not reported in some years, so 2 cells show `INSUFFICIENT_DATA`.
- Shares outstanding are derived as profit ÷ EPS (weighted average). There is no dated share-count fact
  (section 79). This gives 500,000,000 shares for FY2025, which matches the shareholder table (Arise B.V.
  174,500,000 shares = 34.90%, 2025 report p.113).
- Large cash-flow restatements for FY2021 and FY2022 (restated comparatives are marked).
- CRDB is in the security master, but no reports have been ingested. The other DSE companies are not in the
  master.
- T-bills and unit trust funds (v1 scope) are not ingested.

## Not built yet

- Scheduled ingestion (Celery beat), retries, failure alerts. Pipelines are run by hand (CLAUDE.md).
- Admin console: review queue, conflict queue, overrides with a logged reason and source, freshness dashboard.
- Cash-flow tie check (cash movement) and full subtotal checks.
- Report history and the public track record (section 76).
- Accounts, roles, plans and gating. Payments wait for the owner.
- Grounded copilot. `/research-chat` is switched off because the old version showed invented figures.
- Methodology page, legal pages (drafts FOR LAWYER REVIEW), cookie consent.
- Swahili, beginner mode, landing page, screener, compare, watchlist, alerts, portfolio tracker.
- Observability, backups, staging, production deploy.

## Untested

- `docker compose up`, both Dockerfiles, PostgreSQL (Docker not installed; everything ran on SQLite).
- GitHub Actions CI (retargeted to `master` and Node 22; not yet run on GitHub).
- Terraform (`infra/`).

## Skipped tests (declared)

- `tests/test_adversarial.py`, `tests/test_adversarial_multimarket.py`: need `litellm` for the legacy agent
  layer, which is off in v1.
- `tests/test_connectors.py`: the connectors return invented sample data and are unused in v1.
- `tests/test_document_ingestion.py`, `tests/test_live_e2e.py`: skip themselves outside their environments
  (legacy).
- `tests/test_integration.py` was removed. It tested the old Celery research endpoints and a `/health` that
  always said "ok". It is replaced by `tests/v1/test_api.py`.

## Lint

- `npx eslint src` reports 3 errors, all in the mock auth file (`no-explicit-any`). They are left alone until
  decision 7.
