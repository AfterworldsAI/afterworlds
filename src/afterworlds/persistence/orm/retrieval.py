"""ORM models for Retrieval Memory's RPG turn-category sidecar.

CRD Issue 18 / ADR-018 D6 (RPG turn-category marker) and the marker-era
boundary. See migration 0015 for the corresponding schema.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class RpgTurnRetrievalMarkerORM(Base):
    """One row per post-boundary RPG narrative-path DELIVERED turn.

    Written once, inside the existing narrative-persist outer transaction,
    at the same location/transaction-scoping as the Writing-mode metadata
    block — but NOT with that block's best-effort swallow behavior. A
    marker-write failure on an otherwise-deliverable turn must map to a
    typed PIPELINE_ERROR and roll back with the turn (ADR-018 D6). Rows are
    never updated after insert; deletion follows turn deletion.

    Coverage is narrower than "every RPG turn": RPG OOC_HANDLED turns are
    persisted via ``_ooc_persist`` and structurally never reach this table.
    """

    __tablename__ = "rpg_turn_retrieval_markers"

    turn_id: Mapped[str] = mapped_column(
        sa.String(36),
        sa.ForeignKey("turns.turn_id", ondelete="CASCADE"),
        primary_key=True,
    )
    story_id: Mapped[str] = mapped_column(sa.String(36), nullable=False, index=True)
    category: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    created_at: Mapped[str] = mapped_column(sa.String(64), nullable=False)


class RetrievalMarkerEraBoundaryORM(Base):
    """Singleton row recording the persisted marker-era boundary.

    ADR-018 D6 (round-7 addition): a post-boundary marker-write bug leaves
    exactly the same SQLite shape as a legitimate legacy pre-marker turn (no
    marker, no PendingRollRequest) — so the boundary itself must be
    persisted in SQLite, not inferred from app state/timing, and never
    retroactively applied to existing turns (forward-only).

    ``boundary_timestamp`` is the maximum ``turns.timestamp`` (ISO-8601,
    lexicographically sortable — see context_builder.py's timestamp-sort
    rationale) observed across all turns at migration-apply time, or NULL
    when no turns existed yet. A turn is post-boundary when its timestamp
    is strictly greater than this value (or unconditionally post-boundary
    when this value is NULL).
    """

    __tablename__ = "retrieval_marker_era_boundary"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    boundary_timestamp: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
