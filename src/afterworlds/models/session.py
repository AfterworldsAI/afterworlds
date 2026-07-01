"""Mode-specific session state schemas.

Architecture invariant enforced here:
- Session state is cleanly separated from the core Node schema.
- RPG session state holds ONLY transient session/combat context not already
  owned by the character sheet.  HP, spell slots, and similar persistent
  character resources live on ``Dnd5eCharacterSheet`` — not here.
- Branching session state includes pacing stage, branch tree (distinct
  structured model), and plot thread tracker as separate typed fields.
- Writing session state holds persona provenance, authoring controls, beat
  constraints, and minimal version pointers.
"""

from typing import Any, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from afterworlds.models.enums import (
    BranchCountRange,
    BranchingCadence,
    BranchingPlayStatus,
    CritiqueIntensity,
    DiceHandling,
    InteractionStyle,
    LengthPreference,
    PacingStage,
    RpgPlayStatus,
    RpgSessionType,
    RpgSetupPhase,
    RpgTone,
    StyleDensity,
    WritingForm,
    WritingPlayStatus,
)

# ---------------------------------------------------------------------------
# RPG session state
# ---------------------------------------------------------------------------


class CombatContext(BaseModel):
    """Transient combat state — cleared at the end of each encounter."""

    is_in_combat: bool = False
    initiative_order: list[str] = Field(default_factory=list)
    active_conditions: dict[str, list[str]] = Field(default_factory=dict)
    round_number: int = 0


class RpgSessionState(BaseModel):
    """Transient RPG session context.

    Owns only state not already on the character sheet:
    - Play status and pre-play sequence progress
    - Per-session GM and play configuration (dice, gm_cheating, tone, etc.)
    - Active quests (transient, Extractor-maintained)
    - Combat context (non-authoritative encounter scaffolding)

    HP, spell slots, ability scores, equipment, and active conditions are
    owned by ``Dnd5eCharacterSheet``.  Do not duplicate them here.

    ``gm_cheating`` defaults to True (``gm_cheating = on`` per prompt contract).
    ``play_status`` transitions from SETUP to IN_PLAY when the character sheet
    passes ``D20RulesSystemAdapter.is_adjudicable()`` and setup_phase reaches
    COMPLETE.
    """

    session_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    character_sheet_id: UUID
    dice_handling: DiceHandling
    play_status: RpgPlayStatus = RpgPlayStatus.SETUP
    setup_phase: RpgSetupPhase = RpgSetupPhase.WORLD_SETUP
    gm_cheating: bool = True
    tone: RpgTone = RpgTone.BALANCED
    session_type: RpgSessionType = RpgSessionType.OPEN_ENDED
    genre_flavor: str | None = None
    house_rules: str | None = None
    acceptable_content: str | None = None
    active_quests: list[str] = Field(default_factory=list)
    combat_context: CombatContext = Field(default_factory=CombatContext)


# ---------------------------------------------------------------------------
# Branching session state
# ---------------------------------------------------------------------------


class BranchNode(BaseModel):
    """A single entry in the branch tree, with forward pointers."""

    node_id: UUID
    next_node_ids: list[UUID] = Field(default_factory=list)


class BranchTree(BaseModel):
    """Full branch graph for a Branching-mode session.

    ``nodes`` maps str(UUID) → BranchNode.  String keys are used because
    JSON object keys are always strings; UUID values are preserved in each
    ``BranchNode.node_id`` field.  See ADR-0002 for rationale.
    """

    nodes: dict[str, BranchNode] = Field(default_factory=dict)
    root_node_id: UUID | None = None

    @model_validator(mode="after")
    def keys_match_node_ids(self) -> Self:
        for key, branch_node in self.nodes.items():
            try:
                key_uuid = UUID(key)
            except ValueError as err:
                raise ValueError(
                    f"BranchTree key {key!r} is not a valid UUID string"
                ) from err
            if key_uuid != branch_node.node_id:
                raise ValueError(
                    f"BranchTree key {key!r} does not match "
                    f"BranchNode.node_id {branch_node.node_id}"
                )
        return self


class PlotThread(BaseModel):
    """An unresolved narrative thread tracked by the story architect."""

    thread_id: UUID = Field(default_factory=uuid4)
    description: str
    is_resolved: bool = False
    related_node_ids: list[UUID] = Field(default_factory=list)


class BranchingSessionState(BaseModel):
    """Session state for Branching mode.

    Distinct structured fields — not fields on Node:
    - ``pacing_stage`` — current position in the five-stage narrative arc
    - ``branch_tree`` — full branch graph (distinct structured model, dormant)
    - ``plot_thread_tracker`` — unresolved threads queued by the Extractor
    - ``interaction_style`` — None when setup is not yet complete (never silently
      freeform_only for backfilled rows per CRD Issue 16 conservative backfill rule)
    - ``play_status`` — SETUP → IN_PLAY once configuration is finalized
    """

    session_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    pacing_stage: PacingStage
    branch_tree: BranchTree = Field(default_factory=BranchTree)
    plot_thread_tracker: list[PlotThread] = Field(default_factory=list)
    current_node_id: UUID | None = None
    # Issue 16: interaction configuration — nullable so existing rows are
    # never silently backfilled to freeform_only.  None = setup not complete.
    interaction_style: InteractionStyle | None = None
    branching_cadence: BranchingCadence | None = None
    length_preference: LengthPreference | None = None
    branch_count_range: BranchCountRange | None = None
    play_status: BranchingPlayStatus = BranchingPlayStatus.SETUP
    # Optional setup context fields (narrative scaffolding, not mechanical state)
    world_summary: str | None = None
    story_seeds: str | None = None
    character_concept: str | None = None
    supporting_cast: str | None = None
    world_constraints: str | None = None
    pacing_notes: str | None = None
    acceptable_content: str | None = None


# ---------------------------------------------------------------------------
# Writing session state
# ---------------------------------------------------------------------------


class WritingSessionState(BaseModel):
    """Session state for Writing mode.

    persona_id is required at setup; there is no default persona. Registry
    provenance fields are set when a persona is selected and are provenance-only
    in v1 (no historical lookup or mismatch handling).

    Conservative backfill rule: all new fields are nullable or have safe
    defaults. Existing rows without a persona stay in SETUP until setup
    completes explicitly.
    """

    model_config = ConfigDict(extra="forbid")

    session_id: UUID = Field(default_factory=uuid4)
    story_id: UUID

    # Persona provenance — set at setup, not duplicated from registry
    persona_id: str | None = None
    persona_registry_version: int | None = None
    persona_profile_version: int | None = None
    persona_prompt_fingerprint: str | None = None

    play_status: WritingPlayStatus = WritingPlayStatus.SETUP

    # Authoring controls — all nullable; safe defaults on required fields
    reading_interests: str | None = None
    writing_interests: str | None = None
    form: WritingForm | None = None
    form_other: str | None = None
    specific_goals: str = ""
    critique_intensity: CritiqueIntensity = CritiqueIntensity.BALANCED

    tense: str | None = None
    pov: str | None = None
    style_density: StyleDensity = StyleDensity.BALANCED
    dialogue_narration_ratio: int | None = None
    genre_conventions: str | None = None

    beat_constraints: list[str] = Field(default_factory=list)
    version_pointers: list[dict[str, Any]] = Field(default_factory=list)
    acceptable_content: str | None = None

    @field_validator("dialogue_narration_ratio")
    @classmethod
    def _ratio_range(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("dialogue_narration_ratio must be between 0 and 100")
        return v

    @field_validator("beat_constraints")
    @classmethod
    def _constraints_nonempty(cls, v: list[str]) -> list[str]:
        for constraint in v:
            if not constraint.strip():
                raise ValueError("beat_constraints must not contain empty strings")
        return v

    @model_validator(mode="after")
    def _form_other_required(self) -> Self:
        if self.form is WritingForm.OTHER and not self.form_other:
            raise ValueError("form_other is required when form is OTHER")
        return self

    @model_validator(mode="after")
    def _in_play_requires_persona(self) -> Self:
        if self.play_status is WritingPlayStatus.IN_PLAY and not self.persona_id:
            raise ValueError("persona_id is required when play_status is IN_PLAY")
        return self

    @model_validator(mode="after")
    def _in_play_requires_goal(self) -> Self:
        if (
            self.play_status is WritingPlayStatus.IN_PLAY
            and not self.specific_goals.strip()
        ):
            raise ValueError("specific_goals is required when play_status is IN_PLAY")
        return self
