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


class InteractionStyle(StrEnum):
    """Branching-mode interaction contract: how the Sojourner interacts."""

    FREEFORM_ONLY = "freeform_only"
    HYBRID = "hybrid"
    TRUE_CYOA = "true_cyoa"


class BranchingCadence(StrEnum):
    """Branching-mode pacing density — distinct axis from PacingStage."""

    INTERACTIVE = "interactive"
    BALANCED = "balanced"
    IMMERSIVE = "immersive"


class LengthPreference(StrEnum):
    """Preferred response length for Branching-mode narrative beats."""

    SHORT_STORY = "short_story"
    NOVELLA = "novella"
    NOVEL = "novel"


class BranchCountRange(StrEnum):
    """Validated branch-count ranges by interaction style.

    Hybrid allows: 1-2, 2-3, 3-4.
    True CYOA allows: 2-3, 2-4, 2-5.
    """

    ONE_TO_TWO = "1-2"
    TWO_TO_THREE = "2-3"
    THREE_TO_FOUR = "3-4"
    TWO_TO_FOUR = "2-4"
    TWO_TO_FIVE = "2-5"


class BranchingPlayStatus(StrEnum):
    """Play-status for a Branching story: setup phase or active play."""

    SETUP = "setup"
    IN_PLAY = "in_play"


class InteractionRejectionReason(StrEnum):
    """Typed reason an Interaction was rejected (CRD Issue 16).

    Used in ``OrchestrationResult.interaction_rejection_reason`` when
    ``disposition`` is ``INTERACTION_REJECTED``.  A human-readable message
    is always emitted alongside this typed reason via
    ``interaction_rejection_message``.

    INVALID_FOR_INTERACTION_STYLE: input style is incompatible with the
        current ``InteractionStyle`` (e.g. freeform prose in TRUE_CYOA).
    MATERIAL_BRANCH_REWRITE: a branch annotation materially rewrites the
        label in a way that changes the canonical meaning.
    CANON_OR_GENRE_CONTRADICTION: the selected action violates Story Bible
        canon or established genre constraints.
    INVALID_BRANCH_SELECTION: BRANCH_CHOICE intent references an option_id
        that does not appear in the most-recently-presented branch card set.
    """

    INVALID_FOR_INTERACTION_STYLE = "invalid_for_interaction_style"
    MATERIAL_BRANCH_REWRITE = "material_branch_rewrite"
    CANON_OR_GENRE_CONTRADICTION = "canon_or_genre_contradiction"
    INVALID_BRANCH_SELECTION = "invalid_branch_selection"


class BranchPresentationState(StrEnum):
    """Whether branch-choice cards are shown, held, or omitted for a beat.

    SHOWN: branch cards are rendered for the Sojourner this beat.
    HELD: branch cards exist but are withheld (e.g. mid-scene tension).
    OMITTED: no branch cards for this beat (freeform or narrative-only).
    """

    SHOWN = "shown"
    HELD = "held"
    OMITTED = "omitted"


class DiceHandling(StrEnum):
    """Dice-roll mode configured by the player in RPG mode."""

    PLAYER_ROLLS = "player_rolls"
    AI_ROLLS = "ai_rolls"


class RpgPlayStatus(StrEnum):
    """Play-status for an RPG story: setup phase or active play."""

    SETUP = "setup"
    IN_PLAY = "in_play"


class RpgSetupPhase(StrEnum):
    """Progress through the mandatory RPG pre-play sequence."""

    WORLD_SETUP = "world_setup"
    CHARACTER_CREATION = "character_creation"
    PLAY_CONFIGURATION = "play_configuration"
    COMPLETE = "complete"


class RpgSessionType(StrEnum):
    """Pacing expectation set by the Sojourner at play configuration."""

    SHORT_ADVENTURE = "short_adventure"
    CAMPAIGN = "campaign"
    OPEN_ENDED = "open_ended"


class RpgTone(StrEnum):
    """Consequence severity calibration configured at play configuration."""

    GRITTY = "gritty"
    BALANCED = "balanced"
    FORGIVING = "forgiving"
    DANGER_FREE = "danger_free"


class RollVisibility(StrEnum):
    """Who can see the result of a resolved adjudication roll.

    SHOWN — AI roll whose result is shown to the Sojourner.
    HIDDEN — Backend-visible only; player-facing fields nulled in the Writer view.
    PLAYER — Sojourner rolls and reports the result.
    """

    SHOWN = "shown"
    HIDDEN = "hidden"
    PLAYER = "player"


class ConditionVisibility(StrEnum):
    """Whether an active condition is visible to the Sojourner.

    VISIBLE — Shown in visible_state_sidebar and WriterAdjudicationView.
    HIDDEN — Backend-visible only (e.g., a secretly inflicted compulsion or curse
             that the character is unaware of).
    """

    VISIBLE = "visible"
    HIDDEN = "hidden"


class WritingPlayStatus(StrEnum):
    """Lifecycle phase of a Writing-mode session."""

    SETUP = "setup"
    IN_PLAY = "in_play"


class CritiqueIntensity(StrEnum):
    """How directly the persona delivers feedback."""

    GENTLE = "gentle"
    BALANCED = "balanced"
    BLUNT = "blunt"
    RUTHLESS = "ruthless"


class StyleDensity(StrEnum):
    """Prose density preference for the writing project."""

    SPARSE = "sparse"
    BALANCED = "balanced"
    LUSH = "lush"
    LITERARY = "literary"
    PULP = "pulp"


class WritingForm(StrEnum):
    """Primary form of the writing project."""

    SHORT_STORY = "short_story"
    NOVEL = "novel"
    NARRATIVE_NONFICTION = "narrative_nonfiction"
    MEMOIR = "memoir"
    SCREENPLAY = "screenplay"
    OTHER = "other"


class WritingWorkProductKind(StrEnum):
    """What the Writer is producing this turn."""

    SETUP_CONFIRMATION = "setup_confirmation"
    PROSE_CONTINUATION = "prose_continuation"
    DRAFT_PROSE = "draft_prose"
    REVISION = "revision"
    LINE_EDIT = "line_edit"
    CRITIQUE = "critique"
    STRUCTURAL_DIAGNOSIS = "structural_diagnosis"
    BRAINSTORM = "brainstorm"
    CRAFT_EXERCISE = "craft_exercise"
    BEAT_PLAN = "beat_plan"
    OOC_RESPONSE = "ooc_response"


class WritingCanonEligibility(StrEnum):
    """Whether Extractor proposals may route to Story Bible for this turn."""

    EXTRACTOR_ELIGIBLE = "extractor_eligible"
    NON_CANON_SUPPORT = "non_canon_support"


class WritingVersionPointerKind(StrEnum):
    """What kind of provenance reference a WritingVersionPointer stores."""

    TURN = "turn"
    NODE = "node"
    DRAFT_LABEL = "draft_label"
    GENERATED_CANDIDATE = "generated_candidate"
    WORKING_SEGMENT = "working_segment"


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
    EVENT proposals bypass staging and go directly to ``add_event``; there is
    no ``ProposalType.EVENT`` value.
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


class TargetDomain(StrEnum):
    """Domain of a proposal's target entity — used by the Extractor routing layer.

    Determines the natural-key format and writable-field allowlist applied by
    ``StoryBibleService.route_extractor_proposals()``.
    """

    CHARACTER = "character"
    WORLD = "world"
    RELATIONSHIP = "relationship"


class EventKind(StrEnum):
    """Functional classification of an Events Ledger entry.

    Used by the Extractor to classify the type of event being proposed,
    enabling downstream filtering and summarisation without reparsing prose.
    The canonical set is defined here; ``extractor.md`` mirrors it.
    """

    LOCATION_CHANGE = "location_change"
    INVENTORY_GAIN = "inventory_gain"
    INVENTORY_LOSS = "inventory_loss"
    NPC_INTRODUCTION = "npc_introduction"
    STATUS_CHANGE = "status_change"
    RELATIONSHIP_CHANGE = "relationship_change"
    SCENE_TRANSITION = "scene_transition"
    PLOT_REVEAL = "plot_reveal"
    OATH_OR_PROMISE = "oath_or_promise"
    DEATH = "death"
    ROUTINE = "routine"


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
