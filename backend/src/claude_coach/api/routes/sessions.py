"""Session-related API endpoints."""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from claude_coach.schemas.session import (
    SessionList,
    SessionDetail,
    MessageList,
    Session as SessionSchema,
    Message as MessageSchema,
)
from claude_coach.schemas.analytics import (
    SessionTimelineResponse,
    TimelineEvent,
    TimelineSummary,
)
from claude_coach.models import Session, Message, ToolUsage, ErrorEvent, SubagentUsage
from claude_coach.api.deps import get_db

router = APIRouter()


@router.get("/filters")
async def get_filters(db: DBSession = Depends(get_db)):
    """Get unique projects and branches for filtering."""
    projects = (
        db.query(Session.project_path)
        .distinct()
        .order_by(Session.project_path)
        .all()
    )
    branches = (
        db.query(Session.git_branch)
        .filter(Session.git_branch.isnot(None))
        .distinct()
        .order_by(Session.git_branch)
        .all()
    )
    return {
        "projects": [p[0] for p in projects],
        "branches": [b[0] for b in branches],
    }


@router.get("", response_model=SessionList)
async def list_sessions(
    project: Optional[list[str]] = Query(None, description="Filter by project paths"),
    branch: Optional[str] = Query(None, description="Filter by git branch"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: DBSession = Depends(get_db),
):
    """List all sessions with optional filtering."""
    query = db.query(Session)

    if project:
        query = query.filter(Session.project_path.in_(project))
    if branch:
        query = query.filter(Session.git_branch == branch)

    total = query.count()
    sessions = query.order_by(Session.created_at.desc()).offset(offset).limit(limit).all()

    return SessionList(
        sessions=[
            SessionSchema(
                session_id=s.session_id,
                project_path=s.project_path,
                first_prompt=s.first_prompt or "",
                summary=s.summary,
                message_count=s.message_count,
                created=s.created_at.isoformat() if s.created_at else None,
                modified=s.modified_at.isoformat() if s.modified_at else None,
                git_branch=s.git_branch,
            )
            for s in sessions
        ],
        total=total,
    )


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    """Get detailed information about a specific session."""
    session = db.query(Session).filter(Session.session_id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.message_index)
        .all()
    )

    return SessionDetail(
        session_id=session.session_id,
        project_path=session.project_path,
        git_branch=session.git_branch,
        first_prompt=session.first_prompt,
        created=session.created_at.isoformat() if session.created_at else None,
        modified=session.modified_at.isoformat() if session.modified_at else None,
        messages=[
            MessageSchema(
                role=m.role,
                content=m.content or "",
                timestamp=m.timestamp.isoformat() if m.timestamp else None,
                model=m.model,
                input_tokens=m.input_tokens,
                output_tokens=m.output_tokens,
            )
            for m in messages
        ],
        total_input_tokens=session.total_input_tokens,
        total_output_tokens=session.total_output_tokens,
        total_cache_read_tokens=session.total_cache_read_tokens,
        total_cache_creation_tokens=session.total_cache_creation_tokens,
        tool_call_count=session.tool_call_count,
        error_count=session.error_count,
    )


@router.get("/{session_id}/messages", response_model=MessageList)
async def get_session_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: DBSession = Depends(get_db),
):
    """Get messages for a specific session."""
    session = db.query(Session).filter(Session.session_id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    query = db.query(Message).filter(Message.session_id == session.id)
    total = query.count()

    messages = (
        query.order_by(Message.message_index)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return MessageList(
        messages=[
            MessageSchema(
                role=m.role,
                content=m.content or "",
                timestamp=m.timestamp.isoformat() if m.timestamp else None,
                model=m.model,
                input_tokens=m.input_tokens,
                output_tokens=m.output_tokens,
            )
            for m in messages
        ],
        total=total,
    )


@router.get("/{session_id}/timeline", response_model=SessionTimelineResponse)
async def get_session_timeline(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    """Get a chronological timeline of all events in a session.

    Returns messages, tool calls (with category), agent spawns, skill invocations,
    and errors, all merged into a single chronological timeline.
    """
    session = db.query(Session).filter(Session.session_id == session_id).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    events: list[TimelineEvent] = []

    # Collect tool_use_ids for agents to enrich with SubagentUsage data
    subagent_map: dict[str, SubagentUsage] = {}
    subagents = (
        db.query(SubagentUsage)
        .filter(SubagentUsage.session_id == session.id)
        .all()
    )
    for sa in subagents:
        if sa.tool_use_id:
            subagent_map[sa.tool_use_id] = sa

    # Summary counters
    native_count = 0
    mcp_count = 0
    agent_count = 0
    skill_count = 0
    total_tokens = session.total_input_tokens + session.total_output_tokens

    # Add messages
    messages = (
        db.query(Message)
        .filter(Message.session_id == session.id)
        .order_by(Message.message_index)
        .all()
    )
    for m in messages:
        events.append(TimelineEvent(
            type=f"{m.role}_message",
            timestamp=m.timestamp.isoformat() if m.timestamp else None,
            role=m.role,
            content_preview=(m.content[:200] + "...") if m.content and len(m.content) > 200 else m.content,
            model=m.model,
            input_tokens=m.input_tokens,
            output_tokens=m.output_tokens,
        ))

    # Add tool calls
    tool_usages = (
        db.query(ToolUsage)
        .filter(ToolUsage.session_id == session.id)
        .all()
    )
    for t in tool_usages:
        category = t.category or "native"

        if category == "native":
            native_count += 1
        elif category == "mcp":
            mcp_count += 1
        elif category == "agent":
            agent_count += 1
        elif category == "skill":
            skill_count += 1

        event = TimelineEvent(
            type="tool_call" if category in ("native", "mcp") else (
                "agent_spawn" if category == "agent" else "skill_invoke"
            ),
            timestamp=t.timestamp.isoformat() if t.timestamp else None,
            tool_name=t.tool_name,
            category=category,
            mcp_server=t.mcp_server,
            skill_name=t.skill_name,
            subagent_type=t.subagent_type,
        )

        # Enrich agent spawns with completion data
        if category == "agent" and t.tool_use_id and t.tool_use_id in subagent_map:
            sa = subagent_map[t.tool_use_id]
            event.agent_description = sa.description
            event.agent_duration_ms = sa.duration_ms
            event.agent_total_tokens = sa.total_tokens
            event.agent_total_tool_count = sa.total_tool_use_count
            event.agent_status = sa.status

        events.append(event)

    # Add errors
    errors = (
        db.query(ErrorEvent)
        .filter(ErrorEvent.session_id == session.id)
        .all()
    )
    for e in errors:
        events.append(TimelineEvent(
            type="error",
            timestamp=e.timestamp.isoformat() if e.timestamp else None,
            error_type=e.error_type,
            error_message=e.error_message,
        ))

    # Sort all events chronologically
    events.sort(key=lambda e: e.timestamp or "")

    summary = TimelineSummary(
        total_messages=len(messages),
        total_tool_calls=len(tool_usages),
        native_tool_calls=native_count,
        mcp_tool_calls=mcp_count,
        agent_spawns=agent_count,
        skill_invocations=skill_count,
        errors=len(errors),
        total_tokens=total_tokens,
        duration_ms=session.duration_ms,
    )

    return SessionTimelineResponse(
        session_id=session_id,
        events=events,
        summary=summary,
    )
