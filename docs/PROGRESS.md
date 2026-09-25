# Progress

Proof for each step (ROADMAP rule 3). Newest first. Plain-language summary at the top of each entry.

---

## 2026-09-25: production readiness audit, and the fixes that did not need an account

**In plain words:** the owner supplied a production-readiness directive. I audited from scratch, fixed
everything in the repository that stood between this code and a safe deployment, and got CI running for
the first time. The site is still not public: that needs a database and API host in the owner's name, the
two reports approved, and the licensing questions answered. Findings: `docs/AFRIEDGE_PRODUCTION_AUDIT.md`.
Status per capability: `docs/PRODUCTION_CERTIFICATION.md`.

**Found on `master` (not changed).** A second line of work, rebranded "AfriEdge", was pushed to `master`
from another working copy (`~/.gemini/antigravity/scratch/my-afrianalyze`) between 2026-09-17 and 09-24. It
certifies itself `READY_WITH_LIMITATIONS`. Checked: its markets and fixed-income pages have invented
figures in the source, its health page is fixed text, its Uganda connector returns made-up prices, its
portfolio API treats every caller as user 1 with no sign-in, and it claims CI passes remotely when GitHub
had recorded no workflow runs at all. Three production deploys to Vercel from it on 2026-09-24 failed, so
nothing is live. Which line is the product is the owner's decision.

**Fixed on this branch** (16 items, table F-1 to F-16 in the audit). The ones that mattered most:
- CI only ran on `master`, so it had never run. Now five jobs on every push. First run: 3 of 5 passed and
  the 2 failures were real (the web type check had been passing locally on files Next generated earlier;
  a test read CI's database URL). Second run: 5 of 5.
- `/health` said 200 when the database was down, and echoed the database error. New `/ready` answers 503.
- The API Docker image did `COPY . /app/`, which would have shipped `.env` and the local database, and
  installed PyTorch to serve web pages. Now 149 MB, named folders only, non-root. Proved by installing
  `requirements-api.txt` into an empty virtualenv and serving every endpoint from it.
- A production web build without `NEXT_PUBLIC_API_URL` silently pointed every visitor at their own
  machine. It now fails the build.
- PRODUCTION refuses SQLite and localhost CORS; `postgres://` URLs work; `psycopg2` was never actually
  installed on this machine, so loading a Postgres database would have failed on the first command.
- Money on Postgres had never been tested on Postgres. CI now does it: exact to 28 digits.

**Sources probed** (`python -m pipelines.probe_sources`, 16 sources): 5 answer real data requests (DSE,
World Bank, IMF, ECB, UN Comtrade), 9 are reachable with no loader (all of Kenya and Uganda among them),
2 fail certificate verification (KNBS, UBOS) and were not bypassed. `docs/DATA_SOURCE_MATRIX.md`.

**Providers checked** before choosing: Render's free Postgres is deleted after 30 days (+14), so the
database goes on Neon (free tier does not expire; 0.5 GB against our 1.3 MB). API on Render with
`render.yaml`, deploying only after CI passes.

**Tests:** local 222 passed, 4 skipped. CI run #36139810755: all 5 jobs passed (unit 152 passed, 74
skipped without the downloaded reports; Postgres 17 passed). `tsc`, `eslint`, `next build` clean.
pip-audit and npm audit: no known vulnerabilities. Secret scan of all 27 commits: clean.

**Not tested:** anything on real production infrastructure (none exists); Sentry end to end (no project);
backup and restore; Playwright against the changed code (only `/ready` and `/health` were checked in the
browser today).

**My own mistakes today:** a `COPY apps/__init__.py` line in the new Dockerfile for a file that does not
exist (caught before committing); seed rows in a new test missing a required column; a test that read the
machine's `DATABASE_URL` (caught by CI); citing test names in the certification from memory, two of which
did not exist (checked and corrected before committing).

---

## 2026-09-20: share prices, the market index, and a beta that can be defended

**In plain words:** both banks now show a real share price, and the valuation runs end to end. Getting
there turned up two things that would each have produced a confident, wrong answer.

**What was loaded**

| | NMB | CRDB |
|---|---|---|
| Daily prices | 2,473 days, 2016-09-22 to 2026-09-18, 35.6% with no trade | 2,473 days, 2.1% with no trade |
| Last close | TZS 2,070.00 | TZS 2,810.00 |

The DSE All Share Index: 2,460 days. The endpoint serves one date per request and gives no date of its
own, so the history was collected date by date over about 35 minutes. Each level was checked against the
change the DSE publishes with it; 13 that did not reconcile (all the first reading after a market
holiday) and 268 no-data dates were not loaded.

**Two traps, both caught**

1. **NMB split its shares 1:10 on 2026-08-24.** The published price falls from TZS 17,700 to TZS 1,850
   overnight, which is not a loss. Spotted because the resulting multiples were absurd: price/earnings
   1.4 and price/book 0.33 for a bank earning about 30% on equity. Confirmed against press coverage
   (CMSA approval 2026-07-24, post-split trading from 24 August) and against the data itself: exactly one
   tenth, no trading on the two days between, shares in issue 500m to 5,000m. Untreated it would have fed
   every beta method a fabricated 90% one-day fall and priced a 500-million-share company against a
   5-billion-share price. After the fix: NMB P/E 13.6 and P/B 3.34, CRDB 10.0 and 2.67.
   The importer now refuses any unexplained one-day move above 30%.
2. **A beta regressed on these banks' own prices is not one number.** From the same ten years: NMB 0.017
   daily (R² 0.008), 0.066 Dimson, 0.224 weekly, 0.786 monthly; CRDB 0.008 to 1.077. That rise with the
   measurement interval is what thin trading does. The owner chose the industry-average basis on
   2026-09-20: Damodaran's emerging-market "Banks (Regional)", 0.604 across 104 firms, loaded with its
   URL, hash and date. The five regressions stay on the report as a cross-check.

**Honest note on my own working:** an earlier reading of this session claimed local betas of about 2.3
and called them insane. That was wrong. It was measured against a half-finished index download, where a
two-year gap created one enormous fake return. The conclusion that a local beta is unusable still holds,
but for the opposite reason: thin trading pulls it toward zero, not above two.

**Where the valuation lands:** cost of equity 12.94%. NMB target TZS 2,597 against a price of 2,070
(+25%, Undervalued, BUY). CRDB TZS 5,566 against 2,810 (+98%). The report now flags its own fair value
when it sits more than 50% from the traded price and asks for a review first; CRDB trips it. On the
monthly regression beta NMB would be Overvalued/SELL instead, so the open questions at the top of
`docs/KNOWN_GAPS.md` decide what these reports say. Both runs remain drafts.

**Proof:** 210 Python tests pass, 3 skipped. 28 browser checks pass at 1440px and 375px. Types and lint
clean. New tests: 13 on the price and index importers, 9 on share splits, 8 on the industry beta.

**Still not run:** GitHub Actions. The workflow only triggers on pushes to `master` or pull requests into
it, and this work is on `m3-crdb-report` with no pull request open, so CI has never executed.

---

## 2026-09-20: CRDB Bank report, and one pipeline for every bank

**In plain words:** CRDB Bank now has a report built the same way as NMB, from CRDB's own annual reports.
The pipeline is shared, so adding the next bank means writing a short profile, not new code. A third
independent reader was added, and a figure is stored only when at least two readers agree.

### What changed

- **Shared bank pipeline** (`pipelines/banks/`): download, extraction, resolve and load are one pipeline
  driven by a per-bank profile. NMB's commands still work and were re-run from the PDFs to prove nothing
  changed.
- **CRDB profile**: GROUP columns of a GROUP/BANK layout, interest income split over two lines, loan
  impairment from the credit loss note, and handling for problems in CRDB's own PDFs.
- **Third reader**: the PDF's own text lines, alongside Camelot and Docling. A figure needs two readers to
  agree; an outvoted reader is recorded and shown on the Sources tab instead of blocking the figure.
- **Owners' equity for CRDB FY2020-2021** is derived from total equity, only because the report states its
  subsidiaries are 100% owned. The quote is stored with the figure.
- Deleted the modules that only served invented data (Uganda connector, fake DSE price provider, mock
  sign-in). Lint is now clean.

### Proof

NMB regression after the refactor (rebuilt from the PDFs, compared with the previous run):

```
facts same 295 295 | conflicts same 10 10 | checks same 42 42
```

CRDB resolve (`python -m pipelines.banks.resolve --bank=crdb`):

```
facts=297 conflicts=34 {'MISSING_IN_METHOD': 10, 'METHOD_OUTLIER': 5, 'METHOD_DISAGREEMENT': 4, 'RESTATEMENT': 15}
(42 of 42 checks pass, including assets = liabilities + equity for 2020 to 2025)
```

CRDB load: 5 documents (published 2022-02-18, 2023-02-17, 2024-03-15, 2025-03-14, 2026-03-13), 297 facts,
42 checks, 9 cited risks, research run `RA-20260919-003` created as a draft.

Tests: `179 passed, 3 skipped`. Browser checks: `28 passed` at 1440px and 375px (including one that proves the
CRDB page shows the GROUP and not the BANK column), plus the 10 backend-stopped checks. The CRDB suite checks 21 figures typed in by hand from the PDF pages
(2025 report p195, p196, p292, p301, p303, p327; 2024 report p169), that all 297 stored figures appear on the
page they cite, that the GROUP and not the BANK column was read, that derived figures quote their reason, and
that only the known lines are unresolved.

### CRDB ratios as they appear in the report

| Ratio | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|
| Net interest margin | 10.0% | 8.7% | 8.3% | 8.9% | 8.7% |
| Cost-to-income | 55.6% | 49.8% | 50.7% | 45.8% | 41.9% |
| Cost of risk | 0.5% | INSUFFICIENT_DATA | INSUFFICIENT_DATA | 0.9% | 1.2% |
| NPL ratio (stage 3) | 3.0% | 2.7% | 2.6% | 2.6% | 2.7% |
| NPL coverage | 86.0% | 86.7% | 56.2% | 51.9% | 65.7% |
| Loan-to-deposit | 77.7% | 83.9% | 95.3% | 94.8% | 91.9% |
| Return on equity | 24.0% | 26.0% | 26.4% | 28.6% | 30.0% |
| Return on assets | 3.4% | 3.4% | 3.4% | 3.7% | 3.7% |
| Capital adequacy (total capital) | 19.9% | 18.5% | 17.3% | 17.2% | 17.8% |
| Dividend payout | 35.1% | INSUFFICIENT_DATA | INSUFFICIENT_DATA | 30.8% | 32.1% |

Two useful cross-checks:
- Our FY2025 capital adequacy of 17.8% equals the total capital ratio CRDB states on p327 and p101.
- CRDB states an NPL ratio of 2.9% for 2025 (p20). Stage 3 over gross loans on the group basis gives 2.7%.
  The difference is probably a different basis (bank only, or the Bank of Tanzania definition). Worth
  confirming before publishing.

Figure statuses in the CRDB statement tables: 263 VERIFIED, 3 PARTIALLY_VERIFIED, 2 CONFLICTING_SOURCE,
2 INSUFFICIENT_DATA. Confidence 14 of 100 (no beta, 11 unresolved readings, stale reference inputs).

---

## 2026-09-19: NMB vertical slice brought in line with the kit rules

**In plain words:** the NMB Bank report now runs entirely on figures taken from NMB's own annual reports.

- Each figure was read twice by two different methods and matched to the page it came from.
- Every figure carries a status. Anything we cannot verify says why instead of showing a number.
- Money is stored exactly. Draft reports say "Draft, not reviewed" on the page and in the PDF.
- Buy/sell labels are off.
- Share prices are still blocked by the DSE licence, so there is no valuation or model view yet.

Branch: `truth-pass/nmb-vertical-slice`. Commits:

- `9d2a243` data model;
- `c742c6a` pipelines;
- `8add777` engines, report and API;
- `af77d10` frontend;
- `19df621` tests;
- `91ae00b` setup files;
- the docs commit that adds this entry.

### What changed

- **Kit rules applied.**
  - Status words on every figure and ratio.
  - `SHOW_TRADE_LABELS` defaults to off; the model view reads "Undervalued / Fairly valued / Overvalued".
  - `Decimal`/`NUMERIC` storage for all money and rates (`ExactDecimal`, which refuses floats).
  - Publication date for each report, with the quoted evidence.
  - Review lifecycle (draft, in_review, published, superseded), with a named reviewer and an event log.
    Production hides unpublished reports.
  - The research run gets an ID (`RA-YYYYMMDD-NNN`) plus data and config hashes.
- **Extraction fix.** The 2024 report page put the auditor's text and the income statement in one table.
  Rows are now matched on the nearest text cell. Open conflicts went from 39 to 0.
- **Re-extraction.** All five reports were re-extracted with the current code, so every figure comes from one
  pipeline version.
- **Source inconsistency found in NMB's own report.** The 2021 report, p.324, 2020 column does not add up.
  Those two figures are marked CONFLICTING_SOURCE and left out of every calculation (`config/source_issues.json`).
- **Notes.** The "what moved" notes no longer contradict themselves. Example: an impairment charge that fell
  was described as "grew more slowly".
- **Valuation engine.** It refuses a cost of equity at or below terminal growth, and method weights that do
  not sum to 1, instead of crashing.
- **Web.**
  - Draft banner, data as-of date, status badges, a "PV" marker for partly verified figures, and a
    Model view badge.
  - The Sources tab lists figures that don't add up in the source.
  - Short reasons are printed for phone users.
  - Search race condition fixed; AppLayout lint fixed.
- **Tests.** A new `tests/v1` suite with hand-worked values, API contract tests, an NMB end-to-end test,
  Playwright checks at two widths, and a backend-stopped check.
- **Setup files.**
  - `requirements.txt` lists what v1 imports.
  - Docker files fixed: paths, Node 22, standalone build, migrations. They are UNTESTED.
  - CI retargeted to `master`.
  - CLAUDE.md now has the project map and commands.
- **Docs.** New `MY_AFRIANALYZE_MASTER_AUDIT.md` (replaces `AUDIT.md`), `KNOWN_GAPS.md`, `SOURCE_REGISTRY.md`,
  `COMPLIANCE_NOTES.md` and `docs/README.md`.

### Proof

Extraction (Camelot + Docling, both methods on every report):

```
2021: regions=12 rows={'camelot': 369, 'docling': 287} items=48
2022: regions=14 rows={'camelot': 444, 'docling': 308} items=48
2023: regions=15 rows={'camelot': 469, 'docling': 314} items=48
2024: regions=16 rows={'camelot': 491, 'docling': 297} items=49
2025: regions=13 rows={'camelot': 417, 'docling': 282} items=49
```

Resolve (`python -m pipelines.nmb.resolve`):

```
facts=295 conflicts=10 {'RESTATEMENT': 10}
  FAIL 2020 net loans = gross loans + ECL allowance: loans_advances_net 4,108,891 vs gross_loans + ecl_loans 4,103,397 (difference 5,494)
(41 other checks PASS, including assets = liabilities + equity for 2020 to 2025)
```

The failing check is inside the source document. It was verified by reading p.324 of the 2021 report:
- The 2020 column shows gross 4,308,206, allowance (204,809) and net 4,108,891.
- The loan categories sum to 4,313,598.
- The 2021 column adds up exactly.

Load (`python -m pipelines.nmb.load`):

```
Loaded 5 documents (published {2021: '2022-03-30', 2022: '2023-03-30', 2023: '2024-03-27', 2024: '2025-03-27', 2025: '2026-03-31'}),
295 facts, 10 conflicts, 42 checks, 9 risk items. Research run RA-20260919-001 created as draft.
```

Python tests (`python -m pytest -q -rs tests`):

```
152 passed, 8 skipped, 3 warnings in 42.29s
SKIPPED [1] tests\test_adversarial.py:3: legacy LLM agent layer (agents/) needs litellm ...
SKIPPED [1] tests\test_adversarial_multimarket.py:3: legacy LLM agent layer (agents/) needs litellm ...
SKIPPED [4] tests\test_connectors.py: connectors/ serve MOCKED sample data and are unused in v1
SKIPPED [1] tests\test_document_ingestion.py:38: Skipping document ingestion test in TEST environment ...
SKIPPED [1] tests\test_live_e2e.py:6: Requires APP_ENV to be PRODUCTION or DEVELOPMENT ...
```

v1 suite alone (`python -m pytest -q tests/v1`): `83 passed`. It includes:
- `test_every_stored_figure_is_printed_on_its_cited_page`: 295 of 295 figures appear, character for
  character, on the cited PDF page.
- `test_hand_checked_figures`: 18 figures typed in by hand from the PDFs, with their pages:
  - 2025 report p.150, p.151, p.182, p.198, p.202, p.203;
  - 2024 report p.122;
  - 2023 report p.140;
  - 2022 report p.123.
- `test_balance_sheet_ties_every_year`: 2020 to 2025.
- Hand-worked unit tests for every ratio, each beta method (OLS, Dimson, Scholes-Williams, Hamada bottom-up,
  Blume, selection rule), cost of equity, residual income, justified P/B, DDM, projection, scenario
  probability check, model-view bands, the trade-label switch and the confidence score.

Browser, API and web running (`cd apps/web; npx playwright test`, installed Chrome):

```
24 passed (32.8s)
```

This covers all 8 routes at 1440px and 375px:
- no console errors, no HTTP errors, no sideways scrolling;
- search opens the NMB report;
- the report shows the draft banner, statuses and the model view, with no BUY/SELL/HOLD text anywhere;
- the Ratios tab shows CONFLICTING SOURCE for FY2021 cost of risk;
- statement values link to `#page=N` of the source PDF;
- the portfolio wizard refuses to size positions without prices.

Backend stopped (`$env:OFFLINE="1"; npx playwright test`):

```
10 passed (12.1s)
```

On `/`, `/report/DSE:NMB`, `/markets`, `/fixed-income` and `/health`, at both widths:
- each page says the data service is not reachable;
- no amounts or percentages are shown;
- the header shows "DATA: OFFLINE".

Frontend checks:

```
npx tsc --noEmit        -> no errors
npm run build           -> Compiled successfully; 10 app routes + 1 pages route
npx eslint src          -> 3 errors, all in the mock auth file (declared in KNOWN_GAPS.md)
```

API smoke test (FastAPI TestClient):

```
200 /health
200 /api/v1/securities
200 /api/v1/securities?q=nmb
200 /api/v1/securities/DSE:NMB
200 /api/v1/reports/DSE:NMB
200 /api/v1/reports/DSE:NMB/pdf
200 /api/v1/markets/overview
200 /api/v1/fixed-income/TZ
401 /api/v1/portfolios
404 /api/v1/reports/DSE:CRDB   ("No research report for DSE:CRDB yet")
200 POST /api/v1/portfolio/proposals -> available: false (no licensed prices)
```

Screenshots in `docs/screenshots/`:
- `desktop-1440-*.png` and `mobile-375-*.png` for home, report-nmb, markets, fixed-income, portfolio,
  dashboard, health and research-chat;
- `desktop-1440-offline-report.png` and `mobile-375-offline-report.png`.

### NMB ratios as they appear in the report (FY2021 to FY2025)

Please check these by hand against the team's CFA Research Challenge model. "PV" means partly verified: the
dividend is read from report text by one method.

| Ratio | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|---|
| Net interest margin | 11.0% | 10.6% | 10.2% | 9.6% | 9.0% |
| Cost-to-income | 46.1% | 41.6% | 38.9% | 37.8% | 37.1% |
| Cost of risk | CONFLICTING_SOURCE | 1.5% | 1.2% | 1.0% | 0.8% |
| NPL ratio (stage 3) | 4.0% | 3.1% | 3.0% | 2.8% | 2.4% |
| NPL coverage | 107.9% | 116.9% | 101.2% | 97.2% | 101.7% |
| Loan-to-deposit | 69.8% | 79.2% | 91.0% | 88.9% | 83.3% |
| Return on equity | 23.6% | 28.4% | 28.9% | 27.9% | 26.9% |
| Return on assets | 3.7% | 4.6% | 4.9% | 5.0% | 4.8% |
| Capital adequacy (total capital) | 24.6% | 23.1% | 23.3% | 27.2% | 24.7% |
| Dividend payout | 33.0% (PV) | 33.1% (PV) | 33.1% (PV) | 33.1% (PV) | 33.2% (PV) |

Definitions are shown on the Ratios tab:
- NIM uses average earning assets: net loans, placements, and amortised-cost, FVOCI and FVPL securities. Cash
  and BoT balances are excluded.
- Cost-to-income uses operating income before impairment.
- CAR is on the bank-only basis.

Figure statuses in the statement tables:
- 248 VERIFIED;
- 5 PARTIALLY_VERIFIED (dividend per share);
- 0 CONFLICTING_SOURCE (the two affected FY2020 figures are outside the five displayed years);
- 2 INSUFFICIENT_DATA (FVPL not reported).

Confidence: 45 of 100 (Low). The deductions are:
- beta not measured, −40;
- three Damodaran inputs older than 200 days, −15.

### Milestone acceptance status

| Milestone | Check | Status |
|---|---|---|
| M0 | CLAUDE.md with rules, architecture, commands | Done |
| M0 | `docker compose up` runs | UNTESTED (Docker not installed); files corrected |
| M0 | Master audit | Done (`MY_AFRIANALYZE_MASTER_AUDIT.md`) |
| M0 | Playwright smoke test at 1440 and 375 | Done (it passes now, because Milestone 1 fixes landed first) |
| M1 | Report route fixed, no mock values | Done |
| M1 | Security master, search, real health status | Done (5 verified securities) |
| M1 | No static numbers; backend stopped shows no figures | Done (10 offline checks) |
| M1 | Mobile menu, titles, `/macro` removed | Done |
| M2 | Source registry with terms notes | PARTIAL (document, not a table; terms not reviewed) |
| M2 | Scheduled ingestion with retries and alerts | MISSING (commands only) |
| M2 | Freshness shown and stale flagged | PARTIAL (as-of dates and STALE flags; no admin dashboard) |
| M2 | Dual extraction; conflicts recorded; validation blocks publication | Done for NMB. The review gate blocks production display; the admin queue is MISSING |
| M2 | NMB and CRDB, 5 years each | Done (see the 2026-09-20 entry) |
| M3 | Line items, ratios, notes | Done |
| M3 | Beta, cost of equity, valuation, scenarios, model view | Done and producing figures (see the prices entry of 2026-09-20). The beta basis is the owner's decision of 2026-09-20; the cost of equity treatment is still open |
| M3 | Risks cited | Done (9) |
| M3 | Every number traces to a source | Done (295 of 295 checked against pages) |
| M3 | PDF export | Done (draft) |
| M3 | Unit tests and NMB integration test (10+ figures vs PDF pages) | Done (18 hand-checked, 295 automated) |
| M3 | Figures that could not be sourced | Peer P/E and P/B, and the peer-by-peer bottom-up beta (need prices for individual regional banks, outside v1 scope); FY2021 cost of risk (source inconsistency); CRDB loan impairment FY2022-23 |

---

## 2026-09-18: kit documents added

- Commit `32d2a9c`: CLAUDE.md, `docs/PRODUCT_CONTEXT.md` and `docs/ROADMAP.md` from the owner's kit.
- The repository name in section 60 was corrected from `my-afrianalyzesvg` to `MORICE2004/my-afrianalyze`.

## 2026-09-17: baseline audit and frontend import

- Baseline audit (now the last section of `MY_AFRIANALYZE_MASTER_AUDIT.md`).
- Commit `716dfae`: the frontend source was imported into `apps/web`. Before this, GitHub only had a gitlink.
- Baseline test run: 71 passed, 2 failed (`test_use_connector_*`), 3 files failed to import.
