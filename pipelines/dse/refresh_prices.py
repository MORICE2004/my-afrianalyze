r"""Refresh the last weeks of DSE prices for every share that already has a stored history.

    .venv\Scripts\python -m pipelines.dse.refresh_prices            # used by .github/workflows/refresh-data.yml

Only shares already loaded are refreshed. A share's FIRST load is a deliberate ten-year download that passes the
unexplained-jump check over its whole history (pipelines.dse.import_public_prices); a short refresh must not
slip in a share that was refused there (on 2026-10-07: KA, NICO, NMG, TTP, USL, VODA, AFRIPRISE, JATU).
Every import merges (pipelines/dse/merge.py), so history is never deleted. One failing share does not stop the
others; the exit code is 1 if any share failed or had a revision held back for review.

Prices come from the first USABLE provider for the DSE in the configured order (packages/market_data/registry.py:
config/market_data.json, MARKET_DATA_PRIORITY). Today that is the DSE's own website; a paid provider is used only
once its key is set AND its terms are accepted. Whichever is used is recorded as the publisher of the stored file.
"""
from __future__ import annotations

import sys
import time

from packages.database.models import PriceBar, Security
from packages.database.session import SessionLocal
from packages.market_data import registry
from packages.market_data.provider import ProviderUnavailable
from pipelines.dse import import_public_prices


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
    providers = registry.usable("DSE", "history")
    if not providers:
        print("No market-data provider is usable for the DSE: "
              + "; ".join(f"{e.id} {e.state} ({e.state_reason})" for e in registry.entries()))
        return 1
    provider = providers[0]
    entry = next(e for e in registry.entries() if e.id == provider.id)
    print(f"Provider: {provider.name}")
    failed = []
    for code in codes:
        time.sleep(1)
        instrument = f"DSE:{code}"
        try:
            hist = provider.history(provider.symbol_for(instrument), int(days))
        except ProviderUnavailable as exc:
            print(f"{code}: download failed ({exc.detail or exc.public})")
            failed.append(code)
            continue
        bars = {b.trade_date: (b.close, b.volume) for b in hist.bars}
        activity = {b.trade_date: b.activity() for b in hist.bars}
        if provider.id == "dse_public":
            rc = import_public_prices.store_and_merge(instrument, hist.raw.content, bars, activity, url=hist.raw.url)
        else:
            rc = import_public_prices.store_and_merge(
                instrument, hist.raw.content, bars, activity, url=hist.raw.url, kind="provider_price_file",
                publisher=provider.name, title=f"{provider.name} end-of-day prices", listing_url=None,
                terms_note=entry.note)
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
