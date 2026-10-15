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
- Hidden modifiers and their existence, an instruction's backend-only fields
  and a decision's effects never appear in a player-facing view (CRD Issue
  15b, 15b-17).
- ``RpgVisibleState`` is character-visible only; hidden state excluded by
  construction.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

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


class HeldItem(BaseModel):
    """One item in a subject's hands, and how many hands hold it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    item_id: UUID
    hands: Literal[1, 2]


class HandFacts(BaseModel):
    """The GameMaster's hand/grip facts for the acting subject (Owner decision
    2026-10-12): the actual held items in its hands and the hands left free.
    Code validates them; they establish no ammunition, action or waiver."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    held: tuple[HeldItem, ...]
    free_hands: Literal[0, 1, 2]


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
    #: For a ranged attack: the enemies the GameMaster identifies within 5
    #: feet of the attacker (an empty list: none). Code checks each can see
    #: the attacker and isn't Incapacitated (``play.combat/close_combat``).
    hostiles_within_5_feet: tuple[SubjectRef, ...] | None = None
    #: The story's save-affecting aura holders whose aura covers a creature
    #: this attack forces to save (an empty list: none in range).
    auras_in_range: tuple[SubjectRef, ...] | None = None
    #: Whether the attacker is within 5 feet of the target, for a rule that
    #: turns on it (Prone, and Paralyzed's or Unconscious's automatic
    #: Critical Hit). A melee attack with a 5-foot reach implies it.
    target_within_5_feet: bool | None = None
    #: A Versatile weapon used in two hands; a Thrown weapon thrown; a
    #: Finesse weapon's chosen ability.
    two_handed: bool = False
    thrown: bool = False
    ability: str | None = None
    #: What the attacker holds in its hands, and how (required).
    hands: HandFacts | None = None
    #: For a weapon with the Ammunition property: the held ammunition item
    #: fired (OD-15c-1 selection; code checks its typed kind, the weapons it
    #: serves and the quantity, and expends one whether the attack hits).
    ammunition_item_id: UUID | None = None
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
    #: The Light property's extra attack, after an Attack action attack with
    #: another Light weapon this turn: as a Bonus Action (``light``) or, with
    #: the weapon's Nick mastery, as part of the Attack action (``nick``).
    extra: Literal["light", "nick"] | None = None
    cleave_within_5_feet: bool | None = None


class CreatureAttackSelection(BaseModel):
    """The GameMaster's selections for one ``creature_attack``: the attacking
    creature, one of its printed attack entries, the target, and the approved
    contextual facts (OD-15c-1). Never a number."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    attacker: SubjectRef
    entry: str = Field(min_length=1)
    target: SubjectRef
    range: RangeBand
    cover: CoverDegree
    attacker_light: LightLevel
    target_light: LightLevel
    hostiles_within_5_feet: tuple[SubjectRef, ...] | None = None
    target_within_5_feet: bool | None = None
    #: For a trait like Pack Tactics: the attacker's allies the GameMaster
    #: identifies within 5 feet of the target (an empty list: none).
    allies_within_5_feet_of_target: tuple[SubjectRef, ...] | None = None
    auras_in_range: tuple[SubjectRef, ...] | None = None
    #: Part of the attacker's Multiattack: consecutive ``creature_attack``
    #: proposals by one creature marked so form one Multiattack action, which
    #: must match one of its printed alternatives.
    multiattack: bool = False
    #: For an entry printing a charge (*"moved 20+ feet straight toward it
    #: immediately before the hit"*): whether the attacker did (OD-15c-1).
    moved_straight_toward_target: bool | None = None
    #: The follow-up attack an entry's hit allows (*"can make one Bite
    #: attack against it"*): it directly follows that attack, against its
    #: target, and takes no action of its own.
    follows_up: bool = False


class CreatureSaveEffectSelection(BaseModel):
    """The GameMaster's selections for one ``creature_save_effect``: the source
    creature, one of its printed save-effect entries, and the creatures in
    its area or otherwise subject to it (OD-15c-1). Never a number."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source: SubjectRef
    entry: str = Field(min_length=1)
    targets: tuple[SubjectRef, ...] = Field(min_length=1)
    auras_in_range: tuple[SubjectRef, ...] | None = None
    #: For an entry affecting "each enemy" in its area (a Sphinx's roars):
    #: the creatures in the area the GameMaster identifies as the source's
    #: enemies (bystander identification; no allegiance is derived). The
    #: targets must be exactly these. Null for any other entry.
    enemies_in_area: tuple[SubjectRef, ...] | None = None


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


class ContestParticipant(BaseModel):
    """One participant of a generic contest (ADR-015b Group 17), as the
    GameMaster selects it: a subject, the ability of its check and optionally
    a skill that ability governs. ``roll_hidden``: the participant's dice and
    numbers are hidden from the player (a backend hidden roll)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject: SubjectRef
    ability: str
    skill: str | None = None
    roll_hidden: bool = False


class ContestSelection(BaseModel):
    """The GameMaster's selections for one ``contest`` (ADR-015b Group 17):
    identities only. Code derives every number, compares the totals (the
    higher wins; equal totals preserve the prior situation) and applies no
    effect. ``counterpart_perceived``: the acting character perceives the
    opposition; when it does not, the player sees an ordinary check."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    initiator: ContestParticipant
    resister: ContestParticipant
    stakes: str = Field(min_length=1)
    counterpart_perceived: bool = True


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
    #: the GameMaster selects, and the tool activity of a tool check, with
    #: the kind of a Gaming Set or Musical Instrument used.
    ability: str | None = None
    skill: str | None = None
    difficulty: str | None = None
    tool_activity: str | None = None
    tool_variant: str | None = None
    #: The selections of a ``weapon_attack`` (CRD Issue 15c).
    weapon_attack: WeaponAttackSelection | None = None
    #: The one subject an operation names: whose turn ``begin_turn`` or
    #: ``end_turn`` marks, whom ``stabilize`` aids, or whose recovery an
    #: attestation concerns (CRD Issue 15c).
    subject: SubjectRef | None = None
    #: An elapsed-time or completion attestation (OD-15c-2).
    attestation: LifecycleAttestation | None = None
    #: The selections of a ``creature_attack`` (CRD Issue 15c).
    creature_attack: CreatureAttackSelection | None = None
    #: The selections of a ``creature_save_effect`` (CRD Issue 15c).
    creature_save_effect: CreatureSaveEffectSelection | None = None
    #: For ``creature_species`` (CRD Issue 15c, bounded species input): the
    #: accepted species record the scene offers for ``subject``. An identity
    #: from code-generated options, validated in code.
    species: str | None = None
    #: The selections of a ``contest`` (CRD Issue 15b, ADR-015b Group 17).
    contest: ContestSelection | None = None


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


class TurnUseRef(BaseModel):
    """One action instance or once-per-turn slot a record spent, by whom
    (CRD Issue 15c, :mod:`afterworlds.pipeline.rpg.economy`)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    by: SubjectRef
    key: str = Field(min_length=1)


class TurnEdge(BaseModel):
    """One explicit actor-turn edge (CRD Issue 15c, contract G1)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["begin", "end"]
    subject: SubjectRef


class ContestParticipantResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subject: SubjectRef
    step_id: UUID
    total: int


class ContestResolution(BaseModel):
    """The combined result of a generic contest (Group 17), computed once by
    code when the second total is accepted. Higher total wins; equal totals
    are a tie that preserves the prior situation (no winner, no effect)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    contest_id: UUID
    participants: tuple[ContestParticipantResult, ContestParticipantResult]
    result: Literal["win", "tie"]
    winner: SubjectRef | None
    certificate: dict[str, str]

    @model_validator(mode="after")
    def _winner_matches(self) -> Self:
        a, b = self.participants
        if a.total == b.total:
            if self.result != "tie" or self.winner is not None:
                raise ValueError("equal totals are a tie with no winner")
        else:
            best = a if a.total > b.total else b
            if self.result != "win" or self.winner != best.subject:
                raise ValueError("the higher total wins")
        return self


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
    turn_uses: tuple[TurnUseRef, ...] = ()
    #: A contest's combined result (ADR-015b Group 17), on its record.
    contest_resolution: ContestResolution | None = None


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
    """A persisted player-roll request, one step of an action-resolution
    sequence (CRD Issue 15b).

    Revised per ADR-015b's Column Disposition and Owner Decision 15b-36: the
    eight legacy display/derivation fields are gone; the structured
    ``instruction_snapshot_json`` is the only instruction authority, and
    display text derives from it. ``schema_version`` is a diagnostic marker
    (2 when a structured instruction is linked); ``instruction_id is None``
    is the signal code checks. ``adapter_context_hash`` is a non-authoritative
    internal drift diagnostic.
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
    schema_version: Literal[1, 2] = 2
    adapter_context_hash: str | None = None
    sequence_id: UUID | None = None
    step_id: UUID | None = None
    instruction_id: UUID | None = None
    instruction_revision: int | None = None
    instruction_schema_version: int | None = None
    instruction_snapshot_json: str | None = None


# ---------------------------------------------------------------------------
# Roll instruction contract (CRD Issue 15b, ADR-015b Group 2)
# ---------------------------------------------------------------------------

_Outcome = Literal[
    "success", "failure", "critical_success", "critical_failure", "undetermined"
]

#: The roll purposes whose instruction compares a total against a target.
_MAX_DICE = 100
_MAX_SIDES = 1000


class RollTerm(BaseModel):
    """One independently meaningful dice term (15b-4, 15b-5).

    Bounded positive ``count``/``sides``; ``keep_count`` only for a keep
    rule, then ``1 <= keep_count <= count``. No formula is executed.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    term_id: UUID
    count: int = Field(gt=0, le=_MAX_DICE)
    sides: int = Field(gt=1, le=_MAX_SIDES)
    selection_rule: DiceSelectionRule
    keep_count: int | None = None
    contribution: RollContribution = RollContribution.ADD
    label: str | None = None

    @model_validator(mode="after")
    def _keep_count_matches_rule(self) -> Self:
        if self.selection_rule is DiceSelectionRule.SUM_ALL:
            if self.keep_count is not None:
                raise ValueError("keep_count is only for keep-highest/keep-lowest")
        elif self.keep_count is None or not 1 <= self.keep_count <= self.count:
            raise ValueError(
                f"keep_count must be between 1 and count ({self.count}), "
                f"got {self.keep_count}"
            )
        return self


class RollModifierComponent(BaseModel):
    """One code-owned integer modifier of an instruction. A ``HIDDEN``
    component never reaches a player view, nor does its existence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    modifier_id: UUID
    label: str
    value: int
    visibility: ModifierVisibility
    source_kind: str
    source_reference: str | None = None


class RollAdjustmentOption(BaseModel):
    """A parameterless, backend-derived adjustment of a pending roll (15b-9,
    15b-10). ``ability_id`` (the feature or rule granting it) is backend-only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    option_id: str
    ability_id: str
    timing: RollAdjustmentTiming
    player_visible_label: str
    resource_preview: str | None = None


class NaturalOutcome(BaseModel):
    """A die face whose outcome the rules fix whatever the total (an attack's
    natural 20 or 1; a death save's). Backend-only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    face: int
    outcome: _Outcome


class ContestLinkage(BaseModel):
    """Backend-only contest linkage on a participant's instruction (ADR-015b
    Group 17): the contest, both participants and the supplement
    certificate. ``counterpart_perceived`` is the GameMaster-selected fact
    that the acting character perceives the opposition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contest_id: UUID
    participant: SubjectRef
    counterpart: SubjectRef
    counterpart_perceived: bool
    certificate: dict[str, str]
    #: On the first participant's instruction: the counterpart's instruction,
    #: frozen when the contest is created (stored-snapshot authority); its
    #: dice are drawn only when the first result is accepted.
    counterpart_instruction: RollInstructionSnapshot | None = None


class RollInstructionSnapshot(BaseModel):
    """The authoritative structured roll instruction (15b-3).

    ``display_expression``/``display_label`` are display text only. ``dc`` is
    the code-verified target, ``None`` when nothing is compared. The fields
    after ``step_id`` are backend-only and never enter a player view: who
    rolls, the operation and die it belongs to in its sequence, natural-face
    outcomes, an automatic Critical Hit on success, and contest linkage.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    instruction_id: UUID
    instruction_revision: int = Field(ge=1)
    purpose: RollPurpose
    terms: tuple[RollTerm, ...] = Field(min_length=1)
    modifier_components: tuple[RollModifierComponent, ...]
    display_expression: str
    display_label: str
    dc: int | None = None
    source_rule_refs: tuple[str, ...]
    adjustment_options: tuple[RollAdjustmentOption, ...] = ()
    sequence_id: UUID
    step_id: UUID
    roller: SubjectRef
    operation_index: int = Field(ge=0)
    die_index: int = Field(ge=0)
    natural_outcomes: tuple[NaturalOutcome, ...] = ()
    critical_on_success: bool = False
    contest: ContestLinkage | None = None

    @model_validator(mode="after")
    def _distinct_ids(self) -> Self:
        terms = [t.term_id for t in self.terms]
        if len(set(terms)) != len(terms):
            raise ValueError("term_id values are unique within an instruction")
        options = [o.option_id for o in self.adjustment_options]
        if len(set(options)) != len(options):
            raise ValueError("adjustment option ids are unique")
        return self


class PlayerRollTermView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    term_id: UUID
    count: int
    sides: int
    selection_rule: DiceSelectionRule
    keep_count: int | None = None
    contribution: RollContribution
    label: str | None = None


class PlayerModifierView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    modifier_id: UUID
    label: str
    value: int


class PlayerAdjustmentOptionView(BaseModel):
    """``ability_id`` is deliberately absent: it is backend-only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    option_id: str
    player_visible_label: str
    resource_preview: str | None = None


class SequenceProgressView(BaseModel):
    """``step_index`` is 1-based and counts the player's own interactions
    only; ``known_step_count`` is ``None`` when later steps depend on
    unresolved outcomes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    step_index: int = Field(ge=1)
    known_step_count: int | None = None
    step_label: str | None = None
    sequence_label: str | None = None


class PlayerRollInstructionView(BaseModel):
    """The player-visible projection of a pending roll (15b-17)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

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


# ---------------------------------------------------------------------------
# Mechanical decision contract (ADR-015b Group 16, 15b-35)
# ---------------------------------------------------------------------------


class MechanicalDecisionOptionSnapshot(BaseModel):
    """``source_rule_ref`` and ``provisional_effects_json`` are backend-only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    option_id: str
    player_visible_label: str
    source_rule_ref: str | None = None
    provisional_effects_json: str


class MechanicalDecisionSnapshot(BaseModel):
    """The stored authority of a pending decision. Validation and the
    event/audit reconstruction read only this, never live state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    decision_id: UUID
    decision_revision: int = Field(ge=1)
    prompt: str
    options: tuple[MechanicalDecisionOptionSnapshot, ...] = Field(min_length=1)
    source_rule_refs: tuple[str, ...]
    sequence_id: UUID
    step_id: UUID

    @model_validator(mode="after")
    def _distinct_options(self) -> Self:
        ids = [o.option_id for o in self.options]
        if len(set(ids)) != len(ids):
            raise ValueError("option_id values are unique within a decision")
        return self


class MechanicalDecisionOption(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    option_id: str
    player_visible_label: str


class PendingMechanicalDecisionView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    decision_request_id: UUID
    sequence_id: UUID
    decision_revision: int
    interaction_phase: Literal[RpgInteractionPhase.PENDING_MECHANICAL_DECISION]
    prompt: str
    options: tuple[MechanicalDecisionOption, ...]


class MechanicalDecisionSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    decision_request_id: UUID
    expected_decision_revision: StrictInt
    option_id: str


class ActionResolutionAdvanceResult(BaseModel):
    """Exactly the payload matching ``interaction_phase``; neither when ready."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    sequence_id: UUID
    interaction_phase: RpgInteractionPhase
    pending_roll: PlayerRollInstructionView | None = None
    pending_decision: PendingMechanicalDecisionView | None = None

    @model_validator(mode="after")
    def _one_payload(self) -> Self:
        expected = (
            self.interaction_phase is RpgInteractionPhase.PENDING_ROLL,
            self.interaction_phase is RpgInteractionPhase.PENDING_MECHANICAL_DECISION,
        )
        actual = (self.pending_roll is not None, self.pending_decision is not None)
        if expected != actual:
            raise ValueError("the payload must match interaction_phase")
        return self


# ---------------------------------------------------------------------------
# Player-roll submissions (15b-14, 15b-15)
# ---------------------------------------------------------------------------


class PlayerRollTermResult(BaseModel):
    """Raw die faces as submitted. Exact integers only (``StrictInt``): a
    string, float or boolean is refused at ingress, never coerced into a
    legal face (#127 Validation 5, AC16)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    term_id: UUID
    values: tuple[StrictInt, ...]


class RawPlayerRollSubmission(BaseModel):
    """Raw values grouped by ``term_id``. No formula, modifier, target,
    outcome or total is submitted; the backend derives them."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    source: Literal["inline_ui", "physical_self_report"]
    pending_roll_request_id: UUID
    expected_instruction_revision: StrictInt
    term_results: tuple[PlayerRollTermResult, ...]


class PhysicalAggregateRollSubmission(BaseModel):
    """A physical report of the total only: the player's dice plus the
    visible modifiers they were shown. No raw die is ever fabricated."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    source: Literal["physical_self_report"]
    pending_roll_request_id: UUID
    expected_instruction_revision: StrictInt
    reported_aggregate: StrictInt


RollSubmission = Annotated[
    RawPlayerRollSubmission | PhysicalAggregateRollSubmission,
    Field(union_mode="left_to_right"),
]


# ---------------------------------------------------------------------------
# Resolved steps and the ready bundle
# ---------------------------------------------------------------------------


class DerivedRollTermResult(BaseModel):
    """``selected_indices`` are zero-based indexes into ``values``: every one
    for ``SUM_ALL``, the kept dice for a keep rule, so kept and omitted dice
    stay reconstructable."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    term_id: UUID
    values: tuple[int, ...]
    selected_indices: tuple[int, ...]
    contribution_applied_subtotal: int


class ResolvedSequenceStep(BaseModel):
    """One accepted step. The sequence's provisional working view only; the
    durable provenance is the event ledger (15b-34)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    sequence_id: UUID
    step_id: UUID
    step_index: int = Field(ge=1)
    kind: ResolvedStepKind
    instruction_snapshot: RollInstructionSnapshot | None = None
    submission_source: RollSubmissionSource | None = None
    submitted_term_results: tuple[PlayerRollTermResult, ...] | None = None
    reported_aggregate: int | None = None
    raw_values_complete: bool | None = None
    derived_term_results: tuple[DerivedRollTermResult, ...] = ()
    authoritative_total: int | None = None
    internal_outcome: _Outcome | None = None
    decision_snapshot: MechanicalDecisionSnapshot | None = None
    accepted_option_id: str | None = None
    writer_view: WriterAdjudicationView | None = None
    provisional_effects: tuple[SheetEffect, ...] = ()


class ReadyActionResolutionBundle(BaseModel):
    """The complete internal bundle of a ready sequence. The orchestrator
    passes only the visibility-filtered ``writer_views`` to the Writer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    sequence_id: UUID
    story_id: UUID
    session_id: UUID
    node_id: UUID
    character_id: UUID
    originating_turn_id: UUID
    originating_user_input: str
    resolved_steps: tuple[ResolvedSequenceStep, ...]
    writer_views: tuple[WriterAdjudicationView, ...]
    accumulated_provisional_effects: tuple[SheetEffect, ...]


class ActionResolutionSequence(BaseModel):
    """A persisted sequence: one declared action or linked action group.

    At most one unresolved sequence per story (partial unique index); at most
    one pending interaction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    sequence_id: UUID
    story_id: UUID
    session_id: UUID
    node_id: UUID
    character_id: UUID
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

    @model_validator(mode="after")
    def _one_interaction(self) -> Self:
        if (
            self.current_pending_roll_request_id is not None
            and self.current_decision_request_id is not None
        ):
            raise ValueError("a sequence exposes one pending interaction at most")
        return self


# ---------------------------------------------------------------------------
# Action-resolution event ledger (ADR-015b Group 15, 15b-34)
# ---------------------------------------------------------------------------


class RollEventPayload(BaseModel):
    """A ``PLAYER_ROLL``/``AI_ROLL``/``HIDDEN_ROLL`` event. ``total`` and
    ``outcome`` are never null; only the snapshot's ``dc`` may be.
    ``pending_roll_request_id`` is set exactly for player rolls.
    ``contest_resolution`` is set only on a contest-completing roll."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    kind: Literal[
        ResolvedStepKind.PLAYER_ROLL,
        ResolvedStepKind.AI_ROLL,
        ResolvedStepKind.HIDDEN_ROLL,
    ]
    instruction_snapshot: RollInstructionSnapshot
    submission_source: RollSubmissionSource
    pending_roll_request_id: UUID | None
    raw_input_json: str | None
    aggregate_input_json: str | None
    derived_selections_json: str
    subtotal: int | None
    total: int
    outcome: _Outcome
    gm_cheating_at_roll: bool
    contest_resolution: ContestResolution | None = None

    @model_validator(mode="after")
    def _source_consistency(self) -> Self:
        player = self.kind is ResolvedStepKind.PLAYER_ROLL
        backend = self.submission_source is RollSubmissionSource.BACKEND_DICE_SERVICE
        if player == backend:
            raise ValueError(
                "a player roll arrives inline or by physical report; an AI or "
                "hidden roll by the backend dice service"
            )
        if player != (self.pending_roll_request_id is not None):
            raise ValueError("pending_roll_request_id is set exactly for player rolls")
        if (self.raw_input_json is None) == (self.aggregate_input_json is None):
            raise ValueError("exactly one of raw or aggregate input is recorded")
        aggregate = self.aggregate_input_json is not None
        if aggregate and (
            self.submission_source is not RollSubmissionSource.PHYSICAL_SELF_REPORT
        ):
            # Only a physical self-report may be aggregate-only (15b-15): the
            # backend and an inline roll always know every die.
            raise ValueError("only a physical self-report records an aggregate only")
        if aggregate != (self.subtotal is None) or (
            aggregate and self.derived_selections_json != "[]"
        ):
            raise ValueError(
                "an aggregate-only report derives no selection or subtotal; raw "
                "values always do"
            )
        if self.instruction_snapshot.dc is None and self.outcome != "undetermined":
            raise ValueError("a roll with no target resolves undetermined")
        linkage = self.instruction_snapshot.contest
        if self.contest_resolution is not None and (
            linkage is None or linkage.contest_id != self.contest_resolution.contest_id
        ):
            raise ValueError("only a roll of that contest completes it")
        return self


class AdjustmentEventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    kind: Literal[ResolvedStepKind.ADJUSTMENT] = ResolvedStepKind.ADJUSTMENT
    resulting_instruction_snapshot: RollInstructionSnapshot
    accepted_adjustment_option_id: str


class MechanicalDecisionEventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    kind: Literal[ResolvedStepKind.MECHANICAL_DECISION] = (
        ResolvedStepKind.MECHANICAL_DECISION
    )
    decision_snapshot: MechanicalDecisionSnapshot
    accepted_decision_option_id: str


EventPayload = Annotated[
    RollEventPayload | AdjustmentEventPayload | MechanicalDecisionEventPayload,
    Field(discriminator="kind"),
]


class ActionResolutionEvent(BaseModel):
    """One immutable, append-only accepted mechanical outcome. Its common
    envelope carries the stable story/session/character identity, so the final
    audit never joins sequence or session state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    event_id: UUID
    sequence_id: UUID
    step_id: UUID
    story_id: UUID
    session_id: UUID
    character_id: UUID
    event_order: int = Field(ge=1)
    kind: ResolvedStepKind
    mechanical_provenance: str
    provisional_effects_json: str
    created_at: datetime
    payload: EventPayload

    @model_validator(mode="after")
    def _kind_matches_payload(self) -> Self:
        if self.kind is not self.payload.kind:
            raise ValueError(
                f"kind {self.kind.value} must match payload kind "
                f"{self.payload.kind.value}"
            )
        payload = self.payload
        snapshot: RollInstructionSnapshot | MechanicalDecisionSnapshot = (
            payload.instruction_snapshot
            if isinstance(payload, RollEventPayload)
            else (
                payload.resulting_instruction_snapshot
                if isinstance(payload, AdjustmentEventPayload)
                else payload.decision_snapshot
            )
        )
        if (snapshot.sequence_id, snapshot.step_id) != (
            self.sequence_id,
            self.step_id,
        ):
            raise ValueError("an event records its own sequence step's snapshot")
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


ContestLinkage.model_rebuild()
RollInstructionSnapshot.model_rebuild()

__all__ = [
    "ActionResolutionAdvanceResult",
    "ActionResolutionEvent",
    "ActionResolutionSequence",
    "AdjudicationProposalOutput",
    "AdjustmentEventPayload",
    "ContestLinkage",
    "ContestParticipant",
    "ContestSelection",
    "ContestParticipantResult",
    "ContestResolution",
    "DerivedRollTermResult",
    "DiceResult",
    "MechanicalDecisionEventPayload",
    "MechanicalDecisionOption",
    "MechanicalDecisionOptionSnapshot",
    "MechanicalDecisionSnapshot",
    "MechanicalDecisionSubmission",
    "NaturalOutcome",
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
    "RollSubmission",
    "RollTerm",
    "RpgVisibleState",
    "SequenceProgressView",
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
