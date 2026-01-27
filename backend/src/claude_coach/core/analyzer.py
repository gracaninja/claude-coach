"""Analytics engine for Claude Code logs."""

import json
from pathlib import Path
from typing import Optional
from datetime import date, datetime
from collections import defaultdict

from claude_coach.schemas.analytics import (
    TokenUsageResponse,
    TokenDataPoint,
    ToolUsageResponse,
    ToolDataPoint,
    ErrorStatsResponse,
    ErrorDataPoint,
    ContextGrowthResponse,
    ContextDataPoint,
)
from claude_coach.core.parser import LogParser


class Analyzer:
    """Analyze Claude Code logs for insights."""

    def __init__(self, claude_dir: Optional[Path] = None):
        """Initialize analyzer."""
        if claude_dir is None:
            claude_dir = Path.home() / ".claude"
        self.claude_dir = claude_dir
        self.parser = LogParser(claude_dir)

    def get_token_usage(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        session_id: Optional[str] = None,
    ) -> TokenUsageResponse:
        """Get token usage statistics."""
        daily_tokens = defaultdict(lambda: {
            "input": 0,
            "output": 0,
            "cache_read": 0,
            "cache_create": 0,
        })

        sessions = self.parser.list_sessions(limit=1000)

        for session in sessions:
            # Filter by date if provided
            if session.created:
                session_date = datetime.fromisoformat(
                    session.created.replace("Z", "+00:00")
                ).date()

                if start_date and session_date < start_date:
                    continue
                if end_date and session_date > end_date:
                    continue

            # Filter by session_id if provided
            if session_id and session.session_id != session_id:
                continue

            detail = self.parser.get_session(session.session_id)
            if detail:
                date_key = session.created[:10] if session.created else "unknown"
                daily_tokens[date_key]["input"] += detail.total_input_tokens
                daily_tokens[date_key]["output"] += detail.total_output_tokens
                daily_tokens[date_key]["cache_read"] += detail.total_cache_read_tokens
                daily_tokens[date_key]["cache_create"] += detail.total_cache_creation_tokens

        data_points = [
            TokenDataPoint(
                date=date_str,
                input_tokens=tokens["input"],
                output_tokens=tokens["output"],
                cache_read_tokens=tokens["cache_read"],
                cache_creation_tokens=tokens["cache_create"],
            )
            for date_str, tokens in sorted(daily_tokens.items())
        ]

        total_input = sum(d.input_tokens for d in data_points)
        total_output = sum(d.output_tokens for d in data_points)

        return TokenUsageResponse(
            data=data_points,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
        )

    def get_tool_usage(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ToolUsageResponse:
        """Get tool usage statistics."""
        tool_counts = defaultdict(int)

        for project_dir in self.parser._get_project_dirs():
            for session_file in project_dir.glob("*.jsonl"):
                if session_file.name == "sessions-index.json":
                    continue

                with open(session_file) as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            if event.get("type") == "assistant":
                                content = event.get("message", {}).get("content", [])
                                for part in content:
                                    if part.get("type") == "tool_use":
                                        tool_name = part.get("name", "unknown")
                                        tool_counts[tool_name] += 1
                        except json.JSONDecodeError:
                            continue

        data_points = [
            ToolDataPoint(tool_name=name, count=count)
            for name, count in sorted(tool_counts.items(), key=lambda x: -x[1])
        ]

        return ToolUsageResponse(
            data=data_points,
            total_tool_calls=sum(tool_counts.values()),
        )

    def get_error_stats(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> ErrorStatsResponse:
        """Get error statistics."""
        error_types = defaultdict(int)

        for project_dir in self.parser._get_project_dirs():
            for session_file in project_dir.glob("*.jsonl"):
                if session_file.name == "sessions-index.json":
                    continue

                with open(session_file) as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            if event.get("type") == "system" and event.get("subtype") == "api_error":
                                error = event.get("error", {}).get("error", {})
                                error_type = error.get("type", "unknown")
                                error_types[error_type] += 1
                        except json.JSONDecodeError:
                            continue

        data_points = [
            ErrorDataPoint(error_type=err_type, count=count)
            for err_type, count in sorted(error_types.items(), key=lambda x: -x[1])
        ]

        return ErrorStatsResponse(
            data=data_points,
            total_errors=sum(error_types.values()),
        )

    def get_context_growth(self, session_id: str) -> ContextGrowthResponse:
        """Get context size evolution for a session."""
        data_points = []
        cumulative_tokens = 0
        message_index = 0

        for project_dir in self.parser._get_project_dirs():
            session_file = project_dir / f"{session_id}.jsonl"
            if not session_file.exists():
                continue

            with open(session_file) as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event.get("type") == "assistant":
                            usage = event.get("message", {}).get("usage", {})
                            input_tokens = usage.get("input_tokens", 0)
                            cache_read = usage.get("cache_read_input_tokens", 0)

                            # Approximate context size
                            cumulative_tokens = input_tokens + cache_read
                            message_index += 1

                            data_points.append(ContextDataPoint(
                                message_index=message_index,
                                context_tokens=cumulative_tokens,
                                timestamp=event.get("timestamp"),
                            ))
                    except json.JSONDecodeError:
                        continue
            break

        return ContextGrowthResponse(
            session_id=session_id,
            data=data_points,
        )
