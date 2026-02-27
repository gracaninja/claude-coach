"""Analytics-related schemas."""

from pydantic import BaseModel
from typing import Optional


class TokenDataPoint(BaseModel):
    """Token usage for a single day."""

    date: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int


class TokenUsageResponse(BaseModel):
    """Token usage analytics response."""

    data: list[TokenDataPoint]
    total_input_tokens: int
    total_output_tokens: int


class ToolDataPoint(BaseModel):
    """Tool usage count."""

    tool_name: str
    count: int


class ToolUsageResponse(BaseModel):
    """Tool usage analytics response."""

    data: list[ToolDataPoint]
    total_tool_calls: int


class ErrorDataPoint(BaseModel):
    """Error type count."""

    error_type: str
    count: int


class ErrorStatsResponse(BaseModel):
    """Error statistics response."""

    data: list[ErrorDataPoint]
    total_errors: int


class ContextDataPoint(BaseModel):
    """Context size at a point in conversation."""

    message_index: int
    context_tokens: int
    timestamp: Optional[str] = None


class ContextGrowthResponse(BaseModel):
    """Context growth over a session."""

    session_id: str
    data: list[ContextDataPoint]


class PlanModeSessionStats(BaseModel):
    """Plan mode stats for a single session."""

    session_id: str
    planning_time_seconds: float
    execution_time_seconds: float
    planning_tokens: int
    execution_tokens: int
    planning_messages: int
    execution_messages: int
    plan_mode_entries: int
    planning_percentage: float  # Percentage of time in planning


class PlanModeAggregateStats(BaseModel):
    """Aggregated plan mode statistics."""

    total_planning_time_seconds: float
    total_execution_time_seconds: float
    total_planning_tokens: int
    total_execution_tokens: int
    total_planning_messages: int
    total_execution_messages: int
    total_plan_mode_entries: int
    avg_planning_percentage: float
    sessions_with_planning: int
    total_sessions: int


class PlanModeResponse(BaseModel):
    """Plan mode analytics response."""

    aggregate: PlanModeAggregateStats
    sessions: list[PlanModeSessionStats]


# Error Analysis schemas

class ToolErrorDetail(BaseModel):
    """Detailed information about a single tool error."""

    tool_name: str
    error_message: str
    error_category: str
    timestamp: Optional[str] = None
    session_id: str
    project_path: Optional[str] = None
    tool_input: Optional[dict] = None


class SubcategoryDetail(BaseModel):
    """Detail for a subcategory."""

    count: int
    example: Optional[str] = None


class ErrorCategorySummary(BaseModel):
    """Summary of errors in a category with suggestions."""

    category: str
    count: int
    description: str
    suggestion: str
    example_errors: list[str]
    subcategories: Optional[dict[str, SubcategoryDetail]] = None


class ActionableIssue(BaseModel):
    """An actionable issue that can be fixed."""

    issue_type: str
    description: str
    fix: str
    count: int
    projects: list[str]
    examples: list[str]


class ToolErrorSummary(BaseModel):
    """Summary of errors by tool."""

    tool_name: str
    total_errors: int
    by_category: dict[str, int]


class ErrorAnalysisResponse(BaseModel):
    """Comprehensive error analysis response."""

    total_errors: int
    by_category: list[ErrorCategorySummary]
    by_tool: list[ToolErrorSummary]
    recent_errors: list[ToolErrorDetail]
    actionable_issues: list[ActionableIssue]


class DailyErrorSummary(BaseModel):
    """Error summary for a single day."""

    date: str
    total: int
    by_category: dict[str, int]


class TimeframeErrorsResponse(BaseModel):
    """Errors for a specific timeframe."""

    days: int
    total_errors: int
    daily: list[DailyErrorSummary]
    actionable_issues: list[ActionableIssue]


class SessionErrorsResponse(BaseModel):
    """Errors for a specific session."""

    session_id: str
    project_path: Optional[str] = None
    total_errors: int
    by_category: list[ErrorCategorySummary]
    errors: list[ToolErrorDetail]


# ========== Timeline schemas ==========


class TimelineEvent(BaseModel):
    """A single event in a session timeline."""

    type: str  # user_message, assistant_message, tool_call, agent_spawn, skill_invoke, error
    timestamp: Optional[str] = None

    # For messages
    role: Optional[str] = None
    content_preview: Optional[str] = None
    model: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None

    # For tool calls
    tool_name: Optional[str] = None
    category: Optional[str] = None  # native, mcp, skill, agent
    mcp_server: Optional[str] = None

    # For agents
    subagent_type: Optional[str] = None
    agent_description: Optional[str] = None
    agent_duration_ms: Optional[int] = None
    agent_total_tokens: Optional[int] = None
    agent_total_tool_count: Optional[int] = None
    agent_status: Optional[str] = None

    # For skills
    skill_name: Optional[str] = None

    # For errors
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class SessionTimelineResponse(BaseModel):
    """Session timeline with all events."""

    session_id: str
    events: list[TimelineEvent]
    summary: "TimelineSummary"


class TimelineSummary(BaseModel):
    """Summary stats for a session timeline."""

    total_messages: int = 0
    total_tool_calls: int = 0
    native_tool_calls: int = 0
    mcp_tool_calls: int = 0
    agent_spawns: int = 0
    skill_invocations: int = 0
    errors: int = 0
    total_tokens: int = 0
    duration_ms: Optional[int] = None


# ========== Agent analytics schemas ==========


class AgentTypeStats(BaseModel):
    """Stats for a single agent type."""

    subagent_type: str
    count: int
    total_tokens: int = 0
    total_duration_ms: int = 0
    avg_tokens: float = 0
    avg_duration_ms: float = 0
    total_tool_use_count: int = 0


class AgentDailyCount(BaseModel):
    """Agent spawn counts for a day."""

    date: str
    count: int


class AgentAnalyticsResponse(BaseModel):
    """Agent usage analytics."""

    total_spawns: int
    by_type: list[AgentTypeStats]
    daily_trend: list[AgentDailyCount]


# ========== Skill analytics schemas ==========


class SkillStats(BaseModel):
    """Stats for a single skill."""

    skill_name: str
    count: int


class SkillDailyCount(BaseModel):
    """Skill invocation counts for a day."""

    date: str
    count: int


class SkillAnalyticsResponse(BaseModel):
    """Skill usage analytics."""

    total_invocations: int
    by_skill: list[SkillStats]
    daily_trend: list[SkillDailyCount]


# ========== MCP analytics schemas ==========


class McpServerStats(BaseModel):
    """Stats for a single MCP server."""

    server_name: str
    total_calls: int
    tools: list["McpToolStats"]


class McpToolStats(BaseModel):
    """Stats for a single MCP tool."""

    tool_name: str
    count: int


class McpAnalyticsResponse(BaseModel):
    """MCP usage analytics."""

    total_calls: int
    by_server: list[McpServerStats]
