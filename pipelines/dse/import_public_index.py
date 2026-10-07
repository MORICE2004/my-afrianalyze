r"""Load the DSE index levels collected by `fetch_public_index` into the database.

    .venv\Scripts\python -m pipelines.dse.import_public_index --code DSEI --instrument DSE:DSEI

The endpoint gives no date of its own: it returns the last traded level at or before the date asked
for. Each answer also carries that day's `Change`, so this importer checks the series against itself
-- level today minus change today should equal the level on the previous trading day. Dates where
that check fails are reported and NOT loaded, because a level we cannot reconcile is not a level we
can put a beta on.

A date whose level and change repeat the day before is a day the index did not move; it is kept,
because the beta rule needs to see quiet days (PRODUCT_CONTEXT.md section 74).

Owner decision (2026-09-19): use the levels the DSE publishes publicly. Terms note as in
pipelines/dse/import_public_prices.py.
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

from packages.database.models import DataSourceStatus, PriceBar, Security, SourceDocument
from packages.database.session import SessionLocal
from pipelines.dse.import_public_prices import TERMS_NOTE
from pipelines.dse.merge import merge_bars, stored_bars

SRC = Path("data/raw/dse/public/dsei_daily.jsonl")
STORE = Path("data/raw/dse/public")
TOLERANCE = Decimal("0.02")   # the published levels are rounded to two decimals


def _num(text: str) -> Decimal:
    return Decimal(str(text).replace(",", "").strip())


def read_levels(path: Path, code: str) -> tuple[dict[date, tuple[Decimal, Decimal]], list[str]]:
    """Return {day: (level, change)} and a list of complaints about the file."""
    levels: dict[date, tuple[Decimal, Decimal]] = {}
    problems: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        day = date.fromisoformat(rec["asked_for"])
        if rec.get("error"):
            problems.append(f"{day}: not fetched ({rec['error']})")
            continue
        row = next((r for r in rec.get("indices") or [] if r.get("Code") == code), None)
        if row is None:
            problems.append(f"{day}: the answer held no {code} level")
            continue
        levels[day] = (_num(row["ClosingPrice"]), _num(row["Change"]))
    return levels, problems


def reconcile(levels: dict[date, tuple[Decimal, Decimal]],
              stored: dict[date, Decimal] | None = None) -> tuple[dict[date, Decimal], list[str]]:
    """Keep only the days whose published change agrees with the move in the level.

    `stored` holds levels already in the database. A refresh file starts after them, so its first day is
    checked against the last stored level before it, instead of being let through unchecked."""
    stored = stored or {}
    days = sorted(levels)
    good: dict[date, Decimal] = {}
    bad: list[str] = []
    for i, day in enumerate(days):
        level, change = levels[day]
        if i == 0:
            before = [d for d in stored if d < day]
            if not before:
                good[day] = level        # nothing before it to check against
                continue
            previous = stored[max(before)]
        else:
            previous = levels[days[i - 1]][0]
        if abs((previous + change) - level) <= TOLERANCE:
            good[day] = level
        else:
            bad.append(f"{day}: level {level} with change {change} does not follow {previous}")
    return good, bad


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", default="DSEI", help="Index code in the DSE answer (DSEI, TSI, BI ...)")
    ap.add_argument("--instrument", default="DSE:DSEI", help="Instrument id to store it under")
    ap.add_argument("--file", default=str(SRC))
    ap.add_argument("--accept-revisions", action="store_true",
                    help="Overwrite stored levels that the file reports differently (check them first)")
    ap.add_argument("--allow-unreconciled", action="store_true",
                    help="Load days whose published change does not follow the previous level")
    args = ap.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        print(f"Not found: {path}. Run pipelines.dse.fetch_public_index first.")
        return 1

    levels, problems = read_levels(path, args.code)
    if not levels:
        print(f"No {args.code} levels in {path}.")
        return 1
    with SessionLocal() as s:
        already = {d: v[0] for d, v in stored_bars(s, args.instrument).items()}
    good, bad = reconcile(levels, already)
    kept = {d: v[0] for d, v in levels.items()} if args.allow_unreconciled else good

    print(f"{len(levels)} dates read, {len(kept)} loaded.")
    for p in problems[:10]:
        print("  missing:", p)
    for b in bad[:10]:
        print("  does not reconcile:", b)
    if len(problems) > 10 or len(bad) > 10:
        print(f"  ... {len(problems)} missing, {len(bad)} unreconciled in total")
    if not kept:
        print("Nothing left to load.")
        return 1

    content = path.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    # Keep our own copy under its hash, so the record does not depend on where the download happened to be
    # (a refresh runner's working folder disappears when the run ends).
    STORE.mkdir(parents=True, exist_ok=True)
    stored_file = STORE / f"{args.instrument.replace(':', '_')}_index_{sha[:12]}.jsonl"
    if stored_file.resolve() != path.resolve():
        shutil.copyfile(path, stored_file)
    now = datetime.now(timezone.utc)
    flat = sorted(set(kept.values()))
    with SessionLocal() as s:
        doc = s.query(SourceDocument).filter_by(kind="public_index_file", sha256=sha).first()
        if doc is not None:                  # the same collected file again: keep one record
            doc.retrieved_at = now
            doc.file_path = stored_file.as_posix()
        else:
            doc = SourceDocument(
                security_id=args.instrument if s.get(Security, args.instrument) else None,
                kind="public_index_file",
                title=f"DSE published index levels: {args.code}",
                publisher="Dar es Salaam Stock Exchange",
                url="https://dse.co.tz/get/last/traded/indices?from=<date>, one date per request",
                listing_url="https://dse.co.tz/market/data/overview",
                file_path=stored_file.as_posix(), sha256=sha,
                published_on=max(kept), retrieved_at=now, terms_note=TERMS_NOTE)
            s.add(doc)
        s.flush()
        merged = merge_bars(s, args.instrument, {d: (lvl, None) for d, lvl in kept.items()}, doc.id,
                            accept_revisions=args.accept_revisions)
        s.flush()
        total = s.query(PriceBar).filter_by(instrument_id=args.instrument).count()
        first, last = (s.query(PriceBar.trade_date).filter_by(instrument_id=args.instrument)
                       .order_by(PriceBar.trade_date).first()[0],
                       s.query(PriceBar.trade_date).filter_by(instrument_id=args.instrument)
                       .order_by(PriceBar.trade_date.desc()).first()[0])
        held_back = merged.revisions and not args.accept_revisions
        s.merge(DataSourceStatus(
            source="dse_index", last_success_at=now, last_attempt_at=now,
            status="ok" if not (bad or problems or held_back) else "partial", max_age_hours=24 * 5,
            detail=f"{total} days of {args.code} stored ({first} to {last}). Last refresh: {merged.summary()}; "
                   f"{len(bad)} did not reconcile, {len(problems)} were not fetched. "
                   f"Source: DSE published index levels."))
        s.commit()
    print(f"Read {len(kept)} days of {args.code} ({min(kept)} to {max(kept)}, levels {flat[0]} to {flat[-1]}, "
          f"sha256 {sha[:16]}).\nMerge into {args.instrument}: {merged.summary()}.")
    for day, old, new in merged.revisions[:10]:
        print(f"  revised by the source: {day} stored {old}, file says {new}")
    return 2 if held_back else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
