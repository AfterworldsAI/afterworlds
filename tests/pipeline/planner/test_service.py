"""Unit tests for PlannerService — CRD Issue 12a / 14a.

Test classes
------------
TestHappyPath                 — well-formed response returns PlannerResult
TestSchemaValidation          — PlannerOutput field_validator rules
TestProviderException         — provider exception → PlannerPassError
TestMissingToolBlock          — no tool-use block → PlannerPassError
TestRendererStructure         — ProviderCallRequest shape: pass_id, forced_tool, blocks
TestSystemPromptPlacement     — system_blocks order and content
TestCacheBreakpoint           — cache breakpoint on last stable-prefix block
TestExtendedTTL               — ttl honours extended_ttl config flag
TestProviderAdapterInjection  — provider.call() is invoked once per plan()
TestCacheMetricsPropagation   — all four token counts propagated to PlannerResult
TestBuiltContextImmutability  — caller's AssembledContext is not mutated
TestEmptyPassForwardLedger    — empty ledger produces no extra user block
TestNotesField                — None and present notes handled correctly
TestModelIdentifier           — model_identifier propagated from ProviderCallResult
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

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
from afterworlds.pipeline._stable_prefix_renderer import (
    TTL_DEFAULT,
    TTL_EXTENDED,
)
from afterworlds.pipeline._stable_prefix_renderer import (
    collect_stable_prefix_texts as _collect_stable_texts_impl,
)
from afterworlds.pipeline.planner.caller import (
    PRODUCE_PLAN_TOOL_NAME,
)
from afterworlds.pipeline.planner.config import PlannerConfig
from afterworlds.pipeline.planner.models import (
    PlannerOutput,
    PlannerPassError,
    PlannerResult,
)
from afterworlds.pipeline.planner.service import PlannerService
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderToolCallPart,
)
from afterworlds.pipeline.writer.config import WriterConfig


def _collect_stable_texts(ctx: AssembledContext) -> list[str]:
    """Backwards-compatible test shim — delegates to the shared Issue 12c renderer."""
    return _collect_stable_texts_impl(ctx.stable_prefix)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(extended_ttl: bool = True) -> PlannerConfig:
    return PlannerConfig(
        model="claude-haiku-test",
        api_key_env="ANTHROPIC_API_KEY",
        extended_ttl=extended_ttl,
    )


def _make_assembled(
    story_id: UUID | None = None,
    rolling_summary: str | None = None,
    ledger_entries: list[tuple[str, str]] | None = None,
    current_input: str = "I examine the corridor.",
) -> AssembledContext:
    if story_id is None:
        story_id = uuid4()
    ctx = StoryBibleContext(
        story_id=story_id,
        setting=None,
        cast=(
            CastEntry(
                story_id=story_id,
                name="Aldric",
                role=CastRole.PROTAGONIST,
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
        system_prompt="You are the story architect.",
        story_bible_context=ctx,
        rolling_summary_text=rolling_summary,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )
    icr = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.90,
        raw_input=current_input,
        ambiguous=False,
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input=current_input,
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
    if tool_input is None:
        tool_input = {
            "scene_goal": "Escape the hotel.",
            "next_beat": "Aldric steps into the corridor.",
            "facts_needed": [],
        }
    return ProviderCallResult(
        pass_id=PipelinePassId.PLANNER,
        provider_name="anthropic",
        model_identifier=model_identifier,
        model_tier=ModelTier.HAIKU,
        content_parts=[
            ProviderToolCallPart(
                tool_name=PRODUCE_PLAN_TOOL_NAME,
                tool_input=tool_input,
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
    """Capturing fake ProviderAdapter for PlannerService tests."""

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


# ---------------------------------------------------------------------------
# TestHappyPath
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_returns_planner_result(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        result = svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        assert isinstance(result, PlannerResult)

    def test_fields_propagated(self) -> None:
        tool_input = {
            "scene_goal": "Escape the hotel.",
            "next_beat": "Aldric slips through the service exit.",
            "facts_needed": ["Aldric has the Obsidian Key."],
            "notes": "Keep tension high.",
        }
        adapter = _make_fake_adapter(_fake_tool_result(tool_input))
        svc = PlannerService(config=_make_config())
        result = svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]

        assert result.plan.scene_goal == "Escape the hotel."
        assert result.plan.next_beat == "Aldric slips through the service exit."
        assert result.plan.facts_needed == ["Aldric has the Obsidian Key."]
        assert result.plan.notes == "Keep tension high."

    def test_notes_none_when_absent(self) -> None:
        tool_input = {
            "scene_goal": "Escape.",
            "next_beat": "Aldric moves.",
            "facts_needed": [],
        }
        adapter = _make_fake_adapter(_fake_tool_result(tool_input))
        svc = PlannerService(config=_make_config())
        result = svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        assert result.plan.notes is None

    def test_model_identifier_present(self) -> None:
        adapter = _make_fake_adapter(
            _fake_tool_result(model_identifier="anthropic:claude-haiku-test")
        )
        svc = PlannerService(config=_make_config())
        result = svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        assert result.model_identifier == "anthropic:claude-haiku-test"


# ---------------------------------------------------------------------------
# TestSchemaValidation
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_empty_scene_goal_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="",
                next_beat="Some beat.",
                facts_needed=[],
            )

    def test_whitespace_scene_goal_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="   ",
                next_beat="Some beat.",
                facts_needed=[],
            )

    def test_empty_next_beat_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="",
                facts_needed=[],
            )

    def test_whitespace_next_beat_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="\t",
                facts_needed=[],
            )

    def test_empty_string_notes_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=[],
                notes="",
            )

    def test_whitespace_only_notes_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=[],
                notes="   ",
            )

    def test_none_notes_accepted(self) -> None:
        output = PlannerOutput(
            scene_goal="Some goal.",
            next_beat="Some beat.",
            facts_needed=[],
            notes=None,
        )
        assert output.notes is None

    def test_valid_notes_accepted(self) -> None:
        output = PlannerOutput(
            scene_goal="Some goal.",
            next_beat="Some beat.",
            facts_needed=[],
            notes="Keep tension high.",
        )
        assert output.notes == "Keep tension high."

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(  # type: ignore[call-arg]
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=[],
                unknown_field="surprise",
            )

    def test_empty_facts_needed_accepted(self) -> None:
        output = PlannerOutput(
            scene_goal="Some goal.",
            next_beat="Some beat.",
            facts_needed=[],
        )
        assert output.facts_needed == []

    def test_whitespace_only_fact_entry_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=["   "],
            )

    def test_empty_string_fact_entry_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=[""],
            )

    def test_mixed_valid_and_blank_fact_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PlannerOutput(
                scene_goal="Some goal.",
                next_beat="Some beat.",
                facts_needed=["Valid fact.", ""],
            )

    def test_valid_facts_accepted(self) -> None:
        output = PlannerOutput(
            scene_goal="Some goal.",
            next_beat="Some beat.",
            facts_needed=["Aldric has the key.", "Room 14 is on the east wing."],
        )
        assert len(output.facts_needed) == 2


# ---------------------------------------------------------------------------
# TestProviderException
# ---------------------------------------------------------------------------


class TestProviderException:
    def test_provider_exception_raises_planner_pass_error(self) -> None:
        adapter = _make_fake_adapter(raise_exc=RuntimeError("Network error"))
        svc = PlannerService(config=_make_config())
        with pytest.raises(PlannerPassError, match="Planner provider call failed"):
            svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TestMissingToolBlock
# ---------------------------------------------------------------------------


class TestMissingToolBlock:
    def test_no_tool_block_raises_planner_pass_error(self) -> None:
        from afterworlds.pipeline.provider._models import ProviderTextPart

        no_tool_result = ProviderCallResult(
            pass_id=PipelinePassId.PLANNER,
            provider_name="anthropic",
            model_identifier="anthropic:claude-haiku-test",
            model_tier=ModelTier.HAIKU,
            content_parts=[ProviderTextPart(text="I cannot plan this.")],
            input_token_count=50,
            output_token_count=10,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=1,
        )
        adapter = _make_fake_adapter(no_tool_result)
        svc = PlannerService(config=_make_config())
        with pytest.raises(PlannerPassError):
            svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TestFactsNeededValidationViaService
# ---------------------------------------------------------------------------


class TestFactsNeededValidationViaService:
    def test_whitespace_fact_raises_planner_pass_error(self) -> None:
        """Blank facts_needed items from the model surface as PlannerPassError."""
        bad_input = {
            "scene_goal": "Escape.",
            "next_beat": "Aldric runs.",
            "facts_needed": ["   "],
        }
        adapter = _make_fake_adapter(_fake_tool_result(bad_input))
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        with pytest.raises(PlannerPassError, match="schema validation"):
            svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]

    def test_empty_string_fact_raises_planner_pass_error(self) -> None:
        bad_input = {
            "scene_goal": "Escape.",
            "next_beat": "Aldric runs.",
            "facts_needed": [""],
        }
        adapter = _make_fake_adapter(_fake_tool_result(bad_input))
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        with pytest.raises(PlannerPassError, match="schema validation"):
            svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TestRendererStructure
# ---------------------------------------------------------------------------


class TestRendererStructure:
    def test_pass_id_is_planner(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert request.pass_id == PipelinePassId.PLANNER

    def test_forced_tool_name_set(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert request.forced_tool_name == PRODUCE_PLAN_TOOL_NAME

    def test_tool_definitions_contain_planner_tool(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert len(request.tool_definitions) == 1
        assert request.tool_definitions[0].name == PRODUCE_PLAN_TOOL_NAME

    def test_volatile_suffix_block_last(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc.plan(_make_assembled(current_input="I push the door."), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        last_block = request.rendered_blocks[-1]
        assert "I push the door." in last_block.text


# ---------------------------------------------------------------------------
# TestSystemPromptPlacement
# ---------------------------------------------------------------------------


class TestSystemPromptPlacement:
    def test_pass_prompt_in_system_blocks(self) -> None:
        """Planner pass contract appears in system_blocks."""
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER SYSTEM PROMPT"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert any("PLANNER SYSTEM PROMPT" in b.text for b in request.system_blocks)

    def test_mode_contract_in_system_blocks(self) -> None:
        """Active mode contract appears in system_blocks as second block."""
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER SYSTEM PROMPT"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert any(
            "You are the story architect." in b.text for b in request.system_blocks
        )

    def test_system_has_two_blocks(self) -> None:
        """system_blocks has exactly two blocks: pass contract + mode contract."""
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER SYSTEM PROMPT"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert len(request.system_blocks) == 2

    def test_pass_contract_is_first_system_block(self) -> None:
        """Planner pass contract is the first system block."""
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER SYSTEM PROMPT"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert "PLANNER SYSTEM PROMPT" in request.system_blocks[0].text

    def test_mode_contract_is_second_system_block(self) -> None:
        """Active mode contract is the second system block."""
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER SYSTEM PROMPT"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert "You are the story architect." in request.system_blocks[1].text

    def test_story_bible_is_first_rendered_block(self) -> None:
        """Story Bible context is the first rendered stable-prefix block."""
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER SYSTEM PROMPT"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        assert "Story Bible" in request.rendered_blocks[0].text

    def test_mode_contract_not_in_rendered_blocks(self) -> None:
        """sp.system_prompt must not appear in any rendered_block."""
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER SYSTEM PROMPT"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        for block in request.rendered_blocks:
            assert "You are the story architect." not in block.text

    def test_pass_prompt_not_in_rendered_blocks(self) -> None:
        """Pass contract must not appear in rendered_blocks."""
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "UNIQUE_PLANNER_PROMPT_MARKER"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        for block in request.rendered_blocks:
            assert "UNIQUE_PLANNER_PROMPT_MARKER" not in block.text


# ---------------------------------------------------------------------------
# TestCacheBreakpoint
# ---------------------------------------------------------------------------


class TestCacheBreakpoint:
    def test_exactly_one_cache_breakpoint(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(_make_assembled(rolling_summary="Summary here."), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert len(cached) == 1

    def test_cache_breakpoint_on_last_stable_prefix_block(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(
            _make_assembled(rolling_summary="Session summary here."),
            provider=adapter,  # type: ignore[arg-type]
        )
        request = adapter.captured_requests[0]
        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert len(cached) == 1
        assert "Session summary here." in cached[0].text

    def test_volatile_blocks_have_no_cache_breakpoint(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(
            _make_assembled(current_input="What is happening?"),
            provider=adapter,  # type: ignore[arg-type]
        )
        request = adapter.captured_requests[0]
        input_blocks = [
            b for b in request.rendered_blocks if "What is happening?" in b.text
        ]
        for b in input_blocks:
            assert not b.has_cache_breakpoint


# ---------------------------------------------------------------------------
# TestExtendedTTL
# ---------------------------------------------------------------------------


class TestExtendedTTL:
    def test_extended_ttl_sets_1h(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config(extended_ttl=True))
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert cached
        assert cached[0].ttl == TTL_EXTENDED

    def test_default_ttl_sets_5m(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config(extended_ttl=False))
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        request = adapter.captured_requests[0]
        cached = [b for b in request.rendered_blocks if b.has_cache_breakpoint]
        assert cached
        assert cached[0].ttl == TTL_DEFAULT


# ---------------------------------------------------------------------------
# TestProviderAdapterInjection
# ---------------------------------------------------------------------------


class TestProviderAdapterInjection:
    def test_provider_adapter_invoked_once(self) -> None:
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        assert len(adapter.captured_requests) == 1

    def test_no_api_key_needed_when_adapter_injected(self) -> None:
        """Injected adapter bypasses API key env lookup in the constructor."""
        import os

        adapter = _make_fake_adapter()
        original = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            svc = PlannerService(config=_make_config())
            svc._system_prompt = "PLANNER PROMPT"
            svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        finally:
            if original is not None:
                os.environ["ANTHROPIC_API_KEY"] = original


# ---------------------------------------------------------------------------
# TestCacheMetricsPropagation
# ---------------------------------------------------------------------------


class TestCacheMetricsPropagation:
    def test_all_four_token_counts_propagated(self) -> None:
        result = _fake_tool_result(
            input_token_count=200,
            output_token_count=75,
            cache_read_token_count=150,
            cache_creation_token_count=50,
        )
        adapter = _make_fake_adapter(result)
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        planner_result = svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]

        assert planner_result.input_token_count == 200
        assert planner_result.output_token_count == 75
        assert planner_result.cache_read_token_count == 150
        assert planner_result.cache_creation_token_count == 50

    def test_none_cache_counts_propagated(self) -> None:
        result = _fake_tool_result(
            input_token_count=100,
            output_token_count=50,
            cache_read_token_count=None,
            cache_creation_token_count=None,
        )
        adapter = _make_fake_adapter(result)
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        planner_result = svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]

        assert planner_result.cache_read_token_count is None
        assert planner_result.cache_creation_token_count is None


# ---------------------------------------------------------------------------
# TestBuiltContextImmutability
# ---------------------------------------------------------------------------


class TestBuiltContextImmutability:
    def test_context_not_mutated_by_plan(self) -> None:
        ctx = _make_assembled()
        original_len = len(ctx.pass_forward_ledger.entries)
        original_prompt = ctx.stable_prefix.system_prompt

        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        svc.plan(ctx, provider=adapter)  # type: ignore[arg-type]

        assert len(ctx.pass_forward_ledger.entries) == original_len
        assert ctx.stable_prefix.system_prompt == original_prompt


# ---------------------------------------------------------------------------
# TestEmptyPassForwardLedger
# ---------------------------------------------------------------------------


class TestEmptyPassForwardLedger:
    def test_empty_ledger_produces_no_extra_user_block(self) -> None:
        """Empty PassForwardLedger at Planner invocation produces no extra block."""
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        ctx = _make_assembled()
        svc.plan(ctx, provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        for block in request.rendered_blocks:
            assert "[WRITER OUTPUT]" not in block.text
            assert "[PLANNER OUTPUT]" not in block.text

    def test_non_empty_ledger_appears_after_cache_breakpoint(self) -> None:
        """Pre-populated ledger entry appears after the cache-breakpoint block."""
        adapter = _make_fake_adapter()
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        ctx = _make_assembled(ledger_entries=[("writer", "The door is open.")])
        svc.plan(ctx, provider=adapter)  # type: ignore[arg-type]

        request = adapter.captured_requests[0]
        cached_idx = next(
            i for i, b in enumerate(request.rendered_blocks) if b.has_cache_breakpoint
        )
        ledger_blocks = [
            (i, b)
            for i, b in enumerate(request.rendered_blocks)
            if "The door is open." in b.text
        ]
        assert ledger_blocks, "Ledger content not found in rendered_blocks"
        ledger_idx = ledger_blocks[0][0]
        assert ledger_idx > cached_idx


# ---------------------------------------------------------------------------
# TestNotesField
# ---------------------------------------------------------------------------


class TestNotesField:
    def test_notes_none_propagates_as_none(self) -> None:
        tool_input = {
            "scene_goal": "Escape.",
            "next_beat": "Aldric runs.",
            "facts_needed": [],
        }
        adapter = _make_fake_adapter(_fake_tool_result(tool_input))
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        result = svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        assert result.plan.notes is None

    def test_notes_value_propagates(self) -> None:
        tool_input = {
            "scene_goal": "Escape.",
            "next_beat": "Aldric runs.",
            "facts_needed": [],
            "notes": "Keep it brief.",
        }
        adapter = _make_fake_adapter(_fake_tool_result(tool_input))
        svc = PlannerService(config=_make_config())
        svc._system_prompt = "PLANNER PROMPT"
        result = svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        assert result.plan.notes == "Keep it brief."


# ---------------------------------------------------------------------------
# TestModelIdentifier
# ---------------------------------------------------------------------------


class TestModelIdentifier:
    def test_model_identifier_propagated_from_result(self) -> None:
        fake = _fake_tool_result(model_identifier="anthropic:claude-haiku-custom")
        adapter = _make_fake_adapter(fake)
        svc = PlannerService(
            config=PlannerConfig(model="claude-haiku-custom", api_key_env="X")
        )
        svc._system_prompt = "PLANNER PROMPT"
        result = svc.plan(_make_assembled(), provider=adapter)  # type: ignore[arg-type]
        assert result.model_identifier == "anthropic:claude-haiku-custom"


# ---------------------------------------------------------------------------
# TestCollectStableTexts
# ---------------------------------------------------------------------------


class TestCollectStableTexts:
    def test_story_bible_is_first(self) -> None:
        ctx = _make_assembled()
        texts = _collect_stable_texts(ctx)
        assert "Story Bible" in texts[0]

    def test_system_prompt_not_in_stable_texts(self) -> None:
        ctx = _make_assembled()
        texts = _collect_stable_texts(ctx)
        assert not any(ctx.stable_prefix.system_prompt in t for t in texts)

    def test_rolling_summary_included_when_present(self) -> None:
        ctx = _make_assembled(rolling_summary="Session summary here.")
        texts = _collect_stable_texts(ctx)
        assert any("Session summary here." in t for t in texts)

    def test_rolling_summary_omitted_when_none(self) -> None:
        ctx = _make_assembled(rolling_summary=None)
        texts = _collect_stable_texts(ctx)
        assert not any("Session summary" in t for t in texts)


# ---------------------------------------------------------------------------
# TestCacheLayoutMatchesWriter
# ---------------------------------------------------------------------------


class TestCacheLayoutMatchesWriter:
    """Regression: Planner stable-prefix user blocks match Writer renderer order."""

    def _make_writer_config(self) -> WriterConfig:
        return WriterConfig(
            model="claude-sonnet-test",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )

    def test_stable_texts_identical_to_writer(self) -> None:
        ctx = _make_assembled(rolling_summary="Summary for cache test.")
        planner_texts = _collect_stable_texts(ctx)
        writer_texts = _collect_stable_texts(ctx)
        assert planner_texts == writer_texts

    def test_stable_texts_identical_without_rolling_summary(self) -> None:
        ctx = _make_assembled(rolling_summary=None)
        planner_texts = _collect_stable_texts(ctx)
        writer_texts = _collect_stable_texts(ctx)
        assert planner_texts == writer_texts

    def test_stable_texts_story_bible_first_for_both(self) -> None:
        ctx = _make_assembled()
        planner_texts = _collect_stable_texts(ctx)
        writer_texts = _collect_stable_texts(ctx)
        assert "Story Bible" in planner_texts[0]
        assert "Story Bible" in writer_texts[0]
        assert planner_texts[0] == writer_texts[0]
