"""Session-related schemas."""

from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    """A single message in a session."""

    role: str  # user, assistant
    content: str
    timestamp: Optional[str] = None
    model: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class Session(BaseModel):
    """Session summary."""

    session_id: str
    project_path: str
    first_prompt: str
    summary: Optional[str] = None
    message_count: int
    created: Optional[str] = None
    modified: Optional[str] = None
    git_branch: Optional[str] = None


class PlanModeStats(BaseModel):
    """Statistics for planning vs execution mode."""

    planning_time_seconds: float = 0.0
    execution_time_seconds: float = 0.0
    planning_tokens: int = 0
    execution_tokens: int = 0
    planning_messages: int = 0
    execution_messages: int = 0
    plan_mode_entries: int = 0  # How many times entered plan mode


class SessionDetail(BaseModel):
    """Detailed session information."""

    session_id: str
    messages: list[Message]
    total_input_tokens: int
    total_output_tokens: int
    total_cache_read_tokens: int
    total_cache_creation_tokens: int
    tool_call_count: int
    error_count: int
    plan_mode_stats: Optional[PlanModeStats] = None


class SessionList(BaseModel):
    """List of sessions response."""

    sessions: list[Session]
    total: int


class MessageList(BaseModel):
    """List of messages response."""

    messages: list[Message]
    total: int
