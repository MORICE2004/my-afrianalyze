# Handoff

Written 2026-09-20. Branch `m3-crdb-report` (off `truth-pass/nmb-vertical-slice`).
Read this with `CLAUDE.md` (rules and commands), `docs/MY_AFRIANALYZE_MASTER_AUDIT.md` (what is real),
`docs/KNOWN_GAPS.md` (what is missing) and `docs/PROGRESS.md` (proof).

## Where the product stands

Two Tanzanian bank reports are built end to end from the banks' own annual reports:

| | NMB Bank Plc | CRDB Bank Plc |
|---|---|---|
| Page | `/report/DSE:NMB` | `/report/DSE:CRDB` |
| Annual reports | 2021 to 2025 | 2021 to 2025 |
| Figures stored | 295 | 297 |
| Readers agreeing on each figure | 2 of 2 | at least 2 of 3 |
| Tie checks | 41 of 42 pass | 42 of 42 pass |
| Statements | Income statement, balance sheet, cash flow, key notes | same |
| Ratios | 10, all years except cost of risk FY2021 | 10, all years except cost of risk and payout FY2022-23 |
| Price, beta, valuation, model view | BLOCKED (no licensed prices) | BLOCKED |

Everything else on the site (search, markets, fixed income, portfolio wizard, health) shows only sourced data
or says why a figure is missing.

## The one thing blocking the most value

No share prices. Without them there is no price, beta, cost of equity, valuation, target price or model view
for either bank. Three ways forward:

1. **DSE academic route** (your decision of 2026-09-19). Draft request: `docs/DSE_ACADEMIC_DATA_REQUEST.md`.
   You send it; I have not contacted the DSE.
2. **Download the prices the DSE publishes** (your decision of 2026-09-19). The DSE website serves daily
   prices through the address its own chart uses:
   `https://dse.co.tz/api/get/market/prices/for/range/duration?security_code=NMB&days=3650&class=EQUITY`
   Its robots file allows automated access. **Claude Code's own permission check blocked me from downloading
   it.** To let a future session do it, add to `C:\Users\Morice RUGEMARILA\.claude\settings.json`:

   ```json
   { "permissions": { "allow": ["Bash(curl:*dse.co.tz*)"] } }
   ```

   Then the next step is an importer (`pipelines/dse/import_public_prices.py`) that downloads slowly, stores
   each price with its web address and download time, and records that this was your decision. Note the DSE
   Data Vending Policy restricts reuse of its prices; you accepted that risk.
3. **A commercial data vendor.**

Once prices exist, nothing else needs building: the beta, cost of equity and valuation engines are written and
tested, and they switch from BLOCKED to real numbers.

## How to run it

See CLAUDE.md for the full list. The short version, from the repo root in PowerShell:

```powershell
.venv\Scripts\python -m uvicorn apps.api.main:app --port 8000     # API
cd apps\web; npm run dev -- --port 3000                             # web at http://localhost:3000
.venv\Scripts\python -m pytest -q tests                             # 179 pass, 3 skipped
```

To add another bank: write a profile in `pipelines/banks/profiles.py`, run the four commands
(`download_reports`, `extract`, `resolve`, `load` with `--bank=<key>`), then write
`tests/v1/test_<bank>_integration.py` with figures you have checked by hand against the PDF pages.

## How the data pipeline works (in words)

1. **Download** each annual report from the bank's own investor relations page and store a fingerprint
   (SHA-256), so a changed file is noticed.
2. **Read** each statement page with three independent readers: Camelot (table lines), Docling (layout model)
   and the PDF's own text lines.
3. **Agree**: a figure is stored only when at least two readers read it identically. A reader that is outvoted
   is recorded and shown on the Sources tab. A figure only one reader found is not used.
4. **Check**: assets = liabilities + equity, income statement arithmetic, net loans = gross loans less the
   allowance. A failed critical check stops the load.
5. **Load** with provenance: currency, period, page, extraction methods, publication date (the board approval
   date, with the quote) and terms-of-use note.
6. **Report**: deterministic Python computes every ratio and valuation. Each figure carries a status. Nothing
   is shown without a source.
7. **Review**: every run starts as a draft. In production only a run you approved is visible
   (`pipelines.review approve --by "Your Name" --note "..."`).

## Decisions you made (2026-09-19)

| Decision | Where it lives |
|---|---|
| Terminal growth 6% | `config/valuation.json` |
| Buy/Hold/Sell labels need no licence, so they are on | `packages/core/config.py`, `docs/COMPLIANCE_NOTES.md` |
| You review reports; target flow is request → prepare → review → publish | review commands exist; the request queue is not built |
| Use the DSE academic route, and the prices the DSE serves publicly | `docs/DSE_ACADEMIC_DATA_REQUEST.md`, item 2 above |
| Delete only useless fake code | Uganda connector, fake DSE price provider, mock sign-in deleted |

## What I would do next, in order

1. **Prices** (see above). Unblocks valuation for both banks.
2. **CRDB loan impairment for FY2022 and FY2023.** The credit-loss note is laid out differently in those
   years and the readers disagree, so cost of risk is missing for them. It needs the note read by page
   position rather than row order.
3. **Confirm the two source problems** in `config/source_issues.json` (NMB FY2020 loan figures) and CRDB's own
   NPL ratio difference (CRDB states 2.9% for 2025; stage 3 over gross loans on the group basis gives 2.7%,
   probably a different basis).
4. **Review and publish** the two draft runs, so they are visible in production mode.
5. **Docker and CI**: both are written but never run. Install Docker, then `docker compose up`; CI runs on the
   next push.
6. **The rest of the DSE**: the same pipeline, one profile per company, or a labelled "limited coverage" page.
7. **Accounts**, then the report request queue you described, then plans and payments.

## Things to be careful about

- Never let a number reach a page without a source. Every figure in the payload carries a status and a page
  reference; `tests/v1` enforces it.
- Money is `Decimal` everywhere. The database column refuses floats.
- The 2022 and 2023 CRDB PDFs contain garbled letters, and the 2023 report misprints its own heading. The
  fixes are listed in the CRDB profile; do not "clean them up" without re-running the tests.
- Old code in `agents/`, `connectors/`, `models/`, `apps/api/routers|tasks|core` and most of `packages/*` is
  not used by the product. Some of it still contains invented numbers. Do not wire it back in.
- 3 tests skip on purpose (legacy modules). They state their reason.
