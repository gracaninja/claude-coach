"""Add agents, skills, MCP classification

Revision ID: 002
Revises: 001
Create Date: 2026-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add classification columns to tool_usages
    with op.batch_alter_table("tool_usages") as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(16), nullable=True))
        batch_op.add_column(sa.Column("mcp_server", sa.String(128), nullable=True))
        batch_op.add_column(sa.Column("skill_name", sa.String(256), nullable=True))
        batch_op.add_column(sa.Column("subagent_type", sa.String(128), nullable=True))
        batch_op.create_index("ix_tool_usages_category", ["category"])

    # Add agent/skill counters and metadata to sessions
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(sa.Column("subagent_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("skill_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("cli_version", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("slug", sa.String(128), nullable=True))

    # Create subagent_usages table
    op.create_table(
        "subagent_usages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.String(32), nullable=True),
        sa.Column("subagent_type", sa.String(128), nullable=False),
        sa.Column("description", sa.String(512), nullable=True),
        sa.Column("prompt_preview", sa.Text(), nullable=True),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("tool_use_id", sa.String(64), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tool_use_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subagent_usages_session_id", "subagent_usages", ["session_id"])
    op.create_index("ix_subagent_usages_subagent_type", "subagent_usages", ["subagent_type"])


def downgrade() -> None:
    op.drop_table("subagent_usages")

    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_column("slug")
        batch_op.drop_column("cli_version")
        batch_op.drop_column("skill_count")
        batch_op.drop_column("subagent_count")

    with op.batch_alter_table("tool_usages") as batch_op:
        batch_op.drop_index("ix_tool_usages_category")
        batch_op.drop_column("subagent_type")
        batch_op.drop_column("skill_name")
        batch_op.drop_column("mcp_server")
        batch_op.drop_column("category")
