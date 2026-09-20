r"""Build the DSE All Share Index (DSEI) daily series from the DSE's public index endpoint.

The DSE serves index levels one date at a time:

    https://dse.co.tz/get/last/traded/indices?from=YYYY-MM-DD

and returns the last traded level at or before that date, with no date of its own. So the only way to
get a history is to ask for each weekday in turn. This script does that slowly (default 0.75s
between requests, one request per weekday, about 35 minutes for ten years), writes every raw answer
to a JSONL file as it goes, and can be re-run to resume: dates already in the file are not asked for
again.

    .venv\Scripts\python -m pipelines.dse.fetch_public_index --from 2016-09-22 --to 2026-09-18

Because the endpoint returns the *last traded* level, a date that repeats the previous level is a day
the index did not move or did not trade. That is recorded as the level with a zero change, which is
how the exchange itself reports a quiet day, and it is what the zero-volume share in the beta rule
(PRODUCT_CONTEXT.md section 74) needs to see.

Owner decision (2026-09-19): use the levels the DSE publishes on its own website rather than waiting
for a data licence. See pipelines/dse/import_public_prices.py for the terms note.

Run `python -m pipelines.dse.import_public_index` afterwards to load the JSONL into the database.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

OUT = Path("data/raw/dse/public/dsei_daily.jsonl")
URL = "https://dse.co.tz/get/last/traded/indices?from={day}"
UA = "Mozilla/5.0 (my-afrianalyze research backfill)"


def _fetch(day: date, timeout: float) -> list[dict]:
    req = urllib.request.Request(URL.format(day=day.isoformat()), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - fixed https host
        payload = json.load(r)
    if not payload.get("success"):
        raise RuntimeError(payload.get("message", "no data"))
    return payload.get("data") or []


def already_done(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    done = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            if not rec.get("error"):        # a failed date stays on the list, so a re-run retries it
                done.add(rec["asked_for"])
    return done


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", required=True, help="First date, YYYY-MM-DD")
    ap.add_argument("--to", dest="end", required=True, help="Last date, YYYY-MM-DD")
    ap.add_argument("--delay", type=float, default=0.75, help="Seconds between requests (default 0.75)")
    ap.add_argument("--timeout", type=float, default=30.0)
    args = ap.parse_args(argv)

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = already_done(OUT)
    if done:
        print(f"{len(done)} dates already fetched; skipping those.")

    days = []
    d = start
    while d <= end:
        if d.weekday() < 5 and d.isoformat() not in done:   # the DSE trades Monday to Friday
            days.append(d)
        d += timedelta(days=1)
    print(f"Asking for {len(days)} dates, {args.delay}s apart (about {len(days) * args.delay / 60:.0f} minutes).")

    failures = 0
    with OUT.open("a", encoding="utf-8") as fh:
        for i, day in enumerate(days, 1):
            try:
                rows = _fetch(day, args.timeout)
            except Exception as exc:                     # network or endpoint hiccup: record and carry on
                failures += 1
                rows = None
                record = {"asked_for": day.isoformat(), "error": str(exc)[:200]}
            else:
                record = {"asked_for": day.isoformat(), "indices": rows}
            record["retrieved_at"] = datetime.now(timezone.utc).isoformat()
            record["url"] = URL.format(day=day.isoformat())
            fh.write(json.dumps(record) + "\n")
            fh.flush()
            if i % 100 == 0 or i == len(days):
                dsei = next((r for r in (rows or []) if r.get("Code") == "DSEI"), None)
                print(f"  {i}/{len(days)}  {day}  DSEI {dsei['ClosingPrice'] if dsei else '-'}"
                      f"  ({failures} failed)")
            time.sleep(args.delay)

    print(f"Wrote {OUT} ({failures} dates failed; re-run to retry only those that are missing).")
    return 1 if failures and failures == len(days) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
