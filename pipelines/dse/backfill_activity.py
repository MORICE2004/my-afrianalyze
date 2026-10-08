r"""Fill each stored bar's open, high, low, turnover and market cap from the DSE files already on disk.

    .venv\Scripts\python -m pipelines.dse.backfill_activity

Bars stored before 2026-10-08 kept only close and volume, although the DSE's file for the day also states
the opening price, high, low, turnover and market capitalisation. Every file that was imported is stored
with its SHA-256 (data/raw/dse/public), so those fields can be read back without asking the DSE again.

Only fills, never inserts or overwrites: a bar gets a field only when it is empty and the file agrees with
the stored close and volume for that day (so the values describe the same published day). A bar's own source
file is read first; the source_document_id is not changed, because the close still comes from it.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from packages.core.config import REPO_ROOT
from packages.database.models import PriceBar, SourceDocument
from packages.database.session import SessionLocal
from pipelines.dse.import_public_prices import parse_rows
from pipelines.dse.merge import ACTIVITY_FIELDS


def main(argv: list[str]) -> int:
    filled_days, files, skipped = 0, 0, []
    with SessionLocal() as s:
        docs = (s.query(SourceDocument).filter_by(kind="public_price_file")
                .order_by(SourceDocument.retrieved_at).all())
        bars_by_doc: dict[str, dict] = {}
        for doc in docs:
            if not doc.file_path:
                continue
            path = (REPO_ROOT / doc.file_path).resolve()
            if not path.is_file():
                skipped.append(f"{doc.file_path} (missing on disk)")
                continue
            content = path.read_bytes()
            if doc.sha256 and hashlib.sha256(content).hexdigest() != doc.sha256:
                skipped.append(f"{doc.file_path} (SHA-256 does not match the record; not used)")
                continue
            rows = json.loads(content).get("data") or []
            if not rows:
                continue
            instrument = doc.security_id or f"DSE:{str(rows[0].get('company', '')).upper()}"
            bars, activity = parse_rows(rows)
            files += 1
            if instrument not in bars_by_doc:
                bars_by_doc[instrument] = {b.trade_date: b for b in
                                           s.query(PriceBar).filter_by(instrument_id=instrument)}
            stored = bars_by_doc[instrument]
            # The bar's own source file first: sort so that this document's own bars are visited by it.
            for day, (close, volume) in bars.items():
                bar = stored.get(day)
                if bar is None or bar.close != close or (volume is not None and bar.volume != volume):
                    continue
                if bar.source_document_id != doc.id and any(
                        d.id == bar.source_document_id for d in docs if d.retrieved_at >= doc.retrieved_at):
                    continue            # its own file comes later in this loop and fills it from there
                changed = False
                for name in ACTIVITY_FIELDS:
                    if getattr(bar, name) is None and activity[day].get(name) is not None:
                        setattr(bar, name, activity[day][name])
                        changed = True
                filled_days += changed
        s.commit()
        missing = s.query(PriceBar).filter(PriceBar.instrument_id.notin_(["DSE:DSEI"]),
                                           PriceBar.turnover.is_(None)).count()
    print(f"Read {files} stored DSE price files; filled the published activity fields on {filled_days} days. "
          f"{missing} share-days still have no turnover (their file did not state it).")
    for item in skipped:
        print(f"  skipped {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
