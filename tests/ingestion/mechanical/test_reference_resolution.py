"""Reviewed resolution of an accepted empty-target reference — CRD Issue 5d.

The Owner Decision of 2026-09-19 (ADR-005d Decision 7) authorizes one bounded
capability: an accepted reference that was accepted with **no** destination may
be given one by an explicit, authorized, recorded decision. These tests hold the
whole of it and its edges.

**Isolated evidence, deliberately.** Every scenario here runs on the bounded
synthetic fixture in ``conftest`` — two records, one of which is a legitimate
destination. The four real unresolved citations on this branch (*Stat Block*,
*Combat Encounters*, *Combat*, *Opportunity Attack*) name records no accepted
batch has minted and no reviewer has keyed, so resolving one of them here would
be inventing exactly the destination review refused to guess. The real
proposals' four obligations stay open, and
``test_proficiency_references_resolve`` still pins them as unresolved.

What each group proves:

* the production path — accept an unresolved citation, resolve it explicitly, and
  get one effective destination with the accepted history intact;
* meaning versus evidence — the decision moves identity, the authorization does
  not;
* persistence, serialization and replay — the same artifact, deterministically;
* one decision over several citations — two components of one record may cite
  the same wording legitimately, but ``(scope, source_text)`` has one
  destination, so those citations are resolved *together*, whole or not at all;
* the negative controls — unauthorized, stale, conflicting, mismatched, missing
  and tampered inputs each fail closed, and nothing is partly recorded;
* the boundary — a later batch can neither author a destination for an
  unresolved citation nor retarget an accepted one, and the seven accepted
  batches keep their exact committed bytes and identity.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.acceptance import (
    AcceptanceError,
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    _accepted_identity,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.models import (
    ReferenceResolution,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    OracleLoadError,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    derive_obligations,
    load_accepted_inputs,
    oracle_identity,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.reference_resolution import (
    effective_representation,
)
from afterworlds.ingestion.mechanical.representation import (
    RECORD_OWNED_REFERENCE,
    ProvenanceRole,
    ProvenanceTargetKind,
    ReferenceDraft,
    reference_target_key,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_14_HASH,
    SCHEMA_14_VERSION,
    SCHEMA_15_HASH,
    SCHEMA_15_VERSION,
    UnknownSchemaLiftError,
    lift_accepted_inputs,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from tests.ingestion.mechanical.conftest import (
    CREATURE_KEY,
    DESCRIPTOR_KEY,
    NOW,
    OPEN_ENDED_KEY,
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

#: The accepted citation under test: the source says *"the servant"* inside the
#: ``spell:wish`` scope, and review found no destination key it could state.
#: Exactly the shape the four real citations have.
UNRESOLVED = ReferenceDraft(
    from_record_key=SPELL_KEY,
    from_component_key=DESCRIPTOR_KEY,
    source_text="the servant",
    scope_key="spell:wish",
    target_record_key="",
)

#: The destination review approves in these scenarios. A record the accepted
#: representation already states — a resolution may not mint one.
DESTINATION = CREATURE_KEY

UNRESOLVED_FINDING = "reference spell:wish:'the servant': unresolved reference"


def _representation(*extra_references: ReferenceDraft):  # type: ignore[no-untyped-def]
    """The bounded fixture, carrying the unresolved citation and its provenance.

    Every reference gets its own edge because ``REFERENCE`` is in
    ``PROVENANCE_REQUIRED_KINDS``: a citation with no provenance is not a
    weaker citation, it is one whose source nobody recorded.
    """
    references = (UNRESOLVED, *extra_references)
    base = build_representation()
    return build_representation(
        references=references,
        provenance=base.provenance + tuple(reference_claim(ref) for ref in references),
    )


def _proposal(representation=None, **overrides: object) -> MechanicalProposal:  # type: ignore[no-untyped-def]
    base = dict(
        binding=RELEASE_BINDING,
        policy_version=SEMANTIC_POLICY_VERSION,
        policy_hash=semantic_policy_hash(),
        schema_version=SCHEMA_VERSION,
        schema_hash=SCHEMA_HASH,
        proposed_spans=tuple(
            ProposedSpan(span, "tool:classifier@0", "stated basis")
            for span in build_ledger().spans
        ),
        proposed_representation=(
            _representation() if representation is None else representation
        ),
        proposal_origin="tool:proposer@0",
    )
    return MechanicalProposal(**{**base, **overrides})  # type: ignore[arg-type]


def _accepted(**overrides: object) -> AcceptedInputs:
    """Accepted authority carrying one unresolved citation, via the real seam."""
    proposal = _proposal(**overrides)
    return accept_proposal(
        proposal,
        batch_id="batch-1",
        rule="every span of the bounded fixture, reviewed together",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer="owner",
        accepted_at="2026-09-19T00:00:00Z",
    )


def _resolution(**overrides: object) -> ReferenceResolution:
    base = dict(
        resolution_id="resolve-the-servant-1",
        from_record_key=SPELL_KEY,
        from_component_key=DESCRIPTOR_KEY,
        source_text="the servant",
        scope_key="spell:wish",
        target_record_key=DESTINATION,
        package_uuid=RELEASE_BINDING.package_uuid,
        release_version=RELEASE_BINDING.release_version,
        provenance_span_ids=(SPELL_SPAN,),
    )
    return ReferenceResolution(**{**base, **overrides})  # type: ignore[arg-type]


def _resolve(
    prior: AcceptedInputs,
    *resolutions: ReferenceResolution,
    **overrides: object,
) -> AcceptedInputs:
    """One reviewed decision over ``resolutions``, defaulting to the single one.

    ``resolutions`` is positional because the whole point of the plural seam is
    that one action carries however many citations the decision covers; every
    scenario that cares about the authorization states it as a keyword.
    """
    base = dict(
        resolutions=resolutions or (_resolution(),),
        authorized_by="Owner",
        authorization_reference="Owner Decision 2026-09-19 (ADR-005d Decision 7)",
        reviewer="Codex",
        resolved_at="2026-09-19T12:00:00Z",
    )
    return resolve_references(prior, **{**base, **overrides})  # type: ignore[arg-type]


#: A second *component* of the same record citing the same wording in the same
#: scope. Legal by design — each component's citation is its own claim with its
#: own provenance — and the reason one decision has to be able to cover both:
#: ``(scope, source_text)`` resolves to exactly one record or it is ambiguous.
SIBLING_UNRESOLVED = ReferenceDraft(
    from_record_key=SPELL_KEY,
    from_component_key=OPEN_ENDED_KEY,
    source_text="the servant",
    scope_key="spell:wish",
    target_record_key="",
)

#: An unrelated second unresolved citation: different wording, so its
#: destination is nobody else's business and it may be resolved on its own.
OTHER_UNRESOLVED = ReferenceDraft(
    from_record_key=SPELL_KEY,
    from_component_key=OPEN_ENDED_KEY,
    source_text="the wish it was cast from",
    scope_key="spell:wish",
    target_record_key="",
)


#: The *record* stating the same citation directly, beside the component that
#: states it. Publication already refuses this pair — a record owns a reference
#: only where no component states it — and a joint resolution must not launder
#: it by moving both to one destination.
RECORD_OWNED_SIBLING = ReferenceDraft(
    from_record_key=SPELL_KEY,
    from_component_key=RECORD_OWNED_REFERENCE,
    source_text="the servant",
    scope_key="spell:wish",
    target_record_key="",
)

#: The same wording cited in a *different* scope. Scope is part of both the
#: citation key and the ambiguity key, so these two citations are independent
#: decisions and may legitimately go to different records.
OTHER_SCOPE_UNRESOLVED = ReferenceDraft(
    from_record_key=SPELL_KEY,
    from_component_key=OPEN_ENDED_KEY,
    source_text="the servant",
    scope_key="spell:simulacrum",
    target_record_key="",
)


def _sibling_resolution(**overrides: object) -> ReferenceResolution:
    """The decision about ``SIBLING_UNRESOLVED`` — its own id and its own citation."""
    return _resolution(
        resolution_id="resolve-the-servant-open-ended-1",
        from_component_key=OPEN_ENDED_KEY,
        **overrides,
    )


def _record_owned_resolution(**overrides: object) -> ReferenceResolution:
    """The decision about ``RECORD_OWNED_SIBLING``."""
    return _resolution(
        resolution_id="resolve-the-servant-record-owned-1",
        from_component_key=RECORD_OWNED_REFERENCE,
        **overrides,
    )


def _other_scope_resolution(**overrides: object) -> ReferenceResolution:
    """The decision about ``OTHER_SCOPE_UNRESOLVED``."""
    return _resolution(
        resolution_id="resolve-the-servant-simulacrum-1",
        from_component_key=OPEN_ENDED_KEY,
        scope_key="spell:simulacrum",
        **overrides,
    )


def _other_resolution(**overrides: object) -> ReferenceResolution:
    """The decision about ``OTHER_UNRESOLVED``."""
    return _resolution(
        resolution_id="resolve-the-wish-1",
        from_component_key=OPEN_ENDED_KEY,
        source_text="the wish it was cast from",
        **overrides,
    )


# -- the production path ------------------------------------------------------


def test_an_unresolved_citation_is_accepted_and_stays_detectably_unresolved() -> None:
    """Acceptance does not close it, and the honest finding survives acceptance.

    This is the state the four real citations are in. Nothing here repairs it
    implicitly: with no resolution recorded, the effective view *is* the accepted
    view, and publication still reports the obligation.
    """
    accepted = _accepted()
    assert accepted.oracle.reference_resolutions == ()
    assert accepted.reference_resolution_acceptances == ()
    assert UNRESOLVED_FINDING in relationship_and_reference_violations(
        accepted.oracle.representation
    )
    assert (
        effective_representation(accepted.oracle.representation, ())
        is accepted.oracle.representation
    )
    assert UNRESOLVED_FINDING in relationship_and_reference_violations(
        candidate_from_accepted_inputs(accepted).representation
    )


def test_an_explicit_resolution_yields_exactly_one_effective_destination() -> None:
    resolved = _resolve(_accepted())
    effective = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )

    (reference,) = effective.references
    assert reference.target_record_key == DESTINATION
    # Replaced in place, not appended beside: one citation, one destination.
    assert len(effective.references) == len(resolved.oracle.representation.references)
    assert relationship_and_reference_violations(effective) == []


def test_the_resolution_moves_the_citations_provenance_with_it() -> None:
    """A reference's provenance is keyed by the reference — target included.

    Left behind, the claim would address an element the effective view does not
    state *and* leave the resolved citation with no provenance at all, which
    ``PROVENANCE_REQUIRED_KINDS`` refuses.
    """
    resolved = _resolve(_accepted())
    stored = resolved.oracle.representation
    effective = effective_representation(stored, resolved.oracle.reference_resolutions)

    assert len(effective.provenance) == len(stored.provenance)
    claims = {
        c.target_key: c
        for c in effective.provenance
        if c.target_kind is ProvenanceTargetKind.REFERENCE
    }
    assert set(claims) == {reference_target_key(effective.references[0])}
    moved = claims[reference_target_key(effective.references[0])]
    assert (moved.span_id, moved.role) == (SPELL_SPAN, ProvenanceRole.CONTEXTUAL)


def test_the_effective_view_never_quietly_retargets() -> None:
    """A view that applied a retarget would make the refusal unenforceable.

    ``reference_resolution_violations`` refuses a resolution naming a citation
    that already resolves — but only a caller that asked. A view that applied it
    anyway would hand the retarget to every caller that did not, so a resolution
    with nothing empty to fill returns the accepted representation itself.
    """
    already = replace(UNRESOLVED, target_record_key=SPELL_KEY)
    representation = build_representation(
        references=(already,),
        provenance=build_representation().provenance + (reference_claim(already),),
    )
    assert effective_representation(representation, (_resolution(),)) is representation


def test_the_accepted_history_is_not_rewritten() -> None:
    """The original citation, its evidence and its obligations are untouched.

    The whole point of Option A: the artifact still states what every reviewer
    actually accepted, so the acceptance can be audited after the resolution
    exactly as it could before.
    """
    accepted = _accepted()
    resolved = _resolve(accepted)

    assert resolved.oracle.representation == accepted.oracle.representation
    assert UNRESOLVED in resolved.oracle.representation.references
    assert resolved.batches == accepted.batches
    assert resolved.acceptances == accepted.acceptances
    assert resolved.schema_anchors == accepted.schema_anchors
    assert resolved.oracle.spans == accepted.oracle.spans
    assert resolved.oracle.obligations == accepted.oracle.obligations


def test_both_views_state_the_same_obligations() -> None:
    """The loader derives obligations from stored state, the gate judges effective.

    They must not be able to disagree. References carry no obligation, so a
    resolution cannot move one — asserted rather than assumed, because a future
    obligation over references would silently split the two.
    """
    resolved = _resolve(_accepted())
    effective = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )
    assert derive_obligations(effective) == derive_obligations(
        resolved.oracle.representation
    )
    assert resolved.oracle.obligations == derive_obligations(effective)


# -- meaning moves; evidence does not -----------------------------------------


def test_the_decision_changes_the_effective_authority_identity() -> None:
    """A resolved reference means something different, so it identifies differently."""
    accepted = _accepted()
    resolved = _resolve(accepted)

    assert oracle_identity(resolved.oracle) != oracle_identity(accepted.oracle)
    assert (
        identify_projection(candidate_from_accepted_inputs(resolved)).projection_uuid
        != identify_projection(candidate_from_accepted_inputs(accepted)).projection_uuid
    )


def test_who_authorized_it_and_when_do_not_remint_the_projection() -> None:
    """Incidental review evidence is audit metadata (#137 criterion 11)."""
    first = _resolve(_accepted())
    second = _resolve(
        _accepted(),
        authorized_by="Owner (recorded by a second reviewer)",
        reviewer="second-reviewer",
        resolved_at="2026-09-20T00:00:00Z",
        authorization_reference="Owner Decision 2026-09-19, restated in review",
    )

    assert (
        first.reference_resolution_acceptances
        != second.reference_resolution_acceptances
    )
    assert oracle_identity(first.oracle) == oracle_identity(second.oracle)
    assert (
        identify_projection(candidate_from_accepted_inputs(first)).projection_uuid
        == identify_projection(candidate_from_accepted_inputs(second)).projection_uuid
    )


def test_the_gate_and_the_build_derive_the_same_resolved_identity() -> None:
    """The two production chokepoints must move in lockstep.

    ``candidate_from_accepted_inputs`` is what persistence is built from and
    ``gate._accepted_identity`` is what the persisted result is judged against.
    A resolution applied to one and not the other would make every resolved
    build fail as a mismatched projection.
    """
    resolved = _resolve(_accepted())
    assert (
        _accepted_identity(resolved.oracle)
        == identify_projection(candidate_from_accepted_inputs(resolved)).projection_uuid
    )


def test_the_publication_gate_judges_the_resolved_view(session: Session) -> None:
    """Identity equality proves the derivations agree; this proves the gate acts.

    The decision that matters is publication, so the claim is made at the seam
    that decides it. A projection built from the resolved view passes against
    the resolved oracle; the *stored* view's projection — the same accepted
    artifact read without its decision — is refused rather than published as
    though the citation were still open.
    """
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
        if not expected:
            # The refusal is the identity one: the stored view derives a
            # different projection than the decision does.
            assert GateFailureCategory.IDENTITY_MISMATCH in result.categories()


# -- persistence, serialization, replay ---------------------------------------


def test_the_resolved_reference_is_what_reaches_persisted_state(
    session: Session,
) -> None:
    """The build persists the effective view, so downstream paths read one target."""
    resolved = _resolve(_accepted())
    identified = identify_projection(candidate_from_accepted_inputs(resolved))
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert [r.target_record_key for r in rebuilt.representation.references] == [
        DESTINATION
    ]
    assert relationship_and_reference_violations(rebuilt.representation) == []


def test_the_artifact_round_trips_through_its_committed_form(tmp_path: Path) -> None:
    resolved = _resolve(_accepted())
    path = tmp_path / "resolved.json"
    path.write_bytes(serialize_accepted_inputs(resolved))

    reloaded = load_accepted_inputs(path)
    assert (
        reloaded.oracle.reference_resolutions == resolved.oracle.reference_resolutions
    )
    assert (
        reloaded.reference_resolution_acceptances
        == resolved.reference_resolution_acceptances
    )
    assert oracle_identity(reloaded.oracle) == oracle_identity(resolved.oracle)
    assert serialize_accepted_inputs(reloaded) == path.read_bytes()


def test_an_artifact_stating_no_resolution_writes_no_resolution_keys() -> None:
    """Omit-when-empty, which is what keeps every accepted batch byte-identical."""
    payload = accepted_inputs_payload(_accepted())
    assert "reference_resolutions" not in payload
    assert "reference_resolution_records" not in payload["acceptance"]  # type: ignore[operator]


def test_the_committed_state_before_any_decision_loads_as_still_unresolved(
    tmp_path: Path,
) -> None:
    """The shape the four real citations will sit in, possibly for a long time.

    They arrive with the destinations batch and stay open until genuinely
    reviewed destinations exist. So the loader has to accept an artifact that
    states an unresolved citation and no decision about it, and the build has to
    go on reporting it: a capability that made an undecided citation loadable as
    anything else would close all four by omission.
    """
    path = tmp_path / "unresolved.json"
    path.write_bytes(serialize_accepted_inputs(_accepted()))

    reloaded = load_accepted_inputs(path)
    assert reloaded.oracle.reference_resolutions == ()
    assert reloaded.reference_resolution_acceptances == ()
    assert UNRESOLVED_FINDING in relationship_and_reference_violations(
        candidate_from_accepted_inputs(reloaded).representation
    )


def test_a_schema_succession_carries_the_decision_and_proves_stored_content() -> None:
    """A lift transforms nothing, and a resolution is not part of what it proves.

    ``verify_lift_path`` compares the **stored** representation across the step,
    and a resolution never touches that — so a schema-14-era artifact carrying
    one crosses on exactly the evidence it would have without it, and arrives
    still resolved. Proportional coverage: the registered successions themselves
    are the consolidated succession suite's subject, not this module's.
    """
    resolved = _resolve(
        _accepted(schema_version=SCHEMA_14_VERSION, schema_hash=SCHEMA_14_HASH)
    )
    lifted, records = lift_accepted_inputs(
        resolved, (SCHEMA_15_VERSION, SCHEMA_15_HASH)
    )

    assert [r.lift_id for r in records] == ["5d-lift-schema-14-to-15"]
    assert lifted.oracle.representation == resolved.oracle.representation
    assert lifted.oracle.reference_resolutions == resolved.oracle.reference_resolutions
    assert (
        lifted.reference_resolution_acceptances
        == resolved.reference_resolution_acceptances
    )
    # Still one effective destination on the far side of the succession.
    assert [
        r.target_record_key
        for r in effective_representation(
            lifted.oracle.representation, lifted.oracle.reference_resolutions
        ).references
    ] == [DESTINATION]


def test_an_unsupported_succession_refuses_and_carries_nothing() -> None:
    """A resolution does not make an unregistered transition reachable."""
    resolved = _resolve(_accepted())
    with pytest.raises(UnknownSchemaLiftError):
        lift_accepted_inputs(resolved, (SCHEMA_14_VERSION, SCHEMA_14_HASH))
    assert (resolved.oracle.schema_version, resolved.oracle.schema_hash) == (
        SCHEMA_15_VERSION,
        SCHEMA_15_HASH,
    )


def test_replaying_the_same_resolution_is_refused_and_changes_nothing() -> None:
    """Deterministic repeat: the same rule ``accept_proposal`` applies to a batch id."""
    resolved = _resolve(_accepted())
    with pytest.raises(AcceptanceError, match="already recorded"):
        _resolve(resolved)
    assert len(resolved.oracle.reference_resolutions) == 1
    assert len(resolved.reference_resolution_acceptances) == 1


# -- negative controls: every one fails closed, nothing partly recorded -------


@pytest.mark.parametrize(
    "missing",
    ["authorized_by", "authorization_reference", "reviewer", "resolved_at"],
)
def test_an_unattributed_resolution_is_refused(missing: str) -> None:
    """A machine suggestion must not become authority implicitly."""
    with pytest.raises(AcceptanceError, match="must name its"):
        _resolve(_accepted(), **{missing: "   "})


def test_a_second_decision_about_one_citation_is_refused() -> None:
    """Conflicting, not latest-wins: nothing here can choose between them."""
    resolved = _resolve(_accepted())
    with pytest.raises(AcceptanceError, match="conflicts with"):
        _resolve(
            resolved,
            _resolution(
                resolution_id="resolve-the-servant-2", target_record_key=SPELL_KEY
            ),
        )


def test_a_resolution_reviewed_against_another_release_is_refused() -> None:
    with pytest.raises(AcceptanceError, match="was reviewed against release"):
        _resolve(
            _accepted(),
            _resolution(release_version="5.2.1-corpus.other"),
        )


def test_a_resolution_whose_provenance_is_not_what_review_read_is_refused() -> None:
    """Source-bound exactness: the decision was about a citation read from a span."""
    with pytest.raises(AcceptanceError, match="was reviewed against provenance spans"):
        _resolve(
            _accepted(),
            _resolution(provenance_span_ids=(derive_span_id("leaf-elsewhere", 0, 10),)),
        )


def test_a_resolution_that_states_no_id_of_its_own_is_refused() -> None:
    """The id is what an authorization names, so an unnamed decision is nothing."""
    with pytest.raises(AcceptanceError, match="must state its own id"):
        _resolve(_accepted(), _resolution(resolution_id="   "))


def test_a_resolution_the_artifact_already_states_as_a_sibling_is_refused() -> None:
    """The post-hoc form of the edge this exists for, and it is still refused.

    A *first* acceptance can author both the empty citation and the same
    citation resolved: the retarget guard runs only against a ``prior``, so
    what refuses the pair is publication, which reports it as ambiguous. A
    later batch cannot author it. Resolving the empty edge inside such an
    artifact would publish one citation twice rather than close anything, so
    the resolution is refused and the pre-existing ambiguity is left visible
    for whoever has to explain it.
    """
    prior = _accepted(
        representation=_representation(
            replace(UNRESOLVED, target_record_key=DESTINATION)
        )
    )
    with pytest.raises(AcceptanceError, match="publish one citation twice"):
        _resolve(prior)


def test_a_resolution_naming_no_accepted_citation_is_refused() -> None:
    with pytest.raises(AcceptanceError, match="states no unresolved citation"):
        _resolve(
            _accepted(),
            _resolution(source_text="a phrase the source never prints"),
        )


def test_a_resolution_with_no_destination_is_refused() -> None:
    """The state being resolved, recorded as though it were the decision."""
    with pytest.raises(AcceptanceError, match="names no destination record"):
        _resolve(_accepted(), _resolution(target_record_key=""))


def test_retargeting_an_already_resolved_citation_is_refused() -> None:
    """The one boundary the Owner Decision draws inside this capability."""
    resolved = _resolve(_accepted())
    reresolve = replace(
        resolved,
        oracle=replace(
            resolved.oracle,
            representation=effective_representation(
                resolved.oracle.representation,
                resolved.oracle.reference_resolutions,
            ),
            reference_resolutions=(),
        ),
        reference_resolution_acceptances=(),
    )
    with pytest.raises(AcceptanceError, match="retargeting a resolved citation"):
        _resolve(reresolve, _resolution(target_record_key=SPELL_KEY))


def test_a_destination_the_representation_does_not_state_is_refused() -> None:
    """Bound directly: a decision pointing at no record is invalid as a decision.

    Not inferred from the resolved view. The validator words this finding by
    ``scope:source_text`` alone, so every sibling citation of the same phrase
    produces the same string and a pre-existing one would cover for this — see
    ``test_an_invalid_destination_is_refused_behind_a_sibling_stating_it``.
    """
    with pytest.raises(AcceptanceError, match="states no record for"):
        _resolve(_accepted(), _resolution(target_record_key="glossary.invented"))


def test_an_invalid_destination_is_refused_behind_a_sibling_already_stating_it(
    tmp_path: Path,
) -> None:
    """A pre-existing finding must not cover for a newly invalid destination.

    Codex's probe. A sibling component cites the same wording and names the same
    missing record, so the accepted view already reports ``unknown target record
    glossary.invented`` — and the validator words that finding by
    ``scope:source_text`` alone, so the resolved view's *second* occurrence of it
    is byte-identical to the first. Subtracting sets absorbed it: the resolution
    was admitted, the artifact serialized and loaded, and the effective view
    reported an unknown destination twice with nothing accounting for it.
    """
    sibling = ReferenceDraft(
        from_record_key=SPELL_KEY,
        from_component_key=OPEN_ENDED_KEY,
        source_text="the servant",
        scope_key="spell:wish",
        target_record_key="glossary.invented",
    )
    accepted = _accepted(representation=_representation(sibling))
    # The accepted view already states it, once, in the words the resolved view
    # would state it in again.
    assert (
        "reference spell:wish:'the servant': unknown target record glossary.invented"
        in relationship_and_reference_violations(accepted.oracle.representation)
    )
    before = serialize_accepted_inputs(accepted)

    with pytest.raises(AcceptanceError, match="states no record for"):
        _resolve(accepted, _resolution(target_record_key="glossary.invented"))

    assert accepted.oracle.reference_resolutions == ()
    assert accepted.reference_resolution_acceptances == ()
    assert serialize_accepted_inputs(accepted) == before


def test_a_destination_that_would_make_the_citation_ambiguous_is_refused() -> None:
    """One citation, one destination — the finding publication already refuses."""
    sibling = ReferenceDraft(
        from_record_key=SPELL_KEY,
        from_component_key=OPEN_ENDED_KEY,
        source_text="the servant",
        scope_key="spell:wish",
        target_record_key=SPELL_KEY,
    )
    accepted = _accepted(representation=_representation(sibling))
    with pytest.raises(AcceptanceError, match="ambiguous"):
        _resolve(accepted)


# -- the loader holds the same line over committed bytes ---------------------


def _written(inputs: AcceptedInputs, tmp_path: Path, **mutate: object) -> Path:
    payload = json.loads(serialize_accepted_inputs(inputs).decode("utf-8"))
    for key, value in mutate.items():
        if key == "acceptance_records":
            payload["acceptance"]["reference_resolution_records"] = value
        else:
            payload[key] = value
    path = tmp_path / "mutated.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_a_resolution_nobody_authorized_is_not_loadable(tmp_path: Path) -> None:
    """Added after the fact, it would inherit the authorization beside it."""
    resolved = _resolve(_accepted())
    path = _written(resolved, tmp_path, acceptance_records=[])
    with pytest.raises(OracleLoadError, match="no acceptance action records authoriz"):
        load_accepted_inputs(path)


def test_an_authorization_for_a_resolution_nobody_stated_is_not_loadable(
    tmp_path: Path,
) -> None:
    resolved = _resolve(_accepted())
    payload = json.loads(serialize_accepted_inputs(resolved).decode("utf-8"))
    del payload["reference_resolutions"]
    path = tmp_path / "stranded.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OracleLoadError, match="does not state"):
        load_accepted_inputs(path)


def test_two_authorizations_of_one_decision_are_not_loadable(tmp_path: Path) -> None:
    resolved = _resolve(_accepted())
    payload = json.loads(serialize_accepted_inputs(resolved).decode("utf-8"))
    records = payload["acceptance"]["reference_resolution_records"]
    path = _written(resolved, tmp_path, acceptance_records=records + records)
    with pytest.raises(OracleLoadError, match="authorized more than once"):
        load_accepted_inputs(path)


def test_an_unattributed_authorization_is_not_loadable(tmp_path: Path) -> None:
    resolved = _resolve(_accepted())
    payload = json.loads(serialize_accepted_inputs(resolved).decode("utf-8"))
    records = payload["acceptance"]["reference_resolution_records"]
    records[0]["authorization_reference"] = "  "
    path = _written(resolved, tmp_path, acceptance_records=records)
    with pytest.raises(OracleLoadError, match="states no"):
        load_accepted_inputs(path)


def test_a_tampered_resolution_is_not_loadable(tmp_path: Path) -> None:
    """Committed bytes are not self-proving: the seam's rules apply to the file."""
    resolved = _resolve(_accepted())
    payload = json.loads(serialize_accepted_inputs(resolved).decode("utf-8"))
    payload["reference_resolutions"][0]["target_record_key"] = "glossary.invented"
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OracleLoadError, match="do not apply to this accepted"):
        load_accepted_inputs(path)


def test_one_decision_stated_twice_is_not_loadable(tmp_path: Path) -> None:
    """Two statements of one decision, which the seam could never have appended."""
    resolved = _resolve(_accepted())
    stated = json.loads(serialize_accepted_inputs(resolved).decode("utf-8"))[
        "reference_resolutions"
    ]
    path = _written(resolved, tmp_path, reference_resolutions=stated * 2)
    with pytest.raises(OracleLoadError, match="stated more than once"):
        load_accepted_inputs(path)


def test_an_unknown_key_in_a_resolution_is_refused(tmp_path: Path) -> None:
    resolved = _resolve(_accepted())
    payload = json.loads(serialize_accepted_inputs(resolved).decode("utf-8"))
    payload["reference_resolutions"][0]["approved_by"] = "someone"
    path = tmp_path / "widened.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OracleLoadError, match="unexpected"):
        load_accepted_inputs(path)


# -- the boundary a later batch may not cross --------------------------------


def _second_batch(prior: AcceptedInputs, reference: ReferenceDraft) -> AcceptedInputs:
    """One further batch over a disjoint span, stating one more reference."""
    leaf = "leaf-second-batch"
    span_id = derive_span_id(leaf, 0, 24)
    span = SemanticSpan(
        span_id=span_id,
        leaf_id=leaf,
        char_start=0,
        char_end=24,
        disposition=SemanticDisposition.SUBSTANTIVE,
        review_state=ReviewState.PROPOSED,
    )
    base = _representation()
    representation = build_representation(
        references=base.references + (reference,),
        provenance=base.provenance + (reference_claim(reference, span_id),),
    )
    proposal = _proposal(
        representation=representation,
        proposed_spans=(ProposedSpan(span, "tool:classifier@0", "stated basis"),),
    )
    return accept_proposal(
        proposal,
        batch_id="batch-2",
        rule="the second batch's own span",
        resolved_scope=(span_id,),
        reviewer="owner",
        accepted_at="2026-09-19T18:00:00Z",
        prior=prior,
    )


def test_a_later_batch_cannot_author_a_destination_for_an_unresolved_citation() -> None:
    """The edge Codex found, now a refusal that names the supported path.

    The keyed union would retain both — the accepted empty edge and the new one —
    and publication would report the citation unresolved *and* ambiguous.
    """
    resolved_sibling = replace(UNRESOLVED, target_record_key=DESTINATION)
    with pytest.raises(AcceptanceError, match="Resolve it through resolve_references"):
        _second_batch(_accepted(), resolved_sibling)


def test_a_later_batch_cannot_retarget_an_accepted_reference() -> None:
    resolved = _resolve(_accepted())
    effective = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )
    published = replace(
        resolved,
        oracle=replace(
            resolved.oracle, representation=effective, reference_resolutions=()
        ),
        reference_resolution_acceptances=(),
    )
    with pytest.raises(
        AcceptanceError, match="would retarget a citation already accepted"
    ):
        _second_batch(published, replace(UNRESOLVED, target_record_key=SPELL_KEY))


def test_a_later_batch_that_invalidates_a_carried_decision_is_refused() -> None:
    """The carried decision is re-checked against the merged result, not assumed.

    A sibling *component* of the same record citing the same wording in the same
    scope is not a retarget — different citation, different key — so the
    retargeting guard rightly says nothing. But it makes the accepted decision
    describe an authority whose effective view is now ambiguous, and an artifact
    is not written to find that out later.
    """
    resolved = _resolve(_accepted())
    sibling = ReferenceDraft(
        from_record_key=SPELL_KEY,
        from_component_key=OPEN_ENDED_KEY,
        source_text="the servant",
        scope_key="spell:wish",
        target_record_key=SPELL_KEY,
    )
    with pytest.raises(AcceptanceError, match="no longer describe"):
        _second_batch(resolved, sibling)


def test_a_later_batch_carries_the_decision_forward() -> None:
    """A resolution is accepted authority: an extension may not drop it."""
    resolved = _resolve(_accepted())
    unrelated = ReferenceDraft(
        from_record_key=CREATURE_KEY,
        from_component_key=RECORD_OWNED_REFERENCE,
        source_text="the spell that summoned it",
        scope_key="creature:servant",
        target_record_key=SPELL_KEY,
    )
    extended = _second_batch(resolved, unrelated)

    assert (
        extended.oracle.reference_resolutions == resolved.oracle.reference_resolutions
    )
    assert (
        extended.reference_resolution_acceptances
        == resolved.reference_resolution_acceptances
    )
    effective = effective_representation(
        extended.oracle.representation, extended.oracle.reference_resolutions
    )
    assert relationship_and_reference_violations(effective) == []
    assert UNRESOLVED in extended.oracle.representation.references


def test_a_batch_accepted_over_an_unresolved_citation_keeps_it_open() -> None:
    """Extending accepted authority is not resolving anything in it."""
    unrelated = ReferenceDraft(
        from_record_key=CREATURE_KEY,
        from_component_key=RECORD_OWNED_REFERENCE,
        source_text="the spell that summoned it",
        scope_key="creature:servant",
        target_record_key=SPELL_KEY,
    )
    extended = _second_batch(_accepted(), unrelated)
    assert extended.oracle.reference_resolutions == ()
    assert UNRESOLVED_FINDING in relationship_and_reference_violations(
        extended.oracle.representation
    )


# -- the seven accepted batches ----------------------------------------------


PRODUCTION_ORACLE = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "afterworlds"
    / "ingestion"
    / "mechanical"
    / "oracles"
    / "srd-5-2-1-corpus-36b786d8-fa2.json"
)

#: The accepted oracle identity of the nine accepted batches, unchanged by this
#: capability. Pinned here because "the artifact still round-trips" and "the
#: artifact still *identifies* the same" are two claims.
ACCEPTED_ORACLE_IDENTITY = "3b8941ce9039a78e72fd3ddf05952d0da4bed18dc4d38fb99b8b80db137fb407"  # noqa: E501  # pragma: allowlist secret


def test_the_accepted_corpus_is_untouched_by_this_capability() -> None:
    """No schema succession, no new keys, no moved identity, no changed bytes.

    ``reference_resolutions`` lives on the oracle rather than inside
    ``RepresentationDraft``, so ``schema_binding_violations`` never sees it and
    schema 15 stands; omit-when-empty does the rest.
    """
    inputs = load_accepted_inputs(PRODUCTION_ORACLE)
    assert inputs.oracle.reference_resolutions == ()
    assert inputs.reference_resolution_acceptances == ()
    assert oracle_identity(inputs.oracle) == ACCEPTED_ORACLE_IDENTITY
    assert serialize_accepted_inputs(inputs) == PRODUCTION_ORACLE.read_bytes()


# -- one decision, several citations of one wording ---------------------------


def test_two_components_citing_one_wording_are_resolved_in_one_action() -> None:
    """The end state the single-action seam offered no path to.

    Both citations are legitimate and both are empty, but their destination is
    shared: resolving either alone would state ``['', destination]`` for one
    wording, which publication refuses as ambiguous and which this capability
    must go on refusing. One action, two decisions, each keeping its own
    citation and its own reviewed spans.
    """
    accepted = _accepted(representation=_representation(SIBLING_UNRESOLVED))
    resolved = _resolve(accepted, _resolution(), _sibling_resolution())
    effective = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )

    assert {
        r.from_component_key: r.target_record_key for r in effective.references
    } == {
        DESCRIPTOR_KEY: DESTINATION,
        OPEN_ENDED_KEY: DESTINATION,
    }
    assert relationship_and_reference_violations(effective) == []
    # Per-citation source and provenance, one shared authorization.
    assert [
        (r.from_component_key, r.source_text, r.provenance_span_ids)
        for r in resolved.oracle.reference_resolutions
    ] == [
        (DESCRIPTOR_KEY, "the servant", (SPELL_SPAN,)),
        (OPEN_ENDED_KEY, "the servant", (SPELL_SPAN,)),
    ]
    assert {
        (a.resolution_id, a.authorized_by, a.reviewer, a.resolved_at)
        for a in resolved.reference_resolution_acceptances
    } == {
        ("resolve-the-servant-1", "Owner", "Codex", "2026-09-19T12:00:00Z"),
        ("resolve-the-servant-open-ended-1", "Owner", "Codex", "2026-09-19T12:00:00Z"),
    }
    # And the accepted history still states what the reviewers accepted.
    assert resolved.oracle.representation == accepted.oracle.representation


def test_resolving_one_of_two_consistent_citations_alone_is_still_refused() -> None:
    """The intermediate state is ambiguous, and stays refused.

    This is not a gap the joint action papers over: it is why the joint action
    exists. A half-applied decision about one wording is exactly the artifact
    publication must not be able to hold.
    """
    accepted = _accepted(representation=_representation(SIBLING_UNRESOLVED))
    with pytest.raises(AcceptanceError, match="ambiguous"):
        _resolve(accepted)


def test_two_citations_of_one_wording_sent_to_different_records_are_refused() -> None:
    """True ambiguity is refused whether stated in one action or two."""
    accepted = _accepted(representation=_representation(SIBLING_UNRESOLVED))
    with pytest.raises(AcceptanceError, match="ambiguous"):
        _resolve(
            accepted,
            _resolution(),
            _sibling_resolution(target_record_key=SPELL_KEY),
        )


def test_a_record_and_component_citing_one_wording_cannot_be_resolved_together() -> (
    None
):
    """A joint action may not launder a pair publication already refuses.

    Overlap by *owner* rather than by component: the record states the citation
    directly and a component states it too. That pair is one citation published
    twice whatever its destination, so resolving both together does not repair
    it — and because the finding names the target, the resolved wording is a
    finding the accepted view does not state and the action is refused.
    """
    accepted = _accepted(representation=_representation(RECORD_OWNED_SIBLING))
    assert any(
        "states it both directly" in finding
        for finding in relationship_and_reference_violations(
            accepted.oracle.representation
        )
    )
    with pytest.raises(AcceptanceError, match="states it both directly"):
        _resolve(accepted, _resolution(), _record_owned_resolution())


def test_one_wording_cited_in_two_scopes_resolves_to_two_records() -> None:
    """Scope survives resolution: different scopes are different decisions.

    Overlap by *wording alone*. ``(scope, source_text)`` is what has one
    destination, so two scopes citing the same phrase may be sent to different
    records — in one action, since a reviewer deciding both at once is ordinary.
    """
    accepted = _accepted(representation=_representation(OTHER_SCOPE_UNRESOLVED))
    resolved = _resolve(
        accepted,
        _resolution(),
        _other_scope_resolution(target_record_key=SPELL_KEY),
    )

    effective = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )
    assert relationship_and_reference_violations(effective) == []
    assert {
        (ref.scope_key, ref.target_record_key)
        for ref in effective.references
        if ref.source_text == "the servant"
    } == {("spell:wish", DESTINATION), ("spell:simulacrum", SPELL_KEY)}


def test_a_joint_action_with_one_invalid_decision_records_no_part_of_it() -> None:
    """Whole or not at all: the valid half is not quietly kept."""
    accepted = _accepted(representation=_representation(SIBLING_UNRESOLVED))
    before = serialize_accepted_inputs(accepted)
    with pytest.raises(AcceptanceError, match="states no record for"):
        _resolve(
            accepted,
            _resolution(),
            _sibling_resolution(target_record_key="glossary.invented"),
        )
    assert accepted.oracle.reference_resolutions == ()
    assert accepted.reference_resolution_acceptances == ()
    assert serialize_accepted_inputs(accepted) == before


def test_an_action_that_resolves_nothing_is_refused() -> None:
    """An action that decides nothing is not a decision."""
    with pytest.raises(AcceptanceError, match="at least one resolution"):
        resolve_references(
            _accepted(),
            resolutions=(),
            authorized_by="Owner",
            authorization_reference="Owner Decision 2026-09-19 (ADR-005d Decision 7)",
            reviewer="Codex",
            resolved_at="2026-09-19T12:00:00Z",
        )


def test_one_citation_stated_twice_in_one_action_is_refused() -> None:
    """Two decisions about one citation, in one breath, is still a conflict."""
    accepted = _accepted(representation=_representation(SIBLING_UNRESOLVED))
    with pytest.raises(AcceptanceError, match="conflicts with"):
        _resolve(
            accepted,
            _resolution(),
            _resolution(resolution_id="resolve-the-servant-again-1"),
        )


def test_replaying_a_joint_action_is_refused_and_changes_nothing() -> None:
    accepted = _accepted(representation=_representation(SIBLING_UNRESOLVED))
    resolved = _resolve(accepted, _resolution(), _sibling_resolution())
    with pytest.raises(AcceptanceError, match="already recorded"):
        _resolve(resolved, _resolution(), _sibling_resolution())
    assert len(resolved.oracle.reference_resolutions) == 2
    assert len(resolved.reference_resolution_acceptances) == 2


def test_an_action_repeating_one_recorded_decision_is_refused_whole() -> None:
    """A partial replay records no part of itself, including the genuinely new half."""
    accepted = _accepted(representation=_representation(OTHER_UNRESOLVED))
    first = _resolve(accepted)
    with pytest.raises(AcceptanceError, match="already recorded"):
        _resolve(first, _resolution(), _other_resolution())
    assert [r.resolution_id for r in first.oracle.reference_resolutions] == [
        "resolve-the-servant-1"
    ]
    assert len(first.reference_resolution_acceptances) == 1


def test_one_action_and_two_actions_reach_the_same_accepted_authority() -> None:
    """Whether a decision was recorded jointly is evidence, not part of the result.

    Two independent citations can be resolved either way, so the two paths are
    comparable — and they must not identify differently, or the shape of the
    review session would leak into the oracle's identity.
    """
    accepted = _accepted(representation=_representation(OTHER_UNRESOLVED))
    joint = _resolve(accepted, _resolution(), _other_resolution())
    stepwise = _resolve(_resolve(accepted), _other_resolution())

    assert oracle_identity(joint.oracle) == oracle_identity(stepwise.oracle)
    assert serialize_accepted_inputs(joint) == serialize_accepted_inputs(stepwise)


def test_a_jointly_resolved_artifact_reconstructs_from_its_committed_bytes(
    tmp_path: Path,
) -> None:
    accepted = _accepted(representation=_representation(SIBLING_UNRESOLVED))
    resolved = _resolve(accepted, _resolution(), _sibling_resolution())
    path = tmp_path / "jointly-resolved.json"
    path.write_bytes(serialize_accepted_inputs(resolved))

    reloaded = load_accepted_inputs(path)
    assert (
        reloaded.oracle.reference_resolutions == resolved.oracle.reference_resolutions
    )
    assert (
        reloaded.reference_resolution_acceptances
        == resolved.reference_resolution_acceptances
    )
    assert oracle_identity(reloaded.oracle) == oracle_identity(resolved.oracle)
    assert serialize_accepted_inputs(reloaded) == path.read_bytes()
    # And the effective consumer sees one destination for both citations.
    candidate = candidate_from_accepted_inputs(reloaded)
    assert {r.target_record_key for r in candidate.representation.references} == {
        DESTINATION
    }
    assert relationship_and_reference_violations(candidate.representation) == []


def test_half_a_joint_decision_is_not_loadable(tmp_path: Path) -> None:
    """Committed bytes stating one of the two decisions leave the pair ambiguous."""
    accepted = _accepted(representation=_representation(SIBLING_UNRESOLVED))
    resolved = _resolve(accepted, _resolution(), _sibling_resolution())
    payload = json.loads(serialize_accepted_inputs(resolved).decode("utf-8"))
    payload["reference_resolutions"] = [
        r
        for r in payload["reference_resolutions"]
        if r["resolution_id"] == "resolve-the-servant-1"
    ]
    payload["acceptance"]["reference_resolution_records"] = [
        r
        for r in payload["acceptance"]["reference_resolution_records"]
        if r["resolution_id"] == "resolve-the-servant-1"
    ]
    path = tmp_path / "half.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(OracleLoadError, match="do not apply to this accepted"):
        load_accepted_inputs(path)


def test_a_later_batch_carries_a_joint_decision_forward() -> None:
    accepted = _accepted(representation=_representation(SIBLING_UNRESOLVED))
    resolved = _resolve(accepted, _resolution(), _sibling_resolution())
    unrelated = ReferenceDraft(
        from_record_key=CREATURE_KEY,
        from_component_key=RECORD_OWNED_REFERENCE,
        source_text="the spell that summoned it",
        scope_key="creature:servant",
        target_record_key=SPELL_KEY,
    )
    extended = _second_batch(resolved, unrelated)

    assert (
        extended.oracle.reference_resolutions == resolved.oracle.reference_resolutions
    )
    assert (
        extended.reference_resolution_acceptances
        == resolved.reference_resolution_acceptances
    )
    assert {
        r.target_record_key
        for r in effective_representation(
            extended.oracle.representation, extended.oracle.reference_resolutions
        ).references
    } == {DESTINATION, SPELL_KEY}
