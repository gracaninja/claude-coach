"""Anonymize metrics for safe sharing."""

from datetime import date, timedelta
from typing import Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from claude_coach.models import (
    Session,
    Message,
    ToolUsage,
    ErrorEvent,
    DailyStats,
)
from claude_coach.schemas.community import AnonymizedMetrics


class MetricsAnonymizer:
    """Generate anonymized metrics from local data."""

    def __init__(self, db: DBSession):
        self.db = db

    def generate_anonymized_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AnonymizedMetrics:
        """Generate anonymized metrics for a time period.

        This extracts only aggregate statistics - no prompts, code, or
        identifying information is included.
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Query sessions in date range
        sessions_query = self.db.query(Session).filter(
            Session.created_at >= start_date,
            Session.created_at <= end_date,
        )

        sessions = sessions_query.all()
        total_sessions = len(sessions)

        if total_sessions == 0:
            return AnonymizedMetrics(
                period_start=start_date,
                period_end=end_date,
                total_sessions=0,
                total_messages=0,
                avg_messages_per_session=0,
                total_input_tokens=0,
                total_output_tokens=0,
                total_cache_read_tokens=0,
                avg_tokens_per_session=0,
                tool_usage={},
                top_tools=[],
                total_errors=0,
                error_types={},
                cache_hit_rate=0,
                avg_tools_per_session=0,
            )

        # Aggregate session stats
        total_messages = sum(s.message_count for s in sessions)
        total_input_tokens = sum(s.total_input_tokens for s in sessions)
        total_output_tokens = sum(s.total_output_tokens for s in sessions)
        total_cache_read = sum(s.total_cache_read_tokens for s in sessions)
        total_cache_create = sum(s.total_cache_creation_tokens for s in sessions)
        total_tool_calls = sum(s.tool_call_count for s in sessions)
        total_errors = sum(s.error_count for s in sessions)

        # Calculate duration (if available)
        durations = [s.duration_ms for s in sessions if s.duration_ms]
        avg_duration_minutes = None
        if durations:
            avg_duration_minutes = (sum(durations) / len(durations)) / 60000

        # Tool usage counts
        session_ids = [s.id for s in sessions]
        tool_counts = (
            self.db.query(ToolUsage.tool_name, func.count(ToolUsage.id))
            .filter(ToolUsage.session_id.in_(session_ids))
            .group_by(ToolUsage.tool_name)
            .all()
        )
        tool_usage = {name: count for name, count in tool_counts}
        top_tools = sorted(tool_usage.keys(), key=lambda x: tool_usage[x], reverse=True)[:10]

        # Error type counts
        error_counts = (
            self.db.query(ErrorEvent.error_type, func.count(ErrorEvent.id))
            .filter(ErrorEvent.session_id.in_(session_ids))
            .group_by(ErrorEvent.error_type)
            .all()
        )
        error_types = {err_type: count for err_type, count in error_counts}

        # Calculate cache hit rate
        total_cache = total_cache_read + total_cache_create
        cache_hit_rate = total_cache_read / total_cache if total_cache > 0 else 0

        return AnonymizedMetrics(
            period_start=start_date,
            period_end=end_date,
            total_sessions=total_sessions,
            total_messages=total_messages,
            avg_messages_per_session=total_messages / total_sessions,
            avg_session_duration_minutes=avg_duration_minutes,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_cache_read_tokens=total_cache_read,
            avg_tokens_per_session=(total_input_tokens + total_output_tokens) / total_sessions,
            tool_usage=tool_usage,
            top_tools=top_tools,
            total_errors=total_errors,
            error_types=error_types,
            cache_hit_rate=cache_hit_rate,
            avg_tools_per_session=total_tool_calls / total_sessions,
        )

    def export_to_json(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> str:
        """Export anonymized metrics as JSON string."""
        metrics = self.generate_anonymized_metrics(start_date, end_date)
        return metrics.model_dump_json(indent=2)
