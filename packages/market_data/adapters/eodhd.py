"""Adapter for EODHD (https://eodhd.com). UNTESTED: no key exists; written from the provider's documentation
as read on 2026-10-08 (docs/PROVIDER_EVALUATION.md).

  history  GET https://eodhd.com/api/eod/NMB.DSE?api_token=<key>&fmt=json&from=YYYY-MM-DD&to=YYYY-MM-DD&order=a
           -> [{"date", "open", "high", "low", "close", "adjusted_close", "volume"}]
  symbols  DSE securities are "<TICKER>.DSE" (exchange code DSE, MIC XDAR). NSE Kenya is not covered.

The key travels in the query string (EODHD offers no header), so it is never written into the recorded source
URL and never into an error message: requests' own exception text contains the full URL, so only the exception's
type is kept.

Licensing (owner decision pending): EODHD's personal plans are for personal use only, and its $399 internal-use
plan says "Displaying it or sharing it with people outside your company is not permitted"; a public website needs
the Enterprise or Custom plan, by agreement. Its pages also disagree on whether prices come from exchange feeds
or are aggregated, which matters for provenance.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import requests

from packages.market_data.provider import (CURRENT, Bar, Capabilities, History, MarketDataProvider,
                                           ProviderUnavailable, Quote, RawAnswer)

BASE = "https://eodhd.com/api"
CURRENCY = {"DSE": "TZS", "USE": "UGX"}


def _d(v) -> Decimal | None:
    return None if v is None or v == "" else Decimal(str(v))


class EodhdProvider(MarketDataProvider):
    id = "eodhd"
    name = "EODHD"
    capabilities = Capabilities(quote=True, history=True, exchanges_covered=["DSE", "USE"], timing=CURRENT)

    def __init__(self, api_key: str, session: requests.Session | None = None, timeout: float = 30):
        if not api_key:
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.", "EODHD_API_KEY is not set")
        self._key = api_key
        self.http = session or requests
        self.timeout = timeout

    def symbol_for(self, instrument_id: str) -> str:
        exchange, ticker = instrument_id.split(":", 1)
        return f"{ticker}.{exchange}"

    def history(self, symbol: str, days: int) -> History:
        to = date.today()
        params = {"fmt": "json", "from": (to - timedelta(days=days)).isoformat(), "to": to.isoformat(), "order": "a"}
        url = f"{BASE}/eod/{symbol}"
        try:
            r = self.http.get(url, params={**params, "api_token": self._key}, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.",
                                      f"{type(exc).__name__} calling /eod/{symbol}") from exc
        raw = RawAnswer(url=f"{url}?" + "&".join(f"{k}={v}" for k, v in params.items()),     # no token
                        content=r.content, retrieved_at=datetime.now(timezone.utc))
        if r.status_code != 200:
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.",
                                      f"HTTP {r.status_code} for /eod/{symbol}")
        try:
            rows = json.loads(r.content)
        except ValueError as exc:
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.", "answer was not JSON") from exc
        bars = [Bar(trade_date=date.fromisoformat(x["date"]), close=_d(x["close"]), volume=_d(x.get("volume")),
                    open=_d(x.get("open")), high=_d(x.get("high")), low=_d(x.get("low")))
                for x in rows if isinstance(x, dict) and x.get("close") not in (None, "")]
        if not bars:
            raise ProviderUnavailable(self.id, "No recent prices were published for this security.", f"{symbol}: empty")
        exchange = symbol.rsplit(".", 1)[-1]
        return History(bars=bars, raw=raw, currency=CURRENCY.get(exchange, "TZS"))

    def latest_quote(self, symbol: str) -> Quote:
        h = self.history(symbol, 14)
        last = h.bars[-1]
        prev = h.bars[-2].close if len(h.bars) > 1 else None
        return Quote(symbol=symbol, price=last.close, currency=h.currency, as_of=last.trade_date, timing=CURRENT,
                     previous_close=prev, volume=last.volume)
