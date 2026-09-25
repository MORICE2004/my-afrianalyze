"""Production guards: settings that refuse to start on a laptop setup, readiness that tells the truth,
error text that stays on the server, and the brake on expensive requests. No downloaded data needed."""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import apps.api.main as api
from packages.core.config import Settings
from packages.database.base import Base
from packages.database.models import DataSourceStatus, Security
from packages.database.session import get_session

GOOD = {"APP_ENV": "PRODUCTION", "DATABASE_URL": "postgresql://u:p@db.example.net/afri",
        "CORS_ORIGINS": "https://afrianalyze.example"}


# ------------------------------------------------------------------ settings

def test_render_style_postgres_url_is_accepted():
    s = Settings(DATABASE_URL="postgres://u:p@host:5432/db")
    assert s.DATABASE_URL == "postgresql://u:p@host:5432/db"


def test_production_refuses_sqlite():
    with pytest.raises(ValueError, match="PostgreSQL"):
        Settings(**{**GOOD, "DATABASE_URL": "sqlite:///x.db"})


@pytest.mark.parametrize("origins", ["http://localhost:3000", "https://ok.example,http://127.0.0.1:3000", "*"])
def test_production_refuses_open_or_local_cors(origins):
    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        Settings(**{**GOOD, "CORS_ORIGINS": origins})


def test_production_accepts_a_real_configuration():
    s = Settings(**GOOD)
    assert s.cors_origins == ["https://afrianalyze.example"]


def test_development_keeps_its_local_defaults():
    assert Settings(APP_ENV="DEVELOPMENT").DATABASE_URL.startswith("sqlite")


# ------------------------------------------------------------------ readiness

@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'ready.db').as_posix()}")
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, expire_on_commit=False)

    def _session():
        s = maker()
        try:
            yield s
        finally:
            s.close()

    api.app.dependency_overrides[get_session] = _session
    yield maker
    api.app.dependency_overrides.clear()


def _seed_security(maker):
    with maker() as s:
        s.add(Security(id="DSE:TEST", exchange="DSE", local_ticker="TEST", name="Test Plc", sector="Banking",
                       currency="TZS", is_bank=True, industry_template="bank", listing_status="listed",
                       listing_url="https://example.invalid", verified_at=date(2026, 9, 1)))
        s.commit()


def test_empty_database_is_not_ready(db):
    r = TestClient(api.app).get("/ready")
    assert r.status_code == 503
    assert r.json()["status"] == "DATABASE_NOT_SEEDED"


def test_seeded_database_with_fresh_sources_is_healthy(db):
    _seed_security(db)
    with db() as s:
        s.add(DataSourceStatus(source="x", status="ok", last_success_at=datetime.now(timezone.utc),
                               last_attempt_at=datetime.now(timezone.utc),
                               max_age_hours=24, detail=""))
        s.commit()
    r = TestClient(api.app).get("/ready")
    assert (r.status_code, r.json()["status"]) == (200, "APP_HEALTHY")


def test_stale_source_is_degraded_not_down(db):
    _seed_security(db)
    with db() as s:
        s.add(DataSourceStatus(source="dse_prices", status="ok", last_attempt_at=datetime.now(timezone.utc),
                               last_success_at=datetime(2020, 1, 1,
                               tzinfo=timezone.utc), max_age_hours=24, detail=""))
        s.commit()
    r = TestClient(api.app).get("/ready")
    assert r.status_code == 200
    assert r.json() == {**r.json(), "status": "DEGRADED", "stale_or_blocked_sources": ["dse_prices"]}


class _BrokenSession:
    def execute(self, *_a, **_k):
        raise RuntimeError("could not connect to server at secret-host.internal as user admin_user")

    def close(self):
        pass


def test_unreachable_database_is_503_and_its_error_stays_on_the_server():
    api.app.dependency_overrides[get_session] = lambda: _BrokenSession()
    try:
        client = TestClient(api.app)
        ready = client.get("/ready")
        health = client.get("/health")
    finally:
        api.app.dependency_overrides.clear()
    assert (ready.status_code, ready.json()["status"]) == (503, "DATABASE_UNAVAILABLE")
    assert health.json()["status"] == "offline"
    for body in (ready.text, health.text):
        assert "secret-host" not in body and "admin_user" not in body


# ------------------------------------------------------------------ expensive requests

def test_report_requests_are_limited_per_client(db, monkeypatch):
    monkeypatch.setattr(api.settings, "EXPENSIVE_REQUESTS_PER_MINUTE", 3)
    api._hits.clear()
    client = TestClient(api.app)
    codes = [client.get("/api/v1/reports/DSE:NOPE").status_code for _ in range(5)]
    api._hits.clear()
    assert codes == [404, 404, 404, 429, 429]
    # Cheap endpoints are not counted.
    assert client.get("/ready").status_code == 503


# ------------------------------------------------------------------ Postgres

PG = os.environ.get("TEST_POSTGRES_URL")


@pytest.mark.skipif(not PG, reason="TEST_POSTGRES_URL not set (CI sets it to a real Postgres service)")
def test_money_round_trips_exactly_on_postgres():
    from sqlalchemy import Column, Integer, insert, select
    from sqlalchemy.orm import DeclarativeBase

    from packages.database.types import ExactDecimal

    class _B(DeclarativeBase):
        pass

    class _Money(_B):
        __tablename__ = "exact_money_check"
        id = Column(Integer, primary_key=True)
        value = Column(ExactDecimal)

    engine = create_engine(PG)
    _B.metadata.drop_all(engine)
    _B.metadata.create_all(engine)
    exact = Decimal("12345678901234567.8901234567")
    with engine.begin() as conn:
        conn.execute(insert(_Money).values(id=1, value=exact))
        got = conn.execute(select(_Money.value)).scalar_one()
    _B.metadata.drop_all(engine)
    assert isinstance(got, Decimal) and got == exact
