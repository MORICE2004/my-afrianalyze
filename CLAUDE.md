# My AfriAnalyze: Rules for Claude Code

An African investment research and portfolio intelligence platform. AI explains. Deterministic code calculates. Every number has a source.

## Read before any work

1. `docs/PRODUCT_CONTEXT.md`: the full vision (sections 1 to 69) and addendum (70 to 82). Source of truth.
2. `docs/ROADMAP.md`: milestones with acceptance checks.
3. `docs/MY_AFRIANALYZE_MASTER_AUDIT.md`: the current truth about the repo (create it first if it doesn't exist).
4. `docs/KNOWN_GAPS.md` and `docs/PROGRESS.md`.

Never trust an earlier "complete", "live" or "production ready" claim. Verify.

## Non-negotiable rules

1. **No fabricated data.** If it can't be verified, show a status (`VERIFIED`, `PARTIALLY_VERIFIED`, `INSUFFICIENT_DATA`, `BLOCKED`, `STALE`, `CONFLICTING_SOURCE`) and no number.
2. **Pipeline order:** Source → Validated Data → Deterministic Calculation → Research Context → AI Interpretation. An LLM never computes or overwrites a financial figure.
3. **Provenance:** every value carries amount, currency, unit, period, source (URL/document, page, table), retrieval time and validation status.
4. **Money:** `Decimal` in Python, `NUMERIC` in Postgres. No floats for money. FX conversion is explicit (rate, timestamp, source).
5. **Time:** store observation date, publication date and availability date. No look-ahead.
6. **Thin markets:** zero-volume days are recorded. Beta and technical indicators follow section 74.
7. **Recommendations:** trade labels sit behind `SHOW_TRADE_LABELS` (on since the owner's decision of 2026-09-19 that no licence is needed; can be switched off). Every view is traceable and shows uncertainty. Disclaimers everywhere (section 71).
8. **Human review** before anything is published (section 72).
9. **Data rights:** respect source terms. Never bypass logins, paywalls, CAPTCHAs or robots rules (section 73).
10. **Secrets** live in environment variables or Secret Manager. Never in git. No PII or raw documents in PostHog, Sentry or logs.

## Status words (use exactly)

`REAL`, `MOCKED`, `PARTIAL`, `BLOCKED`, `UNTESTED`, `BROKEN`, `MISSING`. Never say "production ready" without the certification matrix in section 64.

## How to work

For every major change: audit → plan → implement → test → adversarial test → verify (including in the browser) → document → commit → report.

- Check `git status`, branch and recent commits before big changes. Don't discard uncommitted work.
- One branch per milestone or P0 item. Small, clear commits.
- Use subagents for independent work, then verify their output yourself.
- After the audit and after each P0 item: commit, update `docs/PROGRESS.md` and `docs/KNOWN_GAPS.md`, post a plain-language report. Keep going unless a decision is needed.
- Ask the owner before: legal or licensing text, paid services, using a source with unclear terms, deleting data, changing the stack, or a valuation method choice with material impact.
- Say plainly when something is broken, over-engineered, impossible, or when data doesn't exist.

## Scope right now

Version 1 is Tanzania only: DSE equities (NMB and CRDB first), Bank of Tanzania T-bills and bonds, verifiable unit trust funds, TZS only (section 77). No payment code until the owner says so.

## Environment

- The owner's machine runs Windows. Use PowerShell-friendly commands or Docker.
- The owner isn't a professional programmer. Explain results simply.

## Project map and commands

Current truth: `docs/MY_AFRIANALYZE_MASTER_AUDIT.md`. Proof of each step: `docs/PROGRESS.md`.

### Where things live (v1 code path)

| Path | What it is |
|---|---|
| `apps/api/main.py` | FastAPI app: `/health`, securities, reports (+ `/pdf`), source files, markets, fixed income, portfolio proposal |
| `apps/web/` | Next.js 16 App Router frontend (`src/app/*` routes, `src/lib/api.ts` client, `src/components/report/*`) |
| `packages/database/` | SQLAlchemy models (`models.py`), `ExactDecimal` type (`types.py`), session (`session.py`) |
| `packages/analysis/` | Deterministic engines: ratios, line items, beta (5 methods + rule), cost of equity, bank valuation, model view, notes |
| `packages/report/` | `builder.py` assembles the report payload with statuses; `pdf.py` renders the PDF |
| `packages/core/config.py` | Settings (env vars below) |
| `pipelines/` | Data jobs run as commands: security master, macro (BoT, NBS, Damodaran), bank reports, review, licensed price import |
| `pipelines/banks/` | Shared bank pipeline (download, dual extraction, resolve, load). `profiles.py` holds one profile per bank (NMB, CRDB): report links, label wording, column layout, tie checks, cited risks |
| `config/*.json` | Securities, valuation assumptions, model-view rule, known source inconsistencies |
| `alembic/` | Database migrations |
| `tests/v1/` | v1 tests (hand-checked values, API contract, NMB and CRDB end to end) |
| `apps/web/e2e/` | Playwright browser checks at 1440px and 375px, plus the backend-stopped checks |
| `data/` (git-ignored) | `raw/` downloaded sources with SHA-256 manifests, `processed/` extraction output, `afrianalyze.db` (SQLite) |

Legacy code that the v1 API does not use (status in the master audit): `agents/`, `connectors/`, `models/`,
`apps/api/routers`, `apps/api/tasks`, `apps/api/core`, most of `packages/*` other than the four above, `run_*_acceptance.py`.

### Setup (PowerShell, from the repo root)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m alembic upgrade head
cd apps\web; npm ci; cd ..\..
```

### Load the data (in this order)

```powershell
.venv\Scripts\python -m pipelines.load_security_master   # config/securities.json -> securities
.venv\Scripts\python -m pipelines.macro                  # BoT bonds + CBR, NBS CPI, Damodaran CRP
# For each bank (--bank=nmb or --bank=crdb):
.venv\Scripts\python -m pipelines.banks.download_reports --bank=crdb   # annual reports 2021-2025 + SHA-256 manifest
.venv\Scripts\python -m pipelines.banks.extract --bank=crdb            # Camelot + Docling, ~5 min per report (years optional)
.venv\Scripts\python -m pipelines.banks.resolve --bank=crdb            # agreement, conflicts, tie checks (exit 1 on a critical failure)
.venv\Scripts\python -m pipelines.banks.load --bank=crdb               # facts, documents, risks; opens a draft research run
```

`pipelines.nmb.*` still works for NMB (it calls the shared pipeline with `--bank=nmb`).
To add a bank: add a profile in `pipelines/banks/profiles.py`, run the four commands, and write
`tests/v1/test_<bank>_integration.py` with figures checked by hand against the PDF pages.

Review and publish (section 72): `.venv\Scripts\python -m pipelines.review list`, then `submit`, `approve` or
`reject` with `--by "Full Name" --note "..."`.

Share prices and the index (the DSE's public data; the owner's decision of 2026-09-19, see
`docs/COMPLIANCE_NOTES.md`):

```powershell
# Prices, one file per security. Download first, then import.
Invoke-WebRequest -UserAgent "Mozilla/5.0" -OutFile nmb_prices.json `
  "https://dse.co.tz/api/get/market/prices/for/range/duration?security_code=NMB&days=3650&class=EQUITY"
.venv\Scripts\python -m pipelines.dse.import_public_prices --instrument DSE:NMB --file nmb_prices.json

# The index. The endpoint serves one date per request, so this takes about 35 minutes for ten years.
# It is resumable: run it again and it only asks for the dates it is missing.
.venv\Scripts\python -m pipelines.dse.fetch_public_index --from 2016-09-22 --to 2026-09-18
.venv\Scripts\python -m pipelines.dse.import_public_index --code DSEI --instrument DSE:DSEI
```

If a licensed file is ever obtained instead:
`.venv\Scripts\python -m pipelines.dse.import_prices --instrument DSE:NMB --file ... --licence "..."`.

### Run

```powershell
.venv\Scripts\python -m uvicorn apps.api.main:app --port 8000      # API
cd apps\web; npm run dev -- --port 3000                              # web, http://localhost:3000
```

`docker compose up` is written for the same stack with PostgreSQL but is UNTESTED (Docker is not installed).

### Test

```powershell
.venv\Scripts\python -m pytest -q tests                  # all Python tests; tests/v1 is the v1 suite
cd apps\web; npx tsc --noEmit; npx eslint src           # types and lint
cd apps\web; npx playwright test                         # browser checks, API and web must be running
# Backend-stopped check: stop the API, then
cd apps\web; $env:OFFLINE = "1"; npx playwright test; Remove-Item Env:OFFLINE
```

Playwright uses the installed Google Chrome (`PW_CHANNEL`, default `chrome`). Screenshots go to `docs/screenshots/`.

### Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `APP_ENV` | `DEVELOPMENT` | `PRODUCTION` hides reports that are not published by a reviewer (403); tests set `TEST` |
| `DATABASE_URL` | SQLite at `data/afrianalyze.db` | PostgreSQL URL in Docker |
| `CORS_ORIGINS` | ports 3000 and 3001 on localhost and 127.0.0.1 | Allowed browser origins |
| `SHOW_TRADE_LABELS` | `true` | BUY/HOLD/SELL labels next to the model view (section 71). On by the owner's decision of 2026-09-19 |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API address the browser uses |
| `API_URL_INTERNAL` | same as above | API address for server-side rendering (Docker: `http://api:8000`) |
| `HF_HUB_DISABLE_SYMLINKS` | set to `1` by the extractor | Lets Docling download its models on Windows without symlink rights |
