"""Generate insights and recommendations from usage patterns."""

from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from claude_coach.models import Session, ToolUsage, ErrorEvent, Message


@dataclass
class Insight:
    """A single insight or recommendation."""

    category: str  # efficiency, tools, errors, patterns
    title: str
    description: str
    severity: str  # info, suggestion, warning
    metric_value: Optional[float] = None
    metric_label: Optional[str] = None


class InsightsEngine:
    """Generate insights from usage data."""

    def __init__(self, db: DBSession):
        self.db = db

    def generate_all_insights(self) -> list[Insight]:
        """Generate all available insights."""
        insights = []

        insights.extend(self._efficiency_insights())
        insights.extend(self._tool_insights())
        insights.extend(self._error_insights())
        insights.extend(self._pattern_insights())

        return insights

    def _efficiency_insights(self) -> list[Insight]:
        """Generate efficiency-related insights."""
        insights = []

        sessions = self.db.query(Session).all()
        if not sessions:
            return insights

        # Cache hit rate analysis
        total_cache_read = sum(s.total_cache_read_tokens for s in sessions)
        total_cache_create = sum(s.total_cache_creation_tokens for s in sessions)
        total_cache = total_cache_read + total_cache_create

        if total_cache > 0:
            cache_hit_rate = total_cache_read / total_cache

            if cache_hit_rate < 0.5:
                insights.append(Insight(
                    category="efficiency",
                    title="Low Cache Hit Rate",
                    description=(
                        "Your cache hit rate is below 50%. Consider keeping related work "
                        "in the same session to benefit from context caching."
                    ),
                    severity="suggestion",
                    metric_value=cache_hit_rate * 100,
                    metric_label="Cache hit rate (%)",
                ))
            elif cache_hit_rate > 0.8:
                insights.append(Insight(
                    category="efficiency",
                    title="Excellent Cache Utilization",
                    description=(
                        "Your cache hit rate is above 80%. You're effectively reusing "
                        "context across conversations."
                    ),
                    severity="info",
                    metric_value=cache_hit_rate * 100,
                    metric_label="Cache hit rate (%)",
                ))

        # Token efficiency
        total_input = sum(s.total_input_tokens for s in sessions)
        total_output = sum(s.total_output_tokens for s in sessions)

        if total_input > 0:
            output_ratio = total_output / total_input

            if output_ratio < 0.1:
                insights.append(Insight(
                    category="efficiency",
                    title="Low Output Ratio",
                    description=(
                        "Your output-to-input token ratio is very low. This might indicate "
                        "large context but brief responses. Consider if all context is necessary."
                    ),
                    severity="suggestion",
                    metric_value=output_ratio * 100,
                    metric_label="Output/Input ratio (%)",
                ))

        return insights

    def _tool_insights(self) -> list[Insight]:
        """Generate tool usage insights."""
        insights = []

        # Get tool usage stats
        tool_counts = (
            self.db.query(ToolUsage.tool_name, func.count(ToolUsage.id).label("count"))
            .group_by(ToolUsage.tool_name)
            .all()
        )

        if not tool_counts:
            return insights

        tool_dict = {name: count for name, count in tool_counts}
        total_tools = sum(tool_dict.values())

        # Check for underutilized tools
        underutilized = []
        if "Grep" not in tool_dict or tool_dict.get("Grep", 0) < total_tools * 0.05:
            underutilized.append("Grep")
        if "Glob" not in tool_dict or tool_dict.get("Glob", 0) < total_tools * 0.05:
            underutilized.append("Glob")

        if underutilized:
            insights.append(Insight(
                category="tools",
                title="Underutilized Search Tools",
                description=(
                    f"Tools like {', '.join(underutilized)} are rarely used. "
                    "These can be more efficient than reading entire files."
                ),
                severity="suggestion",
            ))

        # Check for Bash overuse
        bash_count = tool_dict.get("Bash", 0)
        if bash_count > total_tools * 0.5:
            insights.append(Insight(
                category="tools",
                title="High Bash Usage",
                description=(
                    "Over 50% of tool calls are Bash commands. Consider using "
                    "specialized tools (Read, Edit, Grep) for file operations."
                ),
                severity="suggestion",
                metric_value=bash_count / total_tools * 100,
                metric_label="Bash usage (%)",
            ))

        # Identify most productive tools
        top_tool = max(tool_dict.items(), key=lambda x: x[1])
        insights.append(Insight(
            category="tools",
            title=f"Most Used Tool: {top_tool[0]}",
            description=f"You use {top_tool[0]} most frequently ({top_tool[1]} times).",
            severity="info",
            metric_value=top_tool[1],
            metric_label="Total uses",
        ))

        return insights

    def _error_insights(self) -> list[Insight]:
        """Generate error-related insights."""
        insights = []

        sessions = self.db.query(Session).all()
        if not sessions:
            return insights

        total_sessions = len(sessions)
        total_errors = sum(s.error_count for s in sessions)

        error_rate = total_errors / total_sessions if total_sessions > 0 else 0

        if error_rate > 1:
            # Get most common error type
            error_counts = (
                self.db.query(ErrorEvent.error_type, func.count(ErrorEvent.id))
                .group_by(ErrorEvent.error_type)
                .order_by(func.count(ErrorEvent.id).desc())
                .first()
            )

            if error_counts:
                insights.append(Insight(
                    category="errors",
                    title="Frequent Errors",
                    description=(
                        f"You're experiencing {error_rate:.1f} errors per session on average. "
                        f"Most common: {error_counts[0]}."
                    ),
                    severity="warning",
                    metric_value=error_rate,
                    metric_label="Errors per session",
                ))
        elif total_errors == 0:
            insights.append(Insight(
                category="errors",
                title="No Errors Recorded",
                description="Great job! No API errors have been recorded.",
                severity="info",
            ))

        return insights

    def _pattern_insights(self) -> list[Insight]:
        """Generate workflow pattern insights."""
        insights = []

        sessions = self.db.query(Session).all()
        if not sessions:
            return insights

        # Session length analysis
        session_lengths = [s.message_count for s in sessions]
        avg_length = sum(session_lengths) / len(session_lengths)

        if avg_length > 50:
            insights.append(Insight(
                category="patterns",
                title="Long Sessions",
                description=(
                    "Your average session has many messages. Consider breaking complex "
                    "tasks into smaller, focused sessions for better context management."
                ),
                severity="suggestion",
                metric_value=avg_length,
                metric_label="Avg messages/session",
            ))
        elif avg_length < 5:
            insights.append(Insight(
                category="patterns",
                title="Short Sessions",
                description=(
                    "Your sessions are typically short. This is efficient for quick tasks, "
                    "but for complex work, longer sessions can leverage context better."
                ),
                severity="info",
                metric_value=avg_length,
                metric_label="Avg messages/session",
            ))

        # Duration analysis
        durations = [s.duration_ms for s in sessions if s.duration_ms]
        if durations:
            avg_duration_min = (sum(durations) / len(durations)) / 60000

            if avg_duration_min > 30:
                insights.append(Insight(
                    category="patterns",
                    title="Extended Sessions",
                    description=(
                        f"Your average session lasts {avg_duration_min:.0f} minutes. "
                        "Remember to take breaks during long coding sessions!"
                    ),
                    severity="info",
                    metric_value=avg_duration_min,
                    metric_label="Avg duration (min)",
                ))

        return insights
