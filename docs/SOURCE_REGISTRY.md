# Source registry

Every data source the product uses or plans to use (PRODUCT_CONTEXT.md section 73, ROADMAP Milestone 2).

- Live status comes from `GET /health` (table `data_source_status`).
- Raw responses are saved under `data/raw/` with a SHA-256.
- "Terms reviewed: no" means no one has yet checked whether the source's terms allow use in a paid product.
  Those questions are in `COMPLIANCE_NOTES.md`.

Last updated: 2026-09-19.

| Source | URL | Provides | Refresh | Terms of use notes | Status | Last successful fetch |
|---|---|---|---|---|---|---|
| NMB Bank Plc investor relations | https://www.nmbbank.co.tz/investor-relations-nmb/ | Annual reports FY2021 to FY2025 (PDF) | Yearly (published about end of March) | Public download. Terms reviewed: no. We also host copies (`/api/v1/sources/{id}/file`), which is a separate question | REAL | 2026-09-17 (manifest `data/raw/nmb/manifest.json`) |
| Dar es Salaam Stock Exchange listing pages | https://www.dse.co.tz/ | Company name, symbol, listing date (security master verification, by hand) | When a listing changes | Viewed by hand for verification only; no data copied beyond name and symbol | REAL (manual) | 2026-09-17 (`verified_at` per security) |
| DSE daily prices (public endpoint) | `https://dse.co.tz/api/get/market/prices/for/range/duration?security_code=<CODE>&days=<N>&class=EQUITY` | End-of-day close and volume per security, whole history | Daily | Served publicly by the DSE's own site; its `robots.txt` is `Disallow:` (nothing disallowed). The DSE Data Vending Policy cl. 16.3.3 and 23.1 still restrict reuse: **the owner decided on 2026-09-19 to use the published prices and accepted that risk.** The file is stored and used to calculate, never served on (403) | REAL | 2026-09-20 (NMB and CRDB, 2016-09-22 to 2026-09-18) |
| DSE index levels (public endpoint) | `https://dse.co.tz/get/last/traded/indices?from=<date>` | All Share Index (DSEI) and the four sector indices, one date per request | Daily | As above. Collected date by date at 0.75s intervals; each level is reconciled against the change the DSE publishes with it | REAL | 2026-09-20 (DSEI backfill) |
| Damodaran industry betas (emerging markets) | https://pages.stern.nyu.edu/~adamodar/pc/datasets/betaemerg.xls | Average levered beta, D/E and effective tax rate for "Banks (Regional)" (104 firms), used as the valuation beta | Yearly (January) | Published free for teaching and research, with attribution | REAL | 2026-09-20 (data as of 2026-01-05) |
| DSE licensed price files | https://www.dse.co.tz/ | A licensed end-of-day file, if the owner obtains one | On request | Academic route cl. 17.1, 17.7. Draft request in `DSE_ACADEMIC_DATA_REQUEST.md`, unsent | MISSING | Never |
| Bank of Tanzania, Treasury bond auctions | https://www.bot.go.tz/TBonds (+ POST `/TBonds/AuctionSummaries`) | Weighted average yield to maturity by tenor and auction date | Each auction (about every 2 weeks) | Public page. Terms reviewed: no | REAL | 2026-09-18 |
| Bank of Tanzania, Monetary Policy Committee statement | https://www.bot.go.tz/Adverts/PressRelease/en/2026040215591446.pdf | Central Bank Rate | Quarterly | Public press release. Terms reviewed: no | PARTIAL (fixed URL; STALE) | 2026-09-18 (statement dated April 2026) |
| National Bureau of Statistics, CPI release | https://www.nbs.go.tz/statistics/topic/consumer-price-index-2026 | Headline inflation, year on year | Monthly | Public release. Terms reviewed: no | REAL | 2026-09-18 (August 2026 release) |
| Damodaran Online (NYU Stern), country risk premiums | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html | Tanzania rating, default spread, CRP, total ERP, mature-market ERP, tax rate | January (and mid-year) | Freely published. Commercial reuse and attribution terms not confirmed. Terms reviewed: no | REAL (STALE, as of 2026-01-05) | 2026-09-18 |
| Bank of Tanzania, Treasury bills | https://www.bot.go.tz/ | T-bill auction yields | Weekly | Not checked | MISSING | Never |
| Unit trust managers (e.g. UTT AMIS) | not chosen | Fund NAVs and fees | Daily | Not checked | MISSING | Never |
| Capital Markets and Securities Authority (CMSA) | https://www.cmsa.go.tz/ | Notices, licensed fund list | As published | Not checked | MISSING | Never |
| CRDB Bank Plc investor relations | not added | Annual reports | Yearly | Not checked | MISSING | Never |
