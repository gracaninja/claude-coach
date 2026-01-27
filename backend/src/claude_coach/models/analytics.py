"""Analytics aggregation models."""

from datetime import date
from sqlalchemy import String, Integer, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from claude_coach.models.database import Base


class DailyStats(Base):
    """Daily aggregated statistics."""

    __tablename__ = "daily_stats"
    __table_args__ = (
        UniqueConstraint("date", "project_path", name="uq_daily_stats_date_project"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    project_path: Mapped[str] = mapped_column(String(512), default="*")  # * for all projects

    # Session stats
    session_count: Mapped[int] = mapped_column(Integer, default=0)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # Token stats
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_creation_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # Tool stats
    tool_call_count: Mapped[int] = mapped_column(Integer, default=0)

    # Error stats
    error_count: Mapped[int] = mapped_column(Integer, default=0)


class ToolStats(Base):
    """Tool usage statistics."""

    __tablename__ = "tool_stats"
    __table_args__ = (
        UniqueConstraint("date", "tool_name", name="uq_tool_stats_date_tool"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    tool_name: Mapped[str] = mapped_column(String(128), index=True)

    call_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_ms: Mapped[int] = mapped_column(Integer, default=0)


class ErrorStats(Base):
    """Error type statistics."""

    __tablename__ = "error_stats"
    __table_args__ = (
        UniqueConstraint("date", "error_type", name="uq_error_stats_date_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    error_type: Mapped[str] = mapped_column(String(128), index=True)

    count: Mapped[int] = mapped_column(Integer, default=0)
