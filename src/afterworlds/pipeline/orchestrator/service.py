"""OrchestratorService — CRD Issue 12c / 14a.

Wires existing per-pass callables (Issues 7–12b) into one end-to-end Sojourn
Turn.  Owns the outer transaction, OOC short-circuit, Safety envelope
gating, provider-refusal routing, the parallel-sync Extractor/Contradiction
join, and the disposition-population invariants enforced by the typed
``OrchestrationResult``.

Architectural invariants this module enforces (Issue 12c / 14a):

1. The orchestrator makes no direct model calls.  All model calls remain
   inside ``IntentClassifierService``, ``PlannerService``, ``WriterService``,
   ``SafetyService``, ``ExtractorService``, and ``ContradictionService``.
2. The orchestrator writes no canon directly.  Story Bible writes route
   only through ``StoryBibleService.route_extractor_proposals`` (Issue 10).
   Turn writes remain repository-backed in ``persistence/crud/node.py``.
3. ``AssembledContext`` is built once per Turn via ``ContextBuilder`` and
   threaded through all passes.  The orchestrator's ledger mutations are:
   appending ``PlannerOutput`` after Planner returns, and (RPG IN_PLAY
   turns only) appending adjudication writer-views after the adjudication
   pass.  No other orchestrator code mutates the ledger.
4. Blocked or refused prose produces no Turn row, no Story Bible writes,
   and no Node update.  ``BLOCKED_INPUT_SAFETY`` opens no outer transaction
   at all; later block / refusal / operational-error paths roll the outer
   transaction back.
5. ``SafetyResult`` is never appended to ``PassForwardLedger``.
6. ``RecentTurnReader`` (``RecentTurnsProvider``) is consulted only via the
   Context Builder; the orchestrator does not call it directly.
7. (Issue 14a) A single ``TurnProviderBinding`` is resolved once per turn by
   ``ProviderResolver`` and threaded through every pass.  The orchestrator
   never makes direct model calls or selects models.

The orchestrator's typed result, disposition enum, and
``CapabilityProfileAwareSafetyPolicy`` live in ``models`` so test code can
import them without dragging the service in.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    StablePrefix,
)
from afterworlds.models.enums import IntentType, RpgPlayStatus, StoryMode
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.pipeline._refusal import (
    ProviderRefusal,
    ProviderRefusalError,
)
from afterworlds.pipeline.rpg.models import AdjudicationPassError
from afterworlds.pipeline.rpg.pending import PendingRollDuplicateError

if TYPE_CHECKING:
    from afterworlds.models.character_sheet import Dnd5eCharacterSheet
    from afterworlds.models.rpg import PendingRollRequest, RpgVisibleState, SheetEffect
    from afterworlds.models.session import RpgSessionState
    from afterworlds.pipeline.rpg.dice import DiceService
    from afterworlds.pipeline.rpg.models import AdjudicationPassResult
    from afterworlds.pipeline.rpg.pending import PendingRollRequestService
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from afterworlds.pipeline.rpg.visible_state import RpgVisibleStateService
from afterworlds.pipeline.contradiction.models import (
    ContradictionPassError,
    ContradictionResult,
)
from afterworlds.pipeline.contradiction.service import ContradictionService
from afterworlds.pipeline.extractor.models import ExtractorPassError, ExtractorResult
from afterworlds.pipeline.extractor.service import ExtractorService
from afterworlds.pipeline.orchestrator.models import (
    CapabilityProfileAwareSafetyPolicy,
    OrchestrationResult,
    PipelineDisposition,
    SafetyPolicyContext,
)
from afterworlds.pipeline.planner.models import (
    PlannerPassError,
    PlannerResult,
)
from afterworlds.pipeline.planner.service import PlannerService
from afterworlds.pipeline.provider._protocol import ProviderAdapter
from afterworlds.pipeline.provider._resolver import ProviderResolver
from afterworlds.pipeline.provider._routing import TurnProviderBinding
from afterworlds.pipeline.provider.adapters._scoped import ScopedProviderAdapter
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

#: Default ``max_workers`` for the orchestrator-owned ContradictionService
#: executor (used when no executor is injected).  Bounds the total number of
#: live contradiction worker threads so repeated timeouts cannot accumulate
#: workers without bound — see Codex P1 round 8 / the owner-decision thread
#: on worker buildup.  A small bounded value is the right cap because
#: Contradiction performs no DB I/O, so a single hung worker only blocks
#: one queue slot; the orchestrator still returns PIPELINE_ERROR promptly
#: for the requesting turn because the timeout fires on its own future,
#: not on the worker.
DEFAULT_PARALLEL_PASS_MAX_WORKERS: int = 4


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


def _noop_fn() -> None:
    pass


# ---------------------------------------------------------------------------
# OrchestratorService
# ---------------------------------------------------------------------------


class OrchestratorService:
    """End-to-end Sojourn Turn orchestrator (Issue 12c / 14a).

    The orchestrator's job is policy, not generation.  It schedules existing
    pass services, opens / commits / rolls back the outer transaction,
    short-circuits OOC turns through ``WriterService`` with the v1 OOC
    instruction, runs Safety calls when ``CapabilityProfileAwareSafetyPolicy``
    says so, and joins Extractor with Contradiction in parallel sync against
    the Writer's output.

    **Exception-mapping boundary** (Issue 12c family invariant):

    ``orchestrate_turn`` is an exhaustive typed boundary for ordinary
    operational failures.  Every ``Exception`` raised by an injected
    orchestration dependency or orchestration-owned runtime step maps to
    a typed terminal disposition on the returned ``OrchestrationResult``.
    The specific dispositions remain authoritative for their categories
    (Safety BLOCK verdicts, Contradiction BLOCK, ``ProviderRefusalError``
    → REFUSED_BY_PROVIDER, pass-specific typed errors and the
    contradiction-refusal-with-extractor preservation behavior); for any
    other ``Exception`` the mapping is PIPELINE_ERROR with useful cause
    text in ``pipeline_error_summary``, upstream pass results preserved
    where the result model allows it, and rollback semantics preserved.

    ``BaseException`` (``KeyboardInterrupt``, ``SystemExit``,
    ``concurrent.futures.CancelledError`` raised in the host) is
    explicitly outside this contract and is allowed to propagate so the
    host process can shut down cleanly.  The single ``CancelledError``
    site inside ``_run_parallel_sync`` only normalises future-surfaced
    cancellations from the contradiction worker — caller-side
    ``CancelledError`` still propagates.

    Per-site ``except Exception`` fallbacks therefore appear at every
    injected-service call site in this module; their cause-text prefix
    (e.g. ``"writer unexpected error: ..."``) disambiguates them from
    the typed-error prefixes (e.g. ``"writer pass failed: ..."``) in
    observability and tests.

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
        safety_policy: CapabilityProfileAwareSafetyPolicy controlling
            whether Input Preflight and Output Audit run.
        provider_resolver: ProviderResolver that resolves a
            TurnProviderBinding for each turn.  The binding is used to
            call all pass services with the correct adapter.
        mode_resolver: resolves a story_id to a StoryMode for the Context
            Builder.  Defaults to a SQLite-backed lookup against the
            stories table.
        executor: optional ThreadPoolExecutor for the Contradiction worker.
            When None (default), the orchestrator creates one bounded
            executor of size ``parallel_pass_max_workers`` and reuses it
            for the lifetime of this ``OrchestratorService`` instance.
            ``close()`` releases it; tests should call ``close()`` (or use
            the orchestrator as a context manager) to release the pool.
            When supplied, the caller owns lifecycle and the orchestrator
            NEVER calls ``shutdown`` on it.
        parallel_pass_timeout_seconds: bound on the Contradiction worker
            future join.  Timeout produces PIPELINE_ERROR + rollback.
        parallel_pass_max_workers: ``max_workers`` for the orchestrator-
            owned executor (ignored when ``executor`` is provided).  Caps
            the total number of live contradiction worker threads so
            repeated timeouts cannot accumulate workers without bound;
            see ``DEFAULT_PARALLEL_PASS_MAX_WORKERS`` for the rationale.

    Executor-lifecycle contract (Codex P1 round 8 / owner direction):
        Orchestrator-owned executor is created once in ``__init__`` and
        lives until ``close()``.  Per-turn ``submit()`` queues a fresh
        future; on timeout the orchestrator calls ``future.cancel()``
        (which cancels queued-not-started work but cannot interrupt a
        running provider call).  Already-running contradiction workers
        run to natural completion — they hold one executor slot apiece
        until done.  Total live workers are bounded by ``max_workers``.
        Contradiction has no DB I/O, so a hung worker is side-effect-
        free for canon and only blocks one queue slot.
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
        safety_policy: CapabilityProfileAwareSafetyPolicy,
        provider_resolver: ProviderResolver,
        mode_resolver: ModeResolver | None = None,
        executor: ThreadPoolExecutor | None = None,
        parallel_pass_timeout_seconds: float = DEFAULT_PARALLEL_PASS_TIMEOUT_SECONDS,
        parallel_pass_max_workers: int = DEFAULT_PARALLEL_PASS_MAX_WORKERS,
        rpg_adjudication_service: RpgAdjudicationPassService | None = None,
        rpg_session_sheet_resolver: (
            Callable[[UUID], tuple[RpgSessionState, Dnd5eCharacterSheet]] | None
        ) = None,
        rpg_dice_service: DiceService | None = None,
        rpg_pending_roll_service: PendingRollRequestService | None = None,
        rpg_visible_state_service: RpgVisibleStateService | None = None,
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
        self._provider_resolver = provider_resolver
        self._mode_resolver: ModeResolver = mode_resolver or _default_mode_resolver(
            session_factory
        )
        self._rpg_adjudication_service = rpg_adjudication_service
        self._rpg_session_sheet_resolver = rpg_session_sheet_resolver
        self._rpg_dice_service = rpg_dice_service
        self._rpg_pending_roll_service = rpg_pending_roll_service
        self._rpg_visible_state_service = rpg_visible_state_service
        self._provided_executor = executor
        # Owned executor is created once and reused for the lifetime of
        # this instance — see the Executor-lifecycle contract above.
        self._owned_executor: ThreadPoolExecutor | None = (
            ThreadPoolExecutor(
                max_workers=parallel_pass_max_workers,
                thread_name_prefix="orchestrator-contradiction",
            )
            if executor is None
            else None
        )
        self._timeout = parallel_pass_timeout_seconds
        self._ooc_handler_prompt: str = load_ooc_handler_prompt()

    def close(self) -> None:
        """Release the orchestrator-owned executor.

        No-op when an executor was injected via the constructor — that
        executor's lifecycle is caller-owned.  Safe to call multiple
        times.  Uses ``shutdown(wait=False, cancel_futures=True)`` so
        queued-not-started workers are cancelled and the call does not
        block on still-running workers (Contradiction has no DB I/O, so
        the leak is bounded and side-effect-free).
        """
        if self._owned_executor is not None:
            self._owned_executor.shutdown(wait=False, cancel_futures=True)
            self._owned_executor = None

    def __enter__(self) -> OrchestratorService:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def orchestrate_turn(
        self,
        story_id: UUID,
        node_id: UUID,
        user_input: str,
        sojourner_id: UUID,
        access_path: RuntimeAccessPath,
        *,
        request_risk_signal: bool = False,
        player_reported_total: int | None = None,
    ) -> OrchestrationResult:
        """Run one full Sojourn Turn end-to-end.

        Returns a typed ``OrchestrationResult`` matching one of the eight
        ``PipelineDisposition`` values.  Construction-time invariants on
        the result enforce the spec's per-disposition field matrix.

        ``player_reported_total`` is non-None on the pending-roll consume
        path: the Sojourner is reporting the total from their physical roll.
        """
        turn_start = time.perf_counter()
        latency: dict[str, int] = {}

        # 0. Resolve provider binding for this turn.
        #
        # Fail-fast before any model call.  ProviderConfigError and any other
        # exception from the resolver map to PIPELINE_ERROR per the
        # orchestrator's exhaustive terminal-state contract.
        try:
            binding = self._provider_resolver.resolve_for_turn(
                access_path, sojourner_id
            )
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                _synthesize_intent(user_input),
                latency,
                turn_start,
                f"provider resolution failed: {exc}",
            )

        # 1. Intent classification.
        #
        # `IntentClassifierService.classify` may raise the typed
        # `IntentClassificationError` (parse / validation failure) OR any
        # untyped runtime failure from the injected model caller (transport
        # error, provider hiccup, etc.).  Both must produce a typed
        # PIPELINE_ERROR result rather than escaping `orchestrate_turn` as
        # a raw exception — the orchestrator's terminal-state contract is
        # exhaustive (Issue 12c).
        try:
            intent_result, classify_ms = _timed(
                lambda: self._intent_classifier.classify(user_input, story_id)
            )
            latency["intent"] = classify_ms
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                _synthesize_intent(user_input),
                latency,
                turn_start,
                f"intent classification failed: {exc}",
            )

        # 2. Context assembly (once per turn).
        try:
            ctx, story_mode, ctx_ms = self._build_context(
                story_id, user_input, intent_result
            )
            latency["context"] = ctx_ms
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                intent_result, latency, turn_start, f"context assembly failed: {exc}"
            )

        # OOC short-circuit owns its own pipeline shape.
        # OOC-while-pending: the pending-roll intercept is deliberately skipped
        # for OOC turns — the pending roll waits while the player asks questions.
        if intent_result.intent_type is IntentType.OOC:
            return self._run_ooc(
                ctx,
                story_id,
                node_id,
                sojourner_id,
                intent_result,
                binding,
                latency,
                turn_start,
                request_risk_signal,
            )

        # Pending-roll intercept for RPG in-play narrative turns.
        # Runs before Planner so a block-redirect returns before any LLM call.
        pending_roll: PendingRollRequest | None = None
        if story_mode == StoryMode.RPG and self._rpg_pending_roll_service is not None:
            try:
                pending_roll = self._rpg_pending_roll_service.load_pending_for_story(
                    story_id
                )
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"pending roll lookup failed: {exc}",
                )
            if pending_roll is not None and player_reported_total is None:
                # Player has an outstanding pending roll to report but did not
                # provide a total.  Block and redirect with the original instruction.
                return self._build_result(
                    PipelineDisposition.BLOCKED_PENDING_ROLL,
                    intent_result,
                    latency,
                    turn_start,
                    pending_roll_redirect_message=(
                        pending_roll.player_facing_instruction
                    ),
                )

        return self._run_narrative(
            ctx,
            story_id,
            node_id,
            sojourner_id,
            intent_result,
            binding,
            latency,
            turn_start,
            request_risk_signal,
            story_mode,
            pending_roll=pending_roll,
            player_reported_total=player_reported_total,
        )

    # ------------------------------------------------------------------
    # Narrative path
    # ------------------------------------------------------------------

    def _run_narrative(
        self,
        ctx: AssembledContext,
        story_id: UUID,
        node_id: UUID,
        sojourner_id: UUID,
        intent_result: IntentClassificationResult,
        binding: TurnProviderBinding,
        latency: dict[str, int],
        turn_start: float,
        request_risk_signal: bool,
        story_mode: StoryMode,
        *,
        pending_roll: PendingRollRequest | None = None,
        player_reported_total: int | None = None,
    ) -> OrchestrationResult:
        # 3. Input Safety Preflight, conditional.
        input_safety: SafetyResult | None = None
        preflight_ctx = SafetyPolicyContext(
            eligible_writer_routes=binding.eligible_writer_routes,
            request_risk_signal=request_risk_signal,
            access_path=binding.access_path,
        )
        if self._safety_policy.should_run_input_preflight(preflight_ctx):
            try:
                input_safety, ms = _timed(
                    lambda: self._safety_service.check(
                        ctx,
                        ctx.volatile_suffix.current_input,
                        SafetyTarget.INPUT,
                        provider=ScopedProviderAdapter(binding.adapter, sojourner_id),  # type: ignore[arg-type]
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
            except Exception as exc:  # noqa: BLE001 — see boundary docstring
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"input safety unexpected error: {exc}",
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
            planner_result, ms = _timed(
                lambda: self._planner_service.plan(
                    ctx,
                    provider=ScopedProviderAdapter(binding.adapter, sojourner_id),  # type: ignore[arg-type]
                )
            )
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
        except Exception as exc:  # noqa: BLE001 — see boundary docstring
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"planner unexpected error: {exc}",
                input_safety_result=input_safety,
            )

        ctx.pass_forward_ledger.add("planner", _serialize_planner(planner_result))

        # Preallocate writer_turn_id before adjudication so the PendingRollRequest
        # can record originating_turn_id without waiting for the transaction to open.
        writer_turn_id = uuid4()

        # --- RPG Adjudication pass (Fork A→A1): runs after Planner, before Writer.
        # Result is held in memory and flushed inside the outer transaction (Fork B→B1).
        adj_result: AdjudicationPassResult | None = None
        rpg_session_id: UUID | None = None
        rpg_character_id: UUID | None = None
        rpg_sheet: Dnd5eCharacterSheet | None = None

        if story_mode == StoryMode.RPG and self._rpg_adjudication_service is not None:
            if (
                self._rpg_session_sheet_resolver is None
                or self._rpg_dice_service is None
            ):
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "RPG adjudication wired without session/sheet resolver"
                    " or dice service",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            try:
                session_state, sheet = self._rpg_session_sheet_resolver(story_id)
                rpg_session_id = session_state.session_id
                rpg_character_id = sheet.sheet_id
                rpg_sheet = sheet
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"RPG session/sheet resolution failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            # Gate: skip adjudication for setup turns and for sheets that
            # aren't fully configured.  play_status SETUP covers character
            # creation and world-setup turns that flow through _run_narrative
            # (OOC turns are already short-circuited upstream).
            # is_adjudicable is a second-line guard: if the sheet has since
            # been corrupted, skip cleanly instead of throwing from the adapter.
            _adj_svc = self._rpg_adjudication_service
            if (
                session_state.play_status is RpgPlayStatus.IN_PLAY
                and _adj_svc.is_adjudicable(sheet)
            ):
                # Use local to narrow from DiceService | None for the lambda capture.
                _dice_svc = self._rpg_dice_service
                try:
                    _pending = pending_roll
                    _total = player_reported_total
                    adj_result, adj_ms = _timed(
                        lambda: _adj_svc.adjudicate(
                            ctx,
                            session_state,
                            sheet,
                            _dice_svc,
                            provider=ScopedProviderAdapter(
                                binding.adapter,  # type: ignore[arg-type]
                                sojourner_id,
                            ),
                            story_id=story_id,
                            originating_turn_id=writer_turn_id,
                            pending_roll=_pending,
                            player_reported_total=_total,
                        )
                    )
                    latency["rpg_adjudication"] = adj_ms
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
                except AdjudicationPassError as exc:
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        f"adjudication pass failed: {exc}",
                        input_safety_result=input_safety,
                        planner_result=planner_result,
                    )
                except Exception as exc:  # noqa: BLE001
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        f"adjudication unexpected error: {exc}",
                        input_safety_result=input_safety,
                        planner_result=planner_result,
                    )
                # All except branches return; adj_result is set at this point.
                assert adj_result is not None  # noqa: S101 — mypy narrowing
                if adj_result.writer_views:
                    ctx.pass_forward_ledger.add(
                        "rpg_adjudication", _serialize_adj_views(adj_result)
                    )
        # -------------------------------------------------------------------------

        # Open outer transaction now: Writer is about to persist a Turn.
        # Session lifecycle (factory, begin, finalize, close) is centralized
        # in ``_run_with_transaction`` so the narrative and OOC paths cannot
        # drift, and so every raw exception in that lifecycle is mapped to a
        # typed terminal state per the orchestrator's exhaustive
        # terminal-state contract (Issue 12c).
        return self._run_with_transaction(
            lambda session: self._narrative_persist(
                session,
                ctx,
                story_id,
                node_id,
                sojourner_id,
                intent_result,
                planner_result,
                input_safety,
                binding,
                request_risk_signal,
                latency,
                turn_start,
                writer_turn_id=writer_turn_id,
                adj_result=adj_result,
                rpg_session_id=rpg_session_id,
                rpg_character_id=rpg_character_id,
                pending_roll_consumed=pending_roll,
                rpg_sheet=rpg_sheet,
            ),
            intent_result,
            latency,
            turn_start,
            success_disposition=PipelineDisposition.DELIVERED,
            pre_transaction_fn=binding.pre_transaction_fn,
            post_transaction_fn=binding.post_transaction_fn,
        )

    def _narrative_persist(
        self,
        session: Session,
        ctx: AssembledContext,
        story_id: UUID,
        node_id: UUID,
        sojourner_id: UUID,
        intent_result: IntentClassificationResult,
        planner_result: PlannerResult,
        input_safety: SafetyResult | None,
        binding: TurnProviderBinding,
        request_risk_signal: bool,
        latency: dict[str, int],
        turn_start: float,
        *,
        writer_turn_id: UUID,
        adj_result: AdjudicationPassResult | None = None,
        rpg_session_id: UUID | None = None,
        rpg_character_id: UUID | None = None,
        pending_roll_consumed: PendingRollRequest | None = None,
        rpg_sheet: Dnd5eCharacterSheet | None = None,
    ) -> OrchestrationResult:
        # 5. Writer persists provisional Turn inside the outer transaction.
        #
        # writer_turn_id is pre-allocated by _run_narrative so the adjudication
        # pass can store it as PendingRollRequest.originating_turn_id before the
        # transaction opens.  RefusalFallbackRouter also carries the same id so
        # refusal-log rows are consistent with the Turn row on success.  On
        # failure no Turn is persisted; the log row still carries the candidate id.
        try:
            writer_result, ms = _timed(
                lambda: self._writer_service.write(
                    ctx,
                    story_id,
                    node_id,
                    provider=ScopedProviderAdapter(
                        binding.adapter,  # type: ignore[arg-type]
                        sojourner_id,
                        turn_id=writer_turn_id,
                    ),
                    session=session,
                    turn_id=writer_turn_id,
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
        except Exception as exc:  # noqa: BLE001 — see boundary docstring
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"writer unexpected error: {exc}",
                input_safety_result=input_safety,
                planner_result=planner_result,
            )

        # 5b. [RPG only] Write adjudication audit rows, consume/announce pending
        # roll, inside the outer transaction (Fork B→B1).  Runs only when
        # adjudication produced a result; skipped on non-RPG and no-proposal turns.
        if (
            adj_result is not None
            and rpg_session_id is not None
            and rpg_character_id is not None
        ):
            try:
                self._write_rpg_audit(
                    session,
                    adj_result,
                    writer_result.turn_id,
                    story_id,
                    rpg_session_id,
                    rpg_character_id,
                    pending_roll_consumed=pending_roll_consumed,
                )
            except PendingRollDuplicateError as exc:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"pending roll duplicate on announce: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
                )
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"rpg audit write failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
                )

        # 5c. Apply sheet effects (Fork B→B1) inside the outer transaction, then
        # compute visible state from the post-mutation snapshot.  Both run only
        # when adjudication produced proposals; skipped otherwise.
        rpg_visible_state: RpgVisibleState | None = None
        if adj_result is not None and rpg_sheet is not None:
            all_effects = tuple(
                effect
                for record in adj_result.proposals
                for effect in record.sheet_effects
            )
            if all_effects:
                try:
                    rpg_sheet = self._apply_rpg_sheet_effects(
                        session, all_effects, rpg_sheet
                    )
                except Exception as exc:  # noqa: BLE001
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        f"sheet effect application failed: {exc}",
                        input_safety_result=input_safety,
                        planner_result=planner_result,
                        writer_result=writer_result,
                    )
            if self._rpg_visible_state_service is not None:
                rpg_visible_state = self._rpg_visible_state_service.build(rpg_sheet)

        # 6. Output Safety Audit, conditional.
        output_safety: SafetyResult | None = None
        audit_ctx = SafetyPolicyContext(
            eligible_writer_routes=binding.eligible_writer_routes,
            request_risk_signal=request_risk_signal,
            access_path=binding.access_path,
            writer_result=writer_result,
        )
        if self._safety_policy.should_run_output_audit(audit_ctx):
            _post_writer_turn_id = writer_result.turn_id
            try:
                output_safety, ms = _timed(
                    lambda: self._safety_service.check(
                        ctx,
                        writer_result.assistant_output,
                        SafetyTarget.OUTPUT,
                        provider=ScopedProviderAdapter(
                            binding.adapter,  # type: ignore[arg-type]
                            sojourner_id,
                            turn_id=_post_writer_turn_id,
                        ),
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
            except Exception as exc:  # noqa: BLE001 — see boundary docstring
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"output safety unexpected error: {exc}",
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
        _scoped_post_writer = ScopedProviderAdapter(
            binding.adapter,  # type: ignore[arg-type]
            sojourner_id,
            turn_id=writer_result.turn_id,
        )
        try:
            (
                extractor_result,
                contradiction_result,
                ext_ms,
                contr_ms,
            ) = self._run_parallel_sync(
                ctx, writer_result, story_id, session, _scoped_post_writer
            )
            latency["extractor"] = ext_ms
            latency["contradiction"] = contr_ms
        except _ContradictionRefusalWithExtractor as exc:
            # Contradiction refused after Extractor succeeded — preserve the
            # already-completed extractor_result per the refusal contract
            # ("upstream results preserved; only the failing pass result is
            # absent").  The outer transaction still rolls back because the
            # disposition is REFUSED_BY_PROVIDER, not the success disposition.
            return self._build_result(
                PipelineDisposition.REFUSED_BY_PROVIDER,
                intent_result,
                latency,
                turn_start,
                input_safety_result=input_safety,
                planner_result=planner_result,
                writer_result=writer_result,
                output_safety_result=output_safety,
                extractor_result=exc.extractor_result,
                provider_refusal=exc.refusal,
            )
        except ProviderRefusalError as exc:
            # Extractor-side refusal: the failing pass result must remain
            # absent so the OrchestrationResult invariant
            # ("failing pass result must be None on REFUSED_BY_PROVIDER") holds.
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
        except Exception as exc:  # noqa: BLE001 — see boundary docstring
            # Defense-in-depth: ``_run_parallel_sync`` already maps every
            # known typed failure inside its body, but any unexpected
            # exception from helpers around it (e.g. an executor shutdown
            # in the finally) still must not escape the orchestrator raw.
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"parallel sync unexpected error: {exc}",
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
            rpg_adjudication_result=adj_result,
            rpg_visible_state=rpg_visible_state,
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
        sojourner_id: UUID,
        intent_result: IntentClassificationResult,
        binding: TurnProviderBinding,
        latency: dict[str, int],
        turn_start: float,
        request_risk_signal: bool,
    ) -> OrchestrationResult:
        input_safety: SafetyResult | None = None
        preflight_ctx = SafetyPolicyContext(
            eligible_writer_routes=binding.eligible_writer_routes,
            request_risk_signal=request_risk_signal,
            access_path=binding.access_path,
        )
        if self._safety_policy.should_run_input_preflight(preflight_ctx):
            try:
                input_safety, ms = _timed(
                    lambda: self._safety_service.check(
                        ctx,
                        ctx.volatile_suffix.current_input,
                        SafetyTarget.INPUT,
                        provider=ScopedProviderAdapter(binding.adapter, sojourner_id),  # type: ignore[arg-type]
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
            except Exception as exc:  # noqa: BLE001 — see boundary docstring
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"input safety unexpected error: {exc}",
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

        return self._run_with_transaction(
            lambda session: self._ooc_persist(
                session,
                ooc_ctx,
                story_id,
                node_id,
                sojourner_id,
                intent_result,
                input_safety,
                binding,
                request_risk_signal,
                latency,
                turn_start,
            ),
            intent_result,
            latency,
            turn_start,
            success_disposition=PipelineDisposition.OOC_HANDLED,
            pre_transaction_fn=binding.pre_transaction_fn,
            post_transaction_fn=binding.post_transaction_fn,
        )

    def _ooc_persist(
        self,
        session: Session,
        ooc_ctx: AssembledContext,
        story_id: UUID,
        node_id: UUID,
        sojourner_id: UUID,
        intent_result: IntentClassificationResult,
        input_safety: SafetyResult | None,
        binding: TurnProviderBinding,
        request_risk_signal: bool,
        latency: dict[str, int],
        turn_start: float,
    ) -> OrchestrationResult:
        ooc_turn_id = uuid4()
        try:
            writer_result, ms = _timed(
                lambda: self._writer_service.write(
                    ooc_ctx,
                    story_id,
                    node_id,
                    provider=ScopedProviderAdapter(
                        binding.adapter,  # type: ignore[arg-type]
                        sojourner_id,
                        turn_id=ooc_turn_id,
                    ),
                    session=session,
                    turn_id=ooc_turn_id,
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
        except Exception as exc:  # noqa: BLE001 — see boundary docstring
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"ooc writer unexpected error: {exc}",
                input_safety_result=input_safety,
            )

        output_safety: SafetyResult | None = None
        audit_ctx = SafetyPolicyContext(
            eligible_writer_routes=binding.eligible_writer_routes,
            request_risk_signal=request_risk_signal,
            access_path=binding.access_path,
            writer_result=writer_result,
        )
        if self._safety_policy.should_run_output_audit(audit_ctx):
            _ooc_post_writer_turn_id = writer_result.turn_id
            try:
                output_safety, ms = _timed(
                    lambda: self._safety_service.check(
                        ooc_ctx,
                        writer_result.assistant_output,
                        SafetyTarget.OUTPUT,
                        provider=ScopedProviderAdapter(
                            binding.adapter,  # type: ignore[arg-type]
                            sojourner_id,
                            turn_id=_ooc_post_writer_turn_id,
                        ),
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
            except Exception as exc:  # noqa: BLE001 — see boundary docstring
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"output safety unexpected error: {exc}",
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
        provider: ProviderAdapter,
    ) -> tuple[ExtractorResult, ContradictionResult, int, int]:
        """Run Extractor synchronously and Contradiction on a worker thread.

        Asymmetric by design: Contradiction has no DB I/O so worker-thread
        execution is safe; Extractor writes via the orchestrator-owned
        session under a SAVEPOINT, so it MUST run on the orchestrator
        thread to avoid sharing the session across threads (Issue 12c
        invariant).

        Returns Extractor and Contradiction results plus their individual
        latencies in milliseconds.  Raises:
          - ``ProviderRefusalError`` if Extractor refuses (the failing pass
            result must stay absent on the resulting REFUSED_BY_PROVIDER).
          - ``_ContradictionRefusalWithExtractor`` if Contradiction refuses
            AFTER Extractor completed successfully, so the caller can
            preserve the upstream ``extractor_result`` on the resulting
            REFUSED_BY_PROVIDER per the refusal contract.
          - ``_ParallelSyncError`` for any other operational failure: an
            extractor pass error, a contradiction pass error, a worker
            timeout, or a contradiction worker submission failure (e.g.
            an injected executor that has already been shut down).
          - In every case the caller is responsible for rolling back the
            outer transaction.

        Executor lifecycle (Codex P1 round 8):
          - The orchestrator-owned executor (``self._owned_executor``) is
            a single bounded ``ThreadPoolExecutor`` created in
            ``__init__`` with ``max_workers=parallel_pass_max_workers``.
            It is reused across every turn and lives until ``close()``.
            Per-turn ``submit()`` queues a fresh future; on timeout the
            orchestrator calls ``future.cancel()`` (which cancels
            queued-not-started work but cannot interrupt a running
            provider call).  Total live contradiction workers are
            therefore bounded by ``max_workers`` — repeated timeouts
            against a slow provider cannot accumulate workers without
            bound (the prior per-turn local executor + ``shutdown(wait=
            False, cancel_futures=True)`` design bounded request wall
            time correctly but did not cap worker accumulation).
          - When ``self._provided_executor`` was injected the caller
            owns the executor's lifecycle; the orchestrator never calls
            ``shutdown`` on it.
        """
        executor: ThreadPoolExecutor = (
            self._provided_executor
            if self._provided_executor is not None
            else self._owned_executor  # type: ignore[assignment]
        )
        # ``executor.submit`` itself can raise — most commonly
        # ``RuntimeError("cannot schedule new futures after shutdown")``
        # when an injected executor was already shut down by the caller,
        # or when ``close()`` was called on this orchestrator and a turn
        # is still in flight.  That must NOT escape the orchestrator: the
        # terminal-state contract requires a typed PIPELINE_ERROR, so we
        # wrap any submission failure into ``_ParallelSyncError`` which
        # the caller already maps to PIPELINE_ERROR + outer-txn rollback.
        contradiction_future: Future[tuple[ContradictionResult, int]]
        try:
            contradiction_future = executor.submit(
                _timed_for_thread,
                lambda: self._contradiction_service.check(
                    ctx, writer_result.assistant_output, provider=provider
                ),
            )
        except Exception as exc:  # noqa: BLE001
            raise _ParallelSyncError(
                f"contradiction worker submission failed: {exc}"
            ) from exc

        # Extractor on this thread, under SAVEPOINT inside the outer txn.
        try:
            extractor_result, ext_ms = _timed(
                lambda: self._extractor_service.extract(
                    ctx,
                    writer_result.assistant_output,
                    story_id,
                    writer_result.turn_id,
                    provider=provider,
                    session=session,
                )
            )
        except ProviderRefusalError:
            # Best-effort cancel of the contradiction future: succeeds only
            # if the future has not started yet (the bounded executor may
            # have already promoted it onto a worker thread).  Running
            # work continues until natural completion — it cannot be
            # interrupted — but holds at most one of the executor's
            # ``max_workers`` slots and performs no DB I/O.
            #
            # Extractor refusal must NOT propagate any partial Extractor
            # state: the refusal contract's "failing pass result absent"
            # invariant applies here, so we re-raise the plain
            # ``ProviderRefusalError`` rather than the
            # ``_ContradictionRefusalWithExtractor`` wrapper used for
            # the contradiction-refusal-after-extractor-success case.
            contradiction_future.cancel()
            raise
        except ExtractorPassError as exc:
            contradiction_future.cancel()
            raise _ParallelSyncError(f"extractor: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 — see boundary docstring
            # Unexpected non-typed exception from Extractor (e.g. a
            # transport error, a serialization bug, a SQLAlchemy write
            # surface).  Convert to ``_ParallelSyncError`` so the
            # narrative caller already maps it to PIPELINE_ERROR with
            # the cause text and rolls back the outer transaction.
            # ``BaseException`` is NOT caught.
            contradiction_future.cancel()
            raise _ParallelSyncError(f"extractor unexpected error: {exc}") from exc

        try:
            contradiction_result, contr_ms = contradiction_future.result(
                timeout=self._timeout
            )
        except FutureTimeout as exc:
            # Cancel the future so a queued-but-not-started worker is
            # released back to the executor pool (already-running work
            # cannot be interrupted and will run to natural completion).
            # The orchestrator returns PIPELINE_ERROR promptly here; the
            # bounded executor caps total live workers at ``max_workers``
            # so repeated timeouts against a slow provider cannot
            # accumulate workers without bound.
            contradiction_future.cancel()
            raise _ParallelSyncError(
                f"contradiction worker exceeded {self._timeout:.1f}s timeout"
            ) from exc
        except ProviderRefusalError as exc:
            # Contradiction refused AFTER Extractor completed
            # successfully.  The refusal contract says upstream pass
            # results are preserved on REFUSED_BY_PROVIDER; only the
            # failing pass result is absent.  Carry the completed
            # ``extractor_result`` through the refusal path via a
            # private wrapper so the narrative caller can populate it
            # on the resulting OrchestrationResult.
            raise _ContradictionRefusalWithExtractor(
                exc.refusal, extractor_result
            ) from exc
        except ContradictionPassError as exc:
            raise _ParallelSyncError(f"contradiction: {exc}") from exc
        except CancelledError as exc:
            # ``concurrent.futures.CancelledError`` subclasses
            # ``BaseException`` (Python 3.8+) so it would slip past
            # ``except Exception`` below.  Handle it explicitly so a
            # cancelled contradiction future still maps to a typed
            # PIPELINE_ERROR rather than escaping raw.
            contradiction_future.cancel()
            raise _ParallelSyncError(f"contradiction worker cancelled: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 — see boundary docstring
            # Catch-all for anything else the contradiction worker may
            # surface through the future: a generic ``RuntimeError`` from
            # the injected model caller, a transport error, an unexpected
            # ``ValueError`` from downstream serialization, etc.  Mapped
            # to PIPELINE_ERROR per the orchestrator's exhaustive
            # terminal-state contract; specific typed branches above
            # remain authoritative for their categories.  ``BaseException``
            # is NOT caught so ``KeyboardInterrupt`` / ``SystemExit``
            # propagate and the host process can shut down cleanly.
            contradiction_future.cancel()
            raise _ParallelSyncError(f"contradiction worker failed: {exc}") from exc

        return extractor_result, contradiction_result, ext_ms, contr_ms

    # ------------------------------------------------------------------
    # RPG audit persistence
    # ------------------------------------------------------------------

    def _write_rpg_audit(
        self,
        session: Session,
        adj_result: AdjudicationPassResult,
        turn_id: UUID,
        story_id: UUID,
        session_id: UUID,
        character_id: UUID,
        *,
        pending_roll_consumed: PendingRollRequest | None = None,
    ) -> None:
        """Write adjudication audit rows inside the outer transaction (Fork B→B1).

        Writes one ``RpgRollAuditORM`` row per resolved proposal.
        On the consume path: calls ``mark_consumed`` to update the consumed row.
        On the announce path: calls ``check_no_pending_for_story`` (duplicate
        rejection) then writes one ``PendingRollRequestORM``.
        All writes are rolled back atomically with the Turn on any block.

        Raises:
            PendingRollDuplicateError: if an active pending roll exists when
                this turn is attempting to announce a new one.
        """
        from datetime import UTC, datetime

        from afterworlds.persistence.orm.rpg import (
            PendingRollRequestORM,
            RpgRollAuditORM,
        )

        now_str = datetime.now(tz=UTC).isoformat()

        # Consume path: mark the consumed pending roll before writing audit rows.
        if (
            pending_roll_consumed is not None
            and self._rpg_pending_roll_service is not None
        ):
            self._rpg_pending_roll_service.mark_consumed(
                session, pending_roll_consumed.request_id, turn_id
            )

        for record in adj_result.proposals:
            session.add(
                RpgRollAuditORM(
                    turn_id=str(turn_id),
                    story_id=str(story_id),
                    session_id=str(session_id),
                    character_id=str(character_id),
                    check_label=record.check_label,
                    visibility=record.visibility.value,
                    expression=record.expression,
                    raw_rolls_json=json.dumps(list(record.raw_rolls)),
                    modifiers_json=record.modifiers_json,
                    total=record.total,
                    dc=record.dc,
                    outcome=record.outcome,
                    source=record.source,
                    gm_cheating_at_roll=record.gm_cheating_at_roll,
                    sheet_effects_json=json.dumps(
                        [e.model_dump() for e in record.sheet_effects]
                    ),
                    created_at=now_str,
                )
            )

        # Announce path: duplicate rejection before writing the new row.
        pending = adj_result.pending_roll_request
        if pending is not None:
            if self._rpg_pending_roll_service is not None:
                self._rpg_pending_roll_service.check_no_pending_for_story(
                    session, story_id
                )
            session.add(
                PendingRollRequestORM(
                    request_id=str(pending.request_id),
                    story_id=str(pending.story_id),
                    session_id=str(pending.session_id),
                    character_id=str(pending.character_id),
                    originating_turn_id=str(turn_id),
                    check_label=pending.check_label,
                    player_facing_instruction=pending.player_facing_instruction,
                    expected_value_shape=pending.expected_value_shape,
                    visible_modifier_note=pending.visible_modifier_note,
                    visibility=pending.visibility.value,
                    source_proposal_ref=pending.source_proposal_ref,
                    status="pending",
                    schema_version=1,
                    roll_expression=pending.roll_expression,
                    visible_modifier_total=pending.visible_modifier_total,
                    visible_modifier_breakdown_json=pending.visible_modifier_breakdown_json,
                    hidden_modifier_present=pending.hidden_modifier_present,
                    adapter_context_hash=pending.adapter_context_hash,
                    created_at=now_str,
                )
            )

    # ------------------------------------------------------------------
    # RPG sheet-effect application (Fork B→B1)
    # ------------------------------------------------------------------

    def _apply_rpg_sheet_effects(
        self,
        session: Session,
        effects: tuple[SheetEffect, ...],
        sheet: Dnd5eCharacterSheet,
    ) -> Dnd5eCharacterSheet:
        """Apply sheet effects to the character sheet inside the outer transaction.

        Supports delta/set for current_hp and spell_slot.<N>, plus
        apply_condition and clear_condition against active_conditions.
        Unknown or ambiguous targets fail closed (raise ValueError).
        Callers must handle exceptions and return a pipeline error so the
        outer transaction rolls back Turn + audit rows + mutations atomically.
        """
        import json as _json
        from datetime import UTC, datetime

        from afterworlds.models.character_sheet import (
            Dnd5eActiveCondition,
            Dnd5eCharacterSheet,
            SpellSlotLevel,
        )
        from afterworlds.persistence.crud.character_sheet import update_dnd5e_sheet

        new_current_hp = sheet.current_hp
        new_spell_slots: dict[int, SpellSlotLevel] = dict(sheet.spell_slots)
        new_conditions: list[Dnd5eActiveCondition] = list(sheet.active_conditions)

        for effect in effects:
            value = _json.loads(effect.value_json)

            if effect.operation in ("delta", "set"):
                if effect.target == "current_hp":
                    int_val = int(value)
                    if effect.operation == "delta":
                        new_current_hp = max(
                            0, min(sheet.maximum_hp, new_current_hp + int_val)
                        )
                    else:
                        new_current_hp = max(0, min(sheet.maximum_hp, int_val))
                elif effect.target.startswith("spell_slot."):
                    level_str = effect.target.removeprefix("spell_slot.")
                    if not level_str.isdigit():
                        raise ValueError(
                            f"Unknown sheet-effect target: {effect.target!r}"
                        )
                    slot_level = int(level_str)
                    if slot_level not in new_spell_slots:
                        raise ValueError(
                            f"Unknown sheet-effect target: {effect.target!r}"
                            f" — no spell slot level {slot_level}"
                        )
                    slot = new_spell_slots[slot_level]
                    int_val = int(value)
                    if effect.operation == "delta":
                        new_used = max(0, min(slot.total, slot.used + int_val))
                    else:
                        new_used = max(0, min(slot.total, int_val))
                    new_spell_slots[slot_level] = SpellSlotLevel(
                        total=slot.total, used=new_used
                    )
                else:
                    raise ValueError(f"Unknown sheet-effect target: {effect.target!r}")

            elif effect.operation == "apply_condition":
                if not isinstance(value, dict):
                    raise ValueError("apply_condition value_json must be a JSON object")
                cond_data = {**value, "sheet_id": str(sheet.sheet_id)}
                cond_data.setdefault("condition_id", str(__import__("uuid").uuid4()))
                condition = Dnd5eActiveCondition.model_validate(cond_data)
                new_conditions.append(condition)

            elif effect.operation == "clear_condition":
                if not isinstance(value, dict):
                    raise ValueError("clear_condition value_json must be a JSON object")
                identifier_to_clear = value.get("identifier")
                if not identifier_to_clear:
                    raise ValueError(
                        "clear_condition value_json must contain 'identifier'"
                    )
                new_conditions = [
                    c for c in new_conditions if c.identifier != identifier_to_clear
                ]

            else:
                raise ValueError(
                    f"Unknown sheet-effect operation: {effect.operation!r}"
                )

        mutated = Dnd5eCharacterSheet.model_validate(
            {
                **sheet.model_dump(mode="json"),
                "current_hp": new_current_hp,
                "spell_slots": {k: v.model_dump() for k, v in new_spell_slots.items()},
                "active_conditions": [c.model_dump() for c in new_conditions],
                "updated_at": datetime.now(tz=UTC).isoformat(),
            }
        )
        result = update_dnd5e_sheet(session, mutated)
        if result is None:
            raise ValueError(
                f"Sheet {sheet.sheet_id!r} not found during effect application"
            )
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_context(
        self,
        story_id: UUID,
        user_input: str,
        intent_result: IntentClassificationResult,
    ) -> tuple[AssembledContext, StoryMode, int]:
        mode: StoryMode = self._mode_resolver(story_id)
        ctx, ms = _timed(
            lambda: self._context_builder.assemble(
                story_id=story_id,
                mode=mode,
                current_input=user_input,
                classified_intent=intent_result,
            )
        )
        return ctx, mode, ms

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
        rpg_adjudication_result: AdjudicationPassResult | None = None,
        rpg_visible_state: RpgVisibleState | None = None,
        provider_refusal: ProviderRefusal | None = None,
        pipeline_error_summary: str | None = None,
        pending_roll_redirect_message: str | None = None,
    ) -> OrchestrationResult:
        total_ms = max(0, int((time.perf_counter() - turn_start) * 1000))
        cache_warmed = _any_cache_read(
            input_safety_result,
            planner_result,
            writer_result,
            output_safety_result,
            extractor_result,
            contradiction_result,
        )
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
            rpg_adjudication_result=rpg_adjudication_result,
            rpg_visible_state=rpg_visible_state,
            provider_refusal=provider_refusal,
            pipeline_error_summary=pipeline_error_summary,
            pending_roll_redirect_message=pending_roll_redirect_message,
            total_latency_ms=total_ms,
            pass_latency_breakdown=dict(latency),
            stable_prefix_cache_warmed=cache_warmed,
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

    def _run_with_transaction(
        self,
        inner: Callable[[Session], OrchestrationResult],
        intent_result: IntentClassificationResult,
        latency: dict[str, int],
        turn_start: float,
        *,
        success_disposition: PipelineDisposition,
        pre_transaction_fn: Callable[[], None] = _noop_fn,
        post_transaction_fn: Callable[[], None] = _noop_fn,
    ) -> OrchestrationResult:
        """Run ``inner`` under a fresh session + outer transaction.

        Centralizes every session-lifecycle operation so the narrative and
        OOC wrappers cannot drift and so the orchestrator's exhaustive
        typed-terminal-state contract holds across the entire lifecycle.
        Each lifecycle hook is mapped explicitly:

        - ``self._session_factory()`` raises → PIPELINE_ERROR with the
          underlying cause text preserved.  No session was created, so no
          cleanup is attempted.
        - ``session.begin()`` raises → PIPELINE_ERROR with the underlying
          cause text preserved.  A session exists but no transaction was
          opened, so cleanup only calls ``close()`` (never ``rollback()``).
        - ``inner(session)`` returns a typed result → ``_finalize_transaction``
          decides commit vs rollback per the success disposition; commit
          failure is mapped to PIPELINE_ERROR there.
        - ``inner(session)`` raises ``BaseException`` → best-effort
          rollback then reraise.  This preserves the historical contract
          for genuinely unexpected escapes (including ``KeyboardInterrupt``
          and ``SystemExit``) while keeping the typed-result path for
          everything the inner explicitly catches.
        - ``session.close()`` raises during cleanup → suppressed.  Close
          is a cleanup operation; the typed ``OrchestrationResult`` is the
          boundary contract and must not be silently replaced by a raw
          cleanup exception.  Same rationale applies to the rollback in
          the BaseException branch and inside ``_finalize_transaction``.
        """
        try:
            session = self._session_factory()
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"session factory failed: {exc}",
            )
        try:
            pre_transaction_fn()
            try:
                session.begin()
            except Exception as exc:  # noqa: BLE001
                # No transaction was opened; only ``close()`` runs in the
                # outer finally.  rollback() must NOT be attempted because
                # ``session.in_transaction()`` would be False and calling
                # rollback() on a non-transactional session can itself fail.
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"session begin failed: {exc}",
                )
            try:
                inner_result = inner(session)
            except BaseException:
                if session.in_transaction():
                    with suppress(Exception):
                        session.rollback()
                raise
            return self._finalize_transaction(
                session,
                inner_result,
                intent_result,
                latency,
                turn_start,
                success_disposition=success_disposition,
            )
        finally:
            with suppress(Exception):
                session.close()
            with suppress(Exception):
                post_transaction_fn()

    def _finalize_transaction(
        self,
        session: Session,
        inner_result: OrchestrationResult,
        intent_result: IntentClassificationResult,
        latency: dict[str, int],
        turn_start: float,
        *,
        success_disposition: PipelineDisposition,
    ) -> OrchestrationResult:
        """Apply the post-pipeline commit/rollback decision in one place.

        Centralized so the narrative and OOC wrappers cannot drift on the
        commit policy or on commit-failure handling.

        Policy:
          - ``inner_result.disposition`` matches ``success_disposition`` and
            the session is still in a transaction → try ``session.commit()``.

            - Commit succeeds → return ``inner_result`` unchanged.
            - Commit raises → best-effort rollback, return a typed
              ``PIPELINE_ERROR`` result that preserves the already-
              completed pass results (planner, writer, extractor,
              contradiction, both Safety results) but explicitly drops
              ``delivered_output`` and ``turn_id``.  The Turn write and
              any Extractor SAVEPOINT writes were rolled back, so the
              candidate result's surviving-row claim is no longer true.
              The underlying cause text is preserved in
              ``pipeline_error_summary``.

          - Any other disposition (Safety BLOCK, Contradiction BLOCK,
            refusal, pipeline error from a pass, …) → best-effort rollback
            if the session is still in a transaction, then return the
            inner result unchanged.

        ``session.in_transaction()`` is checked before every operation so
        this remains idempotent even when a downstream pass already rolled
        the transaction back.  ``session.rollback()`` is wrapped in
        ``suppress(Exception)`` because the contract for this method is
        "return a typed result, never raise" — a rollback that itself
        fails must not propagate.
        """
        if inner_result.disposition is success_disposition and session.in_transaction():
            try:
                session.commit()
            except Exception as commit_exc:  # noqa: BLE001
                # Commit failed AFTER nominal pipeline success.  The Turn
                # write and Extractor SAVEPOINT writes did not survive,
                # so the candidate result's ``delivered_output`` and
                # ``turn_id`` cannot stand; the post-pipeline diagnostic
                # is PIPELINE_ERROR with the completed pass results
                # preserved for observability.
                if session.in_transaction():
                    with suppress(Exception):
                        session.rollback()
                return self._build_result(
                    PipelineDisposition.PIPELINE_ERROR,
                    intent_result,
                    latency,
                    turn_start,
                    input_safety_result=inner_result.input_safety_result,
                    planner_result=inner_result.planner_result,
                    writer_result=inner_result.writer_result,
                    output_safety_result=inner_result.output_safety_result,
                    extractor_result=inner_result.extractor_result,
                    contradiction_result=inner_result.contradiction_result,
                    rpg_adjudication_result=inner_result.rpg_adjudication_result,
                    pipeline_error_summary=(
                        f"transaction commit failed after "
                        f"{success_disposition.value}: {commit_exc}"
                    ),
                )
            return inner_result

        if session.in_transaction():
            with suppress(Exception):
                session.rollback()
        return inner_result


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class _ParallelSyncError(Exception):
    """Operational failure during the Extractor || Contradiction stage.

    Raised by ``_run_parallel_sync`` for non-refusal failures: extractor
    operational error, contradiction operational error, contradiction
    worker timeout, or contradiction worker submission failure.  The caller
    maps this to ``PIPELINE_ERROR``.
    """


class _ContradictionRefusalWithExtractor(Exception):
    """Contradiction refused AFTER Extractor completed successfully.

    Internal-only carrier raised by ``_run_parallel_sync`` so the narrative
    caller can populate the already-completed ``extractor_result`` on the
    resulting REFUSED_BY_PROVIDER.  The refusal contract preserves upstream
    pass results; only the failing pass result is absent.  Extractor-side
    refusal continues to raise plain ``ProviderRefusalError`` because the
    failing pass there IS Extractor.
    """

    def __init__(
        self, refusal: ProviderRefusal, extractor_result: ExtractorResult
    ) -> None:
        super().__init__(
            f"contradiction refused after extractor success: {refusal.coarse_reason}"
        )
        self.refusal = refusal
        self.extractor_result = extractor_result


def _any_cache_read(
    *results: object,
) -> bool:
    """Return True if any result reports a non-zero cache_read_token_count."""
    for r in results:
        if r is None:
            continue
        count = getattr(r, "cache_read_token_count", None)
        if isinstance(count, int) and count > 0:
            return True
    return False


def _timed[T](fn: Callable[[], T]) -> tuple[T, int]:
    start = time.perf_counter()
    result = fn()
    elapsed_ms = max(0, int((time.perf_counter() - start) * 1000))
    return result, elapsed_ms


def _timed_for_thread[T](fn: Callable[[], T]) -> tuple[T, int]:
    """Worker-thread variant of ``_timed`` (identical semantics)."""
    return _timed(fn)


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


def _serialize_adj_views(adj_result: AdjudicationPassResult) -> str:
    """Serialize adjudication writer views for the pass-forward ledger.

    Produces a JSON string that the Writer pass reads from the ledger key
    ``"rpg_adjudication"``.  The ``pending_player_roll_instruction`` field is
    included only when the result carries a PLAYER-roll announce so the Writer
    can prompt the Sojourner to roll physical dice.
    """
    views_data = [json.loads(v.model_dump_json()) for v in adj_result.writer_views]
    pending_instruction: str | None = None
    if adj_result.pending_roll_request is not None:
        pending_instruction = adj_result.pending_roll_request.player_facing_instruction
    return json.dumps(
        {"views": views_data, "pending_player_roll_instruction": pending_instruction},
        sort_keys=True,
    )


def _default_mode_resolver(
    session_factory: Callable[[], Session],
) -> ModeResolver:
    """Default mode resolver: SQLite lookup against the stories table."""
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
