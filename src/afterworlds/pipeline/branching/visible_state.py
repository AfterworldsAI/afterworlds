"""BranchingVisibleStateService — CRD Issue 16.

Builds the BranchingVisibleState snapshot surfaced in OrchestrationResult
on every DELIVERED BRANCHING-mode turn.  Reads from BranchingSessionState
plus the current turn's BranchingPassResult (if produced).

FREEFORM_ONLY turns call BranchingWriterService only when producing branch
cards; when the prose WriterService is used instead, ``branching_pass_result``
is None and ``last_branch_options`` / ``last_presentation_state`` are absent
from the snapshot.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from afterworlds.models.enums import BranchPresentationState, InteractionStyle
from afterworlds.pipeline.branching.models import BranchingVisibleState

if TYPE_CHECKING:
    from afterworlds.models.session import BranchingSessionState
    from afterworlds.pipeline.branching.models import BranchingPassResult


class BranchingVisibleStateService:
    """Builds BranchingVisibleState from session state and current pass result."""

    def build(
        self,
        session_state: BranchingSessionState,
        branching_pass_result: BranchingPassResult | None = None,
    ) -> BranchingVisibleState:
        """Return the Sojourner-visible branching snapshot.

        Args:
            session_state: Current BranchingSessionState (config axis).
            branching_pass_result: Output from BranchingWriterService for this
                turn, or None for FREEFORM_ONLY turns that used the prose Writer.

        Returns:
            BranchingVisibleState with code-derived ``freeform_available`` and
            all session config fields populated.

        Raises:
            ValueError: if ``session_state.interaction_style`` or
                ``session_state.branching_cadence`` is None (not yet configured).
        """
        if session_state.interaction_style is None:
            raise ValueError(
                "BranchingVisibleStateService.build called with interaction_style=None;"
                " session must be configured before building visible state."
            )
        if session_state.branching_cadence is None:
            raise ValueError(
                "BranchingVisibleStateService.build called with branching_cadence=None;"
                " session must be configured before building visible state."
            )

        freeform_available = (
            session_state.interaction_style is not InteractionStyle.TRUE_CYOA
        )

        last_branch_options = None
        last_presentation_state: BranchPresentationState | None = None

        if branching_pass_result is not None:
            last_branch_options = branching_pass_result.branch_options or None
            raw_ps = branching_pass_result.branch_presentation_state
            try:
                last_presentation_state = BranchPresentationState(raw_ps)
            except ValueError:
                last_presentation_state = None

        return BranchingVisibleState(
            interaction_style=session_state.interaction_style,
            branching_cadence=session_state.branching_cadence,
            branch_count_range=session_state.branch_count_range,
            freeform_available=freeform_available,
            length_preference=session_state.length_preference,
            last_branch_options=last_branch_options if last_branch_options else None,
            last_presentation_state=last_presentation_state,
        )


__all__ = ["BranchingVisibleStateService"]
