# Deployment runbook

Updated 2026-10-07. Architecture and why: `docs/PRODUCTION_ARCHITECTURE.md`. Variables:
`docs/ENVIRONMENT.md`. Database: `docs/DATABASE_RUNBOOK.md`. Status of each part:
`docs/PRODUCTION_CERTIFICATION.md`.

## Where things stand

| Part | State |
|---|---|
| Web app on Vercel | **Protected previews** only (project `morice2004s-projects/web`, Root Directory `apps/web`, CLI deploys, no Git integration). No production deployment: it needs an API address, which needs Render. See `docs/PROGRESS.md` for the latest preview |
| API on Render | Not created. `render.yaml` and `Dockerfile.api` are ready; CI builds and starts the image on every push |
| Postgres on Neon | Not created |
| Research reports | Runs RA-20261007-001 (NMB) and -002 (CRDB) executed, both `PARTIAL`, both unapproved drafts: production returns 403 |
| Scheduled refresh | Workflow ready; inert until `PRODUCTION_DATABASE_URL` exists and `master` carries it |

## Decisions only the owner can make (before a public launch)

1. **Approve the two research runs** under your own name (two commands each: `pipelines.review submit`,
   then `approve`; `pipelines.review list` shows the current ids). Settle the cost-of-equity question at the
   top of `docs/KNOWN_GAPS.md` first. Today NMB's view changes with the cost-of-equity treatment, so the
   report shows it as **Inconclusive** with no trade label; CRDB is Undervalued under all three treatments.
2. **Publishing DSE figures on a public site** (`DSE_PUBLIC_DISPLAY`). The Data Vending Policy v1.2 forbids
   redistributing website data without a written licence (cl. 23.1); the data is classified `RESTRICTED`.
   Recommended: `false` until the DSE grants a licence (`docs/COMPLIANCE_NOTES.md`). The raw files are
   never served (403) either way.
3. **The annual-report PDFs.** Every figure links to its page in our stored copy. Hosting copies is an open
   rights question; until it is settled the production API has no PDFs and those links say "missing on disk".
4. **Paid plans.** Render's free API sleeps after 15 idle minutes (about a minute to wake). `starter` avoids it.
5. **Make `master` match the canonical branch.** Decided 2026-09-25: `m3-crdb-report` is canonical and
   `master` holds the legacy AfriEdge line (archived as `afriedge-legacy-archive`). `master` is still the
   repository's default branch, and GitHub runs **scheduled workflows only from the default branch**, so the
   weekday data refresh cannot run until the canonical code is on `master`. The plan in
   `docs/REPOSITORY_RECONCILIATION.md`: a merge into `master` that keeps the canonical side, so history stays
   readable. Not done yet because it rewrites what `master` shows; it needs the owner's go-ahead.

## Steps (in this order)

Nothing here needs a secret to pass through chat or git. Where a password is involved, it goes from one
dashboard straight into another.

### 1. Database (Neon)

Create the project in Frankfurt and copy the connection string (`docs/DATABASE_RUNBOOK.md` section 1).
Then load it from your machine (section 2 there).

### 2. API (Render)

1. Render dashboard → **New → Blueprint** → pick `MORICE2004/my-afrianalyze`, branch `m3-crdb-report`
   (or `master` once merged). Render reads `render.yaml`.
2. It asks for the `sync: false` values:
   - `DATABASE_URL`: paste the Neon connection string.
   - `CORS_ORIGINS`: the web app's address, e.g. `https://web-morice2004s-projects.vercel.app` (exactly,
     no trailing slash; several separated by commas).
   - `ALLOWED_HOSTS`: the API's own host, e.g. `afrianalyze-api.onrender.com`.
   - `SENTRY_DSN`: leave empty unless a Sentry project exists (`docs/OBSERVABILITY.md`).
   - `DSE_PUBLIC_DISPLAY`: **your decision** (decision 2 below). `false` until a DSE licence is held: DSE
     prices and everything computed from them show as `BLOCKED`. The API refuses to start if it is unset.
   - `INTERNAL_PROXY_SECRET`: a random value of 32+ characters. Generate it in a password manager (or
     Render's "Generate" button), put the **same** value in Vercel (step 3), and nowhere else.
   - `ANTHROPIC_API_KEY`: optional. Created at console.anthropic.com → API keys. Empty: the copilot
     answers `AI_UNAVAILABLE`. Usage is billed by Anthropic (a paid service: your decision).
   - `POSTHOG_API_KEY` and `ANALYTICS_SALT`: optional, together (`docs/OBSERVABILITY.md`).
3. Wait for the deploy. The health check is `/ready`: it stays red (503) until the database is loaded,
   which is correct.
4. Check: `https://<api>/ready` is 200; `https://<api>/docs` is 404 (off in production);
   `https://<api>/api/v1/securities?q=nmb` lists NMB.
5. Check that rate limits are per visitor (after step 3, so requests come through the web app): on the
   sign-in page, try 11 sign-ins within a minute from your computer, each with a **different** made-up email
   (the same email would hit the per-account lock after 5 instead). The 11th must be refused with a 429
   "too many requests" message. Straight away, try once from your phone **on mobile data** (a different
   address) with another made-up email: it must say the email or password is wrong, not "too many". If the phone is
   also refused, the API is seeing one address for everyone: check `INTERNAL_PROXY_SECRET` is identical on
   Render and Vercel, then try clearing `CLIENT_IP_HEADER` on Render.

### 3. Web (Vercel)

1. Vercel → project `web` → Settings → Environment Variables, **Production** only:
   `NEXT_PUBLIC_API_URL` = `https://<api>`, `API_URL_INTERNAL` = the same, and `INTERNAL_PROXY_SECRET` =
   the value set on Render (mark it Sensitive). Without it every signed-in visitor shares one rate limit.
2. Set the function region once: Vercel → project `web` → Settings → Functions → Region = **Frankfurt
   (fra1)**. Found 2026-10-07: the project default is `iad1` (US East) and `regions` in `apps/web/vercel.json`
   is not applied, so without this every server-side render would cross the Atlantic to reach the API.
   Until it is set, pass the region on each deploy (as the previews do).
3. Deploy: from the repo root, `vercel deploy --prod --regions fra1`. The root `.vercelignore` uploads only
   `apps/web` (not `data/`, `.env` files or the Python code; checked on the preview's file list). The build
   refuses to run without an `https://` API address, so a misconfigured production deploy fails instead of
   shipping a broken site.
4. Deployment Protection stays on until decisions 1 to 3 are made. Turning it off for production is the
   deliberate launch step.

### 4. Scheduled data refresh (GitHub)

1. GitHub → repository Settings → Environments → **New environment** `production`. Optionally add yourself
   as a required reviewer and limit it to the `master` branch.
2. In that environment, **Add secret** `PRODUCTION_DATABASE_URL` = the Neon connection string.
3. Actions → **Refresh data** → *Run workflow* once, and check `/health`: DSE prices and BoT should show today.

### 5. Smoke test (against production)

| Check | Expect |
|---|---|
| `/` | 200, search box, AfriEdge logo |
| `/login`, create an account, save a portfolio | values shown from the latest close; a second account cannot see it |
| Search "NMB", open it | report page (or the 403 "not reviewed" message until approved) |
| A figure's source link | page of the PDF, or "missing on disk" until decision 3 |
| `/health` | sources listed with ages; stale ones marked |
| `/robots.txt` | `Disallow: /` until `NEXT_PUBLIC_ALLOW_INDEXING=true` |
| Browser console | no errors, no CORS failures |
| 375 px wide | no sideways scrolling |

### 6. Domain (when there is one)

Plan: `app.<domain>` for the web app (Vercel → Domains) and `api.<domain>` for the API (Render → Custom
Domains), each a CNAME at your DNS provider. Then update, in this order: Render `ALLOWED_HOSTS` (add
`api.<domain>`), Render `CORS_ORIGINS` (add `https://app.<domain>`), Vercel `NEXT_PUBLIC_API_URL`,
`API_URL_INTERNAL` and `NEXT_PUBLIC_SITE_URL`, then redeploy the web app (the API address is compiled into
it). Keep the old addresses in the lists until the new ones answer. No domain is registered yet.

## Rolling back

- **Web:** Vercel → Deployments → the previous production deployment → *Promote* (or `vercel rollback`).
- **API:** Render → Deploys → previous deploy → *Rollback*.
- **Database:** see `docs/DATABASE_RUNBOOK.md` section 3. Code rollbacks never touch the data.

## Recovering the environment

Everything needed to recreate the setup is in the repo (`render.yaml`, `Dockerfile.api`,
`apps/web/vercel.json`, `.env.example`, this file) except the values: the Neon connection string (Neon
dashboard) and, if used, the Sentry DSN (Sentry dashboard).
