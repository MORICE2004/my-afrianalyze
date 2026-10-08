"""The research on one company as a stream of events, each sent the moment its work is done.

The company page shows these as its progress timeline and reveals each part of the research as it arrives.
Nothing waits on a timer: if the work takes 300 milliseconds, the timeline completes in 300 milliseconds, and
every stage shows its real duration. The stages are the research engine's own (packages/research/engine.py),
so what the reader sees is what a research run records.

Events, one JSON object per line (NDJSON):
  {"event": "step", "step": "company", "state": "COMPLETED", "label": ..., "duration_ms": ...}
  {"event": "security", "data": {...}}       the security master entry
  {"event": "quote", "data": {...}}          the latest stored close (apps/api/routers/market.py)
  {"event": "stage", "data": {...}}          one research-run stage (sources ... synthesis)
  {"event": "report", "data": {...}}         the full report, as GET /api/v1/reports/{id} returns it
  {"event": "unavailable", "status": ..., "reason": ...}   the research cannot be shown; the stream ends
  {"event": "done", "total_ms": ...}

In production the reader sees what a reviewer approved (section 72): the stream loads the published run's frozen
snapshot and replays the stages that run recorded when it executed, marked "recorded" with their execution
time, instead of building a fresh report.
"""
from __future__ import annotations

import time
from collections.abc import Iterator

from sqlalchemy.orm import Session

from packages.core import telemetry
from packages.core.config import AppEnvironment, settings
from packages.database.models import ResearchRun, Security, SourceDocument


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 1)


def events(session: Session, security_id: str, security_view, quote_view, to_wire) -> Iterator[dict]:
    """security_view(sec) and quote_view(sec) are the API's own serialisers, so the stream and the plain
    endpoints can never disagree. to_wire turns Decimals and dates into JSON-safe values."""
    from packages.report.builder import build_report
    from packages.research.engine import input_stages, output_stages

    t_all = time.perf_counter()
    t = time.perf_counter()
    sec = session.get(Security, security_id.upper())
    if sec is None:
        yield {"event": "unavailable", "status": "NOT_FOUND",
               "reason": f"No listed company matches {security_id}."}
        return
    yield {"event": "step", "step": "company", "state": "COMPLETED", "label": f"Found {sec.name}",
           "duration_ms": _ms(t)}
    yield {"event": "security", "data": to_wire(security_view(sec))}

    t = time.perf_counter()
    quote = quote_view(sec)
    yield {"event": "step", "step": "price", "state": "COMPLETED" if quote.get("available") else quote.get("status"),
           "label": "Latest price retrieved" if quote.get("available") else "No price to show",
           "duration_ms": _ms(t)}
    yield {"event": "quote", "data": to_wire(quote)}

    has_docs = session.query(SourceDocument).filter_by(security_id=sec.id, kind="annual_report").first()
    if has_docs is None:
        yield {"event": "unavailable", "status": "INSUFFICIENT_DATA",
               "reason": (f"Research on {sec.name} is not available yet: its annual reports have not been "
                          f"collected and checked. The price above is shown on its own.")}
        yield {"event": "done", "total_ms": _ms(t_all)}
        return

    if settings.APP_ENV == AppEnvironment.PRODUCTION:
        yield from _published(session, sec, t_all)
        return

    for stage in input_stages(session, sec.id):
        yield {"event": "stage", "data": stage}
    t = time.perf_counter()
    report, error = None, None
    try:
        report = build_report(session, sec.id)
    except Exception as exc:  # shown as a FAILED calculations stage, never swallowed
        error = f"{type(exc).__name__}: {exc}"
    build_ms = _ms(t)
    for stage in output_stages(session, sec.id, report, error):
        if stage["stage"] == "calculations":
            stage = {**stage, "duration_ms": round(stage["duration_ms"] + build_ms, 1)}
        yield {"event": "stage", "data": stage}
    if report is None:
        yield {"event": "unavailable", "status": "FAILED",
               "reason": "The research could not be calculated. The problem has been recorded."}
    else:
        telemetry.track("report_viewed", None, {"security_id": sec.id, "frozen": False})
        yield {"event": "report", "data": to_wire(report)}
    yield {"event": "done", "total_ms": _ms(t_all)}


def _published(session: Session, sec: Security, t_all: float) -> Iterator[dict]:
    run = (session.query(ResearchRun).filter_by(security_id=sec.id, status="published")
           .filter(ResearchRun.snapshot.isnot(None)).order_by(ResearchRun.reviewed_at.desc()).first())
    if run is None:
        yield {"event": "unavailable", "status": "IN_REVIEW",
               "reason": (f"The research on {sec.name} is being reviewed and has not been published yet. "
                          f"The price above is current.")}
        yield {"event": "done", "total_ms": _ms(t_all)}
        return
    executed = run.finished_at.isoformat() if run.finished_at else None
    for stage in run.stages or []:
        yield {"event": "stage", "data": {**stage, "recorded": True, "executed_at": executed}}
    report = dict(run.snapshot)
    report["review"] = {**report.get("review", {}), "run_id": run.id, "status": run.status,
                        "reviewer": run.reviewer, "reviewed_at": run.reviewed_at.isoformat() if run.reviewed_at else None,
                        "snapshot_sha256": run.snapshot_sha256, "frozen": True}
    telemetry.track("report_viewed", None, {"security_id": sec.id, "frozen": True})
    yield {"event": "report", "data": report}
    yield {"event": "done", "total_ms": _ms(t_all)}
