"""The combat-turn-1 batch in the Owner-approved replacement chain (#132, #137).

``.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``
accepted the regenerated combat-turn-1 proposal through ``accept_proposal``
with the four-batch state through movement-closure as ``prior``. These tests
hold the state after this batch to the exact approved proposal bytes, which the
published release still derives, and to all of its spans and units; to the four
prior batches retained unchanged inside it; to the proposal's source
relationships; and to a release that cannot publish: Initiative, Opportunity
Attacks and Surprise join Speed in pointing at Playing the Game ("Combat"),
which stays undefined. ``test_damage_and_hit_points_acceptance`` holds the next
state.

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
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.models import ReviewState
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    candidate_from_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import load_proposal, proposal_identity
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.persistence.database import create_engine, create_session_factory
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

#: The one target nothing accepted defines, now cited by four records.
COMBAT = (
    "reference srd-5.2.1/playing-the-game:'Combat': unknown target record play.combat"
)
ENTRIES = {
    "glossary.initiative",
    "glossary.occupied_space",
    "glossary.opportunity_attacks",
    "glossary.reach",
    "glossary.surprise",
    "glossary.unoccupied_space",
}


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load("combat_turn_1", NOTES / "issue-5d-combat-turn-1-generator.py")
BATCH = "combat-turn-1"
PROPOSAL = load_proposal(proposal_path(BATCH))
PRIOR = through("movement-closure")
_binding = PROPOSAL.binding
INPUTS = through(BATCH)


def test_all_four_prior_batches_are_retained() -> None:
    batches = {b.batch_id: b for b in INPUTS.batches}
    # Only the restart's batches: nothing quarantined is inherited.
    assert sorted(batches) == [
        "actions-pilot",
        "combat-turn-1",
        "conditions-pilot",
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
    assert len(raw) == 28263 and b"\r" not in raw
    assert hashlib.sha256(raw).hexdigest() == BATCHES[BATCH][1]
    assert proposal_identity(PROPOSAL) == identity(BATCH)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "combat-turn-1"]
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    assert {a.reviewer for a in INPUTS.acceptances} == {"Ravenlok (Owner)"}
    # One consolidated approval: every acceptance carries its single stamp.
    assert {a.accepted_at for a in INPUTS.acceptances} == {REPLACEMENT.ACCEPTED_AT}


def test_the_whole_scope_is_accepted_beside_the_four_prior_batches() -> None:
    proposed = {p.span.span_id for p in PROPOSAL.proposed_spans}
    prior = {s.span_id for s in PRIOR.oracle.spans}
    assert (len(proposed), len(prior)) == (16, 79 + 75 + 53 + 29)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "combat-turn-1"]
    assert set(batch.resolved_scope) == proposed
    assert {s.span_id for s in INPUTS.oracle.spans} == proposed | prior
    assert {s.review_state for s in INPUTS.oracle.spans} == {ReviewState.ACCEPTED}
    units = {u.unit_id for u in PROPOSAL.proposed_review_units}
    prior_units = {u.unit_id for u in PRIOR.oracle.review_units}
    assert (len(units), len(prior_units)) == (6, 49)
    assert {u.unit_id for u in INPUTS.oracle.review_units} == units | prior_units
    assert {a.unit_id for a in INPUTS.review_unit_acceptances} == units | prior_units
    assert INPUTS.oracle.binding == PROPOSAL.binding == PRIOR.oracle.binding
    assert INPUTS.lifts == () and INPUTS.policy_transitions == ()
    # Combat closes by no resolution: the target stays unknown.
    assert INPUTS.oracle.reference_resolutions == ()


def test_the_representation_is_both_accepted_representations_unchanged() -> None:
    combined = INPUTS.oracle.representation
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(PRIOR.oracle.representation, field.name)
        ) | set(getattr(PROPOSAL.proposed_representation, field.name)), field.name
    assert len(combined.records) == 55
    assert {r.semantic_key for r in PROPOSAL.proposed_representation.records} == (
        ENTRIES
    )
    assert not ENTRIES & {r.semantic_key for r in PRIOR.oracle.representation.records}


def test_the_source_relationships_are_accepted_as_proposed() -> None:
    refs = {
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        + (r.target_record_key,)
        for r in PROPOSAL.proposed_representation.references
    }
    assert len(PROPOSAL.proposed_representation.references) == len(refs) == 5
    play, glossary = "srd-5.2.1/playing-the-game", "srd-5.2.1/rules-glossary"
    oa = "glossary.opportunity_attacks"
    assert refs == {
        ("glossary.initiative", "", "Combat", play, "play.combat"),
        (oa, "", "Combat", play, "play.combat"),
        ("glossary.surprise", "", "Combat", play, "play.combat"),
        (oa, "opportunity_attack", "reach", glossary, "glossary.reach"),
        (
            oa,
            "opportunity_attack",
            "Unarmed Strike",
            glossary,
            "glossary.unarmed_strike",
        ),
    }
    defined = {r.semantic_key for r in INPUTS.oracle.representation.records}
    # Reach is this batch's own; Unarmed Strike is the Actions pilot's.
    assert {"glossary.reach", "glossary.unarmed_strike"} <= defined
    assert "play.combat" not in defined


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


def test_the_recorded_bytes_stay_and_the_current_build_emits(
    session: Session, source_release_db: Path, tmp_path: Path
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


def test_combat_stays_the_one_unresolved_target_now_cited_four_times() -> None:
    def references(inputs: AcceptedInputs) -> list[str]:
        findings = _references(inputs)
        return sorted(f for f in findings if f.startswith("reference "))

    assert references(PRIOR) == [COMBAT]
    assert references(INPUTS) == [COMBAT] * 4


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
    assert sorted(_references(INPUTS)) == [COMBAT] * 4
