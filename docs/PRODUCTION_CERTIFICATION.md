# Production certification

Date: 2026-10-07. Branch `m3-crdb-report` (canonical). Earlier findings: `docs/AFRIEDGE_PRODUCTION_AUDIT.md`.
`master` still holds the quarantined legacy line; nothing here certifies it.

## Overall: `BLOCKED`

The code on this branch does what it says, on real data, and the tests prove what can be proved without
accounts. It is **not a running production system**, and no amount of local work changes that, because the
remaining blockers are outside the repository:

1. **No API host and no database exist** (Render and Neon accounts are the owner's to create).
2. **Nothing is published.** Both research runs are unapproved drafts (owner's review, after the
   cost-of-equity decision).
3. **DSE data may not be shown publicly without a licence** (Data Vending Policy v1.2, cl. 23.1). Production
   will run with `DSE_PUBLIC_DISPLAY=false` until one is held, which blanks every price-based figure.

Statuses: `READY`, `READY_WITH_LIMITATIONS`, `BLOCKED` (needs something outside the repo), `INCONCLUSIVE`,
`INSUFFICIENT_DATA`, `REJECTED` (not built, or fails the bar). **Real** = runs on real data, not fixtures.
**Deployed** = running on production infrastructure (nothing is).

Evidence, 2026-10-07: Python **358 passed, 4 skipped** (the 4 need `litellm` for the legacy agent layer, or
skip themselves); Playwright **46/46** at 1440 and 375 px against the real local API and data; CI run
37604066948 on `450bb0f`, all 5 jobs passed (unit tests, Postgres from zero, API Docker image, gitleaks,
pip-audit and npm audit); local `pip-audit` and `npm audit --omit=dev` clean.

| Capability | Implemented | Real | Tested | Deployed | Evidence | Status | Limitation |
|---|---|---|---|---|---|---|---|
| Frontend (Next.js 16) | yes | yes | tsc, eslint, build in CI; Playwright 46/46; every page at 320/375/390/430 px without sideways scroll | protected preview only | `web-gvgi9zlgt-morice2004s-projects.vercel.app`, commit `b099091`, fra1, Ready | READY_WITH_LIMITATIONS | Playwright not in CI; no production deploy until an API exists; preview has no API, so data pages say the data service is not reachable |
| API (FastAPI) | yes | yes | Python suite; CI serves the image in PRODUCTION mode on Postgres | no | CI "API Docker image" | BLOCKED | No Render service (owner) |
| PostgreSQL | yes | CI Postgres 16 | 3 migrations up/down/up; exact money round trip | no | CI "Postgres from zero" | BLOCKED | Neon not created; full load never run on Postgres |
| Background workers / Redis | none, by decision | n/a | n/a | n/a | Every request finishes within a page load (`PRODUCTION_ARCHITECTURE.md`, re-checked 2026-10-07) | READY_WITH_LIMITATIONS | Rate limits in memory per process (one instance only) |
| Scheduled refresh | yes | yes (run locally) | merge tests 7 (history never shrinks, revisions held, outage recorded) | no | `refresh-data.yml`; 2026-10-07 local refresh: 17 shares + DSEI to 2026-10-06 | BLOCKED | Needs `PRODUCTION_DATABASE_URL` and the code on `master` (schedules run only from the default branch) |
| Authentication | yes | yes | API tests + browser journey; per-email lockout | no | Argon2id; hashed 256-bit session tokens; httpOnly cookie; per-visitor and per-email limits | READY_WITH_LIMITATIONS | No password reset, email verification or account deletion (needs an email service) |
| Authorization | yes | yes | Two-account tests at API and in the browser | no | Every portfolio query filters on the session user; others' ids 404 | READY | |
| DSE equities | yes | yes | importer, merge and discovery tests (9) | no | 28 companies listed; 17 shares priced to 2026-10-06; DSEI 2,472 days | READY_WITH_LIMITATIONS | `RESTRICTED`: public display needs a DSE licence; 8 shares refused (unexplained jumps), 3 not served |
| BoT (bonds, CBR) | yes | yes | `test_bot_cbr.py`; bond pricing checked against BoT's published prices | no | 2Y-25Y yields (15Y auction 2026-09-30); CBR 6.25% | READY_WITH_LIMITATIONS | No T-bills; 7Y last auctioned 2022 |
| NBS CPI | yes | yes | loader range check | no | 4.3% (August 2026) | READY_WITH_LIMITATIONS | No test of its own |
| World Bank | yes | yes | `test_world_bank.py` (3) | no | 188 observations, TZ/KE/UG, to 2025 | READY | Annual data only |
| IMF | no | n/a | n/a | n/a | Terms require permission for commercial redistribution | BLOCKED | `LICENSE_REQUIRED` (owner) |
| NSE, USE, CBK, BoU, KNBS, UBOS | no | n/a | probe only | n/a | Kenya and Uganda outside v1; the schema already carries exchange and currency | REJECTED | Scope decision; KNBS and UBOS certificates fail |
| Company documents | yes | yes | SHA-256 manifests; integration tests | no | NMB and CRDB annual reports FY2021-25 | READY_WITH_LIMITATIONS | Two banks; hosting the PDFs publicly is an open rights question |
| PDF extraction | yes | yes | two-reader agreement; every figure on its page | workstation | 295 + 297 facts | READY_WITH_LIMITATIONS | Runs offline, by design |
| Financial statement analysis | yes | yes | tie checks NMB 41/42 (fails inside NMB's own report), CRDB 41/41 + 1 not runnable | no | `DATA_QUALITY.md` | READY | Banks only |
| Bank metrics | yes | yes | hand-checked tests | no | NIM, cost/income, cost of risk, NPL, ROE, capital | READY | Banks only |
| Research run engine | yes | yes | `test_research_runs.py` (8) | no | 10 stages; COMPLETED/PARTIAL/FAILED/BLOCKED/INSUFFICIENT_DATA; frozen snapshot + SHA-256 served in production; NMB and CRDB runs `PARTIAL` | READY_WITH_LIMITATIONS | `PARTIAL` because of disclosed gaps (unchecked tie check, stale Damodaran inputs) |
| Valuation | yes | yes | hand-checked tests; sensitivity; three cost-of-equity treatments | no | NMB fair value 2,354 / 1,706 / 1,433 TZS by treatment vs price 2,040 → **Inconclusive**, no label; CRDB Undervalued under all three | INCONCLUSIVE | The treatment is the owner's decision; CRDB's 26% loan growth is extrapolated |
| Recommendation (BUY/HOLD/SELL) | yes | yes | `test_recommendation.py` | no | Shown only when the view survives every treatment (`require_robust_view`) | READY_WITH_LIMITATIONS | Labels on by owner decision; no published report yet |
| Technical analysis | yes | yes | `test_technical.py` (11) | no | SMA/EMA/RSI/MACD/Bollinger/OBV with a liquidity gate per window (section 74) | READY_WITH_LIMITATIONS | ATR/ADX/VWAP computed from the DSE's published high, low and turnover since 2026-10-08, only over windows where every day traded |
| Market analysis | yes | yes | API + browser tests | no | DSEI, breadth, gainers/losers over 17 shares (no trade is not a move) | READY_WITH_LIMITATIONS | DSE sector indices (BI, IA, CS) shown; most listed companies still "Unclassified" |
| Fixed income | yes | yes | `test_bonds.py` (11) | no | Yield curve, price, duration, convexity, rate shocks; BoT prices reproduced to 0.0003 (5-25Y) | READY_WITH_LIMITATIONS | No T-bills; 2Y/20Y differ by 0.02-0.03 (BoT averages) |
| Mutual funds | data model and page | no | API test | no | 6 UTT AMIS funds listed with sources, each `BLOCKED` | BLOCKED | Owner to read UTT AMIS terms before any price is loaded |
| Portfolios | yes | yes | API + browser | no | Decimal valuation at the latest close; unpriced → `INSUFFICIENT_DATA`; stale flagged | READY_WITH_LIMITATIONS | TZS only |
| Portfolio risk, optimisation, stress | yes | yes | `test_portfolio_risk.py` (10) | no | Weekly returns; volatility, drawdown, correlation; minimum variance only (no invented expected returns); historical and configured shocks | READY_WITH_LIMITATIONS | Thin trading (NMB had no trade on 35.6% of days) makes risk estimates noisy; no board-lot rules |
| AI copilot | yes | no provider key | `test_copilot.py` (22) with a fake provider | no | Grounded context; deterministic number check withholds `UNGROUNDED`; `AI_UNAVAILABLE` on any failure; sign-in + 20/day | INCONCLUSIVE | Never run against the real model (no `ANTHROPIC_API_KEY`; a paid service) |
| Evidence lineage | yes | yes | `test_every_shown_figure_has_status_source_and_units` | no | Every figure: source, page, status, retrieval | READY_WITH_LIMITATIONS | Source links need the PDFs hosted |
| Economic news | yes | yes | `test_news.py` (12), 2 browser tests | no | CBK RSS, BoT press releases, World Bank API; rule-based relevance with stated reason; headlines and links only; future-dated items rejected | READY_WITH_LIMITATIONS | Reuters, Bloomberg, The EastAfrican, Business Daily, The Citizen: LICENSE_REVIEW_REQUIRED (owner); IMF and AfDB refused requests (403); Bank of Uganda not built |
| Interface (2026-10-08 pass) | yes | yes | 74/74 Playwright (1440 + 375), 80 page views at 320-1440 px light/dark with no overflow, reduced-motion test | no (preview pending) | Search-first, sectioned pages without card walls, verification badge with source popover, Ctrl+K quick search, toasts, plain-language no-view state | READY_WITH_LIMITATIONS | No legal privacy policy or terms text (owner); `/privacy` is a factual description of what is stored |
| Data-quality UI | yes | yes | browser tests | no | `/health` (status, ages, licensing), per-figure status on reports | READY | |
| Sentry | API wired | no | scrubber tests; `pipelines.sentry_check` | no | release = deployed commit | BLOCKED | No Sentry project (owner); browser errors not reported |
| PostHog | API wired | no | `test_telemetry.py` (9) | no | Server-side, allowlisted events, salted ids, EU, no GeoIP | BLOCKED | No PostHog project (owner) |
| CI/CD | yes | yes | 5 CI jobs | GitHub Actions | run 37604066948 green | READY_WITH_LIMITATIONS | Render's `checksPass` gate configured, not yet exercised |
| Security | yes | yes | second pass 2026-10-07; gitleaks, pip-audit, npm audit | n/a | `SECURITY_MODEL.md` (2 rate-limit flaws found and fixed) | READY_WITH_LIMITATIONS | No independent reviewer yet; CSP allows inline scripts |
| Backups | documented | no | not run | n/a | `DATABASE_RUNBOOK.md` | REJECTED | Dump/restore never run; `data/` not backed up |
| Production smoke test | written | no | not run | no | `DEPLOYMENT_RUNBOOK.md` step 5 | BLOCKED | Needs a deployed API |

## The end-to-end journey (locally, real data)

Works: search a DSE company; open NMB or CRDB; real statements with every line's source page; ratios and bank
metrics; valuation with assumptions, sensitivity and the cost-of-equity alternatives; technical indicators
with their liquidity gates; risks; the recommendation with its uncertainty (NMB Inconclusive); the research
run's stages and snapshot; sign up and sign in; create, value, analyse and stress-test a portfolio; markets
breadth; bond analytics; the copilot's `AI_UNAVAILABLE` path. Not working: the copilot's answers (no key),
unit trust prices (blocked on terms), anything in production.

## 2026-10-08 interface and news pass

Verified: Python 409 passed, 4 skipped; Playwright 74/74; `tsc` and `eslint` clean; 80 page views at
320/375/390/430/768/1024/1280/1440 px (light, plus dark at 375 and 1440) with no horizontal scroll. Not
verified: the deployed preview against a production API (no API host); browser analytics (none exist, so no
consent banner is shown; `/privacy` says so).
