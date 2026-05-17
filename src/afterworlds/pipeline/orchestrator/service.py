"""OrchestratorService — CRD Issue 12c.

Wires existing per-pass callables (Issues 7–12b) into one end-to-end Sojourn
Turn.  Owns the outer transaction, OOC short-circuit, Safety envelope
gating, provider-refusal routing, the parallel-sync Extractor/Contradiction
join, and the disposition-population invariants enforced by the typed
``OrchestrationResult``.

Architectural invariants this module enforces (Issue 12c):

1. The orchestrator makes no direct model calls.  All model calls remain
   inside ``IntentClassifierService``, ``PlannerService``, ``WriterService``,
   ``SafetyService``, ``ExtractorService``, and ``ContradictionService``.
2. The orchestrator writes no canon directly.  Story Bible writes route
   only through ``StoryBibleService.route_extractor_proposals`` (Issue 10).
   Turn writes remain repository-backed in ``persistence/crud/node.py``.
3. ``AssembledContext`` is built once per Turn via ``ContextBuilder`` and
   threaded through all passes.  The orchestrator's only ledger mutation
   is appending ``PlannerOutput`` after Planner returns.
4. Blocked or refused prose produces no Turn row, no Story Bible writes,
   and no Node update.  ``BLOCKED_INPUT_SAFETY`` opens no outer transaction
   at all; later block / refusal / operational-error paths roll the outer
   transaction back.
5. ``SafetyResult`` is never appended to ``PassForwardLedger``.
6. ``RecentTurnReader`` (``RecentTurnsProvider``) is consulted only via the
   Context Builder; the orchestrator does not call it directly.

The orchestrator's typed result, disposition enum, and SafetyPolicy live in
``models`` so test code can import them without dragging the service in.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import nullcontext, suppress
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    StablePrefix,
)
from afterworlds.models.enums import IntentType
from afterworlds.models.intent_classification import (
    IntentClassificationError,
    IntentClassificationResult,
)
from afterworlds.pipeline._refusal import (
    ProviderRefusal,
    ProviderRefusalError,
)
from afterworlds.pipeline.contradiction.models import (
    ContradictionPassError,
    ContradictionResult,
)
from afterworlds.pipeline.contradiction.service import ContradictionService
from afterworlds.pipeline.extractor.models import ExtractorPassError, ExtractorResult
from afterworlds.pipeline.extractor.service import ExtractorService
from afterworlds.pipeline.orchestrator.models import (
    OrchestrationResult,
    PipelineDisposition,
    SafetyPolicy,
)
from afterworlds.pipeline.planner.models import (
    PlannerPassError,
    PlannerResult,
)
from afterworlds.pipeline.planner.service import PlannerService
from afterworlds.pipeline.safety.models import (
    SafetyPassError,
    SafetyResult,
    SafetyTarget,
    SafetyVerdict,
)
from afterworlds.pipeline.safety.service import SafetyService
from afterworlds.pipeline.writer.models import WriterPassError, WriterResult
from afterworlds.pipeline.writer.service import WriterService
from afterworlds.services.context_builder import ContextBuilderService
from afterworlds.services.intent_classifier import IntentClassifierService

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default timeout for the Contradiction worker future join (seconds).
DEFAULT_PARALLEL_PASS_TIMEOUT_SECONDS: float = 30.0

#: Provider identifier reported in ``WriterResult.model_identifier`` is of the
#: form ``"<provider>:<model>"``.  The orchestrator extracts the provider
#: portion for ``SafetyPolicy`` consultation.  Defaults to ``"anthropic"`` if
#: the Writer config or result does not surface a provider segment.
_DEFAULT_PROVIDER: str = "anthropic"


# ---------------------------------------------------------------------------
# OOC handler prompt loading
# ---------------------------------------------------------------------------

_PROMPT_DIR: Path = Path(__file__).parents[4] / "docs" / "prompts"


def load_ooc_handler_prompt() -> str:
    """Load the v1 OOC handler instruction from docs/prompts/ooc_handler.md."""
    prompt_path = _PROMPT_DIR / "ooc_handler.md"
    return prompt_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Mode resolver
# ---------------------------------------------------------------------------

#: Resolves a story_id to the StoryMode that should drive context assembly.
#: Injected so the orchestrator does not depend on a particular persistence
#: shape.  v1 default lives in the service module.
ModeResolver = Callable[[UUID], "Any"]


# ---------------------------------------------------------------------------
# OrchestratorService
# ---------------------------------------------------------------------------


class OrchestratorService:
    """End-to-end Sojourn Turn orchestrator (Issue 12c).

    The orchestrator's job is policy, not generation.  It schedules existing
    pass services, opens / commits / rolls back the outer transaction,
    short-circuits OOC turns through ``WriterService`` with the v1 OOC
    instruction, runs Safety calls when ``SafetyPolicy`` says so, and joins
    Extractor with Contradiction in parallel sync against the Writer's
    output.

    Args:
        intent_classifier: callable Intent Classifier (Issue 7).
        context_builder: ContextBuilder (Issue 8).  Builds one
            AssembledContext per turn.
        safety_service: SafetyService (Issue 12b).
        planner_service: PlannerService (Issue 12a).
        writer_service: WriterService (Issue 9) — also used for OOC.
        extractor_service: ExtractorService (Issue 10).
        contradiction_service: ContradictionService (Issue 11).
        session_factory: factory returning a fresh SQLAlchemy Session per
            turn.  The orchestrator opens one outer transaction on the
            session and forwards it into Writer / Extractor for SAVEPOINT
            nesting.
        safety_policy: SafetyPolicy controlling whether Input Preflight
            and Output Audit run.  Conservative v1 default: empty
            whitelist — both run on every turn.
        mode_resolver: resolves a story_id to a StoryMode for the Context
            Builder.  Defaults to a SQLite-backed lookup against the
            stories table.
        executor: optional ThreadPoolExecutor reused across calls.  When
            None (default), a single-worker executor is created and shut
            down per call — the orchestrator does not hold long-lived
            threads.  When supplied, the caller owns lifecycle; the
            orchestrator never calls ``shutdown``.
        parallel_pass_timeout_seconds: bound on the Contradiction worker
            future join.  Timeout produces PIPELINE_ERROR + rollback.
    """

    def __init__(
        self,
        intent_classifier: IntentClassifierService,
        context_builder: ContextBuilderService,
        safety_service: SafetyService,
        planner_service: PlannerService,
        writer_service: WriterService,
        extractor_service: ExtractorService,
        contradiction_service: ContradictionService,
        session_factory: Callable[[], Session],
        safety_policy: SafetyPolicy,
        mode_resolver: ModeResolver | None = None,
        executor: ThreadPoolExecutor | None = None,
        parallel_pass_timeout_seconds: float = DEFAULT_PARALLEL_PASS_TIMEOUT_SECONDS,
    ) -> None:
        self._intent_classifier = intent_classifier
        self._context_builder = context_builder
        self._safety_service = safety_service
        self._planner_service = planner_service
        self._writer_service = writer_service
        self._extractor_service = extractor_service
        self._contradiction_service = contradiction_service
        self._session_factory = session_factory
        self._safety_policy = safety_policy
        self._mode_resolver: ModeResolver = mode_resolver or _default_mode_resolver(
            session_factory
        )
        self._provided_executor = executor
        self._timeout = parallel_pass_timeout_seconds
        self._ooc_handler_prompt: str = load_ooc_handler_prompt()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def orchestrate_turn(
        self,
        story_id: UUID,
        node_id: UUID,
        user_input: str,
        *,
        request_risk_signal: bool = False,
    ) -> OrchestrationResult:
        """Run one full Sojourn Turn end-to-end.

        Returns a typed ``OrchestrationResult`` matching one of the seven
        ``PipelineDisposition`` values.  Construction-time invariants on
        the result enforce the spec's per-disposition field matrix.
        """
        turn_start = time.perf_counter()
        latency: dict[str, int] = {}

        # 1. Intent classification.
        intent_result, classify_ms = self._classify_intent(user_input, story_id)
        latency["intent"] = classify_ms
        if intent_result is None:
            return self._pipeline_error(
                _synthesize_intent(user_input),
                latency,
                turn_start,
                "intent classification failed",
            )

        # 2. Context assembly (once per turn).
        try:
            ctx, ctx_ms = self._build_context(story_id, user_input, intent_result)
            latency["context"] = ctx_ms
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                intent_result, latency, turn_start, f"context assembly failed: {exc}"
            )

        # OOC short-circuit owns its own pipeline shape.
        if intent_result.intent_type is IntentType.OOC:
            return self._run_ooc(
                ctx,
                story_id,
                node_id,
                intent_result,
                latency,
                turn_start,
                request_risk_signal,
            )

        return self._run_narrative(
            ctx,
            story_id,
            node_id,
            intent_result,
            latency,
            turn_start,
            request_risk_signal,
        )

    # ------------------------------------------------------------------
    # Narrative path
    # ------------------------------------------------------------------

    def _run_narrative(
        self,
        ctx: AssembledContext,
        story_id: UUID,
        node_id: UUID,
        intent_result: IntentClassificationResult,
        latency: dict[str, int],
        turn_start: float,
        request_risk_signal: bool,
    ) -> OrchestrationResult:
        writer_provider = self._derive_writer_provider()

        # 3. Input Safety Preflight, conditional.
        input_safety: SafetyResult | None = None
        if self._safety_policy.should_run_input_preflight(
            writer_provider, request_risk_signal
        ):
            try:
                input_safety, ms = _timed(
                    lambda: self._safety_service.check(
                        ctx, ctx.volatile_suffix.current_input, SafetyTarget.INPUT
                    )
                )
                latency["input_safety"] = ms
            except SafetyPassError as exc:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"input safety failed: {exc}",
                )
            assert input_safety is not None  # noqa: S101 — mypy narrowing
            if input_safety.verdict is SafetyVerdict.BLOCK:
                return self._build_result(
                    PipelineDisposition.BLOCKED_INPUT_SAFETY,
                    intent_result,
                    latency,
                    turn_start,
                    input_safety_result=input_safety,
                )

        # 4. Planner.
        try:
            planner_result, ms = _timed(lambda: self._planner_service.plan(ctx))
            latency["planner"] = ms
        except ProviderRefusalError as exc:
            return self._build_result(
                PipelineDisposition.REFUSED_BY_PROVIDER,
                intent_result,
                latency,
                turn_start,
                input_safety_result=input_safety,
                provider_refusal=exc.refusal,
            )
        except PlannerPassError as exc:
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"planner pass failed: {exc}",
                input_safety_result=input_safety,
            )

        ctx.pass_forward_ledger.add("planner", _serialize_planner(planner_result))

        # Open outer transaction now: Writer is about to persist a Turn.
        # We manage commit / rollback explicitly based on disposition rather
        # than relying on the SessionTransaction context manager, because
        # the result is returned (not raised) and the commit decision is
        # data-dependent (DELIVERED vs blocked/refused/error).
        session = self._session_factory()
        try:
            session.begin()
            try:
                result = self._narrative_persist(
                    session,
                    ctx,
                    story_id,
                    node_id,
                    intent_result,
                    planner_result,
                    input_safety,
                    writer_provider,
                    latency,
                    turn_start,
                )
            except BaseException:
                if session.in_transaction():
                    session.rollback()
                raise
            if (
                result.disposition is PipelineDisposition.DELIVERED
                and session.in_transaction()
            ):
                session.commit()
            elif session.in_transaction():
                session.rollback()
            return result
        finally:
            session.close()

    def _narrative_persist(
        self,
        session: Session,
        ctx: AssembledContext,
        story_id: UUID,
        node_id: UUID,
        intent_result: IntentClassificationResult,
        planner_result: PlannerResult,
        input_safety: SafetyResult | None,
        writer_provider: str,
        latency: dict[str, int],
        turn_start: float,
    ) -> OrchestrationResult:
        # 5. Writer persists provisional Turn inside the outer transaction.
        try:
            writer_result, ms = _timed(
                lambda: self._writer_service.write(
                    ctx, story_id, node_id, session=session
                )
            )
            latency["writer"] = ms
        except ProviderRefusalError as exc:
            return self._build_result(
                PipelineDisposition.REFUSED_BY_PROVIDER,
                intent_result,
                latency,
                turn_start,
                input_safety_result=input_safety,
                planner_result=planner_result,
                provider_refusal=exc.refusal,
            )
        except WriterPassError as exc:
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"writer pass failed: {exc}",
                input_safety_result=input_safety,
                planner_result=planner_result,
            )

        # 6. Output Safety Audit, conditional.
        output_safety: SafetyResult | None = None
        if self._safety_policy.should_run_output_audit(writer_provider, writer_result):
            try:
                output_safety, ms = _timed(
                    lambda: self._safety_service.check(
                        ctx, writer_result.assistant_output, SafetyTarget.OUTPUT
                    )
                )
                latency["output_safety"] = ms
            except SafetyPassError as exc:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"output safety failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
                )
            assert output_safety is not None  # noqa: S101 — mypy narrowing
            if output_safety.verdict is SafetyVerdict.BLOCK:
                return self._build_result(
                    PipelineDisposition.BLOCKED_OUTPUT_SAFETY,
                    intent_result,
                    latency,
                    turn_start,
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
                    output_safety_result=output_safety,
                )

        # 7. Extractor || Contradiction (parallel sync, asymmetric).
        try:
            extractor_result, contradiction_result, ext_ms, contr_ms = (
                self._run_parallel_sync(ctx, writer_result, story_id, session)
            )
            latency["extractor"] = ext_ms
            latency["contradiction"] = contr_ms
        except ProviderRefusalError as exc:
            return self._build_result(
                PipelineDisposition.REFUSED_BY_PROVIDER,
                intent_result,
                latency,
                turn_start,
                input_safety_result=input_safety,
                planner_result=planner_result,
                writer_result=writer_result,
                output_safety_result=output_safety,
                provider_refusal=exc.refusal,
            )
        except _ParallelSyncError as exc:
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"parallel sync failed: {exc}",
                input_safety_result=input_safety,
                planner_result=planner_result,
                writer_result=writer_result,
                output_safety_result=output_safety,
            )

        # 8. Gate on Contradiction.
        if contradiction_result.violations:
            return self._build_result(
                PipelineDisposition.BLOCKED_CONTRADICTION,
                intent_result,
                latency,
                turn_start,
                input_safety_result=input_safety,
                planner_result=planner_result,
                writer_result=writer_result,
                output_safety_result=output_safety,
                extractor_result=extractor_result,
                contradiction_result=contradiction_result,
            )

        # ALLOW → commit Turn + Extractor writes.  Outer transaction context
        # manager will commit on normal exit; no explicit commit needed.
        return self._build_result(
            PipelineDisposition.DELIVERED,
            intent_result,
            latency,
            turn_start,
            input_safety_result=input_safety,
            planner_result=planner_result,
            writer_result=writer_result,
            output_safety_result=output_safety,
            extractor_result=extractor_result,
            contradiction_result=contradiction_result,
            delivered_output=writer_result.assistant_output,
            turn_id=writer_result.turn_id,
        )

    # ------------------------------------------------------------------
    # OOC path
    # ------------------------------------------------------------------

    def _run_ooc(
        self,
        ctx: AssembledContext,
        story_id: UUID,
        node_id: UUID,
        intent_result: IntentClassificationResult,
        latency: dict[str, int],
        turn_start: float,
        request_risk_signal: bool,
    ) -> OrchestrationResult:
        writer_provider = self._derive_writer_provider()

        input_safety: SafetyResult | None = None
        if self._safety_policy.should_run_input_preflight(
            writer_provider, request_risk_signal
        ):
            try:
                input_safety, ms = _timed(
                    lambda: self._safety_service.check(
                        ctx, ctx.volatile_suffix.current_input, SafetyTarget.INPUT
                    )
                )
                latency["input_safety"] = ms
            except SafetyPassError as exc:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"input safety failed: {exc}",
                )
            assert input_safety is not None  # noqa: S101 — mypy narrowing
            if input_safety.verdict is SafetyVerdict.BLOCK:
                return self._build_result(
                    PipelineDisposition.BLOCKED_INPUT_SAFETY,
                    intent_result,
                    latency,
                    turn_start,
                    input_safety_result=input_safety,
                )

        # Derive an OOC-specific context: only the system_prompt swaps to the
        # v1 OOC handler instruction.  Story Bible, rolling summary, rules
        # slice, and retrieval are left in place — the OOC prompt instructs
        # the model to ignore them.  Issues 15–17 may revisit this.
        ooc_ctx = _swap_system_prompt(ctx, self._ooc_handler_prompt)

        session = self._session_factory()
        try:
            session.begin()
            try:
                result = self._ooc_persist(
                    session,
                    ooc_ctx,
                    story_id,
                    node_id,
                    intent_result,
                    input_safety,
                    writer_provider,
                    latency,
                    turn_start,
                )
            except BaseException:
                if session.in_transaction():
                    session.rollback()
                raise
            if (
                result.disposition is PipelineDisposition.OOC_HANDLED
                and session.in_transaction()
            ):
                session.commit()
            elif session.in_transaction():
                session.rollback()
            return result
        finally:
            session.close()

    def _ooc_persist(
        self,
        session: Session,
        ooc_ctx: AssembledContext,
        story_id: UUID,
        node_id: UUID,
        intent_result: IntentClassificationResult,
        input_safety: SafetyResult | None,
        writer_provider: str,
        latency: dict[str, int],
        turn_start: float,
    ) -> OrchestrationResult:
        try:
            writer_result, ms = _timed(
                lambda: self._writer_service.write(
                    ooc_ctx, story_id, node_id, session=session
                )
            )
            latency["writer"] = ms
        except ProviderRefusalError as exc:
            return self._build_result(
                PipelineDisposition.REFUSED_BY_PROVIDER,
                intent_result,
                latency,
                turn_start,
                input_safety_result=input_safety,
                provider_refusal=exc.refusal,
            )
        except WriterPassError as exc:
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"ooc handler failed: {exc}",
                input_safety_result=input_safety,
            )

        output_safety: SafetyResult | None = None
        if self._safety_policy.should_run_output_audit(writer_provider, writer_result):
            try:
                output_safety, ms = _timed(
                    lambda: self._safety_service.check(
                        ooc_ctx, writer_result.assistant_output, SafetyTarget.OUTPUT
                    )
                )
                latency["output_safety"] = ms
            except SafetyPassError as exc:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"output safety failed: {exc}",
                    input_safety_result=input_safety,
                    writer_result=writer_result,
                )
            assert output_safety is not None  # noqa: S101 — mypy narrowing
            if output_safety.verdict is SafetyVerdict.BLOCK:
                return self._build_result(
                    PipelineDisposition.BLOCKED_OUTPUT_SAFETY,
                    intent_result,
                    latency,
                    turn_start,
                    input_safety_result=input_safety,
                    writer_result=writer_result,
                    output_safety_result=output_safety,
                )

        return self._build_result(
            PipelineDisposition.OOC_HANDLED,
            intent_result,
            latency,
            turn_start,
            input_safety_result=input_safety,
            writer_result=writer_result,
            output_safety_result=output_safety,
            delivered_output=writer_result.assistant_output,
            turn_id=writer_result.turn_id,
        )

    # ------------------------------------------------------------------
    # Parallel sync — Extractor on orchestrator thread, Contradiction on worker.
    # ------------------------------------------------------------------

    def _run_parallel_sync(
        self,
        ctx: AssembledContext,
        writer_result: WriterResult,
        story_id: UUID,
        session: Session,
    ) -> tuple[ExtractorResult, ContradictionResult, int, int]:
        """Run Extractor synchronously and Contradiction on a worker thread.

        Asymmetric by design: Contradiction has no DB I/O so worker-thread
        execution is safe; Extractor writes via the orchestrator-owned
        session under a SAVEPOINT, so it MUST run on the orchestrator
        thread to avoid sharing the session across threads (Issue 12c
        invariant).

        Returns Extractor and Contradiction results plus their individual
        latencies in milliseconds.  Raises:
          - ``ProviderRefusalError`` if either pass refuses.  The caller
            is responsible for rolling back.
          - ``_ParallelSyncError`` for any other operational failure or
            timeout.  The caller is responsible for rolling back.
        """
        executor_ctx = (
            nullcontext(self._provided_executor)
            if self._provided_executor is not None
            else ThreadPoolExecutor(max_workers=1)
        )
        with executor_ctx as executor:
            assert executor is not None
            contradiction_future: Future[tuple[ContradictionResult, int]] = (
                executor.submit(
                    _timed_for_thread,
                    lambda: self._contradiction_service.check(
                        ctx, writer_result.assistant_output
                    ),
                )
            )

            # Extractor on this thread, under SAVEPOINT inside the outer txn.
            try:
                extractor_result, ext_ms = _timed(
                    lambda: self._extractor_service.extract(
                        ctx,
                        writer_result.assistant_output,
                        story_id,
                        writer_result.turn_id,
                        session=session,
                    )
                )
            except ProviderRefusalError:
                # Cancel/await contradiction so executor exits cleanly.
                _drain_future(contradiction_future, self._timeout)
                raise
            except ExtractorPassError as exc:
                _drain_future(contradiction_future, self._timeout)
                raise _ParallelSyncError(f"extractor: {exc}") from exc

            try:
                contradiction_result, contr_ms = contradiction_future.result(
                    timeout=self._timeout
                )
            except FutureTimeout as exc:
                raise _ParallelSyncError(
                    f"contradiction worker exceeded {self._timeout:.1f}s timeout"
                ) from exc
            except ProviderRefusalError:
                raise
            except ContradictionPassError as exc:
                raise _ParallelSyncError(f"contradiction: {exc}") from exc

            return extractor_result, contradiction_result, ext_ms, contr_ms

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _classify_intent(
        self, user_input: str, story_id: UUID
    ) -> tuple[IntentClassificationResult | None, int]:
        try:
            result, ms = _timed(
                lambda: self._intent_classifier.classify(user_input, story_id)
            )
            return result, ms
        except IntentClassificationError:
            return None, 0

    def _build_context(
        self,
        story_id: UUID,
        user_input: str,
        intent_result: IntentClassificationResult,
    ) -> tuple[AssembledContext, int]:
        mode = self._mode_resolver(story_id)
        return _timed(
            lambda: self._context_builder.assemble(
                story_id=story_id,
                mode=mode,
                current_input=user_input,
                classified_intent=intent_result,
            )
        )

    def _derive_writer_provider(self) -> str:
        config = getattr(self._writer_service, "_config", None)
        provider = getattr(config, "provider", None)
        if isinstance(provider, str) and provider:
            return provider
        return _DEFAULT_PROVIDER

    def _build_result(
        self,
        disposition: PipelineDisposition,
        intent_result: IntentClassificationResult,
        latency: dict[str, int],
        turn_start: float,
        *,
        delivered_output: str | None = None,
        turn_id: UUID | None = None,
        input_safety_result: SafetyResult | None = None,
        planner_result: PlannerResult | None = None,
        writer_result: WriterResult | None = None,
        output_safety_result: SafetyResult | None = None,
        extractor_result: ExtractorResult | None = None,
        contradiction_result: ContradictionResult | None = None,
        provider_refusal: ProviderRefusal | None = None,
        pipeline_error_summary: str | None = None,
    ) -> OrchestrationResult:
        total_ms = max(0, int((time.perf_counter() - turn_start) * 1000))
        return OrchestrationResult(
            disposition=disposition,
            delivered_output=delivered_output,
            turn_id=turn_id,
            intent_classification=intent_result,
            input_safety_result=input_safety_result,
            planner_result=planner_result,
            writer_result=writer_result,
            output_safety_result=output_safety_result,
            extractor_result=extractor_result,
            contradiction_result=contradiction_result,
            provider_refusal=provider_refusal,
            pipeline_error_summary=pipeline_error_summary,
            total_latency_ms=total_ms,
            pass_latency_breakdown=dict(latency),
        )

    def _pipeline_error(
        self,
        intent_result: IntentClassificationResult,
        latency: dict[str, int],
        turn_start: float,
        summary: str,
        *,
        input_safety_result: SafetyResult | None = None,
        planner_result: PlannerResult | None = None,
        writer_result: WriterResult | None = None,
        output_safety_result: SafetyResult | None = None,
    ) -> OrchestrationResult:
        return self._build_result(
            PipelineDisposition.PIPELINE_ERROR,
            intent_result,
            latency,
            turn_start,
            input_safety_result=input_safety_result,
            planner_result=planner_result,
            writer_result=writer_result,
            output_safety_result=output_safety_result,
            pipeline_error_summary=summary,
        )


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class _ParallelSyncError(Exception):
    """Operational failure during the Extractor || Contradiction stage.

    Raised by ``_run_parallel_sync`` for non-refusal failures: extractor
    operational error, contradiction operational error, or contradiction
    worker timeout.  The caller maps this to ``PIPELINE_ERROR``.
    """


def _timed[T](fn: Callable[[], T]) -> tuple[T, int]:
    start = time.perf_counter()
    result = fn()
    elapsed_ms = max(0, int((time.perf_counter() - start) * 1000))
    return result, elapsed_ms


def _timed_for_thread[T](fn: Callable[[], T]) -> tuple[T, int]:
    """Worker-thread variant of ``_timed`` (identical semantics)."""
    return _timed(fn)


def _drain_future(future: Future[Any], timeout: float) -> None:
    """Wait for a worker future to complete, swallowing its result/exception.

    Used after the orchestrator-thread pass has already failed and we just
    need the worker to finish before the executor context manager exits.
    The secondary outcome is intentionally suppressed so it cannot mask
    the original primary failure.
    """
    with suppress(Exception):
        future.result(timeout=timeout)


def _serialize_planner(result: PlannerResult) -> str:
    """Serialize a PlannerResult.plan for inclusion in the ledger.

    Uses Pydantic's deterministic JSON serializer so the resulting string
    is byte-stable for cache integrity (CRD Item 14 invariant #10).
    """
    return result.plan.model_dump_json()


def _swap_system_prompt(
    ctx: AssembledContext, new_system_prompt: str
) -> AssembledContext:
    """Return a derived AssembledContext whose system_prompt is replaced.

    Used by the OOC short-circuit to swap the active mode contract for the
    v1 OOC handler instruction.  All other stable-prefix fields are
    preserved unchanged.  The original ``ctx`` is not mutated.
    """
    sp = ctx.stable_prefix
    new_sp = StablePrefix(
        system_prompt=new_system_prompt,
        story_bible_context=sp.story_bible_context,
        rolling_summary_text=sp.rolling_summary_text,
        rules_package_slice=sp.rules_package_slice,
        retrieval_memory=sp.retrieval_memory,
    )
    return AssembledContext(
        stable_prefix=new_sp,
        volatile_suffix=ctx.volatile_suffix,
        pass_forward_ledger=PassForwardLedger(),
    )


def _synthesize_intent(user_input: str) -> IntentClassificationResult:
    """Fallback intent for pre-classification PIPELINE_ERROR results.

    Intent classification can fail before we know the intent type.  The
    typed ``OrchestrationResult`` requires an ``IntentClassificationResult``
    so the caller can still introspect ``raw_input``.  We synthesize a
    conservative neutral value: ``AUTHOR_INSTRUCTION`` with zero
    confidence.  The disposition is always ``PIPELINE_ERROR`` for this
    path so callers know the classification was not real.
    """
    return IntentClassificationResult(
        intent_type=IntentType.AUTHOR_INSTRUCTION,
        confidence=0.0,
        raw_input=user_input,
        ambiguous=False,
    )


def _default_mode_resolver(
    session_factory: Callable[[], Session],
) -> ModeResolver:
    """Default mode resolver: SQLite lookup against the stories table."""
    from afterworlds.models.enums import StoryMode
    from afterworlds.persistence.orm.story import StoryORM

    def resolve(story_id: UUID) -> StoryMode:
        session = session_factory()
        try:
            row = session.get(StoryORM, str(story_id))
            if row is None:
                raise LookupError(f"story {story_id} not found")
            return StoryMode(row.mode)
        finally:
            session.close()

    return resolve
