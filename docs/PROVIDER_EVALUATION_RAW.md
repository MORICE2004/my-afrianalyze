# Provider Evaluation (raw working note)

Researched: 2026-10-08. Read-only web research. No accounts created, no keys entered, no API calls made with credentials, no terms accepted.
Method: pages fetched with `curl` / WebFetch and read as text. Machine-readable specs (OpenAPI, llms.txt, Postman) were parsed directly so field names below are copied from the provider's own spec, not guessed.

Labels:
- **VERIFIED**: read today on the provider's own site/docs (URL given).
- **CONFLICTING_SOURCE**: the provider's own pages contradict each other.
- **CLAIMED-ELSEWHERE**: seen only on a third-party site.
- **UNKNOWN**: not stated on any public page I could read; needs an account or a sales answer.

Nothing here was tested against a live API. All field names come from docs/specs; real responses may differ.

---

## 1. Mansa (Mansa API / Mansa Markets)

### Who and where
- Operator: Mansa Labs, "a trading name of SereneCircle Limited", Lagos, Nigeria. VERIFIED, https://mansaapi.com/terms
- Mansa Markets ToS says it is "operated by Kobo Terminal, formerly NGX Pulse". VERIFIED, https://www.mansamarkets.com/terms. (The two sites name different operators. Minor, but worth knowing for who signs the contract.)
- Two official sites with **different pricing and licensing text**:
  - Developer API site: https://mansaapi.com (docs, OpenAPI, pricing, licensing, terms)
  - Terminal site: https://www.mansamarkets.com (pricing, /developers page, terms)
- Both point to the same API host, `https://mansaapi.com`.

### Plans and prices (USD per month)

From **mansaapi.com/pricing** (VERIFIED, https://mansaapi.com/pricing):

| Plan | Price | Requests/day | Market-data highlights |
|---|---|---|---|
| Free | $0 | 100 | Live stock prices, ETFs, indices, forex, commodities |
| Starter | $20 | 1,000 | + screener, 45-metric sheets, "Dividend history & corporate actions", NGX disclosures |
| Pro ("professional" tier token) | $50 | 10,000 | + "Daily price history — OHLCV archive, 16 exchanges", insider trades |
| Business | $200 | 100,000 | + "Yields, bonds & full macro suite", "Redistribution-lite (derived datasets, with attribution)", "Webhook support (coming soon)" |
| Institutional | Custom | Unlimited | SLA, invoice billing, bulk data |

Prepaid overage packs: $5 / 7,500 calls, $20 / 35,000, $50 / 100,000. Counter resets midnight UTC.

From **mansamarkets.com/pricing** (VERIFIED, https://mansamarkets.com/pricing), the same price points are described differently:

| Plan | Price | Requests/day | Rights listed |
|---|---|---|---|
| Free | $0 | 100 | "Commercial use & redistribution" not included |
| Starter | $20 | 1,000 | "Commercial use rights"; no redistribution |
| Professional | $50 | 10,000 | "Data redistribution rights", "Webhook event subscriptions", "Single key, multiple environments" |
| Institutional | $200 | 100,000 | SLA uptime, "Webhook · S3 · SFTP data delivery" |

mansamarkets.com/developers (VERIFIED, https://mansamarkets.com/developers) lists Professional $50 as "Commercial use rights" and "Use in production apps"; its FAQ says "Commercial use, including redistribution of data in your app, requires the Professional tier at $50/month".

**Production plan for AfriEdge**: at minimum **Pro/Professional $50** (needed for per-stock OHLCV history; 10,000 req/day). Whether that tier covers AfriEdge's use is CONFLICTING_SOURCE (see licensing below).

### Coverage
- DSE (Tanzania): listed. VERIFIED on https://mansamarkets.com/pricing FAQ, https://www.mansaapi.com/african-stock-market-api, OpenAPI path parameter descriptions ("NGX, GSE, NSE, JSE, BRVM, DSE, or LUSE"). Exchange code `DSE`.
- NSE (Kenya): listed, code `NSE`. VERIFIED (same pages).
- USE (Uganda): listed, code `USE`, on mansamarkets.com/pricing FAQ and mansaapi.com landing page. Not mentioned anywhere in mansaapi.com/docs or the OpenAPI spec. VERIFIED as listed; the API docs say nothing more about it.
- The live terminal page https://www.mansamarkets.com/tanzania showed a DSE board of 26 securities with DSE All Share Index 4,611.00 "Last updated 8 Oct, 11:00 GMT+3". VERIFIED as displayed; numbers not checked against DSE.
- Exchange count is inconsistent across Mansa's own pages (CONFLICTING_SOURCE): 32 countries / 20 exchanges (mansamarkets.com), 19 live / 19 tracked (mansaapi.com landing), 17 exchanges for history (OpenAPI), 16 for OHLCV archive (pricing), 22 for security master (docs), and `live_exchange_coverage: 7` in https://mansaapi.com/health (fetched 2026-10-08T08:16Z).

### Data types (VERIFIED from https://mansaapi.com/openapi.json and https://mansaapi.com/docs unless noted)
- Latest quote: yes, `GET /api/v1/markets/exchanges/{exchange_code}/stocks/{ticker}` (Free tier).
- EOD OHLCV history: yes, `.../stocks/{ticker}/history`, Pro and above.
  - Published depth: JSE from 1980, Kenya from 1992, Morocco 1994, Egypt/Botswana 1995, Ghana/Zambia/Mauritius/Namibia 1996, ZSE 2011. **Tanzania and Uganda are not on the depth list.** DSE stock history depth = UNKNOWN.
  - Prices are "as-published. We ... do not currently back-adjust for splits or corporate actions." (https://mansaapi.com/methodology)
- Index data: yes for DSE. "DSE returns TSI, DSEI, BI, IA, and CS when the DSE feed has current data." Endpoints `/api/v1/markets/exchanges/DSE/indices`, `.../indices/{code}`, `.../indices/{code}/history?range=1D|1W|1M|3M|1Y|ALL`. DSE index endpoints were added 2026-06-08 (https://mansaapi.com/changelog), so DSEI history depth is probably short. Depth = UNKNOWN.
- Dividends / corporate actions: `.../dividends/{ticker}` is documented as **"NGX only"**. `dividends-calendar` also NGX. The terminal page for NMB showed a DSE dividend table (2021 to 2025), but the API doc does not confirm a DSE dividend endpoint. DSE via API = UNKNOWN.
- Fundamentals: `/api/v1/fundamentals/{exchange}/{ticker}` (filing-verified, "on covered NGX names"), `/api/v1/metrics/{exchange}/{ticker}` (~45 metrics, 16 exchanges, weekly), `/api/v1/screener`. Starter and above. DSE coverage of these = UNKNOWN.
- Security master: `/api/v1/identifiers` and `/api/v1/identifiers/{exchange}/{ticker}` (ISIN, FIGI), Starter and above. Search: `/api/v1/markets/search?q=&exchange=&limit=`.
- Bonds / T-bills / yields: `/api/v1/markets/yields/{country}/tbills|curve|auctions`, `/bonds/{country}`, Pro and above. The changelog's coverage list for these (2026-06-11) names Nigeria, Ghana, Kenya, South Africa, Zambia, Malawi, Mauritius, Uganda, Tunisia, Algeria, Botswana, Eswatini, Cape Verde. **Tanzania is not listed.**
- Trading calendar: `/api/v1/markets/calendar/{exchange}/is-open` (Free), `/calendar/{exchange}` (Starter and above).

### Freshness, limits, webhooks
- Cadence: "Markets endpoints currently target 30-minute freshness during market hours" (docs). Methodology: "Not tick data. Quotes target a 30-minute window". After close, data "reflects official end-of-day figures" (mansamarkets.com/pricing). History is `data_freshness: "daily"`. VERIFIED.
- Limits: 100 / 1,000 / 10,000 / 100,000 requests/day by tier. No per-minute limit is published. UNKNOWN.
- Webhooks: **no webhook endpoints in the OpenAPI spec.** mansaapi.com/pricing says "Webhook support (coming soon)" on Business. mansamarkets.com/pricing lists "Webhook event subscriptions" on Professional. CONFLICTING_SOURCE; the API docs show none.

### Licensing / redistribution / public display
- **mansaapi.com/licensing** (VERIFIED, https://mansaapi.com/licensing), table by tier:
  - "Display data in your app or site": Free "Yes, with attribution"; Starter, Professional, Business, Institutional "Yes".
  - "Cache responses to serve your own users": Free/Starter "Up to 24 hours"; Professional/Business "Up to 7 days"; Institutional "Negotiable".
  - "Redistribute or resell raw data": Free/Starter/Professional "No"; Business "Lite — derived datasets, with attribution"; Institutional "Yes, per agreement".
  - Text: "Every tier may display Mansa API data inside your own app, dashboard, or website". Also: "If your users consume the data inside your product's own interface and features, that is display, not redistribution — you're fine on any tier." And: "building a stored copy of our datasets to serve as a data product is redistribution". Free tier requires the attribution "Data by MansaAPI" with a link.
  - Same page also says "Data redistribution requires the Institutional tier", which contradicts its own Business "Lite" row.
- **mansamarkets.com/pricing**: Professional ($50) = "Data redistribution rights". This contradicts mansaapi.com/licensing (Professional = No). CONFLICTING_SOURCE.
- **Mansa Markets ToS** (VERIFIED, https://www.mansamarkets.com/terms):
  - 5.1: licence "solely for your internal business purposes or personal projects". This sits awkwardly next to public display.
  - 5.3 prohibits "Provide real-time data feeds to third parties without our written consent".
  - 5.4: attribute "Mansa Markets" with a link where you display data.
  - 7.2: "Raw financial data sourced from stock exchanges remains the intellectual property of those exchanges. Mansa Markets licences this data for the purpose of providing the Service. Your right to use Market Data ... does not grant you any licence to the underlying exchange data beyond what is necessary for your permitted use."
- **Exchange licensing**: Mansa claims it licenses the data (7.2). Its methodology gives the source as "Official exchange publications and market operators". No page says Mansa holds a DSE data-vendor licence, and none says exchange licensing is the customer's job. UNKNOWN.
- **mansaapi.com ToS** (https://mansaapi.com/terms, updated 2026-06-11): no redistribution "beyond what your tier permits"; keys must not be embedded client-side; governing law Nigeria; no SLA below Institutional.

### API details for an adapter (VERIFIED from https://mansaapi.com/openapi.json, /docs, /llms.txt)
- Base URL: `https://mansaapi.com`
- Auth: `Authorization: Bearer mansa_live_sk_...`. The 401 error text in the OpenAPI spec also accepts an `X-API-Key` header or a `?api_key=` query parameter. Prefer the header.
- Envelope: `{ "success": bool, "data": ..., "meta": {...}, "pagination": {...} }`. The OpenAPI response schemas are generic (`additionalProperties: true`), so field names come only from doc examples.
- Errors: `{ "success": false, "error": { "code": "MISSING_API_KEY" | "INVALID_API_KEY", "message", ... } }`.
- Endpoints:
  - List exchanges: `GET /api/v1/markets/exchanges`
  - Symbols for an exchange: `GET /api/v1/markets/exchanges/DSE/stocks?limit<=200&offset=&sector=&sort_by=ticker|price|change_pct|volume&order=asc|desc`
  - Latest quote: `GET /api/v1/markets/exchanges/DSE/stocks/{ticker}`
  - Historical EOD: `GET /api/v1/markets/exchanges/DSE/stocks/{ticker}/history?range=1M..ALL|from=YYYY-MM-DD&to=YYYY-MM-DD&limit<=20000&order=asc|desc`
  - Search: `GET /api/v1/markets/search?q=&exchange=&limit<=50`
  - Security master: `GET /api/v1/identifiers?exchange=DSE&limit<=200&offset=`
  - DSE indices: `GET /api/v1/markets/exchanges/DSE/indices`, `/indices/DSEI`, `/indices/DSEI/history?range=1Y`
  - Health: `GET /health` (no auth)
- History response (docs example, JSE):
```json
{ "success": true,
  "data": { "exchange": "JSE", "market_id": "south-africa", "ticker": "NPN", "currency": "ZAR", "price_unit": "cents",
    "points": [ { "date": "2021-06-25", "open": 3450.0, "high": 3475.5, "low": 3431.0, "close": 3468.2, "adj_close": 3468.2, "volume": 512330 } ] },
  "meta": { "count": 1248, "first_date": "2021-06-25", "last_date": "2026-06-25", "order": "asc", "data_freshness": "daily" } }
```
  `price_unit` is `"major"` everywhere except JSE, which is in cents.
- DSE index snapshot (docs example):
```json
{ "success": true,
  "data": [ { "code": "DSEI", "name": "DSE All Share Index", "exchange": "DSE", "currency": "TZS", "country": "Tanzania",
              "value": 2875.42, "change_pct": 0.18, "updated_at": "2026-06-08T10:30:00.000Z" } ],
  "meta": { "exchange": "DSE", "count": 1, "data_freshness": "30_minutes" } }
```
- DSE index history (docs example): `data: { code, name, exchange, range, points: [ { t, trade_date, value, change_pct, change_points } ] }`, `meta: { exchange, currency, point_count, data_freshness }`.
- Identifiers row: `exchange, ticker, legal_name, isin, figi, isin_verified_at`.
- **Quote, stock list and search response fields are not documented** (no example JSON). The only hint is a short snippet on mansamarkets.com/developers: `{ "ticker": "MTNGH", "exchange": "GSE", "price": 6.53, "change_pct": 0.77, "volume": 34850000 }` plus a comment `{"stocks": [...], "count": 148}`. The methodology mentions per-row `last_updated` timestamps, and the pricing FAQ says responses carry `updated_at`. Treat these as UNKNOWN until a real response is captured.

### Reliability
- https://mansaapi.com/status (VERIFIED): "All systems operational". It lists 15 incidents between 2026-09-03 and 2026-09-26, all "Key database unavailable" or key-check errors (HTTP 5xx). Several lasted hours: 09-09 13:00 to 09-10 14:30, and 09-25 05:00 to 17:45. A fix landed on 09-27 ("moved to a dedicated paid instance"). Uptime is only shown "since 27 Sept". Authenticated request latency was shown as about 1310 ms.
- No SLA below Institutional (ToS section 7).

### Data-quality observations from Mansa's public pages (not API-verified)
- NMB on https://www.mansamarkets.com/tanzania/nmb showed TSh 2,030, "-85.39% 6M", a 52-week range of 1,770 to 17,710, and "Div Yield 21.13%". This looks like an unadjusted corporate action (Mansa says it does not back-adjust), not a real 85% loss. MyStocks shows the same drop. Check against DSE notices.
- Ticker naming looks wrong in places. Mansa lists `TCCL` as "Tanzania Cigarette Company Limited" (EODHD: Tanga Cement). It lists `MBP` as Mwalimu and `MCB` as Maendeleo (EODHD has these reversed). It lists `USL` as "Urafiki Textile Mill" (EODHD: Uchumi Supermarket). Mark these CONFLICTING_SOURCE and check against the DSE listing.
- DSE session hours: Mansa shows 09:00–15:00, EODHD 10:30–16:00, MyStocks "10:00–16:00". These conflict, so check them against DSE.

### Advertised Mansa claims vs the current site

| Claim | Current site says | Status |
|---|---|---|
| Professional tier with 33 African countries | "32 African countries" (mansamarkets.com/pricing, /developers) | NOT CONFIRMED (32, not 33) |
| 21 exchanges | "20 exchanges" (mansamarkets.com); 19 (mansaapi.com landing); 16 or 17 for history | NOT CONFIRMED |
| DSE + NSE + USE | All three on the exchange lists; USE absent from API docs | CONFIRMED (listing only) |
| 10,000 requests/day | Pro/Professional $50 = 10,000/day on both sites | CONFIRMED |
| Commercial use | mansamarkets.com: Starter has it, but its FAQ says Professional is needed; mansaapi.com: display allowed on all tiers; ToS 5.1 says "internal business purposes or personal projects" | CONFLICTING_SOURCE |
| Production use | "Use in production apps" on Professional (mansamarkets.com/developers) | CONFIRMED on that page only |
| Redistribution rights | Yes on Professional (mansamarkets.com/pricing); No on Professional, Lite on Business, Yes on Institutional (mansaapi.com/licensing) | CONFLICTING_SOURCE |
| Webhook subscriptions | Listed on Professional (mansamarkets.com); "coming soon" on Business (mansaapi.com); none in OpenAPI | NOT CONFIRMED (not in API docs) |
| ~30-minute cadence in market hours | Docs, methodology and /health (`freshness_target: 30_minutes`) | CONFIRMED |

---

## 2. MyStocks Africa (mystocks.africa)

### What it is
- An embedded-investing **Partner API**: brokerage routing, sub-accounts, USD wallets, KYC assertion, plus a read-only Market Data API. Operated by MyStocks Technologies (Pty) Ltd, Cape Town / "Mystocks Inc". VERIFIED, https://mystocks.africa/llms.txt, https://mystocks.africa/terms-of-service
- Docs: https://partners.mystocks.africa/partners/docs ; OpenAPI: https://mystocks.africa/openapi.json (150 paths).

### Plans and prices
- **No public price list for the API.** https://mystocks.africa/pricing and /developers return "Not Found". Production keys "are issued by agreement" (https://mystocks.africa/african-stock-market-api). Production starts with a "Controlled Production Pilot" that MyStocks must approve (https://partners.mystocks.africa/partners/docs/raw/going-live). Price = UNKNOWN.
- Rate-limit tiers (VERIFIED, OpenAPI `info.description`): Sandbox 300 req/min, Starter 100, Growth 500, Enterprise 2,000. Headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`; `Retry-After` on 429. No daily cap is stated.
- SLA tiers (VERIFIED, https://partners.mystocks.africa/partners/docs/raw/sla): Standard 99.5%, Professional 99.9%, Enterprise 99.95%.

### Coverage (VERIFIED, OpenAPI + https://mystocks.africa/african-stock-market-api "confirmed 2026-10-03")
- 12 exchanges: JSE, NSE, NGX, GSE, BRVM, EGX, BSE, SEM, **DSE**, **USE**, LuSE, CSE. The OpenAPI enum also lists ZSE and MSE. Exchange codes `DSE`, `NSE`, `USE`.
- Symbols are exchange-qualified with a country suffix: DSE uses `.TZ` (`NMB.TZ`, `CRDB.TZ`), Kenya `.KE` (`SCOM.KE`). The suffix for Uganda is not shown in docs (UNKNOWN; probably `.UG`).
- The public DSE page (https://mystocks.africa/exchanges/dar-es-salaam-stock-exchange) shows "25+ listed equities" and NMB.TZ at TZS 2,030.00 "as of 2026-10-07", "-87.8%" over about 88 days. This is the same unadjusted-break pattern as Mansa.

### Data types
- Quotes: `/market/quotes`, `/stocks`, `/stocks/{symbol}`, `/market/snapshot`, `/market/movers`. VERIFIED.
- Historical: `/stocks/{symbol}/candles` (recommended; `interval=15m|1h|1d|1w|1mo`, daily window at most 366 days per request) and `/market/ohlcv` (EOD; "open, high, and low fields are null until intraday data is ingested", at most 365 days per request). VERIFIED.
- History depth: "varies by exchange; a few smaller markets accumulate history forward from listing ... Inspect `historyConfidence`". DSE depth = UNKNOWN.
- Prices are "raw and unadjusted for splits and dividends"; only `adjustment=raw` is supported. VERIFIED.
- Index data (DSEI etc.): **no index endpoint in the OpenAPI path list.** UNKNOWN / likely not offered.
- Corporate actions / dividends: `/corporate-actions`, `/corporate-actions/{actionId}`, `/dividends/{symbol}/history`, `/dividends/calendar`. VERIFIED (endpoints exist; DSE coverage UNKNOWN).
- Fundamentals: `/companies/{symbol}` profile, `/companies/{symbol}/news`. Depth of financial statements = UNKNOWN.
- Security master / search: `/companies/tickers?exchange=&search=&limit<=200&cursor=`, `/stocks?exchange=DSE&search=`, `/assets`, `/market/exchanges`. VERIFIED.
- Also offers bonds/T-bills (`/bonds`), funds (`/funds`), FX (`/fx/rates`), market clock and holidays.

### Freshness
- "exchange-supplied, 15-minute-delayed feed ... The API refresh target is 900 seconds"; "real-time delivery is unavailable pending approved feed verification"; "A paid license does not remove this delay." VERIFIED, OpenAPI + https://partners.mystocks.africa/partners/docs/raw/market-data (confirmed 6 Oct 2026).
- Intraday capture is sparse: "the August 2026 partner test observed roughly three snapshots per trading day" (historical-market-data doc).
- Webhooks: yes, signed (HMAC-SHA256), for **events** (orders, dividends, market open/close, incidents), "not tick-by-tick price streaming". SSE `/stream` is available too. VERIFIED.

### Licensing / redistribution / public display (VERIFIED, https://partners.mystocks.africa/partners/docs/raw/data-licensing and .../market-data-redistribution)
- "MyStocks Africa holds market-data rights for every exchange supported by the Partner API."
- "Displaying that data inside your application to your end-users is included under the standard Partner Agreement, subject to attribution and exchange-specific terms."
- Restricted: "Reselling or redistributing raw exchange data", "Creating a data feed, data product, or market-data service", **"Sublicensing API access — all end-users must flow through MyStocks sub-accounts."**
- Caching: "Cache price data for up to 24 hours".
- Attribution: "Market data provided by **MyStocks Africa**"; NSE and JSE may require their own attribution.
- **Public website**: the redistribution doc classifies "Public website, widget, or social post" as "Public redistribution" with the required decision "Is a public-display licence required?" It also says "MyStocks API credentials do not grant a direct exchange licence ... Your executed data schedule controls." So public display is **not** granted by default. It is decided in the signed data schedule (UNKNOWN).
- Exchange terms: "Exchange price data is subject to each exchange's own data-license terms, which are incorporated into your Partner Agreement by reference."

### API details for an adapter (VERIFIED from https://mystocks.africa/openapi.json)
- Base URLs: production `https://mystocks.africa/api/v1/partner`, sandbox `https://mystocks.africa/api/sandbox/v1/partner`.
- Auth: `Authorization: Bearer <key>` or `x-api-key: <key>`. Key prefixes: `sk_sandbox_`, `pk_live_`, read-only `pk_data_`. The docs advise against shipping keys in clients and suggest proxying through your backend.
- Error shape: `{"error": {"code": "ERROR_CODE", "message": "..."}}`.
- Latest quote: `GET /market/quotes?symbol=NMB.TZ&exchange=DSE` (single, returns `data` object) or `?symbols=A.TZ,B.TZ` (batch of up to 50, returns `data[]` plus `not_found[]`) plus `meta`.
  - Quote fields: `id, symbol, name, slug, exchange, exchangeMic, currency, sector, assetType (STOCK|ETF), listingStatus (ACTIVE|SUSPENDED|DELISTED), price, usdPrice, change, changePct, open, dayHigh, dayLow, volume, previousClose, logoUrl, lastPriceUpdate, marketStatus (OPEN|CLOSED), bid (always null), ask (always null), dataFreshnessSeconds, asOf, stale, dataQuality`.
  - `asOf` = "Timestamp of the exchange observation — NOT when the API answered". `stale` = true when older than 30 minutes.
- Stock list: `GET /stocks?exchange=DSE&assetType=&sector=&search=&limit<=200&cursor=` returns `{ stocks: [...same fields...], count, totalCount, hasMore, nextCursor }`.
- Ticker list: `GET /companies/tickers?exchange=DSE` returns `{ tickers: ["NMB.TZ", ...], count, hasMore, nextCursor }`.
- Exchanges: `GET /market/exchanges` returns `data[]: { code, mic, name, country, currency, timezone, trading_hours: {open, close}, settlement: {cycle, cycleDays}, market_status }`.
- Historical candles: `GET /stocks/{symbol}/candles?interval=1d&from=YYYY-MM-DD&to=YYYY-MM-DD&adjustment=raw`. Docs example:
```json
{ "symbol": "SCOM.KE", "name": "Safaricom PLC", "exchange": "NSE", "currency": "KES", "interval": "1d", "adjustment": "raw",
  "candles": [ { "timestamp": "2026-08-07T00:00:00.000Z", "open": 16.2, "high": 16.75, "low": 16.1, "close": 16.5, "volume": 2450000, "ohlcAvailable": true, "volumeAvailable": true } ],
  "meta": { "from": "2026-01-01", "to": "2026-08-10", "count": 147, "source": "delayed_eod", "asOf": "2026-08-07T00:00:00.000Z",
            "ohlcQuality": "reported", "ohlcAvailable": true, "ohlcCoveragePct": 100, "flatCandlePct": 4.08, "volumeAvailable": true,
            "volumeCoveragePct": 100, "volumeStatus": "complete", "zeroVolumePct": 0, "qualityStatus": "complete", "qualityIssues": [],
            "recommendedChartType": "candlestick", "adjusted": false } }
```
- EOD OHLCV (older): `GET /market/ohlcv?symbol=&exchange=&timeframe=1D&from=&to=` returns `data[]: { timestamp, open, high, low, close, volume }`, `meta: { request_id, timestamp, exchange, symbol, timeframe, interval, from, to, count, ohlc_available }`.
- Health: `GET /sla`; incidents also arrive as webhooks `incident.declared` / `incident.resolved`.

### Fit concern
This API is built for brokers and neobanks that route trades. "All end-users must flow through MyStocks sub-accounts" may not fit a research-only site. Ask sales whether a data-only, public-display licence exists.

---

## 3. EODHD (EOD Historical Data, eodhd.com)

### Plans and prices (VERIFIED)
- Personal plans (https://eodhd.com/pricing): Free $0 (20 calls/day, 1 year EOD); Historian/"EOD Historical All-World" $19.99; Active trader/"EOD + Intraday All-World Extended" $29.99; Equity analyst/Fundamentals $59.99; All-in-One $99.99. Paid plans: 100,000 calls/day, 1,000 requests/minute.
- **Personal plans are personal use only**: "The packages on the pricing page are intended for personal use only as commercial use requires a more thorough approach to licensing and data use." (https://eodhd.com/financial-apis/commercial-vs-personal-license-use). The ToS says Non-Professional users may not engage in "Selling, reselling, retransmitting, redistributing, displaying, or granting access to the Information" (https://eodhd.com/financial-apis/terms-conditions).
- Commercial plans (https://eodhd.com/commercial-pricing): **Internal use $399/mo** ("Single-company use"), **Enterprise $2,499/mo**, **Custom from $399/mo**. The FAQ says: "With the internal-usage package, data may only be used inside your company. Displaying it or sharing it with people outside your company is not permitted." Signed agreement: "The Custom plan".
- **Production plan for a public web app**: Internal use ($399) explicitly does not allow it. Public display needs Enterprise or Custom, and no page says outright that Enterprise allows public display (UNKNOWN). Realistically this means talking to sales, at $399 or more per month.

### Coverage (VERIFIED, https://eodhd.com/list-of-stock-markets and https://eodhd.com/exchange/DSE)
- **DSE: yes.** Exchange code `DSE`, MIC `XDAR`, 28 active tickers, symbol format `NMB.DSE`, `CRDB.DSE`, `TBL.DSE`, and so on. Trading hours shown: Mon–Fri 10:30–16:00 (+03).
- **USE: yes.** Code `USE`, MIC `XUGA`, 18 active tickers, hours 10:00–12:00 (+03). https://eodhd.com/exchange/USE
- **NSE Kenya: not on the supported-exchange list** as fetched today (no Nairobi/XNAI entry; https://eodhd.com/exchange/XNAI returns 404). JSE is also absent from the list. Status: NOT COVERED per current page.
- Other African exchanges listed: BSE (XBOT), LUSE, EGX, GSE, RSE, SEM, MSE, XNSA (Nigeria).

### Data types
- EOD OHLCV plus `adjusted_close`: `/api/eod/{SYMBOL}`. VERIFIED. "30+ yrs" is a general claim. DSE depth = UNKNOWN.
- Live/delayed: `/api/real-time/{ticker}`, "15-20 minutes for stocks", covering "US & Global Stocks". Whether DSE has live/delayed quotes = UNKNOWN.
- Dividends and splits: `/api/div/{SYMBOL}`, `/api/splits/{SYMBOL}`. VERIFIED (endpoints exist; DSE coverage UNKNOWN).
- Fundamentals: All-in-One / Fundamentals plans. DSE coverage UNKNOWN.
- Index (DSEI / DSE All Share): UNKNOWN. No public page lists it.
- Security master: `/api/exchange-symbol-list/DSE`, `/api/exchanges-list/`, `/api/search/{query}`. VERIFIED.
- Webhooks: none found. WebSocket real-time is US/forex/crypto only.

### Freshness and limits
- EOD after close; live endpoint delayed 15–20 minutes (where covered). Limits: paid 100,000 calls/day and 1,000 requests/minute. Cost per request: 1 call for EOD/live, 5 for intraday/news, 10 for fundamentals, 100+ for bulk. Over the limit you get HTTP 402. VERIFIED, https://eodhd.com/financial-apis/api-limits

### Provenance warning
- The footer on every page says: "We are not using exchanges data feeds for the pricing data, we are using OTC, peer to peer trades and trading platforms over 100+ sources, we are aggregating our data feeds via VWAP method." The commercial FAQ says: "End-of-day and delayed data comes through direct contracts with 60+ exchanges". CONFLICTING_SOURCE. Which applies to DSE = UNKNOWN. This matters for the "every number has a source" rule.
- EODHD says it "report[s] all commercial users of exchange data to the relevant exchanges", so exchange-side professional-user reporting applies to commercial use.

### API details for an adapter (VERIFIED from EODHD doc pages)
- Base URL: `https://eodhd.com/api`
- Auth: query parameter `api_token=...` (no header option documented). The default format is CSV, so always send `fmt=json`. Note that a query-string token can end up in logs, so redact it.
- Historical EOD: `GET /api/eod/NMB.DSE?api_token=&fmt=json&from=YYYY-MM-DD&to=YYYY-MM-DD&period=d|w|m&order=a|d` returns
```json
[ { "date": "2024-01-02", "open": 295.05, "high": 297.28, "low": 295.05, "close": 297.04, "adjusted_close": 277.9465, "volume": 4458400 } ]
```
  Unknown tickers give HTTP 404 and are still billed. Misspelled `fmt`/`period`/`order` values silently fall back to defaults.
- Latest quote: `GET /api/real-time/NMB.DSE?api_token=&fmt=json` (extra symbols via `s=`) returns
```json
{ "code": "AAPL.US", "timestamp": 1783974420, "gmtoffset": 0, "open": 317.015, "high": 323.45, "low": 315.78,
  "close": 317.31, "volume": 43138419, "previousClose": 315.32, "change": 1.99, "change_p": 0.6311 }
```
- Symbols for an exchange: `GET /api/exchange-symbol-list/DSE?api_token=&fmt=json` returns `[ { "Code", "Name", "Country", "Exchange", "Currency", "Type", "Isin" } ]`. No pagination.
- Exchanges: `GET /api/exchanges-list/?api_token=` returns `[ { "Name", "Code", "OperatingMIC", "Country", "Currency", "CountryISO2", "CountryISO3" } ]`.
- Search: `GET /api/search/{query}?api_token=&fmt=json&exchange=DSE&limit=` returns `[ { "Code", "Exchange", "Name", "Type", "Country", "Currency", "ISIN", "isPrimary", "previousClose", "previousCloseDate" } ]`.
- Dividends: `GET /api/div/NMB.DSE?api_token=&fmt=json` returns `[ { date, declarationDate, recordDate, paymentDate, period, value, unadjustedValue, currency } ]`. Splits: `GET /api/splits/{SYMBOL}` returns `[ { date, split: "2.000000/1.000000" } ]`.

### Reliability
- Uptime page: uptime.eodhistoricaldata.com (linked from the API-limits page; not opened).

---

## Comparison table

| | Mansa | MyStocks Africa | EODHD |
|---|---|---|---|
| DSE covered | Yes (`DSE`) | Yes (`DSE`, symbols `.TZ`) | Yes (`DSE`/XDAR, 28 tickers, `NMB.DSE`) |
| NSE Kenya | Yes (`NSE`) | Yes (`NSE`, `.KE`) | **No** (not on list) |
| USE Uganda | Listed (`USE`); not in API docs | Yes (`USE`) | Yes (`USE`/XUGA, 18 tickers) |
| Freshness | ~30 min target in market hours; EOD after close | 15-min delayed (900 s), pull-based | EOD; delayed 15–20 min where covered (DSE unknown) |
| EOD history | Pro+; DSE depth unknown; unadjusted | Candles ≤366 days/request; depth unknown; unadjusted | 30+ yrs claimed; DSE depth unknown; `adjusted_close` provided |
| DSE index (DSEI) | Yes (TSI, DSEI, BI, IA, CS); added 2026-06 | No endpoint found | Unknown |
| Dividends / corp actions | API "NGX only" | Endpoints exist; DSE unknown | `/div`, `/splits`; DSE unknown |
| T-bills/bonds TZ | Tanzania not in yields coverage list | `/bonds` exists; TZ unknown | Not for TZ (unknown) |
| Security master / search | `/identifiers`, `/markets/search` | `/companies/tickers`, `/stocks?search=` | `/exchange-symbol-list`, `/search` |
| Auth | Bearer header (also X-API-Key, ?api_key) | Bearer or `x-api-key` header | `api_token` query param |
| Limits | 10k/day (Pro $50) | 100–2,000 req/min by tier | 100k calls/day, 1k req/min |
| Webhooks | None in API docs (conflicting marketing) | Yes, signed, events only | None |
| Price for production | $50 (Pro) or $200 (Business), licensing unclear | Not public (agreement + pilot approval) | Personal plans not allowed; $399 internal use forbids display; Enterprise $2,499 / Custom needed |
| Public website display | Allowed on all tiers per mansaapi.com/licensing; ToS 5.1 says "internal business purposes" | Not by default; "Public redistribution" decided in data schedule | Not on personal or internal-use plans |
| Exchange licence | Mansa says it licenses; no DSE contract named | Claims "full market-data rights" for every exchange; exchange terms flow down | Says it reports commercial users to exchanges; footer says prices not from exchange feeds |
| Reliability evidence | 15 auth-DB incidents in Sept 2026; uptime shown since 27 Sept | SLA tiers 99.5–99.95%; `/sla` endpoint | Uptime page exists (not opened) |

---

## Unknowns that need an account or a sales answer

### Mansa
1. Which licence text governs: mansaapi.com/licensing (Professional = no redistribution) or mansamarkets.com/pricing (Professional = redistribution rights)? Get it in writing for public display of DSE prices on AfriEdge.
2. Does ToS 5.1 ("solely for your internal business purposes or personal projects") prohibit a public research website?
3. Can AfriEdge store daily closes in its own Postgres indefinitely for its own calculations, or is that beyond the 7-day cache limit (= "redistribution")?
4. Does Mansa hold a data licence from DSE (and NSE, USE)? Which document? Or is the source scraped "official exchange publications"? Who is liable if DSE objects?
5. DSE per-stock OHLCV history: start date, gaps, whether `open/high/low` are populated or close-only.
6. DSEI/TSI history depth (the endpoint was added 2026-06-08).
7. Exact JSON field names for `/stocks/{ticker}`, `/stocks` list and `/search` (not documented).
8. DSE dividends / corporate actions via API (docs say NGX only).
9. Tanzania T-bill/bond yields (not in the published coverage list).
10. Webhooks: available on which tier, and when?
11. Per-minute rate limit; SLA or uptime history before 27 Sept 2026.
12. Ticker/name errors (TCCL, MBP/MCB, USL) and the NMB price break. How do they correct them, and do they publish corporate-action adjustments?

### MyStocks Africa
1. Price of a data-only licence. Is a data-only partner (no brokerage, no sub-accounts) accepted at all?
2. Is public display on an unauthenticated website allowed? Which data schedule, and at what cost?
3. DSE history depth per symbol (`historyConfidence`), and OHLC vs close-only for DSE.
4. Any DSE index (DSEI) data.
5. DSE corporate-action and dividend coverage.
6. Daily call caps per tier; production approval timeline; jurisdiction and contracting entity.
7. Long-term storage rights beyond the 24-hour cache.

### EODHD
1. Does the Enterprise ($2,499) or a Custom plan permit public display of DSE/USE prices on a website, and at what price for only DSE + USE?
2. DSE data source: direct DSE contract or aggregated "OTC/peer-to-peer ... VWAP"? Needed for provenance.
3. DSE history start date and completeness; whether DSE is in the live/delayed feed; whether DSEI index is carried.
4. DSE dividends/splits and fundamentals coverage.
5. Any plan to add NSE Kenya (currently not listed).
6. Exchange-fee pass-through for DSE/USE professional users.

### Cross-provider data checks to do once any key exists (all UNTESTED)
- NMB price break (about 17,500 down to about 2,030 TZS in 2026). Confirm against a DSE corporate-action notice and decide on our own adjustment logic. All three providers serve raw prices (EODHD also gives `adjusted_close`).
- DSE trading hours: four different values seen (09:00–15:00, 10:00–16:00, 10:30–16:00, 10:00–14:00). Use DSE's own site.
- Ticker-to-name mapping (TCCL, MBP, MCB, USL, TTP) against the DSE listing.
