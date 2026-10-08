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
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func

from packages.analysis import corporate_actions
from packages.database.models import DataSourceStatus, PriceBar, Security, SourceDocument
from packages.database.session import SessionLocal
from pipelines.dse.merge import merge_bars, stored_bars

STORE = Path("data/raw/dse/public")
API = ("https://dse.co.tz/api/get/market/prices/for/range/duration"
       "?security_code={code}&days={days}&class={klass}")
TERMS_NOTE = ("Downloaded from the Dar es Salaam Stock Exchange's public website, which its robots.txt "
              "allows. The DSE Data Vending Policy (cl. 16.3.3, 23.1) restricts reuse of DSE market data; "
              "the owner decided on 2026-09-19 to use the published prices and accepted that risk "
              "(docs/COMPLIANCE_NOTES.md).")


JUMP = Decimal("0.30")      # a one-day move bigger than this is treated as suspicious, not as a return


def unexplained_jumps(bars: dict, instrument: str, only_after: date | None = None) -> list[tuple]:
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
        if only_after is not None and day <= only_after:
            continue                        # both days already stored and checked when they were loaded
        before, after = bars[previous][0], bars[day][0]
        if not before:
            continue
        if abs(after - before) / before <= JUMP:
            continue
        if any(abs((day - d).days) <= 5 for d in split_dates):
            continue                        # the recorded split accounts for it
        out.append((day, before, after))
    return out


# The DSE's field for each of the day's other published values (pipelines/dse/merge.py ACTIVITY_FIELDS).
ACTIVITY_KEYS = {"open": "opening_price", "high": "high", "low": "low", "turnover": "turnover",
                 "market_cap": "market_cap"}


def _dec(v) -> Decimal | None:
    return None if v in (None, "") else Decimal(str(v))


def parse_rows(rows: list[dict]) -> tuple[dict, dict]:
    """(close, volume) per day, and the day's other published fields. A day with no close is skipped."""
    bars: dict[date, tuple] = {}
    activity: dict[date, dict] = {}
    for r in rows:
        close = r.get("closing_price")
        if close in (None, "", 0):
            continue  # no published close for that day
        day = datetime.fromisoformat(str(r["trade_date"])).date()
        bars[day] = (Decimal(str(close)), _dec(r.get("volume")))
        activity[day] = {name: _dec(r.get(key)) for name, key in ACTIVITY_KEYS.items()}
    return bars, activity


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrument", required=True, help="DSE:NMB, DSE:CRDB, DSE:DSEI ...")
    ap.add_argument("--file", required=True, help="JSON file downloaded from the DSE website")
    ap.add_argument("--class", dest="klass", default="EQUITY", help="EQUITY (default) or INDEX")
    ap.add_argument("--days", default="3650", help="The days= value used when downloading (for the record)")
    ap.add_argument("--accept-revisions", action="store_true",
                    help="Overwrite stored closes that the download reports differently (check them first)")
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

    bars, activity = parse_rows(rows)
    if not bars:
        print("No rows carried a closing price; nothing imported.")
        return 1

    return store_and_merge(args.instrument, content, bars, activity,
                           url=API.format(code=code, days=args.days, klass=args.klass),
                           accept_revisions=args.accept_revisions,
                           allow_unexplained_jumps=args.allow_unexplained_jumps)


def store_and_merge(instrument: str, content: bytes, bars: dict, activity: dict, *, url: str,
                    kind: str = "public_price_file", publisher: str = "Dar es Salaam Stock Exchange",
                    title: str = "DSE published end-of-day prices",
                    listing_url: str | None = "https://dse.co.tz/market/data/overview",
                    terms_note: str = TERMS_NOTE, accept_revisions: bool = False,
                    allow_unexplained_jumps: bool = False) -> int:
    """Check, store and merge one provider's answer for one instrument. Every provider goes through this, so
    the jump check, the stored file with its SHA-256 and the never-delete merge apply to all of them. The
    SourceDocument records who published the prices (`publisher`), which is how the source used is kept with
    the data. Returns 0, 1 (refused) or 2 (a past close revised by the source and held back)."""
    # Check the download joined to what is already stored, so the first new day is compared with the last
    # stored one. Days before the download (already checked when they were loaded) are not checked again.
    with SessionLocal() as s:
        stored = stored_bars(s, instrument)
    combined = {**stored, **{d: v for d, v in bars.items() if d not in stored}}
    last_stored = max(stored) if stored else None
    unexplained = unexplained_jumps(combined, instrument,
                                    only_after=None if last_stored is None else min(min(bars), last_stored))
    if unexplained and not allow_unexplained_jumps:
        print(f"Refusing to import {instrument}: {len(unexplained)} one-day move(s) of more than "
              f"{int(JUMP * 100)}% that no recorded corporate action explains.\n")
        for day, before, after in unexplained[:10]:
            print(f"  {day}: {before} -> {after} (x{after / before:.3f})")
        print("\nA move like this is usually a share split, a consolidation or a bad row, not a real return."
              "\nCheck it, then either add it to config/corporate_actions.json with its evidence, or re-run"
              "\nwith --allow-unexplained-jumps if the move is genuine.")
        return 1

    sha = hashlib.sha256(content).hexdigest()
    STORE.mkdir(parents=True, exist_ok=True)
    prefix = "" if kind == "public_price_file" else f"{kind}_"
    stored_file = STORE / f"{prefix}{instrument.replace(':', '_')}_{sha[:12]}.json"
    stored_file.write_bytes(content)

    now = datetime.now(timezone.utc)
    with SessionLocal() as s:
        security_id = instrument if s.get(Security, instrument) else None
        doc = (s.query(SourceDocument)
               .filter_by(kind=kind, sha256=sha, security_id=security_id).first())
        if doc is not None:                 # same file again: keep one record, update when it was fetched
            doc.retrieved_at = now
        else:
            doc = SourceDocument(
                security_id=security_id, kind=kind, title=f"{title}: {instrument}",
                publisher=publisher, url=url, listing_url=listing_url,
                file_path=stored_file.as_posix(), sha256=sha,
                published_on=max(bars), retrieved_at=now, terms_note=terms_note)
            s.add(doc)
        s.flush()
        merged = merge_bars(s, instrument, bars, doc.id, accept_revisions=accept_revisions,
                            activity=activity)
        traded = sum(1 for _, v in bars.values() if v)
        s.flush()
        # One status row covers the source, so describe every instrument that now has prices.
        loaded = (s.query(PriceBar.instrument_id, func.count(), func.min(PriceBar.trade_date),
                          func.max(PriceBar.trade_date))
                  .group_by(PriceBar.instrument_id).order_by(PriceBar.instrument_id).all())
        held_back = merged.revisions and not accept_revisions
        latest = max(hi for *_, hi in loaded)
        s.merge(DataSourceStatus(
            source="dse_prices", last_success_at=now, last_attempt_at=now,
            status="partial" if held_back else "ok", max_age_hours=24 * 5,
            detail="; ".join(f"{iid} {n} days ({lo} to {hi})" for iid, n, lo, hi in loaded)
                   + f". Latest trading day stored: {latest}. Source: DSE published prices."
                   + (f" {instrument}: {len(merged.revisions)} past close(s) revised by the source and not "
                      f"applied; review them." if held_back else "")))
        s.commit()
    print(f"Read {len(bars)} days for {instrument}: {min(bars)} to {max(bars)}, "
          f"{len(bars) - traded} days without a trade ({(len(bars) - traded) / len(bars):.1%}). "
          f"Stored {stored_file} (sha256 {sha[:16]}).\nMerge: {merged.summary()}.")
    for day, old, new in merged.revisions[:10]:
        print(f"  revised by the source: {day} stored {old}, download says {new}")
    # A held-back revision is a failure a person must look at, so scheduled runs go red.
    return 2 if held_back else 0




if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
