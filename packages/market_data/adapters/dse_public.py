"""Adapter for the prices the Dar es Salaam Stock Exchange publishes on its own website.

Endpoints (robots.txt allows them; the owner decided on 2026-09-19 to use them, docs/COMPLIANCE_NOTES.md):

  history  https://dse.co.tz/api/get/market/prices/for/range/duration?security_code=NMB&days=30&class=EQUITY
           one row per session: trade_date, opening_price, high, low, closing_price, volume, turnover,
           shares_in_issue, market_cap. A day without a trade repeats the previous close with volume 0 and
           high = low = 0.
  indices  https://dse.co.tz/get/last/traded/indices?from=YYYY-MM-DD
           DSEI, TSI and the sector indices BI, IA, CS for the last session at or before that date; the answer
           carries no date of its own (pipelines/dse/fetch_public_index.py handles that).

Not used: https://dse.co.tz/api/get/live/market/prices returns a price and change per share but no time, so
its prices cannot be labelled CURRENT or DELAYED honestly (checked 2026-10-08 at 11:28 in Dar es Salaam).

Licensing: RESTRICTED. The DSE Data Vending Policy v1.2 restricts redistribution (cl. 23.1); public display
is switched by DSE_PUBLIC_DISPLAY (packages/core/config.py).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import requests

from packages.market_data.provider import (CURRENT, Bar, Capabilities, History, MarketDataProvider,
                                           ProviderUnavailable, Quote, RawAnswer)
from pipelines.dse.import_public_prices import parse_rows

HISTORY_URL = ("https://dse.co.tz/api/get/market/prices/for/range/duration"
               "?security_code={code}&days={days}&class=EQUITY")
UA = {"User-Agent": "Mozilla/5.0 (AfriEdge market data)"}


class DsePublicProvider(MarketDataProvider):
    id = "dse_public"
    name = "Dar es Salaam Stock Exchange (public website)"
    # Index levels come one date per request, so they are collected by pipelines/dse/fetch_public_index.py.
    capabilities = Capabilities(quote=True, history=True, exchanges_covered=["DSE"], timing=CURRENT)

    def __init__(self, session: requests.Session | None = None, timeout: float = 60):
        self.http = session or requests
        self.timeout = timeout

    def history(self, symbol: str, days: int) -> History:
        url = HISTORY_URL.format(code=symbol, days=days)
        try:
            r = self.http.get(url, headers=UA, timeout=self.timeout)
            r.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.",
                                      f"{type(exc).__name__} fetching {url}") from exc
        retrieved = datetime.now(timezone.utc)
        try:
            payload = json.loads(r.content)
        except ValueError as exc:
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.",
                                      f"the answer for {symbol} was not JSON") from exc
        rows = payload.get("data") or []
        if not payload.get("success") or not rows:
            raise ProviderUnavailable(self.id, "No recent prices were published for this security.",
                                      f"{symbol}: {payload.get('message', 'empty answer')}")
        codes = {str(row.get("company", "")).upper() for row in rows}
        if codes != {symbol.upper()}:
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.",
                                      f"asked for {symbol}, the answer is for {sorted(codes)}")
        closes, activity = parse_rows(rows)
        bars = [Bar(trade_date=d, close=c, volume=v, **activity[d]) for d, (c, v) in sorted(closes.items())]
        return History(bars=bars, raw=RawAnswer(url=url, content=r.content, retrieved_at=retrieved), currency="TZS")

    def latest_quote(self, symbol: str) -> Quote:
        h = self.history(symbol, 10)
        last = h.bars[-1]
        prev = h.bars[-2].close if len(h.bars) > 1 else None
        return Quote(symbol=symbol, price=last.close, currency="TZS", as_of=last.trade_date, timing=CURRENT,
                     previous_close=prev, volume=last.volume)
