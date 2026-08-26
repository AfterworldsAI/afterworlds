"""Closed typed override patch families — CRD Issue 5d, Decision 10.

Eight families, and the set is closed. Which family a payload must be is
decided entirely by the pair *(operation, target kind)*:

===========  ===========  ==========================================
Operation    Target       Patch family
===========  ===========  ==========================================
``DISABLE``  any          :class:`DisablePatch`
``REPLACE``  record       :class:`RecordReplacementPatch`
``REPLACE``  component    :class:`ComponentReplacementPatch`
``REPLACE``  fact         :class:`FactReplacementPatch`
``REPLACE``  prose        :class:`ProseReplacementPatch`
``APPEND``   record       :class:`ComponentAdditionPatch`
``APPEND``   component    :class:`FactAdditionPatch`
``APPEND``   prose        :class:`ProseAdditionPatch`
``APPEND``   fact         *not permitted*
===========  ===========  ==========================================

``APPEND`` onto a fact has no family because a fact is a single value, not a
collection: ADR-005d Decision 10 permits ``APPEND`` "only where the owning
schema permits multiplicity", and a record's components, a component's facts,
and a component's governing prose are the only places multiplicity exists.

Record replacement is **record-kind-specific**, never a generic whole-record
overwrite: :class:`RecordReplacementPatch` declares the ``record_kind`` it
replaces, and a patch whose declared kind is not the target record's kind is a
type-incompatible patch that fails rather than reshaping the record into
something else.

**Authored prose is a distinct runtime authority layer (Owner Decision
2026-08-08), not a second copy of source authority.** ADR-005d's prohibition on
a second *prose store* binds the base projection: its prose bindings resolve
only to an authoritative 5c ``RuleChunk`` with span-exact provenance
(#137 contract 3), and nothing here duplicates that. An override-supplied
whole component may now declare ``PROSE_BOUND`` or ``MIXED`` handling and carry
its own authored text — but that text is never bound to a chunk id, never
claims 5c span provenance, and never copies an irreducibility reason from base
authority; its provenance is the supplying override and the retained
override-set version, and application-layer code enforces that by construction
rather than by convention. The dedicated ``prose`` target kind
(:mod:`afterworlds.services.rules_authority.targets`) exists for exactly the
narrower case: patching *only* a component's governing prose without touching
its typed facts at all.

One thing this module still deliberately refuses to accept, because accepting
it would reopen a decision this PR does not own:

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
from afterworlds.ingestion.mechanical.projection import (
    applicability_payload,
    applicability_payload_violations,
    recurrence_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ApplicabilityKind,
    Comparison,
    ComponentOption,
    CreatureSize,
    FactQualifier,
    MalformedFactPayloadError,
    MechanicalFact,
    ParticipantRole,
    Phase,
    RecordKind,
    RecoveryTrigger,
    Recurrence,
    RecurrenceBoundary,
    RollActor,
    SizeComparison,
    SizeRelation,
    TrackedQuantity,
    UnknownFactFamilyError,
    applicability_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
    fact_payload,
    fact_qualifier_violations,
    option_set_violations,
    recurrence_violations,
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
    "ProseAdditionPatch",
    "ProseReplacementPatch",
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
    REPLACE_PROSE = "replace_prose"
    APPEND_COMPONENT = "append_component"
    APPEND_FACT = "append_fact"
    APPEND_PROSE = "append_prose"


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

    ``authored_prose`` is the component's own authored governing prose — never
    a 5c chunk id, never span provenance, never an irreducibility reason copied
    from base authority (Owner Decision 2026-08-08). It is required exactly
    when ``handling`` is ``PROSE_BOUND`` or ``MIXED`` and forbidden for
    ``STRUCTURED``, mirroring the honesty invariant the build-time projection
    validator already enforces for the base corpus.

    ``applies_when`` and ``options`` are schema 2's component-level shape, and a
    complete component patch must be able to carry both or it cannot author the
    components the representation admits. Both are optional *on the way in* —
    a legacy payload never mentions them — and both are omitted from the
    canonical payload when they hold their legacy defaults, so an unconditional
    direct-fact component keeps exactly the bytes and the override-set identity
    it always had.

    Replacement stays **complete**: omitting either field means unconditional /
    no-options, and the replaced component therefore loses any qualifier or
    option set the base projection gave it rather than silently inheriting it.
    """

    handling: ComponentHandling
    facts: tuple[MechanicalFact, ...]
    semantic_key: str | None = None
    authored_prose: str | None = None
    #: When this component applies at all. ``None`` means unconditionally.
    applies_when: Applicability | None = None
    #: An exhaustive actor choice. Empty, or at least two uniquely keyed
    #: options; never non-empty alongside ``facts``.
    options: tuple[ComponentOption, ...] = ()
    #: Per-fact conditions, addressed by ``(option_key, fact_key)``. Complete
    #: like every other field here: a replacement that omits a qualifier the
    #: base component had drops it rather than inheriting it.
    fact_qualifiers: tuple[FactQualifier, ...] = ()
    #: Schema 4's cadence. Overridable for the same reason ``applies_when`` and
    #: ``fact_qualifiers`` are, and by the same existing contract rather than by
    #: a new decision: ``recurs`` is a component-level meaning-bearing field on
    #: :class:`ComponentDraft`, and a *complete* component patch that could not
    #: carry it would silently republish a repeating effect as a one-off. Its
    #: absence therefore means "states no cadence" — completely, like every
    #: other field here — and never "inherit the base component's".
    recurs: Recurrence | None = None


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


@dataclass(frozen=True)
class ProseReplacementPatch:
    """Replace a component's complete effective governing prose.

    Supersedes both the base projection's 5c-bound prose and any previously
    applied authored prose for that target (ADR-005d Decision 10, amended
    2026-08-08) — it is a replacement of everything shown, not one more
    passage added to it.
    """

    FAMILY = PatchFamily.REPLACE_PROSE

    text: str


@dataclass(frozen=True)
class ProseAdditionPatch:
    """Add one authored passage after a component's existing effective prose.

    The existing effective prose — 5c-bound, previously authored, or both — is
    preserved; this adds one more passage in the same resolution order every
    other override uses.
    """

    FAMILY = PatchFamily.APPEND_PROSE

    text: str


MechanicalPatch = (
    DisablePatch
    | RecordReplacementPatch
    | ComponentReplacementPatch
    | FactReplacementPatch
    | ComponentAdditionPatch
    | FactAdditionPatch
    | ProseReplacementPatch
    | ProseAdditionPatch
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
    (OverrideOperationEnum.DISABLE, MechanicalTargetKind.PROSE): PatchFamily.DISABLE,
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
        OverrideOperationEnum.REPLACE,
        MechanicalTargetKind.PROSE,
    ): PatchFamily.REPLACE_PROSE,
    (
        OverrideOperationEnum.APPEND,
        MechanicalTargetKind.RECORD,
    ): PatchFamily.APPEND_COMPONENT,
    (
        OverrideOperationEnum.APPEND,
        MechanicalTargetKind.COMPONENT,
    ): PatchFamily.APPEND_FACT,
    (
        OverrideOperationEnum.APPEND,
        MechanicalTargetKind.PROSE,
    ): PatchFamily.APPEND_PROSE,
    (
        OverrideOperationEnum.APPEND,
        MechanicalTargetKind.OPTION,
    ): PatchFamily.APPEND_FACT,
    # (APPEND, FACT) is absent on purpose — a fact has no multiplicity to
    # append into, so there is no honest family for it.
    #
    # (DISABLE, OPTION) and (REPLACE, OPTION) are absent for a different
    # reason, and deliberately not the same one: an option *does* have content
    # to suppress or replace, but the source states the choice as exhaustive,
    # so removing or rewriting one arm would publish a choice the source never
    # states. An option is a container an override may add a fact to, and
    # nothing else (Owner Decision 2026-08-19).
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
        # Two different refusals wearing one shape would be a worse message
        # than either. An option is not missing multiplicity — it has content
        # and could be suppressed or replaced; it is the *exhaustiveness* of
        # the choice that forbids it.
        why = (
            "an option is an exhaustive arm of a choice, addressable only as a "
            "container to append a fact into"
            if target_kind is MechanicalTargetKind.OPTION
            else "the owning schema declares no multiplicity there"
        )
        raise InvalidPatchError(
            f"{operation.value} is not permitted on a {target_kind.value} "
            f"target: {why}"
        )
    return family


# ---------------------------------------------------------------------------
# Payload → patch
# ---------------------------------------------------------------------------


def _require_keys(
    payload: Mapping[str, Any],
    expected: set[str],
    what: str,
    *,
    optional: frozenset[str] = frozenset(),
) -> None:
    supplied = set(payload)
    if missing := sorted(expected - supplied):
        raise InvalidPatchError(f"{what} payload is missing {missing}")
    if extra := sorted(supplied - expected - optional):
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


def _build_applicability(raw: object, what: str) -> Applicability | None:
    """Rebuild one applicability from patch JSON, or ``None``.

    Two gates, the same pair the accepted-input and persisted-state loaders
    already run and in the same order: the closed key set first — a misspelled
    key never reaches the typed invariants as the field it was meant to be —
    then the typed contract, which owns every exact-primitive and exact-type
    rule. Nothing is coerced, defaulted, or reinterpreted; the rules are stated
    once, in the representation, and this is a third reader of them rather than
    a third copy.
    """
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise InvalidPatchError(f"{what} applies_when must be an object or null")
    if shape := applicability_payload_violations(dict(raw)):
        raise InvalidPatchError(f"{what} applies_when: {'; '.join(shape)}")
    try:
        built = Applicability(
            kind=ApplicabilityKind(raw["kind"]),
            negated=raw["negated"],
            quantity=(
                None if raw["quantity"] is None else TrackedQuantity(raw["quantity"])
            ),
            comparison=(
                None if raw["comparison"] is None else Comparison(raw["comparison"])
            ),
            value=raw["value"],
            any_of=tuple(
                SizeComparison(
                    category=(
                        None if c["category"] is None else CreatureSize(c["category"])
                    ),
                    relation=(
                        None if c["relation"] is None else SizeRelation(c["relation"])
                    ),
                    at_least=c["at_least"],
                    at_most=c["at_most"],
                    measured=ParticipantRole(c["measured"]),
                    reference=(
                        None
                        if c["reference"] is None
                        else ParticipantRole(c["reference"])
                    ),
                )
                for c in raw["any_of"]
            ),
            trigger=(
                None if raw["trigger"] is None else RecoveryTrigger(raw["trigger"])
            ),
            phase=None if raw["phase"] is None else Phase(raw["phase"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidPatchError(f"{what} applies_when: {exc}") from exc
    if violations := applicability_violations(built):
        raise InvalidPatchError(f"{what} applies_when: {'; '.join(violations)}")
    return built


def _build_option(raw: object, what: str) -> ComponentOption:
    """Rebuild one option of an override-supplied exhaustive actor choice."""
    if not isinstance(raw, Mapping):
        raise InvalidPatchError(f"{what} must be a payload object")
    _require_keys(
        raw, {"semantic_key", "facts"}, what, optional=frozenset({"applies_when"})
    )
    raw_key = raw["semantic_key"]
    if type(raw_key) is not str or not raw_key.strip():
        raise InvalidPatchError(f"{what} semantic_key must be a non-blank string")
    raw_facts = raw["facts"]
    if not isinstance(raw_facts, list):
        raise InvalidPatchError(f"{what} facts must be a list")
    facts = tuple(
        _build_fact(entry, f"{what} fact {index}")
        for index, entry in enumerate(raw_facts)
    )
    keys = [fact_key(f) for f in facts]
    if len(set(keys)) != len(keys):
        raise InvalidPatchError(f"{what} repeats the same typed fact")
    return ComponentOption(
        semantic_key=raw_key,
        facts=facts,
        applies_when=_build_applicability(raw.get("applies_when"), what),
    )


def _build_component_body(value: object, what: str, *, keyed: bool) -> ComponentBody:
    """Rebuild one component body, refusing anything the projection would.

    *keyed* distinguishes an addition (which must name the component it adds)
    from a replacement (whose target already names it).

    ``handling`` may now be ``PROSE_BOUND`` or ``MIXED`` as well as
    ``STRUCTURED`` (Owner Decision 2026-08-08): the same facts/prose honesty
    invariant the build-time projection validator enforces for the base corpus
    (``ingestion.mechanical.validation``) is enforced here for an
    override-supplied component — structured handling has facts and no
    authored prose; prose-bound handling has authored prose and no facts;
    mixed handling has both. Unlike the base corpus, an override-supplied
    component never carries an irreducibility reason: that catalog is 5c's own
    build-time semantic judgment, not one a runtime override author makes.
    """
    if not isinstance(value, Mapping):
        raise InvalidPatchError(
            f"{what} component must be a payload object, got {type(value).__name__}"
        )
    expected = {"handling", "facts"} | ({"semantic_key"} if keyed else set())
    # authored_prose is optional on the way in — existing STRUCTURED payloads
    # that predate Owner Decision 2026-08-08 never mention it — but
    # _component_body_payload always emits it explicitly, so the canonical
    # form is never ambiguous about whether it was "omitted" or "null".
    _require_keys(
        value,
        expected,
        what,
        # Optional on the way in: a legacy payload predating schema 2 never
        # mentions either, and _component_body_payload omits them again when
        # they hold their legacy defaults, so those bytes are unchanged.
        optional=frozenset(
            {
                "authored_prose",
                "applies_when",
                "options",
                "fact_qualifiers",
                "recurs",
            }
        ),
    )

    raw_handling = value["handling"]
    if type(raw_handling) is not str:
        raise InvalidPatchError(f"{what} handling must be a string")
    try:
        handling = ComponentHandling(raw_handling)
    except ValueError as exc:
        raise InvalidPatchError(
            f"{what} handling {raw_handling!r} is not a declared handling"
        ) from exc

    semantic_key: str | None = None
    if keyed:
        raw_key = value["semantic_key"]
        if type(raw_key) is not str or not raw_key.strip():
            raise InvalidPatchError(f"{what} semantic_key must be a non-blank string")
        semantic_key = raw_key

    raw_prose = value.get("authored_prose")
    if raw_prose is not None and (type(raw_prose) is not str or not raw_prose.strip()):
        raise InvalidPatchError(
            f"{what} authored_prose must be a non-blank string or null"
        )
    authored_prose: str | None = raw_prose

    raw_facts = value["facts"]
    if not isinstance(raw_facts, list):
        raise InvalidPatchError(f"{what} facts must be a list")
    facts = tuple(
        _build_fact(entry, f"{what} fact {index}")
        for index, entry in enumerate(raw_facts)
    )
    keys = [fact_key(f) for f in facts]
    if len(set(keys)) != len(keys):
        raise InvalidPatchError(f"{what} repeats the same typed fact")

    applies_when = _build_applicability(value.get("applies_when"), what)

    raw_options = value.get("options")
    if raw_options is None:
        raw_options = []
    if not isinstance(raw_options, list):
        raise InvalidPatchError(f"{what} options must be a list")
    options = tuple(
        _build_option(entry, f"{what} option {index}")
        for index, entry in enumerate(raw_options)
    )
    # The same rule the representation enforces, not a runtime restatement of
    # it: exhaustiveness, duplicate keys, duplicate fact sets, empty options,
    # the exact ComponentOption type, direct-facts-versus-options, and each
    # option's own applicability.
    if violations := option_set_violations(facts, options, what):
        raise InvalidPatchError("; ".join(violations))

    raw_qualifiers = value.get("fact_qualifiers")
    if raw_qualifiers is None:
        raw_qualifiers = []
    if not isinstance(raw_qualifiers, list):
        raise InvalidPatchError(f"{what} fact_qualifiers must be a list")
    fact_qualifiers = tuple(
        _build_fact_qualifier(entry, f"{what} fact qualifier {index}")
        for index, entry in enumerate(raw_qualifiers)
    )
    # Again the representation's own rule rather than a runtime copy: every
    # qualifier must name exactly one fact in its exact scope, with no
    # dangling, wrong-scope, or duplicated entry.
    if violations := fact_qualifier_violations(facts, options, fact_qualifiers, what):
        raise InvalidPatchError("; ".join(violations))

    if handling is ComponentHandling.PROSE_BOUND:
        if facts or options:
            raise InvalidPatchError(
                f"{what} declares prose_bound handling with typed facts"
            )
        if authored_prose is None:
            raise InvalidPatchError(
                f"{what} declares prose_bound handling with no authored prose"
            )
    else:
        # An option's facts are published authority exactly as direct facts
        # are — a choice component has no direct facts by contract, so
        # counting only ``facts`` would reject every honest option-bearing
        # component. Same predicate as ``_finalize_component``'s
        # ``facts_present``.
        if not facts and not any(o.facts for o in options):
            # Structured/mixed handling with no facts is the dishonest
            # declaration the projection validator already rejects for the
            # base corpus; a patch may not introduce it either.
            raise InvalidPatchError(
                f"{what} declares {handling.value} handling with no facts"
            )
        if handling is ComponentHandling.STRUCTURED:
            if authored_prose is not None:
                raise InvalidPatchError(
                    f"{what} declares structured handling with authored prose"
                )
        elif authored_prose is None:
            raise InvalidPatchError(
                f"{what} declares mixed handling with no authored prose"
            )
    return ComponentBody(
        handling=handling,
        facts=facts,
        semantic_key=semantic_key,
        authored_prose=authored_prose,
        applies_when=applies_when,
        options=options,
        fact_qualifiers=fact_qualifiers,
        recurs=_build_recurrence(value.get("recurs"), what),
    )


def _build_recurrence(value: object, what: str) -> Recurrence | None:
    """Rebuild one cadence from patch JSON, or ``None``.

    The same two gates in the same order as every other structure here: the
    closed key set first, then the typed contract that owns the invariants — a
    turn boundary needs a ``whose`` and a day boundary may not carry one. This
    is a third reader of those rules, never a third copy.
    """
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise InvalidPatchError(f"{what} recurs must be an object or null")
    _require_keys(
        dict(value), {"boundary"}, f"{what} recurs", optional=frozenset({"whose"})
    )
    try:
        built = Recurrence(
            boundary=RecurrenceBoundary(value["boundary"]),
            whose=(None if value.get("whose") is None else RollActor(value["whose"])),
        )
    except (TypeError, ValueError) as exc:
        raise InvalidPatchError(f"{what} recurs: {exc}") from exc
    if violations := recurrence_violations(built):
        raise InvalidPatchError(f"{what} recurs: {'; '.join(violations)}")
    return built


def _build_fact_qualifier(value: object, what: str) -> FactQualifier:
    """Rebuild one fact qualifier, refusing anything the projection would.

    ``applies_when`` is required and may not be null: a qualifier that states
    no condition is not a weaker qualifier, it is an entry that means nothing.
    """
    if not isinstance(value, Mapping):
        raise InvalidPatchError(
            f"{what} must be a payload object, got {type(value).__name__}"
        )
    _require_keys(
        value, {"fact_key", "applies_when"}, what, optional=frozenset({"option_key"})
    )
    raw_key = value["fact_key"]
    if type(raw_key) is not str or not raw_key.strip():
        raise InvalidPatchError(f"{what} fact_key must be a non-blank string")
    raw_scope = value.get("option_key", "")
    if type(raw_scope) is not str:
        raise InvalidPatchError(f"{what} option_key must be a string")
    applies_when = _build_applicability(value["applies_when"], what)
    if applies_when is None:
        raise InvalidPatchError(f"{what} states no condition")
    return FactQualifier(
        fact_key=raw_key, option_key=raw_scope, applies_when=applies_when
    )


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


def _build_prose_text(payload: Mapping[str, Any], what: str) -> str:
    raw = payload["text"]
    if type(raw) is not str or not raw.strip():
        raise InvalidPatchError(f"{what} text must be a non-blank string")
    return raw


def _build_replace_prose(payload: Mapping[str, Any]) -> ProseReplacementPatch:
    _require_keys(payload, {"patch", "text"}, "replace_prose")
    return ProseReplacementPatch(text=_build_prose_text(payload, "replace_prose"))


def _build_append_prose(payload: Mapping[str, Any]) -> ProseAdditionPatch:
    _require_keys(payload, {"patch", "text"}, "append_prose")
    return ProseAdditionPatch(text=_build_prose_text(payload, "append_prose"))


_PATCH_BUILDERS: dict[PatchFamily, Any] = {
    PatchFamily.DISABLE: _build_disable,
    PatchFamily.REPLACE_RECORD: _build_replace_record,
    PatchFamily.REPLACE_COMPONENT: _build_replace_component,
    PatchFamily.REPLACE_FACT: _build_replace_fact,
    PatchFamily.REPLACE_PROSE: _build_replace_prose,
    PatchFamily.APPEND_COMPONENT: _build_append_component,
    PatchFamily.APPEND_FACT: _build_append_fact,
    PatchFamily.APPEND_PROSE: _build_append_prose,
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
    # Load-bearing: omitting authored_prose here would let two REPLACE/APPEND
    # component patches differing only in authored text canonicalize to
    # identical bytes and silently share an override-set UUID.
    payload["authored_prose"] = body.authored_prose
    # The schema-2 fields are emitted only when they carry meaning. Emitting
    # them unconditionally as null/[] would remint the identity of every
    # component patch already authored against an unconditional direct-fact
    # component — the same authority under a new identifier, no longer naming
    # the retained version it was recorded against. The parser accepts an
    # absent field and an explicit legacy default identically, so the two
    # spellings canonicalize to one payload and one identity.
    if body.applies_when is not None:
        payload["applies_when"] = applicability_payload(body.applies_when)
    if body.options:
        # Options by their own key, and each option's facts by content-derived
        # fact key — the same ordering rule the top-level facts already use and
        # the same one projection.py applies. Authoring order is not meaning,
        # and letting it through would mint two identities for one choice.
        payload["options"] = [
            {
                "semantic_key": option.semantic_key,
                "facts": [fact_payload(f) for f in sorted(option.facts, key=fact_key)],
                "applies_when": applicability_payload(option.applies_when),
            }
            for option in sorted(body.options, key=lambda o: o.semantic_key)
        ]
    if body.fact_qualifiers:
        # By the scope they address, for the same reason facts and options are
        # ordered by theirs: authoring order is not meaning. Omitted entirely
        # when empty, so a patch authored before schema 3 keeps its exact bytes
        # and its override-set identity.
        payload["fact_qualifiers"] = [
            {
                "fact_key": q.fact_key,
                "option_key": q.option_key,
                "applies_when": applicability_payload(q.applies_when),
            }
            for q in sorted(
                body.fact_qualifiers, key=lambda q: (q.option_key, q.fact_key)
            )
        ]
    if body.recurs is not None:
        # Omitted when absent, like every other post-legacy key here: a patch
        # authored before schema 4 keeps its exact bytes and its override-set
        # identity. Serialized through the representation's own walker, so the
        # patch and the projection cannot disagree about a cadence's canonical
        # form.
        payload["recurs"] = recurrence_payload(body.recurs)
    return payload


def patch_payload(patch: MechanicalPatch) -> dict[str, object]:
    """Canonical identity-bearing payload of one typed patch.

    This is what the override-set identity is derived from, so it must be a
    complete and order-stable statement of the patch's content — a payload that
    dropped a field would let two different patches share an identity. Every
    branch is explicit, with no bare fallthrough, so the closed union stays
    exhaustive as a type-checking property rather than an implicit one.
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
    if isinstance(patch, ProseReplacementPatch):
        return {"patch": PatchFamily.REPLACE_PROSE.value, "text": patch.text}
    if isinstance(patch, ComponentAdditionPatch):
        return {
            "patch": PatchFamily.APPEND_COMPONENT.value,
            "component": _component_body_payload(patch.body),
        }
    if isinstance(patch, FactAdditionPatch):
        return {
            "patch": PatchFamily.APPEND_FACT.value,
            "fact": fact_payload(patch.fact),
        }
    if isinstance(patch, ProseAdditionPatch):
        return {"patch": PatchFamily.APPEND_PROSE.value, "text": patch.text}
    raise AssertionError(f"unhandled patch type {type(patch).__name__}")
