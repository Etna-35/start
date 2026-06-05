"""add per-user review time (review_hour, review_minute)

Revision ID: 0003_user_review_time
Revises: 0002_category_nullable
Create Date: 2026-06-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_user_review_time"
down_revision: Union[str, None] = "0002_category_nullable"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("review_hour", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("review_minute", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "review_minute")
    op.drop_column("users", "review_hour")
