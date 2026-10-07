"""Sign-in and per-user portfolios, tested at the API (not the UI). The core promise: user A can never read,
change or delete user B's portfolio, and nothing works without a valid session. Synthetic test data,
in a throwaway database; nothing here reaches the real one."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import apps.api.main as api
from apps.api.routers.auth import token_hash
from packages.database.base import Base
from packages.database.models import PriceBar, Security, SourceDocument, User, UserSession
from packages.database.session import get_session

PASSWORD = "correct horse battery staple"


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'auth.db').as_posix()}")
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, expire_on_commit=False)
    with maker() as s:
        for sid, cur in (("DSE:TEST", "TZS"), ("DSE:NOPRICE", "TZS"), ("NSE:KTEST", "KES")):
            s.add(Security(id=sid, exchange=sid.split(":")[0], local_ticker=sid.split(":")[1], name=f"{sid} Plc",
                           sector="Banking", currency=cur, is_bank=True, industry_template="bank",
                           listing_status="listed", listing_url="https://example.invalid", verified_at=date(2026, 9, 1)))
        doc = SourceDocument(kind="public_price_file", title="test prices", publisher="test",
                             url="https://example.invalid", retrieved_at=datetime.now(timezone.utc))
        s.add(doc)
        s.flush()
        s.add(PriceBar(instrument_id="DSE:TEST", trade_date=date.today() - timedelta(days=1),
                       close=Decimal("2070.00"), volume=Decimal("100"), source_document_id=doc.id))
        s.commit()

    def _session():
        s = maker()
        try:
            yield s
        finally:
            s.close()

    api.app.dependency_overrides[get_session] = _session
    api._hits.clear()
    yield maker
    api.app.dependency_overrides.clear()
    api._hits.clear()


@pytest.fixture()
def client(db):
    return TestClient(api.app)


def _signup(client, email):
    r = client.post("/api/v1/auth/signup", json={"email": email, "password": PASSWORD})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _portfolio(client, headers, name="Core", holdings=None):
    body = {"name": name, "holdings": holdings if holdings is not None else
            [{"security_id": "DSE:TEST", "quantity": "10", "cost_per_share": "2000"}]}
    r = client.post("/api/v1/portfolios", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


# ------------------------------------------------------------------ sign-up, sign-in, sign-out

def test_signup_stores_only_an_argon2_hash_and_a_token_hash(client, db):
    headers = _signup(client, "A@Example.com ")
    token = headers["Authorization"][7:]
    with db() as s:
        user = s.query(User).one()
        session_row = s.query(UserSession).one()
    assert user.email == "a@example.com"                      # normalised
    assert user.password_hash.startswith("$argon2id$") and PASSWORD not in user.password_hash
    assert session_row.token_hash == token_hash(token) and token not in session_row.token_hash


def test_short_password_and_bad_email_are_refused(client):
    assert client.post("/api/v1/auth/signup", json={"email": "a@example.com", "password": "short"}).status_code == 422
    assert client.post("/api/v1/auth/signup", json={"email": "not-an-email", "password": PASSWORD}).status_code == 422


def test_duplicate_signup_is_refused(client):
    _signup(client, "a@example.com")
    assert client.post("/api/v1/auth/signup", json={"email": "A@example.com", "password": PASSWORD}).status_code == 409


def test_login_works_and_wrong_password_or_unknown_email_get_the_same_answer(client):
    _signup(client, "a@example.com")
    ok = client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": PASSWORD})
    wrong = client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "wrong password!!"})
    unknown = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert ok.status_code == 200 and ok.json()["user"]["email"] == "a@example.com"
    assert (wrong.status_code, wrong.json()) == (unknown.status_code, unknown.json()) == (
        401, {"detail": "Email or password is incorrect."})


def test_logout_ends_the_session(client):
    h = _signup(client, "a@example.com")
    assert client.get("/api/v1/auth/me", headers=h).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=h).status_code == 204
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401


def test_expired_session_is_refused(client, db):
    h = _signup(client, "a@example.com")
    with db() as s:
        s.query(UserSession).update({"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)})
        s.commit()
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer made-up-token"}, {"Authorization": "Basic abc"},
                                     {"Authorization": "Bearer "}])
def test_portfolios_need_a_real_session(client, headers):
    assert client.get("/api/v1/portfolios", headers=headers).status_code == 401
    assert client.post("/api/v1/portfolios", json={"name": "x"}, headers=headers).status_code == 401
    assert client.delete("/api/v1/portfolios/1", headers=headers).status_code == 401


def test_sign_in_attempts_are_rate_limited_per_client(client):
    codes = [client.post("/api/v1/auth/login", json={"email": f"u{i}@example.com", "password": "x"}).status_code
             for i in range(12)]
    assert codes[:10] == [401] * 10 and codes[10:] == [429, 429]


def test_failed_sign_ins_lock_the_account_whatever_the_address(client):
    from apps.api.routers import auth
    auth._failures.clear()
    _signup(client, "victim@example.com")
    api._hits.clear()
    for _ in range(5):
        assert client.post("/api/v1/auth/login", json={"email": "victim@example.com", "password": "guess"}).status_code == 401
    api._hits.clear()                     # a new address: the account lock must still hold
    r = client.post("/api/v1/auth/login", json={"email": "victim@example.com", "password": PASSWORD})
    assert r.status_code == 429 and "15 minutes" in r.json()["detail"]
    auth._failures.clear()
    assert client.post("/api/v1/auth/login", json={"email": "victim@example.com", "password": PASSWORD}).status_code == 200


# ------------------------------------------------------------------ isolation between users

def test_user_a_cannot_read_change_or_delete_user_bs_portfolio(client):
    a, b = _signup(client, "a@example.com"), _signup(client, "b@example.com")
    bs = _portfolio(client, b, name="B's portfolio")
    pid = bs["id"]

    assert client.get(f"/api/v1/portfolios/{pid}", headers=a).status_code == 404
    assert client.put(f"/api/v1/portfolios/{pid}", json={"name": "hijacked", "holdings": []},
                      headers=a).status_code == 404
    assert client.delete(f"/api/v1/portfolios/{pid}", headers=a).status_code == 404
    assert client.get("/api/v1/portfolios", headers=a).json() == {"portfolios": []}

    # B's portfolio is untouched.
    still = client.get(f"/api/v1/portfolios/{pid}", headers=b).json()
    assert still["name"] == "B's portfolio" and len(still["holdings"]) == 1


def test_owner_can_replace_and_delete(client):
    a = _signup(client, "a@example.com")
    p = _portfolio(client, a)
    r = client.put(f"/api/v1/portfolios/{p['id']}", json={"name": "Renamed", "holdings": []}, headers=a)
    assert r.status_code == 200 and r.json()["name"] == "Renamed" and r.json()["totals"]["status"] == "NO_DATA"
    assert client.delete(f"/api/v1/portfolios/{p['id']}", headers=a).status_code == 204
    assert client.get(f"/api/v1/portfolios/{p['id']}", headers=a).status_code == 404


# ------------------------------------------------------------------ values: calculated, never invented

def test_values_come_from_the_stored_close_in_exact_decimals(client):
    a = _signup(client, "a@example.com")
    p = _portfolio(client, a)
    h = p["holdings"][0]
    assert h["price"]["value"] == "2070.00" and h["price"]["status"] == "VERIFIED"
    assert Decimal(h["market_value"]) == Decimal("20700.00")
    assert Decimal(h["gain"]) == Decimal("700.00")             # 10 x (2070 - 2000)
    assert Decimal(h["weight"]) == 1 and p["totals"]["status"] == "VERIFIED"


def test_a_holding_without_a_price_is_insufficient_data_not_zero(client):
    a = _signup(client, "a@example.com")
    p = _portfolio(client, a, holdings=[{"security_id": "DSE:TEST", "quantity": "10"},
                                        {"security_id": "DSE:NOPRICE", "quantity": "5"}])
    unpriced = next(h for h in p["holdings"] if h["security_id"] == "DSE:NOPRICE")
    assert unpriced["price"] == {"available": False, "status": "INSUFFICIENT_DATA",
                                 "reason": "No stored price for this security."}
    assert "market_value" not in unpriced and "weight" not in unpriced
    assert p["totals"]["status"] == "PARTIAL" and p["totals"]["unpriced_holdings"] == ["DSE:NOPRICE"]
    assert Decimal(p["totals"]["market_value"]) == Decimal("20700.00")


@pytest.mark.parametrize("holdings,why", [
    ([{"security_id": "DSE:NOPE", "quantity": "1"}], "Unknown security"),
    ([{"security_id": "NSE:KTEST", "quantity": "1"}], "FX conversion"),
    ([{"security_id": "DSE:TEST", "quantity": "1"}, {"security_id": "dse:test", "quantity": "2"}], "twice"),
])
def test_bad_holdings_are_refused_with_the_reason(client, holdings, why):
    a = _signup(client, "a@example.com")
    r = client.post("/api/v1/portfolios", json={"name": "x", "holdings": holdings}, headers=a)
    assert r.status_code == 422 and why in r.json()["detail"]


@pytest.mark.parametrize("quantity", ["0", "-5", "abc", "1e400", "NaN", "Infinity", "0.00001"])
def test_malformed_quantities_are_refused(client, quantity):
    a = _signup(client, "a@example.com")
    r = client.post("/api/v1/portfolios", json={"name": "x", "holdings": [
        {"security_id": "DSE:TEST", "quantity": quantity}]}, headers=a)
    assert r.status_code == 422


def test_with_dse_display_off_holdings_are_blocked_not_valued(client, monkeypatch):
    from packages.core import config

    a = _signup(client, "a@example.com")
    monkeypatch.setattr(config.settings, "DSE_PUBLIC_DISPLAY", False)
    p = _portfolio(client, a)
    h = p["holdings"][0]
    assert h["price"]["status"] == "BLOCKED" and "Data Vending Policy" in h["price"]["reason"]
    assert "market_value" not in h and p["totals"]["market_value"] is None


def test_analysis_is_owner_only_and_honest_about_thin_history(client):
    a, b = _signup(client, "a@example.com"), _signup(client, "b@example.com")
    p = _portfolio(client, a)
    assert client.get(f"/api/v1/portfolios/{p['id']}/analysis", headers=b).status_code == 404
    assert client.get(f"/api/v1/portfolios/{p['id']}/analysis").status_code == 401
    out = client.get(f"/api/v1/portfolios/{p['id']}/analysis", headers=a).json()
    assert out["available"] and out["risk"]["status"] == "INSUFFICIENT_DATA"     # one stored day only
    assert any(s.get("available") for s in out["stress_tests"])


@pytest.mark.parametrize("targets, why", [
    ({"DSE:TEST": "0.6"}, "add up to 1"),
    ({"DSE:NOPRICE": "1"}, "not held"),
    ({"DSE:TEST": "1.5"}, "between 0 and 1"),
])
def test_bad_target_weights_are_refused(client, targets, why):
    a = _signup(client, "a@example.com")
    r = client.post("/api/v1/portfolios", headers=a, json={
        "name": "x", "holdings": [{"security_id": "DSE:TEST", "quantity": "10"}], "target_weights": targets})
    assert r.status_code == 422 and why in r.json()["detail"]
