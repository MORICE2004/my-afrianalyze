# Known gaps

Last updated: 2026-09-25. Anything fake, partial, blocked or untested is listed here (ROADMAP rule 4).
Full detail and evidence: `docs/MY_AFRIANALYZE_MASTER_AUDIT.md`.

## Owner decisions (2026-09-19)

| Question | Decision | What was done |
|---|---|---|
| DSE price data | Academic route, and (2026-09-19) use the prices the DSE publishes on its own site | NMB and CRDB daily prices are loaded, 2016-09-22 to 2026-09-18 (2,473 days each). The academic request in `DSE_ACADEMIC_DATA_REQUEST.md` is still unsent and would give a licensed series |
| Licence for target prices and BUY/HOLD/SELL | Owner: no licence needed | `SHOW_TRADE_LABELS` on by default; recorded in `COMPLIANCE_NOTES.md` as the owner's position, not legal advice |
| Terminal growth | 6%, the growth rate of the economy | `config/valuation.json`, marked as the owner's assumption |
| Beta basis (2026-09-20) | Use the average beta of comparable listed banks, not a regression on the bank's own price | `config/valuation.json` puts `industry` first in both selection orders. The figure is Damodaran's emerging-market "Banks (Regional)" levered beta, 0.604 across 104 firms, as of 2026-01-05, loaded by `pipelines.macro`. The five local regressions are still computed and shown as a cross-check |
| Reviewer | The owner, for now. Target flow: user requests a report, system prepares it, owner reviews, user sees it | Review command exists; the request queue is MISSING (below) |
| Legacy code | Delete only what is no longer useful | Deleted the Uganda connector and DSE price provider (invented values only), their two tests, and the mock sign-in (and the unused `next-auth` package). Kept the agents, the other connectors (they contain real fetch code) and the old engines |
| Push | Yes | Branch pushed to GitHub |

## Production readiness (2026-09-25)

Full list with evidence: `docs/AFRIEDGE_PRODUCTION_AUDIT.md`; status per capability:
`docs/PRODUCTION_CERTIFICATION.md` (overall `BLOCKED`).

- **Two products on one repository.** `master` holds the "AfriEdge" line with invented figures, a hardcoded
  sign-in and false certification claims (audit M-1 to M-5). Do not deploy or merge it as it stands. Owner
  decision: which line is the product.
- **Not deployed.** No Neon database, no Render API. Steps: `docs/DEPLOYMENT_RUNBOOK.md`.
- **Prices and index are STALE** (loaded 2026-09-20) and nothing refreshes them. Owner decision: a GitHub
  Actions schedule (needs the database URL as a GitHub secret) or a Render cron job (paid).
- **BoT Central Bank Rate loader is BROKEN** on the latest MPC statement.
- **Backups:** review history lives only in the database; `data/` is not backed up; dump/restore untested.
- **Observability:** backend Sentry wired but not connected; frontend Sentry and PostHog MISSING.
- **No Content-Security-Policy.** Playwright is not in CI.

## The one to look at first

**The model says both banks are worth more than the market says.** NMB's fair value is 14% above the
traded price; CRDB's is 79% above it, and the report now says so on the page and asks the reviewer to
check before approving. When a model disagrees this strongly with a traded price, the model is usually
the one that is wrong. Two things to weigh:

- The projection extrapolates the last three years. CRDB's net loans grew 25.9% a year over 2022-2025,
  and the base case carries that forward. A bank cannot compound loans at 26% indefinitely.
- The cost of equity is 12.94%, which is only about 2.2 points above what the Tanzanian government pays
  on a 10-year bond (10.69%). That is a thin premium for bank equity in a frontier market. It comes
  from the risk-free rate having the sovereign default spread removed (`subtract_default_spread` in
  `config/valuation.json`) before the equity risk premium is added. Worth confirming that treatment.

Note how much turns on the beta: on the monthly regression (0.786, Blume-adjusted to 0.857) NMB is
**Overvalued / SELL**; on the industry beta (0.604) it is **Undervalued / BUY**. Same accounts, same
price, opposite answer.

## Still open

| # | Question | Why it matters |
|---|---|---|
| 0 | Confirm the beta basis and the cost of equity treatment above, and the split in `config/corporate_actions.json` (`verified_by: null`) | They decide whether the reports say BUY or SELL |
| 1 | Terms of use of NMB, CRDB, BoT, NBS and Damodaran data in a paid product, and hosting copies of annual reports | Section 73. Questions in `COMPLIANCE_NOTES.md` |
| 2 | Scenario shocks and probabilities (25/50/25), method weights (RI 50%, P/B 30%, DDM 20%), model-view margins (±2%) | Analyst assumptions shown on the page; approve or replace |
| 3 | Install Docker Desktop | Needed to test the Postgres/Docker stack |
| 4 | Confirm the two source inconsistencies noted below, and CRDB's NPL basis | `config/source_issues.json` has `confirmed_by: null` |
| 5 | The DSE Data Vending Policy restricts reuse of DSE market data. The owner decided to use the published prices and accepted that risk | If the DSE objects, the price series and everything built on it must come out. Every price carries its web address, download time and file hash, so it can be removed cleanly |

## Blocked

- **Peer P/E and P/B** need prices for individual regional listed banks (NSE, USE), which are outside the v1
  scope. The `bottom_up` beta method (peer-by-peer, unlevered and relevered) stays BLOCKED for the same
  reason. The valuation does not depend on it: it uses the published industry average instead.
- **Market movers and commentary** on the markets page: they would need the whole DSE board, not two banks.
- **Portfolio sizing**: prices exist now, but the weighting rules, board lots and minimum trade sizes are not
  in the system, so a proposal says so and shows no weights or amounts.

## Data gaps

- **The DSE's own `shares_in_issue` field is wrong for NMB in recent rows**: 25 rows from 2026-06-02 onwards
  say 5,000,000,000 shares, ten times the real 500,000,000 (share capital TZS 20,000m ÷ TZS 40 par). The
  field is never used: the share count is derived from the audited profit ÷ EPS, which gives exactly
  500,000,000 for NMB and 2,611,999,857 for CRDB (the DSE says 2,611,838,584, 0.006% apart, EPS rounding).
- **A local beta is not usable for these banks.** From the same ten years of prices against the DSE All
  Share Index, NMB's beta is 0.017 daily (R² 0.008), 0.066 Dimson, 0.224 weekly and 0.786 monthly (R²
  0.266); CRDB's is 0.008 daily to 1.077 monthly. Beta rising steadily with the measurement interval is
  the signature of thin trading, which pulls a daily regression toward zero. Hence the owner's decision
  above. The regressions stay on the report so the reader can see the spread.
- **The index has 268 dates with no data** (the DSE answers "No data available" for market holidays) and
  13 levels that did not reconcile against the change published with them, all of them the first reading
  after a no-data date. Neither group is loaded: 2,460 days are.
- **Index levels are collected one date at a time** from `get/last/traded/indices?from=<date>`, which returns
  the last traded level and gives no date of its own. Each level is checked against the change the DSE
  publishes with it; levels that do not reconcile are not loaded. NMB did not trade on 35.6% of days and
  CRDB on 2.1%, which the beta rule weighs (section 74).
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
- Only NMB and CRDB have reports ingested. The other DSE companies are not in the security master.
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
