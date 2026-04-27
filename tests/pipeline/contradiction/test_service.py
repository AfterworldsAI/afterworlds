"""Unit tests for ContradictionService — CRD Issue 11.

Test classes
------------
TestHappyPathClear            — clean prose returns CLEAR verdict, empty violations
TestHappyPathBlocked          — prose with violations returns BLOCKED verdict
TestVerdictDerivation         — verdict invariant: BLOCKED iff violations non-empty
TestSchemaValidation          — ContradictionViolation field_validator
TestProviderException         — provider exception → ContradictionPassError
TestMissingToolBlock          — no tool-use block → ContradictionPassError
TestEmptyViolations           — empty violations array is valid (CLEAR)
TestRendererStructure         — payload shape: model, tool_choice, system, ledger order
TestExtendedTTL               — cache_control ttl honours extended_ttl config flag
TestCallerInjection           — custom caller is invoked; default caller not constructed
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
from anthropic.types import Message, TextBlock, ToolUseBlock, Usage

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
from afterworlds.pipeline.contradiction.caller import (
    REPORT_TOOL_NAME,
    ContradictionPayload,
)
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


def _fake_tool_response(
    tool_input: dict[str, Any] | None = None,
    input_tokens: int = 100,
    output_tokens: int = 50,
    cache_read_input_tokens: int | None = None,
    cache_creation_input_tokens: int | None = None,
) -> Message:
    return Message(
        id="msg_fake_contradiction",
        type="message",
        role="assistant",
        content=[
            ToolUseBlock(
                type="tool_use",
                id="toolu_fake_01",
                name=REPORT_TOOL_NAME,
                input=tool_input if tool_input is not None else {"violations": []},
            )
        ],
        model="claude-haiku-4-5-20251001",
        stop_reason="tool_use",
        stop_sequence=None,
        usage=Usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cache_read_input_tokens,
            cache_creation_input_tokens=cache_creation_input_tokens,
        ),
    )


def _make_fake_caller(
    response: Message | None = None,
    raise_exc: Exception | None = None,
):  # type: ignore[no-untyped-def]
    captured: list[ContradictionPayload] = []

    def caller(payload: ContradictionPayload) -> Message:
        captured.append(payload)
        if raise_exc is not None:
            raise raise_exc
        return response or _fake_tool_response()

    caller.captured = captured  # type: ignore[attr-defined]
    return caller


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
        caller = _make_fake_caller(_fake_tool_response({"violations": []}))
        svc = ContradictionService(config=_make_config(), caller=caller)
        ctx = _make_assembled()

        result = svc.check(ctx, "You pocket the key and step into the corridor.")

        assert result.verdict == ContradictionVerdict.CLEAR
        assert result.violations == []

    def test_result_type(self) -> None:
        caller = _make_fake_caller(_fake_tool_response({"violations": []}))
        svc = ContradictionService(config=_make_config(), caller=caller)
        result = svc.check(_make_assembled(), "Prose here.")
        assert isinstance(result, ContradictionResult)

    def test_model_identifier_present(self) -> None:
        caller = _make_fake_caller(_fake_tool_response({"violations": []}))
        svc = ContradictionService(config=_make_config(), caller=caller)
        result = svc.check(_make_assembled(), "Prose here.")
        assert result.model_identifier == "anthropic:claude-haiku-test"


# ---------------------------------------------------------------------------
# TestHappyPathBlocked
# ---------------------------------------------------------------------------


class TestHappyPathBlocked:
    def test_returns_blocked_verdict_on_violations(self) -> None:
        viol = _make_violation_dict()
        caller = _make_fake_caller(_fake_tool_response({"violations": [viol]}))
        svc = ContradictionService(config=_make_config(), caller=caller)

        result = svc.check(_make_assembled(), "Aldric walks into the precinct.")

        assert result.verdict == ContradictionVerdict.BLOCKED
        assert len(result.violations) == 1

    def test_violation_fields_propagated(self) -> None:
        viol = _make_violation_dict(
            category="location_drift",
            description="Aldric at the precinct.",
            canon_reference="Story Bible: Aldric is at The Meridian Hotel.",
        )
        caller = _make_fake_caller(_fake_tool_response({"violations": [viol]}))
        svc = ContradictionService(config=_make_config(), caller=caller)

        result = svc.check(_make_assembled(), "Prose.")

        v = result.violations[0]
        assert v.category == ContradictionCategory.LOCATION_DRIFT
        assert v.description == "Aldric at the precinct."
        assert v.canon_reference == "Story Bible: Aldric is at The Meridian Hotel."

    def test_multiple_violations(self) -> None:
        viols = [
            _make_violation_dict("location_drift", "A at precinct.", "A is at hotel."),
            _make_violation_dict("name_drift", "Called 'Drake'.", "Name is 'Aldric'."),
        ]
        caller = _make_fake_caller(_fake_tool_response({"violations": viols}))
        svc = ContradictionService(config=_make_config(), caller=caller)

        result = svc.check(_make_assembled(), "Prose.")

        assert result.verdict == ContradictionVerdict.BLOCKED
        assert len(result.violations) == 2


# ---------------------------------------------------------------------------
# TestVerdictDerivation
# ---------------------------------------------------------------------------


class TestVerdictDerivation:
    def test_clear_when_empty(self) -> None:
        caller = _make_fake_caller(_fake_tool_response({"violations": []}))
        svc = ContradictionService(config=_make_config(), caller=caller)
        result = svc.check(_make_assembled(), "Prose.")
        assert result.verdict == ContradictionVerdict.CLEAR

    def test_blocked_when_non_empty(self) -> None:
        viol = _make_violation_dict()
        caller = _make_fake_caller(_fake_tool_response({"violations": [viol]}))
        svc = ContradictionService(config=_make_config(), caller=caller)
        result = svc.check(_make_assembled(), "Prose.")
        assert result.verdict == ContradictionVerdict.BLOCKED

    def test_verdict_not_returned_by_model(self) -> None:
        # The tool schema does not include a 'verdict' field.
        # Providing one in the tool input does not propagate to the result.
        tool_input = {
            "violations": [],
            "verdict": "BLOCKED",  # spurious field — should be ignored
        }
        caller = _make_fake_caller(_fake_tool_response(tool_input))
        svc = ContradictionService(config=_make_config(), caller=caller)
        result = svc.check(_make_assembled(), "Prose.")
        # Derived from violations list — not from the model's spurious field.
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
        # Tool input with empty description → validation fails → ContradictionPassError
        bad_input = {
            "violations": [
                {
                    "category": "location_drift",
                    "description": "",
                    "canon_reference": "Some reference.",
                }
            ]
        }
        caller = _make_fake_caller(_fake_tool_response(bad_input))
        svc = ContradictionService(config=_make_config(), caller=caller)

        with pytest.raises(ContradictionPassError, match="schema validation"):
            svc.check(_make_assembled(), "Prose.")


# ---------------------------------------------------------------------------
# TestProviderException
# ---------------------------------------------------------------------------


class TestProviderException:
    def test_provider_exception_raises_pass_error(self) -> None:
        caller = _make_fake_caller(raise_exc=RuntimeError("network timeout"))
        svc = ContradictionService(config=_make_config(), caller=caller)

        with pytest.raises(ContradictionPassError, match="provider call failed"):
            svc.check(_make_assembled(), "Prose.")

    def test_original_exception_chained(self) -> None:
        caller = _make_fake_caller(raise_exc=RuntimeError("boom"))
        svc = ContradictionService(config=_make_config(), caller=caller)

        with pytest.raises(ContradictionPassError) as exc_info:
            svc.check(_make_assembled(), "Prose.")

        assert isinstance(exc_info.value.__cause__, RuntimeError)


# ---------------------------------------------------------------------------
# TestMissingToolBlock
# ---------------------------------------------------------------------------


class TestMissingToolBlock:
    def test_no_tool_block_raises_pass_error(self) -> None:
        prose_response = Message(
            id="msg_fake",
            type="message",
            role="assistant",
            content=[TextBlock(type="text", text="The prose is fine.")],
            model="claude-haiku-4-5-20251001",
            stop_reason="end_turn",
            stop_sequence=None,
            usage=Usage(
                input_tokens=100,
                output_tokens=20,
                cache_read_input_tokens=None,
                cache_creation_input_tokens=None,
            ),
        )
        caller = _make_fake_caller(prose_response)
        svc = ContradictionService(config=_make_config(), caller=caller)

        with pytest.raises(ContradictionPassError, match="no '.*' tool-use block"):
            svc.check(_make_assembled(), "Prose.")

    def test_wrong_tool_name_raises_pass_error(self) -> None:
        wrong_name_response = Message(
            id="msg_fake",
            type="message",
            role="assistant",
            content=[
                ToolUseBlock(
                    type="tool_use",
                    id="toolu_fake",
                    name="some_other_tool",
                    input={"violations": []},
                )
            ],
            model="claude-haiku-4-5-20251001",
            stop_reason="tool_use",
            stop_sequence=None,
            usage=Usage(
                input_tokens=100,
                output_tokens=20,
                cache_read_input_tokens=None,
                cache_creation_input_tokens=None,
            ),
        )
        caller = _make_fake_caller(wrong_name_response)
        svc = ContradictionService(config=_make_config(), caller=caller)

        with pytest.raises(ContradictionPassError):
            svc.check(_make_assembled(), "Prose.")


# ---------------------------------------------------------------------------
# TestEmptyViolations
# ---------------------------------------------------------------------------


class TestEmptyViolations:
    def test_empty_array_is_valid(self) -> None:
        caller = _make_fake_caller(_fake_tool_response({"violations": []}))
        svc = ContradictionService(config=_make_config(), caller=caller)
        result = svc.check(_make_assembled(), "")
        assert result.verdict == ContradictionVerdict.CLEAR
        assert result.violations == []


# ---------------------------------------------------------------------------
# TestRendererStructure
# ---------------------------------------------------------------------------


class TestRendererStructure:
    def test_payload_model_matches_config(self) -> None:
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(_make_assembled(), "Prose.")
        payload = caller.captured[0]
        assert payload["model"] == "claude-haiku-test"

    def test_payload_tool_choice_forces_report_tool(self) -> None:
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(_make_assembled(), "Prose.")
        payload = caller.captured[0]
        assert payload["tool_choice"] == {"type": "tool", "name": REPORT_TOOL_NAME}

    def test_payload_has_system_block(self) -> None:
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(_make_assembled(), "Prose.")
        payload = caller.captured[0]
        assert len(payload["system"]) == 1
        assert payload["system"][0]["type"] == "text"

    def test_system_field_contains_contradiction_pass_prompt(self) -> None:
        """System field must be the Contradiction pass prompt, not the mode contract."""
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(_make_assembled(), "Prose.")
        payload = caller.captured[0]
        system_text = payload["system"][0]["text"]
        # The contradiction prompt is loaded from docs/prompts/contradiction.md.
        # It contains a known heading that must appear here.
        assert "Contradiction Checker" in system_text

    def test_stable_prefix_user_blocks_contain_mode_contract(self) -> None:
        """stable_prefix.system_prompt (mode contract) must appear in user blocks."""
        MODE_CONTRACT = "UNIQUE-MODE-CONTRACT-SENTINEL"
        ctx = _make_assembled()
        from afterworlds.models.context import StablePrefix

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
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(ctx2, "Prose.")

        texts = [b["text"] for b in caller.captured[0]["messages"][0]["content"]]
        assert any(
            MODE_CONTRACT in t for t in texts
        ), "stable_prefix.system_prompt not found in user message blocks"

    def test_mode_contract_appears_before_story_bible(self) -> None:
        """stable_prefix.system_prompt must be the first stable-prefix user block."""
        MODE_CONTRACT = "UNIQUE-MODE-CONTRACT-SENTINEL"
        STORY_BIBLE_MARKER = (
            "Aldric"  # appears in the cast entry rendered by the context
        )
        ctx = _make_assembled()
        from afterworlds.models.context import StablePrefix

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
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(ctx2, "Prose.")

        texts = [b["text"] for b in caller.captured[0]["messages"][0]["content"]]
        contract_idx = next(
            (i for i, t in enumerate(texts) if MODE_CONTRACT in t), None
        )
        bible_idx = next(
            (i for i, t in enumerate(texts) if STORY_BIBLE_MARKER in t), None
        )
        assert contract_idx is not None, "Mode contract block not found"
        assert bible_idx is not None, "Story Bible block not found"
        assert (
            contract_idx < bible_idx
        ), "Mode contract must appear before Story Bible content"

    def test_cache_breakpoint_on_last_stable_prefix_block_not_writer(self) -> None:
        """Cache breakpoint on the final stable-prefix block, before writer/volatile."""
        caller = _make_fake_caller()
        svc = ContradictionService(
            config=_make_config(extended_ttl=True), caller=caller
        )
        svc.check(_make_assembled(), "Writer prose here.")

        content = caller.captured[0]["messages"][0]["content"]
        cache_idx = next(
            (i for i, b in enumerate(content) if b.get("cache_control") is not None),
            None,
        )
        writer_idx = next(
            (
                i
                for i, b in enumerate(content)
                if "[WRITER OUTPUT]" in b.get("text", "")
            ),
            None,
        )
        volatile_idx = next(
            (
                i
                for i, b in enumerate(content)
                if "I step into the corridor." in b.get("text", "")
            ),
            None,
        )
        assert cache_idx is not None, "No cache_control block found"
        assert writer_idx is not None, "No writer output block found"
        assert volatile_idx is not None, "No volatile suffix block found"
        assert (
            cache_idx < writer_idx
        ), "Cache breakpoint must precede writer output block"
        assert (
            cache_idx < volatile_idx
        ), "Cache breakpoint must precede volatile suffix block"

    def test_writer_output_in_ledger_before_volatile_suffix(self) -> None:
        """Writer output must appear before recent turns / current input."""
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        writer_output = "THE WRITER PROSE HERE"
        svc.check(_make_assembled(), writer_output)

        payload = caller.captured[0]
        messages = payload["messages"]
        assert len(messages) == 1
        content_blocks = messages[0]["content"]

        # Find the block containing the writer output and the volatile suffix block.
        texts = [b["text"] for b in content_blocks]
        writer_idx = next((i for i, t in enumerate(texts) if writer_output in t), None)
        volatile_idx = next(
            (i for i, t in enumerate(texts) if "I step into the corridor." in t), None
        )
        assert writer_idx is not None, "Writer output not found in payload"
        assert volatile_idx is not None, "Volatile suffix not found in payload"
        assert (
            writer_idx < volatile_idx
        ), "Writer output block must appear before volatile suffix block"

    def test_writer_output_formatted_as_ledger_entry(self) -> None:
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        writer_output = "You step into the corridor."
        svc.check(_make_assembled(), writer_output)

        payload = caller.captured[0]
        texts = [b["text"] for b in payload["messages"][0]["content"]]
        ledger_block = next((t for t in texts if "[WRITER OUTPUT]" in t), None)
        assert ledger_block is not None, "No [WRITER OUTPUT] ledger block found"
        assert writer_output in ledger_block

    def test_tool_spec_in_payload(self) -> None:
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(_make_assembled(), "Prose.")
        payload = caller.captured[0]
        assert len(payload["tools"]) == 1
        assert payload["tools"][0]["name"] == REPORT_TOOL_NAME


# ---------------------------------------------------------------------------
# TestExtendedTTL
# ---------------------------------------------------------------------------


class TestExtendedTTL:
    def test_extended_ttl_true_sets_1h(self) -> None:
        caller = _make_fake_caller()
        svc = ContradictionService(
            config=_make_config(extended_ttl=True), caller=caller
        )
        svc.check(_make_assembled(), "Prose.")

        payload = caller.captured[0]
        blocks_with_cache = [
            b
            for b in payload["messages"][0]["content"]
            if b.get("cache_control") is not None
        ]
        assert blocks_with_cache, "No cache_control block found"
        assert blocks_with_cache[-1]["cache_control"]["ttl"] == "1h"

    def test_extended_ttl_false_sets_5m(self) -> None:
        caller = _make_fake_caller()
        svc = ContradictionService(
            config=_make_config(extended_ttl=False), caller=caller
        )
        svc.check(_make_assembled(), "Prose.")

        payload = caller.captured[0]
        blocks_with_cache = [
            b
            for b in payload["messages"][0]["content"]
            if b.get("cache_control") is not None
        ]
        assert blocks_with_cache, "No cache_control block found"
        assert blocks_with_cache[-1]["cache_control"]["ttl"] == "5m"

    def test_cache_control_on_last_stable_prefix_block(self) -> None:
        """Cache breakpoint on the final stable-prefix block, not writer output."""
        caller = _make_fake_caller()
        svc = ContradictionService(
            config=_make_config(extended_ttl=True), caller=caller
        )
        svc.check(_make_assembled(), "Writer prose goes here.")

        payload = caller.captured[0]
        content = payload["messages"][0]["content"]
        cache_idx = next(
            (i for i, b in enumerate(content) if b.get("cache_control") is not None),
            None,
        )
        writer_idx = next(
            (
                i
                for i, b in enumerate(content)
                if "[WRITER OUTPUT]" in b.get("text", "")
            ),
            None,
        )
        assert cache_idx is not None
        assert writer_idx is not None
        assert (
            cache_idx < writer_idx
        ), "Cache breakpoint must be on stable prefix, before writer output block"


# ---------------------------------------------------------------------------
# TestCallerInjection
# ---------------------------------------------------------------------------


class TestCallerInjection:
    def test_injected_caller_is_used(self) -> None:
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(_make_assembled(), "Prose.")
        assert len(caller.captured) == 1

    def test_caller_receives_one_call_per_check(self) -> None:
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(_make_assembled(), "Prose 1.")
        svc.check(_make_assembled(), "Prose 2.")
        assert len(caller.captured) == 2


# ---------------------------------------------------------------------------
# TestCacheMetricsPropagation
# ---------------------------------------------------------------------------


class TestCacheMetricsPropagation:
    def test_all_token_counts_propagated(self) -> None:
        response = _fake_tool_response(
            input_tokens=200,
            output_tokens=60,
            cache_read_input_tokens=150,
            cache_creation_input_tokens=50,
        )
        caller = _make_fake_caller(response)
        svc = ContradictionService(config=_make_config(), caller=caller)
        result = svc.check(_make_assembled(), "Prose.")

        assert result.input_token_count == 200
        assert result.output_token_count == 60
        assert result.cache_read_token_count == 150
        assert result.cache_creation_token_count == 50

    def test_none_cache_counts_allowed(self) -> None:
        response = _fake_tool_response(
            input_tokens=100,
            output_tokens=40,
            cache_read_input_tokens=None,
            cache_creation_input_tokens=None,
        )
        caller = _make_fake_caller(response)
        svc = ContradictionService(config=_make_config(), caller=caller)
        result = svc.check(_make_assembled(), "Prose.")

        assert result.cache_read_token_count is None
        assert result.cache_creation_token_count is None

    def test_latency_ms_is_non_negative_int(self) -> None:
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        result = svc.check(_make_assembled(), "Prose.")
        assert isinstance(result.latency_ms, int)
        assert result.latency_ms >= 0


# ---------------------------------------------------------------------------
# TestBuiltContextImmutability
# ---------------------------------------------------------------------------


class TestBuiltContextImmutability:
    def test_caller_context_not_mutated(self) -> None:
        ctx = _make_assembled()
        original_entry_count = len(ctx.pass_forward_ledger.entries)

        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(ctx, "Writer prose.")

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
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)
        svc.check(ctx, "Writer prose.")

        payload = caller.captured[0]
        texts = [b["text"] for b in payload["messages"][0]["content"]]
        ledger_text = next((t for t in texts if "[PLANNER OUTPUT]" in t), None)
        assert ledger_text is not None, "Pre-existing ledger entry not found in payload"

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
        config = ContradictionConfig(model="my-custom-model", api_key_env="KEY_ENV")
        caller = _make_fake_caller()
        svc = ContradictionService(config=config, caller=caller)
        result = svc.check(_make_assembled(), "Prose.")
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
        caller = _make_fake_caller(_fake_tool_response({"violations": [viol]}))
        svc = ContradictionService(config=_make_config(), caller=caller)
        result = svc.check(_make_assembled(), "Prose.")
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
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)

        result = svc.check(ctx, "Writer prose.")
        assert result.verdict == ContradictionVerdict.CLEAR

    def test_conflicting_entry_raises_via_check(self) -> None:
        ctx = _make_assembled(ledger_entries=[("writer", "Old prose.")])
        caller = _make_fake_caller()
        svc = ContradictionService(config=_make_config(), caller=caller)

        with pytest.raises(ContradictionPassError, match="differs from"):
            svc.check(ctx, "New prose.")

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
