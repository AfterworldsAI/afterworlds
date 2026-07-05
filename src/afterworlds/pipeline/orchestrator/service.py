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
import logging
import time
from collections.abc import Callable
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import RuntimeAccessPath
from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    StablePrefix,
)
from afterworlds.models.enums import (
    BranchingPlayStatus,
    IntentType,
    InteractionRejectionReason,
    InteractionStyle,
    RpgPlayStatus,
    StoryMode,
    WritingCanonEligibility,
    WritingForm,
    WritingPlayStatus,
    WritingWorkProductKind,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.retrieval import RetrievalQueryRequest
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.pipeline._refusal import (
    ProviderRefusal,
    ProviderRefusalError,
)
from afterworlds.pipeline.branching.models import (
    BranchingOocExtractionUsageError,
    BranchingPassError,
)
from afterworlds.pipeline.branching.models import (
    BranchingPassResult as _BranchingPassResult,
)
from afterworlds.pipeline.rpg.models import AdjudicationPassError
from afterworlds.pipeline.rpg.pending import PendingRollDuplicateError
from afterworlds.pipeline.writing.models import WritingOocExtractionUsageError

if TYPE_CHECKING:
    from afterworlds.models.character_sheet import Dnd5eCharacterSheet
    from afterworlds.models.rpg import PendingRollRequest, RpgVisibleState, SheetEffect
    from afterworlds.models.session import (
        BranchingSessionState,
        RpgSessionState,
        WritingSessionState,
    )
    from afterworlds.pipeline.branching.models import (
        SelectedBranchContext,
    )
    from afterworlds.pipeline.branching.ooc_config_extractor import (
        BranchingOocConfigExtractorService,
    )
    from afterworlds.pipeline.branching.selection import (
        BranchSelectionValidationService,
    )
    from afterworlds.pipeline.branching.service import BranchingWriterService
    from afterworlds.pipeline.branching.visible_state import (
        BranchingVisibleStateService,
    )
    from afterworlds.pipeline.rpg.dice import DiceService
    from afterworlds.pipeline.rpg.models import AdjudicationPassResult
    from afterworlds.pipeline.rpg.pending import PendingRollRequestService
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from afterworlds.pipeline.rpg.visible_state import RpgVisibleStateService
    from afterworlds.pipeline.writing.models import WritingTurnRequest
    from afterworlds.pipeline.writing.ooc_config_extractor import (
        WritingOocConfigExtractorService,
    )
    from afterworlds.pipeline.writing.visible_state import WritingVisibleStateService
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

logger = logging.getLogger(__name__)

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

#: Intent types for which the Context Builder will use a ``RuleSliceRequest``
#: to include mechanical-rule content in the stable prefix.  Matches the gate
#: inside ``ContextBuilderService.build_stable_prefix()``.
_ADJUDICATING_INTENT_TYPES: frozenset[IntentType] = frozenset(
    {
        IntentType.IN_CHARACTER_ACTION,
        IntentType.DIALOGUE,
        IntentType.LORE_QUESTION,
    }
)


# ---------------------------------------------------------------------------
# OOC handler prompt loading
# ---------------------------------------------------------------------------

_PROMPT_DIR: Path = Path(__file__).parents[4] / "docs" / "prompts"


def load_ooc_handler_prompt() -> str:
    """Load the v1 OOC handler instruction from docs/prompts/ooc_handler.md."""
    prompt_path = _PROMPT_DIR / "ooc_handler.md"
    return prompt_path.read_text(encoding="utf-8")


def load_rpg_ooc_handler_prompt() -> str:
    """Load the RPG-mode OOC handler from docs/prompts/rpg_ooc_handler.md."""
    prompt_path = _PROMPT_DIR / "rpg_ooc_handler.md"
    return prompt_path.read_text(encoding="utf-8")


def load_branching_ooc_handler_prompt() -> str:
    """Load the Branching-mode OOC handler from docs/prompts/branching_ooc_handler.md."""  # noqa: E501
    prompt_path = _PROMPT_DIR / "branching_ooc_handler.md"
    return prompt_path.read_text(encoding="utf-8")


def load_writing_ooc_handler_prompt() -> str:
    """Load the Writing-mode OOC handler from docs/prompts/writing_ooc_handler.md."""
    prompt_path = _PROMPT_DIR / "writing_ooc_handler.md"
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
# Retrieval Memory ingestion seam (CRD Issue 18 / ADR-018 D6/D7)
# ---------------------------------------------------------------------------


class RetrievalIngestionServiceLike(Protocol):
    """Narrow protocol for the retrieval-memory write path.

    The orchestrator depends only on this shape, not on
    ``RetrievalMemoryWriteService`` or ChromaDB directly — mirrors the
    ``_RulesPackageServiceLike``-style narrow protocols in
    ``services/context_builder.py``.
    """

    def ingest_turn(
        self,
        story_id: UUID,
        turn_id: UUID,
        node_id: UUID | None,
        mode: str,
        delivered_output: str,
        created_at: str,
    ) -> None: ...


class RetrievalQueryBuilderLike(Protocol):
    """Narrow protocol for ``pipeline.retrieval.query_builder.RetrievalQueryBuilder``."""  # noqa: E501

    def build_query_request(
        self, story_id: UUID, current_input: str, story_mode: StoryMode
    ) -> RetrievalQueryRequest: ...


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
        branching_writer_service: BranchingWriterService | None = None,
        branching_session_resolver: (
            Callable[[UUID], BranchingSessionState | None] | None
        ) = None,
        branching_visible_state_service: BranchingVisibleStateService | None = None,
        branching_selection_service: BranchSelectionValidationService | None = None,
        branching_ooc_config_extractor: (
            BranchingOocConfigExtractorService | None
        ) = None,
        writing_session_resolver: (
            Callable[[UUID], WritingSessionState | None] | None
        ) = None,
        writing_visible_state_service: WritingVisibleStateService | None = None,
        writing_ooc_config_extractor: WritingOocConfigExtractorService | None = None,
        retrieval_write_service: RetrievalIngestionServiceLike | None = None,
        retrieval_query_builder: RetrievalQueryBuilderLike | None = None,
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
        self._branching_writer_service = branching_writer_service
        self._branching_session_resolver = branching_session_resolver
        self._branching_visible_state_service = branching_visible_state_service
        self._branching_selection_service = branching_selection_service
        self._branching_ooc_config_extractor = branching_ooc_config_extractor
        self._writing_session_resolver = writing_session_resolver
        self._writing_visible_state_service = writing_visible_state_service
        self._writing_ooc_config_extractor = writing_ooc_config_extractor
        self._retrieval_write_service = retrieval_write_service
        self._retrieval_query_builder = retrieval_query_builder
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
        self._rpg_ooc_handler_prompt: str = load_rpg_ooc_handler_prompt()
        self._branching_ooc_handler_prompt: str = load_branching_ooc_handler_prompt()
        self._writing_ooc_handler_prompt: str = load_writing_ooc_handler_prompt()

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
        writing_turn_request: WritingTurnRequest | None = None,
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

        # 2. Early mode resolution (P2-2: must happen before context assembly so
        # we know whether to build a RuleSliceRequest for the stable prefix).
        try:
            story_mode: StoryMode = self._mode_resolver(story_id)
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                intent_result, latency, turn_start, f"mode resolution failed: {exc}"
            )

        # 2a. For RPG adjudicating intents with adjudication wired, resolve
        # session/sheet early so the RuleSliceRequest can be built before
        # context assembly (stable-prefix-once invariant: context is built
        # exactly once, with the rule slice already determined).
        rule_slice_request: RuleSliceRequest | None = None
        pre_session_state: RpgSessionState | None = None
        pre_sheet: Dnd5eCharacterSheet | None = None
        if (
            story_mode is StoryMode.RPG
            and intent_result.intent_type in _ADJUDICATING_INTENT_TYPES
            and self._rpg_adjudication_service is not None
        ):
            if self._rpg_session_sheet_resolver is None:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "RPG adjudication wired without session/sheet resolver",
                )
            try:
                pre_session_state, pre_sheet = self._rpg_session_sheet_resolver(
                    story_id
                )
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"RPG session/sheet resolution failed: {exc}",
                )
            # Only build a rule slice for IN_PLAY sessions; setup turns do not
            # run adjudication so the context builder does not need the slice.
            if pre_session_state.play_status is RpgPlayStatus.IN_PLAY:
                try:
                    _pkg_uuid = UUID(pre_sheet.rules_package_id)
                    rule_slice_request = RuleSliceRequest(package_id=_pkg_uuid)
                except ValueError:
                    # Non-UUID binding (slug) — omit request; adjudication
                    # proceeds without a rule slice and produces "undetermined".
                    rule_slice_request = None

        # 2a-retrieval. Build the retrieval query request before context
        # assembly (ADR-018 D8) — orchestrator-owned and deterministic,
        # mirroring the RuleSliceRequest pattern above. Best-effort: a
        # query-build failure must not fail the turn, only omit retrieval
        # memory for it (same as the Null-provider empty-payload behavior).
        retrieval_query_request: RetrievalQueryRequest | None = None
        if self._retrieval_query_builder is not None:
            try:
                retrieval_query_request = (
                    self._retrieval_query_builder.build_query_request(
                        story_id, user_input, story_mode
                    )
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "retrieval query build failed for story_id=%s: %s",
                    story_id,
                    exc,
                )

        # 2b. Context assembly (once per turn).
        try:
            ctx, _, ctx_ms = self._build_context(
                story_id,
                user_input,
                intent_result,
                mode=story_mode,
                rule_slice_request=rule_slice_request,
                retrieval_query_request=retrieval_query_request,
            )
            latency["context"] = ctx_ms
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                intent_result, latency, turn_start, f"context assembly failed: {exc}"
            )

        # 2c. Writing session pre-resolve and stable prefix extension (once per turn).
        # Must run after context assembly and before any pass so the persona fragment
        # is in the stable prefix that all passes share (Invariant 7).
        pre_writing_state: WritingSessionState | None = None
        if story_mode is StoryMode.WRITING:
            if self._writing_session_resolver is None:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "writing session resolver not wired for WRITING turn;"
                    " cannot determine play status or inject persona context",
                )
            try:
                pre_writing_state = self._writing_session_resolver(story_id)
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"writing session resolution failed: {exc}",
                )
            if pre_writing_state is None:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "writing session not found for story;"
                    " cannot determine play status or inject persona context",
                )
            # IN_PLAY turns require a configured persona present in the registry.
            # SETUP turns have no persona yet; the base mode contract handles setup.
            # (ADR-017 Decision 9: setup gating is via play_status check in code.)
            if pre_writing_state.play_status is WritingPlayStatus.IN_PLAY:
                if pre_writing_state.persona_id is None:
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        "writing IN_PLAY session has no persona_id;"
                        " persona must be configured before Writing output proceeds",
                    )
                if self._writing_visible_state_service is None:
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        "writing visible state service not wired for IN_PLAY turn;"
                        " cannot validate persona before Writing output proceeds",
                    )
                try:
                    from afterworlds.modes.personas.registry import (  # noqa: PLC0415
                        SupportedMode as _SM_W,
                    )

                    self._writing_visible_state_service.registry.get_profile(
                        pre_writing_state.persona_id, _SM_W.WRITING
                    )
                except (KeyError, ValueError) as exc:
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        f"writing IN_PLAY persona_id"
                        f" {pre_writing_state.persona_id!r}"
                        f" not found in registry: {exc}",
                    )
            # Extend stable prefix with persona fragment + authoring controls.
            # SETUP turns may have no persona yet; injection is best-effort and
            # render_context_appendix returns "" when persona_id is None.
            if self._writing_visible_state_service is not None:
                try:
                    _svc = self._writing_visible_state_service
                    _appendix = _svc.render_context_appendix(pre_writing_state)
                    if _appendix:
                        ctx = _extend_system_prompt(ctx, _appendix)
                except Exception:  # noqa: BLE001
                    pass  # best-effort; IN_PLAY persona was already validated above

        # P2-1: when player_reported_total is set in RPG mode the consume path
        # takes precedence over the OOC short-circuit — the player is reporting
        # the result of their physical roll, not asking an out-of-character
        # question, regardless of how the intent classifier classified the input.
        if story_mode is StoryMode.RPG and player_reported_total is not None:
            if self._rpg_pending_roll_service is None:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "player_reported_total provided but RPG pending-roll service"
                    " not wired",
                )
            try:
                _pending_for_consume = (
                    self._rpg_pending_roll_service.load_pending_for_story(story_id)
                )
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"pending roll lookup failed: {exc}",
                )
            if _pending_for_consume is None:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "player_reported_total provided but no pending roll found"
                    " for story",
                )
            # Fail closed: without adjudication, session/sheet resolver, and
            # dice service the pending roll cannot be validated, audited, or
            # applied — routing to narrative would silently bypass the consume
            # lifecycle.
            if (
                self._rpg_adjudication_service is None
                or self._rpg_session_sheet_resolver is None
                or self._rpg_dice_service is None
            ):
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "player_reported_total provided but RPG adjudication consume"
                    " path is not fully wired",
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
                pending_roll=_pending_for_consume,
                player_reported_total=player_reported_total,
                _pre_session_state=pre_session_state,
                _pre_sheet=pre_sheet,
            )

        # OOC short-circuit owns its own pipeline shape.
        # OOC-while-pending: the pending-roll intercept is deliberately skipped
        # for OOC turns — the pending roll waits while the player asks questions.
        # The P2-1 guard above ensures this only fires when player_reported_total
        # is None (i.e. the player is not reporting a roll total).
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
                story_mode=story_mode,
                pre_writing_state=pre_writing_state,
            )

        # Pending-roll intercept for RPG in-play narrative turns.
        # Runs before Planner so a block-redirect returns before any LLM call.
        # At this point player_reported_total is None (P2-1 handled the non-None
        # RPG case above).
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

        # Pre-resolve Branching session state once for INTERACTION_REJECTED check
        # and for the narrative path (HYBRID/TRUE_CYOA).  Modeled on the RPG
        # pre_session_state pattern: resolve once, thread through as _pre_branching_state.  # noqa: E501
        pre_branching_state: BranchingSessionState | None = None
        if story_mode is StoryMode.BRANCHING:
            # In-play interaction-style enforcement (TRUE_CYOA freeform
            # rejection, BRANCH_CHOICE validation) and writer routing all depend
            # on the resolved Branching session state to distinguish setup,
            # FREEFORM_ONLY, HYBRID, TRUE_CYOA, and play status.  Without the
            # resolver we cannot prove the turn is one of the "unchanged" paths,
            # so fail closed before any interaction-style enforcement or
            # writer-routing decision rather than silently proceeding with
            # pre_branching_state=None (which would skip in-play HYBRID/TRUE_CYOA
            # enforcement and downgrade to the prose Writer).
            if self._branching_session_resolver is None:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "branching session resolver not wired for BRANCHING turn;"
                    " cannot determine interaction style or play status",
                )
            try:
                pre_branching_state = self._branching_session_resolver(story_id)
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"branching session resolution failed: {exc}",
                )
            # A wired resolver returning None means the Branching session
            # row/state is missing or corrupt.  Fail closed: without state we
            # cannot prove the turn is setup, FREEFORM_ONLY, HYBRID, or
            # TRUE_CYOA, so treating None as "setup" or "FREEFORM_ONLY" would
            # silently skip in-play enforcement and downgrade to the prose
            # Writer.  Error before any interaction-style enforcement,
            # branch-choice validation, writer routing, or LLM call.
            if pre_branching_state is None:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "branching session state missing or corrupt for BRANCHING"
                    " turn; resolver returned None",
                )

        # INTERACTION_REJECTED: True CYOA mode rejects non-OOC freeform input.
        # Runs after the OOC short-circuit (OOC is always valid) and after the
        # pending-roll intercept (RPG-only).  No LLM call, no Turn, no canon.
        # Gated on in_play: during setup, TRUE_CYOA setup confirmation and
        # clarification route through the ordinary prose Writer path per
        # ADR-016 Decision 3; interaction-style enforcement is in-play only.
        if (
            pre_branching_state is not None
            and pre_branching_state.play_status is BranchingPlayStatus.IN_PLAY
            and pre_branching_state.interaction_style is InteractionStyle.TRUE_CYOA
            and intent_result.intent_type is not IntentType.BRANCH_CHOICE
        ):
            return self._build_result(
                PipelineDisposition.INTERACTION_REJECTED,
                intent_result,
                latency,
                turn_start,
                interaction_rejection_reason=InteractionRejectionReason.INVALID_FOR_INTERACTION_STYLE,
                interaction_rejection_message=(
                    "True CYOA mode requires explicit branch selection"
                    " (e.g., 'I choose option 2')."
                    " Freeform narrative input is not valid in this mode."
                    " Use [OOC] to switch to Hybrid mode."
                ),
            )

        # Fail closed: an in-play HYBRID/TRUE_CYOA BRANCH_CHOICE requires the
        # BranchSelectionValidationService.  Without it we cannot validate the
        # selection against the presented option set; treating the choice as
        # freeform narrative input would bypass the typed branch-card contract
        # and proceed to generation with selected_branch_context=None.  This
        # guard is in-play only, so setup rows stay on the existing wired-only
        # validation path ("setup unchanged").  Must precede any LLM call, Turn
        # persistence, canon mutation, or provider billing.
        if (
            pre_branching_state is not None
            and pre_branching_state.play_status is BranchingPlayStatus.IN_PLAY
            and intent_result.intent_type is IntentType.BRANCH_CHOICE
            and pre_branching_state.interaction_style
            in (
                InteractionStyle.HYBRID,
                InteractionStyle.TRUE_CYOA,
            )
            and self._branching_selection_service is None
        ):
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                "branch selection validation service not wired for in-play"
                " HYBRID/TRUE_CYOA branch choice; refusing unvalidated"
                " selection",
            )

        # INTERACTION_REJECTED: validate BRANCH_CHOICE selection against the
        # presented option set from the current node's mode_metadata.branching.
        # Runs for in-play HYBRID and TRUE_CYOA when intent is BRANCH_CHOICE.
        # Branch-choice validation is an in-play rail: a setup row routes through
        # the prose setup-confirmation path per ADR-016 Decision 3 even when the
        # selection service is wired and the classifier emits BRANCH_CHOICE, so
        # this block is gated on IN_PLAY to match the missing-service guard above.
        # No LLM call, no Turn, no canon mutation on rejection.
        pre_selected_context: SelectedBranchContext | None = None
        if (
            pre_branching_state is not None
            and pre_branching_state.play_status is BranchingPlayStatus.IN_PLAY
            and intent_result.intent_type is IntentType.BRANCH_CHOICE
            and pre_branching_state.interaction_style
            in (
                InteractionStyle.HYBRID,
                InteractionStyle.TRUE_CYOA,
            )
            and self._branching_selection_service is not None
        ):
            from afterworlds.models.node import (
                BranchingNodeMetadata,
                PersistedBranchOption,
            )
            from afterworlds.pipeline.branching.models import (
                BranchSelectionValidationVerdict,
            )

            # A DB/session/crud failure while reading the presented option set
            # is an operational fault, not invalid user input — surface it as
            # PIPELINE_ERROR before any validate() call.  A successful read that
            # yields no options (node missing, non-branching metadata, or empty
            # branch_options) is a valid empty set; the validator then returns
            # INVALID_BRANCH_SELECTION.
            _presented_options: list[PersistedBranchOption] = []
            _lineage_ok = True
            try:
                with self._session_factory() as _read_session:
                    from afterworlds.persistence.crud.node import (
                        get_node as _get_node,
                    )
                    from afterworlds.persistence.crud.node import (
                        node_belongs_to_story as _nbs,
                    )

                    # Lineage guard: never read branch-card options for a node
                    # that does not belong to this story.  Foreign-story option
                    # labels must not reach the selection validator or any
                    # rejection text — fail closed with a generic lineage error
                    # before the options are read.
                    if not _nbs(_read_session, node_id, story_id):
                        _lineage_ok = False
                    else:
                        _current_node = _get_node(_read_session, node_id)
                        if _current_node is not None and isinstance(
                            _current_node.mode_metadata, BranchingNodeMetadata
                        ):
                            _presented_options = list(
                                _current_node.mode_metadata.branch_options
                            )
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"branch-card read failed: {exc}",
                )

            if not _lineage_ok:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"branch-choice lineage check failed: node {node_id} does"
                    f" not belong to story {story_id}",
                )

            _sel_result = self._branching_selection_service.validate(
                intent_result.raw_input,
                _presented_options,
            )
            if _sel_result.verdict is BranchSelectionValidationVerdict.REJECT:
                return self._build_result(
                    PipelineDisposition.INTERACTION_REJECTED,
                    intent_result,
                    latency,
                    turn_start,
                    interaction_rejection_reason=_sel_result.rejection_reason,
                    interaction_rejection_message=(
                        _sel_result.rejection_message
                        or "Branch selection was rejected."
                    ),
                )
            pre_selected_context = _sel_result.selected_context

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
            _pre_session_state=pre_session_state,
            _pre_sheet=pre_sheet,
            _pre_branching_state=pre_branching_state,
            _pre_selected_context=pre_selected_context,
            _pre_writing_state=pre_writing_state,
            writing_turn_request=writing_turn_request,
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
        _pre_session_state: RpgSessionState | None = None,
        _pre_sheet: Dnd5eCharacterSheet | None = None,
        _pre_branching_state: BranchingSessionState | None = None,
        _pre_selected_context: SelectedBranchContext | None = None,
        _pre_writing_state: WritingSessionState | None = None,
        writing_turn_request: WritingTurnRequest | None = None,
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
        # Threaded to _narrative_persist for the RPG turn-retrieval-marker
        # classification (ADR-018 D6). None only when RPG adjudication is
        # not wired for an RPG-mode story; the marker-write block treats
        # that as IN_PLAY/ORDINARY_NARRATIVE (the common case) rather than
        # failing closed, since adjudication wiring is a separate concern.
        rpg_play_status: RpgPlayStatus | None = None

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
            # Use pre-resolved values from early phase (P2-2) when available to
            # avoid a second resolver call for the same story within the same turn.
            if _pre_session_state is not None and _pre_sheet is not None:
                _ss: RpgSessionState = _pre_session_state
                _sh: Dnd5eCharacterSheet = _pre_sheet
            else:
                try:
                    _ss, _sh = self._rpg_session_sheet_resolver(story_id)
                except Exception as exc:  # noqa: BLE001
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        f"RPG session/sheet resolution failed: {exc}",
                        input_safety_result=input_safety,
                        planner_result=planner_result,
                    )
            session_state = _ss
            sheet = _sh
            rpg_session_id = session_state.session_id
            rpg_character_id = sheet.sheet_id
            rpg_sheet = sheet
            rpg_play_status = session_state.play_status
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
                if (
                    adj_result.pending_roll_request is not None
                    and self._rpg_pending_roll_service is None
                ):
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        "RPG pending-roll service not wired; cannot announce"
                        " pending roll",
                        input_safety_result=input_safety,
                        planner_result=planner_result,
                        rpg_adjudication_result=adj_result,
                    )
        # -------------------------------------------------------------------------

        # Open outer transaction now: Writer is about to persist a Turn.
        # Session lifecycle (factory, begin, finalize, close) is centralized
        # in ``_run_with_transaction`` so the narrative and OOC paths cannot
        # drift, and so every raw exception in that lifecycle is mapped to a
        # typed terminal state per the orchestrator's exhaustive
        # terminal-state contract (Issue 12c).
        result = self._run_with_transaction(
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
                branching_state=_pre_branching_state,
                story_mode=story_mode,
                selected_branch_context=_pre_selected_context,
                writing_session_state=_pre_writing_state,
                writing_turn_request=writing_turn_request,
                rpg_play_status=rpg_play_status,
            ),
            intent_result,
            latency,
            turn_start,
            success_disposition=PipelineDisposition.DELIVERED,
            pre_transaction_fn=binding.pre_transaction_fn,
            post_transaction_fn=binding.post_transaction_fn,
        )
        # Retrieval Memory ingestion gate (ADR-018 §6): fires only after the
        # outer transaction has committed successfully, on the post-
        # finalization result — a returned DELIVERED disposition already IS
        # proof of commit (commit failure maps to PIPELINE_ERROR inside
        # _finalize_transaction). Session is closed by now; ingestion opens
        # its own short-lived read, matching the backfill/reindex path.
        # Best-effort and swallowed (D7) — the opposite of the mandatory RPG
        # marker write above: a Chroma failure here must never change
        # `result` or escape this method.
        self._maybe_ingest_retrieval_memory(result, story_id, story_mode)
        return result

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
        branching_state: BranchingSessionState | None = None,
        story_mode: StoryMode = StoryMode.WRITING,
        selected_branch_context: SelectedBranchContext | None = None,
        writing_session_state: WritingSessionState | None = None,
        writing_turn_request: WritingTurnRequest | None = None,
        rpg_play_status: RpgPlayStatus | None = None,
    ) -> OrchestrationResult:
        # Determine if this is a BRANCHING HYBRID/TRUE_CYOA turn (BranchingWriterService
        # replaces WriterService for these modes; FREEFORM_ONLY stays on prose Writer).
        # Gated on in_play: during setup, HYBRID/TRUE_CYOA setup confirmation and
        # clarification route through the prose Writer path per ADR-016 Decision 3.
        # An in-play HYBRID/TRUE_CYOA turn REQUIRES the BranchingWriterService.
        # The service-wiring check is split out from _use_branching_writer so a
        # missing service fails closed (below) rather than silently falling
        # through to the prose Writer, which would bypass the typed branch-card
        # contract and omit branching_pass_result.  Setup turns and
        # FREEFORM_ONLY still route through the prose Writer per ADR-016 Dec. 3.
        _branching_required = (
            story_mode is StoryMode.BRANCHING
            and branching_state is not None
            and branching_state.play_status is BranchingPlayStatus.IN_PLAY
            and branching_state.interaction_style
            in (
                InteractionStyle.HYBRID,
                InteractionStyle.TRUE_CYOA,
            )
        )
        if _branching_required and self._branching_writer_service is None:
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                "branching writer service not wired for in-play"
                " HYBRID/TRUE_CYOA session; refusing prose-writer downgrade",
                input_safety_result=input_safety,
                planner_result=planner_result,
            )
        _use_branching_writer = (
            _branching_required and self._branching_writer_service is not None
        )

        # 5. Writer persists provisional Turn inside the outer transaction.
        #
        # writer_turn_id is pre-allocated by _run_narrative so the adjudication
        # pass can store it as PendingRollRequest.originating_turn_id before the
        # transaction opens.  RefusalFallbackRouter also carries the same id so
        # refusal-log rows are consistent with the Turn row on success.  On
        # failure no Turn is persisted; the log row still carries the candidate id.
        branching_pass_result: _BranchingPassResult | None = None
        if _use_branching_writer:
            # 5a-branching: BranchingWriterService produces narrative + branch cards.
            # Fail-closed: BranchingPassError + ProviderRefusalError both abort the turn.  # noqa: E501
            assert branching_state is not None  # noqa: S101 — narrowed above
            assert (
                self._branching_writer_service is not None
            )  # noqa: S101 — narrowed above
            _branching_svc = self._branching_writer_service
            # Lineage guard: verify node/story lineage before the LLM call so no
            # provider spend is wasted on a turn that cannot be persisted.
            from afterworlds.persistence.crud.node import (
                node_belongs_to_story as _nbs,
            )

            if not _nbs(session, node_id, story_id):
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"branching writer: node {node_id} does not belong to story"
                    f" {story_id}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            _ctx_story_id = ctx.stable_prefix.story_bible_context.story_id
            if _ctx_story_id != story_id:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"branching writer: assembled context story {_ctx_story_id}"
                    f" != target story {story_id}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            _sel_ctx = selected_branch_context
            try:
                branching_pass_result, ms = _timed(
                    lambda: _branching_svc.write(
                        ctx,
                        branching_state,
                        provider=ScopedProviderAdapter(
                            binding.adapter,  # type: ignore[arg-type]
                            sojourner_id,
                            turn_id=writer_turn_id,
                        ),
                        selected_branch_context=_sel_ctx,
                    )
                )
                latency["branching_writer"] = ms
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
            except BranchingPassError as exc:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"branching writer pass failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            except Exception as exc:  # noqa: BLE001 — see boundary docstring
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"branching writer unexpected error: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            # Persist Turn row with branching narrative_text inside the outer
            # transaction.  Turn creation uses the same CRUD as WriterService.
            assert branching_pass_result is not None  # noqa: S101 — mypy narrowing
            _bpr = branching_pass_result
            from datetime import UTC, datetime

            from afterworlds.models.turn import Turn
            from afterworlds.persistence.crud.node import create_turn

            try:
                _icr = ctx.volatile_suffix.classified_intent
                _branching_turn = Turn(
                    turn_id=writer_turn_id,
                    user_input=ctx.volatile_suffix.current_input,
                    assistant_output=_bpr.narrative_text,
                    timestamp=datetime.now(UTC),
                    intent_classification=IntentType(_icr.intent_type.value),
                    node_id=node_id,
                    intent_classification_result=_icr,
                )
                create_turn(session, _branching_turn)
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"branching turn persistence failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    branching_pass_result=branching_pass_result,
                )
            # Phase G: persist branch options + presentation state to
            # Node.mode_metadata.branching.  This metadata is the authoritative
            # surface the next BRANCH_CHOICE turn validates against, so it must be
            # committed in the same transaction that delivers the turn — for
            # held/omitted just as much as for shown.  A shown turn needs its
            # option set persisted; a held/omitted turn needs the prior beat's
            # branch_options cleared (held/omitted always carry an empty option
            # set) so stale cards cannot be selected.  If this write fails we fail
            # closed (PIPELINE_ERROR -> rollback) rather than deliver a turn whose
            # next valid choice surface cannot be trusted.
            try:
                from afterworlds.models.node import (
                    BranchingNodeMetadata,
                    PersistedBranchOption,
                )
                from afterworlds.persistence.crud.node import (
                    get_node as _gn,
                )
                from afterworlds.persistence.crud.node import (
                    update_node as _un,
                )

                _node_to_update = _gn(session, node_id)
                if _node_to_update is None:
                    raise RuntimeError(
                        f"node {node_id} not found for branch-option persistence"
                    )
                _existing_mm = _node_to_update.mode_metadata
                _ps_str = _bpr.branch_presentation_state
                _new_mm = BranchingNodeMetadata(
                    pacing_stage_at_beat=(
                        _existing_mm.pacing_stage_at_beat
                        if isinstance(_existing_mm, BranchingNodeMetadata)
                        else None
                    ),
                    interaction_style=(
                        branching_state.interaction_style if branching_state else None
                    ),
                    branching_cadence=(
                        branching_state.branching_cadence if branching_state else None
                    ),
                    freeform_available=_bpr.freeform_available,
                    branch_count_range=(
                        branching_state.branch_count_range.value
                        if branching_state and branching_state.branch_count_range
                        else None
                    ),
                    branch_options=[
                        PersistedBranchOption(
                            option_id=o.option_id,
                            action_text=o.action_text,
                        )
                        for o in _bpr.branch_options
                    ],
                    branch_presentation_state=_ps_str,
                )
                _node_to_update.mode_metadata = _new_mm
                if _un(session, _node_to_update) is None:
                    raise RuntimeError(
                        f"node {node_id} update returned no row during "
                        "branch-option persistence"
                    )
            except Exception as exc:  # noqa: BLE001
                # Authoritative branch-choice surface failed to persist (shown
                # options unsaved, or stale held/omitted options not cleared).
                # Fail closed so the next turn cannot validate against a surface
                # that was never committed.  The BranchingWriter already ran, so
                # branching_pass_result is preserved for settlement/audit.
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"branch-card metadata persistence failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    branching_pass_result=branching_pass_result,
                )

            # Phase G (selection edge): persist the resolved selection into the
            # node's mode_metadata.branching so callers can replay what was chosen.
            # Best-effort — failure does not block turn delivery.
            if selected_branch_context is not None:
                try:
                    from afterworlds.models.node import (
                        BranchingNodeMetadata as _BNM,
                    )
                    from afterworlds.persistence.crud.node import (
                        get_node as _gn2,
                    )
                    from afterworlds.persistence.crud.node import (
                        update_node as _un2,
                    )

                    _sel_node = _gn2(session, node_id)
                    if _sel_node is not None and isinstance(
                        _sel_node.mode_metadata, _BNM
                    ):
                        _sel_node.mode_metadata.selected_option_id = (
                            selected_branch_context.option_id
                        )
                        # Stable selection record: option_id alone is ambiguous
                        # because IDs (opt_1, …) are reused every beat. Persist
                        # the chosen action text so the selection stays
                        # reconstructable after the next beat's branch_options
                        # overwrite this metadata.
                        _sel_node.mode_metadata.selected_action_text = (
                            selected_branch_context.action_text
                        )
                        _sel_node.mode_metadata.selection_annotation = (
                            selected_branch_context.annotation
                        )
                        _un2(session, _sel_node)
                except Exception:  # noqa: BLE001
                    pass  # Non-critical for current turn delivery

            # Build a thin WriterResult from branching output for downstream passes
            # (Extractor, Contradiction, Output Safety).  These passes need the
            # narrative text; branch_options live in branching_pass_result.
            from afterworlds.pipeline.writer.models import WriterResult as _WriterResult

            writer_result = _WriterResult(
                turn_id=writer_turn_id,
                assistant_output=_bpr.narrative_text,
                model_identifier=_bpr.model_identifier or "",
                latency_ms=_bpr.latency_ms,
                input_token_count=_bpr.input_token_count,
                output_token_count=_bpr.output_token_count,
                cache_read_token_count=_bpr.cache_read_token_count,
                cache_creation_token_count=_bpr.cache_creation_token_count,
                provider=_bpr.provider,
                model_tier=_bpr.model_tier or "",
            )
        else:
            # Thread selected branch context into the ledger when the branching
            # writer is not active (partially-wired orchestrator: selection service
            # wired, branching writer service not).  The prose WriterService renders
            # the ledger as a volatile block, so selected context reaches the model.
            if selected_branch_context is not None:
                _sbc = selected_branch_context
                _sbc_lines = [
                    "[Selected Branch]",
                    f"option_id: {_sbc.option_id}",
                    f"action_text: {_sbc.action_text}",
                ]
                if _sbc.annotation is not None:
                    _sbc_lines.append(f"annotation: {_sbc.annotation}")
                ctx.pass_forward_ledger.add(
                    "branching_selection", "\n".join(_sbc_lines)
                )
            # In-play FREEFORM_ONLY Branching turns use the prose Writer (no
            # branch cards), but the code-owned Branching session configuration
            # still governs storyteller response density.  Surface it as a
            # volatile ledger block so cadence/length preference reaches the
            # model.  Configuration context only: no branch cards or affordances
            # are created here, and this block is never sent on non-Branching
            # stories or for HYBRID/TRUE_CYOA (those use BranchingWriter).
            if (
                story_mode is StoryMode.BRANCHING
                and branching_state is not None
                and branching_state.play_status is BranchingPlayStatus.IN_PLAY
                and branching_state.interaction_style is InteractionStyle.FREEFORM_ONLY
            ):
                _cfg_lines = [
                    "[Branching Session Configuration]",
                    f"interaction_style: {branching_state.interaction_style.value}",
                ]
                if branching_state.branching_cadence is not None:
                    _cfg_lines.append(
                        f"branching_cadence: {branching_state.branching_cadence.value}"
                    )
                if branching_state.length_preference is not None:
                    _cfg_lines.append(
                        "length_preference: "
                        f"{branching_state.length_preference.value}"
                    )
                ctx.pass_forward_ledger.add("branching_config", "\n".join(_cfg_lines))
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
                    rpg_adjudication_result=adj_result,
                )
            except WriterPassError as exc:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"writer pass failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    rpg_adjudication_result=adj_result,
                )
            except Exception as exc:  # noqa: BLE001 — see boundary docstring
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"writer unexpected error: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    rpg_adjudication_result=adj_result,
                )

        # 5a-writing: [WRITING only] Phase G — persist WritingNodeMetadata (persona
        # snapshot + work_product_kind + canon_eligibility + authoring controls
        # snapshot + version pointer refs) inside the outer transaction, on BOTH
        # the delivered Turn (per-turn durable provenance — NodeORM.turns is a
        # list, so multiple Turns can share a Node, and only a per-Turn record
        # survives a later Writing turn on the same Node) and the Node (a
        # Node-level compatibility/summary snapshot, not itself per-turn durable).
        # This is the provenance record that lets future issues filter non-canon
        # output from Rolling Summary (ADR-017 Architecture Note).  Best-effort:
        # failure logs but does not abort the turn (provenance is audit-quality;
        # the turn prose is already persisted).
        if story_mode is StoryMode.WRITING and writing_session_state is not None:
            try:
                from afterworlds.models.node import WritingNodeMetadata as _WNM
                from afterworlds.persistence.crud.node import get_node as _get_node
                from afterworlds.persistence.crud.node import (
                    update_node as _update_node,
                )
                from afterworlds.persistence.crud.node import (
                    update_turn_mode_metadata as _update_turn_mode_metadata,
                )
                from afterworlds.pipeline.writing.models import (
                    AuthoringControlsSnapshot as _ACS,
                )
                from afterworlds.pipeline.writing.models import (
                    WritingVersionPointer as _WVP,
                )

                _w_node = _get_node(session, node_id)
                if _w_node is not None:
                    _wss = writing_session_state
                    _wtr = writing_turn_request

                    # Resolve work_product_kind and canon_eligibility from request.
                    # Setup-provenance invariant (ADR-017 Decision 9): a turn taken
                    # while the session is still in SETUP is a setup-confirmation
                    # turn, not ordinary prose continuation.  When no explicit
                    # writing_turn_request is supplied, default the recorded
                    # work-product kind from play_status rather than blindly to
                    # PROSE_CONTINUATION.
                    # Durable setup-turn guard (ADR-018 D6, corrected from
                    # Issue #117's withdrawn "structurally excluded" claim):
                    # WritingTurnRequest carries no play-status field, so its
                    # validator cannot reject a prose-like work_product_kind
                    # + canon_eligibility_override=EXTRACTOR_ELIGIBLE request
                    # constructed while the session is still in SETUP. Force
                    # both fields on the persisted, durable per-turn record
                    # whenever play_status is SETUP, regardless of what the
                    # request carries — this is the record retrieval
                    # eligibility reads, so it must never expose a
                    # request-supplied override during setup.
                    if _wss.play_status is WritingPlayStatus.SETUP:
                        _wpk = WritingWorkProductKind.SETUP_CONFIRMATION.value
                        _ce = WritingCanonEligibility.NON_CANON_SUPPORT.value
                    elif _wtr is not None:
                        _wpk = _wtr.work_product_kind.value
                        _ce = _wtr.effective_canon_eligibility.value
                    else:
                        _wpk = WritingWorkProductKind.PROSE_CONTINUATION.value
                        _ce = WritingCanonEligibility.NON_CANON_SUPPORT.value

                    # Build authoring-controls snapshot.
                    _acs: dict[str, object] | None = None
                    if _wss.form is not None:
                        try:
                            _acs = _ACS(
                                critique_intensity=_wss.critique_intensity,
                                form=_wss.form,
                                form_other=(
                                    _wss.form_other
                                    if _wss.form is WritingForm.OTHER
                                    else None
                                ),
                                tense=_wss.tense,
                                pov=_wss.pov,
                                style_density=_wss.style_density,
                                dialogue_narration_ratio=_wss.dialogue_narration_ratio,
                                genre_conventions=_wss.genre_conventions,
                                acceptable_content=_wss.acceptable_content,
                            ).model_dump()
                        except Exception:  # noqa: BLE001
                            _acs = None

                    # Snapshot version-pointer references (minimal v1 provenance —
                    # signposts only, no diff/restore/branch semantics).  Skip
                    # malformed entries individually rather than aborting the
                    # whole turn's provenance record.
                    _version_pointer_refs: list[UUID] = []
                    for _raw_vp in _wss.version_pointers:
                        with suppress(Exception):
                            _version_pointer_refs.append(
                                _WVP.model_validate(_raw_vp).pointer_id
                            )

                    # Resolve persona display_name and orientation from registry.
                    _disp_name: str | None = None
                    _orientation: str | None = None
                    if (
                        _wss.persona_id is not None
                        and self._writing_visible_state_service is not None
                    ):
                        try:
                            from afterworlds.modes.personas.registry import (  # noqa: PLC0415
                                SupportedMode as _SM2,
                            )

                            _preg = self._writing_visible_state_service.registry
                            _pprof = _preg.get_profile(_wss.persona_id, _SM2.WRITING)
                            _disp_name = _pprof.display_name
                            _orientation = _pprof.orientation.value
                        except Exception:  # noqa: BLE001
                            pass

                    _writing_metadata = _WNM(
                        persona_id=_wss.persona_id,
                        persona_display_name=_disp_name,
                        relationship_orientation=_orientation,
                        persona_registry_version=_wss.persona_registry_version,
                        persona_profile_version=_wss.persona_profile_version,
                        persona_prompt_fingerprint=_wss.persona_prompt_fingerprint,
                        work_product_kind=_wpk,
                        canon_eligibility=_ce,
                        beat_constraints_snapshot=list(_wss.beat_constraints),
                        version_pointer_refs=_version_pointer_refs,
                        authoring_controls_snapshot=_acs,
                    )
                    # Node.mode_metadata: kept for Node-level compatibility/
                    # summary (e.g. "what governed the most recent turn on
                    # this Node").  NOT per-turn durable — NodeORM.turns is a
                    # list, so a later Writing turn on the same Node
                    # overwrites this.  The per-Turn write below is the
                    # durable provenance record ADR-017 relies on.
                    _w_node.mode_metadata = _writing_metadata
                    _update_node(session, _w_node)
                    _update_turn_mode_metadata(
                        session, writer_turn_id, _writing_metadata
                    )
            except Exception:  # noqa: BLE001
                pass  # Provenance failure does not abort the turn

        # 5a-rpg: [RPG only] Write the turn-category retrieval marker
        # (ADR-018 D6) inside the outer transaction — same location/
        # transaction-scoping as the Writing-mode block above, but NOT its
        # best-effort swallow behavior. This write is mandatory: a
        # marker-write failure on an otherwise-deliverable turn must map to
        # a typed PIPELINE_ERROR and roll back with the turn (never commit
        # markerless). Runs only on the narrative-persist path — the OOC
        # persist path (_ooc_persist) structurally never reaches this block.
        if story_mode is StoryMode.RPG:
            from datetime import UTC, datetime  # noqa: PLC0415

            from afterworlds.models.enums import (  # noqa: PLC0415
                RpgTurnRetrievalCategory as _RTRC,
            )
            from afterworlds.persistence.crud.retrieval import (  # noqa: PLC0415
                create_rpg_turn_retrieval_marker as _create_marker,
            )

            if rpg_play_status is RpgPlayStatus.SETUP:
                _marker_category = _RTRC.SETUP_CONFIRMATION
            elif adj_result is not None and adj_result.pending_roll_request is not None:
                _marker_category = _RTRC.ROLL_REQUEST
            else:
                _marker_category = _RTRC.ORDINARY_NARRATIVE
            try:
                _create_marker(
                    session,
                    turn_id=writer_turn_id,
                    story_id=story_id,
                    category=_marker_category,
                    created_at=datetime.now(UTC).isoformat(),
                )
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"rpg turn retrieval marker write failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
                    rpg_adjudication_result=adj_result,
                    branching_pass_result=branching_pass_result,
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
                    rpg_adjudication_result=adj_result,
                    branching_pass_result=branching_pass_result,
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
                    rpg_adjudication_result=adj_result,
                    branching_pass_result=branching_pass_result,
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
                        rpg_adjudication_result=adj_result,
                        branching_pass_result=branching_pass_result,
                    )
            if self._rpg_visible_state_service is not None:
                try:
                    rpg_visible_state = self._rpg_visible_state_service.build(rpg_sheet)
                except Exception as exc:  # noqa: BLE001
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        f"visible state build failed: {exc}",
                        input_safety_result=input_safety,
                        planner_result=planner_result,
                        writer_result=writer_result,
                        rpg_adjudication_result=adj_result,
                        branching_pass_result=branching_pass_result,
                    )

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
                    rpg_adjudication_result=adj_result,
                    branching_pass_result=branching_pass_result,
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
                    rpg_adjudication_result=adj_result,
                    branching_pass_result=branching_pass_result,
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
                    rpg_adjudication_result=adj_result,
                    branching_pass_result=branching_pass_result,
                )

        # 7. Extractor || Contradiction (parallel sync, asymmetric).
        # Canon is suppressed by default on all Writing turns (NON_CANON_SUPPORT).
        # Proposals only reach the Story Bible when the caller explicitly promotes
        # the turn to EXTRACTOR_ELIGIBLE via WritingTurnRequest. Fail closed: a
        # missing turn request is treated as NON_CANON_SUPPORT, not as promotion.
        _skip_story_bible_routing = story_mode is StoryMode.WRITING and (
            writing_turn_request is None
            or writing_turn_request.effective_canon_eligibility
            is WritingCanonEligibility.NON_CANON_SUPPORT
        )
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
                ctx,
                writer_result,
                story_id,
                session,
                _scoped_post_writer,
                skip_story_bible_routing=_skip_story_bible_routing,
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
                rpg_adjudication_result=adj_result,
                branching_pass_result=branching_pass_result,
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
                rpg_adjudication_result=adj_result,
                branching_pass_result=branching_pass_result,
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
                rpg_adjudication_result=adj_result,
                branching_pass_result=branching_pass_result,
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
                rpg_adjudication_result=adj_result,
                branching_pass_result=branching_pass_result,
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
                rpg_adjudication_result=adj_result,
                branching_pass_result=branching_pass_result,
            )

        # Build branching visible state for BRANCHING-mode DELIVERED turns.
        branching_visible_state = None
        if (
            story_mode is StoryMode.BRANCHING
            and branching_state is not None
            and self._branching_visible_state_service is not None
        ):
            try:
                branching_visible_state = self._branching_visible_state_service.build(
                    branching_state,
                    branching_pass_result,
                )
            except Exception:  # noqa: BLE001
                branching_visible_state = None

        # Build Writing visible state for WRITING-mode DELIVERED turns.
        writing_visible_state = None
        if (
            story_mode is StoryMode.WRITING
            and writing_session_state is not None
            and self._writing_visible_state_service is not None
        ):
            try:
                writing_visible_state = self._writing_visible_state_service.build(
                    writing_session_state
                )
            except Exception:  # noqa: BLE001
                writing_visible_state = None

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
            branching_pass_result=branching_pass_result,
            branching_visible_state=branching_visible_state,
            writing_visible_state=writing_visible_state,
            delivered_output=writer_result.assistant_output,
            turn_id=writer_result.turn_id,
        )

    # ------------------------------------------------------------------
    # OOC path
    # ------------------------------------------------------------------

    def _build_rpg_ooc_state(self, story_id: UUID) -> str | None:
        """Build a player-visible RPG state payload for the OOC handler ledger.

        Returns None when rpg_session_sheet_resolver is not wired (graceful
        degrade — OOC prompt instructs the model to say it lacks state).
        Raises on resolver or service failure; caller maps to PIPELINE_ERROR.

        Allowlisted fields only — never serialises the full sheet or pending
        object (those carry hidden_modifier_present and adapter_context_hash).
        """
        if self._rpg_session_sheet_resolver is None:
            return None
        session_state, sheet = self._rpg_session_sheet_resolver(story_id)
        parts: list[str] = [
            "## RPG Session State",
            f"play_status: {session_state.play_status.value}",
            f"setup_phase: {session_state.setup_phase.value}",
            f"dice_handling: {session_state.dice_handling.value}",
            f"gm_cheating: {session_state.gm_cheating}",
            f"tone: {session_state.tone.value}",
            f"session_type: {session_state.session_type.value}",
        ]
        if self._rpg_visible_state_service is not None:
            visible = self._rpg_visible_state_service.build(sheet)
            char = visible.character
            parts += [
                "",
                "## Character",
                f"name: {char.character_name}",
                f"class: {char.character_class}",
                f"level: {char.level}",
                f"hp: {char.current_hp}/{char.maximum_hp}",
                (
                    f"conditions: {', '.join(char.active_conditions)}"
                    if char.active_conditions
                    else "conditions: none"
                ),
            ]
        if self._rpg_pending_roll_service is not None:
            pending = self._rpg_pending_roll_service.load_pending_for_story(story_id)
            if pending is not None:
                parts += [
                    "",
                    "## Pending Roll",
                    f"check: {pending.check_label}",
                    f"instruction: {pending.player_facing_instruction}",
                ]
                if pending.visible_modifier_note is not None:
                    parts.append(f"modifier: {pending.visible_modifier_note}")
        return "\n".join(parts)

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
        *,
        story_mode: StoryMode,
        pre_writing_state: WritingSessionState | None = None,
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

        # Select mode-specific OOC handler; RPG/Branching/Writing each have a prompt.
        if story_mode is StoryMode.RPG:
            ooc_prompt = self._rpg_ooc_handler_prompt
        elif story_mode is StoryMode.BRANCHING:
            ooc_prompt = self._branching_ooc_handler_prompt
        elif story_mode is StoryMode.WRITING:
            ooc_prompt = self._writing_ooc_handler_prompt
        else:
            ooc_prompt = self._ooc_handler_prompt
        ooc_ctx = _swap_system_prompt(ctx, ooc_prompt)

        if story_mode is StoryMode.RPG:
            try:
                rpg_ooc_state = self._build_rpg_ooc_state(story_id)
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"rpg_ooc_state build failed: {exc}",
                )
            if rpg_ooc_state:
                ooc_ctx.pass_forward_ledger.add("rpg_ooc_state", rpg_ooc_state)
        elif story_mode is StoryMode.WRITING and pre_writing_state is not None:
            from afterworlds.pipeline.writing.context import (  # noqa: PLC0415
                render_writing_ooc_state_block as _writing_ooc_state_fn,
            )

            _writing_ooc_block = _writing_ooc_state_fn(pre_writing_state)
            if _writing_ooc_block:
                ooc_ctx.pass_forward_ledger.add("writing_ooc_state", _writing_ooc_block)

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
                story_mode=story_mode,
                writing_session_state=pre_writing_state,
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
        *,
        story_mode: StoryMode,
        writing_session_state: WritingSessionState | None = None,
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

        # Phase F (OOC config extraction): for BRANCHING turns, extract any
        # interaction-config changes the Sojourner requested and persist them
        # inside this transaction.  Best-effort — failure skips persistence
        # without blocking OOC_HANDLED.
        _ooc_cfg_extractor_result: object | None = None
        # Set when a requested switch to HYBRID/TRUE_CYOA is suppressed because no
        # compatible branch-count range exists.  Appended to the delivered OOC
        # output so the prose response cannot imply a style change that
        # persistence did not actually make (confirmation/persistence parity).
        _ooc_style_noop_note: str | None = None
        # Set when an OOC request supplied an explicit branch_count_range that is
        # invalid for the applicable style and is therefore discarded.  Surfaced
        # for the range-only case (when no style switch was suppressed for the
        # same reason) so the prose cannot imply a range change that did not
        # persist.  Mutually exclusive with _ooc_style_noop_note to avoid
        # contradictory duplicate corrections.
        _ooc_range_noop_note: str | None = None
        # Set when the OOC extractor returned a persona_id that is not in the
        # Writing persona registry, so the persona change was not persisted.
        # Appended to the delivery note so the prose cannot imply a switch that
        # did not happen.
        _ooc_persona_noop_note: str | None = None
        # Set when a requested IN_PLAY transition is suppressed because no
        # verified Writing persona is present after the update.  Appended to the
        # delivery note so the prose cannot imply a setup completion that did
        # not happen.  Can fire together with _ooc_persona_noop_note when the
        # extractor returns an unrecognised persona_id AND play_status=IN_PLAY.
        _ooc_play_noop_note: str | None = None
        # Set when a requested form=OTHER lacks a valid effective form_other (no
        # nonblank new value, and the existing row is not already form=OTHER
        # with a valid custom description).  The CRUD guard silently skips this
        # form change to avoid an unreadable row; surfaced here so the prose
        # cannot imply the form changed when it did not persist.
        _ooc_form_noop_note: str | None = None
        # Set when a requested blank/whitespace specific_goals update is
        # suppressed because the effective post-update play_status is (or
        # remains) IN_PLAY.  Confirmation/persistence parity: the CRUD guard
        # silently keeps the existing goal to avoid an unreadable row;
        # surfaced here so the prose cannot imply the goal was cleared when it
        # was not.  Blank goals remain allowed when the same update
        # transitions the session to SETUP (no note in that case).
        _ooc_goal_noop_note: str | None = None
        if (
            story_mode is StoryMode.BRANCHING
            and self._branching_ooc_config_extractor is not None
        ):
            try:
                from afterworlds.models.enums import InteractionStyle as _IS
                from afterworlds.models.session import BranchingSessionState as _BSS
                from afterworlds.persistence.crud.session_state import (
                    apply_branching_config_update as _apply_cfg,
                )
                from afterworlds.persistence.crud.session_state import (
                    get_branching_session_state_by_story as _get_bss,
                )
                from afterworlds.pipeline.branching.config import (
                    ALLOWED_RANGES_BY_STYLE as _ALLOWED,
                )

                # Scope the extractor's provider call to the OOC prose-writer's
                # turn so any refusal/fallback/provider-call audit row is
                # reconstructable from that same turn (post-writer convention,
                # mirroring the output-audit call above).  turn_id may be None
                # if the writer did not produce one — ScopedProviderAdapter
                # omits it safely in that case.
                _extract_result = self._branching_ooc_config_extractor.extract(
                    ooc_ctx,
                    ScopedProviderAdapter(
                        binding.adapter,  # type: ignore[arg-type]
                        sojourner_id,
                        turn_id=writer_result.turn_id,
                    ),
                )
                # Capture metrics immediately so usage is visible to settlement
                # even if a later best-effort persistence step raises.
                _ooc_cfg_extractor_result = _extract_result
                _cfg_update = _extract_result.config_update

                # Determine the target interaction style for range validation.
                _bss_row: _BSS | None = None
                _target_style: _IS | None = _cfg_update.interaction_style
                if _target_style is None:
                    _bss_row = _get_bss(session, story_id)
                    _target_style = (
                        _bss_row.interaction_style if _bss_row is not None else None
                    )

                # Separate "no range requested" from "explicit range requested but
                # later found invalid" so the two cases get different treatment.
                _requested_range = _cfg_update.branch_count_range

                # Validate branch_count_range against the target style.  Track
                # whether an explicitly requested range was rejected so the
                # range-only case can surface a corrective note (the style-only
                # suppression already carries its own note below).
                _range_invalid = False
                _validated_range = _requested_range
                if _validated_range is not None and _target_style is not None:
                    _allowed_ranges = _ALLOWED.get(_target_style)
                    if (
                        _allowed_ranges is None
                        or _validated_range not in _allowed_ranges
                    ):
                        _range_invalid = True
                        _validated_range = None  # discard invalid range

                # Determine persistence strategy for the style × range pair to
                # avoid leaving the row in a mismatched configuration:
                # • FREEFORM_ONLY: persist style, clear range to NULL.
                # • HYBRID/TRUE_CYOA with a valid requested range: persist both.
                # • HYBRID/TRUE_CYOA, no range requested, persisted range
                #   compatible with target style: persist style, keep existing range.
                # • HYBRID/TRUE_CYOA, no range requested, persisted range
                #   incompatible (or absent): suppress style change (atomicity).
                # • HYBRID/TRUE_CYOA, explicit range requested but invalid:
                #   suppress style change (do not fall back to persisted range).
                _apply_style = _cfg_update.interaction_style
                _should_clear_range = False
                if _cfg_update.interaction_style is _IS.FREEFORM_ONLY:
                    _should_clear_range = True
                elif _cfg_update.interaction_style in (_IS.HYBRID, _IS.TRUE_CYOA):
                    if _validated_range is not None:
                        pass  # persist style + explicit valid range
                    elif _requested_range is None:
                        # No range requested — check if the persisted range is
                        # valid for the target style before allowing the switch.
                        if _bss_row is None:
                            _bss_row = _get_bss(session, story_id)
                        _persisted = (
                            _bss_row.branch_count_range
                            if _bss_row is not None
                            else None
                        )
                        _target_allowed = _ALLOWED.get(_cfg_update.interaction_style)
                        if (
                            _persisted is None
                            or _target_allowed is None
                            or _persisted not in _target_allowed
                        ):
                            _apply_style = None  # incompatible persisted range
                        # else: persisted range is valid for target — allow style
                    else:
                        # Explicit range was requested but is invalid; suppress.
                        _apply_style = None

                # If a switch to HYBRID/TRUE_CYOA was requested but suppressed
                # (no compatible range), the style is NOT persisted.  Record an
                # explicit non-confirmation so the OOC prose cannot silently
                # imply the change happened.
                if _apply_style is None and _cfg_update.interaction_style in (
                    _IS.HYBRID,
                    _IS.TRUE_CYOA,
                ):
                    _allowed_for_note = _ALLOWED.get(_cfg_update.interaction_style)
                    _ranges_txt = (
                        ", ".join(sorted(r.value for r in _allowed_for_note))
                        if _allowed_for_note
                        else ""
                    )
                    _ooc_style_noop_note = (
                        f"[Interaction style not changed: switching to "
                        f"{_cfg_update.interaction_style.value} needs a compatible "
                        f"branch-count range. Set one of: {_ranges_txt} and try "
                        f"again.]"
                    )

                # An explicitly requested branch-count range that is invalid for
                # the applicable style is discarded (never persisted).  Surface a
                # dedicated correction ONLY when the style switch was not itself
                # suppressed for the same reason (that note already names the
                # range and lists compatible ranges — a second note would be a
                # contradictory duplicate) and the range is not being cleared by
                # a deliberate FREEFORM_ONLY switch (a "not changed" note would be
                # false there, since the switch clears it by design).
                if (
                    _range_invalid
                    and _ooc_style_noop_note is None
                    and not _should_clear_range
                    and _requested_range is not None
                ):
                    _range_allowed = (
                        _ALLOWED.get(_target_style)
                        if _target_style is not None
                        else None
                    )
                    _range_ranges_txt = (
                        ", ".join(sorted(r.value for r in _range_allowed))
                        if _range_allowed
                        else ""
                    )
                    _range_style_txt = (
                        _target_style.value
                        if _target_style is not None
                        else "the current interaction style"
                    )
                    if _range_ranges_txt:
                        _ooc_range_noop_note = (
                            f"[Branch-count range not changed: "
                            f"{_requested_range.value} is not valid for "
                            f"{_range_style_txt}. Set one of: {_range_ranges_txt} "
                            f"and try again.]"
                        )
                    else:
                        _ooc_range_noop_note = (
                            f"[Branch-count range not changed: "
                            f"{_requested_range.value} is not valid for "
                            f"{_range_style_txt}.]"
                        )

                _apply_cfg(
                    session,
                    story_id,
                    interaction_style=_apply_style,
                    branching_cadence=_cfg_update.branching_cadence,
                    branch_count_range=_validated_range,
                    length_preference=_cfg_update.length_preference,
                    clear_branch_count_range=_should_clear_range,
                )
            except BranchingOocExtractionUsageError as _usage_exc:
                # The provider call succeeded (tokens consumed) but a local
                # validation step rejected the response.  Preserve the usage-only
                # result for settlement/audit; the config update is skipped as
                # best-effort, exactly like the generic swallow below.
                _ooc_cfg_extractor_result = _usage_exc.usage_result
            except Exception:  # noqa: BLE001
                pass  # Best-effort; OOC prose already delivered

        # Phase F (Writing OOC config extraction): for WRITING turns, extract any
        # session config changes the Sojourner requested and persist them inside
        # this transaction.  Best-effort — failure skips persistence without
        # blocking OOC_HANDLED.
        _writing_ooc_cfg_result: object | None = None
        if (
            story_mode is StoryMode.WRITING
            and self._writing_ooc_config_extractor is not None
        ):
            try:
                from afterworlds.persistence.crud.session_state import (  # noqa: PLC0415
                    apply_writing_config_update as _apply_writing_cfg,
                )

                _w_extract_result = self._writing_ooc_config_extractor.extract(
                    ooc_ctx,
                    ScopedProviderAdapter(
                        binding.adapter,  # type: ignore[arg-type]
                        sojourner_id,
                        turn_id=writer_result.turn_id,
                    ),
                )
                _writing_ooc_cfg_result = _w_extract_result
                _w_cfg = _w_extract_result.config_update

                # Determine registry provenance if persona_id is changing.
                # On a registry miss the persona change is a no-op; other fields
                # in the same update still persist.  A corrective note is recorded
                # so the delivered prose cannot imply a persona switch that did
                # not happen.
                _registry_version: int | None = None
                _profile_version: int | None = None
                _prompt_fingerprint: str | None = None
                _persona_id_to_persist: str | None = None
                if _w_cfg.persona_id is not None:
                    if self._writing_visible_state_service is not None:
                        try:
                            from afterworlds.modes.personas.registry import (  # noqa: PLC0415
                                PersonaAvailability as _PA,
                            )
                            from afterworlds.modes.personas.registry import (
                                SupportedMode as _SM,
                            )

                            _reg = self._writing_visible_state_service.registry
                            _prof = _reg.get_profile(_w_cfg.persona_id, _SM.WRITING)
                            # Registry contract distinguishes resolvable (any
                            # availability) from selectable (ACTIVE only).
                            # Hidden/deprecated profiles may still resolve for
                            # existing persisted sessions but must not be newly
                            # selected via OOC config updates.  Gate ALL
                            # provenance fields on this check together so a
                            # non-ACTIVE profile's version/fingerprint never
                            # lands on the row while persona_id stays unchanged.
                            if _prof.availability is not _PA.ACTIVE:
                                # Never echo the raw requested persona_id here:
                                # WritingConfigUpdate.persona_id is an
                                # extractor/user-supplied free string, and this
                                # note is appended to delivered/persisted OOC
                                # output *after* the output safety audit has
                                # already run — an unsanitized echo would let
                                # arbitrary text bypass that audit.
                                _ooc_persona_noop_note = (
                                    "[Persona not changed: requested persona is"
                                    " not currently available for selection.]"
                                )
                            else:
                                _registry_version = _reg.registry_version
                                _profile_version = _prof.profile_version
                                _prompt_fingerprint = _prof.prompt_fingerprint
                                _persona_id_to_persist = _w_cfg.persona_id
                        except Exception:  # noqa: BLE001
                            _ooc_persona_noop_note = (
                                "[Persona not changed: requested persona is not"
                                " recognized as an available Writing persona.]"
                            )
                    else:
                        # No registry service wired — treat as no-op for safety.
                        _ooc_persona_noop_note = (
                            "[Persona not changed: requested persona could not"
                            " be verified (registry not available).]"
                        )

                # Convert version_pointers to plain dicts for CRUD persistence.
                _vp_dicts: list[dict[str, object]] | None = None
                if _w_cfg.version_pointers is not None:
                    _vp_dicts = [
                        vp.model_dump(mode="json") for vp in _w_cfg.version_pointers
                    ]

                # Form/custom-form invariant: form_other is meaningful only when
                # form is OTHER.  A requested form=OTHER without a valid
                # effective form_other would be silently skipped by the CRUD
                # guard (to avoid an unreadable row) while the OOC turn is still
                # returned as handled.  Surface that suppression here so the
                # prose cannot imply a form change that did not persist.  A
                # stale form_other on a row whose *current* form is not already
                # OTHER must never satisfy this requirement.
                _form_to_persist: WritingForm | None = _w_cfg.form
                _form_other_to_persist: str | None = _w_cfg.form_other
                if _w_cfg.form is WritingForm.OTHER:
                    _new_form_other = (
                        _w_cfg.form_other if (_w_cfg.form_other or "").strip() else None
                    )
                    _existing_form_other = (
                        writing_session_state.form_other
                        if (
                            writing_session_state is not None
                            and writing_session_state.form is WritingForm.OTHER
                            and writing_session_state.form_other
                        )
                        else None
                    )
                    if _new_form_other is None and _existing_form_other is None:
                        _form_to_persist = None
                        _form_other_to_persist = None
                        _ooc_form_noop_note = (
                            "[Form not changed:"
                            ' "other" requires a custom form description.]'
                        )

                # Invariant: a Writing session may enter or remain IN_PLAY only
                # when the resulting persisted state has a verified Writing
                # persona.  Compute the effective persona after this update:
                # use the newly-verified persona_id from this update if present,
                # otherwise fall back to the existing row's persona_id (verified
                # against the registry).  If neither yields a verified persona,
                # suppress the IN_PLAY transition and surface a corrective note.
                _play_status_to_persist = _w_cfg.play_status
                if _w_cfg.play_status is WritingPlayStatus.IN_PLAY:
                    _effective_persona_id: str | None = _persona_id_to_persist
                    if (
                        _effective_persona_id is None
                        and writing_session_state is not None
                        and writing_session_state.persona_id is not None
                        and self._writing_visible_state_service is not None
                    ):
                        try:
                            from afterworlds.modes.personas.registry import (  # noqa: PLC0415
                                SupportedMode as _SM_P,
                            )

                            _reg_p = self._writing_visible_state_service.registry
                            _reg_p.get_profile(
                                writing_session_state.persona_id, _SM_P.WRITING
                            )
                            _effective_persona_id = writing_session_state.persona_id
                        except Exception:  # noqa: BLE001
                            pass
                    if _effective_persona_id is None:
                        _play_status_to_persist = None
                        _ooc_play_noop_note = (
                            "[Play status not changed: IN_PLAY requires a"
                            " verified Writing persona to be configured first.]"
                        )
                    else:
                        # Setup-completion rule (owner decision, PR #116 remediation):
                        # IN_PLAY also requires an immediate writing goal.  Effective
                        # goal is the new value from this update if supplied,
                        # otherwise the existing session state's specific_goals,
                        # trimmed.  writing_interests describes broader project/taste
                        # and does not satisfy this immediate-work gate.
                        _effective_goal = (
                            _w_cfg.specific_goals
                            if _w_cfg.specific_goals is not None
                            else (
                                writing_session_state.specific_goals
                                if writing_session_state is not None
                                else ""
                            )
                        )
                        if not _effective_goal.strip():
                            _play_status_to_persist = None
                            _ooc_play_noop_note = (
                                "[Play status not changed: IN_PLAY requires an"
                                " immediate writing goal.]"
                            )

                # Confirmation/persistence parity (mirrors the form/form_other
                # and persona/play-status notes above): a blank/whitespace
                # specific_goals update would be silently kept-as-is by the
                # CRUD guard when the effective post-update play_status is (or
                # remains) IN_PLAY, to avoid an unreadable row.  Compute the
                # effective status the same way CRUD does — the requested
                # play_status if this update supplies one, else the existing
                # row's current value — and surface the suppression so the
                # prose cannot imply the goal was cleared when it was not.  A
                # blank goal paired with an explicit transition to SETUP is
                # unaffected (no note; CRUD allows it).
                _goals_to_persist = _w_cfg.specific_goals
                if (
                    _w_cfg.specific_goals is not None
                    and not _w_cfg.specific_goals.strip()
                ):
                    _effective_status_for_goal_note = (
                        _play_status_to_persist
                        if _play_status_to_persist is not None
                        else (
                            writing_session_state.play_status
                            if writing_session_state is not None
                            else None
                        )
                    )
                    if _effective_status_for_goal_note is WritingPlayStatus.IN_PLAY:
                        _goals_to_persist = None
                        _ooc_goal_noop_note = (
                            "[Immediate goal not changed: IN_PLAY requires a"
                            " nonblank immediate writing goal. Switch back to"
                            " setup before clearing it.]"
                        )

                _apply_writing_cfg(
                    session,
                    story_id,
                    persona_id=_persona_id_to_persist,
                    persona_registry_version=_registry_version,
                    persona_profile_version=_profile_version,
                    persona_prompt_fingerprint=_prompt_fingerprint,
                    critique_intensity=_w_cfg.critique_intensity,
                    form=_form_to_persist,
                    form_other=_form_other_to_persist,
                    tense=_w_cfg.tense,
                    pov=_w_cfg.pov,
                    style_density=_w_cfg.style_density,
                    dialogue_narration_ratio=_w_cfg.dialogue_narration_ratio,
                    genre_conventions=_w_cfg.genre_conventions,
                    specific_goals=_goals_to_persist,
                    acceptable_content=_w_cfg.acceptable_content,
                    beat_constraints=_w_cfg.beat_constraints,
                    beat_constraints_mode=_w_cfg.beat_constraints_mode,
                    version_pointers=_vp_dicts,
                    play_status=_play_status_to_persist,
                )
            except WritingOocExtractionUsageError as _w_usage_exc:
                _writing_ooc_cfg_result = _w_usage_exc.usage_result
            except Exception:  # noqa: BLE001
                pass  # Best-effort; OOC prose already delivered

        _ooc_delivered = writer_result.assistant_output
        # Compose all suppression notes into one correction block.  Notes are
        # independent: _ooc_persona_noop_note and _ooc_play_noop_note can both
        # fire when the extractor requests an unrecognised persona together with
        # play_status=IN_PLAY.  _ooc_style_noop_note and _ooc_range_noop_note
        # are mutually exclusive with each other but independent of the others.
        _ooc_config_noop_notes = [
            _note
            for _note in (
                _ooc_style_noop_note,
                _ooc_range_noop_note,
                _ooc_persona_noop_note,
                _ooc_play_noop_note,
                _ooc_form_noop_note,
                _ooc_goal_noop_note,
            )
            if _note is not None
        ]
        if _ooc_config_noop_notes:
            _ooc_delivered = (
                _ooc_delivered + "\n\n" + "\n\n".join(_ooc_config_noop_notes)
            )
            # Keep the persisted OOC Turn truthful.  The corrective no-op note is
            # appended to the delivered output because the requested style/range
            # change was suppressed; the raw writer prose alone could falsely
            # imply the change happened.  Persist the same corrected output to
            # the Turn row and mirror it onto the in-memory writer_result so
            # delivered output, returned writer_result, and future recent-turn
            # context all agree.  Done inside this transaction; a write failure
            # rolls the whole OOC turn back rather than persisting a false
            # confirmation.
            if writer_result.turn_id is not None:
                from afterworlds.persistence.crud.node import (
                    update_turn_assistant_output,
                )

                update_turn_assistant_output(
                    session, writer_result.turn_id, _ooc_delivered
                )
            writer_result = writer_result.model_copy(
                update={"assistant_output": _ooc_delivered}
            )

        return self._build_result(
            PipelineDisposition.OOC_HANDLED,
            intent_result,
            latency,
            turn_start,
            input_safety_result=input_safety,
            writer_result=writer_result,
            output_safety_result=output_safety,
            delivered_output=_ooc_delivered,
            turn_id=writer_result.turn_id,
            branching_ooc_config_result=_ooc_cfg_extractor_result,
            writing_ooc_config_result=_writing_ooc_cfg_result,
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
        *,
        skip_story_bible_routing: bool = False,
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
        _skip_routing = skip_story_bible_routing
        try:
            extractor_result, ext_ms = _timed(
                lambda: self._extractor_service.extract(
                    ctx,
                    writer_result.assistant_output,
                    story_id,
                    writer_result.turn_id,
                    provider=provider,
                    session=session,
                    skip_story_bible_routing=_skip_routing,
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
            if self._rpg_pending_roll_service is None:
                raise RuntimeError(
                    "Cannot announce pending roll: _rpg_pending_roll_service"
                    " is not wired"
                )
            self._rpg_pending_roll_service.check_no_pending_for_story(session, story_id)
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
        *,
        mode: StoryMode | None = None,
        rule_slice_request: RuleSliceRequest | None = None,
        retrieval_query_request: RetrievalQueryRequest | None = None,
    ) -> tuple[AssembledContext, StoryMode, int]:
        resolved_mode: StoryMode = (
            mode if mode is not None else self._mode_resolver(story_id)
        )
        ctx, ms = _timed(
            lambda: self._context_builder.assemble(
                story_id=story_id,
                mode=resolved_mode,
                current_input=user_input,
                classified_intent=intent_result,
                rule_slice_request=rule_slice_request,
                retrieval_query_request=retrieval_query_request,
            )
        )
        return ctx, resolved_mode, ms

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
        interaction_rejection_reason: InteractionRejectionReason | None = None,
        interaction_rejection_message: str | None = None,
        branching_pass_result: _BranchingPassResult | None = None,
        branching_visible_state: object | None = None,
        branching_ooc_config_result: object | None = None,
        writing_visible_state: object | None = None,
        writing_ooc_config_result: object | None = None,
    ) -> OrchestrationResult:
        total_ms = max(0, int((time.perf_counter() - turn_start) * 1000))
        cache_warmed = _any_cache_read(
            input_safety_result,
            planner_result,
            writer_result,
            output_safety_result,
            extractor_result,
            contradiction_result,
            rpg_adjudication_result,
            # Branching provider results are stable-prefix-backed calls
            # equivalent to planner/writer/extractor for cache observability.
            branching_pass_result,
            branching_ooc_config_result,
            writing_ooc_config_result,
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
            interaction_rejection_reason=interaction_rejection_reason,
            interaction_rejection_message=interaction_rejection_message,
            branching_pass_result=branching_pass_result,
            branching_visible_state=branching_visible_state,
            branching_ooc_config_result=branching_ooc_config_result,
            writing_visible_state=writing_visible_state,
            writing_ooc_config_result=writing_ooc_config_result,
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
        rpg_adjudication_result: AdjudicationPassResult | None = None,
        branching_pass_result: _BranchingPassResult | None = None,
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
            rpg_adjudication_result=rpg_adjudication_result,
            branching_pass_result=branching_pass_result,
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
                    # Preserve usage-carrying Branching and Writing OOC-config
                    # pass results.  A BranchingWriter, Branching OOC-config
                    # extractor, or Writing OOC-config extractor that ran before
                    # the failed commit already consumed provider tokens; the
                    # disposition changes to PIPELINE_ERROR but that successful
                    # provider-usage evidence must survive so cost settlement
                    # (BRANCHING_WRITER / BRANCHING_OOC_CONFIG_EXTRACTOR /
                    # WRITING_OOC_CONFIG_EXTRACTOR) and audit can reconstruct
                    # the spend.  Delivery is gated by the PIPELINE_ERROR
                    # disposition, not by nulling these records.
                    branching_pass_result=inner_result.branching_pass_result,
                    branching_ooc_config_result=(
                        inner_result.branching_ooc_config_result
                    ),
                    writing_ooc_config_result=(inner_result.writing_ooc_config_result),
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

    def _maybe_ingest_retrieval_memory(
        self, result: OrchestrationResult, story_id: UUID, story_mode: StoryMode
    ) -> None:
        """Fire the Retrieval Memory ingestion gate (ADR-018 §6/D6/D7).

        Gates on the post-finalization ``OrchestrationResult`` — never a
        provisional ``WriterResult.turn_id``, which can still roll back
        before ``_finalize_transaction`` completes. Deny-list dispositions
        (``BLOCKED_PENDING_ROLL``, ``INTERACTION_REJECTED``, all Safety/
        Contradiction blocks, refusals, ``PIPELINE_ERROR``, any rolled-back
        turn) never reach this method's body because they never produce a
        ``DELIVERED`` disposition here.

        Best-effort and swallowed (D7): a failure anywhere in this method
        — including a D6-ineligible turn correctly declining to ingest —
        must never change ``result`` or raise out of this method. This is
        the deliberate opposite of the RPG marker write's mandatory,
        typed-PIPELINE_ERROR semantics inside ``_narrative_persist``.
        """
        if self._retrieval_write_service is None:
            return
        if (
            result.disposition is not PipelineDisposition.DELIVERED
            or result.turn_id is None
        ):
            return
        try:
            from afterworlds.persistence.crud.node import get_turn
            from afterworlds.pipeline.retrieval.eligibility import (
                gather_turn_eligibility_for_turn,
            )

            session = self._session_factory()
            try:
                turn = get_turn(session, result.turn_id)
                if turn is None:
                    return
                decision = gather_turn_eligibility_for_turn(session, turn, story_mode)
                if not decision.eligible:
                    return
                self._retrieval_write_service.ingest_turn(
                    story_id=story_id,
                    turn_id=turn.turn_id,
                    node_id=turn.node_id,
                    mode=story_mode.value,
                    delivered_output=turn.assistant_output,
                    created_at=turn.timestamp.isoformat(),
                )
            finally:
                session.close()
        except Exception as exc:  # noqa: BLE001 — D7: log and swallow, never raise
            logger.error(
                "retrieval memory ingestion failed for turn_id=%s: %s",
                result.turn_id,
                exc,
            )


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


def _extend_system_prompt(ctx: AssembledContext, appendix: str) -> AssembledContext:
    """Return a derived AssembledContext with ``appendix`` appended to system_prompt.

    Used to inject Writing-mode persona + authoring-controls context into the
    stable prefix once per turn.  All other stable-prefix fields are preserved.
    The original ``ctx`` is not mutated.
    """
    sp = ctx.stable_prefix
    new_sp = StablePrefix(
        system_prompt=sp.system_prompt + "\n\n" + appendix,
        story_bible_context=sp.story_bible_context,
        rolling_summary_text=sp.rolling_summary_text,
        rules_package_slice=sp.rules_package_slice,
        retrieval_memory=sp.retrieval_memory,
    )
    return AssembledContext(
        stable_prefix=new_sp,
        volatile_suffix=ctx.volatile_suffix,
        pass_forward_ledger=ctx.pass_forward_ledger,
    )


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
