"""sign-in sessions, and portfolio holdings by quantity

Revision ID: 7c1e5a2f9d30
Revises: 4b3dcb0cd928
Create Date: 2026-09-25

Adds the session table for sign-in, a created_at on users, indexes on the ownership columns every portfolio
query filters on, a foreign key from holdings to securities, and a quantity per holding. The old weight,
cost basis and purchase date columns become optional (weights are now calculated, not stored).
Only adds or relaxes; nothing is dropped on upgrade. Batch mode so SQLite can apply it too.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import packages.database.types  # noqa: F401  (ExactDecimal)

revision: str = "7c1e5a2f9d30"
down_revision: Union[str, None] = "4b3dcb0cd928"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EXACT = packages.database.types.ExactDecimal(precision=28, scale=10)


def upgrade() -> None:
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_user_sessions_token_hash"), "user_sessions", ["token_hash"], unique=True)

    with op.batch_alter_table("users") as b:
        b.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("saved_portfolios") as b:
        b.create_index(b.f("ix_saved_portfolios_user_id"), ["user_id"], unique=False)

    with op.batch_alter_table("portfolio_holdings") as b:
        b.add_column(sa.Column("quantity", EXACT, nullable=True))
        b.alter_column("weight", existing_type=EXACT, nullable=True)
        b.alter_column("cost_basis", existing_type=EXACT, nullable=True)
        b.alter_column("purchase_date", existing_type=sa.DateTime(timezone=True), nullable=True)
        b.create_index(b.f("ix_portfolio_holdings_portfolio_id"), ["portfolio_id"], unique=False)
        b.create_foreign_key("fk_portfolio_holdings_asset_id_securities", "securities", ["asset_id"], ["id"])


def downgrade() -> None:
    # Restoring NOT NULL fails loudly if holdings without a weight exist, rather than deleting them.
    with op.batch_alter_table("portfolio_holdings") as b:
        b.drop_constraint("fk_portfolio_holdings_asset_id_securities", type_="foreignkey")
        b.drop_index(b.f("ix_portfolio_holdings_portfolio_id"))
        b.alter_column("purchase_date", existing_type=sa.DateTime(timezone=True), nullable=False)
        b.alter_column("cost_basis", existing_type=EXACT, nullable=False)
        b.alter_column("weight", existing_type=EXACT, nullable=False)
        b.drop_column("quantity")

    with op.batch_alter_table("saved_portfolios") as b:
        b.drop_index(b.f("ix_saved_portfolios_user_id"))

    with op.batch_alter_table("users") as b:
        b.drop_column("created_at")

    op.drop_index(op.f("ix_user_sessions_token_hash"), table_name="user_sessions")
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_table("user_sessions")
