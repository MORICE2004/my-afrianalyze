r"""Execute a research run for one or more companies.

    .venv\Scripts\python -m pipelines.research_run DSE:NMB DSE:CRDB

Each run records its stages and freezes the report it built (packages/research/engine.py). The run starts as a
draft; publish it with pipelines.review (submit, then approve). Exit code 1 if any run ended FAILED or BLOCKED.
"""
from __future__ import annotations

import sys

from packages.database.session import SessionLocal
from packages.research.engine import execute


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    worst = 0
    with SessionLocal() as s:
        for sid in argv:
            run = execute(s, sid.upper(), actor="pipelines.research_run")
            print(f"{run.id}  {run.security_id}  {run.execution_state}")
            for st in run.stages or []:
                print(f"    {st['stage']:<18} {st['state']:<18} {st['detail'][:110]}")
            if run.execution_state in ("FAILED", "BLOCKED"):
                worst = 1
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
