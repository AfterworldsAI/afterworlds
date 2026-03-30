"""World and Character state models with explicit static / dynamic partitions.

Architecture invariant enforced here:
- Static fields require Sojourner confirmation to change (Extractor policy).
- Dynamic fields are Extractor-maintained and auto-committed.
- This partition is structural — represented by nested sub-models, not merely
  documented in comments.

CharacterState scope is limited to runtime / mechanical / current-state data.
Narrative canon, character profiles, and relationship facts belong in the
Story Bible schema (Issue 4) and must not be added here.
"""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# WorldState
# ---------------------------------------------------------------------------


class WorldStateStaticPartition(BaseModel):
    """Stable world facts — require Sojourner confirmation to change."""

    setting_name: str
    world_rules: list[str] = Field(default_factory=list)
    geography: str | None = None
    time_period: str | None = None


class WorldStateDynamicPartition(BaseModel):
    """Extractor-maintained world conditions — auto-committed each turn."""

    current_location: str | None = None
    time_of_day: str | None = None
    weather: str | None = None
    faction_standings: dict[str, str] = Field(default_factory=dict)


class WorldState(BaseModel):
    """Current world conditions for a story.

    Structural partition:
    - ``static`` — stable facts requiring confirmation to change
    - ``dynamic`` — Extractor-maintained transient conditions
    """

    world_state_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    static: WorldStateStaticPartition
    dynamic: WorldStateDynamicPartition = Field(
        default_factory=WorldStateDynamicPartition
    )
    updated_at: datetime


# ---------------------------------------------------------------------------
# CharacterState
# ---------------------------------------------------------------------------


class CharacterStateStaticPartition(BaseModel):
    """Stable character identity — requires Sojourner confirmation to change."""

    character_name: str


class CharacterStateDynamicPartition(BaseModel):
    """Extractor-maintained runtime character state — auto-committed each turn.

    Scope: runtime / mechanical / current-state data only.
    Narrative canon, profile, and relationship facts belong in the Story Bible.
    """

    current_location: str | None = None
    status_effects: list[str] = Field(default_factory=list)
    relationship_meters: dict[str, str] = Field(default_factory=dict)
    inventory: list[str] = Field(default_factory=list)


class CharacterState(BaseModel):
    """Runtime mechanical state for a character in a story.

    This is NOT the Story Bible character entry.  CharacterState holds
    current-state / mechanical data.  Narrative canon, profile, and
    relationship facts are Story Bible concerns (Issue 4).

    Structural partition:
    - ``static`` — stable identity requiring confirmation to change
    - ``dynamic`` — Extractor-maintained mechanical state
    """

    character_state_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    static: CharacterStateStaticPartition
    dynamic: CharacterStateDynamicPartition = Field(
        default_factory=CharacterStateDynamicPartition
    )
    updated_at: datetime
