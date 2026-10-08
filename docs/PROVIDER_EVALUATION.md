# Market-data provider evaluation

Date: 2026-10-08. Read from each provider's own website, documentation and machine-readable API spec. No account
was created, no key used, nothing accepted: **no provider's live API has been called**, so every adapter below is
`UNTESTED`. Full notes with every URL: `docs/PROVIDER_EVALUATION_RAW.md` (researched by a subagent; the licensing
claims that decide the outcome were re-read by hand the same day).

## Decision needed from the owner

None of the three gives AfriEdge clear, written permission to show prices on a public website at a known price.
Each needs a written answer from sales before any money is spent. Until then AfriEdge keeps using the DSE's own
published end-of-day files (owner decision of 2026-09-19), whose public display is itself switched by
`DSE_PUBLIC_DISPLAY` because the DSE Data Vending Policy restricts redistribution.

| | Mansa API | MyStocks Africa | EODHD |
|---|---|---|---|
| DSE / NSE / USE | listed / listed / listed (USE absent from API docs) | yes / yes / yes | yes / **no** / yes |
| Freshness | ~30 min in market hours, EOD after close | 15-minute delayed | EOD; delayed quotes for DSE unknown |
| DSE history depth | unknown | unknown | unknown |
| DSE indices (DSEI, BI, IA, CS) | yes (added 2026-06) | no endpoint | unknown |
| Split-adjusted | no ("as published") | no | `adjusted_close` given |
| Price for a public site | $50 Pro or $200 Business, terms unclear | not public; partner agreement and pilot | Enterprise $2,499 or Custom (personal plans and the $399 internal plan forbid display) |
| Public display | "Display ... inside your own app ... or website" allowed on every tier, **but** caching "up to 7 days" and "building a stored copy of our datasets" is redistribution; the Mansa Markets terms limit use to "internal business purposes or personal projects" | a public website is "public redistribution", decided in a signed data schedule; end users must go through MyStocks sub-accounts | not on personal or internal-use plans |
| Reliability seen | 15 key-database incidents in September 2026 | SLA 99.5% to 99.95% by tier | not checked |
| Provenance concern | sources "official exchange publications"; no DSE licence named | claims rights for every exchange it covers | its own pages disagree on whether prices come from exchange feeds or are aggregated |

Questions to ask before choosing (each provider's list is in the raw note): written permission to display DSE
prices publicly on AfriEdge; whether storing every daily close permanently (AfriEdge's design, for beta and charts)
is allowed; the DSE history start date; whether the provider holds a DSE data licence; the price.

## Also checked: the DSE's own "live" endpoint

`https://dse.co.tz/api/get/live/market/prices` returns a price and change per share with **no time at all**
(checked at 11:28 in Dar es Salaam on 2026-10-08). A price without a time cannot be labelled current or delayed
honestly, so it is not used.

## What is built so providers can be switched

- `packages/market_data/provider.py`: the interface (quotes, history, index data, security search, exchange
  metadata, market status, corporate actions), each adapter declaring what it supports.
- Adapters: `dse_public` (in use), `mansa` and `eodhd` (written against the documented fields, `UNTESTED`).
  MyStocks is not written: its partner model (end users as MyStocks sub-accounts) does not fit a research site
  unless sales says otherwise.
- `packages/market_data/registry.py` and `config/market_data.json`: the order providers are asked in, overridable
  with `MARKET_DATA_PRIORITY`. A provider is used only when its key is set **and** its licensing word is not
  `LICENSE_REVIEW_REQUIRED`; a key alone switches nothing on.
- Every stored bar keeps the document it came from, whose `publisher` names the provider.
- `pipelines/reconcile_prices.py`: compares the stored closes with every other usable provider and records each
  comparison (`price_reconciliations`); beyond 0.5% a day is `CONFLICTING_SOURCE`, never averaged.
- The web app never calls a provider; it reads only AfriEdge's API.

## To switch to a provider once its terms are accepted

1. Put its key in the API host's dashboard (`MANSA_API_KEY` or `EODHD_API_KEY`), never in git or chat.
2. Change its `licensing` in `config/market_data.json` from `LICENSE_REVIEW_REQUIRED` to the licence held, with the
   agreement's reference in `note`, and commit that.
3. Set `MARKET_DATA_PRIORITY` (for example `mansa,dse_public`).
4. Run `python -m pipelines.reconcile_prices` and read the result before the first scheduled refresh uses it.
