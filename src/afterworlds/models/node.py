"""Node — unified story beat / state transition across all three modes.

Key invariants enforced here:
- ``branching_logic`` is a base Node field; it is never replaced by mode metadata.
- ``mode_metadata`` is a typed discriminated union; it *extends* the base schema,
  it does not duplicate or replace ``branching_logic``.
- Mode-specific session state (RPG dice, quests, combat) lives in session models,
  not here.
"""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from afterworlds.models.enums import (
    BranchingCadence,
    IntentType,
    InteractionStyle,
    normalize_legacy_intent_type,
)


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


class PersistedBranchOption(BaseModel):
    """Branch option as persisted on a Node after delivery.

    ``option_id`` is the code-assigned sequential identifier (``opt_1``, …).
    ``action_text`` is the model-proposed label.
    """

    option_id: str
    action_text: str


class BranchingNodeMetadata(BaseModel):
    """Branching-mode beat metadata — presentation/config/selection only.

    This model stores what was presented and selected for this beat.  It must
    never hold canonical graph pointers — those live in ``Node.branching_logic``
    (a list of next-node UUIDs, populated when edges are realized).

    Issue 16 adds typed output-contract fields so the frontend can render the
    delivered branch card without re-deriving config from session state.

    ``extra_branch_options`` is retained for backward compatibility but new
    code should use ``branch_options`` (typed ``PersistedBranchOption`` list).
    """

    mode: Literal["branching"] = "branching"
    pacing_stage_at_beat: str | None = None
    extra_branch_options: list[str] = Field(default_factory=list)
    # Issue 16: typed output-contract fields (None on legacy/setup nodes)
    interaction_style: InteractionStyle | None = None
    branching_cadence: BranchingCadence | None = None
    freeform_available: bool | None = None
    branch_count_range: str | None = None
    branch_options: list[PersistedBranchOption] = Field(default_factory=list)
    branch_presentation_state: str | None = None
    # Set when the Sojourner resolves their branch selection (Phase G).
    #
    # ``selected_option_id`` alone is NOT a stable selection record: option IDs
    # (``opt_1``, …) are reused every beat, so once this beat's branch_options
    # are overwritten with the next beat's cards the same ID points at a
    # different option.  ``selected_action_text`` captures the chosen option's
    # label independently of ``branch_options`` so the selection stays
    # reconstructable after the next beat's cards are persisted.
    selected_option_id: str | None = None
    selected_action_text: str | None = None
    selection_annotation: str | None = None


class WritingNodeMetadata(BaseModel):
    """Writing-mode beat metadata — persona snapshot, work-product kind, eligibility.

    Records what governed the turn. Session-state row is the authoritative source
    of durable configuration; this metadata is the historical snapshot.
    """

    mode: Literal["writing"] = "writing"

    # Persona snapshot at turn time
    persona_id: str | None = None
    persona_display_name: str | None = None
    relationship_orientation: str | None = None
    persona_registry_version: int | None = None
    persona_profile_version: int | None = None
    persona_prompt_fingerprint: str | None = None

    # Turn classification
    work_product_kind: str | None = None
    canon_eligibility: str | None = None

    # Beat and version provenance
    beat_constraints_snapshot: list[str] = Field(default_factory=list)
    version_pointer_refs: list[UUID] = Field(default_factory=list)

    # Authoring controls snapshot (stored as dict; validated by service)
    authoring_controls_snapshot: dict[str, Any] | None = None


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

    @field_validator("intent_type", mode="before")
    @classmethod
    def _coerce_legacy_intent_type(cls, v: object) -> object:
        if isinstance(v, str):
            return normalize_legacy_intent_type(v)
        return v
