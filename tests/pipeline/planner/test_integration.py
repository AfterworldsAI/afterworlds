"""Default-CI integration tests for PlannerService — CRD Issue 12a.

Uses a high-fidelity fake caller with two scripted scenarios:
  - Scenario A: action input → well-formed plan with notes
  - Scenario B: exploration input → plan with empty facts_needed and no notes

These tests run in default CI (no special env flags required).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from anthropic.types import Message, ToolUseBlock, Usage

from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    RetrievalMemoryPayload,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import CastRole, IntentType
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.story_bible import CastEntry, StoryBibleContext
from afterworlds.pipeline.planner.caller import PRODUCE_PLAN_TOOL_NAME
from afterworlds.pipeline.planner.config import PlannerConfig
from afterworlds.pipeline.planner.service import PlannerService

# ---------------------------------------------------------------------------
# Shared context factory
# ---------------------------------------------------------------------------


def _make_context(current_input: str = "I try to pick the lock.") -> AssembledContext:
    story_id = uuid4()
    ctx = StoryBibleContext(
        story_id=story_id,
        setting=None,
        cast=(
            CastEntry(
                story_id=story_id,
                name="Aldric Crane",
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
        system_prompt="You are the Sojourn story planner.",
        story_bible_context=ctx,
        rolling_summary_text=None,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )
    icr = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.95,
        raw_input=current_input,
        ambiguous=False,
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input=current_input,
        classified_intent=icr,
    )
    return AssembledContext(
        stable_prefix=sp,
        volatile_suffix=vs,
        pass_forward_ledger=PassForwardLedger(),
    )


# ---------------------------------------------------------------------------
# High-fidelity fake
# ---------------------------------------------------------------------------


def _scripted_caller(tool_inputs: list[dict]) -> object:  # type: ignore[type-arg]
    """Return a caller that plays back scripted tool inputs in order."""
    responses = [
        Message(
            id=f"msg_fake_{i}",
            type="message",
            role="assistant",
            content=[
                ToolUseBlock(
                    type="tool_use",
                    id=f"toolu_fake_{i}",
                    name=PRODUCE_PLAN_TOOL_NAME,
                    input=ti,
                )
            ],
            model="claude-haiku-4-5-20251001",
            stop_reason="tool_use",
            stop_sequence=None,
            usage=Usage(
                input_tokens=120,
                output_tokens=60,
                cache_read_input_tokens=90,
                cache_creation_input_tokens=None,
            ),
        )
        for i, ti in enumerate(tool_inputs)
    ]
    idx = [0]

    def caller(payload: object) -> Message:  # type: ignore[type-arg]
        response = responses[idx[0]]
        idx[0] += 1
        return response

    return caller


# ---------------------------------------------------------------------------
# Scenario A — action input with notes
# ---------------------------------------------------------------------------


class TestScenarioAWithNotes:
    SCRIPTED_PLAN = {
        "scene_goal": "Escape room 14 without being detected.",
        "next_beat": "Aldric Crane picks the lock and slips into the corridor.",
        "facts_needed": [
            "Aldric has a lockpick.",
            "Corridor is monitored at midnight.",
        ],
        "notes": "Keep prose tense; use short sentences.",
    }

    def _make_svc(self) -> PlannerService:
        config = PlannerConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        svc = PlannerService(
            config=config,
            caller=_scripted_caller([self.SCRIPTED_PLAN]),  # type: ignore[arg-type]
        )
        svc._system_prompt = "PLANNER PROMPT"
        return svc

    def test_scene_goal_present(self) -> None:
        result = self._make_svc().plan(_make_context("I try to pick the lock."))
        assert result.scene_goal == "Escape room 14 without being detected."

    def test_next_beat_present(self) -> None:
        result = self._make_svc().plan(_make_context("I try to pick the lock."))
        assert "Aldric Crane" in result.next_beat

    def test_facts_needed_populated(self) -> None:
        result = self._make_svc().plan(_make_context("I try to pick the lock."))
        assert len(result.facts_needed) == 2
        assert any("lockpick" in f for f in result.facts_needed)

    def test_notes_present(self) -> None:
        result = self._make_svc().plan(_make_context("I try to pick the lock."))
        assert result.notes is not None
        assert "tense" in result.notes

    def test_token_metrics_present(self) -> None:
        result = self._make_svc().plan(_make_context("I try to pick the lock."))
        assert result.input_token_count == 120
        assert result.output_token_count == 60
        assert result.cache_read_token_count == 90
        assert result.cache_creation_token_count is None

    def test_model_identifier(self) -> None:
        result = self._make_svc().plan(_make_context("I try to pick the lock."))
        assert result.model_identifier == "anthropic:claude-haiku-test"


# ---------------------------------------------------------------------------
# Scenario B — exploration input, no notes
# ---------------------------------------------------------------------------


class TestScenarioBNoNotes:
    SCRIPTED_PLAN = {
        "scene_goal": "Let the player explore the room.",
        "next_beat": "Aldric Crane surveys the hotel room.",
        "facts_needed": [],
    }

    def _make_svc(self) -> PlannerService:
        config = PlannerConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        svc = PlannerService(
            config=config,
            caller=_scripted_caller([self.SCRIPTED_PLAN]),  # type: ignore[arg-type]
        )
        svc._system_prompt = "PLANNER PROMPT"
        return svc

    def test_facts_needed_empty(self) -> None:
        result = self._make_svc().plan(_make_context("I look around the room."))
        assert result.facts_needed == []

    def test_notes_none(self) -> None:
        result = self._make_svc().plan(_make_context("I look around the room."))
        assert result.notes is None

    def test_context_not_mutated(self) -> None:
        ctx = _make_context("I look around the room.")
        original_len = len(ctx.pass_forward_ledger.entries)

        self._make_svc().plan(ctx)

        assert len(ctx.pass_forward_ledger.entries) == original_len
