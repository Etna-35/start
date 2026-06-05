"""make time_entries.category nullable (categories removed from product)

Revision ID: 0002_category_nullable
Revises: 0001_initial
Create Date: 2026-06-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_category_nullable"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "time_entries",
        "category",
        existing_type=sa.String(length=64),
        nullable=True,
        server_default=None,
    )


def downgrade() -> None:
    op.alter_column(
        "time_entries",
        "category",
        existing_type=sa.String(length=64),
        nullable=False,
    )
