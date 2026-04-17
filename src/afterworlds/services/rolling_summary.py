"""Rolling Summary service — compression trigger, generation, and retrieval.

This module implements the Rolling Summary memory layer (CRD Issue 6).

The Rolling Summary is a compressed narrative history that fits within the
stable prefix budget.  It sits between the Immediate layer (recent turns
verbatim) and the Story Bible (structured canon):

  Stable prefix:  [System + mode contract] [Story Bible] [Rolling summary]
  Volatile suffix: [Recent turns verbatim] [Current input + intent]

Design constraints from the issue spec:
  - N is configurable (``ROLLING_SUMMARY_N``).  Start at 10.
  - Summaries are append-only; prior rows are never overwritten.
  - Idempotency is anchored to ``compressed_through_turn_id``, not to trigger
    heuristics.  The DB enforces this via a UNIQUE constraint on
    ``(story_id, compressed_through_turn_id)``.
  - Exactly one row per story may be ``is_current = True`` at any time.
    Enforced by a partial unique index (see migration 0006) and by service
    logic that atomically clears the previous current marker.
  - The summary generation callable is injected — no hardwired provider or
    model.  For tests, a stub can be passed in.
  - No prompt assembly, no Context Builder integration, no pipeline calls.

N-value Known Unknown:
  ``ROLLING_SUMMARY_N`` is the designated Known Unknown from
  ``known_unknowns.md``.  Starting value is 10.  See ADR-0009 for the
  escape-hatch rationale: empirical tuning requires the Context Builder
  (Issue 8) and is deferred to that issue.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from afterworlds.models.rolling_summary import RollingSummary
from afterworlds.persistence.orm.rolling_summary import RollingSummaryORM

# ---------------------------------------------------------------------------
# Configurable constants
# ---------------------------------------------------------------------------

#: Compression trigger interval.  Every N turns, a new rolling summary is
#: produced.  N = 10 is the starting value; tune with testing once the Context
#: Builder (Issue 8) is in place.  See ADR-0009.
ROLLING_SUMMARY_N: int = 10

# ---------------------------------------------------------------------------
# Generator type
# ---------------------------------------------------------------------------

#: Callable interface for the summary generator dependency.
#:
#: Arguments:
#:   prior_summary (str | None): text of the current summary before this
#:     compression, or None if this is the first compression for the story.
#:   turn_texts (list[str]): ordered list of turn content strings for the
#:     turns being compressed into this summary.
#:
#: Returns:
#:   str: the generated summary text.
SummaryGeneratorT = Callable[[str | None, list[str]], str]


# ---------------------------------------------------------------------------
# Trigger helper
# ---------------------------------------------------------------------------


def should_compress(story_turn_count: int, n: int = ROLLING_SUMMARY_N) -> bool:
    """Return True if a compression should fire for the given total turn count.

    Compression fires at multiples of N (N, 2N, 3N, …).  A count of zero
    never triggers compression.

    Args:
        story_turn_count: total number of turns persisted for the story so far
            (including the turn just added).
        n: the compression interval.  Defaults to the module-level
            ``ROLLING_SUMMARY_N`` constant.

    Returns:
        True if ``story_turn_count > 0`` and ``story_turn_count % n == 0``.
    """
    return story_turn_count > 0 and story_turn_count % n == 0


# ---------------------------------------------------------------------------
# ORM ↔ Pydantic conversion
# ---------------------------------------------------------------------------


def _orm_to_model(row: RollingSummaryORM) -> RollingSummary:
    return RollingSummary(
        summary_id=UUID(row.summary_id),
        story_id=UUID(row.story_id),
        text=row.text,
        compressed_from_turn_id=UUID(row.compressed_from_turn_id),
        compressed_through_turn_id=UUID(row.compressed_through_turn_id),
        version_number=row.version_number,
        is_current=row.is_current,
        created_at=datetime.fromisoformat(row.created_at),
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class RollingSummaryService:
    """Service for the Rolling Summary memory layer.

    Responsibilities:
      - Compress a slice of turns into a new summary using an injected generator.
      - Persist the new summary as an append-only row.
      - Atomically manage the ``is_current`` marker.
      - Retrieve the current summary or full history for a story.

    Args:
        session: SQLAlchemy session.
        generator: callable that produces summary text from a prior summary
            (or None) and a list of turn texts.  See :data:`SummaryGeneratorT`.
    """

    def __init__(self, session: Session, generator: SummaryGeneratorT) -> None:
        self._session = session
        self._generator = generator

    # ------------------------------------------------------------------
    # Compression
    # ------------------------------------------------------------------

    def compress(
        self,
        story_id: UUID,
        from_turn_id: UUID,
        through_turn_id: UUID,
        turn_texts: list[str],
    ) -> RollingSummary:
        """Compress a turn slice into a new rolling summary.

        Idempotent: if the current summary for this story already covers
        ``through_turn_id``, the existing row is returned unchanged and the
        generator is **not** called.  The DB unique constraint on
        ``(story_id, compressed_through_turn_id)`` is the authoritative
        idempotency gate; this service method also short-circuits on the
        same condition before attempting a write.

        The new row is inserted with ``is_current = True``.  The prior
        current row (if any) is atomically flipped to ``is_current = False``
        within the same flush so the DB partial unique index is never
        transiently violated.

        Args:
            story_id: UUID of the story being compressed.
            from_turn_id: UUID of the first Turn in the slice.
            through_turn_id: UUID of the last Turn in the slice.
            turn_texts: ordered list of turn content strings for the slice.

        Returns:
            The newly created (or pre-existing idempotent) :class:`RollingSummary`.

        Raises:
            IntegrityError: if the DB constraint is violated by a concurrent
                writer (should not occur in normal single-writer usage).
        """
        sid = str(story_id)
        through_id = str(through_turn_id)

        # --- Idempotency short-circuit (service layer) ---
        existing = (
            self._session.execute(
                select(RollingSummaryORM).where(
                    RollingSummaryORM.story_id == sid,
                    RollingSummaryORM.compressed_through_turn_id == through_id,
                )
            )
            .scalars()
            .first()
        )
        if existing is not None:
            return _orm_to_model(existing)

        # --- Fetch prior summary text ---
        prior = self.get_current_summary(story_id)
        prior_text: str | None = prior.text if prior else None

        # --- Determine next version number ---
        next_version = (prior.version_number + 1) if prior else 1

        # --- Generate new summary text ---
        new_text = self._generator(prior_text, turn_texts)

        # --- Atomically clear previous current marker ---
        if prior is not None:
            prior_row = self._session.get(RollingSummaryORM, str(prior.summary_id))
            if prior_row is not None:
                prior_row.is_current = False

        # --- Persist new row ---
        now = datetime.now(UTC).isoformat()
        new_row = RollingSummaryORM(
            summary_id=str(uuid4()),
            story_id=sid,
            text=new_text,
            compressed_from_turn_id=str(from_turn_id),
            compressed_through_turn_id=through_id,
            version_number=next_version,
            is_current=True,
            created_at=now,
        )
        self._session.add(new_row)
        try:
            self._session.flush()
        except IntegrityError:
            self._session.rollback()
            raise

        return _orm_to_model(new_row)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_current_summary(self, story_id: UUID) -> RollingSummary | None:
        """Return the active current rolling summary, or None.

        This is the method the Context Builder (Issue 8) will call when
        assembling the stable prefix.

        Returns:
            The :class:`RollingSummary` for the current row, or ``None`` if no
            summary has been compressed yet for this story.
        """
        row = (
            self._session.execute(
                select(RollingSummaryORM).where(
                    RollingSummaryORM.story_id == str(story_id),
                    RollingSummaryORM.is_current.is_(True),
                )
            )
            .scalars()
            .first()
        )
        return _orm_to_model(row) if row else None

    def get_summary_history(self, story_id: UUID) -> list[RollingSummary]:
        """Return all summaries for a story in creation order.

        Includes historical (non-current) rows.  Intended for debugging and
        regression investigation; not called by the Context Builder.

        Returns:
            List of :class:`RollingSummary` ordered by ``version_number``
            ascending (creation order).
        """
        rows = (
            self._session.execute(
                select(RollingSummaryORM)
                .where(RollingSummaryORM.story_id == str(story_id))
                .order_by(
                    RollingSummaryORM.version_number.asc(),
                    RollingSummaryORM.summary_id.asc(),
                )
            )
            .scalars()
            .all()
        )
        return [_orm_to_model(r) for r in rows]
