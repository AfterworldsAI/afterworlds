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

from afterworlds.entitlement.enums import PipelinePassId, RuntimeAccessPath
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
from afterworlds.models.intent_classification import (
    IntentClassificationError,
    IntentClassificationResult,
)
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
from afterworlds.pipeline.rpg.models import (
    ActionResolutionError,
    AdjudicationPassError,
    AdjudicationPassResult,
)
from afterworlds.pipeline.writing.models import WritingOocExtractionUsageError
from afterworlds.services.dnd5e_state.errors import (
    BindingRefusedError,
    StaleRevisionError,
)
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome

if TYPE_CHECKING:
    from afterworlds.models.rpg import RpgVisibleState, SheetEffect
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
    from afterworlds.pipeline.rpg.sequence import ActionResolutionService, Delivery
    from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
    from afterworlds.pipeline.rpg.visible_state import RpgVisibleStateService
    from afterworlds.pipeline.writing.models import WritingTurnRequest
    from afterworlds.pipeline.writing.ooc_config_extractor import (
        WritingOocConfigExtractorService,
    )
    from afterworlds.pipeline.writing.visible_state import WritingVisibleStateService
    from afterworlds.services.dnd5e_state.turn import RpgTurnHold, TurnCharacter
from afterworlds.pipeline._stable_prefix_renderer import RenderedBlock
from afterworlds.pipeline.contradiction.models import (
    ContradictionPassError,
    ContradictionResult,
)
from afterworlds.pipeline.contradiction.service import ContradictionService
from afterworlds.pipeline.extractor.models import ExtractorPassError, ExtractorResult
from afterworlds.pipeline.extractor.service import ExtractorService
from afterworlds.pipeline.orchestrator.models import (
    CapabilityProfileAwareSafetyPolicy,
    IntentClassifierUsage,
    OrchestrationResult,
    PipelineDisposition,
    SafetyPolicyContext,
)
from afterworlds.pipeline.planner.models import (
    PlannerPassError,
    PlannerResult,
)
from afterworlds.pipeline.planner.service import PlannerService
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderTextPart,
)
from afterworlds.pipeline.provider._protocol import ProviderAdapter
from afterworlds.pipeline.provider._resolver import ProviderResolver
from afterworlds.pipeline.provider._routing import TurnProviderBinding
from afterworlds.pipeline.provider.adapters._scoped import ScopedProviderAdapter
from afterworlds.pipeline.rolling_summary import (
    RollingSummaryPassError,
    RollingSummaryPassResult,
    RollingSummaryPassService,
)
from afterworlds.pipeline.rpg.setup_writer import RpgSetupWriterService
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
        self,
        story_id: UUID,
        current_input: str,
        story_mode: StoryMode,
        classified_intent: IntentClassificationResult,
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
            Callable[[UUID], tuple[RpgSessionState, TurnCharacter]] | None
        ) = None,
        rpg_session_resolver: Callable[[UUID], RpgSessionState | None] | None = None,
        #: CRD Issue 2b: the durable in-flight lease around RPG turns, and the
        #: post-turn processing of held rule changes and adoptions.
        rpg_turn_hold: RpgTurnHold | None = None,
        rpg_dice_service: DiceService | None = None,
        #: CRD Issue 15b: persists a turn that pauses for the Sojourner as
        #: an action-resolution sequence, gates in-character input on it and
        #: completes it on the final narration.
        rpg_sequence_service: ActionResolutionService | None = None,
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
        rolling_summary_pass_service: RollingSummaryPassService | None = None,
        rpg_setup_writer_service: RpgSetupWriterService | None = None,
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
        self._rpg_session_resolver = rpg_session_resolver
        self._rpg_turn_hold = rpg_turn_hold
        self._rpg_dice_service = rpg_dice_service
        self._rpg_sequence_service = rpg_sequence_service
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
        # ADR-006b: always present -- a due compression is never skipped.
        self._rolling_summary_pass = (
            rolling_summary_pass_service or RollingSummaryPassService()
        )
        # ADR-015c: the RPG setup Writer envelope (same WRITER pass).
        self._rpg_setup_writer = rpg_setup_writer_service or RpgSetupWriterService()
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
        writing_turn_request: WritingTurnRequest | None = None,
    ) -> OrchestrationResult:
        """Run one full Sojourn Turn, bracketed by the RPG turn lease.

        For an RPG story with the CRD Issue 2b hold wired, a durable lease is
        committed before the turn reads any character binding, so a shared rule
        change cannot activate underneath it. The lease is released once the
        turn's transaction has ended, then held changes and adoptions for the
        story are processed. A turn whose lease cannot be taken fails typed,
        before any work.
        """
        lease: str | None = None
        if self._rpg_turn_hold is not None:
            try:
                if self._mode_resolver(story_id) is StoryMode.RPG:
                    lease = self._rpg_turn_hold.acquire(story_id)
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    _synthesize_intent(user_input),
                    {},
                    time.perf_counter(),
                    f"rpg turn lease could not be taken: {exc}",
                )
        try:
            return self._orchestrate_turn(
                story_id,
                node_id,
                user_input,
                sojourner_id,
                access_path,
                request_risk_signal=request_risk_signal,
                writing_turn_request=writing_turn_request,
            )
        finally:
            if lease is not None:
                assert self._rpg_turn_hold is not None
                self._rpg_turn_hold.finish(story_id, lease)

    def _orchestrate_turn(
        self,
        story_id: UUID,
        node_id: UUID,
        user_input: str,
        sojourner_id: UUID,
        access_path: RuntimeAccessPath,
        *,
        request_risk_signal: bool = False,
        writing_turn_request: WritingTurnRequest | None = None,
    ) -> OrchestrationResult:
        """Run one full Sojourn Turn end-to-end.

        Returns a typed ``OrchestrationResult`` matching one of the eight
        ``PipelineDisposition`` values.  Construction-time invariants on
        the result enforce the spec's per-disposition field matrix.
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
        # Round 6 remediation (PR #126 P1): classification is routed through
        # `binding.adapter` (resolved in step 0), the same selected
        # hosted/BYOK access path every other pass uses -- not a standalone
        # process-hosted key. `IntentClassifierService.classify` may raise
        # the typed `IntentClassificationError` (parse / validation failure),
        # a `ProviderRefusalError` (content-policy refusal), OR any untyped
        # runtime failure from the model caller (transport error, provider
        # hiccup, etc.).
        #
        # Round 7 remediation (PR #126 P2): a `ProviderRefusalError` is now
        # caught before the broad exception handler and mapped to
        # `REFUSED_BY_PROVIDER` with `provider_refusal` populated -- the same
        # `_build_result(...)` pattern Planner/Writer/Extractor/Contradiction
        # use, per Architecture Invariant 5 ("Provider refusals are typed
        # pass failures, not Safety verdicts"). Collapsing a content-policy
        # refusal into PIPELINE_ERROR would drop `provider_refusal` and make
        # a content-policy decision look like an infrastructure failure. No
        # real `IntentClassificationResult` exists yet at this point (the
        # classifier failed before producing one), so `_synthesize_intent`
        # supplies the same neutral placeholder used by every other
        # pre-classification failure path. All other classifier failures
        # (parser/schema/transport/unexpected) still map to typed
        # PIPELINE_ERROR, unchanged.
        # Round 8 remediation (PR #126 P1): a fresh, per-turn capture -- not a
        # shared/global holder -- lets the caller below expose the classifier's
        # provider usage without a second provider call. See
        # `_ClassifierUsageCapture`.
        classifier_usage_capture = _ClassifierUsageCapture()
        try:
            intent_caller = _make_intent_classifier_caller(
                binding.adapter,  # type: ignore[arg-type]
                sojourner_id,
                classifier_usage_capture,
            )
            intent_result, classify_ms = _timed(
                lambda: self._intent_classifier.classify(
                    user_input, story_id, model_caller=intent_caller
                )
            )
            latency["intent"] = classify_ms
        except ProviderRefusalError as exc:
            return self._build_result(
                PipelineDisposition.REFUSED_BY_PROVIDER,
                _synthesize_intent(user_input),
                latency,
                turn_start,
                provider_refusal=exc.refusal,
                intent_classifier_usage=_extract_classifier_usage(
                    classifier_usage_capture
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                _synthesize_intent(user_input),
                latency,
                turn_start,
                f"intent classification failed: {exc}",
                intent_classifier_usage=_extract_classifier_usage(
                    classifier_usage_capture
                ),
            )
        # Classification succeeded, so `_call` (inside `intent_caller`) always
        # ran and populated the capture -- carried into every terminal result
        # from here on so hosted settlement can account for classifier spend.
        intent_classifier_usage = _extract_classifier_usage(classifier_usage_capture)

        def _stamp_classifier_usage(result: OrchestrationResult) -> OrchestrationResult:
            """Carry this turn's classifier usage onto a result built deep
            inside `_run_narrative`/`_run_ooc` (and everything nested under
            them) without threading a new parameter through every nested
            call site -- `model_copy` does not re-run the disposition
            validator, which is fine here since this field is additive and
            outside the disposition-population invariant matrix."""
            if intent_classifier_usage is None:
                return result
            return result.model_copy(
                update={"intent_classifier_usage": intent_classifier_usage}
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
        pre_sheet: TurnCharacter | None = None
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
                pre_session_state, pre_sheet = self._resolve_rpg_turn(story_id)
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    _rpg_resolution_failure(exc),
                )
            # The resolver enforces the character's exact recorded binding
            # (CRD Issue 2b): a stale, unpublished, quarantined or invalid
            # binding raised above and failed the turn. Which mechanics an
            # adjudicating turn selects is CRD Issue 15c's selection contract,
            # so no rule slice is requested here.

        # 2a-retrieval. Build the retrieval query request before context
        # assembly (ADR-018 D8) — orchestrator-owned and deterministic,
        # mirroring the RuleSliceRequest pattern above. This is a pre-context
        # read/query-construction step, not the post-commit Chroma
        # ingestion/write path (ADR-018 D7's best-effort swallow applies only
        # to that write path) -- a query-build failure here is a
        # context-assembly failure and must fail the turn with a typed
        # PIPELINE_ERROR, not silently proceed with retrieval memory omitted
        # (Codex review, PR #119 round 8). No configured builder at all
        # (``None``) remains a valid no-retrieval turn.
        retrieval_query_request: RetrievalQueryRequest | None = None
        if self._retrieval_query_builder is not None:
            try:
                retrieval_query_request = (
                    self._retrieval_query_builder.build_query_request(
                        story_id, user_input, story_mode, intent_result
                    )
                )
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"retrieval query construction failed: {exc}",
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

        # OOC short-circuit owns its own pipeline shape.
        # OOC while a sequence is unresolved: the gate below is deliberately
        # skipped for OOC turns (15b-31); OOC never alters the sequence.
        if intent_result.intent_type is IntentType.OOC:
            return _stamp_classifier_usage(
                self._run_ooc(
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
            )

        # Sequence-aware in-character gate (CRD Issue 15b, 15b-31): while the
        # story has an unresolved action-resolution sequence (a pending roll, a
        # pending decision, or one ready for narration), ordinary in-character
        # input is blocked and redirected. Runs before Planner, so no provider
        # call is made.
        if story_mode == StoryMode.RPG and self._rpg_sequence_service is not None:
            try:
                unresolved = self._rpg_sequence_service.unresolved(story_id)
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"action sequence lookup failed: {exc}",
                )
            if unresolved is not None:
                return self._build_result(
                    PipelineDisposition.BLOCKED_PENDING_ROLL,
                    intent_result,
                    latency,
                    turn_start,
                    pending_roll_redirect_message=unresolved.redirect_message,
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

        return _stamp_classifier_usage(
            self._run_narrative(
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
                _pre_session_state=pre_session_state,
                _pre_sheet=pre_sheet,
                _pre_branching_state=pre_branching_state,
                _pre_selected_context=pre_selected_context,
                _pre_writing_state=pre_writing_state,
                writing_turn_request=writing_turn_request,
            )
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
        _pre_session_state: RpgSessionState | None = None,
        _pre_sheet: TurnCharacter | None = None,
        _pre_branching_state: BranchingSessionState | None = None,
        _pre_selected_context: SelectedBranchContext | None = None,
        _pre_writing_state: WritingSessionState | None = None,
        writing_turn_request: WritingTurnRequest | None = None,
        story_start: bool = False,
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

        # Preallocate writer_turn_id before adjudication: a turn that starts an
        # action-resolution sequence records it as its originating turn.
        writer_turn_id = uuid4()

        # --- RPG Adjudication pass (Fork A→A1): runs after Planner, before Writer.
        # Result is held in memory and flushed inside the outer transaction (Fork B→B1).
        adj_result: AdjudicationPassResult | None = None
        rpg_session_id: UUID | None = None
        rpg_character_id: UUID | None = None
        rpg_sheet: TurnCharacter | None = None
        # Threaded to _narrative_persist for the RPG turn-retrieval-marker
        # classification (ADR-018 D6). Resolved independently of adjudication
        # wiring below (Codex #119 P2) — a story can have Retrieval Memory
        # enabled before RPG adjudication is wired, and marker classification
        # must not silently default an unresolved SETUP turn to
        # ORDINARY_NARRATIVE. Remains None only when no session/sheet
        # resolver is wired at all, or resolution fails; the marker-write
        # block below fails closed (typed PIPELINE_ERROR) in that case.
        rpg_play_status: RpgPlayStatus | None = None
        # ADR-015c: the session state this turn resolved, for setup turns.
        rpg_session_state: RpgSessionState | None = None

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
            _sh: TurnCharacter | None
            if _pre_session_state is not None:
                _ss: RpgSessionState = _pre_session_state
                _sh = _pre_sheet
            else:
                try:
                    _ss, _sh = self._resolve_rpg_turn(story_id)
                except Exception as exc:  # noqa: BLE001
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        _rpg_resolution_failure(exc),
                        input_safety_result=input_safety,
                        planner_result=planner_result,
                    )
            session_state = _ss
            rpg_session_id = session_state.session_id
            rpg_play_status = session_state.play_status
            rpg_session_state = session_state
            if _sh is not None:
                rpg_character_id = _sh.sheet_id
                rpg_sheet = _sh
            # Gate: skip adjudication for setup turns. play_status SETUP covers
            # character creation and world-setup turns that flow through
            # _run_narrative (OOC turns are already short-circuited upstream).
            # An IN_PLAY character whose recorded state is not ready for its
            # binding fails the turn typed, naming what is missing (CRD Issue
            # 2b): skipping mechanics silently would degrade the turn.
            _adj_svc = self._rpg_adjudication_service
            if session_state.play_status is RpgPlayStatus.IN_PLAY and _sh is None:
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "[missing_state] an in-play RPG story has no recorded"
                    " character state",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            sheet = _sh
            if (
                session_state.play_status is RpgPlayStatus.IN_PLAY
                and sheet is not None
                and not _adj_svc.is_adjudicable(sheet)
            ):
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    "[missing_state] rpg character state is not ready for its"
                    " rules binding: " + "; ".join(str(f) for f in sheet.readiness[:8]),
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            if session_state.play_status is RpgPlayStatus.IN_PLAY and sheet is not None:
                # Use local to narrow from DiceService | None for the lambda capture.
                _dice_svc = self._rpg_dice_service
                try:
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
                            sequences=self._rpg_sequence_service is not None,
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
                    adj_result.sequence is not None
                    or adj_result.completed_sequence is not None
                ) and self._rpg_sequence_service is None:
                    return self._pipeline_error(
                        intent_result,
                        latency,
                        turn_start,
                        "the turn needs the Sojourner's input or the event"
                        " ledger, and no action sequence service is wired to"
                        " persist it",
                        input_safety_result=input_safety,
                        planner_result=planner_result,
                        rpg_adjudication_result=adj_result,
                    )
        elif story_mode == StoryMode.RPG:
            # RPG adjudication is not wired for this story, but the mandatory
            # turn-retrieval-marker write in _narrative_persist still needs
            # rpg_play_status (ADR-018 D6), independent of adjudication
            # wiring. Reads only the durable session record; never infers
            # from Writer prose. Left None (fails closed at marker-write
            # time) if no resolver is wired or resolution fails.
            #
            # Prefers rpg_session_resolver (session-state-only) over
            # rpg_session_sheet_resolver (session+sheet): a concrete
            # recorded character state does not exist yet during RPG setup (only
            # RpgCharacterSheetBase is bootstrapped at story creation), so a
            # sheet-requiring resolver raises on every setup turn and
            # incorrectly fails this classification closed (Codex P1, PR
            # #126 round 3). rpg_session_sheet_resolver remains the fallback
            # for callers that only wire the sheet-requiring resolver (its
            # tuple's play_status half is still valid session data).
            if self._rpg_session_resolver is not None:
                try:
                    _pre_ss = self._rpg_session_resolver(story_id)
                    rpg_play_status = (
                        _pre_ss.play_status if _pre_ss is not None else None
                    )
                    rpg_session_state = _pre_ss
                except Exception:  # noqa: BLE001
                    rpg_play_status = None
            elif self._rpg_session_sheet_resolver is not None:
                try:
                    _pre_ss2, _ = self._rpg_session_sheet_resolver(story_id)
                    rpg_play_status = _pre_ss2.play_status
                    rpg_session_state = _pre_ss2
                except Exception:  # noqa: BLE001
                    rpg_play_status = None
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
                rpg_sheet=rpg_sheet,
                branching_state=_pre_branching_state,
                story_mode=story_mode,
                selected_branch_context=_pre_selected_context,
                writing_session_state=_pre_writing_state,
                writing_turn_request=writing_turn_request,
                rpg_play_status=rpg_play_status,
                rpg_session_state=rpg_session_state,
                story_start=story_start,
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
        planner_result: PlannerResult | None,
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
        rpg_sheet: TurnCharacter | None = None,
        delivery: Delivery | None = None,
        branching_state: BranchingSessionState | None = None,
        story_mode: StoryMode = StoryMode.WRITING,
        selected_branch_context: SelectedBranchContext | None = None,
        writing_session_state: WritingSessionState | None = None,
        writing_turn_request: WritingTurnRequest | None = None,
        rpg_play_status: RpgPlayStatus | None = None,
        rpg_session_state: RpgSessionState | None = None,
        story_start: bool = False,
    ) -> OrchestrationResult:
        """Writer, Output Safety, Extractor/Contradiction and the RPG delivery
        commits, inside the outer transaction: the shared delivery core of an
        ordinary turn and of an RPG resume (CRD Issue 15b, 15b-21). A resume
        passes its ready sequence's ``delivery`` and no planner result (its
        action was planned on the announce turn; ``planner_skipped``)."""
        planner_skipped = delivery is not None

        def _built(
            disposition: PipelineDisposition,
            intent: IntentClassificationResult,
            lat: dict[str, int],
            start: float,
            **kwargs: Any,
        ) -> OrchestrationResult:
            return self._build_result(
                disposition,
                intent,
                lat,
                start,
                planner_skipped=planner_skipped,
                **kwargs,
            )

        def _error(
            intent: IntentClassificationResult,
            lat: dict[str, int],
            start: float,
            summary: str,
            **kwargs: Any,
        ) -> OrchestrationResult:
            return self._pipeline_error(
                intent, lat, start, summary, planner_skipped=planner_skipped, **kwargs
            )

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
        # ADR-016b: the explicit Begin story operation runs on a story still
        # in SETUP and is routed exactly like the in-play turn it creates.
        _plays = story_start or (
            branching_state is not None
            and branching_state.play_status is BranchingPlayStatus.IN_PLAY
        )
        _branching_required = (
            story_mode is StoryMode.BRANCHING
            and branching_state is not None
            and _plays
            and branching_state.interaction_style
            in (
                InteractionStyle.HYBRID,
                InteractionStyle.TRUE_CYOA,
            )
        )
        if _branching_required and self._branching_writer_service is None:
            return _error(
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
        # writer_turn_id is pre-allocated by _run_narrative (a new id for a
        # resume) before the transaction opens.  RefusalFallbackRouter also
        # carries the same id so
        # refusal-log rows are consistent with the Turn row on success.  On
        # failure no Turn is persisted; the log row still carries the candidate id.
        branching_pass_result: _BranchingPassResult | None = None
        # ADR-015c: what Output Safety audits when it is more than the
        # delivered text (an RPG setup envelope's other visible fields).
        output_audit_text: str | None = None
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
                return _error(
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
                return _error(
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
                return _built(
                    PipelineDisposition.REFUSED_BY_PROVIDER,
                    intent_result,
                    latency,
                    turn_start,
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    provider_refusal=exc.refusal,
                )
            except BranchingPassError as exc:
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"branching writer pass failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            except Exception as exc:  # noqa: BLE001 — see boundary docstring
                return _error(
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
                return _error(
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
                return _error(
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
            # Output Safety also audits the cards the Sojourner is shown
            # (PR #204); the Turn, canon and summary keep the narrative alone.
            if _bpr.branch_options:
                output_audit_text = "\n\n".join(
                    [
                        _bpr.narrative_text,
                        *(f"Choice: {o.action_text}" for o in _bpr.branch_options),
                    ]
                )
        elif (
            story_mode is StoryMode.RPG
            and rpg_play_status is RpgPlayStatus.SETUP
            and delivery is None
        ):
            # 5a-rpg-setup (ADR-015c): the setup Writer returns a versioned
            # envelope -- visible GM text plus a phase-specific proposal --
            # on the same WRITER pass. The Turn and what it proposed (world
            # confirmation target or character candidate) commit together.
            from datetime import UTC as _SUTC  # noqa: PLC0415
            from datetime import datetime as _sdt  # noqa: PLC0415

            from afterworlds.models.turn import Turn as _STurn  # noqa: PLC0415
            from afterworlds.persistence.crud.node import (  # noqa: PLC0415
                create_turn as _screate_turn,
            )
            from afterworlds.pipeline.rpg.setup_writer import (  # noqa: PLC0415
                RpgSetupWriterError,
                visible_output,
            )
            from afterworlds.pipeline.writer.models import (  # noqa: PLC0415
                WriterResult as _SWriterResult,
            )
            from afterworlds.services import rpg_setup as _setup  # noqa: PLC0415

            _snow = _sdt.now(_SUTC).isoformat()
            try:
                _sphase, _sblock = _setup.render_setup_block(
                    session, story_id, node_id, now=_snow, state=rpg_session_state
                )
                _sres, ms = _timed(
                    lambda: self._rpg_setup_writer.write(
                        ctx,
                        _sphase,
                        _sblock,
                        provider=ScopedProviderAdapter(
                            binding.adapter,  # type: ignore[arg-type]
                            sojourner_id,
                            turn_id=writer_turn_id,
                        ),
                    )
                )
                latency["writer"] = ms
            except ProviderRefusalError as exc:
                return _built(
                    PipelineDisposition.REFUSED_BY_PROVIDER,
                    intent_result,
                    latency,
                    turn_start,
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    provider_refusal=exc.refusal,
                )
            except RpgSetupWriterError as exc:
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"rpg setup writer failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            except Exception as exc:  # noqa: BLE001 — see boundary docstring
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"rpg setup writer unexpected error: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                )
            writer_result = _SWriterResult(
                turn_id=writer_turn_id,
                assistant_output=_sres.envelope.gm_text,
                model_identifier=_sres.model_identifier or "",
                latency_ms=_sres.latency_ms,
                input_token_count=_sres.input_token_count,
                output_token_count=_sres.output_token_count,
                cache_read_token_count=_sres.cache_read_token_count,
                cache_creation_token_count=_sres.cache_creation_token_count,
                provider=_sres.provider,
                model_tier=_sres.model_tier or "",
            )
            output_audit_text = visible_output(_sres.envelope)
            try:
                _icr_s = ctx.volatile_suffix.classified_intent
                _screate_turn(
                    session,
                    _STurn(
                        turn_id=writer_turn_id,
                        user_input=ctx.volatile_suffix.current_input,
                        assistant_output=_sres.envelope.gm_text,
                        timestamp=_sdt.now(_SUTC),
                        intent_classification=IntentType(_icr_s.intent_type.value),
                        node_id=node_id,
                        intent_classification_result=_icr_s,
                    ),
                )
                _setup.apply_envelope(
                    session,
                    story_id,
                    node_id,
                    _sphase,
                    writer_turn_id,
                    _sres.envelope,
                    now=_snow,
                    state=rpg_session_state,
                )
            except Exception as exc:  # noqa: BLE001
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"rpg setup persistence failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
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
                and _plays
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
                return _built(
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
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"writer pass failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    rpg_adjudication_result=adj_result,
                )
            except Exception as exc:  # noqa: BLE001 — see boundary docstring
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"writer unexpected error: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    rpg_adjudication_result=adj_result,
                )
            # Phase G for an in-play Freeform-only beat: every narrative beat
            # replaces the choices on offer (ADR-016), and this one offers
            # none, so the anchor Node's committed card set is cleared in the
            # same transaction. Otherwise an earlier card beat's options could
            # be shown and selected again after a later switch back to a card
            # style. Fails closed like the card-beat write.
            if (
                story_mode is StoryMode.BRANCHING
                and branching_state is not None
                and _plays
                and branching_state.interaction_style is InteractionStyle.FREEFORM_ONLY
            ):
                try:
                    from afterworlds.models.node import (  # noqa: PLC0415
                        BranchingNodeMetadata as _FreeBNM,
                    )
                    from afterworlds.persistence.crud.node import (  # noqa: PLC0415
                        get_node as _free_gn,
                    )
                    from afterworlds.persistence.crud.node import (  # noqa: PLC0415
                        update_node as _free_un,
                    )

                    _free_node = _free_gn(session, node_id)
                    if _free_node is None:
                        raise RuntimeError(f"node {node_id} not found")
                    _free_mm = _free_node.mode_metadata
                    _free_node.mode_metadata = _FreeBNM(
                        pacing_stage_at_beat=(
                            _free_mm.pacing_stage_at_beat
                            if isinstance(_free_mm, _FreeBNM)
                            else None
                        ),
                        interaction_style=InteractionStyle.FREEFORM_ONLY,
                        branching_cadence=branching_state.branching_cadence,
                        freeform_available=True,
                        branch_options=[],
                    )
                    if _free_un(session, _free_node) is None:
                        raise RuntimeError(f"node {node_id} update returned no row")
                except Exception as exc:  # noqa: BLE001
                    return _error(
                        intent_result,
                        latency,
                        turn_start,
                        f"branch-card metadata persistence failed: {exc}",
                        input_safety_result=input_safety,
                        planner_result=planner_result,
                        writer_result=writer_result,
                    )

        # 5a-start: [Branching Begin story only] the SETUP -> IN_PLAY
        # transition commits with the opening Turn and its first cards
        # (ADR-016b Decision 4). Conditional on the row still being in SETUP,
        # so a concurrent start can never produce a second opening.
        if story_start:
            import sqlalchemy as _sa  # noqa: PLC0415

            from afterworlds.persistence.orm.session_state import (  # noqa: PLC0415
                BranchingSessionStateORM as _BSS,
            )

            _start_failure: str | None = None
            try:
                _promotion: _sa.CursorResult[Any] = session.execute(  # type: ignore[assignment]
                    _sa.update(_BSS)
                    .where(
                        _BSS.story_id == str(story_id),
                        _BSS.play_status == BranchingPlayStatus.SETUP.value,
                        # The opening was generated for this configuration; a
                        # setup write that landed meanwhile must not be paired
                        # with it (CRD Issue 21 round 1, F3).
                        *_start_config_clauses(_BSS, branching_state),
                    )
                    .values(play_status=BranchingPlayStatus.IN_PLAY.value)
                    .execution_options(synchronize_session=False)
                )
                if _promotion.rowcount != 1:
                    _start_failure = (
                        "the story is no longer in setup with the configuration"
                        " this opening was generated for; retry Begin story"
                    )
            except Exception as exc:  # noqa: BLE001
                _start_failure = str(exc)
            if _start_failure is not None:
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"story start transition failed: {_start_failure}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
                    branching_pass_result=branching_pass_result,
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

            # Round 13 boundary decision (owner-approved, ADR-017 Decision 9 /
            # ADR-018 D6): POST /setup no longer promotes play_status itself
            # (see api/routes/setup.py) -- a story stays SETUP after
            # structured setup until this, the setup-confirmation turn
            # classified SETUP_CONFIRMATION/NON_CANON_SUPPORT above precisely
            # because play_status was still SETUP, actually lands. Promote to
            # IN_PLAY here, in the same session/transaction as the rest of
            # this DELIVERED turn, so the transition is atomic with the
            # turn's own commit -- never speculative, never done in React.
            # Deliberately NOT inside the provenance try/except above: unlike
            # a missing audit record, a failed promotion must not be
            # silently swallowed -- that would strand the story in SETUP.
            # apply_writing_config_update's own play_status guard is a no-op
            # here if persona_id/specific_goals are somehow missing (cannot
            # happen: WritingSetupRequest always persists both together
            # before this turn is reachable), so this call cannot newly
            # corrupt the row.
            if writing_session_state.play_status is WritingPlayStatus.SETUP:
                from afterworlds.persistence.crud.session_state import (  # noqa: PLC0415
                    apply_writing_config_update as _promote_writing_play_status,
                )

                _promote_writing_play_status(
                    session, story_id, play_status=WritingPlayStatus.IN_PLAY
                )

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
            elif rpg_play_status is RpgPlayStatus.IN_PLAY:
                if adj_result is not None and adj_result.sequence is not None:
                    # The turn announces an action-resolution sequence's
                    # first interaction (CRD Issue 15b).
                    _marker_category = _RTRC.ROLL_REQUEST
                else:
                    _marker_category = _RTRC.ORDINARY_NARRATIVE
            else:
                # RpgPlayStatus is a two-value enum (SETUP, IN_PLAY); None
                # here means it could not be resolved at all -- no
                # session/sheet resolver wired, or resolution failed. Fail
                # closed rather than writing a misleading ORDINARY_NARRATIVE
                # marker for an unclassified RPG turn (Codex #119 P2).
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    "RPG turn retrieval marker classification requires"
                    " rpg_play_status, but it could not be resolved (no RPG"
                    " session/sheet resolver wired, or resolution failed)",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
                    rpg_adjudication_result=adj_result,
                    branching_pass_result=branching_pass_result,
                )
            try:
                _create_marker(
                    session,
                    turn_id=writer_turn_id,
                    story_id=story_id,
                    category=_marker_category,
                    created_at=datetime.now(UTC).isoformat(),
                )
            except Exception as exc:  # noqa: BLE001
                return _error(
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

        # 5a-2. [RPG only] Commit-time recheck (CRD Issue 2b): this turn's
        # adjudication was computed against the character's revision and exact
        # binding it read; if either moved, its work cannot commit.
        if (
            adj_result is not None
            and rpg_sheet is not None
            and self._rpg_turn_hold is not None
        ):
            try:
                self._rpg_turn_hold.recheck(session, rpg_sheet)
                # CRD Issue 15c: every other subject the turn read, too.
                for subject in adj_result.subjects:
                    self._rpg_turn_hold.recheck(session, subject)
                # And the story its discovery scans' absences rest on.
                if adj_result.discovery is not None:
                    from afterworlds.services.dnd5e_state.turn import (
                        require_story_unchanged,
                    )

                    require_story_unchanged(session, *adj_result.discovery)
            except StaleRevisionError as exc:
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"rpg character changed during the turn: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
                    rpg_adjudication_result=adj_result,
                    branching_pass_result=branching_pass_result,
                )

        # 5b. [RPG only] Inside the outer transaction (Fork B→B1): the turn's
        # adjudication audit rows; or, for a turn that paused for the Sojourner,
        # its new action-resolution sequence (CRD Issue 15b: no audit and no
        # effect yet); or, for a contest needing no player input, its completed
        # ledger and the audit derived from it (Group 17); or, for a resume,
        # the final audit derived from the sequence's event ledger and the
        # sequence completed.
        if (
            adj_result is not None
            and rpg_session_id is not None
            and rpg_character_id is not None
        ):
            sequences = self._rpg_sequence_service
            try:
                if delivery is not None:
                    assert sequences is not None  # noqa: S101 — resume requires it
                    sequences.complete(session, delivery, writer_result.turn_id)
                elif adj_result.sequence is not None:
                    assert sequences is not None  # noqa: S101 — checked pre-Writer
                    sequences.start(
                        session,
                        adj_result.sequence,
                        story_id=story_id,
                        session_id=rpg_session_id,
                        node_id=node_id,
                        character_id=rpg_character_id,
                        originating_turn_id=writer_result.turn_id,
                    )
                elif adj_result.completed_sequence is not None:
                    # Group 17: a contest needing no player input still
                    # persists its participant events; its audit rows come
                    # from them, committed with this Turn.
                    assert sequences is not None  # noqa: S101 — wired to adjudicate
                    sequences.record_completed(
                        session,
                        adj_result.completed_sequence,
                        story_id=story_id,
                        session_id=rpg_session_id,
                        node_id=node_id,
                        character_id=rpg_character_id,
                        turn_id=writer_result.turn_id,
                    )
                else:
                    self._write_rpg_audit(
                        session,
                        adj_result,
                        writer_result.turn_id,
                        story_id,
                        rpg_session_id,
                        rpg_character_id,
                    )
            except ActionResolutionError as exc:
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"[{exc.code}] action sequence write failed: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
                    rpg_adjudication_result=adj_result,
                    branching_pass_result=branching_pass_result,
                    action_sequence_error=exc.code,
                )
            except Exception as exc:  # noqa: BLE001
                return _error(
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
            from afterworlds.services.dnd5e_state.turn import ITEM_QUANTITY

            every_effect = tuple(
                effect
                for record in adj_result.proposals
                for effect in record.sheet_effects
            )
            item_effects = tuple(e for e in every_effect if e.target == ITEM_QUANTITY)
            all_effects = tuple(e for e in every_effect if e.target != ITEM_QUANTITY)
            if item_effects:
                try:
                    self._apply_item_effects(
                        session, item_effects, rpg_sheet, adj_result.subjects
                    )
                except Exception as exc:  # noqa: BLE001
                    return _error(
                        intent_result,
                        latency,
                        turn_start,
                        f"item expenditure failed: {exc}",
                        input_safety_result=input_safety,
                        planner_result=planner_result,
                        writer_result=writer_result,
                        rpg_adjudication_result=adj_result,
                        branching_pass_result=branching_pass_result,
                    )
            if all_effects:
                try:
                    # The actor's effects, however addressed, apply in order.
                    def _own(e: SheetEffect) -> bool:
                        return e.subject_id is None or (
                            e.subject_kind == "character"
                            and e.subject_id == rpg_sheet.sheet_id  # type: ignore[union-attr]
                        )

                    own = tuple(e for e in all_effects if _own(e))
                    if own:
                        rpg_sheet = self._apply_rpg_sheet_effects(
                            session, own, rpg_sheet
                        )
                    self._apply_subject_effects(
                        session,
                        tuple(e for e in all_effects if not _own(e)),
                        rpg_sheet,
                        adj_result.subjects,
                    )
                except Exception as exc:  # noqa: BLE001
                    return _error(
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
            try:
                self._commit_turn_edges(
                    session, adj_result, writer_result.turn_id, rpg_sheet.sheet_id
                )
            except Exception as exc:  # noqa: BLE001
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"actor-turn edges could not commit: {exc}",
                    input_safety_result=input_safety,
                    planner_result=planner_result,
                    writer_result=writer_result,
                    rpg_adjudication_result=adj_result,
                    branching_pass_result=branching_pass_result,
                )
            if self._rpg_visible_state_service is not None:
                try:
                    rpg_visible_state = self._rpg_visible_state_service.build(
                        rpg_sheet.stored, rpg_sheet.items
                    )
                except Exception as exc:  # noqa: BLE001
                    return _error(
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
            _audited = output_audit_text or writer_result.assistant_output
            try:
                output_safety, ms = _timed(
                    lambda: self._safety_service.check(
                        ctx,
                        _audited,
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
                return _error(
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
                return _error(
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
                return _built(
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
            return _built(
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
            return _built(
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
            return _error(
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
            return _error(
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
            return _built(
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

        # 8a. ADR-006b: record this Turn's durable Rolling Summary eligibility
        # and, when the eligible count reaches the threshold, compress inside
        # this outer transaction so Turn, canon, eligibility and the new
        # current summary commit (or roll back) together. Runs only after
        # Output Safety and the Contradiction gate have passed.
        rolling_summary_result: RollingSummaryPassResult | None = None
        if story_mode in (StoryMode.BRANCHING, StoryMode.RPG):
            from afterworlds.models.node import (  # noqa: PLC0415
                BranchingNodeMetadata as _SumBNM,
            )
            from afterworlds.models.node import (  # noqa: PLC0415
                RpgNodeMetadata as _SumRNM,
            )
            from afterworlds.persistence.crud.node import (  # noqa: PLC0415
                update_turn_mode_metadata as _set_turn_mm,
            )
            from afterworlds.services.rolling_summary import (  # noqa: PLC0415
                RollingSummaryService,
            )

            if story_mode is StoryMode.BRANCHING:
                _eligible = story_start or (
                    branching_state is not None
                    and branching_state.play_status is BranchingPlayStatus.IN_PLAY
                )
                _turn_mm: _SumBNM | _SumRNM = _SumBNM(
                    rolling_summary_eligible=_eligible
                )
            else:
                # A turn announcing a pending roll/decision is not narrative
                # delivery; its resume narration (no new sequence) is.
                _eligible = rpg_play_status is RpgPlayStatus.IN_PLAY and not (
                    adj_result is not None and adj_result.sequence is not None
                )
                _turn_mm = _SumRNM(rolling_summary_eligible=_eligible)
            _summary_upstream: dict[str, Any] = {
                "input_safety_result": input_safety,
                "planner_result": planner_result,
                "writer_result": writer_result,
                "output_safety_result": output_safety,
                "rpg_adjudication_result": adj_result,
                "branching_pass_result": branching_pass_result,
                # Completed before the summary: kept on any non-delivered
                # result for audit (never settled; ADR-006b D5).
                "extractor_result": extractor_result,
                "contradiction_result": contradiction_result,
            }
            try:
                if not _set_turn_mm(session, writer_result.turn_id, _turn_mm):
                    raise RuntimeError(f"turn {writer_result.turn_id} not found")
            except Exception as exc:  # noqa: BLE001
                return _error(
                    intent_result,
                    latency,
                    turn_start,
                    f"rolling summary eligibility write failed: {exc}",
                    **_summary_upstream,
                )
            if _eligible:
                _summary_calls: list[RollingSummaryPassResult] = []
                _summary_provider = ScopedProviderAdapter(
                    binding.adapter,  # type: ignore[arg-type]
                    sojourner_id,
                    turn_id=writer_result.turn_id,
                )

                def _generate(prior: str | None, window: list[str]) -> str:
                    try:
                        produced = self._rolling_summary_pass.summarize(
                            ctx, prior, window, provider=_summary_provider
                        )
                    except RollingSummaryPassError as exc:
                        if exc.usage is not None:
                            _summary_calls.append(exc.usage)
                        raise
                    _summary_calls.append(produced)
                    return produced.summary_text

                try:
                    _, ms = _timed(
                        lambda: RollingSummaryService(
                            session, generator=_generate
                        ).advance_if_due(story_id)
                    )
                    if _summary_calls:
                        latency["rolling_summary"] = ms
                except ProviderRefusalError as exc:
                    return _built(
                        PipelineDisposition.REFUSED_BY_PROVIDER,
                        intent_result,
                        latency,
                        turn_start,
                        provider_refusal=exc.refusal,
                        **_summary_upstream,
                    )
                except RollingSummaryPassError as exc:
                    return _error(
                        intent_result,
                        latency,
                        turn_start,
                        f"rolling summary pass failed: {exc}",
                        rolling_summary_result=exc.usage,
                        **_summary_upstream,
                    )
                except Exception as exc:  # noqa: BLE001
                    return _error(
                        intent_result,
                        latency,
                        turn_start,
                        f"rolling summary persistence failed: {exc}",
                        rolling_summary_result=(
                            _summary_calls[-1] if _summary_calls else None
                        ),
                        **_summary_upstream,
                    )
                rolling_summary_result = _summary_calls[-1] if _summary_calls else None

        # Build branching visible state for BRANCHING-mode DELIVERED turns.
        branching_visible_state = None
        if (
            story_mode is StoryMode.BRANCHING
            and branching_state is not None
            and self._branching_visible_state_service is not None
        ):
            try:
                branching_visible_state = self._branching_visible_state_service.build(
                    (
                        branching_state.model_copy(
                            update={"play_status": BranchingPlayStatus.IN_PLAY}
                        )
                        if story_start
                        else branching_state
                    ),
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
        return _built(
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
            rolling_summary_result=rolling_summary_result,
        )

    # ------------------------------------------------------------------
    # Branching Begin story (ADR-016b)
    # ------------------------------------------------------------------

    def orchestrate_branching_start(
        self,
        story_id: UUID,
        node_id: UUID,
        sojourner_id: UUID,
        access_path: RuntimeAccessPath,
        *,
        request_risk_signal: bool = False,
    ) -> OrchestrationResult:
        """Generate the first playable beat of a configured Branching story.

        The explicit start operation (ADR-016b): it carries no Sojourner text,
        so its intent is code-owned and fixed before context assembly (the
        RPG resume precedent, 15b-22). Context is assembled once, with a
        code-owned ``story_start`` frame; the ordinary narrative path then
        runs Planner, the style's Writer, conditional Safety, Extractor and
        Contradiction, and commits the opening Turn, its first cards and the
        SETUP -> IN_PLAY transition together. A story no longer in setup is
        refused before any provider call (the route answers that as a no-op).
        """
        from afterworlds.services.rolling_summary import (  # noqa: PLC0415
            STORY_START_INPUT,
        )

        turn_start = time.perf_counter()
        latency: dict[str, int] = {}
        intent_result = IntentClassificationResult(
            intent_type=IntentType.BEAT_MILESTONE,
            confidence=1.0,
            raw_input=STORY_START_INPUT,
            ambiguous=False,
        )
        if self._branching_session_resolver is None:
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                "branching session resolver not wired for story start",
            )
        try:
            state = self._branching_session_resolver(story_id)
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"branching session resolution failed: {exc}",
            )
        if state is None or state.play_status is not BranchingPlayStatus.SETUP:
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                "story start requires a Branching story still in setup",
            )
        try:
            binding = self._provider_resolver.resolve_for_turn(
                access_path, sojourner_id
            )
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"provider resolution failed: {exc}",
            )
        retrieval_query_request: RetrievalQueryRequest | None = None
        if self._retrieval_query_builder is not None:
            try:
                retrieval_query_request = (
                    self._retrieval_query_builder.build_query_request(
                        story_id, STORY_START_INPUT, StoryMode.BRANCHING, intent_result
                    )
                )
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    intent_result,
                    latency,
                    turn_start,
                    f"retrieval query construction failed: {exc}",
                )
        try:
            ctx, _, ctx_ms = self._build_context(
                story_id,
                STORY_START_INPUT,
                intent_result,
                mode=StoryMode.BRANCHING,
                retrieval_query_request=retrieval_query_request,
            )
            latency["context"] = ctx_ms
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                intent_result, latency, turn_start, f"context assembly failed: {exc}"
            )
        ctx.pass_forward_ledger.add("story_start", _story_start_frame(state))
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
            StoryMode.BRANCHING,
            _pre_branching_state=state,
            story_start=True,
        )

    # ------------------------------------------------------------------
    # RPG resume (CRD Issue 15b, ADR-015b Group 8)
    # ------------------------------------------------------------------

    def orchestrate_rpg_resume(
        self,
        story_id: UUID,
        node_id: UUID,
        sequence_id: UUID,
        *,
        access_path: RuntimeAccessPath,
        sojourner_id: UUID,
        request_risk_signal: bool = False,
    ) -> OrchestrationResult:
        """Narrate a ready action-resolution sequence: the only path that
        turns its committed mechanics into a delivered Turn (15b-21).

        Before any provider call, the sequence must exist in *story_id*, be
        ready, and have been declared at *node_id*, the story's current
        canonical node the caller resolves as for ordinary turns (15b-23).
        Each refusal is a PIPELINE_ERROR whose ``action_sequence_error``
        carries its typed code, ``ACTION_SEQUENCE_ALREADY_COMPLETED`` included
        (15b-32's success-equivalent mapping is the product layer's).

        The turn then runs the ordinary access path and the shared delivery
        core (:meth:`_narrative_persist`) with the binding's refusal-buffering
        hooks: no Planner (planned on the announce turn), no Input Preflight
        and no intent classification (15b-22, no new Sojourner text). Context
        is the originating input, a code-owned continuation frame and the
        sequence's visibility-filtered views (15b-24). The final audit (from
        the event ledger), the effects, the sequence's completion and the Turn
        commit together; a blocked or failed narration rolls them back and
        leaves the ready sequence and its ledger as they were (15b-34).
        """
        lease: str | None = None
        if self._rpg_turn_hold is not None:
            try:
                lease = self._rpg_turn_hold.acquire(story_id)
            except Exception as exc:  # noqa: BLE001
                return self._pipeline_error(
                    _synthesize_intent(""),
                    {},
                    time.perf_counter(),
                    f"rpg turn lease could not be taken: {exc}",
                    planner_skipped=True,
                )
        try:
            return self._resume(
                story_id,
                node_id,
                sequence_id,
                access_path=access_path,
                sojourner_id=sojourner_id,
                request_risk_signal=request_risk_signal,
            )
        finally:
            if lease is not None:
                assert self._rpg_turn_hold is not None  # noqa: S101
                self._rpg_turn_hold.finish(story_id, lease)

    def _resume(
        self,
        story_id: UUID,
        node_id: UUID,
        sequence_id: UUID,
        *,
        access_path: RuntimeAccessPath,
        sojourner_id: UUID,
        request_risk_signal: bool,
    ) -> OrchestrationResult:
        turn_start = time.perf_counter()
        latency: dict[str, int] = {}
        placeholder = _synthesize_intent("")
        sequences = self._rpg_sequence_service
        if sequences is None:
            return self._pipeline_error(
                placeholder,
                latency,
                turn_start,
                "no action sequence service is wired",
                planner_skipped=True,
            )
        try:
            delivery = sequences.prepare_delivery(story_id, sequence_id, node_id)
        except ActionResolutionError as exc:
            return self._pipeline_error(
                placeholder,
                latency,
                turn_start,
                f"[{exc.code}] {exc}",
                planner_skipped=True,
                action_sequence_error=exc.code,
            )
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                placeholder,
                latency,
                turn_start,
                f"action sequence read failed: {exc}",
                planner_skipped=True,
            )
        bundle = delivery.bundle
        intent_result = _synthesize_resume_intent(bundle.originating_user_input)
        try:
            binding = self._provider_resolver.resolve_for_turn(
                access_path, sojourner_id
            )
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"provider resolution failed: {exc}",
                planner_skipped=True,
            )
        try:
            ctx, _, ctx_ms = self._build_context(
                story_id,
                bundle.originating_user_input,
                intent_result,
                mode=StoryMode.RPG,
            )
            latency["context"] = ctx_ms
        except Exception as exc:  # noqa: BLE001
            return self._pipeline_error(
                intent_result,
                latency,
                turn_start,
                f"context assembly failed: {exc}",
                planner_skipped=True,
            )
        adj_result = AdjudicationPassResult(
            proposals=delivery.records,
            writer_views=bundle.writer_views,
            subjects=tuple(delivery.prepared.subjects.values()),
            coordination=delivery.prepared.coordination,
            discovery=delivery.prepared.discovery,
        )
        if adj_result.writer_views:
            ctx.pass_forward_ledger.add(
                "rpg_adjudication", _serialize_adj_views(adj_result)
            )
        # The code-owned continuation frame (15b-24): system-authored, no new
        # Sojourner prose, and no mechanical fact (those are the views above).
        ctx.pass_forward_ledger.add("rpg_resume_continuation", _CONTINUATION_FRAME)
        result = self._run_with_transaction(
            lambda session: self._narrative_persist(
                session,
                ctx,
                story_id,
                node_id,
                sojourner_id,
                intent_result,
                None,
                None,
                binding,
                request_risk_signal,
                latency,
                turn_start,
                writer_turn_id=uuid4(),
                adj_result=adj_result,
                rpg_session_id=bundle.session_id,
                rpg_character_id=bundle.character_id,
                rpg_sheet=delivery.prepared.sheet,
                delivery=delivery,
                story_mode=StoryMode.RPG,
                rpg_play_status=RpgPlayStatus.IN_PLAY,
            ),
            intent_result,
            latency,
            turn_start,
            success_disposition=PipelineDisposition.DELIVERED,
            pre_transaction_fn=binding.pre_transaction_fn,
            post_transaction_fn=binding.post_transaction_fn,
        )
        self._maybe_ingest_retrieval_memory(result, story_id, StoryMode.RPG)
        return result

    # ------------------------------------------------------------------
    # OOC path
    # ------------------------------------------------------------------

    def _build_rpg_ooc_state(self, story_id: UUID) -> str | None:
        """Build a player-visible RPG state payload for the OOC handler ledger.

        Returns None when rpg_session_sheet_resolver is not wired (graceful
        degrade — OOC prompt instructs the model to say it lacks state).
        Raises on resolver or service failure; caller maps to PIPELINE_ERROR.

        Allowlisted fields only — never serialises the full sheet or a
        sequence's stored authority; a pending interaction appears only as its
        player-visible redirect text (CRD Issue 15b).
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
            visible = self._rpg_visible_state_service.build(sheet.stored, sheet.items)
        else:
            visible = None
        if visible is not None:
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
        if self._rpg_sequence_service is not None:
            unresolved = self._rpg_sequence_service.unresolved(story_id)
            if unresolved is not None:
                parts += [
                    "",
                    "## Pending Interaction",
                    f"state: {unresolved.interaction_phase.value}",
                    f"instruction: {unresolved.redirect_message}",
                ]
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

                # ADR-016b: an in-play story may not become True CYOA (style
                # switch or range change) unless its committed card set is
                # selectable under the effective range -- configuration does
                # not generate cards. Keep the playable configuration and say
                # so, as for the other suppressed changes above.
                if _bss_row is None:
                    _bss_row = _get_bss(session, story_id)
                if (
                    _bss_row is not None
                    and _bss_row.play_status is BranchingPlayStatus.IN_PLAY
                ):
                    from afterworlds.models.node import (  # noqa: PLC0415
                        BranchingNodeMetadata as _OocBNM,
                    )
                    from afterworlds.persistence.crud.node import (  # noqa: PLC0415
                        get_node as _ooc_gn,
                    )
                    from afterworlds.pipeline.branching.config import (  # noqa: PLC0415
                        true_cyoa_unplayable_reason as _tc_reason,
                    )

                    _eff_style = _apply_style or _bss_row.interaction_style
                    _eff_range = (
                        None
                        if _should_clear_range
                        else _validated_range or _bss_row.branch_count_range
                    )
                    _anchor = _ooc_gn(session, node_id)
                    _anchor_mm = _anchor.mode_metadata if _anchor else None
                    _committed = (
                        len(_anchor_mm.branch_options)
                        if isinstance(_anchor_mm, _OocBNM)
                        else 0
                    )
                    _why = _tc_reason(_eff_style, _eff_range, _committed)
                    if _why is not None and (
                        _apply_style is not None or _validated_range is not None
                    ):
                        _apply_style = None
                        _validated_range = None
                        _ooc_style_noop_note = (
                            "[Interaction style and branch-count range not"
                            f" changed: {_why}.]"
                        )
                        _ooc_range_noop_note = None

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
    ) -> None:
        """Write one ``RpgRollAuditORM`` row per resolved record inside the
        outer transaction (Fork B→B1), for a turn resolved without a sequence.
        Rolled back atomically with the Turn on any block. A sequence's final
        audit is derived from its event ledger instead (CRD Issue 15b)."""
        from datetime import UTC, datetime

        from afterworlds.persistence.orm.rpg import RpgRollAuditORM

        now_str = datetime.now(tz=UTC).isoformat()
        if any(r.contest_resolution is not None for r in adj_result.proposals):
            # Group 17: a contest is audited per participant from its events
            # (``record_completed``), never as one record row.
            from afterworlds.pipeline.rpg.models import ActionSequenceIntegrityError

            raise ActionSequenceIntegrityError(
                "a contest reached the record audit path: its participants are "
                "audited from the event ledger"
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
                        [e.model_dump(mode="json") for e in record.sheet_effects]
                    ),
                    created_at=now_str,
                )
            )

    def _resolve_rpg_turn(
        self, story_id: UUID
    ) -> tuple[RpgSessionState, TurnCharacter | None]:
        """The RPG session state, and the bound character when in play.

        CRD Issue 15c wires adjudication in production, so a setup turn must
        not require recorded character state that setup has not created yet:
        the session-only resolver decides play status first, and the
        binding-enforcing sheet resolver runs only for an in-play story. With
        no session-only resolver wired, the sheet resolver decides both.
        """
        assert self._rpg_session_sheet_resolver is not None  # noqa: S101
        if self._rpg_session_resolver is not None:
            state = self._rpg_session_resolver(story_id)
            if state is None:
                raise ValueError(f"no RpgSessionState for story {story_id}")
            if state.play_status is not RpgPlayStatus.IN_PLAY:
                return state, None
        return self._rpg_session_sheet_resolver(story_id)

    # ------------------------------------------------------------------
    # RPG sheet-effect application (Fork B→B1)
    # ------------------------------------------------------------------

    def _apply_rpg_sheet_effects(
        self,
        session: Session,
        effects: tuple[SheetEffect, ...],
        character: TurnCharacter,
    ) -> TurnCharacter:
        """Apply sheet effects to the typed character state inside the outer
        transaction, by compare-and-swap (CRD Issue 2b).

        The write commits only if the character's revision and exact binding
        are still the ones this turn read. No current-HP floor is applied
        (ADR-0003). Unknown or ambiguous targets fail closed (raise); callers
        map that to a pipeline error so the outer transaction rolls back Turn,
        audit rows and mutations atomically.
        """
        from dataclasses import replace
        from datetime import UTC, datetime

        from afterworlds.services.dnd5e_state import service, store
        from afterworlds.services.dnd5e_state.effects import apply_effects

        stored = character.stored
        new_state = apply_effects(stored.state, effects)
        service.check_references(session, stored.story_id, new_state)
        store.save_state(
            session,
            "character",
            stored.sheet_id,
            new_state,
            expected_revision=stored.revision,
            expected_binding=stored.binding,
            now=datetime.now(tz=UTC).isoformat(),
        )
        refreshed = store.get_character(session, stored.sheet_id)
        if refreshed is None:
            raise ValueError(f"character {stored.sheet_id} vanished during the turn")
        return replace(character, stored=refreshed)

    @staticmethod
    def _commit_turn_edges(
        session: Session,
        adj_result: AdjudicationPassResult,
        turn_id: UUID,
        actor_id: UUID,
    ) -> None:
        """Replay the records' actor-turn edges onto the coordination the turn
        read and commit them with the Turn (CRD Issue 15c, contract G1). A
        concurrent change raises, so the outer transaction rolls back."""
        from datetime import UTC, datetime

        from afterworlds.models.dnd5e_state import SubjectReference
        from afterworlds.services.dnd5e_state import coordination

        read = adj_result.coordination
        if read is None:
            return
        document = read.document
        edges = []
        begun = False
        del actor_id  # every use names its subject
        for record in adj_result.proposals:
            for use in record.turn_uses:
                document, used = coordination.use_event(
                    document,
                    SubjectReference(kind=use.by.kind, subject_id=use.by.subject_id),
                    use.key,
                )
                edges.append(used)
            if record.turn_edge is None:
                continue
            ref = record.turn_edge.subject
            document, edge = coordination.apply_edge(
                document,
                record.turn_edge.kind,
                SubjectReference(kind=ref.kind, subject_id=ref.subject_id),
                begun_this_turn=begun,
            )
            begun = begun or edge.kind == "begin"
            edges.append(edge)
        coordination.commit(
            session,
            read,
            document,
            tuple(edges),
            turn_id=turn_id,
            now=datetime.now(tz=UTC).isoformat(),
        )

    @staticmethod
    def _apply_item_effects(
        session: Session,
        effects: tuple[SheetEffect, ...],
        actor: TurnCharacter,
        subjects: tuple[object, ...],
    ) -> None:
        """Expend held items (ammunition) the turn's records spent (CRD Issue
        15c), each by compare-and-swap against the revision the turn read it
        at; the last one removes the holding. Raises on an item the turn did
        not read or a moved revision, so the outer transaction rolls back."""
        from afterworlds.services.dnd5e_state.holdings import spend_item

        read = {
            str(i.item_id): i
            for holder in (actor, *subjects)
            for i in getattr(holder, "items", ())
        }
        spend: dict[str, int] = {}
        for effect in effects:
            value = json.loads(effect.value_json)
            spend[value["item_id"]] = spend.get(value["item_id"], 0) + int(
                value["spend"]
            )
        for item_id, count in spend.items():
            item = read.get(item_id)
            if item is None:
                raise ValueError(f"item {item_id} was not read by this turn")
            spend_item(
                session, item.item_id, expected_revision=item.revision, count=count
            )

    def _apply_subject_effects(
        self,
        session: Session,
        effects: tuple[SheetEffect, ...],
        actor: TurnCharacter,
        subjects: tuple[object, ...],
    ) -> None:
        """Apply subject-addressed effects (CRD Issue 15c), each subject by
        compare-and-swap against the revision and exact binding the turn read
        it at. An effect for a subject the turn did not read fails closed, so
        the outer transaction rolls back Turn, audit rows and every mutation.
        """
        from datetime import UTC, datetime

        from afterworlds.services.dnd5e_state import service, store
        from afterworlds.services.dnd5e_state.effects import apply_effects
        from afterworlds.services.dnd5e_state.turn import TurnCreature

        read: dict[tuple[str, str], object] = {
            ("character", str(actor.sheet_id)): actor
        }
        for subject in subjects:
            kind = "creature" if isinstance(subject, TurnCreature) else "character"
            read[(kind, str(subject.subject_id))] = subject  # type: ignore[attr-defined]
        grouped: dict[tuple[str, str], list[SheetEffect]] = {}
        for effect in effects:
            key = (str(effect.subject_kind), str(effect.subject_id))
            if key not in read:
                raise ValueError(f"an effect names {key}, which this turn did not read")
            grouped.setdefault(key, []).append(effect)
        now = datetime.now(tz=UTC).isoformat()
        for (kind, _), group in grouped.items():
            subject = read[(kind, _)]
            stored = subject.stored  # type: ignore[attr-defined]
            new_state = apply_effects(stored.state, tuple(group))
            service.check_references(session, stored.story_id, new_state)
            store.save_state(
                session,
                kind,
                stored.subject_id,
                new_state,
                expected_revision=stored.revision,
                expected_binding=stored.binding,
                now=now,
            )

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
        intent_classifier_usage: IntentClassifierUsage | None = None,
        planner_skipped: bool = False,
        action_sequence_error: str | None = None,
        rolling_summary_result: RollingSummaryPassResult | None = None,
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
            rolling_summary_result,
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
            intent_classifier_usage=intent_classifier_usage,
            planner_skipped=planner_skipped,
            action_sequence_error=action_sequence_error,
            rolling_summary_result=rolling_summary_result,
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
        intent_classifier_usage: IntentClassifierUsage | None = None,
        planner_skipped: bool = False,
        action_sequence_error: str | None = None,
        rolling_summary_result: RollingSummaryPassResult | None = None,
        extractor_result: ExtractorResult | None = None,
        contradiction_result: ContradictionResult | None = None,
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
            extractor_result=extractor_result,
            contradiction_result=contradiction_result,
            pipeline_error_summary=summary,
            rpg_adjudication_result=rpg_adjudication_result,
            branching_pass_result=branching_pass_result,
            intent_classifier_usage=intent_classifier_usage,
            planner_skipped=planner_skipped,
            action_sequence_error=action_sequence_error,
            rolling_summary_result=rolling_summary_result,
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
                    # ADR-006b: a compression that ran is audit evidence too.
                    rolling_summary_result=inner_result.rolling_summary_result,
                    planner_skipped=inner_result.planner_skipped,
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
            from afterworlds.persistence.crud.retrieval import (
                get_turn_for_eligibility,
            )
            from afterworlds.pipeline.retrieval.eligibility import (
                gather_turn_eligibility_for_turn,
            )

            session = self._session_factory()
            try:
                # get_turn_for_eligibility (not the general-purpose get_turn)
                # so a Writing turn with malformed persisted mode_metadata
                # resolves cleanly to ineligible/not-ingested instead of
                # raising here and being masked by this method's outer D7
                # best-effort swallow (Codex review, PR #119).
                turn = get_turn_for_eligibility(session, result.turn_id)
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


def _synthesize_resume_intent(user_input: str) -> IntentClassificationResult:
    """The code-owned intent of an RPG resume (CRD Issue 15b, 15b-22): the
    originating in-character action, never a classifier result."""
    return IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=1.0,
        raw_input=user_input,
        ambiguous=False,
    )


def _start_config_clauses(orm: Any, state: BranchingSessionState | None) -> list[Any]:
    """SQL conditions matching the Branching configuration a Begin story
    opening was generated for (``IS NULL`` for an unset field)."""
    if state is None:
        return []
    clauses: list[Any] = []
    for column, value in (
        (orm.interaction_style, state.interaction_style),
        (orm.branching_cadence, state.branching_cadence),
        (orm.branch_count_range, state.branch_count_range),
        (orm.length_preference, state.length_preference),
    ):
        clauses.append(column.is_(None) if value is None else column == value.value)
    return clauses


def _story_start_frame(state: BranchingSessionState) -> str:
    """The code-owned frame of a Branching Begin story opening (ADR-016b):
    persisted setup context only, no Sojourner prose and no invented choice."""
    lines = [
        "[Story Start]",
        "This turn is the explicit Begin story operation: write the opening "
        "scene of this story. No player action or choice has happened yet; "
        "do not invent one. Ground the opening in the Story Bible and the "
        "persisted setup context below.",
    ]
    for label, value in (
        ("world_summary", state.world_summary),
        ("story_seeds", state.story_seeds),
        ("character_concept", state.character_concept),
        ("supporting_cast", state.supporting_cast),
        ("world_constraints", state.world_constraints),
        ("pacing_notes", state.pacing_notes),
        ("acceptable_content", state.acceptable_content),
    ):
        if value:
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


#: The code-owned continuation frame of an RPG resume (15b-24).
_CONTINUATION_FRAME = (
    "[Action Resolution]\n"
    "This turn narrates the outcome of the Sojourner's action above, whose "
    "mechanics are now resolved. No new input arrived from the Sojourner. "
    "Narrate the whole action once, from the resolved facts in the "
    "rpg_adjudication block; add no mechanic of your own."
)


_INTENT_CLASSIFIER_MAX_TOKENS = 256


class _ClassifierUsageCapture:
    """Per-turn holder for the Intent Classifier's most recent provider result.

    A fresh instance is created per call to ``_make_intent_classifier_caller``
    (once per turn, in ``orchestrate_turn``) -- never a shared/global instance,
    so concurrent turns never see each other's usage (Round 8 remediation,
    PR #126 P1).
    """

    def __init__(self) -> None:
        self.result: ProviderCallResult | None = None


def _make_intent_classifier_caller(
    adapter: ProviderAdapter, sojourner_id: UUID, usage_capture: _ClassifierUsageCapture
) -> Callable[[str], str]:
    """Build a ``ModelCallerT`` that routes Intent Classification through the
    turn's already-resolved provider adapter.

    Architecture Note (Round 6 remediation, PR #126 P1): Intent Classification
    is a model call, so it must be mediated by the selected access path like
    every other pass -- a standalone process-hosted key bypassing
    ``TurnProviderBinding`` would let a BYOK turn silently spend a
    hosted/server key outside the Sojourner's BYOK pool. ``ScopedProviderAdapter``
    fills sojourner_id (Issue 14a refusal-log scoping) exactly as the other
    passes do; no second, hidden provider resolver is created here.

    Round 8 remediation (PR #126 P1): the raw ``ProviderCallResult`` is
    written to ``usage_capture`` so the caller can carry its usage into
    ``OrchestrationResult.intent_classifier_usage`` for hosted settlement --
    without this, classifier tokens were spent through the selected provider
    but never accounted for.
    """
    scoped = ScopedProviderAdapter(adapter, sojourner_id)

    def _call(prompt: str) -> str:
        request = ProviderCallRequest(
            pass_id=PipelinePassId.INTENT_CLASSIFIER,
            rendered_blocks=[RenderedBlock(text=prompt)],
            max_output_tokens=_INTENT_CLASSIFIER_MAX_TOKENS,
        )
        result = scoped.call(request)
        usage_capture.result = result
        text_parts = [
            part.text
            for part in result.content_parts
            if isinstance(part, ProviderTextPart)
        ]
        if not text_parts:
            raise IntentClassificationError(
                "Provider returned no text content for intent classification"
            )
        return text_parts[0]

    return _call


def _extract_classifier_usage(
    usage_capture: _ClassifierUsageCapture,
) -> IntentClassifierUsage | None:
    """Convert a captured classifier ``ProviderCallResult`` to the narrow
    usage snapshot carried on ``OrchestrationResult``. ``None`` if
    classification never reached a provider result (e.g. refused before
    responding)."""
    result = usage_capture.result
    if result is None:
        return None
    return IntentClassifierUsage(
        pass_id=result.pass_id,
        provider=result.provider_name,
        model_identifier=result.model_identifier,
        model_tier=result.model_tier,
        input_token_count=result.input_token_count,
        output_token_count=result.output_token_count,
        cache_read_token_count=result.cache_read_token_count,
        cache_creation_token_count=result.cache_creation_token_count,
        latency_ms=result.latency_ms,
    )


def _rpg_resolution_failure(exc: Exception) -> str:
    """The typed, visible message for a failed RPG session/sheet resolution.

    CRD Issue 15c (AC5): a stale binding is distinguishable from missing or
    unpublished authority; any other failure is reported as it is.
    """
    if isinstance(exc, BindingRefusedError):
        kind = (
            "stale_binding"
            if exc.outcome is AuthorityOutcome.STALE
            else "missing_authority"
        )
        return f"[{kind}] RPG session/sheet resolution failed: {exc}"
    return f"RPG session/sheet resolution failed: {exc}"


def _serialize_adj_views(adj_result: AdjudicationPassResult) -> str:
    """Serialize adjudication writer views for the pass-forward ledger.

    Produces a JSON string that the Writer pass reads from the ledger key
    ``"rpg_adjudication"``.  The ``pending_player_roll_instruction`` field is
    set only when the turn starts an action-resolution sequence, so the Writer
    asks the Sojourner for what it needs (their roll or decision) and narrates
    no result (CRD Issue 15b).
    """
    views_data = [json.loads(v.model_dump_json()) for v in adj_result.writer_views]
    pending_instruction: str | None = None
    if adj_result.sequence is not None:
        pending_instruction = adj_result.writer_views[0].player_facing_summary
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
