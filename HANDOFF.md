# Handoff

Updated 2026-09-20, after prices were loaded. Branch `m3-crdb-report` (off `truth-pass/nmb-vertical-slice`).

## Read this first

Share prices, the market index and the valuation now work end to end for both banks. Three things to
weigh before you approve either run:

1. **The model says both banks are cheap.** NMB's fair value is 14% above the traded price, CRDB's is
   79% above. The report says so itself and asks for a review. A gap that wide usually means the
   projection is too generous or the cost of equity is too low, not that the market is wrong.
2. **The answer turns on one choice.** With the monthly regression beta, NMB is Overvalued / SELL. With
   the industry beta you chose, it is Undervalued / BUY. Same accounts, same price.
3. **Nothing is published.** Both runs are drafts, and production hides drafts.

Details and the two open questions are at the top of `docs/KNOWN_GAPS.md`.
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
| Share price | TZS 2,070.00 (18 Sep 2026) | TZS 2,810.00 (18 Sep 2026) |
| Price history | 2,473 days, 35.6% with no trade | 2,473 days, 2.1% with no trade |
| Beta | industry 0.604 (104 banks) | industry 0.604 |
| Cost of equity | 12.94% | 12.94% |
| 12-month target | TZS 2,597 (+25%) | TZS 5,566 (+98%, flagged for review) |
| Model view | Undervalued (BUY) | Undervalued (BUY) |
| Confidence | 85/100 | 54/100 |

Everything else on the site (search, markets, fixed income, portfolio wizard, health) shows only sourced data
or says why a figure is missing.

## Where the prices come from

Your decision of 2026-09-19: use the prices the DSE publishes on its own website, whose robots file allows
automated access, rather than waiting for a licence. The DSE Data Vending Policy restricts reuse of its
market data and you accepted that risk; it is written down in `docs/COMPLIANCE_NOTES.md`.

- Daily prices come one file per company from the address the DSE's own chart uses.
- Index levels come one date at a time, because that is all the endpoint serves. Ten years takes about
  35 minutes, and the job can be stopped and restarted.
- Every price carries the web address, the download time and the file's fingerprint. The files themselves
  are never served on to users: the product calculates from the data and does not republish it.
- Commands are in `CLAUDE.md`. The academic request in `docs/DSE_ACADEMIC_DATA_REQUEST.md` is still unsent
  and would give a licensed series if you want one.

**Two traps that are now handled, and would have been expensive:**

- **NMB split its shares 1:10 on 24 August 2026.** The DSE publishes prices as they traded, so the price
  falls from TZS 17,700 to TZS 1,850 overnight. That is not a loss. Untreated it would have fed every beta
  a fake 90% crash and priced a 500-million-share company against a 5-billion-share price. Splits now live
  in `config/corporate_actions.json` with their evidence, and the importer refuses any unexplained one-day
  move above 30%.
- **A beta regressed on these banks' own prices is not usable.** NMB does not trade on 35.6% of days, so
  its beta comes out anywhere from 0.02 (daily) to 0.79 (monthly). You chose the industry-average basis on
  2026-09-20.

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

## Decisions you made

| Decision | Where it lives |
|---|---|
| **2026-09-20:** the valuation beta is the average of comparable listed banks, not a regression on the bank's own price | `config/valuation.json` (`industry` first in both orders); the figure is loaded by `pipelines.macro` from Damodaran |
| Terminal growth 6% | `config/valuation.json` |
| Buy/Hold/Sell labels need no licence, so they are on | `packages/core/config.py`, `docs/COMPLIANCE_NOTES.md` |
| You review reports; target flow is request → prepare → review → publish | review commands exist; the request queue is not built |
| Use the DSE academic route, and the prices the DSE serves publicly | `docs/DSE_ACADEMIC_DATA_REQUEST.md`, item 2 above |
| Delete only useless fake code | Uganda connector, fake DSE price provider, mock sign-in deleted |

## What I would do next, in order

1. **Settle the cost of equity**, and with it whether these reports say BUY or SELL. It is 12.94% today,
   only about 2.2 points more than the Tanzanian government pays on a 10-year bond, because the sovereign
   default spread is removed from the risk-free rate before the equity premium is added. Then look at
   CRDB's 25.9% loan growth being carried forward. See the top of `docs/KNOWN_GAPS.md`.
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
