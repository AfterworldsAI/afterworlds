"""The final-ten reference candidate, in memory.

CRD Issues 5c/5d (#132, #137). REVIEW MATERIAL: nothing here is accepted,
recorded, published or activated, and no Owner approval exists for it. The
reviewer and authorization below are the FRR harness's SIMULATED constants;
there is deliberately no recording step.

The ten citations still unresolved in the accepted oracle
(``issue-5d-current-reference-disposition-2026-10-03.md`` rows 34, 36, 39, 48,
54, 57, 60, 76, 87 and 88) are resolved under the accepted schema-17 semantics
(ADR-005d Decision 7), following the 6 October 2026 Owner directions and
source clarifications. Every destination is an existing record; no record,
component, aggregate, schema or reader change is made. ``_sources`` checks every
drafted group against the pinned source markdown and the accepted
representation. The candidate is additive: the accepted artifact with
``resolve_references`` applied once under the simulated reviewer.

Run: ``python CANDIDATE.py [--write]``. ``--write`` regenerates the proposal and
delta files beside this script; otherwise they are checked.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
NOTES = REPO / ".claude/review-notes"
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    resolve_references,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ReferenceDestination,
    ReferenceResolution,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    accepted_inputs_payload,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    effective_representation,
    reference_resolution_payload,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    ProvenanceTargetKind,
    reference_target_key,
    representation_schema_hash,
)


def _load(name: str, path: Path) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


#: The finite-reference-routes harness (read-only): route helper, delta, round
#: trip, findings reader and the simulated reviewer constants.
FRR = _load(
    "finite_reference_routes_replacement",
    NOTES / "issue-5d-finite-reference-routes-REPLACEMENT.py",
)
REPL = FRR.REPL
APC = FRR.APC
SIMULATED_REVIEWER: str = FRR.SIMULATED_REVIEWER
SIMULATED_RULE: str = FRR.SIMULATED_RULE
SIMULATED_AT = "2026-10-06T00:00:00Z"
_route = FRR._route

ACCEPTED_PATH: Path = FRR.ACCEPTED_PATH
ACCEPTED_SHA256 = "5909e5bdd8c73bf32525b17942924364871146d648b83681518561361a434c0d"
FAMILIAR_INVENTORY = NOTES / "issue-5d-srd-familiar-cr0-inventory-2026-10-06.json"
FAMILIAR_INVENTORY_SHA256 = (
    "2b7c3e4ec210a6ff30618dfbbda891191f3bf0d52ca46a9779aa6d0e256d14b0"
)

PROPOSAL_FILE = HERE / "issue-5d-final-ten-references-PROPOSAL.json"
DELTA_FILE = HERE / "issue-5d-final-ten-references-DELTA.txt"
SRC: Path = FRR.SRC

EQ = "srd-5.2.1/equipment"
MONSTERS = "srd-5.2.1/monsters"
GLOSSARY = "srd-5.2.1/rules-glossary"
SPELLS = "srd-5.2.1/spells"
Draft = tuple[str, tuple[ReferenceDestination, ...]]
Citation = tuple[str, str, str, str]

# --- Row 34 magic-items.md 181: "If a magic item incorporates an item that has
# a purchase cost in "Equipment" (such as a weapon or a suit of armor), add that
# item's cost". The Equipment sections that price objects a magic item can
# incorporate, in printed order; the reader adds their one-hop item members.
# Food, Drink, and Lodging (equipment.md 1976-2065) prices goods (Ale, Bread,
# Cheese, Wine) beside its Inn Stay and Meal service rows; the table is routed
# whole and only its goods are incorporable objects, so no lodging or meal
# price becomes a purchase cost. Excluded: Coins, and the sections pricing only
# services or upkeep (Lifestyle Expenses; Hirelings; Spellcasting) or
# procedures (Magic Items, Crafting, Brewing, Scribing). Scribing Spell Scrolls
# is the Spell Scroll adjustment's own accepted pointer, not this one.
FOOD = "equipment.food_drink_and_lodging"
PRICED_SECTIONS = (
    ("Weapons", "equipment.weapons"),
    ("Armor", "equipment.armor"),
    ("Tools", "equipment.tools"),
    ("Adventuring Gear", "equipment.adventuring_gear"),
    ("Mounts and Vehicles", "equipment.mounts_and_vehicles"),
    ("Food, Drink, and Lodging", FOOD),
)
PURCHASE_COST = _route(
    "Equipment with a purchase cost: Weapons, Armor, Tools, Adventuring Gear, "
    "Mounts and Vehicles, and the priced goods of Food, Drink, and Lodging",
    *((k, "") for _, k in PRICED_SECTIONS),
)

# --- Row 36 monsters.md 171: Gear entries name ordinary Equipment. The 39
# normalized names of the 45 explicit **Gear** entries (all monsters-A-Z.md),
# each its own route to its Equipment item; Wand adds the Arcane Focus entry
# whose Arcane Focuses table prices it and whose prose explains its use
# (equipment.md 1259-1297). The outside-Gear default (monsters.md 175) and the
# GM's latitude (183) stay in the citing prose; nothing is flagged unretrievable.
GEAR_SECTIONS = {
    "weapons": (
        "battleaxe club dagger greataxe greatclub greatsword hand_crossbow "
        "handaxe heavy_crossbow javelin light_crossbow light_hammer longbow "
        "longsword mace morningstar pike pistol rapier scimitar shortbow "
        "shortsword sickle spear warhammer"
    ),
    "armor": (
        "breastplate chain_mail chain_shirt half_plate_armor hide_armor "
        "leather_armor plate_armor shield splint_armor studded_leather_armor"
    ),
    "adventuring_gear": "component_pouch holy_symbol wand",
    "tools": "thieves_tools",
}
GEAR_KEYS = {
    slug: f"equipment.{section}.{slug}"
    for section, slugs in GEAR_SECTIONS.items()
    for slug in slugs.split()
}
GEAR_CONTEXT = {"wand": ("equipment.adventuring_gear.arcane_focus",)}


def _gear_slug(name: str) -> str:
    return re.sub(r"\W+", "_", name.lower().replace("'", "")).strip("_")


def _gear_names() -> list[str]:
    """Every explicit Gear name, quantity and plural removed, first-seen."""
    md = (SRC / "monsters-A-Z.md").read_text(encoding="utf-8")
    lines = re.findall(r"^\*\*Gear\*\* (.+?)\s*<br>$", md, re.M)
    assert len(lines) == 45, len(lines)
    out: list[str] = []
    for line in lines:
        for raw in line.split(", "):
            name = re.sub(r" \(\d+\)$", "", raw.strip())
            if _gear_slug(name) not in GEAR_KEYS and name.endswith("s"):
                name = name[:-1]
            out.append(name)
    return list(dict.fromkeys(sorted(out)))


GEAR = tuple(
    d
    for name in sorted(
        {
            "Battleaxe", "Breastplate", "Chain Mail", "Chain Shirt", "Club",
            "Component Pouch", "Dagger", "Greataxe", "Greatclub", "Greatsword",
            "Half Plate Armor", "Hand Crossbow", "Handaxe", "Heavy Crossbow",
            "Hide Armor", "Holy Symbol", "Javelin", "Leather Armor",
            "Light Crossbow", "Light Hammer", "Longbow", "Longsword", "Mace",
            "Morningstar", "Pike", "Pistol", "Plate Armor", "Rapier", "Scimitar",
            "Shield", "Shortbow", "Shortsword", "Sickle", "Spear", "Splint Armor",
            "Studded Leather Armor", "Thieves' Tools", "Wand", "Warhammer",
        }
    )  # fmt: skip
    for d in _route(
        f"Gear: {name}",
        (GEAR_KEYS[_gear_slug(name)], ""),
        *((k, "") for k in GEAR_CONTEXT.get(_gear_slug(name), ())),
    )
)

# --- Rows 48 and 60: Find Familiar's normal forms are every SRD CR 0 Beast
# (spells.md 2290): the 24 Animals and the Figurine's local Giant Fly, which
# keeps its Magic Items ownership. Pact of the Chain (classes.md 9126) offers the
# normal forms or seven named special forms; its routes are its own, not a
# recursive read of Find Familiar's citation. Special-form keys are those the
# accepted Pact resolutions already name.
GIANT_FLY = "magic_items.figurine_of_wondrous_power.giant_fly"
PACT = (
    "classes.warlock.eldritch_invocation_options.pact_of_the_chain",
    "pact_of_the_chain",
)
SPECIAL_FORMS = (
    ("Imp", "monsters.imp.imp"),
    ("Pseudodragon", "monsters.pseudodragon.pseudodragon"),
    ("Quasit", "monsters.quasit.quasit"),
    ("Skeleton", "monsters.skeletons.skeleton"),
    ("Sphinx of Wonder", "monsters.sphinxes.sphinx_of_wonder"),
    ("Sprite", "monsters.sprite.sprite"),
    ("Venomous Snake", "animals.venomous_snake"),
)


def _normal_forms() -> tuple[tuple[str, str], ...]:
    rows = json.loads(FAMILIAR_INVENTORY.read_text(encoding="utf-8"))
    return tuple((row["name"], row["record_key"]) for row in rows)


def _form_label(name: str, key: str) -> str:
    where = " (Magic Items stat block)" if key == GIANT_FLY else ""
    return f"{name}{where}"


NORMAL_FORMS = tuple(
    d
    for name, key in _normal_forms()
    for d in _route(f"Normal form: {_form_label(name, key)}", (key, ""))
)
PACT_FORMS = NORMAL_FORMS + tuple(
    d for name, key in SPECIAL_FORMS for d in _route(f"Special form: {name}", (key, ""))
)

# --- Row 54 magic-items.md 580: a capitalized creature name in bold points to
# its stat block, in "Monsters" unless the text states otherwise. Every bold
# creature-name cue in the official PDF's Magic Items A-Z (pp.209-252), in
# printed order; each route reads the stat block (the local block where the text
# directs to one) and then the item, whose description keeps the item-specific
# context and modifications (e.g. the Onyx Dog's Intelligence, Common and
# Blindsight). Bag of Tricks, Deck of Illusions, Elemental Gem and Manual of
# Golems print their creatures unbolded under their own accepted "Monsters"
# pointers and are not this citation's.
MI = "magic_items."
STAT_BLOCKS: tuple[tuple[str, str, str], ...] = (
    ("Bag of Beans", "Treant", "monsters.treant.treant"),
    ("Bag of Beans", "Shrieker Fungi", "monsters.fungi.shrieker_fungus"),
    ("Bag of Beans", "Bulette", "monsters.bulette.bulette"),
    (
        "Bag of Beans",
        "Mummy (example of the GM's Undead choice)",
        "monsters.mummies.mummy",
    ),
    (
        "Bag of Beans",
        "Mummy Lord (example of the GM's Undead choice)",
        "monsters.mummies.mummy_lord",
    ),
    (
        "Bowl of Commanding Water Elementals",
        "Water Elemental",
        "monsters.water_elemental.water_elemental",
    ),
    (
        "Brazier of Commanding Fire Elementals",
        "Fire Elemental",
        "monsters.fire_elemental.fire_elemental",
    ),
    (
        "Censer of Controlling Air Elementals",
        "Air Elemental",
        "monsters.air_elemental.air_elemental",
    ),
    ("Cloak of the Bat", "Bat", "animals.bat"),
    (
        "Dust of Dryness",
        "Water Elemental (example)",
        "monsters.water_elemental.water_elemental",
    ),
    ("Efreeti Bottle", "Efreeti", "monsters.efreeti.efreeti"),
    ("Feather Token", "Roc", "monsters.roc.roc"),
    (
        "Figurine of Wondrous Power",
        "Bronze Griffon: Griffon",
        "monsters.griffon.griffon",
    ),
    (
        "Figurine of Wondrous Power",
        "Ebony Fly: Giant Fly (local stat block)",
        GIANT_FLY,
    ),
    ("Figurine of Wondrous Power", "Golden Lions: Lion", "animals.lion"),
    (
        "Figurine of Wondrous Power",
        "Goat of Terror and Goat of Travail: Giant Goat",
        "animals.giant_goat",
    ),
    (
        "Figurine of Wondrous Power",
        "Goat of Traveling: Riding Horse statistics",
        "animals.riding_horse",
    ),
    ("Figurine of Wondrous Power", "Marble Elephant: Elephant", "animals.elephant"),
    (
        "Figurine of Wondrous Power",
        "Obsidian Steed: Nightmare",
        "monsters.nightmare.nightmare",
    ),
    ("Figurine of Wondrous Power", "Onyx Dog: Mastiff", "animals.mastiff"),
    ("Figurine of Wondrous Power", "Serpentine Owl: Giant Owl", "animals.giant_owl"),
    ("Figurine of Wondrous Power", "Silver Raven: Raven", "animals.raven"),
    ("Hat of Many Spells", "Camel", "animals.camel"),
    ("Hat of Many Spells", "Constrictor Snake", "animals.constrictor_snake"),
    ("Hat of Many Spells", "Elephant", "animals.elephant"),
    ("Hat of Many Spells", "Mule", "animals.mule"),
    ("Hat of Many Spells", "Swarm of Bats", "animals.swarm_of_bats"),
    ("Horn of Valhalla", "Berserker", "monsters.berserker.berserker"),
    ("Mysterious Deck", "Knight", "monsters.knight.knight"),
    (
        "Mysterious Deck",
        "Skull: Avatar of Death (local stat block)",
        "magic_items.mysterious_deck.avatar_of_death",
    ),
    ("Pipes of the Sewers", "Swarm of Rats", "animals.swarm_of_rats"),
    ("Ring of Djinni Summoning", "Djinni", "monsters.djinni.djinni"),
    ("Robe of Useful Items", "Riding Horse", "animals.riding_horse"),
    ("Robe of Useful Items", "Mastiffs", "animals.mastiff"),
    (
        "Staff of the Python",
        "Giant Constrictor Snake",
        "animals.giant_constrictor_snake",
    ),
    (
        "Stone of Controlling Earth Elementals",
        "Earth Elemental",
        "monsters.earth_elemental.earth_elemental",
    ),
    ("Wand of Wonder", "Rhinoceros", "animals.rhinoceros"),
    ("Wand of Wonder", "Elephant", "animals.elephant"),
    ("Wand of Wonder", "Rat", "animals.rat"),
    ("Wand of Wonder", "Black Bear", "animals.black_bear"),
    ("Wand of Wonder", "Giant Wasp", "animals.giant_wasp"),
    ("Wand of Wonder", "Frog", "animals.frog"),
)
LOCAL_BLOCKS = {GIANT_FLY, "magic_items.mysterious_deck.avatar_of_death"}
NOT_BOLD_ITEMS = (
    "bag_of_tricks",
    "deck_of_illusions",
    "elemental_gem",
    "manual_of_golems",
)


def _item_key(item: str) -> str:
    return MI + re.sub(r"\W+", "_", item.lower()).strip("_")


ITEM_STAT_BLOCKS = tuple(
    d
    for item, creature, key in STAT_BLOCKS
    for d in _route(f"{item}: {creature}", (key, ""), (_item_key(item), ""))
)

# --- Row 57 spells.md 687: "The GM chooses statistics appropriate for the
# awakened Plant, such as the statistics for the Awakened Shrub or Awakened Tree
# in "Monsters."" Examples of an open GM choice, not an eligibility list. The
# Owner's Awakened Plant is a house rule (docs/house-rules/awakened-plant.md),
# not SRD canon, and is not a destination.
AWAKENED_EXAMPLES = _route(
    "GM's choice, SRD example: Awakened Shrub",
    ("monsters.awakened_plants.awakened_shrub", ""),
) + _route(
    "GM's choice, SRD example: Awakened Tree",
    ("monsters.awakened_plants.awakened_tree", ""),
)

# --- Row 76 playing-the-game.md 186: "Playing the Game" and "Rules Glossary"
# explain which ability modifiers to use for various D20 Tests. The bounded
# glossary inventory of the 6 October clarification: the D20 Test definitions,
# the entry on adding an ability modifier, and the four operative rules that
# name their ability, as examples (specific rules keep their ownership). The
# Proficiency bullet beside it is a separate accepted pointer (play.proficiency).
D20_DEFINITIONS = _route(
    "Which ability: D20 Test, Ability Check, Saving Throw and Attack Roll",
    ("glossary.d20_test", ""),
    ("glossary.ability_check", ""),
    ("glossary.saving_throw", ""),
    ("glossary.attack_roll", ""),
)
APPLYING_MODIFIER = _route(
    "Applying the modifier: Ability Score and Modifier",
    ("glossary.ability_score_and_modifier", ""),
)
OPERATIVE_EXAMPLES = _route(
    "Specific rules naming their ability (examples): Hide, Search, Study, "
    "Unarmed Strike",
    ("glossary.hide", ""),
    ("glossary.search", ""),
    ("glossary.study", ""),
    ("glossary.unarmed_strike", ""),
)
ABILITY_MODIFIERS = D20_DEFINITIONS + APPLYING_MODIFIER + OPERATIVE_EXAMPLES

# --- Rows 39, 87 and 88: one destination each, stated as the plain target.
SPELLBOOK = _route("Wizard: Spellbook", ("classes.wizard.spellcasting", ""))
CANTRIPS = _route("Casting Spells: Cantrips", ("spells.casting_spells", ""))
RITUALS = _route("Casting Spells: Rituals", ("spells.casting_spells", ""))

DRAFTS: dict[Citation, Draft] = {
    (
        "magic_items.magic_item_rarity.magic_item_values_by_rarity",
        "magic_item_values_by_rarity",
        'a purchase cost in "Equipment"',
        EQ,
    ): ("#34", PURCHASE_COST),
    ("monsters.parts_of_a_stat_block", "gear", "Equipment", EQ): ("#36", GEAR),
    ("classes.wizard", "core_traits", "Spellbook", EQ): ("#39", SPELLBOOK),
    (*PACT, "Monsters", MONSTERS): ("#48", PACT_FORMS),
    (
        "magic_items.magic_items_a_z",
        "magic_items_a_z",
        'the stat block is in "Monsters."',
        MONSTERS,
    ): ("#54", ITEM_STAT_BLOCKS),
    ("spells.awaken", "effect", "Monsters", MONSTERS): ("#57", AWAKENED_EXAMPLES),
    ("spells.find_familiar", "effect", "Monsters", MONSTERS): ("#60", NORMAL_FORMS),
    ("play.d20_tests", "add_modifiers", "Rules Glossary", GLOSSARY): (
        "#76",
        ABILITY_MODIFIERS,
    ),
    ("glossary.cantrip", "", "Spells", SPELLS): ("#87", CANTRIPS),
    ("glossary.ritual", "", "Spells", SPELLS): ("#88", RITUALS),
}
#: Destinations outside the citation's printed scope, reconciled explicitly.
SCOPE_EXCEPTIONS = {
    "#39": {"classes.wizard.spellcasting"},
    "#48": {GIANT_FLY},
    "#54": {_item_key(i) for i, _, _ in STAT_BLOCKS} | LOCAL_BLOCKS,
    "#60": {GIANT_FLY},
}
SCOPE_PREFIX: dict[str, str | tuple[str, ...]] = {
    EQ: "equipment.",
    MONSTERS: ("monsters.", "animals."),
    GLOSSARY: "glossary.",
    SPELLS: "spells.",
}


def drafts(
    inputs: AcceptedInputs, which: dict[Citation, Draft] = DRAFTS
) -> tuple[ReferenceResolution, ...]:
    """One reviewed resolution per drafted citation, keyed from the artifact."""
    oracle = inputs.oracle
    view = effective_representation(oracle.representation, oracle.reference_resolutions)
    spans: dict[tuple[str, ...], set[str]] = {}
    for claim in view.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            spans.setdefault(claim.target_key, set()).add(claim.span_id)
    by_citation = {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key): r
        for r in view.references
        if not r.target_record_key
    }
    out = []
    for citation, (row, destinations) in which.items():
        ref = by_citation[citation]
        # The native shape: one destination is the plain target, unlabelled.
        single = destinations if len(destinations) == 1 else ()
        out.append(
            ReferenceResolution(
                resolution_id=f"cited-{row[1:]}-{citation[0]}-{citation[1]}",
                from_record_key=citation[0],
                from_component_key=citation[1],
                source_text=citation[2],
                scope_key=citation[3],
                target_record_key=single[0].target_record_key if single else "",
                release_binding=oracle.binding,
                provenance_span_ids=tuple(sorted(spans[reference_target_key(ref)])),
                destinations=() if single else destinations,
            )
        )
    return tuple(out)


def members(inputs: AcceptedInputs) -> dict[str, set[str]]:
    """catalogue -> its one-hop ``CATALOGUE_MEMBER`` records."""
    out: dict[str, set[str]] = {}
    for rel in inputs.oracle.representation.relationships:
        if rel.kind.value == "catalogue_member":
            out.setdefault(rel.target_record_key, set()).add(rel.source_record_key)
    return out


def _line(path: str, at: int) -> str:
    return (SRC / path).read_text(encoding="utf-8").splitlines()[at - 1]


def _cr0_beasts() -> set[str]:
    """Every stat block in the source typed Beast with Challenge Rating 0."""
    found = set()
    for path in ("animals.md", "monsters-A-Z.md", "magic-items.md"):
        lines = (SRC / path).read_text(encoding="utf-8").splitlines()
        name = ""
        beast = False
        for line in lines:
            if m := re.match(r"^#{2,5} (.+)$", line):
                name, beast = m[1], False
            elif re.match(r"^_\w+(?: or \w+)? Beast[,_ ]", line):
                beast = True
            elif beast and re.match(r"^\*\*CR\*\* 0 \(", line):
                found.add(name)
    return found


def _sources(inputs: AcceptedInputs) -> None:
    """Every drafted group is the source's, and every destination is stated."""
    r = inputs.oracle.representation
    kinds = {x.semantic_key: x.kind.value for x in r.records}
    for row, destinations in DRAFTS.values():
        assert destinations, row
        for d in destinations:
            assert d.target_record_key in kinds and not d.target_component_key, d
            assert not (d.situation or d.class_record_key or d.minimum_class_level)
        labels = [d.alternative_label for d in destinations]
        routes = list(dict.fromkeys(labels))
        assert labels == [x for x in routes for _ in range(labels.count(x))], row
    # Scope: every destination is in its citation's printed scope unless it is a
    # named, reconciled exception (and every exception is actually used).
    for (_, _, _, scope), (row, destinations) in DRAFTS.items():
        outside = {
            d.target_record_key
            for d in destinations
            if not d.target_record_key.startswith(SCOPE_PREFIX[scope])
        }
        assert outside == SCOPE_EXCEPTIONS.get(row, set()), (row, outside)
    cat = members(inputs)

    # 34: the rule and its examples; the five sections price objects.
    assert 'has a purchase cost in "Equipment"' in _line("magic-items.md", 181)
    assert "Plate Armor) " in _line("magic-items.md", 181) + " "
    assert "5,500 GP" in _line("magic-items.md", 182)
    eq = (SRC / "equipment.md").read_text(encoding="utf-8")
    for heading, key in PRICED_SECTIONS:
        assert f"\n## {heading}\n" in eq, heading
        assert kinds[key] and (key == FOOD or cat[key]), key
    headings = [eq.index(f"\n## {h}\n") for h, _ in PRICED_SECTIONS]
    assert headings == sorted(headings)
    # Food, Drink, and Lodging has no item members: its table prices the goods.
    assert not cat.get(FOOD)
    for good, cost in (("Ale (mug)", "4 CP"), ("Bread (loaf)", "2 CP")):
        assert f"<td>{good}</td>\n      <td>{cost}</td>" in eq, good
    assert "<td>Cheese (wedge)</td>\n      <td>1 SP</td>" in eq
    assert "<em>Wine (bottle)</em>" in eq
    # Glaive has no item record: its 20 GP is only the Weapons table's row.
    assert _line("equipment.md", 266).strip() == "<td>Glaive</td>"
    assert _line("equipment.md", 271).strip() == "<td>20 GP</td>"
    assert "equipment.weapons.glaive" not in kinds
    for section, slugs in GEAR_SECTIONS.items():
        for slug in slugs.split():
            assert f"equipment.{section}.{slug}" in cat[f"equipment.{section}"], slug

    # 36: the 45 Gear entries normalize to exactly the 39 routed names.
    assert len(_gear_names()) == 39
    assert {_gear_slug(n) for n in _gear_names()} == set(GEAR_KEYS)
    assert {d.alternative_label for d in GEAR} == {f"Gear: {n}" for n in _gear_names()}
    assert _line("monsters.md", 169) == "### Gear"
    assert "unusable when the monster is defeated" in _line("monsters.md", 175)
    assert "Thieves' Tools (25 GP)" in _line("equipment.md", 760)
    assert _line("equipment.md", 1259) == "#### Arcane Focus (Varies)"
    assert _line("equipment.md", 1295).strip() == "<td>Wand</td>"
    assert _line("equipment.md", 1297).strip() == "<td>10 GP</td>"

    # 39: the Wizard's starting Spellbook is its own Spellcasting rule.
    assert "Spellbook" in _line("classes.md", 9765)
    assert _line("classes.md", 10152).startswith("_Spellbook._")
    assert "spellbook" in {
        c.semantic_key.rsplit(".", 1)[-1]
        for c in r.components
        if c.record_key == "classes.wizard.spellcasting"
    } | {
        c.semantic_key
        for c in r.components
        if c.record_key == "classes.wizard.spellcasting"
    }
    assert not any(
        k.endswith(".spellbook") for k in kinds if k.startswith("equipment.")
    )

    # 48/60: the inventory is every CR 0 Beast stat block in the source.
    assert _sha(FAMILIAR_INVENTORY.read_bytes()) == FAMILIAR_INVENTORY_SHA256
    forms = _normal_forms()
    assert len(forms) == 25 and forms[-1] == ("Giant Fly", GIANT_FLY), forms[-1]
    assert {n for n, _ in forms} == _cr0_beasts(), {n for n, _ in forms} ^ _cr0_beasts()
    for _, key in forms:
        assert kinds[key] == "creature", key
    ff = _line("spells.md", 2290)
    assert "or another Beast that has a Challenge Rating of 0" in ff
    pact = _line("classes.md", 9126)
    for name, key in SPECIAL_FORMS:
        assert f"{name}" in pact and kinds[key] == "creature", name
    accepted_pact = {
        x.target_record_key
        for x in inputs.oracle.reference_resolutions
        if x.from_record_key == PACT[0] and x.from_component_key == PACT[1]
    }
    assert {k for _, k in SPECIAL_FORMS} <= accepted_pact, accepted_pact

    # 54: the bold-cue rule; each item is a magic item, each block a creature;
    # every routed pair is one the accepted item already cites, and every
    # accepted creature citation of a bold-cue item is routed.
    assert "presents it in **bold** type" in _line("magic-items.md", 580)
    view = effective_representation(r, inputs.oracle.reference_resolutions)
    cited: set[tuple[str, str]] = set()
    for ref in view.references:
        if kinds.get(ref.target_record_key) == "creature":
            cited.add((ref.from_record_key, ref.target_record_key))
    routed = {(_item_key(i), k) for i, _, k in STAT_BLOCKS}
    items = {_item_key(i) for i, _, _ in STAT_BLOCKS}
    for item, key in routed:
        assert kinds[item] == "magic_item" and kinds[key] == "creature", (item, key)
    assert routed == {(i, k) for i, k in cited if i in items}, routed ^ cited
    for item in NOT_BOLD_ITEMS:
        assert any(
            x.from_record_key == MI + item
            and x.scope_key == MONSTERS
            and x.destinations
            for x in inputs.oracle.reference_resolutions
        ), item
    for local in LOCAL_BLOCKS:
        assert kinds[local] == "creature" and local.startswith(MI)
    onyx = _line("magic-items.md", 2118)
    assert "Intelligence of 8" in onyx and "Blindsight" in onyx

    # 57: the GM's choice and its two examples.
    awaken = _line("spells.md", 687)
    assert "The GM chooses statistics appropriate for the awakened Plant, such as" in (
        awaken
    )
    assert cat["monsters.awakened_plants"] == {
        "monsters.awakened_plants.awakened_shrub",
        "monsters.awakened_plants.awakened_tree",
    }

    # 76: the pointer, and the glossary entries it routes, by heading.
    assert "explain which ability modifiers to use" in _line("playing-the-game.md", 186)
    glossary = (SRC / "rules-glossary.md").read_text(encoding="utf-8")
    for d in ABILITY_MODIFIERS:
        title = d.target_record_key.removeprefix("glossary.").replace("_", " ")
        assert re.search(
            rf"^#### {re.escape(title)}( \[\w+\])?$", glossary, re.M | re.I
        ), title

    # 87/88: record-owned "See also Spells" in the two glossary entries; Casting
    # Spells carries the Cantrips and Rituals rules (spells.md 95, 97).
    assert _line("rules-glossary.md", 377) == "#### Cantrip"
    assert _line("rules-glossary.md", 379).endswith('_See also_ "Spells."')
    assert _line("rules-glossary.md", 1224) == "#### Ritual"
    assert _line("rules-glossary.md", 1226).endswith('_See also_ "Spells."')
    assert _line("spells.md", 95).startswith("**Cantrips.**")
    assert _line("spells.md", 97).startswith("**Rituals.**")
    casting = {
        c.semantic_key for c in r.components if c.record_key == "spells.casting_spells"
    }
    assert {"cantrips", "rituals"} <= {k.rsplit(".", 1)[-1] for k in casting}, casting


def resolved(
    inputs: AcceptedInputs, which: dict[Citation, Draft] = DRAFTS
) -> AcceptedInputs:
    """Resolve the accepted schema-17 artifact, as one native action (SIMULATED)."""
    return resolve_references(
        inputs,
        resolutions=drafts(inputs, which),
        authorized_by=SIMULATED_REVIEWER,
        authorization_reference=SIMULATED_RULE,
        reviewer=SIMULATED_REVIEWER,
        resolved_at=SIMULATED_AT,
    )


def _preserved(
    before: AcceptedInputs, after: AcceptedInputs, new_ids: set[str]
) -> dict[str, tuple[int, int]]:
    """Every accepted item is carried verbatim; the only additions are the new
    resolutions, their approval records and the references they resolve."""
    old, new = accepted_inputs_payload(before), accepted_inputs_payload(after)
    out: dict[str, tuple[int, int]] = {}
    for path in REPL.COLLECTIONS:
        a = Counter(REPL._key(x) for x in REPL._at(old, path))
        b = Counter(REPL._key(x) for x in REPL._at(new, path))
        lost, added = a - b, b - a
        assert not lost, (path, next(iter(lost))[:300])
        for k in added:
            assert json.loads(k).get("resolution_id") in new_ids, (path, k[:300])
        if added:
            out[".".join(path)] = (0, sum(added.values()))
    assert before.batches == after.batches
    assert before.acceptances == after.acceptances
    assert before.policy_transitions == after.policy_transitions
    o, p = before.oracle, after.oracle
    for name in ("binding", "schema_version", "schema_hash", "representation"):
        assert getattr(o, name) == getattr(p, name), name
    olds = {r.resolution_id: r for r in o.reference_resolutions}
    news = {r.resolution_id: r for r in p.reference_resolutions}
    assert all(news.get(k) == v for k, v in olds.items()), "resolution changed"
    assert set(news) - set(olds) == new_ids, set(news) - set(olds)
    old_acc = before.reference_resolution_acceptances
    new_acc = after.reference_resolution_acceptances
    assert set(old_acc) <= set(new_acc), "approval changed"
    for acc in set(new_acc) - set(old_acc):
        assert acc.resolution_id in new_ids, acc
        assert (acc.authorized_by, acc.reviewer) == (SIMULATED_REVIEWER,) * 2, acc
        assert acc.authorization_reference == SIMULATED_RULE, acc
        assert acc.authorized_by.startswith("SIMULATION"), acc
    return out


def _report(name: str, before: list[str], after: list[str]) -> None:
    print(
        f"findings {name} (refs, leaves)", APC._split(before), "->", APC._split(after)
    )
    cleared = Counter(before) - Counter(after)
    new = Counter(after) - Counter(before)
    print("  cleared", sum(cleared.values()), "new", dict(new))
    assert not new, new
    for line in sorted(cleared.elements()):
        print("  cleared", line[:200])


def main(argv: list[str]) -> None:
    if argv not in ([], ["--write"]):
        raise SystemExit("usage: [--write]")
    write = argv == ["--write"]
    print("SIMULATED (in memory; nothing accepted or recorded)")
    print("simulated reviewer", repr(SIMULATED_REVIEWER), "rule", repr(SIMULATED_RULE))
    committed = ACCEPTED_PATH.read_bytes()
    assert _sha(committed) == ACCEPTED_SHA256, "accepted changed"
    rec = load_accepted_inputs(ACCEPTED_PATH)
    current = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    assert (rec.oracle.schema_version, rec.oracle.schema_hash) == current, current
    assert serialize_accepted_inputs(rec) == committed, "accepted does not round-trip"
    print("schema", current[0], "accepted", ACCEPTED_SHA256)
    _sources(rec)
    print("sources: every drafted group matches the pinned markdown")

    before = APC.findings(rec)
    print("control: accepted, proposed resolutions absent", APC._split(before))
    final = resolved(rec)
    after = APC.findings(final)
    _report("all ten", before, after)
    for line in sorted(after):
        print("  remains", line[:200])
    assert not after, after

    final_bytes = serialize_accepted_inputs(final)
    print("candidate (simulated)", _sha(final_bytes))
    reloaded = FRR.load_accepted_inputs_bytes(final_bytes)
    assert serialize_accepted_inputs(reloaded) == final_bytes, "reload"
    print("  reloads to the same bytes True")
    new_ids = {r.resolution_id for r in drafts(rec)}
    assert len(new_ids) == 10
    changes = _preserved(rec, reloaded, new_ids)
    print(
        "preserved: every accepted item verbatim, including",
        len(rec.oracle.reference_resolutions),
        "resolutions with",
        len(rec.reference_resolution_acceptances),
        "approvals; added:",
    )
    for collection, n in changes.items():
        print("  ", collection, n)
    print("counts", REPL._counts(rec), "->", REPL._counts(reloaded))

    resolutions = tuple(
        r for r in final.oracle.reference_resolutions if r.resolution_id in new_ids
    )
    print(
        "resolutions",
        len(resolutions),
        "destinations",
        sum(len(r.destinations) or 1 for r in resolutions),
    )
    for r in resolutions:
        row = DRAFTS[
            (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        ][0]
        labels = list(dict.fromkeys(d.alternative_label for d in r.destinations))
        print(f"  {row} {r.resolution_id} routes {len(labels)}", end="")
        print(f" destinations {len(r.destinations) or 1}")
    print("persisted round trip", FRR._persisted_round_trip(final))
    assert _sha(ACCEPTED_PATH.read_bytes()) == ACCEPTED_SHA256, "accepted changed"
    print("live accepted oracle unchanged", ACCEPTED_SHA256)

    proposal = (
        json.dumps(
            {
                "accepted_sha256": ACCEPTED_SHA256,
                "representation_schema": list(current),
                "simulated_only": True,
                "reference_resolutions": reference_resolution_payload(resolutions),
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    delta = (
        "# SIMULATED candidate; no Owner approval\n"
        "# Full-text delta from the accepted artifact (evidence blanked)\n"
        + "".join(f"{x}\n" for x in REPL.Delta(rec, reloaded).report())
        + "# Effective reference lines\n"
        + FRR._delta(rec, final)
    ).encode("utf-8")
    for path, data in ((PROPOSAL_FILE, proposal), (DELTA_FILE, delta)):
        if write:
            path.write_bytes(data)
        assert path.read_bytes() == data, f"{path.name} is stale; run --write"
        print(path.name, _sha(data), f"{data.count(b'\n')} lines")
    print("OK")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    main(sys.argv[1:])
