# Database runbook

Production database: Neon Postgres (docs/PRODUCTION_ARCHITECTURE.md). Local development: SQLite at
`data/afrianalyze.db`. One migration today: `4b3dcb0cd928` (initial schema).

What is tested and where:

| Check | Where | Result |
|---|---|---|
| Migrations on an empty SQLite, up, down, up | Local, 2026-09-25 | passed |
| Migrations on an empty Postgres 16, up, down, up | CI job "Postgres from zero" on every push | see the latest CI run |
| Money stored and read back exactly on Postgres (28 significant digits) | CI, `test_money_round_trips_exactly_on_postgres` | see the latest CI run |
| API image runs migrations on start against Postgres | CI job "API Docker image" | see the latest CI run |
| Full data load (all pipelines) into Postgres | **not yet run** | needs the Neon database to exist |
| Backup and restore | **not tested** | see below |

## 1. Create

1. Sign in at <https://neon.com> and create a project, region **AWS Europe Central 1 (Frankfurt)**.
2. Copy the connection string (Dashboard → Connect). It contains the password. Paste it into Render's
   `DATABASE_URL`, and nowhere else; do not paste it in chat or a file in the repo.

## 2. Migrate and load (from your machine, once, then after each new annual report)

The migrations only add tables. The Docker image also runs `alembic upgrade head` on every start, so the
schema is always current, but the data has to be loaded from your machine, because the processed
extraction files (`data/processed`) and the downloaded PDFs are only there.

```powershell
$env:DATABASE_URL = "<paste the Neon connection string>"
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m pipelines.load_security_master
.venv\Scripts\python -m pipelines.macro
.venv\Scripts\python -m pipelines.banks.load --bank=nmb
.venv\Scripts\python -m pipelines.banks.load --bank=crdb
.venv\Scripts\python -m pipelines.dse.import_public_prices --instrument DSE:NMB --file nmb_prices.json
.venv\Scripts\python -m pipelines.dse.import_public_prices --instrument DSE:CRDB --file crdb_prices.json
.venv\Scripts\python -m pipelines.dse.import_public_index --code DSEI --instrument DSE:DSEI
Remove-Item Env:DATABASE_URL
```

Then publish the reviewed runs (`pipelines.review`) against the same database, or the reports stay 403.

Check: `https://<api>/ready` returns 200 with `APP_HEALTHY` or `DEGRADED` (and the list of stale sources).

## 3. Roll back

- **A bad deploy of code:** in Render, *Deploys → pick the previous one → Rollback*. The schema is unchanged
  unless the new code brought a migration.
- **A bad migration:** migrations are written to be reversible (`alembic downgrade -1`), and CI runs the
  downgrade on every push. **But downgrading drops the tables it created, and their data.** Never run a
  downgrade against production without a backup taken first. Nothing in the deploy process runs one.
- **Bad data from a pipeline:** fix the input and re-run the loader. Checked in the code: the bank loader
  deletes and re-inserts that bank's facts, documents, checks and risks; the price and index importers
  delete and re-insert that instrument's bars; the macro jobs and the security master upsert. A re-load
  opens a new draft research run, which must be reviewed again. (What a re-load does to an
  already-published run has not been tested; check `pipelines.review list` afterwards.)

## 4. Back up and restore

- **Neon Free** keeps 6 hours (or 1 GB of changes) of instant restore. That covers "I just ran the wrong
  command", not "the account is gone".
- **Everything in the database can be rebuilt from sources** by the commands in section 2, provided the
  workstation's `data/raw` (downloaded files with SHA-256 manifests) and `data/processed` survive. That
  folder is the real backup of the source data, and it is **not backed up anywhere today** (179 MB, git
  ignored). Copy it to a second place (an external drive or a private cloud folder). This is the most
  important item in this section.
- **Review decisions** (who approved what, and when) exist only in the database. They cannot be rebuilt
  from sources. Take a dump after each approval:

  ```powershell
  pg_dump "<Neon connection string>" --format=custom --file "afrianalyze_$(Get-Date -Format yyyyMMdd).dump"
  ```

  `pg_dump` comes with the PostgreSQL client tools (not installed on this machine yet).
- **Restore** into a new Neon database: `pg_restore --dbname "<new connection string>" --no-owner <file>`,
  then point Render's `DATABASE_URL` at it.

**Not tested:** neither the dump nor the restore has been run. Do both once, into a scratch Neon database,
before relying on them.

## 5. Disaster recovery assumptions

- Losing Neon: rebuild from `data/` (section 2) plus the latest dump for review history. Time: under an hour
  if `data/` is intact, days if the PDFs must be downloaded and extracted again.
- Losing the workstation: the database still serves the site. New reports cannot be extracted until the
  pipeline is set up again (CLAUDE.md "Setup").
- Losing both `data/` and the database: the review history is gone; everything else is rebuildable from
  the public sources, slowly.
