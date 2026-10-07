"""Research runs: real states, no COMPLETED over a failed critical stage, no duplicates, recovery from a run
left RUNNING, and production serving the frozen snapshot a reviewer approved. Synthetic data in a throwaway
database; the report builder is replaced by a small stand-in where the test is about the engine itself."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import apps.api.main as api
from packages.core.config import AppEnvironment, settings
from packages.database.base import Base
from packages.database.models import (FinancialFact, ResearchRun, RiskItem, Security, SourceDocument,
                                      ValidationCheck)
from packages.database.session import get_session
from packages.research import engine
from pipelines import review


@pytest.fixture()
def maker(tmp_path, monkeypatch):
    eng = create_engine(f"sqlite:///{(tmp_path / 'runs.db').as_posix()}")
    Base.metadata.create_all(eng)
    mk = sessionmaker(bind=eng, expire_on_commit=False)
    with mk() as s:
        s.add(Security(id="DSE:TEST", exchange="DSE", local_ticker="TEST", name="Test Bank Plc", sector="Banking",
                       currency="TZS", is_bank=True, industry_template="bank", listing_status="listed",
                       listing_url="https://example.invalid", verified_at=date(2026, 9, 1)))
        s.commit()

    def _session():
        s = mk()
        try:
            yield s
        finally:
            s.close()

    api.app.dependency_overrides[get_session] = _session
    monkeypatch.setattr(review, "SessionLocal", mk, raising=False)
    yield mk
    api.app.dependency_overrides.clear()


def _seed_sources(mk):
    with mk() as s:
        doc = SourceDocument(security_id="DSE:TEST", kind="annual_report", title="Test AR 2025", publisher="Test",
                             url="https://example.invalid/ar.pdf", sha256="a" * 64, fiscal_year=2025,
                             retrieved_at=datetime.now(timezone.utc))
        s.add(doc)
        s.flush()
        s.add(FinancialFact(security_id="DSE:TEST", item_code="total_assets", fiscal_year=2025, statement="BS",
                            label_as_reported="Total assets", value=Decimal("100"), unit="TZS_millions",
                            currency="TZS", period_end=date(2025, 12, 31), basis="consolidated", document_id=doc.id,
                            page=1, column_role="current", extraction_method="test", agreed_by=["a", "b"],
                            is_primary=True))
        s.add(ValidationCheck(security_id="DSE:TEST", fiscal_year=2025, check_name="assets = liabilities + equity",
                              passed=True, detail="ok"))
        s.add(RiskItem(security_id="DSE:TEST", category="credit", title="t", quote="q", document_id=doc.id, page=1))
        s.commit()


def _report(price_value="2000.00", view="Undervalued"):
    return {"years": [2025], "ratios": [{"code": "roe", "values": {"2025": {"available": True, "value": Decimal("0.2")}}}],
            "valuation": {"result": {"available": True, "fair_value": Decimal("2500.123")}},
            "technical": {"available": True, "stale": False, "last_trade_date": "2026-10-06"},
            "header": {"price": {"available": True, "value": Decimal(price_value)},
                       "recommendation": {"available": True, "model_view": view}},
            "review": {}, "security": {"id": "DSE:TEST"}}


def test_overall_state_rules():
    st = lambda name, state: {"stage": name, "state": state, "critical": name in engine.CRITICAL}  # noqa: E731
    ok = [st(n, "COMPLETED") for n in engine.CRITICAL] + [st("valuation", "COMPLETED"), st("ai_interpretation", "SKIPPED")]
    assert engine._overall(ok) == "COMPLETED"
    assert engine._overall(ok[:-2] + [st("valuation", "BLOCKED")]) == "PARTIAL"           # non-critical
    assert engine._overall([st("sources", "INSUFFICIENT_DATA")] + ok[1:]) == "INSUFFICIENT_DATA"
    assert engine._overall([st("documents", "FAILED")] + ok) == "FAILED"                   # FAILED wins
    assert engine._overall([st("extraction", "BLOCKED")] + ok) == "BLOCKED"


def test_a_company_with_no_documents_is_never_completed(maker, monkeypatch):
    monkeypatch.setattr(engine, "build_report", lambda s, sid: _report())
    with maker() as s:
        run = engine.execute(s, "DSE:TEST")
    assert run.execution_state == "INSUFFICIENT_DATA"
    assert {x["stage"]: x["state"] for x in run.stages}["sources"] == "INSUFFICIENT_DATA"


def test_a_build_that_crashes_is_failed_with_the_error_recorded(maker, monkeypatch):
    _seed_sources(maker)

    def boom(s, sid):
        raise RuntimeError("division by zero in the valuation")
    monkeypatch.setattr(engine, "build_report", boom)
    with maker() as s:
        run = engine.execute(s, "DSE:TEST")
    assert run.execution_state == "FAILED" and "division by zero" in run.error
    assert run.snapshot is None
    assert {x["stage"]: x["state"] for x in run.stages}["calculations"] == "FAILED"


def test_a_good_run_stores_an_exact_snapshot(maker, monkeypatch):
    _seed_sources(maker)
    monkeypatch.setattr(engine, "build_report", lambda s, sid: _report())
    with maker() as s:
        run = engine.execute(s, "DSE:TEST")
    assert run.execution_state == "COMPLETED", run.stages
    assert run.snapshot["valuation"]["result"]["fair_value"] == "2500.123"     # exact string, not a float
    assert len(run.snapshot_sha256) == 64 and run.status == "draft"


def test_a_second_request_while_one_is_running_returns_the_same_run(maker, monkeypatch):
    with maker() as s:
        s.add(ResearchRun(id="RA-20261007-900", security_id="DSE:TEST", status="draft", data_sha256="",
                          config_sha256="", execution_state="RUNNING", started_at=datetime.now(timezone.utc)))
        s.commit()
        run = engine.execute(s, "DSE:TEST")
        assert run.id == "RA-20261007-900"
        assert s.query(ResearchRun).count() == 1, "a duplicate run was started"


def test_a_run_left_running_by_a_restart_is_marked_failed(maker, monkeypatch):
    _seed_sources(maker)
    monkeypatch.setattr(engine, "build_report", lambda s, sid: _report())
    with maker() as s:
        s.add(ResearchRun(id="RA-20261007-901", security_id="DSE:TEST", status="draft", data_sha256="",
                          config_sha256="", execution_state="RUNNING",
                          started_at=datetime.now(timezone.utc) - timedelta(hours=1)))
        s.commit()
        new = engine.execute(s, "DSE:TEST")
        old = s.get(ResearchRun, "RA-20261007-901")
    assert old.execution_state == "FAILED" and "process stopped" in old.error
    assert new.id != old.id and new.execution_state == "COMPLETED"


def test_an_unexecuted_run_cannot_be_submitted_or_approved(maker, capsys):
    with maker() as s:
        s.add(ResearchRun(id="RA-20260919-001", security_id="DSE:TEST", status="draft", data_sha256="",
                          config_sha256="", summary={}))
        s.commit()
    assert review.main(["submit", "RA-20260919-001", "--by", "Test Reviewer", "--note", "x"]) == 1
    assert "Execute a run first" in capsys.readouterr().out


def test_production_serves_the_approved_snapshot_not_a_fresh_build(maker, monkeypatch):
    _seed_sources(maker)
    monkeypatch.setattr(engine, "build_report", lambda s, sid: _report(price_value="2000.00"))
    with maker() as s:
        run = engine.execute(s, "DSE:TEST")
    client = TestClient(api.app)
    monkeypatch.setattr(settings, "APP_ENV", AppEnvironment.PRODUCTION)
    monkeypatch.setattr(api, "PRODUCTION", True)
    assert client.get("/api/v1/reports/DSE:TEST").status_code == 403          # a draft is not served
    assert client.get("/api/v1/research-runs?security_id=DSE:TEST").json() == {"runs": []}

    assert review.main(["submit", run.id, "--by", "Test Reviewer", "--note", "checked"]) == 0
    assert review.main(["approve", run.id, "--by", "Test Reviewer", "--note", "checked"]) == 0
    # Data moves after the approval; what readers see must not.
    monkeypatch.setattr(api, "build_report", lambda s, sid: _report(price_value="9999.00"))
    body = client.get("/api/v1/reports/DSE:TEST").json()
    assert body["header"]["price"]["value"] == "2000.00"
    assert body["review"]["frozen"] is True and body["review"]["reviewer"] == "Test Reviewer"
    listed = client.get("/api/v1/research-runs?security_id=DSE:TEST").json()["runs"]
    assert [r["run_id"] for r in listed] == [run.id] and listed[0]["execution_state"] == "COMPLETED"
