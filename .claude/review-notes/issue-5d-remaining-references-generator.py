# ruff: noqa: E501  -- citation keys and span ids are kept whole to be greppable
"""Draft the **remaining-references** resolutions.

REVIEW MATERIAL for CRD Issue 5d (#137) over the accepted authority
``srd-5-2-1-corpus-3fe24ff6-4e3.json`` (release ``5.2.1-corpus.3fe24ff6-4e3``).
It emits unrecorded ``ReferenceResolution`` drafts only. It accepts nothing,
records nothing and writes nothing under ``oracles/``.

Of the 91 unresolved citations the accepted authority states, 25 are drafted
below as 26 resolutions (:data:`DRAFTS`): two are split into their printed
occurrences, both of one drafted and one of the other. Seventeen of the 26
name a record the accepted authority states; the other nine name one of the
six records, or (two) the Casting Spells membership, that exist only
in the unaccepted candidate of ``issue-5d-remaining-references-REPLACEMENT.py``,
which composes these drafts over that candidate in memory. :data:`REKEYED`
drafts a fresh identity for each of the three recorded resolutions whose
component moves to a candidate record: same text, scope, target and span. The
remaining citations stay unresolved and are classified, with evidence, in
``issue-5d-remaining-references-review.md``.

Run: ``python issue-5d-remaining-references-generator.py`` writes the drafts.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from afterworlds.ingestion.mechanical.models import ReferenceResolution, ReleaseBinding
from afterworlds.ingestion.mechanical.oracle import load_accepted_inputs
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
)

REPO = Path(__file__).resolve().parents[2]
ORACLE = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json"
)
DRAFTS_FILE = "issue-5d-remaining-references-resolutions-DRAFTS.json"

#: (from_record, from_component, source_text, scope, target, REFERENCE spans).
#: Grade (a) the named item's own record, (b) a section cited as such, (d) the
#: named rule's own record in the target-scope candidate; the grade and its
#: evidence are per row in the review.
DRAFTS: tuple[tuple[str, str, str, str, str, tuple[str, ...]], ...] = (
    # (a) "Choose 3 Musical Instruments (see Equipment)" names the Musical Instrument tool.
    (
        "classes.bard",
        "core_traits",
        "Equipment",
        "srd-5.2.1/equipment",
        "equipment.tools.musical_instrument",
        ("73a15de1-87fe-504d-9fc1-8253175bfad7",),
    ),
    # (b) "the vehicle's speed in miles per hour (as shown in "Equipment")".
    (
        "gameplay_toolbox.travel_pace",
        "vehicles",
        "Equipment",
        "srd-5.2.1/equipment",
        "equipment.mounts_and_vehicles",
        ("344794da-539d-566c-a95c-2c347fa61700",),
    ),
    # (b) "For more information on the tools, see "Equipment."".
    (
        "magic_items.crafting_magic_items",
        "tools",
        "Equipment",
        "srd-5.2.1/equipment",
        "equipment.tools",
        ("abb1dd4e-f4ee-57b6-b444-e5f4e6e6cb40",),
    ),
    # (b) "a magical version of armor from "Equipment."".
    (
        "magic_items.magic_item_categories",
        "armor",
        "Equipment",
        "srd-5.2.1/equipment",
        "equipment.armor",
        ("d134d508-c19b-530b-9770-df1df84a844f",),
    ),
    # (b) "a magical version of a weapon from "Equipment."".
    (
        "magic_items.magic_item_categories",
        "weapons",
        "Equipment",
        "srd-5.2.1/equipment",
        "equipment.weapons",
        ("e43f5e79-08f4-52f1-bcb4-54de7dc4c2d7",),
    ),
    # (d) "saving throws against extreme cold (see "Gameplay Toolbox")": the `### Extreme Cold` rule.
    (
        "equipment.adventuring_gear",
        "bedroll",
        "Gameplay Toolbox",
        "srd-5.2.1/gameplay-toolbox",
        "gameplay_toolbox.environmental_effects.extreme_cold",
        ("e7e5ef2f-444a-50ca-bf16-fbe5a9a4030d",),
    ),
    (
        "equipment.adventuring_gear",
        "blanket",
        "Gameplay Toolbox",
        "srd-5.2.1/gameplay-toolbox",
        "gameplay_toolbox.environmental_effects.extreme_cold",
        ("e3f84ec5-f098-5df2-949f-3249669bc1bd",),
    ),
    # (b) ""Gameplay Toolbox" has rules that affect which pace you can choose in certain types of terrain".
    (
        "play.exploration.travel_pace",
        "travel_pace",
        "Gameplay Toolbox",
        "srd-5.2.1/gameplay-toolbox",
        "gameplay_toolbox.travel_pace",
        ("41f2ce66-b485-5e4c-a428-5443942d831e",),
    ),
    # (b) "Hundreds of magic items are detailed in "Magic Items"": the part details items only in `## Magic Items A–Z`.
    (
        "equipment.magic_items",
        "magic_items",
        "Magic Items",
        "srd-5.2.1/magic-items",
        "magic_items.magic_items_a_z",
        ("d3b9efb8-76af-5188-87b7-fd2d4a1bcae0",),
    ),
    # (d) "Challenge Rating ... is detailed in "Monsters."": the `### Challenge Rating` rule.
    (
        "glossary.stat_block",
        "challenge_rating",
        "Monsters",
        "srd-5.2.1/monsters",
        "monsters.parts_of_a_stat_block.challenge_rating",
        ("24ec15c9-dfef-59e6-8935-03404f0fc93e",),
    ),
    # (a) "a Ghoul ... (see "Monsters" for its stat block)".
    (
        "spells.create_undead",
        "effect",
        "Monsters",
        "srd-5.2.1/monsters",
        "monsters.ghoul.ghoul",
        ("d0e14d3c-924e-5470-8a25-fd39bba1e725",),
    ),
    # (a) "a Zombie (see "Monsters")".
    (
        "spells.finger_of_death",
        "effect",
        "Monsters",
        "srd-5.2.1/monsters",
        "monsters.zombies.zombie",
        ("2ebf46ad-c392-56c9-aba1-e65eb8c02a35",),
    ),
    # (a) "the Riding Horse stat block (see "Monsters")".
    (
        "spells.phantom_steed",
        "effect",
        "Monsters",
        "srd-5.2.1/monsters",
        "animals.riding_horse",
        ("9798ab14-e95f-5296-9f99-d6ce214dd911",),
    ),
    # (b) ""Playing the Game" explains what each ability means".
    (
        "character_creation.create_your_character",
        "determine_ability_scores",
        "Playing the Game",
        "srd-5.2.1/playing-the-game",
        "play.six_abilities",
        ("0674013e-2e20-524d-a8f6-50dbe21b38f3",),
    ),
    # (a) "The rules for a stat block are detailed in "Rules Glossary"".
    (
        "monsters.parts_of_a_stat_block",
        "parts_of_a_stat_block",
        "Rules Glossary",
        "srd-5.2.1/rules-glossary",
        "glossary.stat_block",
        ("dac4347e-db25-5481-9d21-ab67a467f1c4",),
    ),
    # (b) "For details on different kinds of attacks, see ... "Spells."".
    (
        "monsters.parts_of_a_stat_block",
        "attack_notation",
        "Spells",
        "srd-5.2.1/spells",
        "spells.attack_rolls",
        ("ddfea8c5-df9c-5fd5-8c90-fc6d30bb5dd4",),
    ),
    # (b) ""Spells" for spells' damage dice": the part prints damage dice only in `## Spell Descriptions`.
    (
        "play.damage_and_healing",
        "",
        "Spells",
        "srd-5.2.1/spells",
        "spells.spell_descriptions",
        ("518926b1-25c2-5b9f-8b6a-14238f59ea96",),
    ),
    # (d) "at a Normal, Fast, or Slow pace, as described in "Playing the Game."": the `#### Travel Pace` rule.
    (
        "gameplay_toolbox.travel_pace",
        "travel_pace",
        "Playing the Game",
        "srd-5.2.1/playing-the-game",
        "play.exploration.travel_pace",
        ("a50a4e43-d720-52b0-a544-5172550c8976",),
    ),
    # (d) ""Magic Items" has prices for magic items": the `### Magic Item Values by Rarity` rule.
    (
        "equipment.weapons",
        "selling_equipment",
        "Magic Items",
        "srd-5.2.1/magic-items",
        "magic_items.magic_item_rarity.magic_item_values_by_rarity",
        ("f218b436-c2c0-5212-a09c-b43472fa241d",),
    ),
    # (b) "_See also_ "Spells" ("Casting Spells")": the `## Casting Spells`
    # heading, whose printed sections are its members in the candidate.
    (
        "glossary.spell_attack",
        "",
        "Casting Spells",
        "srd-5.2.1/spells",
        "spells.casting_spells",
        ("e2286836-d9b2-5701-a73d-ded4e6909505",),
    ),
    (
        "glossary.spellcasting_focus",
        "",
        "Casting Spells",
        "srd-5.2.1/spells",
        "spells.casting_spells",
        ("b6549567-304a-5fad-9fc6-07f366374950",),
    ),
    # (a) "a _Spell Scroll_, whose crafting time and cost are given in "Equipment."".
    (
        "magic_items.crafting_magic_items",
        "time_and_cost",
        'whose crafting time and cost are given in "Equipment."',
        "srd-5.2.1/equipment",
        "equipment.scribing_spell_scrolls",
        ("3a0a6678-2637-5f0e-a8db-5628f3f87b22",),
    ),
    # (b) "craft that item using the rules in "Equipment."": the nonmagical item's crafting rules.
    (
        "magic_items.crafting_magic_items",
        "time_and_cost",
        'craft that item using the rules in "Equipment."',
        "srd-5.2.1/equipment",
        "equipment.crafting_nonmagical_items",
        ("d5d97869-3ec0-5091-b447-22d91d2d78b5",),
    ),
    # (b) "The weapons in "Equipment"": the weapons category as such.
    (
        "play.exploration",
        "weapons_beyond_battle",
        'The weapons in "Equipment"',
        "srd-5.2.1/equipment",
        "equipment.weapons",
        ("1b03e279-aa57-532e-a009-7fd7b35f0a5a",),
    ),
    # (d) "your Proficiency Bonus (described in Playing the Game)": the Proficiency
    # Bonus rule, `## Proficiency` up to `### Skill Proficiencies`.
    (
        "character_creation.create_your_character",
        "starting_proficiency_bonus",
        "Playing the Game",
        "srd-5.2.1/playing-the-game",
        "play.proficiency.proficiency_bonus",
        ("6ef106c3-e1ee-5f9a-9b26-69c82fad3317",),
    ),
    # (d) "Choose any 3 skills (see Playing the Game)": the `### Skill Proficiencies` rule.
    (
        "classes.bard",
        "core_traits",
        "Playing the Game",
        "srd-5.2.1/playing-the-game",
        "play.proficiency.skill_proficiencies",
        ("73a15de1-87fe-504d-9fc1-8253175bfad7",),
    ),
)

#: Recorded resolution -> its fresh identity on the candidate record its
#: component moves to (B1). Same text, scope, target and span; never recorded.
REKEYED: dict[str, tuple[str, str, str, str, str, tuple[str, ...]]] = {
    "resolve-play-exploration-travel-pace-equipment-equipment-1": (
        "play.exploration.travel_pace",
        "travel_pace",
        "Equipment",
        "srd-5.2.1/equipment",
        "equipment.mounts_and_vehicles",
        ("41f2ce66-b485-5e4c-a428-5443942d831e",),
    ),
    "resolve-magic-items-magic-item-rarity-magic-item-values-by-rarity-plate-armor-equipment-cited-1": (
        "magic_items.magic_item_rarity.magic_item_values_by_rarity",
        "magic_item_values_by_rarity",
        "Plate Armor",
        "srd-5.2.1/equipment",
        "equipment.armor.plate_armor",
        ("2909e2fc-8085-5114-810c-8eb656af6b29",),
    ),
    "resolve-proficiency-bonus-character-creation-1": (
        "play.proficiency.proficiency_bonus",
        "proficiency_bonus",
        "Character Creation",
        "srd-5.2.1/character-creation",
        "character_creation.level_advancement",
        ("6b8bbca6-0f41-549a-8b8e-bc750f6e3bf6",),
    ),
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def draft_resolutions(binding: ReleaseBinding) -> tuple[ReferenceResolution, ...]:
    """The remaining-reference and re-keyed resolutions, drafted for review
    against *binding*."""
    drafts = tuple(
        ReferenceResolution(
            resolution_id=(
                f"resolve-{_slug(record)}-{_slug(component) or 'record'}"
                f"-{_slug(text)}-remaining-1"
            ),
            from_record_key=record,
            from_component_key=component,
            source_text=text,
            scope_key=scope,
            target_record_key=target,
            release_binding=binding,
            provenance_span_ids=spans,
        )
        for record, component, text, scope, target, spans in (
            *DRAFTS,
            *REKEYED.values(),
        )
    )
    assert len({d.resolution_id for d in drafts}) == len(drafts) == 29
    return drafts


def main() -> int:
    binding = load_accepted_inputs(ORACLE).oracle.binding
    drafts = draft_resolutions(binding)
    out = (json.dumps(reference_resolution_payload(drafts), indent=2) + "\n").encode(
        "utf-8"
    )
    (Path(__file__).resolve().parent / DRAFTS_FILE).write_bytes(out)
    print("drafts", DRAFTS_FILE, len(drafts), hashlib.sha256(out).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
