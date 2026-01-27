"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Sessions table
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("project_path", sa.String(512), nullable=False),
        sa.Column("first_prompt", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("git_branch", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("modified_at", sa.DateTime(), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False, default=0),
        sa.Column("total_input_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("total_output_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("total_cache_read_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("total_cache_creation_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("tool_call_count", sa.Integer(), nullable=False, default=0),
        sa.Column("error_count", sa.Integer(), nullable=False, default=0),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_session_id", "sessions", ["session_id"], unique=True)

    # Messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=True),
        sa.Column("cache_creation_tokens", sa.Integer(), nullable=True),
        sa.Column("cumulative_context_tokens", sa.Integer(), nullable=True),
        sa.Column("message_index", sa.Integer(), nullable=False, default=0),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_session_id", "messages", ["session_id"])

    # Tool usages table
    op.create_table(
        "tool_usages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column("tool_use_id", sa.String(64), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("input_preview", sa.Text(), nullable=True),
        sa.Column("is_error", sa.Boolean(), nullable=False, default=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tool_usages_session_id", "tool_usages", ["session_id"])
    op.create_index("ix_tool_usages_tool_name", "tool_usages", ["tool_name"])

    # Error events table
    op.create_table(
        "error_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("error_type", sa.String(128), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("retry_attempt", sa.Integer(), nullable=True),
        sa.Column("retry_in_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_error_events_session_id", "error_events", ["session_id"])
    op.create_index("ix_error_events_error_type", "error_events", ["error_type"])

    # Daily stats table
    op.create_table(
        "daily_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("project_path", sa.String(512), nullable=False, default="*"),
        sa.Column("session_count", sa.Integer(), nullable=False, default=0),
        sa.Column("message_count", sa.Integer(), nullable=False, default=0),
        sa.Column("input_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("output_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("cache_creation_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("tool_call_count", sa.Integer(), nullable=False, default=0),
        sa.Column("error_count", sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", "project_path", name="uq_daily_stats_date_project"),
    )
    op.create_index("ix_daily_stats_date", "daily_stats", ["date"])

    # Tool stats table
    op.create_table(
        "tool_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column("call_count", sa.Integer(), nullable=False, default=0),
        sa.Column("error_count", sa.Integer(), nullable=False, default=0),
        sa.Column("total_duration_ms", sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", "tool_name", name="uq_tool_stats_date_tool"),
    )
    op.create_index("ix_tool_stats_date", "tool_stats", ["date"])
    op.create_index("ix_tool_stats_tool_name", "tool_stats", ["tool_name"])

    # Error stats table
    op.create_table(
        "error_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("error_type", sa.String(128), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", "error_type", name="uq_error_stats_date_type"),
    )
    op.create_index("ix_error_stats_date", "error_stats", ["date"])
    op.create_index("ix_error_stats_error_type", "error_stats", ["error_type"])


def downgrade() -> None:
    op.drop_table("error_stats")
    op.drop_table("tool_stats")
    op.drop_table("daily_stats")
    op.drop_table("error_events")
    op.drop_table("tool_usages")
    op.drop_table("messages")
    op.drop_table("sessions")
