"""The explicit acceptance action — CRD Issue 5d, contract 2.

One function, because acceptance is one thing: a named reviewer, at a named
time, accepting an exact scope of proposed claims, with the full semantic diff
of what that changed retained as evidence.

    machine proposal  →  human semantic review  →  explicit acceptance

:mod:`proposal` owns the first arrow's output. This module owns the third, and
what it produces — an :class:`~.oracle.AcceptedInputs` — is the committed
artifact a reviewer commits and the build consumes.

Three properties this is built to keep:

* **Silence is not acceptance.** Only span ids named in ``resolved_scope`` are
  accepted. A proposed span the reviewer did not name is dropped, not carried
  forward as "probably fine". The resulting artifact then fails the publication
  gate's population check until every represented leaf is covered, which is the
  honest state rather than an optimistic one.
* **The evidence is the diff, not a digest of it.** The batch retains every
  :class:`~.models.SemanticDiffEntry` in full, and its hash identifies that diff
  rather than substituting for it (see :mod:`accounting`).
* **Evidence never becomes identity.** Reviewer, timestamp, batch grouping,
  rule wording, and the reviewed proposal's identity travel with the ledger and
  are excluded from :func:`~.oracle.oracle_payload`, so re-reviewing an
  unchanged classification cannot remint a projection.
* **The evidence names the representation, not only the spans.** A batch's
  scope and diff say which spans were accepted and what their disposition
  became; they say nothing about records, facts, or prose bindings. Two
  proposals can agree on every span and disagree on all the mechanical
  authority. So each batch also records
  :func:`~.proposal.proposal_identity` — the content-derived identity of the
  exact complete proposal reviewed. ``resolved_scope`` scopes *classification*
  acceptance; ``proposal_identity`` identifies the complete proposed
  *representation* that acceptance drew from.

Accepting over a prior artifact extends it. Batch scopes accumulate and must
stay **disjoint**: a span already accepted cannot be re-accepted here, because
re-acceptance would strand the earlier batch's evidence — its scope member would
name a different batch than the one that recorded it, and the ledger would fail
its own acceptance validation. **Correcting** an earlier acceptance therefore
needs a history model with supersession semantics, which this module deliberately
does not have: no accepted span's disposition, prose, fact or reason code can be
edited here, and nothing supersedes an accepted claim. What it does support is
the workflow full-corpus review actually needs: one complete proposal reviewed
across several disjoint span batches, whose representations merge as a keyed
union rather than piling up duplicates.

One bounded second action exists beside that one, and it is not a correction.
:func:`resolve_references` records explicitly authorized destinations for
accepted references that were accepted with **none** — the Owner Decision of
2026-09-19 under ADR-005d Decision 7, implemented in
:mod:`reference_resolution`. It is an append like every other acceptance: the
unresolved citation and its acceptance evidence stay exactly as reviewed, the
decision and its authorization are added beside them, and the resolved view is
*derived* rather than written back. It is not general supersession and confers
none: it cannot retarget a citation that already resolves, cannot touch prose or
facts, and cannot guess a destination. The reason it has to exist at all is the
keyed union above — a reference's key includes its target, so a later batch that
authors the destination produces a *different* key and the accepted empty edge
survives beside it, reported both unresolved and ambiguous.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import replace
from typing import Any

from afterworlds.ingestion.mechanical.accounting import batch_diff_hash
from afterworlds.ingestion.mechanical.models import (
    AcceptanceBatch,
    AcceptanceRecord,
    ReferenceResolution,
    ReferenceResolutionAcceptance,
    ReviewState,
    ReviewUnitAcceptance,
    SemanticDiffEntry,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    AcceptedOracle,
    derive_obligations,
)
from afterworlds.ingestion.mechanical.policy import (
    PolicyTransitionRecord,
    UnknownPolicyTransitionError,
    accepted_policy_contracts,
    policy_meaning_violations,
    policy_transition_for,
)
from afterworlds.ingestion.mechanical.projection import (
    LegacySchemaPayloadError,
    review_unit_violations,
)
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_shape_violations,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceClaim,
    RepresentationDraft,
    component_target_key,
    held_structure_violations,
    prose_binding_target_key,
    record_target_key,
    reference_target_key,
    relationship_target_key,
    representation_draft_violations,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    BatchSchemaAnchor,
    SchemaLiftError,
    SchemaLiftRecord,
    carried_anchors,
    lift_path,
    schema_binding_violations,
    verify_lift_path,
)

__all__ = ["AcceptanceError", "accept_proposal", "resolve_references"]


class AcceptanceError(ValueError):
    """Raised when an acceptance action cannot be recorded as stated.

    Raised rather than reported: a half-recorded acceptance is worse than none,
    because the artifact would claim review that did not happen.
    """


def _provenance_key(claim: ProvenanceClaim) -> tuple[str, ...]:
    """Stable identity of one provenance edge.

    The same tuple :mod:`validation` uses to detect a duplicate edge, so "the
    same edge" means one thing in this repository rather than two.
    """
    return (claim.target_kind.value, *claim.target_key, claim.span_id, claim.role.value)


#: How each representation collection is keyed for the merge below, reusing the
#: repository's canonical target-key definitions rather than restating them.
#:
#: Three of these keys are strictly narrower than their element's content, so
#: the same key can carry conflicting content and the merge has to say so:
#: a record's kind and parent, a component's handling, reason, and facts, and a
#: prose binding's chunk extent all live outside their keys. The other three —
#: relationships, references, provenance — have keys that already span every
#: field, so under those a key collision *is* content equality and only
#: duplication is possible. Both cases are handled by the same code; the
#: difference is only which failure it can reach.
_COLLECTIONS: tuple[tuple[str, str, Callable[[Any], tuple[str, ...]]], ...] = (
    ("record", "records", record_target_key),
    ("component", "components", component_target_key),
    ("prose binding", "prose_bindings", prose_binding_target_key),
    ("relationship", "relationships", relationship_target_key),
    ("reference", "references", reference_target_key),
    ("provenance edge", "provenance", _provenance_key),
)


def _merged_collection(
    label: str,
    key_of: Callable[[Any], tuple[str, ...]],
    prior_items: tuple[Any, ...],
    new_items: tuple[Any, ...],
) -> tuple[Any, ...]:
    """Keyed union of one collection: retain once, append new, reject conflicts."""
    merged: list[Any] = []
    seen: dict[tuple[str, ...], Any] = {}
    for item in (*prior_items, *new_items):
        key = key_of(item)
        existing = seen.get(key)
        if existing is None:
            seen[key] = item
            merged.append(item)
            continue
        if existing != item:
            raise AcceptanceError(
                f"{label} {list(key)}: this acceptance states different content "
                "under a semantic key already accepted. Nothing here can choose "
                "between them — the earlier reviewer never saw this version."
            )
    return tuple(merged)


def _merge_representation(
    prior: RepresentationDraft | None, proposed: RepresentationDraft
) -> RepresentationDraft:
    """Combine a prior accepted representation with a newly accepted one.

    A **keyed union**, not concatenation. Reviewing one complete proposal across
    several disjoint span batches supplies the same complete representation each
    time; concatenating it would duplicate every record and component, and the
    finished artifact could never publish — :mod:`validation` would report
    duplicate semantic keys and persistence would collide on projection-scoped
    identities.

    So an element whose key was already accepted is retained once, a genuinely
    new element is appended in first-seen order, and an element that reuses an
    accepted key while stating *different* content fails closed. That last case
    is not a merge conflict to resolve: it is one reviewer's authority silently
    replacing another's, and the earlier reviewer never saw the replacement.

    First-seen order rather than sorted, because the accepted result is
    canonicalized downstream anyway (:func:`~.projection.representation_payload`
    orders every collection), so imposing a second ordering here would add a
    rule without adding a guarantee.
    """
    # Before the keyed union, because the union itself is what a hostile
    # subclass would subvert: ``_merged_collection`` builds ``key_of`` keys and
    # compares elements to decide what is "already accepted". A redefined
    # ``__eq__`` there silently drops an element or admits a conflicting one.
    #
    # ``prior`` is loader-built and therefore already exact (see
    # ``oracle.load_accepted_inputs``), but it is checked too rather than
    # trusted: this is the seam where a proposal becomes accepted authority,
    # and a rule with an exception is a rule someone will find the exception in.
    for label, candidate in (("proposed", proposed), ("prior", prior)):
        if candidate is None:
            continue
        if drift := representation_draft_violations(candidate):
            raise AcceptanceError(
                f"{label} representation is not the closed declared shape: "
                + "; ".join(drift)
            )
        # ...and the same rule below the top level. A subclassed nested value
        # object canonicalizes to its declared base's payload, so two proposals
        # asserting different authority would merge identically and share one
        # oracle identity. Every other authority-bearing path runs a validator
        # that refuses such a value first; this seam has neither a ledger nor a
        # bound corpus, so it cannot, and the leak is closed here instead.
        if drift := held_structure_violations(candidate):
            raise AcceptanceError(
                f"{label} representation holds a structure outside its closed "
                "declaration: " + "; ".join(drift)
            )

    if prior is None:
        return proposed

    return RepresentationDraft(
        **{
            field: _merged_collection(
                label, key_of, getattr(prior, field), getattr(proposed, field)
            )
            for label, field, key_of in _COLLECTIONS
        }
    )


def _repeated(ids: Iterable[str]) -> list[str]:
    """Ids stated more than once, sorted.

    Every selection collection here is keyed by id somewhere downstream, and a
    dictionary comprehension over a repeated id keeps the last definition and
    discards the earlier one without saying so.
    """
    return sorted(i for i, count in Counter(ids).items() if count > 1)


def accept_proposal(
    proposal: MechanicalProposal,
    *,
    batch_id: str,
    rule: str,
    resolved_scope: tuple[str, ...],
    reviewer: str,
    accepted_at: str,
    prior: AcceptedInputs | None = None,
    resolved_review_units: tuple[str, ...] = (),
) -> AcceptedInputs:
    """Record one explicit acceptance of *resolved_scope* from *proposal*.

    ``rule`` is how the reviewer selected the scope. It is retained as evidence
    and is **never re-run**: re-evaluating a selector against changed inputs
    would resolve to a different set than the reviewer actually saw, which is
    why ``resolved_scope`` carries the exact span ids alongside it.

    ``resolved_scope`` scopes *classification* acceptance — which spans, and
    what their disposition became. The batch separately records the identity of
    the complete proposal reviewed, which is what ties the accepted
    *representation* to something a human looked at.

    ``resolved_review_units`` names ``unit_id``s of units *this proposal
    proposed* — the coherent sections, entries and tables the reviewer read,
    which leaves each covers, and which rules each must contain. It is a scope
    over the proposal's inventory on exactly the terms ``resolved_scope`` is a
    scope over its spans: the units themselves are proposal content, inside the
    ``proposal_identity`` this batch records, so an altered inventory derives a
    different identity and cannot inherit this acceptance; and naming is what
    accepts, so a proposed unit this action does not name is not accepted.
    Accepted units accumulate across batches on the same terms as scopes — a
    ``unit_id`` a prior batch already recorded cannot be recorded again — and
    the accumulated inventory is checked against the *merged* representation,
    because a unit may legitimately expect a rule an earlier batch structured.

    An acceptance action must resolve *something*, but it need not be a span. A
    reviewer who read a coherent unit and recorded that it states no rule this
    build must carry has accounted for that source as deliberately as one who
    classified a span in it; requiring a span anyway would retain the obsolete
    demand to classify extra text as the price of a legitimate review.

    Extending *prior* requires a disjoint scope: a span it already accepted
    cannot be re-accepted here.

    A proposal whose own proposed spans or proposed units repeat an id is
    refused outright, before anything is resolved. Resolving such an id would
    select whichever definition a dictionary kept last while the retained
    ``proposal_identity`` names both.
    """
    if not resolved_scope and not resolved_review_units:
        raise AcceptanceError(
            "an acceptance action must name at least one span or one review unit"
        )
    if not reviewer.strip():
        raise AcceptanceError("an acceptance action must name its reviewer")
    if not rule.strip():
        raise AcceptanceError("an acceptance action must record its selection rule")

    # The proposal's own selection collections, before either becomes a
    # dictionary. A repeated id is not a hash collision — reversing the two
    # definitions derives a different ``proposal_identity`` — it is an invalid
    # identifier, and keying on it would accept one definition while the
    # identity this batch retains as evidence names both. The discarded
    # definition never reaches the accepted-candidate duplicate validator, so
    # the refusal has to happen here, before anything is keyed.
    #
    # Identical repeats are refused on the same terms: resolving the id still
    # names an entry no reader can point at, and a proposal stating one unit
    # twice has said nothing the second statement adds. This counts ids only,
    # so rejecting a duplicate identifier never depends on what the duplicate
    # definition contains or on whether this action accepts it.
    if repeats := _repeated(p.span.span_id for p in proposal.proposed_spans):
        raise AcceptanceError(f"this proposal proposes spans more than once: {repeats}")
    if repeats := _repeated(u.unit_id for u in proposal.proposed_review_units):
        raise AcceptanceError(
            f"this proposal proposes review units more than once: {repeats}"
        )

    proposed_by_id = {p.span.span_id: p.span for p in proposal.proposed_spans}
    if duplicates := _repeated(resolved_scope):
        raise AcceptanceError(f"resolved scope repeats spans {duplicates}")
    if unknown := sorted(set(resolved_scope) - proposed_by_id.keys()):
        raise AcceptanceError(
            f"resolved scope names spans this proposal did not propose: {unknown}"
        )

    # The same three refusals, over the proposal's inventory. Resolving a unit
    # the proposal does not state would record acceptance of an expectation set
    # outside the ``proposal_identity`` this batch retains — which is the whole
    # reason the inventory moved into the proposal.
    proposed_units_by_id = {u.unit_id: u for u in proposal.proposed_review_units}
    if repeats := _repeated(resolved_review_units):
        raise AcceptanceError(f"resolved review units repeat {repeats}")
    if unproposed := sorted(set(resolved_review_units) - proposed_units_by_id.keys()):
        raise AcceptanceError(
            "resolved review units name units this proposal did not propose: "
            f"{unproposed}"
        )
    accepted_units = tuple(proposed_units_by_id[u] for u in resolved_review_units)

    if prior is not None and prior.oracle.binding != proposal.binding:
        raise AcceptanceError(
            "this proposal binds a different 5c release than the prior accepted "
            "authority it would extend"
        )
    # Recognition first, on the proposal's own declaration. An invented hash,
    # or a known version paired with another version's hash, names no policy
    # this build can state the meaning of — so the reason codes it carries
    # cannot be checked against any closed catalog, and accepting it would mint
    # authority under a policy that does not exist. Same shape as the schema
    # recognition below, for the same reason.
    proposed_policy = (proposal.policy_version, proposal.policy_hash)
    if proposed_policy not in accepted_policy_contracts():
        raise AcceptanceError(
            f"this proposal declares semantic policy {proposal.policy_version!r} "
            f"({proposal.policy_hash}), which is not a contract this build "
            "accepts authority under"
        )

    # A policy difference is refused unless an authorized transition covers this
    # exact succession — the same table-not-comparison rule ``SCHEMA_LIFTS``
    # follows. Crossing is what makes the older policy's codes still readable,
    # and the crossing is recorded, so the artifact keeps saying which
    # successions actually happened rather than being silently reinterpreted.
    policy_steps: tuple[PolicyTransitionRecord, ...] = ()
    if prior is not None:
        prior_policy = (prior.oracle.policy_version, prior.oracle.policy_hash)
        if prior_policy != proposed_policy:
            try:
                crossing = policy_transition_for(prior_policy, proposed_policy)
            except UnknownPolicyTransitionError as exc:
                raise AcceptanceError(
                    "this proposal declares a different semantic policy than the "
                    "prior accepted authority it would extend, and no registered "
                    f"transition authorizes the difference: {exc}"
                ) from exc
            policy_steps = (
                PolicyTransitionRecord(
                    transition_id=crossing.transition_id,
                    from_version=crossing.from_version,
                    from_hash=crossing.from_hash,
                    to_version=crossing.to_version,
                    to_hash=crossing.to_hash,
                ),
            )

    # **The central invariant, and it runs before every branch below.** A
    # representation and the schema identity it declares are admissible together
    # only when its meaning is legal under that version *and* the exact
    # (version, hash) pair is a contract this build accepts authority under —
    # ``schema_binding_violations``, the same function the loader and
    # ``verify_lift`` call.
    #
    # Legality was previously checked only where the schema *changed* — inside
    # ``verify_lift``, on the *prior* — which left three acceptance paths open:
    # no prior at all, a prior declaring the same (version, hash) as the
    # proposal, and the proposed half of a lifted acceptance. On any of those a
    # proposal carrying a schema-4-only family was accepted with ``lifts == ()``,
    # producing accepted authority its own declaration cannot state and that a
    # later lift would then refuse. The recognition half closes the sibling case:
    # an invented hash, or a known version paired with another version's hash,
    # names no contract at all.
    #
    # Checked here rather than inside ``representation_payload``: that function's
    # contract is to emit the declared key set, and putting a full recursive walk
    # on it would run on every identity computation and both sides of every
    # verified lift. Acceptance is the seam authority is *created* at, so nothing
    # reaches canonicalization as accepted authority without passing this first.
    if illegal := schema_binding_violations(
        proposal.proposed_representation,
        (proposal.schema_version, proposal.schema_hash),
    ):
        raise AcceptanceError(
            f"this proposal declares representation schema "
            f"{proposal.schema_version!r} but is not admissible under it, so it "
            "was not built under the schema it names: " + "; ".join(illegal)
        )
    if prior is not None and (
        illegal := schema_binding_violations(
            prior.oracle.representation,
            (prior.oracle.schema_version, prior.oracle.schema_hash),
        )
    ):
        raise AcceptanceError(
            f"the prior accepted authority declares representation schema "
            f"{prior.oracle.schema_version!r} but is not admissible under it, so "
            "it was not accepted under the schema it names: " + "; ".join(illegal)
        )

    # The same question of the *policy* the proposal declares, and a separate
    # one. Schema 12 mints the ``prose_retention_reason_code`` key;
    # ``5d-semantic-policy-2`` mints the catalog its values come from, and the
    # two are versioned independently. A schema-12 proposal declaring
    # ``5d-semantic-policy-1`` is legal and may simply state no retention
    # reason — so the schema check above passes it, and only this one sees a
    # reason code drawn from a catalog the declared policy does not have.
    if unstatable := policy_meaning_violations(
        proposal.proposed_representation, proposal.policy_version
    ):
        raise AcceptanceError(
            f"this proposal declares semantic policy {proposal.policy_version!r} "
            "but carries meaning that policy cannot state: " + "; ".join(unstatable)
        )

    # The prior's *evidence* is validated here, before anything is computed
    # from it: before the lift is looked up, before the representations are
    # merged, and before any anchor is carried or synthesized. An artifact whose
    # own succession evidence does not hold is not a base to extend, and reading
    # its declaration to fill in what its evidence never said is how a restamped
    # in-memory prior turned a schema-3 review into schema-4 anchors that then
    # loaded clean (#137 round 8).
    prior_anchors = _carried_anchors(prior)

    # A schema difference is refused unless an authorized lift covers this exact
    # transition. The check is widened, never removed: identical schemas remain
    # directly acceptable, and everything else must be registered for its exact
    # (version, hash) source and destination pair. An unknown, reversed, skipped,
    # or hash-mismatched transition raises, and "a later version" is never
    # evidence — SCHEMA_LIFTS is a table, not a comparison.
    lift_records: tuple[SchemaLiftRecord, ...] = ()
    if prior is not None and (
        prior.oracle.schema_version,
        prior.oracle.schema_hash,
    ) != (proposal.schema_version, proposal.schema_hash):
        try:
            # Every authorized step, oldest first. A prior reviewed under an
            # older schema may have to cross more than one succession to reach
            # the schema this proposal declares — the committed conditions-1
            # artifact crosses 3 to 4 to 5 — and each crossing is recorded, so
            # the artifact keeps saying which successions actually happened.
            steps = lift_path(
                (prior.oracle.schema_version, prior.oracle.schema_hash),
                (proposal.schema_version, proposal.schema_hash),
            )
            # Proves element by element that the prior accepted content is
            # byte-identical under every schema on the way *before* anything is
            # re-declared. A lift may authorize a wider contract; it may never
            # move a semantic identity the Owner already accepted.
            lift_records = verify_lift_path(steps, prior.oracle.representation)
        # ``LegacySchemaPayloadError`` joins it: a prior whose declared schema
        # cannot serialize its own content is uncanonicalizable, which is the
        # same acceptance failure by a different route. Letting it escape this
        # seam uncategorized would fail closed in the right direction but say
        # the wrong thing about why.
        except (SchemaLiftError, LegacySchemaPayloadError) as exc:
            raise AcceptanceError(
                "this proposal declares a different representation schema than "
                "the prior accepted authority it would extend, and no verified "
                f"lift authorizes the difference: {exc}"
            ) from exc

    if batch_id in {b.batch_id for b in (prior.batches if prior else ())}:
        raise AcceptanceError(f"batch {batch_id!r} is already recorded")

    # Accumulating batch scopes stay disjoint. Re-accepting a span would leave
    # the earlier batch's retained evidence stranded — its scope member would
    # name a different batch than the record that accepted it — and the ledger
    # would fail its own acceptance validation from then on. Refused here,
    # before an artifact exists, rather than producing one that cannot load.
    if prior is not None:
        already = {a.span_id for a in prior.acceptances}
        if overlap := sorted(already.intersection(resolved_scope)):
            raise AcceptanceError(
                f"resolved scope re-accepts spans already accepted: {overlap}. "
                "Batch scopes must be disjoint; correcting an earlier acceptance "
                "needs supersession semantics this module does not have."
            )

    accepted_spans = tuple(
        replace(proposed_by_id[span_id], review_state=ReviewState.ACCEPTED)
        for span_id in resolved_scope
    )
    # Every span in a disjoint scope is newly accepted, so there is no prior
    # disposition to record. The fields stay because the diff shape is shared
    # with a future history model that will have one.
    diff = tuple(
        SemanticDiffEntry(
            span_id=span.span_id,
            prior_disposition=None,
            prior_reason_code=None,
            accepted_disposition=span.disposition,
            accepted_reason_code=span.non_mechanical_reason_code,
        )
        for span in accepted_spans
    )
    batch = AcceptanceBatch(
        batch_id=batch_id,
        rule=rule,
        resolved_scope=tuple(resolved_scope),
        diff=diff,
        semantic_diff_hash="",
        proposal_identity=proposal_identity(proposal),
    )
    batch = replace(batch, semantic_diff_hash=batch_diff_hash(batch))

    spans = tuple(prior.oracle.spans if prior else ()) + accepted_spans
    acceptances = tuple(prior.acceptances if prior else ()) + tuple(
        AcceptanceRecord(
            span_id=span_id,
            batch_id=batch_id,
            reviewer=reviewer,
            accepted_at=accepted_at,
        )
        for span_id in resolved_scope
    )
    # The sibling ledger, on the same terms: who accepted this unit, when, and
    # as part of which action. A batch that resolved only units produces no
    # ``AcceptanceRecord`` at all, so without this its reviewer and timestamp
    # would reach no retained evidence and nothing would attribute the unit to
    # the action that accepted it.
    review_unit_acceptances = tuple(prior.review_unit_acceptances if prior else ()) + (
        tuple(
            ReviewUnitAcceptance(
                unit_id=unit_id,
                batch_id=batch_id,
                reviewer=reviewer,
                accepted_at=accepted_at,
            )
            for unit_id in resolved_review_units
        )
    )

    representation = _merge_representation(
        prior.oracle.representation if prior else None,
        proposal.proposed_representation,
    )
    if prior is not None:
        _refuse_reference_retargeting(prior.oracle.representation, representation)
        # The carried decisions are re-checked against the *merged* result, for
        # the reason the review inventory is: a later batch changes what the
        # accepted representation states, and a resolution that no longer
        # applies to it must not be carried into the artifact as though it did.
        if inapplicable := reference_resolution_violations(
            representation, prior.oracle.reference_resolutions, prior.oracle.binding
        ):
            raise AcceptanceError(
                "this acceptance would extend accepted authority in a way its "
                "existing reviewed reference resolutions no longer describe: "
                + "; ".join(inapplicable)
            )

    # The inventory accumulates like batch scopes do, and for the same reason:
    # two units under one id would make every expectation's parentage ambiguous
    # in the persisted rows and in the artifact alike.
    prior_units = prior.oracle.review_units if prior else ()
    if repeated := sorted(
        set(resolved_review_units) & {u.unit_id for u in prior_units}
    ):
        raise AcceptanceError(
            f"review units already recorded by a prior batch: {repeated}"
        )
    merged_units = prior_units + accepted_units
    # Checked against the merged representation rather than this proposal's,
    # because a unit may expect a rule an earlier batch structured. Refused here,
    # before an artifact exists, rather than producing one the loader rejects —
    # the same terms as the disjoint-scope refusal above.
    # Against the merged spans for the same reason as the merged representation:
    # a unit may have read its rule from a span an earlier batch accepted.
    if violations := review_unit_violations(
        merged_units, representation, proposal.policy_version, _ordered(spans)
    ):
        raise AcceptanceError(
            "this acceptance would record a review inventory that is not "
            f"coverage of what it claims: {violations}"
        )

    return AcceptedInputs(
        oracle=AcceptedOracle(
            binding=proposal.binding,
            policy_version=proposal.policy_version,
            policy_hash=proposal.policy_hash,
            schema_version=proposal.schema_version,
            schema_hash=proposal.schema_hash,
            spans=_ordered(spans),
            representation=representation,
            obligations=derive_obligations(representation),
            review_units=merged_units,
            # Carried, never re-derived and never dropped. A reviewed resolution
            # is accepted authority in its own right; an extension that lost it
            # would silently reopen a citation the Owner closed, and the artifact
            # would state an unresolved reference nobody had decided to reopen.
            reference_resolutions=(prior.oracle.reference_resolutions if prior else ()),
        ),
        batches=tuple(prior.batches if prior else ()) + (batch,),
        acceptances=acceptances,
        review_unit_acceptances=review_unit_acceptances,
        # Every retained batch states the schema it was *reviewed* under, and
        # this new one states the schema the proposal declares. A prior loaded
        # in the legacy unanchored form is anchored here at its own declaration,
        # which is the one reading that form can have — done at the seam that
        # knows both halves, rather than left for a later reader to infer from
        # an empty lift history it cannot interpret (#137 round 7).
        schema_anchors=prior_anchors
        + (
            BatchSchemaAnchor(
                batch_id=batch.batch_id,
                proposal_identity=batch.proposal_identity,
                schema_version=proposal.schema_version,
                schema_hash=proposal.schema_hash,
            ),
        ),
        # Oldest first, and append-only: an artifact records every succession it
        # was carried across, not merely the last one.
        lifts=tuple(prior.lifts if prior else ()) + lift_records,
        # Append-only on the same terms, and empty for every artifact that never
        # crossed a policy boundary — which is all seven accepted batches.
        policy_transitions=tuple(prior.policy_transitions if prior else ())
        + policy_steps,
        # The authorization evidence for the carried resolutions, on the same
        # terms: the decision and the record of who took it are one artifact's
        # two halves, and an extension that kept one without the other would
        # fail its own loader cross-check.
        reference_resolution_acceptances=(
            prior.reference_resolution_acceptances if prior else ()
        ),
    )


def _refuse_reference_retargeting(
    prior: RepresentationDraft, merged: RepresentationDraft
) -> None:
    """Refuse an acceptance that would give an accepted citation a new target.

    The keyed union retains an element whose key was already accepted and
    appends a genuinely new one — and a reference's key
    (``representation.reference_target_key``) **includes its target**. So a
    proposal restating an accepted citation with a different destination is a
    new key, not a conflict, and the union used to keep both: the accepted edge
    and the new one, which :mod:`validation` then reports as an ambiguity
    nothing in the artifact explains.

    Two cases, both refused here and each in its own words:

    * the accepted target is **empty** — authoring a destination cannot close an
      unresolved citation, whatever it says. :func:`resolve_references` is the
      supported path, and pointing at it is the whole value of failing here;
    * the accepted target is **already a destination** — retargeting an accepted
      reference is not authorized by the Owner Decision of 2026-09-19, which
      covers empty-target resolution and nothing else.

    A batch that legitimately mints the record an accepted citation already
    names is untouched: it defines a *record*, and the citation's own key never
    changes, which is why the ten cross-batch targets outstanding in
    ``docs/architecture/known_unknowns.md`` need none of this.
    """
    accepted: dict[tuple[str, ...], set[str]] = {}
    for ref in prior.references:
        accepted.setdefault(reference_target_key(ref)[:4], set()).add(
            ref.target_record_key
        )
    for ref in merged.references:
        citation = reference_target_key(ref)[:4]
        targets = accepted.get(citation)
        if targets is None or ref.target_record_key in targets:
            continue
        scope, text = citation[3], citation[2]
        tag = f"reference {scope}:{text!r} of record {citation[0]}"
        if "" in targets:
            raise AcceptanceError(
                f"{tag}: this acceptance would state the destination "
                f"{ref.target_record_key!r} for a citation already accepted with "
                "none. Authoring a destination cannot close an unresolved "
                "citation — the accepted empty edge is a different key and "
                "survives beside it, reported both unresolved and ambiguous. "
                "Resolve it through resolve_references, which records who "
                "authorized the destination and leaves the accepted history "
                "intact."
            )
        raise AcceptanceError(
            f"{tag}: this acceptance would retarget a citation already accepted "
            f"as resolving to {sorted(targets)}. Retargeting an accepted "
            "reference is not authorized; the Owner Decision of 2026-09-19 "
            "covers resolving an empty target and nothing else."
        )


def resolve_references(
    prior: AcceptedInputs,
    *,
    resolutions: tuple[ReferenceResolution, ...],
    authorized_by: str,
    authorization_reference: str,
    reviewer: str,
    resolved_at: str,
) -> AcceptedInputs:
    """Record one explicitly authorized decision over accepted empty targets.

    The second acceptance action this module states, and deliberately the only
    other one. It is an **append**, exactly like :func:`accept_proposal`: two
    ledger entries per resolution are added — the identity-bearing decision and
    the evidence of who authorized it — and nothing already accepted is edited.
    The accepted representation keeps stating the unresolved citation every
    reviewer accepted; :func:`~.reference_resolution.effective_representation` is
    what the build persists and the gate judges, so the effective authority has
    exactly one destination while the history stays reconstructable.

    **Why one action carries several resolutions.** Two components of one record
    may legitimately cite the same wording in the same scope — each is its own
    claim with its own provenance, and :mod:`validation` says so. Their
    destination, though, is shared: ``(scope, source_text)`` resolving to more
    than one record is the ambiguity publication refuses. So consistent
    same-scope citations cannot be resolved one at a time — the intermediate
    artifact would state ``['', destination]`` for one wording, which is exactly
    the refusal that must not be weakened. They are one reviewed decision and
    this action records them as one: validated together against the accepted
    authority, applied whole or not at all. Each resolution keeps its own
    citation, its own reviewed provenance spans and its own
    ``ReferenceResolutionAcceptance``; what they share is the authorization this
    call names. Nothing about a single resolution changes — it is
    ``resolutions=(one,)`` — and a *genuine* ambiguity, two citations of one
    wording sent to different records, is still refused whether stated in one
    action or several.

    **What it refuses, and why it refuses rather than reports.** A half-recorded
    resolution is worse than none, on the same terms as a half-recorded
    acceptance: the artifact would claim a decision nobody took. Every refusal
    happens before the returned value is built, so a caller that catches
    :class:`AcceptanceError` holds exactly the artifact it held before —

    * anything that is not exactly a closed :class:`ReferenceResolution` in an
      exact ``tuple``, refused **before this action reads a single field**. The
      replay check below keys on ``resolution_id`` and the applicability check
      keys on the citation, so a subclass supplying either through a method or
      an overridden ``__eq__`` would decide its own admission;
    * **no** resolution at all. An action that decides nothing is not a decision;
    * a ``resolution_id`` a prior decision already recorded. **Repeat is refused,
      not absorbed**: the same rule ``accept_proposal`` applies to a ``batch_id``
      it already holds. Replaying an identical decision is therefore
      deterministic — it raises, and the artifact is unchanged — rather than
      appending a second authorization of one decision. Any already-recorded id
      refuses the **whole** action, so a partial replay records no part of it;
    * a second, differently-identified decision about one citation, which is a
      conflict nothing here can choose between;
    * a citation this authority does not state as unresolved, including one
      already resolved — retargeting is not authorized;
    * a destination, provenance, or any one of the six release-binding
      coordinates that is not what review saw;
    * a resolution whose effective view publication would refuse, ambiguity
      above all;
    * an authorization missing its authority, its reference, its reviewer or its
      timestamp. ``authorized_by`` and ``authorization_reference`` are required
      for the reason the whole record exists: a machine suggestion must not
      become authority implicitly, so a resolution nobody is recorded as having
      decided is not one.

    ``prior`` is required and has no default. There is no such thing as
    resolving a reference in an artifact that accepted none.
    """
    for field, value in (
        ("authorizing authority", authorized_by),
        ("authorization reference", authorization_reference),
        ("reviewer", reviewer),
        ("resolution timestamp", resolved_at),
    ):
        if not value.strip():
            raise AcceptanceError(
                f"a reference resolution must name its {field}; an unattributed "
                "resolution is not a reviewed decision"
            )

    # Before ``not resolutions``, before the id set below, and before
    # ``reference_resolution_violations`` — which repeats this pass for the
    # loader's sake. The replay check reads ``resolution_id`` into a set, so a
    # ``str`` subclass with its own ``__hash__`` would answer the
    # already-recorded question about itself, and a resolution subclass would
    # execute a property to do it (#137 round 13).
    if malformed := reference_resolution_shape_violations(resolutions):
        raise AcceptanceError(
            "this resolution action does not state reference resolutions: "
            + "; ".join(malformed)
        )

    if not resolutions:
        raise AcceptanceError(
            "a reference resolution action must state at least one resolution; "
            "an action that resolves nothing is not a reviewed decision"
        )

    if already := sorted(
        {r.resolution_id for r in resolutions}
        & {r.resolution_id for r in prior.oracle.reference_resolutions}
    ):
        raise AcceptanceError(
            f"reference resolution {already} is already recorded by this "
            "accepted authority; a repeat is refused rather than recorded "
            "twice, so replaying this action leaves the artifact exactly as it "
            "was"
        )

    if inapplicable := reference_resolution_violations(
        prior.oracle.representation,
        prior.oracle.reference_resolutions + resolutions,
        prior.oracle.binding,
    ):
        raise AcceptanceError(
            "this resolution does not apply to the accepted authority it would "
            "resolve: " + "; ".join(inapplicable)
        )

    return replace(
        prior,
        oracle=replace(
            prior.oracle,
            reference_resolutions=prior.oracle.reference_resolutions + resolutions,
        ),
        reference_resolution_acceptances=prior.reference_resolution_acceptances
        + tuple(
            ReferenceResolutionAcceptance(
                resolution_id=resolution.resolution_id,
                authorized_by=authorized_by,
                authorization_reference=authorization_reference,
                reviewer=reviewer,
                resolved_at=resolved_at,
            )
            for resolution in resolutions
        ),
    )


def _carried_anchors(prior: AcceptedInputs | None) -> tuple[BatchSchemaAnchor, ...]:
    """The prior artifact's anchors, validated before anything is carried.

    Delegated to ``schema_lift.carried_anchors`` rather than restated: the rule
    that decides whether an artifact's evidence may be carried forward is the
    same rule the loader applies to it, and two implementations of it would
    disagree exactly where it matters. This wrapper exists only to say the
    refusal in the words ``accept_proposal``'s callers already handle.
    """
    if prior is None:
        return ()
    try:
        return carried_anchors(prior)
    except SchemaLiftError as exc:
        raise AcceptanceError(
            "this proposal would extend prior accepted authority whose own "
            f"succession evidence does not hold: {exc}"
        ) from exc


def _ordered(spans: tuple[SemanticSpan, ...]) -> tuple[SemanticSpan, ...]:
    """Spans in a deterministic order, so two equal acceptances write one file.

    Ordered by content — leaf then offsets — rather than by acceptance sequence,
    because the order review happened in is evidence, not part of the accepted
    result, and letting it into the file would make the artifact depend on which
    batch ran first.
    """
    return tuple(sorted(spans, key=lambda s: (s.leaf_id, s.char_start, s.char_end)))
