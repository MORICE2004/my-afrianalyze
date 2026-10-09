r"""Assemble the API for Vercel in build/vercel-api (git-ignored), then deploy that folder.

    .venv\Scripts\python scripts\stage_api_vercel.py
    cd build\vercel-api; vercel deploy --prod --regions fra1

Only what the server runs is copied: the API, the shared packages, configuration, the Alembic migrations, and
the stored source PDFs the page viewer renders (exchange price files are never copied: they are not shown). No
.env file, user data or raw news/price downloads go in; the research database goes in for the build step only. The database is the Postgres server named
by DATABASE_URL in the Vercel project's environment.
"""
from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "vercel-api"
NOT_SHOWN = {"licensed_price_file", "public_price_file", "public_index_file"}


def copytree(rel: str) -> None:
    shutil.copytree(ROOT / rel, OUT / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))


def main() -> None:
    keep = OUT / ".vercel"
    leftover = OUT.parent / ".vercel-api-link"
    saved = leftover if leftover.exists() else None  # a link saved by an interrupted earlier run
    if keep.exists():  # keep the project link between builds
        saved = OUT.parent / ".vercel-api-link"
        shutil.rmtree(saved, ignore_errors=True)
        shutil.move(str(keep), saved)
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)  # Windows can leave the emptied folder itself in place
    if saved:
        shutil.move(str(saved), keep)

    for rel in ("apps/api", "packages", "pipelines", "config", "alembic"):  # as Dockerfile.api
        copytree(rel)
    (OUT / "apps" / "__init__.py").touch()
    shutil.copy(ROOT / "alembic.ini", OUT / "alembic.ini")
    shutil.copy(ROOT / "requirements-api.txt", OUT / "requirements.txt")

    # The source documents the reader can view page by page (annual reports), listed from the database.
    con = sqlite3.connect(ROOT / "data" / "afrianalyze.db")
    rows = con.execute("SELECT kind, file_path FROM source_documents WHERE file_path IS NOT NULL").fetchall()
    size = 0
    for kind, path in rows:
        src = ROOT / path
        if kind in NOT_SHOWN or src.suffix.lower() != ".pdf" or not src.is_file():
            continue
        dst = OUT / path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        size += src.stat().st_size

    # The research database, for the build step only (scripts/vercel_build.py copies it into Postgres and then
    # deletes it). Local accounts, sessions and portfolios are removed from this copy before it leaves the machine.
    (OUT / "data").mkdir(exist_ok=True)
    staged_db = OUT / "data" / "afrianalyze.db"
    shutil.copy(ROOT / "data" / "afrianalyze.db", staged_db)
    scrub = sqlite3.connect(staged_db)
    for table in ("portfolio_holdings", "saved_portfolios", "user_sessions", "users"):
        scrub.execute(f"DELETE FROM {table}")
    scrub.commit()
    scrub.execute("VACUUM")
    scrub.close()
    shutil.copy(ROOT / "scripts" / "vercel_build.py", OUT / "vercel_build.py")

    (OUT / "main.py").write_text(
        '"""Vercel entrypoint: the AfriEdge API (apps/api/main.py)."""\nfrom apps.api.main import app  # noqa: F401\n',
        encoding="utf-8")
    (OUT / ".python-version").write_text("3.12\n", encoding="utf-8")
    (OUT / "vercel.json").write_text(
        '{\n  "$schema": "https://openapi.vercel.sh/vercel.json",\n  "framework": "fastapi",\n  "regions": ["fra1"],\n'
        '  "buildCommand": "python vercel_build.py",\n'
        '  "functions": { "main.py": { "maxDuration": 60, "excludeFiles": "{data/afrianalyze.db,vercel_build.py}" } }\n}\n',
        encoding="utf-8")
    (OUT / ".vercelignore").write_text("__pycache__/\n*.pyc\n.env*\n", encoding="utf-8")
    print(f"staged {OUT} ({size / 1e6:.0f} MB of source PDFs)")


if __name__ == "__main__":
    main()
