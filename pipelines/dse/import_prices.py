r"""Import licensed DSE end-of-day prices from a file.

DSE market data is licensed (DSE Data Vending Policy cl. 16.3.3 and 23.1), so
prices are never scraped. Use this with a file obtained under a DSE licence or
the academic access route (cl. 17.1, 17.7).

    .venv\Scripts\python -m pipelines.dse.import_prices ^
        --instrument DSE:NMB --file path\to\nmb.xlsx ^
        --licence "DSE historical data licence ref ..." ^
        [--date-col Date --close-col Close --volume-col Volume]

Use --instrument DSE:DSEI (or DSE:TSI) for index levels (no volume column).
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from packages.database.models import DataSourceStatus, PriceBar, SourceDocument
from packages.database.session import SessionLocal

STORE = Path("data/raw/dse/licensed")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrument", required=True, help="DSE:NMB, DSE:DSEI, DSE:TSI ...")
    ap.add_argument("--file", required=True)
    ap.add_argument("--licence", required=True, help="Licence or permission reference for this file")
    ap.add_argument("--date-col", default="Date")
    ap.add_argument("--close-col", default="Close")
    ap.add_argument("--volume-col", default=None)
    ap.add_argument("--date-format", default=None)
    args = ap.parse_args(argv)

    src = Path(args.file)
    content = src.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    STORE.mkdir(parents=True, exist_ok=True)
    stored = STORE / f"{args.instrument.replace(':', '_')}_{sha[:12]}{src.suffix}"
    shutil.copyfile(src, stored)

    df = pd.read_excel(stored) if src.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(stored)
    missing = [c for c in (args.date_col, args.close_col, args.volume_col) if c and c not in df.columns]
    if missing:
        print(f"Columns not found: {missing}. Available: {list(df.columns)}")
        return 1
    dates = pd.to_datetime(df[args.date_col], format=args.date_format, dayfirst=args.date_format is None)
    closes = pd.to_numeric(df[args.close_col].astype(str).str.replace(",", ""), errors="coerce")
    vols = (pd.to_numeric(df[args.volume_col].astype(str).str.replace(",", ""), errors="coerce")
            if args.volume_col else None)
    bad = int(closes.isna().sum())
    if bad:
        print(f"{bad} rows have no numeric close price; refusing to import a partial file.")
        return 1

    now = datetime.now(timezone.utc)
    with SessionLocal() as s:
        doc = SourceDocument(security_id=args.instrument if args.instrument.count(":") == 1 and
                             not args.instrument.endswith(("DSEI", "TSI")) else None,
                             kind="licensed_price_file", fiscal_year=None,
                             title=f"Licensed DSE end-of-day data: {args.instrument}",
                             publisher=f"Dar es Salaam Stock Exchange (licence: {args.licence})",
                             url=f"file:{stored.as_posix()}", listing_url=None, file_path=stored.as_posix(),
                             sha256=sha, retrieved_at=now)
        s.add(doc)
        s.flush()
        s.query(PriceBar).filter_by(instrument_id=args.instrument).delete()
        for i in range(len(df)):
            s.add(PriceBar(instrument_id=args.instrument, trade_date=dates.iloc[i].date(),
                           close=float(closes.iloc[i]),
                           volume=None if vols is None or pd.isna(vols.iloc[i]) else float(vols.iloc[i]),
                           source_document_id=doc.id))
        s.merge(DataSourceStatus(source="dse_prices", last_success_at=now, last_attempt_at=now, status="ok",
                                 max_age_hours=24 * 3,
                                 detail=f"Imported {len(df)} rows for {args.instrument} from licensed file {stored.name}"))
        s.commit()
    print(f"Imported {len(df)} rows for {args.instrument} ({dates.min().date()} to {dates.max().date()})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
