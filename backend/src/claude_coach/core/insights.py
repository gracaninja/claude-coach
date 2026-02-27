"""Generate insights and recommendations from usage patterns."""

from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from claude_coach.models import Session, ToolUsage, ErrorEvent, Message, SubagentUsage


@dataclass
class Insight:
    """A single insight or recommendation."""

    category: str  # efficiency, tools, errors, patterns, agents, skills, mcp
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
        insights.extend(self._agent_insights())
        insights.extend(self._skill_insights())
        insights.extend(self._mcp_insights())

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

    def _agent_insights(self) -> list[Insight]:
        """Generate insights about subagent usage patterns."""
        insights = []

        total_sessions = self.db.query(Session).count()
        if total_sessions == 0:
            return insights

        # Count total agent spawns
        total_agents = self.db.query(SubagentUsage).count()

        if total_agents == 0:
            insights.append(Insight(
                category="agents",
                title="No Subagent Usage Detected",
                description=(
                    "You're not using subagents (Task tool). Delegating research, "
                    "exploration, and testing to subagents can speed up complex tasks "
                    "and reduce main context window pressure."
                ),
                severity="suggestion",
                metric_value=0,
                metric_label="Subagent spawns",
            ))
            return insights

        # Agents per session
        agents_per_session = total_agents / total_sessions
        insights.append(Insight(
            category="agents",
            title="Agent Usage Rate",
            description=(
                f"You spawn {agents_per_session:.1f} subagents per session on average "
                f"({total_agents} total across {total_sessions} sessions)."
            ),
            severity="info",
            metric_value=agents_per_session,
            metric_label="Agents per session",
        ))

        # Check for general-purpose overuse
        type_counts = (
            self.db.query(SubagentUsage.subagent_type, func.count(SubagentUsage.id))
            .group_by(SubagentUsage.subagent_type)
            .all()
        )
        type_dict = {t: c for t, c in type_counts}
        general_count = type_dict.get("general-purpose", 0)

        if general_count > total_agents * 0.5 and total_agents > 5:
            insights.append(Insight(
                category="agents",
                title="Consider Specialized Agent Types",
                description=(
                    f"Over 50% of your agents ({general_count}/{total_agents}) are "
                    "'general-purpose'. Specialized types like 'Explore' (for search), "
                    "'Plan' (for architecture), or 'Bash' (for commands) can be faster "
                    "and more token-efficient for specific tasks."
                ),
                severity="suggestion",
                metric_value=general_count / total_agents * 100,
                metric_label="General-purpose (%)",
            ))

        # Check agent token efficiency
        agents_with_tokens = self.db.query(SubagentUsage).filter(
            SubagentUsage.total_tokens.isnot(None)
        ).all()

        if agents_with_tokens:
            avg_tokens = sum(a.total_tokens for a in agents_with_tokens) / len(agents_with_tokens)
            if avg_tokens > 50000:
                insights.append(Insight(
                    category="agents",
                    title="High Token Usage per Agent",
                    description=(
                        f"Your agents average {avg_tokens:,.0f} tokens each. "
                        "Consider using model='haiku' for simple tasks (exploration, "
                        "search) to reduce costs significantly."
                    ),
                    severity="suggestion",
                    metric_value=avg_tokens,
                    metric_label="Avg tokens/agent",
                ))

        return insights

    def _skill_insights(self) -> list[Insight]:
        """Generate insights about skill usage."""
        insights = []

        total_skills = (
            self.db.query(ToolUsage)
            .filter(ToolUsage.category == "skill")
            .count()
        )

        if total_skills == 0:
            insights.append(Insight(
                category="skills",
                title="No Skills Used",
                description=(
                    "You haven't used any Claude Code skills. Skills like "
                    "'brainstorming', 'code-review', and 'writing-plans' provide "
                    "structured workflows that can improve output quality. "
                    "Try /skill in Claude Code to see available skills."
                ),
                severity="suggestion",
                metric_value=0,
                metric_label="Skill invocations",
            ))
        else:
            # Get skill names
            skill_counts = (
                self.db.query(ToolUsage.skill_name, func.count(ToolUsage.id))
                .filter(ToolUsage.category == "skill")
                .group_by(ToolUsage.skill_name)
                .order_by(func.count(ToolUsage.id).desc())
                .all()
            )

            skill_names = [name for name, _ in skill_counts if name]
            top_skill = skill_counts[0] if skill_counts else None

            insights.append(Insight(
                category="skills",
                title=f"Active Skill User ({total_skills} invocations)",
                description=(
                    f"You use {len(skill_names)} different skills. "
                    f"Most used: {top_skill[0]} ({top_skill[1]}x). "
                    "Skills provide structured workflows for common tasks."
                ) if top_skill else f"You've invoked skills {total_skills} times.",
                severity="info",
                metric_value=total_skills,
                metric_label="Total skill invocations",
            ))

        return insights

    def _mcp_insights(self) -> list[Insight]:
        """Generate insights about MCP server usage."""
        insights = []

        # Count MCP tool usage
        mcp_tools = (
            self.db.query(ToolUsage.mcp_server, func.count(ToolUsage.id).label("count"))
            .filter(ToolUsage.category == "mcp")
            .group_by(ToolUsage.mcp_server)
            .order_by(func.count(ToolUsage.id).desc())
            .all()
        )

        total_mcp = sum(count for _, count in mcp_tools)

        if total_mcp == 0:
            insights.append(Insight(
                category="mcp",
                title="No MCP Server Usage",
                description=(
                    "You're not using any MCP (Model Context Protocol) servers. "
                    "MCP servers can extend Claude's capabilities with external tools "
                    "like file systems, databases, browsers, and custom APIs."
                ),
                severity="info",
                metric_value=0,
                metric_label="MCP calls",
            ))
        else:
            server_count = len(mcp_tools)
            top_server = mcp_tools[0] if mcp_tools else None

            insights.append(Insight(
                category="mcp",
                title=f"Using {server_count} MCP Server{'s' if server_count > 1 else ''}",
                description=(
                    f"You have {total_mcp} total MCP tool calls across {server_count} servers. "
                    f"Most active: {top_server[0]} ({top_server[1]} calls)."
                ) if top_server else f"You have {total_mcp} MCP tool calls.",
                severity="info",
                metric_value=total_mcp,
                metric_label="Total MCP calls",
            ))

            # Check for low-usage servers
            low_usage = [name for name, count in mcp_tools if count < 5]
            if low_usage and len(low_usage) < len(mcp_tools):
                insights.append(Insight(
                    category="mcp",
                    title="Underused MCP Servers",
                    description=(
                        f"MCP servers {', '.join(low_usage)} have very few calls. "
                        "Consider if they're still needed, or explore their capabilities more."
                    ),
                    severity="info",
                    metric_value=len(low_usage),
                    metric_label="Underused servers",
                ))

        return insights
