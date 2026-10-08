"""Error reporting (Sentry) and product analytics (PostHog), both inert until their keys are set.

Privacy rules (CLAUDE.md rule 10), enforced here rather than trusted to call sites:
- Sentry: errors only, no tracing; no request bodies, cookies, auth headers, query strings or user details.
  The release is the deployed git commit, so an error can be traced to the code that raised it.
- PostHog: events are sent from the API, not from browser JavaScript, so there is no tracking script and no
  cookie. Only the event names and property keys in ALLOWED are sent; anything else is dropped. A person
  is a salted SHA-256 of their user id (never an email), and GeoIP is off. No portfolio holdings, amounts,
  questions or document content is ever a property.
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Any

from packages.core.config import settings

log = logging.getLogger("afriedge.telemetry")

# event -> property keys allowed with it. Everything else is dropped before sending.
ALLOWED: dict[str, set[str]] = {
    "signup": set(),
    "login": set(),
    "company_viewed": {"security_id"},
    "report_viewed": {"security_id", "frozen"},
    "valuation_viewed": {"security_id"},
    "report_pdf_downloaded": {"security_id"},
    "report_xlsx_downloaded": {"security_id"},
    "research_started": {"security_id"},
    "research_completed": {"security_id", "execution_state"},
    "portfolio_created": {"holdings_count"},
    "portfolio_analysis_started": {"holdings_count"},
    "copilot_question": {"security_id", "status"},
}

_posthog = None


def release() -> str | None:
    """The deployed commit, as the hosting platforms provide it (Render, Vercel), else unset."""
    return os.environ.get("RENDER_GIT_COMMIT") or os.environ.get("VERCEL_GIT_COMMIT_SHA") or os.environ.get("GIT_COMMIT")


SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "proxy-authorization", "set-cookie"}


def scrub_event(event: dict, hint: dict | None = None) -> dict:
    """Sentry before_send: remove anything that could carry a secret or personal data."""
    req = event.get("request") or {}
    for key in ("data", "cookies", "query_string", "env"):
        req.pop(key, None)
    if isinstance(req.get("headers"), dict):
        req["headers"] = {k: ("[removed]" if k.lower() in SENSITIVE_HEADERS else v) for k, v in req["headers"].items()}
    if "url" in req:
        req["url"] = req["url"].split("?")[0]
    event.pop("user", None)
    return event


def init_sentry() -> bool:
    if not settings.SENTRY_DSN:
        return False
    import sentry_sdk

    sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.APP_ENV.value.lower(), release=release(),
                    send_default_pii=False, traces_sample_rate=0.0, max_request_body_size="never",
                    before_send=scrub_event)
    return True


def _client():
    global _posthog
    if _posthog is None and settings.POSTHOG_API_KEY:
        from posthog import Posthog

        _posthog = Posthog(settings.POSTHOG_API_KEY, host=settings.POSTHOG_HOST, disable_geoip=True,
                           privacy_mode=True, timeout=3)
    return _posthog


def person(user_id: int | None) -> str | None:
    if user_id is None:
        return None
    return hashlib.sha256(f"{settings.ANALYTICS_SALT}:{user_id}".encode()).hexdigest()[:32]


def clean(event: str, properties: dict[str, Any] | None) -> dict[str, Any] | None:
    """The properties that may be sent for this event, or None if the event itself is not allowed."""
    if event not in ALLOWED:
        return None
    return {k: v for k, v in (properties or {}).items() if k in ALLOWED[event] and isinstance(v, (str, int, bool))}


def track(event: str, user_id: int | None = None, properties: dict[str, Any] | None = None) -> bool:
    """Send one allowed event. Never raises: analytics must not break a request."""
    props = clean(event, properties)
    if props is None:
        log.warning("telemetry: event %r is not in the allowlist; not sent", event)
        return False
    client = _client()
    if client is None:
        return False
    try:
        client.capture(event, distinct_id=person(user_id),
                       properties={**props, "$process_person_profile": user_id is not None})
        return True
    except Exception:  # noqa: BLE001 - analytics failure is logged, never raised into the request
        log.exception("telemetry: capture failed")
        return False
