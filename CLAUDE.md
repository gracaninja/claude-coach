# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude-Coach extracts insights from Claude Code logs (~/.claude/) for usage analytics and self-improvement coaching. It has a Python/FastAPI backend and a React/Vite frontend.

## Common Commands

### Backend (from `backend/` directory)

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Import Claude Code logs into local database
claude-coach import

# Start API server (dev mode)
claude-coach serve --reload

# Show quick statistics
claude-coach stats

# Run tests
pytest

# Run single test file
pytest tests/test_parser.py

# Run tests with coverage
pytest --cov=claude_coach

# Lint and type check
ruff check src/
mypy src/
```

### Frontend (from `frontend/` directory)

```bash
npm install
npm run dev      # Start dev server at localhost:5173
npm run build    # TypeScript check + Vite build
npm run lint     # ESLint
```

## Architecture

```
backend/
├── src/claude_coach/
│   ├── main.py           # FastAPI app entry, CORS config, router mounts
│   ├── cli.py            # CLI commands (import, serve, stats)
│   ├── api/routes/       # REST endpoints (sessions, analytics, community)
│   ├── core/             # Business logic
│   │   ├── parser.py     # Parses Claude Code JSONL logs
│   │   ├── importer.py   # Imports logs into SQLite database
│   │   ├── analyzer.py   # Computes analytics from stored data
│   │   ├── error_analyzer.py # Categorizes errors with actionable suggestions
│   │   ├── anonymizer.py # Strips sensitive data for export
│   │   └── insights.py   # Generates personalized recommendations
│   ├── models/           # SQLAlchemy models (Session, ToolUsage, ErrorEvent)
│   └── schemas/          # Pydantic schemas for API requests/responses
└── tests/

frontend/
└── src/
    ├── api/              # Axios API clients
    ├── components/       # React components (Layout with project filter)
    ├── context/          # React context (ProjectContext for global filtering)
    ├── pages/            # Page components (Dashboard, Sessions, Analytics, ErrorAnalysis)
    └── hooks/            # Custom React hooks
```

## Key Data Flow

1. `LogParser` reads from `~/.claude/projects/<project>/*.jsonl` files
2. `LogImporter` stores parsed data in SQLite (`~/.claude-coach/claude_coach.db`)
3. API routes query the database via SQLAlchemy
4. Frontend fetches from `/api/*` endpoints using react-query

## API Routes

- `/api/sessions` - Session listing and details
- `/api/analytics/tokens` - Token usage stats
- `/api/analytics/tools` - Tool usage stats
- `/api/analytics/errors` - Error statistics
- `/api/analytics/error-analysis` - Comprehensive error analysis with actionable suggestions
- `/api/analytics/error-analysis/timeframe` - Error trends over time (7/14/30 days)
- `/api/analytics/error-analysis/session/{id}` - Session-specific errors
- `/api/analytics/plan-mode` - Planning vs execution time stats
- `/api/community` - Anonymized export and benchmarks
