r"""Compare the stored closes with every other usable provider and record each comparison.

    .venv\Scripts\python -m pipelines.reconcile_prices            # last 10 days, every stored DSE share

The stored close came from the primary provider (its publisher is on the bar's source document). Each other
provider that is READY for the DSE is asked for the same days; every day both have is recorded in
price_reconciliations with both values, both providers' codes, the difference and MATCH or CONFLICTING_SOURCE
(tolerance: config/market_data.json). A conflict changes nothing that is stored: the quote endpoint then shows
the day as CONFLICTING_SOURCE, and the administrator page lists it.

With no second provider configured (today: no key for Mansa or EODHD) this says so and exits 0.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal

from packages.core.config import settings
from packages.database.models import PriceBar, Security, SourceDocument
from packages.database.session import SessionLocal
from packages.market_data import reconcile, registry
from packages.market_data.provider import ProviderUnavailable


def main(argv: list[str]) -> int:
    days = int(argv[0]) if argv else 10
    tolerance = Decimal(json.loads((settings.CONFIG_DIR / "market_data.json").read_text(encoding="utf-8"))
                        ["reconcile_tolerance_pct"])
    usable = registry.usable("DSE", "history")
    others = usable[1:]
    if not others:
        print("Nothing to reconcile: fewer than two usable providers for the DSE. "
              + "; ".join(f"{e.id}: {e.state}" + (f" ({e.state_reason})" if e.state_reason else "")
                          for e in registry.entries()))
        return 0
    conflicts = recorded = failures = 0
    with SessionLocal() as s:
        shares = [sec for sec in s.query(Security).filter_by(exchange="DSE")
                  if s.query(PriceBar).filter_by(instrument_id=sec.id).first()]
        for sec in shares:
            bars = (s.query(PriceBar).filter_by(instrument_id=sec.id).order_by(PriceBar.trade_date.desc())
                    .limit(days).all())
            for other in others:
                try:
                    hist = other.history(other.symbol_for(sec.id), days + 7)
                except ProviderUnavailable as exc:
                    print(f"{sec.id} {other.id}: {exc.detail or exc.public}")
                    failures += 1
                    continue
                theirs = {b.trade_date: b.close for b in hist.bars}
                for bar in bars:
                    if bar.trade_date not in theirs:
                        continue
                    doc = s.get(SourceDocument, bar.source_document_id)
                    result = reconcile.compare(
                        sec.id, bar.trade_date, provider_a=(doc.publisher if doc else "stored"),
                        symbol_a=sec.local_ticker, close_a=bar.close, currency_a=sec.currency,
                        provider_b=other.name, symbol_b=other.symbol_for(sec.id), close_b=theirs[bar.trade_date],
                        currency_b=hist.currency, tolerance_pct=tolerance)
                    reconcile.record(s, result)
                    recorded += 1
                    if result["status"] != reconcile.MATCH:
                        conflicts += 1
                        print(f"{sec.id} {bar.trade_date}: {result['status']} stored {bar.close}, "
                              f"{other.name} {theirs[bar.trade_date]} ({result['difference_pct']:.2%})")
        s.commit()
    print(f"Recorded {recorded} comparisons: {conflicts} outside the {tolerance:.1%} tolerance, {failures} provider "
          f"failures.")
    return 1 if conflicts or failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
