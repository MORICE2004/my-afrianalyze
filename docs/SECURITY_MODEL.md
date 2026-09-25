# Security model

Updated 2026-09-25. What the system protects, how, and what was checked. This is the v1 code path on
branch `m3-crdb-report`; `master` has different code and its own problems (see
`docs/AFRIEDGE_PRODUCTION_AUDIT.md`, finding M-3).

## What there is to protect

- **Integrity of published figures.** The main risk to users is a wrong number presented as sourced.
  Protected by the pipeline rules (two readers must agree, tie checks, statuses) and by human review: in
  PRODUCTION an unpublished report is 403.
- **The database password.** The only real secret. It lives in Render's settings and, while loading, in a
  shell variable on the owner's machine.
- **Unpublished drafts.** Kept out of view by the 403 above, by Vercel Deployment Protection on the preview,
  and by `robots.txt` disallowing indexing.

There are no user accounts, no personal data and no payments. The API has no endpoint that writes to the
database. That removes most of the usual attack surface (sign-in, sessions, CSRF, IDOR), and is the
reason it is not built yet: sign-in arrives with the first feature that stores something per person.

## Checks (2026-09-25)

| Area | Check | Result |
|---|---|---|
| SQL injection | Every query goes through the SQLAlchemy ORM with bound values; the only textual SQL is `SELECT 1`. Search ranks in Python | none found |
| XSS | React escaping; `dangerouslySetInnerHTML` used 0 times in `apps/web/src` | none found |
| SSRF | The API never fetches a URL; only the offline pipelines do, from fixed source addresses | not applicable |
| Path traversal | `/api/v1/sources/{id}/file` takes an integer id, reads the path from the database, resolves it and refuses anything outside the repo; exchange price files are refused (403) | `test_source_files_are_served_and_paths_are_checked`, `test_the_share_price_is_shown_only_with_the_source_it_came_from` (`tests/v1/test_api.py`) |
| Error disclosure | Database errors go to the server log, not the response (`test_unreachable_database_is_503_and_its_error_stays_on_the_server`); FastAPI returns a bare 500 on unhandled errors; `/docs` and `/openapi.json` are off in PRODUCTION | tested |
| CORS | Only listed origins; methods GET/POST; header `Content-Type`. PRODUCTION refuses `*` and localhost at start-up | tested |
| Host header | `TrustedHostMiddleware` with `ALLOWED_HOSTS` | set it in production |
| Abuse of expensive endpoints | 30 report/PDF builds per client per minute, per server process | tested; in-memory, resets on restart |
| Secrets in git | Regex scan of the full history (27 commits) found none; gitleaks runs over the full history in CI | clean |
| Secrets in the image | Dockerfile copies named folders only, plus `.dockerignore`; CI fails if `.env`, `.venv`, `data` or `.git` appear in the image | tested in CI |
| Container user | Runs as `app` (uid 10001), not root | tested in CI |
| Dependencies | `pip-audit` on `requirements-api.txt`: no known vulnerabilities. `npm audit --omit=dev`: 0 vulnerabilities. Both run in CI | clean on 2026-09-25 |
| Transport | HSTS, `X-Frame-Options: DENY`, `nosniff`, referrer policy set in `apps/web/vercel.json`; Neon and Render are TLS-only | set |
| Error reporting privacy | Sentry: `send_default_pii=False`, request bodies never sent, no tracing | configured, not yet connected |

## Known gaps

| Gap | Severity | Note |
|---|---|---|
| No Content-Security-Policy | P2 | Needs the API origin per environment, and a browser check that Next's hydration scripts still run. Not done blind |
| Rate limit is per process and trusts the load balancer's forwarded address | P2 | Enough to stop one script hammering one server; not a defence against a distributed attack. Render's edge is the real protection |
| No sign-in | not applicable today | Required before any per-user feature (saved portfolios answer 401) |
| Legacy code in the repo (`agents/`, `connectors/`, `apps/api/routers`, `apps/api/tasks`) | P3 | Not imported by the live API, so not reachable over HTTP. The copy of `apps/api/routers/portfolios.py` on `master` has a hardcoded user and must not be mounted (finding M-3) |
| Security review by a second tool | open | `/security-review` or equivalent has not been run on this branch |
