"""The finite-reference-routes candidate, composed in memory.

CRD Issue 5d (#132, #137). REVIEW MATERIAL: nothing here is accepted,
recorded, published or activated, and no Owner approval exists for it. There
is deliberately no recording step.

Inventory rows #23, #38, #49, #51, #52, #53, #55, #71, #73 and the explanatory
occurrence of #54 (``issue-5d-remaining-references-review.md``) are ten
accepted unresolved citations whose source names a finite set of destinations:
a table of creatures, a list of classes' spell lists, the foci the Equipment
chapter describes and the Bard's instrument, a pair of attack-kind sections, or
the Monsters chapter.
Each is resolved to labelled routes under the accepted schema-17 semantics
(ADR-005d Decision 7, amended 2026-10-01): one reviewed decision per citation,
a route's destinations read together in source order (landing first), routes
not exclusive. Labels carry the source's own conditions (bag colour and roll,
gem, card, manual, attack kind, listed sense); no destination is class-gated,
because none of these conditions is the reader's class. Every destination is a
record the accepted authority already states; ``_sources`` checks each drafted
group against the pinned source markdown.

The other #54 occurrence (``the stat block is in "Monsters."``) is out of this
batch and stays unresolved. Deck of Illusions' "The card drawer" result has no
route: the source's footnote excludes it from the Monsters stat blocks.

The Ranged Attacks introduction (playing-the-game.md 1072) is #71's landing
but the accepted combat batch holds it as framing, so it has no component. An
unaccepted combat-damage-breaking replacement (:func:`combat_edit`, its
generator otherwise unchanged) makes it the ``play.combat/ranged`` prose
component, the analogue of ``melee``. Acceptance has no supersession, so the
chain is composed afresh (:func:`composed`): the recorded Equipment
class-eligibility chain at its recorded evidence, the replacement accepted in
combat's recorded place under the simulated reviewer, then the recorded
schema-17 step (lift and the Owner's resolutions) verbatim. Without the
replacement the same composition is the accepted artifact, byte for byte.
``resolve_references`` then resolves the routes in one action under the
simulated reviewer.

Run: ``python issue-5d-finite-reference-routes-REPLACEMENT.py [--write]``.
``--write`` regenerates the combat proposal and the proposal and delta files;
otherwise they are checked. Either way the chain is composed twice (about two
minutes each): once as the control, once with the replacement.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.mechanical.acceptance import (  # noqa: E402
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.authoring import (  # noqa: E402
    EntryBatch,
    build_entry_batch,
    render,
)
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    published_release_binding,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ReferenceDestination,
    ReferenceResolution,
)
from afterworlds.ingestion.mechanical.oracle import (  # noqa: E402
    AcceptedInputs,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (  # noqa: E402
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    identify_projection,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.reference_resolution import (  # noqa: E402
    AlternativeSelection,
    effective_representation,
    reference_resolution_payload,
    select_alternatives,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    REPRESENTATION_SCHEMA_VERSION,
    ProvenanceTargetKind,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.persistence.database import (  # noqa: E402
    create_engine,
    create_session_factory,
)
from afterworlds.persistence.orm.base import Base  # noqa: E402


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


#: The recorded schema-17 step and, through it, the recorded chain, the
#: findings reader and the scratch release (read-only copies).
RA = _load(
    "reference_alternatives_accept",
    HERE / "issue-5d-reference-alternatives-ACCEPT.py",
)
ECE = RA.ECE
REPL = ECE.REPL
APC = ECE.APC
SCRATCH_DB: Path = REPL.SCRATCH_DB
SIMULATED_REVIEWER: str = ECE.SIMULATED_REVIEWER
SIMULATED_RULE: str = ECE.SIMULATED_RULE
SIMULATED_AT = "2026-10-01T00:00:00Z"

ACCEPTED_PATH = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json"
)
ACCEPTED_SHA256 = "cc994e1badee3baf733d2df5d5c88903ad96b4ddd0172f52111ecdf0b4c1f190"

TAG = "finite-reference-routes"
PROPOSAL_FILE = HERE / f"issue-5d-{TAG}-PROPOSAL.json"
DELTA_FILE = HERE / f"issue-5d-{TAG}-DELTA.txt"
SRC = REPO / "docs/sources/community/dnd-5e-srd-markdown"


def _d(record: str, component: str, label: str) -> ReferenceDestination:
    """A label-only destination: no situation, class or level condition."""
    return ReferenceDestination(
        target_record_key=record,
        target_component_key=component,
        alternative_label=label,
        situation="",
        class_record_key="",
        minimum_class_level=0,
    )


def _route(label: str, *targets: tuple[str, str]) -> tuple[ReferenceDestination, ...]:
    """One route: its destinations in source order, the first the landing."""
    return tuple(_d(record, component, label) for record, component in targets)


# --- #23 Pact of the Tome: "any class's spell list" (classes.md 9134). The
# chosen spells are cantrips and level 1 Ritual spells, so each class's route is
# its list's introduction (which defines the R tag), then its Cantrips and Level
# 1 tables. Paladin and Ranger lists have no Cantrips table. The class is the
# list's, not the reader's, so nothing is class-gated.
SPELL_LISTS = (
    ("bard", True),
    ("cleric", True),
    ("druid", True),
    ("paladin", False),
    ("ranger", False),
    ("sorcerer", True),
    ("warlock", True),
    ("wizard", True),
)
TOME = tuple(
    d
    for c, cantrips in SPELL_LISTS
    for d in _route(
        f"{c.capitalize()} spell list: "
        + ("cantrips; " if cantrips else "no cantrips; ")
        + "level 1 spells with the Ritual tag",
        (f"classes.{c}", "spell_list"),
        *([(f"classes.{c}", "cantrips")] if cantrips else []),
        (f"classes.{c}", "level_1_spells"),
    )
)

# --- #38 spells.md 208: "(see "Equipment" for descriptions)" closes the
# sentence on both the Component Pouch and the Spellcasting Focus, so the
# descriptions are the pouch's and every focus's, in equipment.md order: the
# Musical Instrument tool (746), then the gear (1259, 1386, 1402, 1459). Each
# focus label quotes who may use it. The instrument's grant is not in its
# Equipment entry but in the Bard's Spellcasting feature (classes.md 846), so
# that feature follows it as the companion carrying the condition; it is a
# label, not a class gate. The spell rule's own condition ("a feature that
# allows that substitution") stays in the citing text.
GEAR = "equipment.adventuring_gear"
BARD_FOCUS = ("classes.bard.spellcasting", "spellcasting_focus")
POUCH_AND_FOCI = (
    *_route(
        "Musical Instrument: a Bard can use it as a Spellcasting Focus for Bard "
        "spells",
        ("equipment.tools.musical_instrument", ""),
        BARD_FOCUS,
    ),
    *_route(
        "Arcane Focus: a Sorcerer, Warlock, or Wizard can use it as a "
        "Spellcasting Focus",
        (f"{GEAR}.arcane_focus", ""),
    ),
    *_route("Component Pouch", (f"{GEAR}.component_pouch", "")),
    *_route(
        "Druidic Focus: a Druid or Ranger can use it as a Spellcasting Focus",
        (f"{GEAR}.druidic_focus", ""),
    ),
    *_route(
        "Holy Symbol: a Cleric or Paladin can use it as a Spellcasting Focus",
        (f"{GEAR}.holy_symbol", ""),
    ),
)

# --- #49 equipment.md 1684: "See "Monsters" for the animals' stat blocks" --
# every row of the Mounts and Other Animals table, in table order.
MOUNTS = (
    ("Camel", "animals.camel"),
    ("Elephant", "animals.elephant"),
    ("Horse, Draft", "animals.draft_horse"),
    ("Horse, Riding", "animals.riding_horse"),
    ("Mastiff", "animals.mastiff"),
    ("Mule", "animals.mule"),
    ("Pony", "animals.pony"),
    ("Warhorse", "animals.warhorse"),
)

# --- #51 magic-items.md 962: each bag colour's 1d8 table, in roll order.
BAGS: dict[str, tuple[tuple[str, str], ...]] = {
    "Gray": (
        ("Weasel", "animals.weasel"),
        ("Giant Rat", "animals.giant_rat"),
        ("Badger", "animals.badger"),
        ("Boar", "animals.boar"),
        ("Panther", "animals.panther"),
        ("Giant Badger", "animals.giant_badger"),
        ("Dire Wolf", "animals.dire_wolf"),
        ("Giant Elk", "animals.giant_elk"),
    ),
    "Rust": (
        ("Rat", "animals.rat"),
        ("Owl", "animals.owl"),
        ("Mastiff", "animals.mastiff"),
        ("Goat", "animals.goat"),
        ("Giant Goat", "animals.giant_goat"),
        ("Giant Boar", "animals.giant_boar"),
        ("Lion", "animals.lion"),
        ("Brown Bear", "animals.brown_bear"),
    ),
    "Tan": (
        ("Jackal", "animals.jackal"),
        ("Ape", "animals.ape"),
        ("Baboon", "animals.baboon"),
        ("Axe Beak", "monsters.axe_beak.axe_beak"),
        ("Black Bear", "animals.black_bear"),
        ("Giant Weasel", "animals.giant_weasel"),
        ("Giant Hyena", "animals.giant_hyena"),
        ("Tiger", "animals.tiger"),
    ),
}

# --- #52 the Deck of Illusions table, in 1d100 order. Its footnote: "Stat
# blocks for these creatures (except the card drawer) appear in "Monsters."" --
# so 97-00 has no route.
DECK = (
    ("01–03", "Adult Red Dragon", "monsters.red_dragons.adult_red_dragon"),
    ("04–06", "Archmage", "monsters.mages.archmage"),
    ("07–09", "Assassin", "monsters.assassin.assassin"),
    ("10–12", "Bandit Captain", "monsters.bandits.bandit_captain"),
    ("13–15", "Basilisk", "monsters.basilisk.basilisk"),
    ("16–18", "Berserker", "monsters.berserker.berserker"),
    ("19–21", "Bugbear Warrior", "monsters.bugbears.bugbear_warrior"),
    ("22–24", "Cloud Giant", "monsters.cloud_giant.cloud_giant"),
    ("25–27", "Druid", "monsters.druid.druid"),
    ("28–30", "Erinyes", "monsters.erinyes.erinyes"),
    ("31–33", "Ettin", "monsters.ettin.ettin"),
    ("34–36", "Fire Giant", "monsters.fire_giant.fire_giant"),
    ("37–39", "Frost Giant", "monsters.frost_giant.frost_giant"),
    ("40–42", "Gnoll Warrior", "monsters.gnoll.gnoll_warrior"),
    ("43–45", "Goblin Warrior", "monsters.goblins.goblin_warrior"),
    ("46–48", "Guardian Naga", "monsters.guardian_naga.guardian_naga"),
    ("49–51", "Hill Giant", "monsters.hill_giant.hill_giant"),
    ("52–54", "Hobgoblin Warrior", "monsters.hobgoblins.hobgoblin_warrior"),
    ("55–57", "Incubus", "monsters.incubus.incubus"),
    ("58–60", "Iron Golem", "monsters.iron_golem.iron_golem"),
    ("61–63", "Knight", "monsters.knight.knight"),
    ("64–66", "Kobold Warrior", "monsters.kobold.kobold_warrior"),
    ("67–69", "Lich", "monsters.lich.lich"),
    ("70–72", "Medusa", "monsters.medusa.medusa"),
    ("73–75", "Night Hag", "monsters.night_hag.night_hag"),
    ("76–78", "Ogre", "monsters.ogre.ogre"),
    ("79–81", "Oni", "monsters.oni.oni"),
    ("82–84", "Priest", "monsters.priests.priest"),
    ("85–87", "Succubus", "monsters.succubus.succubus"),
    ("88–90", "Troll", "monsters.troll.troll"),
    ("91–93", "Veteran Warrior", "monsters.warriors.veteran_warrior"),
    ("94–96", "Wyvern", "monsters.wyvern.wyvern"),
)
CARD_DRAWER = ("97–00", "The card drawer")

# --- #53 magic-items.md 1935: the gem table, in printed order.
GEMS = (
    ("Blue sapphire", "Air Elemental", "monsters.air_elemental.air_elemental"),
    ("Emerald", "Water Elemental", "monsters.water_elemental.water_elemental"),
    ("Red corundum", "Fire Elemental", "monsters.fire_elemental.fire_elemental"),
    ("Yellow diamond", "Earth Elemental", "monsters.earth_elemental.earth_elemental"),
)

# --- #55 magic-items.md 2658: the GM chooses the type or rolls 1d20.
GOLEMS = (
    ("1–5", "Clay Golem", "monsters.clay_golem.clay_golem"),
    ("6–17", "Flesh Golem", "monsters.flesh_golem.flesh_golem"),
    ("18", "Iron Golem", "monsters.iron_golem.iron_golem"),
    ("19–20", "Stone Golem", "monsters.stone_golem.stone_golem"),
)

# --- #71 monsters.md 379: "For details on different kinds of attacks, see
# "Playing the Game"". The kinds are ### Ranged Attacks (1070) and ### Melee
# Attacks (1084), each read whole through its bound components, the section's
# introduction (``ranged``, from the combat replacement; ``melee``) first; a
# stat block printing "Melee or Ranged Attack Roll" reads both, in source order.
COMBAT = "play.combat"
RANGED = (
    (COMBAT, "ranged"),
    (COMBAT, "range"),
    (COMBAT, "long_range"),
    (COMBAT, "close_combat"),
)
MELEE = ((COMBAT, "melee"), (COMBAT, "reach"), (COMBAT, "opportunity_attacks"))
ATTACK_KINDS = (
    *_route("Melee attack: Melee Attacks", *MELEE),
    *_route("Ranged attack: Ranged Attacks", *RANGED),
    *_route(
        "Melee or Ranged attack: Ranged Attacks and Melee Attacks",
        *RANGED,
        *MELEE,
    ),
)

# --- #73 monsters.md 189: Passive Perception is in every Senses entry; each
# special sense applies when listed. The four are every special sense any
# stat block in the release prints, the ones embedded in spells.md and
# magic-items.md included (``_sources``), not a glossary-closed set.
SPECIAL_SENSES = ("blindsight", "darkvision", "tremorsense", "truesight")
SENSES = (
    *_route(
        "Passive Perception: every Senses entry",
        ("glossary.passive_perception", "passive_perception"),
    ),
    *(
        d
        for s in SPECIAL_SENSES
        for d in _route(
            f"Special sense, when listed: {s.capitalize()}", (f"glossary.{s}", s)
        )
    ),
)

# --- #54 (explanatory occurrence only) magic-items.md 580: the Monsters
# chapter's two sections, read together. Challenge Rating is a
# CATALOGUE_MEMBER of Parts of a Stat Block, so the whole record reaches it.
READING_STAT_BLOCKS = _route(
    "How to read and use a stat block",
    ("monsters.stat_block_overview", ""),
    ("monsters.parts_of_a_stat_block", ""),
)

MONSTERS = "srd-5.2.1/monsters"
DRAFTS: dict[
    tuple[str, str, str, str], tuple[str, tuple[ReferenceDestination, ...]]
] = {
    (
        "classes.warlock.eldritch_invocation_options.pact_of_the_tome",
        "cantrips_and_rituals",
        "any class's spell list",
        "srd-5.2.1/classes",
    ): ("#23", TOME),
    (
        "spells.components",
        "component_pouch_and_focus",
        'see "Equipment" for descriptions',
        "srd-5.2.1/equipment",
    ): ("#38", POUCH_AND_FOCI),
    ("equipment.mounts_and_vehicles", "mounts", "Monsters", MONSTERS): (
        "#49",
        tuple(d for name, key in MOUNTS for d in _route(name, (key, ""))),
    ),
    ("magic_items.bag_of_tricks", "bag_of_tricks", "Monsters", MONSTERS): (
        "#51",
        tuple(
            d
            for colour, rows in BAGS.items()
            for n, (name, key) in enumerate(rows, 1)
            for d in _route(f"{colour} Bag of Tricks, 1d8 roll {n}: {name}", (key, ""))
        ),
    ),
    ("magic_items.deck_of_illusions", "deck_of_illusions", "Monsters", MONSTERS): (
        "#52",
        tuple(
            d
            for band, name, key in DECK
            for d in _route(f"Deck of Illusions, 1d100 {band}: {name}", (key, ""))
        ),
    ),
    ("magic_items.elemental_gem", "elemental_gem", "Monsters", MONSTERS): (
        "#53",
        tuple(
            d for gem, name, key in GEMS for d in _route(f"{gem}: {name}", (key, ""))
        ),
    ),
    ("magic_items.manual_of_golems", "manual_of_golems", "Monsters", MONSTERS): (
        "#55",
        tuple(
            d
            for band, name, key in GOLEMS
            for d in _route(
                f"{name} manual (1d20 {band}, or the GM's choice)", (key, "")
            )
        ),
    ),
    (
        "monsters.parts_of_a_stat_block",
        "attack_notation",
        "Playing the Game",
        "srd-5.2.1/playing-the-game",
    ): ("#71", ATTACK_KINDS),
    (
        "monsters.parts_of_a_stat_block",
        "senses",
        "Rules Glossary",
        "srd-5.2.1/rules-glossary",
    ): ("#73", SENSES),
    (
        "magic_items.magic_items_a_z",
        "magic_items_a_z",
        'How to read and use a stat block is explained in "Monsters."',
        MONSTERS,
    ): ("#54", READING_STAT_BLOCKS),
}


# --- The combat replacement (#71's landing) ---------------------------------
COMBAT_BATCH = "combat-damage-breaking"
#: The recorded combat proposal, and the generator that builds it.
COMBAT_RECORDED: Path = REPL.REPLACEMENT.proposal_path(COMBAT_BATCH)
COMBAT_FILE = HERE / f"issue-5d-{COMBAT_BATCH}-{TAG}-PROPOSAL.json"
#: playing-the-game.md 1072, the whole ``### Ranged Attacks`` introduction.
RANGED_INTRO = (
    "When you make a ranged attack, you fire a bow, hurl an axe, or otherwise "
    "send projectiles to strike a foe at a distance. Many spells also involve "
    "making a ranged attack."
)
RANGED_FRAMING = ("combat", "When you make a ranged attack, you fire a bow")


def combat_edit(batch: EntryBatch) -> EntryBatch:
    """The introduction leaves framing and becomes the ``ranged`` clause and
    prose component, just before ``range``, as ``melee`` is for its section."""
    framing = tuple(f for f in batch.framing if f != RANGED_FRAMING)
    assert len(framing) == len(batch.framing) - 1
    keys = [(c[0], c[1]) for c in batch.clauses]
    i = keys.index(("combat", "range"))
    assert ("combat", "ranged") not in keys
    clauses = (
        *batch.clauses[:i],
        ("combat", "ranged", (None,), (RANGED_INTRO,)),
        *batch.clauses[i:],
    )
    j = [(c.entry, c.key) for c in batch.components].index(("combat", "range"))
    melee = next(c for c in batch.components if (c.entry, c.key) == ("combat", "melee"))
    ranged = dataclasses.replace(batch.components[j], key="ranged")
    assert dataclasses.replace(melee, key="ranged", refs=()) == ranged, ranged
    components = (*batch.components[:j], ranged, *batch.components[j:])
    return dataclasses.replace(
        batch, framing=framing, clauses=clauses, components=components
    )


def combat_rebuilt() -> tuple[bytes, bytes]:
    """The recorded combat proposal rebuilt from the release, and the edited."""
    module = REPL.REPLACEMENT.generator(COMBAT_BATCH)
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            with create_session_factory(engine)() as session:
                binding = published_release_binding(session)
                base = module.batch()
                out = tuple(
                    render(build_entry_batch(session, b, binding).proposal).encode(
                        "utf-8"
                    )
                    for b in (base, combat_edit(base))
                )
        finally:
            engine.dispose()
    return out[0], out[1]


def combat_candidate() -> MechanicalProposal:
    """The written candidate combat proposal."""
    return load_proposal(COMBAT_FILE)


def composed(combat: MechanicalProposal | None) -> AcceptedInputs:
    """The accepted chain, *combat* (if any) accepted in combat's place.

    The loop of ``ECE.composed`` at the Equipment recording's own evidence
    (as ``RA.prior`` replays it), then ``RA.recorded`` at its recorded time;
    only the combat batch's proposal and evidence are a parameter.
    """
    fr, pg, rem, ac = (
        ECE.FINITE_REFERENCE,
        ECE.PLAYING_THE_GAME,
        ECE.REMAINING,
        ECE.ANIMALS_CATALOGUE,
    )
    changed = ECE.proposals()
    finite = fr.proposals()
    playing = pg.proposals()
    base = rem.prior()
    remaining = rem.proposals()
    per, res = REPL._evidence(base)
    steps = ECE.RR._steps(base, rekeyed=True)
    inputs: AcceptedInputs | None = None

    def resolve(step: tuple[Any, ...]) -> AcceptedInputs:
        assert inputs is not None
        (ev,) = {
            (
                res[r.resolution_id].authorized_by,
                res[r.resolution_id].authorization_reference,
                res[r.resolution_id].reviewer,
                res[r.resolution_id].resolved_at,
            )
            for r in step
        }
        return resolve_references(
            inputs,
            resolutions=step,
            authorized_by=ev[0],
            authorization_reference=ev[1],
            reviewer=ev[2],
            resolved_at=ev[3],
        )

    seen = set()
    for batch, proposal in REPL._proposals():
        assert proposal.binding == base.oracle.binding, batch
        rule, who, when = per[batch]
        if batch in remaining:
            proposal = remaining[batch]
            rule, who, when = rem.APPROVAL, rem.OWNER, rem.RECORDED_AT[0]
        if batch == ac.BATCH:
            proposal = ac.candidate()
            rule, who, when = ac.APPROVAL, ac.OWNER, ac.RECORDED_AT[0]
        if batch in finite:
            proposal = finite[batch]
            rule, who, when = fr.APPROVAL, fr.OWNER, fr.RECORDED_AT
        if batch in playing:
            proposal = playing[batch]
            rule, who, when = pg.APPROVAL, pg.OWNER, pg.RECORDED_AT
        if batch in changed:
            proposal = changed[batch]
            rule, who, when = ECE.APPROVAL, ECE.OWNER, ECE.RECORDED_AT
        if batch == COMBAT_BATCH and combat is not None:
            seen.add(batch)
            proposal = combat
            rule, who, when = SIMULATED_RULE, SIMULATED_REVIEWER, SIMULATED_AT
        inputs = accept_proposal(
            proposal,
            batch_id=batch,
            rule=rule,
            resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
            resolved_review_units=tuple(
                u.unit_id for u in proposal.proposed_review_units
            ),
            reviewer=who,
            accepted_at=when,
            prior=inputs,
        )
        if steps.get(batch):
            inputs = resolve(steps[batch])
    assert seen == ({COMBAT_BATCH} if combat is not None else set()), seen
    inputs = resolve(steps["equipment-cited"])
    inputs = rem.resolved(base, inputs, rem.OWNER, rem.RECORDED_AT[1])
    inputs = ac.resolved(inputs, ac.OWNER, ac.RECORDED_AT[1])
    fm = ECE.FRAMING
    inputs = fm.composed(inputs, fm.OWNER, fm.RECORDED_AT[0])
    cc = ECE.CHARACTER_CREATION
    inputs = cc.composed(inputs, cc.OWNER, cc.RECORDED_AT[0])
    inputs = cc.resolved(inputs, cc.OWNER, cc.RECORDED_AT[1])
    return RA.recorded(inputs, RA.RECORDED_AT)  # type: ignore[no-any-return]


def drafts(inputs: AcceptedInputs) -> tuple[ReferenceResolution, ...]:
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
    for citation, (row, destinations) in DRAFTS.items():
        ref = by_citation[citation]
        out.append(
            ReferenceResolution(
                resolution_id=f"routes-{row[1:]}-{citation[0]}-{citation[1]}",
                from_record_key=citation[0],
                from_component_key=citation[1],
                source_text=citation[2],
                scope_key=citation[3],
                target_record_key="",
                release_binding=oracle.binding,
                provenance_span_ids=tuple(sorted(spans[reference_target_key(ref)])),
                destinations=destinations,
            )
        )
    return tuple(out)


def _cells(path: str, heading: str, stop: str | tuple[str, ...]) -> list[str]:
    """The tag-free, non-empty lines from ``heading`` up to ``stop``."""
    lines = (SRC / path).read_text(encoding="utf-8").splitlines()
    start = lines.index(heading)
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith(stop))
    return [
        text
        for line in lines[start + 1 : end]
        if (text := re.sub(r"<[^>]*>", "", line).strip())
    ]


def _pairs(cells: list[str], header: list[str]) -> list[tuple[str, str]]:
    """Read a two-column table: its header, then (key, value) rows."""
    i = cells.index(header[0])
    assert cells[i : i + len(header)] == header, cells[i : i + len(header)]
    body = cells[i + len(header) :]
    return list(zip(body[0::2], body[1::2], strict=True))


def _sources(inputs: AcceptedInputs) -> None:
    """Every drafted group is the source's, and every destination is stated.

    Release: the pinned SRD markdown. Each table is re-read from the source and
    compared row for row with the drafted labels and names; a creature
    destination is checked to be a creature record whose leaf key is the
    printed name.
    """
    r = inputs.oracle.representation
    kinds = {x.semantic_key: x.kind.value for x in r.records}
    comps = {(c.record_key, c.semantic_key) for c in r.components}
    for _, destinations in DRAFTS.values():
        for d in destinations:
            assert d.target_record_key in kinds, d
            if d.target_component_key:
                assert (d.target_record_key, d.target_component_key) in comps, d
            assert not (d.situation or d.class_record_key or d.minimum_class_level)

    def creature(name: str, key: str) -> None:
        assert kinds[key] == "creature", key
        assert key.rsplit(".", 1)[1] == name.lower().replace(" ", "_"), (name, key)

    # #23: one "### <Class> Spell List" per drafted class, and no other.
    classes_md = (SRC / "classes.md").read_text(encoding="utf-8")
    lists = re.findall(r"^### (\w+) Spell List$", classes_md, re.M)
    assert [c.lower() for c in lists] == [c for c, _ in SPELL_LISTS], lists
    for c, cantrips in SPELL_LISTS:
        assert ((f"classes.{c}", "cantrips") in comps) is cantrips, c
    # #38: exactly the items equipment.md says are usable as a focus, and the
    # one class feature granting an Equipment item that is not one of them.
    equipment_md = (SRC / "equipment.md").read_text(encoding="utf-8")
    foci = re.findall(
        r"^#### (.+?) \(Varies\)\n\n.*as a Spellcasting Focus", equipment_md, re.M
    )
    assert foci == ["Arcane Focus", "Druidic Focus", "Holy Symbol"], foci
    grants = set(
        re.findall(
            r"use an? ([A-Z][\w ]+?)(?: or your spellbook)? as a Spellcasting Focus",
            classes_md,
        )
    )
    assert grants == {"Musical Instrument", *foci}, grants
    assert (
        "_Spellcasting Focus._ You can use a Musical Instrument as a Spellcasting "
        "Focus for your Bard spells."
    ) in classes_md
    assert "**Musical Instrument (Varies)**" in equipment_md
    # #49
    mounts = _cells("equipment.md", "**Mounts and Other Animals**", "**")
    assert mounts[:3] == ["Item", "Carrying Capacity", "Cost"], mounts[:3]
    assert mounts[3::3] == [n for n, _ in MOUNTS], mounts
    for _name, key in MOUNTS:
        assert kinds[key] == "creature", key
    # #51: the 1d8 tables print two rolls per row; read them back into order.
    for colour, rows in BAGS.items():
        cells = _cells("magic-items.md", f"**{colour} Bag of Tricks**", ("**", "#"))
        bag = dict(_pairs(cells, ["1d8", "Creature", "1d8", "Creature"]))
        assert bag == {str(n): name for n, (name, _) in enumerate(rows, 1)}, bag
        for name, key in rows:
            creature(name, key)
    # #52
    cells = _cells("magic-items.md", "**Deck of Illusions**", "#")
    footnote = cells.pop()
    assert footnote.startswith(
        "\\*Stat blocks for these creatures (except the card drawer)"
    )
    got = _pairs(cells, ["1d100", "Illusion*"])
    assert got == [(b, n) for b, n, _ in DECK] + [CARD_DRAWER], got
    for _, name, key in DECK:
        creature(name, key)
    # #53
    cells = _cells("magic-items.md", "#### Elemental Gem", "#")
    got = _pairs(cells, ["Gem", "Summoned Elemental"])
    assert got == [(g, n) for g, n, _ in GEMS], got
    for _, name, key in GEMS:
        creature(name, key)
    # #55: four columns; band and golem are the first two.
    cells = _cells("magic-items.md", "#### Manual of Golems", "#")
    i = cells.index("1d20")
    assert cells[i : i + 4] == ["1d20", "Golem", "Time", "Cost"]
    body = cells[i + 4 :]
    assert list(zip(body[0::4], body[1::4], strict=True)) == [
        (b, n) for b, n, _ in GOLEMS
    ]
    for _, name, key in GOLEMS:
        creature(name, key)
    # #71: Ranged Attacks precedes Melee Attacks, and the combined kind is printed.
    play_md = (SRC / "playing-the-game.md").read_text(encoding="utf-8")
    assert play_md.index("### Ranged Attacks") < play_md.index("### Melee Attacks")
    assert f"### Ranged Attacks\n\n{RANGED_INTRO}\n\n#### Range\n" in play_md
    monsters_az = (SRC / "monsters-A-Z.md").read_text(encoding="utf-8")
    assert "Melee or Ranged Attack Roll" in monsters_az
    # #73: every sense any stat block prints, embedded ones included.
    printed: set[str] = set()
    entries = 0
    for name in ("monsters-A-Z.md", "animals.md", "spells.md", "magic-items.md"):
        text = (SRC / name).read_text(encoding="utf-8")
        for entry in re.findall(r"\*\*Senses\*\* ([^<\n]*)", text):
            entries += name in ("spells.md", "magic-items.md")
            for part in re.split(r"[;,]", entry):
                part = re.sub(r"\([^)]*\)", "", part)
                printed.add(re.sub(r"[\d+.]|\bft\b", "", part).strip())
    printed.discard("")
    assert entries == 6, entries
    assert entries == 6, entries
    assert printed == {
        "Passive Perception",
        *(s.capitalize() for s in SPECIAL_SENSES),
    }, printed


def resolved(inputs: AcceptedInputs) -> AcceptedInputs:
    """Resolve the accepted schema-17 artifact, as one native action."""
    return resolve_references(
        inputs,
        resolutions=drafts(inputs),
        authorized_by=SIMULATED_REVIEWER,
        authorization_reference=SIMULATED_RULE,
        reviewer=SIMULATED_REVIEWER,
        resolved_at=SIMULATED_AT,
    )


def _delta(before: AcceptedInputs, after: AcceptedInputs) -> str:
    """Every reference line that differs between the effective views."""

    def lines(inputs: AcceptedInputs) -> Counter[str]:
        o = inputs.oracle
        view = effective_representation(o.representation, o.reference_resolutions)
        return Counter(
            json.dumps(
                list(reference_target_key(r))
                + [
                    r.situation.value if r.situation else "",
                    r.class_record_key,
                    r.minimum_class_level,
                ],
                ensure_ascii=False,
            )
            for r in view.references
        )

    b, a = lines(before), lines(after)
    removed = sorted((b - a).elements())
    added = sorted((a - b).elements())
    return "".join(f"- {x}\n" for x in removed) + "".join(f"+ {x}\n" for x in added)


def _combat(item: object, units: set[str], spans: set[str]) -> bool:
    """Whether ``item`` is the combat batch's own, by its owning field."""
    assert isinstance(item, dict), item
    owner = (
        item.get("record_key")
        or item.get("source_record_key")
        or (item.get("target_key") or [None])[0]
    )
    return bool(
        item.get("batch_id") == COMBAT_BATCH
        or owner == "play.combat"
        or item.get("unit_id") in units
        or item.get("span_id") in spans
    )


def _preserved(
    before: AcceptedInputs, after: AcceptedInputs, new_ids: set[str]
) -> dict[str, tuple[int, int]]:
    """Everything accepted outside the combat batch is carried verbatim,
    evidence included; returns the (lost, added) count per changed collection.

    Every collection is compared as a multiset of canonical items. An item
    that differs must be the combat batch's own or one of ``new_ids``.
    """
    old, new = accepted_inputs_payload(before), accepted_inputs_payload(after)
    units = {
        u["unit_id"]
        for p in (old, new)
        for u in REPL._at(p, ("acceptance", "review_unit_records"))
        if u["batch_id"] == COMBAT_BATCH
    }
    spans = {
        a["span_id"]
        for p in (old, new)
        for a in REPL._at(p, ("acceptance", "records"))
        if a["batch_id"] == COMBAT_BATCH
    }
    out: dict[str, tuple[int, int]] = {}
    for path in REPL.COLLECTIONS:
        a = Counter(REPL._key(x) for x in REPL._at(old, path))
        b = Counter(REPL._key(x) for x in REPL._at(new, path))
        lost = [json.loads(k) for k in (a - b).elements()]
        added = [json.loads(k) for k in (b - a).elements()]
        for x in (*lost, *added):
            ours = x.get("resolution_id") in new_ids and x in added
            assert ours or _combat(x, units, spans), (path, REPL._key(x)[:300])
        if lost or added:
            out[".".join(path)] = (len(lost), len(added))
    assert before.policy_transitions == after.policy_transitions
    o, p = before.oracle, after.oracle
    for name in ("binding", "schema_version", "schema_hash"):
        assert getattr(o, name) == getattr(p, name), name
    olds = {r.resolution_id: r for r in o.reference_resolutions}
    news = {r.resolution_id: r for r in p.reference_resolutions}
    assert all(news.get(k) == v for k, v in olds.items()), "resolution changed"
    assert set(news) - set(olds) == new_ids, set(news) - set(olds)
    old_acc = set(before.reference_resolution_acceptances)
    assert old_acc <= set(after.reference_resolution_acceptances), "approval changed"
    return out


def _persisted_round_trip(inputs: AcceptedInputs) -> bool:
    """Build, persist on a scratch copy of the release, and reconstruct."""
    identified = identify_projection(candidate_from_accepted_inputs(inputs))
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "release.db"
        shutil.copyfile(SCRATCH_DB, db)
        engine = create_engine(f"sqlite:///{db}")
        try:
            Base.metadata.create_all(engine)
            with create_session_factory(engine)() as session:
                persist_draft(session, identified, now=SIMULATED_AT)
                session.flush()
                rebuilt = reconstruct_candidate(session, identified.projection_uuid)
                session.rollback()
        finally:
            engine.dispose()
    built = identified.candidate.representation.references
    return bool(
        rebuilt.representation.references == built
        and identify_projection(rebuilt).projection_uuid == identified.projection_uuid
    )


def load_accepted_inputs_bytes(data: bytes) -> AcceptedInputs:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "candidate.json"
        path.write_bytes(data)
        return load_accepted_inputs(path)


def main(argv: list[str]) -> None:
    if argv not in ([], ["--write"]):
        raise SystemExit("usage: [--write]")
    write = argv == ["--write"]
    print("SIMULATED (in memory; nothing accepted or recorded)")
    committed = ACCEPTED_PATH.read_bytes()
    assert _sha(committed) == ACCEPTED_SHA256, "accepted changed"
    rec = load_accepted_inputs(ACCEPTED_PATH)
    current = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    assert (rec.oracle.schema_version, rec.oracle.schema_hash) == current, current
    print("schema", current[0])

    recorded_combat, edited = combat_rebuilt()
    same = recorded_combat == COMBAT_RECORDED.read_bytes()
    print("combat: the generator rebuilds", COMBAT_RECORDED.name, same)
    assert same
    if write:
        COMBAT_FILE.write_bytes(edited)
    assert COMBAT_FILE.read_bytes() == edited, f"{COMBAT_FILE.name} is stale"
    was, combat = load_proposal(COMBAT_RECORDED), combat_candidate()
    for name, x in (("recorded", was), ("candidate", combat)):
        print(
            f"  {name} identity {proposal_identity(x)} spans",
            len(x.proposed_spans),
            "units",
            len(x.proposed_review_units),
        )
    print(" ", COMBAT_FILE.name, _sha(edited), f"{edited.count(b'\n')} lines")

    control = serialize_accepted_inputs(composed(None))
    same = _sha(control) == ACCEPTED_SHA256
    print("control: the composition without the replacement is the accepted", same)
    assert same
    base = composed(combat)
    print("  with the replacement (simulated)", _sha(serialize_accepted_inputs(base)))
    _sources(base)
    print("sources: every drafted group matches the pinned markdown")
    final = resolved(base)

    final_bytes = serialize_accepted_inputs(final)
    print("candidate (simulated)", _sha(final_bytes))
    reloaded = load_accepted_inputs_bytes(final_bytes)
    assert serialize_accepted_inputs(reloaded) == final_bytes, "reload"
    print("  reloads to the same bytes True")
    new_ids = {r.resolution_id for r in drafts(base)}
    changes = _preserved(rec, reloaded, new_ids)
    print(
        "preserved: everything outside the combat batch, and",
        len(rec.oracle.reference_resolutions),
        "resolutions with",
        len(rec.reference_resolution_acceptances),
        "approvals, verbatim; changed (lost, added):",
    )
    for collection, n in changes.items():
        print("  ", collection, n)
    print("counts", REPL._counts(rec), "->", REPL._counts(reloaded))

    replaced = APC.findings(base)
    same = Counter(replaced) == Counter(APC.findings(rec))
    print("findings unchanged by the combat replacement alone", same)
    assert same
    before, after = APC.findings(rec), APC.findings(final)
    print("findings (refs, leaves)", APC._split(before), "->", APC._split(after))
    cleared = Counter(before) - Counter(after)
    new = Counter(after) - Counter(before)
    print("  cleared", sum(cleared.values()), "new", dict(new))
    assert not new, new
    for line in sorted(after):
        print("  remains", line[:200])

    resolutions = tuple(
        r for r in final.oracle.reference_resolutions if r.resolution_id in new_ids
    )
    print(
        "resolutions",
        len(resolutions),
        "destinations",
        sum(len(r.destinations) for r in resolutions),
        "routes",
        sum(len({d.alternative_label for d in r.destinations}) for r in resolutions),
    )
    for r in resolutions:
        row = DRAFTS[
            (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        ][0]
        labels = list(dict.fromkeys(d.alternative_label for d in r.destinations))
        print(f"  {row} routes {len(labels)} destinations {len(r.destinations)}")

    o = final.oracle
    view = effective_representation(o.representation, o.reference_resolutions)
    gem = tuple(
        r
        for r in view.references
        if r.from_record_key == "magic_items.elemental_gem"
        and r.source_text == "Monsters"
    )
    kept = select_alternatives(
        gem, AlternativeSelection(class_levels={"classes.wizard": 5})
    )
    print(
        "consumer: Elemental Gem, any class selection keeps", len(kept), "of", len(gem)
    )
    assert len(kept) == len(gem) == len(GEMS)
    print("persisted round trip", _persisted_round_trip(final))

    proposal = (
        json.dumps(
            {
                "accepted_sha256": ACCEPTED_SHA256,
                "combat_replacement": {
                    "batch_id": COMBAT_BATCH,
                    "file": COMBAT_FILE.name,
                    "sha256": _sha(edited),
                    "proposal_identity": proposal_identity(combat),
                    "replaces": proposal_identity(was),
                },
                "representation_schema": list(current),
                "reference_resolutions": reference_resolution_payload(resolutions),
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    delta = (
        "# Full-text delta from the accepted artifact (evidence blanked)\n"
        + "".join(f"{x}\n" for x in REPL.Delta(rec, reloaded).report())
        + "# Effective reference lines\n"
        + _delta(rec, final)
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
