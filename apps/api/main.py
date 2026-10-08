"""AfriEdge API.

Only serves stored, sourced data. When something is not available the response
says so and why; there are no fallback values.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from packages.core.config import (DSE_ATTRIBUTION, DSE_DISPLAY_BLOCKED, REPO_ROOT, AppEnvironment,
                                  dse_display_allowed, settings)
from packages.database.models import (DataSourceStatus, MacroObservation, PriceBar, ResearchRun, Security,
                                      SourceDocument)
from packages.database.session import get_session
from apps.api.routers import auth as auth_router
from apps.api.routers import market as market_router
from apps.api.routers import news as news_router
from apps.api.routers import portfolios as portfolios_router
from packages.core import telemetry
from packages.report.builder import build_report

log = logging.getLogger("afriedge.api")
PRODUCTION = settings.APP_ENV == AppEnvironment.PRODUCTION

# Errors only, no tracing, scrubbed of bodies, cookies, auth headers and query strings (telemetry.py).
telemetry.init_sentry()

# The interactive API docs are for development; in production the web app is the interface.
app = FastAPI(title="AfriEdge API", version="0.2.0",
              docs_url=None if PRODUCTION else "/docs", redoc_url=None,
              openapi_url=None if PRODUCTION else "/openapi.json")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Analytics-Consent"],
)

# Report and PDF builds are the only endpoints that do real work per request, so they get a per-client
# limit. This is an in-process brake against a script hammering one server, not a security control: it
# resets on restart and each server instance counts separately.
_EXPENSIVE_PREFIXES = ("/api/v1/reports/", "/api/v1/research/")
_AUTH_PREFIX = "/api/v1/auth/"        # sign-in and sign-up: a tighter budget against password guessing
AUTH_REQUESTS_PER_MINUTE = 10
_hits: dict[str, deque] = {}
_hits_lock = threading.Lock()


def client_ip(request: Request) -> str:
    """The client's address for rate limiting, never from a value the client controls (see config)."""
    import hmac

    forwarded = request.headers.get("x-afriedge-client-ip")
    key = request.headers.get("x-afriedge-proxy-key", "")
    if forwarded and settings.INTERNAL_PROXY_SECRET and hmac.compare_digest(key, settings.INTERNAL_PROXY_SECRET):
        return forwarded.strip()          # set by our own web server, which proved it with the shared secret
    if settings.CLIENT_IP_HEADER:
        value = request.headers.get(settings.CLIENT_IP_HEADER)
        if value:
            return value.strip()
    xff = request.headers.get("x-forwarded-for")
    if settings.TRUSTED_PROXY_HOPS > 0 and xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            return parts[max(0, len(parts) - settings.TRUSTED_PROXY_HOPS)]
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def limit_expensive_requests(request: Request, call_next):
    path = request.url.path
    if path.startswith(_EXPENSIVE_PREFIXES):
        bucket, limit, what = "reports", settings.EXPENSIVE_REQUESTS_PER_MINUTE, "report"
    elif path.startswith(_AUTH_PREFIX) and request.method == "POST":
        bucket, limit, what = "auth", AUTH_REQUESTS_PER_MINUTE, "sign-in"
    else:
        bucket = None
    if bucket:
        client = client_ip(request)
        now = time.monotonic()
        with _hits_lock:
            window = _hits.setdefault(f"{bucket}:{client}", deque())
            while window and now - window[0] > 60:
                window.popleft()
            if len(window) >= limit:
                return JSONResponse({"detail": f"Too many {what} requests. Try again in a minute."},
                                    status_code=429, headers={"Retry-After": "60"})
            window.append(now)
    return await call_next(request)

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

def _database_ok(session: Session) -> bool:
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception:
        # The error can name the database host and user, so it goes to the server log, not the response.
        log.exception("database check failed")
        return False


@app.get("/ready")
def ready(session: Session = Depends(get_session)) -> JSONResponse:
    """For the hosting platform's health check: 503 unless the API can serve data.

    Stale or blocked data sources do not make the API unready (the pages say which data is missing);
    they are reported as DEGRADED so monitoring can see them without taking the service down.
    """
    now = datetime.now(timezone.utc)
    if not _database_ok(session):
        return JSONResponse({"status": "DATABASE_UNAVAILABLE", "checked_at": now.isoformat()}, status_code=503)
    try:
        has_schema = session.query(Security).first() is not None
    except Exception:
        log.exception("schema check failed")
        has_schema = False
    if not has_schema:
        # Connected, but migrations or the security master have not been run: nothing can be served.
        return JSONResponse({"status": "DATABASE_NOT_SEEDED", "checked_at": now.isoformat()}, status_code=503)
    stale = []
    for row in session.query(DataSourceStatus):
        last = _aware(row.last_success_at)
        if row.status != "ok" or last is None or (now - last).total_seconds() / 3600 > row.max_age_hours:
            stale.append(row.source)
    return JSONResponse({"status": "DEGRADED" if stale else "APP_HEALTHY", "checked_at": now.isoformat(),
                         "stale_or_blocked_sources": sorted(stale)})


def _source_registry(rows: dict[str, dict]) -> list[dict]:
    """Every source AfriEdge covers or plans to cover (config/source_registry.json), each with its live
    state from the loaders' own records. A source with no loader can never show a last success."""
    import json

    reg = json.loads((settings.CONFIG_DIR / "source_registry.json").read_text(encoding="utf-8"))
    out = []
    for src in reg["sources"]:
        live = [rows[k] for k in src["status_keys"] if k in rows]
        if src["parser_state"] == "NOT_BUILT":
            state = "COMING" if src["coverage"] == "COMING" else "NOT_BUILT"
        elif not live:
            state = "NEVER_RUN"
        elif any(r["status"] == "failed" for r in live):
            state = "FAILED"
        elif not all(r["fresh"] for r in live):
            state = "STALE"
        elif any(r["status"] == "partial" for r in live):
            state = "PARTIAL"
        else:
            state = "OK"
        successes = [r["last_success_at"] for r in live if r["last_success_at"]]
        retrievals = [r["last_attempt_at"] for r in live if r["last_attempt_at"]]
        failures = [r["last_attempt_at"] for r in live if r["status"] == "failed" and r["last_attempt_at"]]
        out.append({"id": src["id"], "name": src["name"], "country": src["country"], "datasets": src["datasets"],
                    "state": state, "parser_state": src["parser_state"], "coverage": src["coverage"],
                    "licensing": src["licensing"], "licensing_note": src["licensing_note"],
                    "last_success_at": max(successes) if successes else None,
                    "last_retrieval_at": max(retrievals) if retrievals else None,
                    "last_failure_at": max(failures) if failures else None,
                    "probe": src.get("probe")})
    return out


# What readers may see about a source: its name, what it covers, a plain state and dates. Loader messages, error
# text, licensing clauses and probe results are for administrators (/api/v1/admin/data-health), so the public
# endpoint never carries them, whatever the page chooses to display.
PUBLIC_SOURCE_FIELDS = ("source", "fresh", "last_success_at", "age_hours")
PUBLIC_REGISTRY_FIELDS = ("id", "name", "country", "datasets", "state", "coverage", "licensing", "last_success_at")
PUBLIC_STATE = {"OK": "Updated", "STALE": "Delayed", "PARTIAL": "Limited data", "FAILED": "Temporarily unavailable",
                "NEVER_RUN": "Not yet collected", "COMING": "Coming", "NOT_BUILT": "Not yet connected"}


@app.get("/health")
def public_health(session: Session = Depends(get_session)) -> dict:
    """The data-sources report for everyone, in plain words. It answers 200 whenever the API is up; platforms
    use /ready. Technical detail is on the admin endpoint only."""
    h = health(session)
    out = {"status": h["status"], "checked_at": h["checked_at"], "database": {"ok": h["database"]["ok"]},
           "sources": [{k: x.get(k) for k in PUBLIC_SOURCE_FIELDS} for x in h["sources"]]}
    if "registry" in h:
        out["registry"] = [{**{k: r.get(k) for k in PUBLIC_REGISTRY_FIELDS}, "public_state": PUBLIC_STATE.get(r["state"], r["state"])}
                           for r in h["registry"]]
        out["summary"] = h["summary"]
    return out


def health(session: Session) -> dict:
    """The data-health report shown to people on /health. It answers 200 whenever the API is up and says
    in its body whether the database and each source are working. Platforms should use /ready instead."""
    now = datetime.now(timezone.utc)
    if not _database_ok(session):
        return {"status": "offline", "checked_at": now.isoformat(),
                "database": {"ok": False, "detail": "The database is not reachable."}, "sources": []}
    sources = []
    for row in session.query(DataSourceStatus).order_by(DataSourceStatus.source):
        last = _aware(row.last_success_at)
        age_h = None if last is None else (now - last).total_seconds() / 3600
        fresh = row.status == "ok" and age_h is not None and age_h <= row.max_age_hours
        attempt = _aware(row.last_attempt_at)
        sources.append({"source": row.source, "status": row.status, "fresh": fresh,
                        "last_success_at": last.isoformat() if last else None,
                        "last_attempt_at": attempt.isoformat() if attempt else None,
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
            "registry": _source_registry({x["source"]: x for x in sources}),
            "summary": f"{sum(s['fresh'] for s in sources)} of {len(sources)} data sources fresh"}


# ------------------------------------------------------------------ securities

EXCHANGE_COUNTRY = {"DSE": ("TZ", "Tanzania", "Dar es Salaam Stock Exchange"),
                    "NSE": ("KE", "Kenya", "Nairobi Securities Exchange"),
                    "USE": ("UG", "Uganda", "Uganda Securities Exchange")}


def _security(s: Security, session: Session, report_ids: set[str] | None = None) -> dict:
    if report_ids is None:
        has_report = session.query(func.count()).select_from(SourceDocument).filter(
            SourceDocument.security_id == s.id, SourceDocument.kind == "annual_report").scalar() > 0
    else:
        has_report = s.id in report_ids
    country_code, country, exchange_name = EXCHANGE_COUNTRY.get(s.exchange, (None, None, s.exchange))
    from packages.media import library

    return {"photo": library.for_security(s.id), "id": s.id, "exchange": s.exchange, "exchange_name": exchange_name, "country": country,
            "country_code": country_code, "ticker": s.local_ticker, "isin": s.isin, "name": s.name,
            "sector": s.sector, "currency": s.currency, "is_bank": s.is_bank, "listing_url": s.listing_url,
            "verified_at": s.verified_at.isoformat(), "verification_note": s.verification_note,
            "has_report": has_report}


def search_score(s: Security, needle: str) -> float | None:
    """Relevance of one security to a typed query; None = not a match. Lower is better.

    0 exact ticker, id or ISIN; 1 ticker or ISIN prefix; 2 name prefix; 3 a word of the name starts with it;
    4 contained in the name; 5 to 6 a close spelling of the name or ticker (difflib ratio >= 0.75), so a typo
    still finds the company. Plain string work on the security master: no model is called for a search.
    """
    from difflib import SequenceMatcher

    ticker, name, sid, isin = s.local_ticker.lower(), s.name.lower(), s.id.lower(), (s.isin or "").lower()
    if needle in (ticker, sid) or (isin and needle == isin):
        return 0
    if ticker.startswith(needle) or sid.startswith(needle) or (isin and len(needle) >= 4 and isin.startswith(needle)):
        return 1
    if name.startswith(needle):
        return 2
    words = name.replace("&", " ").replace(",", " ").split()
    if any(w.startswith(needle) for w in words):
        return 3
    if len(needle) >= 3 and needle in name:
        return 4
    if len(needle) >= 3:
        best = max([SequenceMatcher(None, needle, name).ratio(), SequenceMatcher(None, needle, ticker).ratio()]
                   + [SequenceMatcher(None, needle, w).ratio() for w in words])
        if best >= 0.75:
            return 5 + (1 - best)
    return None


@app.get("/api/v1/securities")
def list_securities(q: str | None = Query(None, max_length=60), exchange: str | None = None,
                    limit: int = Query(50, ge=1, le=200), session: Session = Depends(get_session)) -> dict:
    query = session.query(Security)
    if exchange:
        query = query.filter(Security.exchange == exchange.upper())
    rows = query.order_by(Security.exchange, Security.local_ticker).all()
    if q and q.strip():
        needle = " ".join(q.strip().lower().split())
        ranked = [(search_score(s, needle), s) for s in rows]
        # Ties: companies with a research report first, then the exchange and ticker.
        report_ids = {sid for (sid,) in session.query(SourceDocument.security_id)
                      .filter(SourceDocument.kind == "annual_report").distinct()}
        rows = [s for sc, s in sorted((x for x in ranked if x[0] is not None),
                                      key=lambda x: (x[0], x[1].id not in report_ids, x[1].id))]
    else:
        report_ids = {sid for (sid,) in session.query(SourceDocument.security_id)
                      .filter(SourceDocument.kind == "annual_report").distinct()}
    total = len(rows)
    return {"results": [_security(s, session, report_ids) for s in rows[:limit]], "count": total}


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
        raise HTTPException(404, f"No research report for {sec.id} yet. Its annual reports have not been ingested.")
    if settings.APP_ENV == AppEnvironment.PRODUCTION:
        # Section 72: in production readers see exactly what a named reviewer approved: the frozen snapshot of
        # the published run, not a fresh build whose numbers may have moved since the approval.
        run = (session.query(ResearchRun).filter_by(security_id=sec.id, status="published")
               .filter(ResearchRun.snapshot.isnot(None)).order_by(ResearchRun.reviewed_at.desc()).first())
        if run is None:
            raise HTTPException(403, f"The {sec.id} report has not been reviewed and published yet.")
        report = dict(run.snapshot)
        report["review"] = {**report.get("review", {}), "run_id": run.id, "status": run.status,
                            "reviewer": run.reviewer, "reviewed_at": run.reviewed_at.isoformat() if run.reviewed_at else None,
                            "snapshot_sha256": run.snapshot_sha256, "frozen": True}
        telemetry.track("report_viewed", None, {"security_id": sec.id, "frozen": True})
        return report
    telemetry.track("report_viewed", None, {"security_id": sec.id, "frozen": False})
    return build_report(session, sec.id)


@app.get("/api/v1/research/{security_id}/stream")
def stream_research(security_id: str, session: Session = Depends(get_session)) -> StreamingResponse:
    """The company page's research, as NDJSON events sent as each stage finishes (packages/research/stream.py).
    The generator owns the session from here: FastAPI may release its dependency before the stream ends."""
    import json as _json

    from packages.research.engine import to_wire
    from packages.research.stream import events

    NL = "\n"                       # NDJSON: one event per line

    def body():
        try:
            for ev in events(session, security_id, lambda sec: _security(sec, session),
                             lambda sec: market_router.quote_for(session, sec), to_wire):
                yield _json.dumps(to_wire(ev), separators=(",", ":")) + NL
        except Exception:
            log.exception("research stream failed for %s", security_id)
            yield _json.dumps({"event": "unavailable", "status": "FAILED",
                               "reason": "The research could not be loaded. Please try again."}) + NL
        finally:
            session.close()

    return StreamingResponse(body(), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


@app.get("/api/v1/reports/{security_id}/pdf")
def get_report_pdf(security_id: str, user=Depends(auth_router.require_feature("excel_export")),
                   session: Session = Depends(get_session)) -> Response:
    """The research as a PDF file. A download, so it carries the same export entitlement as the workbook:
    readers without it view the research on the page and get 401/403 here."""
    from packages.report.pdf import render_pdf

    report = get_report(security_id, session)
    pdf = render_pdf(report)
    telemetry.track("report_pdf_downloaded", user.id, {"security_id": report["security"]["id"]})
    name = f"AfriEdge_{report['security']['id'].replace(':', '_')}_{date.today():%Y%m%d}.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})


@app.get("/api/v1/reports/{security_id}/xlsx")
def get_report_xlsx(security_id: str, user=Depends(auth_router.require_feature("excel_export")),
                    session: Session = Depends(get_session)) -> Response:
    """The analyst workbook (Pro). The entitlement is checked here, on the server: an account without it gets
    403 whatever the page shows. The workbook is the same report a reader sees (the approved snapshot in
    production), laid out in thirteen sheets by packages/report/excel.py."""
    from packages.report.excel import build_workbook

    report = get_report(security_id, session)
    data = build_workbook(report)
    telemetry.track("report_xlsx_downloaded", user.id, {"security_id": report["security"]["id"]})
    name = f"AfriEdge_{report['security']['id'].replace(':', '_')}_{date.today():%Y%m%d}.xlsx"
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})


# ------------------------------------------------------------------ administration

@app.get("/api/v1/admin/data-health")
def admin_data_health(_admin=Depends(auth_router.require_admin), session: Session = Depends(get_session)) -> dict:
    """Everything an administrator needs about each source: state, failure reason, last success, freshness and
    licensing, plus the market-data providers and their priority. Readers never see these details."""
    from packages.market_data import registry
    from packages.database.models import PriceReconciliation

    h = health(session)
    providers = [{"id": e.id, "name": e.name, "state": e.state, "state_reason": e.state_reason,
                  "licensing": e.licensing, "coverage": e.coverage, "note": e.note,
                  "credential_env": e.credential_env} for e in registry.entries()]
    recon = (session.query(PriceReconciliation).order_by(PriceReconciliation.checked_at.desc()).limit(20).all())
    return {**h, "providers": providers,
            "priority_setting": settings.MARKET_DATA_PRIORITY or None,
            "reconciliations": [{"instrument_id": r.instrument_id, "trade_date": r.trade_date.isoformat(),
                                 "currency": r.currency, "provider_a": r.provider_a, "close_a": r.close_a,
                                 "provider_b": r.provider_b, "close_b": r.close_b,
                                 "difference_pct": r.difference_pct, "status": r.status,
                                 "checked_at": r.checked_at.isoformat()} for r in recon],
            "news_sources": news_router.source_health(session),
            "refresh_schedule": "Weekdays 18:00 Dar es Salaam (GitHub Actions, refresh-data.yml), after the DSE close"}


# ------------------------------------------------------------------ unit trusts

@app.get("/api/v1/funds")
def list_funds() -> dict:
    """Unit trust registry (config/funds.json). Each figure is either sourced or says why it is not shown."""
    import json

    cfg = json.loads((settings.CONFIG_DIR / "funds.json").read_text(encoding="utf-8"))
    out = []
    for f in cfg["funds"]:
        mgr = cfg["managers"][f["manager"]]
        reason = (f"Not loaded: {mgr['name']} publishes this on {mgr['nav_page']}, but states no terms for reusing it "
                  f"({mgr['licensing']}). Waiting for the owner's decision; nothing is estimated.")
        out.append({**f, "manager_name": mgr["name"], "licensing": mgr["licensing"],
                    "figures": {k: {"available": False, "status": "BLOCKED", "reason": reason} for k in cfg["fields"]}})
    return {"funds": out, "note": cfg["_comment"]}


# ------------------------------------------------------------------ research copilot

class CopilotQuestion(BaseModel):
    security_id: str = Field(max_length=32)
    question: str = Field(min_length=3, max_length=1000)


# Questions per user per day, in this process. Enough to stop one account running up the AI bill; it resets
# on restart and is per instance (docs/COST_MODEL.md).
_copilot_counts: dict[tuple[int, date], int] = {}
_copilot_lock = threading.Lock()


@app.post("/api/v1/copilot/ask")
def copilot_ask(body: CopilotQuestion, user=Depends(auth_router.current_user),
                session: Session = Depends(get_session)) -> dict:
    from packages.copilot.assistant import ask
    from packages.research.engine import to_wire

    key = (user.id, datetime.now(timezone.utc).date())
    with _copilot_lock:
        if _copilot_counts.get(key, 0) >= settings.COPILOT_DAILY_QUESTIONS:
            raise HTTPException(429, f"You have asked {settings.COPILOT_DAILY_QUESTIONS} questions today, the daily "
                                     f"limit. The reports themselves remain available.")
        _copilot_counts[key] = _copilot_counts.get(key, 0) + 1
    # The same report a reader sees: the approved snapshot in production (403 if none), a live build otherwise.
    report = get_report(body.security_id, session)
    answer = ask(body.question.strip(), to_wire(report))
    telemetry.track("copilot_question", user.id, {"security_id": answer.get("security_id"), "status": answer["status"]})
    return answer


# ------------------------------------------------------------------ research runs

def _visible_runs(session: Session, security_id: str | None):
    q = session.query(ResearchRun).order_by(ResearchRun.created_at.desc())
    if security_id:
        q = q.filter(ResearchRun.security_id == security_id.upper())
    if PRODUCTION:
        # A draft's stage details include its unreviewed model view, so only reviewed runs are public.
        q = q.filter(ResearchRun.status.in_(["published", "superseded"]))
    return q


@app.get("/api/v1/research-runs")
def list_research_runs(security_id: str | None = Query(None, max_length=32),
                       session: Session = Depends(get_session)) -> dict:
    from packages.research.engine import describe

    return {"runs": [describe(r) for r in _visible_runs(session, security_id).limit(20)]}


@app.get("/api/v1/research-runs/{run_id}")
def get_research_run(run_id: str, session: Session = Depends(get_session)) -> dict:
    from packages.research.engine import describe

    run = _visible_runs(session, None).filter(ResearchRun.id == run_id).first()
    if run is None:
        raise HTTPException(404, "Research run not found.")
    return describe(run)


def _viewable_document(session: Session, document_id: int) -> tuple[SourceDocument, Path]:
    doc = session.get(SourceDocument, document_id)
    if doc is None or not doc.file_path:
        raise HTTPException(404, "Document not found.")
    if doc.kind in {"licensed_price_file", "public_price_file", "public_index_file"}:
        # Exchange price data is used to calculate, not republished (DSE terms). Checked before the disk.
        raise HTTPException(403, "Exchange price data files are not shown.")
    path = (REPO_ROOT / doc.file_path).resolve()
    if not path.is_file() or REPO_ROOT.resolve() not in path.parents or path.suffix.lower() != ".pdf":
        raise HTTPException(404, "Document not available.")
    return doc, path


def _page_count(path: Path) -> int:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(path))
    try:
        return len(pdf)
    finally:
        pdf.close()


@app.get("/api/v1/sources/{document_id}")
def get_source_meta(document_id: int, _user=Depends(auth_router.current_user),
                    session: Session = Depends(get_session)) -> dict:
    """What the viewer needs: title, publisher, the publisher's own address and the page count. No file path."""
    doc, path = _viewable_document(session, document_id)
    return {"document_id": doc.id, "title": doc.title, "publisher": doc.publisher, "kind": doc.kind,
            "original_url": doc.url, "retrieved_at": doc.retrieved_at.isoformat() if doc.retrieved_at else None,
            "sha256": doc.sha256, "pages": _page_count(path)}


@app.get("/api/v1/sources/{document_id}/pages/{page}")
def get_source_page(document_id: int, page: int, _user=Depends(auth_router.current_user),
                    session: Session = Depends(get_session)) -> Response:
    """One page of a stored source document, rendered on the server as a PNG image for signed-in readers.
    The PDF itself is never sent: there is no reader endpoint that returns the file. (A page on screen can
    always be captured; what is withheld is the original document and any bulk path to it.)"""
    import io

    import pypdfium2 as pdfium

    _, path = _viewable_document(session, document_id)
    pdf = pdfium.PdfDocument(str(path))
    try:
        if not 1 <= page <= len(pdf):
            raise HTTPException(404, "No such page.")
        image = pdf[page - 1].render(scale=1.6).to_pil()
    finally:
        pdf.close()
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="PNG", optimize=True)
    return Response(buf.getvalue(), media_type="image/png",
                    headers={"Cache-Control": "private, no-store", "Content-Disposition": "inline",
                             "X-Content-Type-Options": "nosniff"})


@app.get("/api/v1/sources/{document_id}/file")
def get_source_file(document_id: int, _admin=Depends(auth_router.require_admin),
                    session: Session = Depends(get_session)) -> FileResponse:
    """The original file, for administrators checking an extraction. Readers use the page viewer above."""
    _, path = _viewable_document(session, document_id)
    return FileResponse(path, media_type="application/pdf", filename=path.name, content_disposition_type="attachment",
                        headers={"Cache-Control": "no-store"})


# ------------------------------------------------------------------ markets

@app.get("/api/v1/markets/overview")
def markets_overview(session: Session = Depends(get_session)) -> dict:
    status = session.get(DataSourceStatus, "dse_prices")
    out = []
    for code, m in MARKETS.items():
        bars = (session.query(PriceBar).filter_by(instrument_id=m["index"])
                .order_by(PriceBar.trade_date.desc()).limit(2).all()) if dse_display_allowed() else []
        if len(bars) == 2:
            summary = market_router.index_summary(session, m["index"])
            index = {**summary, "available": True, "id": m["index"], "attribution": DSE_ATTRIBUTION,
                     "change": summary["change_1d"]}
        else:
            if m["exchange"] == "DSE" and not dse_display_allowed():
                reason, idx_status = DSE_DISPLAY_BLOCKED, "BLOCKED"
            elif m["exchange"] == "DSE":
                reason = "No index data loaded" + (f" ({status.detail})" if status else "")
                idx_status = "INSUFFICIENT_DATA"
            else:
                # Kenya and Uganda are supported by the design but their sources are not integrated yet,
                # and their exchanges' data terms have not been reviewed.
                reason = (f"COMING: {m['exchange']} data is not integrated yet, and its terms of use have not "
                          f"been reviewed (LICENSE_REVIEW_REQUIRED). Nothing is shown until both are done.")
                idx_status = "BLOCKED"
            public = {"DSE": "Tanzania market data is not available right now.",
                      "NSE": "Kenya market data is not yet connected.",
                      "USE": "Uganda market data is not yet connected."}[m["exchange"]]
            if m["exchange"] == "DSE" and not dse_display_allowed():
                public = "Prices from the Dar es Salaam Stock Exchange are not shown until a data licence is held."
            index = {"available": False, "id": m["index"], "status": idx_status, "reason": reason,
                     "public_reason": public}
        count = session.query(func.count()).select_from(Security).filter(Security.exchange == m["exchange"]).scalar()
        out.append({"market": code, "name": m["name"], "exchange": m["exchange"], "currency": m["currency"],
                    "index": index, "securities_in_master": count, "macro": _country_macro(session, code)})
    session_day = market_router.latest_session(session, "DSE") if dse_display_allowed() else None
    return {"markets": out,
            "session": {"exchange": "DSE", "latest_session": session_day.isoformat() if session_day else None,
                        "kind": "End of day",
                        "note": "End-of-day data. Prices update after each session, not during trading."},
            "activity": market_router.activity(session),
            "sectors": market_router.sectors(session),
            "commentary": {"available": False,
                           "reason": "Market commentary is only published when it can be generated from stored, "
                                     "sourced market data. None is loaded."},
            "movers": _dse_movers(session)}


WB_ISO3 = {"TZ": "TZA", "KE": "KEN", "UG": "UGA"}
WB_SHOWN = {"NY.GDP.MKTP.KD.ZG": "Real GDP growth", "FP.CPI.TOTL.ZG": "Inflation",
            "BN.CAB.XOKA.GD.ZS": "Current account (share of GDP)", "PA.NUS.FCRF": "Exchange rate per US dollar"}


def _country_macro(session: Session, market: str) -> dict:
    """Latest annual World Bank figure per indicator for the market's country (CC BY 4.0), each with its year."""
    iso3, rows = WB_ISO3[market], []
    for indicator, label in WB_SHOWN.items():
        o = (session.query(MacroObservation).filter_by(series_id=f"WB_{iso3}_{indicator}")
             .order_by(MacroObservation.observation_date.desc()).first())
        if o is not None:
            rows.append({"indicator": indicator, "label": label, "value": o.value, "unit": o.unit,
                         "year": o.observation_date.year, "source_url": o.source_url})
    if not rows:
        return {"available": False, "status": "INSUFFICIENT_DATA", "reason": "World Bank indicators not loaded."}
    return {"available": True, "rows": rows,
            "attribution": "World Bank, World Development Indicators (CC BY 4.0). Annual figures; the year is shown."}


def _dse_movers(session: Session) -> dict:
    """Breadth and the largest moves on the last trading day, from stored DSE closes. A security whose last
    day had no trade is counted as 'no trade', never as a move (the DSE repeats the previous close)."""
    if not dse_display_allowed():
        return {"available": False, "status": "BLOCKED", "reason": DSE_DISPLAY_BLOCKED}
    listed = {s.id: s for s in session.query(Security).filter_by(exchange="DSE")}
    latest = session.query(func.max(PriceBar.trade_date)).filter(PriceBar.instrument_id.in_(
        [k for k in listed if k != "DSE:DSEI"])).scalar()
    if latest is None:
        return {"available": False, "status": "INSUFFICIENT_DATA", "reason": "No DSE share prices are stored."}
    moves, no_trade, stale = [], [], []
    for sid in sorted(listed):
        bars = (session.query(PriceBar).filter_by(instrument_id=sid).order_by(PriceBar.trade_date.desc()).limit(2).all())
        if len(bars) < 2:
            continue
        last, prev = bars
        if last.trade_date != latest:
            stale.append(sid)
        elif not last.volume:
            no_trade.append(sid)
        elif prev.close:
            moves.append({"security_id": sid, "name": listed[sid].name, "close": last.close,
                          "change": last.close / prev.close - 1, "volume": last.volume})
    moves.sort(key=lambda m: m["change"])
    priced = len(moves) + len(no_trade) + len(stale)
    return {"available": True, "trade_date": latest.isoformat(), "attribution": DSE_ATTRIBUTION,
            "coverage": f"{priced} of {len(listed)} DSE-listed securities have stored prices",
            "breadth": {"up": sum(1 for m in moves if m["change"] > 0), "down": sum(1 for m in moves if m["change"] < 0),
                        "unchanged": sum(1 for m in moves if m["change"] == 0), "no_trade": len(no_trade),
                        "not_updated": len(stale)},
            "gainers": [m for m in reversed(moves) if m["change"] > 0][:5],
            "losers": [m for m in moves if m["change"] < 0][:5],
            "note": ("Change from the previous stored close, for securities that traded on the day. Splits are "
                     "not adjusted here; a security whose history has an unexplained jump is not loaded at all.")}


# ------------------------------------------------------------------ fixed income

def _bond_analytics(m: MacroObservation) -> dict:
    """Duration, convexity and a recomputed price for one auctioned bond. Convention: semi-annual coupons,
    settlement one day after the auction, which reproduces the BoT's published prices (tests/v1/test_bonds.py)."""
    import re
    from datetime import timedelta
    from decimal import Decimal

    from packages.analysis import bonds

    attrs = m.attributes or {}
    coupon = re.match(r"\s*([\d.]+)%", m.label or "")
    try:
        maturity = datetime.strptime(attrs.get("redemption_date", ""), "%d/%m/%Y").date()
    except ValueError:
        maturity = None
    if not coupon or maturity is None:
        return {"available": False, "status": "INSUFFICIENT_DATA",
                "reason": "The auction record lacks the coupon or the redemption date."}
    settle = m.observation_date + timedelta(days=1)
    r = bonds.analyse(Decimal(coupon.group(1)) / 100, m.value, settle, maturity, 2)
    out = {"available": True, "coupon": Decimal(coupon.group(1)) / 100, "maturity": maturity.isoformat(),
           "settlement_assumed": settle.isoformat(), **r,
           "price_change_plus_100bp": bonds.price_change(r["modified_duration"], r["convexity"], Decimal("0.01")),
           "how": "Semi-annual coupons, settlement one day after the auction; computed at the weighted average "
                  "yield. Duration and convexity in years; price per 100 of face value."}
    if attrs.get("weighted_average_price"):
        bot = Decimal(attrs["weighted_average_price"])
        out["check"] = {"bot_published_price": bot, "difference": r["clean_price"] - bot,
                        "note": "The BoT publishes average price and average yield separately; the price at the "
                                "average yield can differ from the average price by a few cents."}
    return out


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
            point["analytics"] = _bond_analytics(m)
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
    capital: Decimal = Field(gt=0, max_digits=18, decimal_places=2)   # money: never a float
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
    universe = [{"id": s.id, "name": s.name, "has_price": s.id in priced} for s in secs]
    if not priced:
        reason = (f"A proposal needs current prices to size positions and check minimum trade sizes. "
                  f"No {m['exchange']} prices are loaded, so no securities, weights or amounts are shown.")
    else:
        reason = (f"Prices are loaded for {len(priced)} of {len(secs)} {m['exchange']} securities, but building a "
                  f"proposal is not implemented yet: the weighting rules, board lots and minimum trade sizes for "
                  f"{m['exchange']} are not in the system. No securities, weights or amounts are shown.")
    return {"available": False, "request": req.model_dump(), "universe": universe, "reason": reason,
            "checks_that_will_apply": ["Position size in shares = amount / last price, rounded down to board lot",
                                       "Every position meets the exchange minimum trade size",
                                       f"Risk profile '{req.risk_profile}' caps equity weight (config)",
                                       "Cash residual reported"]}


# Sign-in and saved portfolios (per-user; every query is scoped to the signed-in user).
@app.middleware("http")
async def analytics_consent(request: Request, call_next):
    """Optional analytics only for visitors who accepted them in the cookie banner; the web app sends
    X-Analytics-Consent: granted for those visitors and nothing for everyone else."""
    token = telemetry.set_consent(request.headers.get("x-analytics-consent") == "granted")
    try:
        return await call_next(request)
    finally:
        telemetry._consent.reset(token)


app.include_router(auth_router.router)
app.include_router(portfolios_router.router)
app.include_router(market_router.router)
app.include_router(news_router.router)
