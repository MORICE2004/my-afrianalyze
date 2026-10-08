"""news images

Revision ID: d2b6f8a4c9e1
Revises: c7a1e3f9b2d4
Create Date: 2026-10-08

The publisher's own preview image for a story, with its checked size.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2b6f8a4c9e1"
down_revision: Union[str, None] = "c7a1e3f9b2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLS = (("image_url", sa.Text()), ("image_width", sa.Integer()), ("image_height", sa.Integer()),
        ("image_checked_at", sa.DateTime(timezone=True)))


def upgrade() -> None:
    with op.batch_alter_table("news_items") as b:
        for name, kind in COLS:
            b.add_column(sa.Column(name, kind, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("news_items") as b:
        for name, _ in reversed(COLS):
            b.drop_column(name)
