r"""Refresh the last weeks of DSE prices for every share that already has a stored history.

    .venv\Scripts\python -m pipelines.dse.refresh_prices            # used by .github/workflows/refresh-data.yml

Only shares already loaded are refreshed. A share's FIRST load is a deliberate ten-year download that passes the
unexplained-jump check over its whole history (pipelines.dse.import_public_prices); a short refresh must not
slip in a share that was refused there (on 2026-10-07: KA, NICO, NMG, TTP, USL, VODA, AFRIPRISE, JATU).
Every import merges (pipelines/dse/merge.py), so history is never deleted. One failing share does not stop the
others; the exit code is 1 if any share failed or had a revision held back for review.
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

import requests

from packages.database.models import PriceBar, Security
from packages.database.session import SessionLocal
from pipelines.dse import import_public_prices

UA = {"User-Agent": "Mozilla/5.0 (AfriEdge scheduled data refresh)"}
URL = "https://dse.co.tz/api/get/market/prices/for/range/duration?security_code={code}&days={days}&class=EQUITY"


def loaded_shares() -> list[str]:
    with SessionLocal() as s:
        have = {iid for (iid,) in s.query(PriceBar.instrument_id).distinct()}
        return sorted(sec.local_ticker for sec in s.query(Security).filter_by(exchange="DSE") if sec.id in have)


def main(argv: list[str]) -> int:
    days = argv[0] if argv else "30"
    codes = loaded_shares()
    if not codes:
        print("No DSE share has a stored history yet; load each one once with pipelines.dse.import_public_prices.")
        return 1
    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        for code in codes:
            time.sleep(1)
            path = Path(tmp) / f"{code}.json"
            try:
                r = requests.get(URL.format(code=code, days=days), headers=UA, timeout=60)
                r.raise_for_status()
                path.write_bytes(r.content)
            except requests.RequestException as exc:
                print(f"{code}: download failed ({type(exc).__name__})")
                failed.append(code)
                continue
            rc = import_public_prices.main(["--instrument", f"DSE:{code}", "--file", str(path), "--days", days])
            if rc != 0:
                failed.append(code)
    summary = (f"Refreshed {len(codes) - len(failed)} of {len(codes)} shares."
               + (f" Needs attention: {', '.join(failed)}." if failed else ""))
    if failed:
        # Record the failed attempt on /health; the last success stays as it was, so the age is still true.
        from datetime import datetime, timezone

        from packages.database.models import DataSourceStatus
        with SessionLocal() as s:
            row = s.get(DataSourceStatus, "dse_prices")
            if row is not None:
                row.last_attempt_at, row.status = datetime.now(timezone.utc), "partial"
                row.detail = f"Last refresh: {summary} " + (row.detail or "")[:900]
                s.commit()
    print(summary)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
