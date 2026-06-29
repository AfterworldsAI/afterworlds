"""Unit tests for BranchingOocConfigExtractorService — CRD Issue 16 Phase F.

Coverage:
- Happy path: returns BranchingConfigUpdate with requested fields.
- All-None result: no config changes requested.
- Provider call failure → raises BranchingPassError.
- Missing tool block → raises BranchingPassError.
- Wrong tool name → raises BranchingPassError.
- Schema validation failure → raises BranchingPassError.
- _render: correct pass_id, forced tool, system prompt present.
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
    IntentType,
    InteractionStyle,
    LengthPreference,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.story_bible import StoryBibleContext
from afterworlds.pipeline.branching.models import (
    BranchingConfigUpdate,
    BranchingOocConfigExtractorResult,
    BranchingOocExtractionUsageError,
    BranchingPassError,
)
from afterworlds.pipeline.branching.ooc_config_extractor import (
    EXTRACT_CONFIG_UPDATE_TOOL_NAME,
    BranchingOocConfigExtractorService,
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


def _make_ctx(ooc_input: str = "Switch to true CYOA mode please") -> AssembledContext:
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
    prefix = StablePrefix(
        system_prompt="branching ooc extractor test", story_bible_context=sbc
    )
    intent = IntentClassificationResult(
        intent_type=IntentType.OOC,
        confidence=0.99,
        raw_input=ooc_input,
        ambiguous=False,
    )
    suffix = VolatileSuffix(
        recent_turns=[],
        current_input=ooc_input,
        classified_intent=intent,
    )
    return AssembledContext(
        stable_prefix=prefix,
        volatile_suffix=suffix,
        pass_forward_ledger=PassForwardLedger(),
    )


def _make_result(tool_input: dict) -> ProviderCallResult:  # type: ignore[type-arg]
    return ProviderCallResult(
        pass_id=PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR,
        provider_name="fake",
        model_identifier="fake-model",
        model_tier=ModelTier.SONNET,
        content_parts=[
            ProviderToolCallPart(
                tool_name=EXTRACT_CONFIG_UPDATE_TOOL_NAME,
                tool_input=tool_input,
            )
        ],
        input_token_count=50,
        output_token_count=20,
        cache_read_token_count=None,
        cache_creation_token_count=None,
        cache_warmed=False,
        latency_ms=5,
    )


_ALL_NONE_INPUT = {
    "interaction_style": None,
    "branching_cadence": None,
    "branch_count_range": None,
    "length_preference": None,
}


class _FakeProvider:
    def __init__(self, tool_input: dict) -> None:  # type: ignore[type-arg]
        self._tool_input = tool_input
        self.last_request: ProviderCallRequest | None = None

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        self.last_request = request
        return _make_result(self._tool_input)

    @property
    def provider_name(self) -> str:
        return "fake"


class _FailingProvider:
    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        raise RuntimeError("network error")

    @property
    def provider_name(self) -> str:
        return "fake"


class _NoToolProvider:
    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        return ProviderCallResult(
            pass_id=PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR,
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
    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        return ProviderCallResult(
            pass_id=PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR,
            provider_name="fake",
            model_identifier="fake-model",
            model_tier=ModelTier.SONNET,
            content_parts=[
                ProviderToolCallPart(
                    tool_name="wrong_tool",
                    tool_input=_ALL_NONE_INPUT,
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


# ---------------------------------------------------------------------------
# Tests: happy paths
# ---------------------------------------------------------------------------


class TestHappyPath:
    """BranchingOocConfigExtractorService returns BranchingOocConfigExtractorResult."""

    def test_all_none_is_valid(self) -> None:
        svc = BranchingOocConfigExtractorService()
        result = svc.extract(_make_ctx(), _FakeProvider(_ALL_NONE_INPUT))
        assert isinstance(result, BranchingOocConfigExtractorResult)
        assert isinstance(result.config_update, BranchingConfigUpdate)
        assert result.config_update.interaction_style is None
        assert result.config_update.branching_cadence is None
        assert result.config_update.branch_count_range is None
        assert result.config_update.length_preference is None

    def test_interaction_style_extracted(self) -> None:
        svc = BranchingOocConfigExtractorService()
        tool_input = {**_ALL_NONE_INPUT, "interaction_style": "true_cyoa"}
        result = svc.extract(_make_ctx(), _FakeProvider(tool_input))
        assert result.config_update.interaction_style is InteractionStyle.TRUE_CYOA

    def test_branching_cadence_extracted(self) -> None:
        svc = BranchingOocConfigExtractorService()
        tool_input = {**_ALL_NONE_INPUT, "branching_cadence": "interactive"}
        result = svc.extract(_make_ctx(), _FakeProvider(tool_input))
        assert result.config_update.branching_cadence is BranchingCadence.INTERACTIVE

    def test_branch_count_range_extracted(self) -> None:
        svc = BranchingOocConfigExtractorService()
        tool_input = {**_ALL_NONE_INPUT, "branch_count_range": "2-3"}
        result = svc.extract(_make_ctx(), _FakeProvider(tool_input))
        assert result.config_update.branch_count_range is BranchCountRange.TWO_TO_THREE

    def test_length_preference_extracted(self) -> None:
        svc = BranchingOocConfigExtractorService()
        tool_input = {**_ALL_NONE_INPUT, "length_preference": "novella"}
        result = svc.extract(_make_ctx(), _FakeProvider(tool_input))
        assert result.config_update.length_preference is LengthPreference.NOVELLA

    def test_multiple_fields_extracted(self) -> None:
        svc = BranchingOocConfigExtractorService()
        tool_input = {
            "interaction_style": "hybrid",
            "branching_cadence": "balanced",
            "branch_count_range": "3-4",
            "length_preference": "short_story",
        }
        result = svc.extract(_make_ctx(), _FakeProvider(tool_input))
        assert result.config_update.interaction_style is InteractionStyle.HYBRID
        assert result.config_update.branching_cadence is BranchingCadence.BALANCED
        assert result.config_update.branch_count_range is BranchCountRange.THREE_TO_FOUR
        assert result.config_update.length_preference is LengthPreference.SHORT_STORY

    def test_provider_metrics_surfaced_in_result(self) -> None:
        """extract() returns provider usage metrics for entitlement settlement."""
        svc = BranchingOocConfigExtractorService()
        result = svc.extract(_make_ctx(), _FakeProvider(_ALL_NONE_INPUT))
        # _FakeProvider returns provider_name="fake", model_tier=ModelTier.SONNET,
        # input_token_count=50, output_token_count=20, latency_ms=5.
        assert result.provider == "fake"
        assert result.input_token_count == 50
        assert result.output_token_count == 20
        assert result.latency_ms == 5
        assert result.model_tier == ModelTier.SONNET.value


# ---------------------------------------------------------------------------
# Tests: fail paths
# ---------------------------------------------------------------------------


class TestProviderFailurePaths:
    """BranchingOocConfigExtractorService raises BranchingPassError on errors."""

    def test_provider_call_failure_raises(self) -> None:
        svc = BranchingOocConfigExtractorService()
        with pytest.raises(BranchingPassError, match="provider call failed"):
            svc.extract(_make_ctx(), _FailingProvider())

    def test_no_tool_block_raises(self) -> None:
        svc = BranchingOocConfigExtractorService()
        with pytest.raises(BranchingPassError, match="missing tool-use block"):
            svc.extract(_make_ctx(), _NoToolProvider())

    def test_wrong_tool_name_raises(self) -> None:
        svc = BranchingOocConfigExtractorService()
        with pytest.raises(BranchingPassError, match="unexpected tool name"):
            svc.extract(_make_ctx(), _WrongToolProvider())

    def test_schema_validation_failure_raises(self) -> None:
        svc = BranchingOocConfigExtractorService()
        bad_input = {
            "interaction_style": "not_a_valid_style",
            "branching_cadence": None,
            "branch_count_range": None,
            "length_preference": None,
        }
        with pytest.raises(BranchingPassError, match="schema validation"):
            svc.extract(_make_ctx(), _FakeProvider(bad_input))


# ---------------------------------------------------------------------------
# Tests: post-provider local failure preserves provider usage
# ---------------------------------------------------------------------------


class TestUsagePreservedOnLocalFailure:
    """Local validation failures *after* a provider result preserve usage.

    When the provider call returns (consuming tokens) but a later local step
    rejects the response, the extractor raises BranchingOocExtractionUsageError
    carrying a usage-only result so settlement still sees the consumed tokens.
    The config_update on that usage result is all-null (no mutation implied).
    """

    def test_no_tool_block_preserves_usage(self) -> None:
        svc = BranchingOocConfigExtractorService()
        with pytest.raises(BranchingOocExtractionUsageError) as exc_info:
            svc.extract(_make_ctx(), _NoToolProvider())
        usage = exc_info.value.usage_result
        # _NoToolProvider: provider="fake", input=50, output=10, no cache tokens.
        assert isinstance(usage, BranchingOocConfigExtractorResult)
        assert usage.provider == "fake"
        assert usage.input_token_count == 50
        assert usage.output_token_count == 10
        assert usage.model_tier == ModelTier.SONNET.value
        # config_update is all-null: no mutation is implied by a failed parse.
        assert usage.config_update.interaction_style is None
        assert usage.config_update.branching_cadence is None
        assert usage.config_update.branch_count_range is None
        assert usage.config_update.length_preference is None

    def test_wrong_tool_name_preserves_usage(self) -> None:
        svc = BranchingOocConfigExtractorService()
        with pytest.raises(BranchingOocExtractionUsageError) as exc_info:
            svc.extract(_make_ctx(), _WrongToolProvider())
        usage = exc_info.value.usage_result
        # _WrongToolProvider: provider="fake", input=50, output=10.
        assert usage.provider == "fake"
        assert usage.input_token_count == 50
        assert usage.output_token_count == 10
        assert usage.config_update.interaction_style is None
        assert usage.config_update.branch_count_range is None

    def test_schema_validation_failure_preserves_usage(self) -> None:
        svc = BranchingOocConfigExtractorService()
        bad_input = {
            "interaction_style": "not_a_valid_style",
            "branching_cadence": None,
            "branch_count_range": None,
            "length_preference": None,
        }
        with pytest.raises(BranchingOocExtractionUsageError) as exc_info:
            svc.extract(_make_ctx(), _FakeProvider(bad_input))
        usage = exc_info.value.usage_result
        # _FakeProvider via _make_result: provider="fake", input=50, output=20.
        assert usage.provider == "fake"
        assert usage.input_token_count == 50
        assert usage.output_token_count == 20
        # The malformed style is discarded — config_update stays all-null.
        assert usage.config_update.interaction_style is None

    def test_provider_call_failure_carries_no_usage(self) -> None:
        """A provider-call exception before any result is a plain error.

        No result was returned, so no usage was consumed — the extractor must
        not fabricate a usage payload (raises BranchingPassError, not the
        usage-carrying subclass).
        """
        svc = BranchingOocConfigExtractorService()
        with pytest.raises(BranchingPassError) as exc_info:
            svc.extract(_make_ctx(), _FailingProvider())
        assert not isinstance(exc_info.value, BranchingOocExtractionUsageError)


# ---------------------------------------------------------------------------
# Tests: _render — verify request structure
# ---------------------------------------------------------------------------


class TestRenderRequestStructure:
    """The ProviderCallRequest produced by _render has the correct shape."""

    def test_forced_tool_name_set(self) -> None:
        svc = BranchingOocConfigExtractorService()
        provider = _FakeProvider(_ALL_NONE_INPUT)
        svc.extract(_make_ctx("change to true cyoa"), provider)
        assert provider.last_request is not None
        assert provider.last_request.forced_tool_name == EXTRACT_CONFIG_UPDATE_TOOL_NAME

    def test_pass_id_is_branching_ooc_config_extractor(self) -> None:
        svc = BranchingOocConfigExtractorService()
        provider = _FakeProvider(_ALL_NONE_INPUT)
        svc.extract(_make_ctx("change to true cyoa"), provider)
        assert provider.last_request is not None
        assert (
            provider.last_request.pass_id
            is PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR
        )

    def test_system_blocks_present(self) -> None:
        svc = BranchingOocConfigExtractorService()
        provider = _FakeProvider(_ALL_NONE_INPUT)
        svc.extract(_make_ctx("change to true cyoa"), provider)
        assert provider.last_request is not None
        assert len(provider.last_request.system_blocks) >= 1

    def test_ooc_input_in_rendered_blocks(self) -> None:
        svc = BranchingOocConfigExtractorService()
        provider = _FakeProvider(_ALL_NONE_INPUT)
        ooc_msg = "Switch to true CYOA with 3 choices per beat"
        svc.extract(_make_ctx(ooc_msg), provider)
        assert provider.last_request is not None
        all_text = " ".join(b.text for b in provider.last_request.rendered_blocks)
        assert ooc_msg in all_text
