# Data quality

Updated 2026-09-25 from the local database. How quality is enforced, what it looks like today, and where a
user sees it.

## The rules (enforced in code, not by convention)

| Rule | Where |
|---|---|
| A figure from an annual report is stored only when two independent readers (Camelot, Docling, PDF text lines) agree; an outvoted reading is recorded as a conflict | `pipelines/banks/resolve.py` |
| Every stored figure must appear on the page it cites | `tests/v1/test_nmb_integration.py`, `test_crdb_integration.py` |
| Statement tie checks (balance sheet balances, income statement adds up, net loans) | `pipelines/banks/resolve.py`, `profiles.py` |
| A figure that does not add up in the issuer's own report is excluded from every calculation | `config/source_issues.json`, `packages/report/builder.py` |
| Prices: wrong-company files refused; missing closes dropped, never carried forward; zero-volume days kept; unexplained >30% one-day moves refused; splits applied from a cited corporate action | `pipelines/dse/import_public_prices.py`, `config/corporate_actions.json` |
| Index: each level must follow from the previous level and the published change (±0.02) | `pipelines/dse/import_public_index.py` |
| Every figure shown carries a status: `VERIFIED`, `PARTIALLY_VERIFIED`, `CONFLICTING_SOURCE`, `INSUFFICIENT_DATA`, `BLOCKED`, `STALE` | `packages/report/builder.py` |
| Each source has a freshness limit; past it the source is `STALE` on `/health` and `DEGRADED` on `/ready` | `data_source_status.max_age_hours` |
| Money is `Decimal`/`NUMERIC`; a float is refused at the database layer | `packages/database/types.py`, tested on SQLite and (in CI) Postgres |

## State today

| Source | Quality |
|---|---|
| NMB annual reports | 295 facts, all two-reader agreed; 10 conflicts recorded and not used; tie checks 41 of 42 (the failure is inside NMB's own FY2021 report, recorded in `config/source_issues.json`) |
| CRDB annual reports | 297 facts; 34 conflicts recorded and not used; tie checks 42 of 42 |
| DSE prices | 2,473 days each for NMB and CRDB; NMB has no trade on 35.6% of days, CRDB 2.1%; NMB's 1:10 split (2026-08-24) applied and cited. **STALE**: last loaded 2026-09-20 |
| DSE index (DSEI) | 2,460 days; 13 refused by the reconciliation, 268 dates not served by the DSE. **STALE** |
| BoT bonds | Each tenor dated to its own auction (the 7Y is from 2022, and is shown with that date) |
| BoT Central Bank Rate | **Failed**: the latest MPC statement is not parsed; the old rate is not used as if current |
| NBS CPI, Damodaran | Current within their limits |

## Where a user sees it (the data-quality dashboard)

The `/health` page lists every source with status, last success, age and limit, and the report page shows
each figure's status, its conflicts and the gaps that stopped a calculation. Against the directive's list:

| Item | Shown |
|---|---|
| Source health, last ingestion, latest success | yes, `/health` |
| Failed, stale, blocked sources | yes, `/health` (status per source) |
| Conflicting data | yes, on the report (per figure), counts in `/health` detail |
| Missing data | yes, as `INSUFFICIENT_DATA` / `BLOCKED` with the reason, on the report |
| Extraction and validation failures as their own list | **no**: they are in the database (`extraction_conflicts`, `validation_checks`) and in the pipeline output, not on a page. P2 |
