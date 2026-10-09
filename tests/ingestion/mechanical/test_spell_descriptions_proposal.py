"""The ``spell-descriptions`` proposal, offered for review -- CRD Issue 5d.

The *Spell Descriptions* section of the *Spells* part, pp107-175, proposed by
``.claude/review-notes/issue-5d-spell-descriptions-generator.py`` from the
release 5c actually publishes, with its resolution drafts. The Owner accepted
the proposal and approved the drafts over the superseded release
(``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``, historical). On the
Monsters-corrected release the regenerated proposal and drafts are batch
eighteen of the replacement chain the Owner accepted, which
``issue-5d-monsters-corrections-ACCEPT.py`` recorded; the seventeen batches
before it are rebuilt here from that recording.

What is pinned, and why:

* the committed artifact is the superseded release's recorded proposal, by
  shape, and the drafts are what the generator drafts; the generator builds
  over the current release (that it no longer derives the recorded bytes is
  retired, see
  ``.claude/review-notes/issue-5c-release-readiness/correction-followup.md``);
* scope is the section's 2036 leaves, heading first, and no leaf or record is
  an accepted one's;
* each spell's descriptor facts restate its printed lines, its level line's
  classes are the ``SPELL_LIST_MEMBER`` edges it cites, and the level lines
  agree with the class tables as the Owner corrected them;
* fidelity: every component reads its reviewed texts, every word of every
  spanned leaf is claimed, only *Wish*'s Instant Health and the descriptors
  carry facts, and latitude is only where the text leaves it to the GM;
* the recorded proposal, composed over the Owner's recorded replacement
  chain rebuilt natively (both the superseded release's): it accepts, then the
  drafts resolve, in memory; every accepted record, resolution and byte is
  preserved, exactly the section's leaves gain coverage, and the class edges
  validate; the committed oracle is that composition replayed at the recorded
  times under the Owner's decision. Judging the composition against a corpus
  needs the superseded release's, which is not rebuilt; that check is retired;
* through the production rules-authority service, over the current accepted
  authority persisted as one draft into the current release:
  the section reaches its spells in printed order, a spell reads its heading,
  level line and descriptor first, a stat block reads as its own scoped
  record, and a disabled spell is gone;
* the Owner's class spell-table correction: the four corrected Level 2 tables
  point at and resolve their inserted spells, read alphabetically and in place
  with the descriptions' membership and schools, and a house rule replaces one
  while a disabled class fails closed.
"""

from __future__ import annotations

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
    REPRESENTATION_SCHEMA_VERSION,
    ActionCost,
    DurationKind,
    HealingFact,
    RangeKind,
    RecordKind,
    RelationshipKind,
    SpellDescriptorFact,
    SpellSchool,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import (
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
    REPLACEMENT,
    animals_recorded,
    current,
    identity,
    kept_whole,
    proposal_path,
    through,
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
ORACLE = REPLACEMENT.ACCEPTED_PATH
BATCH = "spell-descriptions"
SPELLS = "srd-5.2.1/spells"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load(
    "spell_descriptions_generator",
    NOTES / "issue-5d-spell-descriptions-generator.py",
)
PROPOSAL = proposal_path(BATCH)
DRAFTS = REPLACEMENT.drafts_path(BATCH)
IDENTITY = identity(BATCH)
PROPOSAL_SHA256 = BATCHES[BATCH][1]
DRAFTS_SHA256 = REPLACEMENT.DRAFTS[BATCH][0]


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
    """The seventeen-batch chain this packet is composed over, as recorded."""
    inputs = through("class-option-catalogues")
    assert [b.batch_id for b in inputs.batches] == list(BATCHES)[:17]
    return inputs


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


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


def _fact(b: Built, name: str) -> SpellDescriptorFact:
    ((fact,),) = [
        c.facts
        for c in b.proposal.proposed_representation.components
        if (c.record_key, c.semantic_key) == (GEN.spell_key(name), "descriptor")
    ]
    assert isinstance(fact, SpellDescriptorFact)
    return fact


# ---------------------------------------------------------------------------
# The artifacts
# ---------------------------------------------------------------------------


def test_the_committed_artifact_is_the_recorded_proposal_by_shape(built) -> None:  # type: ignore[no-untyped-def]
    data = PROPOSAL.read_bytes()
    assert hashlib.sha256(data).hexdigest() == PROPOSAL_SHA256
    assert b"\r" not in data
    # The generator builds over the current release.
    assert built.binding == current().oracle.binding
    proposal = load_proposal(PROPOSAL, expected_identity=IDENTITY)
    assert json.loads(data)["artifact_kind"] == "machine_proposal"
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(PROPOSAL)


def test_the_drafts_are_the_generator_s_and_name_only_spells(prior) -> None:  # type: ignore[no-untyped-def]
    data = DRAFTS.read_bytes()
    assert hashlib.sha256(data).hexdigest() == DRAFTS_SHA256 and b"\r" not in data
    drafts = GEN.draft_resolutions(prior.oracle.binding, prior=prior)
    assert json.loads(data) == reference_resolution_payload(drafts)
    assert len(drafts) == 1046
    names = {GEN.spell_key(n): n for n in GEN.SPELL_NAMES}
    # Each draft targets the spell whose exact name the accepted pointer prints.
    assert all(names[d.target_record_key] == d.source_text for d in drafts)
    assert {d.scope_key for d in drafts} == {SPELLS}
    assert all(d.resolution_id.endswith("-spell-descriptions-1") for d in drafts)
    # No recorded resolution is redrafted, and nothing broader is guessed.
    recorded = {
        (r.from_record_key, r.from_component_key, r.source_text)
        for r in prior.oracle.reference_resolutions
    }
    assert not recorded & {
        (d.from_record_key, d.from_component_key, d.source_text) for d in drafts
    }
    _, left = GEN.draft_targets(prior)
    assert Counter(text for *_, text in left) == {"Spells": 13, "Casting Spells": 2}


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------


def test_scope_is_the_section_s_2036_leaves(session, built) -> None:  # type: ignore[no-untyped-def]
    rows = (
        session.query(LedgerLeafORM)
        .filter(LedgerLeafORM.package_uuid == built.binding.package_uuid)
        .order_by(LedgerLeafORM.occurrence_index)
        .all()
    )
    (start,) = [i for i, r in enumerate(rows) if r.content == "## Spell Descriptions"]
    section = rows[start : start + len(GEN.LEAVES)]
    assert [r.content for r in section] == [t for _, t in GEN.LEAVES]
    # The section runs to the end of the part: the next leaf is a new part.
    assert start + len(GEN.LEAVES) == len(rows) or rows[
        start + len(GEN.LEAVES)
    ].content.startswith("# ")
    mine = [leaf for u in built.proposal.proposed_review_units for leaf in u.leaf_ids]
    assert len(mine) == len(set(mine)) == 2036
    assert set(mine) == {r.leaf_id for r in section}
    keys = [r.semantic_key for r in built.proposal.proposed_representation.records]
    assert len(keys) == len(set(keys))


def test_no_recorded_leaf_or_record_is_an_accepted_one(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    # Both sides are the superseded release's: the recorded chain and proposal.
    mine = [leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids]
    assert len(mine) == len(set(mine)) == 2036
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    assert not owned & set(mine)
    accepted = {r.semantic_key for r in prior.oracle.representation.records}
    keys = [r.semantic_key for r in recorded.proposed_representation.records]
    assert len(keys) == len(set(keys)) and not accepted & set(keys)


def test_the_records_are_the_section_its_spells_and_their_stat_blocks(built) -> None:  # type: ignore[no-untyped-def]
    records = built.proposal.proposed_representation.records
    assert Counter(r.kind for r in records) == {
        RecordKind.GENERAL_RULE: 1,
        RecordKind.SPELL: 339,
        RecordKind.CREATURE: 4,
    }
    assert [r.semantic_key for r in records if r.kind is RecordKind.SPELL] == [
        GEN.spell_key(n) for n in GEN.SPELL_NAMES
    ]
    assert len(built.proposal.proposed_review_units) == 340
    # A member or scoped record is the edge's source, its host the target; a
    # spell-list edge runs from the class to the spell.
    edges = Counter(
        (
            r.kind,
            "" if r.kind is RelationshipKind.SPELL_LIST_MEMBER else r.target_record_key,
        )
        for r in built.proposal.proposed_representation.relationships
    )
    assert edges == {
        (RelationshipKind.CATALOGUE_MEMBER, "spells.spell_descriptions"): 339,
        (RelationshipKind.SCOPED_WITHIN, "spells.animate_objects"): 1,
        (RelationshipKind.SCOPED_WITHIN, "spells.find_steed"): 1,
        (RelationshipKind.SCOPED_WITHIN, "spells.giant_insect"): 1,
        (RelationshipKind.SCOPED_WITHIN, "spells.summon_dragon"): 1,
        (RelationshipKind.SPELL_LIST_MEMBER, ""): 879,
    }
    assert {
        r.source_record_key
        for r in built.proposal.proposed_representation.relationships
        if r.kind is RelationshipKind.SCOPED_WITHIN
    } == {GEN.creature_key(s) for s in GEN.STAT_BLOCKS}


# ---------------------------------------------------------------------------
# Descriptors and class lists
# ---------------------------------------------------------------------------


def test_descriptor_facts_restate_the_printed_lines(built) -> None:  # type: ignore[no-untyped-def]
    fireball = _fact(built, "Fireball")
    assert (fireball.level, fireball.school, fireball.ritual) == (
        3,
        SpellSchool.EVOCATION,
        False,
    )
    assert fireball.casting_time is not None
    assert fireball.casting_time.cost is ActionCost.ACTION
    assert fireball.spell_range is not None
    assert (fireball.spell_range.kind, fireball.spell_range.feet) == (
        RangeKind.RANGED,
        150,
    )
    assert fireball.components is not None and fireball.components.material
    assert fireball.duration is not None
    assert fireball.duration.kind is DurationKind.INSTANTANEOUS
    # A cantrip is level 0; a ritual and a concentration are read as printed.
    assert _fact(built, "Fire Bolt").level == 0
    assert (
        _fact(built, "Detect Magic").ritual
        and _fact(built, "Detect Magic").concentration
    )
    # A reaction's trigger stays in the governing prose.
    shield = _fact(built, "Shield")
    assert shield.casting_time is not None
    assert shield.casting_time.cost is ActionCost.REACTION
    (descriptor,) = [
        t for t in _texts(built, "spells.shield", "descriptor") if "Reaction" in t
    ]
    assert "_Magic Missile_" in descriptor
    # Consumption is typed; its cost stays in the prose.
    assert _fact(built, "Revivify").components.material_consumed  # type: ignore[union-attr]
    # An arm the contract cannot state is left untyped, never approximated.
    assert _fact(built, "Plant Growth").casting_time is None
    assert _fact(built, "Tsunami").spell_range is None
    assert _fact(built, "Glyph of Warding").duration is None
    assert _fact(built, "Etherealness").duration is None
    untyped = sorted(
        (name, arm)
        for name in GEN.SPELL_NAMES
        for arm, value in (
            ("casting_time", _fact(built, name).casting_time),
            ("range", _fact(built, name).spell_range),
            ("duration", _fact(built, name).duration),
        )
        if value is None
    )
    assert untyped == sorted(
        [
            ("Plant Growth", "casting_time"),
            *((n, "range") for n in ("Clairvoyance", "Meteor Swarm", "Project Image",
                                     "Storm of Vengeance", "Tsunami")),
            *((n, "duration") for n in ("Etherealness", "Glyph of Warding",
                                        "Prestidigitation", "Symbol", "Thaumaturgy")),
        ]
    )  # fmt: skip


def test_level_lines_are_the_class_edges_and_agree_with_the_class_tables(built) -> None:  # type: ignore[no-untyped-def]
    edges = {
        (r.source_record_key, r.target_record_key)
        for r in built.proposal.proposed_representation.relationships
        if r.kind is RelationshipKind.SPELL_LIST_MEMBER
    }
    printed = {
        (f"classes.{GEN.slug(c)}", GEN.spell_key(n))
        for n in GEN.SPELL_NAMES
        for c in GEN.spell_classes(GEN.texts_at(GEN.SECTION + (n,))[1])
    }
    assert edges == printed and len(edges) == 879
    # Each edge is cited on the level line that prints it.
    assert GEN.class_list_disagreements() == () == GEN.CLASS_LIST_DISAGREEMENTS


# ---------------------------------------------------------------------------
# Fidelity
# ---------------------------------------------------------------------------


def test_every_component_reads_its_reviewed_texts(built) -> None:  # type: ignore[no-untyped-def]
    chunk = GEN.SPELL_CHUNK
    components = built.proposal.proposed_representation.components
    mixed = [c for c in components if c.handling is ComponentHandling.MIXED]
    assert [c for c in components if c.all_facts()] == mixed
    assert Counter(c.semantic_key for c in mixed) == {
        "descriptor": 339,
        "instant_health": 1,
    }
    (health,) = [c for c in mixed if c.semantic_key == "instant_health"]
    assert health.facts == (HealingFact(restores_all_hit_points=True),)
    clauses = {(e, k): texts for e, k, _, texts in chunk.clauses}
    for c in chunk.components:
        record = c.record or chunk.placements[c.entry].record_key
        texts = c.texts or clauses[(c.entry, c.key)]
        assert _texts(built, record, c.key) == list(texts), (record, c.key)
    wish = [c.semantic_key for c in components if c.record_key == "spells.wish"]
    assert wish == [
        "descriptor",
        "effect",
        "object_creation",
        "instant_health",
        "resistance",
        "spell_immunity",
        "sudden_learning",
        "roll_redo",
        "reshape_reality",
        "stress",
    ]


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


def test_every_spanned_leaf_is_claimed_and_nothing_excluded(built) -> None:  # type: ignore[no-untyped-def]
    assert _residue(built) == {}
    assert not [
        g for u in built.proposal.proposed_review_units for g in u.excluded_groups
    ]
    for placement in GEN.SPELL_CHUNK.placements.values():
        record = placement.record_key
        first = next(
            c.semantic_key
            for c in built.proposal.proposed_representation.components
            if c.record_key == record
        )
        assert _texts(built, record, first)[0] == placement.heading


def test_latitude_is_only_where_the_text_names_the_gm(built) -> None:  # type: ignore[no-untyped-def]
    for c in GEN.SPELL_CHUNK.components:
        record = c.record or GEN.SPELL_CHUNK.placements[c.entry].record_key
        texts = _texts(built, record, c.key)
        assert (c.reason == GEN.GM) == any(GEN._GM.search(t) for t in texts)
    reasons = {
        (c.record_key, c.semantic_key): c.prose_retention_reason_code
        or c.irreducibility_reason_code
        for c in built.proposal.proposed_representation.components
    }
    assert reasons[("spells.wish", "reshape_reality")] == GEN.GM
    assert reasons[("spells.fireball", "effect")] == GEN.NO_USE


def test_references_name_exact_records_or_stay_unresolved(built) -> None:  # type: ignore[no-untyped-def]
    refs = _refs(built)
    for ref in (
        ("spells.shield", "descriptor", "Magic Missile", SPELLS,
         "spells.magic_missile"),
        ("spells.animate_objects", "effect", "Animated Object", SPELLS,
         "spells.animate_objects.animated_object"),
        ("spells.bless", "descriptor", "Holy Symbol", "srd-5.2.1/equipment",
         "equipment.adventuring_gear.holy_symbol"),
        ("spells.shillelagh", "effect", "Quarterstaff", "srd-5.2.1/equipment",
         "equipment.weapons.quarterstaff"),
        ("spells.find_familiar", "effect", "Owl", "srd-5.2.1/monsters", ""),
        ("spells.phantom_steed", "effect", "Riding Horse", "srd-5.2.1/monsters", ""),
    ):  # fmt: skip
        assert ref in refs, ref
    # Every italic name is one of the described spells, and every one read.
    assert {r[4] for r in refs if r[3] == SPELLS and r[4].count(".") == 1} <= {
        GEN.spell_key(n) for n in GEN.SPELL_NAMES
    }
    # Monster and Animal targets are never guessed.
    assert {r[4] for r in refs if r[3] in (GEN.MONSTERS, GEN.ANIMALS)} == {""}
    assert "Holy Water" in {r[2] for r in refs if r[4] == ""}
    # A record never points at itself; a label is never a term.
    assert not [r for r in refs if r[0] == r[4]]
    assert "Cantrip Upgrade" not in {r[2] for r in refs}


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings(
        GEN.SPELL_CHUNK
    )
    assert (
        Counter(
            f.split(":")[0].split(" ")[1]
            for f in found["representation"]
            if "unresolved reference" in f
        )
        == UNRESOLVED_SCOPES
    )


#: The packet's own unresolved pointers, by scope.
UNRESOLVED_SCOPES = {
    "srd-5.2.1/monsters": 30,
    "srd-5.2.1/animals": 1,
    "srd-5.2.1/equipment": 1,
}


# ---------------------------------------------------------------------------
# Test-only composition with the committed oracle
# ---------------------------------------------------------------------------


def _accepted(prior: AcceptedInputs, proposal: MechanicalProposal) -> AcceptedInputs:
    return accept_proposal(
        proposal,
        batch_id="spell-descriptions",
        rule="test-only",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer="test",
        accepted_at="2026-09-26T00:00:00Z",
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


#: Reference findings left after accepting and resolving, all unresolved.
REMAINING = 1157 - 1046 + 32


def test_accepted_then_resolved_in_memory_preserves_everything(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    oracles = REPO / "src/afterworlds/ingestion/mechanical/oracles"
    on_disk = {p.name: p.read_bytes() for p in oracles.glob("*.json")}
    prior_bytes = serialize_accepted_inputs(prior)
    base = prior.oracle
    assert (
        len(prior.batches),
        len(base.representation.records),
        len(base.spans),
        len(base.review_units),
        len(base.reference_resolutions),
    ) == (17, 603, 2776, 305, 51)
    # Both sides are the superseded release's: the recorded chain and proposal.
    assert recorded.binding == base.binding
    refs_before = _references(prior)
    assert len(refs_before) == 1157

    accepted = _accepted(prior, recorded)
    drafts = GEN.draft_resolutions(base.binding, prior=prior)
    resolved = resolve_references(
        accepted,
        resolutions=drafts,
        authorized_by="test",
        authorization_reference="test-only",
        reviewer="test",
        resolved_at="2026-09-26T00:00:01Z",
    )
    final = resolved.oracle
    # Append-only: every accepted batch, record, span, unit and resolution stays.
    assert resolved.batches[: len(prior.batches)] == prior.batches
    assert set(base.representation.records) < set(final.representation.records)
    assert set(base.spans) < set(final.spans)
    assert set(base.reference_resolutions) < set(final.reference_resolutions)
    assert set(prior.acceptances) < set(resolved.acceptances)
    assert (
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (603 + 344, 2776 + 2050, 305 + 340, 51 + 1046)
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )
    # Exactly the section's leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(resolved) - _covered(prior) == mine
    assert len(mine) == 2036
    # The class edges and every accepted target close; only unresolved
    # pointers remain: the accepted ones no draft names and the packet's own.
    rest = _references(resolved)
    assert all(f.startswith("reference ") and "unresolved" in f for f in rest)
    packet = [
        f
        for f in GEN.expected_representation_findings(GEN.SPELL_CHUNK)
        if "unresolved" in f
    ]
    drafted = {
        f"reference {SPELLS}:{d.source_text!r}: unresolved reference" for d in drafts
    }
    assert sorted(rest) == sorted(
        [*(f for f in refs_before if f not in drafted), *packet]
    )
    assert len(rest) == REMAINING, len(rest)
    # The committed oracle and the recorded prior are untouched.
    assert {p.name: p.read_bytes() for p in oracles.glob("*.json")} == on_disk
    assert serialize_accepted_inputs(prior) == prior_bytes


def test_the_committed_oracle_records_the_owner_acceptance(prior) -> None:  # type: ignore[no-untyped-def]
    # The recorded chain through this batch is the Owner's steps over the
    # seventeen batches before it, which it keeps whole.
    recorded = through(BATCH)
    assert not REPLACEMENT._preserved(
        accepted_inputs_payload(prior), accepted_inputs_payload(recorded)
    )
    assert recorded.batches[: len(prior.batches)] == prior.batches
    # The Animals recording keeps it whole, but for the Magic Items batch's
    # reviewed obligation enlargement of the two shared Equipment records; the
    # committed oracle keeps that outside the replaced Equipment batch.
    # The superseded release's committed file, read by path: the production
    # resolver refuses its binding.
    committed = load_accepted_inputs(ORACLE)
    assert serialize_accepted_inputs(committed) == ORACLE.read_bytes()
    assert not kept_whole(recorded, animals_recorded())
    (batch,) = [b for b in recorded.batches if b.batch_id == BATCH]
    assert (batch.proposal_identity, batch.rule) == (IDENTITY, REPLACEMENT.APPROVAL)
    assert {(a.reviewer, a.accepted_at) for a in recorded.acceptances} == {
        (REPLACEMENT.OWNER, REPLACEMENT.ACCEPTED_AT)
    }
    new = [
        a
        for a in recorded.reference_resolution_acceptances
        if a.resolution_id.endswith("-spell-descriptions-1")
    ]
    assert len(new) == 1046
    assert {
        (a.authorized_by, a.reviewer, a.resolved_at, a.authorization_reference)
        for a in new
    } == {
        (
            REPLACEMENT.OWNER,
            REPLACEMENT.OWNER,
            REPLACEMENT.ACCEPTED_AT,
            REPLACEMENT.AUTHORIZATION_REFERENCE,
        )
    }
    # The resolutions are the reviewed drafts, byte for byte.
    ids = {a.resolution_id for a in new}
    mine = tuple(
        r for r in recorded.oracle.reference_resolutions if r.resolution_id in ids
    )
    assert list(reference_resolution_payload(mine)) == json.loads(DRAFTS.read_bytes())


# ---------------------------------------------------------------------------
# Through the production rules-authority service
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db):  # type: ignore[no-untyped-def]
    """The current accepted authority, persisted as one draft into a private
    copy of the current release, so its class edges have their sources."""
    candidate = candidate_from_accepted_inputs(current())
    assert isinstance(candidate, ProjectionCandidate)
    assert (candidate.schema_version, candidate.schema_hash) == (
        REPRESENTATION_SCHEMA_VERSION,
        representation_schema_hash(),
    )
    path = tmp_path_factory.mktemp("spells") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(candidate)
        persist_draft(s, identified, now="2026-09-26T00:00:00Z")
        s.commit()
        yield s, identified.projection_uuid
    engine.dispose()


def _read(service, built, *records: str) -> list[tuple[str, str, str]]:  # type: ignore[no-untyped-def]
    view = service.gamemaster_view(_request(built, *records))
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    return [
        (c.record_key, c.component_key, e.text)
        for c in view.gamemaster_view.components
        for e in c.governing_prose
    ]


def test_the_section_reaches_its_spells_in_printed_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    reached = _sliced(service, _request(built, "spells.spell_descriptions"))
    assert reached == [
        "spells.spell_descriptions",
        *(GEN.spell_key(n) for n in GEN.SPELL_NAMES),
    ]


def test_a_spell_reads_its_descriptor_then_its_effect(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    read = _read(service, built, "spells.barkskin")
    assert [t for _, _, t in read][:4] == [
        "#### Barkskin",
        "_Level 2 Transmutation (Druid, Ranger)_",
        "**Casting Time:** Bonus Action\n**Range:** Touch",
        "**Component:** V, S, M (a handful of bark)\n**Duration:** 1 hour",
    ]
    assert [k for _, k, _ in read] == ["descriptor"] * 4 + ["effect"] * (len(read) - 4)
    # A class's spell list is an edge no consumer expands: the class does not
    # read its spells, and a spell does not read its classes.
    assert "spells.barkskin" not in _sliced(service, _request(built, "classes.druid"))
    assert _sliced(service, _request(built, "spells.barkskin")) == ["spells.barkskin"]


def test_a_stat_block_is_its_own_scoped_record(persisted, built, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _service(persisted, built, monkeypatch)
    steed = "spells.find_steed.otherworldly_steed"
    assert steed not in {r for r, _, _ in _read(service, built, "spells.find_steed")}
    read = _read(service, built, steed)
    assert read[0][2] == "##### Otherworldly Steed"
    assert [k for _, k, _ in read][-1] == "bonus_actions"


def test_a_disabled_spell_stays_gone(persisted, built, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _service(persisted, built, monkeypatch, _disable("spells.fireball"))
    reached = _sliced(service, _request(built, "spells.spell_descriptions"))
    assert "spells.fireball" not in reached and len(reached) == 339
    refused = service.rule_slice(_request(built, "spells.fireball"))
    assert refused.outcome is AuthorityOutcome.INVALID_REFERENCE


# ---------------------------------------------------------------------------
# The Owner's class spell-table correction (the descriptions are right)
# ---------------------------------------------------------------------------

L2 = "level_2_spells"
CORRECTED = ("classes.bard", "classes.druid", "classes.sorcerer", "classes.wizard")
#: The four Level 2 names the corrected tables print and the PDF's omit.
INSERTED = {
    ("classes.bard", "Phantasmal Force"): "spells.phantasmal_force",
    ("classes.sorcerer", "Mind Spike"): "spells.mind_spike",
    ("classes.sorcerer", "Phantasmal Force"): "spells.phantasmal_force",
    ("classes.wizard", "Phantasmal Force"): "spells.phantasmal_force",
}


def _rows(table: str) -> list[tuple[str, ...]]:
    return [
        tuple(c.strip() for c in re.findall(r"<td>(.*?)</td>", row, re.S))
        for row in re.findall(r"<tr>(.*?)</tr>", table, re.S)
        if "<td>" in row
    ]


def test_the_corrected_tables_point_at_and_resolve_their_spells(prior) -> None:  # type: ignore[no-untyped-def]
    pointers = {
        (r.from_record_key, r.source_text)
        for r in prior.oracle.representation.references
        if r.from_record_key in CORRECTED and r.from_component_key == L2
    }
    assert set(INSERTED) <= pointers
    drafted = {
        (d.from_record_key, d.source_text): d.target_record_key
        for d in GEN.draft_resolutions(prior.oracle.binding, prior=prior)
        if d.from_component_key == L2
    }
    assert {k: drafted[k] for k in INSERTED} == INSERTED


def test_each_corrected_table_agrees_with_the_spell_descriptions(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    level_2 = {
        GEN.spell_key(n): _fact(built, n)
        for n in GEN.SPELL_NAMES
        if _fact(built, n).level == 2
    }
    members = {
        (r.source_record_key, r.target_record_key)
        for r in built.proposal.proposed_representation.relationships
        if r.kind is RelationshipKind.SPELL_LIST_MEMBER
    }
    for cls in CORRECTED:
        view = service.gamemaster_view(_request(built, components=((cls, L2),)))
        assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
        heading, table = [
            e.text for c in view.gamemaster_view.components for e in c.governing_prose
        ]
        assert heading.startswith("#### Level 2 ") and table.startswith("<table>")
        rows = _rows(table)
        # Printed alphabetically; membership and school are the descriptions'.
        assert rows == sorted(rows)
        assert {GEN.spell_key(name) for name, *_ in rows} == {
            s for c, s in members if c == cls and s in level_2
        }
        assert all(
            level_2[GEN.spell_key(name)].school.value == school.lower()
            for name, school, *_ in rows
        )
        # The whole class reads the same table in place, after its heading.
        read = _read(service, built, cls)
        at = [t for _, _, t in read].index(table)
        assert read[at - 1] == (cls, L2, heading) and read[at][1] == L2
    assert _fact(built, "Flaming Sphere").school is SpellSchool.CONJURATION


def test_a_corrected_table_can_be_replaced_or_fails_closed(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    cls = "classes.sorcerer"
    printed = _read(_service(persisted, built, monkeypatch), built, cls)
    house = EffectiveOverrideEntry(
        override_id="replace-sorcerer-level-2",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT, record_key=cls, component_key=L2
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
                "authored_prose": "A house Level 2 list.",
            },
        },
    )
    service = _service(persisted, built, monkeypatch, house)
    view = service.gamemaster_view(_request(built, cls))
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    after = [
        (c.record_key, c.component_key, e)
        for c in view.gamemaster_view.components
        for e in c.governing_prose
    ]
    assert [(r, k, e.text) for r, k, e in after if k != L2] == [
        x for x in printed if x[1] != L2
    ]
    (replaced,) = [e for _, k, e in after if k == L2]
    assert isinstance(replaced, AuthoredProse)
    assert replaced.text == "A house Level 2 list."
    service = _service(persisted, built, monkeypatch, _disable(cls))
    refused = service.rule_slice(_request(built, cls))
    assert refused.outcome is AuthorityOutcome.INVALID_REFERENCE


SCALING = "using_a_higher_level_spell_slot"
FUSED = {"Giant Insect", "Ice Storm", "Wall of Ice"}


def test_a_scaling_rule_fused_into_a_leaf_is_its_own_component(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    # The matcher family: only these three leaves print a trailing label after
    # a line break, and no component text keeps one.
    assert {
        n
        for n in GEN.SPELL_NAMES
        if any(GEN.FUSED_TRAILING.search(t) for t in GEN.texts_at(GEN.SECTION + (n,)))
    } == FUSED
    assert not [
        t
        for _, _, _, ts in GEN.SPELL_CHUNK.clauses
        for t in ts
        if GEN.FUSED_TRAILING.search(t)
    ]
    records = tuple(GEN.spell_key(n) for n in sorted(FUSED))
    service = _service(persisted, built, monkeypatch)
    # Selected by component, each reads exactly its scaling rule.
    view = service.gamemaster_view(
        _request(built, components=tuple((r, SCALING) for r in records))
    )
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    selected = [
        (c.record_key, c.component_key, [e.text for e in c.governing_prose])
        for c in view.gamemaster_view.components
    ]
    assert [(r, k) for r, k, _ in selected] == [(r, SCALING) for r in records]
    assert all(
        len(ts) == 1 and ts[0].startswith("_Using a Higher-Level Spell Slot._ ")
        for _, _, ts in selected
    )
    printed = _read(service, built, *records)
    assert not [t for _, k, t in printed if k == "effect" and "Higher-Level" in t]
    # Replacing the scaling rule leaves every other passage as printed.
    replaced = [
        EffectiveOverrideEntry(
            override_id=f"replace-{r}-{SCALING}",
            origin=OverrideOriginEnum.HOUSE_RULE,
            target=MechanicalTarget(
                kind=MechanicalTargetKind.COMPONENT, record_key=r, component_key=SCALING
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
                    "authored_prose": "A house scaling rule.",
                },
            },
        )
        for r in records
    ]
    service = _service(persisted, built, monkeypatch, *replaced)
    view = service.gamemaster_view(_request(built, *records))
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    after = [
        (c.record_key, c.component_key, e)
        for c in view.gamemaster_view.components
        for e in c.governing_prose
    ]
    assert [(r, k, e.text) for r, k, e in after if k != SCALING] == [
        x for x in printed if x[1] != SCALING
    ]
    house = [e for _, k, e in after if k == SCALING]
    assert len(house) == 3 and all(
        isinstance(e, AuthoredProse) and e.text == "A house scaling rule."
        for e in house
    )
