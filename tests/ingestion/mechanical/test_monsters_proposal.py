"""The ``monsters`` proposal, offered for review -- CRD Issue 5d.

The *Monsters* general rules and the *Monsters A-Z* catalogue below their part
headings, pp254-344, proposed by
``.claude/review-notes/issue-5d-monsters-generator.py`` from the release 5c
actually publishes, with its resolution drafts. The Owner accepted both, over
the twenty-batch replacement chain, and
``issue-5d-monsters-corrections-ACCEPT.py`` recorded them.

What is pinned, and why:

* the committed artifact is the recorded proposal for the Monsters-corrected
  (now superseded) release, by shape, and the drafts are what the generator
  drafts over the twenty-batch replacement chain on that release
  (``issue-5d-monsters-corrections-REPLACEMENT.py``), as the Owner's acceptance
  recorded it; the generator builds over the current release (that it no
  longer derives the recorded bytes is retired, see
  ``.claude/review-notes/issue-5c-release-readiness/correction-followup.md``);
* the committed oracle records exactly that acceptance: the chain kept whole,
  then the packet and its drafts under the Owner's decision and times;
* the reviewed corrections: the Succubus prints AC and Initiative before HP and
  Speed, the *Veteran Warrior* is one stat block, the Young White Dragon's INT
  save is −2;
* grain: two rule records, 177 group records reading their headings and 235
  creature records as members of their group, one prose component per printed
  container, every leaf of both parts claimed once;
* references name exact accepted or packet records or stay unresolved, and the
  batch checks report only those;
* the recorded proposal, composed in memory over the replacement chain (both
  the superseded release's): it accepts, then the drafts resolve; every
  accepted byte is preserved and exactly the parts' leaves gain coverage.
  Judging that composition, or the committed oracle, against a corpus needs
  the superseded release's, which is not rebuilt; those checks are retired;
* through the production rules-authority service, over the current accepted
  authority persisted as one draft into the current release: a
  creature reads its printed containers in order, each preceded by the exact
  *Parts of a Stat Block* rules governing it not yet read (the release prints
  the rules first, and a read follows printed order); a group reaches its creatures in
  printed order; an override of a governing rule's owner suppresses it on the
  creature;
* in the source's own words: alignment as a default suggestion, the *Running
  a Monster* combat rules, class-tag Attunement, carried ammunition, the
  Languages rule for "Understands", and spellcasting exactly where a stat
  block casts -- each suppressed with its owner and read once when selected
  together; plain-named spell dependencies and plural pointers to the stat
  blocks their sources name.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

from afterworlds.ingestion.mechanical.acceptance import (
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
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
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import RecordKind
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from tests.ingestion.mechanical._replacement_chain import (
    COMMITTED_SHA256,
    EQUIPMENT_CITED,
    animals_recorded,
    current,
    equipment_recorded,
    monsters_recorded,
)
from tests.ingestion.mechanical._replacement_chain import REPLACEMENT as RECORDING
from tests.ingestion.mechanical._schema_pins import lifted
from tests.ingestion.mechanical.test_character_origins_feats_proposal import (
    _request,
    _service,
    _sliced,
)
from tests.ingestion.mechanical.test_magic_items_proposal import _disable_component

REPO = Path(__file__).resolve().parents[3]
NOTES = REPO / ".claude" / "review-notes"
ORACLES = REPO / "src/afterworlds/ingestion/mechanical/oracles"
MONSTERS = "srd-5.2.1/monsters"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load("monsters_generator", NOTES / "issue-5d-monsters-generator.py")
PROPOSAL = NOTES / GEN.PROPOSAL_FILE
DRAFTS = NOTES / GEN.DRAFTS_FILE
IDENTITY = "0fd9e1698985748b81499def620a37b89c52a6b8cdc5a4ead69a1b57911239df"
PROPOSAL_SHA256 = "cdf06f4307bd09786f73cc16e4cf75c6609595c9a041ef4d1f47c9dbcf9a4336"
DRAFTS_SHA256 = "1733d78c91f56092b163732e0fc354cf5d21e6fd907f32fe33f7c440f74dc792"
REPLACEMENT = _load(
    "monsters_corrections_replacement",
    NOTES / "issue-5d-monsters-corrections-REPLACEMENT.py",
)
PARTS = "monsters.parts_of_a_stat_block"
ABOLETH = "monsters.aboleth.aboleth"
DRAGONS = "monsters.red_dragons"


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
    """The replacement chain this packet composed over, at its recorded bytes."""
    inputs: AcceptedInputs = GEN.current()
    assert hashlib.sha256(serialize_accepted_inputs(inputs)).hexdigest() == (
        RECORDING.RECORDED_SHA256["chain"]
    )
    assert inputs.oracle.binding.package_uuid == REPLACEMENT.RELEASE[0]
    return inputs


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


def _printed(*path: str) -> list[str]:
    return [t for p, t in GEN.LEAVES if p[: len(path)] == path]


def _refs(b: Built) -> set[tuple[str, str, str, str, str]]:
    return {
        (
            r.from_record_key,
            r.from_component_key,
            r.source_text,
            r.scope_key,
            r.target_record_key,
        )
        for r in b.proposal.proposed_representation.references
    }


# ---------------------------------------------------------------------------
# The artifacts
# ---------------------------------------------------------------------------


def test_the_committed_artifact_is_the_recorded_proposal_by_shape(  # type: ignore[no-untyped-def]
    built, recorded, prior
) -> None:
    data = PROPOSAL.read_bytes()
    assert hashlib.sha256(data).hexdigest() == PROPOSAL_SHA256
    assert b"\r" not in data
    # The generator builds over the current release.
    assert built.binding == current().oracle.binding
    # The recorded proposal and its drafts bind the recorded chain's release.
    assert recorded.binding == prior.oracle.binding
    drafts = GEN.draft_resolutions(prior.oracle.binding, prior=prior)
    assert list(reference_resolution_payload(drafts)) == json.loads(DRAFTS.read_bytes())
    assert hashlib.sha256(DRAFTS.read_bytes()).hexdigest() == DRAFTS_SHA256


UNDEAD = ("spells.create_undead", "using_a_higher_level_spell_slot")
BUDGET = ("gameplay_toolbox.combat_encounters", "step_3_spend_your_budget")
#: The plurals the accepted sources print, to the stat blocks they name.
PLURALS = {
    (*UNDEAD, "Ghasts"): "monsters.ghast.ghast",
    (*UNDEAD, "Ghouls"): "monsters.ghoul.ghoul",
    (*UNDEAD, "Mummies"): "monsters.mummies.mummy",
    (*UNDEAD, "Wights"): "monsters.wight.wight",
    (*BUDGET, "Skeletons"): "monsters.skeletons.skeleton",
    (*BUDGET, "Druids"): "monsters.druid.druid",
    (*BUDGET, "Adult Red Dragons"): "monsters.red_dragons.adult_red_dragon",
    (*BUDGET, "Fire Giants"): "monsters.fire_giant.fire_giant",
    (*BUDGET, "Stirges"): "monsters.stirge.stirge",
    (
        "magic_items.bag_of_beans",
        "bag_of_beans",
        "Shrieker Fungi",
    ): "monsters.fungi.shrieker_fungus",
}


def test_each_draft_names_the_one_stat_block_its_text_prints(prior) -> None:  # type: ignore[no-untyped-def]
    drafts, left = GEN.draft_targets(prior)
    assert (len(drafts), len(left)) == (83, 78)
    plural = {
        (r, c, text): target
        for r, c, text, target, _ in drafts
        if text not in GEN.BLOCK_KEY
    }
    assert plural == PLURALS
    for _, _, text, target, spans in drafts:
        assert spans and (text not in GEN.BLOCK_KEY or GEN.BLOCK_KEY[text] == target)
    # Every one left is no single stat block's printed name; a plural an
    # *Animals* stat block prints stays unresolved.
    texts = {text for _, _, text in left}
    assert not texts & set(GEN.BLOCK_KEY)
    assert {"Giant Rats", "Giant Wasps", "Mastiffs"} <= texts
    # The Owner's *Veteran Warrior*: the Deck of Illusions pointer now names it.
    assert [(r, t) for r, _, text, t, _ in drafts if text == "Veteran Warrior"] == [
        ("magic_items.deck_of_illusions", "monsters.warriors.veteran_warrior")
    ]
    assert Counter(text for _, _, text in left)["Monsters"] == 17


# ---------------------------------------------------------------------------
# Grain
# ---------------------------------------------------------------------------


def test_the_records_are_two_rules_the_groups_and_their_creatures(built) -> None:  # type: ignore[no-untyped-def]
    rep = built.proposal.proposed_representation
    kinds = Counter(r.kind for r in rep.records)
    assert kinds == {RecordKind.GENERAL_RULE: 2 + 177, RecordKind.CREATURE: 235}
    assert len(built.ledger.spans) == len(GEN.LEAVES) == 3139
    assert {c.handling for c in rep.components} == {ComponentHandling.PROSE_BOUND}
    # A creature's components are its own leaves, then each printed container.
    aboleth = [c.semantic_key for c in rep.components if c.record_key == ABOLETH]
    assert aboleth == ["aboleth", "traits", "actions", "legendary_actions"]
    parts = [c.semantic_key for c in rep.components if c.record_key == PARTS]
    assert parts[parts.index("resistances_and_vulnerabilities") + 1] == (
        "running_a_monster"
    )


SUCCUBUS = ("Succubus", "Succubus")
VETERAN = ("Warriors", "Veteran Warrior")
YOUNG_WHITE = ("White Dragons", "Young White Dragon")


def test_the_release_carries_the_reviewed_corrections(built) -> None:  # type: ignore[no-untyped-def]
    # The qualified texts are the release's leaves in its order and, like the
    # PDF, it prints the general rules before the catalogue.
    rows = sorted(built.leaf_rows.values(), key=lambda r: r.occurrence_index)
    assert [r.content for r in rows] == [t for _, t in GEN.LEAVES]
    parts = [p[0] for p, _ in GEN.LEAVES]
    assert parts == sorted(parts, key=[GEN.RULES, GEN.A_Z].index)
    # The Succubus prints AC and Initiative on one line, before HP and Speed.
    succubus = _printed(GEN.A_Z, *SUCCUBUS)
    assert next(t for t in succubus if t.startswith("**AC**")).startswith(
        "**AC** 15 **Initiative** +3 (13) <br>\n**HP** 71 (13d8 + 13) <br>\n"
        "**Speed** 30 ft., Fly 60 ft."
    )
    assert not [t for t in succubus if t.startswith("**Initiative**")]
    # One Veteran Warrior: one heading, one creature record, no other name.
    assert not [
        p for p, t in GEN.LEAVES if "Warrior Veteran" in t or "Warrior Veteran" in p
    ]
    assert _printed(GEN.A_Z, "Warriors").count("### Veteran Warrior") == 1
    rep = built.proposal.proposed_representation
    assert [r.semantic_key for r in rep.records if "veteran" in r.semantic_key] == [
        "monsters.warriors.veteran_warrior"
    ]
    assert GEN.BLOCK_KEY["Veteran Warrior"] == "monsters.warriors.veteran_warrior"
    # The Young White Dragon's INT: score 6, modifier −2, save −2.
    (table,) = [t for t in _printed(GEN.A_Z, *YOUNG_WHITE) if t.startswith("<table>")]
    assert "<td>6</td>\n      <td>−2</td>\n      <td>−2</td>" in table


def test_references_name_exact_records_or_stay_unresolved(built) -> None:  # type: ignore[no-untyped-def]
    refs = _refs(built)
    incubus = "monsters.incubus.incubus"
    assert (
        incubus,
        "traits",
        "Succubus",
        MONSTERS,
        "monsters.succubus.succubus",
    ) in refs
    # A creature naming itself is no reference.
    assert not {r for r in refs if r[0] == r[4]}
    mage = "monsters.mages.mage"
    assert (mage, "actions", "Fireball", "srd-5.2.1/spells", "spells.fireball") in refs
    druid = "monsters.druid.druid"
    assert (
        druid,
        "actions",
        "Long-strider",
        "srd-5.2.1/spells",
        "spells.longstrider",
    ) in refs
    gear = {(r[2], r[4]) for r in refs if r[3] == "srd-5.2.1/equipment"}
    assert ("Daggers", "equipment.weapons.dagger") in gear and ("Battleaxe", "") in gear
    # Spells a stat block depends on by the plain names it prints.
    spells = "srd-5.2.1/spells"
    storm = GEN.BLOCK_KEY["Storm Giant"]
    for name, key in (
        ("Detect Magic", "spells.detect_magic"),
        ("Light", "spells.light"),
        ("Control Weather", "spells.control_weather"),
    ):
        assert (storm, "actions", name, spells, key) in refs
    assert (
        GEN.BLOCK_KEY["Succubus"],
        "actions",
        "Dominate Person",
        spells,
        "spells.dominate_person",
    ) in refs
    tarrasque = GEN.BLOCK_KEY["Tarrasque"]
    assert (
        tarrasque,
        "traits",
        "Magic Missile",
        spells,
        "spells.magic_missile",
    ) in refs
    # Not a spell: a Light Crossbow, Bright Light, the Nalfeshnee's own
    # Teleport, a Fly speed.
    for block, component in (
        ("Assassin", "actions"),
        ("Azer Sentinel", "traits"),
        ("Nalfeshnee", "reactions"),
        ("Pegasus", "pegasus"),
    ):
        assert not {
            r
            for r in refs
            if r[:2] == (GEN.BLOCK_KEY[block], component) and r[3] == spells
        }, block
    pointer = {(r[1], r[2], r[4]) for r in refs if r[0] == PARTS}
    assert ("telepathy", "Rules Glossary", "glossary.telepathy") in pointer
    assert ("gear", "Equipment", "") in pointer
    # The generic equipping leaf points at the whole chapter; the Attunement
    # leaf, its own component, at the Magic Items rule.
    assert ("equipping_a_monster_with_other_items", "Equipment", "") in pointer
    assert (
        "magic_items_and_class_tags",
        "Equipment",
        "equipment.magic_items",
    ) in pointer


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings(
        GEN.MONSTERS_CHUNK
    )


# ---------------------------------------------------------------------------
# Test-only composition with the replacement chain
# ---------------------------------------------------------------------------


def _accepted(prior: AcceptedInputs, proposal: MechanicalProposal) -> AcceptedInputs:
    return accept_proposal(
        proposal,
        batch_id="monsters",
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


def test_accepted_then_resolved_in_memory_preserves_everything(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    on_disk = {p.name: p.read_bytes() for p in ORACLES.iterdir()}
    base = prior.oracle
    assert (
        len(prior.batches),
        len(base.representation.records),
        len(base.spans),
        len(base.review_units),
        len(base.reference_resolutions),
    ) == (20, 1250, 6450, 950, 1099)
    # Both sides are the superseded release's: the recorded chain and proposal.
    assert recorded.binding == base.binding
    refs_before = _references(prior)
    assert len(refs_before) == 315

    drafts = GEN.draft_resolutions(base.binding, prior=prior)
    resolved = resolve_references(
        _accepted(prior, recorded),
        resolutions=drafts,
        authorized_by="test",
        authorization_reference="test-only",
        reviewer="test",
        resolved_at="2026-09-27T00:00:01Z",
    )
    final = resolved.oracle
    # Append-only: every accepted byte the authority holds is still held.
    old, new = accepted_inputs_payload(prior), accepted_inputs_payload(resolved)
    assert not REPLACEMENT._preserved(old, new)
    assert resolved.batches[: len(prior.batches)] == prior.batches
    assert (
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (1250 + 414, 6450 + 3139, 950 + 414, 1099 + 83)
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )
    # Exactly the parts' leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(resolved) - _covered(prior) == mine
    assert len(mine) == 3139
    # Every accepted target closes; only unresolved pointers remain: the
    # committed ones less the drafted, plus the packet's own.
    rest = _references(resolved)
    assert all(f.startswith("reference ") and "unresolved" in f for f in rest)
    packet = [
        f
        for f in GEN.expected_representation_findings(GEN.MONSTERS_CHUNK)
        if "unresolved" in f
    ]
    drafted = {
        f"reference {MONSTERS}:{r.source_text!r}: unresolved reference" for r in drafts
    }
    kept = Counter(refs_before)
    kept.subtract(Counter(f for f in refs_before if f in drafted))
    assert Counter(rest) == +kept + Counter(packet)
    assert len(rest) == 315 - 83 + len(packet) == 317
    assert {p.name: p.read_bytes() for p in ORACLES.iterdir()} == on_disk


def test_the_committed_oracle_records_the_owner_acceptance(prior) -> None:  # type: ignore[no-untyped-def]
    data = RECORDING.ACCEPTED_PATH.read_bytes()
    assert hashlib.sha256(data).hexdigest() == COMMITTED_SHA256
    # The superseded release's committed file, read by path: the production
    # resolver refuses its binding.
    on_disk = load_accepted_inputs(RECORDING.ACCEPTED_PATH)
    assert serialize_accepted_inputs(on_disk) == data
    # The file now also records Animals, then the Equipment and
    # remaining-references replacements; the Monsters recording, rebuilt from
    # its recorded times at its recorded bytes, is kept whole in the Animals
    # recording, which the Equipment recording keeps outside Equipment.
    committed = monsters_recorded()
    assert hashlib.sha256(serialize_accepted_inputs(committed)).hexdigest() == (
        RECORDING.RECORDED_SHA256["resolved"]
    )
    animals = animals_recorded()
    assert not RECORDING._preserved(
        accepted_inputs_payload(committed), accepted_inputs_payload(animals)
    )
    assert not EQUIPMENT_CITED._outside(animals, equipment_recorded())
    # The chain is kept whole, and Monsters is the one batch added over it.
    # ``prior`` already carries the Magic Items enlargement, so it is kept
    # exactly, obligations included.
    assert not RECORDING._preserved(
        accepted_inputs_payload(prior), accepted_inputs_payload(committed)
    )
    # The file orders batches (and their diffs) canonically, not in
    # acceptance order, so compare the canonical payloads.
    assert [
        b
        for b in accepted_inputs_payload(committed)["acceptance"]["batches"]
        if b["batch_id"] != "monsters"
    ] == accepted_inputs_payload(prior)["acceptance"]["batches"]
    (batch,) = [b for b in committed.batches if b.batch_id == "monsters"]
    assert (batch.proposal_identity, batch.rule) == (IDENTITY, RECORDING.APPROVAL)
    _, accepted_at, resolved_at = RECORDING.RECORDED_AT
    mine = [
        a
        for a in (*committed.acceptances, *committed.review_unit_acceptances)
        if a.batch_id == "monsters"
    ]
    assert len(mine) == 3139 + 414
    assert {(a.reviewer, a.accepted_at) for a in mine} == {
        (RECORDING.OWNER, accepted_at)
    }
    drafts = GEN.draft_resolutions(prior.oracle.binding, prior=prior)
    new = {r.resolution_id for r in drafts}
    auths = [
        a for a in committed.reference_resolution_acceptances if a.resolution_id in new
    ]
    assert len(auths) == len(new) == 83
    assert {
        (a.authorized_by, a.reviewer, a.resolved_at, a.authorization_reference)
        for a in auths
    } == {
        (
            RECORDING.OWNER,
            RECORDING.OWNER,
            resolved_at,
            RECORDING.AUTHORIZATION_REFERENCE,
        )
    }
    final = committed.oracle
    assert (
        len(committed.batches),
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (21, 1664, 9589, 1364, 1182)
    refs = _references(committed)
    assert len(refs) == 317
    assert all(f.startswith("reference ") for f in refs)


# ---------------------------------------------------------------------------
# Through the production rules-authority service
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db):  # type: ignore[no-untyped-def]
    """The current accepted authority, persisted as one draft into a private
    copy of the current release."""
    candidate = candidate_from_accepted_inputs(current())
    assert isinstance(candidate, ProjectionCandidate)
    path = tmp_path_factory.mktemp("monsters") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(candidate)
        persist_draft(s, identified, now="2026-09-27T00:00:00Z")
        s.commit()
        yield s, identified.projection_uuid
    engine.dispose()


def _prose(service, built, *records: str):  # type: ignore[no-untyped-def]
    view = service.gamemaster_view(_request(built, *records))
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    return [e for c in view.gamemaster_view.components for e in c.governing_prose]


def _texts(service, built, *records: str) -> list[str]:  # type: ignore[no-untyped-def]
    return [e.text for e in _prose(service, built, *records)]


def _component(entry: str, key: str):  # type: ignore[no-untyped-def]
    (c,) = [
        c for c in GEN.MONSTERS_CHUNK.components if (c.entry, c.key) == (entry, key)
    ]
    return c


def _read(entry: str) -> list[str]:
    """A creature read directly: per component, in source order, the
    governing rules not yet read, which the release prints first, then its
    own texts."""
    out: list[str] = []
    for e, k, _, own in GEN.MONSTERS_CHUNK.clauses:
        if e == entry:
            out += [t for t in _component(e, k).context if t not in out]
            out += own
    return out


def test_a_creature_reads_itself_with_the_rules_governing_it(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    assert _sliced(service, _request(built, ABOLETH)) == [ABOLETH]
    read = _texts(service, built, ABOLETH)
    assert read == _read("aboleth.aboleth")
    assert read.count(GEN.HIT_POINTS) == 1
    # Its own printed leaves, every one, in printed order.
    own = _printed(GEN.A_Z, "Aboleth", "Aboleth")
    assert [t for t in read if t in own] == own
    # Only the rules its header prints: telepathy, not size options or Gear.
    assert GEN.TELEPATHY in read and GEN.SIZE_OPTIONS not in read
    assert not set(GEN.GEAR) & set(read)
    # A header printing size options reads their rule.
    commoner = _component("commoner.commoner", "commoner")
    assert GEN.SIZE_OPTIONS in commoner.context


def test_the_corrected_stat_blocks_read_as_printed(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    for group, block in (SUCCUBUS, VETERAN, YOUNG_WHITE):
        read = _texts(service, built, GEN.BLOCK_KEY[block])
        own = _printed(GEN.A_Z, group, block)
        assert [t for t in read if t in own] == own, block
        assert read == _read(GEN.BLOCK_KEY[block].removeprefix("monsters.")), block


def test_a_group_reaches_its_creatures_once_in_printed_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    blocks = [
        GEN.creature_key("Red Dragons", b)
        for b in GEN.children((GEN.A_Z, "Red Dragons"))
    ]
    assert _sliced(service, _request(built, DRAGONS)) == [DRAGONS, *blocks]
    read = _texts(service, built, DRAGONS)
    assert read[0] == "## Red Dragons"
    assert [t for t in read if t in _printed(GEN.A_Z, "Red Dragons")] == _printed(
        GEN.A_Z, "Red Dragons"
    )
    # Each governing rule once, though every creature reads it; each repeated
    # container heading stays with its own stat block.
    assert read.count(GEN.HIT_POINTS) == 1
    assert read.count("#### Actions") == len(blocks)
    spans = [e.span_id for e in _prose(service, built, DRAGONS)]
    assert len(spans) == len(set(spans))


def test_suppressing_a_governing_rule_suppresses_it_on_the_creature(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    full = _texts(_service(persisted, built, monkeypatch), built, ABOLETH)
    off = _disable_component(PARTS, "hit_points")
    service = _service(persisted, built, monkeypatch, off)
    assert _texts(service, built, ABOLETH) == [t for t in full if t != GEN.HIT_POINTS]
    # The owner selected with its reader reads it; the reader does not repeat it.
    both = _texts(_service(persisted, built, monkeypatch), built, PARTS, ABOLETH)
    assert both.count(GEN.HIT_POINTS) == 1


# The source's own words, not the generator's context lists.
ALIGNMENT = (
    "The alignment specified in a monster's stat block is a default suggestion"
    " of how to roleplay the monster"
)
CLASS_TAG = (
    "A monster with a class tag after its creature type is considered a member"
    " of that class for Attunement purposes."
)
AMMUNITION = (
    "A monster that requires ammunition to make ranged attacks carries the"
    " necessary ammunition."
)
LANGUAGES = "This entry lists languages that the monster can use to communicate."
RUNNING = (
    "To ensure a monster acts in accordance with its Challenge Rating, follow"
    " these rules during combat:"
)
SPELLCASTING = "If a monster can cast any spells, its stat block lists the spells"


def _count(read: list[str], words: str) -> int:
    return sum(words in t for t in read)


def test_a_direct_read_carries_the_rules_its_stat_block_requires(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)

    def read(block: str) -> list[str]:
        return _texts(service, built, GEN.BLOCK_KEY[block])

    aboleth = read("Aboleth")
    # Every stat block: its alignment is a default suggestion, and its CR
    # holds only if it is run by the sidebar's combat rules.
    assert _count(aboleth, ALIGNMENT) == _count(aboleth, RUNNING) == 1
    # No class tag, no ammunition weapon, no spell cast.
    for words in (CLASS_TAG, AMMUNITION, SPELLCASTING):
        assert not _count(aboleth, words), words
    # A class tag carries its Attunement meaning.
    for block in ("Mage", "Priest", "Druid"):
        assert _count(read(block), CLASS_TAG) == 1, block
    # A ranged attack with an ammunition weapon carries its ammunition.
    for block in ("Scout", "Werewolf"):
        assert _count(read(block), AMMUNITION) == 1, block
    # "Understands", capitalised as a header prints it, is the Languages rule.
    assert _count(read("Zombie"), LANGUAGES) == 1
    # Casting is what a component does, whether or not the name is italic.
    for block in ("Storm Giant", "Succubus", "Shield Guardian"):
        assert _count(read(block), SPELLCASTING) == 1, block
    # A spell that targets the Tarrasque is not one it casts.
    assert not _count(read("Tarrasque"), SPELLCASTING)


def test_disabling_a_new_governing_owner_suppresses_it_and_selection_dedups(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    mage = GEN.BLOCK_KEY["Mage"]
    full = _texts(_service(persisted, built, monkeypatch), built, mage)
    for key, words in (
        ("running_a_monster", RUNNING),
        ("magic_items_and_class_tags", CLASS_TAG),
        ("alignment", ALIGNMENT),
    ):
        service = _service(
            persisted, built, monkeypatch, _disable_component(PARTS, key)
        )
        off = _texts(service, built, mage)
        assert not _count(off, words), key
        assert off == [t for t in full if words not in t], key
    # The owner and two readers selected together: each governing span once.
    service = _service(persisted, built, monkeypatch)
    both = _texts(service, built, PARTS, mage, GEN.BLOCK_KEY["Scout"])
    for words in (ALIGNMENT, RUNNING, CLASS_TAG, AMMUNITION):
        assert _count(both, words) == 1, words
    spans = [e.span_id for e in _prose(service, built, PARTS, mage)]
    assert len(spans) == len(set(spans))
