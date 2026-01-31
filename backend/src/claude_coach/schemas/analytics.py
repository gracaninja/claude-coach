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
