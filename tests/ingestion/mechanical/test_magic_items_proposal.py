"""The ``magic-items`` proposal, offered for review -- CRD Issue 5d.

The *Magic Items* part below its heading and the paragraph under it, pp204-253,
proposed by ``.claude/review-notes/issue-5d-magic-items-generator.py`` from the
release 5c actually publishes, with its one resolution draft. The Owner
accepted both ("I accept this exact Magic Items proposal and its one reference
resolution, retaining 315 reference findings and the partial-publication
block."), which ``issue-5d-magic-items-ACCEPT.py`` recorded over the superseded
release (historical). On the Monsters-corrected release the regenerated
proposal and draft are batch twenty of the replacement chain the Owner
accepted, which ``issue-5d-monsters-corrections-ACCEPT.py`` recorded; the
nineteen batches before it are rebuilt here from that recording.

What is pinned, and why:

* the committed artifact is the superseded release's recorded proposal, by
  shape, and the draft is what the generator drafts over the committed
  nineteen-batch authority; the generator builds over the current release
  (that it no longer derives the recorded bytes, or the findings its
  superseded-release cross-reads give, is retired, see
  ``.claude/review-notes/issue-5c-release-readiness/correction-followup.md``);
* scope is the part's 1332 leaves, in printed order; the part heading and the
  paragraph under it stay uncovered, and no leaf is an accepted one's; the only
  accepted records it declares are the basic Potion of Healing and Spell Scroll
  Equipment sells, unchanged but for the family rows it prints as theirs, one
  item in two catalogues (Owner Decision 2026-09-27);
* grain: ten section records, the 258 items as catalogue members of *Magic
  Items A-Z*, and the two stat blocks an item prints scoped within it; *Time and
  Cost*, *Sentient Magic Item Traits* and *Special Purpose* are their own review
  units read into the section the source sets them in; every component
  prose-bound and reading its reviewed texts, every word of every spanned leaf
  claimed, and GM latitude exactly where the text leaves the ruling open;
* references name exact accepted or packet records or stay unresolved, by
  operative meaning: the plain names a cast-spell or rolled-creature table or
  an effect depends on are read, the Giant Goat by its whole name, and the
  Potion of Healing and Spell Scroll each keep one identity;
* the recorded proposal, composed in memory over the recorded chain (both the
  superseded release's): it accepts, then the draft resolves; every accepted
  byte is preserved, exactly the part's leaves gain coverage, the drafted
  *Carpet of Flying* pointer closes and the 315 unresolved pointers left are
  pinned on the representation's own reference findings. Judging that
  composition against a corpus needs the superseded release's, which is not
  rebuilt; that check is retired;
* the committed oracle keeps the chain through this batch whole, which
  preserves the nineteen batches before it but for the two reviewed obligation
  enlargements, under the Owner's decision and recorded time;
* through the production rules-authority service, over the current accepted
  authority persisted as one draft into the current release:
  *Magic Items A-Z* reaches its items once in printed order, a disabled item is
  gone, a replaced item reads replaced in place, the read-into sections read in
  printed order, an item reads its type line after the exact rules governing
  it, which an override of their owner suppresses and the catalogue does not
  repeat, and a stat block is its own scoped record; each catalogue printing a
  shared item reads the parts it prints once, in printed order, and an override
  of the item holds from either.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

from afterworlds.ingestion.mechanical.acceptance import (
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.models import ComponentHandling, ReviewState
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    OracleLoadError,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import persist_draft
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    identify_projection,
    review_unit_violations,
)
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    load_proposal,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordKind,
    RelationshipDraft,
    RelationshipKind,
    relationship_target_key,
)
from afterworlds.ingestion.mechanical.validation import (
    catalogue_parts,
    relationship_and_reference_violations,
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
    COMMITTED_SHA256,
    REPLACEMENT,
    animals_recorded,
    current,
    identity,
    kept_whole,
    proposal_path,
    through,
)
from tests.ingestion.mechanical._replacement_chain import (
    MAGIC_ITEMS as ACCEPT,
)
from tests.ingestion.mechanical._schema_pins import lifted
from tests.ingestion.mechanical.test_character_origins_feats_proposal import (
    _disable,
    _request,
    _service,
    _sliced,
)

REPO = Path(__file__).resolve().parents[3]
NOTES = REPO / ".claude" / "review-notes"
ORACLES = REPO / "src/afterworlds/ingestion/mechanical/oracles"
ORACLE = REPLACEMENT.ACCEPTED_PATH
BATCH = "magic-items"
MAGIC_ITEMS = "srd-5.2.1/magic-items"
PART = "Magic Items"
A_Z = "Magic Items A–Z"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load("magic_items_generator", NOTES / "issue-5d-magic-items-generator.py")
PROPOSAL = proposal_path(BATCH)
DRAFTS = REPLACEMENT.drafts_path(BATCH)
IDENTITY = identity(BATCH)
PROPOSAL_SHA256 = BATCHES[BATCH][1]
DRAFTS_SHA256 = REPLACEMENT.DRAFTS[BATCH][0]
#: The draft's id, as the regenerated draft names it.
RESOLUTION_ID = (
    "resolve-gameplay-toolbox-travel-pace-special-movement-carpet-of-flying-"
    "magic-items-1"
)
SECTION_KEYS = [
    "magic_items.magic_item_categories",
    "magic_items.magic_item_rules",
    "magic_items.magic_item_rarity",
    "magic_items.activating_a_magic_item",
    "magic_items.the_next_dawn",
    "magic_items.cursed_items",
    "magic_items.magic_item_resilience",
    "magic_items.crafting_magic_items",
    "magic_items.sentient_magic_items",
    "magic_items.magic_items_a_z",
]
CATALOGUE = "magic_items.magic_items_a_z"
CRAFTING = "magic_items.crafting_magic_items"
SENTIENT = "magic_items.sentient_magic_items"
FIGURINE = "magic_items.figurine_of_wondrous_power"
DECK = "magic_items.mysterious_deck"
GEAR = "equipment.adventuring_gear"
#: (family, the accepted Equipment record printed as some of its rows, that
#: record's accepted component) -- Owner Decision 2026-09-27.
SHARED = [
    ("Potions of Healing", f"{GEAR}.potion_of_healing", "potion_of_healing"),
    ("Spell Scroll", f"{GEAR}.spell_scroll", "spell_scroll"),
]
SHARED_KEYS = [record for _, record, _ in SHARED]


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
def prior() -> AcceptedInputs:
    """The nineteen-batch chain this packet is composed over, as recorded."""
    inputs = through("gameplay-toolbox")
    assert [b.batch_id for b in inputs.batches] == list(BATCHES)[:19]
    return inputs


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


def _texts(b: Built, record: str, key: str) -> list[str]:
    """The source texts one component's prose bindings are read from, of this
    batch's spans (an accepted batch's are :func:`_accepted_reads`)."""
    spans = {s.span_id: s for s in b.ledger.spans}
    return [
        b.leaf_rows[spans[x.span_id].leaf_id].content[
            spans[x.span_id].char_start : spans[x.span_id].char_end
        ]
        for x in b.proposal.proposed_representation.prose_bindings
        if (x.record_key, x.component_key) == (record, key) and x.span_id in spans
    ]


def _accepted_reads(b: Built) -> dict[tuple[str, str], list[str]]:
    """(record, component) -> the accepted spans it reads, in binding order."""
    mine = {s.span_id for s in b.ledger.spans}
    out: dict[tuple[str, str], list[str]] = {}
    for x in b.proposal.proposed_representation.prose_bindings:
        if x.span_id not in mine:
            out.setdefault((x.record_key, x.component_key), []).append(x.span_id)
    return out


def _refs(b: Built) -> list[tuple[str, str, str, str, str]]:
    return [
        (
            r.from_record_key,
            r.from_component_key,
            r.source_text,
            r.scope_key,
            r.target_record_key,
        )
        for r in b.proposal.proposed_representation.references
    ]


def _printed(*path: str) -> list[str]:
    """Every leaf printed at or below *path* under the part, in order."""
    full = (PART, *path)
    return [t for p, t in GEN.LEAVES if p[: len(full)] == full]


# ---------------------------------------------------------------------------
# The artifacts
# ---------------------------------------------------------------------------


def test_the_committed_artifact_is_the_recorded_proposal_by_shape(built) -> None:  # type: ignore[no-untyped-def]
    data = PROPOSAL.read_bytes()
    assert hashlib.sha256(data).hexdigest() == PROPOSAL_SHA256
    assert b"\r" not in data
    proposal = load_proposal(PROPOSAL, expected_identity=IDENTITY)
    assert json.loads(data)["artifact_kind"] == "machine_proposal"
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(PROPOSAL)
    # The generator builds over the current release.
    assert built.binding == current().oracle.binding


def test_the_one_draft_names_the_item_the_toolbox_cites(prior) -> None:  # type: ignore[no-untyped-def]
    data = DRAFTS.read_bytes()
    assert hashlib.sha256(data).hexdigest() == DRAFTS_SHA256 and b"\r" not in data
    drafts = GEN.draft_resolutions(prior.oracle.binding, prior=prior)
    assert json.loads(data) == reference_resolution_payload(drafts)
    assert [
        (
            d.from_record_key,
            d.from_component_key,
            d.source_text,
            d.scope_key,
            d.target_record_key,
        )
        for d in drafts
    ] == [
        (
            "gameplay_toolbox.travel_pace",
            "special_movement",
            "Carpet of Flying",
            MAGIC_ITEMS,
            "magic_items.carpet_of_flying",
        )
    ]
    # The part pointers name no record: none is guessed.
    _, left = GEN.draft_targets(prior)
    assert sorted(left) == [
        ("equipment.magic_items", "magic_items", "Magic Items"),
        ("equipment.weapons", "selling_equipment", "Magic Items"),
        (
            "gameplay_toolbox.curses_and_magical_contagions",
            "cursed_magic_items",
            "Magic Items",
        ),
    ]


# ---------------------------------------------------------------------------
# Scope and grain
# ---------------------------------------------------------------------------


def test_scope_is_the_part_s_1332_leaves(session, built) -> None:  # type: ignore[no-untyped-def]
    rows = (
        session.query(LedgerLeafORM)
        .filter(LedgerLeafORM.package_uuid == built.binding.package_uuid)
        .order_by(LedgerLeafORM.occurrence_index)
        .all()
    )
    (head,) = [i for i, r in enumerate(rows) if r.content == "# Magic Items"]
    part = rows[head + 2 : head + 2 + len(GEN.LEAVES)]
    assert [r.content for r in part] == [t for _, t in GEN.LEAVES]
    # The part runs to the next part heading.
    assert rows[head + 2 + len(GEN.LEAVES)].content.startswith("# ")
    mine = [leaf for u in built.proposal.proposed_review_units for leaf in u.leaf_ids]
    assert len(mine) == len(set(mine)) == 1332
    assert set(mine) == {r.leaf_id for r in part}
    # The part heading and the paragraph under it stay with the part headings.
    assert not {rows[head].leaf_id, rows[head + 1].leaf_id} & set(mine)
    assert not rows[head + 1].content.startswith("#")
    keys = [r.semantic_key for r in built.proposal.proposed_representation.records]
    assert len(keys) == len(set(keys))


def test_no_recorded_leaf_is_an_accepted_one_but_the_shared_records(  # type: ignore[no-untyped-def]
    recorded, prior
) -> None:
    # Both sides are the superseded release's: the recorded chain and proposal.
    mine = [leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids]
    assert len(mine) == len(set(mine)) == 1332
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    assert not owned & set(mine)
    accepted = {r.semantic_key for r in prior.oracle.representation.records}
    keys = [r.semantic_key for r in recorded.proposed_representation.records]
    # The two items Equipment also sells keep their accepted identity.
    assert len(keys) == len(set(keys)) and accepted & set(keys) == set(SHARED_KEYS)


def test_the_records_are_ten_sections_the_items_and_two_stat_blocks(built) -> None:  # type: ignore[no-untyped-def]
    rep = built.proposal.proposed_representation
    assert Counter(r.kind for r in rep.records) == {
        RecordKind.GENERAL_RULE: 10,
        RecordKind.MAGIC_ITEM: 258,
        RecordKind.CREATURE: 2,
        RecordKind.EQUIPMENT: 2,
    }
    keys = [r.semantic_key for r in rep.records]
    assert [
        r.semantic_key for r in rep.records if r.kind is RecordKind.GENERAL_RULE
    ] == SECTION_KEYS
    assert [r.semantic_key for r in rep.records if r.kind is RecordKind.MAGIC_ITEM] == [
        GEN.item_key(n) for n in GEN.ITEM_NAMES
    ]
    assert "magic_items.armor_1_2_or_3" in keys
    assert not [k for k in keys if "time_and_cost" in k or "special_purpose" in k]
    # The three read-into sections are each reviewed alone: 271 units.
    units = {u.unit_id: u for u in built.proposal.proposed_review_units}
    assert len(units) == 271
    for section, host in GEN.READ_INTO.items():
        unit = units[f"magic-items/{GEN.slug(section)}"]
        assert unit.kind.value == "section"
        assert [built.leaf_rows[x].content for x in unit.leaf_ids] == _printed(section)
        assert {r.record_key for r in unit.expected_rules} == {GEN.section_key(host)}
    edges = Counter((r.kind, r.target_record_key) for r in rep.relationships)
    assert edges == {
        (RelationshipKind.CATALOGUE_MEMBER, CATALOGUE): 258,
        (RelationshipKind.SCOPED_WITHIN, FIGURINE): 1,
        (RelationshipKind.SCOPED_WITHIN, DECK): 1,
        **{
            (RelationshipKind.CATALOGUE_MEMBER, GEN.item_key(n)): 1
            for n, _, _ in SHARED
        },
    }
    # Each item is the catalogue's, in printed order.
    assert [
        r.source_record_key
        for r in rep.relationships
        if r.kind is RelationshipKind.CATALOGUE_MEMBER
        and r.target_record_key == CATALOGUE
    ] == [GEN.item_key(n) for n in GEN.ITEM_NAMES]
    assert {
        r.source_record_key
        for r in rep.relationships
        if r.kind is RelationshipKind.SCOPED_WITHIN
    } == {f"{FIGURINE}.giant_fly", f"{DECK}.avatar_of_death"}


def test_each_section_reads_its_subheadings_in_printed_order(built, prior) -> None:  # type: ignore[no-untyped-def]
    components = built.proposal.proposed_representation.components
    by = {
        k: [c.semantic_key for c in components if c.record_key == k]
        for k in SECTION_KEYS
    }
    assert by["magic_items.magic_item_categories"] == [
        "magic_item_categories",
        "armor",
        "potions",
        "rings",
        "rods",
        "scrolls",
        "staffs",
        "wands",
        "weapons",
        "wondrous_items",
    ]
    assert by["magic_items.activating_a_magic_item"] == [
        "activating_a_magic_item",
        "command_word",
        "consumable_items",
        "spells_cast_from_items",
        "charges",
    ]
    # Time and Cost follows Spells, as the PDF sets it (p208).
    assert by[CRAFTING] == [
        "crafting_magic_items",
        "arcana_proficiency",
        "tools",
        "spells",
        "time_and_cost",
    ]
    # The traits and Special Purpose follow, as the PDF sets them (pp208-209);
    # the four tables floated into Special Purpose are each their own.
    assert by[SENTIENT] == [
        "sentient_magic_items",
        "sentient_magic_item_traits",
        "abilities",
        "alignment",
        "communication",
        "senses",
        "special_purpose",
        "sentient_items_alignment",
        "sentient_items_communication",
        "sentient_items_senses",
        "sentient_items_special_purpose",
        "conflict",
    ]
    for key in by[SENTIENT][7:11]:
        (table,) = _texts(built, SENTIENT, key)
        assert table.startswith("**Sentient Item's ") and "<table>" in table
    assert by[CATALOGUE] == ["magic_items_a_z"]
    assert _texts(built, CATALOGUE, "magic_items_a_z") == GEN.texts_at((PART, A_Z))
    # Each item is its own component -- a casting variant its own besides --
    # each reading the general rules governing it, in source order, then its
    # leaves; together they are every leaf of the item, in printed order.
    for name in GEN.ITEM_NAMES:
        key = GEN.item_key(name)
        parts = GEN.item_components(name)
        assert [c.semantic_key for c in components if c.record_key == key] == [
            k for k, _, _ in parts
        ]
        leaves: list[str] = []
        for k, own_texts, context in parts:
            texts = _texts(built, key, k)
            assert texts == [*(t for t, _ in context), *own_texts]
            leaves += own_texts
        # A family whose table prints an Equipment record's rows reads the
        # table cut at them, rejoining whole.
        whole = GEN.texts_at((PART, A_Z, name))
        assert leaves == whole or (
            name in GEN.SHARED_ROWS and "".join(leaves) == "".join(whole)
        )
        assert leaves[0] == f"#### {name}" and GEN.TYPE_LINE.fullmatch(leaves[1])
        assert parts[0][0] == GEN.slug(name)
    assert [
        c.semantic_key for c in components if c.record_key == f"{DECK}.avatar_of_death"
    ] == ["avatar_of_death", "traits", "actions"]
    # Legacy generator probe, historical by construction: ``GEN.build`` cuts
    # the packet from the current release but borrows the Equipment attunement
    # spans it injects from its own historical ``GEN.current()``, the chain
    # ``prior`` is. This pins what that generator injects -- each attuned item
    # reads the four attunement rules, contextually, and no other accepted
    # span -- not current accepted wiring, which the persisted-current service
    # tests below pin (exact text, order, disable and replace).
    attunement = [
        x.span_id
        for key in GEN.ATTUNEMENT_RULES
        for x in prior.oracle.representation.prose_bindings
        if (x.record_key, x.component_key) == key
    ]
    assert len(attunement) == 4
    assert _accepted_reads(built) == {
        (GEN.item_key(n), GEN.slug(n)): attunement for n in GEN.ATTUNED
    }
    rep = built.proposal.proposed_representation
    claims = {
        (c.target_key, c.span_id): c.role
        for c in rep.provenance
        if c.span_id in set(attunement)
    }
    assert len(claims) == 4 * 140
    assert set(claims.values()) == {ProvenanceRole.CONTEXTUAL}


# ---------------------------------------------------------------------------
# Fidelity
# ---------------------------------------------------------------------------


def _residue(b: Built) -> dict[str, str]:
    """Text of a spanned leaf no span covers."""
    out = {}
    for lid in {s.leaf_id for s in b.ledger.spans}:
        text = list(b.leaf_rows[lid].content)
        for s in b.ledger.spans:
            if s.leaf_id == lid:
                text[s.char_start : s.char_end] = " " * (s.char_end - s.char_start)
        if left := "".join(text).strip():
            out[lid] = left
    return out


def test_every_component_reads_its_reviewed_texts_as_prose(built) -> None:  # type: ignore[no-untyped-def]
    chunk = GEN.MAGIC_ITEMS_CHUNK
    components = built.proposal.proposed_representation.components
    assert {c.handling for c in components} == {ComponentHandling.PROSE_BOUND}
    assert not [c for c in components if c.all_facts()]
    clauses = {(e, k): texts for e, k, _, texts in chunk.clauses}
    for c in chunk.components:
        record = c.record or chunk.placements[c.entry].record_key
        texts = c.texts or clauses[(c.entry, c.key)]
        assert _texts(built, record, c.key) == list(texts)
    assert _residue(built) == {}
    assert not [
        g for u in built.proposal.proposed_review_units for g in u.excluded_groups
    ]
    # Each placed entry's first clause reads its own heading.
    for entry, placement in chunk.placements.items():
        first = next(texts for e, _, _, texts in chunk.clauses if e == entry)
        assert first[0] == placement.heading
    # A section's components never bind an item's leaves.
    item_texts = {t for n in GEN.ITEM_NAMES for t in _printed(A_Z, n)}
    for k in SECTION_KEYS:
        for c in [c for c in components if c.record_key == k]:
            assert not item_texts & set(_texts(built, k, c.semantic_key))


#: (record, component) -> the words by which the source leaves the ruling open
#: to whoever runs the game.
LATITUDE = {
    ("magic_items.magic_item_categories", "potions"): "At your discretion",
    ("magic_items.magic_item_rules", "magic_item_rules"): "Use your discretion",
    (
        "magic_items.magic_item_rarity",
        "magic_item_values_by_rarity",
    ): "If you allow characters to buy and sell",
    ("magic_items.the_next_dawn", "the_next_dawn"): "the GM determines when",
    (CRAFTING, "time_and_cost"): "the GM might allow more assistants",
    (SENTIENT, "sentient_magic_items"): "The GM controls sentient magic items",
    **{
        (f"magic_items.{k}", k): words
        for k, words in {
            "bag_of_beans": "treasure of the GM's choice",
            "bag_of_devouring": "The GM determines the time and plane.",
            "cubic_gate": "linked to planes determined by the GM",
            "dragon_orb": "something else the GM decides",
            "hat_of_many_spells": "The GM chooses the item",
            "iron_flask": "a creature chosen by the GM",
            "mysterious_deck": "A magic item (chosen by the GM)",
            "pipes_of_the_sewers": "(as determined by the GM)",
            "ring_of_spell_storing": "stored spells chosen by the GM",
            "vorpal_sword": "if the GM decides that the creature is too big",
            "wand_of_wonder": "An object of the GM's choice",
            "well_of_many_worlds": "the GM decides where it leads",
        }.items()
    },
    # The Reserve's own leaves: the GM chooses the spells it holds.
    ("magic_items.ioun_stone", "reserve"): "stored spells chosen by the GM",
}


def test_latitude_is_exactly_where_the_text_leaves_the_ruling_open(built) -> None:  # type: ignore[no-untyped-def]
    rep = built.proposal.proposed_representation
    got = {}
    for c in rep.components:
        # Exactly one reason: latitude is irreducible, the rest retained.
        assert (c.irreducibility_reason_code is None) != (
            c.prose_retention_reason_code is None
        )
        assert c.irreducibility_reason_code in (None, GEN.GM)
        assert c.prose_retention_reason_code in (None, GEN.NO_USE)
        if c.irreducibility_reason_code == GEN.GM:
            got[(c.record_key, c.semantic_key)] = " ".join(
                _texts(built, c.record_key, c.semantic_key)
            )
    assert set(got) == set(LATITUDE)
    assert all(words in got[k] for k, words in LATITUDE.items())
    # Each prose binding carries its component's reason.
    reasons = {
        (c.record_key, c.semantic_key): (
            c.irreducibility_reason_code,
            c.prose_retention_reason_code,
        )
        for c in rep.components
    }
    for b in rep.prose_bindings:
        assert reasons[(b.record_key, b.component_key)] == (
            b.irreducibility_reason_code,
            b.prose_retention_reason_code,
        )
    # The GM choosing among printed options or rolling a printed table is
    # reducible; so is the persona procedure with its printed trait tables, and
    # the Ring of Mind Shielding's "if you allow", whose "you" is the bearer.
    for k in [
        ("magic_items.armor_of_resistance", "armor_of_resistance"),
        ("magic_items.carpet_of_flying", "carpet_of_flying"),
        ("magic_items.sphere_of_annihilation", "sphere_of_annihilation"),
        ("magic_items.ring_of_mind_shielding", "ring_of_mind_shielding"),
        (SENTIENT, "sentient_magic_item_traits"),
        (SENTIENT, "special_purpose"),
    ]:
        assert k not in got and _texts(built, *k), k
    assert len(GEN.NOT_LATITUDE) == 16


def test_references_name_exact_records_or_stay_unresolved(built) -> None:  # type: ignore[no-untyped-def]
    refs = _refs(built)
    eq = "srd-5.2.1/equipment"
    mon = "srd-5.2.1/monsters"
    for ref in (
        ("magic_items.bag_of_holding", "bag_of_holding", "Portable Hole",
         MAGIC_ITEMS, "magic_items.portable_hole"),
        ("magic_items.oil_of_sharpness", "oil_of_sharpness", "+3 Weapon",
         MAGIC_ITEMS, "magic_items.weapon_1_2_or_3"),
        ("magic_items.magic_item_rules", "magic_item_rules",
         "Glove of Missile Snaring", MAGIC_ITEMS,
         "magic_items.gloves_of_missile_snaring"),
        (FIGURINE, "figurine_of_wondrous_power", "Giant Fly", MAGIC_ITEMS,
         f"{FIGURINE}.giant_fly"),
        (DECK, "mysterious_deck", "Avatar of Death", MAGIC_ITEMS,
         f"{DECK}.avatar_of_death"),
        ("magic_items.wand_of_fireballs", "wand_of_fireballs", "Fireball",
         "srd-5.2.1/spells", "spells.fireball"),
        ("magic_items.magic_item_categories", "staffs", "Quarterstaff", eq,
         "equipment.weapons.quarterstaff"),
        ("magic_items.sun_blade", "sun_blade", "Finesse", eq,
         "equipment.weapons.finesse"),
        ("magic_items.sun_blade", "sun_blade", "Longsword", eq, ""),
        ("magic_items.hat_of_many_spells", "hat_of_many_spells", "Acid", eq,
         "equipment.adventuring_gear.acid"),
        ("magic_items.hat_of_many_spells", "hat_of_many_spells", "Camel", mon, ""),
        ("magic_items.magic_items_a_z", "magic_items_a_z", "Monsters", mon, ""),
        ("magic_items.magic_item_categories", "scrolls", "Spell Scroll",
         MAGIC_ITEMS, "magic_items.spell_scroll"),
        ("magic_items.magic_item_rarity", "magic_item_values_by_rarity",
         "Scribing Spell Scrolls", eq, "equipment.scribing_spell_scrolls"),
        ("magic_items.rod_of_rulership", "rod_of_rulership", "Charmed",
         "srd-5.2.1/rules-glossary", "glossary.charmed"),
    ):  # fmt: skip
        assert ref in refs, ref
    # An item naming itself or a pointer inside its own record is none.
    assert not [r for r in refs if r[0] == r[4]]
    assert not [
        r for r in refs if r[0] == "magic_items.spell_scroll" and r[2] in GEN.SHARED
    ]
    assert "Conflict" not in {r[2] for r in refs}
    # Monster targets are never guessed; every bold and plain creature is read.
    assert {r[4] for r in refs if r[3] == mon} == {""}
    plain = {t for rs in GEN.PLAIN.values() for t, (s, _) in rs if s == mon}
    assert {r[2] for r in refs if r[3] == mon} == GEN.CREATURE_NAMES | plain | {
        "Monsters"
    }


def _of(built, record: str) -> set[tuple[str, str, str]]:  # type: ignore[no-untyped-def]
    return {(t, s, k) for r, _, t, s, k in _refs(built) if r == record}


def test_plain_names_an_effect_depends_on_are_read(built) -> None:  # type: ignore[no-untyped-def]
    spells, mon = "srd-5.2.1/spells", "srd-5.2.1/monsters"
    # The Wand of Wonder's table casts its spells, printed plainly; "Darkness"
    # is the spell, not the glossary's; "Enlarge/ Reduce" as printed.
    wonder = _of(built, "magic_items.wand_of_wonder")
    for name, key in [
        ("Darkness", "darkness"),
        ("Fireball", "fireball"),
        ("Slow", "slow"),
        ("Enlarge/ Reduce", "enlarge_reduce"),
        ("Greater Restoration", "greater_restoration"),
        ("Polymorph", "polymorph"),
    ]:
        assert (name, spells, f"spells.{key}") in wonder, name
    assert not [x for x in wonder if x[0] == "Darkness" and x[1] != spells]
    for creature in ("Rhinoceros", "Elephant", "Rat", "Black Bear", "Giant Wasp"):
        assert (creature, mon, "") in wonder
    assert ("Cure Wounds", spells, "spells.cure_wounds") in _of(
        built, "magic_items.dragon_orb"
    )
    assert ("Shining Smite", spells, "spells.shining_smite") in _of(
        built, "magic_items.necklace_of_prayer_beads"
    )
    assert ("Wish", spells, "spells.wish") in _of(built, "magic_items.efreeti_bottle")
    cube = _of(built, "magic_items.cube_of_force")
    # The Cube's "Shield" face is the spell, never the armor.
    assert ("Shield", spells, "spells.shield") in cube
    assert not [x for x in cube if x[0] == "Shield" and x[1] != spells]
    # Rolled and conjured creatures, each unresolved; the saddle is gear.
    tricks = {t for t, s, _ in _of(built, "magic_items.bag_of_tricks") if s == mon}
    assert (
        len(tricks - {"Monsters"}) == 24
        and {"Giant Goat", "Goat", "Axe Beak"} <= tricks
    )
    robe = _of(built, "magic_items.robe_of_useful_items")
    assert {("Riding Horse", mon, ""), ("Mastiffs", mon, "")} <= robe
    assert not [x for x in robe if "Saddle" in x[0]]
    illusions = {
        t for t, s, _ in _of(built, "magic_items.deck_of_illusions") if s == mon
    }
    assert len(illusions - {"Monsters"}) == 32 and "Veteran Warrior" in illusions
    # "see Poison in Gameplay Toolbox", to the accepted Poison record.
    assert (
        "Poison",
        "srd-5.2.1/gameplay-toolbox",
        "gameplay_toolbox.poison",
    ) in _of(built, "magic_items.magic_item_categories")


def test_giant_goat_is_read_by_its_whole_printed_name(built) -> None:  # type: ignore[no-untyped-def]
    # "a Giant **Goat**": the bold covers only "Goat"; the name is Giant Goat,
    # cited from both goat figurines, and the source bytes are untouched.
    fig = {t for t, _, _ in _of(built, FIGURINE)}
    assert "Giant Goat" in fig and "Goat" not in fig
    travail = next(
        t for t in _printed(A_Z, "Figurine of Wondrous Power") if "Giant **Goat**" in t
    )
    rep = built.proposal.proposed_representation
    (ref,) = [
        r
        for r in rep.references
        if r.from_record_key == FIGURINE and r.source_text == "Giant Goat"
    ]
    spans = {s.span_id: s for s in built.ledger.spans}
    cited = [
        built.leaf_rows[spans[c.span_id].leaf_id].content
        for c in rep.provenance
        if c.target_kind is ProvenanceTargetKind.REFERENCE
        and c.target_key[:3] == (FIGURINE, ref.from_component_key, "Giant Goat")
    ]
    assert travail in cited and len(cited) == 2


def test_potion_of_healing_and_spell_scroll_keep_one_identity(built) -> None:  # type: ignore[no-untyped-def]
    eq = "srd-5.2.1/equipment"
    potion = (eq, "equipment.adventuring_gear.potion_of_healing")
    scroll = (MAGIC_ITEMS, "magic_items.spell_scroll")
    refs = _refs(built)
    # The basic potion, by its exact name, is the accepted Equipment record;
    # the family's table row printing it is that record's own (Owner Decision
    # 2026-09-27), so the family no longer points at it: it is a member.
    assert {
        (r[3], r[4])
        for r in refs
        if r[2] in ("Potion of Healing", "Potions of Healing")
    } <= {potion}
    assert ("Potion of Healing", *potion) not in _of(
        built, "magic_items.potions_of_healing"
    )
    assert not [r for r in refs if r[2].startswith("Potion of Healing (")]
    # An unqualified Spell Scroll is the family; the quoted Equipment section
    # stays its own pointer.
    assert {
        (r[3], r[4]) for r in refs if r[2] in ("Spell Scroll", "Spell Scrolls")
    } == {scroll}
    assert ("Spell Scroll", *scroll) in _of(built, "magic_items.robe_of_useful_items")
    assert not [r for r in refs if r[4] == "" and r[3] == MAGIC_ITEMS]
    # A stat block cites only glossary terms.
    for r in refs:
        if r[0] in (f"{FIGURINE}.giant_fly", f"{DECK}.avatar_of_death"):
            assert r[3] == "srd-5.2.1/rules-glossary", r


#: The packet's own unresolved pointers, by scope.
UNRESOLVED_SCOPES = {
    "srd-5.2.1/equipment": 41,
    "srd-5.2.1/monsters": 109,
}


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert (
        Counter(
            f.split(":")[0].split(" ")[1]
            for f in found["representation"]
            if "unresolved reference" in f
        )
        == UNRESOLVED_SCOPES
    )


# ---------------------------------------------------------------------------
# Test-only composition with the committed oracle
# ---------------------------------------------------------------------------


def _accepted(prior: AcceptedInputs, proposal: MechanicalProposal) -> AcceptedInputs:
    return accept_proposal(
        proposal,
        batch_id="magic-items",
        rule="test-only",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer="test",
        accepted_at="2026-09-27T00:00:00Z",
        prior=prior,
    )


def _covered(inputs: AcceptedInputs) -> set[str]:
    oracle = inputs.oracle
    return {s.leaf_id for s in oracle.spans} | {
        leaf for u in oracle.review_units for leaf in u.leaf_ids
    }


def _references(inputs: AcceptedInputs) -> list[str]:
    # The effective representation's own relationship and reference findings
    # (resolutions applied): no corpus, so none of the superseded release's is
    # needed.
    return relationship_and_reference_violations(
        candidate_from_accepted_inputs(lifted(inputs)).representation
    )


#: Reference findings left after accepting and resolving, all unresolved: the
#: committed 166, less the one drafted, plus the packet's own.
REMAINING = 166 - 1 + sum(UNRESOLVED_SCOPES.values())


def test_accepted_then_resolved_in_memory_preserves_everything(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    on_disk = {p.name: p.read_bytes() for p in ORACLES.iterdir()}
    base = prior.oracle
    assert (
        len(prior.batches),
        len(base.representation.records),
        len(base.spans),
        len(base.review_units),
        len(base.reference_resolutions),
    ) == (19, 980, 5111, 679, 1098)
    # Both sides are the superseded release's: the recorded chain and proposal.
    assert recorded.binding == base.binding
    refs_before = _references(prior)
    assert len(refs_before) == 166

    accepted = _accepted(prior, recorded)
    drafts = GEN.draft_resolutions(base.binding, prior=prior)
    resolved = resolve_references(
        accepted,
        resolutions=drafts,
        authorized_by="test",
        authorization_reference="test-only",
        reviewer="test",
        resolved_at="2026-09-27T00:00:01Z",
    )
    final = resolved.oracle
    # Append-only: every accepted byte the authority holds is still held, but
    # for the one derived delta: the obligation stating each shared record's
    # prose-bound components also names the family rows it gains.
    old, new = accepted_inputs_payload(prior), accepted_inputs_payload(resolved)
    assert not REPLACEMENT._preserved(
        {**old, "obligations": []}, {**new, "obligations": []}
    )
    was = cast(list[dict[str, Any]], old["obligations"])
    now = {o["record_key"]: o for o in cast(list[dict[str, Any]], new["obligations"])}
    changed = [o["record_key"] for o in was if now[o["record_key"]] != o]
    assert changed == SHARED_KEYS
    for o in was:
        if o["record_key"] in SHARED_KEYS:
            assert now[o["record_key"]] == {
                **o,
                "prose_bound_components": sorted(
                    [*o["prose_bound_components"], GEN.SHARED_COMPONENT]
                ),
            }
    assert resolved.batches[: len(prior.batches)] == prior.batches
    assert (
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (980 + 270, 5111 + 1339, 679 + 271, 1098 + 1)
    # The two shared Equipment records are the accepted ones, each gaining one
    # component: 272 packet records, 270 new.
    records = {r.semantic_key: r for r in final.representation.records}
    old = {r.semantic_key: r for r in base.representation.records}
    assert all(records[k] == old[k] for k in SHARED_KEYS)
    for _, record, key in SHARED:
        assert [
            c.semantic_key
            for c in final.representation.components
            if c.record_key == record
        ] == [key, GEN.SHARED_COMPONENT]
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )
    # Every accepted target closes; only unresolved pointers remain: the
    # committed ones less the drafted, plus the packet's own.
    rest = _references(resolved)
    assert all(f.startswith("reference ") and "unresolved" in f for f in rest)
    drafted = f"reference {MAGIC_ITEMS}:'Carpet of Flying': unresolved reference"
    assert drafted in refs_before and drafted not in rest
    packet = [
        f
        for f in GEN.expected_representation_findings(GEN.MAGIC_ITEMS_CHUNK)
        if "unresolved" in f
    ]
    assert Counter(f.split(":")[0].split(" ")[1] for f in packet) == (UNRESOLVED_SCOPES)
    assert sorted(rest) == sorted([*(f for f in refs_before if f != drafted), *packet])
    assert len(rest) == REMAINING == 315
    # Exactly the part's leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(resolved) - _covered(prior) == mine
    assert len(mine) == 1332
    # The committed directory is untouched.
    assert {p.name: p.read_bytes() for p in ORACLES.iterdir()} == on_disk
    assert hashlib.sha256(ORACLE.read_bytes()).hexdigest() == COMMITTED_SHA256


def test_the_committed_oracle_records_the_owner_acceptance(prior) -> None:  # type: ignore[no-untyped-def]
    # The recorded chain through this batch is the Owner's steps over the
    # nineteen batches before it, which it keeps whole but for the one
    # reviewed derived delta.
    recorded = through(BATCH)
    old, new = accepted_inputs_payload(prior), accepted_inputs_payload(recorded)
    assert not REPLACEMENT._preserved(
        {**old, "obligations": []}, {**new, "obligations": []}
    )
    assert ACCEPT.obligation_delta(prior, recorded) == []
    assert tuple(SHARED_KEYS) == ACCEPT.SHARED_KEYS
    assert ACCEPT.SHARED_COMPONENT == GEN.SHARED_COMPONENT
    assert [b.batch_id for b in recorded.batches] == list(BATCHES)
    assert recorded.batches[: len(prior.batches)] == prior.batches
    assert serialize_accepted_inputs(recorded) == serialize_accepted_inputs(through())
    # The Animals recording keeps it whole, times, obligations and all; the
    # committed oracle keeps that outside the replaced Equipment batch.
    # The superseded release's committed file, read by path: the production
    # resolver refuses its binding.
    committed = load_accepted_inputs(ORACLE)
    data = serialize_accepted_inputs(committed)
    assert data == ORACLE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == COMMITTED_SHA256
    animals = animals_recorded()
    assert not REPLACEMENT._preserved(
        accepted_inputs_payload(recorded), accepted_inputs_payload(animals)
    )
    assert not kept_whole(prior, animals)
    (batch,) = [b for b in recorded.batches if b.batch_id == BATCH]
    assert (batch.proposal_identity, batch.rule) == (IDENTITY, REPLACEMENT.APPROVAL)
    mine = [a for a in recorded.acceptances if a.batch_id == BATCH]
    assert len(mine) == len(recorded.acceptances) - len(prior.acceptances)
    assert {(a.reviewer, a.accepted_at) for a in mine} == {
        (REPLACEMENT.OWNER, REPLACEMENT.ACCEPTED_AT)
    }
    new_acceptances = [
        a
        for a in recorded.reference_resolution_acceptances
        if a.resolution_id.endswith("-magic-items-1")
    ]
    assert [
        (a.resolution_id, a.authorized_by, a.reviewer, a.resolved_at)
        for a in new_acceptances
    ] == [
        (
            RESOLUTION_ID,
            REPLACEMENT.OWNER,
            REPLACEMENT.OWNER,
            REPLACEMENT.ACCEPTED_AT,
        )
    ]
    assert new_acceptances[0].authorization_reference == (
        REPLACEMENT.AUTHORIZATION_REFERENCE
    )
    assert REPLACEMENT.OWNER_REVIEW_SHA256 in REPLACEMENT.AUTHORIZATION_REFERENCE
    # The one resolution is the reviewed draft, byte for byte.
    (resolution,) = [
        r
        for r in recorded.oracle.reference_resolutions
        if r.resolution_id == RESOLUTION_ID
    ]
    assert list(reference_resolution_payload((resolution,))) == json.loads(
        DRAFTS.read_bytes()
    )


# ---------------------------------------------------------------------------
# Through the production rules-authority service
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db):  # type: ignore[no-untyped-def]
    """The current accepted authority, persisted as one draft into a private
    copy of the current release."""
    candidate = candidate_from_accepted_inputs(current())
    assert isinstance(candidate, ProjectionCandidate)
    path = tmp_path_factory.mktemp("magic_items") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(candidate)
        persist_draft(s, identified, now="2026-09-27T00:00:00Z")
        s.commit()
        yield s, identified.projection_uuid
    engine.dispose()


def _view(service, built, *records: str) -> list[tuple[str, str, object]]:  # type: ignore[no-untyped-def]
    view = service.gamemaster_view(_request(built, *records))
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    return [
        (c.record_key, c.component_key, e)
        for c in view.gamemaster_view.components
        for e in c.governing_prose
    ]


#: The leaves of the two stat blocks, which their items' reads do not reach.
STAT_BLOCK_LEAVES = [
    *_printed(A_Z, "Figurine of Wondrous Power", "Giant Fly"),
    *_printed(A_Z, "Mysterious Deck", "Avatar of Death"),
]


EQUIPMENT_RULES = "equipment.magic_items"


def _attunement(service, built) -> list[str]:  # type: ignore[no-untyped-def]
    """The accepted Equipment attunement rules, as their owner reads them."""
    keys = {k for _, k in GEN.ATTUNEMENT_RULES}
    return [
        e.text  # type: ignore[attr-defined]
        for _, k, e in _view(service, built, EQUIPMENT_RULES)
        if k in keys
    ]


def _context(name: str, attunement: list[str]) -> list[str]:
    """What a direct read of *name* carries ahead of its own passages, in
    source order: Equipment precedes this part."""
    return [
        *(attunement if name in GEN.ATTUNED else []),
        *(t for t, _ in GEN.item_context(name)),
    ]


def _read(name: str, attunement: list[str]) -> list[str]:
    """A direct read of *name*: each component's context, then its passages,
    in printed order; the attunement rules govern the item's own key."""
    out: list[str] = []
    for i, (_, texts, context) in enumerate(GEN.item_components(name)):
        if i == 0 and name in GEN.ATTUNED:
            out += attunement
        out += [t for t, _ in context]
        out += [t for t in texts if t not in STAT_BLOCK_LEAVES]
    return out


def _catalogue(attunement: list[str]) -> list[str]:
    """The catalogue read: each item's printed passages, the context owned
    outside the catalogue read once, ahead of the first item reading it."""
    out: list[str] = []
    for name in GEN.ITEM_NAMES:
        for i, (_, texts, context) in enumerate(GEN.item_components(name)):
            outer = attunement if i == 0 and name in GEN.ATTUNED else []
            out += [t for t in (*outer, *(t for t, _ in context)) if t not in out]
            out += [t for t in texts if t not in STAT_BLOCK_LEAVES]
    return [*_printed(A_Z)[: _printed(A_Z).index(f"#### {GEN.ITEM_NAMES[0]}")], *out]


def test_the_catalogue_reaches_its_items_once_in_printed_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    items = [GEN.item_key(n) for n in GEN.ITEM_NAMES]
    # Its items, then what it reads of the Equipment items two families print.
    assert _sliced(service, _request(built, CATALOGUE)) == [
        CATALOGUE,
        *items,
        *SHARED_KEYS,
    ]
    read = _view(service, built, CATALOGUE)
    attunement = _attunement(service, built)
    assert len(attunement) == 4
    assert [e.text for _, _, e in read] == _catalogue(attunement)  # type: ignore[attr-defined]
    # Every governing passage is read once, the external ones at a reader.
    spans = [e.span_id for _, _, e in read]  # type: ignore[attr-defined]
    assert len(spans) == len(set(spans))
    # Selecting the catalogue and an item returns the item once.
    both = _sliced(service, _request(built, CATALOGUE, items[0]))
    assert both.count(items[0]) == 1 and len(both) == 261


def test_an_item_reads_alone_with_its_type_line(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    item = "magic_items.bag_of_holding"
    assert _sliced(service, _request(built, item)) == [item]
    read = _view(service, built, item)
    assert [e.text for _, _, e in read] == _printed(A_Z, "Bag of Holding")  # type: ignore[attr-defined]
    assert read[1][2].text == "_Wondrous Item, Uncommon_"  # type: ignore[attr-defined]


RULES = "magic_items.magic_item_rules"
ACTIVATING = "magic_items.activating_a_magic_item"
FIREBALLS = "magic_items.wand_of_fireballs"


def test_an_item_read_directly_carries_the_rules_governing_it(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    attunement = _attunement(service, built)
    read = _view(service, built, FIREBALLS)
    # Equipment's attunement rules; the wand's Arcane Focus default; the
    # attunement prerequisite (item-only spellcasting does not qualify); Spells
    # Cast from Items (no slot, no components, normal casting time, range,
    # duration and Concentration); Charges (Identify, attuned knowledge); in
    # source order, then the item.
    assert [e.text for _, _, e in read] == [  # type: ignore[attr-defined]
        *attunement,
        GEN.CATEGORY_RULES["Wand"],
        GEN.PREREQUISITES,
        GEN.CAST_FROM_ITEMS,
        GEN.CHARGES,
        *_printed(A_Z, "Wand of Fireballs"),
    ]
    assert "not by using a magic item" in GEN.PREREQUISITES
    assert {r for r, _, _ in read} == {FIREBALLS}
    # Bound to the exact leaves their owners print and own, Equipment's in the
    # accepted batch.
    rules = _view(service, built, RULES)
    activating = _view(service, built, ACTIVATING)
    categories = _view(service, built, "magic_items.magic_item_categories")
    equipment = _view(service, built, EQUIPMENT_RULES)
    owner = {
        e.span_id: (r, k)  # type: ignore[attr-defined]
        for r, k, e in [*rules, *activating, *categories, *equipment]
    }
    assert [owner[e.span_id] for _, _, e in read[:8]] == [  # type: ignore[attr-defined]
        *((EQUIPMENT_RULES, k) for _, k in GEN.ATTUNEMENT_RULES),
        ("magic_items.magic_item_categories", "wands"),
        (RULES, "magic_item_rules"),
        (ACTIVATING, "spells_cast_from_items"),
        (ACTIVATING, "charges"),
    ]
    # A command-word item carries the sound rule; one casting with its user's
    # own ability carries both Spells Cast paragraphs.
    broom = _view(service, built, "magic_items.broom_of_flying")
    assert [e.text for _, _, e in broom][:5] == [*attunement, GEN.COMMAND_WORD]  # type: ignore[attr-defined]
    assert "_Silence_" in GEN.COMMAND_WORD
    staff = [e.text for _, _, e in _view(service, built, "magic_items.staff_of_fire")]  # type: ignore[attr-defined]
    assert staff[4:8] == [
        GEN.CATEGORY_RULES["Staff"],
        GEN.PREREQUISITES,
        GEN.CAST_FROM_ITEMS,
        GEN.OWN_ABILITY,
    ]
    # A potion is drunk as a Bonus Action and consumed; a ring is worn.
    potion_name = next(n for n in GEN.ITEM_NAMES if GEN.category(n) == "Potion")
    potion = _view(service, built, GEN.item_key(potion_name))
    assert [e.text for _, _, e in potion][:2] == [  # type: ignore[attr-defined]
        GEN.CATEGORY_RULES["Potion"],
        GEN.CONSUMED,
    ]
    ring = _view(service, built, "magic_items.ring_of_protection")
    assert [e.text for _, _, e in ring][:5] == [*attunement, GEN.CATEGORY_RULES["Ring"]]  # type: ignore[attr-defined]
    # An item no general rule governs reads only itself.
    holding = _view(service, built, "magic_items.bag_of_holding")
    assert [e.text for _, _, e in holding] == _printed(A_Z, "Bag of Holding")  # type: ignore[attr-defined]
    # Every item read directly: its context, then itself (the Spell Scroll,
    # whose table prints an Equipment record's rows, below).
    for name in ("Mysterious Deck", "Manual of Golems"):
        texts = [e.text for _, _, e in _view(service, built, GEN.item_key(name))]  # type: ignore[attr-defined]
        own = [t for t in _printed(A_Z, name) if t not in STAT_BLOCK_LEAVES]
        assert texts == [*_context(name, attunement), *own], name


@pytest.mark.parametrize(
    ("name", "variant", "before", "after"),
    [
        ("Ioun Stone", "reserve", 17, 2),
        ("Figurine of Wondrous Power", "silver_raven", 17, 0),
    ],
)
def test_casting_context_governs_the_casting_variant_alone(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch, name, variant, before, after
) -> None:
    service = _service(persisted, built, monkeypatch)
    attunement = _attunement(service, built)
    item = GEN.item_key(name)
    read = _view(service, built, item)
    own = [t for t in _printed(A_Z, name) if t not in STAT_BLOCK_LEAVES]
    # One record, read whole in printed order: Spells Cast from Items sits
    # immediately ahead of the casting variant's leaves, and nowhere else.
    assert {r for r, _, _ in read} == {item}
    texts = [e.text for _, _, e in read]  # type: ignore[attr-defined]
    assert [t for t in texts if t in own] == own
    at = texts.index(GEN.CAST_FROM_ITEMS)
    assert texts.count(GEN.CAST_FROM_ITEMS) == 1
    cast = [k for _, k, e in read if e.text in own][before:]  # type: ignore[attr-defined]
    assert [k for _, k, _ in read][at] == variant
    assert cast[: len(cast) - after] == [variant] * (len(cast) - after)
    assert texts[at + 1 : at + 1 + len(cast) - after] == own[before : len(own) - after]
    assert texts == _read(name, attunement)
    # The item's other leaves carry no casting context; the variant carries
    # nothing but it.
    components = GEN.item_components(name)
    assert [k for k, _, _ in components][:2] == [GEN.slug(name), variant]
    assert all(
        GEN.CAST_FROM_ITEMS not in [t for t, _ in c]
        for k, _, c in components
        if k != variant
    )
    (only,) = [c for k, _, c in components if k == variant]
    assert [t for t, _ in only] == [GEN.CAST_FROM_ITEMS]
    # The variant's own words cast; no other variant's do.
    (words,) = [ts for k, ts, _ in components if k == variant]
    assert "cast" in " ".join(words)
    # Disabling the casting variant drops its leaves and its context only;
    # disabling the rule drops the rule and keeps every leaf.
    gone = _service(persisted, built, monkeypatch, _disable_component(item, variant))
    kept = [e.text for _, _, e in _view(gone, built, item)]  # type: ignore[attr-defined]
    assert kept == [t for t in texts if t not in (*words, GEN.CAST_FROM_ITEMS)]
    rule = _service(
        persisted,
        built,
        monkeypatch,
        _disable_component(ACTIVATING, "spells_cast_from_items"),
    )
    kept = [e.text for _, _, e in _view(rule, built, item)]  # type: ignore[attr-defined]
    assert kept == [t for t in texts if t != GEN.CAST_FROM_ITEMS]


def test_casting_context_follows_operative_meaning() -> None:
    # The Reserve casts its stored spells; the deck's Moon grants Wish later
    # and the card is gone; of the figurines, the Silver Raven casts.
    assert "Ioun Stone" in GEN.CASTING_ITEMS
    assert "you can cast any spell stored in it" in " ".join(
        _printed(A_Z, "Ioun Stone")
    )
    assert "Mysterious Deck" not in GEN.CASTING_ITEMS
    assert GEN.CAST_FROM_ITEMS not in [
        t for t, _ in GEN.item_context("Mysterious Deck")
    ]
    # Of the figurines only the Silver Raven casts, and of the stones only the
    # Reserve: the casting rule is theirs, as components of the one item.
    raven = GEN.item_components("Figurine of Wondrous Power")[1][1]
    assert raven[0].startswith("**Silver Raven") and "_Animal Messenger_" in raven[0]
    assert (
        " ".join(_printed(A_Z, "Figurine of Wondrous Power")).count(
            "_Animal Messenger_"
        )
        == 1
    )
    reserve = GEN.item_components("Ioun Stone")[1][1]
    assert reserve[0].startswith("_Reserve (Rare)._") and len(reserve) == 3
    assert set(GEN.CASTING_VARIANTS) == {"Figurine of Wondrous Power", "Ioun Stone"}
    # Every other item is one component.
    assert all(
        len(GEN.item_components(n)) == 1
        for n in GEN.ITEM_NAMES
        if n not in GEN.CASTING_VARIANTS
    )
    # Consumption: potions and the scroll by their category, two by their words.
    consumed = {
        n for n in GEN.ITEM_NAMES if GEN.CONSUMED in [t for t, _ in GEN.item_context(n)]
    }
    assert consumed == {
        n for n in GEN.ITEM_NAMES if GEN.category(n) in {"Potion", "Scroll"}
    } | {"Dust of Disappearance", "Manual of Golems"}
    # The attunement rules are read by exactly the items requiring attunement.
    assert len(GEN.CROSS_READS) == 140


def test_suppressing_a_governing_rule_suppresses_it_on_the_item(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    def disable(record: str, key: str) -> EffectiveOverrideEntry:
        return EffectiveOverrideEntry(
            override_id=f"disable-{key}",
            origin=OverrideOriginEnum.HOUSE_RULE,
            target=MechanicalTarget(
                kind=MechanicalTargetKind.COMPONENT,
                record_key=record,
                component_key=key,
            ),
            operation=OverrideOperationEnum.DISABLE,
            precedence=100,
            apply_order=0,
            is_enabled=True,
            payload={"patch": "disable"},
        )

    base = _service(persisted, built, monkeypatch)
    full = [e.text for _, _, e in _view(base, built, FIREBALLS)]  # type: ignore[attr-defined]
    attunement = _attunement(base, built)

    def without(*gone: str) -> list[str]:
        return [t for t in full if t not in gone]

    cast = disable(ACTIVATING, "spells_cast_from_items")
    service = _service(persisted, built, monkeypatch, cast)
    texts = [e.text for _, _, e in _view(service, built, FIREBALLS)]  # type: ignore[attr-defined]
    assert texts == without(GEN.CAST_FROM_ITEMS)
    # Replacing the owner's reading suppresses the printed passage too; the
    # replacement is the owner's, not carried to its readers.
    house = _replace(RULES, "magic_item_rules", "House attunement.")
    service = _service(persisted, built, monkeypatch, cast, house)
    texts = [e.text for _, _, e in _view(service, built, FIREBALLS)]  # type: ignore[attr-defined]
    assert texts == without(GEN.CAST_FROM_ITEMS, GEN.PREREQUISITES)
    # Disabling the owning section record does the same.
    service = _service(persisted, built, monkeypatch, _disable(RULES))
    texts = [e.text for _, _, e in _view(service, built, FIREBALLS)]  # type: ignore[attr-defined]
    assert texts == without(GEN.PREREQUISITES)
    # So does the accepted Equipment owner: disabled, or replaced.
    service = _service(
        persisted, built, monkeypatch, disable(EQUIPMENT_RULES, "attunement")
    )
    texts = [e.text for _, _, e in _view(service, built, FIREBALLS)]  # type: ignore[attr-defined]
    assert texts == without(attunement[0])
    house = _replace(EQUIPMENT_RULES, "ending_attunement", "House ending.")
    service = _service(persisted, built, monkeypatch, house)
    texts = [e.text for _, _, e in _view(service, built, FIREBALLS)]  # type: ignore[attr-defined]
    assert texts == without(attunement[3])
    owner = [
        e.text  # type: ignore[attr-defined]
        for _, k, e in _view(service, built, EQUIPMENT_RULES)
        if k == "ending_attunement"
    ]
    assert owner == ["House ending."]
    # The catalogue drops it too, and reads everything else as before.
    catalogue = [e.text for _, _, e in _view(service, built, CATALOGUE)]  # type: ignore[attr-defined]
    assert catalogue == [t for t in _catalogue(attunement) if t != attunement[3]]


def test_governing_context_is_read_once_by_its_owner_or_first_reader(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    attunement = _attunement(service, built)

    def reads(*records: str) -> list[tuple[str, str]]:
        return [(r, e.text) for r, _, e in _view(service, built, *records)]  # type: ignore[attr-defined]

    # The owner selected with a reader: the owner reads it, the reader not.
    for owner, owned in ((RULES, [GEN.PREREQUISITES]), (EQUIPMENT_RULES, attunement)):
        read = reads(owner, FIREBALLS)
        assert [r for r, t in read if t in owned] == [owner] * len(owned)
        assert [t for r, t in read if r == FIREBALLS] == [
            *(t for t in _context("Wand of Fireballs", attunement) if t not in owned),
            *_printed(A_Z, "Wand of Fireballs"),
        ]
    # Two readers selected together: each shared passage once, at the first.
    lightning = GEN.item_key("Wand of Lightning Bolts")
    spans = [e.span_id for _, _, e in _view(service, built, FIREBALLS, lightning)]  # type: ignore[attr-defined]
    assert len(spans) == len(set(spans))
    read = reads(FIREBALLS, lightning)
    assert [t for r, t in read if r == lightning] == _printed(
        A_Z, "Wand of Lightning Bolts"
    )
    # The catalogue carries what is owned outside it once; its owner selected
    # with it reads it instead, and the catalogue then does not.
    catalogue = [t for _, t in reads(CATALOGUE)]
    assert catalogue.count(GEN.PREREQUISITES) == 1
    both = reads(RULES, CATALOGUE)
    assert [r for r, t in both if t == GEN.PREREQUISITES] == [RULES]
    assert [t for r, t in both if r != RULES] == [
        t for t in catalogue if t not in _printed("Magic Item Rules")
    ]
    both = reads(EQUIPMENT_RULES, CATALOGUE)
    assert [r for r, t in both if t in attunement] == [EQUIPMENT_RULES] * 4


def test_a_stat_block_is_its_own_scoped_record(persisted, built, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _service(persisted, built, monkeypatch)
    fly = f"{FIGURINE}.giant_fly"
    figurine = _view(service, built, FIGURINE)
    assert fly not in {r for r, _, _ in figurine}
    assert [e.text for _, _, e in figurine] == _read(  # type: ignore[attr-defined]
        "Figurine of Wondrous Power", []
    )
    read = _view(service, built, fly)
    assert [e.text for _, _, e in read] == _printed(  # type: ignore[attr-defined]
        A_Z, "Figurine of Wondrous Power", "Giant Fly"
    )
    death = _view(service, built, f"{DECK}.avatar_of_death")
    assert [k for _, k, _ in death][-1] == "actions"
    assert death[0][2].text == "##### Avatar of Death"  # type: ignore[attr-defined]


def test_a_disabled_item_is_gone_from_the_catalogue(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    gone = "magic_items.vorpal_sword"
    service = _service(persisted, built, monkeypatch, _disable(gone))
    reached = _sliced(service, _request(built, CATALOGUE))
    assert gone not in reached and len(reached) == 258 + len(SHARED_KEYS)
    assert gone not in {r for r, _, _ in _view(service, built, CATALOGUE)}
    refused = service.rule_slice(_request(built, gone))
    assert refused.outcome is AuthorityOutcome.INVALID_REFERENCE


def _disable_component(record: str, key: str) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
        override_id=f"disable-{record}-{key}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=record,
            component_key=key,
        ),
        operation=OverrideOperationEnum.DISABLE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={"patch": "disable"},
    )


def _replace(record: str, key: str, text: str) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
        override_id=f"replace-{key}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=record,
            component_key=key,
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
                "authored_prose": text,
            },
        },
    )


def test_a_replaced_item_reads_replaced_in_the_catalogue(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    item = "magic_items.sending_stones"
    printed = _view(_service(persisted, built, monkeypatch), built, CATALOGUE)
    house = _replace(item, "sending_stones", "House stones.")
    after = _view(_service(persisted, built, monkeypatch, house), built, CATALOGUE)
    assert [x for x in after if x[0] != item] == [x for x in printed if x[0] != item]
    (replaced,) = [e for r, _, e in after if r == item]
    assert isinstance(replaced, AuthoredProse) and replaced.text == "House stones."
    records = list(dict.fromkeys(r for r, _, _ in after))
    assert records == list(dict.fromkeys(r for r, _, _ in printed))


def test_the_read_into_sections_read_in_printed_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    assert _sliced(service, _request(built, CRAFTING)) == [CRAFTING]
    crafting = _view(service, built, CRAFTING)
    assert [e.text for _, _, e in crafting] == [  # type: ignore[attr-defined]
        *_printed("Crafting Magic Items"),
        *_printed("Time and Cost"),
    ]
    sentient = _view(service, built, SENTIENT)
    assert [e.text for _, _, e in sentient] == [  # type: ignore[attr-defined]
        *_printed("Sentient Magic Items"),
        *_printed("Sentient Magic Item Traits"),
        *_printed("Special Purpose"),
    ]
    # A floated table is selected alone, and replaced in place.
    alone = service.gamemaster_view(
        _request(built, components=((SENTIENT, "sentient_items_senses"),))
    )
    assert alone.outcome is AuthorityOutcome.RESOLVED, alone.detail
    assert alone.gamemaster_view is not None
    assert [
        e.text for c in alone.gamemaster_view.components for e in c.governing_prose
    ] == _texts(built, SENTIENT, "sentient_items_senses")
    house = _replace(SENTIENT, "sentient_items_senses", "House senses.")
    after = _view(_service(persisted, built, monkeypatch, house), built, SENTIENT)
    assert [x for x in after if x[1] != "sentient_items_senses"] == [
        x for x in sentient if x[1] != "sentient_items_senses"
    ]
    keys = list(dict.fromkeys(k for _, k, _ in after))
    assert keys == list(dict.fromkeys(k for _, k, _ in sentient))


# ---------------------------------------------------------------------------
# One item in two catalogues (Owner Decision 2026-09-27)
# ---------------------------------------------------------------------------


def _roles(b: Built, record: str, key: str) -> dict[str, ProvenanceRole]:
    """Text -> the role one component's prose bindings claim it by, of this
    batch's spans."""
    spans = {s.span_id: s for s in b.ledger.spans}
    return {
        b.leaf_rows[spans[c.span_id].leaf_id].content[
            spans[c.span_id].char_start : spans[c.span_id].char_end
        ]: c.role
        for c in b.proposal.proposed_representation.provenance
        if c.target_kind is ProvenanceTargetKind.PROSE_BINDING
        and c.target_key[:2] == (record, key)
        and c.span_id in spans
    }


@pytest.mark.parametrize(("name", "record", "key"), SHARED)
def test_an_item_equipment_sells_is_one_record_in_both_catalogues(  # type: ignore[no-untyped-def]
    built, name, record, key
) -> None:
    rep = built.proposal.proposed_representation
    family = GEN.item_key(name)
    head, rows = GEN.shared_rows(name)
    # The record and edge expectations are the current accepted authority's,
    # as the packet is cut from the current release.
    accepted_rep = current().oracle.representation
    accepted = {r.semantic_key: r for r in accepted_rep.records}
    (mine,) = [r for r in rep.records if r.semantic_key == record]
    # The accepted record, unchanged, gaining one component: the family
    # table's rows it prints, read with the table's head.
    assert mine == accepted[record] and mine.kind is RecordKind.EQUIPMENT
    assert [c.semantic_key for c in rep.components if c.record_key == record] == [
        GEN.SHARED_COMPONENT
    ]
    # Its rows, read with what governs them: the family's rules, its type
    # line and rule paragraphs, and the table's head and close -- all context.
    shared = list(GEN.shared_texts(name))
    closer = GEN.shared_closer(name)
    assert sorted(_texts(built, record, GEN.SHARED_COMPONENT)) == sorted(shared)
    assert _roles(built, record, GEN.SHARED_COMPONENT) == {
        **dict.fromkeys(shared, ProvenanceRole.CONTEXTUAL),
        **dict.fromkeys(rows, ProvenanceRole.PRIMARY),
    }
    rules = [t for t, _ in GEN.item_context(name)]
    printed = _printed(A_Z, name)
    assert shared[: len(rules)] == rules and rules
    assert shared[len(rules) :] == [
        p
        for t in printed
        for p in ((head, *rows, closer) if t.startswith("<table>") else (t,))
        if p in shared
    ]
    # The table read directly is whole: its head opens it, its close ends it.
    table = "".join(t for t in shared if t.startswith(("<table>", "    <tr>", "  </")))
    assert table.startswith("<table>") and table.endswith("</table>")
    assert table.count("<tbody>") == table.count("</tbody>") == 1
    assert table.count("<tr>") == table.count("</tr>")
    # What it leaves out is the family's description, not a rule.
    left = [
        t for t in printed if t not in shared and not t.startswith(("#", "<table>"))
    ]
    assert left == (
        ["Whatever its potency, the potion's red liquid glimmers when agitated."]
        if record == SHARED_KEYS[0]
        else []
    )
    # A member of each catalogue, by one edge each: accepted, both edges.
    assert [
        (r.kind, r.target_record_key)
        for r in accepted_rep.relationships
        if r.source_record_key == record
    ] == [
        (RelationshipKind.CATALOGUE_MEMBER, GEAR),
        (RelationshipKind.CATALOGUE_MEMBER, family),
    ]
    assert [
        (r.kind, r.target_record_key)
        for r in rep.relationships
        if r.source_record_key == record
    ] == [(RelationshipKind.CATALOGUE_MEMBER, family)]
    # The family keeps its head, its wider variants and its rules; the shared
    # rows it reads in place, as their owner's.
    roles = _roles(built, family, GEN.slug(name))
    (tbl,) = [t for t in _printed(A_Z, name) if t.startswith("<table>")]
    pieces = GEN.cut(tbl, head, *rows, closer)
    assert "".join(pieces) == tbl and pieces[-1] == closer
    rest = [t for t in pieces if t not in (head, *rows)]
    assert {roles[t] for t in (head, *rest)} == {ProvenanceRole.PRIMARY}
    assert {roles[t] for t in rows} == {ProvenanceRole.CONTEXTUAL}
    assert {roles[t] for t in shared if t in printed} == {ProvenanceRole.PRIMARY}
    assert ("(greater)" if record == SHARED_KEYS[0] else "<td>9</td>") in "".join(rest)


def _parts_findings(candidate: ProjectionCandidate, **changes: Any) -> list[str]:
    return catalogue_parts(dataclasses.replace(candidate.representation, **changes))[1]


def test_membership_in_two_catalogues_is_declared_never_guessed(  # type: ignore[no-untyped-def]
    recorded, prior
) -> None:
    candidate = candidate_from_accepted_inputs(_accepted(prior, recorded))
    assert isinstance(candidate, ProjectionCandidate)
    rep = candidate.representation
    assert catalogue_parts(rep) == (
        {
            **{(record, GEAR): frozenset({key}) for _, record, key in SHARED},
            **{
                (record, GEN.item_key(name)): frozenset({GEN.SHARED_COMPONENT})
                for name, record, _ in SHARED
            },
        },
        [],
    )
    name, record, key = SHARED[0]
    family = GEN.item_key(name)

    def edge(section: str) -> tuple[str, ...]:
        return relationship_target_key(
            RelationshipDraft(record, section, RelationshipKind.CATALOGUE_MEMBER)
        )

    none = (
        f"record {record}: component {GEN.SHARED_COMPONENT} is printed by none "
        f"of its catalogues {sorted([GEAR, family])}"
    )
    cites = (
        f"record {record}: its catalogue edge to {family} cites no span of its "
        "own components"
    )
    # An edge citing nothing is refused, not placed by guess.
    kept = tuple(c for c in rep.provenance if c.target_key != edge(family))
    assert _parts_findings(candidate, provenance=kept) == [cites, none]
    # Nor one citing a span another record owns: the family's own head.
    (claim,) = [c for c in rep.provenance if c.target_key == edge(family)]
    head = next(
        c.span_id
        for c in rep.provenance
        if c.target_kind is ProvenanceTargetKind.PROSE_BINDING
        and c.target_key[:2] == (family, GEN.slug(name))
        and c.role is ProvenanceRole.PRIMARY
    )

    def citing(span: str) -> tuple[object, ...]:
        return tuple(
            dataclasses.replace(c, span_id=span) if c == claim else c
            for c in rep.provenance
        )

    assert _parts_findings(candidate, provenance=citing(head)) == [cites, none]
    # One component printed by both catalogues, the other by none.
    gear_span = next(c.span_id for c in rep.provenance if c.target_key == edge(GEAR))
    assert _parts_findings(candidate, provenance=citing(gear_span)) == [
        f"record {record}: component {key} is printed by both {GEAR} and {family}",
        none,
    ]
    # A family made its member's member is a cycle.
    cycle = (
        *rep.relationships,
        RelationshipDraft(family, record, RelationshipKind.CATALOGUE_MEMBER),
    )
    assert {
        f"record {family}: a catalogue member of itself",
        f"record {record}: a catalogue member of itself",
    } <= set(_parts_findings(candidate, relationships=cycle))


def test_a_shared_item_is_placed_only_where_review_found_it_printed(  # type: ignore[no-untyped-def]
    recorded, prior
) -> None:
    """Its edges' own-span check says which components each catalogue prints,
    not that the catalogue prints them: an edge moved to an unrelated section
    or class feature, citing the same span, is refused by the review
    inventory. (The gate's refusal judged the superseded release's composition
    against a corpus not rebuilt; that check is retired.)"""
    candidate = candidate_from_accepted_inputs(_accepted(prior, recorded))
    assert isinstance(candidate, ProjectionCandidate)
    rep = candidate.representation
    ledger = candidate.classification

    def placement(changed: ProjectionCandidate) -> list[str]:
        return [
            f
            for f in review_unit_violations(
                changed.review_units,
                changed.representation,
                ledger.policy_version,
                ledger.spans,
            )
            if "catalogue edge" in f
        ]

    assert placement(candidate) == []
    name, record, _ = SHARED[0]
    family = GEN.item_key(name)
    feature = next(
        r.semantic_key for r in rep.records if r.kind is RecordKind.CLASS_FEATURE
    )

    def moved(old: str, new: str) -> ProjectionCandidate:
        was = RelationshipDraft(record, old, RelationshipKind.CATALOGUE_MEMBER)
        now = RelationshipDraft(record, new, RelationshipKind.CATALOGUE_MEMBER)
        return dataclasses.replace(
            candidate,
            representation=dataclasses.replace(
                rep,
                relationships=tuple(now if r == was else r for r in rep.relationships),
                provenance=tuple(
                    (
                        dataclasses.replace(c, target_key=relationship_target_key(now))
                        if c.target_key == relationship_target_key(was)
                        else c
                    )
                    for c in rep.provenance
                ),
            ),
        )

    for old, new in [
        (family, CRAFTING),
        (family, GEN.item_key(SHARED[1][0])),
        (family, feature),
        (GEAR, feature),
    ]:
        changed = moved(old, new)
        refused = (
            f"record {record}: its catalogue edge to {new} cites a span no review "
            f"unit found {new} printing"
        )
        assert placement(changed) == [refused], (old, new)


def _texts_of(service, built, *records: str) -> list[tuple[str, str, str]]:  # type: ignore[no-untyped-def]
    return [(r, k, e.text) for r, k, e in _view(service, built, *records)]  # type: ignore[attr-defined]


def _gear_tail(
    house: str | None = None, without: str | None = None
) -> list[tuple[str, str, str]]:
    """What *Equipment* reads after its own reading: each shared record's
    family rows with what governs them, in the order it prints the records,
    rules read once; *house*'s rows replaced, *without*'s disabled. (The two
    tables' closes print the same text at different places, so each is read.)"""
    out: list[tuple[str, str, str]] = []
    for n, r, _ in SHARED:
        if r == without:
            continue
        texts = ["House rows."] if r == house else GEN.shared_texts(n)
        seen = {t for _, _, t in out} & set(_rules(n))
        out += [(r, GEN.SHARED_COMPONENT, t) for t in texts if t not in seen]
    return out


def _rules(name: str) -> list[str]:
    return [t for t, _ in GEN.item_context(name)]


@pytest.mark.parametrize(("name", "record", "key"), SHARED)
def test_each_catalogue_reads_the_shared_item_once_in_printed_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch, name, record, key
) -> None:
    service = _service(persisted, built, monkeypatch)
    attunement = _attunement(service, built)
    family = GEN.item_key(name)
    head, rows = GEN.shared_rows(name)
    table = GEN.SHARED_COMPONENT
    shared = list(GEN.shared_texts(name))
    # Directly: the accepted component, then the family's rows read with what
    # governs them -- its rules, type line and rule paragraphs -- and the
    # table whole, head to close.
    direct = _texts_of(service, built, record)
    own = [t for _, k, t in direct if k == key]
    assert [(k, t) for _, k, t in direct] == [
        *((key, t) for t in own),
        *((table, t) for t in shared),
    ]
    assert own and not set(own) & set(_printed(A_Z))
    rendered = "".join(t for _, k, t in direct if k == table and t[:1] in "< ")
    assert rendered.startswith("<table>") and rendered.endswith("</table>")
    assert rendered.count("<tr>") == rendered.count("</tr>") == 1 + len(rows)
    # The family reaches its member; Equipment does not reach the family.
    assert _sliced(service, _request(built, family)) == [family, record]
    assert family not in _sliced(service, _request(built, GEAR))
    # The family: its context, then its passages in printed order, the shared
    # rows the Equipment record's; then the rest of that record, once.
    fam = _texts_of(service, built, family)
    read = _read(name, attunement)
    assert [t for _, _, t in fam] == [*read, *own]
    assert [(r, k) for r, k, t in fam if t in rows] == [(record, table)] * len(rows)
    assert {(r, k) for r, k, t in fam[: len(read)] if t not in rows} == {
        (family, GEN.slug(name))
    }
    assert {(r, k) for r, k, _ in fam[len(read) :]} == {(record, key)}
    assert _texts_of(service, built, record, family) == fam
    # Equipment: its reading, then -- after it, in the order it prints the
    # records -- what of each shared record it does not print: its family rows
    # with what governs them, context read once.
    gear = _texts_of(service, built, GEAR)
    tail = _gear_tail()
    before = gear[: len(gear) - len(tail)]
    assert gear == [*before, *tail]
    assert not {t for _, _, t in before} & set(_printed(A_Z))
    assert {k for r, k, _ in before if r == record} == {key}
    # Both catalogues: each reads what it prints, nothing twice.
    ((other_name, other),) = [(n, r) for n, r, _ in SHARED if r != record]
    other_tail = [(other, table, t) for t in GEN.shared_texts(other_name)]
    read_first = {t for _, _, t in other_tail} & set(_rules(name))
    both = _view(service, built, GEAR, family)
    assert [(r, k, e.text) for r, k, e in both] == [  # type: ignore[attr-defined]
        *before,
        *other_tail,
        *(x for x in fam[: len(read)] if x[2] not in read_first),
    ]
    spans = [e.span_id for _, _, e in both]  # type: ignore[attr-defined]
    assert len(spans) == len(set(spans))
    # Magic Items A-Z reads the family as the family does: the rows are the
    # record's, where the family prints them, and nothing else of it.
    az = _texts_of(service, built, CATALOGUE)
    assert [x for x in az if x[0] == record] == [(record, table, t) for t in rows]
    texts = [t for _, _, t in az]
    at = texts.index(head)
    assert texts[at : at + len(rows) + 1] == [head, *rows]
    assert texts == _catalogue(attunement)
    sliced = service.rule_slice(_request(built, CATALOGUE))
    assert sliced.outcome is AuthorityOutcome.RESOLVED and sliced.slice is not None
    assert {
        r.semantic_key: [c.semantic_key for c in r.components]
        for r in sliced.slice.records
        if r.semantic_key in SHARED_KEYS
    } == dict.fromkeys(SHARED_KEYS, [table])


@pytest.mark.parametrize(("name", "record", "key"), SHARED)
def test_overrides_of_the_shared_item_hold_from_either_catalogue(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch, name, record, key
) -> None:
    base = _service(persisted, built, monkeypatch)
    attunement = _attunement(base, built)
    family = GEN.item_key(name)
    head, rows = GEN.shared_rows(name)
    table = GEN.SHARED_COMPONENT
    shared = list(GEN.shared_texts(name))
    rules = _rules(name)
    read = _read(name, attunement)
    own = [t for _, k, t in _texts_of(base, built, record) if k == key]
    gear = _texts_of(base, built, GEAR)
    before = gear[: len(gear) - len(_gear_tail())]
    az = [t for _, _, t in _texts_of(base, built, CATALOGUE)]

    def texts(*entries: EffectiveOverrideEntry, of: str) -> list[str]:
        service = _service(persisted, built, monkeypatch, *entries)
        return [t for _, _, t in _texts_of(service, built, of)]

    def refused(entry: EffectiveOverrideEntry, of: str) -> bool:
        service = _service(persisted, built, monkeypatch, entry)
        return (
            service.rule_slice(_request(built, of)).outcome
            is AuthorityOutcome.INVALID_REFERENCE
        )

    # The record disabled: gone from both catalogues, its rows with it; every
    # other variant row and rule stays.
    gone = _disable(record)
    assert texts(gone, of=family) == [t for t in read if t not in rows]
    assert texts(gone, of=CATALOGUE) == [t for t in az if t not in rows]
    assert refused(gone, record)
    service = _service(persisted, built, monkeypatch, gone)
    assert record not in {r for r, _, _ in _texts_of(service, built, GEAR)}
    # Its family rows disabled: gone from the family, A-Z and the Equipment
    # read; the rest of the record stays.
    gone = _disable_component(record, table)
    assert texts(gone, of=family) == [*(t for t in read if t not in rows), *own]
    assert texts(gone, of=CATALOGUE) == [t for t in az if t not in rows]
    assert texts(gone, of=record) == own
    service = _service(persisted, built, monkeypatch, gone)
    assert _texts_of(service, built, GEAR) == [*before, *_gear_tail(without=record)]
    # Its Equipment component disabled: the family and A-Z read as before.
    gone = _disable_component(record, key)
    assert texts(gone, of=family) == read
    assert texts(gone, of=record) == shared
    assert texts(gone, of=CATALOGUE) == az
    # Its family rows replaced: every catalogue printing them reads the
    # replacement where the rows were printed -- the family, A-Z, Equipment
    # and both at once -- once, as the record's; the other variants stay.
    house = _replace(record, table, "House rows.")

    def replaced(printed: list[str]) -> list[str]:
        at = printed.index(rows[0])
        return [*printed[:at], "House rows.", *printed[at + len(rows) :]]

    service = _service(persisted, built, monkeypatch, house)
    fam = _view(service, built, family)
    assert [e.text for _, _, e in fam] == [*replaced(read), *own]  # type: ignore[attr-defined]
    (authored,) = [e for r, k, e in fam if (r, k) == (record, table)]
    assert isinstance(authored, AuthoredProse)
    catalogue = _texts_of(service, built, CATALOGUE)
    assert [t for _, _, t in catalogue] == replaced(az)
    assert [x for x in catalogue if x[0] == record] == [(record, table, "House rows.")]
    assert texts(house, of=record) == [*own, "House rows."]
    assert _texts_of(service, built, GEAR) == [*before, *_gear_tail(house=record)]
    both = [t for _, _, t in _texts_of(service, built, GEAR, family)]
    assert both.count("House rows.") == 1 and not set(rows) & set(both)
    # An unrelated variant replaced leaves the shared rows as they are.
    (other,) = [n for n, _, _ in SHARED if n != name]
    elsewhere = _replace(GEN.item_key(other), GEN.slug(other), "House family.")
    assert texts(elsewhere, of=record) == [*own, *shared]
    # The family disabled: its head, close and rule paragraphs go with it; the
    # record keeps its rows and the rules governing them.
    gone = _disable(family)
    assert refused(gone, family)
    assert texts(gone, of=record) == [*own, *rules, *rows]
    # Its reading replaced does the same: the replacement is the family's.
    gone = _replace(family, GEN.slug(name), "House family.")
    assert texts(gone, of=record) == [*own, *rules, *rows]
    # A rule governing the family, disabled at its owner, leaves the family
    # read and the record's rows without it, and nothing else.
    rule = GEN.CATEGORY_RULES[GEN.category(name)]
    assert rule in read and rule in shared
    gone = _disable_component(
        "magic_items.magic_item_categories", f"{GEN.category(name).lower()}s"
    )
    assert texts(gone, of=family) == [*(t for t in read if t != rule), *own]
    assert texts(gone, of=record) == [*own, *(t for t in shared if t != rule)]
