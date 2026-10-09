r"""Copy the research database (SQLite) into PostgreSQL (e.g. Neon) for the hosted API.

Runs inside the API's Vercel build (scripts/vercel_build.py), where the database address is available but never
shown: Neon's password is a Sensitive variable that cannot be downloaded. It can also run locally:

    $env:SOURCE_DATABASE_URL = "sqlite:///data/afrianalyze.db"   # default: the local database
    $env:TARGET_DATABASE_URL = "<the PostgreSQL address>"
    .venv\Scripts\python -m pipelines.copy_to_postgres

1. Runs the Alembic migrations on the target (this also seeds the free and pro plans).
2. If the target has no research data yet: copies every table in dependency order, values unchanged, leaving out
   what belongs to one machine only (user accounts, sessions, saved portfolios, plans, entitlements, Alembic's
   table), then moves each id sequence past the copied rows.
3. If the target already has data: copies nothing, except the review lifecycle of research runs (status, reviewer,
   dates, notes). An approval made with pipelines.review on the workstation reaches the site on the next deploy;
   nothing is ever approved here.
"""
from __future__ import annotations

import os
import subprocess
import sys

from sqlalchemy import MetaData, create_engine, func, select, text

from packages.core.config import REPO_ROOT

SKIP = {"users", "user_sessions", "saved_portfolios", "portfolio_holdings", "plans", "entitlements", "alembic_version"}
REVIEW_FIELDS = ("status", "reviewer", "reviewed_at", "superseded_by")
BATCH = 1000


def pg(url: str) -> str:
    return "postgresql://" + url[len("postgres://"):] if url.startswith("postgres://") else url


def main() -> int:
    target_url = pg(os.environ.get("TARGET_DATABASE_URL", ""))
    source_url = os.environ.get("SOURCE_DATABASE_URL") or f"sqlite:///{(REPO_ROOT / 'data' / 'afrianalyze.db').as_posix()}"
    if not target_url.startswith("postgresql"):
        print("Set TARGET_DATABASE_URL to the PostgreSQL connection string.", file=sys.stderr)
        return 2
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=REPO_ROOT, check=True,
                   env={**os.environ, "DATABASE_URL": target_url})

    source = create_engine(source_url)
    target = create_engine(target_url)
    meta = MetaData()
    meta.reflect(bind=source)
    tmeta = MetaData()
    tmeta.reflect(bind=target)
    with target.connect() as t:
        has_data = bool(t.execute(text("SELECT count(*) FROM securities")).scalar())

    if has_data:
        runs = meta.tables["research_runs"]
        fields = [f for f in REVIEW_FIELDS if f in runs.c and f in tmeta.tables["research_runs"].c]
        with source.connect() as s, target.begin() as t:
            n = 0
            for r in s.execute(select(runs.c.id, *[runs.c[f] for f in fields])).mappings():
                n += t.execute(tmeta.tables["research_runs"].update().where(tmeta.tables["research_runs"].c.id == r["id"])
                               .values({f: r[f] for f in fields})).rowcount
        print(f"target already holds data: review state synced for {n} research runs")
        return 0

    with source.connect() as s, target.begin() as t:
        for table in meta.sorted_tables:
            if table.name in SKIP or table.name not in tmeta.tables:
                continue
            dest = tmeta.tables[table.name]
            cols = [c.name for c in table.columns if c.name in dest.columns]
            rows = s.execute(select(*[table.c[c] for c in cols])).mappings().all()
            for i in range(0, len(rows), BATCH):
                t.execute(dest.insert(), [dict(r) for r in rows[i:i + BATCH]])
            print(f"{table.name}: {len(rows)} rows")
        for table in tmeta.sorted_tables:
            pk = list(table.primary_key.columns)
            if len(pk) == 1 and str(pk[0].type) in ("INTEGER", "BIGINT"):
                seq = t.execute(text("SELECT pg_get_serial_sequence(:t, :c)"), {"t": table.name, "c": pk[0].name}).scalar()
                if seq:
                    top = t.execute(select(func.max(pk[0]))).scalar() or 0
                    t.execute(text("SELECT setval(:s, :v, :called)"), {"s": seq, "v": max(top, 1), "called": top > 0})
    print("copy complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
