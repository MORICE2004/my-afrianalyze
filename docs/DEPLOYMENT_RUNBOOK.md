# Deployment runbook

Updated 2026-09-25. Architecture and why: `docs/PRODUCTION_ARCHITECTURE.md`. Variables:
`docs/ENVIRONMENT.md`. Database: `docs/DATABASE_RUNBOOK.md`. Status of each part:
`docs/PRODUCTION_CERTIFICATION.md`.

## Where things stand

| Part | State |
|---|---|
| Web app on Vercel | Deployed as a **protected preview** (project `morice2004s-projects/web`, Root Directory `apps/web`, CLI deploys, no Git integration). No production deployment is live: three production attempts on 2026-09-24 failed with Error |
| API on Render | Not created. `render.yaml` and `Dockerfile.api` are ready; CI builds and starts the image on every push |
| Postgres on Neon | Not created |
| Research reports | Both are unapproved drafts, so in production they return 403 |

## Decisions only the owner can make (before a public launch)

1. **Approve the two research runs** under your own name (two commands each: `pipelines.review submit`,
   then `approve`; `pipelines.review list` shows the current ids). Settle the cost-of-equity question at the
   top of `docs/KNOWN_GAPS.md` first: it decides whether NMB says BUY or SELL.
2. **Publishing DSE figures on a public site.** You accepted the Data Vending Policy risk for use; public
   display is the thing the policy restricts (`docs/COMPLIANCE_NOTES.md`). The raw price files are never
   served (403).
3. **The annual-report PDFs.** Every figure links to its page in our stored copy. Hosting copies is an open
   rights question; until it is settled the production API has no PDFs and those links say "missing on disk".
4. **Paid plans.** Render's free API sleeps after 15 idle minutes (about a minute to wake). `starter` avoids it.
5. **Which branch is the product.** `master` holds a separate "AfriEdge" line of work with invented market
   figures and a hardcoded sign-in (`docs/AFRIEDGE_PRODUCTION_AUDIT.md`). Deploy from `m3-crdb-report`, or
   merge it into `master` first; do not deploy `master` as it stands.

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
   - `SENTRY_DSN`: leave empty unless a Sentry project exists.
3. Wait for the deploy. The health check is `/ready`: it stays red (503) until the database is loaded,
   which is correct.
4. Check: `https://<api>/ready` is 200; `https://<api>/docs` is 404 (off in production);
   `https://<api>/api/v1/securities?q=nmb` lists NMB.

### 3. Web (Vercel)

1. Vercel → project `web` → Settings → Environment Variables, **Production** only:
   `NEXT_PUBLIC_API_URL` = `https://<api>`, and `API_URL_INTERNAL` = the same.
2. Deploy: from the repo root, `vercel deploy --prod`. The build refuses to run without an `https://` API
   address, so a misconfigured production deploy fails instead of shipping a broken site.
3. Deployment Protection stays on until decisions 1 to 3 are made. Turning it off for production is the
   deliberate launch step.

### 4. Smoke test (against production)

| Check | Expect |
|---|---|
| `/` | 200, search box |
| Search "NMB", open it | report page (or the 403 "not reviewed" message until approved) |
| A figure's source link | page of the PDF, or "missing on disk" until decision 3 |
| `/health` | sources listed with ages; stale ones marked |
| `/robots.txt` | `Disallow: /` until `NEXT_PUBLIC_ALLOW_INDEXING=true` |
| Browser console | no errors, no CORS failures |
| 375 px wide | no sideways scrolling |

## Rolling back

- **Web:** Vercel → Deployments → the previous production deployment → *Promote* (or `vercel rollback`).
- **API:** Render → Deploys → previous deploy → *Rollback*.
- **Database:** see `docs/DATABASE_RUNBOOK.md` section 3. Code rollbacks never touch the data.

## Recovering the environment

Everything needed to recreate the setup is in the repo (`render.yaml`, `Dockerfile.api`,
`apps/web/vercel.json`, `.env.example`, this file) except the values: the Neon connection string (Neon
dashboard) and, if used, the Sentry DSN (Sentry dashboard).
