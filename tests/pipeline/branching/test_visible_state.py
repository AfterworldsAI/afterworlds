"""Tests for BranchingVisibleStateService — CRD Issue 16 Phase C."""

from __future__ import annotations

from uuid import uuid4

import pytest

from afterworlds.models.enums import (
    BranchCountRange,
    BranchingCadence,
    BranchingPlayStatus,
    BranchPresentationState,
    InteractionStyle,
    LengthPreference,
    PacingStage,
)
from afterworlds.models.session import BranchingSessionState
from afterworlds.pipeline.branching.models import (
    BranchingPassResult,
    BranchOption,
)
from afterworlds.pipeline.branching.visible_state import BranchingVisibleStateService


def _make_session_state(
    interaction_style: InteractionStyle = InteractionStyle.HYBRID,
    branching_cadence: BranchingCadence = BranchingCadence.BALANCED,
    branch_count_range: BranchCountRange | None = BranchCountRange.TWO_TO_THREE,
    length_preference: LengthPreference | None = LengthPreference.NOVELLA,
) -> BranchingSessionState:
    return BranchingSessionState(
        story_id=uuid4(),
        pacing_stage=PacingStage.ESCALATION,
        play_status=BranchingPlayStatus.IN_PLAY,
        interaction_style=interaction_style,
        branching_cadence=branching_cadence,
        branch_count_range=branch_count_range,
        length_preference=length_preference,
    )


def _make_pass_result(
    options: list[BranchOption] | None = None,
    presentation_state: str = "shown",
) -> BranchingPassResult:
    opts = (
        [
            BranchOption(option_id="opt_1", action_text="Take the bridge"),
            BranchOption(option_id="opt_2", action_text="Wade through the river"),
        ]
        if options is None
        else options
    )
    return BranchingPassResult(
        narrative_text="You stand at a crossing.",
        interaction_style=InteractionStyle.HYBRID,
        branching_cadence=BranchingCadence.BALANCED,
        length_preference=LengthPreference.NOVELLA,
        freeform_available=True,
        branch_count_range=BranchCountRange.TWO_TO_THREE,
        branch_options=opts,
        branch_presentation_state=presentation_state,
    )


class TestBranchingVisibleStateService:
    """BranchingVisibleStateService.build() returns typed, code-derived state."""

    def setup_method(self) -> None:
        self.svc = BranchingVisibleStateService()

    def test_hybrid_freeform_available_true(self) -> None:
        state = self.svc.build(_make_session_state(InteractionStyle.HYBRID))
        assert state.freeform_available is True

    def test_true_cyoa_freeform_available_false(self) -> None:
        state = self.svc.build(_make_session_state(InteractionStyle.TRUE_CYOA))
        assert state.freeform_available is False

    def test_freeform_only_freeform_available_true(self) -> None:
        state = self.svc.build(
            _make_session_state(InteractionStyle.FREEFORM_ONLY, branch_count_range=None)
        )
        assert state.freeform_available is True

    def test_session_fields_reflected(self) -> None:
        session = _make_session_state(
            interaction_style=InteractionStyle.TRUE_CYOA,
            branching_cadence=BranchingCadence.IMMERSIVE,
            branch_count_range=BranchCountRange.TWO_TO_FIVE,
            length_preference=LengthPreference.NOVEL,
        )
        state = self.svc.build(session)
        assert state.interaction_style is InteractionStyle.TRUE_CYOA
        assert state.branching_cadence is BranchingCadence.IMMERSIVE
        assert state.branch_count_range is BranchCountRange.TWO_TO_FIVE
        assert state.length_preference is LengthPreference.NOVEL

    def test_schema_version_is_one(self) -> None:
        state = self.svc.build(_make_session_state())
        assert state.schema_version == 1

    def test_no_pass_result_yields_no_last_options(self) -> None:
        state = self.svc.build(_make_session_state(), branching_pass_result=None)
        assert state.last_branch_options is None
        assert state.last_presentation_state is None

    def test_pass_result_populates_last_options(self) -> None:
        pass_result = _make_pass_result(presentation_state="shown")
        state = self.svc.build(_make_session_state(), branching_pass_result=pass_result)
        assert state.last_branch_options is not None
        assert len(state.last_branch_options) == 2
        assert state.last_branch_options[0].option_id == "opt_1"

    def test_pass_result_presentation_state_parsed(self) -> None:
        pass_result = _make_pass_result(presentation_state="held")
        state = self.svc.build(_make_session_state(), branching_pass_result=pass_result)
        assert state.last_presentation_state is BranchPresentationState.HELD

    def test_invalid_presentation_state_yields_none(self) -> None:
        pass_result = _make_pass_result(presentation_state="unknown_value")
        state = self.svc.build(_make_session_state(), branching_pass_result=pass_result)
        assert state.last_presentation_state is None

    def test_empty_branch_options_yields_no_last_options(self) -> None:
        pass_result = _make_pass_result(options=[], presentation_state="omitted")
        state = self.svc.build(_make_session_state(), branching_pass_result=pass_result)
        assert state.last_branch_options is None

    def test_none_interaction_style_raises(self) -> None:
        session = _make_session_state()
        session.interaction_style = None  # type: ignore[assignment]
        with pytest.raises(ValueError, match="interaction_style"):
            self.svc.build(session)

    def test_none_branching_cadence_raises(self) -> None:
        session = _make_session_state()
        session.branching_cadence = None  # type: ignore[assignment]
        with pytest.raises(ValueError, match="branching_cadence"):
            self.svc.build(session)
