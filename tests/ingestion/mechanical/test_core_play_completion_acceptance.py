"""The core-play-completion batch in the replacement chain (#132, #137).

``.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``
accepted the regenerated core-play-completion proposal through
``accept_proposal`` with the eight-batch state *and* its attack-roll resolution
as ``prior``. These tests hold the state after this batch to the exact approved
proposal bytes, which the published release still derives, and to all of its
spans and units; to the eight prior batches and the one resolution retained
unchanged inside it; to the separate accepted ownership of Breaking Objects and
the unowned chapter title; and to a release that cannot publish: twenty-three
references stay unresolved. ``test_core_play_dependencies_acceptance`` holds
the next state.

The recorded states bind the superseded release, whose physical source is not
available: their findings are replayed representation-only and the former
uncovered-leaf claims are retired (``correction-followup.md``). The generator now
builds over the current release, so the recorded bytes are pinned by their
recorded identity and the current build by its own emit.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from afterworlds.ingestion.mechanical.bound_corpus import (
    leaves_under,
)
from afterworlds.ingestion.mechanical.models import ReviewState
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    candidate_from_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import load_proposal, proposal_identity
from afterworlds.ingestion.mechanical.reference_resolution import (
    effective_representation,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.corpus import LedgerLeafORM
from tests.ingestion.mechanical._replacement_chain import (
    BATCHES,
    REPLACEMENT,
    current,
    identity,
    proposal_path,
    through,
)
from tests.ingestion.mechanical._schema_pins import lifted

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"

PLAY, GLOSSARY = "srd-5.2.1/playing-the-game", "srd-5.2.1/rules-glossary"
EQUIPMENT, TOOLBOX = "srd-5.2.1/equipment", "srd-5.2.1/gameplay-toolbox"


def _glossary(text: str, slug: str) -> str:
    return f"reference {GLOSSARY}:'{text}': unknown target record glossary.{slug}"


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: What the eight prior batches left undefined: the three targets this batch
#: defines by holding their content.
CLOSED = sorted(
    [
        _glossary("Armor Class", "armor_class"),
        _glossary("Challenge Rating", "challenge_rating"),
        _glossary("Expertise", "expertise"),
    ]
)
#: What stays unresolved, explicitly: the seven accepted printed pointers with
#: no destination, and the sixteen this batch adds (eleven named glossary
#: entries nobody has authored, five pointers into parts with no record). No
#: destination is guessed.
OUTSTANDING = sorted(
    [_unresolved("srd-5.2.1/character-creation", "Character Creation")] * 2
    + [_unresolved(EQUIPMENT, "Equipment")] * 5
    + [_unresolved(GLOSSARY, "Rules Glossary")]
    + [_unresolved("srd-5.2.1/spells", "Spells")] * 2
    + [
        _unresolved(TOOLBOX, "Combat Encounters"),
        _unresolved(TOOLBOX, "Gameplay Toolbox"),
        _glossary("Attack Roll", "attack_roll"),
        _glossary("Blindsight", "blindsight"),
        _glossary("Burning", "burning"),
        _glossary("Darkvision", "darkvision"),
        _glossary("Dehydration", "dehydration"),
        _glossary("Malnutrition", "malnutrition"),
        _glossary("Stat Block", "stat_block"),
        _glossary("Suffocation", "suffocation"),
        _glossary("Tremorsense", "tremorsense"),
        _glossary("Truesight", "truesight"),
        _glossary("carrying capacity", "carrying_capacity"),
    ]
)
RECORDS = {
    "play.rhythm_of_play",
    "play.six_abilities",
    "play.social_interaction",
    "play.exploration",
    "glossary.armor_class",
    "glossary.challenge_rating",
    "glossary.expertise",
}
CITATION = ("play.combat", "attack_structure", "Playing the Game", PLAY)


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load(
    "core_play_completion_generator",
    NOTES / "issue-5d-core-play-completion-generator.py",
)
BATCH = "core-play-completion"
PROPOSAL = load_proposal(proposal_path(BATCH))
PRIOR = through("checks-actions-rests")
_binding = PROPOSAL.binding
INPUTS = through(BATCH)


def _citation(ref) -> tuple[str, str, str, str]:  # type: ignore[no-untyped-def]
    return (ref.from_record_key, ref.from_component_key, ref.source_text, ref.scope_key)


def test_all_eight_prior_batches_are_retained() -> None:
    batches = {b.batch_id: b for b in INPUTS.batches}
    # Only the restart's batches: nothing quarantined is inherited.
    assert sorted(batches) == [
        "actions-pilot",
        "checks-actions-rests",
        "combat-damage-breaking",
        "combat-turn-1",
        "conditions-pilot",
        "core-play-completion",
        "damage-and-hit-points",
        "movement-closure",
        "reference-closure",
    ]
    for prior in PRIOR.batches:
        retained = batches[prior.batch_id]
        # Loading orders the diff canonically; its entries and hash are unchanged.
        assert set(retained.diff) == set(prior.diff)
        assert dataclasses.replace(retained, diff=prior.diff) == prior
    assert set(PRIOR.acceptances) <= set(INPUTS.acceptances)
    assert set(PRIOR.review_unit_acceptances) <= set(INPUTS.review_unit_acceptances)


def test_it_records_the_owner_acceptance_of_the_exact_proposal() -> None:
    raw = proposal_path(BATCH).read_bytes()
    assert len(raw) == 113775 and b"\r" not in raw
    assert hashlib.sha256(raw).hexdigest() == BATCHES[BATCH][1]
    assert proposal_identity(PROPOSAL) == identity(BATCH)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "core-play-completion"]
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    assert {a.reviewer for a in INPUTS.acceptances} == {"Ravenlok (Owner)"}
    # One consolidated approval: every acceptance carries its single stamp.
    assert {a.accepted_at for a in INPUTS.acceptances} == {REPLACEMENT.ACCEPTED_AT}


def test_the_whole_scope_is_accepted_beside_the_eight_prior_batches() -> None:
    proposed = {p.span.span_id for p in PROPOSAL.proposed_spans}
    prior = {s.span_id for s in PRIOR.oracle.spans}
    assert (len(proposed), len(prior)) == (71, 555)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "core-play-completion"]
    assert set(batch.resolved_scope) == proposed
    assert {s.span_id for s in INPUTS.oracle.spans} == proposed | prior
    assert len(INPUTS.oracle.spans) == 626
    assert {s.review_state for s in INPUTS.oracle.spans} == {ReviewState.ACCEPTED}
    units = {u.unit_id for u in PROPOSAL.proposed_review_units}
    prior_units = {u.unit_id for u in PRIOR.oracle.review_units}
    assert (len(units), len(prior_units)) == (7, 74)
    assert {u.unit_id for u in INPUTS.oracle.review_units} == units | prior_units
    assert {a.unit_id for a in INPUTS.review_unit_acceptances} == units | prior_units
    assert sum(len(u.leaf_ids) for u in PROPOSAL.proposed_review_units) == 85
    assert INPUTS.oracle.binding == PROPOSAL.binding == PRIOR.oracle.binding
    assert INPUTS.lifts == () and INPUTS.policy_transitions == ()


def test_the_representation_is_both_accepted_representations_unchanged() -> None:
    combined = INPUTS.oracle.representation
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(PRIOR.oracle.representation, field.name)
        ) | set(getattr(PROPOSAL.proposed_representation, field.name)), field.name
    assert len(combined.records) == 81
    assert {r.semantic_key for r in PROPOSAL.proposed_representation.records} == (
        RECORDS
    )
    assert not RECORDS & {r.semantic_key for r in PRIOR.oracle.representation.records}


def test_the_one_resolution_and_its_original_citation_are_carried_unchanged() -> None:
    assert INPUTS.oracle.reference_resolutions == PRIOR.oracle.reference_resolutions
    (resolution,) = INPUTS.oracle.reference_resolutions
    assert (
        resolution.resolution_id,
        _citation(resolution),
        resolution.target_record_key,
    ) == ("resolve-attack-roll-playing-the-game-1", CITATION, "play.d20_tests")
    assert (
        INPUTS.reference_resolution_acceptances
        == PRIOR.reference_resolution_acceptances
    )
    (authorization,) = INPUTS.reference_resolution_acceptances
    assert authorization.resolved_at == REPLACEMENT.ACCEPTED_AT
    # The accepted citation keeps its empty target; only the effective view
    # gives it a destination.
    (accepted,) = [
        r for r in INPUTS.oracle.representation.references if _citation(r) == CITATION
    ]
    assert accepted.target_record_key == ""
    (effective,) = [
        r
        for r in effective_representation(
            INPUTS.oracle.representation, INPUTS.oracle.reference_resolutions
        ).references
        if _citation(r) == CITATION
    ]
    assert effective.target_record_key == "play.d20_tests"


@pytest.fixture(scope="module")
def session(source_release_db: Path):  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{source_release_db}")
    with create_session_factory(engine)() as s:
        yield s
    engine.dispose()


def _covered(inputs: AcceptedInputs) -> set[str]:
    oracle = inputs.oracle
    return {s.leaf_id for s in oracle.spans} | {
        leaf for u in oracle.review_units for leaf in u.leaf_ids
    }


def _references(inputs: AcceptedInputs) -> list[str]:
    # The effective representation's own relationship and reference findings
    # (resolutions applied). The recorded state binds the superseded release,
    # whose physical source is not available: representation-only replay.
    return relationship_and_reference_violations(
        candidate_from_accepted_inputs(lifted(inputs)).representation
    )


def test_the_recorded_bytes_stay_and_the_current_build_emits(  # type: ignore[no-untyped-def]
    session, source_release_db: Path, tmp_path: Path
) -> None:
    from afterworlds.ingestion.mechanical.authoring import emit

    # The recorded bytes stay the accepted proposal under its recorded identity.
    recorded = load_proposal(proposal_path(BATCH), expected_identity=identity(BATCH))
    assert proposal_identity(recorded) == identity(BATCH)
    # The generator builds over the current release; its output is no longer
    # the recorded bytes.
    built = GEN.build(session)
    assert built.binding == current().oracle.binding
    assert GEN.batch_findings(built)["partition"] == []
    assert GEN.batch_findings(built)["review_units"] == []
    out = tmp_path / "p.json"
    expected = GEN.expected_representation_findings()
    assert emit(str(source_release_db), lambda _s: built, out, expected) == 0
    assert out.read_bytes() == GEN.render(built.proposal).encode("utf-8")


def test_breaking_objects_stays_separately_owned_and_the_title_framed(  # type: ignore[no-untyped-def]
    session,
) -> None:
    # Read on the current release with its current accepted authority: the recorded
    # state binds the superseded release's package, whose ledger the source DB does not
    # hold (``source_leaf_order`` is package-scoped; the leaf ids themselves are
    # shared). Unit ids name no release.
    accepted = current()
    binding = accepted.oracle.binding
    owners: dict[str, list[str]] = {}
    for unit in accepted.oracle.review_units:
        for leaf in unit.leaf_ids:
            owners.setdefault(leaf, []).append(unit.unit_id)

    def under(*labels: str) -> set[str]:
        return set(
            leaves_under(session, binding.package_uuid, binding.release_version, labels)
        )

    def text(leaf: str) -> str:
        (content,) = (
            row.content
            for row in session.query(LedgerLeafORM).filter(
                LedgerLeafORM.package_uuid == binding.package_uuid,
                LedgerLeafORM.leaf_id == leaf,
            )
        )
        assert isinstance(content, str)
        return content

    # One leaf of the current authority has two owners, the other chapter's
    # title, which a later batch's framing unit also claims. It is not in
    # this chapter; every leaf here has at most one owner.
    shared = {leaf: units for leaf, units in owners.items() if len(units) > 1}
    assert {text(leaf): units for leaf, units in shared.items()} == {
        "# Character Creation": [
            "character-creation-catalogue/character_creation",
            "framing-coverage/character_creation",
        ]
    }
    assert not shared.keys() & under("Playing the Game")

    breaking = under(
        "Playing the Game",
        "Exploration",
        "Interacting with Objects",
        "Breaking Objects",
    )
    assert len(breaking) == 3
    assert {owners[leaf][0] for leaf in breaking} == {
        "combat-damage-breaking/exploration_breaking_objects"
    }
    # Every leaf of the chapter has one owner. Its title, ``# Playing the
    # Game``, sits outside every section: the recorded state left it unowned,
    # and the later framing batch's unit owns it alone. Named by its text.
    chapter = under("Playing the Game")
    assert chapter <= owners.keys()
    (title,) = [
        leaf
        for leaf in chapter
        if owners[leaf] == ["framing-coverage/playing_the_game"]
    ]
    assert text(title) == "# Playing the Game"


def test_three_targets_close_and_twenty_three_references_stay_unresolved() -> None:
    def references(inputs: AcceptedInputs) -> list[str]:
        findings = _references(inputs)
        return sorted(f for f in findings if f.startswith("reference "))

    before = references(PRIOR)
    assert set(CLOSED) <= set(before)
    assert references(INPUTS) == OUTSTANDING
    assert len(OUTSTANDING) == 23
    defined = {r.semantic_key for r in INPUTS.oracle.representation.records}
    assert defined >= RECORDS


def test_the_recorded_state_keeps_exactly_its_unresolved_references() -> None:
    # The superseded release's uncovered-leaf counts are retired with its
    # physical source (``correction-followup.md``).
    # The batch's units add exactly their own recorded leaves.
    assert _covered(INPUTS) - _covered(PRIOR) == {
        leaf for u in PROPOSAL.proposed_review_units for leaf in u.leaf_ids
    }
    # Unfiltered and representation-only: nothing else is reported.
    # Native refusal of an incomplete or unreviewed projection is pinned on the
    # current release by ``test_gate.py``
    # (``test_the_same_projection_claiming_no_unit_is_refused_as_incomplete``)
    # and ``test_source_release_readiness.py``
    # (``test_publishing_an_unreviewed_projection_is_typed_refused``).
    assert sorted(_references(INPUTS)) == OUTSTANDING
