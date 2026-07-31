"""Representation validation — CRD Issue 5d, Decisions 3, 4, and 7.

Checks the keyed representation against the accepted classification it claims
to represent. Like the accounting layer, every check returns violation strings
so one pass reports everything wrong rather than stopping at the first problem.

What this layer is responsible for catching:

* dangling keys — a component on a record that does not exist, a relationship
  or reference to a missing record, provenance for an element nobody declared;
* duplicate semantic keys, which would make an identity ambiguous;
* record assembly errors — a parent cycle, a nested record pointing at itself;
* handling honesty — ``STRUCTURED`` with no facts, ``PROSE_BOUND`` with facts
  and no bound prose, a prose binding without a closed irreducibility reason;
* facts outside the closed typed union;
* provenance errors — an unknown span, a substantive span nothing claims, a
  supporting span nothing links, and two elements both claiming to be what one
  span primarily says; and
* reference resolution errors — an unresolved or ambiguous reference, where the
  same source wording inside one committed scope resolves two ways.

It is *not* responsible for completeness across the corpus. That is the later
publication gate, which runs against reconstructed persisted state. Passing
here means the representation is internally honest, not that it is finished.
"""

from __future__ import annotations

from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ComponentHandling,
    SemanticDisposition,
)
from afterworlds.ingestion.mechanical.policy import irreducibility_reason_for
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceRole,
    ProvenanceTargetKind,
    RepresentationDraft,
    UnknownFactFamilyError,
    fact_key,
    fact_payload,
)

__all__ = ["validate_representation"]


def _validate_records(draft: RepresentationDraft) -> list[str]:
    findings: list[str] = []
    seen: set[str] = set()
    for record in draft.records:
        if record.semantic_key in seen:
            findings.append(f"record {record.semantic_key}: duplicate semantic key")
        seen.add(record.semantic_key)

    keys = {r.semantic_key for r in draft.records}
    parents = {r.semantic_key: r.parent_key for r in draft.records}
    for record in draft.records:
        parent = record.parent_key
        if parent is None:
            continue
        if parent not in keys:
            findings.append(f"record {record.semantic_key}: unknown parent {parent}")
            continue
        # Walk up; a nested record must terminate at a root, not loop.
        seen_path = {record.semantic_key}
        cursor: str | None = parent
        while cursor is not None:
            if cursor in seen_path:
                findings.append(
                    f"record {record.semantic_key}: parent cycle through {cursor}"
                )
                break
            seen_path.add(cursor)
            cursor = parents.get(cursor)
    return findings


def _validate_components(draft: RepresentationDraft) -> list[str]:
    findings: list[str] = []
    record_keys = {r.semantic_key for r in draft.records}
    bound_prose = {(b.record_key, b.component_key) for b in draft.prose_bindings}
    seen: set[tuple[str, str]] = set()

    for component in draft.components:
        key = (component.record_key, component.semantic_key)
        tag = f"component {component.record_key}/{component.semantic_key}"
        if key in seen:
            findings.append(f"{tag}: duplicate semantic key")
        seen.add(key)

        if component.record_key not in record_keys:
            findings.append(f"{tag}: unknown record {component.record_key}")

        fact_keys: set[str] = set()
        for fact in component.facts:
            try:
                key_ = fact_key(fact)
            except UnknownFactFamilyError as exc:
                findings.append(f"{tag}: {exc}")
                continue
            # Facts are identified by content, so a repeat is not a second
            # claim — it is the same claim counted twice, which is exactly the
            # duplicate-as-coverage inflation the completeness proof rejects.
            if key_ in fact_keys:
                findings.append(f"{tag}: duplicate typed fact {key_}")
            fact_keys.add(key_)

        has_prose = key in bound_prose
        if component.handling is ComponentHandling.STRUCTURED:
            if not component.facts:
                findings.append(f"{tag}: structured handling with no typed facts")
            if has_prose:
                findings.append(f"{tag}: structured handling with a prose binding")
            if component.irreducibility_reason_code is not None:
                findings.append(
                    f"{tag}: structured handling with an irreducibility reason"
                )
        elif component.handling is ComponentHandling.PROSE_BOUND:
            if component.facts:
                findings.append(f"{tag}: prose-bound handling with typed facts")
            if not has_prose:
                findings.append(f"{tag}: prose-bound handling with no bound prose")
        else:  # MIXED
            if not component.facts:
                findings.append(f"{tag}: mixed handling with no typed facts")
            if not has_prose:
                findings.append(f"{tag}: mixed handling with no bound prose")

        code = component.irreducibility_reason_code
        if code is not None and irreducibility_reason_for(code) is None:
            findings.append(f"{tag}: irreducibility reason {code!r} is not closed")

    return findings


def _validate_prose_bindings(draft: RepresentationDraft) -> list[str]:
    findings: list[str] = []
    component_keys = {(c.record_key, c.semantic_key) for c in draft.components}
    for binding in draft.prose_bindings:
        tag = f"prose binding {binding.record_key}/{binding.component_key}"
        if (binding.record_key, binding.component_key) not in component_keys:
            findings.append(f"{tag}: unknown component")
        if not binding.chunk_id.strip():
            findings.append(f"{tag}: no authoritative chunk bound")
        if irreducibility_reason_for(binding.irreducibility_reason_code) is None:
            findings.append(
                f"{tag}: irreducibility reason "
                f"{binding.irreducibility_reason_code!r} is not closed"
            )
    return findings


def _validate_relationships_and_references(draft: RepresentationDraft) -> list[str]:
    findings: list[str] = []
    record_keys = {r.semantic_key for r in draft.records}
    component_keys = {(c.record_key, c.semantic_key) for c in draft.components}

    for rel in draft.relationships:
        tag = f"relationship {rel.source_record_key}->{rel.target_record_key}"
        for key in (rel.source_record_key, rel.target_record_key):
            if key not in record_keys:
                findings.append(f"{tag}: unknown record {key}")
        if rel.source_record_key == rel.target_record_key:
            findings.append(f"{tag}: record related to itself")

    # A reference is ambiguous when identical source wording inside one
    # committed scope resolves to more than one target. Unique destination
    # names alone never establish intent, so the scope is what disambiguates.
    resolutions: dict[tuple[str, str], set[str]] = {}
    for ref in draft.references:
        tag = f"reference {ref.scope_key}:{ref.source_text!r}"
        if ref.from_record_key not in record_keys:
            findings.append(f"{tag}: unknown source record {ref.from_record_key}")
        if (ref.from_record_key, ref.from_component_key) not in component_keys:
            findings.append(f"{tag}: unknown source component {ref.from_component_key}")
        if not ref.target_record_key:
            findings.append(f"{tag}: unresolved reference")
        elif ref.target_record_key not in record_keys:
            findings.append(f"{tag}: unknown target record {ref.target_record_key}")
        if not ref.scope_key.strip():
            findings.append(f"{tag}: no committed resolution scope")
        resolutions.setdefault((ref.scope_key, ref.source_text), set()).add(
            ref.target_record_key
        )

    for (scope, text), targets in sorted(resolutions.items()):
        if len(targets) > 1:
            findings.append(
                f"reference {scope}:{text!r}: ambiguous — resolves to "
                f"{sorted(targets)}"
            )
    return findings


def _validate_provenance(
    draft: RepresentationDraft, ledger: ClassificationLedger
) -> list[str]:
    findings: list[str] = []
    spans_by_id = {s.span_id: s for s in ledger.spans}

    declared: dict[ProvenanceTargetKind, set[tuple[str, ...]]] = {
        ProvenanceTargetKind.RECORD: {(r.semantic_key,) for r in draft.records},
        ProvenanceTargetKind.COMPONENT: {
            (c.record_key, c.semantic_key) for c in draft.components
        },
        ProvenanceTargetKind.FACT: {
            (c.record_key, c.semantic_key, fact_key(f))
            for c in draft.components
            for f in c.facts
            if _payloadable(f)
        },
        ProvenanceTargetKind.PROSE_BINDING: {
            (b.record_key, b.component_key) for b in draft.prose_bindings
        },
        ProvenanceTargetKind.RELATIONSHIP: {
            (r.source_record_key, r.target_record_key, r.kind.value)
            for r in draft.relationships
        },
        ProvenanceTargetKind.REFERENCE: {
            (r.scope_key, r.source_text, r.target_record_key) for r in draft.references
        },
    }

    primary_by_span: dict[str, list[tuple[str, ...]]] = {}
    claimed: set[str] = set()
    linked: set[str] = set()

    for claim in draft.provenance:
        tag = f"provenance {claim.target_kind.value}{list(claim.target_key)}"
        if claim.target_key not in declared[claim.target_kind]:
            findings.append(f"{tag}: claim for an undeclared element")
        if claim.span_id not in spans_by_id:
            findings.append(f"{tag}: unknown span {claim.span_id}")
            continue
        if claim.role is ProvenanceRole.PRIMARY:
            primary_by_span.setdefault(claim.span_id, []).append(claim.target_key)
            claimed.add(claim.span_id)
        else:
            linked.add(claim.span_id)

    for span_id, owners in sorted(primary_by_span.items()):
        if len(owners) > 1:
            findings.append(
                f"span {span_id}: conflicting primary claims by "
                f"{sorted(str(list(o)) for o in owners)}"
            )

    for span in ledger.spans:
        if (
            span.disposition is SemanticDisposition.SUBSTANTIVE
            and span.span_id not in claimed
        ):
            findings.append(f"span {span.span_id}: substantive but unclaimed")
        elif (
            span.disposition is SemanticDisposition.SUPPORTING_AUTHORITY
            and span.span_id not in claimed | linked
        ):
            findings.append(f"span {span.span_id}: supporting authority but unlinked")

    return findings


def _payloadable(fact: object) -> bool:
    try:
        fact_payload(fact)
    except UnknownFactFamilyError:
        return False
    return True


def validate_representation(
    draft: RepresentationDraft, ledger: ClassificationLedger
) -> tuple[str, ...]:
    """Return every violation of the keyed representation's internal honesty."""
    findings: list[str] = []
    findings.extend(_validate_records(draft))
    findings.extend(_validate_components(draft))
    findings.extend(_validate_prose_bindings(draft))
    findings.extend(_validate_relationships_and_references(draft))
    findings.extend(_validate_provenance(draft, ledger))
    return tuple(findings)
