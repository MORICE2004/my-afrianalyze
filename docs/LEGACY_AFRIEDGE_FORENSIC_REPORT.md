# Legacy AfriEdge forensic report

Read-only audit, 2026-09-25, of `~/.gemini/antigravity/scratch/my-afrianalyze`, which is `master` at
`b77c609` with a clean working tree (so auditing `git show origin/master:<file>` audits that copy). Archived
unchanged as branch `afriedge-legacy-archive`. File name: the directive asked for `LEGACY_AFIEDGE_...`; the
missing R is taken to be a typo.

Line numbers are in `origin/master`. "Useful" asks whether the idea is worth having; "salvageable" asks
whether the code itself can be used.

## Fake data, fake status, fake identity

| # | File:line | Behaviour | Risk | Useful | Salvageable | In the canonical repo instead |
|---|---|---|---|---|---|---|
| 1 | `apps/api/main.py:143-162` | The "grounded" copilot is given a fixed block labelled "Verified Metrics (FY2025 Audited)": NIM 8.4%, NPL 3.2%, ROE 24.1%, C/I 46.8%, fair value TZS 5,420, "Page 48, Table 4.2", for **any** ticker. NMB's real FY2025 values (two-reader extraction): NIM 9.0%, NPL 2.4%, ROE 26.9%, C/I 37.1%, fair value TZS 2,354 | Critical: invented figures presented to users as audited, with an invented citation | the idea of a copilot | no | Not built. Must be fed the stored report payload only (PRODUCTION_CERTIFICATION: AI copilot) |
| 2 | `apps/web/src/app/report/[symbol]/page.tsx:12-73` | Every ticker shows price 17.50, "▼ -0.45 (-2.5%)", market cap 701.2B, **OVERWEIGHT**, "11.2x P/E", "KES 22 fair value" (Kenyan shillings for Tanzanian banks), RSI 42, support 17.00. The page makes no API call | Critical: a fabricated recommendation on every company | layout ideas only | no | `/report/[id]` renders the API's report with a status on every figure |
| 3 | `apps/web/src/app/markets/page.tsx:9-57` | DSE index series 2,140 to 2,145.32 typed in; two other index charts drawn with `Math.random()`; movers list NMB 4,800, CRDB 540 (real last closes 2,070 and 2,810), Safaricom, MTN, EABL | Critical: invented and random market data | no | no | `/markets` reads `/api/v1/markets/overview` |
| 4 | `apps/web/src/app/fixed-income/page.tsx:9-33, 114` | T-bill and bond yields 3.50% to 12.56%, auction table with clean prices, dates and issue numbers, and "Kenya: 4.5%, Uganda: 6.2%" real yields, all typed in | Critical | no | no | `/fixed-income` reads BoT yields with their auction dates |
| 5 | `apps/web/src/app/health/page.tsx:14-36` | "DSE Connection: Healthy", "Last sync: 2 mins ago", "Database: Healthy, 12ms", "LLM Service: Degraded, 1200ms" as fixed text | High: health status that cannot change | no | no | `/health` reads `data_source_status` |
| 6 | `apps/web/src/app/dashboard/page.tsx:28-54` | "mock data representing a user's saved portfolios" (MTNN.LG, SCOM.NR, EQTY.NR, STANBIC.LG with weights and drift) | High | the drift idea | no | Saved portfolios: 401 until sign-in exists |
| 7 | `apps/web/src/components/PortfolioDashboard.tsx:10-55` | Three portfolios with expected return 10.2% to 16.8%, volatility, yield and allocations typed in | Critical: fabricated expected returns (the directive forbids exactly this) | no | no | Proposal endpoint says "not available" and why |
| 8 | `apps/web/src/components/FinancialMetrics.tsx:17-23` | P/E 12.5, P/B 2.1, ROE 18.5%, dividend yield 5.2% typed in | High | no | no | Ratios come from `packages/analysis/bank_ratios.py` |
| 9 | `apps/web/src/components/MultiMarketChart.tsx:3-9` | `mockData` DSE vs NSE monthly series | High | no | no | none shown until data exists |
| 10 | `apps/web/src/components/research/TechnicalWorkspace.tsx` | Regime fixed to "Bullish", RSI 65.4, "Bullish Crossover", "Golden Cross", chart placeholder | High | the layout | no | Not built in v1 (INSUFFICIENT_DATA rules exist in section 74) |
| 11 | `apps/web/src/components/research/FinancialStatements.tsx:90` | "Data structure mocked for {activeStmt}" | Medium | no | no | Statements come from stored facts |
| 12 | `apps/web/src/components/research/ValuationExplainer.tsx` | Computes the target price **in the browser** (`bookValue * targetPB / sharesOut`, JavaScript floats) | High: an unaudited second calculation that can disagree with the engine | the "show the math chain" idea | no | Rewrite as a view of the engine's own inputs and outputs (not done yet) |
| 13 | `apps/web/src/pages/api/auth/[...nextauth].ts:19-22` | "Mocking authentication success": any email and password sign in as user `1`, "J Smith" | Critical security | no | no | No sign-in; nothing per-user exists |
| 14 | `apps/api/routers/portfolios.py:8-14`, mounted at `apps/api/main.py:40` | `get_current_user()` returns user `1`, `analyst@afriedge.com`, for every request; create/read/update/delete all act on that user | Critical security: anyone could change or delete the portfolios | ownership checks in the queries are the right shape | no (no real identity) | Not ported; `/api/v1/portfolios` answers 401 |
| 15 | `connectors/use/connector.py:66-74` | Uganda prices: `Decimal("31.50") if ticker == "STAN" else Decimal("30.50")`, open 30.00, high 31.00, low 30.00 | Critical | no | no | Deleted on the canonical branch 2026-09-19 for this reason |
| 16 | `apps/api/main.py` `/api/v1/companies` | A hardcoded coverage list including NSE and USE companies with no data behind them | Medium | no | no | `config/securities.json`, each verified on its exchange listing page |
| 17 | `data/source_registry.yaml` | DSE licensing recorded as `PUBLIC_REGULATORY`; the DSE Data Vending Policy restricts redistribution | High (licensing) | the file layout | no | `docs/DATA_SOURCE_MATRIX.md`: `LICENSE_REVIEW_REQUIRED` |
| 18 | `docs/PRODUCTION_CERTIFICATION.md` | CI "REMOTE, passes all 81 test cases"; USE connector, auth, copilot marked "Real: YES" | High: false certification | no | no | `docs/PRODUCTION_CERTIFICATION.md` on the canonical branch |
| 19 | `apps/web/src/app/api/chat/route.ts:32-38` | When the backend is down it says so ("AfriEdge Offline Notice") | none: honest | yes | the pattern | Keep the pattern when a copilot is built |

## Salvage

| Candidate | Class | Reason |
|---|---|---|
| Logo `apps/web/public/logo.png` (1024×1024, black on white) | **KEEP** | Matches the brand direction (black, minimal, no gradient). Ported |
| The name "AfriEdge" | **KEEP** | Owner's decision (directive of 2026-09-25) |
| `apps/web/docs/BRAND_SYSTEM.md` (restrained palette, mono figures, no crypto look) | **PORT** (as principles) | Already how the canonical UI works; recorded in the README |
| EvidenceLineage (extracted text plus calculation chain per figure) | **REWRITE** | Good idea; the canonical report already has figure → page links. A later step can show the formula and inputs the API already returns |
| ValuationExplainer | **REWRITE** | Idea good, code computes figures in the browser |
| ResearchTimeline | **REWRITE** later | Display only; needs real research-run events |
| Every data page, TechnicalWorkspace, PortfolioDashboard, FinancialMetrics, MultiMarketChart, dashboard | **REJECT** | Fake data |
| NextAuth sign-in, portfolio router identity | **REJECT** | Fake identity |
| Uganda connector, `/api/v1/companies`, copilot context | **REJECT** | Invented figures |
| `data/source_registry.yaml`, certification | **REJECT** | False statuses |
| PostHog and telemetry wrappers (`lib/posthog.ts`, `lib/telemetry.ts`) | **REJECT** for now | Written for PostHog without a project; to be done fresh when one exists, with a list of allowed events |

## What was checked not to have been ported

After the port, the canonical branch was searched for the legacy values and names: `17.50`, `701.2B`,
`OVERWEIGHT`, `2145.32`, `5,420`, `24.1%`, `J Smith`, `analyst@afriedge.com`, `mockData`, `Math.random`,
`31.50`. Result recorded in `docs/PROGRESS.md` (2026-09-25, reconciliation entry).
