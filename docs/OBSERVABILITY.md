# Observability

Rewritten 2026-10-07. What exists for the v1 code path, and what is wired but not yet connected to an account.
Code: `packages/core/telemetry.py` (one module for both Sentry and PostHog, so the privacy rules live in one
place and are tested in `tests/v1/test_telemetry.py`).

| Signal | Where | Status |
|---|---|---|
| Is the API up and able to serve? | `GET /ready`: 200 `APP_HEALTHY` or `DEGRADED` (stale sources listed); 503 `DATABASE_UNAVAILABLE` or `DATABASE_NOT_SEEDED`. Render's health check points here | REAL, tested |
| How fresh is each data source? | `GET /health` and the `/health` page: every source with its last success, last attempt, age, limit and licensing word | REAL, tested |
| Did the scheduled refresh work? | `refresh-data.yml` fails the run (red in GitHub Actions, email to the repo owner) when any share fails or a revision is held back; the failed attempt is written to `/health` (`dse_prices` → `partial`, failing shares named) while the last-success time stays true | REAL, tested (`test_a_source_outage_is_recorded_and_nothing_is_lost`); the workflow itself has not run against a production database |
| Server errors | Python logging to stdout (Render collects it). Database errors are logged with the traceback there, never returned to the caller | REAL |
| Error reporting (Sentry, API) | `telemetry.init_sentry()` when `SENTRY_DSN` is set | **wired, not connected** (no Sentry project). `BLOCKED` on the owner creating one |
| Error reporting (Sentry, web) | none | MISSING. The web app's server routes only forward to the API, whose errors are reported; browser errors are not |
| Product analytics (PostHog) | `telemetry.track()` from the API | **wired, not connected** (no PostHog project). `BLOCKED` on the owner creating one |
| CI | GitHub Actions on every push (`.github/workflows/ci.yml`, 5 jobs) | REAL |

## Sentry: what is sent

Errors only (`traces_sample_rate=0`). `send_default_pii=False`, `max_request_body_size="never"`, and a
`before_send` scrubber (`telemetry.scrub_event`) that removes request bodies, cookies, query strings,
environment, the user block, and the values of `Authorization`, `Cookie`, `Set-Cookie`, `X-API-Key` and
`Proxy-Authorization`. The **release** is the deployed git commit (`RENDER_GIT_COMMIT` on Render,
`VERCEL_GIT_COMMIT_SHA` on Vercel), so an error points at the code that raised it.

### To connect it (owner, about five minutes)

1. Create a project at sentry.io (platform Python → FastAPI). Region: EU if offered.
2. Put the DSN in Render's `SENTRY_DSN` (dashboard, not git, not chat).
3. Prove it end to end with the controlled test error, from your machine:
   ```powershell
   $env:SENTRY_DSN = "<copy from the Sentry project page>"; .venv\Scripts\python -m pipelines.sentry_check; Remove-Item Env:SENTRY_DSN
   ```
   It prints an event id. Find that event in Sentry and check: present; no request body, cookie, auth
   header or user. Until this is done, "Sentry works" is not a claim this project can make.

## PostHog: the event schema

Events are sent **from the API, not the browser**: no tracking script, no cookie, nothing for an ad blocker
to see, and no consent banner needed for analytics cookies. Only events and properties on the allowlist below
leave the server; anything else is dropped before sending (tested). A person is a salted SHA-256 of their user
id (`ANALYTICS_SALT`), never an email; anonymous events create no person profile; GeoIP is off; host is the EU
region by default. No portfolio holdings, amounts, copilot question text or document content is ever a property.

| Event | Sent when | Properties allowed |
|---|---|---|
| `signup` | an account is created | none |
| `login` | a sign-in succeeds | none |
| `report_viewed` | a company's report is served (the company page and all its tabs, valuation included, are one report request) | `security_id`, `frozen` (served from a published snapshot) |
| `company_viewed`, `valuation_viewed` | allowlisted, **not sent yet**: the tabs switch in the browser, and analytics is server-side only | `security_id` |
| `report_pdf_downloaded` | the PDF is built | `security_id` |
| `research_started` / `research_completed` | a research run executes | `security_id`; `execution_state` on completion |
| `portfolio_created` | a portfolio is saved | `holdings_count` |
| `portfolio_analysis_started` | risk analysis is run | `holdings_count` |
| `copilot_question` | the copilot answers | `security_id`, `status` (`ANSWERED`, `UNGROUNDED`, `AI_UNAVAILABLE`, ...) |

A failure to send is logged and never breaks the request (tested).

### To connect it (owner)

1. Create a project at posthog.com, **EU Cloud**. Copy the project API key (it starts `phc_`).
2. In Render: `POSTHOG_API_KEY` = that key, and `ANALYTICS_SALT` = a random value of 16+ characters (e.g.
   from a password manager's generator). Production refuses to start with a key and no salt.
3. Check: sign in on the site, open NMB, and see `login` and `report_viewed` arrive in PostHog's
   activity view with no email or IP on them.

Changing the salt makes every person look new; pick it once.
