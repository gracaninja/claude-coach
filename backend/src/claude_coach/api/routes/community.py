"""Community and sharing API endpoints."""

from fastapi import APIRouter, Query, Depends, Response
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session as DBSession

from claude_coach.schemas.community import (
    AnonymizedMetrics,
    CommunityBenchmark,
    UserComparison,
    ExportRequest,
)
from claude_coach.core.anonymizer import MetricsAnonymizer
from claude_coach.core.insights import InsightsEngine, Insight
from claude_coach.api.deps import get_db

router = APIRouter()

# Static community benchmarks (would be dynamic in production)
COMMUNITY_BENCHMARK = CommunityBenchmark(
    total_users=1000,
    data_period_days=30,
    avg_sessions_per_day=3.2,
    avg_messages_per_session=15.5,
    avg_tokens_per_session=25000,
    avg_tools_per_session=8.3,
    tokens_p50=18000,
    tokens_p90=65000,
    tools_p50=6,
    tools_p90=20,
    most_used_tools=["Bash", "Read", "Edit", "Grep", "Write", "Glob", "Task", "TodoWrite"],
    avg_error_rate=0.15,
)


@router.get("/export", response_model=AnonymizedMetrics)
async def export_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: DBSession = Depends(get_db),
):
    """Export anonymized metrics for sharing or backup.

    This endpoint generates metrics that contain NO identifying information:
    - No prompts or message content
    - No file paths or code
    - Only aggregate counts and statistics
    """
    anonymizer = MetricsAnonymizer(db)
    return anonymizer.generate_anonymized_metrics(start_date, end_date)


@router.get("/export/json")
async def export_metrics_json(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: DBSession = Depends(get_db),
):
    """Export anonymized metrics as downloadable JSON file."""
    anonymizer = MetricsAnonymizer(db)
    json_content = anonymizer.export_to_json(start_date, end_date)

    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=claude-coach-metrics.json"
        },
    )


@router.get("/benchmark", response_model=CommunityBenchmark)
async def get_community_benchmark():
    """Get community benchmark data for comparison.

    Note: In a production deployment with opt-in sharing, this would
    be computed from aggregated community data.
    """
    return COMMUNITY_BENCHMARK


@router.get("/compare", response_model=UserComparison)
async def compare_to_community(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    db: DBSession = Depends(get_db),
):
    """Compare your usage to community benchmarks."""
    from datetime import timedelta

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    anonymizer = MetricsAnonymizer(db)
    user_metrics = anonymizer.generate_anonymized_metrics(start_date, end_date)

    # Calculate user stats
    user_sessions_per_day = user_metrics.total_sessions / days if days > 0 else 0
    user_error_rate = (
        user_metrics.total_errors / user_metrics.total_sessions
        if user_metrics.total_sessions > 0
        else 0
    )

    # Calculate percentiles (simplified)
    def percentile_rank(user_val: float, p50: float, p90: float) -> int:
        if user_val <= p50:
            return int((user_val / p50) * 50) if p50 > 0 else 50
        elif user_val <= p90:
            return 50 + int(((user_val - p50) / (p90 - p50)) * 40) if p90 > p50 else 90
        else:
            return min(99, 90 + int(((user_val - p90) / p90) * 10))

    tokens_percentile = percentile_rank(
        user_metrics.avg_tokens_per_session,
        COMMUNITY_BENCHMARK.tokens_p50,
        COMMUNITY_BENCHMARK.tokens_p90,
    )
    tools_percentile = percentile_rank(
        user_metrics.avg_tools_per_session,
        COMMUNITY_BENCHMARK.tools_p50,
        COMMUNITY_BENCHMARK.tools_p90,
    )

    # Cache efficiency percentile (higher is better)
    efficiency_percentile = int(user_metrics.cache_hit_rate * 100)

    # Generate insights
    insights = []

    if user_sessions_per_day > COMMUNITY_BENCHMARK.avg_sessions_per_day * 1.5:
        insights.append("You're a power user! Your session frequency is above average.")
    elif user_sessions_per_day < COMMUNITY_BENCHMARK.avg_sessions_per_day * 0.5:
        insights.append("You use Claude Code less frequently than average.")

    if user_metrics.cache_hit_rate > 0.7:
        insights.append("Great cache efficiency! You're effectively reusing context.")
    elif user_metrics.cache_hit_rate < 0.4:
        insights.append("Try keeping related work in longer sessions to improve caching.")

    if tokens_percentile > 80:
        insights.append("You use more tokens than most users - consider if all context is needed.")

    if user_error_rate > COMMUNITY_BENCHMARK.avg_error_rate * 2:
        insights.append("You're experiencing more errors than average.")

    return UserComparison(
        user_sessions_per_day=user_sessions_per_day,
        user_messages_per_session=user_metrics.avg_messages_per_session,
        user_tokens_per_session=user_metrics.avg_tokens_per_session,
        user_tools_per_session=user_metrics.avg_tools_per_session,
        user_error_rate=user_error_rate,
        user_cache_hit_rate=user_metrics.cache_hit_rate,
        benchmark=COMMUNITY_BENCHMARK,
        sessions_percentile=percentile_rank(
            user_sessions_per_day,
            COMMUNITY_BENCHMARK.avg_sessions_per_day * 0.5,
            COMMUNITY_BENCHMARK.avg_sessions_per_day * 2,
        ),
        tokens_percentile=tokens_percentile,
        efficiency_percentile=efficiency_percentile,
        insights=insights,
    )


@router.get("/insights", response_model=list[dict])
async def get_insights(
    db: DBSession = Depends(get_db),
):
    """Get personalized insights and recommendations based on your usage."""
    engine = InsightsEngine(db)
    insights = engine.generate_all_insights()

    return [
        {
            "category": i.category,
            "title": i.title,
            "description": i.description,
            "severity": i.severity,
            "metric_value": i.metric_value,
            "metric_label": i.metric_label,
        }
        for i in insights
    ]
