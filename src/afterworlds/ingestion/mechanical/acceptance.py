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
its own acceptance validation. Correcting an earlier acceptance therefore needs
a history model with supersession semantics, which this module deliberately does
not have and this PR does not add. What it does support is the workflow
full-corpus review actually needs: one complete proposal reviewed across several
disjoint span batches, whose representations merge as a keyed union rather than
piling up duplicates.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from afterworlds.ingestion.mechanical.accounting import batch_diff_hash
from afterworlds.ingestion.mechanical.models import (
    AcceptanceBatch,
    AcceptanceRecord,
    ReviewState,
    SemanticDiffEntry,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    AcceptedOracle,
    derive_obligations,
)
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceClaim,
    RepresentationDraft,
    component_target_key,
    prose_binding_target_key,
    record_target_key,
    reference_target_key,
    relationship_target_key,
)

__all__ = ["AcceptanceError", "accept_proposal"]


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


def accept_proposal(
    proposal: MechanicalProposal,
    *,
    batch_id: str,
    rule: str,
    resolved_scope: tuple[str, ...],
    reviewer: str,
    accepted_at: str,
    prior: AcceptedInputs | None = None,
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

    Extending *prior* requires a disjoint scope: a span it already accepted
    cannot be re-accepted here.
    """
    if not resolved_scope:
        raise AcceptanceError("an acceptance action must name at least one span")
    if not reviewer.strip():
        raise AcceptanceError("an acceptance action must name its reviewer")
    if not rule.strip():
        raise AcceptanceError("an acceptance action must record its selection rule")

    proposed_by_id = {p.span.span_id: p.span for p in proposal.proposed_spans}
    if duplicates := sorted({s for s in resolved_scope if resolved_scope.count(s) > 1}):
        raise AcceptanceError(f"resolved scope repeats spans {duplicates}")
    if unknown := sorted(set(resolved_scope) - proposed_by_id.keys()):
        raise AcceptanceError(
            f"resolved scope names spans this proposal did not propose: {unknown}"
        )

    if prior is not None and prior.oracle.binding != proposal.binding:
        raise AcceptanceError(
            "this proposal binds a different 5c release than the prior accepted "
            "authority it would extend"
        )
    if prior is not None and (
        prior.oracle.policy_version,
        prior.oracle.policy_hash,
    ) != (proposal.policy_version, proposal.policy_hash):
        raise AcceptanceError(
            "this proposal declares a different semantic policy than the prior "
            "accepted authority it would extend"
        )

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

    representation = _merge_representation(
        prior.oracle.representation if prior else None,
        proposal.proposed_representation,
    )
    return AcceptedInputs(
        oracle=AcceptedOracle(
            binding=proposal.binding,
            policy_version=proposal.policy_version,
            policy_hash=proposal.policy_hash,
            spans=_ordered(spans),
            representation=representation,
            obligations=derive_obligations(representation),
        ),
        batches=tuple(prior.batches if prior else ()) + (batch,),
        acceptances=acceptances,
    )


def _ordered(spans: tuple[SemanticSpan, ...]) -> tuple[SemanticSpan, ...]:
    """Spans in a deterministic order, so two equal acceptances write one file.

    Ordered by content — leaf then offsets — rather than by acceptance sequence,
    because the order review happened in is evidence, not part of the accepted
    result, and letting it into the file would make the artifact depend on which
    batch ran first.
    """
    return tuple(sorted(spans, key=lambda s: (s.leaf_id, s.char_start, s.char_end)))
