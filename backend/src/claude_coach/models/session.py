"""Session and message models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from claude_coach.models.database import Base


class Session(Base):
    """A Claude Code session."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    project_path: Mapped[str] = mapped_column(String(512))
    first_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    git_branch: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Aggregated stats (computed on import)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cache_creation_tokens: Mapped[int] = mapped_column(Integer, default=0)
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    # Duration in milliseconds
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Agent/Skill/MCP summary counters
    subagent_count: Mapped[int] = mapped_column(Integer, default=0)
    skill_count: Mapped[int] = mapped_column(Integer, default=0)

    # Session metadata
    cli_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )
    tool_usages: Mapped[list["ToolUsage"]] = relationship(
        "ToolUsage", back_populates="session", cascade="all, delete-orphan"
    )
    errors: Mapped[list["ErrorEvent"]] = relationship(
        "ErrorEvent", back_populates="session", cascade="all, delete-orphan"
    )
    subagent_usages: Mapped[list["SubagentUsage"]] = relationship(
        "SubagentUsage", back_populates="session", cascade="all, delete-orphan"
    )


class Message(Base):
    """A single message in a session."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)

    # Message data
    role: Mapped[str] = mapped_column(String(32))  # user, assistant, system
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # For assistant messages
    model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cache_read_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cache_creation_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Context tracking
    cumulative_context_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Message index in session
    message_index: Mapped[int] = mapped_column(Integer, default=0)

    # Relationship
    session: Mapped["Session"] = relationship("Session", back_populates="messages")


class ToolUsage(Base):
    """A tool call within a session."""

    __tablename__ = "tool_usages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)

    tool_name: Mapped[str] = mapped_column(String(128), index=True)
    tool_use_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Tool input (truncated for storage)
    input_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Result info
    is_error: Mapped[bool] = mapped_column(Boolean, default=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Classification
    category: Mapped[Optional[str]] = mapped_column(String(16), nullable=True, index=True)  # native, mcp, skill, agent
    mcp_server: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # MCP server name
    skill_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)  # Skill name for Skill tool
    subagent_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # Subagent type for Task tool

    # Relationship
    session: Mapped["Session"] = relationship("Session", back_populates="tool_usages")


class ErrorEvent(Base):
    """An error that occurred during a session."""

    __tablename__ = "error_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)

    error_type: Mapped[str] = mapped_column(String(128), index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Retry info
    retry_attempt: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    retry_in_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationship
    session: Mapped["Session"] = relationship("Session", back_populates="errors")


class SubagentUsage(Base):
    """A subagent spawned via the Task tool during a session."""

    __tablename__ = "subagent_usages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)

    # Agent identification
    agent_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # short hex id
    subagent_type: Mapped[str] = mapped_column(String(128), index=True)  # Explore, Plan, Bash, etc.
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    prompt_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # truncated prompt

    # Configuration
    model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # model override

    # Timing
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    tool_use_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # links to Task tool_use

    # Completion stats (populated from task result)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_tool_use_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # completed, error

    # Relationship
    session: Mapped["Session"] = relationship("Session", back_populates="subagent_usages")
