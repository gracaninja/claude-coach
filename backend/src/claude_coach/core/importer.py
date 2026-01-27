"""Import Claude Code logs into the database."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from claude_coach.models import (
    Session,
    Message,
    ToolUsage,
    ErrorEvent,
    DailyStats,
    ToolStats,
    ErrorStats,
    init_db,
    get_session_factory,
)


class LogImporter:
    """Import Claude Code logs into the database."""

    def __init__(self, claude_dir: Optional[Path] = None, db_path: Optional[Path] = None):
        """Initialize importer."""
        if claude_dir is None:
            claude_dir = Path.home() / ".claude"
        self.claude_dir = claude_dir
        self.projects_dir = claude_dir / "projects"

        # Initialize database
        init_db(db_path)
        self.session_factory = get_session_factory(db_path)

    def import_all(self, force: bool = False) -> dict:
        """Import all sessions from Claude Code logs.

        Args:
            force: If True, re-import sessions even if they exist.

        Returns:
            Dict with import statistics.
        """
        stats = {
            "sessions_imported": 0,
            "sessions_skipped": 0,
            "messages_imported": 0,
            "tool_usages_imported": 0,
            "errors_imported": 0,
        }

        with self.session_factory() as db:
            for project_dir in self._get_project_dirs():
                for session_file in project_dir.glob("*.jsonl"):
                    if session_file.name == "sessions-index.json":
                        continue

                    session_id = session_file.stem

                    # Check if already imported
                    if not force:
                        existing = db.query(Session).filter(
                            Session.session_id == session_id
                        ).first()
                        if existing:
                            stats["sessions_skipped"] += 1
                            continue

                    result = self._import_session(db, session_file, session_id)
                    stats["sessions_imported"] += 1
                    stats["messages_imported"] += result["messages"]
                    stats["tool_usages_imported"] += result["tool_usages"]
                    stats["errors_imported"] += result["errors"]

            # Update aggregated stats
            self._update_daily_stats(db)
            db.commit()

        return stats

    def _get_project_dirs(self) -> list[Path]:
        """Get all project directories."""
        if not self.projects_dir.exists():
            return []
        return [d for d in self.projects_dir.iterdir() if d.is_dir()]

    def _import_session(
        self, db: DBSession, session_file: Path, session_id: str
    ) -> dict:
        """Import a single session."""
        stats = {"messages": 0, "tool_usages": 0, "errors": 0}

        # Parse session file
        messages = []
        tool_usages = []
        errors = []

        total_input = 0
        total_output = 0
        total_cache_read = 0
        total_cache_create = 0
        first_prompt = None
        first_timestamp = None
        last_timestamp = None
        project_path = ""
        git_branch = ""
        message_index = 0
        cumulative_tokens = 0

        with open(session_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type")
                timestamp_str = event.get("timestamp")
                timestamp = self._parse_timestamp(timestamp_str)

                if timestamp:
                    if first_timestamp is None:
                        first_timestamp = timestamp
                    last_timestamp = timestamp

                # Extract project info
                if not project_path and event.get("cwd"):
                    project_path = event.get("cwd", "")
                if not git_branch and event.get("gitBranch"):
                    git_branch = event.get("gitBranch", "")

                if event_type == "user":
                    msg = event.get("message", {})
                    content = msg.get("content", "")

                    if isinstance(content, str):
                        if first_prompt is None and content:
                            first_prompt = content[:500]  # Truncate

                        messages.append(Message(
                            role="user",
                            content=content[:10000],  # Truncate long content
                            timestamp=timestamp,
                            message_index=message_index,
                        ))
                        message_index += 1

                elif event_type == "assistant":
                    msg = event.get("message", {})
                    usage = msg.get("usage", {})

                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    cache_read = usage.get("cache_read_input_tokens", 0)
                    cache_create = usage.get("cache_creation_input_tokens", 0)

                    total_input += input_tokens
                    total_output += output_tokens
                    total_cache_read += cache_read
                    total_cache_create += cache_create
                    cumulative_tokens = input_tokens + cache_read

                    # Extract text content
                    content_parts = msg.get("content", [])
                    text_content = ""
                    for part in content_parts:
                        if part.get("type") == "text":
                            text_content += part.get("text", "")
                        elif part.get("type") == "tool_use":
                            tool_usages.append(ToolUsage(
                                tool_name=part.get("name", "unknown"),
                                tool_use_id=part.get("id"),
                                timestamp=timestamp,
                                input_preview=str(part.get("input", {}))[:500],
                            ))
                            stats["tool_usages"] += 1

                    if text_content:
                        messages.append(Message(
                            role="assistant",
                            content=text_content[:10000],
                            timestamp=timestamp,
                            model=msg.get("model"),
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            cache_read_tokens=cache_read,
                            cache_creation_tokens=cache_create,
                            cumulative_context_tokens=cumulative_tokens,
                            message_index=message_index,
                        ))
                        message_index += 1

                elif event_type == "system" and event.get("subtype") == "api_error":
                    error_data = event.get("error", {}).get("error", {})
                    errors.append(ErrorEvent(
                        error_type=error_data.get("type", "unknown"),
                        error_message=error_data.get("message"),
                        timestamp=timestamp,
                        retry_attempt=event.get("retryAttempt"),
                        retry_in_ms=int(event.get("retryInMs", 0)) if event.get("retryInMs") else None,
                    ))
                    stats["errors"] += 1

        # Calculate duration
        duration_ms = None
        if first_timestamp and last_timestamp:
            duration_ms = int((last_timestamp - first_timestamp).total_seconds() * 1000)

        # Create session
        session = Session(
            session_id=session_id,
            project_path=project_path,
            first_prompt=first_prompt,
            git_branch=git_branch,
            created_at=first_timestamp or datetime.utcnow(),
            modified_at=last_timestamp,
            message_count=len(messages),
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_cache_read_tokens=total_cache_read,
            total_cache_creation_tokens=total_cache_create,
            tool_call_count=len(tool_usages),
            error_count=len(errors),
            duration_ms=duration_ms,
        )

        # Delete existing if force re-import
        db.query(Session).filter(Session.session_id == session_id).delete()

        db.add(session)
        db.flush()  # Get session.id

        # Add messages, tools, errors
        for msg in messages:
            msg.session_id = session.id
            db.add(msg)
            stats["messages"] += 1

        for tool in tool_usages:
            tool.session_id = session.id
            db.add(tool)

        for error in errors:
            error.session_id = session.id
            db.add(error)

        return stats

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO timestamp string."""
        if not timestamp_str:
            return None
        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def _update_daily_stats(self, db: DBSession):
        """Update daily aggregated statistics."""
        # Get all sessions grouped by date
        sessions = db.query(Session).all()

        daily_data = {}
        tool_data = {}
        error_data = {}

        for session in sessions:
            date_key = session.created_at.date()

            # Daily stats
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "session_count": 0,
                    "message_count": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read_tokens": 0,
                    "cache_creation_tokens": 0,
                    "tool_call_count": 0,
                    "error_count": 0,
                }

            daily_data[date_key]["session_count"] += 1
            daily_data[date_key]["message_count"] += session.message_count
            daily_data[date_key]["input_tokens"] += session.total_input_tokens
            daily_data[date_key]["output_tokens"] += session.total_output_tokens
            daily_data[date_key]["cache_read_tokens"] += session.total_cache_read_tokens
            daily_data[date_key]["cache_creation_tokens"] += session.total_cache_creation_tokens
            daily_data[date_key]["tool_call_count"] += session.tool_call_count
            daily_data[date_key]["error_count"] += session.error_count

            # Tool stats
            for tool in session.tool_usages:
                tool_key = (date_key, tool.tool_name)
                if tool_key not in tool_data:
                    tool_data[tool_key] = {"count": 0, "errors": 0, "duration": 0}
                tool_data[tool_key]["count"] += 1
                if tool.is_error:
                    tool_data[tool_key]["errors"] += 1
                if tool.duration_ms:
                    tool_data[tool_key]["duration"] += tool.duration_ms

            # Error stats
            for error in session.errors:
                error_key = (date_key, error.error_type)
                if error_key not in error_data:
                    error_data[error_key] = {"count": 0}
                error_data[error_key]["count"] += 1

        # Clear existing stats and insert new
        db.query(DailyStats).delete()
        db.query(ToolStats).delete()
        db.query(ErrorStats).delete()

        for date_key, data in daily_data.items():
            db.add(DailyStats(date=date_key, project_path="*", **data))

        for (date_key, tool_name), data in tool_data.items():
            db.add(ToolStats(
                date=date_key,
                tool_name=tool_name,
                call_count=data["count"],
                error_count=data["errors"],
                total_duration_ms=data["duration"],
            ))

        for (date_key, error_type), data in error_data.items():
            db.add(ErrorStats(
                date=date_key,
                error_type=error_type,
                count=data["count"],
            ))
