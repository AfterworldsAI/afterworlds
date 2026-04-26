"""Shared enumerations for the Afterworlds core data model."""

from enum import StrEnum


class IntentType(StrEnum):
    """Classified intent of a user input or story beat.

    The full eight-type taxonomy is defined in Issue 7 (CRD Issue 7).
    ``Node.intent_type`` uses this same enum but logically draws from the
    narrower five-type subset (IN_CHARACTER_ACTION, DIALOGUE,
    AUTHOR_INSTRUCTION, BRANCH_CHOICE, BEAT_MILESTONE) that describes what a
    Node *represents* in the story graph.  ``Turn.intent_classification`` uses
    the full taxonomy, including REWIND, LORE_QUESTION, and OOC.
    """

    IN_CHARACTER_ACTION = "in_character_action"
    DIALOGUE = "dialogue"
    AUTHOR_INSTRUCTION = "author_instruction"
    BRANCH_CHOICE = "branch_choice"
    BEAT_MILESTONE = "beat_milestone"
    REWIND = "rewind"
    LORE_QUESTION = "lore_question"
    OOC = "ooc"


# ---------------------------------------------------------------------------
# Legacy persistence compatibility
# ---------------------------------------------------------------------------

#: Maps pre-Issue-7 persisted wire values to the canonical Issue 7 taxonomy.
#: The ORM stores raw enum .value strings; rows written before the rename need
#: to survive ORM→model conversion without a data migration.
_LEGACY_INTENT_MAP: dict[str, str] = {
    "action": "in_character_action",
    "milestone": "beat_milestone",
}


def normalize_legacy_intent_type(v: str) -> str:
    """Return the canonical IntentType wire value, coercing legacy values.

    Args:
        v: raw string from the persistence layer (or any string input).

    Returns:
        The canonical wire value, or ``v`` unchanged if already canonical.
    """
    return _LEGACY_INTENT_MAP.get(v, v)


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

    Mirrors the four routes in the Extractor Update Policy (design.md §4) plus
    EVENT, added for the Events Ledger auto-commit path (CRD Issue 10).
    """

    LOCKED_FACT = "locked_fact"
    SOFT_FACT = "soft_fact"
    TRANSIENT_STATE = "transient_state"
    UNRESOLVED_THREAD = "unresolved_thread"
    EVENT = "event"


class ProposalStatus(StrEnum):
    """Lifecycle status of a provisional staging proposal."""

    PENDING = "pending"
    RATIFIED = "ratified"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Rules Package enums
# ---------------------------------------------------------------------------


class RulesSystemEnum(StrEnum):
    """Supported rule systems for a RulesPackage.

    ``d20`` is the only v1 exemplar.  Additional systems slot in as additional
    Rules Packages using the same schema without structural changes.
    """

    D20 = "d20"


class PublicationStatusEnum(StrEnum):
    """Publication lifecycle status for a RulesPackage.

    ``draft`` — in progress, not visible to play-time queries.
    ``published`` — released and available for play.
    ``retired`` — no longer active; excluded from play-time queries.
    """

    DRAFT = "draft"
    PUBLISHED = "published"
    RETIRED = "retired"


class RuleSourceCategoryEnum(StrEnum):
    """Classification of a source document within a RulesPackage.

    This field classifies the *kind* of source document.  It does NOT
    determine authority ordering.  Authority ordering within a package is
    governed by ``RuleSource.precedence_rank``.  Do not infer winning-rule
    behaviour from category alone.

    ``adventure`` corresponds to what D&D players call a published adventure
    module.  The term ``module`` is not used as a model or table name to
    avoid overloading.
    """

    CORE_RULEBOOK = "core_rulebook"
    SUPPLEMENT = "supplement"
    ADVENTURE = "adventure"


class RuleSubsystemEnum(StrEnum):
    """Subsystem tag for scoping RuleChunk retrieval.

    Used by the Context Builder to retrieve only the rule chunks relevant
    to the current turn's needs (e.g. attack resolution, a spell lookup).
    """

    COMBAT = "combat"
    SPELLS = "spells"
    CONDITIONS = "conditions"
    MOVEMENT = "movement"
    ITEMS = "items"
    CLASSES = "classes"
    RACES = "races"
    GENERAL = "general"


class MechanicalEntityTypeEnum(StrEnum):
    """Discriminated entity type for MechanicalEntity records.

    Each value maps to a distinct typed Pydantic model:
    ``spell`` → SpellEntity, ``condition`` → ConditionEntity,
    ``stat_block`` → StatBlockEntity, ``action`` → ActionEntity,
    ``item`` → ItemEntity.
    """

    CONDITION = "condition"
    ACTION = "action"
    SPELL = "spell"
    ITEM = "item"
    STAT_BLOCK = "stat_block"


class OverrideOriginEnum(StrEnum):
    """Origin classification for a RuleOverride.

    ``house_rule`` — Sojourner-configured override for a play session.
    ``package_patch`` — administrative correction to packaged content.
    """

    HOUSE_RULE = "house_rule"
    PACKAGE_PATCH = "package_patch"


class OverrideOperationEnum(StrEnum):
    """Operation applied by a RuleOverride to its target record.

    ``replace`` — replace target content with override content.
    ``append`` — append override content to existing target content.
    ``disable`` — disable the target record (excluded from active results).
    """

    REPLACE = "replace"
    APPEND = "append"
    DISABLE = "disable"


class SourceLocatorTypeEnum(StrEnum):
    """Type discriminator for the source locator on RuleChunk/MechanicalEntity.

    Supports different source location schemes without forcing a rigid
    document/section/anchor column triad on sources that may not have a
    uniform page/section/anchor shape.

    ``page`` — a page number (e.g. ``"p. 72"``).
    ``heading_anchor`` — a heading identifier (e.g. ``"#spells-fireball"``).
    ``section_path`` — a hierarchical section path (e.g. ``"Chapter 3 > Combat"``).
    ``range`` — a page range (e.g. ``"pp. 72-74"``).
    """

    PAGE = "page"
    HEADING_ANCHOR = "heading_anchor"
    SECTION_PATH = "section_path"
    RANGE = "range"
