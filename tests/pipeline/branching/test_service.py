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
from afterworlds.pipeline.branching.models import (
    BranchingPassError,
    SelectedBranchContext,
)
from afterworlds.pipeline.branching.service import (
    BranchingWriterService,
    _validate_branch_count,
)
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


class _MustNotCallProvider:
    """Stub ProviderAdapter that fails the test if call() is ever reached.

    Used to prove a fail-closed guard fires before any provider spend.
    """

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        raise AssertionError(
            "provider.call() must not be reached when the writer fails closed"
        )

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

    def test_hybrid_none_range_fails_closed(self) -> None:
        # HYBRID branch cards require a configured range; None is a misroute and
        # must fail closed before the provider call (Round 5 Fix 2).
        session = _make_session(
            interaction_style=InteractionStyle.HYBRID, branch_count_range=None
        )
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="branch_count_range"):
            service.write(
                _make_assembled(),
                session,
                provider=_MustNotCallProvider(),
            )

    def test_true_cyoa_none_range_fails_closed(self) -> None:
        # TRUE_CYOA branch cards require a configured range; None must fail closed
        # before the provider call (Round 5 Fix 2).
        session = _make_session(
            interaction_style=InteractionStyle.TRUE_CYOA, branch_count_range=None
        )
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="branch_count_range"):
            service.write(
                _make_assembled(),
                session,
                provider=_MustNotCallProvider(),
            )

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
        # 2-5 range: 5 options is valid.  "2-5" is a TRUE_CYOA-allowed range
        # (not allowed for HYBRID), so this numeric-extreme case must use
        # TRUE_CYOA to remain a compatible persisted style/range combination.
        session = _make_session(
            interaction_style=InteractionStyle.TRUE_CYOA,
            branch_count_range=BranchCountRange.TWO_TO_FIVE,
        )
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


# ---------------------------------------------------------------------------
# Helpers for request inspection tests
# ---------------------------------------------------------------------------


class _CapturingProvider:
    """FakeProvider that records the last ProviderCallRequest."""

    def __init__(self, tool_input: dict) -> None:  # type: ignore[type-arg]
        self._tool_input = tool_input
        self.last_request: ProviderCallRequest | None = None

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        self.last_request = request
        return _make_result(self._tool_input)

    @property
    def provider_name(self) -> str:
        return "fake"


def _all_block_text(request: ProviderCallRequest) -> str:
    return "\n".join(b.text for b in request.rendered_blocks)


def _stable_block_text(request: ProviderCallRequest) -> str:
    # Stable-prefix blocks are identified by the cache-breakpoint signal.
    # Only the last stable block has has_cache_breakpoint=True.  Collect
    # everything up to AND including that block as the "stable region."
    blocks = request.rendered_blocks
    breakpoint_idx = next(
        (i for i, b in enumerate(blocks) if b.has_cache_breakpoint), -1
    )
    if breakpoint_idx == -1:
        return ""
    return "\n".join(b.text for b in blocks[: breakpoint_idx + 1])


# ---------------------------------------------------------------------------
# Test: Fix 1 — SelectedBranchContext threaded into BranchingWriterService
# ---------------------------------------------------------------------------


class TestSelectedBranchContextRendering:
    """SelectedBranchContext appears as volatile block in the provider payload."""

    def test_action_text_and_annotation_in_rendered_blocks(self) -> None:
        sbc = SelectedBranchContext(
            option_id="opt_2",
            action_text="Cross the bridge",
            annotation="cautiously",
        )
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        provider = _CapturingProvider(_valid_tool_input())
        service = BranchingWriterService(config=_make_config())
        service.write(
            _make_assembled(),
            session,
            provider=provider,
            selected_branch_context=sbc,
        )
        assert provider.last_request is not None
        text = _all_block_text(provider.last_request)
        assert "Cross the bridge" in text
        assert "cautiously" in text

    def test_selected_context_not_in_stable_prefix_blocks(self) -> None:
        sbc = SelectedBranchContext(
            option_id="opt_1",
            action_text="Cross the bridge",
            annotation="cautiously",
        )
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        provider = _CapturingProvider(_valid_tool_input())
        service = BranchingWriterService(
            config=BranchingWriterConfig(
                model="claude-sonnet-4-6",
                api_key_env="ANTHROPIC_API_KEY",
                extended_ttl=True,
            )
        )
        service.write(
            _make_assembled(),
            session,
            provider=provider,
            selected_branch_context=sbc,
        )
        assert provider.last_request is not None
        stable_text = _stable_block_text(provider.last_request)
        assert "Cross the bridge" not in stable_text
        assert "cautiously" not in stable_text

    def test_annotation_line_absent_when_none(self) -> None:
        sbc = SelectedBranchContext(
            option_id="opt_1",
            action_text="Cross the bridge",
            annotation=None,
        )
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        provider = _CapturingProvider(_valid_tool_input())
        service = BranchingWriterService(config=_make_config())
        service.write(
            _make_assembled(),
            session,
            provider=provider,
            selected_branch_context=sbc,
        )
        assert provider.last_request is not None
        text = _all_block_text(provider.last_request)
        assert "annotation:" not in text
        assert "Cross the bridge" in text

    def test_no_selected_context_no_selected_branch_block(self) -> None:
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        provider = _CapturingProvider(_valid_tool_input())
        service = BranchingWriterService(config=_make_config())
        service.write(
            _make_assembled(),
            session,
            provider=provider,
        )
        assert provider.last_request is not None
        text = _all_block_text(provider.last_request)
        assert "[Selected Branch]" not in text


# ---------------------------------------------------------------------------
# Test: Round 8 Finding 2 — no duplicate Branching mode contract
# ---------------------------------------------------------------------------


class TestNoDuplicateModeContract:
    """The Branching mode contract is injected exactly once per provider call.

    Regression for PR #112 Round 8: BranchingWriter previously emitted the
    BRANCHING mode contract twice — once as its own ``_system_prompt`` (loaded
    from ``branching_mode.md``) and again via ``stable_prefix.system_prompt``
    (the same file, assembled once by ContextBuilder).  The pass now mirrors the
    prose WriterService convention: the stable-prefix mode contract only.  The
    sentinel "branching mode test" is the stable-prefix system_prompt set by
    ``_make_assembled`` and stands in for ``branching_mode.md`` here.
    """

    _SENTINEL = "branching mode test"  # == stable_prefix.system_prompt

    def _capture(self, session: BranchingSessionState) -> ProviderCallRequest:
        provider = _CapturingProvider(_valid_tool_input())
        service = BranchingWriterService(config=_make_config())
        service.write(_make_assembled(), session, provider=provider)
        assert provider.last_request is not None
        return provider.last_request

    def test_hybrid_contract_appears_exactly_once(self) -> None:
        request = self._capture(
            _make_session(interaction_style=InteractionStyle.HYBRID)
        )
        system_count = sum(b.text.count(self._SENTINEL) for b in request.system_blocks)
        rendered_count = sum(
            b.text.count(self._SENTINEL) for b in request.rendered_blocks
        )
        assert system_count == 1
        # The mode contract must never be duplicated into the user-message region.
        assert rendered_count == 0

    def test_true_cyoa_contract_appears_exactly_once(self) -> None:
        request = self._capture(
            _make_session(
                interaction_style=InteractionStyle.TRUE_CYOA,
                branch_count_range=BranchCountRange.TWO_TO_THREE,
            )
        )
        system_count = sum(b.text.count(self._SENTINEL) for b in request.system_blocks)
        assert system_count == 1

    def test_stable_prefix_contract_is_the_single_system_block(self) -> None:
        request = self._capture(_make_session())
        # Stable prefix included exactly once, as the sole system block.
        assert len(request.system_blocks) == 1
        assert request.system_blocks[0].text == self._SENTINEL

    def test_forced_tool_and_output_contract_still_present(self) -> None:
        request = self._capture(_make_session())
        # Output-format guidance survives via the forced-tool definition.
        assert request.forced_tool_name == PRODUCE_BRANCH_OUTPUT_TOOL_NAME
        assert any(
            t.name == PRODUCE_BRANCH_OUTPUT_TOOL_NAME for t in request.tool_definitions
        )


# ---------------------------------------------------------------------------
# Test: Fix 2 — held/omitted branch_presentation_state allows empty options
# ---------------------------------------------------------------------------


class TestHeldOmittedPresentationState:
    """held/omitted with [] passes; held/omitted with non-empty fails-closed."""

    def test_held_with_empty_options_passes(self) -> None:
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        tool_input = {
            "narrative_text": "The story continues…",
            "branch_options_text": [],
            "branch_presentation_state": "held",
            "pacing_stage_hint": None,
        }
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(tool_input),
        )
        assert result.branch_options == []

    def test_omitted_with_empty_options_passes(self) -> None:
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        tool_input = {
            "narrative_text": "The story continues…",
            "branch_options_text": [],
            "branch_presentation_state": "omitted",
            "pacing_stage_hint": None,
        }
        service = BranchingWriterService(config=_make_config())
        result = service.write(
            _make_assembled(),
            session,
            provider=_FakeProvider(tool_input),
        )
        assert result.branch_options == []

    def test_held_with_nonempty_options_raises(self) -> None:
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        tool_input = {
            "narrative_text": "The story continues…",
            "branch_options_text": ["Option A", "Option B"],
            "branch_presentation_state": "held",
            "pacing_stage_hint": None,
        }
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="held"):
            service.write(
                _make_assembled(),
                session,
                provider=_FakeProvider(tool_input),
            )

    def test_omitted_with_nonempty_options_raises(self) -> None:
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        tool_input = {
            "narrative_text": "The story continues…",
            "branch_options_text": ["Option A"],
            "branch_presentation_state": "omitted",
            "pacing_stage_hint": None,
        }
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="omitted"):
            service.write(
                _make_assembled(),
                session,
                provider=_FakeProvider(tool_input),
            )

    def test_shown_with_zero_options_still_fails(self) -> None:
        # 'shown' with a configured range still enforces count; zero violates min.
        session = _make_session(branch_count_range=BranchCountRange.TWO_TO_THREE)
        tool_input = {
            "narrative_text": "The story continues…",
            "branch_options_text": [],
            "branch_presentation_state": "shown",
            "pacing_stage_hint": None,
        }
        service = BranchingWriterService(config=_make_config())
        with pytest.raises(BranchingPassError, match="0 branch option"):
            service.write(
                _make_assembled(),
                session,
                provider=_FakeProvider(tool_input),
            )


# ---------------------------------------------------------------------------
# Test: Fix 2 — _validate_branch_count unit coverage
# ---------------------------------------------------------------------------


class TestValidateBranchCountDirect:
    """Direct tests for _validate_branch_count with branch_presentation_state."""

    def test_held_empty_returns_none(self) -> None:
        _validate_branch_count([], "2-3", "held")  # should not raise

    def test_omitted_empty_returns_none(self) -> None:
        _validate_branch_count([], "3-4", "omitted")  # should not raise

    def test_held_nonempty_raises(self) -> None:
        with pytest.raises(BranchingPassError, match="held"):
            _validate_branch_count(["A", "B"], "2-3", "held")

    def test_omitted_nonempty_raises(self) -> None:
        with pytest.raises(BranchingPassError, match="omitted"):
            _validate_branch_count(["A"], "2-3", "omitted")

    def test_shown_within_range_passes(self) -> None:
        _validate_branch_count(["A", "B"], "2-3", "shown")  # should not raise

    def test_shown_below_min_raises(self) -> None:
        with pytest.raises(BranchingPassError):
            _validate_branch_count(["A"], "2-3", "shown")

    # Fix 3 (Round 2): TRUE_CYOA forbids held/omitted even with empty options.

    def test_true_cyoa_held_empty_raises(self) -> None:
        """TRUE_CYOA + held + [] must fail — no freeform fallback surface."""
        with pytest.raises(BranchingPassError, match="True CYOA"):
            _validate_branch_count([], "2-3", "held", InteractionStyle.TRUE_CYOA)

    def test_true_cyoa_omitted_empty_raises(self) -> None:
        """TRUE_CYOA + omitted + [] must fail."""
        with pytest.raises(BranchingPassError, match="True CYOA"):
            _validate_branch_count([], "2-3", "omitted", InteractionStyle.TRUE_CYOA)

    def test_true_cyoa_shown_within_range_passes(self) -> None:
        """TRUE_CYOA + shown + valid count must succeed."""
        _validate_branch_count(
            ["A", "B"], "2-3", "shown", InteractionStyle.TRUE_CYOA
        )  # must not raise

    def test_hybrid_held_empty_still_passes(self) -> None:
        """HYBRID + held + [] is valid — Hybrid allows deferred cards."""
        _validate_branch_count(
            [], "2-3", "held", InteractionStyle.HYBRID
        )  # must not raise

    def test_hybrid_omitted_empty_still_passes(self) -> None:
        """HYBRID + omitted + [] is valid."""
        _validate_branch_count(
            [], "2-3", "omitted", InteractionStyle.HYBRID
        )  # must not raise

    def test_none_style_held_empty_still_passes(self) -> None:
        """interaction_style=None preserves legacy behaviour — held + [] passes."""
        _validate_branch_count([], "2-3", "held")  # must not raise


# ---------------------------------------------------------------------------
# Test: PR #112 R14 — persisted branch_count_range / interaction_style
# compatibility.  A shown HYBRID/TRUE_CYOA turn must fail closed when the
# persisted range is not allowed for the active style, even if the option
# count is numerically in-bounds.  Held/omitted behavior is unchanged
# (those paths early-return before the compatibility check).
# ---------------------------------------------------------------------------


class TestPersistedRangeStyleCompatibility:
    """branch_count_range must be known AND allowed for interaction_style."""

    def test_hybrid_allowed_range_shown_passes(self) -> None:
        """HYBRID + allowed range ("1-2"/"2-3"/"3-4") accepts valid counts."""
        _validate_branch_count(["A"], "1-2", "shown", InteractionStyle.HYBRID)
        _validate_branch_count(["A", "B"], "2-3", "shown", InteractionStyle.HYBRID)
        _validate_branch_count(
            ["A", "B", "C"], "3-4", "shown", InteractionStyle.HYBRID
        )  # must not raise

    def test_true_cyoa_allowed_range_shown_passes(self) -> None:
        """TRUE_CYOA + allowed range ("2-3"/"2-4"/"2-5") accepts valid counts."""
        _validate_branch_count(["A", "B"], "2-3", "shown", InteractionStyle.TRUE_CYOA)
        _validate_branch_count(
            ["A", "B", "C", "D"], "2-4", "shown", InteractionStyle.TRUE_CYOA
        )
        _validate_branch_count(
            ["A", "B", "C", "D", "E"], "2-5", "shown", InteractionStyle.TRUE_CYOA
        )  # must not raise

    def test_hybrid_disallowed_range_shown_fails_closed(self) -> None:
        """HYBRID + "2-4"/"2-5" is disallowed even with in-bounds count."""
        with pytest.raises(BranchingPassError, match="not.*allowed"):
            _validate_branch_count(["A", "B"], "2-4", "shown", InteractionStyle.HYBRID)
        with pytest.raises(BranchingPassError, match="not.*allowed"):
            _validate_branch_count(["A", "B"], "2-5", "shown", InteractionStyle.HYBRID)

    def test_true_cyoa_disallowed_range_shown_fails_closed(self) -> None:
        """TRUE_CYOA + "1-2"/"3-4" is disallowed even with in-bounds count."""
        with pytest.raises(BranchingPassError, match="not.*allowed"):
            _validate_branch_count(
                ["A", "B"], "1-2", "shown", InteractionStyle.TRUE_CYOA
            )
        with pytest.raises(BranchingPassError, match="not.*allowed"):
            _validate_branch_count(
                ["A", "B", "C"], "3-4", "shown", InteractionStyle.TRUE_CYOA
            )

    def test_unknown_range_shown_fails_closed(self) -> None:
        """An unknown persisted range fails closed for in-play styles."""
        with pytest.raises(BranchingPassError):
            _validate_branch_count(["A", "B"], "9-9", "shown", InteractionStyle.HYBRID)
        with pytest.raises(BranchingPassError):
            _validate_branch_count(
                ["A", "B"], "9-9", "shown", InteractionStyle.TRUE_CYOA
            )

    def test_none_range_shown_fails_closed(self) -> None:
        """A missing persisted range fails closed for in-play styles (shown)."""
        with pytest.raises(BranchingPassError, match="not.*allowed"):
            _validate_branch_count(["A", "B"], None, "shown", InteractionStyle.HYBRID)

    def test_disallowed_range_held_still_valid(self) -> None:
        """Held/omitted early-return before the compatibility check.

        HYBRID held with an empty list stays valid even when the persisted
        range would be disallowed for shown delivery — held/omitted behavior
        is unchanged by the compatibility guard.
        """
        _validate_branch_count(
            [], "2-4", "held", InteractionStyle.HYBRID
        )  # must not raise
        _validate_branch_count(
            [], "2-4", "omitted", InteractionStyle.HYBRID
        )  # must not raise

    def test_true_cyoa_held_still_invalid(self) -> None:
        """TRUE_CYOA held/omitted remains invalid (unchanged), even allowed range."""
        with pytest.raises(BranchingPassError, match="True CYOA"):
            _validate_branch_count([], "2-3", "held", InteractionStyle.TRUE_CYOA)
