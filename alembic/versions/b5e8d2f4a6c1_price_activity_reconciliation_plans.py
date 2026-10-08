"""daily price activity, provider reconciliation, free and pro plans

Revision ID: b5e8d2f4a6c1
Revises: 9d4b2e7a1c58
Create Date: 2026-10-08

1. price_bars gains the other fields the DSE publishes for each day (open, high, low, turnover, market
   capitalisation). All nullable: bars stored before this keep working, and a backfill fills them from each
   bar's own stored source file (pipelines.dse.backfill_activity).
2. price_reconciliations records every comparison of one day's close between two market-data providers,
   with the difference, so a disagreement is shown as CONFLICTING_SOURCE instead of silently picking one.
3. The two plans the app knows about. "pro" carries the excel_export entitlement; nobody is on it until an
   administrator grants it (pipelines.accounts). There is no payment code.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import packages.database.types

revision: str = "b5e8d2f4a6c1"
down_revision: Union[str, None] = "9d4b2e7a1c58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEC = packages.database.types.ExactDecimal(precision=28, scale=10)
ACTIVITY = ("open", "high", "low", "turnover", "market_cap")


def upgrade() -> None:
    with op.batch_alter_table("price_bars") as b:
        for name in ACTIVITY:
            b.add_column(sa.Column(name, DEC, nullable=True))

    op.create_table(
        "price_reconciliations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.String(length=32), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("provider_a", sa.String(length=40), nullable=False),
        sa.Column("symbol_a", sa.String(length=40), nullable=False),
        sa.Column("close_a", DEC, nullable=False),
        sa.Column("provider_b", sa.String(length=40), nullable=False),
        sa.Column("symbol_b", sa.String(length=40), nullable=False),
        sa.Column("close_b", DEC, nullable=False),
        sa.Column("difference", DEC, nullable=False),
        sa.Column("difference_pct", DEC, nullable=False),
        sa.Column("tolerance_pct", DEC, nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_price_reconciliations_instrument_id", "price_reconciliations", ["instrument_id"])

    plans = sa.table("plans", sa.column("id", sa.String), sa.column("name", sa.String),
                     sa.column("description", sa.Text), sa.column("is_active", sa.Boolean))
    conn = op.get_bind()
    have = {r[0] for r in conn.execute(sa.text("SELECT id FROM plans"))}
    rows = [{"id": "free", "name": "Free", "is_active": True,
             "description": "Company research, markets, fixed income and saved portfolios."},
            {"id": "pro", "name": "Pro", "is_active": True,
             "description": "Everything in Free, plus the analyst workbook (Excel export)."}]
    op.bulk_insert(plans, [r for r in rows if r["id"] not in have])
    if "pro" not in have:
        ent = sa.table("entitlements", sa.column("plan_id", sa.String), sa.column("feature", sa.String),
                       sa.column("monthly_limit", sa.Integer))
        op.bulk_insert(ent, [{"plan_id": "pro", "feature": "excel_export", "monthly_limit": None}])


def downgrade() -> None:
    op.execute("DELETE FROM entitlements WHERE plan_id = 'pro' AND feature = 'excel_export'")
    op.execute("UPDATE users SET plan_id = NULL WHERE plan_id IN ('free', 'pro')")
    op.execute("DELETE FROM plans WHERE id IN ('free', 'pro')")
    op.drop_index("ix_price_reconciliations_instrument_id", table_name="price_reconciliations")
    op.drop_table("price_reconciliations")
    with op.batch_alter_table("price_bars") as b:
        for name in reversed(ACTIVITY):
            b.drop_column(name)
