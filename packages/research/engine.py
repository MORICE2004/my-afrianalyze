"""Execute a research run: build the report once, judge each stage, freeze the result.

A run records ten stages, from the sources to the AI interpretation, each with a state and a plain detail:

    sources, documents, extraction, validation, calculations   <- critical: the run cannot be COMPLETED
    valuation, technical, risk, synthesis, ai_interpretation      without all five completed or partial

Overall state (never COMPLETED when a critical stage failed):
    a critical stage FAILED            -> FAILED
    a critical stage BLOCKED           -> BLOCKED
    a critical stage INSUFFICIENT_DATA -> INSUFFICIENT_DATA
    every stage COMPLETED (or SKIPPED) -> COMPLETED
    otherwise                          -> PARTIAL

The report the run built is stored as `snapshot`, serialised exactly as the API serves it (decimals as
strings), with its SHA-256. A reviewer approves that snapshot, and production serves it, so the numbers
someone signed off cannot drift afterwards. Execution is synchronous: building a report takes well under a
second, so no queue or worker is needed (docs/PRODUCTION_ARCHITECTURE.md).
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone

from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from packages.core import telemetry
from packages.core.config import settings
from packages.database.models import (
    ExtractionConflict,
    FinancialFact,
    ResearchRun,
    ReviewEvent,
    RiskItem,
    Security,
    SourceDocument,
    ValidationCheck,
)
from packages.report.builder import build_report

CRITICAL = ("sources", "documents", "extraction", "validation", "calculations")
STUCK_AFTER = timedelta(minutes=10)
_JSON = TypeAdapter(dict)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    return None if dt is None else dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def to_wire(report: dict) -> dict:
    """The report exactly as the API sends it: Decimal -> exact string, date -> ISO text."""
    return _JSON.dump_python(report, mode="json")


def _stage(name: str, state: str, detail: str, started: float) -> dict:
    return {"stage": name, "state": state, "detail": detail, "critical": name in CRITICAL,
            "duration_ms": round((time.perf_counter() - started) * 1000, 1)}


def _overall(stages: list[dict]) -> str:
    critical = [s["state"] for s in stages if s["critical"]]
    for bad in ("FAILED", "BLOCKED", "INSUFFICIENT_DATA"):
        if bad in critical:
            return bad
    return "COMPLETED" if all(s["state"] in ("COMPLETED", "SKIPPED") for s in stages) else "PARTIAL"


def _assess(session: Session, security_id: str, report: dict | None, build_error: str | None) -> list[dict]:
    t = time.perf_counter()
    stages: list[dict] = []
    docs = session.query(SourceDocument).filter_by(security_id=security_id, kind="annual_report").all()
    stages.append(_stage("sources", "COMPLETED" if docs else "INSUFFICIENT_DATA",
                         f"{len(docs)} annual report(s) on record" if docs
                         else "No annual reports have been ingested for this company", t))
    t = time.perf_counter()
    unhashed = [d.title for d in docs if not d.sha256 or not d.retrieved_at]
    stages.append(_stage("documents", "FAILED" if unhashed else "COMPLETED" if docs else "INSUFFICIENT_DATA",
                         f"Missing hash or retrieval time: {unhashed}" if unhashed
                         else f"{len(docs)} document(s), each with SHA-256 and retrieval time", t))
    t = time.perf_counter()
    facts = session.query(FinancialFact).filter_by(security_id=security_id, is_primary=True).count()
    open_conflicts = (session.query(ExtractionConflict).filter_by(security_id=security_id, status="OPEN")
                      .filter(ExtractionConflict.kind.notin_(["RESTATEMENT", "METHOD_OUTLIER", "SOURCE_INCONSISTENCY"]))
                      .count())
    stages.append(_stage("extraction",
                         "INSUFFICIENT_DATA" if not facts else "PARTIAL" if open_conflicts else "COMPLETED",
                         f"{facts} figures agreed by at least two readers; {open_conflicts} open conflict(s), "
                         f"not used", t))
    t = time.perf_counter()
    checks = session.query(ValidationCheck).filter_by(security_id=security_id).all()
    # A check whose inputs are missing is stored as not passed with "Not checked: ..."; it did not fail.
    unchecked = [c for c in checks if not c.passed and c.detail.startswith("Not checked")]
    failed = [c for c in checks if not c.passed and c not in unchecked]
    ran = len(checks) - len(unchecked)
    stages.append(_stage("validation",
                         "INSUFFICIENT_DATA" if not ran else "PARTIAL" if failed or unchecked else "COMPLETED",
                         f"{ran - len(failed)} of {ran} tie checks pass"
                         + (f"; failing: {', '.join(f'FY{c.fiscal_year} {c.check_name}' for c in failed[:3])} "
                            f"(figures that do not add up in the source are excluded from every calculation)"
                            if failed else "")
                         + (f"; {len(unchecked)} could not be run (inputs missing): "
                            f"{', '.join(f'FY{c.fiscal_year} {c.check_name}' for c in unchecked[:3])}"
                            if unchecked else ""), t))

    if report is None:
        for name in ("calculations", "valuation", "technical", "risk", "synthesis", "ai_interpretation"):
            stages.append({"stage": name, "state": "FAILED" if name == "calculations" else "SKIPPED",
                           "detail": f"The report could not be built: {build_error}" if name == "calculations"
                           else "Not reached", "critical": name in CRITICAL, "duration_ms": 0})
        return stages

    t = time.perf_counter()
    latest = str(max(report["years"])) if report["years"] else None
    ok = sum(1 for r in report["ratios"] if latest and r["values"].get(latest, {}).get("available"))
    total = len(report["ratios"])
    stages.append(_stage("calculations", "COMPLETED" if ok == total else "PARTIAL" if ok else "INSUFFICIENT_DATA",
                         f"{ok} of {total} ratios computed for FY{latest}; the others say why not", t))
    t = time.perf_counter()
    val = report["valuation"]["result"]
    stages.append(_stage("valuation", "COMPLETED" if val.get("available") else val.get("status", "INSUFFICIENT_DATA"),
                         "Residual income, justified P/B and dividend discount, three scenarios"
                         if val.get("available") else val.get("reason", ""), t))
    t = time.perf_counter()
    tech = report["technical"]
    tech_state = ("PARTIAL" if tech.get("stale") else "COMPLETED") if tech.get("available") else tech.get("status", "INSUFFICIENT_DATA")
    stages.append(_stage("technical", tech_state,
                         f"Indicators on closes to {tech.get('last_trade_date')}" + (" (stale)" if tech.get("stale") else "")
                         if tech.get("available") else tech.get("reason", ""), t))
    t = time.perf_counter()
    risks = session.query(RiskItem).filter_by(security_id=security_id).count()
    stages.append(_stage("risk", "COMPLETED" if risks else "INSUFFICIENT_DATA",
                         f"{risks} risks, each quoted from its source page" if risks else "No sourced risks recorded", t))
    t = time.perf_counter()
    rec = report["header"]["recommendation"]
    if not rec.get("available"):
        syn_state, syn = rec.get("status", "INSUFFICIENT_DATA"), rec.get("reason", "")
    elif rec.get("model_view") == "Inconclusive":
        syn_state, syn = "PARTIAL", "Model view withheld: " + rec.get("inconclusive_reason", "")
    else:
        syn_state, syn = "COMPLETED", f"Model view: {rec['model_view']}"
    stages.append(_stage("synthesis", syn_state, syn, t))
    stages.append({"stage": "ai_interpretation", "state": "SKIPPED", "critical": False, "duration_ms": 0,
                   "detail": "Not part of a run: the research copilot answers questions on demand from this run's "
                             "snapshot and never changes a figure."})
    return stages


def execute(session: Session, security_id: str, actor: str = "pipeline") -> ResearchRun:
    """Run the analysis for one security and store the result. Returns the run, whatever its state."""
    if session.get(Security, security_id) is None:
        raise ValueError(f"Unknown security {security_id}")
    now = _now()
    # A run left RUNNING by a crash or restart would block every later run; record what happened instead.
    for stuck in session.query(ResearchRun).filter_by(security_id=security_id, execution_state="RUNNING"):
        if _aware(stuck.started_at) and now - _aware(stuck.started_at) > STUCK_AFTER:
            stuck.execution_state, stuck.finished_at = "FAILED", now
            stuck.error = "Did not finish: the process stopped while the run was in progress."
            session.add(ReviewEvent(run_id=stuck.id, action="execution_failed", actor="engine", note=stuck.error))
        else:
            return stuck                      # a run is already in progress: do not start a duplicate
    session.commit()

    prefix = f"RA-{now:%Y%m%d}-"
    n_today = session.query(ResearchRun).filter(ResearchRun.id.like(prefix + "%")).count()
    run = ResearchRun(id=f"{prefix}{n_today + 1:03d}", security_id=security_id, status="draft",
                      created_at=now, execution_state="QUEUED", data_sha256="", config_sha256="", summary={})
    session.add(run)
    session.add(ReviewEvent(run_id=run.id, action="create", actor=actor, note="Research run queued"))
    session.commit()

    run.execution_state, run.started_at = "RUNNING", _now()
    session.commit()
    telemetry.track("research_started", None, {"security_id": security_id})
    report, wire, error = None, None, None
    try:
        report = build_report(session, security_id)
        wire = to_wire(report)
    except Exception as exc:  # recorded on the run and shown, never swallowed
        error = f"{type(exc).__name__}: {exc}"
        report = None
    stages = _assess(session, security_id, report, error)

    facts = sorted((f.item_code, f.fiscal_year, str(f.value)) for f in
                   session.query(FinancialFact).filter_by(security_id=security_id, is_primary=True))
    run.data_sha256 = hashlib.sha256(json.dumps(facts).encode()).hexdigest()
    run.config_sha256 = hashlib.sha256(b"".join(
        (settings.CONFIG_DIR / n).read_bytes() for n in
        ("valuation.json", "recommendation.json", "source_issues.json", "technical.json"))).hexdigest()
    run.stages, run.error, run.finished_at = stages, error, _now()
    run.execution_state = _overall(stages)
    if wire is not None:
        run.snapshot = wire
        run.snapshot_sha256 = hashlib.sha256(json.dumps(wire, sort_keys=True).encode()).hexdigest()
    run.summary = {"stages": {s["stage"]: s["state"] for s in stages},
                   "model_view": (report or {}).get("header", {}).get("recommendation", {}).get("model_view")}
    # Older drafts of the same company are replaced; a published run stays until a new one is approved.
    for old in session.query(ResearchRun).filter(ResearchRun.security_id == security_id, ResearchRun.id != run.id,
                                                 ResearchRun.status.in_(["draft", "in_review"])):
        old.status, old.superseded_by = "superseded", run.id
    telemetry.track("research_completed", None, {"security_id": security_id, "execution_state": run.execution_state})
    session.add(ReviewEvent(run_id=run.id, action="execute", actor=actor,
                            note=f"{run.execution_state}: " + "; ".join(f"{s['stage']} {s['state']}" for s in stages)))
    session.commit()
    return run


def describe(run: ResearchRun) -> dict:
    """Public view of a run (no snapshot): what ran, how it went, and its review state."""
    return {"run_id": run.id, "security_id": run.security_id, "review_status": run.status,
            "execution_state": run.execution_state or "NOT_EXECUTED",
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "stages": run.stages or [], "error": run.error, "snapshot_sha256": run.snapshot_sha256,
            "reviewer": run.reviewer, "reviewed_at": run.reviewed_at.isoformat() if run.reviewed_at else None}
