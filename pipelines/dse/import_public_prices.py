r"""Import end-of-day prices from the file the DSE website serves publicly.

Owner decision (2026-09-19): use the prices the DSE publishes on its own website
(https://dse.co.tz, whose robots.txt allows automated access) rather than waiting for a data
licence. The DSE Data Vending Policy restricts reuse of its market data; the owner accepted that
risk. Every imported price keeps the web address and download time it came from, and the file
itself is stored with its SHA-256, so the whole series can be traced or removed later.

Download (PowerShell), one file per instrument:

    curl.exe -A "Mozilla/5.0" "https://dse.co.tz/api/get/market/prices/for/range/duration?security_code=NMB&days=3650&class=EQUITY" -o nmb_prices.json

Then:

    .venv\Scripts\python -m pipelines.dse.import_public_prices --instrument DSE:NMB --file nmb_prices.json

The file is the DSE's own JSON: {"success": true, "data": [{trade_date, closing_price, volume, ...}]}.
A day with volume 0 is a day the share did not trade; its closing price is the previous trade, which
is how the exchange reports it. Those days are kept, because the beta methods need to know about them
(PRODUCT_CONTEXT.md section 74).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func

from packages.analysis import corporate_actions
from packages.database.models import DataSourceStatus, PriceBar, Security, SourceDocument
from packages.database.session import SessionLocal

STORE = Path("data/raw/dse/public")
API = ("https://dse.co.tz/api/get/market/prices/for/range/duration"
       "?security_code={code}&days={days}&class={klass}")
TERMS_NOTE = ("Downloaded from the Dar es Salaam Stock Exchange's public website, which its robots.txt "
              "allows. The DSE Data Vending Policy (cl. 16.3.3, 23.1) restricts reuse of DSE market data; "
              "the owner decided on 2026-09-19 to use the published prices and accepted that risk "
              "(docs/COMPLIANCE_NOTES.md).")


JUMP = Decimal("0.30")      # a one-day move bigger than this is treated as suspicious, not as a return


def unexplained_jumps(bars: dict, instrument: str) -> list[tuple]:
    """One-day moves too large to be a real return, unless a recorded split explains them.

    NMB's 1:10 split published as a 90% fall is the reason this exists: a split read as a return would
    poison every beta method. A move within a few days of a recorded split is accepted, because the
    exchange suspends trading around the record date.
    """
    actions = corporate_actions.load_actions(instrument)
    split_dates = [date.fromisoformat(a["effective_date"]) for a in actions]
    out = []
    days = sorted(bars)
    for previous, day in zip(days, days[1:]):
        before, after = bars[previous][0], bars[day][0]
        if not before:
            continue
        if abs(after - before) / before <= JUMP:
            continue
        if any(abs((day - d).days) <= 5 for d in split_dates):
            continue                        # the recorded split accounts for it
        out.append((day, before, after))
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrument", required=True, help="DSE:NMB, DSE:CRDB, DSE:DSEI ...")
    ap.add_argument("--file", required=True, help="JSON file downloaded from the DSE website")
    ap.add_argument("--class", dest="klass", default="EQUITY", help="EQUITY (default) or INDEX")
    ap.add_argument("--days", default="3650", help="The days= value used when downloading (for the record)")
    ap.add_argument("--allow-unexplained-jumps", action="store_true",
                    help="Import even if a one-day move of more than 30% has no recorded corporate action")
    args = ap.parse_args(argv)

    src = Path(args.file)
    if not src.is_file():
        print(f"File not found: {src}")
        return 1
    content = src.read_bytes()
    payload = json.loads(content)
    rows = payload.get("data") or []
    if not payload.get("success") or not rows:
        print(f"The file holds no data: {payload.get('message', payload)}")
        return 1

    code = args.instrument.split(":")[-1]
    codes = {str(r.get("company", "")).upper() for r in rows}
    if codes and codes != {code.upper()}:
        print(f"The file is for {sorted(codes)}, not {code}. Refusing to import it under {args.instrument}.")
        return 1

    bars: dict[object, tuple] = {}
    for r in rows:
        close = r.get("closing_price")
        if close in (None, "", 0):
            continue  # no published close for that day
        day = datetime.fromisoformat(str(r["trade_date"])).date()
        volume = r.get("volume")
        bars[day] = (Decimal(str(close)), None if volume is None else Decimal(str(volume)))
    if not bars:
        print("No rows carried a closing price; nothing imported.")
        return 1

    unexplained = unexplained_jumps(bars, args.instrument)
    if unexplained and not args.allow_unexplained_jumps:
        print(f"Refusing to import {args.instrument}: {len(unexplained)} one-day move(s) of more than "
              f"{int(JUMP * 100)}% that no recorded corporate action explains.\n")
        for day, before, after in unexplained[:10]:
            print(f"  {day}: {before} -> {after} (x{after / before:.3f})")
        print("\nA move like this is usually a share split, a consolidation or a bad row, not a real return."
              "\nCheck it, then either add it to config/corporate_actions.json with its evidence, or re-run"
              "\nwith --allow-unexplained-jumps if the move is genuine.")
        return 1

    sha = hashlib.sha256(content).hexdigest()
    STORE.mkdir(parents=True, exist_ok=True)
    stored = STORE / f"{args.instrument.replace(':', '_')}_{sha[:12]}.json"
    shutil.copyfile(src, stored)

    now = datetime.now(timezone.utc)
    url = API.format(code=code, days=args.days, klass=args.klass)
    with SessionLocal() as s:
        security_id = args.instrument if s.get(Security, args.instrument) else None
        doc = (s.query(SourceDocument)
               .filter_by(kind="public_price_file", sha256=sha, security_id=security_id).first())
        if doc is not None:                 # same file again: keep one record, update when it was fetched
            doc.retrieved_at = now
        else:
            doc = SourceDocument(
                security_id=security_id, kind="public_price_file",
                title=f"DSE published end-of-day prices: {args.instrument}",
                publisher="Dar es Salaam Stock Exchange", url=url,
                listing_url="https://dse.co.tz/market/data/overview",
                file_path=stored.as_posix(), sha256=sha,
                published_on=max(bars), retrieved_at=now, terms_note=TERMS_NOTE)
            s.add(doc)
        s.flush()
        s.query(PriceBar).filter_by(instrument_id=args.instrument).delete()
        for day, (close, volume) in sorted(bars.items()):
            s.add(PriceBar(instrument_id=args.instrument, trade_date=day, close=close, volume=volume,
                           source_document_id=doc.id))
        traded = sum(1 for _, v in bars.values() if v)
        s.flush()
        # One status row covers the source, so describe every instrument that now has prices.
        loaded = (s.query(PriceBar.instrument_id, func.count(), func.min(PriceBar.trade_date),
                          func.max(PriceBar.trade_date))
                  .group_by(PriceBar.instrument_id).order_by(PriceBar.instrument_id).all())
        s.merge(DataSourceStatus(
            source="dse_prices", last_success_at=now, last_attempt_at=now, status="ok", max_age_hours=24 * 5,
            detail="; ".join(f"{iid} {n} days ({lo} to {hi})" for iid, n, lo, hi in loaded)
                   + ". Source: DSE published prices."))
        s.commit()
    print(f"Imported {len(bars)} days for {args.instrument}: {min(bars)} to {max(bars)}, "
          f"{len(bars) - traded} days without a trade ({(len(bars) - traded) / len(bars):.1%}). "
          f"Stored {stored} (sha256 {sha[:16]}).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
