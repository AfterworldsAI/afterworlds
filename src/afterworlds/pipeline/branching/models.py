"""Typed payloads and exceptions for the Branching Writer pass — CRD Issue 16."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from afterworlds.models.enums import (
    BranchCountRange,
    BranchingCadence,
    BranchPresentationState,
    InteractionRejectionReason,
    InteractionStyle,
    LengthPreference,
)


class ProposedBranchOption(BaseModel):
    """Branch option as proposed by the model via forced tool use.

    The model proposes ``action_text`` only.  ``option_id`` is code-assigned
    after validation; it must not appear in the tool schema.
    """

    action_text: str


class BranchOption(BaseModel):
    """Branch option with code-assigned identity, ready for delivery.

    ``option_id`` is assigned by code (sequential ``opt_1``, ``opt_2``, …).
    ``action_text`` comes from the model proposal after range validation.
    """

    option_id: str
    action_text: str


class BranchingWriterProposal(BaseModel):
    """Raw output from the forced-tool call, before code stamps config fields.

    Fields the model may propose:
    - ``narrative_text``: prose narrative for this beat.
    - ``branch_options_text``: list of action labels for presented branch options.
      The model proposes prose labels only; option_id is code-assigned.
    - ``branch_presentation_state``: whether to show, hold, or omit branch cards
      this beat.  Code validates against session state.
    - ``pacing_stage_hint``: optional advisory hint about current arc stage.
      Code does not trust this; it is advisory context only.

    Fields the model must NOT propose (enforced by schema shape — absent from
    the tool input_schema):
    - interaction_style (code-owned from session state)
    - branching_cadence (code-owned from session state)
    - freeform_available (code-derived from interaction_style)
    - branch_count_range (code-owned from session state)
    - option_id for any option (code-assigned sequential)
    """

    narrative_text: str
    branch_options_text: list[str]
    branch_presentation_state: str
    pacing_stage_hint: str | None = None


class BranchingPassResult(BaseModel):
    """Complete result returned by ``BranchingWriterService.write()``.

    Code stamps all affordance fields from session state after validating the
    model's proposal.  The model contributes only ``narrative_text`` and the
    action-text labels for branch options.

    ``branch_options`` is empty for ``FREEFORM_ONLY`` turns (which bypass
    this service entirely and use the prose Writer).
    """

    narrative_text: str
    interaction_style: InteractionStyle
    branching_cadence: BranchingCadence
    length_preference: LengthPreference | None
    freeform_available: bool
    branch_count_range: BranchCountRange | None
    branch_options: list[BranchOption]
    branch_presentation_state: str

    provider: str | None = None
    model_identifier: str | None = None
    model_tier: str | None = None
    latency_ms: int = 0
    input_token_count: int | None = None
    output_token_count: int | None = None
    cache_read_token_count: int | None = None
    cache_creation_token_count: int | None = None


class BranchingPassError(Exception):
    """Fail-closed exception for the Branching Writer pass.

    Covers: no tool_use block, tool name mismatch, malformed proposal output,
    branch-count range violation, provider exception, and schema validation
    failure.  No DB state is committed when this is raised.
    """


# ---------------------------------------------------------------------------
# Branch-selection validation
# ---------------------------------------------------------------------------


class BranchSelectionValidationVerdict(StrEnum):
    """Outcome of validating a BRANCH_CHOICE input against the current card set."""

    ACCEPT = "accept"
    REJECT = "reject"


class BranchSelectionValidationResult(BaseModel):
    """Result of validating a Sojourner's branch selection.

    Populated after resolving a BRANCH_CHOICE intent against the most-recently-
    presented option set.  On ACCEPT, ``selected_context`` is populated and
    passed forward to the Writer.  On REJECT, ``rejection_reason`` and
    ``rejection_message`` are populated for INTERACTION_REJECTED routing.
    """

    model_config = ConfigDict(extra="forbid")

    verdict: BranchSelectionValidationVerdict
    selected_context: SelectedBranchContext | None = None
    rejection_reason: InteractionRejectionReason | None = None
    rejection_message: str | None = None


class SelectedBranchContext(BaseModel):
    """Volatile pass-forward payload for a validated branch selection.

    Created on ACCEPT from branch-selection validation; threaded through to
    the Writer so the narrative can reference the chosen branch.

    IMPORTANT invariants:
    - Never use as a stable prefix or cache key (volatile per turn).
    - Never persist to Node or Story Bible directly — use Node.branching_logic
      for realized selection edges and Node.mode_metadata.branching for
      selection metadata.
    """

    model_config = ConfigDict(extra="forbid")

    option_id: str
    action_text: str
    annotation: str | None = None


# ---------------------------------------------------------------------------
# OOC config update
# ---------------------------------------------------------------------------


class BranchingConfigUpdate(BaseModel):
    """Structured config changes extracted by the OOC handler (CRD Issue 16).

    Produced via forced-tool OOC pass when the Sojourner requests a branching
    config update (e.g. "switch to Hybrid mode", "give me more branches").
    All fields are optional; only non-None fields are applied.

    Validation against ``ALLOWED_RANGES_BY_STYLE`` happens before persistence.
    Transaction-scoped: commits only with OOC_HANDLED; rolls back on any
    Output Safety block, provider refusal, or error.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    interaction_style: InteractionStyle | None = None
    branching_cadence: BranchingCadence | None = None
    branch_count_range: BranchCountRange | None = None
    length_preference: LengthPreference | None = None


# ---------------------------------------------------------------------------
# OOC config extractor result
# ---------------------------------------------------------------------------


class BranchingOocConfigExtractorResult(BaseModel):
    """Result from the OOC config extractor pass (CRD Issue 16 Phase F).

    Wraps the extracted config update with provider usage metrics so the
    entitlement layer can include this pass in credit settlement.
    """

    model_config = ConfigDict(extra="forbid")

    config_update: BranchingConfigUpdate
    provider: str | None = None
    model_identifier: str | None = None
    model_tier: str | None = None
    latency_ms: int = 0
    input_token_count: int | None = None
    output_token_count: int | None = None
    cache_read_token_count: int | None = None
    cache_creation_token_count: int | None = None


# ---------------------------------------------------------------------------
# Branching visible state
# ---------------------------------------------------------------------------


class BranchingVisibleState(BaseModel):
    """Structured branching session state surfaced in OrchestrationResult.

    Populated by ``BranchingVisibleStateService`` on every DELIVERED
    BRANCHING-mode turn.  Carries the current config and the most-recently-
    presented branch options so the frontend can render the branch card.

    ``schema_version`` allows forward-compatible reads by callers.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    interaction_style: InteractionStyle
    branching_cadence: BranchingCadence
    branch_count_range: BranchCountRange | None
    freeform_available: bool
    length_preference: LengthPreference | None
    last_branch_options: list[BranchOption] | None = None
    last_presentation_state: BranchPresentationState | None = None


__all__ = [
    "BranchOption",
    "BranchingConfigUpdate",
    "BranchingOocConfigExtractorResult",
    "BranchingPassError",
    "BranchingPassResult",
    "BranchingVisibleState",
    "BranchingWriterProposal",
    "BranchSelectionValidationResult",
    "BranchSelectionValidationVerdict",
    "ProposedBranchOption",
    "SelectedBranchContext",
]
