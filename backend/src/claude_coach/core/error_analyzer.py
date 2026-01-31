"""Error analyzer for Claude Code session logs."""

import json
import re
from pathlib import Path
from typing import Optional
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class ToolError:
    """Represents a tool error from a session."""

    tool_name: str
    error_message: str
    error_category: str
    timestamp: Optional[str]
    session_id: str
    project_path: str
    tool_input: Optional[dict]
    subcategory: Optional[str] = None


@dataclass
class ActionableIssue:
    """An actionable issue that can be fixed."""

    issue_type: str
    description: str
    fix: str
    count: int
    projects: list[str] = field(default_factory=list)
    example_errors: list[str] = field(default_factory=list)


# Error categories with descriptions and suggestions
ERROR_CATEGORIES = {
    "file_not_found": {
        "description": "Claude tried to access a file that doesn't exist",
        "suggestion": "Ensure you're working in the correct directory. Use 'ls' or file search before reading files. Check for typos in file paths.",
    },
    "directory_instead_of_file": {
        "description": "Claude tried to read a directory as if it were a file",
        "suggestion": "Use 'ls' command to list directory contents instead of Read tool. Verify the path points to a file, not a folder.",
    },
    "tool_not_available": {
        "description": "Claude tried to use a tool that isn't configured (often MCP tools)",
        "suggestion": "Check your MCP server configuration. Ensure required MCP servers are running. Verify tool names match what's available.",
    },
    "user_rejected": {
        "description": "User cancelled or rejected a tool operation",
        "suggestion": "This is expected behavior when users want to control operations. Consider being more explicit about what changes will be made before executing.",
    },
    "edit_string_not_found": {
        "description": "The Edit tool couldn't find the string to replace in the file",
        "suggestion": "Read the file first to see its current content. Ensure the old_string matches exactly including whitespace. The string may have been modified in a previous edit.",
    },
    "edit_multiple_matches": {
        "description": "The Edit tool found multiple matches for the replacement string",
        "suggestion": "Provide more context in old_string to make it unique, or use replace_all=true if all occurrences should be replaced.",
    },
    "file_not_read_first": {
        "description": "Claude tried to write/edit a file without reading it first",
        "suggestion": "Always use the Read tool before Edit or Write tools. This ensures you're working with the current file content.",
    },
    "command_failed": {
        "description": "A bash command exited with a non-zero status code",
        "suggestion": "Check command syntax and ensure required tools are installed. Review stderr output for specific error messages.",
    },
    "http_error": {
        "description": "Web fetch failed with an HTTP error (404, 403, 429, etc.)",
        "suggestion": "Verify URLs are correct. 404 means page not found. 403 means access forbidden. 429 means rate limited - wait before retrying.",
    },
    "file_too_large": {
        "description": "File exceeds the maximum token limit for reading",
        "suggestion": "Use offset and limit parameters to read file in chunks. Consider reading only specific sections relevant to the task.",
    },
    "database_connection": {
        "description": "Failed to connect to a database",
        "suggestion": "Verify database credentials and connection string. Ensure the database server is running and accessible.",
    },
    "mcp_workspace_not_set": {
        "description": "MCP tool requires a workspace to be selected first",
        "suggestion": "Select a workspace before using MCP tools that require one. Follow the tool's guidance on workspace selection.",
    },
    "task_interrupted": {
        "description": "User interrupted an ongoing task/agent",
        "suggestion": "This is expected when users want to stop long-running operations. No action needed.",
    },
    "permission_denied": {
        "description": "Operation failed due to insufficient permissions",
        "suggestion": "Check file/directory permissions. You may need to run with elevated privileges or change ownership.",
    },
    "invalid_input": {
        "description": "Tool received invalid or unrecognized parameters",
        "suggestion": "Review the tool's expected parameters. Remove any unrecognized keys from the input.",
    },
    "other": {
        "description": "Miscellaneous errors that don't fit other categories",
        "suggestion": "Review the specific error message for details on what went wrong.",
    },
}


def categorize_error(error_message: str) -> str:
    """Categorize an error based on its message."""
    err = error_message.lower()

    if "does not exist" in err or "no such file" in err or "path does not exist" in err:
        return "file_not_found"
    if "eisdir" in err:
        return "directory_instead_of_file"
    if "no such tool" in err:
        return "tool_not_available"
    if "user doesn't want" in err or "tool use was rejected" in err:
        return "user_rejected"
    if "old_string" in err and "not found" in err:
        return "edit_string_not_found"
    if "found" in err and "matches" in err and "replace_all" in err:
        return "edit_multiple_matches"
    if "file has not been read yet" in err:
        return "file_not_read_first"
    if "exit code" in err:
        return "command_failed"
    if "status code 404" in err or "status code 403" in err or "status code 429" in err or "request failed" in err:
        return "http_error"
    if "exceeds maximum" in err and "tokens" in err:
        return "file_too_large"
    if "error connecting to database" in err or "failed to connect" in err:
        return "database_connection"
    if "no workspace set" in err:
        return "mcp_workspace_not_set"
    if "interrupted by user" in err:
        return "task_interrupted"
    if "permission denied" in err:
        return "permission_denied"
    if "inputvalidationerror" in err or "unrecognized_key" in err or "unrecognized key" in err:
        return "invalid_input"

    return "other"


def get_subcategory(error: "ToolError") -> Optional[str]:
    """Get detailed subcategory for an error."""
    err = error.error_message.lower()
    tool_input = error.tool_input or {}
    command = tool_input.get("command", "") or ""

    if error.error_category == "command_failed":
        # Extract exit code
        exit_code = None
        match = re.search(r"exit code (\d+)", err)
        if match:
            exit_code = match.group(1)

        # Categorize by command type
        first_word = command.split()[0] if command.split() else ""

        # Check for specific failure patterns
        if "no such file or directory: .venv" in err:
            return "venv_not_found"
        if "is not running" in err:
            return "service_not_running"
        if "command not found" in err or exit_code == "127":
            return "command_not_found"
        if "traceback" in err or "error:" in err and "python" in command.lower():
            return "python_error"
        if "error" in err and ("npm" in first_word or "yarn" in first_word):
            return "npm_error"

        # Categorize by command
        if first_word in ["git"]:
            if exit_code == "128":
                return "git_auth_or_branch"
            return "git_error"
        if first_word in ["python", "python3"] or ".venv/bin/python" in command:
            return "python_error"
        if first_word in ["pytest", "py.test"] or "pytest" in command:
            return "test_failure"
        if first_word in ["docker", "docker-compose"]:
            return "docker_error"
        if first_word in ["npm", "npx", "yarn", "pnpm"]:
            return "npm_error"
        if first_word in ["pip", "pip3"]:
            return "pip_error"

        return f"exit_code_{exit_code}" if exit_code else None

    elif error.error_category == "http_error":
        if "404" in err:
            return "404_not_found"
        if "403" in err:
            return "403_forbidden"
        if "429" in err:
            return "429_rate_limited"
        if "500" in err or "502" in err or "503" in err:
            return "5xx_server_error"

    elif error.error_category == "tool_not_available":
        # Extract tool name
        match = re.search(r"no such tool available: (\S+)", err)
        if match:
            return match.group(1)

    return None


# Actionable issue definitions
ACTIONABLE_PATTERNS = {
    "missing_venv": {
        "description": "Python virtual environment not found",
        "fix": "Create venv before starting work. Add to CLAUDE.md: 'Always check if .venv exists and activate it before running Python commands.'",
        "pattern": lambda err, inp: "no such file or directory: .venv" in err.lower(),
    },
    "docker_not_running": {
        "description": "Docker containers not running",
        "fix": "Start Docker containers before running commands. Add to CLAUDE.md: 'Run docker-compose up -d before executing backend commands.'",
        "pattern": lambda err, inp: "is not running" in err.lower() and "docker" in (inp.get("command", "") or "").lower(),
    },
    "edit_without_read": {
        "description": "Claude tried to edit files without reading them first",
        "fix": "Add to CLAUDE.md: 'ALWAYS read a file before editing it. Never assume file contents.'",
        "pattern": lambda err, inp: "file has not been read yet" in err.lower(),
    },
    "git_auth_error": {
        "description": "Git authentication or branch errors",
        "fix": "Check git credentials are configured. Verify branch names before checkout. Add to CLAUDE.md: 'Always verify branch exists with git branch -a before checkout.'",
        "pattern": lambda err, inp: "exit code 128" in err.lower() and "git" in (inp.get("command", "") or "").lower(),
    },
    "mcp_not_configured": {
        "description": "MCP tools not available",
        "fix": "Configure the required MCP server in claude_desktop_config.json or remove references to unavailable tools.",
        "pattern": lambda err, inp: "no such tool available" in err.lower(),
    },
    "db_connection_failed": {
        "description": "Database connection failures",
        "fix": "Ensure database server is running. Check connection credentials. Add to CLAUDE.md: 'Verify database is accessible before running queries.'",
        "pattern": lambda err, inp: "error connecting to database" in err.lower() or "failed to connect" in err.lower(),
    },
    "test_failures": {
        "description": "Test suite failures",
        "fix": "Review test output for specific failures. Consider running tests in smaller batches to identify issues.",
        "pattern": lambda err, inp: "exit code 1" in err.lower() and ("pytest" in (inp.get("command", "") or "").lower() or "test" in (inp.get("command", "") or "").lower()),
    },
    "command_not_found": {
        "description": "Commands not found in PATH",
        "fix": "Install missing tools or activate the correct environment. Add to CLAUDE.md: 'Activate virtual environment before running Python tools.'",
        "pattern": lambda err, inp: "command not found" in err.lower() or "exit code 127" in err.lower(),
    },
}


class ErrorAnalyzer:
    """Analyze tool errors from Claude Code sessions."""

    def __init__(self, claude_dir: Optional[Path] = None):
        """Initialize analyzer with Claude config directory."""
        if claude_dir is None:
            claude_dir = Path.home() / ".claude"
        self.claude_dir = claude_dir
        self.projects_dir = claude_dir / "projects"

    def _get_project_dirs(self) -> list[Path]:
        """Get all project directories."""
        if not self.projects_dir.exists():
            return []
        return [d for d in self.projects_dir.iterdir() if d.is_dir()]

    def _parse_session_errors(
        self, session_file: Path, project_path: str
    ) -> list[ToolError]:
        """Parse tool errors from a session file."""
        errors = []
        session_tool_uses = {}  # tool_use_id -> {name, input, timestamp}

        with open(session_file) as f:
            for line in f:
                try:
                    event = json.loads(line)

                    # Track tool_use from assistant messages
                    if event.get("type") == "assistant":
                        timestamp = event.get("timestamp")
                        content = event.get("message", {}).get("content", [])
                        if isinstance(content, list):
                            for part in content:
                                if part.get("type") == "tool_use":
                                    tool_id = part.get("id")
                                    session_tool_uses[tool_id] = {
                                        "name": part.get("name"),
                                        "input": part.get("input", {}),
                                        "timestamp": timestamp,
                                    }

                    # Check tool results for errors
                    if event.get("type") == "user":
                        content = event.get("message", {}).get("content", [])
                        if isinstance(content, list):
                            for part in content:
                                if (
                                    part.get("type") == "tool_result"
                                    and part.get("is_error")
                                ):
                                    tool_id = part.get("tool_use_id")
                                    result_content = str(part.get("content", ""))
                                    tool_info = session_tool_uses.get(tool_id, {})

                                    error = ToolError(
                                        tool_name=tool_info.get("name", "unknown"),
                                        error_message=result_content[:1000],
                                        error_category=categorize_error(
                                            result_content
                                        ),
                                        timestamp=tool_info.get("timestamp"),
                                        session_id=session_file.stem,
                                        project_path=project_path,
                                        tool_input=tool_info.get("input"),
                                    )
                                    error.subcategory = get_subcategory(error)
                                    errors.append(error)

                except (json.JSONDecodeError, IOError):
                    continue

        return errors

    def get_session_errors(self, session_id: str) -> Optional[list[ToolError]]:
        """Get all errors for a specific session."""
        for project_dir in self._get_project_dirs():
            session_file = project_dir / f"{session_id}.jsonl"
            if session_file.exists():
                project_path = str(project_dir.name).replace("-", "/")
                return self._parse_session_errors(session_file, project_path)
        return None

    def get_project_errors(
        self, project_filter: Optional[str] = None, limit: int = 1000
    ) -> list[ToolError]:
        """Get all errors, optionally filtered by project."""
        all_errors = []

        for project_dir in self._get_project_dirs():
            project_path = str(project_dir.name).replace("-", "/")

            if project_filter and project_filter not in project_path:
                continue

            for session_file in project_dir.glob("*.jsonl"):
                errors = self._parse_session_errors(session_file, project_path)
                all_errors.extend(errors)

                if len(all_errors) >= limit:
                    break

            if len(all_errors) >= limit:
                break

        # Sort by timestamp, newest first
        all_errors.sort(key=lambda e: e.timestamp or "", reverse=True)
        return all_errors[:limit]

    def analyze_errors(
        self,
        errors: list[ToolError],
    ) -> dict:
        """Analyze a list of errors and generate summaries with suggestions."""
        # Group by category
        by_category = defaultdict(list)
        for error in errors:
            by_category[error.error_category].append(error)

        # Group by tool
        by_tool = defaultdict(lambda: defaultdict(int))
        for error in errors:
            by_tool[error.tool_name][error.error_category] += 1

        # Group by subcategory within each category
        subcategories = defaultdict(lambda: defaultdict(list))
        for error in errors:
            if error.subcategory:
                subcategories[error.error_category][error.subcategory].append(error)

        # Build category summaries with subcategories
        category_summaries = []
        for category, category_errors in sorted(
            by_category.items(), key=lambda x: -len(x[1])
        ):
            cat_info = ERROR_CATEGORIES.get(category, ERROR_CATEGORIES["other"])
            example_messages = list(
                set(e.error_message[:150] for e in category_errors[:5])
            )

            # Build subcategory breakdown
            subcategory_breakdown = {}
            if category in subcategories:
                for subcat, subcat_errors in sorted(
                    subcategories[category].items(), key=lambda x: -len(x[1])
                ):
                    subcategory_breakdown[subcat] = {
                        "count": len(subcat_errors),
                        "example": subcat_errors[0].error_message[:100] if subcat_errors else None,
                    }

            category_summaries.append(
                {
                    "category": category,
                    "count": len(category_errors),
                    "description": cat_info["description"],
                    "suggestion": cat_info["suggestion"],
                    "example_errors": example_messages,
                    "subcategories": subcategory_breakdown,
                }
            )

        # Build tool summaries
        tool_summaries = []
        for tool_name, categories in sorted(
            by_tool.items(), key=lambda x: -sum(x[1].values())
        ):
            tool_summaries.append(
                {
                    "tool_name": tool_name,
                    "total_errors": sum(categories.values()),
                    "by_category": dict(categories),
                }
            )

        # Identify actionable issues
        actionable_issues = self._identify_actionable_issues(errors)

        return {
            "total_errors": len(errors),
            "by_category": category_summaries,
            "by_tool": tool_summaries,
            "actionable_issues": actionable_issues,
        }

    def _identify_actionable_issues(self, errors: list[ToolError]) -> list[dict]:
        """Identify actionable issues that can be fixed."""
        issues = defaultdict(lambda: {"count": 0, "projects": set(), "examples": []})

        for error in errors:
            tool_input = error.tool_input or {}
            for issue_type, issue_def in ACTIONABLE_PATTERNS.items():
                try:
                    if issue_def["pattern"](error.error_message, tool_input):
                        issues[issue_type]["count"] += 1
                        issues[issue_type]["projects"].add(error.project_path)
                        if len(issues[issue_type]["examples"]) < 3:
                            issues[issue_type]["examples"].append(
                                error.error_message[:150]
                            )
                except Exception:
                    continue

        # Convert to list
        result = []
        for issue_type, data in sorted(issues.items(), key=lambda x: -x[1]["count"]):
            if data["count"] > 0:
                issue_def = ACTIONABLE_PATTERNS[issue_type]
                result.append({
                    "issue_type": issue_type,
                    "description": issue_def["description"],
                    "fix": issue_def["fix"],
                    "count": data["count"],
                    "projects": list(data["projects"])[:5],
                    "examples": data["examples"],
                })

        return result

    def get_errors_by_timeframe(
        self,
        days: int = 7,
        project_filter: Optional[str] = None,
    ) -> dict:
        """Get errors grouped by day for the last N days."""
        from datetime import timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        errors = self.get_project_errors(project_filter=project_filter, limit=5000)

        # Filter by date and group
        by_date = defaultdict(list)
        for error in errors:
            if error.timestamp:
                try:
                    dt = datetime.fromisoformat(error.timestamp.replace("Z", "+00:00"))
                    if dt >= cutoff:
                        date_str = dt.strftime("%Y-%m-%d")
                        by_date[date_str].append(error)
                except (ValueError, TypeError):
                    continue

        # Build daily summaries
        daily_summaries = []
        for date_str in sorted(by_date.keys()):
            date_errors = by_date[date_str]
            categories = defaultdict(int)
            for e in date_errors:
                categories[e.error_category] += 1

            daily_summaries.append({
                "date": date_str,
                "total": len(date_errors),
                "by_category": dict(categories),
            })

        # Also get actionable issues for this timeframe
        recent_errors = [e for errs in by_date.values() for e in errs]
        actionable = self._identify_actionable_issues(recent_errors)

        return {
            "days": days,
            "total_errors": len(recent_errors),
            "daily": daily_summaries,
            "actionable_issues": actionable,
        }
