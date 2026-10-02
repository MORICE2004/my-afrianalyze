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

Since 2026-10-02 there are user accounts (email and password) and saved portfolios. No payments and no
other personal data.

## Sign-in and isolation

- Passwords: Argon2id (`argon2-cffi` defaults, the RFC 9106 profile), 12 to 128 characters. A wrong password
  and an unknown email get the same message, and an unknown email is checked against a dummy hash so timing
  does not reveal which accounts exist.
- Sessions: a 256-bit random token; the database stores only its SHA-256. Expires after 7 days; logout
  revokes it. The browser holds it in an httpOnly, SameSite=Lax cookie (Secure in production) on the web
  app's own domain; page JavaScript cannot read it (checked in the browser). The web server forwards it to
  the API as a Bearer token, so the API's CORS policy stays narrow (no Authorization header, no PUT/DELETE).
- CSRF: every state-changing route on the web app requires a same-site Origin header (403 otherwise, tested
  with a forged origin and with none).
- IDOR: every portfolio query filters on the session's user; another user's id answers 404. Tested at the
  API (`tests/v1/test_auth_and_portfolios.py`) and in the browser (`apps/web/e2e/smoke.spec.ts`).
- Abuse: 10 sign-in attempts per minute per client.

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
| CSP allows inline scripts | P2 | `next.config.ts` sets a CSP (only this site and the API; no framing, plugins, base or form hijack). Next.js needs inline scripts; a nonce-based policy would make every page render per request |
| Rate limit is per process and trusts the load balancer's forwarded address | P2 | Enough to stop one script hammering one server; not a defence against a distributed attack. Render's edge is the real protection |
| No password reset, email verification or account deletion | P1 before public sign-ups | Needs an email service (owner's account) |
| Legacy code in the repo (`agents/`, `connectors/`, `apps/api/routers`, `apps/api/tasks`) | P3 | Not imported by the live API, so not reachable over HTTP. The copy of `apps/api/routers/portfolios.py` on `master` has a hardcoded user and must not be mounted (finding M-3) |
| Security review by a second tool | open | `/security-review` or equivalent has not been run on this branch |
