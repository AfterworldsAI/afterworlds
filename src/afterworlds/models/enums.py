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
