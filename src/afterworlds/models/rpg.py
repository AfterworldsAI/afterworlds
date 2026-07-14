"""RPG adjudication DTOs and visible-state payload — CRD Issue 15.

These models are the typed boundaries between the RPG Adjudication Loop,
the d20 Rules System Adapter, the Writer pass, and the Sojourner-facing
visible-state surface.

Architectural invariants enforced here:
- ``RollProposal`` carries no result, no DC, no numeric modifier field.
  Roll-authorship enforcement is structural: the schema makes it physically
  impossible for a model to embed a trust-relevant number in a proposal.
- ``ResolvedAdjudicationRecord`` is immutable (frozen=True) and carries the
  full mechanical audit payload.  It is INTERNAL — never exposed directly to
  the Writer or the Sojourner.
- ``WriterAdjudicationView`` is the visibility-filtered Writer-facing record.
  For HIDDEN rolls, ``total``, ``dc``, and ``outcome`` are None.
- ``hidden_modifier_present`` on ``PendingRollRequest`` is INTERNAL ONLY and
  must never appear in any player-facing output, prompt, or DTO.
- ``RpgVisibleState`` is character-visible only; hidden state excluded by
  construction.

CRD Issue 15b additions (structured roll instructions, action-resolution
sequences, player-roll lifecycle completion — see ADR-015b):
- ``RollInstructionSnapshot``/``RollTerm`` are authoritative; human-readable
  expressions (``display_expression``) are display/diagnostic text only.
- Player-visible projections (``PlayerRollInstructionView`` and friends) omit
  every backend-only field — ``RollAdjustmentOption.ability_id`` in particular
  never appears in ``PlayerAdjustmentOptionView``.
- ``ActionResolutionSequence`` persists one declared action or mechanically
  linked action group; at most one pending interaction (roll XOR decision)
  per sequence.
- ``PendingRollRequest`` is revised per ADR-015b's Column Disposition table:
  legacy display/derivation fields are retired in favor of
  ``instruction_snapshot_json``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from afterworlds.models.enums import (
    ActionResolutionStatus,
    ConditionVisibility,
    DiceSelectionRule,
    ModifierVisibility,
    ResolvedStepKind,
    RollAdjustmentTiming,
    RollContribution,
    RollPurpose,
    RollSubmissionSource,
    RollVisibility,
    RpgInteractionPhase,
    SequenceInteractionKind,
)

# ---------------------------------------------------------------------------
# Roll proposal DTOs (model-emitted; no trust-relevant numbers)
# ---------------------------------------------------------------------------


class RollProposal(BaseModel):
    """A single roll proposed by the adjudication pass model.

    Schema-level invariant: no result, DC, or numeric modifier field exists.
    A model cannot author a trust-relevant number because the schema provides
    no field to embed one.  ``difficulty_reference_note`` is a non-authoritative
    textual hint only — it is never used as a DC by the adapter.
    """

    model_config = ConfigDict(extra="forbid")

    check_label: str
    subsystem_tag: str
    skill_or_attribute_label: str | None = None
    visible_modifier_note: str | None = None
    difficulty_reference_note: str | None = None
    visibility: RollVisibility


class AdjudicationProposalOutput(BaseModel):
    """Structured output from the RPG_ADJUDICATION model pass.

    This is the tool-use / structured-output target.  The adapter resolves
    each ``RollProposal`` into a ``ResolvedAdjudicationRecord``; the model's
    output is advisory only.
    """

    model_config = ConfigDict(extra="forbid")

    rolls: list[RollProposal]
    reasoning_note: str | None = None


# ---------------------------------------------------------------------------
# Dice service result
# ---------------------------------------------------------------------------


class DiceResult(BaseModel):
    """Immutable result from a single ``DiceService.roll`` call.

    ``raw_rolls`` contains all individual die values.  ``chosen`` is the
    single value after keep-highest or keep-lowest selection (for advantage /
    disadvantage); for a straight roll it equals ``raw_rolls[0]``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    expression: str
    raw_rolls: tuple[int, ...]
    chosen: int


# ---------------------------------------------------------------------------
# Sheet effect (code-derived mechanical mutation)
# ---------------------------------------------------------------------------


class SheetEffect(BaseModel):
    """A single authoritative mechanical mutation to apply to the character sheet.

    Sheet effects are derived by code from ``ResolvedAdjudicationRecord`` via
    the d20 adapter — never from model output.

    Operations:
    - ``delta`` — add ``value_json`` (integer, may be negative) to ``target``
    - ``set`` — set ``target`` to the literal value in ``value_json``
    - ``apply_condition`` — add a condition to the sheet-owned condition list;
      ``value_json`` is a JSON object with condition metadata
    - ``clear_condition`` — remove matching condition from the sheet-owned list;
      ``value_json`` is a JSON object with the condition identifier to remove
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    target: str
    operation: Literal["delta", "set", "apply_condition", "clear_condition"]
    value_json: str
    schema_version: Literal[1] = 1


# ---------------------------------------------------------------------------
# Resolved adjudication record (INTERNAL — full mechanical/audit payload)
# ---------------------------------------------------------------------------


class ResolvedAdjudicationRecord(BaseModel):
    """Internal authoritative record of a resolved RPG roll.

    NEVER exposed to the Writer or the Sojourner directly.  Feeds
    ``rpg_roll_audit`` rows and ``sheet_effects`` only.

    ``gm_cheating_at_roll`` is a snapshot of the session config at resolution
    time; it is immutable once set.  When ``gm_cheating_at_roll=False`` (i.e.
    ``gm_cheating = off``), this record is the absolute source of truth for
    outcome and sheet mutations — Writer prose cannot override it.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    check_label: str
    visibility: RollVisibility
    expression: str
    raw_rolls: tuple[int, ...]
    modifiers_json: str
    total: int
    dc: int | None = None
    outcome: Literal[
        "success", "failure", "critical_success", "critical_failure", "undetermined"
    ]
    sheet_effects: tuple[SheetEffect, ...]
    source: Literal["ai", "hidden", "player"]
    gm_cheating_at_roll: bool


# ---------------------------------------------------------------------------
# Writer-facing adjudication view (visibility-filtered)
# ---------------------------------------------------------------------------


class WriterAdjudicationView(BaseModel):
    """Visibility-filtered view of a resolved roll, passed to the Writer.

    For HIDDEN rolls: ``total``, ``dc``, and ``outcome`` are None.
    The Writer receives only what the character perceives.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    check_label: str
    visibility: RollVisibility
    player_facing_summary: str
    total: int | None = None
    dc: int | None = None
    outcome: (
        Literal[
            "success", "failure", "critical_success", "critical_failure", "undetermined"
        ]
        | None
    ) = None


# ---------------------------------------------------------------------------
# Pending roll request (player-roll announce / consume lifecycle)
# ---------------------------------------------------------------------------


class PendingRollRequest(BaseModel):
    """Persisted state for a player-roll request, linked to its sequence.

    Revised per ADR-015b's Column Disposition table (CRD Issue 15b). The
    display/derivation fields the v1 implementation carried directly —
    ``roll_expression``, ``expected_value_shape``, ``visible_modifier_total``,
    ``visible_modifier_breakdown_json``, ``check_label``,
    ``player_facing_instruction``, ``visible_modifier_note``,
    ``hidden_modifier_present`` — are retired in favor of one structured
    ``instruction_snapshot_json``; display text derives from the snapshot.

    New rows require ``sequence_id``/``step_id``/``instruction_id``/
    ``instruction_revision``/``instruction_schema_version``/
    ``instruction_snapshot_json``. Legacy consumed rows may retain nullable
    sequence/instruction linkage.

    ``adapter_context_hash`` surfaces sheet-state drift between announce and
    consume.  In v1, a mismatch produces a diagnostic but does NOT trigger
    recomputation or changed resolution.
    """

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    story_id: UUID
    session_id: UUID
    character_id: UUID
    visibility: RollVisibility
    source_proposal_ref: str
    originating_turn_id: UUID
    consumed_turn_id: UUID | None = None
    status: Literal["pending", "consumed", "cancelled", "expired"] = "pending"
    created_at: datetime
    schema_version: Literal[1] = 1
    adapter_context_hash: str | None = None

    sequence_id: UUID | None = None
    step_id: UUID | None = None
    instruction_id: UUID | None = None
    instruction_revision: int | None = None
    instruction_schema_version: int | None = None
    instruction_snapshot_json: str | None = None


# ---------------------------------------------------------------------------
# Roll Instruction Contract (CRD Issue 15b — authoritative structured roll)
# ---------------------------------------------------------------------------


class RollTerm(BaseModel):
    """One independently meaningful dice term within a RollInstructionSnapshot.

    Enforced here: bounded positive ``count``/``sides``; ``keep_count`` only
    set for keep operations, and then ``1 <= keep_count <= count``. Adapter
    approval for supported dice/operations is a caller concern (the adapter
    decides which shapes it will *generate*), not this model's — this model
    only rejects shapes that could never be legal for any adapter. This model
    does not execute arbitrary formulas.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    term_id: UUID
    count: int = Field(gt=0)
    sides: int = Field(gt=0)
    selection_rule: DiceSelectionRule
    keep_count: int | None = None
    contribution: RollContribution = RollContribution.ADD
    label: str | None = None

    @model_validator(mode="after")
    def keep_count_matches_selection_rule(self) -> Self:
        if self.selection_rule is DiceSelectionRule.SUM_ALL:
            if self.keep_count is not None:
                raise ValueError(
                    f"keep_count must be None for selection_rule=SUM_ALL, "
                    f"got {self.keep_count}"
                )
            return self
        if self.keep_count is None:
            raise ValueError(
                f"keep_count is required for selection_rule={self.selection_rule.value}"
            )
        if not (1 <= self.keep_count <= self.count):
            raise ValueError(
                f"keep_count ({self.keep_count}) must be between 1 and "
                f"count ({self.count})"
            )
        return self


class RollModifierComponent(BaseModel):
    """One code-owned integer modifier contributing to a RollInstructionSnapshot total.

    ``visibility`` gates whether this component may appear in
    ``PlayerModifierView`` — HIDDEN components are never surfaced player-side.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    modifier_id: UUID
    label: str
    value: int
    visibility: ModifierVisibility
    source_kind: str
    source_reference: str | None = None


class RollAdjustmentOption(BaseModel):
    """A typed, backend-derived adjustment a Sojourner may apply to a pending roll.

    V1 selection is a stable ``option_id`` only, no typed parameters (15b-10)
    — see the "Parameterized adjustments" Known Unknown for mechanics that
    would need more than that. ``ability_id`` is backend-only and must never
    appear in ``PlayerAdjustmentOptionView``.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    option_id: str
    ability_id: str
    timing: RollAdjustmentTiming
    player_visible_label: str
    resource_preview: str | None = None


class RollInstructionSnapshot(BaseModel):
    """The authoritative structured roll instruction (CRD Issue 15b).

    Human-readable ``display_expression``/``display_label`` are display and
    diagnostic text only — never the resolution authority. Supersedes the
    v1 ``roll_expression`` string per ADR-015b.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    instruction_id: UUID
    instruction_revision: int
    purpose: RollPurpose

    terms: tuple[RollTerm, ...]
    modifier_components: tuple[RollModifierComponent, ...]

    display_expression: str
    display_label: str

    source_rule_refs: tuple[str, ...]
    adjustment_options: tuple[RollAdjustmentOption, ...]

    sequence_id: UUID
    step_id: UUID

    dc: int | None = None
    """Code-verified difficulty/target value (ADR-015b 15b-34).

    ``None`` for rolls with no compare-outcome and, in v1, for every roll —
    no Rules Package entity carries a DC field yet (see the "Rules Package
    DC-data-modeling gap" Known Unknown). Backend-only; never appears in
    ``PlayerRollInstructionView``.
    """


# ---------------------------------------------------------------------------
# Player-visible contracts (CRD Issue 15b — hidden state excluded by construction)
# ---------------------------------------------------------------------------


class PlayerRollTermView(BaseModel):
    """Player-visible projection of a RollTerm — no backend-only fields."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    term_id: UUID
    count: int
    sides: int
    selection_rule: DiceSelectionRule
    keep_count: int | None = None
    contribution: RollContribution
    label: str | None = None


class PlayerModifierView(BaseModel):
    """Player-visible projection of a PLAYER_VISIBLE RollModifierComponent only."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    modifier_id: UUID
    label: str
    value: int


class PlayerAdjustmentOptionView(BaseModel):
    """Player-visible projection of a RollAdjustmentOption.

    ``ability_id`` is deliberately absent — it is backend-only.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    option_id: str
    player_visible_label: str
    resource_preview: str | None = None


class SequenceProgressView(BaseModel):
    """Player-visible progress marker within an ActionResolutionSequence.

    ``step_index`` is 1-based. ``known_step_count`` may be ``None`` where
    later steps depend on unresolved outcomes.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    step_index: int
    known_step_count: int | None = None
    step_label: str | None = None
    sequence_label: str | None = None


class PlayerRollInstructionView(BaseModel):
    """Player-visible projection of a RollInstructionSnapshot for a pending roll.

    No hidden value, hidden-modifier-existence flag, hidden target, internal
    rule reference, adapter hash, or backend-only identity may enter this DTO.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    pending_roll_request_id: UUID
    sequence_id: UUID
    instruction_id: UUID
    instruction_revision: int

    purpose: RollPurpose
    interaction_phase: Literal[RpgInteractionPhase.PENDING_ROLL]
    progress: SequenceProgressView

    display_label: str
    display_expression: str
    terms: tuple[PlayerRollTermView, ...]
    visible_modifiers: tuple[PlayerModifierView, ...]
    visible_modifier_total: int

    adjustment_options: tuple[PlayerAdjustmentOptionView, ...]


class MechanicalDecisionOption(BaseModel):
    """One selectable option for a pending mechanical decision."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    option_id: str
    player_visible_label: str


class PendingMechanicalDecisionView(BaseModel):
    """Player-visible pending mechanical decision within an ActionResolutionSequence."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    decision_request_id: UUID
    sequence_id: UUID
    interaction_phase: Literal[RpgInteractionPhase.PENDING_MECHANICAL_DECISION]
    prompt: str
    options: tuple[MechanicalDecisionOption, ...]
    decision_revision: int


class MechanicalDecisionOptionSnapshot(BaseModel):
    """One backend-authoritative option within a MechanicalDecisionSnapshot.

    ADR-015b 15b-35.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    option_id: str
    player_visible_label: str
    source_rule_ref: str | None = None
    provisional_effects_json: str


class MechanicalDecisionSnapshot(BaseModel):
    """The authoritative structured mechanical-decision instruction (ADR-015b 15b-35).

    Mirrors ``RollInstructionSnapshot``'s snapshot/revision pattern for the
    decision interaction kind.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    decision_id: UUID
    decision_revision: int
    prompt: str
    options: tuple[MechanicalDecisionOptionSnapshot, ...]
    source_rule_refs: tuple[str, ...]
    sequence_id: UUID
    step_id: UUID


class MechanicalDecisionSubmission(BaseModel):
    """Player selection of one MechanicalDecisionSnapshot option (ADR-015b 15b-35)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    decision_request_id: UUID
    expected_decision_revision: int
    option_id: str


class ActionResolutionAdvanceResult(BaseModel):
    """Result of one ActionResolutionService advancement call.

    Exactly one payload matching ``interaction_phase`` is populated, except
    ``READY_FOR_NARRATION``, which carries neither. An accepted adjustment
    returns the revised ``PENDING_ROLL`` instruction — it does not create a
    separate pending-adjustment state.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    sequence_id: UUID
    interaction_phase: RpgInteractionPhase

    pending_roll: PlayerRollInstructionView | None = None
    pending_decision: PendingMechanicalDecisionView | None = None


# ---------------------------------------------------------------------------
# Player-roll submissions (CRD Issue 15b)
# ---------------------------------------------------------------------------


class PlayerRollTermResult(BaseModel):
    """Raw per-term submitted values for one RollTerm."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    term_id: UUID
    values: tuple[int, ...]


class RawPlayerRollSubmission(BaseModel):
    """Inline or physical raw-value roll submission, grouped by ``term_id``.

    The client submits no authoritative formula, modifier, target, outcome,
    or total — the backend derives selections, subtotals, totals, and
    outcomes from ``term_results``.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    source: Literal["inline_ui", "physical_self_report"]
    pending_roll_request_id: UUID
    expected_instruction_revision: int
    term_results: tuple[PlayerRollTermResult, ...]


class PhysicalAggregateRollSubmission(BaseModel):
    """Physical self-report of an aggregate-only result (no raw per-die values)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    source: Literal["physical_self_report"]
    pending_roll_request_id: UUID
    expected_instruction_revision: int
    reported_aggregate: int


# ---------------------------------------------------------------------------
# Resolved steps and ready bundle (CRD Issue 15b)
# ---------------------------------------------------------------------------


class DerivedRollTermResult(BaseModel):
    """Code-derived resolution of one RollTerm's submitted or generated values.

    ``selected_indices`` are zero-based indexes into ``values``. For
    ``SUM_ALL`` every index is selected; for keep-highest/keep-lowest, kept
    and omitted dice remain reconstructable from ``values`` and
    ``selected_indices``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    term_id: UUID
    values: tuple[int, ...]
    selected_indices: tuple[int, ...]
    contribution_applied_subtotal: int


class ResolvedSequenceStep(BaseModel):
    """One resolved step (roll, adjustment, or decision) within a sequence.

    ``step_index`` is 1-based. ``AI_ROLL``/``HIDDEN_ROLL`` support contested
    checks and other adapter-resolved opposing mechanics — hidden steps may
    have internal results and provisional effects while exposing only their
    visibility-filtered ``WriterAdjudicationView``. Resolved steps are the
    source for projected-state reconstruction, final audit rows, ordered
    Writer views, and provisional-effect application.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    sequence_id: UUID
    step_id: UUID
    step_index: int
    kind: ResolvedStepKind

    instruction_snapshot: RollInstructionSnapshot | None = None
    submission_source: RollSubmissionSource | None = None

    submitted_term_results: tuple[PlayerRollTermResult, ...] | None = None
    reported_aggregate: int | None = None
    raw_values_complete: bool | None = None

    derived_term_results: tuple[DerivedRollTermResult, ...] = ()
    authoritative_total: int | None = None
    internal_outcome: str | None = None

    writer_view: WriterAdjudicationView | None = None
    provisional_effects: tuple[SheetEffect, ...] = ()

    decision_snapshot: MechanicalDecisionSnapshot | None = None
    accepted_option_id: str | None = None


class ReadyActionResolutionBundle(BaseModel):
    """Complete internal bundle for a sequence that has reached READY_FOR_NARRATION.

    Reuses the shipped per-result ``WriterAdjudicationView`` — it does not
    create a second visibility model. ``ActionResolutionService`` supplies
    this to the orchestrator; the orchestrator passes only approved
    visibility-filtered facts to Writer.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    sequence_id: UUID
    story_id: UUID
    node_id: UUID
    character_id: UUID
    session_id: UUID
    originating_turn_id: UUID

    originating_user_input: str
    resolved_steps: tuple[ResolvedSequenceStep, ...]
    writer_views: tuple[WriterAdjudicationView, ...]
    accumulated_provisional_effects: tuple[SheetEffect, ...]


# ---------------------------------------------------------------------------
# Action-Resolution Sequence (CRD Issue 15b — persisted lifecycle unit)
# ---------------------------------------------------------------------------


class ActionResolutionSequence(BaseModel):
    """Persisted unit spanning one declared action or mechanically linked action group.

    At most one unresolved sequence exists per story (enforced by a SQLite
    partial unique index over ``active``/``ready_for_narration`` statuses at
    the ORM layer). A sequence exposes at most one pending interaction: a
    roll or a mechanical decision, never both.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    sequence_id: UUID
    story_id: UUID
    node_id: UUID
    character_id: UUID
    session_id: UUID
    originating_turn_id: UUID

    status: ActionResolutionStatus
    current_interaction_kind: SequenceInteractionKind

    current_pending_roll_request_id: UUID | None = None
    current_decision_request_id: UUID | None = None

    resolved_steps: tuple[ResolvedSequenceStep, ...]
    projected_state_json: str
    provisional_effects_json: str

    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Action-Resolution Event Ledger (CRD Issue 15b, ADR-015b 15b-34 — durable,
# append-only pre-delivery mechanical provenance)
# ---------------------------------------------------------------------------


class RollEventPayload(BaseModel):
    """Payload for a PLAYER_ROLL/AI_ROLL/HIDDEN_ROLL ActionResolutionEvent.

    ``total``/``outcome`` are non-null for every accepted roll — matching
    the shipped ``ResolvedAdjudicationRecord.total``/bounded ``outcome``.
    Only ``instruction_snapshot.dc`` remains nullable, for checks with no
    compare-outcome target. ``pending_roll_request_id`` is required for
    ``PLAYER_ROLL`` (a real ``PendingRollRequest`` row always exists) and
    null for ``AI_ROLL``/``HIDDEN_ROLL``, and is never reconstructed later
    from ``PendingRollRequest`` — this event is the sole source once
    written. ``gm_cheating_at_roll`` is a snapshot of the session's
    ``gm_cheating`` config at roll-acceptance time, immutable once set.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    kind: Literal[
        ResolvedStepKind.PLAYER_ROLL,
        ResolvedStepKind.AI_ROLL,
        ResolvedStepKind.HIDDEN_ROLL,
    ]
    instruction_snapshot: RollInstructionSnapshot
    submission_source: RollSubmissionSource | None
    pending_roll_request_id: UUID | None
    raw_input_json: str | None
    aggregate_input_json: str | None
    derived_selections_json: str
    subtotal: int | None
    total: int
    outcome: Literal[
        "success", "failure", "critical_success", "critical_failure", "undetermined"
    ]
    gm_cheating_at_roll: bool


class AdjustmentEventPayload(BaseModel):
    """Payload for an ADJUSTMENT ActionResolutionEvent — a revised instruction."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    kind: Literal[ResolvedStepKind.ADJUSTMENT] = ResolvedStepKind.ADJUSTMENT
    resulting_instruction_snapshot: RollInstructionSnapshot
    accepted_adjustment_option_id: str


class MechanicalDecisionEventPayload(BaseModel):
    """Payload for a MECHANICAL_DECISION ActionResolutionEvent — a chosen option.

    Carries the complete immutable ``MechanicalDecisionSnapshot``, including
    ``decision_id``/``decision_revision``, so this event never depends on
    ``ActionResolutionSequence.resolved_steps`` or other mutable sequence
    state to reconstruct its accepted authority.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    kind: Literal[ResolvedStepKind.MECHANICAL_DECISION] = (
        ResolvedStepKind.MECHANICAL_DECISION
    )
    decision_snapshot: MechanicalDecisionSnapshot
    accepted_decision_option_id: str


class ActionResolutionEvent(BaseModel):
    """One immutable, append-only record of an accepted mechanical outcome.

    Written inside the intermediate transaction (15b-34) that advances a
    sequence — never updated or deleted once committed. ``story_id``,
    ``session_id``, and ``character_id`` are carried directly on every
    event so a ``RollEventPayload``-carrying event can supply
    ``rpg_roll_audit``'s identity columns on its own, without joining
    ``ActionResolutionSequence`` or ``RpgSessionState`` (see the Final
    Audit Projection in ADR-015b). ``kind`` and ``payload.kind`` must
    agree; no other kind/payload combination is constructible.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    event_id: UUID
    sequence_id: UUID
    step_id: UUID
    story_id: UUID
    session_id: UUID
    character_id: UUID
    event_order: int
    kind: ResolvedStepKind
    mechanical_provenance: str
    provisional_effects_json: str
    created_at: datetime
    payload: RollEventPayload | AdjustmentEventPayload | MechanicalDecisionEventPayload

    @model_validator(mode="after")
    def kind_matches_payload_kind(self) -> Self:
        if self.kind != self.payload.kind:
            raise ValueError(
                f"kind ({self.kind.value}) must match payload.kind "
                f"({self.payload.kind.value})"
            )
        return self


# ---------------------------------------------------------------------------
# RPG visible-state payload (character-visible only; hidden state excluded)
# ---------------------------------------------------------------------------


class VisibleCharacterState(BaseModel):
    """Character state visible to the Sojourner.

    ``active_conditions`` contains only ``display_label`` strings for
    conditions with ``ConditionVisibility.VISIBLE``.  Hidden conditions are
    excluded by construction.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    character_name: str
    character_class: str
    level: int
    current_hp: int
    maximum_hp: int
    active_conditions: tuple[str, ...]


class VisibleItem(BaseModel):
    """An inventory item visible to the Sojourner."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    quantity: int = 1


class VisibleLocation(BaseModel):
    """The current location as the character perceives it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    brief_description: str | None = None


class VisibleRelationship(BaseModel):
    """A relationship the character is aware of."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    character_name: str
    relationship_description: str


class RpgVisibleState(BaseModel):
    """Visible game state for the RPG mode sidebar / visible-state surface.

    Character-visible only.  Hidden state (hidden rolls, unseen threats,
    undetected NPCs, hidden relationships) excluded by construction.
    ``schema_version`` is a payload version lock — consumers must check it.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    character: VisibleCharacterState
    inventory: tuple[VisibleItem, ...]
    location: VisibleLocation | None = None
    relationship_meters: tuple[VisibleRelationship, ...]
    known_objectives: tuple[str, ...]
    schema_version: Literal[1] = 1


__all__ = [
    "ActionResolutionAdvanceResult",
    "ActionResolutionEvent",
    "ActionResolutionSequence",
    "AdjudicationProposalOutput",
    "AdjustmentEventPayload",
    "DerivedRollTermResult",
    "DiceResult",
    "MechanicalDecisionEventPayload",
    "MechanicalDecisionOption",
    "MechanicalDecisionOptionSnapshot",
    "MechanicalDecisionSnapshot",
    "MechanicalDecisionSubmission",
    "PendingMechanicalDecisionView",
    "PendingRollRequest",
    "PhysicalAggregateRollSubmission",
    "PlayerAdjustmentOptionView",
    "PlayerModifierView",
    "PlayerRollInstructionView",
    "PlayerRollTermResult",
    "PlayerRollTermView",
    "RawPlayerRollSubmission",
    "ReadyActionResolutionBundle",
    "ResolvedAdjudicationRecord",
    "ResolvedSequenceStep",
    "RollAdjustmentOption",
    "RollEventPayload",
    "RollInstructionSnapshot",
    "RollModifierComponent",
    "RollProposal",
    "RollTerm",
    "RpgVisibleState",
    "SequenceProgressView",
    "SheetEffect",
    "VisibleCharacterState",
    "VisibleItem",
    "VisibleLocation",
    "VisibleRelationship",
    "WriterAdjudicationView",
    # Re-export enums for convenience
    "ActionResolutionStatus",
    "ConditionVisibility",
    "DiceSelectionRule",
    "ModifierVisibility",
    "ResolvedStepKind",
    "RollAdjustmentTiming",
    "RollContribution",
    "RollPurpose",
    "RollSubmissionSource",
    "RollVisibility",
    "RpgInteractionPhase",
    "SequenceInteractionKind",
]
