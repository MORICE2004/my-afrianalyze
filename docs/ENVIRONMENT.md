# Environment variables

Every variable the live code reads, from `packages/core/config.py` and `apps/web` (checked 2026-09-25 by
searching the code for `settings.` and `process.env.`). `.env.example` lists the same names with no values.

Classes: `PUBLIC` (ends up in the browser), `SERVER_ONLY` (not secret, but only the server needs it),
`SECRET` (never in git, logs or chat; set it in the host's dashboard), `OPTIONAL`,
`REQUIRED_FOR_PRODUCTION`.

## API (Render)

| Variable | Class | Default | What it does |
|---|---|---|---|
| `APP_ENV` | SERVER_ONLY, REQUIRED_FOR_PRODUCTION | `DEVELOPMENT` | `PRODUCTION` turns on the guards below, hides unpublished reports (403) and switches off `/docs`. `TEST` is for pytest only |
| `DATABASE_URL` | **SECRET**, REQUIRED_FOR_PRODUCTION | SQLite at `data/afrianalyze.db` | Postgres connection string (contains the password). `postgres://` is accepted and rewritten. In PRODUCTION anything other than Postgres refuses to start |
| `CORS_ORIGINS` | SERVER_ONLY, REQUIRED_FOR_PRODUCTION | localhost ports 3000/3001 | Comma-separated browser origins, e.g. `https://afrianalyze.vercel.app`. PRODUCTION refuses localhost and `*` |
| `ALLOWED_HOSTS` | SERVER_ONLY, OPTIONAL | `*` | Host names the API answers to, e.g. `afrianalyze-api.onrender.com`. Set it in production |
| `SHOW_TRADE_LABELS` | SERVER_ONLY | `true` | BUY/HOLD/SELL next to the model view (owner decision 2026-09-19) |
| `EXPENSIVE_REQUESTS_PER_MINUTE` | SERVER_ONLY, OPTIONAL | `30` | Per-client limit on report and PDF builds |
| `SENTRY_DSN` | SERVER_ONLY, OPTIONAL | empty (off) | Where errors are reported. Not a password, but kept out of git |
| `PORT` | SERVER_ONLY | `8000` | Set by Render; read by the Docker command |
| `FIRECRAWL_API_KEY` | SECRET, OPTIONAL | empty | Read only by legacy connectors; the v1 code path does not use it |

## Web (Vercel)

| Variable | Class | Default | What it does |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | **PUBLIC**, REQUIRED_FOR_PRODUCTION | `http://localhost:8000` | The API address the browser calls. Compiled into the JavaScript. A Vercel production build fails unless it is `https://` |
| `API_URL_INTERNAL` | SERVER_ONLY, OPTIONAL | `NEXT_PUBLIC_API_URL` | Address for server-side rendering (in Docker: `http://api:8000`) |
| `NEXT_PUBLIC_ALLOW_INDEXING` | PUBLIC, OPTIONAL | unset | `true` lets search engines index the site. Leave unset until reports are published |
| `VERCEL`, `VERCEL_ENV` | set by Vercel | | Used to skip the standalone bundle and to apply the production-build guard |

## Pipelines (your machine, writing to the production database)

The pipelines read the same `DATABASE_URL`. Run them with the production URL set in the shell for that
command only; do not put it in a file:

```powershell
$env:DATABASE_URL = "<paste from Neon>"; .venv\Scripts\python -m alembic upgrade head; Remove-Item Env:DATABASE_URL
```

## Rules

- Anything starting `NEXT_PUBLIC_` is visible to every visitor. Never put a database URL, key or token in one.
- Secret files: `.env` and `.env*` are git-ignored (checked); `apps/web/.env.local` holds only the Vercel
  CLI's own token and is git-ignored.
- Development, preview and production use different databases: development uses the local SQLite file,
  and the only production database is the one whose URL is typed into Render. Vercel preview builds call
  whatever `NEXT_PUBLIC_API_URL` their environment sets; point Preview at nothing, or at a staging API,
  never at a production API that can be written to. (The API has no write endpoints today, which
  limits the damage.)
- Not used by the live code, so not listed: `SECRET_KEY`, `REDIS_URL`, `SUPABASE_*`, `S3_*`, LLM keys,
  `POSTHOG_*`. Earlier documents listed them for systems that were never wired in.
