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

Updated 2026-10-07 from the `data_source_status` table. Licensing words (`config/source_registry.json`, shown
on `/health`): `PUBLIC`, `LICENSE_REQUIRED`, `LICENSE_REVIEW_REQUIRED`, `RESTRICTED`.

| Source | Dataset | Loader | Last success | Validation | Licensing | Status |
|---|---|---|---|---|---|---|
| DSE company list + live price list | 28 listed companies (26 quoted); 26 added as "Unclassified", 2 (NMB, CRDB) already verified by hand and left alone | `pipelines/dse/discover_securities.py` | 2026-10-07 | Name read only from the company's own list entry; refuses a name two codes would share; never changes an existing security | `RESTRICTED` (see below) | REAL |
| DSE public price endpoint | Daily close/OHLC/volume for **17 shares**, 2016 to 2026-10-06 (2,473 to 2,485 days each): NMB, CRDB, DCB, DSE, EABL, JHL, KCB, MBP, MCB, MKCB, MUCOBA, PAL, SWIS, TBL, TCC, TOL, TPCC | `import_public_prices.py` (first load), `refresh_prices.py` (scheduled) | 2026-10-07 | Wrong-company files refused; missing closes dropped, never carried forward; unexplained >30% one-day moves refused over the stored + new series; split adjustment from `config/corporate_actions.json`; **merge**: new days added, a changed past close held back for review (exit 2), nothing deleted | `RESTRICTED` → display gated by `DSE_PUBLIC_DISPLAY` | REAL, fresh |
| (refused at first load) | KA, NICO, NMG, TTP, USL, VODA, AFRIPRISE, JATU: unexplained jumps in their history; TCPLC, SWALA, YETU: no data served. EABL is loaded but did not trade on any day | | | | | INSUFFICIENT_DATA |
| DSE public index endpoint | DSEI daily level, 2,472 days to 2026-10-06 | `fetch_public_index.py --from auto`, `import_public_index.py` | 2026-10-07 | Each level = previous level + published change (±0.02), the first new day checked against the stored level; merge | `RESTRICTED` | REAL, PARTIAL (268 holiday dates not served, 13 levels refused) |
| NMB / CRDB investor relations | Annual reports FY2021-FY2025 (PDF) | `pipelines/banks/*` | 2026-09-19 | Two independent readers must agree; tie checks (NMB 41/42, the failure inside NMB's own FY2021 report; CRDB 41/41 run, 1 could not be run); every figure on its cited page | `PUBLIC` to read; republishing our copies is an open question | REAL (295 + 297 facts) |
| Bank of Tanzania | Treasury bond yields 2Y-25Y | `pipelines/macro.py:bot_bonds` | 2026-10-07 | Range checks; each tenor dated to its own auction (7Y last auctioned 2022-11-09) | `PUBLIC` | REAL |
| Bank of Tanzania | Central Bank Rate | `pipelines/macro.py:bot_cbr` (newest MPC statement found on the notices page each run) | 2026-10-07 | Decision sentence must be found or the job fails; an older rate is never carried forward | `PUBLIC` | REAL: 6.25% (raised, 2 July 2026) |
| NBS Tanzania | Headline CPI inflation | `pipelines/macro.py:nbs_inflation` | 2026-10-07 | Range check | `PUBLIC` | REAL: 4.3% (August 2026) |
| Damodaran (NYU Stern) | Country risk premium; EM regional bank beta | `pipelines/macro.py:damodaran*` | 2026-10-07 | Refuses implausible values or a changed sheet layout | `PUBLIC` with attribution | REAL, data dated 2026-01-05 (STALE under the 200-day rule) |
| World Bank Indicators API | Real GDP growth, CPI inflation, current account (% of GDP), official USD exchange rate for TZ, KE, UG (188 observations, to 2025) | `pipelines/macro.py:world_bank` | 2026-10-07 | Empty country-years kept empty (4), never filled | `PUBLIC` (CC BY 4.0) | REAL |

### Not loaded, by decision

| Source | Why | Licensing |
|---|---|---|
| UTT AMIS unit trust prices | `config/funds.json` lists the six funds with their sources; prices are not loaded until the owner reads UTT AMIS's terms. The funds page shows each fund as `BLOCKED` with that reason | `LICENSE_REVIEW_REQUIRED` |
| IMF DataMapper | The IMF's terms require written permission for commercial redistribution | `LICENSE_REQUIRED` |
| ECB, UN Comtrade | Reachable; terms not yet read; not needed for v1 | `LICENSE_REVIEW_REQUIRED` |
| NSE, CBK, KNBS, USE, BoU, UBOS | Kenya and Uganda are outside v1; KNBS and UBOS certificates fail | `LICENSE_REVIEW_REQUIRED` |

### The DSE's terms

The DSE Data Vending Policy v1.2 forbids reproducing or redistributing market data from its website without a
written licence (cl. 23.1) and requires an agreement with fees for end-of-day distributors (cl. 4.5(ii)).
Hence `RESTRICTED`: the data is used for research on the owner's decision (2026-09-19), and **showing it on a
public site needs a licence**. Production refuses to start until `DSE_PUBLIC_DISPLAY` is set on purpose; with
`false`, every DSE price, index level and price-derived figure is replaced by a `BLOCKED` notice. Details:
`docs/COMPLIANCE_NOTES.md`.

## Every source in the production directive, as probed

| Source | Country | Robots | Bot challenge | Data request | Probe result | Loader in v1 |
|---|---|---|---|---|---|---|
| DSE (dse.co.tz) | TZ | present, allows | no | 200, parsed | `WORKING` | yes (prices, index, company list) |
| CMSA (cmsa.go.tz) | TZ | present, allows | no | none tried | `REACHABLE_NO_LOADER` | no |
| Bank of Tanzania (bot.go.tz) | TZ | no robots.txt (404) | no | none tried by the probe | `REACHABLE_NO_LOADER` | yes, via `pipelines.macro` (bonds, CBR) |
| NBS Tanzania (nbs.go.tz) | TZ | present, allows | no | none tried by the probe | `REACHABLE_NO_LOADER` | yes, via `pipelines.macro` (CPI) |
| NSE Kenya (nse.co.ke) | KE | present, allows | no | none tried | `REACHABLE_NO_LOADER` | no |
| CMA Kenya (cma.or.ke) | KE | present, allows | no | none tried | `REACHABLE_NO_LOADER` | no |
| CMA Resource Centre (cmarcp.or.ke) | KE | present, allows | no | none tried | `REACHABLE_NO_LOADER` | no |
| Central Bank of Kenya (centralbank.go.ke) | KE | present, allows | no | none tried | `REACHABLE_NO_LOADER` | no |
| KNBS (knbs.or.ke) | KE | unknown | unknown | TLS certificate fails verification | `UNAVAILABLE` | no |
| USE Uganda (use.or.ug) | UG | no robots.txt | no | none tried | `REACHABLE_NO_LOADER` | no |
| Bank of Uganda (bou.or.ug) | UG | robots.txt has no rules | no | none tried | `REACHABLE_NO_LOADER` | no |
| UBOS (ubos.org) | UG | unknown | unknown | TLS certificate fails verification | `UNAVAILABLE` | no |
| World Bank API | Global | present, allows | no | 200, parsed (Tanzania GDP) | `WORKING` | yes (`pipelines.macro:world_bank`) |
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
