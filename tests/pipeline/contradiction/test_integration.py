"""Default-CI integration tests for ContradictionService — CRD Issue 11 / 14a.

Uses a high-fidelity fake ProviderAdapter with two scripted scenarios:
  - Scenario A: clean prose → CLEAR verdict, no violations
  - Scenario B: location-drift prose → BLOCKED verdict, one violation
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
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
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderToolCallPart,
)


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


class _ScriptedAdapter:
    """Fake ProviderAdapter that plays back scripted contradiction tool inputs."""

    def __init__(self, tool_inputs: list[dict]) -> None:
        self._responses = [
            ProviderCallResult(
                pass_id=PipelinePassId.CONTRADICTION,
                provider_name="anthropic",
                model_identifier="anthropic:claude-haiku-test",
                model_tier=ModelTier.HAIKU,
                content_parts=[
                    ProviderToolCallPart(
                        tool_name=REPORT_TOOL_NAME,
                        tool_input=ti,
                    )
                ],
                input_token_count=120,
                output_token_count=40,
                cache_read_token_count=80,
                cache_creation_token_count=None,
                cache_warmed=True,
                latency_ms=5,
            )
            for ti in tool_inputs
        ]
        self._idx = 0
        self.provider_name = "anthropic"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        result = self._responses[self._idx]
        self._idx += 1
        return result


class TestScenarioAClear:
    WRITER_OUTPUT = (
        "You pocket the Obsidian Key and step into the corridor. "
        "The Meridian's red-carpeted hallway stretches ahead."
    )

    def test_verdict_clear(self) -> None:
        adapter = _ScriptedAdapter([{"violations": []}])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        svc = ContradictionService(config=config)
        result = svc.check(_make_context(), self.WRITER_OUTPUT, provider=adapter)  # type: ignore[arg-type]

        assert result.verdict == ContradictionVerdict.CLEAR
        assert result.violations == []

    def test_token_metrics_present(self) -> None:
        adapter = _ScriptedAdapter([{"violations": []}])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        svc = ContradictionService(config=config)
        result = svc.check(_make_context(), self.WRITER_OUTPUT, provider=adapter)  # type: ignore[arg-type]

        assert result.input_token_count == 120
        assert result.output_token_count == 40
        assert result.cache_read_token_count == 80

    def test_model_identifier(self) -> None:
        adapter = _ScriptedAdapter([{"violations": []}])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
        )
        svc = ContradictionService(config=config)
        result = svc.check(_make_context(), self.WRITER_OUTPUT, provider=adapter)  # type: ignore[arg-type]
        assert result.model_identifier == "anthropic:claude-haiku-test"


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
        adapter = _ScriptedAdapter([self.SCRIPTED_VIOLATION])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        svc = ContradictionService(config=config)
        result = svc.check(_make_context(), self.WRITER_OUTPUT, provider=adapter)  # type: ignore[arg-type]

        assert result.verdict == ContradictionVerdict.BLOCKED
        assert len(result.violations) == 1

    def test_violation_category(self) -> None:
        from afterworlds.pipeline.contradiction.models import ContradictionCategory

        adapter = _ScriptedAdapter([self.SCRIPTED_VIOLATION])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
        )
        svc = ContradictionService(config=config)
        result = svc.check(_make_context(), self.WRITER_OUTPUT, provider=adapter)  # type: ignore[arg-type]
        assert result.violations[0].category == ContradictionCategory.LOCATION_DRIFT

    def test_violation_description_and_canon(self) -> None:
        adapter = _ScriptedAdapter([self.SCRIPTED_VIOLATION])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
        )
        svc = ContradictionService(config=config)
        result = svc.check(_make_context(), self.WRITER_OUTPUT, provider=adapter)  # type: ignore[arg-type]

        v = result.violations[0]
        assert "precinct" in v.description
        assert "Meridian Hotel" in v.canon_reference

    def test_context_not_mutated(self) -> None:
        ctx = _make_context()
        original_len = len(ctx.pass_forward_ledger.entries)

        adapter = _ScriptedAdapter([self.SCRIPTED_VIOLATION])
        config = ContradictionConfig(
            model="claude-haiku-test",
            api_key_env="ANTHROPIC_API_KEY",
        )
        svc = ContradictionService(config=config)
        svc.check(ctx, self.WRITER_OUTPUT, provider=adapter)  # type: ignore[arg-type]

        assert len(ctx.pass_forward_ledger.entries) == original_len
