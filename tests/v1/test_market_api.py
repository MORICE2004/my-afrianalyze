"""Quotes, price series, search ranking, the markets page and the research stream, against the local database
(real DSE data; skipped where it is not loaded, as in CI)."""
from __future__ import annotations

import json
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from packages.database.models import PriceBar
from packages.database.session import SessionLocal

try:
    with SessionLocal() as _s:
        _loaded = _s.query(PriceBar).filter_by(instrument_id="DSE:NMB").first() is not None
except Exception:
    _loaded = False
pytestmark = pytest.mark.skipif(not _loaded, reason="DSE prices not loaded locally")

client = TestClient(app)


def test_a_quote_carries_its_date_source_currency_and_freshness_never_live():
    q = client.get("/api/v1/securities/DSE:NMB/quote").json()
    assert q["available"] and q["currency"] == "TZS" and q["licensing"] == "RESTRICTED"
    assert q["timing"] in ("CURRENT", "STALE") and q["public_label"] in ("Updated", "Out of date")
    assert "LIVE" not in json.dumps(q).upper().replace("NOT LIVE", "")
    assert q["source"]["publisher"] == "Dar es Salaam Stock Exchange" and q["trade_date"]
    with SessionLocal() as s:
        last = s.query(PriceBar).filter_by(instrument_id="DSE:NMB").order_by(PriceBar.trade_date.desc()).first()
    assert Decimal(q["price"]) == last.close and q["trade_date"] == last.trade_date.isoformat()


def test_a_no_trade_day_shows_no_high_or_low():
    with SessionLocal() as s:
        quiet = (s.query(PriceBar).filter(PriceBar.volume == 0, PriceBar.instrument_id.like("DSE:%"))
                 .order_by(PriceBar.trade_date.desc()).first())
    if quiet is None:
        pytest.skip("no stored no-trade day")
    q = client.get(f"/api/v1/securities/{quiet.instrument_id}/quote").json()
    if q["trade_date"] == quiet.trade_date.isoformat():
        assert q["traded"] is False and q["high"] is None and q["low"] is None and q["turnover"] is None


def test_index_series_leave_out_round_trip_days_and_say_so():
    r = client.get("/api/v1/prices/DSE:DSEI", params={"days": 3700}).json()
    days = {p["date"] for p in r["points"]}
    assert "2026-08-24" not in days and "2026-08-21" in days
    assert any("source error" in n for n in r["notes"])


def test_share_series_are_split_adjusted():
    r = client.get("/api/v1/prices/DSE:NMB", params={"days": 120}).json()
    by_day = {p["date"]: Decimal(p["close"]) for p in r["points"]}
    # NMB split 1:10 on 2026-08-24; the 2026-08-19 close of 17,700 is shown as 1,770.
    assert by_day.get("2026-08-19") == Decimal("1770")
    assert any("split" in n for n in r["notes"])


@pytest.mark.parametrize("q, first", [("nmb", "DSE:NMB"), ("NMB Bank", "DSE:NMB"), ("crdb bnk", "DSE:CRDB"),
                                      ("cr", "DSE:CRDB"), ("KE1000001402", "NSE:SCOM")])
def test_search_finds_by_ticker_name_isin_and_a_typo(q, first):
    r = client.get("/api/v1/securities", params={"q": q}).json()
    assert r["results"] and r["results"][0]["id"] == first
    top = r["results"][0]
    assert {"exchange", "exchange_name", "country", "currency", "has_report"} <= set(top)


def test_search_with_no_match_is_empty_not_an_error():
    r = client.get("/api/v1/securities", params={"q": "zzzz"})
    assert r.status_code == 200 and r.json()["results"] == []


def test_the_markets_page_has_session_activity_and_the_dse_sector_indices():
    o = client.get("/api/v1/markets/overview").json()
    assert o["session"]["kind"] == "End of day" and o["session"]["latest_session"]
    a = o["activity"]
    assert a["available"] and a["currency"] == "TZS" and Decimal(a["turnover"]) >= 0
    assert a["securities_traded"] <= a["securities_stored"]
    ids = [i["id"] for i in o["sectors"]["indices"]]
    assert ids == ["DSE:BI", "DSE:IA", "DSE:CS"]
    kenya = next(m for m in o["markets"] if m["exchange"] == "NSE")
    assert kenya["index"]["public_reason"] == "Kenya market data is not yet connected."


def test_the_research_stream_sends_each_stage_then_the_report():
    lines = client.get("/api/v1/research/DSE:NMB/stream").text.splitlines()
    events = [json.loads(x) for x in lines]
    kinds = [e["event"] for e in events]
    assert kinds[:4] == ["step", "security", "step", "quote"]
    stages = [e["data"]["stage"] for e in events if e["event"] == "stage"]
    assert stages == ["sources", "documents", "extraction", "validation", "calculations", "valuation", "technical",
                      "risk", "synthesis", "ai_interpretation"]
    assert kinds.index("report") > max(i for i, k in enumerate(kinds) if k == "stage")
    assert kinds[-1] == "done" and all(e["data"]["duration_ms"] >= 0 for e in events if e["event"] == "stage")
    report = next(e["data"] for e in events if e["event"] == "report")
    plain = client.get("/api/v1/reports/DSE:NMB").json()
    assert report["header"]["recommendation"] == plain["header"]["recommendation"]


def test_a_company_without_research_streams_its_price_and_says_why():
    events = [json.loads(x) for x in client.get("/api/v1/research/DSE:TBL/stream").text.splitlines()]
    kinds = [e["event"] for e in events]
    assert "quote" in kinds and "report" not in kinds
    gone = next(e for e in events if e["event"] == "unavailable")
    assert gone["status"] == "INSUFFICIENT_DATA" and "annual reports" in gone["reason"]


def test_an_unknown_company_in_the_stream():
    events = [json.loads(x) for x in client.get("/api/v1/research/DSE:NOPE/stream").text.splitlines()]
    assert events == [{"event": "unavailable", "status": "NOT_FOUND", "reason": "No listed company matches DSE:NOPE."}]
