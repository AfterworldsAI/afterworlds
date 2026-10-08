"""The core-play-dependencies batch in the replacement chain (#132, #137).

``.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``
accepted the regenerated core-play-dependencies proposal through
``accept_proposal`` with the nine-batch state *and* its attack-roll resolution
as ``prior``. These tests hold the state after this batch to the exact approved
proposal bytes, which the published release still derives, and to all of its
spans and units; to the nine prior batches and the one resolution retained
unchanged inside it, the resolution still applying beside the two Stat Block
pointers of the same wording (the Owner's citation-identity decision); and to a
release that cannot publish: twenty reference findings stay.
``test_character_creation_foundations_acceptance`` holds the next state.

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
    reference_resolution_violations,
)
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
EQUIPMENT, TOOLBOX = "srd-5.2.1/equipment", "srd-5.2.1/gameplay-toolbox"
MONSTERS = "srd-5.2.1/monsters"


def _glossary(text: str, slug: str) -> str:
    return f"reference {GLOSSARY}:'{text}': unknown target record glossary.{slug}"


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: What the nine prior batches left undefined: the eleven targets this batch
#: defines by holding their content.
CLOSED = sorted(
    _glossary(text, slug)
    for text, slug in [
        ("Attack Roll", "attack_roll"),
        ("Blindsight", "blindsight"),
        ("Burning", "burning"),
        ("Darkvision", "darkvision"),
        ("Dehydration", "dehydration"),
        ("Malnutrition", "malnutrition"),
        ("Stat Block", "stat_block"),
        ("Suffocation", "suffocation"),
        ("Tremorsense", "tremorsense"),
        ("Truesight", "truesight"),
        ("carrying capacity", "carrying_capacity"),
    ]
)
#: The twenty findings the Owner accepted as retained: the twelve accepted
#: printed pointers with no destination, the five named glossary entries nobody
#: has authored, and the three broad pointers this batch adds. No destination
#: is guessed.
PRIOR_UNRESOLVED = sorted(
    [_unresolved("srd-5.2.1/character-creation", "Character Creation")] * 2
    + [_unresolved(EQUIPMENT, "Equipment")] * 5
    + [_unresolved(TOOLBOX, "Combat Encounters")]
    + [_unresolved(TOOLBOX, "Gameplay Toolbox")]
    + [_unresolved(GLOSSARY, "Rules Glossary")]
    + [_unresolved("srd-5.2.1/spells", "Spells")] * 2
)
NEW_MISSING = sorted(
    [
        _glossary("Alignment", "alignment"),
        _glossary("Creature Type", "creature_type"),
        _glossary("Experience Points", "experience_points"),
        _glossary("Passive Perception", "passive_perception"),
        _glossary("Size", "size"),
    ]
)
BROAD = sorted(
    [_unresolved(MONSTERS, "Monsters")] + [_unresolved(PLAY, "Playing the Game")] * 2
)
OUTSTANDING = sorted(PRIOR_UNRESOLVED + NEW_MISSING + BROAD)
RECORDS = {
    "glossary.attack_roll",
    "glossary.blindsight",
    "glossary.burning",
    "glossary.carrying_capacity",
    "glossary.darkvision",
    "glossary.dehydration",
    "glossary.malnutrition",
    "glossary.stat_block",
    "glossary.suffocation",
    "glossary.tremorsense",
    "glossary.truesight",
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
    "core_play_dependencies_generator",
    NOTES / "issue-5d-core-play-dependencies-generator.py",
)
BATCH = "core-play-dependencies"
PROPOSAL = load_proposal(proposal_path(BATCH))
PRIOR = through("core-play-completion")
_binding = PROPOSAL.binding
INPUTS = through(BATCH)


def _citation(ref) -> tuple[str, str, str, str]:  # type: ignore[no-untyped-def]
    return (ref.from_record_key, ref.from_component_key, ref.source_text, ref.scope_key)


def test_all_nine_prior_batches_are_retained() -> None:
    batches = {b.batch_id: b for b in INPUTS.batches}
    # Only the restart's batches: nothing quarantined is inherited.
    assert sorted(batches) == [
        "actions-pilot",
        "checks-actions-rests",
        "combat-damage-breaking",
        "combat-turn-1",
        "conditions-pilot",
        "core-play-completion",
        "core-play-dependencies",
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
    assert set(PRIOR.oracle.spans) <= set(INPUTS.oracle.spans)


def test_it_records_the_owner_acceptance_of_the_exact_proposal() -> None:
    raw = proposal_path(BATCH).read_bytes()
    assert len(raw) == 112597 and b"\r" not in raw
    assert hashlib.sha256(raw).hexdigest() == BATCHES[BATCH][1]
    assert proposal_identity(PROPOSAL) == identity(BATCH)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "core-play-dependencies"]
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    assert {a.reviewer for a in INPUTS.acceptances} == {"Ravenlok (Owner)"}
    # One consolidated approval: every acceptance carries its single stamp.
    assert {a.accepted_at for a in INPUTS.acceptances} == {REPLACEMENT.ACCEPTED_AT}


def test_the_whole_scope_is_accepted_beside_the_nine_prior_batches() -> None:
    proposed = {p.span.span_id for p in PROPOSAL.proposed_spans}
    prior = {s.span_id for s in PRIOR.oracle.spans}
    assert (len(proposed), len(prior)) == (66, 626)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "core-play-dependencies"]
    assert set(batch.resolved_scope) == proposed
    assert {s.span_id for s in INPUTS.oracle.spans} == proposed | prior
    assert len(INPUTS.oracle.spans) == 692
    assert {s.review_state for s in INPUTS.oracle.spans} == {ReviewState.ACCEPTED}
    units = {u.unit_id for u in PROPOSAL.proposed_review_units}
    prior_units = {u.unit_id for u in PRIOR.oracle.review_units}
    assert (len(units), len(prior_units)) == (11, 81)
    assert {u.unit_id for u in INPUTS.oracle.review_units} == units | prior_units
    assert {a.unit_id for a in INPUTS.review_unit_acceptances} == units | prior_units
    assert len(INPUTS.oracle.review_units) == 92
    assert sum(len(u.leaf_ids) for u in PROPOSAL.proposed_review_units) == 52
    assert INPUTS.oracle.binding == PROPOSAL.binding == PRIOR.oracle.binding
    assert INPUTS.lifts == () and INPUTS.policy_transitions == ()


def test_the_representation_is_both_accepted_representations_unchanged() -> None:
    combined = INPUTS.oracle.representation
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(PRIOR.oracle.representation, field.name)
        ) | set(getattr(PROPOSAL.proposed_representation, field.name)), field.name
    assert len(combined.records) == 92
    assert {r.semantic_key for r in PROPOSAL.proposed_representation.records} == (
        RECORDS
    )
    assert not RECORDS & {r.semantic_key for r in PRIOR.oracle.representation.records}


def test_the_one_resolution_still_applies_beside_the_stat_block_pointers() -> None:
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
    binding = INPUTS.oracle.binding
    assert (
        reference_resolution_violations(
            INPUTS.oracle.representation, INPUTS.oracle.reference_resolutions, binding
        )
        == []
    )
    # The accepted citation keeps its empty target; only the effective view
    # gives it a destination. The two Stat Block pointers of the same wording
    # are distinct citations and stay unresolved.
    (accepted,) = [
        r for r in INPUTS.oracle.representation.references if _citation(r) == CITATION
    ]
    assert accepted.target_record_key == ""
    effective = effective_representation(
        INPUTS.oracle.representation, INPUTS.oracle.reference_resolutions
    )
    assert sorted(
        (r.from_record_key, r.from_component_key, r.target_record_key)
        for r in effective.references
        if (r.source_text, r.scope_key) == ("Playing the Game", PLAY)
    ) == [
        ("glossary.stat_block", "ability_scores", ""),
        ("glossary.stat_block", "ac_initiative_hp", ""),
        ("play.combat", "attack_structure", "play.d20_tests"),
    ]


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
    out = tmp_path / "p.json"
    expected = GEN.expected_representation_findings()
    assert emit(str(source_release_db), lambda _s: built, out, expected) == 0
    assert out.read_bytes() == GEN.render(built.proposal).encode("utf-8")


def test_eleven_targets_close_and_the_accepted_twenty_findings_stay() -> None:
    def references(inputs: AcceptedInputs) -> list[str]:
        findings = _references(inputs)
        return sorted(f for f in findings if f.startswith("reference "))

    assert references(PRIOR) == sorted(CLOSED + PRIOR_UNRESOLVED)
    assert references(INPUTS) == OUTSTANDING
    assert (len(PRIOR_UNRESOLVED), len(NEW_MISSING), len(BROAD)) == (12, 5, 3)
    assert len(OUTSTANDING) == 20
    assert not any("ambiguous" in f for f in OUTSTANDING)


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
