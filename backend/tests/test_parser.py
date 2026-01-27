"""Tests for the log parser."""

import json
import tempfile
from pathlib import Path

import pytest

from claude_coach.core.parser import LogParser


@pytest.fixture
def mock_claude_dir():
    """Create a temporary Claude directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        claude_dir = Path(tmpdir)
        projects_dir = claude_dir / "projects" / "-test-project"
        projects_dir.mkdir(parents=True)

        # Create sessions-index.json
        index_data = {
            "version": 1,
            "entries": [
                {
                    "sessionId": "test-session-1",
                    "fullPath": str(projects_dir / "test-session-1.jsonl"),
                    "firstPrompt": "Hello",
                    "messageCount": 2,
                    "created": "2026-01-01T10:00:00.000Z",
                    "modified": "2026-01-01T10:05:00.000Z",
                    "gitBranch": "main",
                    "projectPath": "/test/project",
                }
            ],
            "originalPath": "/test/project",
        }
        with open(projects_dir / "sessions-index.json", "w") as f:
            json.dump(index_data, f)

        # Create session JSONL
        session_events = [
            {
                "type": "user",
                "message": {"role": "user", "content": "Hello"},
                "timestamp": "2026-01-01T10:00:00.000Z",
            },
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "model": "claude-opus-4-5-20251101",
                    "content": [{"type": "text", "text": "Hi there!"}],
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "cache_read_input_tokens": 100,
                        "cache_creation_input_tokens": 50,
                    },
                },
                "timestamp": "2026-01-01T10:00:01.000Z",
            },
        ]
        with open(projects_dir / "test-session-1.jsonl", "w") as f:
            for event in session_events:
                f.write(json.dumps(event) + "\n")

        yield claude_dir


def test_list_sessions(mock_claude_dir):
    """Test listing sessions."""
    parser = LogParser(mock_claude_dir)
    sessions = parser.list_sessions()

    assert len(sessions) == 1
    assert sessions[0].session_id == "test-session-1"
    assert sessions[0].first_prompt == "Hello"
    assert sessions[0].message_count == 2


def test_get_session(mock_claude_dir):
    """Test getting session details."""
    parser = LogParser(mock_claude_dir)
    session = parser.get_session("test-session-1")

    assert session is not None
    assert session.session_id == "test-session-1"
    assert session.total_input_tokens == 10
    assert session.total_output_tokens == 5
    assert len(session.messages) == 2


def test_get_session_not_found(mock_claude_dir):
    """Test getting a non-existent session."""
    parser = LogParser(mock_claude_dir)
    session = parser.get_session("nonexistent")

    assert session is None
