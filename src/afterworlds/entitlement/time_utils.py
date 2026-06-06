"""UTC datetime normalisation utilities."""

from __future__ import annotations

from datetime import UTC, datetime


def to_utc_naive(dt: datetime) -> datetime:
    """Normalise a datetime to UTC-naive for safe cross-tzinfo comparison.

    SQLite can reload DateTime columns as offset-naive; callers may inject
    timezone-aware clocks.  Converting both sides through this function before
    comparing avoids TypeError.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt
