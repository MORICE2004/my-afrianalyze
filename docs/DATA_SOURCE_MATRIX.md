# Data source matrix

Checked 2026-09-25 13:07 UTC by `python -m pipelines.probe_sources` (robots rules, bot challenge, one real
data request per source; certificate errors reported, never bypassed), and against the `data_source_status`
table for what is actually loaded. Terms and licensing detail: `docs/SOURCE_REGISTRY.md` and
`docs/COMPLIANCE_NOTES.md`.

**Reachable is not implemented.** A source counts as implemented only when a loader has extracted,
validated and stored its data. Most sources below are reachable and have no loader.

Probe result words: `WORKING` (a real data request returned data we parsed), `REACHABLE_NO_LOADER` (the site
answers; nothing in this repo reads its data), `BLOCKED` (bot challenge), `UNAVAILABLE`.

## Loaded today (the v1 code path)

| Source | Dataset | Loader | Last success | Validation | Licensing | Status |
|---|---|---|---|---|---|---|
| DSE public price endpoint | Daily close, OHLC, volume, NMB and CRDB, 2016-09-22 to 2026-09-18 (2,473 days each) | `pipelines/dse/import_public_prices.py` | 2026-09-20 | Refuses a file for the wrong company; days with no close dropped, never carried forward; unexplained >30% one-day moves refused; split adjustment from `config/corporate_actions.json` | `LICENSE_REVIEW_REQUIRED`: DSE Data Vending Policy restricts redistribution; the owner accepted the risk for use on 2026-09-19, public display is an open question | **STALE** (older than its 120 h limit; no scheduled refresh) |
| DSE public index endpoint | DSEI daily level, 2,460 days | `pipelines/dse/fetch_public_index.py`, `import_public_index.py` | 2026-09-20 | Each level must equal the previous level plus the published change (±0.02); 13 days refused, 268 dates not served | Same as above | **STALE**, PARTIAL |
| NMB Bank investor relations | Annual reports FY2021-FY2025 (PDF) | `pipelines/banks/*` | 2026-09-19 | Two independent readers must agree; tie checks; every figure found on its cited page | Publicly posted by the issuer; republishing our copies is an open question | REAL (295 facts) |
| CRDB Bank investor relations | Annual reports FY2021-FY2025 (PDF) | `pipelines/banks/*` | 2026-09-19 | As above | As above | REAL (297 facts) |
| Bank of Tanzania | Treasury bond yields (2Y to 25Y) | `pipelines/macro.py:bot_bonds` | 2026-09-18 | Yield range checks; each tenor dated to its own auction | Public statistics | REAL; within its 21-day limit until 2026-10-09 |
| Bank of Tanzania | Central Bank Rate | `pipelines/macro.py:bot_cbr` | never (last attempt failed) | Parsed from the MPC statement PDF | Public | **BROKEN**: a newer MPC decision is not parsed |
| NBS Tanzania | Headline CPI inflation | `pipelines/macro.py:nbs_inflation` | 2026-09-18 | Range check | Public | REAL |
| Damodaran (NYU Stern) | Country risk premium; emerging-market bank industry beta | `pipelines/macro.py:damodaran*` | 2026-09-18 / 09-20 | Refuses implausible values or a changed sheet layout | Free for use with attribution | REAL |

## Every source in the production directive, as probed

| Source | Country | Robots | Bot challenge | Data request | Probe result | Loader in v1 |
|---|---|---|---|---|---|---|
| DSE (dse.co.tz) | TZ | present, allows | no | 200, parsed | `WORKING` | yes (prices, index) |
| CMSA (cmsa.go.tz) | TZ | present, allows | no | none tried | `REACHABLE_NO_LOADER` | no |
| Bank of Tanzania (bot.go.tz) | TZ | no robots.txt (404) | no | none tried by the probe | `REACHABLE_NO_LOADER` | yes, via `pipelines.macro` (bonds; CBR broken) |
| NBS Tanzania (nbs.go.tz) | TZ | present, allows | no | none tried by the probe | `REACHABLE_NO_LOADER` | yes, via `pipelines.macro` (CPI) |
| NSE Kenya (nse.co.ke) | KE | present, allows | no | none tried | `REACHABLE_NO_LOADER` | no |
| CMA Kenya (cma.or.ke) | KE | present, allows | no | none tried | `REACHABLE_NO_LOADER` | no |
| CMA Resource Centre (cmarcp.or.ke) | KE | present, allows | no | none tried | `REACHABLE_NO_LOADER` | no |
| Central Bank of Kenya (centralbank.go.ke) | KE | present, allows | no | none tried | `REACHABLE_NO_LOADER` | no |
| KNBS (knbs.or.ke) | KE | unknown | unknown | TLS certificate fails verification | `UNAVAILABLE` | no |
| USE Uganda (use.or.ug) | UG | no robots.txt | no | none tried | `REACHABLE_NO_LOADER` | no |
| Bank of Uganda (bou.or.ug) | UG | robots.txt has no rules | no | none tried | `REACHABLE_NO_LOADER` | no |
| UBOS (ubos.org) | UG | unknown | unknown | TLS certificate fails verification | `UNAVAILABLE` | no |
| World Bank API | Global | present, allows | no | 200, parsed (Tanzania GDP) | `WORKING` | no |
| IMF DataMapper API | Global | present, allows | home page yes (403); the API itself answers | 200, parsed (Tanzania real GDP growth) | `WORKING` | no |
| ECB Data API | Global | present, allows | no | 200, parsed (EUR/USD) | `WORKING` | no |
| UN Comtrade public preview | Global | no rules | no | 200, parsed (Tanzania total exports 2023) | `WORKING` | no |

Notes:

- The IMF API ignores the country in the path and returns every country; a loader must pick the country key.
- KNBS and UBOS: Python's certificate check fails (most likely an incomplete certificate chain on their
  servers). Turning verification off would work around it, and would also remove the protection it gives,
  so it is not done. Retry when their certificates are fixed.
- Kenya and Uganda are outside v1 (CLAUDE.md "Scope right now": Tanzania only). Building their loaders is
  a scope change for the owner to make. The legacy `connectors/nse`, `connectors/cbk`, `connectors/bou` code
  is not used by the v1 API and is not counted here.
- DSE, NSE and USE redistribution rights: `LICENSE_REVIEW_REQUIRED` for all three. Only the DSE's terms have
  been read (`docs/COMPLIANCE_NOTES.md`).
