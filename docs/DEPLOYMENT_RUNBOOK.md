# Deployment

Written 2026-09-20 for a public launch. The web app is ready for Vercel. The rest is not a matter of
running one command, and this file says exactly why and what is left.

Read it with `docs/COMPLIANCE_NOTES.md` (the open legal questions) and `docs/KNOWN_GAPS.md`.

## The shape of the thing

| Part | What it is | Where it can go |
|---|---|---|
| `apps/web` | Next.js 16 | **Vercel** (ready, see below) |
| `apps/api` | FastAPI, Python | **Not Vercel.** Needs a host that runs a long-lived Python process with a disk: Render, Fly.io, Railway |
| Database | SQLite locally, 1.3 MB | Managed PostgreSQL. Migrations exist (`alembic`); never yet run against PostgreSQL |
| `data/raw` | 179 MB, of which 175 MB is 12 annual-report PDFs | Object storage, or the API host's disk. See "The PDFs" below |

Vercel alone gets you the front end and nothing behind it, so every figure would read "not available".

## Done already

- `apps/web/vercel.json`: framework, Frankfurt region (closest Vercel region to Tanzania), and security
  headers (HSTS, `X-Frame-Options: DENY`, `nosniff`, referrer policy).
- `next.config.ts` no longer forces `output: "standalone"` on Vercel, which builds its own way. The
  Docker image still gets the standalone bundle. Both builds verified.

## Before anything goes public

**1. Approve the two research runs.** Nothing else matters until this is done: in production the reports
return HTTP 403 and the site has no product on it. Verified today:

```
403  /api/v1/reports/DSE:NMB    "has not been reviewed and published yet"
403  /api/v1/reports/DSE:CRDB   "has not been reviewed and published yet"
```

Approving is yours to do, under your own name:

A run goes draft to in_review to published, so each one takes two commands:

```powershell
.venv\Scripts\python -m pipelines.review submit  RA-20260919-001 --by "Your Full Name" --note "..."
.venv\Scripts\python -m pipelines.review approve RA-20260919-001 --by "Your Full Name" --note "..."
.venv\Scripts\python -m pipelines.review submit  RA-20260919-003 --by "Your Full Name" --note "..."
.venv\Scripts\python -m pipelines.review approve RA-20260919-003 --by "Your Full Name" --note "..."
```

(`pipelines.review list` shows the current run ids, which change when a report is rebuilt.)

Before you sign them, settle the cost of equity question at the top of `docs/KNOWN_GAPS.md`. Today both
reports say BUY, CRDB on a 98% upside that the report itself flags as needing review, and on a different
but equally defensible beta NMB is a SELL instead.

**2. Decide on publishing DSE market data openly.** You accepted the Data Vending Policy risk to build
the product (`docs/COMPLIANCE_NOTES.md`). A public website showing DSE prices is a different and larger
exposure than using them on your own machine, because redistribution is the thing the policy actually
restricts. The price files themselves are already withheld (HTTP 403, they are never served on), so the
question is only about the figures shown on the page.

**3. Decide about the annual-report PDFs.** Every figure links to the page it came from, which is the
best thing about this product. That link serves our stored copy of the bank's annual report. Publishing
those copies is listed as an open legal question in `docs/COMPLIANCE_NOTES.md`. Three ways:

- **Host them** (175 MB). Keeps the promise intact. Resolve the rights question first.
- **Link to the bank instead.** No copies republished, but the stored `url` is the investor-relations
  landing page, not the file, so "page 324" becomes "somewhere in this report". The product loses its
  edge. Getting direct PDF links per year would restore it.
- **Keep sources for signed-in users only.** Needs accounts, which are not built.

**4. The licensing question you have already answered once.** Your position of 2026-09-19 is that target
prices and BUY/HOLD/SELL labels need no licence. Publishing to the public is when that position starts
to matter. It is recorded as your position, not as legal advice.

## Steps, once those are settled

### 1. Database

Create a managed PostgreSQL (Render, Neon, Supabase). Then, from your machine:

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://USER:PASSWORD@HOST/DBNAME"
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m pipelines.load_security_master
.venv\Scripts\python -m pipelines.macro
# then per bank, the four commands in CLAUDE.md, and the price and index importers
```

This has never been run against PostgreSQL. Expect the money columns to need checking first: they are
`NUMERIC` there and `ExactDecimal` here, which is the point, but it is untested.

### 2. API

Deploy `apps/api` to Render or Fly from the repo. Environment:

| Variable | Value |
|---|---|
| `APP_ENV` | `PRODUCTION` |
| `DATABASE_URL` | the PostgreSQL URL |
| `CORS_ORIGINS` | your Vercel domain, exactly |
| `SHOW_TRADE_LABELS` | `true` or `false` |

It needs a persistent disk if you host the PDFs, and enough memory for the report build.

Never put these in git. Set them in the host's own settings.

### 3. Web

In Vercel: **New Project → import the repository → set Root Directory to `apps/web`.** Then:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | the public API address |
| `API_URL_INTERNAL` | the same address |

Deploy, then check: search finds NMB, a report opens, a figure links to its source, `/health` shows the
sources, and the disclaimer is on every page.

### 4. Afterwards

- Point a domain at it.
- Turn on Vercel's deployment protection for preview builds so drafts are not public.
- Watch the first `pipelines.macro` run against PostgreSQL.
- `docs/INCIDENT_RESPONSE.md` covers what to do if a figure turns out to be wrong in public.

## What I did not do

I did not deploy. Three reasons, all of them yours to lift: the reports are unapproved drafts, so a
public site would have no product on it; publishing DSE data and the banks' PDFs are open questions;
and signing in to Vercel and a database host is yours to do, because I do not enter credentials.
