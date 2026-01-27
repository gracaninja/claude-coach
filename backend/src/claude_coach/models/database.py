"""Database configuration and session management."""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Default to SQLite in user's home directory
DEFAULT_DB_PATH = Path.home() / ".claude-coach" / "claude_coach.db"


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


def get_database_url(db_path: Path | None = None) -> str:
    """Get the database URL."""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def create_db_engine(db_path: Path | None = None):
    """Create database engine."""
    url = get_database_url(db_path)
    return create_engine(url, echo=False)


def get_session_factory(db_path: Path | None = None):
    """Get a session factory."""
    engine = create_db_engine(db_path)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(db_path: Path | None = None):
    """Initialize the database, creating all tables."""
    engine = create_db_engine(db_path)
    Base.metadata.create_all(bind=engine)
    return engine
