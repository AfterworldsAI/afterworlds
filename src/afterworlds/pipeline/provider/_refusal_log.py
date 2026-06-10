"""Provider refusal log ORM — CRD Issue 14a.

``provider_refusal_log`` is append-only via SQLite UPDATE/DELETE triggers
(same pattern as ``entitlement_event``).  Coarse and non-sensitive only:
no prompt text, Sojourner input, response excerpts, or key material in any
column.

The in-memory ``ProviderRefusal.raw_response_excerpt`` stays in-memory for
audit context — it is never persisted here, never emitted to default log
output, and sanitized before any DEBUG opt-in emission.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class ProviderRefusalEvent(Base):
    """One append-only row per refusal attempt."""

    __tablename__ = "provider_refusal_log"

    # INTEGER PRIMARY KEY = SQLite rowid alias; auto-increments without AUTOINCREMENT.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    turn_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    sojourner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    pass_id: Mapped[str] = mapped_column(String(32), nullable=False)

    primary_provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    primary_model_identifier: Mapped[str] = mapped_column(String(256), nullable=False)

    refusal_category: Mapped[str] = mapped_column(String(32), nullable=False)
    fallback_outcome: Mapped[str] = mapped_column(String(64), nullable=False)

    fallback_provider_name: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    fallback_model_identifier: Mapped[str | None] = mapped_column(
        String(256), nullable=True
    )

    # Coarse advisory metadata only — no prompts, inputs, excerpts, or key material.
    coarse_metadata_json: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_provider_refusal_log_turn_id", "turn_id"),
        Index("ix_provider_refusal_log_sojourner_id", "sojourner_id"),
        Index("ix_provider_refusal_log_created_at", "created_at"),
    )


__all__ = ["ProviderRefusalEvent"]
