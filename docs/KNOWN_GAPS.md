# Known gaps

Last updated: 2026-10-07. Anything fake, partial, blocked or untested is listed here (ROADMAP rule 4).
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

## Production readiness (2026-10-07)

Status per capability: `docs/PRODUCTION_CERTIFICATION.md` (overall `BLOCKED`). Owner actions, in order:

1. **Neon and Render accounts** (`DEPLOYMENT_RUNBOOK.md` steps 1-2), with `INTERNAL_PROXY_SECRET` set to the
   same value on Render and Vercel.
2. **`DSE_PUBLIC_DISPLAY`**: the DSE's policy forbids public redistribution without a licence (`RESTRICTED`).
   Production will not start until you set it; `false` is the safe value.
3. **Cost-of-equity treatment**, then review and approve the runs RA-20261007-001 (NMB) and -002 (CRDB).
4. **Update `master`** to the canonical branch (needed for the scheduled refresh) and add
   `PRODUCTION_DATABASE_URL` to the GitHub `production` environment.
5. Optional: Sentry and PostHog projects; an Anthropic key for the copilot (paid); a domain.
6. Read UTT AMIS's terms (unit trust prices) and decide; the IMF needs written permission.

Still missing whatever the accounts: password reset and email verification (needs an email service); tested
backups (`data/` is not backed up, dump/restore never run); Playwright in CI; browser-side error reporting.

## The one to look at first

**The answer for NMB depends on a method choice.** With the configured cost of equity (12.94%) NMB's fair
value is TZS 2,354 against a price of 2,040; with the two other standard treatments (15.25% and 16.77%) it is
1,706 and 1,433, below the price. Since 2026-10-07 the report computes all three and, because the view flips,
shows NMB as **Inconclusive** with no trade label. CRDB is Undervalued under all three (5,026 / 3,624 / 3,035 against a price of 2,910; the base case is 73%
above the market). When a model disagrees this strongly with a traded price, the model is usually the one
that is wrong. Two things to weigh:

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

- **News publishers (owner's decision).** Only official sources are fetched: Central Bank of Kenya (RSS), Bank of
  Tanzania (press releases), World Bank (public API). Reuters, Bloomberg, The EastAfrican, Business Daily Africa
  and The Citizen are `LICENSE_REVIEW_REQUIRED`; IMF and AfDB answered 403 and are not retried; Bank of Uganda,
  DSE, NSE and USE announcements have no loader. `config/news_sources.json`.
- **News relevance is keyword rules**, so it can miss a story worded unusually (shown as "Impact not assessed")
  and can tag a story by a word in its headline. It never predicts direction.
- **No legal privacy policy, terms or contact page.** `/privacy` describes what the site stores, from the code.
  Legal text needs the owner.


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
- **Market commentary** and a sector view: movers and breadth now cover 17 shares, but 26 of the 28 companies
  are "Unclassified" until their sectors are checked by hand.
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
- **Bank of Tanzania CBR.** Fixed 2026-10-02: the newest MPC statement is found on the notices page each run
  (6.25%, raised 2 July 2026).
- **Damodaran** default spread, CRP and mature ERP are dated 2026-01-05. They are STALE under the 200-day rule
  and cost 15 confidence points. A mid-year update may exist; re-run `pipelines.macro` after checking.
- The 7-year TZS bond was last auctioned in 2022. It is shown on the curve with that date.
- Dividend per share comes from report text, read by one method, so it is `PARTIALLY_VERIFIED`.
- FVPL investment securities are not reported in some years, so 2 cells show `INSUFFICIENT_DATA`.
- Shares outstanding are derived as profit ÷ EPS (weighted average). There is no dated share-count fact
  (section 79). This gives 500,000,000 shares for FY2025, which matches the shareholder table (Arise B.V.
  174,500,000 shares = 34.90%, 2025 report p.113).
- Large cash-flow restatements for FY2021 and FY2022 (restated comparatives are marked).
- Only NMB and CRDB have reports ingested. The other 26 DSE companies are in the security master (discovered
  2026-10-07), 15 of them with prices; their statements are not loaded.
- **CRDB loan impairment FY2022 and FY2023**: the credit loss note is laid out differently in those reports
  and the readers disagree, so cost of risk and dividend payout are not shown for those years.
- **CRDB EPS and interest detail for FY2020-2021**: only one reader found them, so they are not used.
- **CRDB NPL ratio**: CRDB states 2.9% for 2025 (p20); stage 3 over gross loans on the group basis gives 2.7%.
  Confirm which basis to show before publishing.
- CRDB owners' equity for FY2020-2021 is derived from total equity because the report states the subsidiaries
  are 100% owned. The quote is stored with the figure.
- T-bills are not ingested. Unit trust funds are listed (`config/funds.json`) but their prices are
  `BLOCKED` until UTT AMIS's terms are read.

## Not built yet

- Scheduled ingestion runs as a GitHub Actions workflow (written and tested locally; inert until the
  production database exists). Bank reports are still loaded by hand, by design.
- Admin console: review queue, conflict queue, overrides with a logged reason and source, freshness dashboard.
- Cash-flow tie check (cash movement) and full subtotal checks.
- Report history and the public track record (section 76).
- Report request queue: a user asks for a report, the system prepares it, the owner reviews it, the user
  sees it. Needs accounts (a request is tied to a person).
- Roles, plans and gating (accounts exist since 2026-10-02). Payments wait for the owner.
- Grounded copilot: built (2026-10-07), never run against the real model (no API key).
- Methodology page, legal pages (drafts FOR LAWYER REVIEW), cookie consent.
- Swahili, beginner mode, screener, compare, watchlist, alerts.
- Tested backups, staging, production deploy.

## Untested

- `docker compose up` locally (Docker not installed). The API image and Postgres are tested in CI on every push.
- The scheduled refresh workflow against a real production database.
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
