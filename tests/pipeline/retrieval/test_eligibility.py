"""Unit tests for the shared retrieval-eligibility predicate.

CRD Issue 18 / ADR-018 D6/D8. These exercise ``decide_turn_eligibility``
directly (pure function, no I/O) — the DB-integration path
(``gather_turn_eligibility`` / ``gather_turn_eligibility_for_turn``) is
covered in ``tests/persistence/test_retrieval_markers_db.py``.
"""

from __future__ import annotations

from afterworlds.models.enums import (
    IntentType,
    RpgTurnRetrievalCategory,
    StoryMode,
    WritingCanonEligibility,
)
from afterworlds.models.node import WritingNodeMetadata
from afterworlds.pipeline.retrieval.eligibility import decide_turn_eligibility


def _decide(**overrides: object) -> object:
    defaults: dict[str, object] = {
        "story_mode": StoryMode.WRITING,
        "intent_classification": IntentType.DIALOGUE,
        "mode_metadata": None,
        "rpg_marker_category": None,
        "is_post_boundary": True,
    }
    defaults.update(overrides)
    return decide_turn_eligibility(**defaults)  # type: ignore[arg-type]


class TestOocExclusion:
    def test_ooc_always_excluded_regardless_of_mode(self) -> None:
        for mode in StoryMode:
            decision = _decide(story_mode=mode, intent_classification=IntentType.OOC)
            assert decision.eligible is False  # type: ignore[attr-defined]


class TestWritingEligibility:
    def test_extractor_eligible_is_eligible(self) -> None:
        metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.EXTRACTOR_ELIGIBLE.value
        )
        decision = _decide(story_mode=StoryMode.WRITING, mode_metadata=metadata)
        assert decision.eligible is True  # type: ignore[attr-defined]

    def test_non_canon_support_is_ineligible(self) -> None:
        metadata = WritingNodeMetadata(
            canon_eligibility=WritingCanonEligibility.NON_CANON_SUPPORT.value
        )
        decision = _decide(story_mode=StoryMode.WRITING, mode_metadata=metadata)
        assert decision.eligible is False  # type: ignore[attr-defined]

    def test_missing_metadata_is_ineligible(self) -> None:
        """Best-effort write failure must be treated as ineligible, never eligible."""
        decision = _decide(story_mode=StoryMode.WRITING, mode_metadata=None)
        assert decision.eligible is False  # type: ignore[attr-defined]

    def test_malformed_metadata_is_ineligible(self) -> None:
        decision = _decide(story_mode=StoryMode.WRITING, mode_metadata="not-metadata")
        assert decision.eligible is False  # type: ignore[attr-defined]


class TestRpgEligibility:
    def test_ordinary_narrative_marker_eligible(self) -> None:
        decision = _decide(
            story_mode=StoryMode.RPG,
            rpg_marker_category=RpgTurnRetrievalCategory.ORDINARY_NARRATIVE,
            is_post_boundary=True,
        )
        assert decision.eligible is True  # type: ignore[attr-defined]

    def test_roll_request_marker_ineligible(self) -> None:
        decision = _decide(
            story_mode=StoryMode.RPG,
            rpg_marker_category=RpgTurnRetrievalCategory.ROLL_REQUEST,
            is_post_boundary=True,
        )
        assert decision.eligible is False  # type: ignore[attr-defined]

    def test_setup_confirmation_marker_ineligible(self) -> None:
        decision = _decide(
            story_mode=StoryMode.RPG,
            rpg_marker_category=RpgTurnRetrievalCategory.SETUP_CONFIRMATION,
            is_post_boundary=True,
        )
        assert decision.eligible is False  # type: ignore[attr-defined]

    def test_post_boundary_markerless_is_data_integrity_error(self) -> None:
        decision = _decide(
            story_mode=StoryMode.RPG,
            rpg_marker_category=None,
            is_post_boundary=True,
        )
        assert decision.eligible is False  # type: ignore[attr-defined]
        assert decision.data_integrity_error is True  # type: ignore[attr-defined]

    def test_pre_boundary_markerless_is_eligible_ordinary_narrative(self) -> None:
        """Legacy turns predating the marker era are treated as ORDINARY_NARRATIVE."""
        decision = _decide(
            story_mode=StoryMode.RPG,
            rpg_marker_category=None,
            is_post_boundary=False,
        )
        assert decision.eligible is True  # type: ignore[attr-defined]
        assert decision.data_integrity_error is False  # type: ignore[attr-defined]

    def test_pre_boundary_markerless_with_pending_roll_is_excluded(self) -> None:
        """Codex #119 P1: a legacy pre-marker roll-request turn has no
        marker row (predates the sidecar entirely), so the markerless
        pre-boundary fallback above would otherwise wrongly treat it as
        eligible ORDINARY_NARRATIVE. PendingRollRequest.originating_turn_id
        is the only signal that can exclude it (ADR-018 D6 era-boundary
        table, "Before persisted boundary, roll-request" row)."""
        decision = _decide(
            story_mode=StoryMode.RPG,
            rpg_marker_category=None,
            is_post_boundary=False,
            has_pending_roll_request=True,
        )
        assert decision.eligible is False  # type: ignore[attr-defined]
        assert decision.data_integrity_error is False  # type: ignore[attr-defined]

    def test_pre_boundary_markerless_without_pending_roll_remains_eligible(
        self,
    ) -> None:
        """Same shape as above but with no PendingRollRequest row: must
        remain eligible — the pending-roll check must not over-exclude
        ordinary legacy turns that never announced a roll."""
        decision = _decide(
            story_mode=StoryMode.RPG,
            rpg_marker_category=None,
            is_post_boundary=False,
            has_pending_roll_request=False,
        )
        assert decision.eligible is True  # type: ignore[attr-defined]

    def test_post_boundary_markerless_remains_data_integrity_error(self) -> None:
        """A post-boundary markerless turn is a data-integrity error
        regardless of has_pending_roll_request — the coverage invariant
        (ADR-018 D6) means every post-boundary narrative-path turn must have
        a marker row; a missing one is a bug to surface, not to paper over
        by falling through to the pending-roll or legacy-eligible paths."""
        decision = _decide(
            story_mode=StoryMode.RPG,
            rpg_marker_category=None,
            is_post_boundary=True,
            has_pending_roll_request=False,
        )
        assert decision.eligible is False  # type: ignore[attr-defined]
        assert decision.data_integrity_error is True  # type: ignore[attr-defined]

    def test_pending_roll_request_governs_regardless_of_marker_category(self) -> None:
        """ADR-018 D6: PendingRollRequest.originating_turn_id governs the
        exclusion decision regardless of marker category — verified here
        against an ORDINARY_NARRATIVE marker, which would otherwise be
        eligible."""
        decision = _decide(
            story_mode=StoryMode.RPG,
            rpg_marker_category=RpgTurnRetrievalCategory.ORDINARY_NARRATIVE,
            is_post_boundary=True,
            has_pending_roll_request=True,
        )
        assert decision.eligible is False  # type: ignore[attr-defined]


class TestBranchingEligibility:
    def test_branching_default_eligible(self) -> None:
        """Branching setup confirmations remain eligible as ordinary narrative
        (CRD Issue 16) — no special sidecar exclusion for Branching."""
        decision = _decide(story_mode=StoryMode.BRANCHING)
        assert decision.eligible is True  # type: ignore[attr-defined]
