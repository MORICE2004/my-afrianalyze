"""Economic and market news, read from the news_items cache that pipelines.news fills. Nothing here calls a
news source, so a slow or failing publisher never slows a page.

Readers see plain words: when a source's last fetch failed or is older than its limit, the response says "some
news sources are temporarily unavailable" and still returns everything cached. The error itself is only on the
admin data-health page.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from packages.core.config import settings
from packages.database.models import DataSourceStatus, MacroObservation, NewsItem, Security
from packages.database.session import get_session
from packages.media import library

router = APIRouter(tags=["news"])

SOURCES_UNAVAILABLE = "Some news sources are temporarily unavailable. Stories already collected are still shown."
TIER_LABEL = {1: "Official", 2: "Wire", 3: "Regional press"}


def news_sources() -> list[dict]:
    return json.loads((settings.CONFIG_DIR / "news_sources.json").read_text(encoding="utf-8"))["sources"]


def _aware(d: datetime | None) -> datetime | None:
    return None if d is None else (d if d.tzinfo else d.replace(tzinfo=timezone.utc))


def source_health(session: Session) -> list[dict]:
    """Every whitelisted source with its configured state and, for connected ones, its last fetch."""
    now = datetime.now(timezone.utc)
    out = []
    for s in news_sources():
        row = session.get(DataSourceStatus, s["status_key"]) if s.get("status_key") else None
        last = _aware(row.last_success_at) if row else None
        fresh = bool(row and row.status == "ok" and last and (now - last).total_seconds() / 3600 <= row.max_age_hours)
        out.append({"id": s["id"], "name": s["name"], "tier": s["tier"], "country": s.get("country"),
                    "state": s["state"], "home": s.get("home"), "terms_note": s.get("terms_note"),
                    "image_rights": s.get("image_rights"), "image_rights_note": s.get("image_rights_note"),
                    "last_success_at": last.isoformat() if last else None,
                    "last_attempt_at": _aware(row.last_attempt_at).isoformat() if row else None,
                    "status": row.status if row else None, "detail": row.detail if row else None,
                    "fresh": fresh if s["state"] == "CONNECTED" else None})
    return out


def _item(n: NewsItem, src: dict) -> dict:
    s = src.get(n.source_id, {})
    return {"id": n.id, "title": n.title, "url": n.url, "language": n.language,
            "published_at": _aware(n.published_at).isoformat(), "retrieved_at": _aware(n.retrieved_at).isoformat(),
            "summary": n.summary, "countries": n.countries, "categories": n.categories,
            # A publisher's image is shown only when its terms permit it (config/news_sources.json image_rights).
            "image": ({"url": n.image_url, "width": n.image_width, "height": n.image_height,
                       "credit": s.get("name", n.source_id), "rights": "PERMITTED",
                       "retrieved_at": _aware(n.image_checked_at).isoformat() if n.image_checked_at else None}
                      if n.image_url and s.get("image_rights") == "PERMITTED" else None),
            # Otherwise an openly licensed photo of the publishing institution or the story's city (never the event).
            "photos": library.for_news(n.source_id, n.countries or []),
            "relevance": n.relevance, "relevance_reason": n.relevance_reason,
            "source": {"id": n.source_id, "name": s.get("name", n.source_id), "tier": s.get("tier"),
                       "tier_label": TIER_LABEL.get(s.get("tier"))},
            "companies": [{"security_id": c["security_id"], "name": c["name"], "link": c["link"]}
                          for c in (n.related or {}).get("companies", [])]}


@router.get("/api/v1/news")
def list_news(country: str | None = Query(None, pattern="^(TZ|KE|UG)$"),
              category: str | None = Query(None, max_length=40),
              relevance: str | None = Query(None, pattern="^(HIGH|MEDIUM|LOW|NOT_ASSESSED)$"),
              security: str | None = Query(None, max_length=32),
              q: str | None = Query(None, max_length=80),
              limit: int = Query(30, ge=1, le=100), session: Session = Depends(get_session)) -> dict:
    """Stories newest first. Filters are applied in Python because countries and categories are JSON lists;
    the cache is small (hundreds of rows), and the newest 600 are scanned."""
    src = {s["id"]: s for s in news_sources()}
    rows = session.query(NewsItem).order_by(NewsItem.published_at.desc()).limit(600).all()
    picked = []
    for n in rows:
        if country and country not in (n.countries or []):
            continue
        if category and category not in (n.categories or []):
            continue
        if relevance and n.relevance != relevance:
            continue
        if q and q.strip().lower() not in n.title.lower():
            continue
        if security and not any(c["security_id"] == security for c in (n.related or {}).get("companies", [])):
            continue
        picked.append(_item(n, src))
        if len(picked) >= limit:
            break
    health = source_health(session)
    connected = [h for h in health if h["state"] == "CONNECTED"]
    some_down = any(not h["fresh"] for h in connected)
    categories = sorted({c for n in rows for c in (n.categories or [])})
    # The lead story, by a stated rule: the newest story rated HIGH relevance published in the last 21 days, or
    # failing that the newest story. No hand-picked ranking.
    recent = datetime.now(timezone.utc).timestamp() - 21 * 86400
    lead = next((i for i in picked if i["relevance"] == "HIGH" and datetime.fromisoformat(i["published_at"]).timestamp() >= recent),
                picked[0] if picked else None)
    return {"items": picked, "count": len(picked), "categories": categories,
            "lead_id": lead["id"] if lead else None,
            "lead_rule": "The newest story rated high relevance in the last 21 days; otherwise the newest story.",
            "sources": [{"name": h["name"], "tier": h["tier"], "connected": h["state"] == "CONNECTED"} for h in health],
            "some_sources_unavailable": some_down, "notice": SOURCES_UNAVAILABLE if some_down else None,
            "relevance_method": ("Market relevance comes from fixed rules: which asset class the story affects, "
                                 "which country, and which economic variable it discloses. It is not a sentiment "
                                 "score and makes no prediction."),
            "terms": "Headlines and links only; each story opens on the publisher's own site."}


@router.get("/api/v1/news/{news_id}")
def get_news(news_id: str, session: Session = Depends(get_session)) -> dict:
    if len(news_id) != 40 or not all(c in "0123456789abcdef" for c in news_id):
        raise HTTPException(status_code=404, detail="Story not found.")
    n = session.get(NewsItem, news_id)
    if n is None:
        raise HTTPException(status_code=404, detail="Story not found.")
    src = {s["id"]: s for s in news_sources()}
    related = n.related or {}
    indicators = []
    for ind in related.get("indicators", []):
        o = (session.query(MacroObservation).filter_by(series_id=ind["series_id"])
             .order_by(MacroObservation.observation_date.desc()).first())
        indicators.append({"series_id": ind["series_id"], "label": ind["label"], "available": o is not None,
                           **({"value": o.value, "unit": o.unit, "date": o.observation_date.isoformat(),
                               "source_url": o.source_url} if o is not None else
                              {"reason": "Not loaded in AfriEdge yet."})})
    companies = []
    for c in related.get("companies", []):
        s = session.get(Security, c["security_id"])
        if s is not None:
            companies.append({"security_id": s.id, "name": s.name, "ticker": s.local_ticker, "exchange": s.exchange,
                              "currency": s.currency, "link": c["link"], "why": c["why"]})
    return {**_item(n, src), "markets": related.get("markets", []), "indicators": indicators,
            "related_companies": companies,
            "why_it_matters": (n.relevance_reason if n.relevance != "NOT_ASSESSED" else None),
            "caution": ("Potentially relevant because of the variable and market named above. AfriEdge does not "
                        "predict how prices will react.")}
