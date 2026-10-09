r"""Copy the local SQLite database into an empty PostgreSQL database (e.g. Neon) for the hosted API.

    $env:TARGET_DATABASE_URL = "<from the Vercel project's environment, never typed into chat>"
    .venv\Scripts\python -m pipelines.copy_to_postgres

1. Runs the Alembic migrations on the target, so its schema is exactly the one the code expects (this also seeds
   the free and pro plans).
2. Copies every table row by row in dependency order, values unchanged (exact decimals stay exact).
3. Leaves out what belongs to this machine only: user accounts, sessions and saved portfolios (local test
   accounts), plans and entitlements (seeded by the migration), and the Alembic bookkeeping table.
4. Moves each id sequence past the copied rows, so new rows get fresh ids.

It refuses to write into a target that already has research data, so it never mixes two copies.
"""
from __future__ import annotations

import os
import subprocess
import sys

from sqlalchemy import MetaData, create_engine, func, select, text

from packages.core.config import REPO_ROOT, settings

SKIP = {"users", "user_sessions", "saved_portfolios", "portfolio_holdings", "plans", "entitlements", "alembic_version"}
BATCH = 1000


def main() -> int:
    target_url = os.environ.get("TARGET_DATABASE_URL", "")
    if target_url.startswith("postgres://"):
        target_url = "postgresql://" + target_url[len("postgres://"):]
    if not target_url.startswith("postgresql"):
        print("Set TARGET_DATABASE_URL to the PostgreSQL connection string.", file=sys.stderr)
        return 2
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=REPO_ROOT, check=True,
                   env={**os.environ, "DATABASE_URL": target_url})

    source = create_engine(settings.DATABASE_URL)
    target = create_engine(target_url)
    meta = MetaData()
    meta.reflect(bind=source)
    with target.connect() as t:
        if t.execute(text("SELECT count(*) FROM securities")).scalar():
            print("The target already holds data; nothing copied.", file=sys.stderr)
            return 1
    tmeta = MetaData()
    tmeta.reflect(bind=target)
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
            if len(pk) == 1 and pk[0].autoincrement and str(pk[0].type) in ("INTEGER", "BIGINT"):
                seq = t.execute(text("SELECT pg_get_serial_sequence(:t, :c)"), {"t": table.name, "c": pk[0].name}).scalar()
                if seq:
                    top = t.execute(select(func.max(pk[0]))).scalar() or 0
                    t.execute(text("SELECT setval(:s, :v, :called)"), {"s": seq, "v": max(top, 1), "called": top > 0})
    print("copy complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
