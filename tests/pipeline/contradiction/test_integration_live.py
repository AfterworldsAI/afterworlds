"""Opt-in live integration test for ContradictionService — CRD Issue 11.

Requires the AFTERWORLDS_LIVE_TESTS environment variable to be set to '1'
and a valid ANTHROPIC_API_KEY.

Not run in default CI.  Run manually or in a dedicated live-test job::

    AFTERWORLDS_LIVE_TESTS=1 pytest tests/pipeline/contradiction/
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest

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
from afterworlds.pipeline.contradiction.config import ContradictionConfig
from afterworlds.pipeline.contradiction.models import (
    ContradictionVerdict,
)
from afterworlds.pipeline.contradiction.service import ContradictionService
from afterworlds.pipeline.provider.adapters._anthropic import AnthropicDirectAdapter

pytestmark = pytest.mark.skipif(
    os.environ.get("AFTERWORLDS_LIVE_TESTS") != "1",
    reason="Set AFTERWORLDS_LIVE_TESTS=1 to run live provider tests",
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
        system_prompt="You are the Sojourn contradiction checker.",
        story_bible_context=ctx,
        rolling_summary_text=None,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )
    icr = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.95,
        raw_input="I examine the corridor.",
        ambiguous=False,
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input="I examine the corridor.",
        classified_intent=icr,
    )
    return AssembledContext(
        stable_prefix=sp,
        volatile_suffix=vs,
        pass_forward_ledger=PassForwardLedger(),
    )


def _make_adapter() -> AnthropicDirectAdapter:
    return AnthropicDirectAdapter(api_key=os.environ["ANTHROPIC_API_KEY"])


class TestLiveClear:
    def test_clean_prose_returns_clear(self) -> None:
        svc = ContradictionService(config=ContradictionConfig.from_env())

        writer_output = (
            "You pocket the Obsidian Key and step into the corridor. "
            "The Meridian's red-carpeted hallway stretches ahead, gas lamps"
            " flickering. You check room numbers as you pass: twelve,"
            " thirteen, fourteen. You pause at your own door, Room 14."
        )

        result = svc.check(_make_context(), writer_output, provider=_make_adapter())

        assert result.verdict == ContradictionVerdict.CLEAR
        assert result.input_token_count is not None
        assert result.output_token_count is not None
        assert result.latency_ms >= 0


class TestLiveBlocked:
    def test_location_drift_returns_blocked(self) -> None:
        svc = ContradictionService(config=ContradictionConfig.from_env())

        writer_output = (
            "The rain hammers the cobblestones outside the police precinct as you "
            "spread the crime-scene photographs across a borrowed desk. "
            "Sergeant Vance leans against the doorframe, watching."
        )

        result = svc.check(_make_context(), writer_output, provider=_make_adapter())

        assert result.verdict == ContradictionVerdict.BLOCKED
        assert len(result.violations) >= 1
        categories = [v.category.value for v in result.violations]
        assert "location_drift" in categories
