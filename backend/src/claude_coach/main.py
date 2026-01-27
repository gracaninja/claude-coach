"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from claude_coach.api.routes import sessions, analytics, community

app = FastAPI(
    title="Claude-Coach API",
    description="Extract insights from Claude Code logs for self-improvement and coaching",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for local frontend development and tunnels
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development/tunneling
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(community.router, prefix="/api/community", tags=["community"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "claude-coach"}


@app.get("/api/health")
async def health():
    """Health check for API."""
    return {"status": "healthy"}
