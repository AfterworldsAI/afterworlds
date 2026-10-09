"""Typed override application over the immutable base projection — Decision 10.

The base projection is never modified. Application reads the reconstructed
projection, layers the ordered override state on top of it, and returns a
separate effective view; the ``rp_mech_*`` rows and the projection UUID are
untouched by construction, because nothing here holds a database session.

Existing precedence and operation semantics are preserved exactly as ADR-005d
Decision 10 requires:

* ordering is ascending ``(precedence, override_id)``, the same rule the chunk
  override path applies;
* ``DISABLE`` suppresses an exact target and **stops later applicable
  processing** for that target — mirroring the chunk path's behaviour of
  halting once a disable wins, rather than letting a later replace resurrect
  suppressed authority;
* ``REPLACE`` supplies a complete validated replacement; and
* ``APPEND`` adds a complete typed component or fact, and only where the owning
  schema permits multiplicity.

Every refusal is typed. An override whose target does not exist, whose patch is
outside the closed union, or whose patch is incompatible with the target's own
type raises :class:`OverrideApplicationError`, which the service seam reports as
``INVALID_OVERRIDE`` — never as a skipped override, and never as an effective
view that silently omits a change someone authored.

**Provenance is exact and source-linked.** A base element carries the 5c leaf
subspans that were accepted as its provenance; an override-supplied element
carries the stable identity and origin of the override record that supplied it.
Those are different kinds of authority and the view says which is which rather
than blurring them into one "source" string.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.projection import ProjectionCandidate
from afterworlds.ingestion.mechanical.raw_state import (
    PersistedStateReconstructionError,
)
from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ComponentDraft,
    ComponentOption,
    FactQualifier,
    MechanicalFact,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordKind,
    Recurrence,
    RelationshipKind,
    component_damage_composition_violations,
    component_participant_violations,
    component_roll_outcome_violations,
    fact_key,
    fact_qualifier_target_key,
    fact_target_key,
    option_set_violations,
    prose_binding_target_key,
    relationship_target_key,
)
from afterworlds.ingestion.mechanical.validation import catalogue_parts
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.services.rules_authority.override_set import (
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
)
from afterworlds.services.rules_authority.patches import (
    ComponentAdditionPatch,
    ComponentBody,
    ComponentReplacementPatch,
    DisablePatch,
    FactAdditionPatch,
    FactReplacementPatch,
    InvalidPatchError,
    ProseAdditionPatch,
    ProseReplacementPatch,
    RecordReplacementPatch,
    patch_from_payload,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)

__all__ = [
    "AppliedOverride",
    "AuthoredProse",
    "EffectiveAuthority",
    "EffectiveComponent",
    "EffectiveFact",
    "EffectiveFactQualifier",
    "EffectiveRecord",
    "GoverningProseEntry",
    "OverrideApplicationError",
    "SourceProse",
    "apply_override_set",
]


class OverrideApplicationError(ValueError):
    """Raised when an override cannot be applied to the bound projection."""

    def __init__(self, override_id: str, detail: str) -> None:
        super().__init__(f"override {override_id}: {detail}")
        self.override_id = override_id
        self.detail = detail


@dataclass(frozen=True)
class EffectiveFactQualifier:
    """A fact's applicability limitation, carrying its *own* authority.

    Separate from the fact's provenance on purpose. A fact and the limitation
    on it are usually stated by *different* spans: Grappled's surcharge is one
    clause and the size exception limiting it is another. Merging them into the
    fact's span set would make *"this limitation comes from span Y"*
    indistinguishable from the fact's own accounting, which is why the
    qualifier is addressed by its own
    :attr:`~afterworlds.ingestion.mechanical.representation.ProvenanceTargetKind.FACT_QUALIFIER`
    target rather than sharing the fact's.

    ``span_ids`` is empty exactly when an override supplied the qualifier, in
    which case ``supplied_by_*`` names it — the same convention
    :class:`EffectiveFact` already uses. A qualifier's authorship always
    matches its fact's, because a qualifier only ever arrives with the fact it
    limits: from the base projection, or from a component patch supplying both.
    """

    applies_when: Applicability
    span_ids: tuple[str, ...] = ()
    supplied_by_override_id: str | None = None
    supplied_by_origin: OverrideOriginEnum | None = None


@dataclass(frozen=True)
class EffectiveFact:
    """One typed fact in the effective view, with its exact provenance."""

    fact_key: str
    fact: MechanicalFact
    #: The owning option, when this fact lives inside an exhaustive actor
    #: choice; ``None`` for a fact held directly on the component.
    option_key: str | None = None
    #: 5c leaf subspans accepted as this fact's provenance. Empty exactly when
    #: the fact came from an override rather than from the source corpus.
    span_ids: tuple[str, ...] = ()
    #: The override that supplied this fact, when one did.
    supplied_by_override_id: str | None = None
    supplied_by_origin: OverrideOriginEnum | None = None
    #: This fact's own condition, or ``None`` when it is limited only by its
    #: enclosing component or option. Held on the fact so suppression cannot
    #: leave a qualifier behind: removing the fact removes it by construction.
    qualifier: EffectiveFactQualifier | None = None


@dataclass(frozen=True)
class SourceProse:
    """One accepted governing span of exact 5c source prose.

    ``text`` is resolved later, by the GameMaster view, from the authoritative
    ``RuleChunk`` the service reads by this exact ``chunk_id``; it is ``None``
    here because this type is built before that resolution happens. It is
    never anything but exact 5c text — never a fabricated id, never a
    stand-in for authored text.

    ``char_start``/``char_end`` are the accepted span's half-open offsets into
    that chunk, recorded by the build-time prose binding and proved against the
    bound release there. Resolution slices them, so a component governed by one
    clause of a paragraph returns that clause: the rest of the paragraph is
    other components' authority, or none, and returning it would overstate what
    governs this component. ``span_id`` names the accepted span itself, so a
    reader can tie the passage back to the classification that accepted it.

    ``option_key`` is the arm this passage governs, or ``""`` where it governs
    the component as a whole. Carried through rather than flattened at this
    boundary: ``Help``'s two arms are governed by two different clauses of the
    same paragraph, and a component-grain entry would say each clause governs
    both — false about the arm it does not describe, not merely imprecise.
    Component-wide prose keeps the empty scope, which is what all twenty
    accepted bindings state, so nothing accepted changes shape here.

    ``option_key`` is *not* a fifth identity element: it is content of the
    effective view, and the build-time provenance coordinate that owns identity
    is ``prose_binding_target_key``.
    """

    chunk_id: str
    span_id: str
    char_start: int
    char_end: int
    text: str | None = None
    option_key: str = ""


@dataclass(frozen=True)
class AuthoredProse:
    """One passage of authored governing prose (Owner Decision 2026-08-08).

    A distinct runtime authority layer, not a second copy of 5c source
    authority: ``text`` is exact and already resolved (it came from the
    override's own validated payload, not from a lookup), and its provenance
    is the supplying override's stable identity and origin — never a
    fabricated ``chunk_id``, never 5c span provenance, and never an
    irreducibility claim copied from base-projection authority.
    """

    text: str
    supplied_by_override_id: str
    supplied_by_origin: OverrideOriginEnum


#: Effective governing prose is one of exactly these two kinds. Closed so a
#: consumer switching on kind cannot silently miss a third one appearing later.
GoverningProseEntry = SourceProse | AuthoredProse


@dataclass(frozen=True)
class EffectiveOption:
    """One option of an exhaustive actor choice, in the effective view.

    Kept as its own element rather than folded into the component's facts:
    the options of a choice are **mutually exclusive**, and flattening them
    would publish "you may crawl *and* you may stand up" as simultaneously
    applicable authority. Every consumer that reads facts for adjudication
    must read this boundary too.
    """

    semantic_key: str
    facts: tuple[EffectiveFact, ...]
    applies_when: Applicability | None = None


@dataclass(frozen=True)
class EffectiveComponent:
    """One component of the effective view.

    A component is either a conjunction (``facts``) or an exhaustive actor
    choice (``options``), never both — the projection contract enforces it, and
    consumers may rely on it.
    """

    record_key: str
    semantic_key: str
    handling: ComponentHandling
    irreducibility_reason_code: str | None
    #: Why the source prose is retained when applying its meaning does *not*
    #: require judgement. Schema 12. Carried beside the irreducibility reason
    #: rather than folded into it, because a reader that cannot tell the two
    #: apart reads ``irreducibility_reason_code is None`` as "this component is
    #: structured" — which it meant before schema 12 and does not mean now.
    prose_retention_reason_code: str | None
    facts: tuple[EffectiveFact, ...]
    options: tuple[EffectiveOption, ...] = ()
    applies_when: Applicability | None = None
    #: Exact ordered governing prose: 5c-bound passages in source reading
    #: order, then authored passages in the order overrides resolve in.
    #: Empty for a purely structured component
    #: that has never had authored prose attached to it.
    governing_prose: tuple[GoverningProseEntry, ...] = ()
    #: How often the component's stated effect repeats, when the source states
    #: a cadence. Carried through the effective view rather than dropped at the
    #: projection boundary: a repeating effect read as a one-off is the wrong
    #: rule, and an override that supplies a component is complete, so it
    #: supplies this too.
    recurs: Recurrence | None = None
    span_ids: tuple[str, ...] = ()
    supplied_by_override_id: str | None = None
    supplied_by_origin: OverrideOriginEnum | None = None


@dataclass(frozen=True)
class EffectiveRecord:
    """One record of the effective view."""

    semantic_key: str
    kind: RecordKind
    parent_key: str | None
    components: tuple[EffectiveComponent, ...]
    span_ids: tuple[str, ...] = ()
    supplied_by_override_id: str | None = None
    supplied_by_origin: OverrideOriginEnum | None = None


@dataclass(frozen=True)
class AppliedOverride:
    """Ordered provenance for one entry of the override set.

    ``applied`` is ``False`` for an entry that was reached but had no effect —
    an entry disabled at authoring time, or one whose target an earlier
    ``DISABLE`` already suppressed. Reporting it rather than dropping it is what
    makes the provenance *ordered*: an auditor sees the whole set in the order
    it was resolved, and why each entry did or did not change anything.
    """

    override_id: str
    origin: OverrideOriginEnum
    target: MechanicalTarget
    operation: OverrideOperationEnum
    precedence: int
    apply_order: int
    is_enabled: bool
    payload: dict[str, object]
    applied: bool
    note: str = ""


#: A catalogue section's reading: runs of (record key, component key, indices
#: into that component's governing prose), in source order.
Reading = tuple[tuple[str, str, tuple[int, ...]], ...]


@dataclass(frozen=True)
class EffectiveAuthority:
    """The complete effective mechanical authority of one binding."""

    binding: RulesPackageBinding
    records: tuple[EffectiveRecord, ...]
    applied_overrides: tuple[AppliedOverride, ...]
    #: (section key, member keys in printed order) for every surviving section
    #: with surviving ``CATALOGUE_MEMBER`` entries. A catalogue section's own
    #: record holds only its introduction; this is how a consumer that names the
    #: section still reaches the entries it prints.
    members: tuple[tuple[str, tuple[str, ...]], ...] = ()
    #: (section key, reading) for each section in :attr:`members`: the
    #: section's and its members' passages in source order (Owner Decision
    #: 2026-09-24). Each run is ``(record key, component key, indices)`` into
    #: that component's governing prose; a member printed in two places -- a
    #: table row and a later description -- reads in two runs, and context a
    #: member reads (its table head) is read once, where its owner prints it.
    #: Context whose owner is outside the catalogue (a category rule, another
    #: part's rule) is read once, at the first member reading it.
    readings: tuple[tuple[str, Reading], ...] = ()
    #: (span id, owner record key, owner component key) of every passage a
    #: surviving component reads as context. A view that reads the owner reads
    #: the passage there; one that does not reads it once, at its first reader.
    context_owners: tuple[tuple[str, str, str], ...] = ()


# ---------------------------------------------------------------------------
# Base view assembly
# ---------------------------------------------------------------------------


def _provenance_index(
    candidate: ProjectionCandidate,
) -> dict[tuple[ProvenanceTargetKind, tuple[str, ...]], tuple[str, ...]]:
    """Map each element's provenance key to the spans claimed for it.

    Primary and contextual claims are both retained, in a stable order, because
    a consumer explaining a value needs the text that states it *and* the text
    that limits it. Their distinction is preserved by ordering primary claims
    first rather than by discarding one kind.
    """
    grouped: dict[
        tuple[ProvenanceTargetKind, tuple[str, ...]], list[tuple[int, str]]
    ] = {}
    for claim in candidate.representation.provenance:
        rank = 0 if claim.role is ProvenanceRole.PRIMARY else 1
        grouped.setdefault((claim.target_kind, claim.target_key), []).append(
            (rank, claim.span_id)
        )
    return {
        key: tuple(span for _, span in sorted(set(claims)))
        for key, claims in grouped.items()
    }


def _base_qualifier(
    component: ComponentDraft,
    fact: MechanicalFact,
    option_key: str,
    spans: dict[tuple[ProvenanceTargetKind, tuple[str, ...]], tuple[str, ...]],
) -> EffectiveFactQualifier | None:
    """One base fact's qualifier, with the qualifier's own source spans."""
    applies_when = component.qualifier_for(fact, option_key)
    if applies_when is None:
        return None
    return EffectiveFactQualifier(
        applies_when=applies_when,
        span_ids=spans.get(
            (
                ProvenanceTargetKind.FACT_QUALIFIER,
                fact_qualifier_target_key(
                    component.record_key,
                    component.semantic_key,
                    fact_key(fact),
                    option_key,
                ),
            ),
            (),
        ),
    )


def _base_records(
    candidate: ProjectionCandidate, leaf_order: Mapping[str, int]
) -> dict[str, EffectiveRecord]:
    """Assemble the immutable base projection as an effective view.

    *leaf_order* maps each bound span's 5c leaf to its persisted
    ``occurrence_index`` — the release's global reading order, bound by its
    digests. A component's source passages are read in that order and then by
    offset within the leaf, so a heading stays beside the body it labels. A
    ``chunk_id`` is an opaque identity and says nothing about where a passage
    is printed.

    A record's components are read the same way: each at the printed position
    of the first passage it owns (its ``PRIMARY`` prose binding), so a section
    reads its rules as the source prints them. Context a component also reads
    does not place it -- that passage is its owner's. A component owning no
    passage has no printed position and reads after the placed ones, by key.
    """
    draft = candidate.representation
    spans = _provenance_index(candidate)
    located = {span.span_id: span for span in candidate.classification.spans}
    prose: dict[tuple[str, str], list[SourceProse]] = {}
    for binding in sorted(
        draft.prose_bindings,
        key=lambda b: (
            leaf_order[located[b.span_id].leaf_id],
            located[b.span_id].char_start,
            located[b.span_id].char_end,
            # Two arms of one choice may bind the same extent, which has one
            # printed position; the scope only makes their order deterministic.
            b.option_key,
        ),
    ):
        prose.setdefault((binding.record_key, binding.component_key), []).append(
            SourceProse(
                chunk_id=binding.chunk_id,
                span_id=binding.span_id,
                char_start=binding.chunk_char_start,
                char_end=binding.chunk_char_end,
                option_key=binding.option_key,
            )
        )

    bound = {prose_binding_target_key(b): b for b in draft.prose_bindings}
    printed: dict[tuple[str, str], tuple[int, int]] = {}
    for claim in draft.provenance:
        if (
            claim.target_kind is ProvenanceTargetKind.PROSE_BINDING
            and claim.role is ProvenanceRole.PRIMARY
            and claim.target_key in bound
        ):
            owner = bound[claim.target_key]
            span = located[claim.span_id]
            at = (leaf_order[span.leaf_id], span.char_start)
            key = (owner.record_key, owner.component_key)
            printed[key] = min(printed.get(key, at), at)

    def _reading_order(c: EffectiveComponent) -> tuple[int, int, int, str]:
        at = printed.get((c.record_key, c.semantic_key))
        return (0, *at, c.semantic_key) if at else (1, 0, 0, c.semantic_key)

    components: dict[str, list[EffectiveComponent]] = {}
    for component in draft.components:

        def _effective(
            scoped: tuple[MechanicalFact, ...],
            option_key: str,
            component: ComponentDraft = component,
        ) -> tuple[EffectiveFact, ...]:
            return tuple(
                EffectiveFact(
                    fact_key=fact_key(fact),
                    fact=fact,
                    option_key=option_key or None,
                    # Built by the same function the projection used, so the
                    # two cannot drift: a direct fact keeps its three-element
                    # key and only an option fact carries the fourth.
                    span_ids=spans.get(
                        (
                            ProvenanceTargetKind.FACT,
                            fact_target_key(
                                component.record_key,
                                component.semantic_key,
                                fact,
                                option_key,
                            ),
                        ),
                        (),
                    ),
                    # The qualifier's own spans, keyed by its own target kind.
                    # Same coordinates as the fact, different authority — which
                    # is exactly why the kind separates them.
                    qualifier=_base_qualifier(component, fact, option_key, spans),
                )
                for fact in scoped
            )

        facts = _effective(component.facts, "")
        options = tuple(
            EffectiveOption(
                semantic_key=option.semantic_key,
                facts=_effective(option.facts, option.semantic_key),
                applies_when=option.applies_when,
            )
            for option in component.options
        )
        components.setdefault(component.record_key, []).append(
            EffectiveComponent(
                record_key=component.record_key,
                semantic_key=component.semantic_key,
                handling=component.handling,
                irreducibility_reason_code=component.irreducibility_reason_code,
                prose_retention_reason_code=component.prose_retention_reason_code,
                facts=facts,
                options=options,
                applies_when=component.applies_when,
                recurs=component.recurs,
                governing_prose=tuple(
                    prose.get((component.record_key, component.semantic_key), ())
                ),
                span_ids=spans.get(
                    (
                        ProvenanceTargetKind.COMPONENT,
                        (component.record_key, component.semantic_key),
                    ),
                    (),
                ),
            )
        )

    return {
        record.semantic_key: EffectiveRecord(
            semantic_key=record.semantic_key,
            kind=record.kind,
            parent_key=record.parent_key,
            components=tuple(
                sorted(components.get(record.semantic_key, []), key=_reading_order)
            ),
            span_ids=spans.get(
                (ProvenanceTargetKind.RECORD, (record.semantic_key,)), ()
            ),
        )
        for record in draft.records
    }


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


def _component_from_body(
    body: ComponentBody,
    record_key: str,
    semantic_key: str,
    entry: EffectiveOverrideEntry,
) -> EffectiveComponent:
    #: Qualifiers by the exact scope they address, so a body's qualifier for
    #: one option's fact can never attach to an identical fact in another arm.
    #: A patch body reaches here already parsed, so its coordinates are
    #: strings — but this dict is keyed by them, and a malformed pair would
    #: raise while building it rather than being refused as a patch. Filtering
    #: keeps the same rule the representation applies: an invalid coordinate is
    #: never consumed by code that assumes a valid one.
    supplied_qualifiers = {
        (q.option_key, q.fact_key): q.applies_when
        for q in body.fact_qualifiers
        if type(q.fact_key) is str and type(q.option_key) is str
    }

    def _supplied(
        facts: tuple[MechanicalFact, ...], option_key: str | None
    ) -> tuple[EffectiveFact, ...]:
        return tuple(
            EffectiveFact(
                fact_key=fact_key(f),
                fact=f,
                option_key=option_key,
                supplied_by_override_id=entry.override_id,
                supplied_by_origin=entry.origin,
                # Complete like every other field of a component patch: a
                # qualifier the body omits is genuinely absent, never inherited
                # from the component being replaced. It is override authority,
                # so it names 5c spans nowhere.
                qualifier=(
                    EffectiveFactQualifier(
                        applies_when=applies_when,
                        supplied_by_override_id=entry.override_id,
                        supplied_by_origin=entry.origin,
                    )
                    if (
                        applies_when := supplied_qualifiers.get(
                            (option_key or "", fact_key(f))
                        )
                    )
                    is not None
                    else None
                ),
            )
            for f in facts
        )

    return EffectiveComponent(
        record_key=record_key,
        semantic_key=semantic_key,
        handling=body.handling,
        # Neither reason. Both answer "why is the *source* prose retained",
        # and an override-supplied component has no source prose: its
        # authority is the authored patch, which names its own override id.
        irreducibility_reason_code=None,
        prose_retention_reason_code=None,
        facts=_supplied(body.facts, None),
        # Built fresh rather than by replacing the base component, so a
        # replacement that omits these fields genuinely removes the qualifier
        # and option set the base projection carried instead of inheriting
        # stale state. Component replacement is complete by contract.
        applies_when=body.applies_when,
        options=tuple(
            EffectiveOption(
                semantic_key=option.semantic_key,
                # An option's facts are override-supplied authority exactly as
                # direct facts are, so each carries the supplying override's
                # identity and origin and names 5c spans nowhere.
                facts=_supplied(option.facts, option.semantic_key),
                applies_when=option.applies_when,
            )
            for option in body.options
        ),
        recurs=body.recurs,
        governing_prose=(
            (
                AuthoredProse(
                    text=body.authored_prose,
                    supplied_by_override_id=entry.override_id,
                    supplied_by_origin=entry.origin,
                ),
            )
            if body.authored_prose is not None
            else ()
        ),
        supplied_by_override_id=entry.override_id,
        supplied_by_origin=entry.origin,
    )


def _find_component(
    record: EffectiveRecord, key: str
) -> tuple[int, EffectiveComponent] | None:
    for index, component in enumerate(record.components):
        if component.semantic_key == key:
            return index, component
    return None


def _find_fact(
    component: EffectiveComponent, key: str, option_key: str | None = None
) -> tuple[int, EffectiveFact] | None:
    """Locate a fact within its own scope.

    ``option_key`` is ``None`` for the component's direct facts and names an
    option otherwise. The scopes are searched separately on purpose: the same
    fact may legitimately appear in two options, and a scope-blind lookup would
    resolve a target for one of them onto the other.
    """
    scoped = (
        component.facts
        if option_key is None
        else next(
            (o.facts for o in component.options if o.semantic_key == option_key), ()
        )
    )
    for index, fact in enumerate(scoped):
        if fact.fact_key == key:
            return index, fact
    return None


def component_published_facts(
    component: EffectiveComponent,
) -> tuple[EffectiveFact, ...]:
    """Every fact the component publishes, direct and per-option.

    For counting and family recognition only. This **loses** mutual
    exclusivity, so it must never reach a consumer that presents facts as
    simultaneously applicable — the GameMaster view builds from ``facts`` and
    ``options`` separately for exactly that reason.
    """
    return (*component.facts, *(f for o in component.options for f in o.facts))


def _suppressed_by(
    target: MechanicalTarget,
    disabled_records: set[str],
    disabled_components: set[tuple[str, str]],
    disabled_facts: set[tuple[str, str, str, str]],
    disabled_prose: set[tuple[str, str]],
) -> str | None:
    """Is this target already suppressed by an earlier ``DISABLE``?

    Suppression is inherited downward: disabling a record disables the
    components, facts, and prose beneath it, so a later override aimed at one
    of them has nothing to change. That is the existing precedence rule — the
    first winning disable stops later processing of that target — applied to
    the record/component/fact/prose hierarchy the chunk path never had.

    Prose and facts are siblings under a component, not one nested inside the
    other: disabling a component's prose does not suppress its facts, and
    disabling a fact does not touch its prose. Only a component- or
    record-level ``DISABLE`` reaches both.
    """
    if target.record_key in disabled_records:
        return "record"
    if target.kind is MechanicalTargetKind.RECORD:
        return None
    assert target.component_key is not None
    if (target.record_key, target.component_key) in disabled_components:
        return "component"
    if target.kind is MechanicalTargetKind.COMPONENT:
        return None
    if target.kind is MechanicalTargetKind.PROSE:
        if (target.record_key, target.component_key) in disabled_prose:
            return "prose"
        return None
    if target.kind is MechanicalTargetKind.OPTION:
        # An option target names the container, not a fact, so no individual
        # fact disable suppresses it — but the record and component disables
        # above already did, which is the whole inheritance it participates in.
        # Appending into an option of a suppressed component would resurrect
        # authority the disable removed.
        return None
    assert target.kind is MechanicalTargetKind.FACT
    assert target.fact_key is not None
    if (
        target.record_key,
        target.component_key,
        target.fact_key,
        target.option_key or "",
    ) in disabled_facts:
        return "fact"
    return None


def _finalize_component(
    record: EffectiveRecord,
    component: EffectiveComponent,
    disabled_facts: set[tuple[str, str, str, str]],
) -> EffectiveComponent:
    """Filter disabled facts and derive final effective handling from what
    survives — unconditionally, for every component, from its own final
    ``facts``/``governing_prose`` (Owner Decision 2026-08-09, generalized).
    This is the single derivation seam: nothing upstream sets ``handling`` for
    a component a prose or fact operation touched, so there is no tracking
    set whose membership could go stale if a semantic key is later
    reincarnated by a replacement, and the result cannot depend on which
    override family supplied the authority or which operation resolved last.

    A component with neither surviving facts nor surviving prose is not
    content-bearing; this derivation does not invent a policy for that
    unrelated state and leaves ``handling`` exactly as declared — by the base
    projection, or by whichever REPLACE/APPEND most recently (re)created this
    component version. That declared value is never mutated mid-resolution by
    any prose or fact operation (only by a component/record replacement
    actually re-declaring it), so this fallback is itself order-independent
    between a fact ``DISABLE`` and a prose ``DISABLE`` racing to empty the
    same component out.
    """
    facts = tuple(
        fact
        for fact in component.facts
        if (record.semantic_key, component.semantic_key, fact.fact_key, "")
        not in disabled_facts
    )
    # Suppression reaches inside a choice: disabling a record or a component
    # disables the facts beneath it wherever they live, and an option's facts
    # are beneath it exactly as direct facts are.
    options = tuple(
        replace(
            option,
            facts=tuple(
                fact
                for fact in option.facts
                if (
                    record.semantic_key,
                    component.semantic_key,
                    fact.fact_key,
                    option.semantic_key,
                )
                not in disabled_facts
            ),
        )
        for option in component.options
    )
    facts_present = bool(facts) or any(o.facts for o in options)
    prose_present = bool(component.governing_prose)
    if facts_present and prose_present:
        handling = ComponentHandling.MIXED
    elif facts_present:
        handling = ComponentHandling.STRUCTURED
    elif prose_present:
        handling = ComponentHandling.PROSE_BOUND
    else:
        handling = component.handling
    # Both retention reasons, cleared together: each explains why *prose* is
    # retained, and a component that ends up STRUCTURED retains none.
    structured = handling is ComponentHandling.STRUCTURED
    reason = None if structured else component.irreducibility_reason_code
    retention = None if structured else component.prose_retention_reason_code
    return replace(
        component,
        facts=facts,
        # The rebuilt options, not the originals: they are what ``facts_present``
        # was derived from, and returning the unfiltered ones would leave a
        # disabled option fact visible in the assembled projection while the
        # handling above already accounted for its removal.
        options=options,
        handling=handling,
        irreducibility_reason_code=reason,
        prose_retention_reason_code=retention,
    )


def apply_override_set(
    candidate: ProjectionCandidate,
    override_set: EffectiveOverrideSet,
    binding: RulesPackageBinding,
    *,
    leaf_order: Mapping[str, int],
) -> EffectiveAuthority:
    """Layer *override_set* over the reconstructed base projection.

    *leaf_order* is the bound release's reading order for the leaves the
    projection's prose bindings cite (see :func:`_base_records`). Required, so
    no caller can fall back to presenting source passages in identity order.

    Raises :class:`OverrideApplicationError` for any override that cannot be
    applied. The caller turns that into ``INVALID_OVERRIDE``; nothing here
    degrades a failure into a partially applied view, because a view missing one
    authored change is indistinguishable from one where that change was never
    authored.
    """
    records = _base_records(candidate, leaf_order)
    disabled_records: set[str] = set()
    disabled_components: set[tuple[str, str]] = set()
    disabled_facts: set[tuple[str, str, str, str]] = set()
    disabled_prose: set[tuple[str, str]] = set()
    provenance: list[AppliedOverride] = []

    for entry in override_set.entries:
        note = ""
        applied = False
        if entry.is_enabled:
            applied, note = _apply_entry(
                entry,
                records,
                disabled_records,
                disabled_components,
                disabled_facts,
                disabled_prose,
            )
        else:
            note = "authored disabled"
        provenance.append(
            AppliedOverride(
                override_id=entry.override_id,
                origin=entry.origin,
                target=entry.target,
                operation=entry.operation,
                precedence=entry.precedence,
                apply_order=entry.apply_order,
                is_enabled=entry.is_enabled,
                payload=entry.payload,
                applied=applied,
                note=note,
            )
        )

    surviving = tuple(
        replace(
            record,
            components=tuple(
                _finalize_component(record, component, disabled_facts)
                for component in record.components
                if (record.semantic_key, component.semantic_key)
                not in disabled_components
            ),
        )
        for key, record in sorted(records.items())
        if key not in disabled_records
    )
    owners = _owners(candidate)
    surviving = _without_suppressed_context(surviving, owners)
    _verify_final_option_sets(surviving, provenance)
    _verify_final_participant_rules(surviving, provenance)
    grouped = _members(candidate, records, disabled_records, leaf_order)
    parts, stale = catalogue_parts(candidate.representation)
    if stale:
        raise PersistedStateReconstructionError("; ".join(stale))
    return EffectiveAuthority(
        binding=binding,
        records=surviving,
        applied_overrides=tuple(provenance),
        members=tuple(
            (section, tuple(member for _, member in found))
            for section, found in grouped.items()
        ),
        readings=_readings(candidate, surviving, grouped, owners, leaf_order, parts),
        context_owners=tuple(
            sorted(
                {
                    (entry.span_id, *owners[entry.span_id])
                    for record in surviving
                    for component in record.components
                    for entry in component.governing_prose
                    if isinstance(entry, SourceProse)
                    and entry.span_id in owners
                    and owners[entry.span_id]
                    != (record.semantic_key, component.semantic_key)
                }
            )
        ),
    )


def _members(
    candidate: ProjectionCandidate,
    records: Mapping[str, EffectiveRecord],
    disabled_records: set[str],
    leaf_order: Mapping[str, int],
) -> dict[str, list[tuple[tuple[int, int], str]]]:
    """Each catalogue section's surviving members, placed and in printed order.

    Read only from the projection's explicit ``CATALOGUE_MEMBER`` edges, never
    from key prefixes and never from another relationship kind: a
    ``SCOPED_WITHIN`` edge states containment and is not a catalogue. A member
    or section an override disabled is left out, so membership cannot
    resurrect suppressed authority.

    Each member is placed by its own edge's provenance -- the member's first
    reviewed clause -- so a member needs no prose binding to be ordered. An
    edge naming a record the projection does not hold, or with no classified
    span to place it by, is persisted state that no longer describes one
    authority, and fails as reconstruction.
    """
    located = {span.span_id: span for span in candidate.classification.spans}
    cited: dict[tuple[str, ...], list[str]] = {}
    for claim in candidate.representation.provenance:
        if claim.target_kind is ProvenanceTargetKind.RELATIONSHIP:
            cited.setdefault(claim.target_key, []).append(claim.span_id)

    grouped: dict[str, list[tuple[tuple[int, int], str]]] = {}
    for rel in candidate.representation.relationships:
        if rel.kind is not RelationshipKind.CATALOGUE_MEMBER:
            continue
        member, section = rel.source_record_key, rel.target_record_key
        for key in (member, section):
            if key not in records:
                raise PersistedStateReconstructionError(
                    f"{member} is a catalogue member of {section}, but the "
                    f"projection holds no record {key}"
                )
        spans = [located.get(s) for s in cited.get(relationship_target_key(rel), ())]
        if not spans or None in spans:
            raise PersistedStateReconstructionError(
                f"catalogue member {member} of {section} has no classified "
                "provenance span to place it by"
            )
        if member in disabled_records or section in disabled_records:
            continue
        at = min((leaf_order[s.leaf_id], s.char_start) for s in spans if s)
        grouped.setdefault(section, []).append((at, member))
    return {section: sorted(found) for section, found in sorted(grouped.items())}


def _owners(candidate: ProjectionCandidate) -> dict[str, tuple[str, str]]:
    """The (record, component) whose prose binding claims each span as primary."""
    bound = {
        prose_binding_target_key(b): (b.record_key, b.component_key)
        for b in candidate.representation.prose_bindings
    }
    return {
        claim.span_id: bound[claim.target_key]
        for claim in candidate.representation.provenance
        if claim.target_kind is ProvenanceTargetKind.PROSE_BINDING
        and claim.role is ProvenanceRole.PRIMARY
        and claim.target_key in bound
    }


def _without_suppressed_context(
    surviving: tuple[EffectiveRecord, ...], owners: Mapping[str, tuple[str, str]]
) -> tuple[EffectiveRecord, ...]:
    """Drop context whose owner no longer reads it.

    A passage another component reads as context -- a row's table head -- is
    its owner's authority. Once an override disables or replaces the owner's
    reading of it, no other component brings it back: suppression is of the
    passage, however it is reached.
    """
    kept = {
        (record.semantic_key, component.semantic_key, entry.span_id)
        for record in surviving
        for component in record.components
        for entry in component.governing_prose
        if isinstance(entry, SourceProse)
    }
    suppressed = {span for span, (r, c) in owners.items() if (r, c, span) not in kept}
    return tuple(
        replace(
            record,
            components=tuple(
                replace(
                    component,
                    governing_prose=tuple(
                        entry
                        for entry in component.governing_prose
                        if not (
                            isinstance(entry, SourceProse)
                            and entry.span_id in suppressed
                        )
                    ),
                )
                for component in record.components
            ),
        )
        for record in surviving
    )


#: Sort order of a placed passage: (unplaced tier, leaf, offset, record,
#: component, index into the component's governing prose).
_Order = tuple[int, int, int, str, str, int]


def _readings(
    candidate: ProjectionCandidate,
    surviving: tuple[EffectiveRecord, ...],
    grouped: Mapping[str, list[tuple[tuple[int, int], str]]],
    owners: Mapping[str, tuple[str, str]],
    leaf_order: Mapping[str, int],
    parts: Mapping[tuple[str, str], frozenset[str]],
) -> tuple[tuple[str, Reading], ...]:
    """Each catalogue section read in source order, its members interleaved.

    Every passage the section or a surviving member owns is placed at its own
    printed position, and consecutive passages of one component form a run. So
    a member row reads between the rows around it, and an item printed twice --
    its table row and its later description -- reads in two runs, each where it
    is printed. Context a member reads (its table head and group row) is not
    placed when its owner is the section or a member: that owner reads it once,
    where it is printed, and a direct read of the member still carries it.
    Context owned outside the catalogue has no place in it, so it is read once,
    at the first component reading it, immediately ahead of the passage it
    precedes there -- the section's own included, since Owner Decision
    2026-09-27 makes an item's family table a catalogue; a view also reading
    the owner reads it there instead (see
    :attr:`EffectiveAuthority.context_owners`). An authored passage has no
    printed position: it reads after the passage it follows in its component
    or, with none, at the member's own position (its ``CATALOGUE_MEMBER``
    edge); a section's
    component with no placed passage reads after the placed ones, by key.
    """
    located = {span.span_id: span for span in candidate.classification.spans}
    by_key = {record.semantic_key: record for record in surviving}
    printed = {(m, k) for (m, _), keys in parts.items() for k in keys}
    out: list[tuple[str, Reading]] = []
    for section, found in grouped.items():
        anchors = {section: (1, 0, 0), **{m: (0, *at) for at, m in found}}
        # A member's parts printed by another member of this catalogue -- an
        # Equipment item's rows in an item family's table -- are read where
        # that member prints them, as the family reads them: its authority,
        # replaced as replaced. One hop, and only the parts declared.
        via: dict[str, str] = {}
        for _, member in found:
            for where, inner in grouped.get(member, ()):
                if (inner, member) in parts and inner not in anchors:
                    anchors[inner], via[inner] = (0, *where), member

        def here(
            record_key: str,
            key: str,
            section: str = section,
            via: Mapping[str, str] = via,
        ) -> bool:
            """Whether this catalogue prints the component (Owner Decision
            2026-09-27): a member of more than one catalogue is read in each
            only through the components *parts* declares that catalogue
            prints (:func:`~afterworlds.ingestion.mechanical.validation.
            catalogue_parts`) and any owning no source span, so its
            appearance in another is not pulled into this one. Read through
            a member, it is read only through the parts that member prints."""
            if record_key in via:
                return key in parts[(record_key, via[record_key])]
            return (record_key, key) not in printed or key in parts.get(
                (record_key, section), ()
            )

        placed: list[_Order] = []
        outside: set[str] = set()  # context owned elsewhere, placed once
        for record_key, anchor in anchors.items():
            for component in by_key[record_key].components:
                key = component.semantic_key
                if not here(record_key, key):
                    continue
                at, first = anchor, len(placed)
                ahead: list[int] = []  # outside context, read before what follows
                for i, entry in enumerate(component.governing_prose):
                    if isinstance(entry, SourceProse):
                        owner = owners.get(entry.span_id)
                        if owner != (record_key, key):
                            # Context: an owner the catalogue reads reads it in
                            # place; any other's is read here, once.
                            if (
                                owner is None
                                or (owner[0] in anchors and here(*owner))
                                or entry.span_id in outside
                            ):
                                continue
                            outside.add(entry.span_id)
                            ahead.append(i)
                            continue
                        span = located[entry.span_id]
                        at = (0, leaf_order[span.leaf_id], span.char_start)
                    placed.extend((*at, record_key, key, j) for j in ahead)
                    ahead.clear()
                    placed.append((*at, record_key, key, i))
                placed.extend((*at, record_key, key, j) for j in ahead)
                if len(placed) == first:  # nothing to read, still its facts
                    placed.append((*anchor, record_key, key, -1))
        runs: list[tuple[str, str, list[int]]] = []
        for *_, record_key, key, i in sorted(placed):
            if not runs or runs[-1][:2] != (record_key, key):
                runs.append((record_key, key, []))
            if i >= 0:
                runs[-1][2].append(i)
        out.append((section, tuple((r, c, tuple(ix)) for r, c, ix in runs)))
    return tuple(out)


def _blame_for(
    record_key: str, component_key: str, provenance: list[AppliedOverride]
) -> str:
    """Which override to name for a *final-state* violation.

    There is no single culprit for an invariant that only fails once the whole
    ordered set has been applied — an earlier entry may have created the shape
    a later one completed. The last applied override that touched this
    component is the one whose application produced the invalid state, so it is
    the honest anchor for the report; the detail string says so, rather than
    implying it is the only cause.
    """
    touched = [
        o
        for o in provenance
        if o.applied
        and o.target.record_key == record_key
        and o.target.component_key == component_key
    ]
    if touched:
        return touched[-1].override_id
    applied = [o for o in provenance if o.applied]
    return applied[-1].override_id if applied else "?"


def _verify_final_option_sets(
    records: tuple[EffectiveRecord, ...], provenance: list[AppliedOverride]
) -> None:
    """Every surviving component must still satisfy the choice contract.

    The local checks inside the fact operations are per-scope: an append or a
    replacement inside one option sees only that option's facts, and a
    fact-scoped ``DISABLE`` is not resolved into removal until
    ``_finalize_component``. None of them can see that two arms have become
    indistinguishable, or that an arm has been emptied — component-wide
    properties of the *final* state.

    Checked here, after the whole ordered set has been applied and suppression
    resolved, so an intermediate shape a later entry legitimately repairs is
    never rejected. A violation fails the entire application through the
    established ``INVALID_OVERRIDE`` path: a view missing one authored change,
    or publishing a choice whose arms cannot be told apart, is worse than no
    view at all.

    The rule itself is
    :func:`~afterworlds.ingestion.mechanical.representation.option_set_violations`
    — the same one the corpus is built under. The effective view is projected
    back into the representation's own types to ask it, which deliberately
    discards provenance: the contract is about what the facts *say*, not about
    which override supplied them.
    """
    for record in records:
        for component in record.components:
            options = tuple(
                ComponentOption(
                    semantic_key=option.semantic_key,
                    facts=tuple(f.fact for f in option.facts),
                    applies_when=option.applies_when,
                )
                for option in component.options
            )
            tag = f"component {record.semantic_key}/{component.semantic_key}"
            # Schema 5. A component's damage composition is a property of the
            # *final* state exactly as its option set is, so an override set
            # that leaves a per-interval damage beside a damage scaling is
            # refused here through the same established path. Asked of every
            # component, not only one with options.
            direct = tuple(f.fact for f in component.facts)
            if outcome := component_roll_outcome_violations(
                direct,
                options,
                component.applies_when,
                tag,
                _effective_qualifiers(component),
            ):
                raise OverrideApplicationError(
                    _blame_for(record.semantic_key, component.semantic_key, provenance),
                    "the applied override set leaves a roll-outcome condition "
                    "with no uniquely established roll (reported against the "
                    f"last override to touch it): {'; '.join(outcome)}",
                )
            if composition := component_damage_composition_violations(
                direct, options, tag
            ):
                raise OverrideApplicationError(
                    _blame_for(record.semantic_key, component.semantic_key, provenance),
                    "the applied override set leaves an ambiguous damage "
                    "composition (reported against the last override to touch "
                    f"it): {'; '.join(composition)}",
                )
            if not component.options:
                continue
            violations = option_set_violations(
                tuple(f.fact for f in component.facts),
                options,
                tag,
            )
            if violations:
                raise OverrideApplicationError(
                    _blame_for(record.semantic_key, component.semantic_key, provenance),
                    "the applied override set leaves an invalid actor choice "
                    f"(reported against the last override to touch it): "
                    f"{'; '.join(violations)}",
                )


def _effective_qualifiers(component: EffectiveComponent) -> tuple[FactQualifier, ...]:
    """The component's per-fact conditions, projected back into draft types.

    The effective view holds a qualifier on its fact; the representation rule
    reads them as a component-level set. Converting here keeps the rule itself
    single-sourced rather than growing a second effective-view spelling of it.
    """
    return (
        *(
            FactQualifier(
                fact_key=f.fact_key,
                option_key="",
                applies_when=f.qualifier.applies_when,
            )
            for f in component.facts
            if f.qualifier is not None
        ),
        *(
            FactQualifier(
                fact_key=f.fact_key,
                option_key=option.semantic_key,
                applies_when=f.qualifier.applies_when,
            )
            for option in component.options
            for f in option.facts
            if f.qualifier is not None
        ),
    )


def _verify_final_participant_rules(
    records: tuple[EffectiveRecord, ...], provenance: list[AppliedOverride]
) -> None:
    """Every surviving component must still establish the counterparts it names.

    The sibling of :func:`_verify_final_option_sets`, and it exists for exactly
    the same reason. ``COUNTERPART`` is only meaningful where a closed
    structure in the same component establishes the binary relation, and no
    per-scope operation can see whether that relation survives: a complete
    component patch supplies its own facts without seeing what it replaced, and
    a fact-scoped ``DISABLE`` is not resolved into removal until
    ``_finalize_component``. Two ways an ordered set could otherwise publish
    what the base schema refuses:

    * a ``REPLACE``/``APPEND`` introducing a ``COUNTERPART``-paid cost, or a
      counterpart-bearing size test, into a component that establishes nothing;
    * a ``DISABLE``/``REPLACE`` removing the sole
      :class:`~afterworlds.ingestion.mechanical.representation.MovementTransportFact`
      while counterpart-bearing authority survives beside it.

    Both leave a claim about a creature the typed structure can no longer name
    — the "some other entity in the prose" failure the role exists to prevent.

    Checked after the whole ordered set has been applied and suppression
    resolved, so an intermediate shape a later entry legitimately repairs is
    never rejected, and failing through the established ``INVALID_OVERRIDE``
    path. The rule itself is
    :func:`~afterworlds.ingestion.mechanical.representation.component_participant_violations`
    — the same one the corpus is built under, asked of the effective view
    projected back into the representation's own types. It is not restated
    here, because a second copy would drift from the schema it is enforcing.
    """
    for record in records:
        for component in record.components:
            violations = component_participant_violations(
                tuple(f.fact for f in component.facts),
                tuple(
                    ComponentOption(
                        semantic_key=option.semantic_key,
                        facts=tuple(f.fact for f in option.facts),
                        applies_when=option.applies_when,
                    )
                    for option in component.options
                ),
                component.applies_when,
                f"component {record.semantic_key}/{component.semantic_key}",
                # A qualifier can name the counterpart too, so the final state
                # has to be asked about it as well — otherwise an override
                # could introduce a counterpart-bearing limitation into a
                # component that establishes nothing.
                _effective_qualifiers(component),
            )
            if violations:
                raise OverrideApplicationError(
                    _blame_for(record.semantic_key, component.semantic_key, provenance),
                    "the applied override set leaves a counterpart reference "
                    "nothing establishes (reported against the last override to "
                    f"touch it): {'; '.join(violations)}",
                )


def _apply_prose_entry(
    entry: EffectiveOverrideEntry,
    patch: DisablePatch | ProseReplacementPatch | ProseAdditionPatch,
    target: MechanicalTarget,
    record: EffectiveRecord,
    records: dict[str, EffectiveRecord],
    disabled_prose: set[tuple[str, str]],
) -> tuple[bool, str]:
    """Apply one entry targeting prose authority (Owner Decision 2026-08-08).

    Prose is a sibling of a component's typed facts, never nested inside their
    application: this never touches ``facts`` or ``handling`` — those are
    derived exactly once, at final assembly, from each component's own final
    ``facts`` and ``governing_prose`` (``_finalize_component``, Owner Decision
    2026-08-09, generalized), the same way regardless of which override
    family supplied the authority or what order it resolved in. Leaving
    ``handling`` alone here also keeps ``_apply_entry``'s ``FactAdditionPatch``
    refusal reading the component's actual *declared* handling, as it did
    before this overlay existed, rather than a value a prose operation
    computed mid-sequence.

    The two retention reasons are the fields this does touch, and only on
    ``REPLACE``: that operation discards every prior governing-prose entry
    — source or authored — for exactly one new authored passage, so a reason
    the base corpus recorded to justify the now-discarded *source* prose's
    irreducibility can no longer honestly describe what governs this
    component. Carrying it forward would present authored-only authority
    under a source-derived irreducibility claim, which ADR-005d forbids the
    same way it forbids a fabricated ``chunk_id`` or copied span provenance.
    ``prose_retention_reason_code`` is cleared by the same sentence, word for
    word: it too justifies the *source* prose ``REPLACE`` just discarded, and
    schema 12 states exactly one of the two, so clearing one and keeping the
    other would leave the component claiming its authored passage is retained
    for a reason nobody reviewed it against.
    ``APPEND`` and ``DISABLE`` leave them untouched: ``APPEND`` only adds to
    existing governing prose, so any source prose the reason describes
    remains effective; ``DISABLE``'s reason-preserving behavior for a
    now-empty ``PROSE_BOUND`` component is the already-settled exception
    Decision 10 names and is unchanged by this fix.
    """
    assert target.component_key is not None
    found = _find_component(record, target.component_key)
    if found is None:
        raise OverrideApplicationError(
            entry.override_id,
            f"target {target.describe()} names no component of {target.record_key!r}",
        )
    index, component = found
    components = list(record.components)

    if isinstance(patch, DisablePatch):
        disabled_prose.add((target.record_key, target.component_key))
        components[index] = replace(component, governing_prose=())
        records[target.record_key] = replace(record, components=tuple(components))
        return True, "prose suppressed"

    authored = AuthoredProse(
        text=patch.text,
        supplied_by_override_id=entry.override_id,
        supplied_by_origin=entry.origin,
    )
    if isinstance(patch, ProseReplacementPatch):
        components[index] = replace(
            component,
            governing_prose=(authored,),
            irreducibility_reason_code=None,
            prose_retention_reason_code=None,
        )
        records[target.record_key] = replace(record, components=tuple(components))
        return True, "prose replaced"

    assert isinstance(patch, ProseAdditionPatch)
    governing_prose = (*component.governing_prose, authored)
    components[index] = replace(component, governing_prose=governing_prose)
    records[target.record_key] = replace(record, components=tuple(components))
    return True, "prose appended"


def _apply_entry(
    entry: EffectiveOverrideEntry,
    records: dict[str, EffectiveRecord],
    disabled_records: set[str],
    disabled_components: set[tuple[str, str]],
    disabled_facts: set[tuple[str, str, str, str]],
    disabled_prose: set[tuple[str, str]],
) -> tuple[bool, str]:
    """Apply one enabled entry, returning whether it changed anything."""
    target = entry.target
    try:
        patch = patch_from_payload(
            entry.payload, operation=entry.operation, target=target
        )
    except InvalidPatchError as exc:
        raise OverrideApplicationError(entry.override_id, str(exc)) from exc

    record = records.get(target.record_key)
    if record is None:
        raise OverrideApplicationError(
            entry.override_id,
            f"target {target.describe()} names no record in the bound projection",
        )

    suppressed = _suppressed_by(
        target, disabled_records, disabled_components, disabled_facts, disabled_prose
    )
    if suppressed is not None:
        return False, f"target already suppressed by an earlier {suppressed} disable"

    if target.kind is MechanicalTargetKind.PROSE:
        # required_patch_family guarantees only these three families pair with
        # a PROSE target; narrowed explicitly because that guarantee is a
        # runtime invariant mypy cannot see through target.kind alone.
        assert isinstance(
            patch, (DisablePatch, ProseReplacementPatch, ProseAdditionPatch)
        )
        return _apply_prose_entry(
            entry,
            patch,
            target,
            record,
            records,
            disabled_prose,
        )

    if isinstance(patch, DisablePatch):
        if target.kind is MechanicalTargetKind.RECORD:
            disabled_records.add(target.record_key)
            return True, "record suppressed"
        assert target.component_key is not None
        found = _find_component(record, target.component_key)
        if found is None:
            raise OverrideApplicationError(
                entry.override_id,
                f"target {target.describe()} names no component of "
                f"{target.record_key!r}",
            )
        if target.kind is MechanicalTargetKind.COMPONENT:
            disabled_components.add((target.record_key, target.component_key))
            return True, "component suppressed"
        assert target.fact_key is not None
        # Scoped, not scope-blind. A choice component holds no direct facts, so
        # a scope-blind lookup rejects every valid option-fact disable as
        # INVALID_OVERRIDE; and where the same fact key appears in two options
        # it would resolve one option's target onto the other.
        if _find_fact(found[1], target.fact_key, target.option_key) is None:
            raise OverrideApplicationError(
                entry.override_id,
                f"target {target.describe()} names no fact of "
                f"{target.component_key!r}",
            )
        disabled_facts.add(
            (
                target.record_key,
                target.component_key,
                target.fact_key,
                target.option_key or "",
            )
        )
        return True, "fact suppressed"

    if isinstance(patch, RecordReplacementPatch):
        if patch.record_kind is not record.kind:
            raise OverrideApplicationError(
                entry.override_id,
                f"record replacement declares kind {patch.record_kind.value!r}, "
                f"target record {target.record_key!r} is "
                f"{record.kind.value!r}",
            )
        records[target.record_key] = replace(
            record,
            components=tuple(
                _component_from_body(
                    body, target.record_key, body.semantic_key or "", entry
                )
                for body in sorted(patch.components, key=lambda b: b.semantic_key or "")
            ),
            supplied_by_override_id=entry.override_id,
            supplied_by_origin=entry.origin,
        )
        # A replaced record's previously suppressed children no longer exist;
        # clearing them keeps suppression from applying to unrelated new
        # components that happen to reuse a semantic key.
        disabled_components.difference_update(
            {k for k in disabled_components if k[0] == target.record_key}
        )
        disabled_facts.difference_update(
            {k for k in disabled_facts if k[0] == target.record_key}
        )
        disabled_prose.difference_update(
            {k for k in disabled_prose if k[0] == target.record_key}
        )
        return True, "record replaced"

    if isinstance(patch, ComponentAdditionPatch):
        # Appending a component targets the *record*, so this branch comes
        # before the component-key assertion below: the target legitimately
        # carries no component key, because the patch is what names the
        # component being added.
        key = patch.body.semantic_key or ""
        if _find_component(record, key) is not None:
            raise OverrideApplicationError(
                entry.override_id,
                f"appending component {key!r} to record {target.record_key!r} "
                "would duplicate an existing component",
            )
        # Authored text has no printed position, so it is not sorted in among
        # the source's components as if it had one: it reads after them.
        records[target.record_key] = replace(
            record,
            components=(
                *record.components,
                _component_from_body(patch.body, target.record_key, key, entry),
            ),
        )
        return True, "component appended"

    assert target.component_key is not None
    if isinstance(patch, ComponentReplacementPatch):
        found = _find_component(record, target.component_key)
        if found is None:
            raise OverrideApplicationError(
                entry.override_id,
                f"target {target.describe()} names no component of "
                f"{target.record_key!r}",
            )
        index, _existing = found
        components = list(record.components)
        components[index] = _component_from_body(
            patch.body, target.record_key, target.component_key, entry
        )
        records[target.record_key] = replace(record, components=tuple(components))
        disabled_facts.difference_update(
            {
                k
                for k in disabled_facts
                if k[0] == target.record_key and k[1] == target.component_key
            }
        )
        disabled_prose.discard((target.record_key, target.component_key))
        return True, "component replaced"

    found = _find_component(record, target.component_key)
    if found is None:
        raise OverrideApplicationError(
            entry.override_id,
            f"target {target.describe()} names no component of "
            f"{target.record_key!r}",
        )
    index, component = found
    # Reachable for a FACT or OPTION target: PROSE returned above, and RECORD/
    # COMPONENT patches were each handled and returned by their own branch. An
    # OPTION target reaches here carrying a non-None option_key and no
    # fact_key, which is exactly the shape the addition path below wants.
    assert isinstance(patch, (FactReplacementPatch, FactAdditionPatch))
    new_fact = patch.fact
    new_key = fact_key(new_fact)

    # Every fact operation resolves inside one scope: the component's direct
    # facts, or one named option's. A target naming an option that does not
    # exist fails rather than silently falling back to the direct facts.
    option_key = target.option_key
    if option_key is not None and not any(
        o.semantic_key == option_key for o in component.options
    ):
        raise OverrideApplicationError(
            entry.override_id,
            f"target {target.describe()} names no option of "
            f"{target.component_key!r}",
        )

    def _scope() -> tuple[EffectiveFact, ...]:
        if option_key is None:
            return component.facts
        return next(o.facts for o in component.options if o.semantic_key == option_key)

    def _rebuild(updated: list[EffectiveFact]) -> EffectiveComponent:
        if option_key is None:
            return replace(component, facts=tuple(updated))
        return replace(
            component,
            options=tuple(
                replace(o, facts=tuple(updated)) if o.semantic_key == option_key else o
                for o in component.options
            ),
        )

    if isinstance(patch, FactReplacementPatch):
        assert target.fact_key is not None
        position = _find_fact(component, target.fact_key, option_key)
        if position is None:
            raise OverrideApplicationError(
                entry.override_id,
                f"target {target.describe()} names no fact of "
                f"{target.component_key!r}",
            )
        fact_index, _ = position
        if (
            new_key != target.fact_key
            and _find_fact(component, new_key, option_key) is not None
        ):
            raise OverrideApplicationError(
                entry.override_id,
                f"replacement fact {new_key} already exists in component "
                f"{target.component_key!r}",
            )
        facts = list(_scope())
        # REPLACE supplies a *complete* fact, so the replacement is
        # unqualified: the old fact's qualifier leaves the view with the fact
        # it named. Carrying it forward would preserve a source-authored
        # limitation the replacement payload never declares, and nothing in
        # REPLACE constrains the replacement's family — the same size clause
        # could end up limiting unrelated authority while citing the source
        # span that states it. A replacement meant to stay conditional is
        # authored as a component patch carrying its own ``fact_qualifiers``.
        facts[fact_index] = EffectiveFact(
            fact_key=new_key,
            fact=new_fact,
            option_key=option_key,
            supplied_by_override_id=entry.override_id,
            supplied_by_origin=entry.origin,
        )
        note = "fact replaced"
    else:
        assert isinstance(patch, FactAdditionPatch)
        if _find_fact(component, new_key, option_key) is not None:
            raise OverrideApplicationError(
                entry.override_id,
                f"appending fact {new_key} to component {target.component_key!r} "
                "would duplicate an existing fact",
            )
        if component.handling is ComponentHandling.PROSE_BOUND:
            # A prose-bound component asserts its meaning cannot be reduced to
            # typed facts. Appending one would contradict the published
            # handling, which is a projection-level judgement an override may
            # not quietly reverse.
            raise OverrideApplicationError(
                entry.override_id,
                f"component {target.component_key!r} is prose-bound; a typed "
                "fact cannot be appended to it",
            )
        if option_key is None and component.options:
            # A choice's direct-fact list is empty by contract. Appending to it
            # would publish a fact that holds alongside *whichever* option is
            # taken — a shape the projection refuses at build time, so an
            # override may not create it either.
            raise OverrideApplicationError(
                entry.override_id,
                f"component {target.component_key!r} states an actor choice; a "
                "fact must be appended to one of its options, not beside them",
            )
        facts = [
            *_scope(),
            EffectiveFact(
                fact_key=new_key,
                fact=new_fact,
                option_key=option_key,
                supplied_by_override_id=entry.override_id,
                supplied_by_origin=entry.origin,
            ),
        ]
        note = "fact appended"

    components = list(record.components)
    components[index] = _rebuild(facts)
    records[target.record_key] = replace(record, components=tuple(components))
    return True, note
