"""API dependencies."""

from typing import Generator
from sqlalchemy.orm import Session

from claude_coach.models import get_session_factory

# Create session factory
SessionFactory = get_session_factory()


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()
