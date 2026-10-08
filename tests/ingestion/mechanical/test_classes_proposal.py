"""The ``classes`` proposals, offered for review -- CRD Issue 5d.

The whole *Classes* part, pp28-82, in two chunks proposed by
``.claude/review-notes/issue-5d-classes-generator.py`` from the release 5c
actually publishes: ``classes`` (twelve classes, their features, progression
and spell-list tables, their included subclasses) and
``class-option-catalogues`` (*Metamagic Options* and *Eldritch Invocation
Options*). The Owner accepted both, regenerated on the corrected release, with
the one resolution draft as part of the replacement chain;
``.claude/review-notes/issue-5d-monsters-corrections-ACCEPT.py`` recorded them,
regenerated on the Monsters-corrected release, in
``srd-5-2-1-corpus-3fe24ff6-4e3.json``.

What is pinned, and why:

* on the current release the catalogue generator derives the batch the
  current committed oracle accepted, and the classes generator a proposal
  that oracle does not hold (it accepts the finite-reference one); both
  committed artifacts are the superseded release's proposals, by shape; the
  one resolution draft is what the generator drafts;
* scope is 1174 of the part's 1175 leaves -- all but ``# Classes`` --; in the
  recorded proposals no leaf or record is an accepted one's;
* the batch checks report the accepted and other-chunk targets and the
  unresolved pointers, and nothing else; every spell cited is one the
  *Spells* part prints; a named item with no record of its own stays
  unresolved, never widened to the section that lists it;
* fidelity: every component reads its reviewed texts, prose-bound but each
  class's progression table, which is mixed and whose typed entitlements
  reconstruct the table; every word of every spanned leaf is claimed; every
  heading is read by its record and only subclass mottos are excluded;
* the recorded proposals, composed *in this test only* with the recorded
  chain and the draft (all the superseded release's): the draft and the
  recorded resolutions apply, both chunks accept in memory, and the
  superseded oracle, read by path, records the Owner's acceptance. Judging
  that composition against a corpus needs the superseded release's, which is
  not rebuilt; those checks are retired (see
  ``.claude/review-notes/issue-5c-release-readiness/correction-followup.md``);
* through the production rules-authority service, over one persisted draft
  of both chunks: a class, subclass, catalogue or option reads its headings,
  levels, prerequisites and costs in printed order, *Defensive Tactics* as a
  Hunter feature at level 7; a combined read orders
  the same whatever its selector order; a disabled record stays gone; a
  replaced component reads replaced in place; narrowing keeps printed order.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.models import ComponentHandling, ReviewState
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    OracleLoadError,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import persist_draft
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    identify_projection,
)
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ProgressionEntryFact,
    RecordKind,
    SpellSlotProgressionFact,
    representation_schema_hash,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.corpus import LedgerLeafORM
from afterworlds.services.rules_authority.application import AuthoredProse
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import EffectiveOverrideEntry
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)
from tests.ingestion.mechanical._replacement_chain import (
    BATCHES,
    FINITE_REFERENCE,
    REPLACEMENT,
    animals_recorded,
    character_creation_recorded,
    current,
    identity,
    kept_whole,
    proposal_path,
    through,
)
from tests.ingestion.mechanical.test_character_origins_feats_proposal import (
    _disable,
    _request,
    _service,
    _sliced,
)

REPO = Path(__file__).resolve().parents[3]
NOTES = REPO / ".claude" / "review-notes"
ORACLE = REPLACEMENT.ACCEPTED_PATH
CLASSES = "srd-5.2.1/classes"
SPELLS = "srd-5.2.1/spells"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load("classes_generator", NOTES / "issue-5d-classes-generator.py")
PROPOSAL = proposal_path("classes")
OPTIONS = proposal_path("class-option-catalogues")
DRAFTS = REPLACEMENT.drafts_path("classes")
IDENTITY = identity("classes")
OPTIONS_IDENTITY = identity("class-option-catalogues")
#: The batch the Classes chunks were composed over.
PREVIOUS = list(BATCHES)[list(BATCHES).index("classes") - 1]


@pytest.fixture(scope="module")
def session(source_release_db: Path):  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{source_release_db}")
    with create_session_factory(engine)() as s:
        yield s
    engine.dispose()


@pytest.fixture(scope="module")
def built(session):  # type: ignore[no-untyped-def]
    return GEN.build(session)


@pytest.fixture(scope="module")
def options(session):  # type: ignore[no-untyped-def]
    return GEN.build_options(session)


@pytest.fixture(scope="module")
def prior() -> AcceptedInputs:
    """The recorded chain through the batch before Classes, rebuilt natively.

    It is bound to the superseded release, so it composes only with the
    recorded proposals.
    """
    assert PREVIOUS == "rules-glossary-completion"
    return through(PREVIOUS)


@pytest.fixture(scope="module")
def recorded() -> tuple[MechanicalProposal, MechanicalProposal]:
    """The committed proposals: the superseded release's, as the Owner accepted them."""
    return (
        load_proposal(PROPOSAL, expected_identity=IDENTITY),
        load_proposal(OPTIONS, expected_identity=OPTIONS_IDENTITY),
    )


def _texts(b: Built, record: str, key: str) -> list[str]:
    """The source texts one component's prose bindings are read from."""
    spans = {s.span_id: s for s in b.ledger.spans}
    return [
        b.leaf_rows[spans[x.span_id].leaf_id].content[
            spans[x.span_id].char_start : spans[x.span_id].char_end
        ]
        for x in b.proposal.proposed_representation.prose_bindings
        if (x.record_key, x.component_key) == (record, key)
    ]


def _refs(*bs: Built) -> list[tuple[str, str, str, str, str]]:
    return [
        (
            r.from_record_key,
            r.from_component_key,
            r.source_text,
            r.scope_key,
            r.target_record_key,
        )
        for b in bs
        for r in b.proposal.proposed_representation.references
    ]


# ---------------------------------------------------------------------------
# The artifacts
# ---------------------------------------------------------------------------


def test_the_current_release_derives_the_catalogues_its_oracle_accepted(  # type: ignore[no-untyped-def]
    built, options
) -> None:
    batches = {b.batch_id: b.proposal_identity for b in current().batches}
    assert proposal_identity(options.proposal) == batches["class-option-catalogues"]
    # The current oracle accepts the finite-reference Classes proposal instead.
    assert proposal_identity(built.proposal) not in batches.values()
    assert OPTIONS_IDENTITY not in batches.values()


@pytest.mark.parametrize(
    ("path", "identity"), [(PROPOSAL, IDENTITY), (OPTIONS, OPTIONS_IDENTITY)]
)
def test_the_committed_artifacts_are_the_superseded_release_s_proposals(
    path: Path, identity: str
) -> None:
    assert b"\r" not in path.read_bytes()
    proposal = load_proposal(path, expected_identity=identity)
    assert json.loads(path.read_text("utf-8"))["artifact_kind"] == "machine_proposal"
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(path)


def test_the_draft_is_the_generator_s_and_names_the_wizard(prior) -> None:  # type: ignore[no-untyped-def]
    drafts = GEN.draft_resolutions(prior.oracle.binding)
    assert json.loads(DRAFTS.read_text("utf-8")) == reference_resolution_payload(drafts)
    assert (
        hashlib.sha256(DRAFTS.read_bytes()).hexdigest()
        == REPLACEMENT.DRAFTS["classes"][0]
    )
    assert b"\r" not in DRAFTS.read_bytes()
    ((record, component, text, target),) = [
        (d.from_record_key, d.from_component_key, d.source_text, d.target_record_key)
        for d in drafts
    ]
    assert (record, component, text, target) == (
        "character_origins.elf",
        "elven_lineage",
        "Wizard spell list",
        "classes.wizard",
    )
    assert (
        drafts[0].resolution_id
        == "resolve-character-origins-elf-elven-lineage-wizard-spell-list-classes-1"
    )


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


def _classes_leaves(session, built) -> list[LedgerLeafORM]:  # type: ignore[no-untyped-def]
    """The part's leaves in printed order: ``# Classes`` to the last Wizard leaf."""
    rows = (
        session.query(LedgerLeafORM)
        .filter(LedgerLeafORM.package_uuid == built.binding.package_uuid)
        .order_by(LedgerLeafORM.occurrence_index)
        .all()
    )
    (start,) = [i for i, r in enumerate(rows) if r.content == "# Classes"]
    return rows[start : start + 1175]


def test_scope_is_1174_of_the_part_s_1175_leaves(  # type: ignore[no-untyped-def]
    session, built, options
) -> None:
    part = _classes_leaves(session, built)
    assert [r.content for r in part[:2]] == ["# Classes", "## Barbarian"]
    assert part[-1].content == GEN.LEAVES[-1][1]
    assert [r.content for r in part[1:]] == [t for _, t in GEN.LEAVES]
    mine = [
        leaf
        for b in (built, options)
        for u in b.proposal.proposed_review_units
        for leaf in u.leaf_ids
    ]
    assert len(mine) == len(set(mine)) == 1174
    assert set(mine) == {r.leaf_id for r in part[1:]}
    keys = [
        r.semantic_key
        for b in (built, options)
        for r in b.proposal.proposed_representation.records
    ]
    assert len(keys) == len(set(keys))


def test_no_recorded_leaf_or_record_is_an_accepted_one(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    # Both sides are the superseded release's: the recorded chain and proposals.
    mine = [
        leaf for x in recorded for u in x.proposed_review_units for leaf in u.leaf_ids
    ]
    assert len(mine) == len(set(mine)) == 1174
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    assert not owned & set(mine)
    accepted = {r.semantic_key for r in prior.oracle.representation.records}
    keys = [r.semantic_key for x in recorded for r in x.proposed_representation.records]
    assert len(keys) == len(set(keys)) and not accepted & set(keys)


def test_the_records_are_classes_features_and_subclasses(built, options) -> None:  # type: ignore[no-untyped-def]
    records = built.proposal.proposed_representation.records
    kinds = Counter(r.kind for r in records)
    assert kinds == {
        RecordKind.CLASS: 12,
        RecordKind.CHARACTER_ADVANCEMENT: 12,
        RecordKind.CLASS_FEATURE: 244,
    }
    assert [r.semantic_key for r in records if r.kind is RecordKind.CLASS] == [
        GEN.cls_key(c) for c in GEN.CLASS_NAMES
    ]
    subclasses = [
        p.record_key
        for p in GEN.CLASSES_CHUNK.placements.values()
        if p.heading.startswith("### ")
    ]
    assert len(subclasses) == 12
    # One unit per class, multiclass entry and subclass: Defensive Tactics
    # is read inside the Hunter unit that prints it, not as a unit of its own.
    assert len(built.proposal.proposed_review_units) == 36
    assert "classes/defensive_tactics" not in {
        u.unit_id for u in built.proposal.proposed_review_units
    }
    option_records = options.proposal.proposed_representation.records
    assert Counter(r.kind for r in option_records) == {RecordKind.CLASS_FEATURE: 40}
    assert len(options.proposal.proposed_review_units) == 40


# ---------------------------------------------------------------------------
# Batch checks and references
# ---------------------------------------------------------------------------


#: Each named item the accepted *Equipment* has no record of, once per class
#: that names it, and the two printed "(see Equipment)" part pointers.
EQUIPMENT_UNRESOLVED = {
    "Burglar's Pack": 1,
    "Dungeoneer's Pack": 2,
    "Entertainer's Pack": 1,
    "Explorer's Pack": 4,
    "Priest's Pack": 2,
    "Scholar's Pack": 2,
    "Chain Mail": 2,
    "Chain Shirt": 1,
    "Equipment": 2,
    "Flail": 1,
    "Greataxe": 1,
    "Greatsword": 1,
    "Handaxes": 1,
    "Javelins": 2,
    "Leather Armor": 4,
    "Longbow": 2,
    "Longsword": 1,
    "Mace": 1,
    "Musical Instrument": 2,
    "Musical Instruments": 1,
    "Scimitar": 2,
    "Shortsword": 3,
    "Sickle": 2,
    "Spellbook": 1,
    "Studded Leather Armor": 2,
}
NON_SPELL_UNRESOLVED = sorted(
    [
        "reference srd-5.2.1/animals:'Animals': unresolved reference",
        *(
            f"reference srd-5.2.1/animals:{n!r}: unresolved reference"
            for n in ("Rat", "Riding Horse", "Spider", "Wolf")
        ),
        'reference srd-5.2.1/classes:"any class\'s spell list": unresolved reference',
        "reference srd-5.2.1/classes:'Bard, Cleric, Druid, and Wizard spell lists': "
        "unresolved reference",
        "reference srd-5.2.1/classes:'Cleric, Druid, or Wizard spell list': "
        "unresolved reference",
        *["reference srd-5.2.1/monsters:'Monsters': unresolved reference"] * 2,
        *(
            f"reference srd-5.2.1/equipment:{n!r}: unresolved reference"
            for n, count in EQUIPMENT_UNRESOLVED.items()
            for _ in range(count)
        ),
        "reference srd-5.2.1/playing-the-game:'Playing the Game': unresolved reference",
        *(
            f"reference srd-5.2.1/monsters:{n!r}: unresolved reference"
            for n in (
                "Imp",
                "Pseudodragon",
                "Quasit",
                "Skeleton",
                "Sphinx of Wonder",
                "Sprite",
                "Venomous Snake",
            )
        ),
    ]
)


def test_the_batch_checks_report_only_the_out_of_batch_targets(built, options) -> None:  # type: ignore[no-untyped-def]
    found = [GEN.batch_findings(b) for b in (built, options)]
    for f in found:
        assert f["partition"] == [] and f["review_units"] == []
    assert found[0]["representation"] == GEN.expected_representation_findings(
        GEN.CLASSES_CHUNK
    )
    assert found[1]["representation"] == GEN.expected_representation_findings(
        GEN.OPTIONS_CHUNK
    )
    unresolved = sorted(
        f
        for x in found
        for f in x["representation"]
        if "unresolved" in f and not f.startswith(f"reference {SPELLS}:")
    )
    assert unresolved == NON_SPELL_UNRESOLVED


def _printed_spells(session, built) -> set[str]:  # type: ignore[no-untyped-def]
    """Each spell *Spells* describes: a heading followed by its level line."""
    rows = [
        r.content
        for r in session.query(LedgerLeafORM)
        .filter(LedgerLeafORM.package_uuid == built.binding.package_uuid)
        .order_by(LedgerLeafORM.occurrence_index)
    ]
    return {
        m[1]
        for a, b in zip(rows, rows[1:], strict=False)
        if (m := re.fullmatch(r"#### (.+)", a))
        and re.match(r"_(Level \d|\w+ Cantrip)", b)
    }


def test_every_spell_cited_is_described_in_spells(session, built, options) -> None:  # type: ignore[no-untyped-def]
    printed = _printed_spells(session, built)
    assert len(printed) == 339
    cited = {r[2] for r in _refs(built, options) if r[3] == SPELLS}
    # Every spell is cited: with the Owner's class-table correction, Phantasmal
    # Force (on no printed class table) is on the Bard, Sorcerer and Wizard ones.
    assert cited - printed == {"Spells"}
    assert cited & printed == printed
    assert "Phantasmal Force" in cited
    # Every spell pointer stays unresolved: there are no spell records yet.
    assert {r[4] for r in _refs(built, options) if r[3] == SPELLS} == {""}
    # The italic spells prose names are exactly the qualified set.
    assert GEN.SEEN_SPELLS == GEN.SPELL_NAMES and len(GEN.SPELL_NAMES) == 58


def test_pointers_name_the_records_printed(built, options) -> None:  # type: ignore[no-untyped-def]
    refs = _refs(built, options)
    for ref in (
        ("classes.sorcerer.metamagic", "metamagic", "Metamagic Options", CLASSES,
         "classes.sorcerer.metamagic_options"),
        ("classes.warlock.eldritch_invocations", "eldritch_invocations",
         "Eldritch Invocation Options", CLASSES,
         "classes.warlock.eldritch_invocation_options"),
        ("classes.warlock.pact_magic", "pact_magic", "Warlock spell list", CLASSES,
         "classes.warlock"),
        ("classes.paladin.fighting_style", "blessed_warrior", "Cleric class's section",
         CLASSES, "classes.cleric"),
        ("classes.wizard.wizard_subclass", "wizard_subclass", "Evoker", CLASSES,
         "classes.wizard.evoker"),
        ("classes.fighter.fighting_style", "fighting_style", "Defense",
         "srd-5.2.1/feats", "feats.defense"),
        ("classes.barbarian.epic_boon", "epic_boon", "Boon of Irresistible Offense",
         "srd-5.2.1/feats", "feats.boon_of_irresistible_offense"),
        ("classes.wizard.wizard_subclass", "expanding_and_replacing_a_spellbook",
         "Spell Scroll", "srd-5.2.1/equipment",
         "equipment.adventuring_gear.spell_scroll"),
        ("classes.warlock.eldritch_invocation_options.thirsting_blade",
         "thirsting_blade", "Pact of the Blade", CLASSES,
         "classes.warlock.eldritch_invocation_options.pact_of_the_blade"),
    ):  # fmt: skip
        assert ref in refs, ref
    # Every subclass named "detailed after" its class is the record that follows.
    detailed = [r for r in refs if r[0].endswith("_subclass") and r[3] == CLASSES]
    assert len(detailed) == 12
    # A glossary term is never cited from a table, a heading or a spell name.
    assert not [r for r in refs if r[0] == r[4]]
    assert "Proficiency Bonus" not in {r[2] for r in refs}


def test_a_named_target_is_exact_or_unresolved(built) -> None:  # type: ignore[no-untyped-def]
    refs = _refs(built)
    # Never widened to the section that lists a named item.
    assert not {r[4] for r in refs} & {
        "equipment.armor",
        "equipment.weapons",
        "equipment.adventuring_gear",
        "equipment.tools",
    }
    core = [r for r in refs if r[1] == "core_traits"]
    # "Starting Equipment" is a row label; only a printed "(see Equipment)" points.
    assert sorted(r[0] for r in core if r[2] == "Equipment") == [
        "classes.bard",
        "classes.monk",
    ]
    assert {r[4] for r in core if r[2] == "Equipment"} == {""}
    assert ("classes.bard", "core_traits", "Playing the Game",
            "srd-5.2.1/playing-the-game", "") in refs  # fmt: skip
    # An item or category with a record of its own keeps it.
    for ref in (
        ("classes.wizard", "core_traits", "Quarterstaff", "srd-5.2.1/equipment",
         "equipment.weapons.quarterstaff"),
        ("classes.rogue", "core_traits", "Thieves' Tools", "srd-5.2.1/equipment",
         "equipment.tools.thieves_tools"),
        ("classes.barbarian", "core_traits", "Simple", "srd-5.2.1/equipment",
         "equipment.weapons.category"),
    ):  # fmt: skip
        assert ref in refs, ref
    assert [r[4] for r in core if r[0] == "classes.barbarian" and "armor" in r[2]] == [
        "equipment.armor.category"
    ]
    # A label's markup is not a name: "Temporary Hit Points" is not "Hit Points".
    wild = [
        r[4]
        for r in refs
        if r[:2] == ("classes.druid.wild_shape", "temporary_hit_points")
        and r[3] == "srd-5.2.1/rules-glossary"
    ]
    assert wild == ["glossary.temporary_hit_points"]


# ---------------------------------------------------------------------------
# Fidelity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["built", "options"])
def test_every_component_reads_its_reviewed_texts(request, name) -> None:  # type: ignore[no-untyped-def]
    b = request.getfixturevalue(name)
    chunk = GEN.CLASSES_CHUNK if name == "built" else GEN.OPTIONS_CHUNK
    components = b.proposal.proposed_representation.components
    mixed = [c for c in components if c.handling is ComponentHandling.MIXED]
    assert [c for c in components if c.all_facts()] == mixed
    assert {c.handling for c in components} - {ComponentHandling.MIXED} == {
        ComponentHandling.PROSE_BOUND
    }
    assert [(c.record_key, c.semantic_key) for c in mixed] == (
        [(GEN.cls_key(c), "progression") for c in GEN.CLASS_NAMES]
        if name == "built"
        else []
    )
    clauses = {(e, k): texts for e, k, _, texts in chunk.clauses}
    for c in chunk.components:
        record = c.record or chunk.placements[c.entry].record_key
        texts = c.texts or clauses[(c.entry, c.key)]
        assert _texts(b, record, c.key) == list(texts), (record, c.key)


def _facts(built, cls: str):  # type: ignore[no-untyped-def]
    (c,) = [
        c
        for c in built.proposal.proposed_representation.components
        if (c.record_key, c.semantic_key) == (GEN.cls_key(cls), "progression")
    ]
    assert _texts(built, c.record_key, "progression")[0].startswith(
        f"**{cls} Features**"
    )
    return c.facts


def test_a_progression_table_reconstructs_from_its_facts(built) -> None:  # type: ignore[no-untyped-def]
    """Canary 5: level-indexed entitlements and feature references."""
    records = {r.semantic_key for r in built.proposal.proposed_representation.records}
    features = {}
    for cls in GEN.CLASS_NAMES:
        granted = [
            f
            for f in _facts(built, cls)
            if isinstance(f, ProgressionEntryFact) and "." in f.entitlement_key
        ]
        # Every feature the table names is a record of that class.
        assert {f.entitlement_key for f in granted} <= records
        assert all(f.entitlement_key.startswith(GEN.cls_key(cls)) for f in granted)
        features[cls] = {
            lvl: [f.entitlement_key for f in granted if f.level == lvl]
            for lvl in range(1, 21)
        }
    host = "classes.barbarian"
    assert features["Barbarian"][1] == [
        f"{host}.rage",
        f"{host}.unarmored_defense",
        f"{host}.weapon_mastery",
    ]
    # A repeated feature is the latest printed record at or below its level.
    assert features["Barbarian"][8] == [f"{host}.ability_score_improvement"]
    assert features["Barbarian"][13] == [f"{host}.improved_brutal_strike_13"]
    assert features["Barbarian"][17] == [f"{host}.improved_brutal_strike_17"]
    assert features["Ranger"][14][-1] == "classes.ranger.natures_veil"
    fighter = _facts(built, "Fighter")
    assert ProgressionEntryFact(17, "classes.fighter.action_surge", 2) in fighter
    assert ProgressionEntryFact(13, "classes.fighter.indomitable", 2) in fighter
    # Counts by level; a dash states no fact.
    barbarian = _facts(built, "Barbarian")
    rages = {f.level: f.quantity for f in barbarian if f.entitlement_key == "rages"}
    assert (rages[1], rages[3], rages[20]) == (2, 3, 6)
    cleric = _facts(built, "Cleric")
    assert 1 not in {
        f.level
        for f in cleric
        if getattr(f, "entitlement_key", "") == "channel_divinity"
    }
    # The spell-slot grid, both indices typed.
    wizard = {
        (f.character_level, f.slot_level): f.slots
        for f in _facts(built, "Wizard")
        if isinstance(f, SpellSlotProgressionFact)
    }
    assert wizard[(1, 1)] == 2 and wizard[(20, 9)] == 1 and (1, 2) not in wizard
    assert len(wizard) == 108
    warlock = [
        f for f in _facts(built, "Warlock") if isinstance(f, SpellSlotProgressionFact)
    ]
    assert SpellSlotProgressionFact(1, 1, 1) in warlock
    assert SpellSlotProgressionFact(20, 5, 4) in warlock and len(warlock) == 20
    # Proficiency Bonus is the accepted play.proficiency bands: never restated.
    assert not [
        f
        for cls in GEN.CLASS_NAMES
        for f in _facts(built, cls)
        if getattr(f, "entitlement_key", "") == "proficiency_bonus"
    ]


def test_latitude_is_only_where_the_rule_leaves_it_to_the_gm(built, options) -> None:  # type: ignore[no-untyped-def]
    latitude = sorted(
        (c.record_key, c.semantic_key)
        for b in (built, options)
        for c in b.proposal.proposed_representation.components
        if (c.irreducibility_reason_code or c.prose_retention_reason_code)
        == "gamemaster_latitude"
    )
    assert latitude == [
        ("classes.druid.wild_shape", "known_forms"),
        ("classes.druid.wild_shape", "objects"),
        ("classes.paladin.channel_divinity", "breaking_your_oath"),
    ]
    # The release appends Channel Divinity's DC sentence (p55) to the sidebar
    # (p54); it reads as the feature's own rule, not under GM latitude.
    oath = _texts(built, "classes.paladin.channel_divinity", "breaking_your_oath")
    body = _texts(built, "classes.paladin.channel_divinity", "channel_divinity")
    assert body[-1] == GEN.OATH_DC and GEN.OATH_DC not in oath[-1]
    assert oath[-1].endswith("abandon the class and adopt another one.")


def _residue(b: Built) -> dict[str, str]:
    """Text of a spanned leaf no span covers, blockquote markers aside."""
    out = {}
    for lid in {s.leaf_id for s in b.ledger.spans}:
        text = list(b.leaf_rows[lid].content)
        for s in b.ledger.spans:
            if s.leaf_id == lid:
                text[s.char_start : s.char_end] = " " * (s.char_end - s.char_start)
        if left := "".join(text).replace(">", "").strip():
            out[lid] = left
    return out


@pytest.mark.parametrize("name", ["built", "options"])
def test_every_spanned_leaf_is_claimed_and_only_mottos_excluded(  # type: ignore[no-untyped-def]
    request, name
) -> None:
    b = request.getfixturevalue(name)
    chunk = GEN.CLASSES_CHUNK if name == "built" else GEN.OPTIONS_CHUNK
    assert _residue(b) == {}
    excluded = [
        b.leaf_rows[leaf].content
        for u in b.proposal.proposed_review_units
        for g in u.excluded_groups
        for leaf in g.leaf_ids
    ]
    assert all(m.startswith("_") and m.endswith("_") for m in excluded)
    assert len(excluded) == (12 if name == "built" else 0)
    # Every placement heading -- class, subclass, multiclass, catalogue,
    # option -- is read by its own record, first.
    for placement in chunk.placements.values():
        record = placement.record_key
        assert _texts(b, record, _first_key(chunk, record))[0] == placement.heading


def _first_key(chunk, record: str) -> str:  # type: ignore[no-untyped-def]
    return next(
        str(c.key)
        for c in chunk.components
        if (c.record or chunk.placements[c.entry].record_key) == record
    )


def test_a_dropped_feature_component_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    chunk = GEN.CLASSES_CHUNK
    monkeypatch.setattr(
        chunk,
        "components",
        [
            c
            for c in chunk.components
            if (c.record, c.key) != ("classes.barbarian.rage", "rage_damage")
        ],
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found and all(f.startswith("review unit classes/barbarian: ") for f in found)


# ---------------------------------------------------------------------------
# Test-only composition with the committed oracle
# ---------------------------------------------------------------------------


def _composed(  # type: ignore[no-untyped-def]
    prior: AcceptedInputs, *xs: MechanicalProposal, drafts=()
) -> AcceptedInputs:
    oracle, accepted = prior.oracle, prior.oracle.representation
    return dataclasses.replace(
        prior,
        oracle=dataclasses.replace(
            oracle,
            spans=(*oracle.spans, *(p.span for x in xs for p in x.proposed_spans)),
            review_units=(
                *oracle.review_units,
                *(u for x in xs for u in x.proposed_review_units),
            ),
            representation=dataclasses.replace(
                accepted,
                **{
                    f.name: (
                        *getattr(accepted, f.name),
                        *(
                            y
                            for x in xs
                            for y in getattr(x.proposed_representation, f.name)
                        ),
                    )
                    for f in dataclasses.fields(accepted)
                },
            ),
            reference_resolutions=(*oracle.reference_resolutions, *drafts),
        ),
    )


def test_composed_the_draft_and_the_recorded_resolutions_apply(  # type: ignore[no-untyped-def]
    recorded, prior
) -> None:
    assert (len(prior.batches), len(prior.oracle.representation.records)) == (15, 295)
    assert len(prior.oracle.reference_resolutions) == 50
    drafts = GEN.draft_resolutions(prior.oracle.binding)
    composed = _composed(prior, *recorded, drafts=drafts)
    assert (
        reference_resolution_violations(
            composed.oracle.representation,
            composed.oracle.reference_resolutions,
            composed.oracle.binding,
        )
        == []
    )


def test_both_chunks_accept_through_the_native_seam_in_memory_only(  # type: ignore[no-untyped-def]
    recorded, prior
) -> None:
    oracles = REPO / "src/afterworlds/ingestion/mechanical/oracles"
    on_disk = {p.name: p.read_bytes() for p in oracles.glob("*.json")}
    before = serialize_accepted_inputs(prior)
    state = prior
    for batch_id, proposal in zip(
        ("classes", "class-option-catalogues"), recorded, strict=True
    ):
        state = accept_proposal(
            proposal,
            batch_id=batch_id,
            rule="test-only",
            resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
            resolved_review_units=tuple(
                u.unit_id for u in proposal.proposed_review_units
            ),
            reviewer="test",
            accepted_at="2026-09-26T00:00:00Z",
            prior=state,
        )
    assert [b.batch_id for b in state.batches][-2:] == [
        "classes",
        "class-option-catalogues",
    ]
    assert len(state.oracle.representation.records) == 295 + 268 + 40
    assert state.oracle.reference_resolutions == prior.oracle.reference_resolutions
    assert {p.name: p.read_bytes() for p in oracles.glob("*.json")} == on_disk
    assert serialize_accepted_inputs(prior) == before


def test_the_committed_oracle_records_the_owner_acceptance(prior) -> None:  # type: ignore[no-untyped-def]
    # The superseded release's committed oracle, read by path: the production
    # resolver refuses its binding.
    committed = load_accepted_inputs(ORACLE)
    # The recorded chain after both chunks and the draft is the first
    # seventeen batches of the recording, kept whole by the Animals recording
    # (which the committed file keeps outside the replaced Equipment batch),
    # under the Owner's one decision and time.
    chain = through("class-option-catalogues")
    assert [b.batch_id for b in chain.batches] == list(BATCHES)[:17]
    assert not kept_whole(chain, through())
    assert not kept_whole(chain, animals_recorded())
    drafts = GEN.draft_resolutions(prior.oracle.binding)
    # The committed file now holds the Owner-accepted finite-reference
    # Classes proposal; the Character Creation catalogue recording, which it
    # keeps outside the five replaced batches, holds this acceptance.
    (batch,) = [b for b in committed.batches if b.batch_id == "classes"]
    assert (batch.proposal_identity, batch.rule) == (
        FINITE_REFERENCE.PROPOSALS["classes"][0],
        FINITE_REFERENCE.APPROVAL,
    )
    recorded = character_creation_recorded()
    for batch_id, expected in (
        ("classes", IDENTITY),
        ("class-option-catalogues", OPTIONS_IDENTITY),
    ):
        (batch,) = [b for b in recorded.batches if b.batch_id == batch_id]
        assert (batch.proposal_identity, batch.rule) == (
            expected,
            REPLACEMENT.APPROVAL,
        )
        mine = [a for a in recorded.acceptances if a.batch_id == batch_id]
        assert set(batch.resolved_scope) == {a.span_id for a in mine}
        assert {(a.reviewer, a.accepted_at) for a in mine} == {
            (REPLACEMENT.OWNER, REPLACEMENT.ACCEPTED_AT)
        }
    old = {r.resolution_id for r in prior.oracle.reference_resolutions}
    (new,) = [
        r for r in chain.oracle.reference_resolutions if r.resolution_id not in old
    ]
    assert (
        new.resolution_id,
        new.from_record_key,
        new.from_component_key,
        new.target_record_key,
    ) == (
        drafts[0].resolution_id,
        "character_origins.elf",
        "elven_lineage",
        "classes.wizard",
    )
    (auth,) = [
        a
        for a in committed.reference_resolution_acceptances
        if a.resolution_id == new.resolution_id
    ]
    assert (auth.authorized_by, auth.reviewer, auth.resolved_at) == (
        REPLACEMENT.OWNER,
        REPLACEMENT.OWNER,
        REPLACEMENT.ACCEPTED_AT,
    )
    assert auth.authorization_reference == REPLACEMENT.AUTHORIZATION_REFERENCE
    final = chain.oracle
    assert (
        len(chain.batches),
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (17, 603, 2776, 305, 51)
    assert set(prior.oracle.reference_resolutions) < set(final.reference_resolutions)
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )


# ---------------------------------------------------------------------------
# Through the production rules-authority service, both chunks as one draft
# ---------------------------------------------------------------------------


def _merge(a, b):  # type: ignore[no-untyped-def]
    """Two frozen records field by field: tuples join, anything else is *a*'s."""
    return dataclasses.replace(
        a,
        **{
            f.name: (*getattr(a, f.name), *getattr(b, f.name))
            for f in dataclasses.fields(a)
            if isinstance(getattr(a, f.name), tuple)
        },
    )


def _candidate(built, options) -> ProjectionCandidate:  # type: ignore[no-untyped-def]
    return ProjectionCandidate(
        binding=built.binding,
        classification=_merge(built.ledger, options.ledger),
        representation=_merge(
            built.proposal.proposed_representation,
            options.proposal.proposed_representation,
        ),
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
    )


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db, built, options):  # type: ignore[no-untyped-def]
    """Both chunks persisted as one draft into a private copy of the release."""
    path = tmp_path_factory.mktemp("classes") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(_candidate(built, options))
        persist_draft(s, identified, now="2026-09-26T00:00:00Z")
        s.commit()
        yield s, identified.projection_uuid
    engine.dispose()


def _view(service, built, *records: str, components=()):  # type: ignore[no-untyped-def]
    view = service.gamemaster_view(_request(built, *records, components=components))
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    return view.gamemaster_view.components


def _read(view) -> list[tuple[str, str, str]]:  # type: ignore[no-untyped-def]
    """(record, component, text) of every passage, in the order the view reads."""
    return [
        (c.record_key, c.component_key, e.text) for c in view for e in c.governing_prose
    ]


def _members(host: str) -> list[str]:
    chunk = (
        GEN.CLASSES_CHUNK
        if host.count(".") < 2 or "hunter" in host
        else GEN.OPTIONS_CHUNK
    )
    entries = {v.record_key: k for k, v in chunk.placements.items()}
    host_entry = entries.get(host)
    return [k for k, _, e in chunk.records if e == host_entry] + [
        chunk.placements[m].record_key for m, s in chunk.members if s == host_entry
    ]


def test_a_class_reads_features_and_members(persisted, built, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _service(persisted, built, monkeypatch)
    reached = _sliced(service, _request(built, "classes.barbarian"))
    assert reached[0] == "classes.barbarian"
    assert set(reached[1:]) == set(_members("classes.barbarian"))
    read = _read(_view(service, built, "classes.barbarian"))
    texts = [t for _, _, t in read]
    # The class's name, core traits, level 1, progression, then each feature
    # under its own heading.
    assert texts[0] == "## Barbarian"
    assert texts[1].startswith("**Core Barbarian Traits**")
    assert texts.index("#### Level 1: Rage") < texts.index("#### Level 2: Danger Sense")
    for level in (13, 17):
        (text,) = [
            t
            for r, _, t in read
            if r == f"classes.barbarian.improved_brutal_strike_{level}"
            and t.startswith("####")
        ]
        assert text == f"#### Level {level}: Improved Brutal Strike"
    # The multiclass rules read their own bullets, not the level 1 ones twice.
    multiclass = [t for r, _, t in read if r.endswith("as_a_multiclass_character")]
    assert multiclass[0] == "#### As a Multiclass Character"
    assert len(multiclass) == 2 and multiclass[1].startswith("• Gain the following")


def test_a_subclass_and_defensive_tactics_read_in_printed_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    hunter = "classes.ranger.hunter"
    dt = f"{hunter}.defensive_tactics"
    read = _read(_view(service, built, hunter))
    assert read[0] == (hunter, "hunter", "### Ranger Subclass: Hunter")
    headings = [t for _, _, t in read if t.startswith("####")]
    assert headings == [
        "#### Level 3: Hunter's Lore",
        "#### Level 3: Hunter's Prey",
        "#### Level 7: Defensive Tactics",
        "#### Level 11: Superior Hunter's Prey",
        "#### Level 15: Superior Hunter's Defense",
    ]
    # One feature, one record: a Hunter member read under its level heading,
    # the leaf it prints like Hunter's Prey read by each where it is printed.
    assert dt in _sliced(service, _request(built, hunter))
    own = [t for _, _, t in _read(_view(service, built, dt))]
    assert own[0] == "#### Level 7: Defensive Tactics"
    assert own[1].startswith("You gain one of the following feature options")
    assert [t for r, _, t in read if r == dt] == own
    # One hop: the class reaches the subclass, the subclass its features.
    assert dt not in _sliced(service, _request(built, "classes.ranger"))
    # Selecting the subclass with its feature reads the feature once.
    assert _read(_view(service, built, hunter, dt)) == read


def test_a_disabled_subclass_is_not_read_back_by_its_class(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    hunter = "classes.ranger.hunter"
    service = _service(persisted, built, monkeypatch)
    ranger = _read(_view(service, built, "classes.ranger"))
    # The class reads the subclass under its own heading, once, selected or not.
    assert [t for _, _, t in ranger].count("### Ranger Subclass: Hunter") == 1
    # Selecting it too reaches its features, one hop from it, each read once.
    both = _read(_view(service, built, "classes.ranger", hunter))
    assert len(both) == len(set(both))
    assert [t for _, _, t in both].count("### Ranger Subclass: Hunter") == 1
    assert set(ranger) <= set(both)
    assert "#### Level 7: Defensive Tactics" in {t for _, _, t in both}
    service = _service(persisted, built, monkeypatch, _disable(hunter))
    read = _read(_view(service, built, "classes.ranger"))
    assert hunter not in {r for r, _, _ in read}
    assert "### Ranger Subclass: Hunter" not in {t for _, _, t in read}


def test_a_catalogue_reads_its_options_with_costs_and_prerequisites(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    catalogue = "classes.warlock.eldritch_invocation_options"
    reached = _sliced(service, _request(built, catalogue))
    options = [
        GEN.OPTIONS_CHUNK.placements[m].record_key
        for m, s in GEN.OPTIONS_CHUNK.members
        if s == "eldritch_invocation_options"
    ]
    assert reached == [catalogue, *options]
    read = _read(
        _view(
            service,
            built,
            "classes.warlock.eldritch_invocation_options.thirsting_blade",
        )
    )
    assert read[0][2] == "#### Thirsting Blade"
    assert read[1][2].startswith("_Prerequisite: Level 5+ Warlock, Pact of the Blade")
    meta = _read(
        _view(service, built, "classes.sorcerer.metamagic_options.careful_spell")
    )
    assert [t for _, _, t in meta][:2] == [
        "#### Careful Spell",
        "_Cost: 1 Sorcery Point_",
    ]
    # The catalogue reads its own heading and each option's, once each.
    whole = [t for _, _, t in _read(_view(service, built, catalogue))]
    assert whole[0] == "### Eldritch Invocation Options"
    option_headings = [t for t in whole if t.startswith("#### ")]
    assert len(option_headings) == len(set(option_headings)) == len(options)
    # A class reaches its catalogue by pointer, not as a member.
    assert catalogue not in _sliced(service, _request(built, "classes.warlock"))


def test_a_combined_read_orders_the_same_whatever_its_selector_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    records = (
        "classes.sorcerer.metamagic_options",
        "classes.wizard",
        "classes.cleric.life_domain",
    )
    orders = [
        _read(_view(service, built, *o)) for o in (records, tuple(reversed(records)))
    ]
    assert orders[0] == orders[1]


def test_narrowing_keeps_printed_order(persisted, built, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _service(persisted, built, monkeypatch)
    record = "classes.warlock.pact_magic"
    printed = [c.key for c in GEN.CLASSES_CHUNK.components if c.record == record]
    wanted = tuple(reversed(printed[1:4]))
    view = _view(service, built, components=tuple((record, k) for k in wanted))
    assert [c.component_key for c in view] == [k for k in printed if k in wanted]


def test_a_disabled_record_stays_gone(persisted, built, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _service(
        persisted, built, monkeypatch, _disable("classes.barbarian.rage")
    )
    reached = _sliced(service, _request(built, "classes.barbarian"))
    assert "classes.barbarian.rage" not in reached
    refused = service.rule_slice(_request(built, "classes.barbarian.rage"))
    assert refused.outcome is AuthorityOutcome.INVALID_REFERENCE
    service = _service(persisted, built, monkeypatch, _disable("classes.barbarian"))
    assert _sliced(service, _request(built, "classes.barbarian.rage")) == [
        "classes.barbarian.rage"
    ]


def test_a_replaced_component_reads_replaced_in_its_place(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    record, key = "classes.barbarian.rage", "rage_damage"
    replaced = EffectiveOverrideEntry(
        override_id=f"replace-{record}-{key}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT, record_key=record, component_key=key
        ),
        operation=OverrideOperationEnum.REPLACE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "prose_bound",
                "facts": [],
                "authored_prose": "A house rage damage rule.",
            },
        },
    )
    service = _service(persisted, built, monkeypatch, replaced)
    view = _view(service, built, record)
    printed = [c.key for c in GEN.CLASSES_CHUNK.components if c.record == record]
    assert [c.component_key for c in view] == printed
    (entry,) = view[printed.index(key)].governing_prose
    assert (
        isinstance(entry, AuthoredProse) and entry.text == "A house rage damage rule."
    )
