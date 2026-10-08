"""API contract against the local database. Needs the NMB pipeline to have been run:

    .venv\\Scripts\\python -m pipelines.load_security_master
    .venv\\Scripts\\python -m pipelines.macro
    .venv\\Scripts\\python -m pipelines.nmb.resolve
    .venv\\Scripts\\python -m pipelines.nmb.load
"""
from __future__ import annotations

from decimal import Decimal

import pypdfium2 as pdfium
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from packages.core.config import AppEnvironment, settings
from packages.database.models import FinancialFact
from packages.database.session import SessionLocal

try:
    with SessionLocal() as _s:
        _loaded = _s.query(FinancialFact).filter_by(security_id="DSE:NMB").first() is not None
except Exception:  # no database or no tables yet (e.g. CI before the pipeline has run)
    _loaded = False
pytestmark = pytest.mark.skipif(not _loaded, reason="NMB data not loaded; run the pipeline first (see module docstring)")

client = TestClient(app)


@pytest.fixture(scope="module")
def report() -> dict:
    r = client.get("/api/v1/reports/DSE:NMB")
    assert r.status_code == 200, r.text
    return r.json()


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def test_health_reports_every_source_with_its_own_freshness():
    h = client.get("/health").json()
    assert h["status"] in {"online", "degraded", "offline"}
    prices = next(s for s in h["sources"] if s["source"] == "dse_prices")
    assert prices["status"] == "ok" and prices["detail"], "DSE prices are loaded, so say so"
    assert "DSE published prices" in prices["detail"], "the health page must name where prices came from"
    # A source that is not ok must never be reported as fresh, and must drag the whole status down.
    for s in h["sources"]:
        if s["status"] != "ok":
            assert s["fresh"] is False, s["source"]
            assert h["status"] != "online"


def test_search_ranks_exact_ticker_first():
    r = client.get("/api/v1/securities", params={"q": "nmb"}).json()
    assert r["results"][0]["id"] == "DSE:NMB"
    assert client.get("/api/v1/securities", params={"q": "zzzz"}).json()["count"] == 0
    assert client.get("/api/v1/securities/DSE:NOPE").status_code == 404


def test_report_is_a_draft_until_a_named_reviewer_publishes_it(report):
    assert report["review"]["status"] == "draft"
    assert report["review"]["run_id"].startswith("RA-")
    assert report["review"]["reviewer"] is None


def test_production_hides_unreviewed_reports(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", AppEnvironment.PRODUCTION)
    r = client.get("/api/v1/reports/DSE:NMB")
    assert r.status_code == 403 and "not been reviewed" in r.json()["detail"]
    assert client.get("/api/v1/reports/DSE:NMB/pdf").status_code in (401, 403)


def test_the_share_price_is_shown_only_with_the_source_it_came_from(report):
    price = report["header"]["price"]
    if not price["available"]:
        assert price["status"] == "BLOCKED" and price["reason"]
        return
    assert price["currency"] == "TZS" and price["trade_date"]
    src = price["source"]
    assert "dse.co.tz" in src["url"] and len(src["sha256"]) == 64 and src["retrieved_at"]
    assert "viewer_url" not in src and "file_url" not in src, "exchange price files are not shown"


def test_a_trade_label_appears_only_when_there_is_a_valuation_behind_it(report):
    # Labels are switched on (owner decision 2026-09-19), but a label needs a target price behind it.
    assert report["trade_labels_enabled"] is True
    rec = report["header"]["recommendation"]
    if rec["available"]:
        assert report["header"]["target_price"]["available"] is True
        assert report["header"]["fair_value_range"]["available"] is True
        assert rec["model_view"] in {"Undervalued", "Fairly valued", "Overvalued", "Inconclusive"}
        if rec["model_view"] == "Inconclusive":
            # The view flips with the cost-of-equity method, so no label at all (robust_view).
            assert "trade_label" not in rec and rec["inconclusive_reason"]
            return
        assert rec["trade_label"] in {"BUY", "HOLD", "SELL"}
        # The label must follow the model view, never contradict it.
        assert (rec["trade_label"] == "BUY") == (rec["model_view"] == "Undervalued")
        assert (rec["trade_label"] == "SELL") == (rec["model_view"] == "Overvalued")
    else:
        assert rec["status"] == "BLOCKED" and rec["reason"]
        assert "trade_label" not in set(_keys(report))
        for block in ("target_price", "fair_value_range"):
            assert report["header"][block]["available"] is False
            assert report["header"][block]["status"] == "BLOCKED"


def test_every_shown_figure_has_status_source_and_units(report):
    shown = 0
    for st in report["statements"]:
        for row in st["rows"]:
            for year, cell in row["cells"].items():
                if not cell["available"]:
                    assert "value" not in cell and cell["reason"]
                    continue
                if row.get("derived"):
                    assert cell["derived"]
                    continue
                shown += 1
                assert cell["status"] in {"VERIFIED", "PARTIALLY_VERIFIED"}
                assert cell["currency"] == "TZS" and cell["unit"] and cell["period_end"] == f"{year}-12-31"
                assert cell["source"]["page"] and cell["source"]["sha256"] and cell["source"]["url"].startswith("https://")
    assert shown >= 240


def test_figure_that_does_not_add_up_in_the_source_is_not_used(report):
    cor = next(r for r in report["ratios"] if r["code"] == "cost_of_risk")["values"]["2021"]
    assert cor["available"] is False and cor["status"] == "CONFLICTING_SOURCE"
    assert "value" not in cor and "p.226" in cor["reason"]
    issues = [c for c in report["conflicts"] if c["kind"] == "SOURCE_INCONSISTENCY"]
    assert {(c["fiscal_year"], c["item_code"]) for c in issues} == {(2020, "gross_loans"), (2020, "ecl_loans")}


def test_stale_inputs_are_flagged(report):
    for key, inp in report["cost_of_equity"]["inputs"].items():
        assert inp is not None, key
        assert inp["status"] in {"VERIFIED", "STALE"} and inp["age_days"] >= 0 and inp["source_url"]


class _User:
    id, role, email = 1, "user", "reader@example.invalid"


@pytest.fixture()
def as_user(monkeypatch):
    """A signed-in reader (role and plan chosen per test) without touching the users table."""
    from apps.api.routers import auth as auth_router

    who = _User()
    app.dependency_overrides[auth_router.current_user] = lambda: who
    monkeypatch.setattr(auth_router, "features", lambda session, user: set(getattr(user, "feats", set())))
    yield who
    app.dependency_overrides.clear()


def test_report_pdf_is_an_export_refused_without_the_entitlement(as_user):
    app.dependency_overrides.clear()
    assert client.get("/api/v1/reports/DSE:NMB/pdf").status_code == 401
    from apps.api.routers import auth as auth_router
    app.dependency_overrides[auth_router.current_user] = lambda: as_user
    assert client.get("/api/v1/reports/DSE:NMB/pdf").status_code == 403


def test_pdf_says_draft_and_carries_the_disclaimer(as_user):
    as_user.feats = {"excel_export"}
    r = client.get("/api/v1/reports/DSE:NMB/pdf")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    pdf = pdfium.PdfDocument(r.content)
    first = pdf[0].get_textpage().get_text_range()
    assert "DRAFT, NOT REVIEWED" in first
    assert "Model view" in first
    whole = " ".join(pdf[i].get_textpage().get_text_range() for i in range(len(pdf)))
    assert "not investment advice" in whole.lower()
    # A trade word may only appear where the model view stands behind it (owner's decision 2026-09-19).
    report = client.get("/api/v1/reports/DSE:NMB").json()
    if not report["header"]["recommendation"].get("available"):
        for word in (" BUY", " SELL", "HOLD"):
            assert word not in whole, "no trade call without a valuation behind it"


def test_source_documents_are_viewed_as_pages_never_downloaded(report, as_user):
    from apps.api.routers import auth as auth_router

    doc = report["sources"]["documents"][0]
    did = doc["document_id"]
    assert doc["viewer_url"].startswith(f"/sources/{did}") and "file_url" not in doc
    # A signed-in reader gets the page count and rendered pages, never the file or its location on disk.
    meta = client.get(f"/api/v1/sources/{did}").json()
    assert meta["pages"] > 0 and "file_path" not in meta and "data/" not in str(meta)
    r = client.get(f"/api/v1/sources/{did}/pages/1")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png" and r.content[1:4] == b"PNG"
    assert "no-store" in r.headers["cache-control"]
    assert client.get(f"/api/v1/sources/{did}/pages/{meta['pages'] + 1}").status_code == 404
    # The original file: refused to a reader, given to an administrator.
    assert client.get(f"/api/v1/sources/{did}/file").status_code == 403
    as_user.role = "admin"
    r = client.get(f"/api/v1/sources/{did}/file")
    assert r.status_code == 200 and r.content[:4] == b"%PDF"
    assert client.get("/api/v1/sources/999999/file").status_code == 404
    # Signed out: nothing at all.
    app.dependency_overrides.pop(auth_router.current_user)
    for path in (f"/api/v1/sources/{did}", f"/api/v1/sources/{did}/pages/1", f"/api/v1/sources/{did}/file"):
        assert client.get(path).status_code == 401, path


def test_price_history_is_capped_to_what_charts_show():
    assert client.get("/api/v1/prices/DSE:NMB?days=3650").status_code == 422


def test_fixed_income_points_carry_sources():
    fi = client.get("/api/v1/fixed-income/TZ").json()
    assert fi["curve"], "no bond auction data loaded"
    for p in fi["curve"]:
        assert p["available"] and p["source_url"].startswith("https://") and p["as_of"]


def test_markets_and_portfolios_do_not_invent_numbers():
    m = client.get("/api/v1/markets/overview").json()
    for x in m["markets"]:
        if x["index"]["available"]:          # only the DSE index is collected; others must stay unavailable
            assert x["index"]["id"] == "DSE:DSEI" and x["index"]["trade_date"] and "change" in x["index"]
        else:
            assert x["index"]["reason"]
    # Commentary is not built, so it must say so rather than show something invented.
    assert m["commentary"]["available"] is False
    # Movers come from stored DSE closes: every mover traded that day, and the coverage is stated.
    mv = m["movers"]
    if mv["available"]:
        assert mv["coverage"] and "Dar es Salaam Stock Exchange" in mv["attribution"]
        for x in mv["gainers"] + mv["losers"]:
            assert Decimal(x["volume"]) > 0 and x["security_id"].startswith("DSE:")
    else:
        assert mv["reason"]
    assert client.get("/api/v1/portfolios").status_code == 401
    ok = {"market": "TZ", "capital": 1_000_000, "currency": "TZS", "risk_profile": "Moderate", "horizon_years": 5}
    r = client.post("/api/v1/portfolio/proposals", json=ok)
    assert r.status_code == 200, "the wizard must never crash, even once prices exist"
    body = r.json()
    assert body["available"] is False and "not implemented" in body["reason"]
    assert "weights" not in body and "positions" not in body
    assert client.post("/api/v1/portfolio/proposals", json=ok | {"currency": "KES"}).status_code == 422
    assert client.post("/api/v1/portfolio/proposals", json=ok | {"capital": -5}).status_code == 422


def test_unknown_or_uncovered_security():
    assert client.get("/api/v1/reports/DSE:NOPE").status_code == 404
    r = client.get("/api/v1/reports/NSE:SCOM")  # in the security master, no reports ingested
    assert r.status_code == 404 and "No research report" in r.json()["detail"]


def test_the_copilot_needs_sign_in_has_a_daily_cap_and_degrades_to_ai_unavailable(monkeypatch):
    from types import SimpleNamespace

    import apps.api.main as api_main
    from apps.api.routers.auth import current_user

    q = {"security_id": "DSE:NMB", "question": "Why is ROE high?"}
    assert client.post("/api/v1/copilot/ask", json=q).status_code == 401

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    app.dependency_overrides[current_user] = lambda: SimpleNamespace(id=987654, email="t@example.com")
    monkeypatch.setattr(api_main.settings, "COPILOT_DAILY_QUESTIONS", 2)
    api_main._copilot_counts.clear()
    try:
        first = client.post("/api/v1/copilot/ask", json=q)
        second = client.post("/api/v1/copilot/ask", json=q)
        third = client.post("/api/v1/copilot/ask", json=q)
    finally:
        app.dependency_overrides.pop(current_user, None)
        api_main._copilot_counts.clear()
    assert first.status_code == 200 and first.json()["status"] == "AI_UNAVAILABLE"
    assert first.json()["security_id"] == "DSE:NMB"
    assert second.status_code == 200 and third.status_code == 429
    # The deterministic report is unaffected by the AI being unavailable.
    assert client.get("/api/v1/reports/DSE:NMB").status_code == 200
