"""SQLAlchemy DeclarativeBase for all ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all Afterworlds ORM models."""
