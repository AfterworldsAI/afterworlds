"""Labelled alternative destinations of one citation — CRD Issue 5d, schema 17.

The Owner Decisions of 2026-10-01 (ADR-005d Decision 7, proposed amendment)
let one accepted citation name several destinations, grouped into labelled
routes by the class, class level or situation that selects them. A route's
members are read together, landing first; routes are not exclusive, so several
may apply, and an unknown choice keeps every route rather than guessing one.

Isolated evidence on the bounded synthetic fixture, as in
``test_reference_resolution``: the real batch is drafted in the candidate
harness, not here.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import replace
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import canonical_bytes
from afterworlds.ingestion.mechanical import projection
from afterworlds.ingestion.mechanical.acceptance import (
    AcceptanceError,
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    _accepted_identity,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.models import (
    ReferenceDestination,
    ReferenceResolution,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    OracleLoadError,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    oracle_identity,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (
    compute_persisted_state_digest,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (
    SCHEMA_16_VERSION,
    IdentifiedProjection,
    LegacySchemaPayloadError,
    identify_projection,
    representation_payload,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.publication import (
    PublicationOutcome,
    _publish_projection,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    AlternativeSelection,
    effective_representation,
    routes,
    select_alternatives,
)
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    ReferenceSituation,
    reference_target_key,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_16_HASH,
    SCHEMA_17_HASH,
    SCHEMA_17_VERSION,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.persistence.orm.mechanical import MechanicalReferenceORM
from tests.ingestion.mechanical.conftest import (
    CREATURE_KEY,
    DESCRIPTOR_KEY,
    NOW,
    RELEASE_BINDING,
    SCHEMA_HASH,
    SCHEMA_VERSION,
    SPELL_KEY,
    SPELL_SPAN,
    build_ledger,
    build_representation,
    mark_release_published,
    reference_claim,
)

FIGHTER = "class:fighter"
PALADIN = "class:paladin"

#: The accepted citation: the source names a feature, review found no single
#: destination, and the destination differs by class.
UNRESOLVED = ReferenceDraft(
    from_record_key=SPELL_KEY,
    from_component_key=DESCRIPTOR_KEY,
    source_text="Fighting Style feature",
    scope_key="spell:wish",
    target_record_key="",
)


def _representation(*references: ReferenceDraft):  # type: ignore[no-untyped-def]
    """The bounded fixture plus two class records and *references* with edges."""
    base = build_representation()
    references = references or (UNRESOLVED,)
    return build_representation(
        records=(
            *base.records,
            RecordDraft(semantic_key=FIGHTER, kind=RecordKind.CLASS),
            RecordDraft(semantic_key=PALADIN, kind=RecordKind.CLASS),
        ),
        references=references,
        provenance=base.provenance + tuple(reference_claim(r) for r in references),
    )


def _entries(value: object) -> list[dict[str, object]]:
    """A payload collection, checked to be the list of objects it serializes as."""
    assert isinstance(value, list)
    assert all(isinstance(entry, dict) for entry in value)
    return value


def _alt(
    target: str = FIGHTER,
    label: str = "Fighter",
    **overrides: object,
) -> ReferenceDraft:
    """One resolved alternative of ``UNRESOLVED``."""
    return replace(
        UNRESOLVED,
        target_record_key=target,
        alternative_label=label,
        **overrides,  # type: ignore[arg-type]
    )


FIGHTER_ROUTE = ReferenceDestination(
    target_record_key=FIGHTER,
    target_component_key="",
    alternative_label="Fighter level 1",
    situation="",
    class_record_key=FIGHTER,
    minimum_class_level=1,
)
PALADIN_ROUTE = ReferenceDestination(
    target_record_key=PALADIN,
    target_component_key="",
    alternative_label="Paladin level 2",
    situation="",
    class_record_key=PALADIN,
    minimum_class_level=2,
)


def _accepted(
    schema: tuple[str, str] = (SCHEMA_VERSION, SCHEMA_HASH),
) -> AcceptedInputs:
    proposal = MechanicalProposal(
        binding=RELEASE_BINDING,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        schema_version=schema[0],
        schema_hash=schema[1],
        proposed_spans=tuple(
            ProposedSpan(span, "tool:classifier@0", "stated basis")
            for span in build_ledger().spans
        ),
        proposed_representation=_representation(),
        proposal_origin="tool:proposer@0",
    )
    return accept_proposal(
        proposal,
        batch_id="batch-1",
        rule="every span of the bounded fixture, reviewed together",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer="owner",
        accepted_at="2026-10-01T00:00:00Z",
    )


def _resolution(**overrides: object) -> ReferenceResolution:
    base = dict(
        resolution_id="resolve-fighting-style-1",
        from_record_key=SPELL_KEY,
        from_component_key=DESCRIPTOR_KEY,
        source_text="Fighting Style feature",
        scope_key="spell:wish",
        target_record_key="",
        release_binding=RELEASE_BINDING,
        provenance_span_ids=(SPELL_SPAN,),
        destinations=(FIGHTER_ROUTE, PALADIN_ROUTE),
    )
    return ReferenceResolution(**{**base, **overrides})  # type: ignore[arg-type]


def _resolve(
    prior: AcceptedInputs,
    *resolutions: ReferenceResolution,
    lift_to: tuple[str, str] | None = None,
) -> AcceptedInputs:
    return resolve_references(
        prior,
        lift_to=lift_to,
        resolutions=resolutions or (_resolution(),),
        authorized_by="Owner",
        authorization_reference="Owner Decisions 2026-10-01 (ADR-005d Decision 7)",
        reviewer="Codex",
        resolved_at="2026-10-01T12:00:00Z",
    )


# -- serialization and the singleton -----------------------------------------


def test_an_alternative_serializes_only_the_keys_it_states() -> None:
    ref = _alt(situation=ReferenceSituation.INITIAL_CHARACTER)
    (payload,) = _entries(
        representation_payload(_representation(ref, _alt(PALADIN, "P")))["references"]
    )[:1]
    assert payload["alternative_label"] == "Fighter"
    assert payload["situation"] == "initial_character"
    assert "target_component_key" not in payload
    assert "class_record_key" not in payload
    assert "minimum_class_level" not in payload


def test_a_singleton_reference_keeps_its_accepted_payload_and_coordinate() -> None:
    """Omit-when-empty: nothing accepted under schema 16 moves."""
    single = replace(UNRESOLVED, target_record_key=FIGHTER)
    (payload,) = _entries(representation_payload(_representation(single))["references"])
    assert set(payload) == {
        "from_record_key",
        "from_component_key",
        "source_text",
        "scope_key",
        "target_record_key",
    }
    assert len(reference_target_key(single)) == 5
    assert representation_payload(
        _representation(single), schema_version=SCHEMA_16_VERSION
    ) == representation_payload(_representation(single))


def test_a_legacy_schema_refuses_rather_than_drops_an_alternative() -> None:
    with pytest.raises(LegacySchemaPayloadError):
        representation_payload(
            _representation(_alt(), _alt(PALADIN, "Paladin")),
            schema_version=SCHEMA_16_VERSION,
        )


# -- the validator: routes, their members, and ambiguity -----------------------


def test_labelled_alternatives_of_one_citation_are_legal() -> None:
    draft = _representation(_alt(), _alt(PALADIN, "Paladin"))
    assert relationship_and_reference_violations(draft) == []


def test_one_route_may_read_several_destinations_together() -> None:
    """A landing and its supporting text share one label; that is one route."""
    multi = ReferenceSituation.MULTICLASS
    group = (
        _alt(FIGHTER, "Multiclass", situation=multi),
        _alt(PALADIN, "Multiclass", situation=multi),
    )
    assert relationship_and_reference_violations(_representation(*group)) == []
    single = _alt(CREATURE_KEY, "Single", situation=ReferenceSituation.SINGLE_CLASS)
    mixed = _representation(single, *group)
    assert relationship_and_reference_violations(mixed) == []
    assert [label for label, _ in routes(mixed.references)] == ["Single", "Multiclass"]


def test_unlabelled_destinations_of_one_citation_stay_ambiguous() -> None:
    """Two destinations without labels read as both; that is not an alternative."""
    draft = _representation(_alt(label=""), _alt(PALADIN, ""))
    assert any("ambiguous" in f for f in relationship_and_reference_violations(draft))


@pytest.mark.parametrize(
    "references",
    [
        pytest.param((_alt(), _alt(PALADIN, "")), id="one-unlabelled"),
        pytest.param(
            (_alt(class_record_key=FIGHTER), _alt(PALADIN, "Fighter")),
            id="route-with-split-conditions",
        ),
        pytest.param((_alt(),), id="lone-labelled"),
    ],
)
def test_an_incomplete_alternative_set_is_a_finding(
    references: tuple[ReferenceDraft, ...],
) -> None:
    assert relationship_and_reference_violations(_representation(*references))


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        pytest.param(
            _alt(target_component_key="no-such-component"),
            "does not exist",
            id="unknown-component",
        ),
        pytest.param(
            _alt(SPELL_KEY, target_component_key="no-such-component"),
            "does not exist",
            id="wrong-grain",
        ),
        pytest.param(
            _alt(CREATURE_KEY, class_record_key=SPELL_KEY),
            "is not a class record",
            id="class-key-not-a-class",
        ),
        pytest.param(
            _alt(class_record_key=FIGHTER, minimum_class_level=21),
            "outside 0-20",
            id="level-past-twenty",
        ),
        pytest.param(
            _alt(minimum_class_level=3), "names no class", id="level-without-class"
        ),
        pytest.param(_alt(label=" Fighter"), "not trimmed", id="untrimmed-label"),
        pytest.param(
            _alt("no:such-record"),
            "unknown target record",
            id="unknown-target-record",
        ),
    ],
)
def test_an_inexact_alternative_is_a_finding(bad: ReferenceDraft, message: str) -> None:
    draft = _representation(bad, _alt(PALADIN, "Paladin"))
    findings = relationship_and_reference_violations(draft)
    assert any(message in f for f in findings), findings


def test_a_component_destination_on_its_own_record_is_exact() -> None:
    draft = _representation(
        _alt(SPELL_KEY, "component", target_component_key=DESCRIPTOR_KEY),
        _alt(PALADIN, "Paladin"),
    )
    assert relationship_and_reference_violations(draft) == []


def test_alternative_keys_without_a_target_are_a_finding() -> None:
    draft = _representation(replace(UNRESOLVED, alternative_label="Fighter"))
    findings = relationship_and_reference_violations(draft)
    assert any("but no target" in f for f in findings), findings


# -- resolution: fan-out, provenance, identity ---------------------------------


def test_a_resolution_fans_one_citation_out_in_reviewed_order() -> None:
    resolved = _resolve(_accepted())
    view = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )
    refs = [r for r in view.references if r.source_text == UNRESOLVED.source_text]
    assert [(r.target_record_key, r.alternative_label) for r in refs] == [
        (FIGHTER, "Fighter level 1"),
        (PALADIN, "Paladin level 2"),
    ]
    assert [(r.class_record_key, r.minimum_class_level) for r in refs] == [
        (FIGHTER, 1),
        (PALADIN, 2),
    ]
    # Every alternative carries the citation's provenance; none is orphaned.
    claimed = {
        c.target_key
        for c in view.provenance
        if c.target_kind is ProvenanceTargetKind.REFERENCE
    }
    assert {reference_target_key(r) for r in refs} <= claimed
    assert reference_target_key(UNRESOLVED) not in claimed
    assert relationship_and_reference_violations(view) == []


def test_the_gate_and_the_build_derive_the_same_identity() -> None:
    resolved = _resolve(_accepted())
    assert (
        _accepted_identity(resolved.oracle)
        == identify_projection(candidate_from_accepted_inputs(resolved)).projection_uuid
    )


def test_the_artifact_round_trips_through_its_committed_form(tmp_path: Path) -> None:
    resolved = _resolve(_accepted())
    path = tmp_path / "resolved.json"
    path.write_bytes(serialize_accepted_inputs(resolved))
    reloaded = load_accepted_inputs(path)
    assert (
        reloaded.oracle.reference_resolutions == resolved.oracle.reference_resolutions
    )
    assert oracle_identity(reloaded.oracle) == oracle_identity(resolved.oracle)
    assert serialize_accepted_inputs(reloaded) == path.read_bytes()


def test_a_single_destination_resolution_writes_no_destinations_key() -> None:
    resolved = _resolve(
        _accepted(), _resolution(destinations=(), target_record_key=FIGHTER)
    )
    (stated,) = _entries(accepted_inputs_payload(resolved)["reference_resolutions"])
    assert "destinations" not in stated


def test_persistence_reconstructs_every_alternative(session: Session) -> None:
    resolved = _resolve(_accepted())
    identified = identify_projection(candidate_from_accepted_inputs(resolved))
    persist_draft(session, identified, now=NOW)
    session.flush()
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert (
        rebuilt.representation.references
        == identified.candidate.representation.references
    )
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid


def test_the_publication_gate_judges_the_alternatives(session: Session) -> None:
    """The resolved view publishes; the stored, unresolved view does not."""
    resolved = _resolve(_accepted())
    mark_release_published(session)
    for inputs, expected in ((resolved, True), (_accepted(), False)):
        identified = identify_projection(candidate_from_accepted_inputs(inputs))
        persist_draft(session, identified, now=NOW)
        record_persisted_state_digest(session, identified.projection_uuid)
        session.flush()
        result = run_publication_gate(
            session, identified.projection_uuid, resolved.oracle
        )
        assert result.passed is expected, result.failures


# -- route order is meaning (ADR-005d Decision 7, 2026-10-01) -----------------

#: One route, Fighter landing and Paladin support: the stated order a reader is
#: shown, which is also the order a plain canonical sort happens to produce.
ONE_ROUTE = tuple(
    replace(
        d, alternative_label="one route", class_record_key="", minimum_class_level=0
    )
    for d in (FIGHTER_ROUTE, PALADIN_ROUTE)
)
#: The identity the reversed route persisted under before route order was
#: identity-bearing — the same as the stated order's, which is the defect.
#: Captured from the unfixed build (parent ``5795e93``), whose artifacts were
#: schema 17: the pre-fix state is rebuilt under that contract
#: (:data:`SCHEMA_17`), not under whatever schema the build has since reached.
SCHEMA_16 = (SCHEMA_16_VERSION, SCHEMA_16_HASH)
#: The contract the reference-alternatives lift introduced, pinned: it stays
#: schema 17 after later successions (schema 18, CRD Issue 2b G1).
SCHEMA_17 = (SCHEMA_17_VERSION, SCHEMA_17_HASH)
PRE_FIX_UUID = "29b1d00f-737f-5605-90ea-0d7a1a984822"


def _route_identified(
    destinations: tuple[ReferenceDestination, ...],
) -> IdentifiedProjection:
    return identify_projection(
        candidate_from_accepted_inputs(
            _resolve(_accepted(), _resolution(destinations=destinations))
        )
    )


def _stated(session: Session, projection_uuid: str) -> list[tuple[str, list[str]]]:
    references = reconstruct_candidate(session, projection_uuid).representation
    return [
        (label, [r.target_record_key for r in members])
        for label, members in routes(references.references)
    ]


def test_route_and_member_order_are_identity_bearing() -> None:
    stated = _route_identified(ONE_ROUTE)
    assert _route_identified(ONE_ROUTE[::-1]).projection_uuid != stated.projection_uuid
    two = (FIGHTER_ROUTE, PALADIN_ROUTE)
    assert (
        _route_identified(two[::-1]).projection_uuid
        != _route_identified(two).projection_uuid
    )


def test_independent_citations_stay_canonically_unordered() -> None:
    first = (_alt(FIGHTER, "one route"), _alt(PALADIN, "one route"))
    second = tuple(replace(r, source_text="Other feature") for r in first)
    single = replace(UNRESOLVED, source_text="Third", target_record_key=FIGHTER)

    def payload(*refs: ReferenceDraft) -> list[dict[str, object]]:
        return _entries(representation_payload(_representation(*refs))["references"])

    stated = payload(*first, *second, single)
    assert payload(single, *second, *first) == stated
    assert payload(first[0], second[0], single, first[1], second[1]) == stated
    assert payload(first[1], first[0], *second, single) != stated
    # With no route, references are a set in exactly the plain canonical order.
    unrouted = payload(single, replace(single, source_text="Fourth"))
    assert unrouted == sorted(unrouted, key=canonical_bytes)


def test_the_stated_route_order_round_trips_through_sql(session: Session) -> None:
    for destinations, expected in (
        (ONE_ROUTE, [FIGHTER, PALADIN]),
        (ONE_ROUTE[::-1], [PALADIN, FIGHTER]),
    ):
        identified = _route_identified(destinations)
        persist_draft(session, identified, now=NOW)
        session.flush()
        assert _stated(session, identified.projection_uuid) == [("one route", expected)]
        rebuilt = reconstruct_candidate(session, identified.projection_uuid)
        assert (
            identify_projection(rebuilt).projection_uuid == identified.projection_uuid
        )


def test_a_swapped_destination_changes_the_digest_and_fails_the_gate(
    session: Session,
) -> None:
    resolved = _resolve(_accepted(), _resolution(destinations=ONE_ROUTE))
    identified = identify_projection(candidate_from_accepted_inputs(resolved))
    uuid_ = identified.projection_uuid
    mark_release_published(session)
    persist_draft(session, identified, now=NOW)
    recorded = record_persisted_state_digest(session, uuid_)
    assert run_publication_gate(session, uuid_, resolved.oracle).passed

    first, second = session.scalars(
        sa.select(MechanicalReferenceORM)
        .where(MechanicalReferenceORM.projection_uuid == uuid_)
        .order_by(MechanicalReferenceORM.row_id)
    )
    for column in ("target_record_key", "target_component_key", "situation"):
        a, b = getattr(first, column), getattr(second, column)
        setattr(first, column, b)
        setattr(second, column, a)
    session.flush()

    assert _stated(session, uuid_) == [("one route", [PALADIN, FIGHTER])]
    assert compute_persisted_state_digest(session, uuid_) != recorded
    result = run_publication_gate(session, uuid_, resolved.oracle)
    assert not result.passed
    assert GateFailureCategory.PERSISTED_STATE in result.categories()
    assert any(
        "reconstructed state derives" in f.detail for f in result.failures
    ), result.failures


def test_a_projection_persisted_before_route_order_counted_is_stale(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pre-fix state is refused as stale; nothing re-blesses its digest."""
    resolved = _resolve(_accepted(SCHEMA_17), _resolution(destinations=ONE_ROUTE[::-1]))
    mark_release_published(session)
    with monkeypatch.context() as pre_fix:
        # The unfixed rule: every reference sorted as one set.
        pre_fix.setattr(
            projection,
            "_references_payload",
            lambda refs, version: canonical_order(
                projection._reference_payload(r, version) for r in refs
            ),
        )
        identified = identify_projection(candidate_from_accepted_inputs(resolved))
        persist_draft(session, identified, now=NOW)
        record_persisted_state_digest(session, identified.projection_uuid)
    assert identified.projection_uuid == PRE_FIX_UUID

    gate = run_publication_gate(session, PRE_FIX_UUID, resolved.oracle)
    assert GateFailureCategory.PERSISTED_STATE in gate.categories(), gate.failures
    assert GateFailureCategory.IDENTITY_MISMATCH in gate.categories(), gate.failures
    published = _publish_projection(session, PRE_FIX_UUID, resolved.oracle, now=NOW)
    assert published.outcome is PublicationOutcome.STALE


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        pytest.param(
            {"target_record_key": FIGHTER}, "both a destination", id="both-forms"
        ),
        pytest.param(
            {"destinations": (FIGHTER_ROUTE,)}, "one alternative", id="one-alternative"
        ),
        pytest.param(
            {"destinations": (FIGHTER_ROUTE, replace(PALADIN_ROUTE, situation="x"))},
            "unknown situation",
            id="unknown-situation",
        ),
        pytest.param(
            {
                "destinations": (
                    FIGHTER_ROUTE,
                    replace(PALADIN_ROUTE, target_record_key="no:such-record"),
                )
            },
            "no:such-record",
            id="unknown-destination",
        ),
        pytest.param(
            {
                "destinations": (
                    FIGHTER_ROUTE,
                    replace(PALADIN_ROUTE, target_component_key="nothing"),
                )
            },
            "does not exist",
            id="wrong-grain-destination",
        ),
        pytest.param(
            {
                "destinations": (
                    FIGHTER_ROUTE,
                    replace(PALADIN_ROUTE, alternative_label=""),
                )
            },
            "ambiguous",
            id="unlabelled-destination",
        ),
        pytest.param(
            {"release_binding": replace(RELEASE_BINDING, bundle_root_hash="0" * 64)},
            "was reviewed against release",
            id="release-mismatch",
        ),
        pytest.param(
            {"provenance_span_ids": ()}, "provenance spans", id="no-provenance"
        ),
    ],
)
def test_an_inexact_resolution_is_refused_whole(
    overrides: dict[str, object], message: str
) -> None:
    prior = _accepted()
    with pytest.raises(AcceptanceError, match=message):
        _resolve(prior, _resolution(**overrides))


def test_an_accepted_destination_is_not_overridden_by_alternatives() -> None:
    """Retargeting stays unauthorized: alternatives resolve only an empty target."""
    once = _resolve(
        _accepted(), _resolution(destinations=(), target_record_key=FIGHTER)
    )
    with pytest.raises(AcceptanceError, match="conflicts with"):
        _resolve(once, _resolution(resolution_id="resolve-fighting-style-2"))


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda d: d.pop("alternative_label"), id="missing-field"),
        pytest.param(
            lambda d: d.__setitem__("minimum_class_level", True), id="bool-level"
        ),
        pytest.param(
            lambda d: d.__setitem__("minimum_class_level", "1"), id="string-level"
        ),
    ],
)
def test_a_malformed_committed_destination_fails_closed(
    tmp_path: Path, mutate: object
) -> None:
    payload = json.loads(serialize_accepted_inputs(_resolve(_accepted())))
    mutate(payload["reference_resolutions"][0]["destinations"][1])  # type: ignore[operator]
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(path)


# -- the consumer: select, never guess ------------------------------------------

HIT_POINTS = (
    _alt(CREATURE_KEY, "initial", situation=ReferenceSituation.INITIAL_CHARACTER),
    _alt(CREATURE_KEY, "later", situation=ReferenceSituation.LATER_LEVEL),
)
STYLE = (
    _alt(FIGHTER, "Fighter", class_record_key=FIGHTER, minimum_class_level=1),
    _alt(PALADIN, "Paladin", class_record_key=PALADIN, minimum_class_level=2),
)
MULTICLASS_ENTRY = (
    _alt(FIGHTER, "Fighter", class_record_key=FIGHTER),
    _alt(PALADIN, "Paladin", class_record_key=PALADIN),
)


def test_a_missing_selection_keeps_every_alternative_in_order() -> None:
    for refs in (HIT_POINTS, STYLE, MULTICLASS_ENTRY):
        assert select_alternatives(refs, AlternativeSelection()) == refs


def test_a_situation_known_not_to_hold_drops_its_alternative() -> None:
    later = AlternativeSelection(
        situations={ReferenceSituation.INITIAL_CHARACTER: False}
    )
    assert select_alternatives(HIT_POINTS, later) == HIT_POINTS[1:]
    # Known true says nothing about the other situation, so it is kept.
    first = AlternativeSelection(
        situations={ReferenceSituation.INITIAL_CHARACTER: True}
    )
    assert select_alternatives(HIT_POINTS, first) == HIT_POINTS


def test_a_class_level_route_reads_the_level_in_that_class_not_the_total() -> None:
    """Fighter 1 / Paladin 1 is total level 2 and still not a Paladin level 2."""
    split = AlternativeSelection(class_levels={FIGHTER: 1, PALADIN: 1})
    assert select_alternatives(STYLE, split) == STYLE[:1]
    # An unknown class level keeps the route rather than guessing it away.
    partial = AlternativeSelection(class_levels={FIGHTER: 1})
    assert select_alternatives(STYLE, partial) == STYLE
    none = AlternativeSelection(class_levels={FIGHTER: 0, PALADIN: 1})
    assert select_alternatives(STYLE, none) == ()


def test_a_class_route_without_a_level_drops_only_a_known_other_class() -> None:
    entering = AlternativeSelection(class_record_keys=frozenset({PALADIN}))
    assert select_alternatives(MULTICLASS_ENTRY, entering) == MULTICLASS_ENTRY[1:]


def test_known_class_and_known_level_both_constrain_a_route() -> None:
    """A level route is still a class route: the class is checked too."""
    paladin_only = AlternativeSelection(
        class_record_keys=frozenset({PALADIN}), class_levels={FIGHTER: 5, PALADIN: 2}
    )
    assert select_alternatives(STYLE, paladin_only) == STYLE[1:]
    too_low = AlternativeSelection(
        class_record_keys=frozenset({PALADIN}), class_levels={PALADIN: 1}
    )
    assert select_alternatives(STYLE, too_low) == ()
    # Several qualifying classes are routes that all apply, not a contradiction.
    both = AlternativeSelection(
        class_record_keys=frozenset({FIGHTER, PALADIN}),
        class_levels={FIGHTER: 1, PALADIN: 2},
    )
    assert select_alternatives(STYLE, both) == STYLE
    # A known class with an unknown level keeps that class's route.
    unknown_level = AlternativeSelection(class_record_keys=frozenset({PALADIN}))
    assert select_alternatives(STYLE, unknown_level) == STYLE[1:]


def test_selection_never_adds_or_reorders() -> None:
    mixed = (*STYLE, *HIT_POINTS)
    kept = select_alternatives(mixed, AlternativeSelection(class_levels={FIGHTER: 5}))
    assert kept == mixed
    assert select_alternatives(reversed(mixed), AlternativeSelection()) == tuple(
        reversed(mixed)
    )


# -- the schema seam and the native lift ---------------------------------------


def test_a_schema_16_artifact_refuses_routes_at_the_seam() -> None:
    with pytest.raises(AcceptanceError, match="cannot"):
        _resolve(_accepted(SCHEMA_16))


def test_the_loader_refuses_routes_under_schema_16(tmp_path: Path) -> None:
    """The same trust boundary when a file, not the seam, states them."""
    prior = _accepted(SCHEMA_16)
    smuggled = replace(
        prior,
        oracle=replace(prior.oracle, reference_resolutions=(_resolution(),)),
    )
    path = tmp_path / "smuggled.json"
    path.write_bytes(serialize_accepted_inputs(smuggled))
    with pytest.raises(OracleLoadError, match="cannot"):
        load_accepted_inputs(path)


def test_lift_and_resolve_is_one_native_action(tmp_path: Path) -> None:
    prior = _accepted(SCHEMA_16)
    before = serialize_accepted_inputs(prior)
    resolved = _resolve(prior, lift_to=SCHEMA_17)
    assert (resolved.oracle.schema_version, resolved.oracle.schema_hash) == SCHEMA_17
    assert [r.lift_id for r in resolved.lifts[len(prior.lifts) :]] == [
        "5d-lift-schema-16-to-17"
    ]
    path = tmp_path / "lifted.json"
    path.write_bytes(serialize_accepted_inputs(resolved))
    assert serialize_accepted_inputs(load_accepted_inputs(path)) == path.read_bytes()
    # Either half refused leaves nothing behind: the caller keeps its artifact.
    with pytest.raises(AcceptanceError, match="cannot be lifted"):
        _resolve(prior, lift_to=("no-such-schema", "0" * 64))
    with pytest.raises(AcceptanceError, match="provenance spans"):
        _resolve(prior, _resolution(provenance_span_ids=()), lift_to=SCHEMA_17)
    assert serialize_accepted_inputs(prior) == before


def test_lifting_to_the_current_build_runs_every_later_succession() -> None:
    """The current native action from schema 16 lifts through 17 to the build's
    schema (20, CRD Issue 15c C7); the historical 16 -> 17 action above is unchanged."""
    from afterworlds.ingestion.mechanical.representation import (
        REPRESENTATION_SCHEMA_VERSION,
        representation_schema_hash,
    )

    current = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    prior = _accepted(SCHEMA_16)
    resolved = _resolve(prior, lift_to=current)
    assert (resolved.oracle.schema_version, resolved.oracle.schema_hash) == current
    assert [r.lift_id for r in resolved.lifts[len(prior.lifts) :]] == [
        "5d-lift-schema-16-to-17",
        "5d-lift-schema-17-to-18",
        "5d-lift-schema-18-to-19",
        "5d-lift-schema-19-to-20",
    ]


def test_a_singleton_resolution_needs_no_lift() -> None:
    """Legacy identity: schema 16 still resolves one destination, unchanged."""
    prior = _accepted(SCHEMA_16)
    single = _resolve(prior, _resolution(destinations=(), target_record_key=FIGHTER))
    assert single.oracle.schema_version == SCHEMA_16_VERSION
    assert single.lifts == prior.lifts
    (stated,) = _entries(accepted_inputs_payload(single)["reference_resolutions"])
    assert "destinations" not in stated


# -- migration 0036 -------------------------------------------------------------


def _alembic_cfg(db_path: str):  # type: ignore[no-untyped-def]
    from alembic.config import Config

    cfg = Config(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "alembic.ini")
    )
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _insert_reference(db_path: str, **columns: object) -> None:
    engine = sa.create_engine(f"sqlite:///{db_path}")
    row = {
        "projection_uuid": "p",
        "from_record_key": "a",
        "from_component_key": "",
        "source_text": "s",
        "scope_key": "x",
        "target_record_key": "b",
        **columns,
    }
    names = ", ".join(row)
    values = ", ".join(f":{k}" for k in row)
    with engine.begin() as conn:
        conn.execute(
            sa.text(f"INSERT INTO rp_mech_references ({names}) VALUES ({values})"), row
        )
    engine.dispose()


def test_migration_0036_defaults_existing_rows_and_refuses_a_lossy_downgrade() -> None:
    from alembic import command

    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "scratch.db")
        cfg = _alembic_cfg(db_path)
        command.upgrade(cfg, "0035")
        _insert_reference(db_path)
        command.upgrade(cfg, "0036")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        with engine.connect() as conn:
            row = conn.execute(
                sa.text(
                    "SELECT target_component_key, alternative_label, situation, "
                    "class_record_key, minimum_class_level FROM rp_mech_references"
                )
            ).one()
        engine.dispose()
        assert tuple(row) == ("", "", None, "", 0)

        _insert_reference(db_path, alternative_label="Fighter")
        with pytest.raises(RuntimeError, match="1 reference rows"):
            command.downgrade(cfg, "0035")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        with engine.begin() as conn:
            conn.execute(
                sa.text("DELETE FROM rp_mech_references WHERE alternative_label != ''")
            )
        engine.dispose()
        command.downgrade(cfg, "0035")
        engine = sa.create_engine(f"sqlite:///{db_path}")
        columns = {
            c["name"] for c in sa.inspect(engine).get_columns("rp_mech_references")
        }
        engine.dispose()
        assert "alternative_label" not in columns
