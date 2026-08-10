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

from dataclasses import dataclass, replace

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.projection import ProjectionCandidate
from afterworlds.ingestion.mechanical.representation import (
    MechanicalFact,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordKind,
    fact_key,
)
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
class EffectiveFact:
    """One typed fact in the effective view, with its exact provenance."""

    fact_key: str
    fact: MechanicalFact
    #: 5c leaf subspans accepted as this fact's provenance. Empty exactly when
    #: the fact came from an override rather than from the source corpus.
    span_ids: tuple[str, ...] = ()
    #: The override that supplied this fact, when one did.
    supplied_by_override_id: str | None = None
    supplied_by_origin: OverrideOriginEnum | None = None


@dataclass(frozen=True)
class SourceProse:
    """One passage of exact 5c source prose, identified by its chunk.

    ``text`` is resolved later, by the GameMaster view, from the authoritative
    ``RuleChunk`` the service reads by this exact ``chunk_id``; it is ``None``
    here because this type is built before that resolution happens. It is
    never anything but an exact 5c chunk — never a fabricated id, never a
    stand-in for authored text.
    """

    chunk_id: str
    text: str | None = None


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
class EffectiveComponent:
    """One component of the effective view."""

    record_key: str
    semantic_key: str
    handling: ComponentHandling
    irreducibility_reason_code: str | None
    facts: tuple[EffectiveFact, ...]
    #: Exact ordered governing prose: 5c-bound, authored, or both, in the
    #: order overrides resolve in. Empty for a purely structured component
    #: that has never had authored prose attached to it.
    governing_prose: tuple[GoverningProseEntry, ...] = ()
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


@dataclass(frozen=True)
class EffectiveAuthority:
    """The complete effective mechanical authority of one binding."""

    binding: RulesPackageBinding
    records: tuple[EffectiveRecord, ...]
    applied_overrides: tuple[AppliedOverride, ...]


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


def _base_records(candidate: ProjectionCandidate) -> dict[str, EffectiveRecord]:
    """Assemble the immutable base projection as an effective view."""
    draft = candidate.representation
    spans = _provenance_index(candidate)
    prose: dict[tuple[str, str], list[str]] = {}
    for binding in draft.prose_bindings:
        prose.setdefault((binding.record_key, binding.component_key), []).append(
            binding.chunk_id
        )

    components: dict[str, list[EffectiveComponent]] = {}
    for component in draft.components:
        facts = tuple(
            EffectiveFact(
                fact_key=fact_key(fact),
                fact=fact,
                span_ids=spans.get(
                    (
                        ProvenanceTargetKind.FACT,
                        (component.record_key, component.semantic_key, fact_key(fact)),
                    ),
                    (),
                ),
            )
            for fact in component.facts
        )
        components.setdefault(component.record_key, []).append(
            EffectiveComponent(
                record_key=component.record_key,
                semantic_key=component.semantic_key,
                handling=component.handling,
                irreducibility_reason_code=component.irreducibility_reason_code,
                facts=facts,
                governing_prose=tuple(
                    SourceProse(chunk_id=chunk_id)
                    for chunk_id in sorted(
                        prose.get((component.record_key, component.semantic_key), ())
                    )
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
                sorted(
                    components.get(record.semantic_key, []),
                    key=lambda c: c.semantic_key,
                )
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
    return EffectiveComponent(
        record_key=record_key,
        semantic_key=semantic_key,
        handling=body.handling,
        irreducibility_reason_code=None,
        facts=tuple(
            EffectiveFact(
                fact_key=fact_key(f),
                fact=f,
                supplied_by_override_id=entry.override_id,
                supplied_by_origin=entry.origin,
            )
            for f in body.facts
        ),
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
    component: EffectiveComponent, key: str
) -> tuple[int, EffectiveFact] | None:
    for index, fact in enumerate(component.facts):
        if fact.fact_key == key:
            return index, fact
    return None


def _suppressed_by(
    target: MechanicalTarget,
    disabled_records: set[str],
    disabled_components: set[tuple[str, str]],
    disabled_facts: set[tuple[str, str, str]],
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
    assert target.kind is MechanicalTargetKind.FACT
    assert target.fact_key is not None
    if (target.record_key, target.component_key, target.fact_key) in disabled_facts:
        return "fact"
    return None


def _finalize_component(
    record: EffectiveRecord,
    component: EffectiveComponent,
    disabled_facts: set[tuple[str, str, str]],
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
        if (record.semantic_key, component.semantic_key, fact.fact_key)
        not in disabled_facts
    )
    facts_present = bool(facts)
    prose_present = bool(component.governing_prose)
    if facts_present and prose_present:
        handling = ComponentHandling.MIXED
    elif facts_present:
        handling = ComponentHandling.STRUCTURED
    elif prose_present:
        handling = ComponentHandling.PROSE_BOUND
    else:
        handling = component.handling
    reason = (
        None
        if handling is ComponentHandling.STRUCTURED
        else component.irreducibility_reason_code
    )
    return replace(
        component, facts=facts, handling=handling, irreducibility_reason_code=reason
    )


def apply_override_set(
    candidate: ProjectionCandidate,
    override_set: EffectiveOverrideSet,
    binding: RulesPackageBinding,
) -> EffectiveAuthority:
    """Layer *override_set* over the reconstructed base projection.

    Raises :class:`OverrideApplicationError` for any override that cannot be
    applied. The caller turns that into ``INVALID_OVERRIDE``; nothing here
    degrades a failure into a partially applied view, because a view missing one
    authored change is indistinguishable from one where that change was never
    authored.
    """
    records = _base_records(candidate)
    disabled_records: set[str] = set()
    disabled_components: set[tuple[str, str]] = set()
    disabled_facts: set[tuple[str, str, str]] = set()
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
    return EffectiveAuthority(
        binding=binding,
        records=surviving,
        applied_overrides=tuple(provenance),
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

    ``irreducibility_reason_code`` is the one field this does touch, and only
    on ``REPLACE``: that operation discards every prior governing-prose entry
    — source or authored — for exactly one new authored passage, so a reason
    the base corpus recorded to justify the now-discarded *source* prose's
    irreducibility can no longer honestly describe what governs this
    component. Carrying it forward would present authored-only authority
    under a source-derived irreducibility claim, which ADR-005d forbids the
    same way it forbids a fabricated ``chunk_id`` or copied span provenance.
    ``APPEND`` and ``DISABLE`` leave it untouched: ``APPEND`` only adds to
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
            component, governing_prose=(authored,), irreducibility_reason_code=None
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
    disabled_facts: set[tuple[str, str, str]],
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
        if _find_fact(found[1], target.fact_key) is None:
            raise OverrideApplicationError(
                entry.override_id,
                f"target {target.describe()} names no fact of "
                f"{target.component_key!r}",
            )
        disabled_facts.add((target.record_key, target.component_key, target.fact_key))
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
        records[target.record_key] = replace(
            record,
            components=tuple(
                sorted(
                    [
                        *record.components,
                        _component_from_body(patch.body, target.record_key, key, entry),
                    ],
                    key=lambda c: c.semantic_key,
                )
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
    # Reachable only for a FACT target: PROSE returned above, and RECORD/
    # COMPONENT patches were each handled and returned by their own branch.
    assert isinstance(patch, (FactReplacementPatch, FactAdditionPatch))
    new_fact = patch.fact
    new_key = fact_key(new_fact)

    if isinstance(patch, FactReplacementPatch):
        assert target.fact_key is not None
        position = _find_fact(component, target.fact_key)
        if position is None:
            raise OverrideApplicationError(
                entry.override_id,
                f"target {target.describe()} names no fact of "
                f"{target.component_key!r}",
            )
        fact_index, _old = position
        if new_key != target.fact_key and _find_fact(component, new_key) is not None:
            raise OverrideApplicationError(
                entry.override_id,
                f"replacement fact {new_key} already exists in component "
                f"{target.component_key!r}",
            )
        facts = list(component.facts)
        facts[fact_index] = EffectiveFact(
            fact_key=new_key,
            fact=new_fact,
            supplied_by_override_id=entry.override_id,
            supplied_by_origin=entry.origin,
        )
        note = "fact replaced"
    else:
        assert isinstance(patch, FactAdditionPatch)
        if _find_fact(component, new_key) is not None:
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
        facts = [
            *component.facts,
            EffectiveFact(
                fact_key=new_key,
                fact=new_fact,
                supplied_by_override_id=entry.override_id,
                supplied_by_origin=entry.origin,
            ),
        ]
        note = "fact appended"

    components = list(record.components)
    components[index] = replace(component, facts=tuple(facts))
    records[target.record_key] = replace(record, components=tuple(components))
    return True, note
