"""Retrieval eligibility predicate — CRD Issue 18 / ADR-018 D6 / D8.

The single eligibility predicate every consumer must share: the ingestion
gate, the retrieval-query-tail builder, backfill, and reindex all call
:func:`gather_turn_eligibility`, never a locally re-derived check (ADR-018
sibling-audit checkpoint #5). The predicate reads only committed
SQLite-reconstructable state — never a transient in-memory request object
(e.g. ``WritingTurnRequest``) — so live ingestion and offline
backfill/reindex always agree.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.enums import (
    IntentType,
    RpgTurnRetrievalCategory,
    StoryMode,
    WritingCanonEligibility,
)
from afterworlds.models.node import ModeMetadata, WritingNodeMetadata
from afterworlds.models.turn import Turn
from afterworlds.persistence.crud.node import get_turn
from afterworlds.persistence.crud.retrieval import (
    get_era_boundary_timestamp,
    get_rpg_turn_retrieval_marker,
    has_pending_roll_request_originating_from_turn,
)
from afterworlds.persistence.crud.retrieval import is_post_boundary as _is_post_boundary
from afterworlds.persistence.orm.node import TurnORM


@dataclass(frozen=True)
class EligibilityDecision:
    """Outcome of the retrieval-eligibility predicate for one committed turn."""

    eligible: bool
    data_integrity_error: bool = False
    reason: str = ""


def decide_turn_eligibility(
    *,
    story_mode: StoryMode,
    intent_classification: IntentType,
    mode_metadata: ModeMetadata | None,
    rpg_marker_category: RpgTurnRetrievalCategory | None,
    is_post_boundary: bool,
    has_pending_roll_request: bool = False,
) -> EligibilityDecision:
    """Pure decision function — no I/O. See module docstring for callers.

    Mode-specific rules (ADR-018 D6/D8):
      - OOC turns are always excluded, regardless of mode.
      - Writing: eligible only when committed ``WritingNodeMetadata``
        exists and its ``canon_eligibility`` reads ``EXTRACTOR_ELIGIBLE``.
        Missing/malformed metadata (the Writing block's best-effort write
        can fail silently) is treated as ineligible, never as eligible.
      - RPG: ``has_pending_roll_request`` (a persisted ``PendingRollRequest``
        row whose ``originating_turn_id`` matches this turn) is checked
        before marker classification and governs regardless of marker
        category — this is what excludes a legacy pre-marker roll-request
        turn, since it predates the marker sidecar entirely and carries no
        marker row (ADR-018 D6 era-boundary table). Otherwise, eligible only
        for ``ORDINARY_NARRATIVE`` markers. A markerless post-boundary turn
        is a data-integrity error (ineligible, flagged); a markerless
        pre-boundary (legacy) turn with no pending-roll row is eligible.
      - Branching (and any other mode): eligible by default once the OOC
        filter above is applied — Branching setup confirmations remain
        eligible as ordinary narrative turns (CRD Issue 16).
    """
    if intent_classification is IntentType.OOC:
        return EligibilityDecision(eligible=False, reason="ooc turn")

    if story_mode is StoryMode.WRITING:
        if not isinstance(mode_metadata, WritingNodeMetadata):
            return EligibilityDecision(
                eligible=False,
                reason="missing or malformed WritingNodeMetadata"
                " (treated as ineligible per the best-effort-write safe default)",
            )
        if (
            mode_metadata.canon_eligibility
            != WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
        ):
            return EligibilityDecision(
                eligible=False,
                reason=f"canon_eligibility={mode_metadata.canon_eligibility!r}",
            )
        return EligibilityDecision(eligible=True)

    if story_mode is StoryMode.RPG:
        if has_pending_roll_request:
            return EligibilityDecision(
                eligible=False,
                reason="PendingRollRequest.originating_turn_id matches this turn"
                " (roll-request procedural output)",
            )
        if rpg_marker_category is None:
            if is_post_boundary:
                return EligibilityDecision(
                    eligible=False,
                    data_integrity_error=True,
                    reason="post-boundary RPG narrative-path turn missing marker row",
                )
            return EligibilityDecision(
                eligible=True,
                reason="pre-boundary legacy turn treated as ORDINARY_NARRATIVE",
            )
        if rpg_marker_category is RpgTurnRetrievalCategory.ORDINARY_NARRATIVE:
            return EligibilityDecision(eligible=True)
        return EligibilityDecision(
            eligible=False, reason=f"rpg marker category={rpg_marker_category.value}"
        )

    return EligibilityDecision(eligible=True)


def gather_turn_eligibility_for_turn(
    session: Session, turn: Turn, story_mode: StoryMode
) -> EligibilityDecision:
    """Decide eligibility for an already-fetched *turn*.

    Split from :func:`gather_turn_eligibility` so callers that already hold
    the committed ``Turn`` (e.g. the ingestion gate, which also needs
    ``turn.assistant_output``/``turn.node_id`` to build the chunk) do not
    issue a second redundant read.
    """
    marker_category: RpgTurnRetrievalCategory | None = None
    post_boundary = True
    has_pending_roll_request = False
    if story_mode is StoryMode.RPG:
        marker_category = get_rpg_turn_retrieval_marker(session, turn.turn_id)
        raw_row = session.get(TurnORM, str(turn.turn_id))
        assert raw_row is not None  # noqa: S101 — caller-supplied turn exists
        boundary = get_era_boundary_timestamp(session)
        post_boundary = _is_post_boundary(raw_row.timestamp, boundary)
        has_pending_roll_request = has_pending_roll_request_originating_from_turn(
            session, turn.turn_id
        )

    return decide_turn_eligibility(
        story_mode=story_mode,
        intent_classification=turn.intent_classification,
        mode_metadata=turn.mode_metadata,
        rpg_marker_category=marker_category,
        is_post_boundary=post_boundary,
        has_pending_roll_request=has_pending_roll_request,
    )


def gather_turn_eligibility(
    session: Session, turn_id: UUID, story_mode: StoryMode
) -> EligibilityDecision:
    """Read committed SQLite state for *turn_id* and decide eligibility.

    Returns ``eligible=False`` with a reason when the turn does not exist
    (e.g. already deleted) rather than raising, since callers (backfill,
    reindex) iterate turn IDs that may no longer be present.
    """
    turn = get_turn(session, turn_id)
    if turn is None:
        return EligibilityDecision(eligible=False, reason="turn not found")
    return gather_turn_eligibility_for_turn(session, turn, story_mode)
