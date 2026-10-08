"""Prices for pages and charts: the latest quote of a security, a price series, and the DSE's market activity
and sector indices. Everything is read from stored bars (pipelines merge every provider's answer into them);
nothing here calls a provider.

Freshness words (never LIVE: nothing AfriEdge shows is a live price):
  CURRENT  the close of the exchange's latest stored session, and that session is within the source's limit
  STALE    older than that
Readers see plain labels ("Updated", "Out of date"); the words above are for the API and the admin page.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from packages.analysis import corporate_actions
from packages.core.config import DSE_ATTRIBUTION, DSE_DISPLAY_BLOCKED, dse_display_allowed
from packages.database.models import DataSourceStatus, PriceBar, Security, SourceDocument
from packages.database.session import get_session
from packages.market_data import reconcile
from packages.market_data.quality import MOVE, WITHIN, round_trips

router = APIRouter(tags=["market"])

INDICES = {"DSE:DSEI": "DSE All Share Index", "DSE:TSI": "Tanzania Share Index",
           "DSE:BI": "Banks, Finance & Investments", "DSE:IA": "Industrial & Allied",
           "DSE:CS": "Commercial Services"}
SECTOR_INDICES = ("DSE:BI", "DSE:IA", "DSE:CS")
PUBLIC_LABEL = {"CURRENT": "Updated", "STALE": "Out of date"}


def _blocked() -> dict:
    return {"available": False, "status": "BLOCKED", "licensing": "RESTRICTED", "reason": DSE_DISPLAY_BLOCKED,
            "public_label": "Price not shown",
            "public_reason": "Prices from the Dar es Salaam Stock Exchange are not shown until a data licence is held."}


def _max_age_days(session: Session) -> int:
    row = session.get(DataSourceStatus, "dse_prices")
    return (row.max_age_hours if row else 120) // 24


def latest_session(session: Session, exchange: str = "DSE") -> date | None:
    """The most recent day any security of the exchange has a stored close (the exchange's last session)."""
    ids = [s.id for s in session.query(Security.id).filter(Security.exchange == exchange)]
    return session.query(func.max(PriceBar.trade_date)).filter(PriceBar.instrument_id.in_(ids)).scalar()


def _source(session: Session, doc_id: int) -> dict | None:
    doc = session.get(SourceDocument, doc_id)
    if doc is None:
        return None
    return {"document_id": doc.id, "publisher": doc.publisher, "title": doc.title, "url": doc.url,
            "retrieved_at": doc.retrieved_at.isoformat() if doc.retrieved_at else None}


def quote_for(session: Session, sec: Security, today: date | None = None) -> dict:
    if sec.exchange == "DSE" and not dse_display_allowed():
        return {**_blocked(), "security_id": sec.id, "currency": sec.currency}
    bars = (session.query(PriceBar).filter_by(instrument_id=sec.id).order_by(PriceBar.trade_date.desc())
            .limit(2).all())
    if not bars:
        return {"available": False, "status": "INSUFFICIENT_DATA", "security_id": sec.id, "currency": sec.currency,
                "reason": f"No prices are stored for {sec.id}.", "public_label": "Limited data",
                "public_reason": "No recent price is available for this company yet."}
    last = bars[0]
    prev = bars[1] if len(bars) > 1 else None
    today = today or datetime.now(timezone.utc).date()
    session_day = latest_session(session, sec.exchange) or last.trade_date
    age = (today - last.trade_date).days
    timing = "CURRENT" if last.trade_date == session_day and age <= _max_age_days(session) else "STALE"
    traded = bool(last.volume)
    last_trade = (last.trade_date if traded else
                  session.query(func.max(PriceBar.trade_date)).filter(PriceBar.instrument_id == sec.id,
                                                                      PriceBar.volume > 0).scalar())
    # A split between the two days would read as a fall: compare on the adjusted basis.
    actions = corporate_actions.load_actions(sec.id)
    change = change_pct = None
    if prev is not None:
        adj = corporate_actions.adjust_prices({prev.trade_date: prev.close, last.trade_date: last.close}, actions)
        p0, p1 = adj[prev.trade_date], adj[last.trade_date]
        change, change_pct = p1 - p0, (p1 / p0 - 1) if p0 else None
    rec = reconcile.latest_for(session, sec.id)
    conflict = None
    if rec is not None and rec.trade_date == last.trade_date:
        conflict = {"status": rec.status, "provider_a": rec.provider_a, "close_a": rec.close_a,
                    "provider_b": rec.provider_b, "close_b": rec.close_b, "difference_pct": rec.difference_pct,
                    "checked_at": rec.checked_at.isoformat()}
    status = "CONFLICTING_SOURCE" if conflict and conflict["status"] == "CONFLICTING_SOURCE" else (
        "STALE" if timing == "STALE" else "VERIFIED")
    return {
        "available": True, "security_id": sec.id, "currency": sec.currency, "status": status,
        "price": last.close, "trade_date": last.trade_date.isoformat(),
        "previous_close": prev.close if prev else None, "previous_date": prev.trade_date.isoformat() if prev else None,
        "change": change, "change_pct": change_pct,
        "traded": traded, "last_traded_date": last_trade.isoformat() if last_trade else None,
        "volume": last.volume, "turnover": last.turnover if traded else None,
        # The DSE publishes high = low = 0 on a day without a trade; that is not a price.
        "high": last.high if traded and last.high else None, "low": last.low if traded and last.low else None,
        "market_cap": last.market_cap,
        "timing": timing, "public_label": PUBLIC_LABEL[timing],
        "freshness": {"age_days": age, "latest_session": session_day.isoformat(), "max_age_days": _max_age_days(session),
                      "kind": "End of day"},
        "licensing": "RESTRICTED" if sec.exchange == "DSE" else "UNKNOWN",
        "attribution": DSE_ATTRIBUTION if sec.exchange == "DSE" else None,
        "source": _source(session, last.source_document_id),
        "reconciliation": conflict,
        "split_adjusted_change": bool(actions),
    }


@router.get("/api/v1/securities/{security_id}/quote")
def get_quote(security_id: str, session: Session = Depends(get_session)) -> dict:
    sec = session.get(Security, security_id.upper())
    if sec is None:
        raise HTTPException(404, f"Unknown security {security_id}")
    return quote_for(session, sec)


def series(session: Session, instrument_id: str, days: int) -> dict:
    """Split-adjusted closes for a chart. For an index, round-trip days are left out and listed."""
    bars = session.query(PriceBar).filter_by(instrument_id=instrument_id).order_by(PriceBar.trade_date).all()
    if not bars:
        return {"available": False, "status": "INSUFFICIENT_DATA", "instrument_id": instrument_id,
                "reason": f"No prices are stored for {instrument_id}.",
                "public_reason": "There is no price history for this yet."}
    since = bars[-1].trade_date - timedelta(days=days)
    closes = {b.trade_date: b.close for b in bars}
    vols = {b.trade_date: b.volume for b in bars}
    excluded: list[date] = []
    notes: list[str] = []
    if instrument_id in INDICES:
        excluded = round_trips(closes)
        if excluded:
            closes = {d: v for d, v in closes.items() if d not in set(excluded)}
    else:
        actions = corporate_actions.load_actions(instrument_id)
        closes = corporate_actions.adjust_prices(closes, actions)
        notes = corporate_actions.describe(actions)
    shown_excluded = [d for d in excluded if d >= since]
    if shown_excluded:
        notes.append(f"{len(shown_excluded)} day(s) left out: the published level jumps more than {MOVE:.0%} and "
                     f"returns within {WITHIN} sessions, a source error rather than a market move "
                     f"({', '.join(d.isoformat() for d in shown_excluded)}).")
    points = [{"date": d.isoformat(), "close": c, "volume": vols.get(d)} for d, c in sorted(closes.items()) if d >= since]
    return {"available": True, "instrument_id": instrument_id, "points": points, "notes": notes,
            "first": points[0]["date"] if points else None, "last": points[-1]["date"] if points else None,
            "attribution": DSE_ATTRIBUTION}


@router.get("/api/v1/prices/{instrument_id}")
def get_prices(instrument_id: str, days: int = Query(365, ge=5, le=3700),
               session: Session = Depends(get_session)) -> dict:
    iid = instrument_id.upper()
    if iid not in INDICES and session.get(Security, iid) is None:
        raise HTTPException(404, f"Unknown instrument {instrument_id}")
    if iid.startswith("DSE:") and not dse_display_allowed():
        return {**_blocked(), "instrument_id": iid}
    return series(session, iid, days)


# ------------------------------------------------------------------ the DSE's market page

def _period_change(closes: dict[date, Decimal], since: date) -> Decimal | None:
    days = sorted(closes)
    base = [d for d in days if d <= since]
    if not base or not days:
        return None
    start = closes[base[-1]]
    return closes[days[-1]] / start - 1 if start else None


def index_summary(session: Session, instrument_id: str) -> dict:
    bars = session.query(PriceBar).filter_by(instrument_id=instrument_id).order_by(PriceBar.trade_date).all()
    name = INDICES[instrument_id]
    if len(bars) < 2:
        return {"id": instrument_id, "name": name, "available": False, "status": "INSUFFICIENT_DATA",
                "reason": f"{name}: fewer than two levels stored."}
    closes = {b.trade_date: b.close for b in bars}
    bad = set(round_trips(closes))
    clean = {d: v for d, v in closes.items() if d not in bad}
    days = sorted(clean)
    last_day = days[-1]
    return {"id": instrument_id, "name": name, "available": True, "value": clean[last_day],
            "trade_date": last_day.isoformat(),
            "change_1d": clean[last_day] / clean[days[-2]] - 1,
            "change_1m": _period_change(clean, last_day - timedelta(days=30)),
            "change_ytd": _period_change(clean, date(last_day.year - 1, 12, 31)),
            "change_1y": _period_change(clean, last_day - timedelta(days=365)),
            "excluded_days": len(bad)}


def activity(session: Session) -> dict:
    """The latest session's totals over the shares AfriEdge stores (not the whole exchange)."""
    if not dse_display_allowed():
        return _blocked()
    day = latest_session(session, "DSE")
    if day is None:
        return {"available": False, "status": "INSUFFICIENT_DATA", "reason": "No DSE share prices are stored."}
    ids = [s.id for s in session.query(Security.id).filter(Security.exchange == "DSE")]
    rows = session.query(PriceBar).filter(PriceBar.instrument_id.in_(ids), PriceBar.trade_date == day).all()
    traded = [r for r in rows if r.volume]
    turnover = sum((r.turnover for r in traded if r.turnover is not None), Decimal(0))
    missing = sum(1 for r in traded if r.turnover is None)
    return {"available": True, "trade_date": day.isoformat(), "currency": "TZS",
            "turnover": turnover, "volume": sum((r.volume for r in traded), Decimal(0)),
            "securities_traded": len(traded), "securities_stored": len(rows),
            "market_cap": sum((r.market_cap for r in rows if r.market_cap is not None), Decimal(0)),
            "turnover_missing": missing,
            "coverage": (f"Totals over the {len(rows)} DSE shares AfriEdge stores prices for, on {day}; "
                         f"other listed securities are not included."),
            "attribution": DSE_ATTRIBUTION}


def sectors(session: Session) -> dict:
    if not dse_display_allowed():
        return _blocked()
    out = [index_summary(session, i) for i in SECTOR_INDICES]
    return {"available": any(s["available"] for s in out), "indices": out,
            "basis": ("The DSE's own sector indices, as it publishes them. Companies are not assigned to a sector "
                      "by AfriEdge."),
            "attribution": DSE_ATTRIBUTION}
