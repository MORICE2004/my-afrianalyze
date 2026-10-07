# Security model

Updated 2026-10-07 (second pass). What the system protects, how, and what was checked. This is the v1 code
path on branch `m3-crdb-report`; `master` holds the quarantined legacy line (`docs/AFRIEDGE_PRODUCTION_AUDIT.md`,
finding M-3) and is not covered here.

## What there is to protect

- **Integrity of published figures.** The main risk to users is a wrong number presented as sourced.
  Protected by the pipeline rules (two readers must agree, tie checks, statuses), by human review (in
  PRODUCTION an unpublished report is 403 and a published one is served from its frozen, hashed snapshot),
  and by the copilot's grounding check (below).
- **Secrets.** The database password; `INTERNAL_PROXY_SECRET`; optionally the Anthropic key, PostHog key and
  analytics salt. All live in the hosts' dashboards (Render, Vercel, GitHub environment secrets). None is
  in git (gitleaks over the full history in CI), and none is needed in chat.
- **Accounts and saved portfolios** (email, Argon2id hash, holdings). No payments, no other personal data.
- **Unpublished drafts.** 403 in production, Vercel Deployment Protection on the preview, `robots.txt`
  disallows indexing.

## Sign-in and isolation

- Passwords: Argon2id (`argon2-cffi` defaults, RFC 9106 profile), 12 to 128 characters. A wrong password
  and an unknown email get the same message; an unknown email is checked against a dummy hash so timing
  does not reveal which accounts exist.
- Sessions: a 256-bit random token; the database stores only its SHA-256. 7-day expiry; logout revokes.
  httpOnly, SameSite=Lax cookie (Secure in production) on the web app's own domain; page JavaScript cannot
  read it. The web server forwards it to the API as a Bearer token, so the API's CORS stays narrow.
- CSRF: every state-changing route on the web app requires a same-site `Origin` (403 otherwise; tested
  with a forged origin and with none).
- IDOR: every portfolio query filters on the session's user; another user's id answers 404 (API test and a
  two-account browser test).
- Brute force: 10 sign-in/sign-up requests per minute per visitor address, and **per email** 5 failed
  sign-ins in 15 minutes lock that email for the rest of the window, from any address (added 2026-10-07).

## Rate limiting and the visitor's address (fixed 2026-10-07)

The second pass found two flaws, both fixed in commit `450bb0f`:

1. **Spoofable address.** Uvicorn trusted the leftmost `X-Forwarded-For`, which any visitor can set, so
   a script could rotate fake addresses and never hit a limit. Now uvicorn runs with `--no-proxy-headers`
   and `client_ip()` in `apps/api/main.py` decides, in order: the web server's `x-afriedge-client-ip`
   **only** when it carries the right `x-afriedge-proxy-key` (constant-time compare against
   `INTERNAL_PROXY_SECRET`); else the header named by `CLIENT_IP_HEADER` (`cf-connecting-ip` on Render,
   which Cloudflare overwrites); else the address `TRUSTED_PROXY_HOPS` from the right of `X-Forwarded-For`;
   else the socket.
2. **One shared bucket.** Every signed-in request reaches the API from Vercel's servers, so all visitors
   shared Vercel's addresses and one heavy user could lock everyone out. The web server now passes the
   visitor's address (from Vercel's own `x-real-ip`) with the shared secret, so limits apply per visitor.

Limits: 30 report/PDF builds per visitor per minute; 10 auth POSTs per minute; 20 copilot questions per
account per day. All in memory per process: they reset on restart and are not shared across instances. With
one free Render instance that is enough; a second instance would need a shared store.

## AI copilot

- Answers only from a context the server builds from stored, validated data (source facts, calculated
  values, statuses). The model may not compute or change a figure (CLAUDE.md rule 2).
- **Grounding check, deterministic:** every number in the answer must match a number in the context, or
  the answer is withheld and the user sees `UNGROUNDED`. Tested against fabricated numbers, run ids and
  year-like strings (`tests/v1/test_copilot.py`, 22 tests).
- Any provider failure (no key, timeout, refusal, malformed output) returns `AI_UNAVAILABLE` and no text.
- Requires sign-in; 20 questions per account per day; the question text is never logged or sent to analytics.
- Not tested against the real provider: no `ANTHROPIC_API_KEY` exists on this machine.

## Checks (2026-10-07 unless dated)

| Area | Check | Result |
|---|---|---|
| SQL injection | ORM with bound values throughout; the only textual SQL is `SELECT 1` | none found |
| XSS | React escaping; `dangerouslySetInnerHTML` used 0 times in `apps/web/src`; copilot text rendered as text | none found |
| SSRF | The API never fetches a URL a user supplies; only the offline pipelines fetch, from fixed addresses | not applicable |
| Path traversal | `/api/v1/sources/{id}/file` takes an integer id, reads the path from the database, resolves it and refuses anything outside the store; exchange price files 403 before any disk check | tested (`tests/v1/test_api.py`) |
| Error disclosure | Database errors go to the server log only; `/docs` and `/openapi.json` off in PRODUCTION | tested |
| CORS | Listed origins only; GET/POST; `Content-Type`. PRODUCTION refuses `*` and localhost | tested |
| Host header | `TrustedHostMiddleware` with `ALLOWED_HOSTS` | set it in production |
| Rate-limit bypass | Forged `X-Forwarded-For` and forged `x-afriedge-client-ip` without the key are ignored | tested (`test_production_config.py`; per-email lock in `test_auth_and_portfolios.py`) |
| Start-up guards | PRODUCTION refuses SQLite, `*`/localhost CORS, a missing `DSE_PUBLIC_DISPLAY`, an `INTERNAL_PROXY_SECRET` under 32 characters, PostHog without a salt | tested |
| Secrets in git | gitleaks over the full history in CI; local scan 2026-10-07 | clean |
| Secrets in the image | `.dockerignore`; CI fails if `.env`, `.venv`, `data` or `.git` are in the image | tested in CI |
| Container user | `app` (uid 10001), not root | tested in CI |
| Dependencies | `pip-audit` (requirements-api.txt) and `npm audit --omit=dev`, in CI and locally | clean 2026-10-07 |
| Transport | HSTS, `X-Frame-Options: DENY`, `nosniff`, referrer policy, CSP (`apps/web/vercel.json`, `next.config.ts`) | set |
| Telemetry privacy | Sentry scrubber; PostHog allowlist, salted ids, no GeoIP | tested (`test_telemetry.py`, 9) |

## Known gaps

| Gap | Severity | Note |
|---|---|---|
| No password reset, email verification or account deletion | P1 before public sign-ups | Needs an email service (owner's account) |
| Rate limits are per process, in memory | P2 | Fine for one instance; a shared store (e.g. Postgres or Redis) before scaling out |
| CSP allows inline scripts | P2 | Next.js needs them; a nonce policy would make every page render per request |
| `CLIENT_IP_HEADER=cf-connecting-ip` on Render is an assumption | P2 | Verify on the first deploy (`docs/DEPLOYMENT_RUNBOOK.md`); if absent the API falls back to `TRUSTED_PROXY_HOPS` |
| Legacy code in the repo (`agents/`, `connectors/`, `apps/api/tasks`) | P3 | Not imported by the live API, so not reachable over HTTP |
| Independent review | open | The 2026-10-07 pass was by the same assistant that wrote the code; a second reviewer (`/security-review` or a person) has not looked |
