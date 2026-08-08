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
    RecordReplacementPatch,
    patch_from_payload,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)

__all__ = [
    "AppliedOverride",
    "EffectiveAuthority",
    "EffectiveComponent",
    "EffectiveFact",
    "EffectiveRecord",
    "OverrideApplicationError",
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
class EffectiveComponent:
    """One component of the effective view."""

    record_key: str
    semantic_key: str
    handling: ComponentHandling
    irreducibility_reason_code: str | None
    facts: tuple[EffectiveFact, ...]
    #: Authoritative 5c chunks holding this component's exact governing prose.
    prose_chunk_ids: tuple[str, ...] = ()
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
                prose_chunk_ids=tuple(
                    sorted(
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
) -> str | None:
    """Is this target already suppressed by an earlier ``DISABLE``?

    Suppression is inherited downward: disabling a record disables the
    components and facts beneath it, so a later override aimed at one of them
    has nothing to change. That is the existing precedence rule — the first
    winning disable stops later processing of that target — applied to the
    record/component/fact hierarchy the chunk path never had.
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
    assert target.fact_key is not None
    if (target.record_key, target.component_key, target.fact_key) in disabled_facts:
        return "fact"
    return None


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
                replace(
                    component,
                    facts=tuple(
                        fact
                        for fact in component.facts
                        if (record.semantic_key, component.semantic_key, fact.fact_key)
                        not in disabled_facts
                    ),
                )
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


def _apply_entry(
    entry: EffectiveOverrideEntry,
    records: dict[str, EffectiveRecord],
    disabled_records: set[str],
    disabled_components: set[tuple[str, str]],
    disabled_facts: set[tuple[str, str, str]],
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
        target, disabled_records, disabled_components, disabled_facts
    )
    if suppressed is not None:
        return False, f"target already suppressed by an earlier {suppressed} disable"

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
        return True, "component replaced"

    found = _find_component(record, target.component_key)
    if found is None:
        raise OverrideApplicationError(
            entry.override_id,
            f"target {target.describe()} names no component of "
            f"{target.record_key!r}",
        )
    index, component = found
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
