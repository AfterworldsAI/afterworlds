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
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from afterworlds.models.enums import ConditionVisibility, RollVisibility

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
    """Persisted state for a player-roll request spanning two turns.

    Created on the announce turn; consumed on the turn the Sojourner reports
    the result.  Stores the code-derived roll terms snapshot so consumption
    validates against what was announced, not freshly recomputed state.

    ``hidden_modifier_present`` is INTERNAL ONLY — it must never appear in
    ``WriterAdjudicationView``, ``RpgVisibleState``, player-facing prompts,
    or delivered output.

    ``adapter_context_hash`` surfaces sheet-state drift between announce and
    consume.  In v1, a mismatch produces a diagnostic but does NOT trigger
    recomputation or changed resolution.
    """

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    story_id: UUID
    session_id: UUID
    character_id: UUID
    check_label: str
    player_facing_instruction: str
    expected_value_shape: str
    visible_modifier_note: str | None = None
    visibility: RollVisibility
    source_proposal_ref: str
    originating_turn_id: UUID
    consumed_turn_id: UUID | None = None
    status: Literal["pending", "consumed", "cancelled", "expired"] = "pending"
    created_at: datetime
    schema_version: Literal[1] = 1
    roll_expression: str
    visible_modifier_total: int | None = None
    visible_modifier_breakdown_json: str | None = None
    hidden_modifier_present: bool = False
    adapter_context_hash: str | None = None


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
    "AdjudicationProposalOutput",
    "DiceResult",
    "PendingRollRequest",
    "ResolvedAdjudicationRecord",
    "RollProposal",
    "RpgVisibleState",
    "SheetEffect",
    "VisibleCharacterState",
    "VisibleItem",
    "VisibleLocation",
    "VisibleRelationship",
    "WriterAdjudicationView",
    # Re-export visibility enums for convenience
    "ConditionVisibility",
    "RollVisibility",
]
