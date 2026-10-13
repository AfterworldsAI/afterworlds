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
from afterworlds.ingestion.mechanical.policy import (
    irreducibility_reason_for,
    prose_retention_reason_for,
)
from afterworlds.ingestion.mechanical.representation import (
    PROVENANCE_REQUIRED_KINDS,
    RECORD_OWNED_REFERENCE,
    AmmunitionKind,
    AmmunitionSupplyFact,
    ComponentDraft,
    FactFamily,
    ProseBindingDraft,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordKind,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
    RepresentationDraft,
    UnknownFactFamilyError,
    WeaponProperty,
    WeaponPropertyFact,
    applicability_violations,
    component_damage_composition_violations,
    component_participant_violations,
    component_roll_outcome_violations,
    declared_provenance_targets,
    fact_invariant_violations,
    fact_key,
    fact_qualifier_violations,
    fact_target_key,
    option_set_violations,
    prose_bindings_by_target_key,
    reference_target_key,
    relationship_target_key,
    representation_draft_violations,
)

__all__ = [
    "catalogue_parts",
    "relationship_and_reference_violations",
    "validate_representation",
]

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

        # A component addresses itself by this key everywhere: provenance
        # coordinates, override targets, prose bindings, and a reference's
        # ownership position. A blank one is unaddressable, and since schema 4
        # spells record ownership as the *absence* of a component key, a
        # blank-keyed component would also collide with every record-owned
        # reference coordinate of the same record.
        if not component.semantic_key.strip():
            findings.append(f"{tag}: blank semantic key")

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
            component_damage_composition_violations(
                component.facts, component.options, tag
            )
        )

        findings.extend(
            component_roll_outcome_violations(
                component.facts,
                component.options,
                component.applies_when,
                tag,
                component.fact_qualifiers,
            )
        )

        findings.extend(
            component_participant_violations(
                component.facts,
                component.options,
                component.applies_when,
                tag,
                component.fact_qualifiers,
            )
        )

        # A qualifier must name exactly one fact in its exact scope. Checked
        # here rather than per fact because resolving a qualifier means looking
        # at the component's whole fact population, direct and per-option.
        findings.extend(
            fact_qualifier_violations(
                component.facts, component.options, component.fact_qualifiers, tag
            )
        )

        has_prose = key in bound_prose
        code = component.irreducibility_reason_code
        retention = component.prose_retention_reason_code
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
            if retention is not None:
                findings.append(
                    f"{tag}: structured handling with a prose retention reason"
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
            # A component whose meaning is carried as exact governing prose
            # must say *why*, under a closed catalog, and **exactly one of the
            # two catalogs applies**. Silence is the backlog state PROSE_BOUND
            # must never become; stating both is a component that claims its
            # meaning is irreducible *and* that it is reducible but has no
            # identified structured use, which are contradictory claims about
            # the same passage. Neither may be reported as the other: labelling
            # reducible meaning with an irreducibility code is the relabelling
            # ADR-005d forbids in those words (Owner Decision 2026-09-16).
            stated = [c for c in (code, retention) if c is not None and c.strip()]
            if not stated:
                findings.append(
                    f"{tag}: {handling} handling with no irreducibility reason "
                    "and no prose retention reason"
                )
            elif len(stated) == 2:
                findings.append(
                    f"{tag}: {handling} handling states both an irreducibility "
                    "reason and a prose retention reason; exactly one says why "
                    "this meaning is carried as prose"
                )

        if (
            code is not None
            and code.strip()
            and irreducibility_reason_for(code) is None
        ):
            findings.append(f"{tag}: irreducibility reason {code!r} is not closed")
        if (
            retention is not None
            and retention.strip()
            and prose_retention_reason_for(retention) is None
        ):
            findings.append(
                f"{tag}: prose retention reason {retention!r} is not closed"
            )

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
        elif binding.option_key:
            # Schema 6. An option key that names nothing would make the binding
            # unresolvable at runtime while still reading as scoped, which is
            # worse than an unscoped binding: the prose would silently govern
            # no arm at all rather than every arm.
            tag = f"{tag} option {binding.option_key}"
            if binding.option_key not in {o.semantic_key for o in component.options}:
                findings.append(f"{tag}: names no option of its component")

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
        retention = binding.prose_retention_reason_code
        # The binding half of the component's exactly-one rule, and it is a
        # separate check rather than an inference from the component: a binding
        # may name a component this draft does not carry, and the loop above has
        # already reported that without giving this one anything to compare
        # against.
        stated = [c for c in (code, retention) if c is not None and c.strip()]
        if not stated:
            findings.append(
                f"{tag}: no irreducibility reason and no prose retention reason"
            )
        elif len(stated) == 2:
            findings.append(
                f"{tag}: states both an irreducibility reason and a prose "
                "retention reason; exactly one says why this passage is prose"
            )
        if code is not None and code.strip():
            if irreducibility_reason_for(code) is None:
                findings.append(f"{tag}: irreducibility reason {code!r} is not closed")
            elif component is not None and code != component.irreducibility_reason_code:
                # Two independently valid reasons that disagree are a
                # contradiction about *why* this authority is prose-bound.
                # Neither copy wins.
                findings.append(
                    f"{tag}: reason {code!r} disagrees with its component's "
                    f"{component.irreducibility_reason_code!r}"
                )
        if retention is not None and retention.strip():
            # Compared against the component's *same-kind* code, never across
            # kinds. A binding retained for a reducibility reason under a
            # component that states an irreducibility one is already caught by
            # the exactly-one rules on each side; matching it against the other
            # catalog here would report the same contradiction a second time in
            # terms that name the wrong field.
            if prose_retention_reason_for(retention) is None:
                findings.append(
                    f"{tag}: prose retention reason {retention!r} is not closed"
                )
            elif (
                component is not None
                and retention != component.prose_retention_reason_code
            ):
                findings.append(
                    f"{tag}: retention reason {retention!r} disagrees with its "
                    f"component's {component.prose_retention_reason_code!r}"
                )
    return findings


def catalogue_parts(
    draft: RepresentationDraft,
) -> tuple[dict[tuple[str, str], frozenset[str]], list[str]]:
    """(member, section) -> the member's components that section prints, for
    each member of more than one catalogue; and every finding its edges state.

    One item may be printed in two catalogues under one identity (Owner
    Decision 2026-09-27): the basic Potion of Healing is an *Equipment* gear
    row and the first row of the *Magic Items* family table. Each catalogue
    reads the member's passages it prints, and only those. Which those are is
    declared, never inferred from keys or positions: each edge's
    ``RELATIONSHIP`` provenance cites the span the member's component owns
    (PRIMARY) where that section prints it, so each edge names exactly the
    components owning a span it cites. Every such component is named by
    exactly one edge; one owning no source span is the member's in every
    catalogue. Anything else, and any membership cycle, is refused rather
    than chosen.
    """
    findings: list[str] = []
    sections: dict[str, list[str]] = {}
    for rel in draft.relationships:
        # A self-edge is already refused as a record related to itself.
        if (
            rel.kind is RelationshipKind.CATALOGUE_MEMBER
            and rel.source_record_key != rel.target_record_key
        ):
            sections.setdefault(rel.source_record_key, []).append(rel.target_record_key)

    # A catalogue reaches its members one hop; a cycle would make a record a
    # member of its own member.
    for start in sorted(sections):
        stack, seen = list(sections[start]), set()
        while stack:
            key = stack.pop()
            if key == start:
                findings.append(f"record {start}: a catalogue member of itself")
                break
            if key not in seen:
                seen.add(key)
                stack.extend(sections.get(key, ()))

    shared = {m: s for m, s in sections.items() if len(set(s)) > 1}
    if not shared:
        return {}, findings
    bindings = prose_bindings_by_target_key(draft)
    owner = {
        claim.span_id: (
            bindings[claim.target_key].record_key,
            bindings[claim.target_key].component_key,
        )
        for claim in draft.provenance
        if claim.target_kind is ProvenanceTargetKind.PROSE_BINDING
        and claim.role is ProvenanceRole.PRIMARY
        and claim.target_key in bindings
    }
    cited: dict[tuple[str, ...], list[str]] = {}
    for claim in draft.provenance:
        if claim.target_kind is ProvenanceTargetKind.RELATIONSHIP:
            cited.setdefault(claim.target_key, []).append(claim.span_id)
    owning = {(r, c) for r, c in owner.values()}
    parts: dict[tuple[str, str], frozenset[str]] = {}
    for member, parents in sorted(shared.items()):
        claimed: dict[str, str] = {}
        for section in sorted(set(parents)):
            edge = relationship_target_key(
                RelationshipDraft(member, section, RelationshipKind.CATALOGUE_MEMBER)
            )
            spans = cited.get(edge, [])
            if not spans or any(owner.get(s, ("",))[0] != member for s in spans):
                findings.append(
                    f"record {member}: its catalogue edge to {section} cites no "
                    "span of its own components"
                )
                continue
            keys = {owner[s][1] for s in spans}
            for key in sorted(keys):
                if key in claimed:
                    findings.append(
                        f"record {member}: component {key} is printed by both "
                        f"{claimed[key]} and {section}"
                    )
                claimed.setdefault(key, section)
            parts[(member, section)] = frozenset(keys)
        for key in sorted({c for r, c in owning if r == member} - set(claimed)):
            findings.append(
                f"record {member}: component {key} is printed by none of its "
                f"catalogues {sorted(set(parents))}"
            )
    return parts, findings


def relationship_and_reference_violations(draft: RepresentationDraft) -> list[str]:
    """Every finding one representation's relationships and references state.

    Public because a second seam depends on it. A reference resolution is only
    applicable where the resolved view introduces no finding this function does
    not already report of the accepted view — ambiguity above all — and deciding
    that with a second hand-written scan over the citation coordinates would be
    two definitions of ambiguity that eventually disagree. Named like the other
    cross-module checks (``schema_binding_violations``,
    ``policy_meaning_violations``) rather than like the private validators it
    sits among.
    """
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

    findings.extend(catalogue_parts(draft)[1])

    # A reference is ambiguous when one citation resolves to more than one
    # target. A citation is identified by where it occurs as well as what it
    # says — source record, owning component, printed wording and committed
    # scope, the first four coordinates of ``reference_target_key`` — so two
    # citations of identical wording in one scope are two claims and may
    # resolve differently, or one may stay unresolved (ADR-005d Decision 7 as
    # amended by the Owner's citation-identity decision). Unique destination
    # names alone still never establish intent.
    resolutions: dict[tuple[str, ...], list[ReferenceDraft]] = {}
    class_keys = {r.semantic_key for r in draft.records if r.kind is RecordKind.CLASS}
    # Which citations each record publishes in its own right, and which it
    # publishes through a component. A record may legitimately do either; doing
    # both for one citation is the same source statement published twice —
    # whatever each form's destination, so the target is not part of this key.
    citations: dict[tuple[str, str, str], tuple[set[str], set[str]]] = {}
    for ref in draft.references:
        tag = f"reference {ref.scope_key}:{ref.source_text!r}"
        if ref.from_record_key not in record_keys:
            findings.append(f"{tag}: unknown source record {ref.from_record_key}")
        # Exactly one ownership form, and each is checked against what it
        # claims. A component-owned reference must name a component that really
        # exists in this record — unchanged. A record-owned one names no
        # component at all, so there is nothing to dangle; its owner is the
        # source record, already checked immediately above.
        if (
            ref.from_component_key != RECORD_OWNED_REFERENCE
            and (
                ref.from_record_key,
                ref.from_component_key,
            )
            not in component_keys
        ):
            findings.append(f"{tag}: unknown source component {ref.from_component_key}")
        owners, targets = citations.setdefault(
            (ref.from_record_key, ref.source_text, ref.scope_key), (set(), set())
        )
        owners.add(ref.from_component_key)
        targets.add(ref.target_record_key)
        if not ref.target_record_key:
            findings.append(f"{tag}: unresolved reference")
        elif ref.target_record_key not in record_keys:
            findings.append(f"{tag}: unknown target record {ref.target_record_key}")
        if not ref.scope_key.strip():
            findings.append(f"{tag}: no committed resolution scope")
        findings.extend(_alternative_violations(ref, tag, component_keys, class_keys))
        resolutions.setdefault(reference_target_key(ref)[:4], []).append(ref)

    # Record ownership means *no legitimate component states it*. When a
    # component of the same record does state it, the record-owned form
    # contradicts its own justification and the pair publishes one citation
    # twice — the reference-shaped case of the duplicated-projection defect
    # ADR-005d Decision 5 forbids. Two *components* citing the same wording stay
    # legal: each is its own claim, and each carries its own provenance.
    # The destinations stay in the wording: a resolution that moves either form
    # changes the finding, so the resolution seam's delta still sees it.
    for (record, text, scope), (owners, targets) in sorted(citations.items()):
        if RECORD_OWNED_REFERENCE in owners and len(owners) > 1:
            findings.append(
                f"reference {scope}:{text!r} -> {', '.join(sorted(targets))}: "
                f"record {record} states "
                "it both directly and through "
                f"{sorted(o for o in owners if o != RECORD_OWNED_REFERENCE)}; a "
                "record owns a reference only where no component states it"
            )

    # One citation with several destinations is legal only when every member is
    # labelled (Owner Decisions 2026-10-01). A label names one *route*: its
    # members are read together, in order — the first is where the reader
    # lands, the rest is the text that route needs — so a route's conditions
    # belong to the route, not to one member. Routes are not exclusive; several
    # may apply to one character. An unlabelled pair is still one citation
    # resolving two ways — ambiguous — and a lone labelled destination is a
    # route with nothing to route between.
    for (_, _, text, scope), members in sorted(resolutions.items()):
        targets = {ref.target_record_key for ref in members}
        labels = [ref.alternative_label for ref in members]
        if len(members) == 1:
            if labels[0]:
                findings.append(
                    f"reference {scope}:{text!r}: labelled as an alternative "
                    "but the citation states no other"
                )
            continue
        if not all(labels):
            findings.append(
                f"reference {scope}:{text!r}: ambiguous — resolves to "
                f"{sorted(targets)}"
            )
            continue
        routes: dict[str, set[tuple[object, ...]]] = {}
        for ref in members:
            routes.setdefault(ref.alternative_label, set()).add(
                (ref.situation, ref.class_record_key, ref.minimum_class_level)
            )
        for label, conditions in sorted(routes.items()):
            if len(conditions) > 1:
                findings.append(
                    f"reference {scope}:{text!r}: route {label!r} states "
                    "different conditions for its members"
                )

    findings.extend(_validate_spell_list_membership(draft, record_keys))
    return findings


#: The highest level a class has in the bound release.
_MAX_CLASS_LEVEL = 20


def _alternative_violations(
    ref: ReferenceDraft,
    tag: str,
    component_keys: set[tuple[str, str]],
    class_keys: set[str],
) -> list[str]:
    """What one reference's schema-17 alternative keys fail to state exactly.

    A component destination must exist on the target record — naming one on
    another record is the wrong grain, not a near miss. A class route names a
    class record and a level in that class, never a total character level.
    """
    findings: list[str] = []
    stated = (
        ref.target_component_key
        or ref.alternative_label
        or ref.situation is not None
        or ref.class_record_key
        or ref.minimum_class_level
    )
    if stated and not ref.target_record_key:
        findings.append(f"{tag}: states an alternative destination but no target")
        return findings
    if ref.alternative_label != ref.alternative_label.strip():
        findings.append(f"{tag}: alternative label is not trimmed")
    if (
        ref.target_component_key
        and (ref.target_record_key, ref.target_component_key) not in component_keys
    ):
        findings.append(
            f"{tag}: target component {ref.target_record_key}/"
            f"{ref.target_component_key} does not exist"
        )
    if ref.class_record_key and ref.class_record_key not in class_keys:
        findings.append(f"{tag}: {ref.class_record_key} is not a class record")
    if not 0 <= ref.minimum_class_level <= _MAX_CLASS_LEVEL:
        findings.append(
            f"{tag}: minimum class level {ref.minimum_class_level} is outside "
            f"0-{_MAX_CLASS_LEVEL}"
        )
    elif ref.minimum_class_level and not ref.class_record_key:
        findings.append(f"{tag}: a minimum class level names no class")
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


def _validate_duplicated_fact_authority(
    draft: RepresentationDraft, ledger: ClassificationLedger
) -> list[str]:
    """One source statement may not become two copies of the same authority.

    ADR-005d Decision 5 requires a duplicated-fact projection to fail. The
    per-scope duplicate check above cannot see this case: it compares facts
    *within* one component's scope, so two sibling components each holding an
    equivalent fact are two separate scopes and each looks clean.

    That gap is real and was found by building it. A disjunctive trigger —
    Suffocation's *"When a creature runs out of breath **or** is choking, it
    gains 1 Exhaustion level"* — invites an authoring shape with one component
    per arm, each carrying its own copy of the single stated consequence. The
    whole representation validated, while publishing two accrual claims where
    the source made one. Labelling one provenance edge ``PRIMARY`` and the other
    ``CONTEXTUAL`` is what let it through, and that labelling is itself the
    defect: the consequence clause *states* both facts, so calling it merely
    contextual for one of them is false about where the authority came from.

    **The rule, kept as narrow as the defect.** Two *different* components of one
    record may not hold facts with the same content-derived key when both draw
    that fact from the **same substantive span**. All three conditions are
    required, and each one is load-bearing:

    * **Different components.** Two options of one component are mutually
      exclusive alternatives, not a repeat — the per-scope check already says so,
      and this must not contradict it. Option facts resolve to their owning
      component here, so a choice is never reported.
    * **Equivalent fact, not merely equal family.** Keyed by ``fact_key``, the
      same content-derived key persistence and override targeting use.
    * **Shared substantive span.** The same mechanic stated by two genuinely
      different rules is normal authority, so two components holding an
      equivalent fact from *different* spans is left alone. Cross-record
      duplication is likewise not this rule's business.

    Deliberately **not** global cross-component fact uniqueness, and deliberately
    not derived by reading positions out of a provenance target key: the sites
    are built by walking the declared components, so a key's shape can change
    without silently changing what this rule means. The role on the edge is not
    consulted at all — the duplication is the same defect whichever label it
    wears.
    """
    # Built from the declared components, never parsed back out of target keys.
    sites: dict[tuple[str, ...], tuple[str, str, str]] = {}
    for component in draft.components:
        owner = (component.record_key, component.semantic_key)
        for fact in component.facts:
            try:
                key = fact_key(fact)
            except UnknownFactFamilyError:
                continue
            sites[fact_target_key(*owner, fact)] = (*owner, key)
        for option in component.options:
            for fact in option.facts:
                try:
                    key = fact_key(fact)
                except UnknownFactFamilyError:
                    continue
                sites[fact_target_key(*owner, fact, option.semantic_key)] = (
                    *owner,
                    key,
                )

    substantive = {
        span.span_id
        for span in ledger.spans
        if span.disposition is SemanticDisposition.SUBSTANTIVE
    }
    by_span: dict[str, set[tuple[str, str, str]]] = {}
    for claim in draft.provenance:
        if claim.target_kind is not ProvenanceTargetKind.FACT:
            continue
        if claim.span_id not in substantive:
            continue
        site = sites.get(claim.target_key)
        if site is not None:
            by_span.setdefault(claim.span_id, set()).add(site)

    findings: list[str] = []
    for span_id in sorted(by_span):
        holders: dict[tuple[str, str], set[str]] = {}
        for record_key, component_key, key in by_span[span_id]:
            holders.setdefault((record_key, key), set()).add(component_key)
        for (record_key, key), components in sorted(holders.items()):
            if len(components) > 1:
                findings.append(
                    f"record {record_key}: fact {key} is stated once by span "
                    f"{span_id} but held by sibling components "
                    f"{sorted(components)}; one source statement may not become "
                    "two copies of the same authority"
                )
    return findings


def _validate_ammunition_supplies(draft: RepresentationDraft) -> list[str]:
    """Each narrowed ``ammunition_supply`` names accepted Ammunition weapons of
    its own kind, and no weapon is claimed by two narrowed rows of one kind.

    Schema 20 (CRD Issue 15c C7). Relational, so it lives here rather than in
    the intrinsic invariant manifest: whether a reference resolves, and to
    which weapon-side ammunition, is a property of the rest of the draft.
    """
    weapon_kinds: dict[tuple[str, str], set[AmmunitionKind]] = {}
    supplies: list[tuple[str, AmmunitionSupplyFact]] = []
    components = {(c.record_key, c.semantic_key) for c in draft.components}
    for component in draft.components:
        key = (component.record_key, component.semantic_key)
        facts = (*component.facts, *(f for o in component.options for f in o.facts))
        for fact in facts:
            if (
                type(fact) is WeaponPropertyFact
                and fact.weapon_property is WeaponProperty.AMMUNITION
                and fact.ammunition is not None
            ):
                weapon_kinds.setdefault(key, set()).add(fact.ammunition)
            elif type(fact) is AmmunitionSupplyFact:
                supplies.append((f"component {key[0]}/{key[1]}", fact))

    findings: list[str] = []
    claimed: dict[tuple[AmmunitionKind, tuple[str, str]], str] = {}
    for tag, supply in supplies:
        for ref in supply.for_weapons or ():
            target = (ref.record_key, ref.component_key)
            where = f"{tag}: ammunition_supply names {target[0]}/{target[1]}"
            kinds = weapon_kinds.get(target)
            if target not in components:
                findings.append(f"{where}, which is not a component of this draft")
            elif kinds is None:
                findings.append(f"{where}, which has no Ammunition weapon property")
            elif supply.kind not in kinds:
                findings.append(
                    f"{where}, whose ammunition is {sorted(k.value for k in kinds)}, "
                    f"not {supply.kind.value}"
                )
            other = claimed.setdefault((supply.kind, target), tag)
            if other != tag:
                findings.append(
                    f"{where}, already narrowed to by {other}; two {supply.kind.value} "
                    "rows may not both claim one weapon"
                )
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
    findings.extend(relationship_and_reference_violations(draft))
    findings.extend(_validate_provenance(draft, ledger, corpus))
    findings.extend(_validate_duplicated_fact_authority(draft, ledger))
    findings.extend(_validate_ammunition_supplies(draft))
    return tuple(findings)
