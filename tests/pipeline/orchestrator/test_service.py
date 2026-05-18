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
from contextlib import suppress
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
    ProviderRefusal,
)
from afterworlds.pipeline.contradiction.models import (
    ContradictionCategory,
    ContradictionResult,
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
    intent_exc: Exception | None = None,
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
    classifier = FakeIntentClassifier(
        make_intent(intent), raise_error=intent_error, raise_exc=intent_exc
    )
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
        # P1 fix follow-up: the typed-error summary must preserve the
        # underlying cause text, not just say "intent classification failed".
        assert "synthetic failure" in (result.pipeline_error_summary or "")

    def test_intent_generic_runtime_exception_routes_to_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        """Codex P1 #87: any (not just IntentClassificationError) exception
        from IntentClassifierService.classify() must convert to a typed
        PIPELINE_ERROR rather than escape the orchestrator as a raw
        exception.  Covers transport/runtime/provider failures from the
        injected model caller.
        """
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            intent_exc=RuntimeError("upstream provider 503"),
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "intent classification failed" in (result.pipeline_error_summary or "")
        assert "upstream provider 503" in (result.pipeline_error_summary or "")

    def test_intent_connection_error_routes_to_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        """Regression: ConnectionError from a stub transport must not crash
        the turn — must produce a typed PIPELINE_ERROR result.
        """
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            intent_exc=ConnectionError("DNS lookup failed"),
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "DNS lookup failed" in (result.pipeline_error_summary or "")


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
        """Codex P1 #87: a parallel_pass_timeout_seconds breach must
        actually bound wall time, not just produce the correct disposition.
        Historical ``with ThreadPoolExecutor() as exc:`` pattern called
        ``shutdown(wait=True)`` on exit, blocking on the still-running
        Contradiction worker for its natural runtime (~2s here against a
        0.1s configured timeout).

        After the fix the orchestrator's locally-owned executor is torn
        down with ``shutdown(wait=False, cancel_futures=True)`` in a
        ``finally`` block, so the call returns shortly after the timeout
        fires.  The leaked worker thread continues in the background — it
        has no DB I/O so the leak is bounded and side-effect-free — but
        the orchestrator does not wait for it.
        """
        import time

        story_id, node_id = seeded_story
        # Contradiction sleeps far past the 0.1s timeout.  Before the fix
        # the call took ~the contradiction_delay; after the fix it should
        # return ~immediately after the timeout fires.
        orch, *_ = _make_orchestrator(
            session_factory,
            contradiction_delay=2.0,
            parallel_timeout=0.1,
        )
        start = time.perf_counter()
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        elapsed = time.perf_counter() - start

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "timeout" in (result.pipeline_error_summary or "").lower()
        # Tolerant bound — must complete well before the 2s
        # contradiction_delay; CI jitter friendly but well under the
        # historical blocking behavior's ~2s.
        assert elapsed < 0.8, (
            f"orchestrator did not respect parallel-sync timeout: "
            f"elapsed {elapsed:.3f}s ≈ contradiction_delay; "
            f"shutdown(wait=False) regression?"
        )


# ---------------------------------------------------------------------------
# Bounded orchestrator-owned executor lifecycle (Codex P1 #87 round 8)
#
# The orchestrator-owned executor is created once in ``__init__`` with
# ``max_workers=parallel_pass_max_workers`` and reused across every turn.
# Repeated timeouts cannot create unbounded worker threads — total live
# workers are capped by ``max_workers``.  Queued-but-not-started work is
# cancellable on timeout.  Injected executors remain caller-owned and the
# orchestrator never shuts them down.
# ---------------------------------------------------------------------------


class TestBoundedOwnedExecutorLifecycle:
    def test_owned_executor_is_reused_across_turns(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(session_factory)
        try:
            executor_before = orch._owned_executor
            orch.orchestrate_turn(story_id, node_id, "I open the door.")
            assert orch._owned_executor is executor_before
            orch.orchestrate_turn(story_id, node_id, "I close the door.")
            assert orch._owned_executor is executor_before
        finally:
            orch.close()

    def test_repeated_timeouts_do_not_accumulate_worker_threads(
        self, session_factory, seeded_story
    ) -> None:
        """Run many turns whose contradiction worker hangs past the
        timeout.  Worker threads must be bounded by ``max_workers``.

        Prior design (per-turn local executor + ``shutdown(wait=False,
        cancel_futures=True)``) would have created one fresh hung worker
        per turn — unbounded.  After the bounded-owned-executor fix the
        executor's own ``_threads`` set is capped at ``max_workers``
        regardless of how many turns we run.
        """
        story_id, node_id = seeded_story
        max_workers = 2
        # Long contradiction delay so workers stay stuck past the timeout;
        # tiny timeout so each turn returns fast.
        orch, *_ = _make_orchestrator(
            session_factory,
            contradiction_delay=5.0,
            parallel_timeout=0.05,
        )
        # Replace the owned executor with one whose size we control for
        # this test.  Introspect via the executor's own ``_threads`` set
        # so the assertion measures only THIS orchestrator's workers and
        # cannot be polluted by hung worker threads leaked from other
        # tests in the suite (a global ``threading.enumerate()`` view
        # would include any contradiction-named thread leaked elsewhere).
        from concurrent.futures import ThreadPoolExecutor

        orch.close()
        orch._owned_executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=f"orchestrator-contradiction-{id(orch)}",
        )

        try:
            for _ in range(8):
                result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
                assert result.disposition is PipelineDisposition.PIPELINE_ERROR
                assert "timeout" in (result.pipeline_error_summary or "").lower()

            owned_threads = orch._owned_executor._threads  # type: ignore[attr-defined]
            assert len(owned_threads) <= max_workers, (
                f"expected <= {max_workers} threads in the orchestrator-"
                f"owned executor, found {len(owned_threads)}: "
                f"{[t.name for t in owned_threads]}"
            )
        finally:
            orch.close()

    def test_repeated_timeouts_return_promptly(
        self, session_factory, seeded_story
    ) -> None:
        """Every turn returns within a small bound of the configured
        timeout, even when prior turns left workers hung.  Queued futures
        are cancelled on timeout so they do not wait on the upstream
        running worker."""
        import time

        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            contradiction_delay=5.0,
            parallel_timeout=0.05,
        )
        try:
            elapsed_per_turn: list[float] = []
            for _ in range(6):
                start = time.perf_counter()
                result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
                elapsed_per_turn.append(time.perf_counter() - start)
                assert result.disposition is PipelineDisposition.PIPELINE_ERROR
            # No turn took more than ~0.8s — well under the 5s
            # contradiction_delay.  This proves that even queued futures
            # behind hung workers are cancelled promptly on timeout.
            assert (
                max(elapsed_per_turn) < 0.8
            ), f"per-turn elapsed seconds: {elapsed_per_turn}"
        finally:
            orch.close()

    def test_queued_contradiction_future_is_cancellable_on_timeout(
        self, session_factory, seeded_story
    ) -> None:
        """Inject a single-worker executor pre-loaded with a blocker so the
        orchestrator's contradiction future has to queue.  When the
        orchestrator times out it calls ``future.cancel()`` — for a queued-
        but-not-started future that succeeds and the contradiction service
        is never actually called.
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor

        story_id, node_id = seeded_story
        executor = ThreadPoolExecutor(max_workers=1)
        blocker_release = threading.Event()
        # Fill the only worker slot with a blocker so the next submit
        # queues without starting.
        blocker_future = executor.submit(blocker_release.wait)

        orch, *_, _, contradiction = _make_orchestrator(
            session_factory,
            executor=executor,
            parallel_timeout=0.1,
        )
        try:
            result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

            assert result.disposition is PipelineDisposition.PIPELINE_ERROR
            assert "timeout" in (result.pipeline_error_summary or "").lower()
            # The contradiction service was never called — its queued
            # future was cancelled before the executor could promote it
            # onto a worker.
            assert len(contradiction.calls) == 0, (
                "contradiction worker should not have run — queued "
                "future was cancelled on timeout"
            )
        finally:
            # Release the blocker, drain, shut down the injected executor.
            blocker_release.set()
            blocker_future.result(timeout=2.0)
            executor.shutdown(wait=True)
            orch.close()

    def test_injected_executor_lifecycle_is_caller_owned(
        self, session_factory, seeded_story
    ) -> None:
        """Orchestrator MUST NOT call ``shutdown`` on a caller-injected
        executor — neither per-turn nor on ``close()``.  The injected
        executor must still accept submissions afterward.
        """
        from concurrent.futures import ThreadPoolExecutor

        story_id, node_id = seeded_story
        executor = ThreadPoolExecutor(max_workers=2)
        # With an injected executor, ``_owned_executor`` must be None so
        # ``close()`` has nothing of its own to release.
        orch, *_ = _make_orchestrator(session_factory, executor=executor)
        try:
            assert orch._owned_executor is None
            orch.orchestrate_turn(story_id, node_id, "I open the door.")
            # close() should be a no-op for the injected executor.
            orch.close()
            # Still alive — can submit and the future completes.
            fut = executor.submit(lambda: "still-alive")
            assert fut.result(timeout=2.0) == "still-alive"
            # And another orchestrate_turn after close still works
            # against the same injected executor.
            orch2, *_ = _make_orchestrator(session_factory, executor=executor)
            try:
                result = orch2.orchestrate_turn(story_id, node_id, "another input.")
                assert result.disposition is PipelineDisposition.DELIVERED
            finally:
                orch2.close()
        finally:
            executor.shutdown(wait=True)


# ---------------------------------------------------------------------------
# Parallel-sync submission failure routing (Codex P1 #87)
#
# ``executor.submit(...)`` itself can raise — most commonly
# ``RuntimeError("cannot schedule new futures after shutdown")`` when an
# injected executor has already been shut down by the caller.  That must
# not escape ``orchestrate_turn`` as a raw exception; the orchestrator's
# exhaustive typed-terminal-state contract requires PIPELINE_ERROR + outer
# transaction rollback for any operational failure inside the parallel-sync
# stage, submission failure included.
# ---------------------------------------------------------------------------


class TestParallelSyncSubmitFailure:
    def test_shutdown_executor_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        # Pre-shut-down injected executor: the orchestrator's next
        # ``executor.submit(...)`` call inside ``_run_parallel_sync`` will
        # raise ``RuntimeError("cannot schedule new futures after shutdown")``
        # before any contradiction future is assigned.  Without the fix
        # that exception escapes ``orchestrate_turn`` raw.
        executor = ThreadPoolExecutor(max_workers=1)
        executor.shutdown(wait=False)

        orch, *_ = _make_orchestrator(session_factory, executor=executor)

        # Must not raise.
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "submission failed" in summary, summary
        assert "parallel sync failed" in summary, summary
        # Single canonical terminal-cause channel held: no rogue refusal.
        assert result.provider_refusal is None
        # Outer transaction rolled back: provisional Turn did not survive.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_submit_raising_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        """Focused unit-style coverage: any ``submit()`` exception, not just
        the shutdown ``RuntimeError``, must map to PIPELINE_ERROR.  Uses a
        ThreadPoolExecutor subclass whose ``submit`` always raises so the
        path is exercised without relying on shutdown-specific message text.
        """

        class _ExplodingExecutor(ThreadPoolExecutor):
            def submit(self, fn, /, *args, **kwargs):  # type: ignore[override]
                raise RuntimeError("synthetic submit failure")

        story_id, node_id = seeded_story
        executor = _ExplodingExecutor(max_workers=1)
        try:
            orch, *_ = _make_orchestrator(session_factory, executor=executor)
            result = orch.orchestrate_turn(story_id, node_id, "I open the door.")
        finally:
            executor.shutdown(wait=False)

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "synthetic submit failure" in summary, summary
        assert result.provider_refusal is None
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []


# ---------------------------------------------------------------------------
# Generic contradiction-worker exception routing (Codex P1 #87 round 6)
#
# ``contradiction_future.result(timeout=...)`` historically only caught
# ``FutureTimeout``, ``ProviderRefusalError``, and ``ContradictionPassError``.
# Any other worker exception (generic ``RuntimeError``, ``CancelledError``,
# transport error, etc.) escaped raw — violating the orchestrator's
# exhaustive typed-terminal-state contract.  The final ``except Exception``
# branch must map those to PIPELINE_ERROR + outer-transaction rollback.
# ``BaseException`` is deliberately NOT caught so ``KeyboardInterrupt`` /
# ``SystemExit`` still propagate.
# ---------------------------------------------------------------------------


class TestParallelSyncContradictionWorkerExceptions:
    def test_runtime_error_from_worker_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            contradiction_exc=RuntimeError("synthetic worker failure"),
        )

        # Must not raise — generic worker exceptions must become typed.
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "contradiction worker failed" in summary, summary
        assert "synthetic worker failure" in summary, summary
        # Single canonical terminal-cause channel held.
        assert result.provider_refusal is None
        # Provisional Turn rolled back at the outer transaction boundary.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_value_error_from_worker_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        """Distinct exception type to prove the catch-all is type-agnostic."""
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            contradiction_exc=ValueError("bad payload"),
        )

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "contradiction worker failed" in summary, summary
        assert "bad payload" in summary, summary
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_cancelled_error_from_worker_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        """``concurrent.futures.CancelledError`` from the worker — surfaced
        when the future is cancelled before completion — must also map to
        PIPELINE_ERROR.  It subclasses ``BaseException`` (Python 3.8+) so
        it would slip past a plain ``except Exception``; the orchestrator
        handles it via an explicit ``except CancelledError`` branch.
        """
        from concurrent.futures import CancelledError

        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            contradiction_exc=CancelledError("worker cancelled"),
        )

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "contradiction worker cancelled" in summary, summary
        # Single canonical terminal-cause channel held.
        assert result.provider_refusal is None
        # Outer transaction rolled back: no provisional Turn persisted.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_baseexception_subclass_still_propagates(
        self, session_factory, seeded_story
    ) -> None:
        """Defense in depth: ``KeyboardInterrupt`` / ``SystemExit`` must
        propagate past the orchestrator so the host process can shut down.
        The new catch-all is ``except Exception``, not ``except BaseException``.
        """
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            contradiction_exc=KeyboardInterrupt("user hit Ctrl-C"),
        )
        with pytest.raises(KeyboardInterrupt):
            orch.orchestrate_turn(story_id, node_id, "I open the door.")


# ---------------------------------------------------------------------------
# Systematic exception-mapping family (Codex P1 #87 round 7)
#
# Owner direction (Issue 12c): ``orchestrate_turn`` is an exhaustive typed
# boundary for ordinary operational failures.  Every ``Exception`` raised
# by an injected orchestration dependency or orchestration-owned runtime
# step maps to a typed terminal disposition; the specific dispositions
# (Safety BLOCK verdicts, Contradiction BLOCK, ``ProviderRefusalError`` →
# REFUSED_BY_PROVIDER, pass-specific typed errors, contradiction-refusal-
# with-extractor preservation) remain authoritative for their categories;
# any other ``Exception`` becomes PIPELINE_ERROR with cause text.
#
# ``BaseException`` (``KeyboardInterrupt``, ``SystemExit``) propagates.
#
# This class proves the family rule holds at every per-site fallback, not
# just the two cases Codex flagged.  Each site:
#   - narrative Input Safety, narrative Output Safety
#   - OOC Input Safety, OOC Output Safety
#   - Planner
#   - narrative Writer, OOC Writer
#   - Extractor (inside _run_parallel_sync)
# has its own test asserting:
#   - no raw exception escapes,
#   - disposition is PIPELINE_ERROR,
#   - cause text uses the per-site "unexpected error" disambiguator,
#   - no rogue provider_refusal,
#   - upstream pass results preserved as the result model allows,
#   - outer transaction rolled back (no Turn persisted) when applicable.
# Plus a final ``KeyboardInterrupt`` propagation test per pass to prove
# the catch-all was not widened to ``except BaseException``.
# ---------------------------------------------------------------------------


class TestUnexpectedExceptionFamily:
    # -- Planner --------------------------------------------------------

    def test_planner_unexpected_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            planner_exc=RuntimeError("planner blew up"),
        )

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "planner unexpected error" in summary, summary
        assert "planner blew up" in summary, summary
        assert result.provider_refusal is None
        # Planner ran before Writer, so no Turn was ever persisted.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_planner_keyboard_interrupt_propagates(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            planner_exc=KeyboardInterrupt("ctrl-c during planner"),
        )
        with pytest.raises(KeyboardInterrupt):
            orch.orchestrate_turn(story_id, node_id, "I open the door.")

    # -- Narrative Writer ----------------------------------------------

    def test_narrative_writer_unexpected_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            writer_exc=RuntimeError("writer blew up"),
        )

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "writer unexpected error" in summary, summary
        assert "writer blew up" in summary, summary
        assert result.provider_refusal is None
        # Upstream pass results preserved.
        assert result.planner_result is not None
        # Provisional Turn rolled back.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_narrative_writer_keyboard_interrupt_propagates(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            writer_exc=KeyboardInterrupt("ctrl-c during writer"),
        )
        with pytest.raises(KeyboardInterrupt):
            orch.orchestrate_turn(story_id, node_id, "I open the door.")

    # -- OOC Writer ----------------------------------------------------

    def test_ooc_writer_unexpected_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            intent=IntentType.OOC,
            writer_exc=RuntimeError("ooc writer blew up"),
        )

        result = orch.orchestrate_turn(story_id, node_id, "[OOC] What is HP?")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "ooc writer unexpected error" in summary, summary
        assert "ooc writer blew up" in summary, summary
        assert result.provider_refusal is None
        # OOC short-circuit skipped Planner; planner_result remains None.
        assert result.planner_result is None
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_ooc_writer_keyboard_interrupt_propagates(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            intent=IntentType.OOC,
            writer_exc=KeyboardInterrupt("ctrl-c during ooc writer"),
        )
        with pytest.raises(KeyboardInterrupt):
            orch.orchestrate_turn(story_id, node_id, "[OOC] anything")

    # -- Narrative Input Safety ----------------------------------------

    def test_narrative_input_safety_unexpected_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            safety_input=RuntimeError("input safety blew up"),
        )

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "input safety unexpected error" in summary, summary
        assert "input safety blew up" in summary, summary
        assert result.provider_refusal is None
        # Failure before Writer → no Turn.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    # -- Narrative Output Safety ---------------------------------------

    def test_narrative_output_safety_unexpected_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            safety_output=RuntimeError("output safety blew up"),
        )

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "output safety unexpected error" in summary, summary
        assert "output safety blew up" in summary, summary
        assert result.provider_refusal is None
        # Upstream preserved through Writer; provisional Turn rolled back.
        assert result.planner_result is not None
        assert result.writer_result is not None
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    # -- OOC Input Safety ----------------------------------------------

    def test_ooc_input_safety_unexpected_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            intent=IntentType.OOC,
            safety_input=RuntimeError("ooc input safety blew up"),
        )

        result = orch.orchestrate_turn(story_id, node_id, "[OOC] foo")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "input safety unexpected error" in summary, summary
        assert "ooc input safety blew up" in summary, summary
        assert result.provider_refusal is None
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    # -- OOC Output Safety ---------------------------------------------

    def test_ooc_output_safety_unexpected_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            intent=IntentType.OOC,
            safety_output=RuntimeError("ooc output safety blew up"),
        )

        result = orch.orchestrate_turn(story_id, node_id, "[OOC] foo")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "output safety unexpected error" in summary, summary
        assert "ooc output safety blew up" in summary, summary
        assert result.provider_refusal is None
        # OOC writer ran before output-safety failed; preserved for
        # observability.
        assert result.writer_result is not None
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    # -- Extractor (inside _run_parallel_sync) -------------------------

    def test_extractor_unexpected_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            extractor_exc=RuntimeError("extractor blew up"),
        )

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        # Path: Extractor catch-all → _ParallelSyncError → narrative
        # caller's parallel-sync mapping → PIPELINE_ERROR.  Both prefixes
        # must appear in the cause chain text.
        assert "parallel sync failed" in summary, summary
        assert "extractor unexpected error" in summary, summary
        assert "extractor blew up" in summary, summary
        assert result.provider_refusal is None
        # Upstream Writer result preserved by the parallel-sync caller.
        assert result.writer_result is not None
        # Provisional Turn rolled back; Extractor SAVEPOINT writes (if any)
        # rolled back with it.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_extractor_keyboard_interrupt_propagates(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            extractor_exc=KeyboardInterrupt("ctrl-c during extractor"),
        )
        with pytest.raises(KeyboardInterrupt):
            orch.orchestrate_turn(story_id, node_id, "I open the door.")


# ---------------------------------------------------------------------------
# Preserve extractor_result on contradiction refusal (Codex P2 #87)
#
# Refusal contract: "upstream pass results are preserved; only the failing
# pass result is absent."  When Extractor completes successfully and
# Contradiction refuses, the resulting REFUSED_BY_PROVIDER must carry the
# completed ``extractor_result``.  Extractor-side refusal continues to
# leave ``extractor_result`` absent because Extractor IS the failing pass
# in that case.
# ---------------------------------------------------------------------------


class TestExtractorPreservationOnContradictionRefusal:
    def test_contradiction_refusal_preserves_extractor_result(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_, extractor, contradiction = _make_orchestrator(
            session_factory,
            contradiction_exc=make_refusal(PassIdentifier.CONTRADICTION),
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert result.provider_refusal is not None
        assert result.provider_refusal.pass_identifier is PassIdentifier.CONTRADICTION
        # Upstream pass results preserved.
        assert result.planner_result is not None
        assert result.writer_result is not None
        # Extractor completed before Contradiction refused — must be preserved.
        assert result.extractor_result is not None
        # Failing pass (Contradiction) result must be absent.
        assert result.contradiction_result is None
        # Sanity: Extractor was actually invoked on the orchestrator thread.
        assert len(extractor.calls) == 1

    def test_extractor_refusal_leaves_extractor_result_none(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            extractor_exc=make_refusal(PassIdentifier.EXTRACTOR),
        )
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert result.provider_refusal is not None
        assert result.provider_refusal.pass_identifier is PassIdentifier.EXTRACTOR
        # The failing pass result must remain absent — this is what the
        # OrchestrationResult invariant enforces, and the refusal contract
        # requires.
        assert result.extractor_result is None
        # Upstream Writer result still preserved.
        assert result.writer_result is not None

    def test_contradiction_refusal_rolls_back_provisional_turn_and_writes(
        self, session_factory, seeded_story, session
    ) -> None:
        """Real-SQLite proof: even though ``extractor_result`` is preserved
        on the OrchestrationResult, the outer transaction (and the
        Extractor SAVEPOINT inside it) still rolls back.  The provisional
        Turn and every Story Bible write category must not survive.
        """
        story_id, node_id = seeded_story
        # Seed a named character so SoftFactProposal has a target.
        sbs_seed = StoryBibleService(session)
        sbs_seed.add_cast_entry(
            story_id,
            CastEntry(
                story_id=story_id,
                name="Mira",
                role=CastRole_ANTAGONIST(),
                current_location="village",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        )
        session.commit()

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

        orch, *_ = _make_orchestrator(
            session_factory,
            contradiction_exc=make_refusal(PassIdentifier.CONTRADICTION),
            extractor_real_sbs=StoryBibleService(session_factory()),
            extractor_proposal_factory=proposal_factory,
        )

        result = orch.orchestrate_turn(story_id, node_id, "Mira moves.")
        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        # Per the refusal contract, the completed extractor_result is
        # surfaced on the OrchestrationResult …
        assert result.extractor_result is not None

        # … yet none of those writes persisted: outer transaction rolled back.
        post_turn = session.execute(select(TurnORM)).scalars().all()
        post_event = session.execute(select(SBEventORM)).scalars().all()
        post_thread = session.execute(select(SBUnresolvedThreadORM)).scalars().all()
        post_stage = session.execute(select(SBProvisionalStagingORM)).scalars().all()
        assert [t.turn_id for t in post_turn] == [t.turn_id for t in pre_turn]
        assert [e.event_id for e in post_event] == [e.event_id for e in pre_event]
        assert [t.thread_id for t in post_thread] == [t.thread_id for t in pre_thread]
        assert [p.proposal_id for p in post_stage] == [p.proposal_id for p in pre_stage]


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


# ---------------------------------------------------------------------------
# Single canonical terminal-cause channel (Codex P2 #87)
#
# Audit the invariant family: every disposition must populate at most one
# of provider_refusal / pipeline_error_summary so downstream analytics,
# support reconstruction, and entitlement routing can resolve "why did
# this turn end?" from a single field without ambiguity.
# ---------------------------------------------------------------------------


def _stub_writer_result(prose: str = "Narrator: the door swings open."):
    return WriterResult(
        turn_id=uuid4(),
        assistant_output=prose,
        model_identifier="anthropic:fake-sonnet",
        latency_ms=1,
        input_token_count=1,
        output_token_count=1,
        cache_read_token_count=0,
        cache_creation_token_count=0,
    )


def _stub_extractor_result():
    from afterworlds.models.extractor import (
        ExtractorProposalSet,
        ExtractorRoutingSummary,
    )
    from afterworlds.pipeline.extractor.models import ExtractorResult

    return ExtractorResult(
        proposal_set=ExtractorProposalSet(proposals=[]),
        routed=ExtractorRoutingSummary(
            locked_fact_staged_ids=[],
            soft_fact_staged_ids=[],
            transient_state_staged_ids=[],
            unresolved_thread_staged_ids=[],
            event_ids=[],
        ),
        input_token_count=1,
        output_token_count=1,
        cache_read_token_count=0,
        cache_creation_token_count=0,
    )


def _stub_contradiction_result(
    verdict: ContradictionVerdict = ContradictionVerdict.CLEAR,
    violations: list[ContradictionViolation] | None = None,
):
    return ContradictionResult(
        verdict=verdict,
        violations=violations or [],
        model_identifier="anthropic:fake-haiku",
        latency_ms=1,
        input_token_count=1,
        output_token_count=1,
        cache_read_token_count=0,
        cache_creation_token_count=0,
    )


def _stub_refusal(pass_id: PassIdentifier = PassIdentifier.WRITER) -> ProviderRefusal:
    return ProviderRefusal(
        provider="anthropic",
        model="fake",
        pass_identifier=pass_id,
        coarse_reason="content policy",
        raw_response_excerpt="declined",
    )


class TestSingleTerminalCauseChannel:
    """Every disposition must populate at most one of provider_refusal /
    pipeline_error_summary.  This audit covers the whole family, not just
    the disposition Codex flagged, so the rule cannot drift later when a
    new disposition is added.
    """

    # -- DELIVERED ------------------------------------------------------

    def test_delivered_forbids_provider_refusal(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.DELIVERED,
                delivered_output="prose",
                turn_id=uuid4(),
                intent_classification=intent,
                planner_result=_stub_planner_result(),
                writer_result=_stub_writer_result(),
                extractor_result=_stub_extractor_result(),
                contradiction_result=_stub_contradiction_result(),
                provider_refusal=_stub_refusal(),  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    def test_delivered_forbids_pipeline_error_summary(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.DELIVERED,
                delivered_output="prose",
                turn_id=uuid4(),
                intent_classification=intent,
                planner_result=_stub_planner_result(),
                writer_result=_stub_writer_result(),
                extractor_result=_stub_extractor_result(),
                contradiction_result=_stub_contradiction_result(),
                pipeline_error_summary="ghost cause",  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    # -- OOC_HANDLED ----------------------------------------------------

    def test_ooc_handled_forbids_provider_refusal(self) -> None:
        intent = make_intent(IntentType.OOC, "[OOC] ?")
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.OOC_HANDLED,
                delivered_output="OOC reply",
                turn_id=uuid4(),
                intent_classification=intent,
                writer_result=_stub_writer_result("OOC reply"),
                provider_refusal=_stub_refusal(),  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    def test_ooc_handled_forbids_pipeline_error_summary(self) -> None:
        intent = make_intent(IntentType.OOC, "[OOC] ?")
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.OOC_HANDLED,
                delivered_output="OOC reply",
                turn_id=uuid4(),
                intent_classification=intent,
                writer_result=_stub_writer_result("OOC reply"),
                pipeline_error_summary="ghost cause",  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    # -- BLOCKED_INPUT_SAFETY ------------------------------------------

    def test_blocked_input_safety_forbids_provider_refusal(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_INPUT_SAFETY,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                input_safety_result=_block_safety(SafetyTarget.INPUT),
                provider_refusal=_stub_refusal(),  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    def test_blocked_input_safety_forbids_pipeline_error_summary(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_INPUT_SAFETY,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                input_safety_result=_block_safety(SafetyTarget.INPUT),
                pipeline_error_summary="ghost cause",  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    # -- BLOCKED_OUTPUT_SAFETY -----------------------------------------

    def test_blocked_output_safety_forbids_provider_refusal_narrative(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_OUTPUT_SAFETY,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                planner_result=_stub_planner_result(),
                writer_result=_stub_writer_result(),
                output_safety_result=_block_safety(SafetyTarget.OUTPUT),
                provider_refusal=_stub_refusal(),  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    def test_blocked_output_safety_forbids_pipeline_error_summary_narrative(
        self,
    ) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_OUTPUT_SAFETY,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                planner_result=_stub_planner_result(),
                writer_result=_stub_writer_result(),
                output_safety_result=_block_safety(SafetyTarget.OUTPUT),
                pipeline_error_summary="ghost cause",  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    def test_blocked_output_safety_forbids_provider_refusal_ooc(self) -> None:
        intent = make_intent(IntentType.OOC, "[OOC] ?")
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_OUTPUT_SAFETY,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                writer_result=_stub_writer_result(),
                output_safety_result=_block_safety(SafetyTarget.OUTPUT),
                provider_refusal=_stub_refusal(),  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    # -- BLOCKED_CONTRADICTION -----------------------------------------

    def test_blocked_contradiction_forbids_provider_refusal(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_CONTRADICTION,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                planner_result=_stub_planner_result(),
                writer_result=_stub_writer_result(),
                contradiction_result=_stub_contradiction_result(
                    verdict=ContradictionVerdict.BLOCKED,
                    violations=[
                        ContradictionViolation(
                            category=ContradictionCategory.OTHER,
                            description="x",
                            canon_reference="ref",
                        )
                    ],
                ),
                provider_refusal=_stub_refusal(),  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    def test_blocked_contradiction_forbids_pipeline_error_summary(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_CONTRADICTION,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                planner_result=_stub_planner_result(),
                writer_result=_stub_writer_result(),
                contradiction_result=_stub_contradiction_result(
                    verdict=ContradictionVerdict.BLOCKED,
                    violations=[
                        ContradictionViolation(
                            category=ContradictionCategory.OTHER,
                            description="x",
                            canon_reference="ref",
                        )
                    ],
                ),
                pipeline_error_summary="ghost cause",  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    # -- REFUSED_BY_PROVIDER -------------------------------------------

    def test_refused_by_provider_forbids_pipeline_error_summary(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.REFUSED_BY_PROVIDER,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                provider_refusal=_stub_refusal(),
                pipeline_error_summary="ghost cause",  # forbidden
                total_latency_ms=10,
                pass_latency_breakdown={},
            )

    # -- PIPELINE_ERROR ------------------------------------------------

    def test_pipeline_error_forbids_provider_refusal(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.PIPELINE_ERROR,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                pipeline_error_summary="real cause",
                provider_refusal=_stub_refusal(),  # forbidden
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


# ---------------------------------------------------------------------------
# StoryBibleService session-threading regression (Codex P1 #87)
# ---------------------------------------------------------------------------


class TestStoryBibleSessionThreading:
    """Codex P1 #87 third finding: ``route_extractor_proposals`` must thread
    the caller-supplied session through helpers without mutating
    ``self._session``.  Mutating instance state introduces a thread-safety
    race when a single service handles concurrent turns.
    """

    def test_self_session_not_mutated_when_session_supplied(
        self, session_factory, seeded_story, session
    ) -> None:
        from afterworlds.models.extractor import (
            EventProposal,
            ExtractorProposalSet,
            LockedFactProposal,
            SoftFactProposal,
            UnresolvedThreadProposal,
        )

        story_id, _ = seeded_story
        # Service uses one session; the orchestrator passes a different
        # session.  After routing, the service's session attribute must
        # still be the original — not the caller's.
        service_session = session_factory()
        sbs = StoryBibleService(service_session)
        # Seed a named cast entry so soft-fact routing can resolve it.
        sbs.add_cast_entry(
            story_id,
            CastEntry(
                story_id=story_id,
                name="Mira",
                role=CastRole_ANTAGONIST(),
                current_location="village",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            ),
        )
        service_session.commit()
        original_session_id = id(sbs._session)
        assert sbs._session is service_session

        # Build a non-trivial proposal set covering every routing branch
        # so each helper is actually exercised with the caller's session.
        proposal_set = ExtractorProposalSet(
            proposals=[
                LockedFactProposal(fact_text="The vault is sealed."),
                SoftFactProposal(
                    target_domain=TargetDomain.CHARACTER,
                    target_natural_key="Mira",
                    target_field="current_location",
                    proposed_value="forest",
                ),
                UnresolvedThreadProposal(description="What did Mira hide?"),
                EventProposal(
                    description="Mira fled to the forest.",
                    significance=EventSignificance.MAJOR_PLOT_TURN,
                    event_kind=EventKind.LOCATION_CHANGE,
                ),
            ]
        )

        caller_session = session_factory()
        caller_session.begin()
        try:
            from uuid import uuid4

            sbs.route_extractor_proposals(
                story_id, uuid4(), proposal_set, session=caller_session
            )
        finally:
            if caller_session.in_transaction():
                caller_session.rollback()
            caller_session.close()

        # The service's session identity must be the SAME object as before.
        # Any deviation would mean ``self._session`` was overwritten — the
        # thread-safety regression Codex flagged.
        assert sbs._session is service_session
        assert id(sbs._session) == original_session_id

        service_session.close()

    def test_concurrent_calls_do_not_corrupt_self_session(
        self, session_factory, seeded_story
    ) -> None:
        """Stress regression: many concurrent route_extractor_proposals calls
        through one service instance, each with its own session, must not
        cross-contaminate writes.  This would have failed under the
        previous ``self._session`` swap pattern under enough contention.

        Codex P2 #87 round 6: the previous version was vacuously passing
        whenever workers raised before appending to ``seen_session_ids``
        (``all(...)`` over an empty list is True).  In practice the
        conftest's default in-memory SQLite engine uses
        ``SingletonThreadPool``, so workers raised
        ``sqlite3.ProgrammingError`` on cross-thread connection use —
        every observation was lost and the test passed for the wrong
        reason.

        The fix is twofold:

        1. Build a temp-file SQLite engine inline so each worker thread
           gets its own connection from the pool (WAL mode set by the
           project's ``create_engine`` hook allows concurrent readers
           plus a single serialised writer).  Per-connection SAVEPOINTs
           do not collide.
        2. Capture worker exceptions in a lock-guarded list and assert
           both ``worker_errors == []`` AND
           ``len(seen_session_ids) == WORKER_COUNT`` so silent failure
           cannot hide.
        """
        import os
        import tempfile
        import threading
        from uuid import uuid4

        from afterworlds.models.extractor import (
            EventProposal,
            ExtractorProposalSet,
        )
        from afterworlds.models.node import (
            BranchingNodeMetadata,
            Node,
            NodeMetadata,
            StateDelta,
        )
        from afterworlds.models.story import Arc, Chapter, Story
        from afterworlds.persistence.crud.node import create_node
        from afterworlds.persistence.crud.story import (
            create_arc,
            create_chapter,
            create_story,
        )
        from afterworlds.persistence.database import (
            create_engine,
            create_session_factory,
        )
        from afterworlds.persistence.orm.base import Base

        WORKER_COUNT = 8

        # Default conftest engine uses SingletonThreadPool against an
        # in-memory SQLite — workers would hit
        # ``sqlite3.ProgrammingError`` on cross-thread connection access.
        # Use a temp-file SQLite database so each thread gets its own
        # connection from the pool and SAVEPOINTs do not collide; WAL
        # journal mode (set by the project's connect-hook) lets readers
        # run concurrently with a single serialised writer.
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        thread_safe_engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(thread_safe_engine)
        try:
            sf = create_session_factory(thread_safe_engine)

            # Seed a minimal Story / Arc / Chapter / Node chain so
            # route_extractor_proposals has a valid story to operate on.
            seed_session = sf()
            now = datetime(2026, 1, 1, tzinfo=UTC)
            story = Story(
                title="Threading Test Story",
                mode=StoryMode_BRANCHING(),
                created_at=now,
                updated_at=now,
            )
            create_story(seed_session, story)
            arc = Arc(story_id=story.story_id, title="Arc 1", order=0)
            create_arc(seed_session, arc)
            chapter = Chapter(arc_id=arc.arc_id, title="Chapter 1", order=0)
            create_chapter(seed_session, chapter)
            node = Node(
                chapter_id=chapter.chapter_id,
                content="",
                state_delta=StateDelta(),
                branching_logic=[],
                intent_type=IntentType.IN_CHARACTER_ACTION,
                metadata=NodeMetadata(timestamp=now),
                mode_metadata=BranchingNodeMetadata(),
            )
            create_node(seed_session, node)
            seed_session.commit()
            story_id = story.story_id
            seed_session.close()

            service_session = sf()
            sbs = StoryBibleService(service_session)
            original_session_id = id(service_session)

            seen_session_ids: list[int] = []
            seen_session_ids_lock = threading.Lock()
            worker_errors: list[BaseException] = []
            worker_errors_lock = threading.Lock()

            def worker() -> None:
                try:
                    caller_session = sf()
                    caller_session.begin()
                    try:
                        proposal_set = ExtractorProposalSet(
                            proposals=[
                                EventProposal(
                                    description="thread-event",
                                    significance=EventSignificance.ROUTINE,
                                    event_kind=EventKind.ROUTINE,
                                )
                            ]
                        )
                        sbs.route_extractor_proposals(
                            story_id,
                            uuid4(),
                            proposal_set,
                            session=caller_session,
                        )
                        with seen_session_ids_lock:
                            seen_session_ids.append(id(sbs._session))
                    finally:
                        if caller_session.in_transaction():
                            caller_session.rollback()
                        caller_session.close()
                except BaseException as exc:  # noqa: BLE001 — test surface
                    # Capture worker failures so the main thread can
                    # assert on them.  Without this, a worker that raises
                    # before the append would leave ``seen_session_ids``
                    # short or empty and let ``all(...)`` vacuously pass.
                    with worker_errors_lock:
                        worker_errors.append(exc)

            threads = [threading.Thread(target=worker) for _ in range(WORKER_COUNT)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # No worker may have raised — covers the case where session
            # threading itself blew up before any observation could be made.
            assert worker_errors == [], (
                f"{len(worker_errors)} worker(s) raised: "
                f"{[type(e).__name__ + ': ' + str(e) for e in worker_errors]}"
            )
            # Exactly the configured number of observations were recorded —
            # guards against vacuous ``all(...)`` over an empty list AND
            # against a partial-completion regression.
            assert len(seen_session_ids) == WORKER_COUNT, (
                f"expected {WORKER_COUNT} observations, " f"got {len(seen_session_ids)}"
            )
            # Every observation must show the original service session —
            # never any of the caller sessions opened by the workers.
            assert all(sid == original_session_id for sid in seen_session_ids)
            # And the service's ``_session`` attribute must still be the
            # original — no caller-supplied session leaked into it.
            assert sbs._session is service_session
            service_session.close()
        finally:
            Base.metadata.drop_all(thread_safe_engine)
            thread_safe_engine.dispose()
            # Best-effort temp-file cleanup; ignore Windows file-lock
            # races that occasionally surface after the engine is
            # disposed.  The OS removes the file at reboot anyway.
            with suppress(OSError):
                os.unlink(db_path)


def StoryMode_BRANCHING():
    from afterworlds.models.enums import StoryMode

    return StoryMode.BRANCHING


def _volatile_for(intent):
    from afterworlds.models.context import VolatileSuffix

    return VolatileSuffix(
        recent_turns=[],
        current_input=intent.raw_input,
        classified_intent=intent,
    )


# ---------------------------------------------------------------------------
# Commit-failure path (Codex P1 #87, round 2)
# ---------------------------------------------------------------------------


class _CommitFailingSessionFactory:
    """Wraps a real session factory and patches each returned session's
    ``commit`` to raise a configurable exception.  Tracks how many times
    each session's ``rollback`` was called so tests can assert the
    orchestrator attempted a best-effort rollback after commit failure.
    """

    def __init__(
        self,
        real_factory,  # type: ignore[no-untyped-def]
        commit_exc: Exception,
    ) -> None:
        self._real_factory = real_factory
        self._commit_exc = commit_exc
        self.rollback_calls: int = 0
        self.commit_attempts: int = 0

    def __call__(self):  # type: ignore[no-untyped-def]
        sess = self._real_factory()
        outer = self  # capture for nested closures

        original_commit = sess.commit
        original_rollback = sess.rollback

        def failing_commit() -> None:
            outer.commit_attempts += 1
            raise outer._commit_exc

        def counted_rollback() -> None:
            outer.rollback_calls += 1
            return original_rollback()

        sess.commit = failing_commit  # type: ignore[method-assign,assignment]
        sess.rollback = counted_rollback  # type: ignore[method-assign,assignment]
        # Preserve original_commit reference so tests can introspect if needed.
        sess._original_commit = original_commit  # type: ignore[attr-defined]
        return sess


class TestCommitFailureRoutesToPipelineError:
    """Codex P1 #87 round 2: ``session.commit()`` at the post-pipeline
    finalize boundary can raise (flush / constraint / IO / disk-full /
    transient deadlock).  The orchestrator must convert that into a
    typed PIPELINE_ERROR result rather than letting a raw SQLAlchemy
    exception escape past ``orchestrate_turn``'s exhaustive-disposition
    contract.

    All tests build the orchestrator with a session factory whose
    sessions raise on commit; everything else (Planner, Writer,
    Extractor, Contradiction, Safety) runs the happy path so the inner
    pipeline produces a nominal DELIVERED or OOC_HANDLED before the
    finalize boundary fails.
    """

    def test_narrative_commit_failure_returns_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        failing_factory = _CommitFailingSessionFactory(
            session_factory, RuntimeError("simulated disk full")
        )
        orch, *_ = _make_orchestrator(failing_factory)

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        # Must NOT have raised.  Must produce a typed PIPELINE_ERROR.
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        # Cause text preserved.
        assert "transaction commit failed" in (result.pipeline_error_summary or "")
        assert "delivered" in (result.pipeline_error_summary or "")
        assert "simulated disk full" in (result.pipeline_error_summary or "")
        # delivered_output / turn_id MUST NOT survive — the spec says only
        # DELIVERED / OOC_HANDLED leave a surviving Turn row.
        assert result.delivered_output is None
        assert result.turn_id is None
        # Pre-commit pass results are preserved for observability.
        assert result.planner_result is not None
        assert result.writer_result is not None
        assert result.extractor_result is not None
        assert result.contradiction_result is not None
        # Rollback was attempted at the finalize boundary.
        assert failing_factory.rollback_calls >= 1
        # No Turn row in the database — the candidate Turn was rolled back.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_ooc_commit_failure_returns_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        failing_factory = _CommitFailingSessionFactory(
            session_factory, ConnectionError("simulated DB timeout")
        )
        orch, *_ = _make_orchestrator(failing_factory, intent=IntentType.OOC)

        result = orch.orchestrate_turn(story_id, node_id, "[OOC] What is HP?")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "transaction commit failed" in (result.pipeline_error_summary or "")
        assert "ooc_handled" in (result.pipeline_error_summary or "")
        assert "simulated DB timeout" in (result.pipeline_error_summary or "")
        # OOC path: delivered_output and turn_id must not survive either.
        assert result.delivered_output is None
        assert result.turn_id is None
        # Writer ran successfully before the commit boundary; preserved.
        assert result.writer_result is not None
        # OOC short-circuit skipped Planner / Extractor / Contradiction;
        # those remain None as in the original OOC_HANDLED candidate.
        assert result.planner_result is None
        assert result.extractor_result is None
        assert result.contradiction_result is None
        # Rollback attempted.
        assert failing_factory.rollback_calls >= 1
        # No OOC Turn persisted.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_narrative_commit_failure_attempts_rollback(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        failing_factory = _CommitFailingSessionFactory(
            session_factory, RuntimeError("boom")
        )
        orch, *_ = _make_orchestrator(failing_factory)

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        # The orchestrator tried exactly one commit; the failure path then
        # ran a best-effort rollback (one or more times depending on
        # whether SQLAlchemy auto-rollback fires too — at least one
        # rollback must have been observed by the wrapper).
        assert failing_factory.commit_attempts == 1
        assert failing_factory.rollback_calls >= 1

    def test_commit_failure_does_not_leak_delivered_output(
        self, session_factory, seeded_story
    ) -> None:
        """Defense in depth: the OrchestrationResult model invariant
        already forbids ``delivered_output`` on PIPELINE_ERROR, but assert
        the orchestrator does not even attempt to smuggle the candidate
        prose through — relying on the validator alone would silently
        convert the bug into an OrchestratorError instead of a clean
        PIPELINE_ERROR.
        """
        story_id, node_id = seeded_story
        failing_factory = _CommitFailingSessionFactory(
            session_factory, RuntimeError("commit gone wrong")
        )
        orch, _, _, _, _, writer, *_ = _make_orchestrator(failing_factory)

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        # The Writer fake produced a real assistant_output for the
        # candidate DELIVERED result.  After the commit failure the
        # post-pipeline diagnostic must not surface it as delivered prose.
        candidate_prose = writer.assistant_output
        assert candidate_prose  # sanity: Writer did produce prose
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.delivered_output is None
        assert result.delivered_output != candidate_prose
        # The Writer result is preserved for observability — the prose is
        # still inspectable there, just not promoted to delivered_output.
        assert result.writer_result is not None
        assert result.writer_result.assistant_output == candidate_prose


# ---------------------------------------------------------------------------
# Session-lifecycle failure routing (Codex P1 #87 round 5)
#
# Every raw exception in the session lifecycle (factory call, ``begin()``,
# ``close()``) must be funnelled through the orchestrator's typed
# terminal-state contract.  ``session_factory()`` and ``session.begin()``
# failures map to PIPELINE_ERROR with cause text; ``session.close()``
# failures are suppressed so they cannot silently replace an already-
# constructed typed ``OrchestrationResult`` with a raw cleanup exception.
# ---------------------------------------------------------------------------


def _factory_that_explodes(exc: Exception):  # type: ignore[no-untyped-def]
    """Session factory whose ``__call__`` raises before any session exists."""

    def _factory():  # type: ignore[no-untyped-def]
        raise exc

    return _factory


class _BeginFailingSessionFactory:
    """Session factory whose sessions raise on ``begin()``.

    Wraps a real factory so the orchestrator gets a working session shell;
    ``close()`` calls are counted to prove cleanup is still attempted even
    though no transaction was opened, and ``rollback()`` calls are counted
    to prove the orchestrator does NOT attempt rollback when ``begin()``
    failed (no transaction exists to roll back).
    """

    def __init__(
        self,
        real_factory,  # type: ignore[no-untyped-def]
        begin_exc: Exception,
    ) -> None:
        self._real_factory = real_factory
        self._begin_exc = begin_exc
        self.close_calls: int = 0
        self.rollback_calls: int = 0
        self.begin_attempts: int = 0

    def __call__(self):  # type: ignore[no-untyped-def]
        sess = self._real_factory()
        outer = self

        original_close = sess.close
        original_rollback = sess.rollback

        def failing_begin(*args, **kwargs):  # type: ignore[no-untyped-def]
            outer.begin_attempts += 1
            raise outer._begin_exc

        def tracking_close() -> None:
            outer.close_calls += 1
            return original_close()

        def counted_rollback() -> None:
            outer.rollback_calls += 1
            return original_rollback()

        sess.begin = failing_begin  # type: ignore[method-assign,assignment]
        sess.close = tracking_close  # type: ignore[method-assign,assignment]
        sess.rollback = counted_rollback  # type: ignore[method-assign,assignment]
        return sess


class _CloseFailingSessionFactory:
    """Session factory whose sessions raise on ``close()`` AFTER cleanup.

    Used to prove the orchestrator's outer ``finally`` suppresses
    ``session.close()`` failures so they cannot replace a typed
    DELIVERED / OOC_HANDLED result with a raw exception.  The wrapper
    calls the real close first so SQLite resources are still released.
    """

    def __init__(
        self,
        real_factory,  # type: ignore[no-untyped-def]
        close_exc: Exception,
    ) -> None:
        self._real_factory = real_factory
        self._close_exc = close_exc
        self.close_attempts: int = 0

    def __call__(self):  # type: ignore[no-untyped-def]
        sess = self._real_factory()
        outer = self

        original_close = sess.close

        def raising_close() -> None:
            outer.close_attempts += 1
            original_close()
            raise outer._close_exc

        sess.close = raising_close  # type: ignore[method-assign,assignment]
        return sess


class TestSessionLifecycleFailureRouting:
    # -- session_factory() raises ---------------------------------------

    def test_narrative_session_factory_failure_routes_to_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            _factory_that_explodes(RuntimeError("synthetic factory failure"))
        )

        # Must not raise.
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "session factory failed" in summary, summary
        assert "synthetic factory failure" in summary, summary
        # Single canonical terminal-cause channel held: no rogue refusal.
        assert result.provider_refusal is None
        # No Turn / Writer / Extractor results because the factory failed
        # before any pass could touch the session.
        assert result.writer_result is None
        assert result.extractor_result is None
        assert result.contradiction_result is None

    def test_ooc_session_factory_failure_routes_to_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            _factory_that_explodes(ConnectionError("DB unreachable")),
            intent=IntentType.OOC,
        )

        result = orch.orchestrate_turn(story_id, node_id, "[OOC] What is HP?")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "session factory failed" in summary, summary
        assert "DB unreachable" in summary, summary
        assert result.provider_refusal is None

    # -- session.begin() raises -----------------------------------------

    def test_narrative_session_begin_failure_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        failing_factory = _BeginFailingSessionFactory(
            session_factory, RuntimeError("synthetic begin failure")
        )
        orch, *_ = _make_orchestrator(failing_factory)

        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "session begin failed" in summary, summary
        assert "synthetic begin failure" in summary, summary
        # Cleanup attempted safely: ``close()`` ran exactly once even though
        # no transaction was opened, and ``rollback()`` was NOT called
        # because there was no transaction to roll back.
        assert failing_factory.begin_attempts == 1
        assert failing_factory.close_calls == 1
        assert failing_factory.rollback_calls == 0
        # No Turn persisted.
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    def test_ooc_session_begin_failure_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        failing_factory = _BeginFailingSessionFactory(
            session_factory, RuntimeError("OOC begin exploded")
        )
        orch, *_ = _make_orchestrator(failing_factory, intent=IntentType.OOC)

        result = orch.orchestrate_turn(story_id, node_id, "[OOC] What is HP?")

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "session begin failed" in summary, summary
        assert "OOC begin exploded" in summary, summary
        assert failing_factory.begin_attempts == 1
        assert failing_factory.close_calls == 1
        assert failing_factory.rollback_calls == 0
        verify = session.execute(select(TurnORM)).scalars().all()
        assert verify == []

    # -- session.close() raises (happy-path cleanup) --------------------

    def test_close_failure_does_not_replace_delivered_result(
        self, session_factory, seeded_story
    ) -> None:
        """Regression: a typed DELIVERED result must survive a ``close()``
        exception in the outer ``finally``.  The cleanup-suppress
        contract: the typed ``OrchestrationResult`` is the boundary, raw
        cleanup exceptions are suppressed.
        """
        story_id, node_id = seeded_story
        failing_factory = _CloseFailingSessionFactory(
            session_factory, RuntimeError("synthetic close failure")
        )
        orch, *_ = _make_orchestrator(failing_factory)

        # Must not raise — typed result must survive cleanup failure.
        result = orch.orchestrate_turn(story_id, node_id, "I open the door.")

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.delivered_output is not None
        assert result.turn_id is not None
        # close() was actually attempted; the original resource was freed
        # before the synthetic raise.
        assert failing_factory.close_attempts == 1

    def test_close_failure_does_not_replace_ooc_handled_result(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        failing_factory = _CloseFailingSessionFactory(
            session_factory, RuntimeError("ooc close failure")
        )
        orch, *_ = _make_orchestrator(failing_factory, intent=IntentType.OOC)

        result = orch.orchestrate_turn(story_id, node_id, "[OOC] What is HP?")

        assert result.disposition is PipelineDisposition.OOC_HANDLED
        assert result.delivered_output is not None
        assert result.turn_id is not None
        assert failing_factory.close_attempts == 1


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
