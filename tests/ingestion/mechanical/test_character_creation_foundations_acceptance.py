"""Character-creation-foundations and its two resolutions (#132, #137).

``.claude/review-notes/issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py``
accepted the regenerated character-creation-foundations proposal in two
native steps under the one Owner approval: ``accept_proposal`` over the
ten-batch state *and* its attack-roll resolution, then one
``resolve_references`` action carrying the two reviewed drafts. These tests
hold the state after this batch to the exact approved proposal bytes, which the
published release still derives, and to all of its spans and units; to the ten
prior batches and the attack-roll resolution retained unchanged inside it; to
the two "Character Creation" citations resolved as an authorized overlay that
leaves the accepted citations untouched; to a GameMaster reading passages in
printed order from that authority; and to a release that cannot publish:
twenty-nine reference findings stay.
``test_character_origins_feats_acceptance`` holds the next state.

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
from collections import Counter
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
from afterworlds.persistence.orm.corpus import LedgerLeafORM
from afterworlds.services.rules_authority.application import (
    SourceProse,
    _base_records,
)
from afterworlds.services.rules_authority.service import source_leaf_order
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

CC, PLAY = "srd-5.2.1/character-creation", "srd-5.2.1/playing-the-game"
GLOSSARY, EQUIPMENT = "srd-5.2.1/rules-glossary", "srd-5.2.1/equipment"
TOOLBOX, CLASSES = "srd-5.2.1/gameplay-toolbox", "srd-5.2.1/classes"
ORIGINS, FEATS = "srd-5.2.1/character-origins", "srd-5.2.1/feats"


def _glossary(text: str, slug: str) -> str:
    return f"reference {GLOSSARY}:'{text}': unknown target record glossary.{slug}"


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: What the ten prior batches left undefined: the five Stat Block targets this
#: batch defines by holding their content.
CLOSED = sorted(
    _glossary(label, slug)
    for label, slug in [
        ("Alignment", "alignment"),
        ("Creature Type", "creature_type"),
        ("Experience Points", "experience_points"),
        ("Passive Perception", "passive_perception"),
        ("Size", "size"),
    ]
)
#: The two accepted citations the two resolutions answer.
RESOLVED = [_unresolved(CC, "Character Creation")] * 2
#: The prior pointers that stay, none given a guessed destination.
PRIOR_UNRESOLVED = sorted(
    [_unresolved(EQUIPMENT, "Equipment")] * 5
    + [_unresolved(TOOLBOX, "Combat Encounters")]
    + [_unresolved(TOOLBOX, "Gameplay Toolbox")]
    + [_unresolved(GLOSSARY, "Rules Glossary")]
    + [_unresolved("srd-5.2.1/spells", "Spells")] * 2
    + [_unresolved(PLAY, "Playing the Game")] * 2
    + [_unresolved("srd-5.2.1/monsters", "Monsters")]
)
#: The sixteen outward pointers this batch adds, retained as the Owner decided.
NEW = sorted(
    [_unresolved(ORIGINS, "Character Origins")] * 2
    + [_unresolved(CLASSES, "Classes")] * 6
    + [_unresolved(EQUIPMENT, "Equipment")] * 5
    + [_unresolved(FEATS, "Feats")]
    + [_unresolved(PLAY, "Playing the Game")] * 2
)
OUTSTANDING = sorted(PRIOR_UNRESOLVED + NEW)
RECORDS = {
    "character_creation.character_sheet",
    "character_creation.create_your_character",
    "character_creation.level_advancement",
    "character_creation.multiclassing",
    "character_creation.starting_at_higher_levels",
    "character_creation.trinkets",
    "glossary.alignment",
    "glossary.creature_type",
    "glossary.experience_points",
    "glossary.passive_perception",
    "glossary.size",
}
ATTACK_ROLL = ("play.combat", "attack_structure", "Playing the Game", PLAY)
#: Each resolved citation and the destination the Owner approved for it.
DESTINATIONS = {
    (
        "resolve-armor-class-character-creation-1",
        ("play.d20_tests", "armor_class", "Character Creation", CC),
        "character_creation.create_your_character",
        ("4e1f6ecf-d4c1-5b6d-a24c-c8676b1b7506",),
    ),
    (
        "resolve-proficiency-bonus-character-creation-1",
        ("play.proficiency", "proficiency_bonus", "Character Creation", CC),
        "character_creation.level_advancement",
        ("6b8bbca6-0f41-549a-8b8e-bc750f6e3bf6",),
    ),
}


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load(
    "character_creation_foundations_gen",
    NOTES / "issue-5d-character-creation-foundations-generator.py",
)
BATCH = "character-creation-foundations"
PROPOSAL = load_proposal(proposal_path(BATCH))
PRIOR = through("core-play-dependencies")
FIRST = accepted_only(BATCH)
_binding = PROPOSAL.binding
INPUTS = through(BATCH)


def _citation(ref) -> tuple[str, str, str, str]:  # type: ignore[no-untyped-def]
    return (ref.from_record_key, ref.from_component_key, ref.source_text, ref.scope_key)


def test_all_ten_prior_batches_are_retained() -> None:
    batches = {b.batch_id: b for b in INPUTS.batches}
    # Only the restart's batches: nothing quarantined is inherited.
    assert sorted(batches) == [
        "actions-pilot",
        "character-creation-foundations",
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
    assert set(PRIOR.oracle.review_units) <= set(INPUTS.oracle.review_units)
    assert set(PRIOR.oracle.obligations) <= set(INPUTS.oracle.obligations)


def test_it_records_the_owner_acceptance_of_the_exact_proposal() -> None:
    raw = proposal_path(BATCH).read_bytes()
    assert len(raw) == 226514 and b"\r" not in raw
    assert hashlib.sha256(raw).hexdigest() == BATCHES[BATCH][1]
    assert proposal_identity(PROPOSAL) == identity(BATCH)
    (batch,) = [
        b for b in INPUTS.batches if b.batch_id == "character-creation-foundations"
    ]
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    assert {a.reviewer for a in INPUTS.acceptances} == {"Ravenlok (Owner)"}
    # One consolidated approval: every acceptance carries its single stamp.
    assert {a.accepted_at for a in INPUTS.acceptances} == {REPLACEMENT.ACCEPTED_AT}


def test_the_whole_scope_is_accepted_beside_the_ten_prior_batches() -> None:
    proposed = {p.span.span_id for p in PROPOSAL.proposed_spans}
    prior = {s.span_id for s in PRIOR.oracle.spans}
    assert (len(proposed), len(prior)) == (152, 692)
    (batch,) = [
        b for b in INPUTS.batches if b.batch_id == "character-creation-foundations"
    ]
    assert set(batch.resolved_scope) == proposed
    assert {s.span_id for s in INPUTS.oracle.spans} == proposed | prior
    assert len(INPUTS.oracle.spans) == 844
    assert {s.review_state for s in INPUTS.oracle.spans} == {ReviewState.ACCEPTED}
    units = {u.unit_id for u in PROPOSAL.proposed_review_units}
    prior_units = {u.unit_id for u in PRIOR.oracle.review_units}
    assert (len(units), len(prior_units)) == (11, 92)
    assert {u.unit_id for u in INPUTS.oracle.review_units} == units | prior_units
    assert {a.unit_id for a in INPUTS.review_unit_acceptances} == units | prior_units
    assert len(INPUTS.oracle.review_units) == 103
    assert sum(len(u.leaf_ids) for u in PROPOSAL.proposed_review_units) == 179
    assert INPUTS.oracle.binding == PROPOSAL.binding == PRIOR.oracle.binding
    assert INPUTS.lifts == () and INPUTS.policy_transitions == ()


def test_the_representation_is_both_accepted_representations_unchanged() -> None:
    combined = INPUTS.oracle.representation
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(PRIOR.oracle.representation, field.name)
        ) | set(getattr(PROPOSAL.proposed_representation, field.name)), field.name
    assert len(combined.records) == 103
    assert len(PROPOSAL.proposed_representation.components) == 69
    assert {r.semantic_key for r in PROPOSAL.proposed_representation.records} == (
        RECORDS
    )
    assert not RECORDS & {r.semantic_key for r in PRIOR.oracle.representation.records}
    # Resolving edits nothing accepted: the representation is step 1's.
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(FIRST.oracle.representation, field.name)
        ), field.name


def test_the_two_resolutions_are_an_authorized_overlay_on_the_accepted_citations() -> (
    None
):
    resolutions = INPUTS.oracle.reference_resolutions
    by_id = {r.resolution_id: r for r in resolutions}
    assert sorted(by_id) == [
        "resolve-armor-class-character-creation-1",
        "resolve-attack-roll-playing-the-game-1",
        "resolve-proficiency-bonus-character-creation-1",
    ]
    # The attack-roll resolution and its authorization are carried unchanged.
    (attack_roll,) = PRIOR.oracle.reference_resolutions
    assert by_id.pop(attack_roll.resolution_id) == attack_roll
    assert (_citation(attack_roll), attack_roll.target_record_key) == (
        ATTACK_ROLL,
        "play.d20_tests",
    )
    authorizations = {
        a.resolution_id: a for a in INPUTS.reference_resolution_acceptances
    }
    assert len(authorizations) == 3
    (attack_roll_authorization,) = PRIOR.reference_resolution_acceptances
    assert authorizations.pop(attack_roll.resolution_id) == attack_roll_authorization
    binding = INPUTS.oracle.binding
    new = set(by_id.values())
    assert {
        (r.resolution_id, _citation(r), r.target_record_key, r.provenance_span_ids)
        for r in new
    } == DESTINATIONS
    assert all(r.release_binding == binding for r in new)
    # Exactly the reviewed drafts, as the generator states them.
    assert new == {
        GEN.draft_armor_class_resolution(binding),
        GEN.draft_proficiency_bonus_resolution(binding),
    }
    assert set(authorizations) == set(by_id)
    for authorization in authorizations.values():
        assert (
            authorization.authorized_by
            == authorization.reviewer
            == ("Ravenlok (Owner)")
        )
        assert (
            authorization.authorization_reference == REPLACEMENT.AUTHORIZATION_REFERENCE
        )
        assert authorization.resolved_at == REPLACEMENT.ACCEPTED_AT
    assert (
        reference_resolution_violations(
            INPUTS.oracle.representation, resolutions, binding
        )
        == []
    )
    # The accepted citations keep their empty targets; only the effective view
    # gives them destinations.
    accepted = {
        _citation(r): r.target_record_key
        for r in INPUTS.oracle.representation.references
        if r.source_text == "Character Creation"
    }
    assert accepted == {c: "" for _, c, _, _ in DESTINATIONS}
    effective = effective_representation(INPUTS.oracle.representation, resolutions)
    assert {
        _citation(r): r.target_record_key
        for r in effective.references
        if _citation(r) in accepted
    } == {c: target for _, c, target, _ in DESTINATIONS}


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


def test_the_committed_authority_reads_in_printed_order(session) -> None:  # type: ignore[no-untyped-def]
    # The consumer reads the eleven batches' records through the loader the service
    # uses: every passage in ledger position, then position in its leaf. Read on the
    # current release with its current accepted authority: the recorded state binds the
    # superseded release's package, whose ledger the source DB does not hold
    # (``source_leaf_order`` is package-scoped; the leaf ids themselves are shared).
    # Record keys name no release.
    candidate = candidate_from_accepted_inputs(current())
    every = _base_records(candidate, source_leaf_order(session, candidate))
    records = {
        key: every[key]
        for key in {r.semantic_key for r in INPUTS.oracle.representation.records}
    }
    spans = {s.span_id: s for s in candidate.classification.spans}
    position = {
        row.leaf_id: row.occurrence_index
        for row in session.query(LedgerLeafORM).filter(
            LedgerLeafORM.package_uuid == candidate.binding.package_uuid
        )
    }
    multi = 0
    for record in records.values():
        for component in record.components:
            passages = [
                e for e in component.governing_prose if isinstance(e, SourceProse)
            ]
            printed = [
                (position[spans[e.span_id].leaf_id], spans[e.span_id].char_start)
                for e in passages
            ]
            assert printed == sorted(printed), component.semantic_key
            multi += len(passages) > 1
    # The recorded state's multi-passage components are the ten batches' 100
    # and this batch's 29, counted from its prose bindings, which name no
    # release. The current accepted authority no longer holds three of them as
    # components; every other one reads here.
    recorded = Counter(
        (b.record_key, b.component_key)
        for b in INPUTS.oracle.representation.prose_bindings
    )
    assert sum(n > 1 for n in recorded.values()) == 129
    held = {(key, c.semantic_key) for key, r in records.items() for c in r.components}
    assert {k for k, n in recorded.items() if n > 1} - held == {
        ("play.exploration", "pace_effects"),
        ("play.exploration", "travel_pace"),
        ("play.proficiency", "skill_list"),
    }
    assert multi == 129 - 3
    (tiers,) = [
        c
        for c in records["character_creation.level_advancement"].components
        if c.semantic_key == "tiers_of_play"
    ]
    starts = [
        "With each new level, characters acquire new capabilities",
        "#### Tier 1 (Levels 1–4)",
        "In tier 1, characters are apprentice",
        "#### Tier 2 (Levels 5–10)",
        "In tier 2, characters are full-fledged",
        "#### Tier 3 (Levels 11–16)",
        "In tier 3, characters have reached",
        "#### Tier 4 (Levels 17–20)",
        "At tier 4, characters achieve the pinnacle",
    ]
    leaves = {
        row.leaf_id: row.content
        for row in session.query(LedgerLeafORM).filter(
            LedgerLeafORM.package_uuid == candidate.binding.package_uuid
        )
    }
    read = [
        leaves[spans[e.span_id].leaf_id][
            spans[e.span_id].char_start : spans[e.span_id].char_end
        ]
        for e in tiers.governing_prose
        if isinstance(e, SourceProse)
    ]
    assert len(read) == len(starts)
    assert all(t.startswith(s) for t, s in zip(read, starts, strict=True))


def test_five_targets_close_two_citations_resolve_and_29_findings_stay() -> None:
    def references(inputs: AcceptedInputs) -> list[str]:
        findings = _references(inputs)
        return sorted(f for f in findings if f.startswith("reference "))

    assert references(PRIOR) == sorted(CLOSED + RESOLVED + PRIOR_UNRESOLVED)
    # Accepted but not yet resolved: the batch's sixteen pointers join.
    assert references(FIRST) == sorted(RESOLVED + OUTSTANDING)
    assert len(references(FIRST)) == 31
    assert references(INPUTS) == OUTSTANDING
    assert (len(PRIOR_UNRESOLVED), len(NEW)) == (13, 16)
    assert len(OUTSTANDING) == 29
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
