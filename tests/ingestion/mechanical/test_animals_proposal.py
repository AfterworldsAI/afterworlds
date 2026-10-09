"""The ``animals`` proposal and its Owner acceptance -- CRD Issue 5d.

The *Animals* part below its heading, pp344-364, proposed by
``.claude/review-notes/issue-5d-animals-generator.py`` from the release 5c
actually publishes, with its resolution drafts, over the twenty-one batches
the *Monsters* recording wrote. ``issue-5d-animals-ACCEPT.py`` recorded both,
under the Owner's approval, into the committed oracle.

What is pinned, and why:

* the committed artifact is the superseded release's recorded proposal, by
  shape, and the drafts are what the generator drafts over the committed
  oracle; the generator no longer builds over the current release (its
  in-place reads look up the superseded package), so what needed that build
  (the derived bytes, the batch checks, the reads from the release) is
  retired, see
  ``.claude/review-notes/issue-5c-release-readiness/correction-followup.md``;
* the qualified texts are the current release's leaves in its order;
* grain: 95 creature records, one prose component per printed container,
  every leaf of the part claimed once, no accepted authority shares a name;
* references name exact accepted records;
* each component reads, in place, only accepted *Parts of a Stat Block* spans,
  the texts the *Monsters* generator selects for the same print;
* the recorded proposal, composed in memory over that prior (both the
  superseded release's): it accepts, then the drafts resolve; every accepted
  byte is preserved, exactly the part's leaves gain coverage, and only chapter
  pointers stay open (judging coverage against a corpus needs the superseded
  release's, which is not rebuilt; that check is retired);
* the committed oracle is exactly that composition under the Owner's approval
  at the recorded times, keeping the prior whole;
* through the production rules-authority service, over the current accepted
  authority persisted as one draft into the current release: an
  animal reads, per printed container, the governing rules not yet read and
  then its own text (the current release prints *Monsters* before *Animals*,
  as ``issue-5c-release-order-candidate.md``'s reader proof records); a
  disable or override of a governing rule's owner suppresses its printed text
  on the animal, and an override's house text stays with the rules
  owner; selected together with the owner or a *Monsters* creature, each
  governing span is read once.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

import pytest

from afterworlds.ingestion.mechanical.acceptance import (
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    AcceptedOracle,
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
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, load_proposal
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import RecordKind
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.corpus import LedgerLeafORM
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from tests.ingestion.mechanical._replacement_chain import ANIMALS as ACCEPT
from tests.ingestion.mechanical._replacement_chain import (
    ANIMALS_CATALOGUE,
    CHARACTER_CREATION,
    COMMITTED_SHA256,
    EQUIPMENT_CITED,
    EQUIPMENT_CLASS_ELIGIBILITY,
    EQUIPMENT_SPELL_REFERENCES,
    FINAL_TEN_REFERENCES,
    FINITE_REFERENCE,
    FINITE_REFERENCE_ROUTES,
    FRAMING,
    PLAYING_THE_GAME,
    REFERENCE_ALTERNATIVES,
    REMAINING,
    animals_catalogue_recorded,
    animals_recorded,
    character_creation_recorded,
    current,
    equipment_class_eligibility_recorded,
    equipment_recorded,
    equipment_spell_references_recorded,
    finite_reference_recorded,
    finite_reference_routes_recorded,
    framing_recorded,
    monsters_recorded,
    playing_the_game_recorded,
    reference_alternatives_recorded,
    remaining_recorded,
)
from tests.ingestion.mechanical._replacement_chain import REPLACEMENT as RECORDING
from tests.ingestion.mechanical._schema_pins import lifted
from tests.ingestion.mechanical.test_character_origins_feats_proposal import (
    _request,
    _service,
    _sliced,
)
from tests.ingestion.mechanical.test_magic_items_proposal import (
    _disable_component,
    _replace,
)

REPO = Path(__file__).resolve().parents[3]
NOTES = REPO / ".claude" / "review-notes"
ORACLES = REPO / "src/afterworlds/ingestion/mechanical/oracles"
MONSTERS = "srd-5.2.1/monsters"
ANIMALS = "srd-5.2.1/animals"

#: The generator the recording drafted with, so both share one rebuilt prior.
GEN = ACCEPT.GEN
MG = GEN.MG
PROPOSAL = NOTES / GEN.PROPOSAL_FILE
DRAFTS = NOTES / GEN.DRAFTS_FILE
IDENTITY = "19685bc2b3c9a22d484b0435ba78950185dab00590a58bae36c8f41ca2fb53cd"
PROPOSAL_SHA256 = "a3057b73ec23db2bf169286446e25047ef7d54ebc96061083e3c9a2d48045ebb"
DRAFTS_SHA256 = "924ef579a879f73c1281d1263ba8c49f166302a11578808814a3d05f776766ac"
PARTS = "monsters.parts_of_a_stat_block"
WOLF = "animals.wolf"
OWL = "animals.giant_owl"
ABOLETH = "monsters.aboleth.aboleth"


@pytest.fixture(scope="module")
def session(source_release_db: Path):  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{source_release_db}")
    with create_session_factory(engine)() as s:
        yield s
    engine.dispose()


@pytest.fixture(scope="module")
def bound() -> AcceptedOracle:
    """The current release's accepted authority: what the service reads."""
    return current().oracle


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


@pytest.fixture(scope="module")
def prior() -> AcceptedInputs:
    """The twenty-one batches this packet composed over, rebuilt from the
    Monsters recording at its recorded bytes."""
    inputs: AcceptedInputs = monsters_recorded()
    assert inputs is GEN.current()
    data = serialize_accepted_inputs(inputs)
    assert hashlib.sha256(data).hexdigest() == GEN.CURRENT_SHA256
    assert RECORDING.RECORDED_SHA256["resolved"] == GEN.CURRENT_SHA256
    return inputs


def _printed(*path: str) -> list[str]:
    return [t for p, t in GEN.LEAVES if p[: len(path)] == path]


def _refs(p: MechanicalProposal) -> set[tuple[str, str, str, str, str]]:
    return {
        (
            r.from_record_key,
            r.from_component_key,
            r.source_text,
            r.scope_key,
            r.target_record_key,
        )
        for r in p.proposed_representation.references
    }


# ---------------------------------------------------------------------------
# The artifacts
# ---------------------------------------------------------------------------


def test_the_committed_artifact_is_the_recorded_proposal_by_shape(  # type: ignore[no-untyped-def]
    recorded, prior
) -> None:
    data = PROPOSAL.read_bytes()
    assert hashlib.sha256(data).hexdigest() == PROPOSAL_SHA256
    assert b"\r" not in data
    # The recorded proposal and its drafts bind the recorded chain's release.
    assert recorded.binding == prior.oracle.binding
    drafts = GEN.draft_resolutions(prior.oracle.binding, prior=prior)
    assert list(reference_resolution_payload(drafts)) == json.loads(DRAFTS.read_bytes())
    assert hashlib.sha256(DRAFTS.read_bytes()).hexdigest() == DRAFTS_SHA256


def test_the_qualified_texts_are_the_release_leaves_in_order(session, bound) -> None:  # type: ignore[no-untyped-def]
    rows = (
        session.query(LedgerLeafORM)
        .filter(LedgerLeafORM.package_uuid == bound.binding.package_uuid)
        .order_by(LedgerLeafORM.occurrence_index)
        .all()
    )
    texts = [t for _, t in GEN.LEAVES]
    (start,) = [i for i, r in enumerate(rows) if r.content == texts[0]]
    assert [r.content for r in rows[start : start + len(texts)]] == texts
    # Every ability table prints MOD then SAVE for each score, and each
    # modifier is the score's.
    tables = [t for _, t in GEN.LEAVES if t.startswith("<table>")]
    assert len(tables) == len(GEN.NAMES)
    assert all(t.count("<th>MOD</th>") == t.count("<th>SAVE</th>") == 3 for t in tables)


#: The plurals the accepted sources print, to the stat blocks they name.
BUDGET = ("gameplay_toolbox.combat_encounters", "step_3_spend_your_budget")
PLURALS = {
    (*BUDGET, "Giant Wasps"): "animals.giant_wasp",
    (*BUDGET, "Giant Rats"): "animals.giant_rat",
    (
        "magic_items.robe_of_useful_items",
        "robe_of_useful_items",
        "Mastiffs",
    ): "animals.mastiff",
}


def test_each_draft_names_the_one_stat_block_its_text_prints(prior) -> None:  # type: ignore[no-untyped-def]
    drafts, left = GEN.draft_targets(prior)
    assert (len(drafts), len(left)) == (65, 19)
    plural = {
        (r, c, text): target
        for r, c, text, _, target, _ in drafts
        if text not in GEN.ANIMAL_KEY
    }
    assert plural == PLURALS
    for _, _, text, scope, target, spans in drafts:
        assert spans and scope in (MONSTERS, ANIMALS)
        assert text not in GEN.ANIMAL_KEY or GEN.ANIMAL_KEY[text] == target
    # Wild Shape's recommended forms keep their own "Animals" scope.
    assert sorted(
        (text, target) for r, _, text, scope, target, _ in drafts if scope == ANIMALS
    ) == [
        ("Rat", "animals.rat"),
        ("Riding Horse", "animals.riding_horse"),
        ("Spider", "animals.spider"),
        ("Wolf", "animals.wolf"),
    ]
    # Only chapter pointers stay open.
    assert Counter((scope, text) for _, _, text, scope in left) == {
        (ANIMALS, "Animals"): 2,
        (MONSTERS, "Monsters"): 17,
    }


# ---------------------------------------------------------------------------
# Grain
# ---------------------------------------------------------------------------


def test_the_records_are_the_stat_blocks(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    # Both sides are the superseded release's: the recorded chain and proposal.
    rep = recorded.proposed_representation
    assert Counter(r.kind for r in rep.records) == {RecordKind.CREATURE: 95}
    assert len(recorded.proposed_spans) == len(GEN.LEAVES) == 835
    assert {c.handling for c in rep.components} == {ComponentHandling.PROSE_BOUND}
    assert len(rep.components) == 253
    # The recorded artifact holds components in canonical order; the print
    # order was the retired generator build's, not a recorded byte.
    owl = [c.semantic_key for c in rep.components if c.record_key == OWL]
    assert owl == ["actions", "giant_owl", "traits"]
    # No accepted record, Monsters stat block, Spell or Item creature holds
    # an Animals stat block.
    accepted = {r.semantic_key for r in prior.oracle.representation.records}
    assert not accepted & {r.semantic_key for r in rep.records}
    names = {k.rsplit(".", 1)[-1] for k in accepted}
    assert not names & {k.removeprefix("animals.") for k in GEN.ANIMAL_KEY.values()}


def test_references_name_exact_accepted_records(recorded) -> None:  # type: ignore[no-untyped-def]
    refs = _refs(recorded)
    spells = "srd-5.2.1/spells"
    assert {(r[2], r[4]) for r in refs if r[3] == spells} == {
        ("Detect Evil and Good", "spells.detect_evil_and_good"),
        ("Detect Magic", "spells.detect_magic"),
        ("Clairvoyance", "spells.clairvoyance"),
    }
    assert {r[:2] for r in refs if r[3] == spells} == {(OWL, "actions")}
    # Every target is an accepted record, none this packet's own.
    assert all(r[4] and not r[4].startswith("animals.") for r in refs)


def test_each_component_reads_the_accepted_rules_monsters_selects(  # type: ignore[no-untyped-def]
    recorded, prior
) -> None:
    # Both sides are the superseded release's: the recorded chain and proposal.
    rep = recorded.proposed_representation
    read: dict[tuple[str, str], list[str]] = {}
    own_spans = {p.span.span_id for p in recorded.proposed_spans}
    for b in rep.prose_bindings:
        if b.span_id not in own_spans:
            read.setdefault((b.record_key, b.component_key), []).append(b.span_id)
    assert sum(map(len, read.values())) == 1133
    assert set(read) == set(GEN.ANIMALS_CHUNK.context)
    accepted = {
        b.span_id
        for b in prior.oracle.representation.prose_bindings
        if b.record_key == PARTS
    }
    assert {s for ss in read.values() for s in ss} <= accepted
    # The same texts a Monsters stat block would read for the same print.
    wolf = GEN.ANIMALS_CHUNK.context[(WOLF, "wolf")]
    assert wolf == tuple(
        t for t, _ in MG.header_context(tuple(_printed("Animals", "Wolf")))
    )
    for text in (MG.ALIGNMENT, MG.HIT_POINTS, MG.RUNNING):
        assert text in wolf
    assert set(MG.SPELLCASTING) <= set(GEN.ANIMALS_CHUNK.context[(OWL, "actions")])
    assert not any(
        set(MG.SPELLCASTING) & set(ctx)
        for key, ctx in GEN.ANIMALS_CHUNK.context.items()
        if key != (OWL, "actions")
    )


# ---------------------------------------------------------------------------
# Test-only composition with the committed oracle
# ---------------------------------------------------------------------------


def _accepted(prior: AcceptedInputs, proposal: MechanicalProposal) -> AcceptedInputs:
    return accept_proposal(
        proposal,
        batch_id="animals",
        rule="test-only",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer="test",
        accepted_at="2026-09-28T00:00:00Z",
        prior=prior,
    )


def _covered(inputs: AcceptedInputs) -> set[str]:
    oracle = inputs.oracle
    return {s.leaf_id for s in oracle.spans} | {
        leaf for u in oracle.review_units for leaf in u.leaf_ids
    }


def _findings(inputs: AcceptedInputs) -> list[str]:
    # The representation's own relationship and reference findings
    # (resolutions applied): no corpus, so none of the superseded release's is
    # needed. Its leaf findings judged that corpus and are retired.
    rep = candidate_from_accepted_inputs(lifted(inputs)).representation
    return relationship_and_reference_violations(rep)


def test_accepted_then_resolved_in_memory_preserves_everything(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    on_disk = {p.name: p.read_bytes() for p in ORACLES.iterdir()}
    base = prior.oracle
    assert (
        len(prior.batches),
        len(base.representation.records),
        len(base.spans),
        len(base.review_units),
        len(base.reference_resolutions),
    ) == (21, 1664, 9589, 1364, 1182)
    # Both sides are the superseded release's: the recorded chain and proposal.
    assert recorded.binding == base.binding
    refs_before = _findings(prior)
    assert len(refs_before) == 317

    drafts = GEN.draft_resolutions(base.binding, prior=prior)
    resolved = resolve_references(
        _accepted(prior, recorded),
        resolutions=drafts,
        authorized_by="test",
        authorization_reference="test-only",
        reviewer="test",
        resolved_at="2026-09-28T00:00:01Z",
    )
    final = resolved.oracle
    # Append-only: every accepted byte the authority holds is still held.
    old, new = accepted_inputs_payload(prior), accepted_inputs_payload(resolved)
    assert not RECORDING._preserved(old, new)
    assert resolved.batches[: len(prior.batches)] == prior.batches
    assert (
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (1664 + 95, 9589 + 835, 1364 + 95, 1182 + 65)
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )
    # Exactly the part's leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(resolved) - _covered(prior) == mine
    assert len(mine) == 835
    rest = _findings(resolved)
    # Every accepted target and read closes; only the chapter pointers remain.
    drafted = Counter(
        f"reference {r.scope_key}:{r.source_text!r}: unresolved reference"
        for r in drafts
    )
    assert Counter(rest) == Counter(refs_before) - drafted
    assert len(rest) == 317 - 65
    assert {p.name: p.read_bytes() for p in ORACLES.iterdir()} == on_disk


def test_the_committed_oracle_records_the_owner_acceptance(prior) -> None:  # type: ignore[no-untyped-def]
    # The superseded release's committed file, read by path: the production
    # resolver refuses its binding.
    on_disk = load_accepted_inputs(ACCEPT.ACCEPTED_PATH)
    assert serialize_accepted_inputs(on_disk) == ACCEPT.ACCEPTED_PATH.read_bytes()
    # The file now records the Equipment replacement, then the
    # remaining-references one; the Animals recording, the Owner's two steps
    # over the prior rebuilt from their recorded times at their recorded bytes,
    # is kept in the Equipment recording outside Equipment, evidence included.
    committed = animals_recorded()
    data = serialize_accepted_inputs(committed)
    assert hashlib.sha256(data).hexdigest() == ACCEPT.RECORDED_SHA256["resolved"]
    assert not EQUIPMENT_CITED._outside(committed, equipment_recorded())
    # The prior is kept whole, times and approvals included, and Animals is
    # the one batch added over it.
    assert not RECORDING._preserved(
        accepted_inputs_payload(prior), accepted_inputs_payload(committed)
    )
    assert [
        b
        for b in accepted_inputs_payload(committed)["acceptance"]["batches"]
        if b["batch_id"] != "animals"
    ] == accepted_inputs_payload(prior)["acceptance"]["batches"]
    (batch,) = [b for b in committed.batches if b.batch_id == "animals"]
    assert (batch.proposal_identity, batch.rule) == (IDENTITY, ACCEPT.APPROVAL)
    accepted_at, resolved_at = ACCEPT.RECORDED_AT
    mine = [
        a
        for a in (*committed.acceptances, *committed.review_unit_acceptances)
        if a.batch_id == "animals"
    ]
    assert len(mine) == 835 + 95
    assert {(a.reviewer, a.accepted_at) for a in mine} == {(ACCEPT.OWNER, accepted_at)}
    drafts = GEN.draft_resolutions(prior.oracle.binding, prior=prior)
    new = {r.resolution_id for r in drafts}
    auths = [
        a for a in committed.reference_resolution_acceptances if a.resolution_id in new
    ]
    assert len(auths) == len(new) == 65
    assert {
        (a.authorized_by, a.reviewer, a.resolved_at, a.authorization_reference)
        for a in auths
    } == {(ACCEPT.OWNER, ACCEPT.OWNER, resolved_at, ACCEPT.AUTHORIZATION_REFERENCE)}
    assert ACCEPT.OWNER_REVIEW_SHA256 in ACCEPT.AUTHORIZATION_REFERENCE
    final = committed.oracle
    assert (
        len(committed.batches),
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (22, 1759, 10424, 1459, 1247)
    refs = _findings(committed)
    assert len(refs) == 252
    assert all(f.startswith("reference ") for f in refs)


def test_the_committed_oracle_records_the_equipment_replacement() -> None:  # type: ignore[no-untyped-def]
    # The file now records the remaining-references replacement; the Equipment
    # recording, the Owner's two steps over the Animals recording rebuilt from
    # their recorded times at their recorded bytes, is kept there outside the
    # eight replaced batches.
    committed = equipment_recorded()
    data = serialize_accepted_inputs(committed)
    assert hashlib.sha256(data).hexdigest() == (
        EQUIPMENT_CITED.RECORDED_SHA256["resolved"]
    )
    assert not EQUIPMENT_CITED._outside(animals_recorded(), committed)
    assert not EQUIPMENT_CITED._approvals(committed)
    (batch,) = [b for b in committed.batches if b.batch_id == "equipment"]
    assert (batch.proposal_identity, batch.rule) == (
        EQUIPMENT_CITED.IDENTITY,
        EQUIPMENT_CITED.APPROVAL,
    )
    assert EQUIPMENT_CITED._read_back(committed) == EQUIPMENT_CITED.RECORDED_AT
    final = committed.oracle
    assert (
        len(committed.batches),
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (22, 1826, 10484, 1459, 1408)
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )
    refs = _findings(committed)
    assert len(refs) == 91
    assert all(f.startswith("reference ") for f in refs)


def test_the_remaining_references_recording_is_kept() -> None:  # type: ignore[no-untyped-def]
    # The file now records the Animals catalogue replacement; the
    # remaining-references recording, the Owner's two steps over the Equipment
    # recording rebuilt from their recorded times at their recorded bytes, is
    # kept there outside Animals.
    committed = remaining_recorded()
    data = serialize_accepted_inputs(committed)
    assert hashlib.sha256(data).hexdigest() == REMAINING.RECORDED_SHA256["resolved"]
    assert serialize_accepted_inputs(REMAINING.recorded()) == data
    prior = equipment_recorded()
    assert not REMAINING._kept(prior, committed)
    assert not REMAINING._approvals(committed)
    assert REMAINING._read_back(committed) == REMAINING.RECORDED_AT
    assert {
        b.batch_id: (b.proposal_identity, b.rule)
        for b in committed.batches
        if b.batch_id in REMAINING.PROPOSALS
    } == {b: (i, REMAINING.APPROVAL) for b, (i, _) in REMAINING.PROPOSALS.items()}
    assert REMAINING._expectations(prior, committed) == (10432, 10432, 38, 10, 0, 0)
    final = committed.oracle
    assert (
        len(committed.batches),
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (22, 1832, 10484, 1459, 1434)
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )
    refs = _findings(committed)
    assert len(refs) == 68
    assert all(f.startswith("reference ") for f in refs)


def test_the_animals_catalogue_recording_is_kept() -> None:  # type: ignore[no-untyped-def]
    # The file now records the framing-coverage batch; the Animals catalogue
    # recording, the Owner's two steps over the remaining-references recording
    # rebuilt from their recorded times at their recorded bytes, is kept whole.
    committed = animals_catalogue_recorded()
    data = serialize_accepted_inputs(committed)
    assert hashlib.sha256(data).hexdigest() == (
        ANIMALS_CATALOGUE.RECORDED_SHA256["resolved"]
    )
    prior = remaining_recorded()
    assert not ANIMALS_CATALOGUE._kept(prior, committed)
    assert not ANIMALS_CATALOGUE._approvals(committed)
    assert ANIMALS_CATALOGUE._read_back(committed) == ANIMALS_CATALOGUE.RECORDED_AT
    (batch,) = [b for b in committed.batches if b.batch_id == "animals"]
    assert (batch.proposal_identity, batch.rule) == (
        ANIMALS_CATALOGUE.IDENTITY,
        ANIMALS_CATALOGUE.APPROVAL,
    )
    assert ANIMALS_CATALOGUE._reowned(committed) == (836, 96)
    assert ANIMALS_CATALOGUE._expectations(prior, committed) == (10432, 10433, 0, 1)
    final = committed.oracle
    assert (
        len(committed.batches),
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (22, 1833, 10485, 1460, 1438)
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )
    refs = _findings(committed)
    assert len(refs) == 64
    assert all(f.startswith("reference ") for f in refs)


def test_the_framing_coverage_recording_rebuilds() -> None:  # type: ignore[no-untyped-def]
    # The framing-coverage recording, rebuilt from its recorded time: the
    # Owner's one step over the Animals catalogue recording.
    recorded = framing_recorded()
    data = serialize_accepted_inputs(recorded)
    assert hashlib.sha256(data).hexdigest() == FRAMING.RECORDED_SHA256["recorded"]
    prior = animals_catalogue_recorded()
    at = FRAMING._read_back(recorded)
    assert (at,) == FRAMING.RECORDED_AT
    assert serialize_accepted_inputs(FRAMING.composed(prior, FRAMING.OWNER, at)) == data
    assert not FRAMING._approvals(recorded)
    (batch,) = [b for b in recorded.batches if b.batch_id == FRAMING.BATCH]
    assert (batch.proposal_identity, batch.rule) == (FRAMING.IDENTITY, FRAMING.APPROVAL)
    # Counts, no violations, the prior kept whole, the reviewed DELTA, and
    # no span on the unit-only leaves.
    # The version-pinned verifier judges at this build's schema, so both
    # sides are carried across the registered crossings first; the byte
    # and replay assertions above stay on the recorded artifact itself.
    FRAMING._check("recorded", lifted(prior), lifted(recorded))
    refs = _findings(recorded)
    assert len(refs) == 64
    assert all(f.startswith("reference ") for f in refs)


def test_the_character_creation_catalogue_recording_rebuilds() -> None:  # type: ignore[no-untyped-def]
    # The Character Creation catalogue recording, rebuilt from its recorded
    # times: the Owner's two native steps over the framing-coverage recording.
    # The committed file keeps it outside the five finite-reference batches.
    recorded = character_creation_recorded()
    data = serialize_accepted_inputs(recorded)
    assert hashlib.sha256(data).hexdigest() == (
        CHARACTER_CREATION.RECORDED_SHA256["recorded"]
    )
    prior = framing_recorded()
    acc_at, res_at = CHARACTER_CREATION._read_back(recorded)
    assert (acc_at, res_at) == CHARACTER_CREATION.RECORDED_AT
    assert not CHARACTER_CREATION._approvals(recorded)
    (batch,) = [b for b in recorded.batches if b.batch_id == CHARACTER_CREATION.BATCH]
    assert (batch.proposal_identity, batch.rule) == (
        CHARACTER_CREATION.IDENTITY,
        CHARACTER_CREATION.APPROVAL,
    )
    # Counts, no violations, the two cleared findings, the prior kept whole,
    # the six members and framing unit unchanged, and the reviewed DELTA.
    # The version-pinned verifier judges at this build's schema, so both
    # sides are carried across the registered crossings first; the byte
    # and replay assertions above stay on the recorded artifact itself.
    CHARACTER_CREATION._check("recorded", lifted(prior), lifted(recorded))
    refs = _findings(recorded)
    assert len(refs) == 62
    assert all(f.startswith("reference ") for f in refs)


def test_the_finite_reference_atoms_recording_rebuilds() -> None:  # type: ignore[no-untyped-def]
    # The finite-reference atoms recording, rebuilt from its recorded time:
    # the Owner's one native step over the Character Creation catalogue
    # recording. The committed file keeps it outside the two Playing the Game
    # batches.
    recorded = finite_reference_recorded()
    data = serialize_accepted_inputs(recorded)
    assert hashlib.sha256(data).hexdigest() == (
        FINITE_REFERENCE.RECORDED_SHA256["recorded"]
    )
    assert FINITE_REFERENCE._read_back(recorded) == FINITE_REFERENCE.RECORDED_AT
    assert not FINITE_REFERENCE._approvals(recorded)
    assert {
        b.batch_id: (b.proposal_identity, b.rule)
        for b in recorded.batches
        if b.batch_id in FINITE_REFERENCE.PROPOSALS
    } == {
        b: (i, FINITE_REFERENCE.APPROVAL)
        for b, (i, _) in FINITE_REFERENCE.PROPOSALS.items()
    }
    # Counts, no violations, the ten cleared findings, the nineteen other
    # batches and all 1440 resolutions kept, prose, expectations and consumer
    # reading unchanged, and the reviewed DELTA.
    # The version-pinned verifier judges at this build's schema, so both
    # sides are carried across the registered crossings first; the byte
    # and replay assertions above stay on the recorded artifact itself.
    FINITE_REFERENCE._check(
        "recorded", lifted(character_creation_recorded()), lifted(recorded)
    )
    refs = _findings(recorded)
    assert len(refs) == 52
    assert all(f.startswith("reference ") for f in refs)


def test_the_playing_the_game_atoms_recording_rebuilds() -> None:  # type: ignore[no-untyped-def]
    # The Playing the Game atoms recording, rebuilt from its recorded time:
    # the Owner's one native step over the finite-reference atoms recording.
    # The committed file keeps it outside Equipment.
    recorded = playing_the_game_recorded()
    data = serialize_accepted_inputs(recorded)
    assert hashlib.sha256(data).hexdigest() == (
        PLAYING_THE_GAME.RECORDED_SHA256["recorded"]
    )
    assert PLAYING_THE_GAME._read_back(recorded) == PLAYING_THE_GAME.RECORDED_AT
    assert not PLAYING_THE_GAME._approvals(recorded)
    assert {
        b.batch_id: (b.proposal_identity, b.rule)
        for b in recorded.batches
        if b.batch_id in PLAYING_THE_GAME.PROPOSALS
    } == {
        b: (i, PLAYING_THE_GAME.APPROVAL)
        for b, (i, _) in PLAYING_THE_GAME.PROPOSALS.items()
    }
    # Counts, no violations, the three cleared findings, the twenty-two other
    # batches and all 1440 resolutions kept, prose, expectations and consumer
    # reading unchanged, and the reviewed DELTA.
    # The version-pinned verifier judges at this build's schema, so both
    # sides are carried across the registered crossings first; the byte
    # and replay assertions above stay on the recorded artifact itself.
    PLAYING_THE_GAME._check(
        "recorded", lifted(finite_reference_recorded()), lifted(recorded)
    )
    refs = _findings(recorded)
    assert len(refs) == 49
    assert all(f.startswith("reference ") for f in refs)


def test_the_equipment_class_eligibility_recording_rebuilds() -> None:  # type: ignore[no-untyped-def]
    # The Equipment class-eligibility recording, rebuilt from its recorded
    # time: the Owner's one native step over the Playing the Game atoms
    # recording. The committed file keeps it whole under the reference-routes
    # lift and resolutions.
    ece = EQUIPMENT_CLASS_ELIGIBILITY
    recorded = equipment_class_eligibility_recorded()
    data = serialize_accepted_inputs(recorded)
    assert hashlib.sha256(data).hexdigest() == ece.RECORDED_SHA256["recorded"]
    assert ece._read_back(recorded) == ece.RECORDED_AT
    assert not ece._approvals(recorded)
    assert {
        b.batch_id: (b.proposal_identity, b.rule)
        for b in recorded.batches
        if b.batch_id in ece.PROPOSALS
    } == {b: (i, ece.APPROVAL) for b, (i, _) in ece.PROPOSALS.items()}
    # Counts, no violations, the three cleared findings, the twenty-three
    # other batches and all 1440 resolutions kept, prose, expectations and
    # consumer reading unchanged, and the reviewed DELTA.
    # The version-pinned verifier judges at this build's schema, so both
    # sides are carried across the registered crossings first; the byte
    # and replay assertions above stay on the recorded artifact itself.
    ece._check("recorded", lifted(playing_the_game_recorded()), lifted(recorded))
    refs = _findings(recorded)
    assert len(refs) == 46
    assert all(f.startswith("reference ") for f in refs)


def test_the_reference_alternatives_recording_rebuilds() -> None:  # type: ignore[no-untyped-def]
    # The reference-alternatives recording, rebuilt from its recorded time:
    # the Owner's one native action over the Equipment class-eligibility
    # recording. The committed file keeps it outside combat-damage-breaking.
    rar = REFERENCE_ALTERNATIVES
    prior = equipment_class_eligibility_recorded()
    recorded = reference_alternatives_recorded()
    data = serialize_accepted_inputs(recorded)
    assert hashlib.sha256(data).hexdigest() == rar.RECORDED_SHA256["recorded"]
    assert rar._read_back(prior, recorded) == rar.RECORDED_AT
    assert not rar._approvals(prior, recorded)
    # Counts, no violations, the thirteen cleared findings, the 24 batches
    # and all 1440 resolutions and their approvals kept, 13 resolutions with
    # 132 routes and 197 destinations, and the reviewed DELTA.
    rar._check("recorded", prior, recorded)
    refs = _findings(recorded)
    assert len(refs) == 33
    assert all(f.startswith("reference ") for f in refs)


def test_the_finite_reference_routes_recording_rebuilds() -> None:  # type: ignore[no-untyped-def]
    # The finite-reference-routes recording, rebuilt from its recorded time:
    # the Owner's one native action over the reference-alternatives
    # recording. The committed file keeps it whole.
    frr = FINITE_REFERENCE_ROUTES
    recorded = finite_reference_routes_recorded()
    data = serialize_accepted_inputs(recorded)
    assert hashlib.sha256(data).hexdigest() == frr.RECORDED_SHA256["recorded"]
    assert frr._read_back(recorded) == frr.RECORDED_AT
    assert not frr._approvals(recorded)
    # Counts, no violations, the ten cleared findings, the 23 other batches
    # and all 1453 resolutions and their approvals kept, 10 resolutions with
    # 94 routes and 121 destinations, and the reviewed DELTA.
    frr._check("recorded", reference_alternatives_recorded(), recorded)
    refs = _findings(recorded)
    assert len(refs) == 23
    assert all(f.startswith("reference ") for f in refs)


def test_the_equipment_spell_references_recording_rebuilds() -> None:  # type: ignore[no-untyped-def]
    # The equipment-spell-references recording, rebuilt from its recorded
    # time: the Owner's one native action over the finite-reference-routes
    # recording. The committed file keeps it whole.
    esr = EQUIPMENT_SPELL_REFERENCES
    recorded = equipment_spell_references_recorded()
    data = serialize_accepted_inputs(recorded)
    assert hashlib.sha256(data).hexdigest() == esr.RECORDED_SHA256["recorded"]
    assert esr._read_back(recorded) == esr.RECORDED_AT
    assert not esr._approvals(recorded)
    # Counts, no violations, the thirteen cleared findings, the 24 batches
    # and all 1463 resolutions and their approvals kept, 13 resolutions with
    # 15 routes and 62 destinations, and the reviewed DELTA.
    esr._check("recorded", finite_reference_routes_recorded(), recorded)
    refs = _findings(recorded)
    assert len(refs) == 10
    assert all(f.startswith("reference ") for f in refs)


def test_the_committed_oracle_records_final_ten_references() -> None:  # type: ignore[no-untyped-def]
    data = ACCEPT.ACCEPTED_PATH.read_bytes()
    assert hashlib.sha256(data).hexdigest() == COMMITTED_SHA256
    # The superseded release's committed file, read by path: the production
    # resolver refuses its binding.
    committed = load_accepted_inputs(ACCEPT.ACCEPTED_PATH)
    assert serialize_accepted_inputs(committed) == data
    # The Owner's one native action: the equipment-spell-references recording
    # with the ten reviewed resolutions appended, at the recorded time.
    ften = FINAL_TEN_REFERENCES
    prior = equipment_spell_references_recorded()
    assert ften._read_back(committed) == ften.RECORDED_AT
    assert (
        serialize_accepted_inputs(ften.recorded(prior, ften.OWNER, ften.RECORDED_AT))
        == data
    )
    assert not ften._approvals(committed)
    # Counts, no violations, the ten cleared findings, the 24 batches and all
    # 1476 resolutions and their approvals kept, 10 resolutions with 144
    # routes and 201 destinations, and the reviewed PROPOSAL and DELTA.
    ften._check("recorded", prior, committed)
    refs = _findings(committed)
    assert len(refs) == 0


# ---------------------------------------------------------------------------
# Through the production rules-authority service
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db):  # type: ignore[no-untyped-def]
    """The current accepted authority, persisted as one draft into a private
    copy of the current release."""
    candidate = candidate_from_accepted_inputs(current())
    assert isinstance(candidate, ProjectionCandidate)
    path = tmp_path_factory.mktemp("animals") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(candidate)
        persist_draft(s, identified, now="2026-09-28T00:00:00Z")
        s.commit()
        yield s, identified.projection_uuid
    engine.dispose()


def _prose(service, bound, *records: str):  # type: ignore[no-untyped-def]
    view = service.gamemaster_view(_request(bound, *records))
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    return [e for c in view.gamemaster_view.components for e in c.governing_prose]


def _texts(service, bound, *records: str) -> list[str]:  # type: ignore[no-untyped-def]
    return [e.text for e in _prose(service, bound, *records)]


def _read(record: str) -> list[str]:
    """An animal read directly: per printed container, the governing rules not
    yet read, then its own texts, in source order (the current release prints
    *Monsters* before *Animals*)."""
    out: list[str] = []
    entry = record.removeprefix("animals.")
    for e, k, _, own in GEN.ANIMALS_CHUNK.clauses:
        if e == entry:
            out += [t for t in GEN.ANIMALS_CHUNK.context[(record, k)] if t not in out]
            out += own
    return out


def test_an_animal_reads_itself_with_the_rules_governing_it(  # type: ignore[no-untyped-def]
    persisted, bound, monkeypatch
) -> None:
    service = _service(persisted, bound, monkeypatch)
    assert _sliced(service, _request(bound, WOLF)) == [WOLF]
    for record in (WOLF, OWL, "animals.swarm_of_insects"):
        read = _texts(service, bound, record)
        assert read == _read(record), record
        own = [t for p, t in GEN.LEAVES if GEN.animal_key(p[1]) == record]
        assert [t for t in read if t in own] == own
    wolf = _texts(service, bound, WOLF)
    assert wolf.count(MG.HIT_POINTS) == wolf.count(MG.RUNNING) == 1
    assert set(MG.SPELLCASTING) <= set(_texts(service, bound, OWL))
    assert not set(MG.SPELLCASTING) & set(wolf)
    # Each read governing passage is the accepted rules span itself.
    parts = {e.span_id for e in _prose(service, bound, PARTS)}
    governing = set(GEN.ANIMALS_CHUNK.context[(WOLF, "wolf")])
    rules = [e for e in _prose(service, bound, WOLF) if e.text in governing]
    assert rules and {e.span_id for e in rules} <= parts


def test_suppressing_a_governing_rule_suppresses_it_on_the_animal(  # type: ignore[no-untyped-def]
    persisted, bound, monkeypatch
) -> None:
    full = _texts(_service(persisted, bound, monkeypatch), bound, WOLF)
    assert MG.HIT_POINTS in full
    off = _service(
        persisted, bound, monkeypatch, _disable_component(PARTS, "hit_points")
    )
    assert _texts(off, bound, WOLF) == [t for t in full if t != MG.HIT_POINTS]
    running = _service(
        persisted, bound, monkeypatch, _disable_component(PARTS, "running_a_monster")
    )
    assert _texts(running, bound, WOLF) == [t for t in full if t != MG.RUNNING]
    # A house rule replacing the owner suppresses the printed rule on the
    # animal; the house text stays with the rules owner, read when the owner is
    # selected, and is not propagated into the animal's contextual read.
    house = _service(
        persisted,
        bound,
        monkeypatch,
        _replace(PARTS, "hit_points", "House hit points."),
    )
    replaced = _texts(house, bound, WOLF)
    assert MG.HIT_POINTS not in replaced
    assert [t for t in replaced if t in full] == [t for t in full if t != MG.HIT_POINTS]


def test_selected_together_each_governing_span_is_read_once(  # type: ignore[no-untyped-def]
    persisted, bound, monkeypatch
) -> None:
    service = _service(persisted, bound, monkeypatch)
    for records in ((PARTS, WOLF), (WOLF, OWL), (ABOLETH, WOLF)):
        read = _texts(service, bound, *records)
        for text in (MG.HIT_POINTS, MG.ALIGNMENT, MG.RUNNING):
            assert read.count(text) == 1, (records, text)
        spans = [e.span_id for e in _prose(service, bound, *records)]
        assert len(spans) == len(set(spans)), records
