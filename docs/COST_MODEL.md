# Cost model

Rewritten 2026-09-25. The previous version assumed LLM extraction of annual reports (GPT-4o, $0.25 to
$0.50 per report) and an AWS database. Neither is how the product works: figures are extracted by Docling
and Camelot on the owner's machine, and **the v1 code path makes no LLM calls at all**. Every figure is
computed by deterministic Python.

## Monthly running cost at launch

| Item | Plan | Cost | Limit that matters |
|---|---|---|---|
| Web (Vercel) | Hobby | $0 | Hobby is for non-commercial use (Vercel's terms). A commercial launch needs Pro, currently listed at $20 per member per month; check before launch |
| API (Render) | Free | $0 | Sleeps after 15 idle minutes; about a minute to wake. Starter (paid) removes that |
| Database (Neon) | Free | $0 | 0.5 GB (we use about 1.3 MB); 100 CU-hours per month; 6-hour restore window |
| Error reporting (Sentry) | Developer (free) | $0 | Event quota; errors only, no tracing |
| CI (GitHub Actions) | Free minutes | $0 | A full run takes a few minutes; public repositories are free, private ones have a monthly allowance |
| Extraction (Docling, Camelot) | Owner's machine | electricity | About 5 minutes per annual report, a few times a year per bank |
| LLM calls | none | $0 | None in the v1 code path |

The prices above were checked against provider pages on 2026-09-25 for Render and Neon
(`docs/PRODUCTION_ARCHITECTURE.md`, sources). Vercel's and Sentry's were not re-checked today; confirm on
their pricing pages before relying on them.

## What would change the cost

- **Always-on API** (no cold starts): Render Starter, a paid plan.
- **Scheduled data refresh**: free as a GitHub Actions schedule; a Render cron job is paid.
- **A research copilot**: the first LLM cost. It must answer from the stored report payload only and be
  rate-limited per user, and it needs sign-in first. Not built.
- **Hosting the annual-report PDFs**: 175 MB today; object storage costs cents, but the rights question
  comes first.
- **Adding exchanges** (NSE, USE): same infrastructure; the cost is extraction time and licensing.

## Guards against surprise costs

- No tracing in Sentry (`traces_sample_rate=0.0`).
- The report and PDF endpoints are rate-limited per client.
- Nothing calls an LLM, so there is no token spend to run away.
