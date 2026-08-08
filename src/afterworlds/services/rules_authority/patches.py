"""Closed typed override patch families — CRD Issue 5d, Decision 10.

Six families, and the set is closed. Which family a payload must be is decided
entirely by the pair *(operation, target kind)*:

===========  ===========  ==========================================
Operation    Target       Patch family
===========  ===========  ==========================================
``DISABLE``  any          :class:`DisablePatch`
``REPLACE``  record       :class:`RecordReplacementPatch`
``REPLACE``  component    :class:`ComponentReplacementPatch`
``REPLACE``  fact         :class:`FactReplacementPatch`
``APPEND``   record       :class:`ComponentAdditionPatch`
``APPEND``   component    :class:`FactAdditionPatch`
``APPEND``   fact         *not permitted*
===========  ===========  ==========================================

``APPEND`` onto a fact has no family because a fact is a single value, not a
collection: ADR-005d Decision 10 permits ``APPEND`` "only where the owning
schema permits multiplicity", and a record's components and a component's facts
are the only two places multiplicity exists.

Record replacement is **record-kind-specific**, never a generic whole-record
overwrite: :class:`RecordReplacementPatch` declares the ``record_kind`` it
replaces, and a patch whose declared kind is not the target record's kind is a
type-incompatible patch that fails rather than reshaping the record into
something else.

Two things this module deliberately refuses to accept, because accepting them
would reopen decisions this PR does not own:

* **Prose-bound authority.** An override-supplied component must be
  ``STRUCTURED``. ``PROSE_BOUND`` and ``MIXED`` handling require exact governing
  prose bound to an authoritative 5c ``RuleChunk`` with span-exact provenance
  (#137 contract 3), which is build-time evidence a runtime patch does not
  have. Authoring prose here would create the second prose store ADR-005d
  forbids, so a prose-bound override component is rejected. ``DISABLE``
  remains available for a prose-bound base component.
* **Anything outside the closed typed-fact union.** Facts are rebuilt through
  CRD Issue 5d's own :func:`fact_from_payload`, so an unknown family, a missing
  field, an extra field, or a mistyped value is rejected here exactly as it is
  in persistence — there is no looser runtime door into the same union.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.representation import (
    MalformedFactPayloadError,
    MechanicalFact,
    RecordKind,
    UnknownFactFamilyError,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
    fact_payload,
)
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)

__all__ = [
    "ComponentAdditionPatch",
    "ComponentBody",
    "ComponentReplacementPatch",
    "DisablePatch",
    "FactAdditionPatch",
    "FactReplacementPatch",
    "InvalidPatchError",
    "MechanicalPatch",
    "PatchFamily",
    "RecordReplacementPatch",
    "patch_from_payload",
    "patch_payload",
    "required_patch_family",
]


class PatchFamily(StrEnum):
    """The closed patch union's discriminator."""

    DISABLE = "disable"
    REPLACE_RECORD = "replace_record"
    REPLACE_COMPONENT = "replace_component"
    REPLACE_FACT = "replace_fact"
    APPEND_COMPONENT = "append_component"
    APPEND_FACT = "append_fact"


class InvalidPatchError(ValueError):
    """Raised when a payload is not a valid member of the closed patch union.

    Every runtime caller turns this into the typed ``INVALID_OVERRIDE`` state
    rather than letting it escape: a malformed patch is an authority failure to
    report, not an exception to propagate into a turn.
    """


# ---------------------------------------------------------------------------
# Patch shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ComponentBody:
    """The complete typed content of one override-supplied component.

    ``semantic_key`` is ``None`` for a replacement, where the target already
    names the component being replaced, and required for an addition, where the
    patch is what names it. Carrying the key twice would let a patch disagree
    with its own target.
    """

    handling: ComponentHandling
    facts: tuple[MechanicalFact, ...]
    semantic_key: str | None = None


@dataclass(frozen=True)
class DisablePatch:
    """Suppress an exact target. Carries no content by construction."""

    FAMILY = PatchFamily.DISABLE


@dataclass(frozen=True)
class RecordReplacementPatch:
    """A complete replacement for one record of a declared kind."""

    FAMILY = PatchFamily.REPLACE_RECORD

    record_kind: RecordKind
    components: tuple[ComponentBody, ...]


@dataclass(frozen=True)
class ComponentReplacementPatch:
    """A complete replacement for one component."""

    FAMILY = PatchFamily.REPLACE_COMPONENT

    body: ComponentBody


@dataclass(frozen=True)
class FactReplacementPatch:
    """A complete replacement for one typed fact."""

    FAMILY = PatchFamily.REPLACE_FACT

    fact: MechanicalFact


@dataclass(frozen=True)
class ComponentAdditionPatch:
    """One complete additional component for a record."""

    FAMILY = PatchFamily.APPEND_COMPONENT

    body: ComponentBody


@dataclass(frozen=True)
class FactAdditionPatch:
    """One complete additional typed fact for a component."""

    FAMILY = PatchFamily.APPEND_FACT

    fact: MechanicalFact


MechanicalPatch = (
    DisablePatch
    | RecordReplacementPatch
    | ComponentReplacementPatch
    | FactReplacementPatch
    | ComponentAdditionPatch
    | FactAdditionPatch
)


#: The one family a payload may be, given what the override says it does. This
#: mapping is the type-compatibility contract: a payload of any other family is
#: rejected before it can touch authority, so a ``REPLACE`` never quietly
#: behaves like an ``APPEND`` because its payload said so.
_REQUIRED_FAMILY: dict[
    tuple[OverrideOperationEnum, MechanicalTargetKind], PatchFamily
] = {
    (OverrideOperationEnum.DISABLE, MechanicalTargetKind.RECORD): PatchFamily.DISABLE,
    (
        OverrideOperationEnum.DISABLE,
        MechanicalTargetKind.COMPONENT,
    ): PatchFamily.DISABLE,
    (OverrideOperationEnum.DISABLE, MechanicalTargetKind.FACT): PatchFamily.DISABLE,
    (
        OverrideOperationEnum.REPLACE,
        MechanicalTargetKind.RECORD,
    ): PatchFamily.REPLACE_RECORD,
    (
        OverrideOperationEnum.REPLACE,
        MechanicalTargetKind.COMPONENT,
    ): PatchFamily.REPLACE_COMPONENT,
    (
        OverrideOperationEnum.REPLACE,
        MechanicalTargetKind.FACT,
    ): PatchFamily.REPLACE_FACT,
    (
        OverrideOperationEnum.APPEND,
        MechanicalTargetKind.RECORD,
    ): PatchFamily.APPEND_COMPONENT,
    (
        OverrideOperationEnum.APPEND,
        MechanicalTargetKind.COMPONENT,
    ): PatchFamily.APPEND_FACT,
    # (APPEND, FACT) is absent on purpose — a fact has no multiplicity to
    # append into, so there is no honest family for it.
}


def required_patch_family(
    operation: OverrideOperationEnum, target_kind: MechanicalTargetKind
) -> PatchFamily:
    """The single patch family this operation/target pair permits.

    Raises :class:`InvalidPatchError` for the one pair with no family, which is
    how ``APPEND`` onto a fact fails: explicitly, and before anything is
    applied.
    """
    family = _REQUIRED_FAMILY.get((operation, target_kind))
    if family is None:
        raise InvalidPatchError(
            f"{operation.value} is not permitted on a {target_kind.value} target: "
            "the owning schema declares no multiplicity there"
        )
    return family


# ---------------------------------------------------------------------------
# Payload → patch
# ---------------------------------------------------------------------------


def _require_keys(payload: Mapping[str, Any], expected: set[str], what: str) -> None:
    supplied = set(payload)
    if missing := sorted(expected - supplied):
        raise InvalidPatchError(f"{what} payload is missing {missing}")
    if extra := sorted(supplied - expected):
        raise InvalidPatchError(f"{what} payload carries extra {extra}")


def _build_fact(value: object, what: str) -> MechanicalFact:
    if not isinstance(value, Mapping):
        raise InvalidPatchError(
            f"{what} fact must be a payload object, got {type(value).__name__}"
        )
    try:
        fact = fact_from_payload(value)
    except (UnknownFactFamilyError, MalformedFactPayloadError) as exc:
        raise InvalidPatchError(
            f"{what} fact is not a valid typed fact: {exc}"
        ) from exc
    if violations := fact_invariant_violations(fact):
        raise InvalidPatchError(
            f"{what} fact violates its own family contract: {'; '.join(violations)}"
        )
    return fact


def _build_component_body(value: object, what: str, *, keyed: bool) -> ComponentBody:
    """Rebuild one component body, refusing anything the projection would.

    *keyed* distinguishes an addition (which must name the component it adds)
    from a replacement (whose target already names it).
    """
    if not isinstance(value, Mapping):
        raise InvalidPatchError(
            f"{what} component must be a payload object, got {type(value).__name__}"
        )
    expected = {"handling", "facts"} | ({"semantic_key"} if keyed else set())
    _require_keys(value, expected, what)

    raw_handling = value["handling"]
    if type(raw_handling) is not str:
        raise InvalidPatchError(f"{what} handling must be a string")
    try:
        handling = ComponentHandling(raw_handling)
    except ValueError as exc:
        raise InvalidPatchError(
            f"{what} handling {raw_handling!r} is not a declared handling"
        ) from exc
    if handling is not ComponentHandling.STRUCTURED:
        # Prose-bound authority needs an authoritative 5c chunk and span-exact
        # provenance, which a runtime patch cannot supply. Rejecting it here is
        # what keeps overrides from becoming a second prose store.
        raise InvalidPatchError(
            f"{what} declares {handling.value} handling; an override-supplied "
            "component must be structured, because prose-bound authority "
            "requires build-time 5c prose binding and provenance"
        )

    semantic_key: str | None = None
    if keyed:
        raw_key = value["semantic_key"]
        if type(raw_key) is not str or not raw_key.strip():
            raise InvalidPatchError(f"{what} semantic_key must be a non-blank string")
        semantic_key = raw_key

    raw_facts = value["facts"]
    if not isinstance(raw_facts, list):
        raise InvalidPatchError(f"{what} facts must be a list")
    facts = tuple(
        _build_fact(entry, f"{what} fact {index}")
        for index, entry in enumerate(raw_facts)
    )
    if not facts:
        # Structured handling with no facts is the dishonest declaration the
        # projection validator already rejects; a patch may not introduce it.
        raise InvalidPatchError(f"{what} declares structured handling with no facts")
    keys = [fact_key(f) for f in facts]
    if len(set(keys)) != len(keys):
        raise InvalidPatchError(f"{what} repeats the same typed fact")
    return ComponentBody(handling=handling, facts=facts, semantic_key=semantic_key)


def _build_disable(payload: Mapping[str, Any]) -> DisablePatch:
    _require_keys(payload, {"patch"}, "disable")
    return DisablePatch()


def _build_replace_record(payload: Mapping[str, Any]) -> RecordReplacementPatch:
    _require_keys(payload, {"patch", "record_kind", "components"}, "replace_record")
    raw_kind = payload["record_kind"]
    if type(raw_kind) is not str:
        raise InvalidPatchError("replace_record record_kind must be a string")
    try:
        kind = RecordKind(raw_kind)
    except ValueError as exc:
        raise InvalidPatchError(
            f"replace_record record_kind {raw_kind!r} is not a declared record kind"
        ) from exc
    raw_components = payload["components"]
    if not isinstance(raw_components, list) or not raw_components:
        raise InvalidPatchError(
            "replace_record components must be a non-empty list: a record "
            "replacement is complete or it is not a replacement"
        )
    components = tuple(
        _build_component_body(entry, f"replace_record component {index}", keyed=True)
        for index, entry in enumerate(raw_components)
    )
    keys = [c.semantic_key for c in components]
    if len(set(keys)) != len(keys):
        raise InvalidPatchError("replace_record repeats a component semantic_key")
    return RecordReplacementPatch(record_kind=kind, components=components)


def _build_replace_component(payload: Mapping[str, Any]) -> ComponentReplacementPatch:
    _require_keys(payload, {"patch", "component"}, "replace_component")
    return ComponentReplacementPatch(
        body=_build_component_body(
            payload["component"], "replace_component", keyed=False
        )
    )


def _build_replace_fact(payload: Mapping[str, Any]) -> FactReplacementPatch:
    _require_keys(payload, {"patch", "fact"}, "replace_fact")
    return FactReplacementPatch(fact=_build_fact(payload["fact"], "replace_fact"))


def _build_append_component(payload: Mapping[str, Any]) -> ComponentAdditionPatch:
    _require_keys(payload, {"patch", "component"}, "append_component")
    return ComponentAdditionPatch(
        body=_build_component_body(payload["component"], "append_component", keyed=True)
    )


def _build_append_fact(payload: Mapping[str, Any]) -> FactAdditionPatch:
    _require_keys(payload, {"patch", "fact"}, "append_fact")
    return FactAdditionPatch(fact=_build_fact(payload["fact"], "append_fact"))


_PATCH_BUILDERS: dict[PatchFamily, Any] = {
    PatchFamily.DISABLE: _build_disable,
    PatchFamily.REPLACE_RECORD: _build_replace_record,
    PatchFamily.REPLACE_COMPONENT: _build_replace_component,
    PatchFamily.REPLACE_FACT: _build_replace_fact,
    PatchFamily.APPEND_COMPONENT: _build_append_component,
    PatchFamily.APPEND_FACT: _build_append_fact,
}


def patch_from_payload(
    payload: object,
    *,
    operation: OverrideOperationEnum,
    target: MechanicalTarget,
) -> MechanicalPatch:
    """Rebuild the typed patch a stored payload declares, or refuse it.

    The declared ``patch`` discriminator must be exactly the family the
    operation and target permit. A well-formed payload of the wrong family is
    still refused — that is what makes a cross-family patch a typed failure
    rather than a silently reinterpreted one.
    """
    if not isinstance(payload, Mapping):
        raise InvalidPatchError(
            f"override payload must be an object, got {type(payload).__name__}"
        )
    required = required_patch_family(operation, target.kind)
    raw = payload.get("patch")
    try:
        family = PatchFamily(str(raw))
    except ValueError as exc:
        raise InvalidPatchError(
            f"{raw!r} is not a member of the closed patch union"
        ) from exc
    if family is not required:
        raise InvalidPatchError(
            f"{operation.value} on a {target.kind.value} target requires a "
            f"{required.value} patch, got {family.value}"
        )
    return _PATCH_BUILDERS[family](payload)  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Patch → payload
# ---------------------------------------------------------------------------


def _component_body_payload(body: ComponentBody) -> dict[str, object]:
    payload: dict[str, object] = {}
    if body.semantic_key is not None:
        payload["semantic_key"] = body.semantic_key
    payload["handling"] = body.handling.value
    # Facts are ordered by their content-derived key rather than by authoring
    # order: two patches supplying the same facts in a different order are the
    # same patch, and must not mint two override-set identities.
    payload["facts"] = [fact_payload(f) for f in sorted(body.facts, key=fact_key)]
    return payload


def patch_payload(patch: MechanicalPatch) -> dict[str, object]:
    """Canonical identity-bearing payload of one typed patch.

    This is what the override-set identity is derived from, so it must be a
    complete and order-stable statement of the patch's content — a payload that
    dropped a field would let two different patches share an identity.
    """
    if isinstance(patch, DisablePatch):
        return {"patch": PatchFamily.DISABLE.value}
    if isinstance(patch, RecordReplacementPatch):
        return {
            "patch": PatchFamily.REPLACE_RECORD.value,
            "record_kind": patch.record_kind.value,
            "components": [
                _component_body_payload(c)
                for c in sorted(patch.components, key=lambda c: c.semantic_key or "")
            ],
        }
    if isinstance(patch, ComponentReplacementPatch):
        return {
            "patch": PatchFamily.REPLACE_COMPONENT.value,
            "component": _component_body_payload(patch.body),
        }
    if isinstance(patch, FactReplacementPatch):
        return {
            "patch": PatchFamily.REPLACE_FACT.value,
            "fact": fact_payload(patch.fact),
        }
    if isinstance(patch, ComponentAdditionPatch):
        return {
            "patch": PatchFamily.APPEND_COMPONENT.value,
            "component": _component_body_payload(patch.body),
        }
    return {
        "patch": PatchFamily.APPEND_FACT.value,
        "fact": fact_payload(patch.fact),
    }
