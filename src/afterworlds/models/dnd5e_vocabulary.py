"""Closed D&D 5e state vocabularies the accepted Rules Package schema lacks.

CRD Issue 2b. Each is exactly what the pinned SRD 5.2.1 source prints, so a
recorded value is a source-backed identity rather than free text. They type
*state fields*; they are not Rules Package authority and assert no rule.
``tests/models/test_dnd5e_vocabulary.py`` re-derives every member from the
pinned source, so an omission or a typo fails rather than being trusted.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "ORIGIN_CHOICE_SOURCES",
    "Alignment",
    "ArmorCategory",
    "CreatureType",
    "DraconicAncestor",
    "ElvenLineage",
    "FiendishLegacy",
    "GiantAncestry",
    "GnomishLineage",
    "Language",
]


class Language(StrEnum):
    """Standard and Rare Languages tables, ``character-creation.md``:206, :261."""

    COMMON = "common"
    COMMON_SIGN_LANGUAGE = "common_sign_language"
    DRACONIC = "draconic"
    DWARVISH = "dwarvish"
    ELVISH = "elvish"
    GIANT = "giant"
    GNOMISH = "gnomish"
    GOBLIN = "goblin"
    HALFLING = "halfling"
    ORC = "orc"
    ABYSSAL = "abyssal"
    CELESTIAL = "celestial"
    DEEP_SPEECH = "deep_speech"
    DRUIDIC = "druidic"
    INFERNAL = "infernal"
    PRIMORDIAL = "primordial"
    SYLVAN = "sylvan"
    THIEVES_CANT = "thieves_cant"
    UNDERCOMMON = "undercommon"


class Alignment(StrEnum):
    """The Nine Alignments, ``character-creation.md``:542-566, plus Unaligned
    (the *Unaligned Creatures* note printed among them)."""

    LAWFUL_GOOD = "lawful_good"
    NEUTRAL_GOOD = "neutral_good"
    CHAOTIC_GOOD = "chaotic_good"
    LAWFUL_NEUTRAL = "lawful_neutral"
    NEUTRAL = "neutral"
    CHAOTIC_NEUTRAL = "chaotic_neutral"
    LAWFUL_EVIL = "lawful_evil"
    NEUTRAL_EVIL = "neutral_evil"
    CHAOTIC_EVIL = "chaotic_evil"
    UNALIGNED = "unaligned"


class CreatureType(StrEnum):
    """Creature Type, ``rules-glossary.md``:515."""

    ABERRATION = "aberration"
    BEAST = "beast"
    CELESTIAL = "celestial"
    CONSTRUCT = "construct"
    DRAGON = "dragon"
    ELEMENTAL = "elemental"
    FEY = "fey"
    FIEND = "fiend"
    GIANT = "giant"
    HUMANOID = "humanoid"
    MONSTROSITY = "monstrosity"
    OOZE = "ooze"
    PLANT = "plant"
    UNDEAD = "undead"


class ArmorCategory(StrEnum):
    """Armor Training, ``rules-glossary.md``:231: Light, Medium or Heavy armor
    and Shields — the Armor table's group rows (``equipment.md``:474-579)."""

    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    SHIELD = "shield"


# ---------------------------------------------------------------------------
# Origin choices whose options the source prints without accepted identities.
# Each is offered by exactly one species component; a selection from one is
# valid only as a choice made under that component.
# ---------------------------------------------------------------------------


class DraconicAncestor(StrEnum):
    """Draconic Ancestors table, ``character-origins.md``:107."""

    BLACK = "black"
    BLUE = "blue"
    BRASS = "brass"
    BRONZE = "bronze"
    COPPER = "copper"
    GOLD = "gold"
    GREEN = "green"
    RED = "red"
    SILVER = "silver"
    WHITE = "white"


class ElvenLineage(StrEnum):
    """Elven Lineages table, ``character-origins.md``:196."""

    DROW = "drow"
    HIGH_ELF = "high_elf"
    WOOD_ELF = "wood_elf"


class GnomishLineage(StrEnum):
    """Gnomish Lineage options, ``character-origins.md``:247-251."""

    FOREST_GNOME = "forest_gnome"
    ROCK_GNOME = "rock_gnome"


class GiantAncestry(StrEnum):
    """Giant Ancestry benefits, ``character-origins.md``:261-271."""

    CLOUD_GIANT = "cloud_giant"
    FIRE_GIANT = "fire_giant"
    FROST_GIANT = "frost_giant"
    HILL_GIANT = "hill_giant"
    STONE_GIANT = "stone_giant"
    STORM_GIANT = "storm_giant"


class FiendishLegacy(StrEnum):
    """Fiendish Legacies table, ``character-origins.md``:341."""

    ABYSSAL = "abyssal"
    CHTHONIC = "chthonic"
    INFERNAL = "infernal"


#: The (record, component) that offers each origin-choice vocabulary.
ORIGIN_CHOICE_SOURCES: dict[type[StrEnum], tuple[str, str]] = {
    DraconicAncestor: ("character_origins.dragonborn", "draconic_ancestry"),
    ElvenLineage: ("character_origins.elf", "elven_lineage"),
    GnomishLineage: ("character_origins.gnome", "gnomish_lineage"),
    GiantAncestry: ("character_origins.goliath", "giant_ancestry"),
    FiendishLegacy: ("character_origins.tiefling", "fiendish_legacy"),
}
