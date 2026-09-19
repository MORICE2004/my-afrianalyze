"""My AfriAnalyze API.

Only serves stored, sourced data. When something is not available the response
says so and why; there are no fallback values.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from packages.core.config import REPO_ROOT, AppEnvironment, settings
from packages.database.models import DataSourceStatus, MacroObservation, PriceBar, Security, SourceDocument
from packages.database.session import get_session
from packages.report.builder import build_report

app = FastAPI(title="My AfriAnalyze API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

MARKETS = {
    "TZ": {"exchange": "DSE", "currency": "TZS", "name": "Tanzania (DSE)", "index": "DSE:DSEI"},
    "KE": {"exchange": "NSE", "currency": "KES", "name": "Kenya (NSE)", "index": "NSE:NASI"},
    "UG": {"exchange": "USE", "currency": "UGX", "name": "Uganda (USE)", "index": "USE:ALSI"},
}


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ------------------------------------------------------------------ health

@app.get("/health")
def health(session: Session = Depends(get_session)) -> dict:
    now = datetime.now(timezone.utc)
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:
        return {"status": "offline", "checked_at": now.isoformat(),
                "database": {"ok": False, "detail": str(exc)}, "sources": []}
    sources = []
    for row in session.query(DataSourceStatus).order_by(DataSourceStatus.source):
        last = _aware(row.last_success_at)
        age_h = None if last is None else (now - last).total_seconds() / 3600
        fresh = row.status == "ok" and age_h is not None and age_h <= row.max_age_hours
        sources.append({"source": row.source, "status": row.status, "fresh": fresh,
                        "last_success_at": last.isoformat() if last else None,
                        "age_hours": None if age_h is None else round(age_h, 1),
                        "max_age_hours": row.max_age_hours, "detail": row.detail})
    if not sources:
        overall = "degraded"
    elif all(s["fresh"] for s in sources):
        overall = "online"
    else:
        overall = "degraded"
    return {"status": overall, "checked_at": now.isoformat(), "database": {"ok": True},
            "sources": sources,
            "summary": f"{sum(s['fresh'] for s in sources)} of {len(sources)} data sources fresh"}


# ------------------------------------------------------------------ securities

def _security(s: Security, session: Session) -> dict:
    has_report = session.query(func.count()).select_from(SourceDocument).filter(
        SourceDocument.security_id == s.id, SourceDocument.kind == "annual_report").scalar() > 0
    return {"id": s.id, "exchange": s.exchange, "ticker": s.local_ticker, "isin": s.isin, "name": s.name,
            "sector": s.sector, "currency": s.currency, "is_bank": s.is_bank, "listing_url": s.listing_url,
            "verified_at": s.verified_at.isoformat(), "verification_note": s.verification_note,
            "has_report": has_report}


@app.get("/api/v1/securities")
def list_securities(q: str | None = Query(None, max_length=60), exchange: str | None = None,
                    session: Session = Depends(get_session)) -> dict:
    query = session.query(Security)
    if exchange:
        query = query.filter(Security.exchange == exchange.upper())
    rows = query.order_by(Security.exchange, Security.local_ticker).all()
    if q:
        needle = q.strip().lower()

        def score(s: Security) -> int | None:
            ticker, name, sid = s.local_ticker.lower(), s.name.lower(), s.id.lower()
            if needle in (ticker, sid):
                return 0
            if ticker.startswith(needle) or sid.startswith(needle):
                return 1
            if name.startswith(needle):
                return 2
            if needle in name or needle in sid:
                return 3
            return None

        ranked = [(score(s), s) for s in rows]
        rows = [s for sc, s in sorted((x for x in ranked if x[0] is not None), key=lambda x: (x[0], x[1].id))]
    return {"results": [_security(s, session) for s in rows], "count": len(rows)}


@app.get("/api/v1/securities/{security_id}")
def get_security(security_id: str, session: Session = Depends(get_session)) -> dict:
    s = session.get(Security, security_id.upper())
    if s is None:
        raise HTTPException(404, f"Unknown security {security_id}. Use EXCHANGE:TICKER, e.g. DSE:NMB.")
    return _security(s, session)


# ------------------------------------------------------------------ reports

@app.get("/api/v1/reports/{security_id}")
def get_report(security_id: str, session: Session = Depends(get_session)) -> dict:
    sec = session.get(Security, security_id.upper())
    if sec is None:
        raise HTTPException(404, f"Unknown security {security_id}")
    has_docs = session.query(SourceDocument).filter_by(security_id=sec.id, kind="annual_report").first()
    if has_docs is None:
        raise HTTPException(404, f"No research report for {sec.id} yet. Only DSE:NMB has sourced data.")
    report = build_report(session, sec.id)
    # Section 72: in production nothing reaches users before a named reviewer publishes it.
    if settings.APP_ENV == AppEnvironment.PRODUCTION and report["review"]["status"] != "published":
        raise HTTPException(403, f"The {sec.id} report has not been reviewed and published yet.")
    return report


@app.get("/api/v1/reports/{security_id}/pdf")
def get_report_pdf(security_id: str, session: Session = Depends(get_session)) -> Response:
    from packages.report.pdf import render_pdf

    report = get_report(security_id, session)
    pdf = render_pdf(report)
    name = f"AfriAnalyze_{report['security']['id'].replace(':', '_')}_{date.today():%Y%m%d}.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@app.get("/api/v1/sources/{document_id}/file")
def get_source_file(document_id: int, session: Session = Depends(get_session)) -> FileResponse:
    doc = session.get(SourceDocument, document_id)
    if doc is None or not doc.file_path:
        raise HTTPException(404, "Source file not stored")
    path = (REPO_ROOT / doc.file_path).resolve()
    if not path.is_file() or REPO_ROOT.resolve() not in path.parents:
        raise HTTPException(404, "Source file missing on disk")
    if doc.kind == "licensed_price_file":
        raise HTTPException(403, "Licensed data files are not redistributed")
    return FileResponse(path, media_type="application/pdf", filename=Path(doc.file_path).name,
                        content_disposition_type="inline")


# ------------------------------------------------------------------ markets

@app.get("/api/v1/markets/overview")
def markets_overview(session: Session = Depends(get_session)) -> dict:
    status = session.get(DataSourceStatus, "dse_prices")
    out = []
    for code, m in MARKETS.items():
        bars = (session.query(PriceBar).filter_by(instrument_id=m["index"])
                .order_by(PriceBar.trade_date.desc()).limit(2).all())
        if len(bars) == 2:
            last, prev = bars
            index = {"available": True, "id": m["index"], "value": last.close,
                     "trade_date": last.trade_date.isoformat(),
                     "change": (last.close - prev.close) / prev.close}
        else:
            index = {"available": False, "id": m["index"],
                     "reason": "No licensed index data loaded"
                     + (f" ({status.detail})" if status and m["exchange"] == "DSE" else "")}
        count = session.query(func.count()).select_from(Security).filter(Security.exchange == m["exchange"]).scalar()
        out.append({"market": code, "name": m["name"], "exchange": m["exchange"], "currency": m["currency"],
                    "index": index, "securities_in_master": count})
    return {"markets": out,
            "commentary": {"available": False,
                           "reason": "Market commentary is only published when it can be generated from stored, "
                                     "sourced market data. None is loaded."},
            "movers": {"available": False, "reason": "Needs licensed end-of-day prices for listed securities."}}


# ------------------------------------------------------------------ fixed income

@app.get("/api/v1/fixed-income/TZ")
def fixed_income_tz(session: Session = Depends(get_session)) -> dict:
    latest: dict[str, MacroObservation] = {}
    for m in session.query(MacroObservation).order_by(MacroObservation.observation_date):
        latest[m.series_id] = m

    def obs(m: MacroObservation | None) -> dict:
        if m is None:
            return {"available": False, "reason": "Not loaded"}
        age = (date.today() - m.observation_date).days
        return {"available": True, "value": m.value, "as_of": m.observation_date.isoformat(), "age_days": age,
                "label": m.label, "source_name": m.source_name, "source_url": m.source_url,
                "attributes": m.attributes}

    curve = []
    for sid, m in latest.items():
        if sid.startswith("BOT_TBOND_") and sid.endswith("Y_WAYTM"):
            tenor = int(sid.removeprefix("BOT_TBOND_").removesuffix("Y_WAYTM"))
            point = obs(m) | {"tenor_years": tenor, "stale": (date.today() - m.observation_date).days > 365}
            curve.append(point)
    curve.sort(key=lambda p: p["tenor_years"])
    by_tenor = {p["tenor_years"]: p for p in curve}
    spread = ({"available": True, "value": by_tenor[10]["value"] - by_tenor[2]["value"],
               "formula": "10Y weighted average YTM - 2Y weighted average YTM (latest auctions; dates differ)",
               "dates": [by_tenor[2]["as_of"], by_tenor[10]["as_of"]]}
              if 2 in by_tenor and 10 in by_tenor else {"available": False, "reason": "2Y or 10Y auction missing"})
    inflation = obs(latest.get("NBS_CPI_HEADLINE_YOY"))
    real = ({"available": True, "value": (1 + by_tenor[10]["value"]) / (1 + inflation["value"]) - 1,
             "formula": "(1 + 10Y auction YTM) / (1 + latest headline inflation) - 1",
             "inputs": {"ytm_10y": by_tenor[10]["value"], "inflation": inflation["value"]}}
            if 10 in by_tenor and inflation["available"] else {"available": False, "reason": "Inputs missing"})
    return {"country": "TZ", "currency": "TZS", "curve": curve, "spread_2y_10y": spread,
            "policy_rate": obs(latest.get("BOT_CBR")), "inflation": inflation, "real_yield_10y": real,
            "note": "Yields are weighted average yields to maturity at the most recent Bank of Tanzania auction "
                    "for each tenor. Auction dates differ by tenor, so this is not a same-day curve."}


# ------------------------------------------------------------------ portfolios

class ProposalRequest(BaseModel):
    market: str = Field(pattern="^(TZ|KE|UG)$")
    capital: float = Field(gt=0)
    currency: str
    risk_profile: str = Field(pattern="^(Conservative|Moderate|Aggressive)$")
    horizon_years: int = Field(ge=1, le=40)


@app.post("/api/v1/portfolio/proposals")
def portfolio_proposal(req: ProposalRequest, session: Session = Depends(get_session)) -> dict:
    m = MARKETS[req.market]
    if req.currency != m["currency"]:
        raise HTTPException(422, f"Capital for {m['name']} must be in {m['currency']}")
    secs = session.query(Security).filter_by(exchange=m["exchange"]).order_by(Security.local_ticker).all()
    priced = {s.id for s in secs if session.query(PriceBar).filter_by(instrument_id=s.id).first()}
    universe = [{"id": s.id, "name": s.name, "has_licensed_price": s.id in priced} for s in secs]
    if not priced:
        return {"available": False, "request": req.model_dump(), "universe": universe,
                "reason": (f"A proposal needs current prices to size positions and check minimum trade sizes. "
                           f"No licensed {m['exchange']} prices are loaded, so no securities, weights or amounts "
                           f"are shown."),
                "checks_that_will_apply": ["Position size in shares = amount / last price, rounded down to board lot",
                                           "Every position meets the exchange minimum trade size",
                                           f"Risk profile '{req.risk_profile}' caps equity weight (config)",
                                           "Cash residual reported"]}
    raise HTTPException(501, "Proposal construction with licensed prices is not implemented yet")


@app.get("/api/v1/portfolios")
def saved_portfolios() -> dict:
    raise HTTPException(401, "Sign-in is not implemented. Saved portfolios are only shown for an authenticated user.")
