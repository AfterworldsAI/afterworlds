"""Unit tests for Issue 16 models and validators — CRD Issue 16.

Coverage:
- PipelineDisposition.INTERACTION_REJECTED validator (required / forbidden fields).
- BranchingCadence is distinct from PacingStage (no overlapping values).
- BranchCountRange members cover all five configured ranges.
- InteractionStyle members.
- BranchingPlayStatus members.
- OrchestrationResult accepts INTERACTION_REJECTED with correct fields.
- InteractionRejectionReason enum values (four values).
- BranchPresentationState enum values.
- BranchingVisibleState schema.
- BranchTree dormancy (must not be used, repurposed, or deleted).
- ALLOWED_RANGES_BY_STYLE per-style mapping.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from afterworlds.models.enums import (
    BranchCountRange,
    BranchingCadence,
    BranchingPlayStatus,
    IntentType,
    InteractionRejectionReason,
    InteractionStyle,
    PacingStage,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.pipeline._refusal import PassIdentifier, ProviderRefusal
from afterworlds.pipeline.orchestrator.models import (
    OrchestrationResult,
    OrchestratorError,
    PipelineDisposition,
)

# ---------------------------------------------------------------------------
# Minimal OrchestrationResult field kit for INTERACTION_REJECTED
# ---------------------------------------------------------------------------


def _base_intent(
    intent: IntentType = IntentType.IN_CHARACTER_ACTION,
) -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=intent,
        confidence=0.95,
        raw_input="I cross the bridge",
        ambiguous=False,
    )


_DEFAULT_REASON = InteractionRejectionReason.INVALID_FOR_INTERACTION_STYLE


def _interaction_rejected(
    reason: InteractionRejectionReason = _DEFAULT_REASON,
    message: str = "True CYOA mode requires explicit branch selection.",
    **overrides: object,
) -> OrchestrationResult:
    """Build a minimal valid INTERACTION_REJECTED OrchestrationResult."""
    kwargs: dict = {
        "disposition": PipelineDisposition.INTERACTION_REJECTED,
        "delivered_output": None,
        "turn_id": None,
        "intent_classification": _base_intent(),
        "interaction_rejection_reason": reason,
        "interaction_rejection_message": message,
        "total_latency_ms": 5,
        "pass_latency_breakdown": {},
    }
    kwargs.update(overrides)
    return OrchestrationResult(**kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Test: INTERACTION_REJECTED validator
# ---------------------------------------------------------------------------


class TestInteractionRejectedValidator:
    """OrchestrationResult enforces field invariants for INTERACTION_REJECTED."""

    def test_valid_construction_succeeds(self) -> None:
        result = _interaction_rejected()
        assert result.disposition is PipelineDisposition.INTERACTION_REJECTED
        assert (
            result.interaction_rejection_reason
            is InteractionRejectionReason.INVALID_FOR_INTERACTION_STYLE
        )
        assert result.interaction_rejection_message is not None

    def test_none_reason_raises(self) -> None:
        with pytest.raises(OrchestratorError, match="interaction_rejection_reason"):
            _interaction_rejected(reason=None)  # type: ignore[arg-type]

    def test_empty_message_raises(self) -> None:
        with pytest.raises(OrchestratorError, match="interaction_rejection_message"):
            _interaction_rejected(message="")

    def test_none_message_raises(self) -> None:
        with pytest.raises(OrchestratorError, match="interaction_rejection_message"):
            _interaction_rejected(message=None)  # type: ignore[arg-type]

    def test_turn_id_present_raises(self) -> None:
        with pytest.raises(OrchestratorError, match="turn_id"):
            _interaction_rejected(turn_id=uuid4())

    def test_delivered_output_present_raises(self) -> None:
        with pytest.raises(OrchestratorError, match="delivered_output"):
            _interaction_rejected(delivered_output="some output")

    def test_planner_result_present_raises(self) -> None:
        from afterworlds.pipeline.planner.models import PlannerOutput, PlannerResult

        planner_result = PlannerResult(
            plan=PlannerOutput(
                scene_goal="reach the bridge",
                next_beat="cross safely",
                facts_needed=["bridge condition"],
            ),
            model_identifier="fake-model",
            latency_ms=5,
            input_token_count=None,
            output_token_count=None,
            cache_read_token_count=None,
            cache_creation_token_count=None,
        )
        with pytest.raises(OrchestratorError, match="planner_result absent"):
            _interaction_rejected(planner_result=planner_result)

    def test_writer_result_present_raises(self) -> None:
        from uuid import uuid4

        from afterworlds.pipeline.writer.models import WriterResult

        writer_result = WriterResult(
            turn_id=uuid4(),
            assistant_output="narrative",
            model_identifier="fake-model",
            latency_ms=10,
            input_token_count=None,
            output_token_count=None,
            cache_read_token_count=None,
            cache_creation_token_count=None,
        )
        with pytest.raises(OrchestratorError, match="writer_result absent"):
            _interaction_rejected(writer_result=writer_result)

    def test_pending_roll_redirect_message_present_raises(self) -> None:
        with pytest.raises(OrchestratorError, match="pending_roll_redirect_message"):
            _interaction_rejected(
                pending_roll_redirect_message="Please roll your attack."
            )

    def test_provider_refusal_present_raises(self) -> None:
        refusal = ProviderRefusal(
            provider="fake",
            pass_identifier=PassIdentifier.WRITER,
            coarse_reason="policy",
        )
        with pytest.raises(OrchestratorError, match="provider_refusal"):
            _interaction_rejected(provider_refusal=refusal)

    def test_pipeline_error_summary_present_raises(self) -> None:
        with pytest.raises(OrchestratorError, match="pipeline_error_summary"):
            _interaction_rejected(pipeline_error_summary="something broke")


# ---------------------------------------------------------------------------
# Test: PipelineDisposition contains INTERACTION_REJECTED
# ---------------------------------------------------------------------------


class TestPipelineDispositionEnum:
    def test_interaction_rejected_present(self) -> None:
        assert "interaction_rejected" in [d.value for d in PipelineDisposition]

    def test_all_nine_dispositions_present(self) -> None:
        values = {d.value for d in PipelineDisposition}
        assert values == {
            "delivered",
            "ooc_handled",
            "blocked_input_safety",
            "blocked_output_safety",
            "blocked_contradiction",
            "blocked_pending_roll",
            "interaction_rejected",
            "refused_by_provider",
            "pipeline_error",
        }


# ---------------------------------------------------------------------------
# Test: BranchingCadence is distinct from PacingStage
# ---------------------------------------------------------------------------


class TestBranchingCadenceDistinctFromPacingStage:
    """BranchingCadence and PacingStage are orthogonal — no overlapping values."""

    def test_no_overlapping_values(self) -> None:
        cadence_values = {c.value for c in BranchingCadence}
        pacing_values = {p.value for p in PacingStage}
        assert cadence_values.isdisjoint(
            pacing_values
        ), f"Overlap detected: {cadence_values & pacing_values}"

    def test_branching_cadence_members(self) -> None:
        assert BranchingCadence.INTERACTIVE.value == "interactive"
        assert BranchingCadence.BALANCED.value == "balanced"
        assert BranchingCadence.IMMERSIVE.value == "immersive"

    def test_pacing_stage_members_unchanged(self) -> None:
        assert PacingStage.SETUP.value == "setup"
        assert PacingStage.ESCALATION.value == "escalation"
        assert PacingStage.REVERSAL.value == "reversal"
        assert PacingStage.CLIMAX.value == "climax"
        assert PacingStage.AFTERMATH.value == "aftermath"


# ---------------------------------------------------------------------------
# Test: BranchCountRange values
# ---------------------------------------------------------------------------


class TestBranchCountRangeValues:
    def test_all_five_ranges(self) -> None:
        assert BranchCountRange.ONE_TO_TWO.value == "1-2"
        assert BranchCountRange.TWO_TO_THREE.value == "2-3"
        assert BranchCountRange.THREE_TO_FOUR.value == "3-4"
        assert BranchCountRange.TWO_TO_FOUR.value == "2-4"
        assert BranchCountRange.TWO_TO_FIVE.value == "2-5"

    def test_five_members(self) -> None:
        assert len(list(BranchCountRange)) == 5


# ---------------------------------------------------------------------------
# Test: InteractionStyle values
# ---------------------------------------------------------------------------


class TestInteractionStyleValues:
    def test_three_styles(self) -> None:
        assert InteractionStyle.FREEFORM_ONLY.value == "freeform_only"
        assert InteractionStyle.HYBRID.value == "hybrid"
        assert InteractionStyle.TRUE_CYOA.value == "true_cyoa"

    def test_three_members(self) -> None:
        assert len(list(InteractionStyle)) == 3


# ---------------------------------------------------------------------------
# Test: BranchingPlayStatus values
# ---------------------------------------------------------------------------


class TestBranchingPlayStatusValues:
    def test_two_statuses(self) -> None:
        assert BranchingPlayStatus.SETUP.value == "setup"
        assert BranchingPlayStatus.IN_PLAY.value == "in_play"


# ---------------------------------------------------------------------------
# Test: InteractionRejectionReason enum
# ---------------------------------------------------------------------------


class TestInteractionRejectionReasonEnum:
    def test_four_members(self) -> None:
        values = {r.value for r in InteractionRejectionReason}
        assert values == {
            "invalid_for_interaction_style",
            "invalid_branch_selection",
            "material_branch_rewrite",
            "canon_or_genre_contradiction",
        }

    def test_is_str_enum(self) -> None:
        assert isinstance(InteractionRejectionReason.INVALID_BRANCH_SELECTION, str)


# ---------------------------------------------------------------------------
# Test: SelectedBranchContext
# ---------------------------------------------------------------------------


class TestSelectedBranchContext:
    def test_accepts_valid_fields(self) -> None:
        from afterworlds.pipeline.branching.models import SelectedBranchContext

        ctx = SelectedBranchContext(
            option_id="opt_1",
            action_text="Take the bridge",
            annotation="but stop for the sword",
        )
        assert ctx.option_id == "opt_1"
        assert ctx.action_text == "Take the bridge"
        assert ctx.annotation == "but stop for the sword"

    def test_annotation_optional(self) -> None:
        from afterworlds.pipeline.branching.models import SelectedBranchContext

        ctx = SelectedBranchContext(option_id="opt_2", action_text="Wade the river")
        assert ctx.annotation is None

    def test_extra_fields_forbidden(self) -> None:
        from pydantic import ValidationError

        from afterworlds.pipeline.branching.models import SelectedBranchContext

        with pytest.raises(ValidationError):
            SelectedBranchContext(  # type: ignore[call-arg]
                option_id="opt_1",
                action_text="Take the bridge",
                unknown_field="boom",
            )


# ---------------------------------------------------------------------------
# Test: BranchingConfigUpdate
# ---------------------------------------------------------------------------


class TestBranchingConfigUpdate:
    def test_all_none_is_valid(self) -> None:
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        update = BranchingConfigUpdate()
        assert update.interaction_style is None
        assert update.branching_cadence is None
        assert update.branch_count_range is None
        assert update.length_preference is None

    def test_accepts_valid_interaction_style(self) -> None:
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        update = BranchingConfigUpdate(interaction_style=InteractionStyle.HYBRID)
        assert update.interaction_style is InteractionStyle.HYBRID

    def test_accepts_valid_branch_count_range(self) -> None:
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        update = BranchingConfigUpdate(branch_count_range=BranchCountRange.TWO_TO_THREE)
        assert update.branch_count_range is BranchCountRange.TWO_TO_THREE

    def test_extra_fields_forbidden(self) -> None:
        from pydantic import ValidationError

        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        with pytest.raises(ValidationError):
            BranchingConfigUpdate(unknown_field="boom")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Test: BranchPresentationState enum
# ---------------------------------------------------------------------------


class TestBranchPresentationStateEnum:
    def test_three_members(self) -> None:
        from afterworlds.models.enums import BranchPresentationState

        assert BranchPresentationState.SHOWN.value == "shown"
        assert BranchPresentationState.HELD.value == "held"
        assert BranchPresentationState.OMITTED.value == "omitted"

    def test_disjoint_from_branching_play_status(self) -> None:
        from afterworlds.models.enums import BranchPresentationState

        ps_vals = {v.value for v in BranchPresentationState}
        bps_vals = {v.value for v in BranchingPlayStatus}
        assert ps_vals.isdisjoint(bps_vals)


# ---------------------------------------------------------------------------
# Test: BranchingVisibleState schema
# ---------------------------------------------------------------------------


class TestBranchingVisibleState:
    def test_schema_version_defaults_to_1(self) -> None:
        from afterworlds.pipeline.branching.models import BranchingVisibleState

        vs = BranchingVisibleState(
            interaction_style=InteractionStyle.HYBRID,
            branching_cadence=BranchingCadence.BALANCED,
            branch_count_range=BranchCountRange.TWO_TO_THREE,
            freeform_available=True,
            length_preference=None,
        )
        assert vs.schema_version == 1

    def test_extra_fields_forbidden(self) -> None:
        import pytest
        from pydantic import ValidationError

        from afterworlds.pipeline.branching.models import BranchingVisibleState

        with pytest.raises(ValidationError):
            BranchingVisibleState(  # type: ignore[call-arg]
                interaction_style=InteractionStyle.HYBRID,
                branching_cadence=BranchingCadence.BALANCED,
                branch_count_range=None,
                freeform_available=True,
                length_preference=None,
                unexpected_field="boom",
            )


# ---------------------------------------------------------------------------
# Test: BranchTree dormancy
# ---------------------------------------------------------------------------


class TestBranchTreeDormancy:
    """BranchTree must remain dormant: not used, repurposed, or deleted (ADR-016)."""

    def test_branch_tree_type_exists(self) -> None:
        from afterworlds.models.session import BranchTree

        assert BranchTree is not None

    def test_branch_tree_is_default_on_session(self) -> None:
        from afterworlds.models.enums import PacingStage
        from afterworlds.models.session import BranchingSessionState, BranchTree

        state = BranchingSessionState(
            story_id=uuid4(),
            pacing_stage=PacingStage.SETUP,
        )
        assert isinstance(state.branch_tree, BranchTree)

    def test_branch_tree_has_no_active_children(self) -> None:
        from afterworlds.models.session import BranchTree

        tree = BranchTree()
        assert not hasattr(tree, "nodes") or len(getattr(tree, "nodes", [])) == 0


# ---------------------------------------------------------------------------
# Test: ALLOWED_RANGES_BY_STYLE
# ---------------------------------------------------------------------------


class TestAllowedRangesByStyle:
    def test_freeform_only_has_no_range(self) -> None:
        from afterworlds.pipeline.branching.config import ALLOWED_RANGES_BY_STYLE

        assert ALLOWED_RANGES_BY_STYLE[InteractionStyle.FREEFORM_ONLY] is None

    def test_hybrid_allowed_ranges(self) -> None:
        from afterworlds.pipeline.branching.config import ALLOWED_RANGES_BY_STYLE

        hybrid_ranges = ALLOWED_RANGES_BY_STYLE[InteractionStyle.HYBRID]
        assert hybrid_ranges is not None
        assert BranchCountRange.ONE_TO_TWO in hybrid_ranges
        assert BranchCountRange.TWO_TO_THREE in hybrid_ranges
        assert BranchCountRange.THREE_TO_FOUR in hybrid_ranges
        assert BranchCountRange.TWO_TO_FOUR not in hybrid_ranges
        assert BranchCountRange.TWO_TO_FIVE not in hybrid_ranges

    def test_true_cyoa_allowed_ranges(self) -> None:
        from afterworlds.pipeline.branching.config import ALLOWED_RANGES_BY_STYLE

        cyoa_ranges = ALLOWED_RANGES_BY_STYLE[InteractionStyle.TRUE_CYOA]
        assert cyoa_ranges is not None
        assert BranchCountRange.TWO_TO_THREE in cyoa_ranges
        assert BranchCountRange.TWO_TO_FOUR in cyoa_ranges
        assert BranchCountRange.TWO_TO_FIVE in cyoa_ranges
        assert BranchCountRange.ONE_TO_TWO not in cyoa_ranges
        assert BranchCountRange.THREE_TO_FOUR not in cyoa_ranges


# ---------------------------------------------------------------------------
# Test: BranchingWriterConfig.from_env
# ---------------------------------------------------------------------------


class TestBranchingWriterConfigFromEnv:
    def test_defaults_when_env_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from afterworlds.pipeline.branching.config import BranchingWriterConfig

        monkeypatch.delenv("AFTERWORLDS_BRANCHING_WRITER_MODEL", raising=False)
        monkeypatch.delenv("AFTERWORLDS_BRANCHING_WRITER_API_KEY_ENV", raising=False)
        monkeypatch.delenv("AFTERWORLDS_BRANCHING_WRITER_EXTENDED_TTL", raising=False)
        cfg = BranchingWriterConfig.from_env()
        assert cfg.model != ""
        assert cfg.api_key_env == "ANTHROPIC_API_KEY"
        assert cfg.extended_ttl is True

    def test_model_override_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from afterworlds.pipeline.branching.config import BranchingWriterConfig

        monkeypatch.setenv("AFTERWORLDS_BRANCHING_WRITER_MODEL", "custom-model")
        cfg = BranchingWriterConfig.from_env()
        assert cfg.model == "custom-model"

    def test_extended_ttl_false_when_set_to_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from afterworlds.pipeline.branching.config import BranchingWriterConfig

        monkeypatch.setenv("AFTERWORLDS_BRANCHING_WRITER_EXTENDED_TTL", "false")
        cfg = BranchingWriterConfig.from_env()
        assert cfg.extended_ttl is False
