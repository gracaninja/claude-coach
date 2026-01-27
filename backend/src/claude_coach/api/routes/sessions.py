"""Session-related API endpoints."""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from claude_coach.schemas.session import (
    SessionList,
    SessionDetail,
    MessageList,
    Session as SessionSchema,
    Message as MessageSchema,
)
from claude_coach.models import Session, Message
from claude_coach.api.deps import get_db

router = APIRouter()


@router.get("", response_model=SessionList)
async def list_sessions(
    project: Optional[str] = Query(None, description="Filter by project path"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: DBSession = Depends(get_db),
):
    """List all sessions with optional filtering."""
    query = db.query(Session)

    if project:
        query = query.filter(Session.project_path.contains(project))

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
