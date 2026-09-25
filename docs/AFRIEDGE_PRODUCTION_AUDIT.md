# Production audit (2026-09-25)

Done against the production-readiness directive the owner supplied on 2026-09-25, which calls the
product "AfriEdge". In this repository the product is **My AfriAnalyze**; the name is kept until the owner
decides otherwise. No earlier report was taken as evidence. Everything below was checked in the code, in
CI, against the Vercel project or against the live sources, on the date above.

Severity: **P0** production blocker, **P1** financial or data reliability, **P2** major UX or operations,
**P3** nice to have, **P4** future feature. Status: `FIXED` (with the evidence), `OPEN`, `BLOCKED`
(needs something outside the repo), `DECISION` (the owner's call).

## Summary

- **The repository has two diverging products.** Branch `m3-crdb-report` (this audit) is the verified
  Tanzania work: NMB and CRDB reports from the banks' own annual reports, DSE prices and a sourced
  valuation. Branch `master` has 5 commits since the split (2026-09-17 to 09-24) that rebrand it
  "AfriEdge" and certify it `READY_WITH_LIMITATIONS`. That certification does not survive inspection
  (M-1 to M-5).
- **On this branch, 16 production problems were found and fixed today**, including a CI that had never run,
  a health check that called a broken API healthy, and a Docker image that would have shipped `.env`.
- **Nothing is deployed to production.** The web app is a protected Vercel preview. No API host or
  database exists yet; creating them needs the owner's accounts.
- **The live code contains no fake data.** A search for mock, fake, dummy, placeholder, synthetic, sample,
  TODO, FIXME, NotImplemented and hardcoded values over the v1 code path (`apps/api/main.py`,
  `packages/analysis`, `report`, `core`, `database`, `pipelines`, `apps/web/src`) found only input
  placeholders and comments.

## The v1 code path, measured

Importing the live API and every pipeline loads 4 of the 22 packages under `packages/` (`analysis`,
`core`, `database`, `report`) and no code from `agents/`, `connectors/`, `models/`, `apps/api/routers`,
`apps/api/tasks` or `apps/api/core`. Those are legacy: not reachable over HTTP, not part of any figure
shown. They are listed in the master audit and kept pending a clean-up decision (O-11).

## Findings on `master` (not changed; read-only inspection)

| ID | Finding | Where | Sev. | Evidence | Status |
|---|---|---|---|---|---|
| M-1 | Two lines of work on one repository; `master` does not contain the verified bank reports, prices or valuation, and `m3-crdb-report` does not contain the AfriEdge UI | `git merge-base` = `193c2ba`; master +5, branch +27 | P0 | `git rev-list --count` | DECISION |
| M-2 | Invented market figures in the page source: an intraday index series (2,140 to 2,145.32) and T-bill yields 3.50% to 6.80%; the health page shows fixed text ("Healthy", "Last sync: 2 mins ago", "LLM Service Degraded, 1200ms") | `master:apps/web/src/app/markets/page.tsx:9-22`, `fixed-income/page.tsx:9-12`, `health/page.tsx:14-36` | P0 | `git show origin/master:<file>`; the health page seen live on the other working copy at `localhost:3000` | OPEN on master |
| M-3 | "Tenant isolation" is a hardcoded user: `get_current_user()` returns `id=1, analyst@afriedge.com` for every request, and the router is mounted. Anyone could read, change or delete user 1's portfolios | `master:apps/api/routers/portfolios.py:8-14`, `main.py:40` | P0 security | `git show` | OPEN on master |
| M-4 | The Uganda connector returns made-up prices (`Decimal("31.50") if ticker == "STAN" else Decimal("30.50")`). This branch deleted that connector for this reason on 2026-09-19 | `master:connectors/use/connector.py:66-74` | P0 | `git show` | OPEN on master |
| M-5 | `master:docs/PRODUCTION_CERTIFICATION.md` marks CI "REMOTE, passes all 81 test cases"; GitHub had recorded **zero** workflow runs for the repository before today. It marks the USE connector, auth and the copilot "Real: YES" | `master:docs/PRODUCTION_CERTIFICATION.md` | P0 (false claims) | `gh run list` returned `[]` before 2026-09-25 | OPEN on master |
| M-6 | Three `Production` deployments to Vercel on 2026-09-24 ended in Error, so nothing is live in production. The preview from 2026-09-20 remains the only Ready build | Vercel project `web` | P2 | `vercel ls web` | noted |

**Recommendation:** deploy from `m3-crdb-report`. Before merging it into `master`, decide what of the
AfriEdge work to keep (the name and logo are easy to carry over); none of M-2 to M-4 should be merged.

## Findings on this branch, fixed today

| ID | Finding | Sev. | Fix | Verification |
|---|---|---|---|---|
| F-1 | CI triggered only on `master`, where no work happens: it had never run | P0 | Runs on every push; five jobs | First run 2026-09-25 (#36139306403): 3 of 5 passed; the 2 failures were real (F-10, and a test reading CI's DATABASE_URL) and were fixed; rerun #36139810755: 5 of 5 passed |
| F-2 | `/health` returned HTTP 200 when the database was down, and echoed the raw database error (host, user) | P0 | New `/ready`: 503 `DATABASE_UNAVAILABLE` / `DATABASE_NOT_SEEDED`, else `APP_HEALTHY` / `DEGRADED`; errors logged, not returned | `test_unreachable_database_is_503_and_its_error_stays_on_the_server`, `test_empty_database_is_not_ready`; CI checks 503 on a migrated, unseeded Postgres |
| F-3 | `Dockerfile.api` did `COPY . /app/` with no `.dockerignore`: `.env`, `.venv`, `.vercel`, the local database and `node_modules` would go into the image | P0 | Copies named folders only; `.dockerignore`; non-root user | CI "API Docker image" job checks the image contents and user |
| F-4 | The API image installed the full extraction stack (Docling, Camelot, PyTorch: several GB) to serve pages | P1 | `requirements-api.txt` (149 MB) | Installed into an empty virtualenv; served the report (NMB fair value 2,354.07, same as locally), a 21 KB PDF, markets and fixed income; PyTorch, Docling, Camelot not loaded |
| F-5 | Nothing stopped PRODUCTION running on SQLite or with localhost/`*` CORS | P1 | Settings refuse to start | 5 tests in `test_production_config.py` |
| F-6 | `postgres://` URLs (Render, Heroku) are rejected by SQLAlchemy 2 | P1 | Rewritten to `postgresql://` | `test_render_style_postgres_url_is_accepted`; CI starts the image with a `postgres://` URL |
| F-7 | A `%` in the database password (URL-encoded) would break Alembic (configparser interpolation) | P2 | Escaped in `alembic/env.py` | read |
| F-8 | With `NEXT_PUBLIC_API_URL` unset, the web app silently used `http://localhost:8000`, so a production site would call each visitor's own machine | P0 | A Vercel production build fails unless it is `https://` | `VERCEL_ENV=production next build` exits 1 with the message; normal build passes |
| F-9 | `psycopg2` was listed (unpinned) but not installed on the workstation, so it could not load a Postgres database | P1 | Pinned 2.9.13, installed | Settings tests pass with a Postgres URL in the environment |
| F-10 | The local type check passed only because of files Next had generated earlier; a clean checkout had 4 type errors | P2 | CI runs `next typegen` first | Reproduced locally (4 errors), fixed (0) |
| F-11 | "Money is NUMERIC on Postgres" had never been tested on Postgres | P1 | Postgres round-trip test in CI | `test_money_round_trips_exactly_on_postgres` passed in CI run #36139306403 |
| F-12 | `.env.example` listed variables the code does not read (`SECRET_KEY`, Redis, Supabase, S3, LLM keys) and defaulted to PRODUCTION | P2 | Rewritten from the code | `docs/ENVIRONMENT.md` |
| F-13 | No `robots.txt`: unpublished drafts could be indexed | P2 | Disallow all until `NEXT_PUBLIC_ALLOW_INDEXING=true` | `/robots.txt` in the build output |
| F-14 | `OBSERVABILITY.md`, `COST_MODEL.md`, `ANALYTICS.md` described legacy or non-existent systems (LLM extraction, a `telemetry.ts` that does not exist) | P2 | Rewritten or marked superseded | read against the code |
| F-15 | Interactive API docs exposed in production | P3 | Off in PRODUCTION | CI: `/docs` is 404 in PRODUCTION mode |
| F-16 | No limit on report/PDF builds | P2 | 30 per client per minute per process | `test_report_requests_are_limited_per_client` |

## Open

| ID | Finding | Sev. | Status | What unblocks it |
|---|---|---|---|---|
| O-1 | No API host and no Postgres exist | P0 | BLOCKED | Owner creates Neon and Render accounts (`docs/DEPLOYMENT_RUNBOOK.md`) |
| O-2 | Both research runs are unapproved drafts, so production shows no report (403) | P0 | DECISION | Owner reviews and approves under their name |
| O-3 | Cost-of-equity treatment (`subtract_default_spread` gives 12.94%, about 2.2 points over the 10-year TZS yield) and CRDB's 25.9% loan-growth extrapolation are unsettled; NMB flips BUY/SELL on the beta choice | P1 | DECISION | `docs/KNOWN_GAPS.md` first section |
| O-4 | Prices and index are STALE (loaded 2026-09-20); nothing refreshes them on a schedule | P1 | DECISION | GitHub Actions schedule (DB secret in GitHub) or Render cron (paid): `docs/PRODUCTION_ARCHITECTURE.md` |
| O-5 | BoT Central Bank Rate loader fails on the latest MPC statement | P1 | OPEN | Fix the parser |
| O-6 | Review history exists only in the database; `data/` (the source of everything else) is not backed up; dump and restore untested | P1 | OPEN | `docs/DATABASE_RUNBOOK.md` section 4 |
| O-7 | DSE redistribution on a public site; republishing the banks' PDFs | P0 for public launch | `LICENSE_REVIEW_REQUIRED` | Owner decision (`docs/COMPLIANCE_NOTES.md`) |
| O-8 | Kenya and Uganda: sources reachable, no loaders; outside v1 scope (CLAUDE.md) | P4 | DECISION | Scope change by the owner |
| O-9 | Sentry backend wired but not connected; frontend Sentry and PostHog missing | P2 | BLOCKED | Owner creates the projects |
| O-10 | No Content-Security-Policy | P2 | OPEN | Needs the per-environment API origin and a browser check |
| O-11 | 18 legacy packages, `agents/`, `connectors/`, legacy routers and tasks in the repo | P3 | DECISION | Delete or archive (deleting is the owner's call) |
| O-12 | Not built in v1 (the directive assumes them): sign-in, AI copilot, technical indicators on the report, portfolio construction, optimisation, stress tests, unit trusts, T-bills | P4 | MISSING | Roadmap milestones; each needs its data first |
| O-13 | Playwright browser checks are not in CI (they need the loaded data) | P2 | OPEN | A seeded CI database, or run against the deployed site |
| O-14 | Vercel Hobby is for non-commercial use | P2 | DECISION | Pro plan before a commercial launch |
| O-15 | KNBS and UBOS certificates fail verification | P3 | BLOCKED | Their servers; not bypassed |
