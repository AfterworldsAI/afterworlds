"""Node — unified story beat / state transition across all three modes.

Key invariants enforced here:
- ``branching_logic`` is a base Node field; it is never replaced by mode metadata.
- ``mode_metadata`` is a typed discriminated union; it *extends* the base schema,
  it does not duplicate or replace ``branching_logic``.
- Mode-specific session state (RPG dice, quests, combat) lives in session models,
  not here.
"""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from afterworlds.models.enums import IntentType


class StateDelta(BaseModel):
    """World mutations caused by this story beat."""

    world_changes: dict[str, str] = Field(default_factory=dict)
    character_changes: dict[str, str] = Field(default_factory=dict)
    inventory_gains: list[str] = Field(default_factory=list)
    inventory_losses: list[str] = Field(default_factory=list)


class NodeMetadata(BaseModel):
    """Narrative metadata for a Node beat."""

    pov: str | None = None
    location: str | None = None
    mood: str | None = None
    tense: str | None = None
    timestamp: datetime | None = None


class RpgNodeMetadata(BaseModel):
    """RPG-mode beat metadata — mechanical notes, dice outcomes."""

    mode: Literal["rpg"] = "rpg"
    mechanical_notes: str | None = None
    dice_results: list[int] = Field(default_factory=list)


class BranchingNodeMetadata(BaseModel):
    """Branching-mode beat metadata.

    ``extra_branch_options`` holds additional Branching-mode detail for this
    beat.  It does *not* replace ``Node.branching_logic``, which remains the
    canonical location of next-node pointers.
    """

    mode: Literal["branching"] = "branching"
    pacing_stage_at_beat: str | None = None
    extra_branch_options: list[str] = Field(default_factory=list)


class WritingNodeMetadata(BaseModel):
    """Writing-mode beat metadata — beat constraints and version pointers."""

    mode: Literal["writing"] = "writing"
    beat_constraints: list[str] = Field(default_factory=list)
    version_pointer: UUID | None = None


ModeMetadata = Annotated[
    RpgNodeMetadata | BranchingNodeMetadata | WritingNodeMetadata,
    Field(discriminator="mode"),
]


class Node(BaseModel):
    """A story beat / state transition — unified entity across all three modes.

    ``branching_logic`` is a first-class base field holding pointers to the
    next possible nodes.  Mode-specific metadata lives in ``mode_metadata``
    and *extends* this base schema without replacing ``branching_logic``.
    """

    node_id: UUID = Field(default_factory=uuid4)
    chapter_id: UUID
    content: str
    state_delta: StateDelta = Field(default_factory=StateDelta)
    branching_logic: list[UUID] = Field(default_factory=list)
    intent_type: IntentType
    metadata: NodeMetadata = Field(default_factory=NodeMetadata)
    mode_metadata: ModeMetadata | None = None
