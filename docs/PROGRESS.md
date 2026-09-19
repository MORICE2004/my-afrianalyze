# Progress

Proof for each step (ROADMAP rule 3). Newest first. Plain-language summary at the top of each entry.

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
| M2 | NMB and CRDB, 5 years each | NMB done; CRDB MISSING |
| M3 | Line items, ratios, notes | Done |
| M3 | Beta, cost of equity, valuation, scenarios, model view | Engines done and tested; output BLOCKED (DSE prices) |
| M3 | Risks cited | Done (9) |
| M3 | Every number traces to a source | Done (295 of 295 checked against pages) |
| M3 | PDF export | Done (draft) |
| M3 | Unit tests and NMB integration test (10+ figures vs PDF pages) | Done (18 hand-checked, 295 automated) |
| M3 | Figures that could not be sourced | Price, beta, CoE result, valuation, target, peers (all BLOCKED by the DSE licence); FY2021 cost of risk (source inconsistency) |

---

## 2026-09-18: kit documents added

- Commit `32d2a9c`: CLAUDE.md, `docs/PRODUCT_CONTEXT.md` and `docs/ROADMAP.md` from the owner's kit.
- The repository name in section 60 was corrected from `my-afrianalyzesvg` to `MORICE2004/my-afrianalyze`.

## 2026-09-17: baseline audit and frontend import

- Baseline audit (now the last section of `MY_AFRIANALYZE_MASTER_AUDIT.md`).
- Commit `716dfae`: the frontend source was imported into `apps/web`. Before this, GitHub only had a gitlink.
- Baseline test run: 71 passed, 2 failed (`test_use_connector_*`), 3 files failed to import.
