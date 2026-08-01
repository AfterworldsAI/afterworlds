"""Records, components, typed facts, and provenance — CRD Issue 5d, Decisions 3–4.

Everything here is keyed by **committed semantic keys**, never by position and
never by a derived identity. That ordering is deliberate: ADR-005d Decision 6
requires identity derivation to be acyclic, so the projection identity is
computed from this keyed content and the stable record/component/fact IDs are
derived from that identity afterwards (see :mod:`projection`). Nothing in this
module may contain a derived ID.

The typed fact union is closed. A structure that is not one of the declared
families is rejected — there is no generic dictionary, no expression string, no
numeric key-value bag to fall back on. When a component's meaning cannot be
reduced faithfully into a declared family, the honest answer is to bind exact
governing prose under a closed irreducibility reason, not to widen the union
into something that can hold anything.

The union is deliberately small. Each family below is justified by a required
real-corpus canary in #137, which is the source discovery available today:

* ``ability_check`` — the illusion canary's typed check/DC-source authority;
* ``creature_ability_score`` — the composite-creature canary's ability grid;
* ``spell_descriptor`` — the Wish and spell-scoped-creature canaries; and
* ``progression_entry`` — the class-progression-table canary.

That is not a claim of corpus completeness. Full-corpus accounting has not run
yet, and when it surfaces a substantive family this union cannot represent, the
family is added explicitly here or the affected component is classified honestly
as prose-bound.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, fields
from enum import StrEnum
from typing import Any, ClassVar, cast

from afterworlds.ingestion.corpus.hashing import canonical_bytes, sha256_hex
from afterworlds.ingestion.mechanical.models import ComponentHandling

__all__ = [
    "AbilityCheckFact",
    "AbilityScore",
    "ComponentDraft",
    "CreatureAbilityScoreFact",
    "DcKind",
    "FactFamily",
    "MechanicalFact",
    "ProgressionEntryFact",
    "ProseBindingDraft",
    "ProvenanceClaim",
    "ProvenanceRole",
    "ProvenanceTargetKind",
    "RecordDraft",
    "RecordKind",
    "ReferenceDraft",
    "RelationshipDraft",
    "RelationshipKind",
    "RepresentationDraft",
    "SpellDescriptorFact",
    "SpellSchool",
    "MalformedFactPayloadError",
    "UnknownFactFamilyError",
    "fact_from_payload",
    "fact_invariant_violations",
    "prose_bindings_by_target_key",
    "fact_key",
    "fact_payload",
]


class RecordKind(StrEnum):
    """Closed record vocabulary (#137 contract 3).

    ``CREATURE`` is the record kind for every creature stat block. Source
    ancestry such as *Animals* or *Monsters A–Z* is where a creature was found,
    not what kind of record it is, and rules-defined creature type is a
    descriptor rather than a kind.
    """

    GENERAL_RULE = "general_rule"
    GLOSSARY_RULE = "glossary_rule"
    CHARACTER_CREATION = "character_creation"
    CHARACTER_ADVANCEMENT = "character_advancement"
    CLASS = "class"
    CLASS_FEATURE = "class_feature"
    SPECIES = "species"
    BACKGROUND = "background"
    FEAT = "feat"
    EQUIPMENT = "equipment"
    SPELL = "spell"
    CONDITION = "condition"
    GAMEPLAY_TOOL = "gameplay_tool"
    MAGIC_ITEM = "magic_item"
    CREATURE = "creature"


class RelationshipKind(StrEnum):
    """Closed relationship vocabulary between records."""

    #: A record wholly contained by another, e.g. a spell-scoped stat block.
    SCOPED_WITHIN = "scoped_within"
    #: One record grants another, e.g. a progression level granting a feature.
    GRANTS = "grants"
    #: One record is required before another applies.
    PREREQUISITE = "prerequisite"


class ProvenanceTargetKind(StrEnum):
    """What a provenance claim attaches source text to."""

    RECORD = "record"
    COMPONENT = "component"
    FACT = "fact"
    PROSE_BINDING = "prose_binding"
    RELATIONSHIP = "relationship"
    REFERENCE = "reference"


class ProvenanceRole(StrEnum):
    """Whether a span *states* the claim or merely supports it.

    Contextual claims may overlap freely — several components can legitimately
    draw context from one sentence. Two primary claims over the same span
    cannot: that is two structures both asserting they are what the text says.
    """

    PRIMARY = "primary"
    CONTEXTUAL = "contextual"


class AbilityScore(StrEnum):
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"


class SpellSchool(StrEnum):
    ABJURATION = "abjuration"
    CONJURATION = "conjuration"
    DIVINATION = "divination"
    ENCHANTMENT = "enchantment"
    EVOCATION = "evocation"
    ILLUSION = "illusion"
    NECROMANCY = "necromancy"
    TRANSMUTATION = "transmutation"


class DcKind(StrEnum):
    """Where a check's difficulty class comes from.

    A missing source value is never invented: ``FIXED`` is the only kind that
    carries a number, and the others say *where the number comes from* rather
    than guessing one.
    """

    FIXED = "fixed"
    SPELL_SAVE_DC = "spell_save_dc"
    CONTESTED = "contested"
    GAMEMASTER_SET = "gamemaster_set"


class FactFamily(StrEnum):
    """The closed typed-fact union's discriminator."""

    ABILITY_CHECK = "ability_check"
    CREATURE_ABILITY_SCORE = "creature_ability_score"
    SPELL_DESCRIPTOR = "spell_descriptor"
    PROGRESSION_ENTRY = "progression_entry"


@dataclass(frozen=True)
class AbilityCheckFact:
    """A check or save with a typed DC source."""

    FAMILY: ClassVar[FactFamily] = FactFamily.ABILITY_CHECK

    ability: AbilityScore
    dc_kind: DcKind
    dc_value: int | None = None


@dataclass(frozen=True)
class CreatureAbilityScoreFact:
    """One cell of a creature's ability grid."""

    FAMILY: ClassVar[FactFamily] = FactFamily.CREATURE_ABILITY_SCORE

    ability: AbilityScore
    score: int


@dataclass(frozen=True)
class SpellDescriptorFact:
    """The typed descriptors a spell record carries.

    Casting time, range, and duration are deliberately absent: representing
    them faithfully needs their own typed families, and holding them as free
    text here would be the untyped escape hatch this union exists to prevent.
    Until those families are justified by accounting, that authority is
    prose-bound.
    """

    FAMILY: ClassVar[FactFamily] = FactFamily.SPELL_DESCRIPTOR

    level: int
    school: SpellSchool
    ritual: bool
    concentration: bool


@dataclass(frozen=True)
class ProgressionEntryFact:
    """One level-indexed entitlement from a progression table."""

    FAMILY: ClassVar[FactFamily] = FactFamily.PROGRESSION_ENTRY

    level: int
    entitlement_key: str
    quantity: int | None = None


MechanicalFact = (
    AbilityCheckFact
    | CreatureAbilityScoreFact
    | SpellDescriptorFact
    | ProgressionEntryFact
)

_FACT_TYPES: dict[FactFamily, type] = {
    FactFamily.ABILITY_CHECK: AbilityCheckFact,
    FactFamily.CREATURE_ABILITY_SCORE: CreatureAbilityScoreFact,
    FactFamily.SPELL_DESCRIPTOR: SpellDescriptorFact,
    FactFamily.PROGRESSION_ENTRY: ProgressionEntryFact,
}


class UnknownFactFamilyError(TypeError):
    """Raised when a structure outside the closed union is offered as a fact."""


class MalformedFactPayloadError(ValueError):
    """Raised when a persisted payload cannot rebuild its declared family."""


# ---------------------------------------------------------------------------
# Intrinsic family invariants
# ---------------------------------------------------------------------------
#
# Class membership is not validity. A fact can belong to the closed union and
# still contradict its own declared contract, and such a fact would persist as
# mechanically unusable authority. Each family therefore declares its intrinsic
# invariants here, next to the family itself, so adding a family without
# thinking about its invariants is a visible omission rather than a silent one.
#
# Only constraints intrinsic to the declared fields belong here. Corpus-specific
# limits — the SRD's 0–9 spell levels, its 1–30 ability scores — are policy about
# a particular Rules Package, not properties of the type, and enforcing them here
# would make the union quietly SRD-only. Bounds below are limited to what the
# field's own meaning requires: an ordinal or magnitude cannot be negative, a
# semantic key cannot be blank, and a stated quantity cannot be zero or less.


# Shared primitive checks. Python's ``bool`` is a subclass of ``int``, so a bare
# ``isinstance(value, int)`` accepts ``True`` — and a string like ``"false"`` is
# truthy, so a mistyped Boolean silently inverts a rule downstream. Every
# integer check below therefore excludes ``bool`` explicitly, and no check ever
# coerces: ``"12"`` is not 12, ``1`` is not ``True``, and normalizing either
# would be inventing authority the source never stated.


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _int_field(value: object, field: str) -> list[str]:
    if not _is_int(value):
        return [f"{field} must be an integer, got {type(value).__name__} {value!r}"]
    return []


def _optional_int_field(value: object, field: str) -> list[str]:
    if value is None:
        return []
    return _int_field(value, field)


def _bool_field(value: object, field: str) -> list[str]:
    if not isinstance(value, bool):
        return [f"{field} must be a boolean, got {type(value).__name__} {value!r}"]
    return []


def _str_field(value: object, field: str) -> list[str]:
    if not isinstance(value, str) or isinstance(value, StrEnum):
        return [f"{field} must be a string, got {type(value).__name__} {value!r}"]
    return []


def _enum_field(value: object, enum_cls: type[StrEnum], field: str) -> list[str]:
    """The field must hold the declared enum member, not a look-alike string.

    ``StrEnum`` members *are* strings, so a plain ``"wisdom"`` would satisfy a
    string check while carrying none of the enum's guarantees.
    """
    if not isinstance(value, enum_cls):
        return [
            f"{field} must be {enum_cls.__name__}, got "
            f"{type(value).__name__} {value!r}"
        ]
    return []


def _check_ability_check(fact: AbilityCheckFact) -> list[str]:
    findings = [
        *_enum_field(fact.ability, AbilityScore, "ability"),
        *_enum_field(fact.dc_kind, DcKind, "dc_kind"),
        *_optional_int_field(fact.dc_value, "dc_value"),
    ]
    if findings:
        # The DC relationship below reads dc_kind and dc_value; checking it
        # against mistyped values would report a second, misleading violation.
        return findings
    if fact.dc_kind is DcKind.FIXED:
        if fact.dc_value is None:
            findings.append("fixed DC without a dc_value")
    elif fact.dc_value is not None:
        findings.append(
            f"{fact.dc_kind.value} DC carries dc_value {fact.dc_value}; the "
            "value comes from the named source, not from the fact"
        )
    return findings


def _check_creature_ability_score(fact: CreatureAbilityScoreFact) -> list[str]:
    findings = [
        *_enum_field(fact.ability, AbilityScore, "ability"),
        *_int_field(fact.score, "score"),
    ]
    if findings:
        return findings
    if fact.score < 0:
        findings.append(f"negative ability score {fact.score}")
    return findings


def _check_spell_descriptor(fact: SpellDescriptorFact) -> list[str]:
    findings = [
        *_int_field(fact.level, "level"),
        *_enum_field(fact.school, SpellSchool, "school"),
        *_bool_field(fact.ritual, "ritual"),
        *_bool_field(fact.concentration, "concentration"),
    ]
    if findings:
        return findings
    if fact.level < 0:
        findings.append(f"negative spell level {fact.level}")
    return findings


def _check_progression_entry(fact: ProgressionEntryFact) -> list[str]:
    findings = [
        *_int_field(fact.level, "level"),
        *_str_field(fact.entitlement_key, "entitlement_key"),
        *_optional_int_field(fact.quantity, "quantity"),
    ]
    if findings:
        return findings
    if fact.level < 0:
        findings.append(f"negative progression level {fact.level}")
    if not fact.entitlement_key.strip():
        findings.append("progression entry without an entitlement key")
    if fact.quantity is not None and fact.quantity < 1:
        findings.append(f"progression quantity {fact.quantity} grants nothing")
    return findings


_FACT_INVARIANTS: dict[FactFamily, Callable[[Any], list[str]]] = {
    FactFamily.ABILITY_CHECK: _check_ability_check,
    FactFamily.CREATURE_ABILITY_SCORE: _check_creature_ability_score,
    FactFamily.SPELL_DESCRIPTOR: _check_spell_descriptor,
    FactFamily.PROGRESSION_ENTRY: _check_progression_entry,
}


def fact_invariant_violations(fact: object) -> tuple[str, ...]:
    """Return violations of *fact*'s own family contract.

    Membership of the closed union is checked first: an unknown family has no
    invariants to check because it has no contract.
    """
    family = getattr(fact, "FAMILY", None)
    if not isinstance(family, FactFamily) or _FACT_TYPES.get(family) is not type(fact):
        return (
            f"{type(fact).__name__} is not a member of the closed typed-fact union",
        )
    return tuple(_FACT_INVARIANTS[family](fact))


# JSON-side primitive checks. A persisted payload arrives as plain JSON values,
# so each builder states the exact primitive shape it accepts before it
# constructs anything. Nothing is coerced: ``"12"`` stays a string and fails,
# because turning it into 12 would be this layer inventing a mechanical value
# the persisted row does not contain.


def _json_enum(value: object, enum_cls: type[StrEnum], field: str) -> list[str]:
    """The stored value must be a plain string naming a declared member."""
    if type(value) is not str:
        return [
            f"{field} must be a string {enum_cls.__name__} value, got "
            f"{type(value).__name__} {value!r}"
        ]
    try:
        enum_cls(value)
    except ValueError:
        return [f"{field} {value!r} is not a declared {enum_cls.__name__}"]
    return []


def _reject(family: FactFamily, findings: list[str]) -> None:
    if findings:
        raise MalformedFactPayloadError(
            f"{family.value} payload has mistyped fields: {'; '.join(findings)}"
        )


def _build_ability_check(p: Mapping[str, Any]) -> AbilityCheckFact:
    _reject(
        FactFamily.ABILITY_CHECK,
        [
            *_json_enum(p["ability"], AbilityScore, "ability"),
            *_json_enum(p["dc_kind"], DcKind, "dc_kind"),
            *_optional_int_field(p["dc_value"], "dc_value"),
        ],
    )
    return AbilityCheckFact(
        ability=AbilityScore(p["ability"]),
        dc_kind=DcKind(p["dc_kind"]),
        dc_value=p["dc_value"],
    )


def _build_creature_ability_score(p: Mapping[str, Any]) -> CreatureAbilityScoreFact:
    _reject(
        FactFamily.CREATURE_ABILITY_SCORE,
        [
            *_json_enum(p["ability"], AbilityScore, "ability"),
            *_int_field(p["score"], "score"),
        ],
    )
    return CreatureAbilityScoreFact(
        ability=AbilityScore(p["ability"]), score=p["score"]
    )


def _build_spell_descriptor(p: Mapping[str, Any]) -> SpellDescriptorFact:
    _reject(
        FactFamily.SPELL_DESCRIPTOR,
        [
            *_int_field(p["level"], "level"),
            *_json_enum(p["school"], SpellSchool, "school"),
            *_bool_field(p["ritual"], "ritual"),
            *_bool_field(p["concentration"], "concentration"),
        ],
    )
    return SpellDescriptorFact(
        level=p["level"],
        school=SpellSchool(p["school"]),
        ritual=p["ritual"],
        concentration=p["concentration"],
    )


def _build_progression_entry(p: Mapping[str, Any]) -> ProgressionEntryFact:
    _reject(
        FactFamily.PROGRESSION_ENTRY,
        [
            *_int_field(p["level"], "level"),
            *_str_field(p["entitlement_key"], "entitlement_key"),
            *_optional_int_field(p["quantity"], "quantity"),
        ],
    )
    return ProgressionEntryFact(
        level=p["level"],
        entitlement_key=p["entitlement_key"],
        quantity=p["quantity"],
    )


_FACT_BUILDERS: dict[FactFamily, Callable[[Mapping[str, Any]], MechanicalFact]] = {
    FactFamily.ABILITY_CHECK: _build_ability_check,
    FactFamily.CREATURE_ABILITY_SCORE: _build_creature_ability_score,
    FactFamily.SPELL_DESCRIPTOR: _build_spell_descriptor,
    FactFamily.PROGRESSION_ENTRY: _build_progression_entry,
}


def fact_from_payload(
    payload: Mapping[str, Any], *, declared_family: str | None = None
) -> MechanicalFact:
    """Rebuild a typed fact from its persisted payload.

    Strict by design. A persisted payload is only authority if it still says
    exactly what it said when it was written, so this rejects rather than
    repairs:

    * an unknown family — not a forward-compatible unknown, but a fact this
      build cannot honestly represent;
    * a missing field, which would otherwise rebuild into a fact with a
      silently defaulted value;
    * an extra field, which would otherwise be dropped, hiding whatever was
      added to the row; and
    * a payload discriminator that disagrees with the column that stores it
      alongside — one of the two has been rewritten, and guessing which is
      not reconstruction.

    Explicit per-family builders rather than reflection, so each family states
    the exact field set it accepts.
    """
    raw = payload.get("family")
    try:
        family = FactFamily(str(raw))
    except ValueError:
        raise UnknownFactFamilyError(
            f"{raw!r} is not a member of the closed typed-fact union"
        ) from None

    if declared_family is not None and declared_family != family.value:
        raise MalformedFactPayloadError(
            f"persisted family {declared_family!r} disagrees with payload family "
            f"{family.value!r}"
        )

    expected = {f.name for f in fields(_FACT_TYPES[family])} | {"family"}
    supplied = set(payload)
    if missing := sorted(expected - supplied):
        raise MalformedFactPayloadError(f"{family.value} payload is missing {missing}")
    if extra := sorted(supplied - expected):
        raise MalformedFactPayloadError(f"{family.value} payload carries extra {extra}")

    try:
        return _FACT_BUILDERS[family](payload)
    except (TypeError, ValueError) as exc:
        raise MalformedFactPayloadError(
            f"{family.value} payload does not rebuild its declared family: {exc}"
        ) from exc


def fact_key(fact: object) -> str:
    """Stable content-derived key for one fact within its component.

    Derived from the canonical payload, never from a position in the component's
    fact tuple, so reordering or inserting a sibling fact cannot churn it.
    """
    return sha256_hex(canonical_bytes(fact_payload(fact)))[:16]


def fact_payload(fact: object) -> dict[str, object]:
    """Canonical payload for one typed fact.

    Raises rather than returning findings: an unknown family has no canonical
    form, so there is nothing honest to serialize. Callers that want a
    collected report use :func:`validation.validate_representation`.
    """
    family = getattr(fact, "FAMILY", None)
    if not isinstance(family, FactFamily) or _FACT_TYPES.get(family) is not type(fact):
        raise UnknownFactFamilyError(
            f"{type(fact).__name__} is not a member of the closed typed-fact union"
        )
    # Safe now: the family check above proved *fact* is one of the declared
    # frozen dataclasses, which is what asdict needs.
    payload: dict[str, object] = {"family": family.value}
    for key, value in sorted(asdict(cast(Any, fact)).items()):
        payload[key] = value.value if isinstance(value, StrEnum) else value
    return payload


# ---------------------------------------------------------------------------
# Keyed drafts — semantic keys only, no derived identities
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecordDraft:
    """A semantic record assembled from accepted membership.

    ``parent_key`` is set for a nested record — the complete creature stat block
    embedded in spell authority is a record in its own right, not a copy.
    """

    semantic_key: str
    kind: RecordKind
    parent_key: str | None = None


@dataclass(frozen=True)
class ComponentDraft:
    """One publishable component of a record."""

    record_key: str
    semantic_key: str
    handling: ComponentHandling
    #: Required for PROSE_BOUND and MIXED; must name a closed catalog reason.
    irreducibility_reason_code: str | None = None
    facts: tuple[MechanicalFact, ...] = ()


@dataclass(frozen=True)
class ProseBindingDraft:
    """Exact governing prose for a component, bound to the 5c chunk that holds it.

    Resolution goes through the authoritative ``RuleChunk`` rather than copying
    text into a second prose store, so there is exactly one authority for what
    the source says.
    """

    component_key: str
    record_key: str
    chunk_id: str
    irreducibility_reason_code: str


@dataclass(frozen=True)
class RelationshipDraft:
    """A typed relationship between two records."""

    source_record_key: str
    target_record_key: str
    kind: RelationshipKind


@dataclass(frozen=True)
class ReferenceDraft:
    """A source-authored mechanical reference resolved at build time.

    ``scope_key`` is the committed source scope the reference was resolved
    within, which is what makes a repeated name resolvable: the same wording in
    two scopes is two references, not one ambiguity.
    """

    from_record_key: str
    from_component_key: str
    source_text: str
    scope_key: str
    target_record_key: str


@dataclass(frozen=True)
class ProvenanceClaim:
    """An exact 5c leaf-subspan claim by one representation element."""

    target_kind: ProvenanceTargetKind
    target_key: tuple[str, ...]
    span_id: str
    role: ProvenanceRole


@dataclass(frozen=True)
class RepresentationDraft:
    """The complete keyed representation for one candidate projection."""

    records: tuple[RecordDraft, ...]
    components: tuple[ComponentDraft, ...]
    prose_bindings: tuple[ProseBindingDraft, ...]
    relationships: tuple[RelationshipDraft, ...]
    references: tuple[ReferenceDraft, ...]
    provenance: tuple[ProvenanceClaim, ...]


# ---------------------------------------------------------------------------
# Canonical provenance target identities
# ---------------------------------------------------------------------------
#
# One definition per target kind, used everywhere a target is enumerated,
# required, claimed, or checked. Building these tuples inline in more than one
# place is how a key drifts: the enumerator and the validator then disagree
# about what "the same element" means, and a claim can match an element it was
# never about.
#
# Each key must identify exactly one declared element. Two elements that differ
# semantically must not share a key — that is why a prose binding carries its
# chunk and reason (one component may bind several passages) and a reference
# carries its owning component (the same wording in one scope may be cited by
# more than one component).


def record_target_key(record: RecordDraft) -> tuple[str, ...]:
    """Provenance key of a record."""
    return (record.semantic_key,)


def component_target_key(component: ComponentDraft) -> tuple[str, ...]:
    """Provenance key of a component."""
    return (component.record_key, component.semantic_key)


def fact_target_key(
    record_key: str, component_key: str, fact: object
) -> tuple[str, ...]:
    """Provenance key of one typed fact, keyed by content rather than position."""
    return (record_key, component_key, fact_key(fact))


def prose_binding_target_key(binding: ProseBindingDraft) -> tuple[str, ...]:
    """Provenance key of one prose binding.

    ``(record_key, component_key)`` alone cannot address a component that binds
    more than one passage, so the bound chunk and the reason it is bound are
    part of the identity.
    """
    return (
        binding.record_key,
        binding.component_key,
        binding.chunk_id,
        binding.irreducibility_reason_code,
    )


def relationship_target_key(relationship: RelationshipDraft) -> tuple[str, ...]:
    """Provenance key of one typed relationship."""
    return (
        relationship.source_record_key,
        relationship.target_record_key,
        relationship.kind.value,
    )


def reference_target_key(reference: ReferenceDraft) -> tuple[str, ...]:
    """Provenance key of one resolved reference, including its source ownership."""
    return (
        reference.from_record_key,
        reference.from_component_key,
        reference.source_text,
        reference.scope_key,
        reference.target_record_key,
    )


def prose_bindings_by_target_key(
    draft: RepresentationDraft,
) -> dict[tuple[str, ...], ProseBindingDraft]:
    """Map each prose binding's provenance key back to the binding itself.

    Provenance validation needs the binding, not just its key, to check that a
    claimed span lies inside the chunk that binding names. Recovering it
    through the same key function keeps one definition of "the same element".
    """
    return {prose_binding_target_key(b): b for b in draft.prose_bindings}


def declared_provenance_targets(
    draft: RepresentationDraft,
) -> dict[ProvenanceTargetKind, set[tuple[str, ...]]]:
    """Every element a provenance claim may legitimately name.

    Facts whose family is unknown are omitted: they have no content-derived key,
    and they are reported separately as facts outside the closed union.
    """
    facts: set[tuple[str, ...]] = set()
    for component in draft.components:
        for fact in component.facts:
            try:
                facts.add(
                    fact_target_key(component.record_key, component.semantic_key, fact)
                )
            except UnknownFactFamilyError:
                continue

    return {
        ProvenanceTargetKind.RECORD: {record_target_key(r) for r in draft.records},
        ProvenanceTargetKind.COMPONENT: {
            component_target_key(c) for c in draft.components
        },
        ProvenanceTargetKind.FACT: facts,
        ProvenanceTargetKind.PROSE_BINDING: {
            prose_binding_target_key(b) for b in draft.prose_bindings
        },
        ProvenanceTargetKind.RELATIONSHIP: {
            relationship_target_key(r) for r in draft.relationships
        },
        ProvenanceTargetKind.REFERENCE: {
            reference_target_key(r) for r in draft.references
        },
    }


#: Element kinds that must each carry their own provenance (ADR-005d Decision 3).
#: Records and components are deliberately absent: their obligation is span
#: coverage under the classification contract, not a per-element edge, and
#: conflating the two would let a component claim stand in for the traceability
#: of every fact beneath it.
PROVENANCE_REQUIRED_KINDS: tuple[ProvenanceTargetKind, ...] = (
    ProvenanceTargetKind.FACT,
    ProvenanceTargetKind.PROSE_BINDING,
    ProvenanceTargetKind.RELATIONSHIP,
    ProvenanceTargetKind.REFERENCE,
)
