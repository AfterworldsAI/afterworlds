"""Pydantic models for the Rolling Summary memory layer.

The Rolling Summary is one of the six memory layers.  It is a compressed,
auto-updated narrative history that lives in the stable prefix alongside the
Story Bible.  It is structurally separate from:

- The Story Bible (structured canon).
- Retrieval Memory (semantic vector store).
- Immediate layer (recent turns verbatim).

These models represent persisted summary rows.  The service layer
(:mod:`afterworlds.services.rolling_summary`) is responsible for trigger
logic, generation, and retrieval.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RollingSummary(BaseModel):
    """One persisted rolling summary row.

    Each row covers a closed, non-overlapping range of turns
    [``compressed_from_turn_id`` … ``compressed_through_turn_id``].

    ``version_number`` increases monotonically per story starting at 1.
    ``is_current`` marks the single active row for the story; only one row
    per story may carry ``is_current = True`` at any time.

    Rows are append-only — prior summaries are never overwritten in place.
    """

    summary_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    text: str
    compressed_from_turn_id: UUID
    compressed_through_turn_id: UUID
    version_number: int
    is_current: bool = False
    created_at: datetime
