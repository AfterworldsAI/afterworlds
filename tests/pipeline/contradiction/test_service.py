"""Unit tests for ContradictionService — CRD Issue 11 / 14a.

Test classes
------------
TestHappyPathClear            — clean prose returns CLEAR verdict, empty violations
TestHappyPathBlocked          — prose with violations returns BLOCKED verdict
TestVerdictDerivation         — verdict invariant: BLOCKED iff violations non-empty
TestSchemaValidation          — ContradictionViolation field_validator
TestProviderException         — provider exception → ContradictionPassError
TestMissingToolBlock          — no tool-use block → ContradictionPassError
TestEmptyViolations           — empty violations array is valid (CLEAR)
TestRendererStructure         — ProviderCallRequest shape: pass_id, tool, system, order
TestExtendedTTL               — cache breakpoint ttl honours extended_ttl config flag
TestAdapterInjection          — injected adapter is invoked; default not constructed
TestCacheMetricsPropagation   — all four token counts propagated to ContradictionResult
TestBuiltContextImmutability  — caller's AssembledContext is not mutated
TestPassForwardLedgerPreserved — pre-existing ledger entries preserved in derived ctx
TestNonEmptyStringValidation  — field_validator blocks empty/whitespace strings
TestScopeBoundary             — model_identifier includes provider prefix
TestCategoryPlumbing          — all ContradictionCategory values accepted from model
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.models.context import (
    AssembledContext,
    PassForwardEntry,
    PassForwardLedger,
    RetrievalMemoryPayload,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import (
    CastRole,
    IntentType,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.story_bible import (
    CastEntry,
    StoryBibleContext,
)
from afterworlds.pipeline._stable_prefix_renderer import TTL_DEFAULT, TTL_EXTENDED
from afterworlds.pipeline.contradiction.caller import REPORT_TOOL_NAME
from afterworlds.pipeline.contradiction.config import ContradictionConfig
from afterworlds.pipeline.contradiction.models import (
    ContradictionCategory,
    ContradictionPassError,
    ContradictionResult,
    ContradictionVerdict,
    ContradictionViolation,
)
from afterworlds.pipeline.contradiction.service import (
    ContradictionService,
    _derive_context,
)
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderTextPart,
    ProviderToolCallPart,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(extended_ttl: bool = True) -> ContradictionConfig:
    return ContradictionConfig(
        model="claude-haiku-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=extended_ttl,
    )


def _make_assembled(
    story_id: UUID | None = None,
    ledger_entries: list[tuple[str, str]] | None = None,
) -> AssembledContext:
    if story_id is None:
        story_id = uuid4()
    ctx = StoryBibleContext(
        story_id=story_id,
        setting=None,
        cast=(
            CastEntry(
                cast_id=uuid4(),
                story_id=story_id,
                name="Aldric",
                role=CastRole.PROTAGONIST,
                current_location="The Meridian Hotel, Room 14",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        ),
        locked_facts=(),
        forbidden_facts=(),
        relationship_ledger=(),
        active_plot_threads=(),
        events=(),
    )
    sp = StablePrefix(
        system_prompt="You are the contradiction checker.",
        story_bible_context=ctx,
        rolling_summary_text=None,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )
    icr = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.90,
        raw_input="I step into the corridor.",
        ambiguous=False,
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input="I step into the corridor.",
        classified_intent=icr,
    )
    entries = []
    if ledger_entries:
        for name, content in ledger_entries:
            entries.append(PassForwardEntry(pass_name=name, content=content))
    return AssembledContext(
        stable_prefix=sp,
        volatile_suffix=vs,
        pass_forward_ledger=PassForwardLedger(entries=entries),
    )


def _fake_tool_result(
    tool_input: dict[str, Any] | None = None,
    input_token_count: int = 100,
    output_token_count: int = 50,
    cache_read_token_count: int | None = None,
    cache_creation_token_count: int | None = None,
    model_identifier: str = "anthropic:claude-haiku-test",
) -> ProviderCallResult:
    return ProviderCallResult(
        pass_id=PipelinePassId.CONTRADICTION,
        provider_name="anthropic",
        model_identifier=model_identifier,
        model_tier=ModelTier.HAIKU,
        content_parts=[
            ProviderToolCallPart(
                tool_name=REPORT_TOOL_NAME,
                tool_input=tool_input if tool_input is not None else {"violations": []},
            )
        ],
        input_token_count=input_token_count,
        output_token_count=output_token_count,
        cache_read_token_count=cache_read_token_count,
        cache_creation_token_count=cache_creation_token_count,
        cache_warmed=bool(cache_read_token_count),
        latency_ms=1,
    )


class _FakeProviderAdapter:
    """Capturing fake ProviderAdapter for ContradictionService tests."""

    def __init__(
        self,
        result: ProviderCallResult | None = None,
        raise_exc: Exception | None = None,
    ) -> None:
        self._result = result
        self._raise_exc = raise_exc
        self.captured_requests: list[ProviderCallRequest] = []
        self.provider_name = "anthropic"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        self.captured_requests.append(request)
        if self._raise_exc is not None:
            raise self._raise_exc
        return self._result or _fake_tool_result()


def _make_fake_adapter(
    result: ProviderCallResult | None = None,
    raise_exc: Exception | None = None,
) -> _FakeProviderAdapter:
    return _FakeProviderAdapter(result=result, raise_exc=raise_exc)


def _make_violation_dict(
    category: str = "location_drift",
    description: str = "Aldric is at the police precinct.",
    canon_reference: str = "Story Bible: Aldric is at The Meridian Hotel, Room 14.",
) -> dict[str, Any]:
    return {
        "category": category,
        "description": description,
        "canon_reference": canon_reference,
    }


# ---------------------------------------------------------------------------
# TestHappyPathClear
# ---------------------------------------------------------------------------


class TestHappyPathClear:
    def test_returns_clear_verdict_on_empty_violations(self) -> None:
        adapter = _make_fake_adapter(_fake_tool_result({"violations": []}))
        svc = ContradictionService(config=_make_config())
        ctx = _make_assembled()

        result = svc.check(  # type: ignore[arg-type]
            ctx, "You pocket the key and step into the corridor.", provider=adapter
        )

        assert result.verdict == ContradictionVerdict.CLEAR
        assert result.violations == []

    def test_result_type(self) -> None:
        adapter = _make_fake_adapter(_fake_tool_result({"violations": []}))
        svc = ContradictionService(config=_make_config())
        result = svc.check(_make_assembled(), "Prose here.", provider=adapter)  # type: ignore[arg-type]
        assert isinstance(result, ContradictionResult)

    def test_model_identifier_present(self) -> None:
        adapter = _make_fake_adapter(_fake_tool_result({"violations": []}))
        svc = ContradictionService(config=_make_config())
        result = svc.check(_make_assembled(), "Prose here.", provider=adapter)  # type: ignore[arg-type]
        assert result.model_identifier == "anthropic:claude-haiku-test"


# ---------------------------------------------------------------------------
# TestHappyPathBlocked
# ---------------------------------------------------------------------------


class TestHappyPathBlocked:
    def test_returns_blocked_verdict_on_violations(self) -> None:
        viol = _make_violation_dict()
        adapter = _make_fake_adapter(_fake_tool_result({"violations": [viol]}))
        svc = ContradictionService(config=_make_config())

        result = svc.check(  # type: ignore[arg-type]
            _make_assembled(), "Aldric walks into the precinct.", provider=adapter
        )

        assert result.verdict == ContradictionVerdict.BLOCKED
        assert len(result.violations) == 1

    def test_violation_fields_propagated(self) -> None:
        viol = _make_violation_dict(
            category="location_drift",
            description="Aldric at the precinct.",
            canon_reference="Story Bible: Aldric is at The Meridian Hotel.",
        )
        adapter = _make_fake_adapter(_fake_tool_result({"violations": [viol]}))
        svc = ContradictionService(config=_make_config())

        result = svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]

        v = result.violations[0]
        assert v.category == ContradictionCategory.LOCATION_DRIFT
        assert v.description == "Aldric at the precinct."
        assert v.canon_reference == "Story Bible: Aldric is at The Meridian Hotel."

    def test_multiple_violations(self) -> None:
        viols = [
            _make_violation_dict("location_drift", "A at precinct.", "A is at hotel."),
            _make_violation_dict("name_drift", "Called 'Drake'.", "Name is 'Aldric'."),
        ]
        adapter = _make_fake_adapter(_fake_tool_result({"violations": viols}))
        svc = ContradictionService(config=_make_config())

        result = svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]

        assert result.verdict == ContradictionVerdict.BLOCKED
        assert len(result.violations) == 2


# ---------------------------------------------------------------------------
# TestVerdictDerivation
# ---------------------------------------------------------------------------


class TestVerdictDerivation:
    def test_clear_when_empty(self) -> None:
        adapter = _make_fake_adapter(_fake_tool_result({"violations": []}))
        svc = ContradictionService(config=_make_config())
        result = svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        assert result.verdict == ContradictionVerdict.CLEAR

    def test_blocked_when_non_empty(self) -> None:
        viol = _make_violation_dict()
        adapter = _make_fake_adapter(_fake_tool_result({"violations": [viol]}))
        svc = ContradictionService(config=_make_config())
        result = svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        assert result.verdict == ContradictionVerdict.BLOCKED

    def test_verdict_not_returned_by_model(self) -> None:
        tool_input = {
            "violations": [],
            "verdict": "BLOCKED",
        }
        adapter = _make_fake_adapter(_fake_tool_result(tool_input))
        svc = ContradictionService(config=_make_config())
        result = svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        assert result.verdict == ContradictionVerdict.CLEAR


# ---------------------------------------------------------------------------
# TestSchemaValidation
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_empty_description_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty string"):
            ContradictionViolation(
                category=ContradictionCategory.OTHER,
                description="",
                canon_reference="Some reference.",
            )

    def test_whitespace_description_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty string"):
            ContradictionViolation(
                category=ContradictionCategory.OTHER,
                description="   ",
                canon_reference="Some reference.",
            )

    def test_empty_canon_reference_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty string"):
            ContradictionViolation(
                category=ContradictionCategory.OTHER,
                description="The prose says X.",
                canon_reference="",
            )

    def test_whitespace_canon_reference_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty string"):
            ContradictionViolation(
                category=ContradictionCategory.OTHER,
                description="The prose says X.",
                canon_reference="\t\n",
            )

    def test_valid_violation_accepted(self) -> None:
        v = ContradictionViolation(
            category=ContradictionCategory.LOCATION_DRIFT,
            description="Aldric is at the precinct.",
            canon_reference="Story Bible: Aldric is at The Meridian Hotel.",
        )
        assert v.category == ContradictionCategory.LOCATION_DRIFT

    def test_schema_validation_error_wraps_as_pass_error(self) -> None:
        bad_input = {
            "violations": [
                {
                    "category": "location_drift",
                    "description": "",
                    "canon_reference": "Some reference.",
                }
            ]
        }
        adapter = _make_fake_adapter(_fake_tool_result(bad_input))
        svc = ContradictionService(config=_make_config())

        with pytest.raises(ContradictionPassError, match="schema validation"):
            svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TestProviderException
# ---------------------------------------------------------------------------


class TestProviderException:
    def test_provider_exception_raises_pass_error(self) -> None:
        adapter = _make_fake_adapter(raise_exc=RuntimeError("network timeout"))
        svc = ContradictionService(config=_make_config())

        with pytest.raises(ContradictionPassError, match="provider call failed"):
            svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]

    def test_original_exception_chained(self) -> None:
        adapter = _make_fake_adapter(raise_exc=RuntimeError("boom"))
        svc = ContradictionService(config=_make_config())

        with pytest.raises(ContradictionPassError) as exc_info:
            svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]

        assert isinstance(exc_info.value.__cause__, RuntimeError)


# ---------------------------------------------------------------------------
# TestMissingToolBlock
# ---------------------------------------------------------------------------


class TestMissingToolBlock:
    def test_no_tool_block_raises_pass_error(self) -> None:
        no_tool_result = ProviderCallResult(
            pass_id=PipelinePassId.CONTRADICTION,
            provider_name="anthropic",
            model_identifier="anthropic:claude-haiku-test",
            model_tier=ModelTier.HAIKU,
            content_parts=[ProviderTextPart(text="The prose is fine.")],
            input_token_count=100,
            output_token_count=20,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=1,
        )
        adapter = _make_fake_adapter(no_tool_result)
        svc = ContradictionService(config=_make_config())

        with pytest.raises(
            ContradictionPassError,
            match="no '.*' tool-use block|missing tool-use block",
        ):
            svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]

    def test_wrong_tool_name_raises_pass_error(self) -> None:
        wrong_name_result = ProviderCallResult(
            pass_id=PipelinePassId.CONTRADICTION,
            provider_name="anthropic",
            model_identifier="anthropic:claude-haiku-test",
            model_tier=ModelTier.HAIKU,
            content_parts=[
                ProviderToolCallPart(
                    tool_name="some_other_tool",
                    tool_input={"violations": []},
                )
            ],
            input_token_count=100,
            output_token_count=20,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=1,
        )
        adapter = _make_fake_adapter(wrong_name_result)
        svc = ContradictionService(config=_make_config())

        with pytest.raises(ContradictionPassError):
            svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TestEmptyViolations
# ---------------------------------------------------------------------------


class TestEmptyViolations:
    def test_empty_array_is_valid(self) -> None:
        adapter = _make_fake_adapter(_fake_tool_result({"violations": []}))
        svc = ContradictionService(config=_make_config())
        result = svc.check(_make_assembled(), "", provider=adapter)  # type: ignore[arg-type]
        assert result.verdict == ContradictionVerdict.CLEAR
        assert result.violations == []


# ---------------------------------------------------------------------------
# TestRendererStructure
# ---------------------------------------------------------------------------


class TestRendererStructure:
    def test_pass_id_is_contradiction(self) -> None:
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert request.pass_id == PipelinePassId.CONTRADICTION

    def test_forced_tool_name_set(self) -> None:
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert request.forced_tool_name == REPORT_TOOL_NAME

    def test_payload_has_system_blocks(self) -> None:
        """system_blocks carries [pass contract, mode contract]."""
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert len(request.system_blocks) == 2

    def test_system_block_contains_contradiction_pass_prompt(self) -> None:
        """First system block is the Contradiction pass prompt."""
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert "Contradiction Checker" in request.system_blocks[0].text

    def test_mode_contract_is_second_system_block(self) -> None:
        """Issue 12c: mode contract moved from user blocks to system_blocks[1]."""
        MODE_CONTRACT = "UNIQUE-MODE-CONTRACT-SENTINEL"
        ctx = _make_assembled()
        new_sp = StablePrefix(
            system_prompt=MODE_CONTRACT,
            story_bible_context=ctx.stable_prefix.story_bible_context,
            rolling_summary_text=ctx.stable_prefix.rolling_summary_text,
            rules_package_slice=ctx.stable_prefix.rules_package_slice,
            retrieval_memory=ctx.stable_prefix.retrieval_memory,
        )
        ctx2 = AssembledContext(
            stable_prefix=new_sp,
            volatile_suffix=ctx.volatile_suffix,
            pass_forward_ledger=ctx.pass_forward_ledger,
        )
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(ctx2, "Prose.", provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        assert request.system_blocks[1].text == MODE_CONTRACT

    def test_mode_contract_absent_from_rendered_blocks(self) -> None:
        """Issue 12c: mode contract no longer duplicated into rendered_blocks."""
        MODE_CONTRACT = "UNIQUE-MODE-CONTRACT-SENTINEL"
        ctx = _make_assembled()
        new_sp = StablePrefix(
            system_prompt=MODE_CONTRACT,
            story_bible_context=ctx.stable_prefix.story_bible_context,
            rolling_summary_text=None,
            rules_package_slice=None,
            retrieval_memory=ctx.stable_prefix.retrieval_memory,
        )
        ctx2 = AssembledContext(
            stable_prefix=new_sp,
            volatile_suffix=ctx.volatile_suffix,
            pass_forward_ledger=ctx.pass_forward_ledger,
        )
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(ctx2, "Prose.", provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        assert not any(
            MODE_CONTRACT in b.text for b in request.rendered_blocks
        ), "Mode contract must not appear in rendered_blocks after 12c"

    def test_cache_breakpoint_precedes_writer_output_and_volatile(self) -> None:
        """Cache breakpoint on the final stable-prefix block, before writer/volatile."""
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config(extended_ttl=True))
        svc.check(_make_assembled(), "Writer prose here.", provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        blocks = request.rendered_blocks
        cache_idx = next(
            (i for i, b in enumerate(blocks) if b.has_cache_breakpoint),
            None,
        )
        writer_idx = next(
            (i for i, b in enumerate(blocks) if "[WRITER OUTPUT]" in b.text),
            None,
        )
        volatile_idx = next(
            (i for i, b in enumerate(blocks) if "I step into the corridor." in b.text),
            None,
        )
        assert cache_idx is not None, "No cache breakpoint block found"
        assert writer_idx is not None, "No writer output block found"
        assert volatile_idx is not None, "No volatile suffix block found"
        assert (
            cache_idx < writer_idx
        ), "Cache breakpoint must precede writer output block"
        assert (
            cache_idx < volatile_idx
        ), "Cache breakpoint must precede volatile suffix block"

    def test_writer_output_in_ledger_before_volatile_suffix(self) -> None:
        """Writer output must appear before current input in rendered_blocks."""
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        writer_output = "THE WRITER PROSE HERE"
        svc.check(_make_assembled(), writer_output, provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        texts = [b.text for b in request.rendered_blocks]
        writer_idx = next((i for i, t in enumerate(texts) if writer_output in t), None)
        volatile_idx = next(
            (i for i, t in enumerate(texts) if "I step into the corridor." in t), None
        )
        assert writer_idx is not None, "Writer output not found in rendered_blocks"
        assert volatile_idx is not None, "Volatile suffix not found in rendered_blocks"
        assert (
            writer_idx < volatile_idx
        ), "Writer output block must appear before volatile suffix block"

    def test_writer_output_formatted_as_ledger_entry(self) -> None:
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        writer_output = "You step into the corridor."
        svc.check(_make_assembled(), writer_output, provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        ledger_block = next(
            (b.text for b in request.rendered_blocks if "[WRITER OUTPUT]" in b.text),
            None,
        )
        assert ledger_block is not None, "No [WRITER OUTPUT] ledger block found"
        assert writer_output in ledger_block

    def test_tool_definitions_contain_report_tool(self) -> None:
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert len(request.tool_definitions) == 1
        assert request.tool_definitions[0].name == REPORT_TOOL_NAME


# ---------------------------------------------------------------------------
# TestExtendedTTL
# ---------------------------------------------------------------------------


class TestExtendedTTL:
    def test_extended_ttl_true_sets_1h(self) -> None:
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config(extended_ttl=True))
        svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert cached, "No cache breakpoint block found"
        assert cached[-1].ttl == TTL_EXTENDED

    def test_extended_ttl_false_sets_5m(self) -> None:
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config(extended_ttl=False))
        svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert cached, "No cache breakpoint block found"
        assert cached[-1].ttl == TTL_DEFAULT

    def test_cache_control_on_last_stable_prefix_block(self) -> None:
        """Cache breakpoint on the final stable-prefix block, not writer output."""
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config(extended_ttl=True))
        svc.check(_make_assembled(), "Writer prose goes here.", provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        blocks = request.rendered_blocks
        cache_idx = next(
            (i for i, b in enumerate(blocks) if b.has_cache_breakpoint),
            None,
        )
        writer_idx = next(
            (i for i, b in enumerate(blocks) if "[WRITER OUTPUT]" in b.text),
            None,
        )
        assert cache_idx is not None
        assert writer_idx is not None
        assert (
            cache_idx < writer_idx
        ), "Cache breakpoint must be on stable prefix, before writer output block"


# ---------------------------------------------------------------------------
# TestAdapterInjection
# ---------------------------------------------------------------------------


class TestAdapterInjection:
    def test_injected_adapter_is_used(self) -> None:
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        assert len(adapter.captured_requests) == 1

    def test_adapter_receives_one_call_per_check(self) -> None:
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(_make_assembled(), "Prose 1.", provider=adapter)  # type: ignore[arg-type]
        svc.check(_make_assembled(), "Prose 2.", provider=adapter)  # type: ignore[arg-type]
        assert len(adapter.captured_requests) == 2


# ---------------------------------------------------------------------------
# TestCacheMetricsPropagation
# ---------------------------------------------------------------------------


class TestCacheMetricsPropagation:
    def test_all_token_counts_propagated(self) -> None:
        result = _fake_tool_result(
            input_token_count=200,
            output_token_count=60,
            cache_read_token_count=150,
            cache_creation_token_count=50,
        )
        adapter = _make_fake_adapter(result)
        svc = ContradictionService(config=_make_config())
        contradiction_result = svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]

        assert contradiction_result.input_token_count == 200
        assert contradiction_result.output_token_count == 60
        assert contradiction_result.cache_read_token_count == 150
        assert contradiction_result.cache_creation_token_count == 50

    def test_none_cache_counts_allowed(self) -> None:
        result = _fake_tool_result(
            input_token_count=100,
            output_token_count=40,
            cache_read_token_count=None,
            cache_creation_token_count=None,
        )
        adapter = _make_fake_adapter(result)
        svc = ContradictionService(config=_make_config())
        contradiction_result = svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]

        assert contradiction_result.cache_read_token_count is None
        assert contradiction_result.cache_creation_token_count is None

    def test_latency_ms_is_non_negative_int(self) -> None:
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        result = svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        assert isinstance(result.latency_ms, int)
        assert result.latency_ms >= 0


# ---------------------------------------------------------------------------
# TestBuiltContextImmutability
# ---------------------------------------------------------------------------


class TestBuiltContextImmutability:
    def test_caller_context_not_mutated(self) -> None:
        ctx = _make_assembled()
        original_entry_count = len(ctx.pass_forward_ledger.entries)

        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(ctx, "Writer prose.", provider=adapter)  # type: ignore[arg-type]

        assert len(ctx.pass_forward_ledger.entries) == original_entry_count

    def test_derived_context_has_writer_entry(self) -> None:
        ctx = _make_assembled()
        writer_output = "You step forward."
        derived = _derive_context(ctx, writer_output)

        assert len(derived.pass_forward_ledger.entries) == 1
        assert derived.pass_forward_ledger.entries[0].pass_name == "writer"
        assert derived.pass_forward_ledger.entries[0].content == writer_output

    def test_original_context_unchanged_after_derive(self) -> None:
        ctx = _make_assembled()
        _derive_context(ctx, "Prose.")
        assert len(ctx.pass_forward_ledger.entries) == 0


# ---------------------------------------------------------------------------
# TestPassForwardLedgerPreserved
# ---------------------------------------------------------------------------


class TestPassForwardLedgerPreserved:
    def test_pre_existing_ledger_entries_preserved(self) -> None:
        ctx = _make_assembled(ledger_entries=[("planner", "Plan output goes here.")])
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())
        svc.check(ctx, "Writer prose.", provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        assert any(
            "[PLANNER OUTPUT]" in b.text for b in request.rendered_blocks
        ), "Pre-existing ledger entry not found in rendered_blocks"

    def test_writer_entry_appended_after_existing_entries(self) -> None:
        ctx = _make_assembled(ledger_entries=[("planner", "Plan output.")])
        derived = _derive_context(ctx, "Writer prose.")

        entries = derived.pass_forward_ledger.entries
        assert len(entries) == 2
        assert entries[0].pass_name == "planner"
        assert entries[1].pass_name == "writer"


# ---------------------------------------------------------------------------
# TestNonEmptyStringValidation
# ---------------------------------------------------------------------------


class TestNonEmptyStringValidation:
    @pytest.mark.parametrize("description", ["", "   ", "\t", "\n"])
    def test_empty_description_rejected(self, description: str) -> None:
        with pytest.raises(ValueError):
            ContradictionViolation(
                category=ContradictionCategory.OTHER,
                description=description,
                canon_reference="Valid reference.",
            )

    @pytest.mark.parametrize("canon_reference", ["", "   ", "\t", "\n"])
    def test_empty_canon_reference_rejected(self, canon_reference: str) -> None:
        with pytest.raises(ValueError):
            ContradictionViolation(
                category=ContradictionCategory.OTHER,
                description="Valid description.",
                canon_reference=canon_reference,
            )


# ---------------------------------------------------------------------------
# TestScopeBoundary
# ---------------------------------------------------------------------------


class TestScopeBoundary:
    def test_model_identifier_has_provider_prefix(self) -> None:
        """model_identifier from ProviderCallResult must include provider prefix."""
        custom_result = _fake_tool_result(model_identifier="anthropic:my-custom-model")
        adapter = _make_fake_adapter(custom_result)
        svc = ContradictionService(
            config=ContradictionConfig(model="my-custom-model", api_key_env="KEY_ENV")
        )
        result = svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        assert result.model_identifier == "anthropic:my-custom-model"

    def test_no_story_id_parameter_in_check(self) -> None:
        import inspect

        sig = inspect.signature(ContradictionService.check)
        assert "story_id" not in sig.parameters

    def test_no_story_bible_service_in_constructor(self) -> None:
        import inspect

        sig = inspect.signature(ContradictionService.__init__)
        assert "story_bible_service" not in sig.parameters


# ---------------------------------------------------------------------------
# TestCategoryPlumbing
# ---------------------------------------------------------------------------


class TestCategoryPlumbing:
    @pytest.mark.parametrize(
        "category",
        [
            "dead_character_acting",
            "item_never_acquired",
            "locked_fact_violated",
            "location_drift",
            "name_drift",
            "pov_tense_shift",
            "other",
        ],
    )
    def test_all_categories_accepted(self, category: str) -> None:
        viol = {
            "category": category,
            "description": "Some prose text.",
            "canon_reference": "Story Bible fact.",
        }
        adapter = _make_fake_adapter(_fake_tool_result({"violations": [viol]}))
        svc = ContradictionService(config=_make_config())
        result = svc.check(_make_assembled(), "Prose.", provider=adapter)  # type: ignore[arg-type]
        assert result.verdict == ContradictionVerdict.BLOCKED
        assert result.violations[0].category.value == category


# ---------------------------------------------------------------------------
# TestDeriveContextIdempotency
# ---------------------------------------------------------------------------


class TestDeriveContextIdempotency:
    """_derive_context is idempotent around Writer output.

    Four cases per the Issue 11 fix spec:
      1. No existing writer entry → appends writer_output.
      2. Matching writer entry already present → no duplicate appended.
      3. Conflicting writer entry → ContradictionPassError.
      4. Multiple writer entries → ContradictionPassError.
    """

    def test_no_writer_entry_appends(self) -> None:
        ctx = _make_assembled()
        derived = _derive_context(ctx, "Writer prose.")

        writer_entries = [
            e for e in derived.pass_forward_ledger.entries if e.pass_name == "writer"
        ]
        assert len(writer_entries) == 1
        assert writer_entries[0].content == "Writer prose."

    def test_matching_writer_entry_not_duplicated(self) -> None:
        ctx = _make_assembled(ledger_entries=[("writer", "Writer prose.")])
        derived = _derive_context(ctx, "Writer prose.")

        writer_entries = [
            e for e in derived.pass_forward_ledger.entries if e.pass_name == "writer"
        ]
        assert len(writer_entries) == 1
        assert writer_entries[0].content == "Writer prose."

    def test_conflicting_writer_entry_raises(self) -> None:
        ctx = _make_assembled(ledger_entries=[("writer", "Original prose.")])

        with pytest.raises(ContradictionPassError, match="differs from"):
            _derive_context(ctx, "Different prose.")

    def test_multiple_writer_entries_raises(self) -> None:
        ctx = _make_assembled(
            ledger_entries=[
                ("writer", "First prose."),
                ("writer", "Second prose."),
            ]
        )

        with pytest.raises(ContradictionPassError, match="2 'writer' entries"):
            _derive_context(ctx, "Any prose.")

    def test_idempotent_via_check_service(self) -> None:
        """check() does not raise when the ledger already has the same writer entry."""
        ctx = _make_assembled(ledger_entries=[("writer", "Writer prose.")])
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())

        result = svc.check(ctx, "Writer prose.", provider=adapter)  # type: ignore[arg-type]
        assert result.verdict == ContradictionVerdict.CLEAR

    def test_conflicting_entry_raises_via_check(self) -> None:
        ctx = _make_assembled(ledger_entries=[("writer", "Old prose.")])
        adapter = _make_fake_adapter()
        svc = ContradictionService(config=_make_config())

        with pytest.raises(ContradictionPassError, match="differs from"):
            svc.check(ctx, "New prose.", provider=adapter)  # type: ignore[arg-type]

    def test_original_context_not_mutated_on_idempotent_path(self) -> None:
        ctx = _make_assembled(ledger_entries=[("writer", "Writer prose.")])
        original_len = len(ctx.pass_forward_ledger.entries)
        _derive_context(ctx, "Writer prose.")
        assert len(ctx.pass_forward_ledger.entries) == original_len

    def test_non_writer_entries_preserved_alongside_writer(self) -> None:
        ctx = _make_assembled(ledger_entries=[("planner", "Plan output.")])
        derived = _derive_context(ctx, "Writer prose.")

        entries = derived.pass_forward_ledger.entries
        assert len(entries) == 2
        assert entries[0].pass_name == "planner"
        assert entries[1].pass_name == "writer"
