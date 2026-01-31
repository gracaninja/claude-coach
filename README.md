# Claude-Coach

Extract insights from Claude Code logs for self-improvement and coaching.

## Features

- **Usage Analytics**: Track tool usage, token consumption, and session patterns
- **Performance Metrics**: Monitor response times, error rates, and context growth
- **Error Analysis**: Categorize errors with actionable suggestions for fixing them
- **Learning Insights**: Identify workflow patterns and improvement opportunities
- **Community Comparison**: Compare your usage to community benchmarks
- **Anonymized Export**: Share metrics without exposing code or prompts
- **Privacy First**: All data stays local by default

## Quick Start

### 1. Import Your Logs

```bash
cd backend
pip install -e ".[dev]"

# Import Claude Code logs into local database
claude-coach import
```

### 2. Start the Backend

```bash
claude-coach serve
# or
uvicorn claude_coach.main:app --reload
```

### 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open Dashboard

Visit http://localhost:5173 to see your insights.

## CLI Commands

```bash
# Import logs from Claude Code
claude-coach import [--claude-dir PATH] [--force]

# Start API server
claude-coach serve [--host HOST] [--port PORT] [--reload]

# Show quick statistics
claude-coach stats
```

## Architecture

```
claude-coach/
├── backend/           # FastAPI + SQLAlchemy
│   ├── src/claude_coach/
│   │   ├── api/       # REST endpoints
│   │   ├── core/      # Parsing & analysis
│   │   ├── models/    # Database models
│   │   └── schemas/   # Pydantic schemas
│   └── tests/
├── frontend/          # React + Vite
│   └── src/
│       ├── components/
│       ├── pages/
│       └── hooks/
└── README.md
```

## Data Sources

Claude-Coach reads from your local Claude Code logs:

| Source | Location | Data |
|--------|----------|------|
| Session logs | `~/.claude/projects/<project>/*.jsonl` | Full conversation history |
| Sessions index | `~/.claude/projects/<project>/sessions-index.json` | Session metadata |
| Stats cache | `~/.claude/stats-cache.json` | Aggregated statistics |
| Debug logs | `~/.claude/debug/*.txt` | System events |

## Insights Available

- Token usage over time
- Tool usage frequency and patterns
- Response latency analysis
- Error rate tracking with categorization
- Context size evolution
- Cache efficiency metrics
- Planning vs execution time analysis
- Personalized recommendations

### Error Analysis

The error analysis dashboard helps you identify and fix recurring issues:

- **16 Error Categories**: file_not_found, command_failed, http_error, edit_string_not_found, and more
- **Subcategory Drill-Down**: See specific error types (e.g., python_error, git_auth_error, test_failure)
- **Actionable Issues**: Get specific suggestions for fixing errors via CLAUDE.md or configuration
- **Trend Analysis**: Track error patterns over 7/14/30 day periods
- **Project Filtering**: Focus on errors from specific projects

## Community Features

### Anonymized Export

Export your usage metrics without exposing any sensitive data:

```bash
# Via CLI (coming soon)
claude-coach export --output metrics.json

# Via API
curl http://localhost:8000/api/community/export > metrics.json
```

### What's Shared vs Private

| Shared (Anonymized) | Never Shared |
|---------------------|--------------|
| Session counts | Prompts/messages |
| Token totals | File paths |
| Tool usage counts | Code content |
| Error types | Project names |
| Cache hit rates | Git branches |

### Community Benchmarks

Compare your usage to community averages:
- Sessions per day
- Tokens per session
- Tool efficiency
- Error rates

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/sessions` | List all sessions |
| `GET /api/sessions/{id}` | Session details |
| `GET /api/analytics/tokens` | Token usage stats |
| `GET /api/analytics/tools` | Tool usage stats |
| `GET /api/analytics/errors` | Error statistics |
| `GET /api/analytics/error-analysis` | Comprehensive error analysis with suggestions |
| `GET /api/analytics/error-analysis/timeframe` | Error trends over time |
| `GET /api/analytics/error-analysis/session/{id}` | Session-specific errors |
| `GET /api/analytics/plan-mode` | Planning vs execution stats |
| `GET /api/community/export` | Anonymized metrics |
| `GET /api/community/compare` | Compare to benchmarks |
| `GET /api/community/insights` | Personalized insights |

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

MIT License - see [LICENSE](LICENSE) for details.
