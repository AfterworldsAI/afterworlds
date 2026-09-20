"""Reviewed resolution of an accepted empty-target reference — CRD Issue 5d.

Owner Decision of 2026-09-19, recorded under ADR-005d Decision 7: *"Option A is
clearly the best choice. You are authorized to implement A."* The bounded
capability that decision authorizes, and nothing wider:

    accepted citation with no destination
      →  reviewed destination, recorded as an explicit decision
      →  one effective reference, original acceptance untouched

**The edge this exists for.** Acceptance is append-only and keyed
(:mod:`acceptance`), and ``representation.reference_target_key`` includes
``target_record_key``. So a later batch that authors the destination cannot close
an empty citation: its reference is a *different* key, the keyed union retains
both, and :func:`~.validation.relationship_and_reference_violations` then reports
the same citation twice — ``unresolved reference`` for the empty edge and
``ambiguous`` for the pair. This is not the case of the ten cross-batch targets
already outstanding in ``docs/architecture/known_unknowns.md``: those name a
destination key that no accepted batch has minted a record for yet, so the *same*
key resolves the moment one does, and no decision is needed. An empty target is
the case where review could state no key at all, and only an explicit decision
can supply one.

**What this module does not do.** It resolves an empty target and nothing else.
Retargeting an already-resolved citation is refused, as is editing accepted prose
or facts, general supersession of an accepted claim, ingesting a source, and
guessing a destination. There is no second acceptance system: a resolution is a
record on the accepted oracle, validated by the validator the rest of the build
already uses, and taken through :func:`~.acceptance.resolve_references` — the
same seam ``accept_proposal`` lives at.

**Two views, one artifact.** The accepted representation keeps stating exactly
what each of the seven accepted batches' reviewers accepted, including the empty
edge — :func:`effective_representation` derives the resolved view the build,
gate, query and override paths judge and persist. Nothing is rewritten, nothing
is erased, and a missing resolution stays detectably unresolved rather than
silently closed.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace

from afterworlds.ingestion.mechanical.models import ReferenceResolution
from afterworlds.ingestion.mechanical.projection import ReleaseBinding
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceTargetKind,
    RepresentationDraft,
    reference_target_key,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)

__all__ = [
    "effective_representation",
    "reference_resolution_payload",
    "reference_resolution_violations",
]


def effective_representation(
    representation: RepresentationDraft,
    resolutions: tuple[ReferenceResolution, ...],
) -> RepresentationDraft:
    """The accepted representation as its reviewed resolutions state it.

    Each resolved citation's empty-target reference is replaced **in place** by
    the same reference carrying its reviewed destination. Never appended beside:
    appending is precisely the shape that produces one unresolved edge and one
    ambiguity, which is the defect this module exists to close.

    The matching provenance claims move with it. ``ProvenanceTargetKind.REFERENCE``
    claims are keyed by :func:`~.representation.reference_target_key`, which
    includes the target, and ``REFERENCE`` is in ``PROVENANCE_REQUIRED_KINDS`` —
    so a resolved reference whose claims kept the empty-target coordinates would
    orphan every one of them *and* leave the resolved reference with no
    provenance at all. Same spans, same roles, same claims; only the coordinate
    of the element they attach to follows the element.

    The identity function when there are no resolutions, and deliberately
    returns the argument itself rather than a copy: every one of the seven
    accepted batches states none, and an object rebuilt field-by-field is one
    more place a future field could be dropped in.
    """
    if not resolutions:
        return representation

    by_citation = {r.citation_key(): r for r in resolutions}
    remapped: dict[tuple[str, ...], tuple[str, ...]] = {}
    references = []
    for ref in representation.references:
        resolution = by_citation.get(
            (
                ref.from_record_key,
                ref.from_component_key,
                ref.source_text,
                ref.scope_key,
            )
        )
        # An already-targeted reference is left exactly as accepted even when a
        # resolution names its citation. Retargeting is unauthorized, and this
        # view is not where that refusal is reported — a view that quietly
        # applied it would make the refusal in
        # :func:`reference_resolution_violations` unenforceable.
        if resolution is None or ref.target_record_key:
            references.append(ref)
            continue
        resolved = replace(ref, target_record_key=resolution.target_record_key)
        remapped[reference_target_key(ref)] = reference_target_key(resolved)
        references.append(resolved)

    if not remapped:
        return representation

    provenance = tuple(
        (
            replace(claim, target_key=remapped[claim.target_key])
            if claim.target_kind is ProvenanceTargetKind.REFERENCE
            and claim.target_key in remapped
            else claim
        )
        for claim in representation.provenance
    )
    return replace(representation, references=tuple(references), provenance=provenance)


def reference_resolution_violations(
    representation: RepresentationDraft,
    resolutions: tuple[ReferenceResolution, ...],
    binding: ReleaseBinding,
) -> list[str]:
    """Every reason these resolutions do not apply to this accepted authority.

    Reported rather than raised, on the same terms as ``schema_binding_violations``
    and ``review_unit_violations``: the acceptance seam turns findings into a
    refusal before anything is recorded, and the loader turns them into a refusal
    before a committed file becomes authority. Both call this, so an artifact
    that loads is one the seam would have produced.

    **The destination is checked directly, and the delta is a multiset.** A
    decision that names a record this authority does not state is invalid as a
    decision, not merely inconvenient as a consequence, so it is refused here in
    its own words rather than inferred from the resolved view. Inference was
    unsound: :func:`~.validation.relationship_and_reference_violations` tags a
    reference by ``scope:source_text`` alone, so two components legitimately
    citing one wording produce byte-identical findings, and a set difference
    silently absorbed the second one — an invalid destination could hide behind
    a sibling's pre-existing finding. The delta below therefore subtracts
    :class:`~collections.Counter` multisets: two occurrences of one finding minus
    one occurrence still reports one.

    The delta stays a **delta against the accepted view** rather than a
    restatement of the reference rules, and still owns ambiguity, the
    record-owned/component cross-form case and anything else the validator
    grows, each in the words publication is judged by. Restating ambiguity here
    would be a second definition of it that eventually disagrees.
    """
    findings: list[str] = []
    seen_ids: set[str] = set()
    seen_citations: dict[tuple[str, str, str, str], str] = {}
    record_keys = {r.semantic_key for r in representation.records}
    by_key = {reference_target_key(r): r for r in representation.references}
    provenance_by_key: dict[tuple[str, ...], set[str]] = {}
    for claim in representation.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            provenance_by_key.setdefault(claim.target_key, set()).add(claim.span_id)

    for resolution in resolutions:
        tag = f"reference resolution {resolution.resolution_id!r}"
        if not resolution.resolution_id.strip():
            findings.append("a reference resolution must state its own id")
            continue
        if resolution.resolution_id in seen_ids:
            findings.append(f"{tag}: stated more than once")
            continue
        seen_ids.add(resolution.resolution_id)

        if not resolution.target_record_key.strip():
            # An empty destination resolves nothing: it is the state being
            # resolved, recorded as though it were the decision.
            findings.append(f"{tag}: names no destination record")
            continue

        # The destination must be a record this accepted authority actually
        # states. Bound here rather than read off the resolved view: a decision
        # pointing at nothing is invalid on its own terms, and the resolved
        # view's wording for it is shared with every sibling citation of the
        # same phrase, which is how a missing destination used to hide.
        if resolution.target_record_key not in record_keys:
            findings.append(
                f"{tag}: names the destination "
                f"{resolution.target_record_key!r}, which this accepted "
                "authority states no record for; a resolution binds a "
                "destination review read here, and cannot mint one"
            )
            continue

        # Two decisions about one citation. Neither is stale on its face and
        # nothing here can choose between them, which is exactly why this fails
        # closed rather than applying the later one.
        citation = resolution.citation_key()
        if (earlier := seen_citations.get(citation)) is not None:
            findings.append(
                f"{tag}: conflicts with {earlier!r}; both resolve the citation "
                f"{resolution.scope_key}:{resolution.source_text!r} of record "
                f"{resolution.from_record_key}"
            )
            continue
        seen_citations[citation] = resolution.resolution_id

        if (resolution.package_uuid, resolution.release_version) != (
            binding.package_uuid,
            binding.release_version,
        ):
            findings.append(
                f"{tag}: was reviewed against release {resolution.package_uuid}/"
                f"{resolution.release_version}, not {binding.package_uuid}/"
                f"{binding.release_version}"
            )
            continue

        unresolved_key = (*citation, "")
        accepted = by_key.get(unresolved_key)
        if accepted is None:
            resolved_now = sorted(
                key[4] for key in by_key if key[:4] == citation and key[4]
            )
            if resolved_now:
                findings.append(
                    f"{tag}: the citation "
                    f"{resolution.scope_key}:{resolution.source_text!r} of record "
                    f"{resolution.from_record_key} already resolves to "
                    f"{resolved_now}; retargeting a resolved citation is not "
                    "authorized by the Owner Decision of 2026-09-19"
                )
            else:
                findings.append(
                    f"{tag}: this accepted authority states no unresolved "
                    f"citation {resolution.scope_key}:"
                    f"{resolution.source_text!r} owned by "
                    f"{resolution.from_record_key}/{resolution.from_component_key}"
                )
            continue

        resolved_key = (*citation, resolution.target_record_key)
        if resolved_key in by_key:
            findings.append(
                f"{tag}: the accepted representation already states this exact "
                "reference beside the unresolved one, so applying the "
                "resolution would publish one citation twice"
            )
            continue

        # Source-bound exactness. The decision approved a destination for a
        # citation read out of exactly these spans; a citation whose provenance
        # now cites others is not the one review saw, whatever its wording.
        recorded = tuple(sorted(resolution.provenance_span_ids))
        actual = tuple(sorted(provenance_by_key.get(unresolved_key, ())))
        if recorded != actual:
            findings.append(
                f"{tag}: was reviewed against provenance spans {list(recorded)}, "
                f"but the accepted citation cites {list(actual)}"
            )

    if findings:
        # The delta below is only meaningful over resolutions that apply at all.
        # Running it over a set already known to be inapplicable would report
        # consequences of the refusals above as if they were separate defects.
        return findings

    accepted_findings = Counter(relationship_and_reference_violations(representation))
    effective = effective_representation(representation, resolutions)
    effective_findings = Counter(relationship_and_reference_violations(effective))
    if introduced := sorted((effective_findings - accepted_findings).elements()):
        findings.append(
            "applying these resolutions would make the effective references "
            "state something publication refuses: " + "; ".join(introduced)
        )
    return findings


def reference_resolution_payload(
    resolutions: tuple[ReferenceResolution, ...],
) -> list[dict[str, object]]:
    """Canonical payload of the accepted resolutions, in a deterministic order.

    Ordered by ``resolution_id`` rather than by the order decisions were taken,
    for the reason ``acceptance._ordered`` orders spans by content: the sequence
    review happened in is evidence, not part of the accepted result, and letting
    it into the payload would make the oracle's identity depend on it.
    """
    return [
        {
            "resolution_id": r.resolution_id,
            "from_record_key": r.from_record_key,
            "from_component_key": r.from_component_key,
            "source_text": r.source_text,
            "scope_key": r.scope_key,
            "target_record_key": r.target_record_key,
            "package_uuid": r.package_uuid,
            "release_version": r.release_version,
            "provenance_span_ids": list(r.provenance_span_ids),
        }
        for r in sorted(resolutions, key=lambda r: r.resolution_id)
    ]
