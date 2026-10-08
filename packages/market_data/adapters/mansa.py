"""Adapter for Mansa API (https://mansaapi.com). UNTESTED: no key exists; written from the provider's OpenAPI
spec and docs as read on 2026-10-08 (docs/PROVIDER_EVALUATION.md).

  history  GET /api/v1/markets/exchanges/{exchange}/stocks/{ticker}/history?from=YYYY-MM-DD&to=YYYY-MM-DD&order=asc
           -> {"success": true, "data": {"currency", "price_unit", "points": [{date, open, high, low, close,
               adj_close, volume}]}, "meta": {"data_freshness": "daily", ...}}       (Pro tier and above)
  auth     Authorization: Bearer <MANSA_API_KEY>

The latest-quote endpoint's fields are not documented, so the quote is taken from the last two history points
(documented), which is the end-of-day close: CURRENT, never DELAYED. Mansa states its prices are as published
and not adjusted for splits; AfriEdge applies its own recorded corporate actions (config/corporate_actions.json).

Licensing (owner decision pending): mansaapi.com/licensing allows display "inside your own app ... or website"
on every tier, but caching only "up to 7 days" on Professional, and calls "building a stored copy of our datasets"
redistribution. AfriEdge stores every close permanently, so written confirmation is needed before use.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import requests

from packages.market_data.provider import (CURRENT, Bar, Capabilities, History, MarketDataProvider,
                                           ProviderUnavailable, Quote, RawAnswer)

BASE = "https://mansaapi.com"


def _d(v) -> Decimal | None:
    return None if v is None or v == "" else Decimal(str(v))


class MansaProvider(MarketDataProvider):
    id = "mansa"
    name = "Mansa API"
    capabilities = Capabilities(quote=True, history=True, exchanges_covered=["DSE", "NSE", "USE"], timing=CURRENT)

    def __init__(self, api_key: str, session: requests.Session | None = None, timeout: float = 30):
        if not api_key:
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.", "MANSA_API_KEY is not set")
        self._key = api_key
        self.http = session or requests
        self.timeout = timeout

    def _get(self, path: str, params: dict) -> tuple[dict, RawAnswer]:
        url = f"{BASE}{path}"
        try:
            r = self.http.get(url, params=params, headers={"Authorization": f"Bearer {self._key}"}, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.",
                                      f"{type(exc).__name__} calling {path}") from exc
        query = "&".join(f"{k}={v}" for k, v in params.items())
        raw = RawAnswer(url=f"{url}?{query}", content=r.content, retrieved_at=datetime.now(timezone.utc))
        try:
            payload = json.loads(r.content)
        except ValueError as exc:
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.",
                                      f"HTTP {r.status_code}, not JSON") from exc
        if r.status_code != 200 or not payload.get("success"):
            err = (payload.get("error") or {}) if isinstance(payload, dict) else {}
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.",
                                      f"HTTP {r.status_code} {err.get('code', '')} {err.get('message', '')}".strip())
        return payload, raw

    def history(self, symbol: str, days: int, exchange: str = "DSE") -> History:
        to = date.today()
        payload, raw = self._get(f"/api/v1/markets/exchanges/{exchange}/stocks/{symbol}/history",
                                 {"from": (to - timedelta(days=days)).isoformat(), "to": to.isoformat(), "order": "asc"})
        data = payload.get("data") or {}
        if data.get("price_unit") not in (None, "major"):
            raise ProviderUnavailable(self.id, "Market data is temporarily unavailable.",
                                      f"unexpected price_unit {data.get('price_unit')!r}")
        bars = []
        for p in data.get("points") or []:
            close = _d(p.get("close"))
            if close is None:
                continue
            bars.append(Bar(trade_date=date.fromisoformat(p["date"]), close=close, volume=_d(p.get("volume")),
                            open=_d(p.get("open")), high=_d(p.get("high")), low=_d(p.get("low"))))
        if not bars:
            raise ProviderUnavailable(self.id, "No recent prices were published for this security.",
                                      f"{exchange}:{symbol}: no points")
        return History(bars=bars, raw=raw, currency=data.get("currency") or "TZS")

    def latest_quote(self, symbol: str) -> Quote:
        h = self.history(symbol, 14)
        last = h.bars[-1]
        prev = h.bars[-2].close if len(h.bars) > 1 else None
        return Quote(symbol=symbol, price=last.close, currency=h.currency, as_of=last.trade_date, timing=CURRENT,
                     previous_close=prev, volume=last.volume)
