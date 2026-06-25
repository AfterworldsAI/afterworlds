"""Orchestrator typed shapes and execution policy — CRD Issue 12c / 14a.

This module defines the exhaustive disposition enum, the typed
``OrchestrationResult`` produced by ``OrchestratorService.orchestrate_turn``,
and the ``OrchestratorError`` raised when a result is constructed with invalid
field combinations.

Issue 14a: ``SafetyPolicy`` (12c) is replaced by
``CapabilityProfileAwareSafetyPolicy`` from ``pipeline.provider._routing``.
``SafetyPolicy`` is re-exported here for import compatibility with existing
tests; new code should import ``CapabilityProfileAwareSafetyPolicy`` directly.

The disposition-population invariants table in Issue 12c is enforced at
``OrchestrationResult`` construction time via a Pydantic ``model_validator``.
Violation always raises ``OrchestratorError`` — never silently coerces the
result into a different disposition.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from afterworlds.models.enums import InteractionRejectionReason
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.rpg import RpgVisibleState
from afterworlds.pipeline._refusal import ProviderRefusal
from afterworlds.pipeline.contradiction.models import (
    ContradictionResult,
    ContradictionVerdict,
)
from afterworlds.pipeline.extractor.models import ExtractorResult
from afterworlds.pipeline.planner.models import PlannerResult
from afterworlds.pipeline.provider._routing import (
    CapabilityProfileAwareSafetyPolicy,
    SafetyPolicyContext,
)
from afterworlds.pipeline.rpg.models import AdjudicationPassResult
from afterworlds.pipeline.safety.models import SafetyResult, SafetyVerdict
from afterworlds.pipeline.writer.models import WriterResult

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Disposition enum
# ---------------------------------------------------------------------------


class PipelineDisposition(StrEnum):
    """Exhaustive terminal states of a Sojourn Turn (Issue 12c).

    Adding a new disposition is a load-bearing change: it requires a new
    value here, a new entry in the result-population invariant validator on
    ``OrchestrationResult``, and a corresponding test in the disposition
    matrix.  See Issue 12c "Architectural Invariants to Enforce" #7.
    """

    DELIVERED = "delivered"
    OOC_HANDLED = "ooc_handled"
    BLOCKED_INPUT_SAFETY = "blocked_input_safety"
    BLOCKED_OUTPUT_SAFETY = "blocked_output_safety"
    BLOCKED_CONTRADICTION = "blocked_contradiction"
    BLOCKED_PENDING_ROLL = "blocked_pending_roll"
    INTERACTION_REJECTED = "interaction_rejected"
    REFUSED_BY_PROVIDER = "refused_by_provider"
    PIPELINE_ERROR = "pipeline_error"


# ---------------------------------------------------------------------------
# Orchestrator error
# ---------------------------------------------------------------------------


class OrchestratorError(Exception):
    """Raised when an ``OrchestrationResult`` is constructed with invalid
    field combinations.

    This is an architectural-invariant guardrail — it is not raised in
    response to provider, Safety, or Contradiction outcomes.  It indicates
    that the orchestrator (or a test) built a result whose field set does
    not match the spec's invariants for its disposition.
    """


# ---------------------------------------------------------------------------
# OrchestrationResult
# ---------------------------------------------------------------------------


class OrchestrationResult(BaseModel):
    """Typed result returned by ``OrchestratorService.orchestrate_turn``.

    Population invariants per Issue 12c "Disposition-population invariants"
    table are enforced at construction time.  Building a result that does
    not match the table for its disposition raises ``OrchestratorError``.
    The orchestrator never silently coerces a refused or blocked turn into
    ``DELIVERED`` / ``OOC_HANDLED`` by manipulating field absence.
    """

    model_config = ConfigDict(extra="forbid")

    disposition: PipelineDisposition
    delivered_output: str | None
    turn_id: UUID | None

    intent_classification: IntentClassificationResult
    input_safety_result: SafetyResult | None = None
    planner_result: PlannerResult | None = None
    writer_result: WriterResult | None = None
    output_safety_result: SafetyResult | None = None
    extractor_result: ExtractorResult | None = None
    contradiction_result: ContradictionResult | None = None

    provider_refusal: ProviderRefusal | None = None
    pipeline_error_summary: str | None = None

    total_latency_ms: int
    pass_latency_breakdown: dict[str, int]

    # Additive Issue 14a field: True iff any pass reported a cache read.
    # Issue 19 uses this for optional "resuming your story" UX.
    stable_prefix_cache_warmed: bool = False

    # Additive Issue 15 fields: populated for RPG in-play turns only.
    # None for all non-RPG turns and for RPG setup/OOC turns.
    rpg_adjudication_result: AdjudicationPassResult | None = None
    rpg_visible_state: RpgVisibleState | None = None

    # Set on BLOCKED_PENDING_ROLL: the player_facing_instruction from the
    # PendingRollRequest that the Sojourner must resolve before proceeding.
    # None on all other dispositions.
    pending_roll_redirect_message: str | None = None

    # Set on INTERACTION_REJECTED: typed reason and human-readable message why
    # the input was rejected (non-billable; no Turn, no Node, no canon mutation).
    # Both are None on all other dispositions; both are required (non-empty) on
    # INTERACTION_REJECTED per CRD Issue 16.
    interaction_rejection_reason: InteractionRejectionReason | None = None
    interaction_rejection_message: str | None = None

    # Additive Issue 16 field: full structured branching output for HYBRID/TRUE_CYOA
    # turns.  Populated in place of writer_result for those modes; None otherwise.
    # Type is BranchingPassResult from pipeline.branching.models — declared as Any
    # here to avoid an import cycle; narrowed to BranchingPassResult by callers.
    branching_pass_result: Any | None = None

    # Additive Issue 16 field: branching session visible state for DELIVERED
    # BRANCHING-mode turns.  None for all non-BRANCHING turns and non-DELIVERED
    # dispositions.  Type is BranchingVisibleState from pipeline.branching.models —
    # declared as Any here to avoid an import cycle.
    branching_visible_state: Any | None = None

    @model_validator(mode="after")
    def _enforce_disposition_invariants(self) -> OrchestrationResult:
        """Enforce the per-disposition required / forbidden field matrix.

        Implements the table in Issue 12c "Disposition-population
        invariants".  Each branch checks both required positive fields and
        forbidden field combinations.  Failures raise OrchestratorError so
        the orchestrator (or a buggy test) cannot smuggle an inconsistent
        result past the type boundary.

        **Single canonical terminal-cause channel (Codex P2 #87):** every
        disposition must populate at most one of ``provider_refusal`` /
        ``pipeline_error_summary``.  That one-channel rule is enforced
        family-wide here so downstream analytics, support reconstruction,
        and entitlement routing (Issue 13) can always resolve "why did this
        turn end?" from a single field without ambiguity:

        | Disposition              | provider_refusal | pipeline_error_summary |
        |--------------------------|------------------|------------------------|
        | DELIVERED                | forbid           | forbid                 |
        | OOC_HANDLED              | forbid           | forbid                 |
        | BLOCKED_INPUT_SAFETY     | forbid           | forbid                 |
        | BLOCKED_OUTPUT_SAFETY    | forbid           | forbid                 |
        | BLOCKED_CONTRADICTION    | forbid           | forbid                 |
        | BLOCKED_PENDING_ROLL     | forbid           | forbid                 |
        | REFUSED_BY_PROVIDER      | require          | forbid                 |
        | PIPELINE_ERROR           | forbid           | require                |
        """
        # Import deferred to avoid circulars: IntentType lives next to enums
        # that may transitively import models that import this module.
        from afterworlds.models.enums import IntentType

        d = self.disposition
        is_ooc = self.intent_classification.intent_type == IntentType.OOC

        # rpg_visible_state and branching_visible_state are only valid on
        # successfully-delivered turns.
        if d is not PipelineDisposition.DELIVERED:
            self._forbid(
                "rpg_visible_state absent on non-DELIVERED",
                self.rpg_visible_state is not None,
            )
            self._forbid(
                "branching_visible_state absent on non-DELIVERED",
                self.branching_visible_state is not None,
            )

        if d is PipelineDisposition.DELIVERED:
            self._require(
                "delivered_output non-empty", self._non_empty_str(self.delivered_output)
            )
            self._require("turn_id present", self.turn_id is not None)
            self._require("planner_result present", self.planner_result is not None)
            self._require("writer_result present", self.writer_result is not None)
            self._require("extractor_result present", self.extractor_result is not None)
            self._require(
                "contradiction_result present", self.contradiction_result is not None
            )
            assert self.contradiction_result is not None
            self._require(
                "contradiction verdict CLEAR",
                self.contradiction_result.verdict is ContradictionVerdict.CLEAR,
            )
            self._forbid("provider_refusal absent", self.provider_refusal is not None)
            self._forbid(
                "pipeline_error_summary absent",
                self.pipeline_error_summary is not None,
            )

        elif d is PipelineDisposition.OOC_HANDLED:
            self._require(
                "delivered_output non-empty", self._non_empty_str(self.delivered_output)
            )
            self._require("turn_id present", self.turn_id is not None)
            self._require("writer_result present", self.writer_result is not None)
            self._require("intent is OOC", is_ooc)
            self._forbid(
                "planner_result absent on OOC", self.planner_result is not None
            )
            self._forbid(
                "extractor_result absent on OOC", self.extractor_result is not None
            )
            self._forbid(
                "contradiction_result absent on OOC",
                self.contradiction_result is not None,
            )
            self._forbid("provider_refusal absent", self.provider_refusal is not None)
            self._forbid(
                "pipeline_error_summary absent",
                self.pipeline_error_summary is not None,
            )

        elif d is PipelineDisposition.BLOCKED_INPUT_SAFETY:
            self._require("delivered_output is None", self.delivered_output is None)
            self._require("turn_id is None", self.turn_id is None)
            self._require(
                "input_safety_result present", self.input_safety_result is not None
            )
            assert self.input_safety_result is not None
            self._require(
                "input safety verdict BLOCK",
                self.input_safety_result.verdict is SafetyVerdict.BLOCK,
            )
            self._forbid(
                "planner_result absent before input block",
                self.planner_result is not None,
            )
            self._forbid("writer_result absent", self.writer_result is not None)
            self._forbid(
                "output_safety_result absent",
                self.output_safety_result is not None,
            )
            self._forbid("extractor_result absent", self.extractor_result is not None)
            self._forbid(
                "contradiction_result absent",
                self.contradiction_result is not None,
            )
            self._forbid(
                "provider_refusal absent on input-safety block",
                self.provider_refusal is not None,
            )
            self._forbid(
                "pipeline_error_summary absent on input-safety block",
                self.pipeline_error_summary is not None,
            )

        elif d is PipelineDisposition.BLOCKED_OUTPUT_SAFETY:
            self._require("delivered_output is None", self.delivered_output is None)
            self._require("turn_id is None", self.turn_id is None)
            self._require("writer_result present", self.writer_result is not None)
            self._require(
                "output_safety_result present",
                self.output_safety_result is not None,
            )
            assert self.output_safety_result is not None
            self._require(
                "output safety verdict BLOCK",
                self.output_safety_result.verdict is SafetyVerdict.BLOCK,
            )
            if is_ooc:
                self._forbid(
                    "planner_result absent on OOC output-block",
                    self.planner_result is not None,
                )
            else:
                self._require(
                    "planner_result present on narrative output-block",
                    self.planner_result is not None,
                )
            self._forbid(
                "extractor_result absent on output block",
                self.extractor_result is not None,
            )
            self._forbid(
                "contradiction_result absent on output block",
                self.contradiction_result is not None,
            )
            self._forbid(
                "provider_refusal absent on output-safety block",
                self.provider_refusal is not None,
            )
            self._forbid(
                "pipeline_error_summary absent on output-safety block",
                self.pipeline_error_summary is not None,
            )

        elif d is PipelineDisposition.BLOCKED_CONTRADICTION:
            self._require("delivered_output is None", self.delivered_output is None)
            self._require("turn_id is None", self.turn_id is None)
            self._require("writer_result present", self.writer_result is not None)
            self._require(
                "contradiction_result present",
                self.contradiction_result is not None,
            )
            assert self.contradiction_result is not None
            self._require(
                "contradiction verdict BLOCKED",
                self.contradiction_result.verdict is ContradictionVerdict.BLOCKED,
            )
            self._require("planner_result present", self.planner_result is not None)
            # extractor_result may be present (extraction completed under
            # SAVEPOINT) — the SAVEPOINT plus outer transaction rolls back
            # those writes when Contradiction blocks.
            self._forbid(
                "provider_refusal absent on contradiction block",
                self.provider_refusal is not None,
            )
            self._forbid(
                "pipeline_error_summary absent on contradiction block",
                self.pipeline_error_summary is not None,
            )

        elif d is PipelineDisposition.BLOCKED_PENDING_ROLL:
            self._require("delivered_output is None", self.delivered_output is None)
            self._require("turn_id is None", self.turn_id is None)
            self._require(
                "pending_roll_redirect_message present",
                self._non_empty_str(self.pending_roll_redirect_message),
            )
            self._forbid("planner_result absent", self.planner_result is not None)
            self._forbid("writer_result absent", self.writer_result is not None)
            self._forbid("extractor_result absent", self.extractor_result is not None)
            self._forbid(
                "contradiction_result absent",
                self.contradiction_result is not None,
            )
            self._forbid(
                "provider_refusal absent on pending-roll block",
                self.provider_refusal is not None,
            )
            self._forbid(
                "pipeline_error_summary absent on pending-roll block",
                self.pipeline_error_summary is not None,
            )

        elif d is PipelineDisposition.INTERACTION_REJECTED:
            # Non-billable: no Turn, no Node, no canon mutation.
            # Modeled on BLOCKED_PENDING_ROLL per 12c extension procedure.
            self._require("delivered_output is None", self.delivered_output is None)
            self._require("turn_id is None", self.turn_id is None)
            self._require(
                "interaction_rejection_reason non-empty",
                self.interaction_rejection_reason is not None,
            )
            self._require(
                "interaction_rejection_message non-empty",
                self._non_empty_str(self.interaction_rejection_message),
            )
            self._forbid("planner_result absent", self.planner_result is not None)
            self._forbid("writer_result absent", self.writer_result is not None)
            self._forbid("extractor_result absent", self.extractor_result is not None)
            self._forbid(
                "contradiction_result absent",
                self.contradiction_result is not None,
            )
            self._forbid(
                "pending_roll_redirect_message absent on INTERACTION_REJECTED",
                self.pending_roll_redirect_message is not None,
            )
            self._forbid(
                "provider_refusal absent on INTERACTION_REJECTED",
                self.provider_refusal is not None,
            )
            self._forbid(
                "pipeline_error_summary absent on INTERACTION_REJECTED",
                self.pipeline_error_summary is not None,
            )

        elif d is PipelineDisposition.REFUSED_BY_PROVIDER:
            self._require("delivered_output is None", self.delivered_output is None)
            self._require("turn_id is None", self.turn_id is None)
            self._require("provider_refusal present", self.provider_refusal is not None)
            # Spec: "failing pass result is None; upstream results preserved".
            # Map ProviderRefusal.pass_identifier → the corresponding result
            # field on this model.  The pass that refused must not have left
            # a populated result behind.
            assert self.provider_refusal is not None
            from afterworlds.pipeline._refusal import PassIdentifier

            failing_field_by_pass: dict[PassIdentifier, object] = {
                PassIdentifier.PLANNER: self.planner_result,
                PassIdentifier.RPG_ADJUDICATION: self.rpg_adjudication_result,
                PassIdentifier.BRANCHING_WRITER: self.branching_pass_result,
                PassIdentifier.WRITER: self.writer_result,
                PassIdentifier.EXTRACTOR: self.extractor_result,
                PassIdentifier.CONTRADICTION: self.contradiction_result,
            }
            failing_value = failing_field_by_pass.get(
                self.provider_refusal.pass_identifier
            )
            self._forbid(
                "failing pass result must be None on REFUSED_BY_PROVIDER",
                failing_value is not None,
            )
            # Single canonical terminal-cause channel: refusal carries the
            # cause, pipeline_error_summary must NOT also be populated.
            self._forbid(
                "pipeline_error_summary absent on REFUSED_BY_PROVIDER",
                self.pipeline_error_summary is not None,
            )

        elif d is PipelineDisposition.PIPELINE_ERROR:
            self._require("delivered_output is None", self.delivered_output is None)
            self._require("turn_id is None", self.turn_id is None)
            self._require(
                "pipeline_error_summary present",
                self.pipeline_error_summary is not None,
            )
            # Single canonical terminal-cause channel: pipeline_error_summary
            # carries the cause, provider_refusal must NOT also be populated
            # (refusal is its own disposition).
            self._forbid(
                "provider_refusal absent on PIPELINE_ERROR",
                self.provider_refusal is not None,
            )

        return self

    # ------------------------------------------------------------------
    # Internal validator helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _non_empty_str(value: str | None) -> bool:
        return value is not None and bool(value)

    @staticmethod
    def _require(label: str, condition: bool) -> None:
        if not condition:
            raise OrchestratorError(
                f"OrchestrationResult invariant failed: required — {label}"
            )

    @staticmethod
    def _forbid(label: str, condition: bool) -> None:
        if condition:
            raise OrchestratorError(
                f"OrchestrationResult invariant failed: forbidden — {label}"
            )


# 12c compatibility alias — new code should import CapabilityProfileAwareSafetyPolicy.
SafetyPolicy = CapabilityProfileAwareSafetyPolicy

__all__ = [
    "CapabilityProfileAwareSafetyPolicy",
    "InteractionRejectionReason",
    "OrchestrationResult",
    "OrchestratorError",
    "PipelineDisposition",
    "SafetyPolicy",
    "SafetyPolicyContext",
]
