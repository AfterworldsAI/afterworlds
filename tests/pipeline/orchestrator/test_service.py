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
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.models.character_sheet import Dnd5eAbilityScores, Dnd5eCharacterSheet
from afterworlds.models.context import AssembledContext
from afterworlds.models.enums import (
    DiceHandling,
    EventKind,
    EventSignificance,
    IntentType,
    RpgPlayStatus,
    RpgSessionType,
    RpgSetupPhase,
    RpgTone,
    StoryMode,
    TargetDomain,
)
from afterworlds.models.extractor import (
    EventProposal,
    ExtractorProposalSet,
    LockedFactProposal,
    SoftFactProposal,
    UnresolvedThreadProposal,
)
from afterworlds.models.rpg import (
    PendingRollRequest,
    RpgVisibleState,
    VisibleCharacterState,
)
from afterworlds.models.session import RpgSessionState
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
    CapabilityProfileAwareSafetyPolicy,
    OrchestrationResult,
    OrchestratorError,
    OrchestratorService,
    PipelineDisposition,
)
from afterworlds.pipeline.planner.models import PlannerOutput
from afterworlds.pipeline.provider._routing import (
    EligibleModelRoute,
    SafetyWhitelistStatus,
    TurnProviderBinding,
)
from afterworlds.pipeline.safety.models import (
    SafetyCategory,
    SafetyConcern,
    SafetyPassError,
    SafetyReport,
    SafetyResult,
    SafetyTarget,
    SafetyVerdict,
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
# Test-scoped sojourner + fake resolver
# ---------------------------------------------------------------------------

_SOJOURNER = uuid4()


class _FakeProviderAdapter:
    """Minimal adapter placeholder; fake pass services ignore the provider kwarg."""

    provider_name = "fake-anthropic"

    def call(self, request: object) -> object:  # type: ignore[override]
        raise NotImplementedError("_FakeProviderAdapter.call should not be reached")


def _make_fake_resolver(trusted: bool = False) -> object:
    """Return a duck-typed ProviderResolver that yields a fixed TurnProviderBinding.

    ``trusted=True`` → all eligible routes have ``trusted_for_safety_skip=True``
    (safety may be skipped by ``CapabilityProfileAwareSafetyPolicy``).
    ``trusted=False`` (default) → routes are not trusted; safety always runs.
    """
    route = EligibleModelRoute(
        provider_name="fake-anthropic",
        model_identifier="fake-anthropic:claude-test",
        whitelist_status=(
            SafetyWhitelistStatus.WHITELISTED
            if trusted
            else SafetyWhitelistStatus.NOT_WHITELISTED
        ),
        supports_required_capabilities=trusted,
    )
    adapter = _FakeProviderAdapter()
    binding = TurnProviderBinding(
        adapter=adapter,
        primary_writer_route=route,
        eligible_writer_routes=(route,),
        access_path=RuntimeAccessPath.HOSTED,
    )

    class _Resolver:
        def resolve_for_turn(self, access_path: object, sojourner_id: object) -> object:
            return binding

    return _Resolver()


# ---------------------------------------------------------------------------
# Orchestrator factory
# ---------------------------------------------------------------------------


def _null_branching_resolver(_story_id: UUID) -> None:
    """Default branching-session resolver for mode-agnostic orchestrator tests.

    The harness mode defaults to ``StoryMode.BRANCHING``, which now requires a
    wired ``branching_session_resolver`` (a missing resolver fails closed).
    These generic pipeline tests carry no branching session, so resolution
    yields ``None`` and the turn routes through the prose Writer exactly as it
    did under the prior fail-open behavior.
    """
    return None


def _make_orchestrator(  # type: ignore[no-untyped-def]
    session_factory,
    *,
    intent: IntentType = IntentType.IN_CHARACTER_ACTION,
    intent_error: bool = False,
    intent_exc: Exception | None = None,
    safety_input: SafetyResult | Exception | None = None,
    safety_output: SafetyResult | Exception | None = None,
    safety_policy: CapabilityProfileAwareSafetyPolicy | None = None,
    trusted_routes: bool = False,
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
    resolver = _make_fake_resolver(trusted=trusted_routes)
    orch = OrchestratorService(
        intent_classifier=classifier,
        context_builder=ctx_builder,
        safety_service=safety,
        planner_service=planner,
        writer_service=writer,
        extractor_service=extractor,
        contradiction_service=contradiction,
        session_factory=session_factory,
        safety_policy=safety_policy or CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=resolver,  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(),
        branching_session_resolver=_null_branching_resolver,
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
    )


def _allow_safety(target: SafetyTarget) -> SafetyResult:
    return SafetyResult(report=SafetyReport(concerns=[]), target=target)


# ---------------------------------------------------------------------------
# Disposition matrix
# ---------------------------------------------------------------------------


class TestDispositionDelivered:
    def test_happy_path_returns_delivered(self, session_factory, seeded_story) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(session_factory)
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "[OOC] Help?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.OOC_HANDLED
        assert result.delivered_output
        assert result.turn_id is not None
        assert planner.calls == []
        assert extractor.calls == []
        assert contradiction.calls == []
        assert writer.calls and writer.calls[0][
            0
        ].stable_prefix.system_prompt.startswith("# Branching Mode OOC Handler")


class TestDispositionBlockedInputSafety:
    def test_input_block_short_circuits(self, session_factory, seeded_story) -> None:
        story_id, node_id = seeded_story
        orch, _, _, _, planner, writer, extractor, contradiction = _make_orchestrator(
            session_factory,
            safety_input=_block_safety(SafetyTarget.INPUT),
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "harmful?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Tell me a joke.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.BLOCKED_CONTRADICTION
        assert result.disposition is not PipelineDisposition.PIPELINE_ERROR

    def test_refusal_never_becomes_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory, writer_exc=make_refusal(PassIdentifier.WRITER)
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert result.disposition is not PipelineDisposition.PIPELINE_ERROR

    def test_fallback_call_error_becomes_refused_not_pipeline_error(
        self, session_factory, seeded_story
    ) -> None:
        """P2 #1 taxonomy guard: fallback ProviderCallError → REFUSED_BY_PROVIDER.

        After the P2 #1 fix, RefusalFallbackRouter._handle_refusal re-raises
        primary_refusal (ProviderRefusalError) instead of the fallback's
        ProviderCallError when the fallback has an operational failure.  The
        router-level proof is in test_adapters.py; this test verifies the
        orchestrator maps that ProviderRefusalError to REFUSED_BY_PROVIDER.
        """
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            writer_exc=make_refusal(PassIdentifier.WRITER),
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert result.disposition is not PipelineDisposition.PIPELINE_ERROR

    def test_safety_pass_error_never_becomes_refused(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory, safety_input=SafetyPassError("nope")
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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

        def plan_recorded(ctx: AssembledContext, **kwargs):
            events.append("planner")
            return original_plan(ctx, **kwargs)

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

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        orch.orchestrate_turn(
            story_id, node_id, "[OOC] What is HP?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert len(writer.calls) == 1
        derived_ctx = writer.calls[0][0]
        assert derived_ctx.stable_prefix.system_prompt.startswith(
            "# Branching Mode OOC Handler"
        )

    def test_ooc_persists_turn_with_ooc_intent(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(session_factory, intent=IntentType.OOC)
        result = orch.orchestrate_turn(
            story_id, node_id, "[OOC] Hello?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        orch.orchestrate_turn(
            story_id, node_id, "[OOC] ?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        orch.orchestrate_turn(
            story_id, node_id, "[OOC] ?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "[OOC] ?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.BLOCKED_INPUT_SAFETY
        assert writer.calls == []

    def test_rpg_ooc_uses_rpg_handler_prompt(
        self, session_factory, seeded_story
    ) -> None:
        """RPG mode OOC turns must use rpg_ooc_handler.md, not the generic fallback."""
        story_id, node_id = seeded_story
        writer = FakeWriterService()
        orch = OrchestratorService(
            intent_classifier=FakeIntentClassifier(make_intent(IntentType.OOC)),
            context_builder=FakeContextBuilder(),
            safety_service=FakeSafetyService(),
            planner_service=FakePlannerService(),
            writer_service=writer,
            extractor_service=FakeExtractorService(),
            contradiction_service=FakeContradictionService(),
            session_factory=session_factory,
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
            mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        )
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What is my AC?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert len(writer.calls) == 1
        derived_ctx = writer.calls[0][0]
        assert derived_ctx.stable_prefix.system_prompt.startswith("# RPG OOC Handler")

    def test_branching_ooc_uses_branching_handler_prompt(
        self, session_factory, seeded_story
    ) -> None:
        """Branching mode OOC turns use the branching-specific ooc handler."""
        story_id, node_id = seeded_story
        orch, *_, writer, _, _ = _make_orchestrator(
            session_factory, intent=IntentType.OOC
        )
        orch.orchestrate_turn(
            story_id, node_id, "[OOC] What is HP?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert len(writer.calls) == 1
        derived_ctx = writer.calls[0][0]
        assert derived_ctx.stable_prefix.system_prompt.startswith(
            "# Branching Mode OOC Handler"
        )


# ---------------------------------------------------------------------------
# Branching OOC config persistence strategy (Round 3 Fix 2)
# ---------------------------------------------------------------------------


from dataclasses import dataclass as _dataclass  # noqa: E402


@_dataclass
class _FakeBranchingOocExtractor:
    """Returns a fixed BranchingOocConfigExtractorResult; never calls the provider."""

    config_update: object

    def extract(self, ctx: object, provider: object) -> object:
        from afterworlds.pipeline.branching.models import (
            BranchingOocConfigExtractorResult,
        )

        return BranchingOocConfigExtractorResult(
            config_update=self.config_update,  # type: ignore[arg-type]
            provider="fake",
            model_identifier="fake-haiku",
            model_tier="haiku",
            latency_ms=5,
            input_token_count=10,
            output_token_count=5,
        )


@_dataclass
class _TurnCapturingOocExtractor:
    """Records the turn_id on the ScopedProviderAdapter handed to extract().

    Returns an all-None config update so the best-effort persistence path is a
    no-op; the test only asserts on the provider scope.
    """

    captured_turn_id: object = None
    called: bool = False

    def extract(self, ctx: object, provider: object) -> object:
        from afterworlds.pipeline.branching.models import (
            BranchingConfigUpdate,
            BranchingOocConfigExtractorResult,
        )

        self.called = True
        self.captured_turn_id = getattr(provider, "_turn_id", "MISSING")
        return BranchingOocConfigExtractorResult(
            config_update=BranchingConfigUpdate(),
            provider="fake",
            model_identifier="fake-haiku",
            model_tier="haiku",
            latency_ms=5,
            input_token_count=10,
            output_token_count=5,
        )


def _make_ooc_cfg_orch(
    session_factory: object, config_update: object
) -> OrchestratorService:
    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent(IntentType.OOC)),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(),
        branching_ooc_config_extractor=_FakeBranchingOocExtractor(  # type: ignore[arg-type]
            config_update
        ),
    )


class TestBranchingOocConfigPersistence:
    """Round 3 Fix 2: style-only OOC transitions respect persisted range compat."""

    def _seed_bss(
        self,
        session: object,
        story_id: UUID,
        *,
        interaction_style: object,
        branch_count_range: object = None,
    ) -> None:
        from afterworlds.models.enums import PacingStage
        from afterworlds.models.session import BranchingSessionState
        from afterworlds.persistence.crud.session_state import (
            create_branching_session_state,
        )

        bss = BranchingSessionState(
            story_id=story_id,
            pacing_stage=PacingStage.SETUP,
            interaction_style=interaction_style,  # type: ignore[arg-type]
            branch_count_range=branch_count_range,  # type: ignore[arg-type]
        )
        create_branching_session_state(session, bss)  # type: ignore[arg-type]
        session.commit()  # type: ignore[union-attr]

    def _read_bss(self, session: object, story_id: UUID) -> object:
        from afterworlds.persistence.crud.session_state import (
            get_branching_session_state_by_story,
        )

        session.expire_all()  # type: ignore[union-attr]
        return get_branching_session_state_by_story(session, story_id)  # type: ignore[arg-type]

    def test_hybrid_2_3_to_true_cyoa_no_range_persists_style_and_keeps_range(
        self, session_factory, seeded_story, session
    ) -> None:
        """HYBRID 2-3 → TRUE_CYOA (no range): style changes to TRUE_CYOA, 2-3 kept."""
        from afterworlds.models.enums import BranchCountRange, InteractionStyle
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        story_id, node_id = seeded_story
        self._seed_bss(
            session,
            story_id,
            interaction_style=InteractionStyle.HYBRID,
            branch_count_range=BranchCountRange.TWO_TO_THREE,
        )

        orch = _make_ooc_cfg_orch(
            session_factory,
            BranchingConfigUpdate(interaction_style=InteractionStyle.TRUE_CYOA),
        )
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Switch to true CYOA",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        bss = self._read_bss(session, story_id)
        assert bss is not None
        assert bss.interaction_style is InteractionStyle.TRUE_CYOA
        assert bss.branch_count_range is BranchCountRange.TWO_TO_THREE

    def test_hybrid_3_4_to_true_cyoa_no_range_suppresses_style_change(
        self, session_factory, seeded_story, session
    ) -> None:
        """HYBRID 3-4 → TRUE_CYOA (no range): suppressed — 3-4 invalid for TRUE_CYOA."""
        from afterworlds.models.enums import BranchCountRange, InteractionStyle
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        story_id, node_id = seeded_story
        self._seed_bss(
            session,
            story_id,
            interaction_style=InteractionStyle.HYBRID,
            branch_count_range=BranchCountRange.THREE_TO_FOUR,
        )

        orch = _make_ooc_cfg_orch(
            session_factory,
            BranchingConfigUpdate(interaction_style=InteractionStyle.TRUE_CYOA),
        )
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Switch to true CYOA",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        bss = self._read_bss(session, story_id)
        assert bss is not None
        assert bss.interaction_style is InteractionStyle.HYBRID
        assert bss.branch_count_range is BranchCountRange.THREE_TO_FOUR

    def test_explicit_invalid_range_suppresses_style_does_not_fallback_to_persisted(
        self, session_factory, seeded_story, session
    ) -> None:
        """Explicit invalid range: suppress style; no fallback to persisted range."""
        from afterworlds.models.enums import BranchCountRange, InteractionStyle
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        story_id, node_id = seeded_story
        self._seed_bss(
            session,
            story_id,
            interaction_style=InteractionStyle.HYBRID,
            branch_count_range=BranchCountRange.TWO_TO_THREE,
        )

        orch = _make_ooc_cfg_orch(
            session_factory,
            BranchingConfigUpdate(
                interaction_style=InteractionStyle.TRUE_CYOA,
                branch_count_range=BranchCountRange.THREE_TO_FOUR,
            ),
        )
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Switch to CYOA with 3-4",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        bss = self._read_bss(session, story_id)
        assert bss is not None
        assert bss.interaction_style is InteractionStyle.HYBRID
        assert bss.branch_count_range is BranchCountRange.TWO_TO_THREE

    def test_freeform_only_clears_range_unchanged(
        self, session_factory, seeded_story, session
    ) -> None:
        """FREEFORM_ONLY: persists style and clears branch count range."""
        from afterworlds.models.enums import BranchCountRange, InteractionStyle
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        story_id, node_id = seeded_story
        self._seed_bss(
            session,
            story_id,
            interaction_style=InteractionStyle.HYBRID,
            branch_count_range=BranchCountRange.TWO_TO_THREE,
        )

        orch = _make_ooc_cfg_orch(
            session_factory,
            BranchingConfigUpdate(interaction_style=InteractionStyle.FREEFORM_ONLY),
        )
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Switch to freeform",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        bss = self._read_bss(session, story_id)
        assert bss is not None
        assert bss.interaction_style is InteractionStyle.FREEFORM_ONLY
        assert bss.branch_count_range is None

    def test_explicit_valid_range_persists_style_and_range(
        self, session_factory, seeded_story, session
    ) -> None:
        """Explicit valid range for target style: persists both style and range."""
        from afterworlds.models.enums import BranchCountRange, InteractionStyle
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        story_id, node_id = seeded_story
        self._seed_bss(
            session,
            story_id,
            interaction_style=InteractionStyle.HYBRID,
            branch_count_range=None,
        )

        orch = _make_ooc_cfg_orch(
            session_factory,
            BranchingConfigUpdate(
                interaction_style=InteractionStyle.TRUE_CYOA,
                branch_count_range=BranchCountRange.TWO_TO_FOUR,
            ),
        )
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Switch to CYOA with 2-4",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        bss = self._read_bss(session, story_id)
        assert bss is not None
        assert bss.interaction_style is InteractionStyle.TRUE_CYOA
        assert bss.branch_count_range is BranchCountRange.TWO_TO_FOUR

    def test_config_extractor_provider_scoped_to_ooc_writer_turn(
        self, session_factory, seeded_story, session
    ) -> None:
        """Round 6 Fix 2: the extractor's provider call is scoped to
        writer_result.turn_id so any refusal/fallback/provider-call audit row
        is reconstructable from the OOC turn (not an unscoped None)."""
        from afterworlds.models.enums import BranchCountRange, InteractionStyle

        story_id, node_id = seeded_story
        self._seed_bss(
            session,
            story_id,
            interaction_style=InteractionStyle.HYBRID,
            branch_count_range=BranchCountRange.TWO_TO_THREE,
        )

        extractor = _TurnCapturingOocExtractor()
        orch = OrchestratorService(
            intent_classifier=FakeIntentClassifier(make_intent(IntentType.OOC)),
            context_builder=FakeContextBuilder(),
            safety_service=FakeSafetyService(),
            planner_service=FakePlannerService(),
            writer_service=FakeWriterService(),
            extractor_service=FakeExtractorService(),
            contradiction_service=FakeContradictionService(),
            session_factory=session_factory,  # type: ignore[arg-type]
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
            mode_resolver=fixed_mode_resolver(),
            branching_ooc_config_extractor=extractor,  # type: ignore[arg-type]
        )
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] no config change",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert extractor.called
        # The scoped turn id must be the OOC writer's persisted turn — proving
        # turn_id=writer_result.turn_id flowed into the ScopedProviderAdapter.
        assert extractor.captured_turn_id not in (None, "MISSING")
        assert session.get(TurnORM, str(extractor.captured_turn_id)) is not None


# ---------------------------------------------------------------------------
# RPG OOC state grounding (Round 5 Fix 3)
# ---------------------------------------------------------------------------

_NOW_RPG = datetime(2026, 1, 1, tzinfo=UTC)


def _make_rpg_session_state(story_id: UUID) -> RpgSessionState:
    return RpgSessionState(
        story_id=story_id,
        character_sheet_id=uuid4(),
        dice_handling=DiceHandling.PLAYER_ROLLS,
        play_status=RpgPlayStatus.IN_PLAY,
        setup_phase=RpgSetupPhase.COMPLETE,
        gm_cheating=False,
        tone=RpgTone.BALANCED,
        session_type=RpgSessionType.OPEN_ENDED,
    )


def _make_rpg_sheet(story_id: UUID) -> Dnd5eCharacterSheet:
    return Dnd5eCharacterSheet(
        story_id=story_id,
        rules_package_id="dnd5e-v1",
        character_name="Aldric",
        created_at=_NOW_RPG,
        updated_at=_NOW_RPG,
        character_class="fighter",
        background="soldier",
        level=3,
        ability_scores=Dnd5eAbilityScores(
            strength=16,
            dexterity=12,
            constitution=14,
            intelligence=10,
            wisdom=11,
            charisma=9,
        ),
        skills={},
        current_hp=25,
        maximum_hp=28,
    )


class _FakeVisibleStateService:
    """Returns a canned RpgVisibleState for testing."""

    def build(self, sheet: Dnd5eCharacterSheet) -> RpgVisibleState:
        return RpgVisibleState(
            character=VisibleCharacterState(
                character_name=sheet.character_name,
                character_class=sheet.character_class,
                level=sheet.level,
                current_hp=sheet.current_hp,
                maximum_hp=sheet.maximum_hp,
                active_conditions=(),
            ),
            inventory=(),
            location=None,
            relationship_meters=(),
            known_objectives=(),
        )


class _FakePendingRollService:
    def __init__(self, pending: PendingRollRequest | None = None) -> None:
        self._pending = pending

    def load_pending_for_story(self, story_id: UUID) -> PendingRollRequest | None:
        return self._pending


def _make_rpg_ooc_orchestrator(
    session_factory,
    *,
    pending: PendingRollRequest | None = None,
    wire_resolver: bool = True,
):
    """Build an OrchestratorService wired for RPG OOC state tests."""
    writer = FakeWriterService()
    story_holder: dict[str, UUID] = {}

    def resolver(story_id: UUID):
        story_holder["id"] = story_id
        return _make_rpg_session_state(story_id), _make_rpg_sheet(story_id)

    orch = OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent(IntentType.OOC)),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=writer,
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        rpg_session_sheet_resolver=resolver if wire_resolver else None,
        rpg_visible_state_service=_FakeVisibleStateService(),  # type: ignore[arg-type]
        rpg_pending_roll_service=_FakePendingRollService(pending),  # type: ignore[arg-type]
    )
    return orch, writer


class TestRpgOocStateGrounding:
    def test_rpg_ooc_ledger_contains_state_entry(
        self, session_factory, seeded_story
    ) -> None:
        """RPG OOC Writer call must receive rpg_ooc_state in the pass-forward ledger."""
        story_id, node_id = seeded_story
        orch, writer = _make_rpg_ooc_orchestrator(session_factory)
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What is my AC?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert len(writer.calls) == 1
        ledger = writer.calls[0][0].pass_forward_ledger
        names = [e.pass_name for e in ledger.entries]
        assert "rpg_ooc_state" in names

    def test_rpg_ooc_state_contains_session_fields(
        self, session_factory, seeded_story
    ) -> None:
        """rpg_ooc_state payload must include session config fields."""
        story_id, node_id = seeded_story
        orch, writer = _make_rpg_ooc_orchestrator(session_factory)
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What is my AC?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        ledger = writer.calls[0][0].pass_forward_ledger
        content = next(
            e.content for e in ledger.entries if e.pass_name == "rpg_ooc_state"
        )
        assert "play_status" in content
        assert "dice_handling" in content
        assert "gm_cheating" in content
        assert "tone" in content

    def test_rpg_ooc_state_contains_character_fields(
        self, session_factory, seeded_story
    ) -> None:
        """rpg_ooc_state payload must include character name, class, level, and hp."""
        story_id, node_id = seeded_story
        orch, writer = _make_rpg_ooc_orchestrator(session_factory)
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What is my AC?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        ledger = writer.calls[0][0].pass_forward_ledger
        content = next(
            e.content for e in ledger.entries if e.pass_name == "rpg_ooc_state"
        )
        assert "Aldric" in content
        assert "fighter" in content
        assert "3" in content
        assert "25" in content
        assert "28" in content

    def test_rpg_ooc_with_pending_roll_includes_summary(
        self, session_factory, seeded_story
    ) -> None:
        """Pending roll check_label and instruction must appear in rpg_ooc_state."""
        from afterworlds.models.enums import RollVisibility

        story_id, node_id = seeded_story
        pending = PendingRollRequest(
            request_id=uuid4(),
            story_id=story_id,
            session_id=uuid4(),
            character_id=uuid4(),
            check_label="Stealth check",
            player_facing_instruction="Roll 1d20",
            expected_value_shape="integer",
            visibility=RollVisibility.PLAYER,
            source_proposal_ref="skill_check/Stealth check",
            originating_turn_id=uuid4(),
            created_at=_NOW_RPG,
            roll_expression="1d20",
        )
        orch, writer = _make_rpg_ooc_orchestrator(session_factory, pending=pending)
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What roll do I need?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        ledger = writer.calls[0][0].pass_forward_ledger
        content = next(
            e.content for e in ledger.entries if e.pass_name == "rpg_ooc_state"
        )
        assert "Stealth check" in content
        assert "Roll 1d20" in content

    def test_rpg_ooc_pending_roll_not_consumed(
        self, session_factory, seeded_story
    ) -> None:
        """OOC path must not call mark_consumed — pending roll status is unchanged."""
        from afterworlds.models.enums import RollVisibility

        story_id, node_id = seeded_story
        pending = PendingRollRequest(
            request_id=uuid4(),
            story_id=story_id,
            session_id=uuid4(),
            character_id=uuid4(),
            check_label="Perception check",
            player_facing_instruction="Roll 1d20 +3",
            expected_value_shape="integer",
            visibility=RollVisibility.PLAYER,
            source_proposal_ref="skill_check/Perception check",
            originating_turn_id=uuid4(),
            created_at=_NOW_RPG,
            roll_expression="1d20",
            visible_modifier_total=3,
        )
        pending_svc = _FakePendingRollService(pending)
        # Attach a mark_consumed spy — OOC must NOT call it.
        consumed_calls: list[object] = []
        pending_svc.mark_consumed = lambda *a, **kw: consumed_calls.append(a)  # type: ignore[attr-defined]

        writer = FakeWriterService()
        orch = OrchestratorService(
            intent_classifier=FakeIntentClassifier(make_intent(IntentType.OOC)),
            context_builder=FakeContextBuilder(),
            safety_service=FakeSafetyService(),
            planner_service=FakePlannerService(),
            writer_service=writer,
            extractor_service=FakeExtractorService(),
            contradiction_service=FakeContradictionService(),
            session_factory=session_factory,
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
            mode_resolver=fixed_mode_resolver(StoryMode.RPG),
            rpg_session_sheet_resolver=lambda sid: (
                _make_rpg_session_state(sid),
                _make_rpg_sheet(sid),
            ),
            rpg_visible_state_service=_FakeVisibleStateService(),  # type: ignore[arg-type]
            rpg_pending_roll_service=pending_svc,  # type: ignore[arg-type]
        )
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What roll do I need?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert consumed_calls == []

    def test_non_rpg_ooc_has_no_rpg_state_in_ledger(
        self, session_factory, seeded_story
    ) -> None:
        """Non-RPG OOC must not inject rpg_ooc_state into the ledger."""
        story_id, node_id = seeded_story
        writer = FakeWriterService()
        orch = OrchestratorService(
            intent_classifier=FakeIntentClassifier(make_intent(IntentType.OOC)),
            context_builder=FakeContextBuilder(),
            safety_service=FakeSafetyService(),
            planner_service=FakePlannerService(),
            writer_service=writer,
            extractor_service=FakeExtractorService(),
            contradiction_service=FakeContradictionService(),
            session_factory=session_factory,
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
            mode_resolver=fixed_mode_resolver(StoryMode.BRANCHING),
            rpg_session_sheet_resolver=lambda sid: (
                _make_rpg_session_state(sid),
                _make_rpg_sheet(sid),
            ),
            rpg_visible_state_service=_FakeVisibleStateService(),  # type: ignore[arg-type]
        )
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] How does HP work?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        ledger = writer.calls[0][0].pass_forward_ledger
        names = [e.pass_name for e in ledger.entries]
        assert "rpg_ooc_state" not in names

    def test_rpg_ooc_resolver_not_wired_degrades_gracefully(
        self, session_factory, seeded_story
    ) -> None:
        """When resolver is None, OOC succeeds with no rpg_ooc_state in ledger."""
        story_id, node_id = seeded_story
        orch, writer = _make_rpg_ooc_orchestrator(session_factory, wire_resolver=False)
        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What is my AC?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert result.disposition is PipelineDisposition.OOC_HANDLED
        ledger = writer.calls[0][0].pass_forward_ledger
        names = [e.pass_name for e in ledger.entries]
        assert "rpg_ooc_state" not in names

    def test_rpg_ooc_planner_and_extractor_not_called(
        self, session_factory, seeded_story
    ) -> None:
        """OOC short-circuit must not invoke Planner, Extractor, or Contradiction."""
        story_id, node_id = seeded_story
        orch, writer = _make_rpg_ooc_orchestrator(session_factory)
        # Retrieve the internal fake services via the _make_orchestrator approach
        # by re-building with access to extractor/planner.
        planner = FakePlannerService()
        extractor = FakeExtractorService()
        orch2 = OrchestratorService(
            intent_classifier=FakeIntentClassifier(make_intent(IntentType.OOC)),
            context_builder=FakeContextBuilder(),
            safety_service=FakeSafetyService(),
            planner_service=planner,
            writer_service=writer,
            extractor_service=extractor,
            contradiction_service=FakeContradictionService(),
            session_factory=session_factory,
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
            mode_resolver=fixed_mode_resolver(StoryMode.RPG),
            rpg_session_sheet_resolver=lambda sid: (
                _make_rpg_session_state(sid),
                _make_rpg_sheet(sid),
            ),
            rpg_visible_state_service=_FakeVisibleStateService(),  # type: ignore[arg-type]
        )
        orch2.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What is my AC?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert planner.calls == []
        assert extractor.calls == []

    def test_rpg_ooc_pending_roll_visible_modifier_note_included(
        self, session_factory, seeded_story
    ) -> None:
        """visible_modifier_note included in rpg_ooc_state when pending roll has one."""
        from afterworlds.models.enums import RollVisibility

        story_id, node_id = seeded_story
        pending = PendingRollRequest(
            request_id=uuid4(),
            story_id=story_id,
            session_id=uuid4(),
            character_id=uuid4(),
            check_label="Stealth check",
            player_facing_instruction="Roll 1d20 +5",
            expected_value_shape="integer",
            visibility=RollVisibility.PLAYER,
            source_proposal_ref="skill_check/Stealth check",
            originating_turn_id=uuid4(),
            created_at=_NOW_RPG,
            roll_expression="1d20",
            visible_modifier_note="+5",
            visible_modifier_total=5,
        )
        orch, writer = _make_rpg_ooc_orchestrator(session_factory, pending=pending)
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What modifier applies?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        ledger = writer.calls[0][0].pass_forward_ledger
        content = next(
            e.content for e in ledger.entries if e.pass_name == "rpg_ooc_state"
        )
        assert "+5" in content

    def test_rpg_ooc_hidden_condition_excluded_from_state(
        self, session_factory, seeded_story
    ) -> None:
        """Hidden condition excluded; visible condition present in rpg_ooc_state."""
        from afterworlds.models.character_sheet import Dnd5eActiveCondition
        from afterworlds.models.enums import ConditionVisibility
        from afterworlds.pipeline.rpg.visible_state import RpgVisibleStateService

        story_id, node_id = seeded_story
        sheet_id = uuid4()
        visible_cond = Dnd5eActiveCondition(
            sheet_id=sheet_id,
            identifier="blessed",
            display_label="Blessed",
            source="spell",
            visibility=ConditionVisibility.VISIBLE,
        )
        hidden_cond = Dnd5eActiveCondition(
            sheet_id=sheet_id,
            identifier="poisoned_secret",
            display_label="Poisoned",
            source="trap",
            visibility=ConditionVisibility.HIDDEN,
        )
        writer = FakeWriterService()

        def resolver(sid):
            sheet = _make_rpg_sheet(sid).model_copy(
                update={"active_conditions": [visible_cond, hidden_cond]}
            )
            return _make_rpg_session_state(sid), sheet

        orch = OrchestratorService(
            intent_classifier=FakeIntentClassifier(make_intent(IntentType.OOC)),
            context_builder=FakeContextBuilder(),
            safety_service=FakeSafetyService(),
            planner_service=FakePlannerService(),
            writer_service=writer,
            extractor_service=FakeExtractorService(),
            contradiction_service=FakeContradictionService(),
            session_factory=session_factory,
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
            mode_resolver=fixed_mode_resolver(StoryMode.RPG),
            rpg_session_sheet_resolver=resolver,
            rpg_visible_state_service=RpgVisibleStateService(),  # type: ignore[arg-type]
        )
        orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What conditions affect me?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        ledger = writer.calls[0][0].pass_forward_ledger
        content = next(
            e.content for e in ledger.entries if e.pass_name == "rpg_ooc_state"
        )
        assert "Blessed" in content
        assert "Poisoned" not in content


# ---------------------------------------------------------------------------
# Safety policy invocation
# ---------------------------------------------------------------------------


class TestSafetyPolicyInvocation:
    def test_trusted_routes_skip_both_safety_calls(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        # trusted_routes=True → all eligible routes are Anthropic-direct →
        # CapabilityProfileAwareSafetyPolicy._can_skip returns True.
        orch, _, _, safety, *_ = _make_orchestrator(
            session_factory, trusted_routes=True
        )
        result = orch.orchestrate_turn(
            story_id, node_id, "I act.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert result.disposition is PipelineDisposition.DELIVERED
        assert safety.calls == []
        assert result.input_safety_result is None
        assert result.output_safety_result is None

    def test_request_risk_signal_forces_input_preflight(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        # trusted_routes=True but request_risk_signal overrides the skip.
        orch, _, _, safety, *_ = _make_orchestrator(
            session_factory, trusted_routes=True
        )
        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I act.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            request_risk_signal=True,
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
        orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
        orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
            orch.orchestrate_turn(
                story_id,
                node_id,
                "I open the door.",
                _SOJOURNER,
                RuntimeAccessPath.HOSTED,
            )
            assert orch._owned_executor is executor_before
            orch.orchestrate_turn(
                story_id,
                node_id,
                "I close the door.",
                _SOJOURNER,
                RuntimeAccessPath.HOSTED,
            )
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
                result = orch.orchestrate_turn(
                    story_id,
                    node_id,
                    "I open the door.",
                    _SOJOURNER,
                    RuntimeAccessPath.HOSTED,
                )
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
                result = orch.orchestrate_turn(
                    story_id,
                    node_id,
                    "I open the door.",
                    _SOJOURNER,
                    RuntimeAccessPath.HOSTED,
                )
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
            result = orch.orchestrate_turn(
                story_id,
                node_id,
                "I open the door.",
                _SOJOURNER,
                RuntimeAccessPath.HOSTED,
            )

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
            orch.orchestrate_turn(
                story_id,
                node_id,
                "I open the door.",
                _SOJOURNER,
                RuntimeAccessPath.HOSTED,
            )
            # close() should be a no-op for the injected executor.
            orch.close()
            # Still alive — can submit and the future completes.
            fut = executor.submit(lambda: "still-alive")
            assert fut.result(timeout=2.0) == "still-alive"
            # And another orchestrate_turn after close still works
            # against the same injected executor.
            orch2, *_ = _make_orchestrator(session_factory, executor=executor)
            try:
                result = orch2.orchestrate_turn(
                    story_id,
                    node_id,
                    "another input.",
                    _SOJOURNER,
                    RuntimeAccessPath.HOSTED,
                )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
            result = orch.orchestrate_turn(
                story_id,
                node_id,
                "I open the door.",
                _SOJOURNER,
                RuntimeAccessPath.HOSTED,
            )
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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
            orch.orchestrate_turn(
                story_id,
                node_id,
                "I open the door.",
                _SOJOURNER,
                RuntimeAccessPath.HOSTED,
            )


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

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
            orch.orchestrate_turn(
                story_id,
                node_id,
                "I open the door.",
                _SOJOURNER,
                RuntimeAccessPath.HOSTED,
            )

    # -- Narrative Writer ----------------------------------------------

    def test_narrative_writer_unexpected_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            writer_exc=RuntimeError("writer blew up"),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
            orch.orchestrate_turn(
                story_id,
                node_id,
                "I open the door.",
                _SOJOURNER,
                RuntimeAccessPath.HOSTED,
            )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "[OOC] What is HP?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
            orch.orchestrate_turn(
                story_id,
                node_id,
                "[OOC] anything",
                _SOJOURNER,
                RuntimeAccessPath.HOSTED,
            )

    # -- Narrative Input Safety ----------------------------------------

    def test_narrative_input_safety_unexpected_runtime_error_routes_to_pipeline_error(
        self, session_factory, seeded_story, session
    ) -> None:
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            safety_input=RuntimeError("input safety blew up"),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "[OOC] foo", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "[OOC] foo", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
            orch.orchestrate_turn(
                story_id,
                node_id,
                "I open the door.",
                _SOJOURNER,
                RuntimeAccessPath.HOSTED,
            )


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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "Mira moves.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        orch_ooc.orchestrate_turn(
            story_id, node_id, "[OOC] First.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        orch, *_ = _make_orchestrator(session_factory)
        orch.orchestrate_turn(
            story_id, node_id, "I act.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
        from afterworlds.entitlement.enums import ModelTier, PipelinePassId
        from afterworlds.models.context import PassForwardLedger
        from afterworlds.pipeline.provider._models import (
            ProviderCallResult,
            ProviderTextPart,
        )
        from afterworlds.pipeline.writer.config import WriterConfig
        from afterworlds.pipeline.writer.service import WriterService

        story_id, node_id = seeded_story

        fake_result = ProviderCallResult(
            pass_id=PipelinePassId.WRITER,
            content_parts=[ProviderTextPart(text="hello")],
            input_token_count=10,
            output_token_count=2,
            cache_read_token_count=0,
            cache_creation_token_count=None,
            cache_warmed=False,
            provider_name="fake-anthropic",
            model_identifier="fake-anthropic:claude-test",
            model_tier=ModelTier.HAIKU,
            latency_ms=1,
        )

        class _FakeAdapter:
            provider_name = "fake-anthropic"

            def call(self, request: object) -> object:
                return fake_result

        config = WriterConfig(
            model="claude-fake", api_key_env="ANTHROPIC_API_KEY", extended_ttl=True
        )
        writer = WriterService(session=session, config=config)
        ctx = AssembledContext(
            stable_prefix=_stable_prefix_for(story_id),
            volatile_suffix=_volatile_for(make_intent()),
            pass_forward_ledger=PassForwardLedger(),
        )
        result = writer.write(ctx, story_id, node_id, provider=_FakeAdapter())  # type: ignore[arg-type]
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

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "[OOC] What is HP?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "[OOC] What is HP?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "[OOC] What is HP?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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
        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "[OOC] What is HP?", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

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

        result = orch.orchestrate_turn(
            story_id, node_id, "Mira moves.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
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
        from afterworlds.pipeline.writer.service import WriterService
        from tests.pipeline.orchestrator.conftest import make_assembled

        story_id = uuid4()
        ctx = make_assembled(story_id)
        expected = collect_stable_prefix_texts(ctx.stable_prefix)

        # All six services produce ProviderCallRequest; stable region is in
        # request.rendered_blocks up to and including the cache-breakpoint block.
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

        # _render() on each service returns ProviderCallRequest.
        planner_req = PlannerService(config=cfg_planner)._render(ctx)
        writer_req = WriterService(session=None, config=cfg_writer)._render(ctx)  # type: ignore[arg-type]
        safety_input_req = SafetyService(config=cfg_safety)._render(
            ctx, "raw input", SafetyTarget.INPUT
        )
        safety_output_req = SafetyService(config=cfg_safety)._render(
            ctx, "writer output", SafetyTarget.OUTPUT
        )
        extractor_req = ExtractorService(
            session=None,  # type: ignore[arg-type]
            story_bible_service=None,  # type: ignore[arg-type]
            config=cfg_extractor,
        )._render(ctx, "writer prose")
        contr_req = ContradictionService(config=cfg_contr)._render(
            _derive_context(ctx, "writer prose")
        )

        requests = {
            "planner": planner_req,
            "writer": writer_req,
            "safety_input": safety_input_req,
            "safety_output": safety_output_req,
            "extractor": extractor_req,
            "contradiction": contr_req,
        }
        slices = {
            name: _stable_slice_blocks(req.rendered_blocks)
            for name, req in requests.items()
        }

        # All six slices must be byte-identical to the canonical text list.
        for name, sl in slices.items():
            assert sl == expected, f"{name} stable region drifted: {sl} vs {expected}"

        # Cache breakpoint position is identical across all six.
        breakpoints = {
            name: _cache_breakpoint_idx(req.rendered_blocks)
            for name, req in requests.items()
        }
        assert len(set(breakpoints.values())) == 1, breakpoints


def _stable_slice_blocks(rendered_blocks: list) -> list[str]:
    """Return leading stable-region texts up to and including the breakpoint block."""
    out: list[str] = []
    for b in rendered_blocks:
        out.append(b.text)
        if b.has_cache_breakpoint:
            return out
    return out


def _cache_breakpoint_idx(rendered_blocks: list) -> int | None:
    for i, b in enumerate(rendered_blocks):
        if b.has_cache_breakpoint:
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
        assert [b.text for b in blocks_1h] == texts
        assert [b.text for b in blocks_5m] == texts
        assert blocks_1h[-1].ttl == "1h"
        assert blocks_5m[-1].ttl == "5m"


# ---------------------------------------------------------------------------
# BLOCKED_PENDING_ROLL disposition (CRD Issue 15 Phase 6)
# ---------------------------------------------------------------------------


def _make_pending_roll_request() -> PendingRollRequest:
    from datetime import UTC, datetime
    from uuid import uuid4

    from afterworlds.models.enums import RollVisibility
    from afterworlds.models.rpg import PendingRollRequest

    return PendingRollRequest(
        request_id=uuid4(),
        story_id=uuid4(),
        session_id=uuid4(),
        character_id=uuid4(),
        check_label="Stealth Check",
        player_facing_instruction="Roll a Stealth Check and report the total!",
        expected_value_shape="d20",
        visibility=RollVisibility.PLAYER,
        source_proposal_ref="roll_0",
        originating_turn_id=uuid4(),
        created_at=datetime.now(tz=UTC),
        roll_expression="1d20+5",
    )


class TestBlockedPendingRollDisposition:
    def test_valid_blocked_pending_roll(self) -> None:
        intent = make_intent()
        result = OrchestrationResult(
            disposition=PipelineDisposition.BLOCKED_PENDING_ROLL,
            delivered_output=None,
            turn_id=None,
            intent_classification=intent,
            pending_roll_redirect_message="Roll a Stealth Check and report the total!",
            total_latency_ms=5,
            pass_latency_breakdown={},
        )
        assert result.disposition is PipelineDisposition.BLOCKED_PENDING_ROLL
        assert result.pending_roll_redirect_message is not None

    def test_blocked_pending_roll_requires_redirect_message(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError, match="pending_roll_redirect_message"):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_PENDING_ROLL,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                pending_roll_redirect_message=None,  # missing
                total_latency_ms=5,
                pass_latency_breakdown={},
            )

    def test_blocked_pending_roll_forbids_planner_result(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError, match="planner_result"):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_PENDING_ROLL,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                pending_roll_redirect_message="Roll!",
                planner_result=_stub_planner_result(),  # forbidden
                total_latency_ms=5,
                pass_latency_breakdown={},
            )

    def test_blocked_pending_roll_forbids_provider_refusal(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_PENDING_ROLL,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                pending_roll_redirect_message="Roll!",
                provider_refusal=_stub_refusal(),  # forbidden
                total_latency_ms=5,
                pass_latency_breakdown={},
            )

    def test_blocked_pending_roll_forbids_pipeline_error_summary(self) -> None:
        intent = make_intent()
        with pytest.raises(OrchestratorError):
            OrchestrationResult(
                disposition=PipelineDisposition.BLOCKED_PENDING_ROLL,
                delivered_output=None,
                turn_id=None,
                intent_classification=intent,
                pending_roll_redirect_message="Roll!",
                pipeline_error_summary="ghost cause",  # forbidden
                total_latency_ms=5,
                pass_latency_breakdown={},
            )


# ---------------------------------------------------------------------------
# Pending-roll orchestrator intercept (CRD Issue 15 Phase 6)
# ---------------------------------------------------------------------------


class _FakePendingRollService:
    """Programmable fake for PendingRollRequestService."""

    def __init__(self, pending: object = None) -> None:
        self._pending = pending
        self.consumed: list[tuple[object, object]] = []
        self.checked: list[object] = []

    def load_pending_for_story(self, story_id: object) -> object:
        return self._pending

    def mark_consumed(
        self, session: object, request_id: object, consumed_turn_id: object
    ) -> None:
        self.consumed.append((request_id, consumed_turn_id))

    def check_no_pending_for_story(self, session: object, story_id: object) -> None:
        self.checked.append(story_id)


def _make_orchestrator_with_pending(
    session_factory: object,
    pending_roll_svc: object,
    *,
    mode_resolver: object | None = None,
    intent_type: IntentType = IntentType.IN_CHARACTER_ACTION,
) -> OrchestratorService:
    from afterworlds.models.enums import StoryMode
    from tests.pipeline.orchestrator.conftest import (  # noqa: E402
        FakeContextBuilder,
        FakeContradictionService,
        FakeExtractorService,
        FakeIntentClassifier,
        FakePlannerService,
        FakeSafetyService,
        FakeWriterService,
        fixed_mode_resolver,
        make_intent,
    )

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent(intent_type)),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=mode_resolver or fixed_mode_resolver(StoryMode.RPG),
        rpg_pending_roll_service=pending_roll_svc,  # type: ignore[arg-type]
    )


class TestPendingRollIntercept:
    def test_block_redirect_when_pending_exists_and_no_total(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        pending = _make_pending_roll_request()
        pending_svc = _FakePendingRollService(pending=pending)
        orch = _make_orchestrator_with_pending(session_factory, pending_svc)

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I sneak past the guard.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            # player_reported_total NOT supplied
        )

        assert result.disposition is PipelineDisposition.BLOCKED_PENDING_ROLL
        assert result.pending_roll_redirect_message == (
            pending.player_facing_instruction
        )
        assert result.delivered_output is None
        assert result.turn_id is None

    def test_no_block_when_no_pending_exists(
        self, session_factory, seeded_story
    ) -> None:
        story_id, node_id = seeded_story
        pending_svc = _FakePendingRollService(pending=None)
        orch = _make_orchestrator_with_pending(session_factory, pending_svc)

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I sneak past the guard.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        # No pending roll → normal narrative path → DELIVERED
        assert result.disposition is PipelineDisposition.DELIVERED

    def test_ooc_skips_pending_roll_check(self, session_factory, seeded_story) -> None:
        """OOC turns must not be blocked by a pending roll."""
        story_id, node_id = seeded_story
        pending = _make_pending_roll_request()
        pending_svc = _FakePendingRollService(pending=pending)
        orch = _make_orchestrator_with_pending(
            session_factory, pending_svc, intent_type=IntentType.OOC
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] What is my stealth modifier?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        # OOC short-circuit must proceed even with pending roll.
        assert result.disposition is PipelineDisposition.OOC_HANDLED
        assert result.pending_roll_redirect_message is None


# ---------------------------------------------------------------------------
# TestRpgVisibleState — CRD Issue 15 Phase 7
# ---------------------------------------------------------------------------
#
# Verify that rpg_visible_state is populated on a DELIVERED in-play RPG turn
# and is None when the service is not wired or adjudication does not run.


class _FakeRpgAdjudicationService:
    """Minimal fake for RpgAdjudicationPassService."""

    def __init__(self, adjudicable: bool = True) -> None:
        self.adjudicable = adjudicable

    def is_adjudicable(self, sheet: object) -> bool:
        return self.adjudicable

    def adjudicate(self, *args: object, **kwargs: object) -> object:
        from afterworlds.pipeline.rpg.models import AdjudicationPassResult

        return AdjudicationPassResult(proposals=(), writer_views=())


def _make_rpg_session_and_sheet() -> tuple[object, object]:
    """Return (RpgSessionState, Dnd5eCharacterSheet) for an in-play RPG turn."""
    from datetime import UTC, datetime
    from uuid import uuid4

    from afterworlds.models.character_sheet import (
        Dnd5eAbilityScores,
        Dnd5eCharacterSheet,
    )
    from afterworlds.models.enums import DiceHandling, RpgPlayStatus
    from afterworlds.models.session import RpgSessionState

    now = datetime(2026, 1, 1, tzinfo=UTC)
    story_id = uuid4()
    sheet = Dnd5eCharacterSheet(
        story_id=story_id,
        rules_package_id="dnd5e-v1",
        character_name="Aldric",
        character_class="Fighter",
        background="Soldier",
        level=3,
        ability_scores=Dnd5eAbilityScores(
            strength=16,
            dexterity=12,
            constitution=15,
            intelligence=10,
            wisdom=11,
            charisma=9,
        ),
        equipment=["Longsword", "Shield"],
        current_hp=28,
        maximum_hp=28,
        active_conditions=[],
        created_at=now,
        updated_at=now,
    )
    session_state = RpgSessionState(
        story_id=story_id,
        character_sheet_id=sheet.sheet_id,
        dice_handling=DiceHandling.AI_ROLLS,
        play_status=RpgPlayStatus.IN_PLAY,
    )
    return session_state, sheet


def _make_orchestrator_with_adjudication(
    session_factory: object,
    *,
    with_visible_state_service: bool = True,
    adjudicable: bool = True,
    play_status_setup: bool = False,
) -> OrchestratorService:
    from afterworlds.models.enums import DiceHandling, RpgPlayStatus, StoryMode

    session_state, sheet = _make_rpg_session_and_sheet()

    if play_status_setup:
        from afterworlds.models.session import RpgSessionState

        session_state = RpgSessionState(
            story_id=session_state.story_id,
            character_sheet_id=session_state.character_sheet_id,
            dice_handling=DiceHandling.AI_ROLLS,
            play_status=RpgPlayStatus.SETUP,
        )

    from afterworlds.pipeline.rpg.dice import SystemRandomDiceService
    from afterworlds.pipeline.rpg.visible_state import RpgVisibleStateService

    visible_svc = RpgVisibleStateService() if with_visible_state_service else None

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent()),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        rpg_adjudication_service=_FakeRpgAdjudicationService(adjudicable=adjudicable),  # type: ignore[arg-type]
        rpg_session_sheet_resolver=lambda _sid: (session_state, sheet),  # type: ignore[arg-type]
        rpg_dice_service=SystemRandomDiceService(seed=42),  # type: ignore[arg-type]
        rpg_visible_state_service=visible_svc,  # type: ignore[arg-type]
    )


class TestRpgVisibleState:
    def test_visible_state_populated_on_in_play_delivered_turn(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        story_id, node_id = seeded_story
        orch = _make_orchestrator_with_adjudication(session_factory)

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.rpg_visible_state is not None
        assert result.rpg_visible_state.character.character_name == "Aldric"
        assert result.rpg_visible_state.character.character_class == "Fighter"
        assert result.rpg_visible_state.character.current_hp == 28
        assert result.rpg_visible_state.character.active_conditions == ()
        assert len(result.rpg_visible_state.inventory) == 2  # noqa: PLR2004

    def test_visible_state_none_when_service_not_wired(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        story_id, node_id = seeded_story
        orch = _make_orchestrator_with_adjudication(
            session_factory, with_visible_state_service=False
        )

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.rpg_visible_state is None

    def test_visible_state_none_when_play_status_is_setup(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        story_id, node_id = seeded_story
        orch = _make_orchestrator_with_adjudication(
            session_factory, play_status_setup=True
        )

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I am setting up my character.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        # SETUP turns skip adjudication → visible state is not computed.
        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.rpg_visible_state is None


# ---------------------------------------------------------------------------
# TestRpgAuditErrorMapping — CRD Issue 15 remediation Fix 3
# ---------------------------------------------------------------------------
#
# _narrative_persist must map any non-PendingRollDuplicateError exception from
# _write_rpg_audit to PIPELINE_ERROR (the new except Exception branch).


class _FailingOnConsumePendingRollService:
    """Fake pending-roll service whose mark_consumed raises a given exception."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def load_pending_for_story(self, story_id: object) -> object:
        return _make_pending_roll_request()

    def mark_consumed(
        self, session: object, request_id: object, consumed_turn_id: object
    ) -> None:
        raise self._exc

    def check_no_pending_for_story(self, session: object, story_id: object) -> None:
        pass


def _make_orchestrator_for_audit_errors(
    session_factory: object,
    *,
    pending_svc: object,
) -> OrchestratorService:
    from afterworlds.models.enums import StoryMode
    from afterworlds.pipeline.rpg.dice import SystemRandomDiceService

    session_state, sheet = _make_rpg_session_and_sheet()

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent()),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        rpg_adjudication_service=_FakeRpgAdjudicationService(),  # type: ignore[arg-type]
        rpg_session_sheet_resolver=lambda _sid: (session_state, sheet),  # type: ignore[arg-type]
        rpg_dice_service=SystemRandomDiceService(seed=42),  # type: ignore[arg-type]
        rpg_pending_roll_service=pending_svc,  # type: ignore[arg-type]
    )


class TestRpgAuditErrorMapping:
    def test_already_consumed_error_maps_to_pipeline_error(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """PendingRollAlreadyConsumedError from mark_consumed → PIPELINE_ERROR."""
        from afterworlds.pipeline.rpg.pending import PendingRollAlreadyConsumedError

        story_id, node_id = seeded_story
        failing_svc = _FailingOnConsumePendingRollService(
            PendingRollAlreadyConsumedError("already consumed")
        )
        orch = _make_orchestrator_for_audit_errors(
            session_factory, pending_svc=failing_svc
        )

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            player_reported_total=15,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "rpg audit write failed" in result.pipeline_error_summary

    def test_general_audit_failure_maps_to_pipeline_error(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Any non-PendingRollDuplicateError from _write_rpg_audit → PIPELINE_ERROR."""
        story_id, node_id = seeded_story
        failing_svc = _FailingOnConsumePendingRollService(
            RuntimeError("synthetic db failure")
        )
        orch = _make_orchestrator_for_audit_errors(
            session_factory, pending_svc=failing_svc
        )

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            player_reported_total=15,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "rpg audit write failed" in result.pipeline_error_summary


# ---------------------------------------------------------------------------
# TestRpgPendingRollServiceGuard — CRD Issue 15 remediation Round 8 Fix 1
# ---------------------------------------------------------------------------


class _AdjServiceAnnouncingPending:
    """Fake adjudication service that always announces a new pending roll."""

    def is_adjudicable(self, sheet: object) -> bool:
        return True

    def adjudicate(self, *args: object, **kwargs: object) -> object:
        from afterworlds.pipeline.rpg.models import AdjudicationPassResult

        return AdjudicationPassResult(
            proposals=(),
            writer_views=(),
            pending_roll_request=_make_pending_roll_request(),
        )


def _make_rpg_orch_announcing_pending_no_svc(
    session_factory: object,
) -> OrchestratorService:
    """RPG orchestrator: adj announces a pending roll but no lifecycle service wired."""
    from afterworlds.models.enums import StoryMode
    from afterworlds.pipeline.rpg.dice import SystemRandomDiceService

    session_state, sheet = _make_rpg_session_and_sheet()

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent()),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        rpg_adjudication_service=_AdjServiceAnnouncingPending(),  # type: ignore[arg-type]
        rpg_session_sheet_resolver=lambda _sid: (session_state, sheet),  # type: ignore[arg-type]
        rpg_dice_service=SystemRandomDiceService(seed=42),  # type: ignore[arg-type]
        # rpg_pending_roll_service intentionally absent
    )


class TestRpgPendingRollServiceGuard:
    def test_pending_announce_without_service_is_pipeline_error(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Pending roll without service wired: PIPELINE_ERROR, no transaction opens."""
        story_id, node_id = seeded_story
        orch = _make_rpg_orch_announcing_pending_no_svc(session_factory)

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "pending-roll service not wired" in result.pipeline_error_summary

    def test_pending_announce_without_service_no_turn_written(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Guard fires pre-transaction: turn_id is None, writer_result is None."""
        story_id, node_id = seeded_story
        orch = _make_rpg_orch_announcing_pending_no_svc(session_factory)

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.turn_id is None
        assert result.writer_result is None

    def test_pending_announce_without_service_adj_result_preserved(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """PIPELINE_ERROR from the wiring guard must carry rpg_adjudication_result."""
        story_id, node_id = seeded_story
        orch = _make_rpg_orch_announcing_pending_no_svc(session_factory)

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.rpg_adjudication_result is not None

    def test_no_pending_request_path_unaffected_by_guard(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """AI_ROLLS with no pending_roll_request is unaffected by the guard."""
        story_id, node_id = seeded_story
        # _FakeRpgAdjudicationService returns AdjudicationPassResult with no pending.
        orch = _make_orchestrator_with_adjudication(session_factory)

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED


# ---------------------------------------------------------------------------
# TestRpgAdjResultPreservedDownstream — CRD Issue 15 remediation Round 8 Fix 2
# ---------------------------------------------------------------------------


def _make_rpg_adj_orch_downstream_failure(
    session_factory: object,
    *,
    writer_exc: Exception | None = None,
    safety_output: SafetyResult | Exception | None = None,
    contradiction_violations: list[ContradictionViolation] | None = None,
    extractor_exc: Exception | None = None,
) -> OrchestratorService:
    """RPG orchestrator with adjudication and a configurable downstream failure."""
    from afterworlds.models.enums import StoryMode
    from afterworlds.pipeline.rpg.dice import SystemRandomDiceService

    session_state, sheet = _make_rpg_session_and_sheet()

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent()),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(output_verdict=safety_output),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(raise_exc=writer_exc),
        extractor_service=FakeExtractorService(raise_exc=extractor_exc),
        contradiction_service=FakeContradictionService(
            violations=contradiction_violations
        ),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        rpg_adjudication_service=_FakeRpgAdjudicationService(),  # type: ignore[arg-type]
        rpg_session_sheet_resolver=lambda _sid: (session_state, sheet),  # type: ignore[arg-type]
        rpg_dice_service=SystemRandomDiceService(seed=42),  # type: ignore[arg-type]
    )


class TestRpgAdjResultPreservedDownstream:
    def test_writer_refusal_carries_adj_result(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Writer refusal after adjudication carries rpg_adjudication_result."""
        story_id, node_id = seeded_story
        orch = _make_rpg_adj_orch_downstream_failure(
            session_factory,
            writer_exc=make_refusal(PassIdentifier.WRITER),
        )

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert result.rpg_adjudication_result is not None

    def test_output_safety_block_carries_adj_result(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """BLOCKED_OUTPUT_SAFETY after adjudication carries rpg_adjudication_result."""
        story_id, node_id = seeded_story
        orch = _make_rpg_adj_orch_downstream_failure(
            session_factory,
            safety_output=_block_safety(SafetyTarget.OUTPUT),
        )

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.BLOCKED_OUTPUT_SAFETY
        assert result.rpg_adjudication_result is not None

    def test_contradiction_block_carries_adj_result(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """BLOCKED_CONTRADICTION after adjudication carries rpg_adjudication_result."""
        story_id, node_id = seeded_story
        orch = _make_rpg_adj_orch_downstream_failure(
            session_factory,
            contradiction_violations=[
                ContradictionViolation(
                    category=ContradictionCategory.LOCKED_FACT_VIOLATED,
                    description="synthetic conflict",
                    canon_reference="locked_fact_id=99",
                )
            ],
        )

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.BLOCKED_CONTRADICTION
        assert result.rpg_adjudication_result is not None

    def test_parallel_sync_failure_carries_adj_result(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Parallel-sync failure after adjudication carries rpg_adjudication_result."""
        story_id, node_id = seeded_story
        orch = _make_rpg_adj_orch_downstream_failure(
            session_factory,
            extractor_exc=RuntimeError("synthetic extractor failure"),
        )

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.rpg_adjudication_result is not None

    def test_audit_write_failure_carries_adj_result(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Audit write failure carries rpg_adjudication_result."""
        story_id, node_id = seeded_story
        failing_svc = _FailingOnConsumePendingRollService(
            RuntimeError("synthetic audit failure")
        )
        orch = _make_orchestrator_for_audit_errors(
            session_factory, pending_svc=failing_svc
        )

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            player_reported_total=15,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.rpg_adjudication_result is not None


# ---------------------------------------------------------------------------
# TestRpgVisibleStateBuildFailure — CRD Issue 15 remediation Round 8 Fix 3
# ---------------------------------------------------------------------------


class _FailingVisibleStateService:
    """Fake visible-state service that always raises on build()."""

    def build(self, sheet: object) -> object:
        raise RuntimeError("synthetic visible-state build failure")


def _make_rpg_orch_failing_visible_state(
    session_factory: object,
) -> OrchestratorService:
    """RPG orchestrator with adjudication and a visible-state service that raises."""
    from afterworlds.models.enums import StoryMode
    from afterworlds.pipeline.rpg.dice import SystemRandomDiceService

    session_state, sheet = _make_rpg_session_and_sheet()

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent()),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        rpg_adjudication_service=_FakeRpgAdjudicationService(),  # type: ignore[arg-type]
        rpg_session_sheet_resolver=lambda _sid: (session_state, sheet),  # type: ignore[arg-type]
        rpg_dice_service=SystemRandomDiceService(seed=42),  # type: ignore[arg-type]
        rpg_visible_state_service=_FailingVisibleStateService(),  # type: ignore[arg-type]
    )


class TestRpgVisibleStateBuildFailure:
    def test_visible_state_build_failure_returns_pipeline_error(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """visible-state build() raising returns PIPELINE_ERROR, not raw exception."""
        story_id, node_id = seeded_story
        orch = _make_rpg_orch_failing_visible_state(session_factory)

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.pipeline_error_summary is not None
        assert "visible state build failed" in result.pipeline_error_summary

    def test_visible_state_build_failure_no_turn_committed(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Transaction rolls back on visible-state failure: turn_id is None."""
        story_id, node_id = seeded_story
        orch = _make_rpg_orch_failing_visible_state(session_factory)

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.turn_id is None

    def test_visible_state_build_failure_preserves_adj_result(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """PIPELINE_ERROR from visible-state failure carries rpg_adjudication_result."""
        story_id, node_id = seeded_story
        orch = _make_rpg_orch_failing_visible_state(session_factory)

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.rpg_adjudication_result is not None

    def test_visible_state_build_failure_preserves_writer_result(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """PIPELINE_ERROR from visible-state failure carries writer_result."""
        story_id, node_id = seeded_story
        orch = _make_rpg_orch_failing_visible_state(session_factory)

        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.writer_result is not None


# ---------------------------------------------------------------------------
# P3: RPG adjudication cache tokens reflected in stable_prefix_cache_warmed
# ---------------------------------------------------------------------------


class TestRpgAdjudicationCacheWarmed:
    """_build_result must pass rpg_adjudication_result to _any_cache_read."""

    def test_cache_warmed_when_only_adjudication_has_cache_tokens(
        self, session_factory: object
    ) -> None:
        from afterworlds.pipeline.rpg.models import AdjudicationPassResult

        orch = _make_orchestrator_with_adjudication(session_factory)
        adj_result = AdjudicationPassResult(
            proposals=(), writer_views=(), cache_read_token_count=5
        )
        result = orch._build_result(  # type: ignore[attr-defined]
            PipelineDisposition.PIPELINE_ERROR,
            make_intent(),
            {},
            0.0,
            pipeline_error_summary="test",
            rpg_adjudication_result=adj_result,
        )
        assert result.stable_prefix_cache_warmed is True

    def test_cache_not_warmed_when_adjudication_has_no_cache(
        self, session_factory: object
    ) -> None:
        from afterworlds.pipeline.rpg.models import AdjudicationPassResult

        orch = _make_orchestrator_with_adjudication(session_factory)
        adj_result = AdjudicationPassResult(
            proposals=(), writer_views=(), cache_read_token_count=None
        )
        result = orch._build_result(  # type: ignore[attr-defined]
            PipelineDisposition.PIPELINE_ERROR,
            make_intent(),
            {},
            0.0,
            pipeline_error_summary="test",
            rpg_adjudication_result=adj_result,
        )
        assert result.stable_prefix_cache_warmed is False


# ---------------------------------------------------------------------------
# P2-1: Pending-roll consume path takes precedence over OOC routing (Round 11)
# ---------------------------------------------------------------------------


class TestPendingRollPrecedenceOverOoc:
    """player_reported_total in RPG mode takes precedence over OOC short-circuit."""

    def test_ooc_intent_with_total_bypasses_ooc_routes_to_narrative(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """OOC intent + player_reported_total → narrative consume path, NOT OOC."""
        story_id, node_id = seeded_story
        pending = _make_pending_roll_request()
        pending_svc = _FakePendingRollService(pending=pending)
        orch = _make_orchestrator_for_consume_wiring(
            session_factory, pending_svc, intent_type=IntentType.OOC
        )
        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "[OOC] I rolled 15 for my stealth check.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            player_reported_total=15,
        )
        # P2-1: when player_reported_total is set the consume path must take
        # precedence — OOC_HANDLED would mean the fix is absent.
        assert result.disposition is PipelineDisposition.DELIVERED

    def test_ooc_intent_without_total_still_routes_to_ooc(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """OOC intent + no total + pending → OOC fires; pending roll not consumed."""
        story_id, node_id = seeded_story
        pending = _make_pending_roll_request()
        pending_svc = _FakePendingRollService(pending=pending)
        orch = _make_orchestrator_with_pending(
            session_factory, pending_svc, intent_type=IntentType.OOC
        )
        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "[OOC] What is my stealth modifier?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert result.disposition is PipelineDisposition.OOC_HANDLED

    def test_total_with_no_pending_roll_is_pipeline_error(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """player_reported_total set but no pending roll for story → PIPELINE_ERROR."""
        story_id, node_id = seeded_story
        pending_svc = _FakePendingRollService(pending=None)
        orch = _make_orchestrator_with_pending(session_factory, pending_svc)
        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I rolled a 15.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            player_reported_total=15,
        )
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "no pending roll" in (result.pipeline_error_summary or "").lower()

    def test_total_without_pending_roll_service_is_pipeline_error(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """player_reported_total set but service not wired → PIPELINE_ERROR."""
        story_id, node_id = seeded_story
        orch = _make_orchestrator_with_pending(
            session_factory,
            None,  # type: ignore[arg-type]
        )
        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I rolled a 15.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            player_reported_total=15,
        )
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "not wired" in (result.pipeline_error_summary or "").lower()


# ---------------------------------------------------------------------------
# P2 Round 12: consume-path service wiring guard
# ---------------------------------------------------------------------------


def _make_orchestrator_for_consume_wiring(
    session_factory: object,
    pending_roll_svc: object,
    *,
    wire_adjudication: bool = True,
    wire_session_resolver: bool = True,
    wire_dice: bool = True,
    intent_type: IntentType = IntentType.IN_CHARACTER_ACTION,
) -> OrchestratorService:
    from afterworlds.models.enums import StoryMode
    from afterworlds.pipeline.rpg.dice import SystemRandomDiceService
    from tests.pipeline.orchestrator.conftest import (  # noqa: E402
        FakeContextBuilder,
        FakeContradictionService,
        FakeExtractorService,
        FakeIntentClassifier,
        FakePlannerService,
        FakeSafetyService,
        FakeWriterService,
        fixed_mode_resolver,
        make_intent,
    )

    session_state, sheet = _make_rpg_session_and_sheet()

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(make_intent(intent_type)),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.RPG),
        rpg_adjudication_service=(
            _FakeRpgAdjudicationService() if wire_adjudication else None  # type: ignore[arg-type]
        ),
        rpg_session_sheet_resolver=(
            (lambda _sid: (session_state, sheet)) if wire_session_resolver else None  # type: ignore[arg-type]
        ),
        rpg_dice_service=(
            SystemRandomDiceService(seed=42) if wire_dice else None  # type: ignore[arg-type]
        ),
        rpg_pending_roll_service=pending_roll_svc,  # type: ignore[arg-type]
    )


class TestConsumePathServiceWiringGuard:
    """Consume-path services must all be wired when player_reported_total is set."""

    def test_consume_path_adjudication_missing_is_pipeline_error(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """adj=None, pending+total → PIPELINE_ERROR 'not fully wired'."""
        story_id, node_id = seeded_story
        pending = _make_pending_roll_request()
        pending_svc = _FakePendingRollService(pending=pending)
        orch = _make_orchestrator_for_consume_wiring(
            session_factory, pending_svc, wire_adjudication=False
        )
        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I rolled a 15.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            player_reported_total=15,
        )
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "not fully wired" in (result.pipeline_error_summary or "")
        assert pending_svc.consumed == []

    def test_consume_path_session_resolver_missing_is_pipeline_error(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """resolver=None, pending+total → PIPELINE_ERROR; intercepted before consume."""
        story_id, node_id = seeded_story
        pending = _make_pending_roll_request()
        pending_svc = _FakePendingRollService(pending=pending)
        orch = _make_orchestrator_for_consume_wiring(
            session_factory, pending_svc, wire_session_resolver=False
        )
        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I rolled a 15.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            player_reported_total=15,
        )
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "resolver" in (result.pipeline_error_summary or "")
        assert pending_svc.consumed == []

    def test_consume_path_dice_service_missing_is_pipeline_error(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """dice=None, pending+total → PIPELINE_ERROR 'not fully wired'."""
        story_id, node_id = seeded_story
        pending = _make_pending_roll_request()
        pending_svc = _FakePendingRollService(pending=pending)
        orch = _make_orchestrator_for_consume_wiring(
            session_factory, pending_svc, wire_dice=False
        )
        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I rolled a 15.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            player_reported_total=15,
        )
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "not fully wired" in (result.pipeline_error_summary or "")
        assert pending_svc.consumed == []

    def test_consume_path_all_services_wired_delivers(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """All wired + pending + total → DELIVERED; pending roll consumed."""
        story_id, node_id = seeded_story
        pending = _make_pending_roll_request()
        pending_svc = _FakePendingRollService(pending=pending)
        orch = _make_orchestrator_for_consume_wiring(session_factory, pending_svc)
        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I rolled a 15.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
            player_reported_total=15,
        )
        assert result.disposition is PipelineDisposition.DELIVERED
        assert pending_svc.consumed != []

    def test_ooc_no_total_pending_still_routes_to_ooc(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """OOC + no total + pending → OOC_HANDLED; wiring guard is not triggered."""
        story_id, node_id = seeded_story
        pending = _make_pending_roll_request()
        pending_svc = _FakePendingRollService(pending=pending)
        orch = _make_orchestrator_for_consume_wiring(
            session_factory,
            pending_svc,
            wire_adjudication=False,
            intent_type=IntentType.OOC,
        )
        result = orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "[OOC] What is my stealth modifier?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert result.disposition is PipelineDisposition.OOC_HANDLED


# ---------------------------------------------------------------------------
# P2-2: RuleSliceRequest built before context assembly (Round 11)
# ---------------------------------------------------------------------------


class _SpyContextBuilder:
    """Wraps FakeContextBuilder to capture rule_slice_request per assemble() call."""

    def __init__(self) -> None:
        self._inner = FakeContextBuilder()
        self.rule_slice_requests: list[object] = []

    def assemble(
        self,
        story_id: object,
        mode: object,
        current_input: object,
        classified_intent: object,
        rule_slice_request: object = None,
    ) -> object:
        self.rule_slice_requests.append(rule_slice_request)
        return self._inner.assemble(  # type: ignore[arg-type]
            story_id, mode, current_input, classified_intent, rule_slice_request
        )


class TestRuleSlicePreContext:
    """RuleSliceRequest is built before _build_context() for adjudicating RPG turns."""

    def _make_orch(
        self,
        session_factory: object,
        spy: _SpyContextBuilder,
        *,
        intent_type: IntentType = IntentType.IN_CHARACTER_ACTION,
        rules_package_id: str = "dnd5e-v1",
        mode: StoryMode = StoryMode.RPG,
        wire_adjudication: bool = True,
        play_status_setup: bool = False,
    ) -> OrchestratorService:
        from afterworlds.pipeline.rpg.dice import SystemRandomDiceService

        session_state, sheet = _make_rpg_session_and_sheet()
        sheet = sheet.model_copy(update={"rules_package_id": rules_package_id})
        if play_status_setup:
            from afterworlds.models.enums import DiceHandling, RpgPlayStatus
            from afterworlds.models.session import RpgSessionState

            session_state = RpgSessionState(
                story_id=session_state.story_id,  # type: ignore[attr-defined]
                character_sheet_id=session_state.character_sheet_id,  # type: ignore[attr-defined]
                dice_handling=DiceHandling.AI_ROLLS,
                play_status=RpgPlayStatus.SETUP,
            )
        return OrchestratorService(
            intent_classifier=FakeIntentClassifier(make_intent(intent_type)),
            context_builder=spy,  # type: ignore[arg-type]
            safety_service=FakeSafetyService(),
            planner_service=FakePlannerService(),
            writer_service=FakeWriterService(),
            extractor_service=FakeExtractorService(),
            contradiction_service=FakeContradictionService(),
            session_factory=session_factory,  # type: ignore[arg-type]
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
            mode_resolver=fixed_mode_resolver(mode),
            rpg_adjudication_service=(
                _FakeRpgAdjudicationService() if wire_adjudication else None  # type: ignore[arg-type]
            ),
            rpg_session_sheet_resolver=lambda _sid: (session_state, sheet),  # type: ignore[arg-type]
            rpg_dice_service=SystemRandomDiceService(seed=42),  # type: ignore[arg-type]
            rpg_visible_state_service=_FakeVisibleStateService(),  # type: ignore[arg-type]
        )

    def test_uuid_binding_passes_rule_slice_request_to_context(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Adjudicating intent + UUID rules_package_id → non-None RuleSliceRequest."""
        from uuid import UUID, uuid4

        from afterworlds.models.rules_package import RuleSliceRequest

        pkg_id = str(uuid4())
        story_id, node_id = seeded_story
        spy = _SpyContextBuilder()
        orch = self._make_orch(session_factory, spy, rules_package_id=pkg_id)
        orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert len(spy.rule_slice_requests) == 1
        rsr = spy.rule_slice_requests[0]
        assert rsr is not None
        assert isinstance(rsr, RuleSliceRequest)
        assert rsr.package_id == UUID(pkg_id)

    def test_slug_binding_omits_rule_slice_request(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Non-UUID slug binding → RuleSliceRequest is None (slug→UUID gap)."""
        story_id, node_id = seeded_story
        spy = _SpyContextBuilder()
        orch = self._make_orch(session_factory, spy, rules_package_id="dnd5e-v1")
        orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert len(spy.rule_slice_requests) == 1
        assert spy.rule_slice_requests[0] is None

    def test_ooc_intent_omits_rule_slice_request(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """OOC is not an adjudicating intent → no early resolution → None."""
        story_id, node_id = seeded_story
        spy = _SpyContextBuilder()
        # Wire pending-roll service so RPG OOC path can build state gracefully.
        pending_svc = _FakePendingRollService(pending=None)
        orch = _make_orchestrator_with_pending(
            session_factory,
            pending_svc,
            intent_type=IntentType.OOC,
        )
        # Replace the context_builder with our spy after construction so the
        # rest of the wiring comes from the helper.
        orch._context_builder = spy  # type: ignore[attr-defined]
        orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "[OOC] What level am I?",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert len(spy.rule_slice_requests) == 1
        assert spy.rule_slice_requests[0] is None

    def test_setup_turn_omits_rule_slice_request(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """RPG + adjudicating intent but play_status=SETUP → no rule slice."""
        from uuid import uuid4

        pkg_id = str(uuid4())
        story_id, node_id = seeded_story
        spy = _SpyContextBuilder()
        orch = self._make_orch(
            session_factory, spy, rules_package_id=pkg_id, play_status_setup=True
        )
        orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert len(spy.rule_slice_requests) == 1
        assert spy.rule_slice_requests[0] is None

    def test_non_rpg_mode_omits_rule_slice_request(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Non-RPG mode → rule-slice construction skipped entirely."""
        from uuid import uuid4

        story_id, node_id = seeded_story
        spy = _SpyContextBuilder()
        orch = self._make_orch(
            session_factory,
            spy,
            rules_package_id=str(uuid4()),
            mode=StoryMode.BRANCHING,
            wire_adjudication=False,
        )
        orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I choose option A.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert len(spy.rule_slice_requests) == 1
        assert spy.rule_slice_requests[0] is None

    def test_no_adjudication_service_omits_rule_slice_request(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """RPG + adjudicating intent but adjudication service absent → None."""
        from uuid import uuid4

        story_id, node_id = seeded_story
        spy = _SpyContextBuilder()
        orch = self._make_orch(
            session_factory,
            spy,
            rules_package_id=str(uuid4()),
            wire_adjudication=False,
        )
        orch.orchestrate_turn(
            story_id,  # type: ignore[arg-type]
            node_id,  # type: ignore[arg-type]
            "I attack the goblin.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )
        assert len(spy.rule_slice_requests) == 1
        assert spy.rule_slice_requests[0] is None


# ---------------------------------------------------------------------------
# Fix 4: Branching-writer lineage guard — cross-story node rejects before LLM call
# ---------------------------------------------------------------------------


class _FakeBranchingWriterService:
    """Stub branching writer that must NOT be called if the lineage guard fires."""

    def __init__(self) -> None:
        self.called = False

    def write(self, *args: object, **kwargs: object) -> object:  # type: ignore[override]
        self.called = True
        raise AssertionError(
            "BranchingWriterService.write() must not be reached when the"
            " lineage guard fires"
        )


class TestBranchingWriterLineageGuard:
    """_narrative_persist lineage guard rejects cross-story node before LLM call."""

    def test_cross_story_node_returns_pipeline_error(
        self,
        session_factory: object,
        session: object,
        seeded_story: tuple[UUID, UUID],
    ) -> None:
        """Using node_id from story B with story A's story_id → PIPELINE_ERROR."""
        from datetime import UTC, datetime

        from afterworlds.entitlement.enums import RuntimeAccessPath
        from afterworlds.models.enums import (
            BranchingCadence,
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
            PacingStage,
            StoryMode,
        )
        from afterworlds.models.node import (
            BranchingNodeMetadata,
            Node,
            NodeMetadata,
            StateDelta,
        )
        from afterworlds.models.session import BranchingSessionState
        from afterworlds.models.story import Arc, Chapter, Story
        from afterworlds.persistence.crud.node import create_node
        from afterworlds.persistence.crud.story import (
            create_arc,
            create_chapter,
            create_story,
        )

        # story_A is the seeded fixture story.
        story_a_id, _node_a_id = seeded_story

        # Seed a second story (story_B) with its own node.
        now = datetime(2026, 1, 1, tzinfo=UTC)
        story_b = Story(
            title="Story B (different story)",
            mode=StoryMode.BRANCHING,
            created_at=now,
            updated_at=now,
        )
        create_story(session, story_b)  # type: ignore[arg-type]
        arc_b = Arc(story_id=story_b.story_id, title="Arc B", order=0)
        create_arc(session, arc_b)  # type: ignore[arg-type]
        chap_b = Chapter(arc_id=arc_b.arc_id, title="Chapter B", order=0)
        create_chapter(session, chap_b)  # type: ignore[arg-type]
        node_b = Node(
            chapter_id=chap_b.chapter_id,
            content="",
            state_delta=StateDelta(),
            branching_logic=[],
            intent_type=IntentType.IN_CHARACTER_ACTION,
            metadata=NodeMetadata(timestamp=now),
            mode_metadata=BranchingNodeMetadata(),
        )
        create_node(session, node_b)  # type: ignore[arg-type]
        session.commit()  # type: ignore[union-attr]

        def _branching_resolver(sid: UUID) -> BranchingSessionState:
            return BranchingSessionState(
                story_id=sid,
                pacing_stage=PacingStage.ESCALATION,
                interaction_style=InteractionStyle.HYBRID,
                branching_cadence=BranchingCadence.BALANCED,
                play_status=BranchingPlayStatus.IN_PLAY,
            )

        fake_branching_writer = _FakeBranchingWriterService()

        orch = OrchestratorService(
            intent_classifier=FakeIntentClassifier(
                make_intent(IntentType.IN_CHARACTER_ACTION, "I cross the bridge.")
            ),
            context_builder=FakeContextBuilder(),
            safety_service=FakeSafetyService(),
            planner_service=FakePlannerService(),
            writer_service=FakeWriterService(),
            extractor_service=FakeExtractorService(),
            contradiction_service=FakeContradictionService(),
            session_factory=session_factory,  # type: ignore[arg-type]
            safety_policy=CapabilityProfileAwareSafetyPolicy(),
            provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
            mode_resolver=fixed_mode_resolver(StoryMode.BRANCHING),
            branching_writer_service=fake_branching_writer,  # type: ignore[arg-type]
            branching_session_resolver=_branching_resolver,
        )

        result = orch.orchestrate_turn(
            story_a_id,  # story A
            node_b.node_id,  # node belongs to story B — cross-story mismatch
            "I cross the bridge.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert fake_branching_writer.called is False


# ---------------------------------------------------------------------------
# Branch-card read path: operational fault vs invalid input (Round 4 Fix 1)
# ---------------------------------------------------------------------------


class _RecordingBranchingWriterService:
    """Records that write() was reached, then aborts with a sentinel error.

    Used to prove a *valid* opt_N selection proceeds past branch-selection
    validation into the branching writer pass (rather than being rejected),
    without standing up a full DELIVERED branching pipeline.
    """

    def __init__(self) -> None:
        self.called = False

    def write(self, *args: object, **kwargs: object) -> object:  # type: ignore[override]
        from afterworlds.pipeline.branching.models import BranchingPassError

        self.called = True
        raise BranchingPassError("sentinel-reached-branching-writer")


def _seed_branching_story_with_options(
    session: object,
    option_labels: list[str],
) -> tuple[UUID, UUID]:
    """Seed a BRANCHING story + node, optionally carrying presented options."""
    from datetime import UTC, datetime

    from afterworlds.models.enums import IntentType, StoryMode
    from afterworlds.models.node import (
        BranchingNodeMetadata,
        Node,
        NodeMetadata,
        PersistedBranchOption,
        StateDelta,
    )
    from afterworlds.models.story import Arc, Chapter, Story
    from afterworlds.persistence.crud.node import create_node
    from afterworlds.persistence.crud.story import (
        create_arc,
        create_chapter,
        create_story,
    )

    now = datetime(2026, 1, 1, tzinfo=UTC)
    story = Story(
        title="Branching read-path story",
        mode=StoryMode.BRANCHING,
        created_at=now,
        updated_at=now,
    )
    create_story(session, story)  # type: ignore[arg-type]
    arc = Arc(story_id=story.story_id, title="Arc", order=0)
    create_arc(session, arc)  # type: ignore[arg-type]
    chap = Chapter(arc_id=arc.arc_id, title="Chapter", order=0)
    create_chapter(session, chap)  # type: ignore[arg-type]
    options = [
        PersistedBranchOption(option_id=f"opt_{i + 1}", action_text=label)
        for i, label in enumerate(option_labels)
    ]
    node = Node(
        chapter_id=chap.chapter_id,
        content="",
        state_delta=StateDelta(),
        branching_logic=[],
        intent_type=IntentType.IN_CHARACTER_ACTION,
        metadata=NodeMetadata(timestamp=now),
        mode_metadata=BranchingNodeMetadata(branch_options=options),
    )
    create_node(session, node)  # type: ignore[arg-type]
    session.commit()  # type: ignore[union-attr]
    return story.story_id, node.node_id


def _make_branching_choice_orchestrator(
    session_factory: object,
    branching_writer: object,
    raw_input: str,
    interaction_style: object = None,
):  # type: ignore[no-untyped-def]
    """Orchestrator wired for an in-play BRANCH_CHOICE turn with selection validation.

    Defaults to HYBRID; pass ``interaction_style`` to exercise TRUE_CYOA routing.
    """
    from afterworlds.models.enums import (
        BranchingCadence,
        BranchingPlayStatus,
        IntentType,
        InteractionStyle,
        PacingStage,
        StoryMode,
    )
    from afterworlds.models.session import BranchingSessionState
    from afterworlds.pipeline.branching.selection import (
        BranchSelectionValidationService,
    )

    resolved_style = (
        InteractionStyle.HYBRID if interaction_style is None else interaction_style
    )

    def _branching_resolver(sid: UUID) -> BranchingSessionState:
        return BranchingSessionState(
            story_id=sid,
            pacing_stage=PacingStage.ESCALATION,
            interaction_style=resolved_style,  # type: ignore[arg-type]
            branching_cadence=BranchingCadence.BALANCED,
            play_status=BranchingPlayStatus.IN_PLAY,
        )

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(
            make_intent(IntentType.BRANCH_CHOICE, raw_input)
        ),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.BRANCHING),
        branching_writer_service=branching_writer,  # type: ignore[arg-type]
        branching_session_resolver=_branching_resolver,
        branching_selection_service=BranchSelectionValidationService(),
    )


class TestBranchCardReadPath:
    """BRANCH_CHOICE branch-card read: DB faults are PIPELINE_ERROR, not rejection."""

    def test_branch_card_read_failure_routes_to_pipeline_error(
        self,
        session_factory: object,
        session: object,
        monkeypatch,  # type: ignore[no-untyped-def]
    ) -> None:
        """A crud/session error reading presented options → PIPELINE_ERROR, no LLM."""
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        writer = _FakeBranchingWriterService()
        orch = _make_branching_choice_orchestrator(session_factory, writer, "opt_1")

        def _boom(*args: object, **kwargs: object) -> object:
            raise RuntimeError("synthetic branch-card read failure")

        monkeypatch.setattr("afterworlds.persistence.crud.node.get_node", _boom)

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "branch-card read failed" in summary, summary
        assert "synthetic branch-card read failure" in summary, summary
        # Operational fault is never reclassified as user-invalid input.
        assert result.interaction_rejection_reason is None
        # No LLM call on the failure path.
        assert writer.called is False

    def test_empty_presented_options_after_read_rejects(
        self,
        session_factory: object,
        session: object,
    ) -> None:
        """Successful read with no options → INVALID_BRANCH_SELECTION, no LLM."""
        from afterworlds.models.enums import InteractionRejectionReason

        story_id, node_id = _seed_branching_story_with_options(session, [])
        writer = _FakeBranchingWriterService()
        orch = _make_branching_choice_orchestrator(session_factory, writer, "opt_1")

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.INTERACTION_REJECTED
        assert (
            result.interaction_rejection_reason
            is InteractionRejectionReason.INVALID_BRANCH_SELECTION
        )
        # No LLM call on the rejection path.
        assert writer.called is False

    def test_valid_opt_n_proceeds_to_branching_writer(
        self,
        session_factory: object,
        session: object,
    ) -> None:
        """A valid opt_N selection passes validation and reaches the writer pass."""
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        writer = _RecordingBranchingWriterService()
        orch = _make_branching_choice_orchestrator(session_factory, writer, "opt_1")

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        # Not rejected: validation accepted and the narrative path was entered,
        # reaching the branching writer (which aborts with a sentinel error).
        assert writer.called is True
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "sentinel-reached-branching-writer" in (
            result.pipeline_error_summary or ""
        )
        assert result.interaction_rejection_reason is None

    def test_true_cyoa_in_play_valid_choice_proceeds_to_branching_writer(
        self,
        session_factory: object,
        session: object,
    ) -> None:
        """TRUE_CYOA + in_play + valid opt_N still routes to the branching writer.

        Finding 1 enumerates "HYBRID/TRUE_CYOA + in_play uses BranchingWriter".
        Under TRUE_CYOA the only path that reaches the writer is a valid
        BRANCH_CHOICE (freeform is rejected), so this exercises the selection
        harness rather than the freeform routing harness.
        """
        from afterworlds.models.enums import InteractionStyle

        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        writer = _RecordingBranchingWriterService()
        orch = _make_branching_choice_orchestrator(
            session_factory,
            writer,
            "opt_1",
            interaction_style=InteractionStyle.TRUE_CYOA,
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert writer.called is True
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "sentinel-reached-branching-writer" in (
            result.pipeline_error_summary or ""
        )
        assert result.interaction_rejection_reason is None


# ---------------------------------------------------------------------------
# Round 7 Finding 1: in_play gating of interaction-style enforcement.
#
# Branching interaction-style enforcement (TRUE_CYOA freeform rejection and
# HYBRID/TRUE_CYOA BranchingWriter routing) applies only when
# play_status == IN_PLAY.  During setup, confirmation/clarification routes
# through the ordinary prose Writer path per ADR-016 Decision 3.
# ---------------------------------------------------------------------------


class _SuccessfulBranchingWriterService:
    """Branching writer fake that returns a complete, valid pass result.

    Lets a HYBRID/TRUE_CYOA in-play turn proceed past the writer into the
    downstream Extractor/Contradiction passes (used by the refusal-preservation
    tests below).
    """

    def __init__(self) -> None:
        self.called = False

    def write(self, *args: object, **kwargs: object) -> object:  # type: ignore[override]
        from afterworlds.models.enums import BranchingCadence, InteractionStyle
        from afterworlds.pipeline.branching.models import (
            BranchingPassResult,
            BranchOption,
        )

        self.called = True
        return BranchingPassResult(
            narrative_text="The corridor forks before you.",
            interaction_style=InteractionStyle.HYBRID,
            branching_cadence=BranchingCadence.BALANCED,
            length_preference=None,
            freeform_available=True,
            branch_count_range=None,
            branch_options=[
                BranchOption(option_id="opt_1", action_text="Go left"),
                BranchOption(option_id="opt_2", action_text="Go right"),
            ],
            branch_presentation_state="shown",
            provider="anthropic",
            model_identifier="claude-haiku-4-5",
            model_tier="haiku",
            latency_ms=7,
        )


class _PresentationBranchingWriterService:
    """Branching writer fake returning a chosen presentation state + option set.

    Held/omitted beats always carry an empty option list (the branching
    validator forbids non-empty held/omitted), so the orchestrator's node
    metadata write must clear any prior beat's branch_options.
    """

    def __init__(
        self,
        presentation_state: str,
        *,
        options: list[tuple[str, str]] | None = None,
    ) -> None:
        self.called = False
        self._presentation_state = presentation_state
        self._options = options or []

    def write(self, *args: object, **kwargs: object) -> object:  # type: ignore[override]
        from afterworlds.models.enums import BranchingCadence, InteractionStyle
        from afterworlds.pipeline.branching.models import (
            BranchingPassResult,
            BranchOption,
        )

        self.called = True
        return BranchingPassResult(
            narrative_text="The corridor narrows; you hold your ground.",
            interaction_style=InteractionStyle.HYBRID,
            branching_cadence=BranchingCadence.BALANCED,
            length_preference=None,
            freeform_available=True,
            branch_count_range=None,
            branch_options=[
                BranchOption(option_id=oid, action_text=txt)
                for oid, txt in self._options
            ],
            branch_presentation_state=self._presentation_state,
            provider="anthropic",
            model_identifier="claude-haiku-4-5",
            model_tier="haiku",
            latency_ms=7,
        )


def _make_branching_routing_orchestrator(
    session_factory: object,
    *,
    interaction_style: object,
    play_status: object,
    intent_type: object,
    branching_writer: object,
    raw_input: str,
):  # type: ignore[no-untyped-def]
    """Orchestrator wired for a BRANCHING turn at a given style/play_status."""
    from afterworlds.models.enums import (
        BranchingCadence,
        PacingStage,
        StoryMode,
    )
    from afterworlds.models.session import BranchingSessionState

    def _branching_resolver(sid: UUID) -> BranchingSessionState:
        return BranchingSessionState(
            story_id=sid,
            pacing_stage=PacingStage.ESCALATION,
            interaction_style=interaction_style,  # type: ignore[arg-type]
            branching_cadence=BranchingCadence.BALANCED,
            play_status=play_status,  # type: ignore[arg-type]
        )

    return OrchestratorService(
        intent_classifier=FakeIntentClassifier(
            make_intent(intent_type, raw_input)  # type: ignore[arg-type]
        ),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.BRANCHING),
        branching_writer_service=branching_writer,  # type: ignore[arg-type]
        branching_session_resolver=_branching_resolver,
    )


class TestBranchingInPlayGating:
    """Interaction-style enforcement is gated on play_status == IN_PLAY."""

    def test_true_cyoa_setup_freeform_not_rejected(
        self, session_factory: object, session: object
    ) -> None:
        """TRUE_CYOA + setup + non-branch input → prose Writer, not rejected."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        writer = _FakeBranchingWriterService()  # must-not-call stub
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.TRUE_CYOA,
            play_status=BranchingPlayStatus.SETUP,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=writer,
            raw_input="Make the tone darker, please.",
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "Make the tone darker, please.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        # Setup clarification is NOT rejected and routes through prose Writer.
        assert result.disposition is not PipelineDisposition.INTERACTION_REJECTED
        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.interaction_rejection_reason is None
        assert writer.called is False

    def test_true_cyoa_in_play_freeform_rejected(
        self, session_factory: object, session: object
    ) -> None:
        """TRUE_CYOA + in_play + non-branch input → INTERACTION_REJECTED."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionRejectionReason,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        writer = _FakeBranchingWriterService()  # must-not-call stub
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.TRUE_CYOA,
            play_status=BranchingPlayStatus.IN_PLAY,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=writer,
            raw_input="I wander off the path on my own.",
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I wander off the path on my own.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.INTERACTION_REJECTED
        assert (
            result.interaction_rejection_reason
            is InteractionRejectionReason.INVALID_FOR_INTERACTION_STYLE
        )
        assert writer.called is False

    def test_hybrid_setup_uses_prose_writer(
        self, session_factory: object, session: object
    ) -> None:
        """HYBRID + setup → prose Writer, BranchingWriter not reached."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        writer = _FakeBranchingWriterService()  # must-not-call stub
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.HYBRID,
            play_status=BranchingPlayStatus.SETUP,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=writer,
            raw_input="Yes, that premise sounds right.",
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "Yes, that premise sounds right.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert writer.called is False

    def test_hybrid_in_play_uses_branching_writer(
        self, session_factory: object, session: object
    ) -> None:
        """HYBRID + in_play → BranchingWriter is reached."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        writer = _RecordingBranchingWriterService()  # records + aborts
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.HYBRID,
            play_status=BranchingPlayStatus.IN_PLAY,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=writer,
            raw_input="I push deeper into the corridor.",
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I push deeper into the corridor.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert writer.called is True
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR

    def test_freeform_only_in_play_unchanged_uses_prose_writer(
        self, session_factory: object, session: object
    ) -> None:
        """FREEFORM_ONLY + in_play → prose Writer (never BranchingWriter)."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        writer = _FakeBranchingWriterService()  # must-not-call stub
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.FREEFORM_ONLY,
            play_status=BranchingPlayStatus.IN_PLAY,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=writer,
            raw_input="I improvise and follow the sound.",
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I improvise and follow the sound.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.interaction_rejection_reason is None
        assert writer.called is False


# ---------------------------------------------------------------------------
# Round 7 Finding 2: preserve branching_pass_result on downstream refusal.
#
# After a successful BranchingWriter pass, a downstream provider refusal
# (Extractor refusal, or Contradiction refusal after Extractor succeeded)
# must preserve the upstream successful ``branching_pass_result``.  Only the
# failing downstream pass result remains absent.
# ---------------------------------------------------------------------------


def _make_branching_refusal_orchestrator(
    session_factory: object,
    *,
    extractor_exc: Exception | None = None,
    contradiction_exc: Exception | None = None,
    safety_output: object | None = None,
    contradiction_violations: object | None = None,
):  # type: ignore[no-untyped-def]
    """BRANCHING HYBRID in-play orchestrator with a successful BranchingWriter.

    ``safety_output`` and ``contradiction_violations`` let the same harness drive
    the downstream terminal paths (output-safety BLOCK, contradiction BLOCK)
    exercised by the Round 9 Finding 3 preservation tests.
    """
    from afterworlds.models.enums import (
        BranchingCadence,
        BranchingPlayStatus,
        IntentType,
        InteractionStyle,
        PacingStage,
        StoryMode,
    )
    from afterworlds.models.session import BranchingSessionState

    def _branching_resolver(sid: UUID) -> BranchingSessionState:
        return BranchingSessionState(
            story_id=sid,
            pacing_stage=PacingStage.ESCALATION,
            interaction_style=InteractionStyle.HYBRID,
            branching_cadence=BranchingCadence.BALANCED,
            play_status=BranchingPlayStatus.IN_PLAY,
        )

    branching_writer = _SuccessfulBranchingWriterService()
    orch = OrchestratorService(
        intent_classifier=FakeIntentClassifier(
            make_intent(IntentType.IN_CHARACTER_ACTION, "I push deeper.")
        ),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(output_verdict=safety_output),
        planner_service=FakePlannerService(),
        writer_service=FakeWriterService(),
        extractor_service=FakeExtractorService(raise_exc=extractor_exc),
        contradiction_service=FakeContradictionService(
            raise_exc=contradiction_exc,
            violations=contradiction_violations,  # type: ignore[arg-type]
        ),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.BRANCHING),
        branching_writer_service=branching_writer,  # type: ignore[arg-type]
        branching_session_resolver=_branching_resolver,
    )
    return orch, branching_writer


class TestBranchingPassResultPreservedOnRefusal:
    """Downstream refusals preserve the upstream branching_pass_result."""

    def test_extractor_refusal_preserves_branching_pass_result(
        self, session_factory: object, session: object
    ) -> None:
        """BranchingWriter success + Extractor refusal → result preserved."""
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Go left", "Go right"]
        )
        orch, branching_writer = _make_branching_refusal_orchestrator(
            session_factory,
            extractor_exc=make_refusal(PassIdentifier.EXTRACTOR),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert result.provider_refusal is not None
        assert result.provider_refusal.pass_identifier is PassIdentifier.EXTRACTOR
        assert branching_writer.called is True
        # Upstream success preserved …
        assert result.branching_pass_result is not None
        assert result.writer_result is not None
        # … failing downstream pass result remains absent.
        assert result.extractor_result is None

    def test_contradiction_refusal_preserves_branching_pass_result(
        self, session_factory: object, session: object
    ) -> None:
        """BranchingWriter + Extractor success + Contradiction refusal."""
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Go left", "Go right"]
        )
        orch, branching_writer = _make_branching_refusal_orchestrator(
            session_factory,
            contradiction_exc=make_refusal(PassIdentifier.CONTRADICTION),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        assert result.provider_refusal is not None
        assert result.provider_refusal.pass_identifier is PassIdentifier.CONTRADICTION
        assert branching_writer.called is True
        # Upstream successes preserved, including the Extractor that completed.
        assert result.branching_pass_result is not None
        assert result.extractor_result is not None
        # Failing pass (Contradiction) result absent.
        assert result.contradiction_result is None

    def test_prose_writer_refusal_leaves_branching_pass_result_none(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Prose-Writer path: Extractor refusal carries no branching_pass_result."""
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            extractor_exc=make_refusal(PassIdentifier.EXTRACTOR),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.REFUSED_BY_PROVIDER
        # No branching writer ran; the field stays None (behavior unchanged).
        assert result.branching_pass_result is None


# ---------------------------------------------------------------------------
# Round 8 Finding 1: branch-card persistence is fail-closed on shown turns.
#
# For HYBRID/TRUE_CYOA turns that DELIVER selectable branch cards, the option
# set persisted on the node is the authoritative source for later BRANCH_CHOICE
# validation.  If persistence fails on a shown turn the orchestrator must fail
# closed (PIPELINE_ERROR -> rollback) rather than deliver unbacked cards.  The
# Phase G selected-edge write stays best-effort.
# ---------------------------------------------------------------------------


class TestBranchCardPersistenceFailClosed:
    """Shown branch-card turns persist the authoritative option set or fail closed."""

    def test_hybrid_shown_turn_persists_options_before_delivery(
        self, session_factory: object, session: object
    ) -> None:
        """HYBRID + in_play DELIVER persists the shown option set on the node."""
        from afterworlds.models.node import BranchingNodeMetadata
        from afterworlds.persistence.crud.node import get_node

        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch, branching_writer = _make_branching_refusal_orchestrator(session_factory)

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert branching_writer.called is True
        with session_factory() as read_session:  # type: ignore[operator]
            node = get_node(read_session, node_id)
        assert node is not None
        assert isinstance(node.mode_metadata, BranchingNodeMetadata)
        assert [o.option_id for o in node.mode_metadata.branch_options] == [
            "opt_1",
            "opt_2",
        ]
        assert node.mode_metadata.branch_presentation_state == "shown"

    def test_true_cyoa_shown_turn_persists_options_before_delivery(
        self, session_factory: object, session: object
    ) -> None:
        """TRUE_CYOA + valid BRANCH_CHOICE DELIVER persists the shown option set."""
        from afterworlds.models.enums import InteractionStyle
        from afterworlds.models.node import BranchingNodeMetadata
        from afterworlds.persistence.crud.node import get_node

        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        writer = _SuccessfulBranchingWriterService()
        orch = _make_branching_choice_orchestrator(
            session_factory,
            writer,
            "opt_1",
            interaction_style=InteractionStyle.TRUE_CYOA,
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert writer.called is True
        with session_factory() as read_session:  # type: ignore[operator]
            node = get_node(read_session, node_id)
        assert node is not None
        assert isinstance(node.mode_metadata, BranchingNodeMetadata)
        assert [o.option_id for o in node.mode_metadata.branch_options] == [
            "opt_1",
            "opt_2",
        ]
        assert node.mode_metadata.branch_presentation_state == "shown"

    def test_shown_turn_persistence_failure_fails_closed(
        self,
        session_factory: object,
        session: object,
        monkeypatch,  # type: ignore[no-untyped-def]
    ) -> None:
        """A persistence fault on a shown turn → PIPELINE_ERROR, no delivered cards."""
        from afterworlds.models.node import BranchingNodeMetadata
        from afterworlds.persistence.crud.node import get_node

        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch, branching_writer = _make_branching_refusal_orchestrator(session_factory)

        def _boom(*args: object, **kwargs: object) -> object:
            raise RuntimeError("synthetic branch-option persistence failure")

        # The only update_node on a HYBRID freeform turn is the branch-card write.
        monkeypatch.setattr("afterworlds.persistence.crud.node.update_node", _boom)

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "branch-card metadata persistence failed" in summary, summary
        assert "synthetic branch-option persistence failure" in summary, summary
        # Owner decision (Round 9): branching_pass_result records that
        # BranchingWriter ran and consumed provider tokens — it is a
        # settlement/audit record, NOT the branch-card delivery signal.  It is
        # preserved on this fail-closed path; delivery is gated by the
        # PIPELINE_ERROR disposition plus the absence of deliverable state.
        assert result.branching_pass_result is not None
        # Failing closed means NOT surfacing selectable cards: no deliverable
        # branch-card visible state is built.
        assert result.branching_visible_state is None
        # Transaction rolled back: no option set committed to the node.
        with session_factory() as read_session:  # type: ignore[operator]
            node = get_node(read_session, node_id)
        assert node is not None
        assert isinstance(node.mode_metadata, BranchingNodeMetadata)
        assert node.mode_metadata.branch_options == []

    def test_shown_turn_missing_node_fails_closed(
        self,
        session_factory: object,
        session: object,
        monkeypatch,  # type: ignore[no-untyped-def]
    ) -> None:
        """A get_node miss on a shown turn → PIPELINE_ERROR, no delivered cards."""
        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch, _branching_writer = _make_branching_refusal_orchestrator(session_factory)

        # The branch-card persistence block re-fetches the node before writing;
        # a missing row must fail closed rather than deliver unpersisted cards.
        monkeypatch.setattr(
            "afterworlds.persistence.crud.node.get_node",
            lambda *args, **kwargs: None,
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "branch-card metadata persistence failed" in summary, summary
        # Owner decision (Round 9): preserve the settlement/audit record; gate
        # delivery on PIPELINE_ERROR + absence of deliverable branch-card state.
        assert result.branching_pass_result is not None
        assert result.branching_visible_state is None

    def test_persisted_option_set_drives_later_branch_choice(
        self, session_factory: object, session: object
    ) -> None:
        """A later BRANCH_CHOICE validates against the orchestrator-persisted set."""
        # Turn 1: HYBRID shown turn — seed carries NO options; the turn persists
        # opt_1/opt_2 onto the node.
        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch1, writer1 = _make_branching_refusal_orchestrator(session_factory)
        r1 = orch1.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )
        assert r1.disposition is PipelineDisposition.DELIVERED
        assert writer1.called is True

        # Turn 2: a valid opt_1 BRANCH_CHOICE reads the persisted set and proceeds.
        writer2 = _RecordingBranchingWriterService()
        orch2 = _make_branching_choice_orchestrator(session_factory, writer2, "opt_1")
        r2 = orch2.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        # The seed carried no options; only the persisted set makes opt_1 valid.
        assert writer2.called is True
        assert r2.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "sentinel-reached-branching-writer" in (r2.pipeline_error_summary or "")
        assert r2.interaction_rejection_reason is None

    def test_phase_g_selected_edge_failure_is_non_blocking(
        self,
        session_factory: object,
        session: object,
        monkeypatch,  # type: ignore[no-untyped-def]
    ) -> None:
        """Selected-edge persistence failure stays best-effort once cards persisted."""
        import afterworlds.persistence.crud.node as _node_crud
        from afterworlds.models.node import BranchingNodeMetadata

        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        writer = _SuccessfulBranchingWriterService()
        orch = _make_branching_choice_orchestrator(session_factory, writer, "opt_1")

        real_update = _node_crud.update_node
        calls = {"n": 0}

        def _fail_on_selected_edge(sess: object, node: object) -> object:
            # First update_node = branch-card persistence (must succeed); second =
            # Phase G selected-edge persistence (forced to fail, best-effort).
            calls["n"] += 1
            if calls["n"] >= 2:
                raise RuntimeError("synthetic selected-edge persistence failure")
            return real_update(sess, node)  # type: ignore[arg-type]

        monkeypatch.setattr(
            "afterworlds.persistence.crud.node.update_node", _fail_on_selected_edge
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        # Card persistence succeeded; the selected-edge failure does not block.
        assert result.disposition is PipelineDisposition.DELIVERED
        assert calls["n"] >= 2
        with session_factory() as read_session:  # type: ignore[operator]
            node = _node_crud.get_node(read_session, node_id)
        assert node is not None
        assert isinstance(node.mode_metadata, BranchingNodeMetadata)
        # Authoritative option set committed …
        assert [o.option_id for o in node.mode_metadata.branch_options] == [
            "opt_1",
            "opt_2",
        ]
        # … but the best-effort selection annotation was not.
        assert node.mode_metadata.selected_option_id is None


# ---------------------------------------------------------------------------
# Round 10 Finding 1: held/omitted node metadata is authoritative.
#
# A HYBRID held/omitted beat must clear any prior beat's branch_options and
# record the new presentation state in the same transaction that delivers the
# turn.  If that write fails the orchestrator fails closed (PIPELINE_ERROR ->
# rollback, branching_pass_result preserved) rather than continue best-effort,
# because leftover options would let the Sojourner select stale cards from a
# prior shown beat.  (TRUE_CYOA forbids held/omitted entirely, so this rule is
# exercised under HYBRID.)
# ---------------------------------------------------------------------------


class TestHeldOmittedBranchMetadataAuthoritative:
    """Held/omitted clears stale options; a failed clear fails closed."""

    def _make_held_omitted_orch(
        self,
        session_factory: object,
        writer: object,
        raw_input: str,
    ):  # type: ignore[no-untyped-def]
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        return _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.HYBRID,
            play_status=BranchingPlayStatus.IN_PLAY,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=writer,
            raw_input=raw_input,
        )

    def test_held_after_shown_clears_branch_options(
        self, session_factory: object, session: object
    ) -> None:
        """HYBRID held beat clears the prior shown beat's options, records held."""
        from afterworlds.models.node import BranchingNodeMetadata
        from afterworlds.persistence.crud.node import get_node

        # Prior beat left selectable cards on the node.
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        writer = _PresentationBranchingWriterService("held")
        orch = self._make_held_omitted_orch(
            session_factory, writer, "I hold my position."
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I hold my position.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert writer.called is True
        with session_factory() as read_session:  # type: ignore[operator]
            node = get_node(read_session, node_id)
        assert node is not None
        assert isinstance(node.mode_metadata, BranchingNodeMetadata)
        # Stale options cleared; new presentation state recorded.
        assert node.mode_metadata.branch_options == []
        assert node.mode_metadata.branch_presentation_state == "held"

    def test_omitted_after_shown_clears_branch_options(
        self, session_factory: object, session: object
    ) -> None:
        """HYBRID omitted beat clears the prior options and records omitted."""
        from afterworlds.models.node import BranchingNodeMetadata
        from afterworlds.persistence.crud.node import get_node

        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        writer = _PresentationBranchingWriterService("omitted")
        orch = self._make_held_omitted_orch(
            session_factory, writer, "I keep walking quietly."
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I keep walking quietly.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert writer.called is True
        with session_factory() as read_session:  # type: ignore[operator]
            node = get_node(read_session, node_id)
        assert node is not None
        assert isinstance(node.mode_metadata, BranchingNodeMetadata)
        assert node.mode_metadata.branch_options == []
        assert node.mode_metadata.branch_presentation_state == "omitted"

    def test_held_metadata_clear_failure_fails_closed(
        self,
        session_factory: object,
        session: object,
        monkeypatch,  # type: ignore[no-untyped-def]
    ) -> None:
        """A failed held-metadata clear → PIPELINE_ERROR, pass result preserved."""
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        writer = _PresentationBranchingWriterService("held")
        orch = self._make_held_omitted_orch(
            session_factory, writer, "I hold my position."
        )

        def _boom(*args: object, **kwargs: object) -> object:
            raise RuntimeError("synthetic held-metadata clear failure")

        # The only update_node on a HYBRID freeform held turn is the metadata
        # clear (no selected-edge write without a BRANCH_CHOICE selection).
        monkeypatch.setattr("afterworlds.persistence.crud.node.update_node", _boom)

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I hold my position.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        # Previously held/omitted persistence was best-effort; it now fails closed.
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "branch-card metadata persistence failed" in summary, summary
        assert "synthetic held-metadata clear failure" in summary, summary
        # BranchingWriter ran → settlement/audit record preserved (Round 9 rule).
        assert result.branching_pass_result is not None
        # No deliverable branch-card state on the failed turn.
        assert result.branching_visible_state is None
        # NOTE: the transaction rolls back, so the node still holds the prior
        # shown beat's options.  The invariant is "no DELIVERED turn where a
        # held state coexists with leftover selectable options" — enforced by
        # the PIPELINE_ERROR rollback above, not by post-failure erasure, so we
        # deliberately do not assert the prior options were removed.

    def test_omitted_metadata_clear_failure_fails_closed(
        self,
        session_factory: object,
        session: object,
        monkeypatch,  # type: ignore[no-untyped-def]
    ) -> None:
        """A failed omitted-metadata clear also fails closed, preserving the record."""
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        writer = _PresentationBranchingWriterService("omitted")
        orch = self._make_held_omitted_orch(
            session_factory, writer, "I keep walking quietly."
        )

        def _boom(*args: object, **kwargs: object) -> object:
            raise RuntimeError("synthetic omitted-metadata clear failure")

        monkeypatch.setattr("afterworlds.persistence.crud.node.update_node", _boom)

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I keep walking quietly.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "branch-card metadata persistence failed" in (
            result.pipeline_error_summary or ""
        )
        assert result.branching_pass_result is not None
        assert result.branching_visible_state is None


# ---------------------------------------------------------------------------
# Round 10 Finding 2: in-play HYBRID/TRUE_CYOA require BranchingWriterService.
#
# A wiring gap must fail closed (PIPELINE_ERROR), never silently downgrade to
# the prose Writer — that would bypass the typed branch-card contract and omit
# branching_pass_result.  Setup turns and FREEFORM_ONLY still use prose Writer
# per ADR-016 Decision 3.
# ---------------------------------------------------------------------------


class TestBranchingWriterRequiredWhenInPlay:
    """In-play HYBRID/TRUE_CYOA fail closed when BranchingWriterService is missing."""

    def test_in_play_hybrid_missing_writer_fails_closed(
        self, session_factory: object, session: object
    ) -> None:
        """In-play HYBRID without a branching writer → PIPELINE_ERROR, not prose."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.HYBRID,
            play_status=BranchingPlayStatus.IN_PLAY,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=None,
            raw_input="I push deeper.",
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "not wired" in summary, summary
        assert "prose-writer downgrade" in summary, summary
        # No branching writer ran → no settlement record (nothing to bill).
        assert result.branching_pass_result is None

    def test_in_play_true_cyoa_missing_writer_fails_closed(
        self, session_factory: object, session: object
    ) -> None:
        """In-play TRUE_CYOA (valid BRANCH_CHOICE) without a writer → PIPELINE_ERROR."""
        from afterworlds.models.enums import InteractionStyle

        # TRUE_CYOA only reaches the writer gate via a valid BRANCH_CHOICE.
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        orch = _make_branching_choice_orchestrator(
            session_factory,
            None,
            "opt_1",
            interaction_style=InteractionStyle.TRUE_CYOA,
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "not wired" in (result.pipeline_error_summary or "")
        # Fail-closed wiring guard, not a user-input rejection (selection passed).
        assert result.interaction_rejection_reason is None
        assert result.branching_pass_result is None

    def test_setup_hybrid_missing_writer_uses_prose(
        self, session_factory: object, session: object
    ) -> None:
        """Setup HYBRID without a branching writer still routes to prose Writer."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.HYBRID,
            play_status=BranchingPlayStatus.SETUP,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=None,
            raw_input="Yes, that premise sounds right.",
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "Yes, that premise sounds right.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.branching_pass_result is None

    def test_setup_true_cyoa_missing_writer_uses_prose(
        self, session_factory: object, session: object
    ) -> None:
        """Setup TRUE_CYOA freeform without a writer still routes to prose Writer."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.TRUE_CYOA,
            play_status=BranchingPlayStatus.SETUP,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=None,
            raw_input="Make the tone darker, please.",
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "Make the tone darker, please.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.branching_pass_result is None

    def test_freeform_only_in_play_missing_writer_uses_prose(
        self, session_factory: object, session: object
    ) -> None:
        """In-play FREEFORM_ONLY uses prose Writer regardless of branching wiring."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.FREEFORM_ONLY,
            play_status=BranchingPlayStatus.IN_PLAY,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=None,
            raw_input="I wander down the lane.",
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I wander down the lane.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.branching_pass_result is None

    def test_in_play_hybrid_wired_writer_emits_branching_pass_result(
        self, session_factory: object, session: object
    ) -> None:
        """Properly wired in-play HYBRID uses BranchingWriter and emits the record."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        writer = _SuccessfulBranchingWriterService()
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.HYBRID,
            play_status=BranchingPlayStatus.IN_PLAY,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=writer,
            raw_input="I push deeper.",
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert writer.called is True
        assert result.branching_pass_result is not None


# ---------------------------------------------------------------------------
# Round 9 Finding 1: BRANCH_CHOICE node/story lineage guard.
#
# Before reading a node's branch-card options for BRANCH_CHOICE validation, the
# node must be confirmed to belong to the current story.  A node from another
# story must never have its option labels passed to the selection validator or
# echoed in rejection text; a mismatch fails closed with a generic lineage
# PIPELINE_ERROR, NOT an INVALID_BRANCH_SELECTION carrying foreign labels.
#
# The complementary scenarios are already covered elsewhere:
# • valid same-story node still validates → TestBranchCardReadPath
#   .test_valid_opt_n_proceeds_to_branching_writer
# • same-story empty options → INVALID_BRANCH_SELECTION → TestBranchCardReadPath
#   .test_empty_presented_options_after_read_rejects
# • DB/session read failure → PIPELINE_ERROR → TestBranchCardReadPath
#   .test_branch_card_read_failure_routes_to_pipeline_error
# ---------------------------------------------------------------------------


class TestBranchChoiceLineageGuard:
    """A BRANCH_CHOICE node from another story fails closed before validation."""

    def test_foreign_story_node_does_not_expose_option_labels(
        self, session_factory: object, session: object
    ) -> None:
        """opt labels of a foreign-story node never reach validation or output."""
        # Story A is the caller's story; story B owns the node carrying the
        # distinctive option labels that must never leak.
        story_a_id, _node_a_id = _seed_branching_story_with_options(session, [])
        _story_b_id, node_b_id = _seed_branching_story_with_options(
            session, ["FOREIGNLABEL_BRIDGE", "FOREIGNLABEL_RIVER"]
        )
        writer = _FakeBranchingWriterService()  # must-not-call stub
        orch = _make_branching_choice_orchestrator(session_factory, writer, "opt_1")

        result = orch.orchestrate_turn(
            story_a_id, node_b_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        # Fails closed as a generic lineage PIPELINE_ERROR, not user-invalid.
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert result.interaction_rejection_reason is None
        assert result.interaction_rejection_message is None
        summary = result.pipeline_error_summary or ""
        assert "lineage" in summary, summary
        # The foreign option labels never surface anywhere in the result.
        assert "FOREIGNLABEL" not in summary, summary
        assert "FOREIGNLABEL" not in (result.delivered_output or "")
        # No LLM call on the lineage-failure path.
        assert writer.called is False

    def test_foreign_story_node_fails_before_validation(
        self, session_factory: object, session: object
    ) -> None:
        """A foreign-story node is rejected as lineage failure, never as input."""
        story_a_id, _node_a_id = _seed_branching_story_with_options(session, [])
        _story_b_id, node_b_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        writer = _FakeBranchingWriterService()  # must-not-call stub
        orch = _make_branching_choice_orchestrator(session_factory, writer, "opt_1")

        result = orch.orchestrate_turn(
            story_a_id, node_b_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        # The lineage check precedes selection validation entirely.
        assert result.disposition is not PipelineDisposition.INTERACTION_REJECTED
        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert writer.called is False


# ---------------------------------------------------------------------------
# Round 9 Finding 3: branching_pass_result preserved on downstream terminals.
#
# Owner decision: branching_pass_result is the settlement/audit record that
# BranchingWriter ran and consumed provider tokens — NOT the branch-card
# delivery signal.  Once BranchingWriter succeeds, every later terminal path
# (output-safety BLOCK, contradiction BLOCK, downstream pipeline error) must
# preserve it so the BRANCHING_WRITER pass is billed.  Prose-Writer turns carry
# no branching_pass_result, so those terminals stay unchanged.
# ---------------------------------------------------------------------------


class TestBranchingPassResultPreservedOnTerminals:
    """Post-BranchingWriter terminal paths preserve the settlement/audit record."""

    def test_output_safety_block_preserves_branching_pass_result(
        self, session_factory: object, session: object
    ) -> None:
        """BranchingWriter success + output-safety BLOCK → result preserved."""
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Go left", "Go right"]
        )
        orch, branching_writer = _make_branching_refusal_orchestrator(
            session_factory,
            safety_output=_block_safety(SafetyTarget.OUTPUT),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.BLOCKED_OUTPUT_SAFETY
        assert branching_writer.called is True
        assert result.branching_pass_result is not None

    def test_contradiction_block_preserves_branching_pass_result(
        self, session_factory: object, session: object
    ) -> None:
        """BranchingWriter + Extractor success + Contradiction BLOCK → preserved."""
        violations = [
            ContradictionViolation(
                category=ContradictionCategory.LOCKED_FACT_VIOLATED,
                description="locked fact violated",
                canon_reference="locked_fact_id=123",
            )
        ]
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Go left", "Go right"]
        )
        orch, branching_writer = _make_branching_refusal_orchestrator(
            session_factory,
            contradiction_violations=violations,
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.BLOCKED_CONTRADICTION
        assert branching_writer.called is True
        assert result.branching_pass_result is not None
        assert result.contradiction_result is not None

    def test_turn_persistence_failure_preserves_branching_pass_result(
        self,
        session_factory: object,
        session: object,
        monkeypatch,  # type: ignore[no-untyped-def]
    ) -> None:
        """BranchingWriter success + Turn-persistence fault → preserved record."""
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Go left", "Go right"]
        )
        orch, branching_writer = _make_branching_refusal_orchestrator(session_factory)

        def _boom(*args: object, **kwargs: object) -> object:
            raise RuntimeError("synthetic branching turn persistence failure")

        monkeypatch.setattr("afterworlds.persistence.crud.node.create_turn", _boom)

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "branching turn persistence failed" in summary, summary
        assert branching_writer.called is True
        # Settlement/audit record preserved even when the Turn could not persist.
        assert result.branching_pass_result is not None

    def test_downstream_pipeline_error_preserves_branching_pass_result(
        self, session_factory: object, session: object
    ) -> None:
        """BranchingWriter success + non-refusal downstream fault → preserved."""
        story_id, node_id = _seed_branching_story_with_options(
            session, ["Go left", "Go right"]
        )
        orch, branching_writer = _make_branching_refusal_orchestrator(
            session_factory,
            extractor_exc=RuntimeError("synthetic downstream extractor fault"),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I push deeper.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert branching_writer.called is True
        assert result.branching_pass_result is not None

    def test_prose_writer_output_block_leaves_branching_pass_result_none(
        self, session_factory: object, seeded_story: tuple[object, object]
    ) -> None:
        """Prose-Writer output BLOCK carries no branching_pass_result (unchanged)."""
        story_id, node_id = seeded_story
        orch, *_ = _make_orchestrator(
            session_factory,
            safety_output=_block_safety(SafetyTarget.OUTPUT),
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I open the door.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.BLOCKED_OUTPUT_SAFETY
        assert result.branching_pass_result is None


# ---------------------------------------------------------------------------
# Round 9 Finding 2: suppressed OOC style switch surfaces an explicit non-
# confirmation so the delivered prose cannot imply a change persistence did not
# make.  When a requested switch to HYBRID/TRUE_CYOA lacks a compatible branch
# range, the style is NOT persisted AND the delivered OOC output carries a
# visible "Interaction style not changed" note.  Valid switches that DO persist
# carry no such note.
# ---------------------------------------------------------------------------


def _seed_branching_session_state(
    session: object,
    story_id: UUID,
    *,
    interaction_style: object,
    branch_count_range: object = None,
) -> None:
    """Seed a BranchingSessionState row for OOC config no-op tests."""
    from afterworlds.models.enums import PacingStage
    from afterworlds.models.session import BranchingSessionState
    from afterworlds.persistence.crud.session_state import (
        create_branching_session_state,
    )

    bss = BranchingSessionState(
        story_id=story_id,
        pacing_stage=PacingStage.SETUP,
        interaction_style=interaction_style,  # type: ignore[arg-type]
        branch_count_range=branch_count_range,  # type: ignore[arg-type]
    )
    create_branching_session_state(session, bss)  # type: ignore[arg-type]
    session.commit()  # type: ignore[union-attr]


def _read_branching_session_state(session: object, story_id: UUID) -> object:
    from afterworlds.persistence.crud.session_state import (
        get_branching_session_state_by_story,
    )

    session.expire_all()  # type: ignore[union-attr]
    return get_branching_session_state_by_story(session, story_id)  # type: ignore[arg-type]


_OOC_STYLE_NOOP_SENTINEL = "Interaction style not changed"


class TestBranchingOocStyleNoopSurfaced:
    """A suppressed OOC style switch is surfaced, never silently confirmed."""

    def test_freeform_to_hybrid_no_range_surfaces_non_confirmation(
        self, session_factory, seeded_story, session
    ) -> None:
        """FREEFORM_ONLY → HYBRID (no range): not persisted, note surfaced."""
        from afterworlds.models.enums import InteractionStyle
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        story_id, node_id = seeded_story
        _seed_branching_session_state(
            session, story_id, interaction_style=InteractionStyle.FREEFORM_ONLY
        )

        orch = _make_ooc_cfg_orch(
            session_factory,
            BranchingConfigUpdate(interaction_style=InteractionStyle.HYBRID),
        )
        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Switch to hybrid",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        # Persistence unchanged …
        bss = _read_branching_session_state(session, story_id)
        assert bss is not None
        assert bss.interaction_style is InteractionStyle.FREEFORM_ONLY
        # … and the delivered prose surfaces the non-confirmation explicitly.
        assert _OOC_STYLE_NOOP_SENTINEL in (result.delivered_output or "")
        assert "hybrid" in (result.delivered_output or "")

    def test_freeform_to_true_cyoa_no_range_surfaces_non_confirmation(
        self, session_factory, seeded_story, session
    ) -> None:
        """FREEFORM_ONLY → TRUE_CYOA (no range): not persisted, note surfaced."""
        from afterworlds.models.enums import InteractionStyle
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        story_id, node_id = seeded_story
        _seed_branching_session_state(
            session, story_id, interaction_style=InteractionStyle.FREEFORM_ONLY
        )

        orch = _make_ooc_cfg_orch(
            session_factory,
            BranchingConfigUpdate(interaction_style=InteractionStyle.TRUE_CYOA),
        )
        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Switch to true CYOA",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        bss = _read_branching_session_state(session, story_id)
        assert bss is not None
        assert bss.interaction_style is InteractionStyle.FREEFORM_ONLY
        assert _OOC_STYLE_NOOP_SENTINEL in (result.delivered_output or "")
        assert "true_cyoa" in (result.delivered_output or "")

    def test_invalid_explicit_range_surfaces_non_confirmation(
        self, session_factory, seeded_story, session
    ) -> None:
        """HYBRID 2-3 → TRUE_CYOA + invalid 3-4: suppressed and surfaced."""
        from afterworlds.models.enums import BranchCountRange, InteractionStyle
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        story_id, node_id = seeded_story
        _seed_branching_session_state(
            session,
            story_id,
            interaction_style=InteractionStyle.HYBRID,
            branch_count_range=BranchCountRange.TWO_TO_THREE,
        )

        orch = _make_ooc_cfg_orch(
            session_factory,
            BranchingConfigUpdate(
                interaction_style=InteractionStyle.TRUE_CYOA,
                branch_count_range=BranchCountRange.THREE_TO_FOUR,
            ),
        )
        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Switch to CYOA with 3-4",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        bss = _read_branching_session_state(session, story_id)
        assert bss is not None
        assert bss.interaction_style is InteractionStyle.HYBRID
        assert bss.branch_count_range is BranchCountRange.TWO_TO_THREE
        assert _OOC_STYLE_NOOP_SENTINEL in (result.delivered_output or "")

    def test_valid_persisted_range_style_switch_carries_no_note(
        self, session_factory, seeded_story, session
    ) -> None:
        """HYBRID 2-3 → TRUE_CYOA (no range): persists, no non-confirmation note."""
        from afterworlds.models.enums import BranchCountRange, InteractionStyle
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        story_id, node_id = seeded_story
        _seed_branching_session_state(
            session,
            story_id,
            interaction_style=InteractionStyle.HYBRID,
            branch_count_range=BranchCountRange.TWO_TO_THREE,
        )

        orch = _make_ooc_cfg_orch(
            session_factory,
            BranchingConfigUpdate(interaction_style=InteractionStyle.TRUE_CYOA),
        )
        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Switch to true CYOA",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        bss = _read_branching_session_state(session, story_id)
        assert bss is not None
        assert bss.interaction_style is InteractionStyle.TRUE_CYOA
        assert bss.branch_count_range is BranchCountRange.TWO_TO_THREE
        assert _OOC_STYLE_NOOP_SENTINEL not in (result.delivered_output or "")

    def test_valid_explicit_style_and_range_carries_no_note(
        self, session_factory, seeded_story, session
    ) -> None:
        """HYBRID 2-3 → TRUE_CYOA + valid 2-4: persists both, no note."""
        from afterworlds.models.enums import BranchCountRange, InteractionStyle
        from afterworlds.pipeline.branching.models import BranchingConfigUpdate

        story_id, node_id = seeded_story
        _seed_branching_session_state(
            session,
            story_id,
            interaction_style=InteractionStyle.HYBRID,
            branch_count_range=BranchCountRange.TWO_TO_THREE,
        )

        orch = _make_ooc_cfg_orch(
            session_factory,
            BranchingConfigUpdate(
                interaction_style=InteractionStyle.TRUE_CYOA,
                branch_count_range=BranchCountRange.TWO_TO_FOUR,
            ),
        )
        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "[OOC] Switch to CYOA with 2-4",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        bss = _read_branching_session_state(session, story_id)
        assert bss is not None
        assert bss.interaction_style is InteractionStyle.TRUE_CYOA
        assert bss.branch_count_range is BranchCountRange.TWO_TO_FOUR
        assert _OOC_STYLE_NOOP_SENTINEL not in (result.delivered_output or "")


def _make_branching_orch_without_resolver(
    session_factory: object,
    *,
    intent_type: object,
    raw_input: str,
):  # type: ignore[no-untyped-def]
    """BRANCHING orchestrator with NO branching_session_resolver wired.

    Exposes the prose writer and branching writer fakes so callers can prove
    neither pass ran when the missing-resolver guard fails closed.
    """
    from afterworlds.models.enums import StoryMode
    from afterworlds.pipeline.branching.selection import (
        BranchSelectionValidationService,
    )

    writer = FakeWriterService()
    branching_writer = _FakeBranchingWriterService()
    orch = OrchestratorService(
        intent_classifier=FakeIntentClassifier(
            make_intent(intent_type, raw_input)  # type: ignore[arg-type]
        ),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=writer,
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.BRANCHING),
        branching_writer_service=branching_writer,  # type: ignore[arg-type]
        # branching_session_resolver intentionally omitted (None).
        branching_selection_service=BranchSelectionValidationService(),
    )
    return orch, writer, branching_writer


class TestBranchingResolverRequired:
    """A BRANCHING turn fails closed when branching_session_resolver is absent.

    Without the resolver the orchestrator cannot distinguish setup,
    FREEFORM_ONLY, HYBRID, TRUE_CYOA, or play status, so it must not proceed
    with pre_branching_state=None and silently downgrade to the prose Writer.
    """

    def test_in_character_action_missing_resolver_fails_closed(
        self, session_factory: object, session: object
    ) -> None:
        """In-character BRANCHING turn + no resolver → PIPELINE_ERROR, no writer."""
        from afterworlds.models.enums import IntentType

        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch, writer, branching_writer = _make_branching_orch_without_resolver(
            session_factory,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            raw_input="I press onward.",
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "I press onward.", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "resolver not wired" in summary, summary
        # Fail closed before any writer routing: neither pass ran, no Turn.
        assert writer.calls == []
        assert branching_writer.called is False

    def test_branch_choice_missing_resolver_fails_closed_before_rejection(
        self, session_factory: object, session: object
    ) -> None:
        """BRANCH_CHOICE + no resolver → PIPELINE_ERROR, not INTERACTION_REJECTED.

        Proves the guard precedes TRUE_CYOA freeform rejection and branch
        selection validation, both of which depend on the resolved state.
        """
        from afterworlds.models.enums import IntentType

        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        orch, writer, branching_writer = _make_branching_orch_without_resolver(
            session_factory,
            intent_type=IntentType.BRANCH_CHOICE,
            raw_input="opt_1",
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "resolver not wired" in (result.pipeline_error_summary or "")
        # Not a user-input rejection: error precedes interaction-style checks.
        assert result.interaction_rejection_reason is None
        assert writer.calls == []
        assert branching_writer.called is False

    def test_wired_resolver_setup_hybrid_still_delivers(
        self, session_factory: object, session: object
    ) -> None:
        """Positive control: a wired resolver still permits the setup prose path."""
        from afterworlds.models.enums import (
            BranchingPlayStatus,
            IntentType,
            InteractionStyle,
        )

        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch = _make_branching_routing_orchestrator(
            session_factory,
            interaction_style=InteractionStyle.HYBRID,
            play_status=BranchingPlayStatus.SETUP,
            intent_type=IntentType.IN_CHARACTER_ACTION,
            branching_writer=_FakeBranchingWriterService(),
            raw_input="Let's begin the tale.",
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "Let's begin the tale.",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        assert result.branching_pass_result is None


def _make_branching_choice_orch_without_selection(
    session_factory: object,
    *,
    interaction_style: object,
    play_status: object,
    raw_input: str,
):  # type: ignore[no-untyped-def]
    """In-play/SETUP BRANCH_CHOICE orchestrator with NO selection service wired.

    Exposes the writer fakes so callers can prove no narrative pass ran when
    the missing-selection-service guard fails closed.
    """
    from afterworlds.models.enums import (
        BranchingCadence,
        IntentType,
        PacingStage,
        StoryMode,
    )
    from afterworlds.models.session import BranchingSessionState

    def _branching_resolver(sid: UUID) -> BranchingSessionState:
        return BranchingSessionState(
            story_id=sid,
            pacing_stage=PacingStage.ESCALATION,
            interaction_style=interaction_style,  # type: ignore[arg-type]
            branching_cadence=BranchingCadence.BALANCED,
            play_status=play_status,  # type: ignore[arg-type]
        )

    writer = FakeWriterService()
    branching_writer = _FakeBranchingWriterService()
    orch = OrchestratorService(
        intent_classifier=FakeIntentClassifier(
            make_intent(IntentType.BRANCH_CHOICE, raw_input)
        ),
        context_builder=FakeContextBuilder(),
        safety_service=FakeSafetyService(),
        planner_service=FakePlannerService(),
        writer_service=writer,
        extractor_service=FakeExtractorService(),
        contradiction_service=FakeContradictionService(),
        session_factory=session_factory,  # type: ignore[arg-type]
        safety_policy=CapabilityProfileAwareSafetyPolicy(),
        provider_resolver=_make_fake_resolver(),  # type: ignore[arg-type]
        mode_resolver=fixed_mode_resolver(StoryMode.BRANCHING),
        branching_writer_service=branching_writer,  # type: ignore[arg-type]
        branching_session_resolver=_branching_resolver,
        # branching_selection_service intentionally omitted (None).
    )
    return orch, writer, branching_writer


class TestBranchChoiceValidationServiceRequired:
    """In-play HYBRID/TRUE_CYOA BRANCH_CHOICE fails closed without selection svc.

    Without BranchSelectionValidationService the selection cannot be validated
    against the presented option set; treating it as freeform narrative would
    bypass the typed branch-card contract and bill a turn for an unvalidated
    choice.  Setup rows stay on the existing wired-only path (guard is in-play
    only).
    """

    def test_in_play_hybrid_missing_selection_service_fails_closed(
        self, session_factory: object, session: object
    ) -> None:
        """In-play HYBRID BRANCH_CHOICE + no selection svc → PIPELINE_ERROR, no turn."""
        from afterworlds.models.enums import BranchingPlayStatus, InteractionStyle

        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        orch, writer, branching_writer = _make_branching_choice_orch_without_selection(
            session_factory,
            interaction_style=InteractionStyle.HYBRID,
            play_status=BranchingPlayStatus.IN_PLAY,
            raw_input="opt_1",
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        summary = result.pipeline_error_summary or ""
        assert "selection validation service not wired" in summary, summary
        # No LLM call, no Turn, no billing: neither writer ran.
        assert writer.calls == []
        assert branching_writer.called is False
        # Fail-closed wiring guard, not a user-input rejection.
        assert result.interaction_rejection_reason is None

    def test_in_play_true_cyoa_missing_selection_service_fails_closed(
        self, session_factory: object, session: object
    ) -> None:
        """In-play TRUE_CYOA BRANCH_CHOICE + no selection svc → PIPELINE_ERROR."""
        from afterworlds.models.enums import BranchingPlayStatus, InteractionStyle

        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        orch, writer, branching_writer = _make_branching_choice_orch_without_selection(
            session_factory,
            interaction_style=InteractionStyle.TRUE_CYOA,
            play_status=BranchingPlayStatus.IN_PLAY,
            raw_input="opt_2",
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_2", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.PIPELINE_ERROR
        assert "selection validation service not wired" in (
            result.pipeline_error_summary or ""
        )
        assert writer.calls == []
        assert branching_writer.called is False
        assert result.interaction_rejection_reason is None

    def test_setup_hybrid_missing_selection_service_unchanged(
        self, session_factory: object, session: object
    ) -> None:
        """Positive control: setup BRANCH_CHOICE + no selection svc → prose, no error.

        The guard is in-play only, so setup behavior is unchanged: the missing
        selection service does not fail the turn closed during setup.
        """
        from afterworlds.models.enums import BranchingPlayStatus, InteractionStyle

        story_id, node_id = _seed_branching_story_with_options(session, [])
        orch, writer, branching_writer = _make_branching_choice_orch_without_selection(
            session_factory,
            interaction_style=InteractionStyle.HYBRID,
            play_status=BranchingPlayStatus.SETUP,
            raw_input="opt_1",
        )

        result = orch.orchestrate_turn(
            story_id, node_id, "opt_1", _SOJOURNER, RuntimeAccessPath.HOSTED
        )

        assert result.disposition is PipelineDisposition.DELIVERED
        # Setup routes through the prose Writer, not the branching writer.
        assert len(writer.calls) == 1
        assert branching_writer.called is False

    def test_wired_selection_service_invalid_choice_still_rejected(
        self, session_factory: object, session: object
    ) -> None:
        """Positive control: a wired service still returns INTERACTION_REJECTED."""
        from afterworlds.models.enums import InteractionStyle

        story_id, node_id = _seed_branching_story_with_options(
            session, ["Take the bridge", "Wade the river"]
        )
        orch = _make_branching_choice_orchestrator(
            session_factory,
            _FakeBranchingWriterService(),
            "I wander off the map entirely",
            interaction_style=InteractionStyle.HYBRID,
        )

        result = orch.orchestrate_turn(
            story_id,
            node_id,
            "I wander off the map entirely",
            _SOJOURNER,
            RuntimeAccessPath.HOSTED,
        )

        assert result.disposition is PipelineDisposition.INTERACTION_REJECTED
        assert result.interaction_rejection_reason is not None
