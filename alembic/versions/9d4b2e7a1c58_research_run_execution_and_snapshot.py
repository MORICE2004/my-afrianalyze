"""research run execution state, stages and frozen report snapshot

Revision ID: 9d4b2e7a1c58
Revises: 7c1e5a2f9d30
Create Date: 2026-10-07

Adds nullable columns only; existing runs keep working and simply have no execution record.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "9d4b2e7a1c58"
down_revision: Union[str, None] = "7c1e5a2f9d30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMNS = [
    ("execution_state", sa.String(length=20)),
    ("stages", sa.JSON()),
    ("started_at", sa.DateTime(timezone=True)),
    ("finished_at", sa.DateTime(timezone=True)),
    ("error", sa.Text()),
    ("snapshot", sa.JSON()),
    ("snapshot_sha256", sa.String(length=64)),
]


def upgrade() -> None:
    with op.batch_alter_table("research_runs") as b:
        for name, type_ in COLUMNS:
            b.add_column(sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("research_runs") as b:
        for name, _ in reversed(COLUMNS):
            b.drop_column(name)
