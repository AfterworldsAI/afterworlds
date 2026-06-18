"""Opt-in live integration test for PlannerService — CRD Issue 12a.

Requires the AFTERWORLDS_LIVE_TESTS environment variable to be set to '1'
and a valid ANTHROPIC_API_KEY.

Not run in default CI.  Run manually or in a dedicated live-test job::

    AFTERWORLDS_LIVE_TESTS=1 pytest tests/pipeline/planner/
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
from afterworlds.pipeline.planner.config import PlannerConfig
from afterworlds.pipeline.planner.service import PlannerService
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
        system_prompt=(
            "You are the Sojourn story planner. Your role is to analyse"
            " the player's intent and the Story Bible, then produce a"
            " structured plan the Writer pass will execute."
        ),
        story_bible_context=ctx,
        rolling_summary_text=None,
        rules_package_slice=None,
        retrieval_memory=RetrievalMemoryPayload(),
    )
    icr = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.95,
        raw_input="I try to pick the lock.",
        ambiguous=False,
    )
    vs = VolatileSuffix(
        recent_turns=[],
        current_input="I try to pick the lock.",
        classified_intent=icr,
    )
    return AssembledContext(
        stable_prefix=sp,
        volatile_suffix=vs,
        pass_forward_ledger=PassForwardLedger(),
    )


def _make_adapter() -> AnthropicDirectAdapter:
    return AnthropicDirectAdapter(api_key=os.environ["ANTHROPIC_API_KEY"])


class TestLivePlan:
    def test_returns_non_empty_plan(self) -> None:
        svc = PlannerService(config=PlannerConfig.from_env())
        adapter = _make_adapter()

        result = svc.plan(_make_context(), provider=adapter)

        assert result.plan.scene_goal.strip()
        assert result.plan.next_beat.strip()
        assert isinstance(result.plan.facts_needed, list)
        assert result.input_token_count is not None
        assert result.output_token_count is not None
        assert result.latency_ms >= 0

    def test_notes_is_none_or_non_empty_string(self) -> None:
        svc = PlannerService(config=PlannerConfig.from_env())
        adapter = _make_adapter()

        result = svc.plan(_make_context(), provider=adapter)

        assert result.plan.notes is None or (
            isinstance(result.plan.notes, str) and result.plan.notes.strip()
        )
