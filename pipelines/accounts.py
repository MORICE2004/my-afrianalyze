r"""Account administration from the command line (there is no payment code: plans are granted by hand).

    .venv\Scripts\python -m pipelines.accounts show --email someone@example.com
    .venv\Scripts\python -m pipelines.accounts grant-plan --email someone@example.com --plan pro
    .venv\Scripts\python -m pipelines.accounts set-role --email someone@example.com --role admin

Run it with DATABASE_URL pointing at the database you mean (production: the Neon URL from the dashboard, set in
the shell for this one command, never written to a file). It changes nothing but the one user's plan or role,
and prints what it did. Passwords are never read or shown.
"""
from __future__ import annotations

import argparse
import sys

from packages.database.models import Entitlement, Plan, User
from packages.database.session import SessionLocal

ROLES = ("user", "admin")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="pipelines.accounts")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("show", "grant-plan", "set-role"):
        p = sub.add_parser(name)
        p.add_argument("--email", required=True)
        if name == "grant-plan":
            p.add_argument("--plan", required=True, help="free or pro (the plans table)")
        if name == "set-role":
            p.add_argument("--role", required=True, choices=ROLES)
    args = ap.parse_args(argv)

    with SessionLocal() as s:
        user = s.query(User).filter_by(email=args.email.strip().lower()).first()
        if user is None:
            print(f"No account with the email {args.email}. The person must sign up first.")
            return 1
        if args.cmd == "grant-plan":
            plan = s.get(Plan, args.plan)
            if plan is None or not plan.is_active:
                print(f"No active plan '{args.plan}'. Plans: {', '.join(p.id for p in s.query(Plan))}.")
                return 1
            user.plan_id = plan.id
            s.commit()
        elif args.cmd == "set-role":
            user.role = args.role
            s.commit()
        features = sorted(e.feature for e in s.query(Entitlement).filter_by(plan_id=user.plan_id)) if user.plan_id else []
        print(f"{user.email}: plan {user.plan_id or 'free'}, role {user.role}, features {features or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
