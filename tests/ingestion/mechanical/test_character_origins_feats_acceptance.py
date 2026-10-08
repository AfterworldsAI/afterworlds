"""Character-origins-feats, its three resolutions: the recorded chain (#132, #137).

``.claude/review-notes/issue-5d-monsters-corrections-ACCEPT.py``
recorded ``oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json``, which accepts this
batch in two native steps under the one Owner approval: ``accept_proposal``,
with the eleven-batch state and its three resolutions as ``prior``, then one
``resolve_references`` action carrying the three reviewed drafts. Later
batches extend that file, so these tests rebuild the twelve-batch state
through the seams, preserved inside the committed file. They hold it to the exact
approved proposal bytes and to all of its spans and units; to the eleven
prior batches, three resolutions and their authorizations retained unchanged
inside it, carried across the one registered lift from schema 15 to 16 and
recorded as crossing it; to the three "Character Origins" and "Feats" citations
resolved as an authorized overlay that leaves the accepted citations untouched;
and to the ninety-one reference findings that stay. On the current release,
the three catalogue sections reach their members in printed order from the
current accepted authority. The committed file is the superseded release's,
read by path: the production resolver refuses its binding. The check that
held the twelve-batch state's uncovered leaves judged it against that
release's corpus, which is not rebuilt; it is retired (see
``.claude/review-notes/issue-5c-release-readiness/correction-followup.md``).
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from afterworlds.ingestion.mechanical.models import ReviewState
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.proposal import load_proposal, proposal_identity
from afterworlds.ingestion.mechanical.reference_resolution import (
    effective_representation,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import RelationshipKind
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
    SCHEMA_16_HASH,
    SCHEMA_16_VERSION,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.services.rules_authority.application import apply_override_set
from afterworlds.services.rules_authority.override_set import EffectiveOverrideSet
from afterworlds.services.rules_authority.service import _select, source_leaf_order
from tests.ingestion.mechanical._replacement_chain import (
    BATCHES,
    COMMITTED_SHA256,
    REPLACEMENT,
    accepted_only,
    current,
    equipment_recorded,
    identity,
    proposal_path,
    through,
)
from tests.ingestion.mechanical._schema_pins import lifted

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"

CC = "srd-5.2.1/character-creation"
ORIGINS, FEATS = "srd-5.2.1/character-origins", "srd-5.2.1/feats"
SPELLS, EQUIPMENT = "srd-5.2.1/spells", "srd-5.2.1/equipment"
CLASSES = "srd-5.2.1/classes"


def _unresolved(scope: str, text: str) -> str:
    return f"reference {scope}:{text!r}: unresolved reference"


#: The three accepted citations the three resolutions answer.
RESOLVED = sorted(
    [_unresolved(ORIGINS, "Character Origins")] * 2 + [_unresolved(FEATS, "Feats")]
)
#: The catalogue pointers this batch adds, retained as the Owner decided.
NEW_UNRESOLVED = Counter({SPELLS: 23, EQUIPMENT: 35, CLASSES: 7})
#: Each resolved citation and the destination the Owner approved for it.
DESTINATIONS = {
    (
        "resolve-choose-background-character-origins-1",
        (
            "character_creation.create_your_character",
            "choose_background",
            "Character Origins",
            ORIGINS,
        ),
        "character_origins.backgrounds",
        ("9051aa97-c4d4-5640-9d82-6f011e776a15",),
    ),
    (
        "resolve-choose-species-character-origins-1",
        (
            "character_creation.create_your_character",
            "choose_species",
            "Character Origins",
            ORIGINS,
        ),
        "character_origins.species",
        ("e0bfa3fa-8494-5b9e-a8da-a742ea5b6923",),
    ),
    (
        "resolve-background-feat-feats-1",
        (
            "character_creation.create_your_character",
            "background_feat",
            "Feats",
            FEATS,
        ),
        "feats.feat_descriptions",
        ("d131ec53-eaef-593a-9bdf-47800204accd",),
    ),
}
#: Each catalogue section and its entries in the order the release prints them;
#: the feats are the one catalogue whose printed order is not key order.
CATALOGUES = {
    "character_origins.backgrounds": [
        f"character_origins.{s}" for s in ("acolyte", "criminal", "sage", "soldier")
    ],
    "character_origins.species": [
        f"character_origins.{s}"
        for s in (
            "dragonborn",
            "dwarf",
            "elf",
            "gnome",
            "goliath",
            "halfling",
            "human",
            "orc",
            "tiefling",
        )
    ],
    "feats.feat_descriptions": [
        f"feats.{s}"
        for s in (
            "alert",
            "magic_initiate",
            "savage_attacker",
            "skilled",
            "ability_score_improvement",
            "grappler",
            "archery",
            "defense",
            "great_weapon_fighting",
            "two_weapon_fighting",
            "boon_of_combat_prowess",
            "boon_of_dimensional_travel",
            "boon_of_fate",
            "boon_of_irresistible_offense",
            "boon_of_spell_recall",
            "boon_of_the_night_spirit",
            "boon_of_truesight",
        )
    ],
}


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load(
    "character_origins_feats_gen",
    NOTES / "issue-5d-character-origins-feats-generator.py",
)
BATCH = "character-origins-feats"
PROPOSAL = load_proposal(proposal_path(BATCH))
PRIOR = through("character-creation-foundations")
FIRST = accepted_only(BATCH)
#: The recorded state after this batch, preserved in the committed file.
INPUTS = through(BATCH)


def _citation(ref) -> tuple[str, str, str, str]:  # type: ignore[no-untyped-def]
    return (ref.from_record_key, ref.from_component_key, ref.source_text, ref.scope_key)


def test_the_recorded_bytes_are_what_the_two_seams_record() -> None:
    # The superseded release's committed file, read by path at its recorded
    # bytes (the production resolver refuses its binding). The twelve-batch
    # state is kept whole in the Equipment recording, which the file keeps
    # outside the eight remaining-references batches.
    committed = load_accepted_inputs(REPLACEMENT.ACCEPTED_PATH)
    data = serialize_accepted_inputs(committed)
    assert data == REPLACEMENT.ACCEPTED_PATH.read_bytes()
    assert hashlib.sha256(data).hexdigest() == COMMITTED_SHA256
    assert not REPLACEMENT._preserved(
        accepted_inputs_payload(INPUTS), accepted_inputs_payload(equipment_recorded())
    )


def test_all_eleven_prior_batches_are_retained_across_the_one_lift() -> None:
    # The prior was accepted under schema 15; accepting this schema-16 batch
    # carried it across the registered lift, by identity, and recorded that.
    assert PRIOR.oracle.schema_version == SCHEMA_15_VERSION and PRIOR.lifts == ()
    assert INPUTS.oracle.schema_version == SCHEMA_16_VERSION
    (lift,) = INPUTS.lifts
    assert (
        lift.lift_id,
        lift.from_version,
        lift.from_hash,
        lift.to_version,
        lift.to_hash,
    ) == (
        "5d-lift-schema-15-to-16",
        SCHEMA_15_VERSION,
        SCHEMA_15_HASH,
        SCHEMA_16_VERSION,
        SCHEMA_16_HASH,
    )
    assert INPUTS.policy_transitions == ()
    batches = {b.batch_id: b for b in INPUTS.batches}
    assert sorted(batches) == sorted(
        [b.batch_id for b in PRIOR.batches] + ["character-origins-feats"]
    )
    assert len(batches) == 12
    for prior in PRIOR.batches:
        retained = batches[prior.batch_id]
        # Its diff entries and hash are unchanged.
        assert set(retained.diff) == set(prior.diff)
        assert dataclasses.replace(retained, diff=prior.diff) == prior
    assert set(PRIOR.acceptances) <= set(INPUTS.acceptances)
    assert set(PRIOR.review_unit_acceptances) <= set(INPUTS.review_unit_acceptances)
    assert set(PRIOR.oracle.spans) <= set(INPUTS.oracle.spans)
    assert set(PRIOR.oracle.review_units) <= set(INPUTS.oracle.review_units)
    assert set(PRIOR.oracle.obligations) <= set(INPUTS.oracle.obligations)
    # Each prior resolution is carried unchanged.
    assert set(PRIOR.oracle.reference_resolutions) <= set(
        INPUTS.oracle.reference_resolutions
    )
    assert set(PRIOR.reference_resolution_acceptances) <= set(
        INPUTS.reference_resolution_acceptances
    )


def test_it_records_the_owner_acceptance_of_the_exact_proposal() -> None:
    raw = proposal_path(BATCH).read_bytes()
    assert len(raw) == 384874 and b"\r" not in raw
    assert hashlib.sha256(raw).hexdigest() == BATCHES[BATCH][1]
    assert proposal_identity(PROPOSAL) == identity(BATCH)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "character-origins-feats"]
    assert batch.proposal_identity == identity(BATCH)
    assert batch.rule == REPLACEMENT.APPROVAL
    assert {a.reviewer for a in INPUTS.acceptances} == {"Ravenlok (Owner)"}
    # One consolidated approval: every acceptance carries its single stamp.
    assert {a.accepted_at for a in INPUTS.acceptances} == {REPLACEMENT.ACCEPTED_AT}


def test_the_whole_scope_is_accepted_beside_the_eleven_prior_batches() -> None:
    proposed = {p.span.span_id for p in PROPOSAL.proposed_spans}
    prior = {s.span_id for s in PRIOR.oracle.spans}
    assert (len(proposed), len(prior)) == (172, 844)
    (batch,) = [b for b in INPUTS.batches if b.batch_id == "character-origins-feats"]
    assert set(batch.resolved_scope) == proposed
    assert {s.span_id for s in INPUTS.oracle.spans} == proposed | prior
    assert len(INPUTS.oracle.spans) == 1016
    assert {s.review_state for s in INPUTS.oracle.spans} == {ReviewState.ACCEPTED}
    units = {u.unit_id for u in PROPOSAL.proposed_review_units}
    prior_units = {u.unit_id for u in PRIOR.oracle.review_units}
    assert (len(units), len(prior_units)) == (33, 103)
    assert {u.unit_id for u in INPUTS.oracle.review_units} == units | prior_units
    assert {a.unit_id for a in INPUTS.review_unit_acceptances} == units | prior_units
    assert sum(len(u.leaf_ids) for u in PROPOSAL.proposed_review_units) == 208
    assert INPUTS.oracle.binding == PROPOSAL.binding == PRIOR.oracle.binding


def test_the_representation_is_both_accepted_representations_unchanged() -> None:
    combined = INPUTS.oracle.representation
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(PRIOR.oracle.representation, field.name)
        ) | set(getattr(PROPOSAL.proposed_representation, field.name)), field.name
    assert len(combined.records) == 136
    assert len(PROPOSAL.proposed_representation.records) == 33
    assert len(PROPOSAL.proposed_representation.components) == 149
    assert not {r.semantic_key for r in PROPOSAL.proposed_representation.records} & {
        r.semantic_key for r in PRIOR.oracle.representation.records
    }
    members = [
        r for r in combined.relationships if r.kind is RelationshipKind.CATALOGUE_MEMBER
    ]
    assert len(members) == 30
    assert {(r.source_record_key, r.target_record_key) for r in members} == {
        (m, s) for s, ms in CATALOGUES.items() for m in ms
    }
    # Resolving edits nothing accepted: the representation is step 1's.
    for field in dataclasses.fields(combined):
        assert set(getattr(combined, field.name)) == set(
            getattr(FIRST.oracle.representation, field.name)
        ), field.name


def test_the_three_resolutions_overlay_the_accepted_citations() -> None:
    resolutions = INPUTS.oracle.reference_resolutions
    assert len(resolutions) == 6
    prior_ids = {r.resolution_id for r in PRIOR.oracle.reference_resolutions}
    new = {r for r in resolutions if r.resolution_id not in prior_ids}
    binding = INPUTS.oracle.binding
    assert {
        (r.resolution_id, _citation(r), r.target_record_key, r.provenance_span_ids)
        for r in new
    } == DESTINATIONS
    assert all(r.release_binding == binding for r in new)
    # Exactly the reviewed drafts, as the generator states them.
    assert new == {
        GEN.draft_choose_background_resolution(binding),
        GEN.draft_choose_species_resolution(binding),
        GEN.draft_background_feat_resolution(binding),
    }
    authorizations = set(INPUTS.reference_resolution_acceptances) - set(
        PRIOR.reference_resolution_acceptances
    )
    assert {a.resolution_id for a in authorizations} == {r.resolution_id for r in new}
    for authorization in authorizations:
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
    cited = {c for _, c, _, _ in DESTINATIONS}
    accepted = {
        _citation(r): r.target_record_key
        for r in INPUTS.oracle.representation.references
        if _citation(r) in cited
    }
    assert accepted == {c: "" for c in cited}
    effective = effective_representation(INPUTS.oracle.representation, resolutions)
    assert {
        _citation(r): r.target_record_key
        for r in effective.references
        if _citation(r) in cited
    } == {c: target for _, c, target, _ in DESTINATIONS}


@pytest.fixture(scope="module")
def session(source_release_db: Path):  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{source_release_db}")
    with create_session_factory(engine)() as s:
        yield s
    engine.dispose()


@pytest.mark.parametrize("section", list(CATALOGUES))
def test_the_accepted_authority_reaches_each_catalogue_in_printed_order(  # type: ignore[no-untyped-def]
    session, section
) -> None:
    # The current accepted authority over the current release's ledger (the
    # recorded twelve batches bind the superseded release, whose leaves the
    # current database does not hold), through the projection and selection
    # the service uses: naming a section reads its introduction, then its
    # members.
    candidate = candidate_from_accepted_inputs(current())
    empty = EffectiveOverrideSet(
        candidate.binding.package_uuid, candidate.binding.release_version, ()
    )
    authority = apply_override_set(
        candidate,
        empty,
        RulesPackageBinding(
            package_uuid=UUID(candidate.binding.package_uuid),
            release_version=candidate.binding.release_version,
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "accepted"),
            override_set_uuid=UUID(empty.override_set_uuid),
        ),
        leaf_order=source_leaf_order(session, candidate),
    )
    assert dict(authority.members)[section] == tuple(CATALOGUES[section])
    request = RuleSliceRequest(
        package_id=UUID(candidate.binding.package_uuid), record_selectors=(section,)
    )
    selected, missing = _select(authority, request)
    assert not missing
    assert [r.semantic_key for r in selected] == [section, *CATALOGUES[section]]


def test_three_citations_resolve_and_91_findings_stay() -> None:
    def references(inputs: AcceptedInputs) -> list[str]:
        # Reference findings are the representation's own (resolutions
        # applied): no corpus, so none of the superseded release's is needed.
        rep = candidate_from_accepted_inputs(lifted(inputs)).representation
        findings = relationship_and_reference_violations(rep)
        return sorted(f for f in findings if f.startswith("reference "))

    before = references(PRIOR)
    assert len(before) == 29
    assert set(RESOLVED) <= set(before)
    added = sorted(
        f for f in GEN.expected_representation_findings() if "unresolved reference" in f
    )
    assert Counter(f.split(":")[0].removeprefix("reference ") for f in added) == (
        NEW_UNRESOLVED
    )
    # Accepted but not yet resolved: the batch's 65 catalogue pointers join and
    # every glossary target it cites closes.
    assert references(FIRST) == sorted(before + added)
    assert len(references(FIRST)) == 94
    outstanding = references(INPUTS)
    assert Counter(outstanding) == Counter(before + added) - Counter(RESOLVED)
    assert len(outstanding) == 91
    assert not any("ambiguous" in f for f in outstanding)
