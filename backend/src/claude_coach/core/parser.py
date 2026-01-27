"""Log parser for Claude Code session logs."""

import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from claude_coach.schemas.session import Session, SessionDetail, Message, PlanModeStats


class LogParser:
    """Parse Claude Code log files."""

    def __init__(self, claude_dir: Optional[Path] = None):
        """Initialize parser with Claude config directory."""
        if claude_dir is None:
            claude_dir = Path.home() / ".claude"
        self.claude_dir = claude_dir
        self.projects_dir = claude_dir / "projects"

    def _get_project_dirs(self) -> list[Path]:
        """Get all project directories."""
        if not self.projects_dir.exists():
            return []
        return [d for d in self.projects_dir.iterdir() if d.is_dir()]

    def _parse_sessions_index(self, project_dir: Path) -> list[dict]:
        """Parse sessions-index.json for a project."""
        index_file = project_dir / "sessions-index.json"
        if not index_file.exists():
            return []

        try:
            with open(index_file) as f:
                data = json.load(f)
                return data.get("entries", [])
        except (json.JSONDecodeError, IOError):
            return []

    def list_sessions(
        self,
        project: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Session]:
        """List all sessions, optionally filtered by project."""
        sessions = []

        for project_dir in self._get_project_dirs():
            if project and project not in str(project_dir):
                continue

            for entry in self._parse_sessions_index(project_dir):
                sessions.append(Session(
                    session_id=entry.get("sessionId", ""),
                    project_path=entry.get("projectPath", ""),
                    first_prompt=entry.get("firstPrompt", ""),
                    summary=entry.get("summary"),
                    message_count=entry.get("messageCount", 0),
                    created=entry.get("created"),
                    modified=entry.get("modified"),
                    git_branch=entry.get("gitBranch"),
                ))

        # Sort by modified date, newest first
        sessions.sort(key=lambda s: s.modified or "", reverse=True)

        return sessions[offset:offset + limit]

    def get_session(self, session_id: str) -> Optional[SessionDetail]:
        """Get detailed session information."""
        for project_dir in self._get_project_dirs():
            session_file = project_dir / f"{session_id}.jsonl"
            if session_file.exists():
                return self._parse_session_file(session_file, session_id)
        return None

    def _parse_timestamp(self, ts: Optional[str]) -> Optional[datetime]:
        """Parse ISO timestamp string to datetime."""
        if not ts:
            return None
        try:
            # Handle various ISO formats
            ts = ts.replace("Z", "+00:00")
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None

    def _parse_session_file(self, session_file: Path, session_id: str) -> SessionDetail:
        """Parse a session JSONL file."""
        messages = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_read = 0
        total_cache_create = 0
        tool_calls = []
        errors = []

        # Plan mode tracking
        in_plan_mode = False
        plan_mode_start: Optional[datetime] = None
        plan_mode_entries = 0
        planning_time_seconds = 0.0
        execution_time_seconds = 0.0
        planning_tokens = 0
        execution_tokens = 0
        planning_messages = 0
        execution_messages = 0
        last_timestamp: Optional[datetime] = None

        with open(session_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    event_type = event.get("type")
                    timestamp = self._parse_timestamp(event.get("timestamp"))

                    if event_type == "user":
                        msg = event.get("message", {})
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            messages.append(Message(
                                role="user",
                                content=content,
                                timestamp=event.get("timestamp"),
                            ))
                            # Count messages by mode
                            if in_plan_mode:
                                planning_messages += 1
                            else:
                                execution_messages += 1

                    elif event_type == "assistant":
                        msg = event.get("message", {})
                        usage = msg.get("usage", {})

                        msg_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                        total_input_tokens += usage.get("input_tokens", 0)
                        total_output_tokens += usage.get("output_tokens", 0)
                        total_cache_read += usage.get("cache_read_input_tokens", 0)
                        total_cache_create += usage.get("cache_creation_input_tokens", 0)

                        # Track tokens by mode
                        if in_plan_mode:
                            planning_tokens += msg_tokens
                            planning_messages += 1
                        else:
                            execution_tokens += msg_tokens
                            execution_messages += 1

                        content_parts = msg.get("content", [])
                        text_content = ""
                        for part in content_parts:
                            if part.get("type") == "text":
                                text_content += part.get("text", "")
                            elif part.get("type") == "tool_use":
                                tool_name = part.get("name", "")
                                tool_calls.append({
                                    "name": tool_name,
                                    "timestamp": event.get("timestamp"),
                                })

                                # Detect plan mode transitions
                                if tool_name == "EnterPlanMode":
                                    if not in_plan_mode:
                                        in_plan_mode = True
                                        plan_mode_start = timestamp
                                        plan_mode_entries += 1
                                        # Add execution time from last timestamp
                                        if last_timestamp and timestamp:
                                            execution_time_seconds += (timestamp - last_timestamp).total_seconds()

                                elif tool_name == "ExitPlanMode":
                                    if in_plan_mode and plan_mode_start and timestamp:
                                        planning_time_seconds += (timestamp - plan_mode_start).total_seconds()
                                        in_plan_mode = False
                                        plan_mode_start = None

                        if text_content:
                            messages.append(Message(
                                role="assistant",
                                content=text_content,
                                timestamp=event.get("timestamp"),
                                model=msg.get("model"),
                                input_tokens=usage.get("input_tokens"),
                                output_tokens=usage.get("output_tokens"),
                            ))

                    elif event_type == "system" and event.get("subtype") == "api_error":
                        errors.append({
                            "error": event.get("error", {}),
                            "timestamp": event.get("timestamp"),
                        })

                    # Track time between messages for execution mode
                    if timestamp:
                        if last_timestamp and not in_plan_mode:
                            execution_time_seconds += (timestamp - last_timestamp).total_seconds()
                        last_timestamp = timestamp

                except json.JSONDecodeError:
                    continue

        # Create plan mode stats
        plan_mode_stats = PlanModeStats(
            planning_time_seconds=planning_time_seconds,
            execution_time_seconds=execution_time_seconds,
            planning_tokens=planning_tokens,
            execution_tokens=execution_tokens,
            planning_messages=planning_messages,
            execution_messages=execution_messages,
            plan_mode_entries=plan_mode_entries,
        )

        return SessionDetail(
            session_id=session_id,
            messages=messages,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            total_cache_read_tokens=total_cache_read,
            total_cache_creation_tokens=total_cache_create,
            tool_call_count=len(tool_calls),
            error_count=len(errors),
            plan_mode_stats=plan_mode_stats,
        )

    def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> Optional[list[Message]]:
        """Get messages for a session."""
        session = self.get_session(session_id)
        if session is None:
            return None
        return session.messages[offset:offset + limit]
