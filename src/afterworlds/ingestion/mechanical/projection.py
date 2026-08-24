"""Projection identity and candidate assembly — CRD Issue 5d, Decisions 6 and 8.

Identity derivation is acyclic, and the order matters:

1. the **payload** is assembled from the exact 5c release binding, the accepted
   classification, the declared semantic policy, and the keyed representation —
   semantic keys only, no derived identity anywhere inside it;
2. the **projection UUID** is content-derived from that payload; then
3. stable record, component, and fact IDs are derived from the projection UUID
   plus their committed semantic keys.

Doing it the other way — putting derived IDs into the payload the UUID is
computed from — would be circular, and deriving IDs from list positions would
churn every identity whenever an unrelated sibling was inserted.

**A computed identity is not a publishable projection.** This module can
identify any candidate, including a dishonest one; that is what makes the
identity useful for comparing candidates at all. Before a projection may be
published or activated, every one of these must succeed: the declared policy
binding, the span partition, explicit acceptance, representation validation,
persistence reconstruction, and the later exact completeness gate.
:func:`validate_candidate` covers the first four; the rest belong to the
persistence and gate layers. Nothing here activates anything.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from afterworlds.ingestion.corpus.hashing import content_id, hash_obj
from afterworlds.ingestion.mechanical.accounting import (
    classification_payload,
    validate_acceptance,
    validate_partition,
    validate_policy_binding,
    validate_reason_codes,
)
from afterworlds.ingestion.mechanical.bound_corpus import BoundCorpusSnapshot
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.models import ClassificationLedger
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    Applicability,
    ComponentDraft,
    Recurrence,
    RepresentationDraft,
    _dataclass_payload,
    fact_key,
    fact_payload,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import validate_representation

__all__ = [
    "applicability_payload",
    "recurrence_payload",
    "IdentifiedProjection",
    "ProjectionCandidate",
    "ReleaseBinding",
    "derive_component_id",
    "derive_fact_id",
    "derive_record_id",
    "identify_projection",
    "projection_payload",
    "projection_uuid",
    "release_binding_payload",
    "representation_payload",
    "validate_candidate",
    "LegacySchemaPayloadError",
    "SCHEMA_1_VERSION",
    "SCHEMA_2_VERSION",
    "SCHEMA_3_VERSION",
    "SCHEMA_4_VERSION",
    "UnsupportedSchemaVersionError",
    "validate_schema_binding",
]


@dataclass(frozen=True)
class ReleaseBinding:
    """The exact published 5c release a projection is built over (#137 contract 1).

    All six values are required. A matching slug, display name, source label, or
    filename is not a binding — these are the reconstructable proof identities
    CRD Issue 5c already publishes, so a projection cannot claim a release it
    was not actually built from.
    """

    package_uuid: str
    release_version: str
    authoritative_source_hash: str
    transform_config_hash: str
    bundle_root_hash: str
    persisted_corpus_digest: str


@dataclass(frozen=True)
class ProjectionCandidate:
    """A built-but-unproven projection: identifiable, not yet publishable.

    ``schema_version``/``schema_hash`` are the candidate's own declaration of
    the closed representation contract it was built under, exactly as
    :class:`~.models.ClassificationLedger` declares the semantic policy it was
    accepted under. Declared rather than read from current constants, so a
    projection reconstructed in a year states the union it was built against
    instead of being silently re-identified under whatever the union has since
    become.
    """

    binding: ReleaseBinding
    classification: ClassificationLedger
    representation: RepresentationDraft
    schema_version: str
    schema_hash: str


def release_binding_payload(binding: ReleaseBinding) -> dict[str, object]:
    """Canonical payload of the 5c release binding."""
    return {
        "package_uuid": binding.package_uuid,
        "release_version": binding.release_version,
        "authoritative_source_hash": binding.authoritative_source_hash,
        "transform_config_hash": binding.transform_config_hash,
        "bundle_root_hash": binding.bundle_root_hash,
        "persisted_corpus_digest": binding.persisted_corpus_digest,
    }


#: The representation schema version whose canonical component payload had no
#: ``applies_when`` and no ``options`` keys at all. Schema 2 added both, so a
#: projection persisted under schema 1 must still serialize without them or it
#: re-identifies as a different projection.
SCHEMA_1_VERSION = "5d-representation-schema-1"
#: Schema 2 added ``applies_when`` and ``options``; schema 3 added
#: ``fact_qualifiers`` beside them. Each merged version is named here because
#: each one is a contract something may already be persisted under.
SCHEMA_2_VERSION = "5d-representation-schema-2"
SCHEMA_3_VERSION = "5d-representation-schema-3"
SCHEMA_4_VERSION = "5d-representation-schema-4"


class LegacySchemaPayloadError(ValueError):
    """Raised when a candidate carries meaning its declared schema cannot hold.

    Omitting a *default* field to reproduce an old identity is compatibility;
    omitting a field that carries meaning would be forging one. A schema-1
    declaration holding a real qualifier or a real option set, or a schema-2
    one holding a real fact qualifier, is a state that cannot honestly be
    serialized under either contract, so it fails closed.
    """


class UnsupportedSchemaVersionError(ValueError):
    """Raised when a payload is requested under a version this build cannot serialize.

    Distinct from :class:`LegacySchemaPayloadError` on purpose. That one means
    *this draft* says more than the named contract can hold; this one means the
    contract itself is unknown, so nothing can be said about what it holds. A
    caller reconstructing historical state must not have an unrecognised
    version quietly fall through to current-schema behaviour and derive an
    identity under a contract that was never asked for.
    """

    def __init__(self, schema_version: str) -> None:
        super().__init__(
            f"representation schema {schema_version!r} is not a version this "
            f"build can serialize; known versions are "
            f"{sorted(_MERGED_COMPONENT_FIELDS)}"
        )
        self.schema_version = schema_version


@dataclass(frozen=True)
class _VersionedComponentField:
    """One component payload key, and the version that introduced it.

    ``holds_meaning`` is what makes omission honest. The rule the schema-1
    branch established and this generalises: *the code that decides to drop a
    field is the code that must prove the field is empty*, or the two drift
    into silently discarding meaning. Keeping the emitter and the proof on the
    same object is what stops the next added field from acquiring one without
    the other.
    """

    key: str
    #: Named in the refusal so the message says which contract introduced the
    #: field, not merely that some field was too new.
    introduced_in: str
    payload: Callable[[ComponentDraft], object]
    holds_meaning: Callable[[ComponentDraft], bool]
    #: Post-schema-3 keys are omitted when they carry no meaning, so an
    #: inherited schema-3 component is byte-identical under a later schema —
    #: Owner Decision 2026-08-24. Schema 1-3 keys keep unconditional emission:
    #: the committed conditions-1 artifact contains "applies_when": null, so
    #: omitting it would move the identity this rule exists to hold still.
    omit_when_empty: bool = False


_COMPONENT_FIELDS: tuple[_VersionedComponentField, ...] = (
    _VersionedComponentField(
        key="applies_when",
        introduced_in="schema-2",
        payload=lambda c: applicability_payload(c.applies_when),
        holds_meaning=lambda c: c.applies_when is not None,
    ),
    _VersionedComponentField(
        key="options",
        introduced_in="schema-2",
        # Options are canonically ordered by their key, so the source's order
        # of "crawl or ... right yourself" does not reach the payload hash:
        # the source states no precedence between them.
        payload=lambda c: canonical_order(
            {
                "semantic_key": o.semantic_key,
                "facts": canonical_order(fact_payload(f) for f in o.facts),
                "applies_when": applicability_payload(o.applies_when),
            }
            for o in c.options
        ),
        holds_meaning=lambda c: bool(c.options),
    ),
    _VersionedComponentField(
        key="fact_qualifiers",
        introduced_in="schema-3",
        # Keyed by the fact they qualify and its scope, so canonical ordering
        # is over meaning rather than authoring order — the same rule every
        # other collection in this payload follows.
        payload=lambda c: canonical_order(
            {
                "fact_key": q.fact_key,
                "option_key": q.option_key,
                "applies_when": applicability_payload(q.applies_when),
            }
            for q in c.fact_qualifiers
        ),
        holds_meaning=lambda c: bool(c.fact_qualifiers),
    ),
    _VersionedComponentField(
        key="recurs",
        introduced_in="schema-4",
        payload=lambda c: recurrence_payload(c.recurs),
        holds_meaning=lambda c: c.recurs is not None,
        omit_when_empty=True,
    ),
)

#: Every merged representation schema version, and the component payload keys
#: *that* version emits beyond the five schema 1 already had.
#:
#: A registry rather than a chain of version comparisons. Each merged contract
#: is a thing state may already be persisted under, so each states its own key
#: set explicitly and a later succession cannot silently redefine an earlier
#: one. Written as literals for the same reason: keying the current row by
#: ``REPRESENTATION_SCHEMA_VERSION`` would make schema 4 quietly inherit schema
#: 3's row and delete schema 3's, which is the exact failure this table exists
#: to prevent.
_MERGED_COMPONENT_FIELDS: dict[str, frozenset[str]] = {
    SCHEMA_1_VERSION: frozenset(),
    SCHEMA_2_VERSION: frozenset({"applies_when", "options"}),
    SCHEMA_3_VERSION: frozenset({"applies_when", "options", "fact_qualifiers"}),
    # Its own row, written out rather than inherited. Schema 4's post-schema-3
    # additions are all *fact and value-object* fields, which the representation
    # walker omits when empty; no component key joins the set here. A component
    # key that does join it later must be added to this row explicitly.
    SCHEMA_4_VERSION: frozenset(
        {"applies_when", "options", "fact_qualifiers", "recurs"}
    ),
}

# Minting a new schema without giving it a row here would leave the current
# contract unserializable rather than silently wrong, which is the direction
# this whole module fails in.
assert REPRESENTATION_SCHEMA_VERSION in _MERGED_COMPONENT_FIELDS, (
    f"representation schema {REPRESENTATION_SCHEMA_VERSION!r} declares no "
    "component key set; add its row to _MERGED_COMPONENT_FIELDS"
)


def _emitted_component_fields(schema_version: str) -> frozenset[str]:
    """The component keys *schema_version* emits, or fail closed.

    Resolved once per payload rather than per component, so a draft with no
    components still refuses an unknown version instead of serializing an empty
    component list under a contract nobody recognises.
    """
    try:
        return _MERGED_COMPONENT_FIELDS[schema_version]
    except KeyError:
        raise UnsupportedSchemaVersionError(schema_version) from None


def _component_versioned_payload(
    component: ComponentDraft, schema_version: str, emitted: frozenset[str]
) -> dict[str, object]:
    """The post-schema-1 component keys *this* schema version emits.

    Owner Decision 2026-08-20 (Option A) established the rule at the
    ``0027 -> 0028`` boundary: a projection persisted under schema 1 must still
    reconstruct with its original UUID, payload hash, derived IDs, and recorded
    digest after the upgrade. Its canonical wire payload never had those keys,
    so emitting them — even as ``null`` and ``[]`` — re-identifies unchanged
    historical state as a different projection and makes
    ``verify_persisted_state`` reject it.

    The rule is general, not a schema-1 exception: **every** merged version
    serializes exactly its own key set. Schema 3 proved why. It added
    ``fact_qualifiers`` with only a schema-1 branch in place, so schema-2
    payloads silently gained a key their merged contract never had and
    re-identified the same way schema 1 once did.

    This preserves historical *reconstruction* only. It does not revoke #137's
    clean-baseline policy, does not establish general legacy compatibility, and
    does not make a superseded projection activatable —
    ``validate_schema_binding`` still refuses one as current authority,
    unchanged.

    The omission and the fail-closed check are the same loop on purpose: the
    code that decides to drop a field is the code that must prove the field is
    empty, or the two could drift into silently discarding meaning.
    """
    payload: dict[str, object] = {}
    for field in _COMPONENT_FIELDS:
        if field.omit_when_empty and not field.holds_meaning(component):
            # Absent and default say the same thing for a post-schema-3 key, so
            # one canonical form serves both and an inherited component keeps
            # the exact payload it was accepted with.
            continue
        if field.key in emitted:
            payload[field.key] = field.payload(component)
        elif field.holds_meaning(component):
            raise LegacySchemaPayloadError(
                f"component {component.record_key}/{component.semantic_key} "
                f"declares schema {schema_version!r}, which has no "
                f"{field.key!r} key — that arrived with {field.introduced_in}; "
                "refusing to omit meaning-bearing data to reproduce a legacy "
                "identity"
            )
    return payload


def representation_payload(
    draft: RepresentationDraft,
    *,
    schema_version: str = REPRESENTATION_SCHEMA_VERSION,
) -> dict[str, object]:
    """Canonical, identity-bearing payload of the keyed representation.

    Every collection here is unordered by meaning, so each is ordered by its
    elements' complete canonical payload rather than by a chosen subset of
    fields — see :mod:`canonical` for why a partial sort key is a defect
    waiting for the next field. Keyed throughout, so nothing derived from the
    identity is inside the thing the identity is computed from.

    Resolving the version's key set here — once, before any component — is what
    makes an unrecognised version fail closed even for a draft with no
    components at all.
    """
    emitted = _emitted_component_fields(schema_version)
    return {
        "records": canonical_order(
            {
                "semantic_key": r.semantic_key,
                "kind": r.kind.value,
                "parent_key": r.parent_key,
            }
            for r in draft.records
        ),
        "components": canonical_order(
            {
                "record_key": c.record_key,
                "semantic_key": c.semantic_key,
                "handling": c.handling.value,
                "irreducibility_reason_code": c.irreducibility_reason_code,
                "facts": canonical_order(fact_payload(f) for f in c.facts),
                **_component_versioned_payload(c, schema_version, emitted),
            }
            for c in draft.components
        ),
        "prose_bindings": canonical_order(
            {
                "record_key": b.record_key,
                "component_key": b.component_key,
                "chunk_id": b.chunk_id,
                # The accepted span and its extent are meaning-bearing. A
                # binding moved to a different clause of the same chunk governs
                # different text, so it is a different projection — the same
                # reason the chunk itself has always been in this payload.
                "span_id": b.span_id,
                "chunk_char_start": b.chunk_char_start,
                "chunk_char_end": b.chunk_char_end,
                "irreducibility_reason_code": b.irreducibility_reason_code,
            }
            for b in draft.prose_bindings
        ),
        "relationships": canonical_order(
            {
                "source_record_key": r.source_record_key,
                "target_record_key": r.target_record_key,
                "kind": r.kind.value,
            }
            for r in draft.relationships
        ),
        "references": canonical_order(
            {
                "from_record_key": r.from_record_key,
                "from_component_key": r.from_component_key,
                "source_text": r.source_text,
                "scope_key": r.scope_key,
                "target_record_key": r.target_record_key,
            }
            for r in draft.references
        ),
        "provenance": canonical_order(
            {
                "target_kind": p.target_kind.value,
                "target_key": list(p.target_key),
                "span_id": p.span_id,
                "role": p.role.value,
            }
            for p in draft.provenance
        ),
    }


def projection_payload(candidate: ProjectionCandidate) -> dict[str, object]:
    """The complete meaning-bearing payload a projection identity covers.

    ``representation_schema`` is here because the representation payload alone
    does not say what its contents are *allowed to mean*. A candidate whose
    facts all belong to families a schema change did not touch produces byte-
    identical content before and after that change, and without this block it
    would keep the same UUID across two different union contracts — so a stored
    binding could not identify which contract governs it (ADR-005d Decisions 4
    and 6).

    Taken from the candidate's declaration rather than from the module
    constants, for the same reason ``classification_payload`` takes the policy
    from the ledger: substituting current code here would re-identify history.
    """
    return {
        "release_binding": release_binding_payload(candidate.binding),
        "classification": classification_payload(candidate.classification),
        "representation_schema": {
            "version": candidate.schema_version,
            "hash": candidate.schema_hash,
        },
        # Serialized under the candidate's *own* declared schema, for the same
        # reason the schema block above is taken from the declaration rather
        # than the module constants: substituting current code here would
        # re-identify history.
        "representation": representation_payload(
            candidate.representation, schema_version=candidate.schema_version
        ),
    }


def validate_schema_binding(candidate: ProjectionCandidate) -> tuple[str, ...]:
    """Return violations of the candidate's declared representation schema.

    The mirror of :func:`~.accounting.validate_policy_binding`: a candidate
    declaring a schema this build does not implement must fail rather than be
    built under a union it never agreed to. Unsupported and mismatched are the
    same refusal here — both mean the declaration and the code disagree about
    what a fact may say.
    """
    findings: list[str] = []
    if candidate.schema_version != REPRESENTATION_SCHEMA_VERSION:
        findings.append(
            f"candidate declares representation schema {candidate.schema_version!r}, "
            f"build implements {REPRESENTATION_SCHEMA_VERSION!r}"
        )
    expected = representation_schema_hash()
    if candidate.schema_hash != expected:
        findings.append(
            f"candidate declares representation schema hash "
            f"{candidate.schema_hash!r}, committed union hashes to {expected!r}"
        )
    return tuple(findings)


def projection_uuid(candidate: ProjectionCandidate) -> str:
    """Content-derived projection identity.

    Any change to the bound release, the accepted classification, the declared
    semantic policy, record assembly, components, facts, prose bindings,
    relationships, references, or provenance mints a different projection.
    """
    return content_id("mechanical_projection", projection_payload(candidate))


def derive_record_id(projection_uuid_: str, record_key: str) -> str:
    """Stable record ID — projection identity plus the committed semantic key."""
    return content_id("mechanical_record", projection_uuid_, record_key)


def derive_component_id(
    projection_uuid_: str, record_key: str, component_key: str
) -> str:
    """Stable component ID."""
    return content_id(
        "mechanical_component", projection_uuid_, record_key, component_key
    )


def recurrence_payload(recurrence: Recurrence | None) -> dict[str, object] | None:
    """Canonical payload of one recurrence, or ``None``.

    Delegates to the representation walker for the same reason
    :func:`applicability_payload` does: one serialization of one structure.
    """
    if recurrence is None:
        return None
    return _dataclass_payload(recurrence)


def applicability_payload(
    applicability: Applicability | None,
) -> dict[str, object] | None:
    """Canonical payload of one applicability, or ``None``.

    Delegates to the representation walker rather than restating the field list
    here. Two hand-written serializations of one structure is exactly the drift
    this module refuses elsewhere, and the walker already owns the rule that
    matters: a post-schema-3 field is omitted when it carries no meaning, which
    is what keeps a schema-3 applicability byte-identical after schema 4 exists.

    Every schema-1..3 field is still emitted unconditionally, including the
    unset ones, so a payload's key set remains the shape for those and the
    loader can still reject on it.
    """
    if applicability is None:
        return None
    return _dataclass_payload(applicability)


#: The exact key set :func:`applicability_payload` emits, and therefore the
#: exact key set a stored or committed applicability payload must carry. It is
#: closed in both directions: a missing key is lost content, and an extra key
#: is a claim about a field the shape does not have — most often a misspelling
#: that would otherwise enter as silently ignored.
_APPLICABILITY_PAYLOAD_KEYS = frozenset(
    {
        "kind",
        "negated",
        "quantity",
        "comparison",
        "value",
        "any_of",
        "trigger",
        "phase",
    }
)

#: Post-schema-3 applicability keys. Admissible when present and admissible when
#: absent — the canonical payload omits them when they carry no meaning, so
#: absence reads as the declared default and nothing is lost. They are kept out
#: of the required set above so a schema-3 payload still validates unchanged.
_APPLICABILITY_OPTIONAL_KEYS = frozenset(
    {"outcome", "damage_outcome", "required_quantity", "fraction", "unit"}
)
_SIZE_COMPARISON_PAYLOAD_KEYS = frozenset(
    {"category", "relation", "at_least", "at_most", "measured", "reference"}
)


def applicability_payload_violations(raw: object) -> list[str]:
    """Violations of one applicability *payload*'s key set and array shape.

    The typed invariant checker owns the field contract, but it can only see
    what was already constructed: a payload with a misspelled or missing key
    never reaches it as the field it was meant to be. This is the half of the
    contract that lives in the JSON, and both the accepted-input loader and the
    persisted-state loader run it before constructing anything.

    Primitive *types* are deliberately not re-checked here — the typed
    invariants own that, so there is one statement of the rule rather than two
    that can drift.
    """
    if not isinstance(raw, dict):
        return [f"applicability is {type(raw).__name__}, not an object"]
    findings: list[str] = []
    supplied = set(raw)
    if missing := sorted(_APPLICABILITY_PAYLOAD_KEYS - supplied):
        findings.append(f"applicability payload is missing {missing}")
    if extra := sorted(
        supplied - _APPLICABILITY_PAYLOAD_KEYS - _APPLICABILITY_OPTIONAL_KEYS
    ):
        findings.append(f"applicability payload carries unexpected {extra}")
    any_of = raw.get("any_of")
    if "any_of" in supplied:
        if not isinstance(any_of, list):
            findings.append(f"any_of is {type(any_of).__name__}, not an array")
        else:
            for index, member in enumerate(any_of):
                if not isinstance(member, dict):
                    findings.append(
                        f"any_of[{index}] is {type(member).__name__}, not an object"
                    )
                    continue
                held = set(member)
                if lost := sorted(_SIZE_COMPARISON_PAYLOAD_KEYS - held):
                    findings.append(f"any_of[{index}] is missing {lost}")
                if odd := sorted(held - _SIZE_COMPARISON_PAYLOAD_KEYS):
                    findings.append(f"any_of[{index}] carries unexpected {odd}")
    return findings


def derive_fact_id(
    projection_uuid_: str,
    record_key: str,
    component_key: str,
    fact: object,
    option_key: str = "",
) -> str:
    """Stable fact ID, keyed by the fact's content rather than its position.

    A fact held directly on the component derives from the same four parts it
    always has, so **every pre-schema-2 fact id is unchanged**; an option fact
    adds its option key, which is what keeps one fact appearing in two options
    of a component from collapsing to a single id.
    """
    parts: tuple[str, ...] = (
        projection_uuid_,
        record_key,
        component_key,
        fact_key(fact),
    )
    if option_key:
        parts = (*parts, option_key)
    return content_id("mechanical_fact", *parts)


@dataclass(frozen=True)
class IdentifiedProjection:
    """A candidate plus the identities derived from it, in that order."""

    candidate: ProjectionCandidate
    projection_uuid: str
    payload_hash: str
    record_ids: dict[str, str]
    component_ids: dict[tuple[str, str], str]
    #: Keyed ``(record_key, component_key, option_key, fact_key)`` — the
    #: option key is ``""`` for a fact held directly on the component.
    fact_ids: dict[tuple[str, str, str, str], str]


def identify_projection(candidate: ProjectionCandidate) -> IdentifiedProjection:
    """Compute the projection identity, then every stable subidentity from it.

    Identification is not proof: the result may still be unpublishable. See
    :func:`validate_candidate` and the persistence/gate layers.
    """
    payload = projection_payload(candidate)
    uuid_ = content_id("mechanical_projection", payload)
    draft = candidate.representation

    record_ids = {
        r.semantic_key: derive_record_id(uuid_, r.semantic_key) for r in draft.records
    }
    component_ids = {
        (c.record_key, c.semantic_key): derive_component_id(
            uuid_, c.record_key, c.semantic_key
        )
        for c in draft.components
    }
    # Keyed by option as well as component: the same fact in two options of
    # one component is two distinct pieces of authority, and a shared id would
    # make one of them unaddressable in persistence and provenance alike.
    fact_ids = {
        (c.record_key, c.semantic_key, option_key, fact_key(f)): derive_fact_id(
            uuid_, c.record_key, c.semantic_key, f, option_key
        )
        for c in draft.components
        for option_key, scoped in (
            ("", c.facts),
            *((o.semantic_key, o.facts) for o in c.options),
        )
        for f in scoped
    }

    return IdentifiedProjection(
        candidate=candidate,
        projection_uuid=uuid_,
        payload_hash=hash_obj(payload),
        record_ids=record_ids,
        component_ids=component_ids,
        fact_ids=fact_ids,
    )


def validate_candidate(
    candidate: ProjectionCandidate, corpus: BoundCorpusSnapshot
) -> tuple[str, ...]:
    """Return every violation that blocks this candidate from being published.

    Covers the bound release's agreement with the candidate, the declared
    policy binding, the span partition over each represented leaf, closed
    reason codes, explicit acceptance, and the keyed representation. An empty
    result means the candidate is internally honest — it does *not* mean the
    projection is complete, persisted, reconstructable, or publishable. Those
    are proven by the persistence layer and the exact completeness gate,
    against reconstructed state.

    *corpus* is the single resolved view of the bound 5c release, so every
    release-scoped check reads the same source rather than querying its own.
    """
    findings: list[str] = []
    ledger = candidate.classification
    binding = candidate.binding

    # The candidate, its classification, and the snapshot must all name one
    # release. Two of the three agreeing is not agreement.
    if binding.package_uuid != corpus.package_uuid:
        findings.append(
            f"binding names package {binding.package_uuid}, corpus snapshot is "
            f"{corpus.package_uuid}"
        )
    if binding.release_version != corpus.release_version:
        findings.append(
            f"binding names release {binding.release_version}, corpus snapshot is "
            f"{corpus.release_version}"
        )
    if ledger.package_uuid != binding.package_uuid:
        findings.append(
            f"classification names package {ledger.package_uuid}, binding is "
            f"{binding.package_uuid}"
        )
    if ledger.release_version != binding.release_version:
        findings.append(
            f"classification names release {ledger.release_version}, binding is "
            f"{binding.release_version}"
        )

    findings.extend(validate_policy_binding(ledger))
    findings.extend(validate_schema_binding(candidate))

    leaf_lengths = corpus.leaf_lengths
    claimed_leaves = {s.leaf_id for s in ledger.spans}
    for leaf_id in sorted(claimed_leaves | set(leaf_lengths)):
        if leaf_id not in leaf_lengths:
            findings.append(f"leaf {leaf_id}: classified but not in the bound release")
            continue
        findings.extend(
            validate_partition(leaf_id, leaf_lengths[leaf_id], ledger.spans)
        )

    findings.extend(validate_reason_codes(ledger.spans))
    findings.extend(validate_acceptance(ledger))
    findings.extend(validate_representation(candidate.representation, ledger, corpus))
    return tuple(findings)
