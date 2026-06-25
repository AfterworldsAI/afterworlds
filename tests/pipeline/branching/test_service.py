"""Unit tests for BranchingWriterService — CRD Issue 16.

Coverage:
- Code-owns-affordances: option_id sequential, style/cadence/freeform from session.
- freeform_available derivation (HYBRID → True, TRUE_CYOA → False).
- branch_count_range validation: within bounds, below min, above max, unknown range,
  None range (no validation).
- Fail-closed error paths: no tool block, wrong tool name, schema failure.
- ProviderRefusalError propagates unchanged.
- None interaction_style / None branching_cadence raise BranchingPassError.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import (
    BranchCountRange,
    BranchingCadence,
    BranchingPlayStatus,
    IntentType,
    InteractionStyle,
    LengthPreference,
    PacingStage,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.session import BranchingSessionState
from afterworlds.models.story_bible import StoryBibleContext
from afterworlds.pipeline._refusal import (
    PassIdentifier,
    ProviderRefusal,
    ProviderRefusalError,
)
from afterworlds.pipeline.branching.caller import PRODUCE_BRANCH_OUTPUT_TOOL_NAME
from afterworlds.pipeline.branching.config import BranchingWriterConfig
from afterworlds.pipeline.branching.models import BranchingPassError
from afterworlds.pipeline.branching.service import BranchingWriterService
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderToolCallPart,
)

_STORY_ID = uuid4()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config() -> BranchingWriterConfig:
    return BranchingWriterConfig(
        model="claude-sonnet-4-6",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=False,
    )


def _make_session(
    interaction_style: InteractionStyle | None = InteractionStyle.HYBRID,
    branching_cadence: BranchingCadence | None = BranchingCadence.BALANCED,
    branch_count_range: BranchCountRange | None = BranchCountRange.TWO_TO_THREE,
    length_preference: LengthPreference | None = LengthPreference.NOVELLA,
) -> BranchingSessionState:
    return BranchingSessionState(
        story_id=_STORY_ID,
        pacing_stage=PacingStage.ESCALATION,
        interaction_style=interaction_style,
        branching_cadence=branching_cadence,
        branch_count_range=branch_count_range,
        length_preference=length_preference,
        play_status=BranchingPlayStatus.IN_PLAY,
    )


def _make_assembled() -> AssembledContext:
    sbc = StoryBibleContext(
        story_id=_STORY_ID,
        setting=None,
        cast=(),
        locked_facts=(),
        forbidden_facts=(),
        relationship_ledger=(),
        active_plot_threads=(),
        events=(),
    )
    prefix = StablePrefix(system_prompt="branching mode test", story_bible_context=sbc)
    intent = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.9,
        raw_input="I take the left path",
        ambiguous=False,
    )
    suffix = VolatileSuffix(
        recent_turns=[],
        current_input="I take the left path",
        classified_intent=intent,
    )
    return AssembledContext(
        stable_prefix=prefix,
        volatile_suffix=suffix,
        pass_forward_ledger=PassForwardLedger(),
    )


def _make_result(tool_input: dict) -> ProviderCallResult:  # type: ignore[type-arg]
    return ProviderCallResult(
        pass_id=PipelinePassId.BRANCHING_WRITER,
        provider_name="fake",
        model_identifier="fake-model",
        model_tier=ModelTier.SONNET,
        content_parts=[
            ProviderToolCallPart(
                tool_name=PRODUCE_BRANCH_OUTPUT_TOOL_NAME,
                tool_input=tool_input,
            )
        ],
        input_token_count=100,
        output_token_count=50,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        cache_warmed=False,
        latency_ms=10,
    )


class _FakeProvider:
    """Stub ProviderAdapter that returns a fixed tool call result."""

    def __init__(self, tool_input: dict) -> None:  # type: ignore[type-arg]
        self._tool_input = tool_input

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        return _make_result(self._tool_input)

    @property
    def provider_name(self) -> str:
        return "fake"


class _RefusingProvider:
    """Stub ProviderAdapter that raises ProviderRefusalError."""

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        raise ProviderRefusalError(
            ProviderRefusal(
                provider="fake",
                pass_identifier=PassIdentifier.BRANCHING_WRITER,
                coarse_reason="policy",
            )
        )

    @property
    def provider_name(self) -> str:
        return "fake"


class _FailingProvider:
    """Stub ProviderAdapter that raises a generic exception."""

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        raise RuntimeError("network error")

    @property
    def provider_name(self) -> str:
        return "fake"


class _NoToolProvider:
    """Returns a ProviderCallResult with no tool-use blocks."""

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        return ProviderCallResult(
            pass_id=PipelinePassId.BRANCHING_WRITER,
            provider_name="fake",
            model_identifier="fake-model",
            model_tier=ModelTier.SONNET,
            content_parts=[],
            input_token_count=50,
            output_token_count=10,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=5,
        )

    @property
    def provider_name(self) -> str:
        return "fake"


class _WrongToolProvider:
    """Returns a ProviderCallResult with the wrong tool name."""

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        return ProviderCallResult(
            pass_id=PipelinePassId.BRANCHING_WRITER,
            provider_name="fake",
            model_identifier="fake-model",
            model_tier=ModelTier.SONNET,
            content_parts=[
                ProviderToolCallPart(
                    tool_name="wrong_tool_name",
                    tool_input={"narrative_text": "text"},
                )
            ],
            input_token_count=50,
            output_token_count=10,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=5,
        )

    @property
    def provider_name(self) -> str:
        return "fake"


def _valid_tool_input(options: list[str] | None = None) -> dict:  # type: ignore[type-arg]
    if options is None:
        options = ["Cross the rope bridge", "Take the forest path"]
    return {
        "narrative_text": "The path splits ahead.",
        "branch_options_text": options,
        "branch_presentation_state": "shown",
        "pacing_stage_hint": None,
    }


# ---------------------------------------------------------------------------
# Test: code-owns-affordances (option_id sequential, style/cadence from session)
# ---------------------------------------------------------------------------


class TestCodeOwnsAffordances:
    """option_id is code-assigned sequential; affordances come from session state."""

    def test_option_ids_sequential(self) -> None:
        options = ["Cross the bridge", "Take the tunnel", "Turn back"]
        session = _make_session(
            interaction_style=InteractionStyle.TRUE_CYOA,
            branch_count_range=BranchCountRange.TWO_TO_THREE,
        )
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input(options)),
        )
        assert [o.option_id for o in result.branch_options] == [
            "opt_1",
            "opt_2",
            "opt_3",
        ]

    def test_action_text_from_model(self) -> None:
        options = ["Cross the bridge", "Take the tunnel"]
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input(options)),
        )
        assert [o.action_text for o in result.branch_options] == options

    def test_interaction_style_from_session_not_model(self) -> None:
        session = _make_session(interaction_style=InteractionStyle.HYBRID)
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input()),
        )
        assert result.interaction_style is InteractionStyle.HYBRID

    def test_branching_cadence_from_session(self) -> None:
        session = _make_session(branching_cadence=BranchingCadence.IMMERSIVE)
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input()),
        )
        assert result.branching_cadence is BranchingCadence.IMMERSIVE

    def test_branch_count_range_from_session(self) -> None:
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input()),
        )
        assert result.branch_count_range is BranchCountRange.TWO_TO_THREE

    def test_length_preference_from_session(self) -> None:
        session = _make_session(length_preference=LengthPreference.SHORT_STORY)
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input()),
        )
        assert result.length_preference is LengthPreference.SHORT_STORY


# ---------------------------------------------------------------------------
# Test: freeform_available derivation
# ---------------------------------------------------------------------------


class TestFreeformAvailable:
    """freeform_available is derived from interaction_style by code."""

    def test_hybrid_freeform_available_true(self) -> None:
        session = _make_session(interaction_style=InteractionStyle.HYBRID)
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input()),
        )
        assert result.freeform_available is True

    def test_true_cyoa_freeform_available_false(self) -> None:
        session = _make_session(
            interaction_style=InteractionStyle.TRUE_CYOA,
            branch_count_range=BranchCountRange.TWO_TO_THREE,
        )
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input()),
        )
        assert result.freeform_available is False


# ---------------------------------------------------------------------------
# Test: branch_count_range validation (fail-closed, never clamp/pad/truncate)
# ---------------------------------------------------------------------------


class TestBranchCountRangeValidation:
    """Fail-closed validation: out-of-range count raises BranchingPassError."""

    def test_within_range_passes(self) -> None:
        # 2-3 range: 2 options is valid
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input(["Option A", "Option B"])),
        )
        assert len(result.branch_options) == 2

    def test_below_minimum_raises(self) -> None:
        # 2-3 range: 1 option is invalid
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="1 branch option"):
            service.write(
                _make_assembled(),
                session,
                provider=_FakeProvider(_valid_tool_input(["Only one option"])),
            )

    def test_above_maximum_raises(self) -> None:
        # 2-3 range: 5 options is invalid
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="5 branch option"):
            service.write(
                _make_assembled(),
                session,
                provider=_FakeProvider(_valid_tool_input(["A", "B", "C", "D", "E"])),
            )

    def test_none_range_skips_validation(self) -> None:
        # None branch_count_range: any count is accepted
        session = _make_session(branch_count_range=None)
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input(["A", "B", "C", "D", "E"])),
        )
        assert len(result.branch_options) == 5

    def test_three_four_range_max_boundary(self) -> None:
        # 3-4 range: 4 options is valid
        session = _make_session(branch_count_range=BranchCountRange.THREE_TO_FOUR)
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input(["A", "B", "C", "D"])),
        )
        assert len(result.branch_options) == 4

    def test_two_five_range_extreme(self) -> None:
        # 2-5 range: 5 options is valid
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_FIVE)
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(_valid_tool_input(["A", "B", "C", "D", "E"])),
        )
        assert len(result.branch_options) == 5


# ---------------------------------------------------------------------------
# Test: fail-closed on None session config
# ---------------------------------------------------------------------------


class TestNullSessionConfigRaises:
    """interaction_style=None or branching_cadence=None raises BranchingPassError."""

    def test_interaction_style_none_raises(self) -> None:
        session = _make_session(interaction_style=None)
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="interaction_style=None"):
            service.write(
                _make_assembled(),
                session,
                provider=_FakeProvider(_valid_tool_input()),
            )

    def test_branching_cadence_none_raises(self) -> None:
        session = _make_session(branching_cadence=None)
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="branching_cadence=None"):
            service.write(
                _make_assembled(),
                session,
                provider=_FakeProvider(_valid_tool_input()),
            )


# ---------------------------------------------------------------------------
# Test: provider failure paths (fail-closed)
# ---------------------------------------------------------------------------


class TestProviderFailurePaths:
    """Provider errors are wrapped or propagated unchanged."""

    def test_refusal_propagates_unchanged(self) -> None:
        session = _make_session()
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(ProviderRefusalError):
            service.write(_make_assembled(), session, provider=_RefusingProvider())

    def test_generic_exception_wrapped_in_branching_pass_error(self) -> None:
        session = _make_session()
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="provider call failed"):
            service.write(_make_assembled(), session, provider=_FailingProvider())

    def test_no_tool_block_raises(self) -> None:
        session = _make_session()
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="missing tool-use block"):
            service.write(_make_assembled(), session, provider=_NoToolProvider())

    def test_wrong_tool_name_raises(self) -> None:
        session = _make_session()
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="unexpected tool name"):
            service.write(_make_assembled(), session, provider=_WrongToolProvider())

    def test_invalid_schema_raises(self) -> None:
        # Missing required 'branch_options_text' field → schema validation fails
        session = _make_session()
        service = BranchingWriterService(config=_make_config())
        bad_input = {
            "narrative_text": "Some narrative",
            # branch_options_text missing
            "branch_presentation_state": "shown",
        }
        with pytest.raises(BranchingPassError, match="schema validation"):
            service.write(
                _make_assembled(),
                session,
                provider=_FakeProvider(bad_input),
            )
