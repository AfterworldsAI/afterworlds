"""The combat-damage-breaking batch in the replacement chain (#132, #137).

``.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``
accepted the regenerated combat-damage-breaking proposal through
``accept_proposal`` with the six-batch state through damage-and-hit-points as
``prior``. These tests hold the state after this batch to the exact approved
proposal bytes, which the published release still derives, and to all of its
spans and units; to the six prior batches retained unchanged inside it; to the
three targets the prior batches left undefined, now defined by this batch's own
content; and to a release that cannot publish: twelve references stay
unresolved (nine citations of five undefined targets and three pointers into
parts with no record). ``test_checks_actions_rests_acceptance`` holds the next
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

PLAY, GLOSSARY = "srd-5.2.1/playing-the-game", "srd-5.2.1/rules-glossary"
#: What the six prior batches left unresolved: the three targets this batch
#: defines.
CLOSED = sorted(
    [f"reference {PLAY}:'Combat': unknown target record play.combat"] * 4
    + [
        f"reference {PLAY}:'Damage and Healing': unknown target record "
        "play.damage_and_healing"
    ]
    * 5
    + [
        f"reference {GLOSSARY}:'Breaking Objects': unknown target record "
        "glossary.breaking_objects"
    ]
)


def _glossary(text: str, slug: str) -> str:
    return f"reference {GLOSSARY}:'{text}': unknown target record glossary.{slug}"


#: What stays unresolved: nine citations of five undefined targets and three
#: printed pointers into parts no record exists for.
OUTSTANDING = sorted(
    [
        f"reference {PLAY}:'Playing the Game': unresolved reference",
        "reference srd-5.2.1/equipment:'Equipment': unresolved reference",
        "reference srd-5.2.1/spells:'Spells': unresolved reference",
        f"reference {PLAY}:'Actions': unknown target record play.actions",
        _glossary("Damage types", "damage_types"),
        _glossary("dead", "dead"),
        _glossary("Long Rests", "long_rest"),
        _glossary("Short", "short_rest"),
        _glossary("Short Rest", "short_rest"),
    ]
    + [_glossary("Long Rest", "long_rest")] * 3
)
RECORDS = {
    "play.combat",
    "play.damage_and_healing",
    "play.exploration.breaking_objects",
    "glossary.breaking_objects",
    "glossary.damage_threshold",
}


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load(
    "combat_damage_breaking", NOTES / "issue-5d-combat-damage-breaking-generator.py"
)
BATCH = "combat-damage-breaking"
PROPOSAL = load_proposal(proposal_path(BATCH))
PRIOR = through("damage-and-hit-points")
_binding = PROPOSAL.binding
INPUTS = through(BATCH)


def test_all_six_prior_batches_are_retained() -> None:
    batches = {b.batch_id: b for b in INPUTS.batches}
    # Only the restart's batches: nothing quarantined is inherited.
    assert sorted(batches) == [
        "actions-pilot",
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
    assert len(raw) == 253450 and b"\r" not in raw
    assert hashlib.sha256(raw).hexdigest() == BATCHES[BATCH][1]
    assert proposal_identity(PROPOSAL) == identity(BATCH)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "combat-damage-breaking"]
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    assert {a.reviewer for a in INPUTS.acceptances} == {"Ravenlok (Owner)"}
    # One consolidated approval: every acceptance carries its single stamp.
    assert {a.accepted_at for a in INPUTS.acceptances} == {REPLACEMENT.ACCEPTED_AT}


def test_the_whole_scope_is_accepted_beside_the_six_prior_batches() -> None:
    proposed = {p.span.span_id for p in PROPOSAL.proposed_spans}
    prior = {s.span_id for s in PRIOR.oracle.spans}
    assert (len(proposed), len(prior)) == (162, 268)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "combat-damage-breaking"]
    assert set(batch.resolved_scope) == proposed
    assert {s.span_id for s in INPUTS.oracle.spans} == proposed | prior
    assert len(INPUTS.oracle.spans) == 430
    assert {s.review_state for s in INPUTS.oracle.spans} == {ReviewState.ACCEPTED}
    units = {u.unit_id for u in PROPOSAL.proposed_review_units}
    prior_units = {u.unit_id for u in PRIOR.oracle.review_units}
    assert (len(units), len(prior_units)) == (5, 62)
    assert {u.unit_id for u in INPUTS.oracle.review_units} == units | prior_units
    assert {a.unit_id for a in INPUTS.review_unit_acceptances} == units | prior_units
    assert INPUTS.oracle.binding == PROPOSAL.binding == PRIOR.oracle.binding
    assert INPUTS.lifts == () and INPUTS.policy_transitions == ()
    # No resolution is accepted: the three targets close by definition alone.
    assert INPUTS.oracle.reference_resolutions == ()


def test_the_representation_is_both_accepted_representations_unchanged() -> None:
    combined = INPUTS.oracle.representation
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(PRIOR.oracle.representation, field.name)
        ) | set(getattr(PROPOSAL.proposed_representation, field.name)), field.name
    assert len(combined.records) == 67
    assert {r.semantic_key for r in PROPOSAL.proposed_representation.records} == (
        RECORDS
    )
    assert not RECORDS & {r.semantic_key for r in PRIOR.oracle.representation.records}


def test_the_marching_order_sidebar_and_the_part_pointers_are_accepted() -> None:
    combined = INPUTS.oracle.representation
    assert any(
        c.record_key == "play.exploration.breaking_objects"
        and c.semantic_key == "marching_order"
        for c in combined.components
    )
    pointers = sorted(
        (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        for r in combined.references
        if not r.target_record_key
    )
    assert pointers == sorted(
        [
            ("play.combat", "attack_structure", "Playing the Game", PLAY),
            ("play.damage_and_healing", "", "Equipment", "srd-5.2.1/equipment"),
            ("play.damage_and_healing", "", "Spells", "srd-5.2.1/spells"),
        ]
    )


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


def test_three_targets_close_and_twelve_references_stay_unresolved() -> None:
    def references(inputs: AcceptedInputs) -> list[str]:
        findings = _references(inputs)
        return sorted(f for f in findings if f.startswith("reference "))

    assert references(PRIOR) == CLOSED
    assert references(INPUTS) == OUTSTANDING
    defined = {r.semantic_key for r in INPUTS.oracle.representation.records}
    assert {
        "play.combat",
        "play.damage_and_healing",
        "glossary.breaking_objects",
    } <= defined
    assert (
        not {
            "play.actions",
            "glossary.short_rest",
            "glossary.long_rest",
            "glossary.damage_types",
            "glossary.dead",
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
