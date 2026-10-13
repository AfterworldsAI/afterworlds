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

from pydantic import BaseModel, ConfigDict, Field

from afterworlds.models.enums import ConditionVisibility, RollVisibility

# ---------------------------------------------------------------------------
# Roll proposal DTOs (model-emitted; no trust-relevant numbers)
# ---------------------------------------------------------------------------


class SubjectRef(BaseModel):
    """A character or continuing creature of the story, by id (CRD Issue 15c).
    Code checks that it belongs to the story before reading it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["character", "creature"]
    subject_id: UUID


#: Where an attack's target is relative to the attacker, as the GameMaster
#: selects it from the options code generates for this attack (Owner decision
#: OD-15c-1): within the weapon's reach (melee), within its normal range,
#: beyond normal but within long range, or beyond long range.
RangeBand = Literal[
    "within_reach",
    "within_normal_range",
    "beyond_normal_within_long_range",
    "beyond_long_range",
]
#: The degree of cover the target has against this attack (``play.combat``).
CoverDegree = Literal["none", "half", "three_quarters", "total"]
#: The light and obscurement at a subject's location, as it bears on seeing
#: it (``rules-glossary.md`` Vision and Light). Code derives sight from these,
#: the subjects' recorded conditions and source-qualified senses; it executes
#: bright and dim light only and refuses the rest until sense ranges are
#: supplied for the operation.
LightLevel = Literal[
    "bright", "dim", "darkness", "magical_darkness", "heavily_obscured"
]


class WeaponAttackSelection(BaseModel):
    """The GameMaster's selections for one ``weapon_attack``: identities and
    approved contextual facts only, never a number. Code validates each
    against the weapon, the subjects and the source, and derives every value.
    The facts are recorded with this attack's provenance; they are not a
    reusable position record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    weapon_item_id: UUID
    target: SubjectRef
    range: RangeBand
    cover: CoverDegree
    attacker_light: LightLevel
    target_light: LightLevel
    #: For a ranged attack: whether a hostile creature that can see the
    #: attacker and isn't Incapacitated is within 5 feet of it.
    hostile_within_5_feet: bool | None = None
    #: Whether the attacker is within 5 feet of the target, for a rule that
    #: turns on it (Prone, and Paralyzed's or Unconscious's automatic
    #: Critical Hit). A melee attack with a 5-foot reach implies it.
    target_within_5_feet: bool | None = None
    #: A Versatile weapon used in two hands; a Thrown weapon thrown; a
    #: Finesse weapon's chosen ability.
    two_handed: bool = False
    thrown: bool = False
    ability: str | None = None
    #: A melee attack that would reduce the target to 0 Hit Points knocks it
    #: out instead (``knocking_out``, optional for the attacker).
    knock_out: bool = False
    #: Use the weapon's optional mastery property (Graze, Push, Slow, Topple),
    #: which the wielder's Weapon Mastery feature must cover. Sap and Vex are
    #: not optional and apply whenever it does.
    mastery: bool = False
    #: Push: how far the target is pushed straight away, up to the source's
    #: distance (OD-15c-1).
    push_ft: Literal[5, 10] | None = None
    #: Cleave's extra attack, against a second creature, made with the same
    #: weapon after the previous attack hit. ``cleave_within_5_feet`` is the
    #: GameMaster's fact that the second creature is within 5 feet of the
    #: first (OD-15c-1).
    cleave: bool = False
    cleave_within_5_feet: bool | None = None


class LifecycleAttestation(BaseModel):
    """The GameMaster's attestation about one recovery instance (CRD Issue
    15c, OD-15c-2), never a result: code holds the interval, the thresholds and
    the consequence, and consumes each instance once.

    ``instance_id`` names a Stable recovery instance (``stable_recovery``) or
    a knockout's Unconscious condition instance (``knockout_recovery``).
    ``elapsed_hours`` is the *total* time since that instance began (4: four
    or more), for
    ``stable_recovery`` only; a repeated attestation adds nothing.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    instance_id: str = Field(min_length=1)
    elapsed_hours: Literal[1, 2, 3, 4] | None = None


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
    #: CRD Issue 15c: the roster operation the GameMaster selects, and the
    #: code-admitted identity it selects (``record_key/component_key``). These
    #: are identities, never numbers; code validates both and derives every
    #: value. The labels above are display text only.
    operation: str | None = None
    check_identity: str | None = None
    #: Closed-vocabulary selections an operation may need, validated in code:
    #: the ability and skill of a difficulty check, the Typical DC identity
    #: the GameMaster selects, and the tool activity of a tool check.
    ability: str | None = None
    skill: str | None = None
    difficulty: str | None = None
    tool_activity: str | None = None
    #: The selections of a ``weapon_attack`` (CRD Issue 15c).
    weapon_attack: WeaponAttackSelection | None = None
    #: The one subject an operation names: whose turn ``begin_turn`` or
    #: ``end_turn`` marks, whom ``stabilize`` aids, or whose recovery an
    #: attestation concerns (CRD Issue 15c).
    subject: SubjectRef | None = None
    #: An elapsed-time or completion attestation (OD-15c-2).
    attestation: LifecycleAttestation | None = None


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
    operation: Literal[
        "delta",
        "set",
        "apply_condition",
        "clear_condition",
        "apply_effect",
        "end_effect",
    ]
    value_json: str
    schema_version: Literal[1] = 1
    #: CRD Issue 15c: the subject the effect applies to. ``None`` is the
    #: turn's acting character (the earlier single-subject meaning).
    subject_kind: Literal["character", "creature"] | None = None
    subject_id: UUID | None = None


# ---------------------------------------------------------------------------
# Resolved adjudication record (INTERNAL — full mechanical/audit payload)
# ---------------------------------------------------------------------------


class TurnEdge(BaseModel):
    """One explicit actor-turn edge (CRD Issue 15c, contract G1)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["begin", "end"]
    subject: SubjectRef


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
    #: The actor-turn edge this record applies, if any (CRD Issue 15c). The
    #: orchestrator replays every record's edge onto the coordination the
    #: turn read and commits it with the Turn.
    turn_edge: TurnEdge | None = None
    #: A once-per-turn use this record takes (``record/component``) for the
    #: acting character in the active turn; replayed and committed like edges.
    turn_use: str | None = None


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
