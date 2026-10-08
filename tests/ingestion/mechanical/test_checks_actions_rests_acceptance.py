"""Checks-actions-rests and its resolution in the replacement chain (#132, #137).

``.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``
accepted the regenerated checks-actions-rests proposal in two native steps
under the one Owner approval: ``accept_proposal`` over the seven-batch state
through combat-damage-breaking, then ``resolve_references`` of the drafted
attack-roll resolution over that result. These tests hold the state after this
batch to the exact approved proposal bytes, which the published release still
derives, and to all of its spans and units; to the seven prior batches retained
unchanged inside it; to both steps, the resolution as an overlay that leaves the
accepted citation's empty target in place; and to a release that cannot
publish: ten references stay unresolved.
``test_core_play_completion_acceptance`` holds the next state.

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
from tests.ingestion.mechanical._replacement_chain import (
    BATCHES,
    REPLACEMENT,
    accepted_only,
    current,
    identity,
    proposal_path,
    through,
)
from tests.ingestion.mechanical._schema_pins import lifted

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"

PLAY, GLOSSARY = "srd-5.2.1/playing-the-game", "srd-5.2.1/rules-glossary"


def _glossary(text: str, slug: str) -> str:
    return f"reference {GLOSSARY}:'{text}': unknown target record glossary.{slug}"


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: What the seven prior batches left unresolved: the five targets this batch
#: defines, and the attack-roll pointer its resolution answers.
CLOSED = sorted(
    [
        f"reference {PLAY}:'Actions': unknown target record play.actions",
        _glossary("Damage types", "damage_types"),
        _glossary("dead", "dead"),
        _glossary("Long Rests", "long_rest"),
        _glossary("Short", "short_rest"),
        _glossary("Short Rest", "short_rest"),
        _unresolved(PLAY, "Playing the Game"),
    ]
    + [_glossary("Long Rest", "long_rest")] * 3
)
#: What stays unresolved, explicitly: three targets nobody has accepted and
#: seven printed pointers into parts with no record. No destination is guessed.
OUTSTANDING = sorted(
    [
        _glossary("Armor Class", "armor_class"),
        _glossary("Challenge Rating", "challenge_rating"),
        _glossary("Expertise", "expertise"),
        _unresolved(GLOSSARY, "Rules Glossary"),
    ]
    + [_unresolved("srd-5.2.1/character-creation", "Character Creation")] * 2
    + [_unresolved("srd-5.2.1/equipment", "Equipment")] * 2
    + [_unresolved("srd-5.2.1/spells", "Spells")] * 2
)
RECORDS = {
    "play.d20_tests",
    "play.proficiency",
    "play.actions",
    "glossary.damage_types",
    "glossary.dead",
    "glossary.long_rest",
    "glossary.short_rest",
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
    "checks_actions_rests_gen", NOTES / "issue-5d-checks-actions-rests-generator.py"
)
BATCH = "checks-actions-rests"
PROPOSAL = load_proposal(proposal_path(BATCH))
PRIOR = through("combat-damage-breaking")
FIRST = accepted_only(BATCH)
_binding = PROPOSAL.binding
INPUTS = through(BATCH)


def _citation(ref) -> tuple[str, str, str, str]:  # type: ignore[no-untyped-def]
    return (ref.from_record_key, ref.from_component_key, ref.source_text, ref.scope_key)


def test_all_seven_prior_batches_are_retained() -> None:
    batches = {b.batch_id: b for b in INPUTS.batches}
    # Only the restart's batches: nothing quarantined is inherited.
    assert sorted(batches) == [
        "actions-pilot",
        "checks-actions-rests",
        "combat-damage-breaking",
        "combat-turn-1",
        "conditions-pilot",
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
    assert len(raw) == 194790 and b"\r" not in raw
    assert hashlib.sha256(raw).hexdigest() == BATCHES[BATCH][1]
    assert proposal_identity(PROPOSAL) == identity(BATCH)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "checks-actions-rests"]
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    assert {a.reviewer for a in INPUTS.acceptances} == {"Ravenlok (Owner)"}
    # One consolidated approval: every acceptance carries its single stamp.
    assert {a.accepted_at for a in INPUTS.acceptances} == {REPLACEMENT.ACCEPTED_AT}


def test_the_whole_scope_is_accepted_beside_the_seven_prior_batches() -> None:
    proposed = {p.span.span_id for p in PROPOSAL.proposed_spans}
    prior = {s.span_id for s in PRIOR.oracle.spans}
    assert (len(proposed), len(prior)) == (125, 430)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "checks-actions-rests"]
    assert set(batch.resolved_scope) == proposed
    assert {s.span_id for s in INPUTS.oracle.spans} == proposed | prior
    assert len(INPUTS.oracle.spans) == 555
    assert {s.review_state for s in INPUTS.oracle.spans} == {ReviewState.ACCEPTED}
    units = {u.unit_id for u in PROPOSAL.proposed_review_units}
    prior_units = {u.unit_id for u in PRIOR.oracle.review_units}
    assert (len(units), len(prior_units)) == (7, 67)
    assert {u.unit_id for u in INPUTS.oracle.review_units} == units | prior_units
    assert {a.unit_id for a in INPUTS.review_unit_acceptances} == units | prior_units
    assert INPUTS.oracle.binding == PROPOSAL.binding == PRIOR.oracle.binding
    assert INPUTS.lifts == () and INPUTS.policy_transitions == ()


def test_the_representation_is_both_accepted_representations_unchanged() -> None:
    combined = INPUTS.oracle.representation
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(PRIOR.oracle.representation, field.name)
        ) | set(getattr(PROPOSAL.proposed_representation, field.name)), field.name
    assert len(combined.records) == 74
    assert {r.semantic_key for r in PROPOSAL.proposed_representation.records} == (
        RECORDS
    )
    assert not RECORDS & {r.semantic_key for r in PRIOR.oracle.representation.records}
    # The resolution step edits nothing the acceptance step recorded (loading
    # orders entries canonically, so compare contents).
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(FIRST.oracle.representation, field.name)
        ), field.name
    assert {b.batch_id: set(b.diff) for b in INPUTS.batches} == {
        b.batch_id: set(b.diff) for b in FIRST.batches
    }
    assert set(INPUTS.acceptances) == set(FIRST.acceptances)


def test_the_resolution_is_an_authorized_overlay_on_the_accepted_citation() -> None:
    draft = GEN.draft_attack_roll_resolution(INPUTS.oracle.binding)
    assert FIRST.oracle.reference_resolutions == ()
    assert INPUTS.oracle.reference_resolutions == (draft,)
    assert (
        draft.resolution_id,
        _citation(draft),
        draft.target_record_key,
        draft.provenance_span_ids,
    ) == (
        "resolve-attack-roll-playing-the-game-1",
        CITATION,
        "play.d20_tests",
        ("aeefa376-825e-5b97-a815-7409beee2672",),
    )
    assert draft.release_binding == PROPOSAL.binding
    (authorization,) = INPUTS.reference_resolution_acceptances
    assert authorization.resolution_id == draft.resolution_id
    assert authorization.authorized_by == authorization.reviewer == "Ravenlok (Owner)"
    assert authorization.authorization_reference == (
        REPLACEMENT.AUTHORIZATION_REFERENCE
    )
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


def test_six_citations_close_and_ten_references_stay_unresolved() -> None:
    def references(inputs: AcceptedInputs) -> list[str]:
        findings = _references(inputs)
        return sorted(f for f in findings if f.startswith("reference "))

    assert references(PRIOR) == sorted(
        CLOSED
        + [
            _unresolved("srd-5.2.1/equipment", "Equipment"),
            _unresolved("srd-5.2.1/spells", "Spells"),
        ]
    )
    # Accepted alone, the attack-roll pointer is still unresolved.
    assert references(FIRST) == sorted(
        OUTSTANDING + [_unresolved(PLAY, "Playing the Game")]
    )
    assert references(INPUTS) == OUTSTANDING
    defined = {r.semantic_key for r in INPUTS.oracle.representation.records}
    assert defined >= RECORDS
    assert (
        not {
            "glossary.armor_class",
            "glossary.challenge_rating",
            "glossary.expertise",
        }
        & defined
    )


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
