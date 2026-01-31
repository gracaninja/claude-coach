"""Analytics API endpoints."""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from claude_coach.schemas.analytics import (
    TokenUsageResponse,
    TokenDataPoint,
    ToolUsageResponse,
    ToolDataPoint,
    ErrorStatsResponse,
    ErrorDataPoint,
    ContextGrowthResponse,
    ContextDataPoint,
    PlanModeResponse,
    PlanModeAggregateStats,
    PlanModeSessionStats,
    ErrorAnalysisResponse,
    ErrorCategorySummary,
    ToolErrorSummary,
    ToolErrorDetail,
    SessionErrorsResponse,
    ActionableIssue,
    TimeframeErrorsResponse,
    DailyErrorSummary,
    SubcategoryDetail,
)
from claude_coach.models import (
    Session,
    Message,
    DailyStats,
    ToolStats,
    ErrorStats,
    ToolUsage,
    ErrorEvent,
)
from claude_coach.api.deps import get_db
from claude_coach.core.parser import LogParser
from claude_coach.core.error_analyzer import ErrorAnalyzer

router = APIRouter()


@router.get("/tokens", response_model=TokenUsageResponse)
async def get_token_usage(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    session_id: Optional[str] = Query(None),
    project: Optional[list[str]] = Query(None, description="Filter by project paths"),
    db: DBSession = Depends(get_db),
):
    """Get token usage statistics."""
    if project:
        # When filtering by project, aggregate from sessions directly
        from sqlalchemy import cast, Date
        query = db.query(
            cast(Session.created_at, Date).label("date"),
            func.sum(Session.total_input_tokens).label("input_tokens"),
            func.sum(Session.total_output_tokens).label("output_tokens"),
            func.sum(Session.total_cache_read_tokens).label("cache_read_tokens"),
            func.sum(Session.total_cache_creation_tokens).label("cache_creation_tokens"),
        ).filter(Session.project_path.in_(project))

        if start_date:
            query = query.filter(cast(Session.created_at, Date) >= start_date)
        if end_date:
            query = query.filter(cast(Session.created_at, Date) <= end_date)

        stats = query.group_by(cast(Session.created_at, Date)).order_by(cast(Session.created_at, Date)).all()

        data_points = [
            TokenDataPoint(
                date=str(s.date),
                input_tokens=s.input_tokens or 0,
                output_tokens=s.output_tokens or 0,
                cache_read_tokens=s.cache_read_tokens or 0,
                cache_creation_tokens=s.cache_creation_tokens or 0,
            )
            for s in stats
        ]
    else:
        query = db.query(DailyStats)

        if start_date:
            query = query.filter(DailyStats.date >= start_date)
        if end_date:
            query = query.filter(DailyStats.date <= end_date)

        stats = query.order_by(DailyStats.date).all()

        data_points = [
            TokenDataPoint(
                date=str(s.date),
                input_tokens=s.input_tokens,
                output_tokens=s.output_tokens,
                cache_read_tokens=s.cache_read_tokens,
                cache_creation_tokens=s.cache_creation_tokens,
            )
            for s in stats
        ]

    total_input = sum(d.input_tokens for d in data_points)
    total_output = sum(d.output_tokens for d in data_points)

    return TokenUsageResponse(
        data=data_points,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
    )


@router.get("/tools", response_model=ToolUsageResponse)
async def get_tool_usage(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    project: Optional[list[str]] = Query(None, description="Filter by project paths"),
    db: DBSession = Depends(get_db),
):
    """Get tool usage statistics."""
    # Aggregate tool stats
    query = (
        db.query(
            ToolUsage.tool_name,
            func.count(ToolUsage.id).label("count"),
        )
    )

    if project:
        query = query.join(Session, ToolUsage.session_id == Session.id).filter(
            Session.project_path.in_(project)
        )

    query = query.group_by(ToolUsage.tool_name).order_by(func.count(ToolUsage.id).desc())

    results = query.all()

    data_points = [
        ToolDataPoint(tool_name=name, count=count)
        for name, count in results
    ]

    return ToolUsageResponse(
        data=data_points,
        total_tool_calls=sum(d.count for d in data_points),
    )


@router.get("/errors", response_model=ErrorStatsResponse)
async def get_error_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    project: Optional[list[str]] = Query(None, description="Filter by project paths"),
    db: DBSession = Depends(get_db),
):
    """Get error statistics."""
    if project:
        # When filtering by project, aggregate from ErrorEvent directly
        query = (
            db.query(
                ErrorEvent.error_type,
                func.count(ErrorEvent.id).label("total"),
            )
            .join(Session, ErrorEvent.session_id == Session.id)
            .filter(Session.project_path.in_(project))
        )
        query = query.group_by(ErrorEvent.error_type).order_by(func.count(ErrorEvent.id).desc())
        results = query.all()
    else:
        query = db.query(ErrorStats)

        if start_date:
            query = query.filter(ErrorStats.date >= start_date)
        if end_date:
            query = query.filter(ErrorStats.date <= end_date)

        # Aggregate by error type
        results = (
            db.query(
                ErrorStats.error_type,
                func.sum(ErrorStats.count).label("total"),
            )
            .group_by(ErrorStats.error_type)
            .order_by(func.sum(ErrorStats.count).desc())
            .all()
        )

    data_points = [
        ErrorDataPoint(error_type=err_type, count=int(total))
        for err_type, total in results
    ]

    return ErrorStatsResponse(
        data=data_points,
        total_errors=sum(d.count for d in data_points),
    )


@router.get("/context-growth/{session_id}", response_model=ContextGrowthResponse)
async def get_context_growth(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    """Get context size evolution for a session."""
    session = db.query(Session).filter(Session.session_id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .filter(Message.role == "assistant")
        .filter(Message.cumulative_context_tokens.isnot(None))
        .order_by(Message.message_index)
        .all()
    )

    data_points = [
        ContextDataPoint(
            message_index=m.message_index,
            context_tokens=m.cumulative_context_tokens or 0,
            timestamp=m.timestamp.isoformat() if m.timestamp else None,
        )
        for m in messages
    ]

    return ContextGrowthResponse(
        session_id=session_id,
        data=data_points,
    )


@router.get("/plan-mode", response_model=PlanModeResponse)
async def get_plan_mode_stats(
    db: DBSession = Depends(get_db),
):
    """Get planning vs execution mode statistics.

    Parses session logs to detect plan mode from Write to ~/.claude/plans/
    and ExitPlanMode tool calls, calculating time and tokens spent in each mode.
    """
    parser = LogParser()
    sessions = parser.list_sessions(limit=2000)

    session_stats: list[PlanModeSessionStats] = []
    total_planning_time = 0.0
    total_execution_time = 0.0
    total_planning_tokens = 0
    total_execution_tokens = 0
    total_planning_messages = 0
    total_execution_messages = 0
    total_plan_entries = 0
    sessions_with_planning = 0

    for session in sessions:
        detail = parser.get_session(session.session_id)
        if not detail or not detail.plan_mode_stats:
            continue

        stats = detail.plan_mode_stats
        total_time = stats.planning_time_seconds + stats.execution_time_seconds
        planning_pct = (
            (stats.planning_time_seconds / total_time * 100)
            if total_time > 0
            else 0.0
        )

        session_stats.append(
            PlanModeSessionStats(
                session_id=session.session_id,
                planning_time_seconds=stats.planning_time_seconds,
                execution_time_seconds=stats.execution_time_seconds,
                planning_tokens=stats.planning_tokens,
                execution_tokens=stats.execution_tokens,
                planning_messages=stats.planning_messages,
                execution_messages=stats.execution_messages,
                plan_mode_entries=stats.plan_mode_entries,
                planning_percentage=planning_pct,
            )
        )

        total_planning_time += stats.planning_time_seconds
        total_execution_time += stats.execution_time_seconds
        total_planning_tokens += stats.planning_tokens
        total_execution_tokens += stats.execution_tokens
        total_planning_messages += stats.planning_messages
        total_execution_messages += stats.execution_messages
        total_plan_entries += stats.plan_mode_entries

        if stats.plan_mode_entries > 0:
            sessions_with_planning += 1

    total_time_all = total_planning_time + total_execution_time
    avg_planning_pct = (
        (total_planning_time / total_time_all * 100)
        if total_time_all > 0
        else 0.0
    )

    aggregate = PlanModeAggregateStats(
        total_planning_time_seconds=total_planning_time,
        total_execution_time_seconds=total_execution_time,
        total_planning_tokens=total_planning_tokens,
        total_execution_tokens=total_execution_tokens,
        total_planning_messages=total_planning_messages,
        total_execution_messages=total_execution_messages,
        total_plan_mode_entries=total_plan_entries,
        avg_planning_percentage=avg_planning_pct,
        sessions_with_planning=sessions_with_planning,
        total_sessions=len(session_stats),
    )

    return PlanModeResponse(
        aggregate=aggregate,
        sessions=session_stats,
    )


@router.get("/error-analysis", response_model=ErrorAnalysisResponse)
async def get_error_analysis(
    project: Optional[str] = Query(None, description="Filter by project path substring"),
    limit: int = Query(500, description="Maximum number of errors to analyze"),
):
    """Get comprehensive error analysis with suggestions.

    Analyzes tool errors from session logs, categorizes them,
    and provides actionable suggestions for reducing errors.
    """
    analyzer = ErrorAnalyzer()
    errors = analyzer.get_project_errors(project_filter=project, limit=limit)
    analysis = analyzer.analyze_errors(errors)

    # Convert subcategories to proper schema
    categories = []
    for cat in analysis["by_category"]:
        subcats = None
        if cat.get("subcategories"):
            subcats = {
                k: SubcategoryDetail(count=v["count"], example=v.get("example"))
                for k, v in cat["subcategories"].items()
            }
        categories.append(ErrorCategorySummary(
            category=cat["category"],
            count=cat["count"],
            description=cat["description"],
            suggestion=cat["suggestion"],
            example_errors=cat["example_errors"],
            subcategories=subcats,
        ))

    return ErrorAnalysisResponse(
        total_errors=analysis["total_errors"],
        by_category=categories,
        by_tool=[ToolErrorSummary(**tool) for tool in analysis["by_tool"]],
        recent_errors=[
            ToolErrorDetail(
                tool_name=e.tool_name,
                error_message=e.error_message,
                error_category=e.error_category,
                timestamp=e.timestamp,
                session_id=e.session_id,
                project_path=e.project_path,
                tool_input=e.tool_input,
            )
            for e in errors[:50]  # Return 50 most recent errors
        ],
        actionable_issues=[
            ActionableIssue(**issue) for issue in analysis["actionable_issues"]
        ],
    )


@router.get("/error-analysis/timeframe", response_model=TimeframeErrorsResponse)
async def get_errors_by_timeframe(
    days: int = Query(7, description="Number of days to look back"),
    project: Optional[str] = Query(None, description="Filter by project path substring"),
):
    """Get error analysis for a specific timeframe.

    Returns daily error counts and actionable issues for the last N days.
    Useful for tracking error trends and identifying recurring issues.
    """
    analyzer = ErrorAnalyzer()
    result = analyzer.get_errors_by_timeframe(days=days, project_filter=project)

    return TimeframeErrorsResponse(
        days=result["days"],
        total_errors=result["total_errors"],
        daily=[DailyErrorSummary(**d) for d in result["daily"]],
        actionable_issues=[ActionableIssue(**i) for i in result["actionable_issues"]],
    )


@router.get("/error-analysis/session/{session_id}", response_model=SessionErrorsResponse)
async def get_session_errors(
    session_id: str,
):
    """Get detailed error analysis for a specific session.

    Returns all tool errors for the session with categorization
    and suggestions for improvement.
    """
    analyzer = ErrorAnalyzer()
    errors = analyzer.get_session_errors(session_id)

    if errors is None:
        raise HTTPException(status_code=404, detail="Session not found")

    analysis = analyzer.analyze_errors(errors)

    # Get project path from first error or session
    project_path = errors[0].project_path if errors else None

    return SessionErrorsResponse(
        session_id=session_id,
        project_path=project_path,
        total_errors=len(errors),
        by_category=[
            ErrorCategorySummary(**cat) for cat in analysis["by_category"]
        ],
        errors=[
            ToolErrorDetail(
                tool_name=e.tool_name,
                error_message=e.error_message,
                error_category=e.error_category,
                timestamp=e.timestamp,
                session_id=e.session_id,
                project_path=e.project_path,
                tool_input=e.tool_input,
            )
            for e in errors
        ],
    )
