"""The market-data provider layer without the network: registry states, adapters parsing the documented
answers, the EODHD key never reaching a stored URL or an error, and the reconciliation rule. Synthetic answers
shaped like each provider's documentation (no key exists for Mansa or EODHD, so their live answers are UNTESTED)."""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal as D

import pytest
import requests

from packages.core.config import settings
from packages.market_data import reconcile, registry
from packages.market_data.adapters.dse_public import DsePublicProvider
from packages.market_data.adapters.eodhd import EodhdProvider
from packages.market_data.adapters.mansa import MansaProvider
from packages.market_data.provider import ProviderUnavailable

SECRET = "not-a-real-key-used-only-in-tests"


class FakeResponse:
    def __init__(self, payload, status=200):
        self.content = json.dumps(payload).encode()
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


class FakeHttp:
    def __init__(self, payload=None, status=200, exc=None):
        self.payload, self.status, self.exc, self.calls = payload, status, exc, []

    def get(self, url, **kw):
        self.calls.append((url, kw))
        if self.exc:
            raise self.exc
        return FakeResponse(self.payload, self.status)


# ------------------------------------------------------------------ registry

def test_without_keys_only_the_exchanges_own_files_are_usable(monkeypatch):
    monkeypatch.setattr(settings, "MANSA_API_KEY", "")
    monkeypatch.setattr(settings, "EODHD_API_KEY", "")
    monkeypatch.setattr(settings, "MARKET_DATA_PRIORITY", "")
    states = {e.id: e.state for e in registry.entries()}
    assert states == {"dse_public": "READY", "mansa": "NOT_CONFIGURED", "eodhd": "NOT_CONFIGURED"}
    assert [p.id for p in registry.usable("DSE", "history")] == ["dse_public"]


def test_a_key_alone_does_not_switch_on_a_provider_whose_terms_are_unresolved(monkeypatch):
    monkeypatch.setattr(settings, "MANSA_API_KEY", SECRET)
    monkeypatch.setattr(settings, "MARKET_DATA_PRIORITY", "mansa,dse_public")
    entries = registry.entries()
    assert [e.id for e in entries][:2] == ["mansa", "dse_public"]          # the priority setting reorders
    assert entries[0].state == "LICENSE_REVIEW_REQUIRED"
    assert [p.id for p in registry.usable("DSE", "history")] == ["dse_public"]


# ------------------------------------------------------------------ adapters

def _dse_rows(code="NMB"):
    return {"success": True, "data": [
        {"trade_date": "2026-10-05T00:00:00", "company": code, "closing_price": 2030, "volume": 602877,
         "opening_price": 2100, "high": 2100, "low": 2010, "turnover": 1220070790, "market_cap": 10150000000000},
        {"trade_date": "2026-10-06T00:00:00", "company": code, "closing_price": 2040, "volume": 317656,
         "opening_price": 2120, "high": 2120, "low": 2030, "turnover": 646843800, "market_cap": 10200000000000}]}


def test_dse_adapter_reads_every_published_field():
    p = DsePublicProvider(session=FakeHttp(_dse_rows()))
    h = p.history("NMB", 30)
    last = h.bars[-1]
    assert (last.trade_date, last.close, last.volume, last.turnover, last.high) == (
        date(2026, 10, 6), D("2040"), D("317656"), D("646843800"), D("2120"))
    q = p.latest_quote("NMB")
    assert q.timing == "CURRENT" and q.previous_close == D("2030") and q.as_of == date(2026, 10, 6)


def test_dse_adapter_refuses_an_answer_for_another_company():
    p = DsePublicProvider(session=FakeHttp(_dse_rows("CRDB")))
    with pytest.raises(ProviderUnavailable) as e:
        p.history("NMB", 30)
    assert "CRDB" in e.value.detail and "temporarily unavailable" in e.value.public


def test_mansa_adapter_reads_the_documented_history_and_sends_the_key_in_a_header():
    http = FakeHttp({"success": True, "data": {"currency": "TZS", "price_unit": "major", "points": [
        {"date": "2026-10-05", "open": 2100, "high": 2100, "low": 2010, "close": 2030, "adj_close": 2030, "volume": 602877},
        {"date": "2026-10-06", "open": 2120, "high": 2120, "low": 2030, "close": 2040, "adj_close": 2040, "volume": 317656}]},
        "meta": {"data_freshness": "daily"}})
    h = MansaProvider(SECRET, session=http).history("NMB", 30)
    assert [b.close for b in h.bars] == [D("2030"), D("2040")] and h.currency == "TZS"
    url, kw = http.calls[0]
    assert kw["headers"]["Authorization"] == f"Bearer {SECRET}"
    assert SECRET not in h.raw.url and SECRET not in url


def test_eodhd_key_never_reaches_the_recorded_url_or_an_error():
    http = FakeHttp([{"date": "2026-10-06", "open": 2120, "high": 2120, "low": 2030, "close": 2040,
                      "adjusted_close": 2040, "volume": 317656}])
    p = EodhdProvider(SECRET, session=http)
    h = p.history(p.symbol_for("DSE:NMB"), 30)
    assert p.symbol_for("DSE:NMB") == "NMB.DSE" and h.bars[0].close == D("2040")
    assert SECRET not in h.raw.url
    # requests puts the full URL, token included, into its exception text: none of it may surface.
    failing = EodhdProvider(SECRET, session=FakeHttp(exc=requests.ConnectionError(
        f"https://eodhd.com/api/eod/NMB.DSE?api_token={SECRET}")))
    with pytest.raises(ProviderUnavailable) as e:
        failing.history("NMB.DSE", 30)
    assert SECRET not in str(e.value) and SECRET not in e.value.detail and SECRET not in e.value.public


def test_an_adapter_never_invents_a_capability():
    with pytest.raises(ProviderUnavailable) as e:
        DsePublicProvider().search("NMB")
    assert "not available" in e.value.public


# ------------------------------------------------------------------ reconciliation

def _cmp(b, cur_b="TZS"):
    return reconcile.compare("DSE:NMB", date(2026, 10, 6), provider_a="DSE", symbol_a="NMB", close_a=D("2040"),
                             currency_a="TZS", provider_b="Other", symbol_b="NMB.DSE", close_b=D(b),
                             currency_b=cur_b, tolerance_pct=D("0.005"))


def test_reconciliation_matches_within_the_tolerance_and_flags_beyond_it():
    assert _cmp("2045")["status"] == "MATCH"                       # 0.25%
    r = _cmp("2100")                                               # 2.9%
    assert r["status"] == "CONFLICTING_SOURCE" and r["difference"] == D("60")
    assert r["close_a"] == D("2040") and r["close_b"] == D("2100")  # both kept, never averaged


def test_a_different_currency_is_not_compared():
    assert _cmp("2040", "USD")["status"] == "CURRENCY_MISMATCH"
