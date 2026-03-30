"""Mode-specific session state schemas.

Architecture invariant enforced here:
- Session state is cleanly separated from the core Node schema.
- RPG session state holds ONLY transient session/combat context not already
  owned by the character sheet.  HP, spell slots, and similar persistent
  character resources live on ``Dnd5eCharacterSheet`` — not here.
- Branching session state includes pacing stage, branch tree (distinct
  structured model), and plot thread tracker as separate typed fields.
- Writing session state holds beat constraints and version history pointers.
"""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from afterworlds.models.enums import DiceHandling, PacingStage, WritingPersona

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
    - Dice configuration
    - Active quests (transient, Extractor-maintained)
    - Combat context (cleared between encounters)

    HP, spell slots, ability scores, and equipment are owned by
    ``Dnd5eCharacterSheet``.  Do not duplicate them here.
    """

    session_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    character_sheet_id: UUID
    dice_handling: DiceHandling
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
    - ``branch_tree`` — full branch graph (distinct structured model)
    - ``plot_thread_tracker`` — unresolved threads queued by the Extractor
    """

    session_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    pacing_stage: PacingStage
    branch_tree: BranchTree = Field(default_factory=BranchTree)
    plot_thread_tracker: list[PlotThread] = Field(default_factory=list)
    current_node_id: UUID | None = None


# ---------------------------------------------------------------------------
# Writing session state
# ---------------------------------------------------------------------------


class WritingSessionState(BaseModel):
    """Session state for Writing mode."""

    session_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    beat_constraints: list[str] = Field(default_factory=list)
    version_history_pointers: list[UUID] = Field(default_factory=list)
    persona: WritingPersona | None = None
