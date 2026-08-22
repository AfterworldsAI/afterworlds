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

from afterworlds.ingestion.mechanical.bound_corpus import BoundCorpusSnapshot
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ComponentHandling,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.policy import irreducibility_reason_for
from afterworlds.ingestion.mechanical.representation import (
    PROVENANCE_REQUIRED_KINDS,
    ComponentDraft,
    FactFamily,
    ProseBindingDraft,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordKind,
    RelationshipKind,
    RepresentationDraft,
    applicability_violations,
    component_participant_violations,
    declared_provenance_targets,
    fact_invariant_violations,
    fact_key,
    option_set_violations,
    prose_bindings_by_target_key,
    representation_draft_violations,
)

__all__ = ["validate_representation"]

#: Dispositions whose text may serve as a component's governing prose. A
#: non-mechanical or unresolved span states no mechanic, so binding authority to
#: it would reintroduce as authority exactly what the accounting set aside.
_PROSE_BEARING_DISPOSITIONS = frozenset(
    {SemanticDisposition.SUBSTANTIVE, SemanticDisposition.SUPPORTING_AUTHORITY}
)


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


def _validate_options(component: ComponentDraft, tag: str) -> list[str]:
    """The component-draft spelling of the shared option-set contract.

    The rule itself lives in :func:`.representation.option_set_violations` so
    the override patch path enforces the same one rather than a second copy.
    """
    return option_set_violations(component.facts, component.options, tag)


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

        # Facts are checked per *scope*: the component's own list, and each
        # option's list. Duplicates are a defect within a scope, because a
        # repeat is the same claim counted twice — but the same fact appearing
        # in two mutually exclusive options is not a repeat, it is one claim
        # each, and collapsing the two scopes would report a defect that is not
        # there.
        scopes: list[tuple[str, tuple[object, ...]]] = [("", component.facts)]
        scopes.extend((o.semantic_key, o.facts) for o in component.options)
        for option_key, scoped in scopes:
            scope_tag = tag if not option_key else f"{tag} option {option_key}"
            fact_keys: set[str] = set()
            for fact in scoped:
                # Family membership *and* the family's own contract: a fact can
                # belong to the closed union and still contradict itself, and
                # such a fact would persist as mechanically unusable authority.
                violations = fact_invariant_violations(fact)
                if violations:
                    findings.extend(f"{scope_tag}: {v}" for v in violations)
                    continue
                key_ = fact_key(fact)
                if key_ in fact_keys:
                    findings.append(f"{scope_tag}: duplicate typed fact {key_}")
                fact_keys.add(key_)

        findings.extend(_validate_options(component, tag))
        if component.applies_when is not None:
            findings.extend(
                f"{tag}: {v}" for v in applicability_violations(component.applies_when)
            )

        # The counterpart rule is component-scoped and cannot live on a fact:
        # no fact can see whether a neighbour establishes the relation it
        # depends on. Establishment flows from the component into its options
        # but never across two mutually exclusive arms. The same function is
        # asked again of the final effective view after overrides resolve.
        findings.extend(
            component_participant_violations(
                component.facts, component.options, component.applies_when, tag
            )
        )

        has_prose = key in bound_prose
        code = component.irreducibility_reason_code
        # Option facts are structured authority exactly as direct facts are: a
        # component whose whole meaning is an actor choice publishes typed
        # facts, they simply live one level down.
        published = component.all_facts()
        if component.handling is ComponentHandling.STRUCTURED:
            if not published:
                findings.append(f"{tag}: structured handling with no typed facts")
            if has_prose:
                findings.append(f"{tag}: structured handling with a prose binding")
            if code is not None:
                findings.append(
                    f"{tag}: structured handling with an irreducibility reason"
                )
        else:
            handling = component.handling.value
            if component.handling is ComponentHandling.PROSE_BOUND:
                if published:
                    findings.append(f"{tag}: {handling} handling with typed facts")
            elif not published:
                findings.append(f"{tag}: mixed handling with no typed facts")
            if not has_prose:
                findings.append(f"{tag}: {handling} handling with no bound prose")
            # A component that says its meaning is irreducible must say *why*,
            # under the closed catalog. Silence here is the backlog state
            # PROSE_BOUND must never become.
            if code is None or not code.strip():
                findings.append(
                    f"{tag}: {handling} handling with no irreducibility reason"
                )

        if (
            code is not None
            and code.strip()
            and irreducibility_reason_for(code) is None
        ):
            findings.append(f"{tag}: irreducibility reason {code!r} is not closed")

    return findings


def _validate_prose_extent(
    binding: ProseBindingDraft,
    spans_by_id: dict[str, SemanticSpan],
    corpus: BoundCorpusSnapshot,
    tag: str,
) -> list[str]:
    """Check that a binding governs exactly the accepted span it names.

    Governing prose is *accepted* authority, so it resolves through the
    classification rather than around it, and the chunk-relative offsets the
    binding carries for runtime resolution are recomputed here from the bound
    release. A binding whose declared extent disagrees with the span it names is
    rejected: the whole point of carrying offsets is that runtime need not
    re-derive them, which is only safe if the build proved them.
    """
    findings: list[str] = []
    span = spans_by_id.get(binding.span_id)
    if span is None:
        return [f"{tag}: unknown accepted span {binding.span_id!r}"]

    # Governing prose must be text the accounting accepted as saying something.
    # Binding a component's authority to licensing, navigation, or flavour text
    # would let material the classification excluded back in as authority.
    if span.disposition not in _PROSE_BEARING_DISPOSITIONS:
        findings.append(
            f"{tag}: span {binding.span_id} is {span.disposition.value}; governing "
            "prose resolves only to substantive or supporting authority"
        )

    extent = corpus.chunk_relative_range(
        binding.chunk_id, span.leaf_id, span.char_start, span.char_end
    )
    if extent is None:
        findings.append(
            f"{tag}: chunk {binding.chunk_id} does not unambiguously contain span "
            f"{binding.span_id} [{span.char_start},{span.char_end}) of leaf "
            f"{span.leaf_id}"
        )
    elif (binding.chunk_char_start, binding.chunk_char_end) != extent:
        findings.append(
            f"{tag}: declared chunk extent "
            f"[{binding.chunk_char_start},{binding.chunk_char_end}) is not the "
            f"bound span's extent {list(extent)}"
        )
    return findings


def _validate_prose_bindings(
    draft: RepresentationDraft,
    ledger: ClassificationLedger,
    corpus: BoundCorpusSnapshot,
) -> list[str]:
    findings: list[str] = []
    components = {(c.record_key, c.semantic_key): c for c in draft.components}
    spans_by_id = {s.span_id: s for s in ledger.spans}
    for binding in draft.prose_bindings:
        tag = f"prose binding {binding.record_key}/{binding.component_key}"
        component = components.get((binding.record_key, binding.component_key))
        if component is None:
            findings.append(f"{tag}: unknown component")

        # Exact governing prose resolves through the bound release's own
        # authoritative chunk population. A non-empty string is not resolution:
        # a fabricated id, another package's chunk, and a chunk that exists but
        # was never projected into this release all fail here.
        if binding.chunk_id not in corpus.authoritative_chunk_ids:
            findings.append(
                f"{tag}: chunk {binding.chunk_id!r} is not authoritative prose of "
                f"release {corpus.package_uuid}/{corpus.release_version}"
            )
        else:
            findings.extend(_validate_prose_extent(binding, spans_by_id, corpus, tag))

        code = binding.irreducibility_reason_code
        if irreducibility_reason_for(code) is None:
            findings.append(f"{tag}: irreducibility reason {code!r} is not closed")
        elif component is not None and code != component.irreducibility_reason_code:
            # Two independently valid reasons that disagree are a contradiction
            # about *why* this authority is prose-bound. Neither copy wins.
            findings.append(
                f"{tag}: reason {code!r} disagrees with its component's "
                f"{component.irreducibility_reason_code!r}"
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

    findings.extend(_validate_spell_list_membership(draft, record_keys))
    return findings


def _validate_spell_list_membership(
    draft: RepresentationDraft, record_keys: set[str]
) -> list[str]:
    """A spell-list qualifier and its membership edge are one claim.

    The ``Special`` column of a class spell-list table qualifies a membership
    the same table states. Splitting that across a fact and a relationship is
    the right typing — the edge is the classification, the fact is what the
    source says about it — but only if neither half can exist alone. A
    qualifier without its edge would be a claim about a membership the
    projection never declares, and it would silently vanish from any consumer
    that reads the relationship graph.

    ``SPELL_LIST_MEMBER`` also carries a domain claim the other relationship
    kinds do not, so its endpoints are constrained: it means *this class's spell
    list includes this spell*, and a consumer reading it as eligibility to
    prepare or know would be misled by any other pair. A creature or an item on
    either end is not a weaker version of that statement; it is a different one.

    ``SCOPED_WITHIN``, ``GRANTS``, and ``PREREQUISITE`` stay deliberately
    polymorphic — a spell scopes a creature, a level grants a feature, a feat
    requires a species — so nothing here invents endpoint rules for them.

    A membership edge with no qualifier is normal and stays valid: most rows of
    a ``Spell | School | Special`` table say nothing in the ``Special`` column,
    and requiring a qualifier would force one to be invented.
    """
    findings: list[str] = []
    kinds = {r.semantic_key: r.kind for r in draft.records}
    members: set[tuple[str, str]] = set()

    for rel in draft.relationships:
        if rel.kind is not RelationshipKind.SPELL_LIST_MEMBER:
            continue
        members.add((rel.source_record_key, rel.target_record_key))
        tag = (
            f"spell-list membership {rel.source_record_key} -> {rel.target_record_key}"
        )
        source_kind = kinds.get(rel.source_record_key)
        target_kind = kinds.get(rel.target_record_key)
        # A missing endpoint is already reported as an unknown record by the
        # relationship checks above; repeating it here would say it twice.
        if source_kind is not None and source_kind is not RecordKind.CLASS:
            findings.append(
                f"{tag}: source is a {source_kind.value} record; a spell list "
                "belongs to a class"
            )
        if target_kind is not None and target_kind is not RecordKind.SPELL:
            findings.append(
                f"{tag}: target is a {target_kind.value} record; only a spell "
                "can be on a spell list"
            )

    for component in draft.components:
        for fact in component.all_facts():
            if getattr(fact, "FAMILY", None) is not FactFamily.SPELL_LIST_QUALIFIER:
                continue
            target = getattr(fact, "spell_record_key", "")
            tag = (
                f"spell-list qualifier {component.record_key}/"
                f"{component.semantic_key} -> {target}"
            )
            owner_kind = kinds.get(component.record_key)
            if owner_kind is not None and owner_kind is not RecordKind.CLASS:
                # The Special column is a column of the *class's* table, so the
                # qualifier belongs to the class component that states the list.
                findings.append(
                    f"{tag}: qualifier sits on a {owner_kind.value} record; the "
                    "Special column belongs to the class stating the list"
                )
            if target not in record_keys:
                findings.append(f"{tag}: unknown spell record")
                continue
            if kinds.get(target) is not RecordKind.SPELL:
                findings.append(
                    f"{tag}: qualifies a {kinds[target].value} record; a "
                    "spell-list qualifier names a spell"
                )
            if (component.record_key, target) not in members:
                findings.append(
                    f"{tag}: qualifies a membership the projection does not "
                    "declare as a spell_list_member relationship"
                )
    return findings


#: Which provenance roles a span of each disposition may carry.
#:
#: NON_MECHANICAL and UNRESOLVED admit nothing: the accepted classification says
#: this text states no mechanic, so citing it as governing provenance would let
#: licensing, navigation, or flavour text back in as authority through a side
#: door. SUPPORTING_AUTHORITY admits contextual links only — it explains or
#: bounds a mechanic and must never be counted as the primary statement of one.
_ADMISSIBLE_ROLES: dict[SemanticDisposition, frozenset[ProvenanceRole]] = {
    SemanticDisposition.SUBSTANTIVE: frozenset(
        {ProvenanceRole.PRIMARY, ProvenanceRole.CONTEXTUAL}
    ),
    SemanticDisposition.SUPPORTING_AUTHORITY: frozenset({ProvenanceRole.CONTEXTUAL}),
    SemanticDisposition.NON_MECHANICAL: frozenset(),
    SemanticDisposition.UNRESOLVED: frozenset(),
}


def _validate_provenance(
    draft: RepresentationDraft,
    ledger: ClassificationLedger,
    corpus: BoundCorpusSnapshot,
) -> list[str]:
    """Validate provenance as a closed relation, not a one-way check.

    Three obligations, and an edge must satisfy all of them before it counts
    for anything:

    * **forward** — the claim names a declared element and an existing span;
    * **admissible** — the span's accepted disposition permits that role, and a
      prose binding's claim cites text its own chunk actually covers; and
    * **reverse** — every authoritative element carries at least one edge.

    The chunk-locality half is what closes the relation over the 5c projection.
    A prose binding names an exact chunk and a provenance edge names an exact
    span; without joining them, a binding to chunk A could cite a span that
    only ever projected into chunk B, and the candidate would persist governing
    prose that does not contain the text it claims to govern.

    Admissibility is decided *before* an edge joins any coverage set, so an
    inadmissible claim cannot satisfy substantive coverage, supporting linkage,
    or an element's own traceability. An exact duplicate edge is one claim
    recorded twice, not two, and is rejected rather than counted twice.
    """
    findings: list[str] = []
    spans_by_id = {s.span_id: s for s in ledger.spans}
    declared = declared_provenance_targets(draft)
    bindings_by_key = prose_bindings_by_target_key(draft)

    primary_by_span: dict[str, list[tuple[str, ...]]] = {}
    claimed: set[str] = set()
    linked: set[str] = set()
    covered: dict[ProvenanceTargetKind, set[tuple[str, ...]]] = {
        kind: set() for kind in ProvenanceTargetKind
    }
    seen_edges: set[tuple[str, tuple[str, ...], str, str]] = set()

    for claim in draft.provenance:
        tag = f"provenance {claim.target_kind.value}{list(claim.target_key)}"
        edge = (
            claim.target_kind.value,
            claim.target_key,
            claim.span_id,
            claim.role.value,
        )
        if edge in seen_edges:
            findings.append(
                f"{tag}: duplicate provenance edge for span {claim.span_id}"
            )
            continue
        seen_edges.add(edge)

        admissible = True
        if claim.target_key not in declared[claim.target_kind]:
            findings.append(f"{tag}: claim for an undeclared element")
            admissible = False

        span = spans_by_id.get(claim.span_id)
        if span is None:
            findings.append(f"{tag}: unknown span {claim.span_id}")
            continue
        if claim.role not in _ADMISSIBLE_ROLES[span.disposition]:
            findings.append(
                f"{tag}: {claim.role.value} claim on a "
                f"{span.disposition.value} span {claim.span_id}"
            )
            admissible = False

        binding = bindings_by_key.get(claim.target_key)
        if binding is not None and not corpus.covers_span(
            binding.chunk_id, span.leaf_id, span.char_start, span.char_end
        ):
            findings.append(
                f"{tag}: span {claim.span_id} "
                f"[{span.char_start},{span.char_end}) of leaf {span.leaf_id} is not "
                f"covered by bound chunk {binding.chunk_id}"
            )
            admissible = False

        if not admissible:
            continue

        covered[claim.target_kind].add(claim.target_key)
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

    # Reverse obligation. A component claiming the span a fact came from does
    # not make that fact traceable; the element carries its own evidence.
    for kind in PROVENANCE_REQUIRED_KINDS:
        for target in sorted(declared[kind] - covered[kind]):
            findings.append(
                f"{kind.value} {list(target)}: no provenance to a 5c leaf subspan"
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


def validate_representation(
    draft: RepresentationDraft,
    ledger: ClassificationLedger,
    corpus: BoundCorpusSnapshot,
) -> tuple[str, ...]:
    """Return every violation of the keyed representation's internal honesty.

    *corpus* is the resolved snapshot of the bound 5c release — the one source
    of release-scoped truth these validators read, so no validator needs a
    database of its own.
    """
    # The exact-type boundary first, and nothing else if it fails. Every
    # validator below reads fields, builds keys, and dedups through sets and
    # dicts; a subclass with a hostile ``__eq__`` only has to be consulted once
    # to collapse two distinct elements into one, and the finding it should
    # have produced is gone by then. Returning early also keeps the report
    # about the actual defect rather than burying it under downstream noise
    # produced by reading a type we have just refused.
    if drift := representation_draft_violations(draft):
        return tuple(drift)

    findings: list[str] = []
    findings.extend(_validate_records(draft))
    findings.extend(_validate_components(draft))
    findings.extend(_validate_prose_bindings(draft, ledger, corpus))
    findings.extend(_validate_relationships_and_references(draft))
    findings.extend(_validate_provenance(draft, ledger, corpus))
    return tuple(findings)
