"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("max_user_id", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("alias", sa.String(length=64), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="member"),
        sa.Column("consent_accepted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Moscow"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_max_user_id", "users", ["max_user_id"], unique=True)

    op.create_table(
        "time_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("action_text", sa.Text(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("abc_score", sa.String(length=1), nullable=True),
        sa.Column("source", sa.String(length=16), nullable=False, server_default="text"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_time_entries_user_id", "time_entries", ["user_id"])
    op.create_index("ix_time_entries_entry_date", "time_entries", ["entry_date"])

    op.create_table(
        "daily_review_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column("entry_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_daily_review_sessions_user_id", "daily_review_sessions", ["user_id"])
    op.create_index("ix_daily_review_sessions_review_date", "daily_review_sessions", ["review_date"])

    op.create_table(
        "parse_errors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("error_type", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("parse_errors")
    op.drop_index("ix_daily_review_sessions_review_date", table_name="daily_review_sessions")
    op.drop_index("ix_daily_review_sessions_user_id", table_name="daily_review_sessions")
    op.drop_table("daily_review_sessions")
    op.drop_index("ix_time_entries_entry_date", table_name="time_entries")
    op.drop_index("ix_time_entries_user_id", table_name="time_entries")
    op.drop_table("time_entries")
    op.drop_index("ix_users_max_user_id", table_name="users")
    op.drop_table("users")
