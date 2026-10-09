"""Build step of the API's Vercel deployment (copied to the deploy root by scripts/stage_api_vercel.py).

Vercel runs this after installing the requirements and before packaging the function. The database address is
available here as an environment variable even though, being Sensitive, it can never be downloaded. Steps:
migrations, then the first-time copy of the research data or, later, the sync of review approvals
(pipelines/copy_to_postgres.py). The research database file that was uploaded for this step is then deleted so
it is not packaged into the running API.
"""
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
db = root / "data" / "afrianalyze.db"
target = os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL", "")
if not target:
    sys.exit("DATABASE_URL is not set for this deployment")
env = {**os.environ, "TARGET_DATABASE_URL": target, "SOURCE_DATABASE_URL": f"sqlite:///{db.as_posix()}"}
code = subprocess.run([sys.executable, "-m", "pipelines.copy_to_postgres"], cwd=root, env=env).returncode
db.unlink(missing_ok=True)
sys.exit(code)
