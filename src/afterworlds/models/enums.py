"""Shared enumerations for the Afterworlds core data model."""

from enum import StrEnum


class IntentType(StrEnum):
    """Classified intent of a user input or story beat."""

    ACTION = "action"
    DIALOGUE = "dialogue"
    AUTHOR_INSTRUCTION = "author_instruction"
    BRANCH_CHOICE = "branch_choice"
    MILESTONE = "milestone"
    REWIND = "rewind"
    LORE_QUESTION = "lore_question"


class StoryMode(StrEnum):
    """The three narrative modes of Afterworlds."""

    RPG = "rpg"
    BRANCHING = "branching"
    WRITING = "writing"


class PacingStage(StrEnum):
    """Branching-mode pacing stages tracked internally by the story architect."""

    SETUP = "setup"
    ESCALATION = "escalation"
    REVERSAL = "reversal"
    CLIMAX = "climax"
    AFTERMATH = "aftermath"


class DiceHandling(StrEnum):
    """Dice-roll mode configured by the player in RPG mode."""

    PLAYER_ROLLS = "player_rolls"
    AI_ROLLS = "ai_rolls"


class WritingPersona(StrEnum):
    """Writing-mode persona selected by the Sojourner."""

    # Mentors — teaching through making
    CHIRON = "chiron"
    MERLIN = "merlin"
    VIDURA = "vidura"
    # Peers — creative collaborators
    ODIN = "odin"
    ATHENA = "athena"
    THOTH = "thoth"


# ---------------------------------------------------------------------------
# Story Bible enums
# ---------------------------------------------------------------------------


class EventSignificance(StrEnum):
    """Significance classification for Events Ledger entries.

    The always-include set for the Events Ledger tiered inclusion policy is
    defined in ``services.story_bible.ALWAYS_INCLUDE_SIGNIFICANCE``.  That
    constant is the single source of truth — callers must not duplicate the
    policy logic.  See ADR-0005 for the full taxonomy and rationale.
    """

    ROUTINE = "routine"
    CHARACTER_DEATH = "character_death"
    LOCKED_FACT_ESTABLISHED = "locked_fact_established"
    MAJOR_PLOT_TURN = "major_plot_turn"
    RELATIONSHIP_CHANGE = "relationship_change"
    WORLD_STATE_CHANGE = "world_state_change"
    FORBIDDEN_FACT_ESTABLISHED = "forbidden_fact_established"


class CastRole(StrEnum):
    """Narrative role of a cast member within a Story."""

    PROTAGONIST = "protagonist"
    ANTAGONIST = "antagonist"
    SUPPORTING = "supporting"
    MINOR = "minor"
    OTHER = "other"


class RelationshipType(StrEnum):
    """Type of directional relationship between two cast members."""

    ALLY = "ally"
    ENEMY = "enemy"
    NEUTRAL = "neutral"
    ROMANTIC = "romantic"
    FAMILIAL = "familial"
    OTHER = "other"


class ThreadStatus(StrEnum):
    """Lifecycle status of an unresolved plot thread."""

    OPEN = "open"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class ProposalType(StrEnum):
    """Extractor route classification for a provisional staging entry.

    Mirrors the four routes in the Extractor Update Policy (design.md §4).
    """

    LOCKED_FACT = "locked_fact"
    SOFT_FACT = "soft_fact"
    TRANSIENT_STATE = "transient_state"
    UNRESOLVED_THREAD = "unresolved_thread"


class ProposalStatus(StrEnum):
    """Lifecycle status of a provisional staging proposal."""

    PENDING = "pending"
    RATIFIED = "ratified"
    REJECTED = "rejected"
