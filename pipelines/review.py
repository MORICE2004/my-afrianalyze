r"""Human review of research runs (PRODUCT_CONTEXT.md section 72).

    .venv\Scripts\python -m pipelines.review list
    .venv\Scripts\python -m pipelines.review submit  RA-20260918-001 --by "Analyst Name" --note "Ready"
    .venv\Scripts\python -m pipelines.review approve RA-20260918-001 --by "Reviewer Name" --note "Checked ..."
    .venv\Scripts\python -m pipelines.review reject  RA-20260918-001 --by "Reviewer Name" --note "Fix ..."

Lifecycle: draft -> in_review -> published -> superseded. Approval needs a named
reviewer and a note. Publishing a run supersedes the previously published run for
the same security. Every action is written to review_events.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from packages.database.models import ResearchRun, ReviewEvent
from packages.database.session import SessionLocal

TRANSITIONS = {"submit": ("draft", "in_review"), "approve": ("in_review", "published"),
               "reject": ("in_review", "draft")}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["list", *TRANSITIONS])
    ap.add_argument("run_id", nargs="?")
    ap.add_argument("--by", help="Full name of the person taking the action")
    ap.add_argument("--note", help="Reason or review note")
    args = ap.parse_args(argv)

    with SessionLocal() as s:
        if args.action == "list":
            for r in s.query(ResearchRun).order_by(ResearchRun.created_at.desc()):
                print(f"{r.id}  {r.security_id:10s} {r.status:10s} created {r.created_at:%Y-%m-%d %H:%M} "
                      f"reviewer={r.reviewer or '-'}")
            return 0
        if not (args.run_id and args.by and args.note):
            print("run_id, --by and --note are required")
            return 2
        if len(args.by.split()) < 2:
            print("--by must be the reviewer's full name")
            return 2
        run = s.get(ResearchRun, args.run_id)
        if run is None:
            print(f"No run {args.run_id}")
            return 1
        before, after = TRANSITIONS[args.action]
        if run.status != before:
            print(f"{run.id} is {run.status}; '{args.action}' needs status {before}")
            return 1
        now = datetime.now(timezone.utc)
        if args.action == "approve":
            if run.summary.get("failed_checks"):
                print(f"{run.id} has {run.summary['failed_checks']} failed validation check(s). Approving anyway is "
                      "allowed only if the note explains each one.")
            for old in s.query(ResearchRun).filter_by(security_id=run.security_id, status="published"):
                old.status, old.superseded_by = "superseded", run.id
                s.add(ReviewEvent(run_id=old.id, action="supersede", actor=args.by, note=f"Replaced by {run.id}"))
            run.reviewer, run.reviewed_at = args.by, now
        run.status = after
        s.add(ReviewEvent(run_id=run.id, action=args.action, actor=args.by, note=args.note, at=now))
        s.commit()
        print(f"{run.id}: {before} -> {after} by {args.by}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
