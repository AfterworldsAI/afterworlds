"""Unit + integration tests for OrchestratorService — CRD Issue 12c.

Coverage map (Issue 12c "Tests" section):

Unit tests:
- Disposition matrix (one test per PipelineDisposition).
- Disposition taxonomy guard.
- OOC short-circuit.
- Non-OOC order.
- Safety policy invocation.
- Ledger composition.
- TTL plumbing.
- Provider refusal across all four narrative/state passes.
- SafetyPassError routing for both targets.
- Safety taxonomy guard.
- Parallel-sync correctness.
- Parallel-sync timeout.
- Invariant enforcement on OrchestrationResult construction.
- OOC exclusion through RecentTurnsProvider.
- Writer backward-compatible session seam.

Default-CI integration tests:
- Delivered narrative path.
- OOC handled path.
- Input Safety BLOCK — no transaction, no Turn.
- Output Safety BLOCK — rollback, no Extractor/Contradiction calls.
- Contradiction BLOCK SAVEPOINT proof against real SQLite.
- Refusal path — Writer refusal rolls back, surfaces typed refusal.
- SafetyPassError path — Output Safety failure rolls back.
- Stable-prefix structural-identity integration across six pass renders.

The opt-in live-provider end-to-end orchestration test (Issue 12c
acceptance criterion #21) is scaffolded in
``test_integration_live.py``; it follows the existing Issue 9–12b
pattern and is gated by ``AFTERWORLDS_LIVE_TESTS=1``.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import (
    EventKind,
    EventSignificance,
    IntentType,
    TargetDomain,
)
from afterworlds.models.extractor import (
    EventProposal,
    ExtractorProposalSet,
    LockedFactProposal,
    SoftFactProposal,
    UnresolvedThreadProposal,
)
from afterworlds.models.story_bible import CastEntry
from afterworlds.persistence.orm.node import TurnORM
from afterworlds.persistence.orm.story_bible import (
    SBEventORM,
    SBProvisionalStagingORM,
    SBUnresolvedThreadORM,
)
from afterworlds.pipeline._refusal import (
    PassIdentifier,
)
from afterworlds.pipeline.contradiction.models import (
    ContradictionCategory,
    ContradictionVerdict,
    ContradictionViolation,
)
from afterworlds.pipeline.orchestrator import (
    OrchestrationResult,
    OrchestratorError,
    OrchestratorService,
    PipelineDisposition,
    SafetyPolicy,
)
from afterworlds.pipeline.planner.models import PlannerOutput
from afterworlds.pipeline.safety.models import (
    SafetyCategory,
    SafetyConcern,
    SafetyPassError,
    SafetyReport,
    SafetyResult,
    SafetyTarget,
    SafetyVerdict,
    TokenUsage,
)
from afterworlds.pipeline.writer.models import WriterResult
from afterworlds.services.story_bible import StoryBibleService
from tests.pipeline.orchestrator.conftest import (
    FakeContextBuilder,
    FakeContradictionService,
    FakeExtractorService,
    FakeIntentClassifier,
    FakePlannerService,
    FakeSafetyService,
    FakeWriterService,
    fixed_mode_resolver,
    make_intent,
    make_refusal,
)

# ---------------------------------------------------------------------------
# Orchestrator factory
# ---------------------------------------------------------------------------


def _make_orchestrator(  # type: ignore[no-untyped-def]
    session_factory,
    *,
    intent: IntentType = IntentType.IN_CHARACTER_ACTION,
    intent_error: bool = False,
    safety_input: SafetyResult | Exception | None = None,
    safety_output: SafetyResult | Exception | None = None,
    safety_policy: SafetyPolicy | None = None,
    planner_exc: Exception | None = None,
    writer_exc: Exception | None = None,
    extractor_exc: Exception | None = None,
    contradiction_violations: list[ContradictionViolation] | None = None,
    contradiction_exc: Exception | None = None,
    contradiction_delay: float = 0.0,
    extractor_delay: float = 0.0,
    extractor_real_sbs: StoryBibleService | None = None,
    extractor_proposal_factory=None,
    parallel_timeout: float = 30.0,
    executor: ThreadPoolExecutor | None = None,
):
    classifier = FakeIntentClassifier(make_intent(intent), raise_error=intent_error)
    ctx_builder = FakeContextBuilder()
    safety = FakeSafetyService(input_verdict=safety_input, output_verdict=safety_output)
    planner = FakePlannerService(raise_exc=planner_exc)
    writer = FakeWriterService(raise_exc=writer_exc)
    extractor = FakeExtractorService(
        raise_exc=extractor_exc,
        delay_seconds=extractor_delay,
        story_bible_service=extractor_real_sbs,
        proposal_set_factory=extractor_proposal_factory,
    )
    contradiction = FakeContradictionService(
        violations=contradiction_violations,
        raise_exc=contradiction_exc,
        delay_seconds=contradiction_delay,
    )
    orch = OrchestratorService(
        intent_classifier=classifier,
        context_builder=ctx_builder,
        safety_service=safety,
        planner_service=planner,
        writer_service=writer,
        extractor_service=extractor,
        contradiction_service=contradiction,
        session_factory=session_factory,
        safety_policy=safety_policy or SafetyPolicy(),
        mode_resolver=fixed_mode_resolver(),
        executor=executor,
        parallel_pass_timeout_seconds=parallel_timeout,
    )
    return (
        orch,
        classifier,
        ctx_builder,
        safety,
        planner,
        writer,
        extractor,
        contradiction,
    )


def _block_safety(target: SafetyTarget) -> SafetyResult:
    return SafetyResult(
        report=SafetyReport(
            concerns=[
                SafetyConcern(
                    category=SafetyCategory.OTHER,
                    description="synthetic",
                    evidence_summary="test",
                )
            ]
        ),
        target=target,
        usage=TokenUsage(),
    )


def _allow_safety(target: SafetyTarget) -> SafetyResult:
    return SafetyResult(
        report=SafetyReport(concerns=[]), target=target, usage=TokenUsage()
    )


# ---------------------------------------------------------------------------
# Disposition matrix
# ---------------------------------------------------------------------------


class TestDispositionDelivered:
    def test_happy_path_returns_delivered(self, session_factory, seeded_story) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(session_factory)
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.delivered_output
        assert result.turn_id is not None
        assert result.planner_result is not None
        assert result.writer_result is not None
        assert result.extractor_result is not None
        assert result.contradiction_result is not None
        assert result.contradiction_result.verdict is ContradictionVerdict.CLEAR


class TestDispositionOOCHandled:
    def test_ooc_returns_ooc_handled(self, session_factory, seeded_story) -> None:
        story_id, node_id = seeded_story
        orch, _, _, _, planner, writer, extractor, contradiction = _make_orchestrator(
            session_factory, intent=IntentType.OOC
        )
        result = orch.orchestrate_turn(story_id, node_id, "[OOC] Help?")
        assert result.disposition is PipelineDisposition.OOC_HANDLED
        assert result.delivered_output
        assert result.turn_id is not None
        assert planner.calls == []
        assert extractor.calls == []
        assert contradiction.calls == []
        assert writer.calls and writer.calls[0][
            0
        ].stable_prefix.system_prompt.startswith("# OOC Handler")


class TestDispositionBlockedInputSafety:
    def test_input_block_short_circuits(self, session_factory, seeded_story) -> None:
        story_id, node_id = seeded_story
        orch, _, _, _, planner, writer, extractor, contradiction = _make_orchestrator(
            session_factory,
            safety_input=_block_safety(SafetyTarget.INPUT),
        )
        result = orch.orchestrate_turn(story_id, node_id, "harmful?")
        assert result.disposition is PipelineDisposition.BLOCKED_INPUT_SAFETY
        assert result.turn_id is None
        assert result.delivered_output is None
        assert result.input_safety_result is not None
        assert result.input_safety_result.verdict is SafetyVerdict.BLOCK
        assert planner.calls == []
        assert writer.calls == []
        assert extractor.calls == []
        assert contradiction.calls == []


class TestDispositionBlockedOutputSafety:
    def test_narrative_output_block_rolls_back(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_, extractor, contradiction = _make_orchestrator(
            session_factory,
            safety_output=_block_safety(SafetyTarget.OUTPUT),
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.BLOCKED_OUTPUT_SAFETY
        assert result.turn_id is None
        assert result.planner_result is not None
        assert result.writer_result is not None
        assert extractor.calls == []
        assert contradiction.calls == []
        # No Turn persisted: the outer transaction rolled back.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_ooc_output_block_rolls_back(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_, extractor, contradiction = _make_orchestrator(
            session_factory,
            intent=IntentType.OOC,
            safety_output=_block_safety(SafetyTarget.OUTPUT),
        )
        result = orch.orchestrate_turn(story_id, node_id, "[OOC] Tell me a joke.")
        assert result.disposition is PipelineDisposition.BLOCKED_OUTPUT_SAFETY
        assert result.turn_id is None
        assert result.planner_result is None
        assert result.writer_result is not None
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []


class TestDispositionBlockedContradiction:
    def test_contradiction_block_rolls_back(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        violations = [
            ContradictionViolation(
                category=ContradictionCategory.LOCKED_FACT_VIOLATED,
                description="locked fact violated",
                canon_reference="locked_fact_id=123",
            )
        ]
        orch, *_ = _make_orchestrator(
            session_factory, contradiction_violations=violations
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.BLOCKED_CONTRADICTION
        assert result.turn_id is None
        assert result.contradiction_result is not None
        assert result.contradiction_result.verdict is ContradictionVerdict.BLOCKED
        # No Turn persisted.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []


class TestDispositionRefusedByProvider:
    @pytest.mark.parametrize(
        "pass_id,maker",
        [
            (
                PassIdentifier.PLANNER,
                lambda: dict(planner_exc=make_refusal(PassIdentifier.PLANNER)),
            ),
            (
                PassIdentifier.WRITER,
                lambda: dict(writer_exc=make_refusal(PassIdentifier.WRITER)),
            ),
            (
                PassIdentifier.EXTRACTOR,
                lambda: dict(extractor_exc=make_refusal(PassIdentifier.EXTRACTOR)),
            ),
            (
                PassIdentifier.CONTRADICTION,
                lambda: dict(
                    contradiction_exc=make_refusal(PassIdentifier.CONTRADICTION)
                ),
            ),
        ],
    )
    def test_refusal_routes_to_refused(
        self, session_factory, seeded_story, session, pass_id, maker
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(session_factory, **maker())
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert result.provider_refusal is not None
        assert result.provider_refusal.pass_identifier is pass_id
        assert result.turn_id is None
        # No Turn persisted regardless of where refusal happened.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []


class TestDispositionPipelineError:
    def test_safety_pass_error_routes_to_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            safety_input=SafetyPassError("input safety borked"),
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary
        assert "input safety" in result.pipeline_error_summary

    def test_output_safety_pass_error_rolls_back(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            safety_output=SafetyPassError("output safety borked"),
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "output safety" in (result.pipeline_error_summary or "")
        # Provisional Turn rolled back.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_intent_classification_failure_routes_to_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(session_factory, intent_error=True)
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "intent classification failed" in (result.pipeline_error_summary or "")


# ---------------------------------------------------------------------------
# Taxonomy guards
# ---------------------------------------------------------------------------


class TestDispositionTaxonomyGuard:
    def test_safety_block_never_becomes_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory, safety_input=_block_safety(SafetyTarget.INPUT)
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.BLOCKED_INPUT_SAFETY
        assert result.disposition is not PipelineDisposition.PIPELINE_ERROR

    def test_contradiction_block_never_becomes_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        violations = [
            ContradictionViolation(
                category=ContradictionCategory.OTHER,
                description="invented",
                canon_reference="ref",
            )
        ]
        orch, *_ = _make_orchestrator(
            session_factory, contradiction_violations=violations
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.BLOCKED_CONTRADICTION
        assert result.disposition is not PipelineDisposition.PIPELINE_ERROR

    def test_refusal_never_becomes_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory, writer_exc=make_refusal(PassIdentifier.WRITER)
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert result.disposition is not PipelineDisposition.PIPELINE_ERROR

    def test_safety_pass_error_never_becomes_refused(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory, safety_input=SafetyPassError("nope")
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.disposition is not PipelineDisposition.REFUSED_BY_PROVIDER


# ---------------------------------------------------------------------------
# Pipeline ordering
# ---------------------------------------------------------------------------


class TestNonOOCOrder:
    def test_canonical_sequence(self, session_factory, seeded_story) -> None:
        story_id, node_id = seeded_story
        events: list[str] = []

        def record_safety(target: SafetyTarget):
            def _make() -> SafetyResult:
                events.append(f"safety_{target.value}")
                return _allow_safety(target)

            return _make

        (
            orch,
            classifier,
            ctx_builder,
            safety,
            planner,
            writer,
            extractor,
            contradiction,
        ) = _make_orchestrator(
            session_factory,
            safety_input=record_safety(SafetyTarget.INPUT),
            safety_output=record_safety(SafetyTarget.OUTPUT),
        )

        # Wrap fake pass services to record their call order.
        original_plan = planner.plan

        def plan_recorded(ctx: AssembledContext):
            events.append("planner")
            return original_plan(ctx)

        planner.plan = plan_recorded  # type: ignore[method-assign]

        original_write = writer.write

        def write_recorded(*args, **kwargs):
            events.append("writer")
            return original_write(*args, **kwargs)

        writer.write = write_recorded  # type: ignore[method-assign]

        original_extract = extractor.extract

        def extract_recorded(*args, **kwargs):
            events.append("extractor")
            return original_extract(*args, **kwargs)

        extractor.extract = extract_recorded  # type: ignore[method-assign]

        original_check = contradiction.check

        def check_recorded(*args, **kwargs):
            events.append("contradiction")
            return original_check(*args, **kwargs)

        contradiction.check = check_recorded  # type: ignore[method-assign]

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.DELIVERED

        # Intent and Context are orchestrator-internal but we can infer order
        # from the fake calls: classifier called first.
        assert classifier.calls
        assert ctx_builder.calls
        # Canonical sequence (Issue 12c spec).  Extractor and Contradiction
        # are parallel; we accept either ordering as long as both appear
        # after Output Safety and before the result is returned.
        order = [e for e in events]
        assert order.index("safety_input") < order.index("planner")
        assert order.index("planner") < order.index("writer")
        assert order.index("writer") < order.index("safety_output")
        assert order.index("safety_output") < order.index("extractor")
        assert order.index("safety_output") < order.index("contradiction")


# ---------------------------------------------------------------------------
# OOC short-circuit
# ---------------------------------------------------------------------------


class TestOOCShortCircuit:
    def test_ooc_invokes_writer_with_ooc_handler_prompt(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_, writer, _, _ = _make_orchestrator(
            session_factory, intent=IntentType.OOC
        )
        orch.orchestrate_turn(story_id, node_id, "[OOC] What is HP?")
        assert len(writer.calls) == 1
        derived_ctx = writer.calls[0][0]
        assert derived_ctx.stable_prefix.system_prompt.startswith("# OOC Handler")

    def test_ooc_persists_turn_with_ooc_intent(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(session_factory, intent=IntentType.OOC)
        result = orch.orchestrate_turn(story_id, node_id, "[OOC] Hello?")
        assert result.disposition is PipelineDisposition.OOC_HANDLED
        row = (
            session.execute(
                select(TurnORM).where(TurnORM.turn_id == str(result.turn_id))
            )
            .scalars()
            .one()
        )
        assert row.intent_classification == IntentType.OOC.value

    def test_ooc_skips_planner_extractor_contradiction(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, _, _, _, planner, _, extractor, contradiction = _make_orchestrator(
            session_factory, intent=IntentType.OOC
        )
        orch.orchestrate_turn(story_id, node_id, "[OOC] ?")
        assert planner.calls == []
        assert extractor.calls == []
        assert contradiction.calls == []

    def test_ooc_runs_safety_when_policy_says_so(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, _, _, safety, *_ = _make_orchestrator(
            session_factory, intent=IntentType.OOC
        )
        orch.orchestrate_turn(story_id, node_id, "[OOC] ?")
        # Conservative default: both Input and Output Safety run.
        targets = {t for t, _ in safety.calls}
        assert SafetyTarget.INPUT in targets
        assert SafetyTarget.OUTPUT in targets

    def test_ooc_input_block_short_circuits_before_writer(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_, writer, _, _ = _make_orchestrator(
            session_factory,
            intent=IntentType.OOC,
            safety_input=_block_safety(SafetyTarget.INPUT),
        )
        result = orch.orchestrate_turn(story_id, node_id, "[OOC] ?")
        assert result.disposition is PipelineDisposition.BLOCKED_INPUT_SAFETY
        assert writer.calls == []


# ---------------------------------------------------------------------------
# Safety policy invocation
# ---------------------------------------------------------------------------


class TestSafetyPolicyInvocation:
    def test_whitelisted_provider_skips_both_safety_calls(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        policy = SafetyPolicy(whitelisted_providers=frozenset({"anthropic"}))
        orch, _, _, safety, *_ = _make_orchestrator(
            session_factory, safety_policy=policy
        )
        # Need the Writer fake to report provider "anthropic" — by default
        # _derive_writer_provider falls through to "anthropic", so this works.
        result = orch.orchestrate_turn(story_id, node_id, "I act.")
        assert result.disposition is PipelineDisposition.DELIVERED
        assert safety.calls == []
        assert result.input_safety_result is None
        assert result.output_safety_result is None

    def test_request_risk_signal_forces_input_preflight(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        policy = SafetyPolicy(whitelisted_providers=frozenset({"anthropic"}))
        orch, _, _, safety, *_ = _make_orchestrator(
            session_factory, safety_policy=policy
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I act.", request_risk_signal=True
        )
        assert result.disposition is PipelineDisposition.DELIVERED
        assert any(t is SafetyTarget.INPUT for t, _ in safety.calls)


# ---------------------------------------------------------------------------
# Ledger composition
# ---------------------------------------------------------------------------


class TestLedgerComposition:
    def test_writer_sees_planner_output_in_ledger(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, _, _, _, _, writer, *_ = _make_orchestrator(session_factory)
        orch.orchestrate_turn(story_id, node_id, "I open the door.")
        derived = writer.calls[0][0]
        assert len(derived.pass_forward_ledger.entries) == 1
        assert derived.pass_forward_ledger.entries[0].pass_name == "planner"
        # PlannerOutput serializes as JSON; assert known fields are present.
        ledger_text = derived.pass_forward_ledger.entries[0].content
        assert '"scene_goal"' in ledger_text
        assert '"next_beat"' in ledger_text

    def test_safety_result_never_in_ledger(self, session_factory, seeded_story) -> None:
        story_id, node_id = seeded_story
        orch, _, _, _, _, writer, extractor, contradiction = _make_orchestrator(
            session_factory
        )
        orch.orchestrate_turn(story_id, node_id, "I open the door.")
        for ctx in [
            writer.calls[0][0],
            extractor.calls[0][0],
            contradiction.calls[0][0],
        ]:
            for entry in ctx.pass_forward_ledger.entries:
                assert entry.pass_name != "input_safety"
                assert entry.pass_name != "output_safety"


# ---------------------------------------------------------------------------
# Parallel sync
# ---------------------------------------------------------------------------


class TestParallelSync:
    def test_extractor_on_orchestrator_thread_contradiction_on_worker(
        self, session_factory, seeded_story
    ) -> None:
        import threading

        story_id, node_id = seeded_story
        orch, *_, extractor, contradiction = _make_orchestrator(session_factory)
        orch.orchestrate_turn(story_id, node_id, "I open the door.")

        main_tid = threading.get_ident()
        assert extractor.thread_observation["extractor"] == main_tid
        assert contradiction.thread_observation["contradiction"] != main_tid

    def test_wall_time_approx_max_not_sum(self, session_factory, seeded_story) -> None:
        import time

        story_id, node_id = seeded_story
        # 0.3s each; if sequential the total exceeds 0.6s, parallel hovers
        # around 0.3s (plus other overhead).
        orch, *_ = _make_orchestrator(
            session_factory,
            extractor_delay=0.3,
            contradiction_delay=0.3,
        )
        start = time.perf_counter()
        orch.orchestrate_turn(story_id, node_id, "I open the door.")
        elapsed = time.perf_counter() - start
        # Tolerant bound to keep test non-flaky on slow CI.
        assert elapsed < 0.55, f"parallel-sync wall time {elapsed:.3f}s ≈ sum"

    def test_timeout_routes_to_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        # Force contradiction to block past timeout.
        orch, *_ = _make_orchestrator(
            session_factory,
            contradiction_delay=2.0,
            parallel_timeout=0.1,
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "timeout" in (result.pipeline_error_summary or "").lower()


# ---------------------------------------------------------------------------
# Invariant enforcement on OrchestrationResult
# ---------------------------------------------------------------------------


class TestResultInvariants:
    def test_delivered_requires_planner_writer_extractor_contradiction(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.DELIVERED,
                delivered_output="prose",
                turn_id=uuid4(),
                intent_classification=intent,
                planner_result=None,  # missing
                writer_result=None,
                extractor_result=None,
                contradiction_result=None,
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    def test_ooc_handled_forbids_planner_result(self) -> None:

        intent = make_intent(IntentType.OOC, "[OOC] ?")
        writer_result = WriterResult(
            turn_id=uuid4(),
            assistant_output="OOC reply",
            model_identifier="anthropic:fake",
            latency_ms=1,
            input_token_count=1,
            output_token_count=1,
            cache_read_token_count=0,
            cache_creation_token_count=0,
        )
        planner_result = _stub_planner_result()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.OOC_HANDLED,
                delivered_output="OOC reply",
                turn_id=uuid4(),
                intent_classification=intent,
                writer_result=writer_result,
                planner_result=planner_result,  # forbidden on OOC_HANDLED
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    def test_blocked_input_safety_forbids_planner_result(self) -> None:
        intent = make_intent()
        planner_result = _stub_planner_result()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_INPUT_SAFETY,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                input_safety_result=_block_safety(SafetyTarget.INPUT),
                planner_result=planner_result,  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    def test_refused_by_provider_requires_refusal(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.REFUSED_BY_PROVIDER,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                provider_refusal=None,  # missing
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    def test_pipeline_error_requires_summary(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.PIPELINE_ERROR,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                pipeline_error_summary=None,  # missing
                total_latency_ms=10,
                pass_latency_breakdown={},
            )


def _stub_planner_result():
    from afterworlds.pipeline.planner.models import PlannerResult

    return PlannerResult(
        plan=PlannerOutput(
            scene_goal="g",
            next_beat="b",
            facts_needed=["f"],
            notes=None,
        ),
        model_identifier="anthropic:fake",
        latency_ms=1,
        input_token_count=1,
        output_token_count=1,
        cache_read_token_count=0,
        cache_creation_token_count=0,
    )


# ---------------------------------------------------------------------------
# OOC exclusion through RecentTurnsProvider
# ---------------------------------------------------------------------------


class TestOOCExclusion:
    def test_ooc_turns_excluded_by_default(
        self, session_factory, seeded_story, session
    ) -> None:
        from afterworlds.services.context_builder import (
            SQLiteRecentTurnsProvider,
        )

        story_id, node_id = seeded_story
        orch_ooc, *_ = _make_orchestrator(session_factory, intent=IntentType.OOC)
        orch_ooc.orchestrate_turn(story_id, node_id, "[OOC] First.")
        orch, *_ = _make_orchestrator(session_factory)
        orch.orchestrate_turn(story_id, node_id, "I act.")

        provider = SQLiteRecentTurnsProvider(session)
        excluded = provider.get_recent_turns(story_id, limit=10)
        included = provider.get_recent_turns(story_id, limit=10, exclude_ooc=False)
        assert all(t.intent_classification is not IntentType.OOC for t in excluded)
        assert any(t.intent_classification is IntentType.OOC for t in included)


# ---------------------------------------------------------------------------
# Writer session backward-compat
# ---------------------------------------------------------------------------


class TestWriterBackwardCompat:
    def test_writer_standalone_still_commits_when_no_session(
        self, session, seeded_story
    ) -> None:
        """WriterService.write(session=None) still commits — preserves Issue 9."""
        from anthropic.types import Message, TextBlock, Usage

        from afterworlds.models.context import PassForwardLedger
        from afterworlds.pipeline.writer.config import WriterConfig
        from afterworlds.pipeline.writer.service import WriterService

        story_id, node_id = seeded_story

        msg = Message(
            id="msg_fake",
            type="message",
            role="assistant",
            content=[TextBlock(type="text", text="hello")],
            model="claude-fake",
            stop_reason="end_turn",
            stop_sequence=None,
            usage=Usage(
                input_tokens=10,
                output_tokens=2,
                cache_read_input_tokens=0,
                cache_creation_input_tokens=0,
            ),
        )

        def fake_caller(payload):  # type: ignore[no-untyped-def]
            return msg

        config = WriterConfig(
            model="claude-fake", api_key_env="ANTHROPIC_API_KEY", extended_ttl=True
        )
        writer = WriterService(session=session, config=config, caller=fake_caller)
        ctx = AssembledContext(
            stable_prefix=_stable_prefix_for(story_id),
            volatile_suffix=_volatile_for(make_intent()),
            pass_forward_ledger=PassForwardLedger(),
        )
        result = writer.write(ctx, story_id, node_id)
        # Default behavior committed the Turn — readable in a fresh session.
        assert session.get(TurnORM, str(result.turn_id)) is not None


def _stable_prefix_for(story_id):
    from tests.pipeline.orchestrator.conftest import make_stable_prefix

    return make_stable_prefix(story_id)


def _volatile_for(intent):
    from afterworlds.models.context import VolatileSuffix

    return VolatileSuffix(
        recent_turns=[],
        current_input=intent.raw_input,
        classified_intent=intent,
    )


# ---------------------------------------------------------------------------
# Default-CI integration tests: real SQLite SAVEPOINT proof
# ---------------------------------------------------------------------------


class TestContradictionBlockSAVEPOINTProof:
    """Real-SQLite proof that Contradiction BLOCK rolls back every Extractor
    write category alongside the provisional Turn."""

    @staticmethod
    def _seed_named_cast(session, story_id):  # type: ignore[no-untyped-def]
        cast = CastEntry(
            story_id=story_id,
            name="Mira",
            role=CastRole_ANTAGONIST(),
            current_location="village",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        sbs = StoryBibleService(session)
        sbs.add_cast_entry(story_id, cast)
        session.commit()
        return sbs

    def test_contradiction_block_rolls_back_everything(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        # Seed a named character so soft-fact updates have a target.
        sbs_seed = StoryBibleService(session)
        cast = CastEntry(
            story_id=story_id,
            name="Mira",
            role=CastRole_ANTAGONIST(),
            current_location="village",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        sbs_seed.add_cast_entry(story_id, cast)
        session.commit()

        # Pre-snapshot row counts.
        pre_turn = session.execute(select(TurnORM)).scalars().all()
        pre_event = session.execute(select(SBEventORM)).scalars().all()
        pre_thread = session.execute(select(SBUnresolvedThreadORM)).scalars().all()
        pre_stage = session.execute(select(SBProvisionalStagingORM)).scalars().all()

        def proposal_factory():
            return ExtractorProposalSet(
                proposals=[
                    LockedFactProposal(fact_text="The vault is sealed."),
                    SoftFactProposal(
                        target_domain=TargetDomain.CHARACTER,
                        target_natural_key="Mira",
                        target_field="current_location",
                        proposed_value="forest",
                    ),
                    UnresolvedThreadProposal(
                        description="What did Mira hide in the forest?"
                    ),
                    EventProposal(
                        description="Mira fled to the forest.",
                        significance=EventSignificance.MAJOR_PLOT_TURN,
                        event_kind=EventKind.LOCATION_CHANGE,
                    ),
                ]
            )

        violations = [
            ContradictionViolation(
                category=ContradictionCategory.LOCATION_DRIFT,
                description="invented",
                canon_reference="ref",
            )
        ]
        # The orchestrator opens its own session per turn from session_factory;
        # we use the real Story Bible service bound to a different session for
        # routing.  The session and orchestrator session may live in the same
        # SQLite database file because we use an in-memory engine shared via
        # the same Engine instance.
        orch, *_ = _make_orchestrator(
            session_factory,
            contradiction_violations=violations,
            extractor_real_sbs=StoryBibleService(session_factory()),
            extractor_proposal_factory=proposal_factory,
        )

        result = orch.orchestrate_turn(story_id, node_id, "Mira moves.")
        assert result.disposition is PipelineDisposition.BLOCKED_CONTRADICTION

        # Post-state: every category must equal the pre-snapshot.  No Turn,
        # no event, no thread, no staging row from this turn.
        post_turn = session.execute(select(TurnORM)).scalars().all()
        post_event = session.execute(select(SBEventORM)).scalars().all()
        post_thread = session.execute(select(SBUnresolvedThreadORM)).scalars().all()
        post_stage = session.execute(select(SBProvisionalStagingORM)).scalars().all()
        assert [t.turn_id for t in post_turn] == [t.turn_id for t in pre_turn]
        assert [e.event_id for e in post_event] == [e.event_id for e in pre_event]
        assert [t.thread_id for t in post_thread] == [t.thread_id for t in pre_thread]
        assert [p.proposal_id for p in post_stage] == [p.proposal_id for p in pre_stage]


def CastRole_ANTAGONIST():
    from afterworlds.models.enums import CastRole

    return CastRole.ANTAGONIST


# ---------------------------------------------------------------------------
# Structural-identity integration: stable region is byte-identical across passes
# ---------------------------------------------------------------------------


class TestStablePrefixStructuralIdentity:
    def test_six_pass_payloads_share_stable_region(self) -> None:
        from afterworlds.pipeline._stable_prefix_renderer import (
            collect_stable_prefix_texts,
        )
        from afterworlds.pipeline.contradiction.config import ContradictionConfig
        from afterworlds.pipeline.contradiction.service import (
            ContradictionService,
            _derive_context,
        )
        from afterworlds.pipeline.extractor.config import ExtractorConfig
        from afterworlds.pipeline.extractor.service import ExtractorService
        from afterworlds.pipeline.planner.config import PlannerConfig
        from afterworlds.pipeline.planner.service import PlannerService
        from afterworlds.pipeline.safety.config import SafetyConfig
        from afterworlds.pipeline.safety.service import SafetyService
        from afterworlds.pipeline.writer.config import WriterConfig
        from afterworlds.pipeline.writer.renderer import PromptRenderer
        from tests.pipeline.orchestrator.conftest import make_assembled

        story_id = uuid4()
        ctx = make_assembled(story_id)
        expected = collect_stable_prefix_texts(ctx.stable_prefix)

        # Each renderer's _render builds a payload; extract the stable region
        # (blocks BEFORE any pass-specific tail like the writer-output block
        # or volatile suffix).  We compare those slices to the canonical
        # expected list.
        cfg_planner = PlannerConfig(
            model="claude-fake-haiku",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        cfg_writer = WriterConfig(
            model="claude-fake-sonnet",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        cfg_safety = SafetyConfig(
            model="claude-fake-haiku",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        cfg_extractor = ExtractorConfig(
            model="claude-fake-sonnet",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )
        cfg_contr = ContradictionConfig(
            model="claude-fake-haiku",
            api_key_env="ANTHROPIC_API_KEY",
            extended_ttl=True,
        )

        # PlannerService._render and equivalents are private; reach through
        # name-mangled access for the test.
        planner_payload = PlannerService(
            config=cfg_planner, caller=_DummyCaller()
        )._render(ctx)
        writer_payload = PromptRenderer(cfg_writer).render(ctx)
        safety_input_payload = SafetyService(
            config=cfg_safety, caller=_DummyCaller()
        )._render(ctx, "raw input", SafetyTarget.INPUT)
        safety_output_payload = SafetyService(
            config=cfg_safety, caller=_DummyCaller()
        )._render(ctx, "writer output", SafetyTarget.OUTPUT)
        extractor_payload = ExtractorService(
            session=None,  # type: ignore[arg-type]
            story_bible_service=None,  # type: ignore[arg-type]
            config=cfg_extractor,
            caller=_DummyCaller(),
        )._render(ctx, "writer prose")
        contr_payload = ContradictionService(
            config=cfg_contr, caller=_DummyCaller()
        )._render(_derive_context(ctx, "writer prose"))

        # For each payload, the stable region is the leading block(s) whose
        # last block carries the cache_control marker.  Slice up to and
        # including that block.
        payloads = {
            "planner": planner_payload,
            "writer": writer_payload,
            "safety_input": safety_input_payload,
            "safety_output": safety_output_payload,
            "extractor": extractor_payload,
            "contradiction": contr_payload,
        }
        slices = {
            name: _stable_slice(p["messages"][0]["content"])  # type: ignore[index]
            for name, p in payloads.items()
        }

        # All six slices must be byte-identical to the canonical text list.
        for name, sl in slices.items():
            assert sl == expected, f"{name} stable region drifted: {sl} vs {expected}"

        # Cache breakpoint position is identical across all six.
        breakpoints = {
            name: _cache_breakpoint_index(p["messages"][0]["content"])
            for name, p in payloads.items()
        }
        assert len(set(breakpoints.values())) == 1, breakpoints


class _DummyCaller:
    def call(self, payload):  # type: ignore[no-untyped-def]
        raise AssertionError(
            "_DummyCaller should not be invoked — test only inspects rendered payload"
        )


def _stable_slice(content_blocks):  # type: ignore[no-untyped-def]
    """Return leading stable-region texts up to and including the breakpoint block."""
    out: list[str] = []
    for b in content_blocks:
        out.append(b["text"])
        if b.get("cache_control") is not None:
            return out
    return out


def _cache_breakpoint_index(content_blocks):  # type: ignore[no-untyped-def]
    for i, b in enumerate(content_blocks):
        if b.get("cache_control") is not None:
            return i
    return None


# ---------------------------------------------------------------------------
# TTL plumbing for the shared renderer
# ---------------------------------------------------------------------------


class TestSharedRendererTTLPlumbing:
    def test_ttl_changes_only_breakpoint_marker(self) -> None:
        from afterworlds.pipeline._stable_prefix_renderer import (
            collect_stable_prefix_texts,
            render_stable_prefix_blocks,
        )
        from tests.pipeline.orchestrator.conftest import make_stable_prefix

        sp = make_stable_prefix(uuid4())
        texts = collect_stable_prefix_texts(sp)
        blocks_1h = render_stable_prefix_blocks(sp, "1h")
        blocks_5m = render_stable_prefix_blocks(sp, "5m")
        assert [b["text"] for b in blocks_1h] == texts
        assert [b["text"] for b in blocks_5m] == texts
        assert blocks_1h[-1]["cache_control"]["ttl"] == "1h"
        assert blocks_5m[-1]["cache_control"]["ttl"] == "5m"
