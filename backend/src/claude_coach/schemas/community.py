"""Community and sharing schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import date


class AnonymizedMetrics(BaseModel):
    """Anonymized metrics that can be safely shared."""

    # Time period
    period_start: date
    period_end: date

    # Session stats (no identifying info)
    total_sessions: int
    total_messages: int
    avg_messages_per_session: float
    avg_session_duration_minutes: Optional[float] = None

    # Token stats
    total_input_tokens: int
    total_output_tokens: int
    total_cache_read_tokens: int
    avg_tokens_per_session: float

    # Tool usage (counts only, no content)
    tool_usage: dict[str, int]  # tool_name -> count
    top_tools: list[str]  # Top 10 tools

    # Error stats (types only)
    total_errors: int
    error_types: dict[str, int]  # error_type -> count

    # Efficiency metrics
    cache_hit_rate: float  # cache_read / (cache_read + cache_create)
    avg_tools_per_session: float


class CommunityBenchmark(BaseModel):
    """Community benchmark data for comparison."""

    # Sample info
    total_users: int
    data_period_days: int

    # Averages
    avg_sessions_per_day: float
    avg_messages_per_session: float
    avg_tokens_per_session: float
    avg_tools_per_session: float

    # Percentiles for comparison
    tokens_p50: int
    tokens_p90: int
    tools_p50: int
    tools_p90: int

    # Common tools across community
    most_used_tools: list[str]

    # Error rates
    avg_error_rate: float  # errors per 100 sessions


class UserComparison(BaseModel):
    """Compare user stats to community benchmarks."""

    # User stats
    user_sessions_per_day: float
    user_messages_per_session: float
    user_tokens_per_session: float
    user_tools_per_session: float
    user_error_rate: float
    user_cache_hit_rate: float

    # Community benchmarks
    benchmark: CommunityBenchmark

    # Percentile rankings
    sessions_percentile: int  # 0-100, where user ranks
    tokens_percentile: int
    efficiency_percentile: int  # Based on cache hit rate

    # Insights
    insights: list[str]


class ExportRequest(BaseModel):
    """Request to export anonymized metrics."""

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    include_tool_details: bool = True
    include_error_details: bool = True


class ContributeRequest(BaseModel):
    """Request to contribute anonymized metrics to community."""

    metrics: AnonymizedMetrics
    user_id: Optional[str] = None  # Optional anonymous user ID for tracking
