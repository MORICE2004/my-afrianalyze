# Cost model

Rewritten 2026-09-25; copilot cost added 2026-10-07. The previous version assumed LLM extraction of annual reports (GPT-4o, $0.25 to
$0.50 per report) and an AWS database. Neither is how the product works: figures are extracted by Docling
and Camelot on the owner's machine. Every figure is computed by deterministic Python. The only LLM call is
the optional research copilot, which explains stored figures and never computes one.

## Monthly running cost at launch

| Item | Plan | Cost | Limit that matters |
|---|---|---|---|
| Web (Vercel) | Hobby | $0 | Hobby is for non-commercial use (Vercel's terms). A commercial launch needs Pro, currently listed at $20 per member per month; check before launch |
| API (Render) | Free | $0 | Sleeps after 15 idle minutes; about a minute to wake. Starter (paid) removes that |
| Database (Neon) | Free | $0 | 0.5 GB (we use about 1.3 MB); 100 CU-hours per month; 6-hour restore window |
| Error reporting (Sentry) | Developer (free) | $0 | Event quota; errors only, no tracing |
| CI (GitHub Actions) | Free minutes | $0 | A full run takes a few minutes; public repositories are free, private ones have a monthly allowance |
| Extraction (Docling, Camelot) | Owner's machine | electricity | About 5 minutes per annual report, a few times a year per bank |
| Research copilot (Anthropic, `claude-opus-5-5`) | pay per use; off without a key | $0 until a key is set | Estimate below; capped at 20 questions per account per day |
| Product analytics (PostHog) | Free tier | $0 | Event quota; server-side events only |

The prices above were checked against provider pages on 2026-09-25 for Render and Neon
(`docs/PRODUCTION_ARCHITECTURE.md`, sources). Vercel's and Sentry's were not re-checked today; confirm on
their pricing pages before relying on them.

## What would change the cost

- **Always-on API** (no cold starts): Render Starter, a paid plan.
- **Scheduled data refresh**: free as a GitHub Actions schedule; a Render cron job is paid.
- **The research copilot** (built 2026-10-07; inert without `ANTHROPIC_API_KEY`). **Estimate, not measured**
  (it has never run against the real model): NMB's context is about 81,000 characters, roughly 20,000 tokens.
  At the published Opus 5.5 prices ($4 per million input tokens, $20 per million output, $0.20 per million
  for cached reads; cache writes cost more than plain input), one question costs roughly **$0.03-0.07** when
  the context is cached (asked within a few minutes of another question on the same company) and roughly
  **$0.10-0.16** when not, mostly output and thinking. At the cap of 20 questions per account per day, one
  very active account costs at most about $3 a day. Measure the real figure from the first week of usage in
  the Anthropic console and set a monthly spend limit there.
- **Hosting the annual-report PDFs**: 175 MB today; object storage costs cents, but the rights question
  comes first.
- **Adding exchanges** (NSE, USE): same infrastructure; the cost is extraction time and licensing.

## Guards against surprise costs

- No tracing in Sentry (`traces_sample_rate=0.0`).
- The report and PDF endpoints are rate-limited per client.
- The copilot requires sign-in, is capped at 20 questions per account per day, and has a bounded output
  (`max_tokens` 8,000). Set a monthly spend limit in the Anthropic console as the final stop.
