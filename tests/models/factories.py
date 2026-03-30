"""Shared test helpers for model tests."""

from datetime import UTC, datetime


def make_datetime() -> datetime:
    """Return a timezone-aware datetime for use in tests."""
    return datetime.now(UTC)
