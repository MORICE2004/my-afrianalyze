<p align="center"><img src="apps/web/public/logo.png" alt="AfriEdge" width="220"></p>

# AfriEdge

**African Financial Intelligence.** Research on listed African companies in which every figure can be traced
to the page of the document it came from, every calculation is done by deterministic code, and anything that
cannot be verified says so instead of showing a number.

Status: **not yet in production.** What is certified and what is not is in
[`docs/PRODUCTION_CERTIFICATION.md`](docs/PRODUCTION_CERTIFICATION.md). Research and education only; nothing
here is investment advice.

## Who it is for

Investors, analysts and students who want to understand an African listed company from its own audited
accounts, with the arithmetic shown, rather than from a summary they cannot check.

## What it covers today

| Area | Today | Notes |
|---|---|---|
| Tanzania, DSE equities | **NMB Bank Plc** and **CRDB Bank Plc**: five years of audited statements, bank ratios, valuation, model view, risks, PDF report | Both reports are drafts until a named reviewer approves them |
| DSE prices and DSEI index | Ten years of daily closes from the DSE's public data | Licensing for public display is under review |
| Bank of Tanzania | Treasury bond yield curve; Central Bank Rate | |
| NBS Tanzania | Headline CPI | |
| Portfolios | Sign in, save portfolios, value them from the latest stored close | TZS only; no optimisation or stress tests yet |
| Kenya (NSE, CBK, KNBS), Uganda (USE, BoU, UBOS) | **Coming.** Supported by the design, not integrated | Shown as COMING on `/health` and `/markets`; no data is shown |
| World Bank, IMF, ECB, UN Comtrade | **Coming.** Their APIs were tested and answer | No loaders yet |
| AI research copilot | **Not built** | Will answer only from the stored, cited report |
| Technical analysis on the report | **Not built** | Thin trading makes most indicators unreliable; rules are written (section 74 of the product context) |

Every source and its live state: the **All sources** table on `/health`
([`config/source_registry.json`](config/source_registry.json)).

## How the evidence works

```
Source document → raw file (SHA-256) → two independent readers must agree → tie checks
  → stored figure with its page, period, currency and unit → deterministic calculation → page with a status
```

- Figures from annual reports are read by independent extractors (Camelot, Docling, PDF text); a value is
  stored only when at least two agree, and only if it appears on the page it cites.
- Every figure shown carries a status: `VERIFIED`, `PARTIALLY_VERIFIED`, `CONFLICTING_SOURCE`,
  `INSUFFICIENT_DATA`, `BLOCKED` or `STALE`. A figure without a verified source is never shown as a number.
- Money is `Decimal` in Python and `NUMERIC` in PostgreSQL, and goes over the wire as an exact string.

## How valuation works

Banks are valued as banks: residual income, justified price-to-book and a multi-stage dividend discount
model, with bear, base and bull scenarios and a sensitivity table. The cost of equity is built from a dated,
sourced risk-free rate, equity risk premium, country risk premium and an industry beta (Damodaran's
emerging-market bank beta), each shown with its source. The model view (undervalued / fairly valued /
overvalued) follows a written rule; BUY/HOLD/SELL labels sit behind `SHOW_TRADE_LABELS`. Open methodology
questions are listed at the top of [`docs/KNOWN_GAPS.md`](docs/KNOWN_GAPS.md).

## How portfolio analysis works

A signed-in user saves holdings (security and quantity). The API values each holding from the latest stored
close, calculates weights and gains in `Decimal`, and marks a holding with no stored price as
`INSUFFICIENT_DATA` rather than zero. Each portfolio is visible only to its owner (tested at the API and in
the browser).

## Architecture

```
Browser ──HTTPS──▶ Next.js on Vercel (apps/web) ──HTTPS──▶ FastAPI on Render (apps/api) ──TLS──▶ PostgreSQL on Neon
                     │ httpOnly session cookie, same-origin checks          ▲
                     └ CSP, security headers                              │
Workstation: extraction pipelines (Docling, Camelot) ─────────────────────┘
GitHub Actions: CI on every push; weekday refresh of prices and macro data
```

Why each piece, and what was deliberately left out (Redis, workers):
[`docs/PRODUCTION_ARCHITECTURE.md`](docs/PRODUCTION_ARCHITECTURE.md).

## Development

Windows / PowerShell, from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m uvicorn apps.api.main:app --port 8000
cd apps\web; npm ci; npm run dev
```

Loading the data, running each test suite and every command: [`CLAUDE.md`](CLAUDE.md) ("Project map and
commands"). Environment variables: [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md).

## Production deployment

[`docs/DEPLOYMENT_RUNBOOK.md`](docs/DEPLOYMENT_RUNBOOK.md) (Neon, Render, Vercel; smoke tests; rollback) and
[`docs/DATABASE_RUNBOOK.md`](docs/DATABASE_RUNBOOK.md) (migrations, backup, restore).

## Current limitations

The honest list, with evidence, is [`docs/KNOWN_GAPS.md`](docs/KNOWN_GAPS.md) and
[`docs/AFRIEDGE_PRODUCTION_AUDIT.md`](docs/AFRIEDGE_PRODUCTION_AUDIT.md). The largest today: not deployed;
both reports unreviewed; two companies only; no password reset (needs an email service); no copilot.

## History

This repository was called My AfriAnalyze until 2026-09-25. A separate "AfriEdge" line of work on `master`
was audited and found to show invented figures; it is archived as branch `afriedge-legacy-archive` and only
its logo and name were carried over ([`docs/REPOSITORY_RECONCILIATION.md`](docs/REPOSITORY_RECONCILIATION.md),
[`docs/LEGACY_AFRIEDGE_FORENSIC_REPORT.md`](docs/LEGACY_AFRIEDGE_FORENSIC_REPORT.md)).
