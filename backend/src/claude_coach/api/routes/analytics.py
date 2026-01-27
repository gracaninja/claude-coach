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
)
from claude_coach.models import (
    Session,
    Message,
    DailyStats,
    ToolStats,
    ErrorStats,
    ToolUsage,
)
from claude_coach.api.deps import get_db
from claude_coach.core.parser import LogParser

router = APIRouter()


@router.get("/tokens", response_model=TokenUsageResponse)
async def get_token_usage(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    session_id: Optional[str] = Query(None),
    db: DBSession = Depends(get_db),
):
    """Get token usage statistics."""
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
    db: DBSession = Depends(get_db),
):
    """Get tool usage statistics."""
    # Aggregate tool stats
    query = (
        db.query(
            ToolUsage.tool_name,
            func.count(ToolUsage.id).label("count"),
        )
        .group_by(ToolUsage.tool_name)
        .order_by(func.count(ToolUsage.id).desc())
    )

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
    db: DBSession = Depends(get_db),
):
    """Get error statistics."""
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

    Parses session logs to detect EnterPlanMode/ExitPlanMode tool calls
    and calculates time and tokens spent in each mode.
    """
    parser = LogParser()
    sessions = parser.list_sessions(limit=100)

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
