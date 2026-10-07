"""Telemetry privacy: what may leave the API, and that analytics can never break a request. No Sentry or PostHog
project exists, so nothing is sent; the tests use the real scrubber and a fake PostHog client."""
from __future__ import annotations

import pytest

from packages.core import telemetry
from packages.core.config import Settings


def test_sentry_events_lose_secrets_bodies_queries_and_the_user():
    event = {"request": {"url": "https://api.afriedge.example/api/v1/portfolios?token=abc",
                         "headers": {"Authorization": "Bearer s3cret", "Cookie": "afriedge_session=x", "Accept": "*/*"},
                         "data": '{"password": "hunter2hunter2"}', "cookies": {"a": "b"}, "query_string": "token=abc",
                         "env": {"REMOTE_ADDR": "1.2.3.4"}},
             "user": {"email": "a@example.com", "ip_address": "1.2.3.4"}}
    out = telemetry.scrub_event(event)
    flat = str(out)
    for secret in ("s3cret", "afriedge_session", "hunter2", "token=abc", "a@example.com", "1.2.3.4"):
        assert secret not in flat
    assert out["request"]["headers"]["Accept"] == "*/*"
    assert out["request"]["url"] == "https://api.afriedge.example/api/v1/portfolios"


def test_sentry_is_off_without_a_dsn(monkeypatch):
    monkeypatch.setattr(telemetry.settings, "SENTRY_DSN", "")
    assert telemetry.init_sentry() is False


def test_only_allowlisted_events_and_properties_pass():
    assert telemetry.clean("portfolio_created", {"holdings_count": 2, "holdings": ["DSE:NMB"], "value": 9e9}) == {"holdings_count": 2}
    assert telemetry.clean("copilot_question", {"security_id": "DSE:NMB", "question": "my salary is..."}) == {"security_id": "DSE:NMB"}
    assert telemetry.clean("password_reset_typed", {}) is None


def test_people_are_salted_hashes_not_ids_or_emails(monkeypatch):
    monkeypatch.setattr(telemetry.settings, "ANALYTICS_SALT", "a-long-random-salt-value")
    a = telemetry.person(1)
    monkeypatch.setattr(telemetry.settings, "ANALYTICS_SALT", "another-long-random-salt")
    assert a != telemetry.person(1) and "1" != a and len(a) == 32
    assert telemetry.person(None) is None


class _FakePostHog:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def capture(self, event, **kw):
        if self.fail:
            raise RuntimeError("network down")
        self.sent.append((event, kw))


def test_tracking_sends_only_clean_properties(monkeypatch):
    fake = _FakePostHog()
    monkeypatch.setattr(telemetry, "_client", lambda: fake)
    assert telemetry.track("portfolio_created", 7, {"holdings_count": 2, "holdings": ["DSE:NMB"]})
    (event, kw), = fake.sent
    assert event == "portfolio_created" and kw["properties"]["holdings_count"] == 2
    assert "holdings" not in kw["properties"] and kw["distinct_id"] != 7


def test_an_analytics_failure_never_breaks_the_request(monkeypatch):
    monkeypatch.setattr(telemetry, "_client", lambda: _FakePostHog(fail=True))
    assert telemetry.track("login", 1) is False


def test_without_a_key_nothing_is_sent(monkeypatch):
    monkeypatch.setattr(telemetry.settings, "POSTHOG_API_KEY", "")
    monkeypatch.setattr(telemetry, "_posthog", None)
    assert telemetry.track("login", 1) is False


def test_production_refuses_analytics_without_a_salt():
    base = {"APP_ENV": "PRODUCTION", "DATABASE_URL": "postgresql://u:p@h/d", "CORS_ORIGINS": "https://a.example",
            "DSE_PUBLIC_DISPLAY": "false", "POSTHOG_API_KEY": "phc_test", "INTERNAL_PROXY_SECRET": "x" * 32}
    with pytest.raises(ValueError, match="ANALYTICS_SALT"):
        Settings(**base)
    assert Settings(**base, ANALYTICS_SALT="x" * 16).POSTHOG_API_KEY == "phc_test"
