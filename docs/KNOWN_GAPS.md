# Known gaps

Last updated: 2026-09-19. Anything fake, partial, blocked or untested is listed here (ROADMAP rule 4).
Full detail and evidence: `docs/MY_AFRIANALYZE_MASTER_AUDIT.md`.

## Owner decisions (2026-09-19)

| Question | Decision | What was done |
|---|---|---|
| DSE price data | Academic route | Draft request in `DSE_ACADEMIC_DATA_REQUEST.md`. **The owner sends it.** Prices stay BLOCKED until a file arrives |
| Licence for target prices and BUY/HOLD/SELL | Owner: no licence needed | `SHOW_TRADE_LABELS` on by default; recorded in `COMPLIANCE_NOTES.md` as the owner's position, not legal advice |
| Terminal growth | 6%, the growth rate of the economy | `config/valuation.json`, marked as the owner's assumption |
| Reviewer | The owner, for now. Target flow: user requests a report, system prepares it, owner reviews, user sees it | Review command exists; the request queue is MISSING (below) |
| Legacy code | Delete only what is no longer useful | Deleted the Uganda connector and DSE price provider (invented values only), their two tests, and the mock sign-in (and the unused `next-auth` package). Kept the agents, the other connectors (they contain real fetch code) and the old engines |
| Push | Yes | Branch pushed to GitHub |

## Still open

| # | Question | Why it matters |
|---|---|---|
| 1 | Terms of use of NMB, CRDB, BoT, NBS and Damodaran data in a paid product, and hosting copies of annual reports | Section 73. Questions in `COMPLIANCE_NOTES.md` |
| 2 | Scenario shocks and probabilities (25/50/25), method weights (RI 50%, P/B 30%, DDM 20%), model-view margins (±2%) | Analyst assumptions shown on the page; approve or replace |
| 3 | Install Docker Desktop | Needed to test the Postgres/Docker stack |
| 4 | Confirm the two source inconsistencies noted below, and CRDB's NPL basis | `config/source_issues.json` has `confirmed_by: null` |
| 5 | Allow downloading from dse.co.tz in Claude Code's settings (see `HANDOFF.md`) | Claude Code's permission check blocked the price download |

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
- **CRDB loan impairment FY2022 and FY2023**: the credit loss note is laid out differently in those reports
  and the readers disagree, so cost of risk and dividend payout are not shown for those years.
- **CRDB EPS and interest detail for FY2020-2021**: only one reader found them, so they are not used.
- **CRDB NPL ratio**: CRDB states 2.9% for 2025 (p20); stage 3 over gross loans on the group basis gives 2.7%.
  Confirm which basis to show before publishing.
- CRDB owners' equity for FY2020-2021 is derived from total equity because the report states the subsidiaries
  are 100% owned. The quote is stored with the figure.
- T-bills and unit trust funds (v1 scope) are not ingested.

## Not built yet

- Scheduled ingestion (Celery beat), retries, failure alerts. Pipelines are run by hand (CLAUDE.md).
- Admin console: review queue, conflict queue, overrides with a logged reason and source, freshness dashboard.
- Cash-flow tie check (cash movement) and full subtotal checks.
- Report history and the public track record (section 76).
- Report request queue: a user asks for a report, the system prepares it, the owner reviews it, the user
  sees it. Needs accounts (a request is tied to a person).
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
- `tests/test_document_ingestion.py`: skips itself in the test environment (legacy).
- `tests/test_connectors.py` and `tests/test_live_e2e.py` were deleted with the invented-data connectors they
  tested.
- `tests/test_integration.py` was removed. It tested the old Celery research endpoints and a `/health` that
  always said "ok". It is replaced by `tests/v1/test_api.py`.

## Lint

- `npx eslint src` reports no problems (the mock auth file was deleted).
