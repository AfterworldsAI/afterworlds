"""Default-CI integration tests for ContradictionService — CRD Issue 11.

Uses a high-fidelity fake caller with two scripted scenarios:
  - Scenario A: clean prose → CLEAR verdict, no violations
  - Scenario B: location-drift prose → BLOCKED verdict, one violation

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
from afterworlds.pipeline.contradiction.caller import REPORT_TOOL_NAME
from afterworlds.pipeline.contradiction.config import ContradictionConfig
from afterworlds.pipeline.contradiction.models import ContradictionVerdict
from afterworlds.pipeline.contradiction.service import ContradictionService

# ---------------------------------------------------------------------------
# Shared context factory
# ---------------------------------------------------------------------------


def _make_context() -> AssembledContext:
    story_id = uuid4()
    ctx = StoryBibleContext(
        story_id=story_id,
        setting=None,
        cast=(
            CastEntry(
                cast_id=uuid4(),
                story_id=story_id,
                name="Aldric Crane",
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
        confidence=0.95,
        raw_input="I check the corridor.",
        ambiguous=False,
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input="I check the corridor.",
        classified_intent=icr,
    )
    return AssembledContext(
        stable_prefix=sp,
        volatile_suffix=vs,
        pass_forward_ledger=PassForwardLedger(),
    )


# ---------------------------------------------------------------------------
# High-fidelity fakes
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
                    name=REPORT_TOOL_NAME,
                    input=ti,
                )
            ],
            model="claude-haiku-4-5-20251001",
            stop_reason="tool_use",
            stop_sequence=None,
            usage=Usage(
                input_tokens=120,
                output_tokens=40,
                cache_read_input_tokens=80,
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
# Scenario A — clean prose
# ---------------------------------------------------------------------------


class TestScenarioAClear:
    WRITER_OUTPUT = (
        "You pocket the Obsidian Key and step into the corridor. "
        "The Meridian's red-carpeted hallway stretches ahead."
    )

    def test_verdict_clear(self) -> None:
        fake = _scripted_caller([{"violations": []}])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        svc = ContradictionService(config=config, caller=fake)  # type: ignore[arg-type]
        result = svc.check(_make_context(), self.WRITER_OUTPUT)

        assert result.verdict == ContradictionVerdict.CLEAR
        assert result.violations == []

    def test_token_metrics_present(self) -> None:
        fake = _scripted_caller([{"violations": []}])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        svc = ContradictionService(config=config, caller=fake)  # type: ignore[arg-type]
        result = svc.check(_make_context(), self.WRITER_OUTPUT)

        assert result.input_token_count == 120
        assert result.output_token_count == 40
        assert result.cache_read_token_count == 80

    def test_model_identifier(self) -> None:
        fake = _scripted_caller([{"violations": []}])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
        )
        svc = ContradictionService(config=config, caller=fake)  # type: ignore[arg-type]
        result = svc.check(_make_context(), self.WRITER_OUTPUT)
        assert result.model_identifier == "anthropic:claude-haiku-test"


# ---------------------------------------------------------------------------
# Scenario B — blocked (location drift)
# ---------------------------------------------------------------------------


class TestScenarioBBlocked:
    WRITER_OUTPUT = (
        "The rain hammers the cobblestones outside the police precinct as you "
        "spread the crime-scene photographs across a borrowed desk."
    )

    SCRIPTED_VIOLATION = {
        "violations": [
            {
                "category": "location_drift",
                "description": (
                    "Aldric Crane is at the police precinct, spreading photographs "
                    "across a desk."
                ),
                "canon_reference": (
                    "Story Bible shows Aldric Crane's current_location as "
                    "'The Meridian Hotel, Room 14'."
                ),
            }
        ]
    }

    def test_verdict_blocked(self) -> None:
        fake = _scripted_caller([self.SCRIPTED_VIOLATION])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        svc = ContradictionService(config=config, caller=fake)  # type: ignore[arg-type]
        result = svc.check(_make_context(), self.WRITER_OUTPUT)

        assert result.verdict == ContradictionVerdict.BLOCKED
        assert len(result.violations) == 1

    def test_violation_category(self) -> None:
        from afterworlds.pipeline.contradiction.models import ContradictionCategory

        fake = _scripted_caller([self.SCRIPTED_VIOLATION])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
        )
        svc = ContradictionService(config=config, caller=fake)  # type: ignore[arg-type]
        result = svc.check(_make_context(), self.WRITER_OUTPUT)

        assert result.violations[0].category == ContradictionCategory.LOCATION_DRIFT

    def test_violation_description_and_canon(self) -> None:
        fake = _scripted_caller([self.SCRIPTED_VIOLATION])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
        )
        svc = ContradictionService(config=config, caller=fake)  # type: ignore[arg-type]
        result = svc.check(_make_context(), self.WRITER_OUTPUT)

        v = result.violations[0]
        assert "precinct" in v.description
        assert "Meridian Hotel" in v.canon_reference

    def test_context_not_mutated(self) -> None:
        ctx = _make_context()
        original_len = len(ctx.pass_forward_ledger.entries)

        fake = _scripted_caller([self.SCRIPTED_VIOLATION])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
        )
        svc = ContradictionService(config=config, caller=fake)  # type: ignore[arg-type]
        svc.check(ctx, self.WRITER_OUTPUT)

        assert len(ctx.pass_forward_ledger.entries) == original_len
