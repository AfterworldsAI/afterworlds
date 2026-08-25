"""Committed accepted authority — CRD Issue 5d, Decisions 4 and 5.

This module owns both halves of what a reviewer commits: the accepted
**oracle** the publication gate judges persisted state against, and the
accepted **inputs** the production build consumes, which are the oracle plus the
review evidence that accepted it (:class:`AcceptedInputs`).

The only property that makes the gate's comparison worth anything is
independence: an oracle derived from the projection it checks proves nothing but
that the code is self-consistent.

Independence is structural here, not a convention:

* this module imports no session, no ORM, and nothing from
  :mod:`persistence`, :mod:`raw_state`, or :mod:`gate`. There is no code path,
  public or private, that builds an ``AcceptedOracle`` from a persisted
  projection or from a :class:`ProjectionCandidate`.
  :func:`candidate_from_accepted_inputs` runs the *other* way — committed bytes
  become a candidate — and the oracle those bytes also carry is what later judges
  it;
* :func:`load_accepted_inputs` reads a committed JSON file and nothing else. Its
  whole input is bytes on disk that a reviewer accepted and a commit records; and
* the declared semantic policy comes from the *file*, never from the current
  :mod:`policy` constants. Reading current code here would let a policy change
  silently re-bless an oracle nobody re-reviewed — the exact self-attestation
  this file exists to prevent. When the frozen policy changes, every committed
  oracle fails its binding check until a reviewer re-accepts it. That is the
  intended cost.

**What the oracle does not carry.** The represented-leaf population is *not*
declared here. It is read from the bound CRD Issue 5c release, which is already
independent accepted authority with its own publication proof. Re-declaring
28,109 leaf ids in a committed file would add a second place to drift from 5c
without adding a second opinion.

**What is committed today.** ``oracles/`` holds accepted authority for the
production SRD 5.2.1 release covering CRD Issue 5d batch ``conditions-1`` only,
so that release resolves to a committed oracle — but not to full-corpus
authority. A projection over the whole release therefore fails the gate as
incomplete rather than as unjudged, and nothing over it has been published or
activated. Later content batches extend that same artifact through the
propose → review → accept workflow (:mod:`proposal`, :mod:`acceptance`), which
merges over prior accepted inputs rather than replacing them; the machinery that
judges the result lives here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.mechanical.accounting import (
    acceptance_evidence_payload,
    span_payload,
    validate_acceptance,
)
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.models import (
    AcceptanceBatch,
    AcceptanceRecord,
    ClassificationLedger,
    ComponentHandling,
    ReviewState,
    SemanticDiffEntry,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    ReleaseBinding,
    applicability_payload_violations,
    representation_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    Applicability,
    ApplicabilityKind,
    Comparison,
    ComponentDraft,
    ComponentOption,
    CreatureSize,
    FactFamily,
    FactQualifier,
    MalformedFactPayloadError,
    ParticipantRole,
    Phase,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RecoveryTrigger,
    Recurrence,
    RecurrenceBoundary,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
    RepresentationDraft,
    RollActor,
    SizeComparison,
    SizeRelation,
    TrackedQuantity,
    UnknownFactFamilyError,
    applicability_violations,
    fact_from_payload,
    recurrence_violations,
)
from afterworlds.ingestion.mechanical.schema_lift import SchemaLiftRecord

__all__ = [
    "ACCEPTED_ARTIFACT_KIND",
    "COMMITTED_ORACLE_DIR",
    "AcceptedInputs",
    "AcceptedOracle",
    "OracleLoadError",
    "RecordObligation",
    "accepted_inputs_payload",
    "candidate_from_accepted_inputs",
    "committed_inputs_for",
    "committed_oracle_for",
    "derive_obligations",
    "load_accepted_inputs",
    "load_oracle",
    "obligation_payload",
    "oracle_identity",
    "oracle_payload",
]

#: Committed accepted authority, one JSON file per published 5c release.
COMMITTED_ORACLE_DIR = Path(__file__).resolve().parent / "oracles"

#: The discriminator a committed accepted-inputs artifact must declare. A
#: machine proposal declares something else and has a different shape besides
#: (:mod:`afterworlds.ingestion.mechanical.proposal`), so it cannot be loaded as
#: accepted authority by renaming it, moving it, or editing one field.
ACCEPTED_ARTIFACT_KIND = "accepted_authority"


class OracleLoadError(ValueError):
    """A committed oracle file that will not load as accepted authority.

    Raised rather than reported: an oracle that cannot be read is not a weaker
    oracle, it is no oracle, and a gate run against a half-parsed one would
    compare persisted state to a shape nobody accepted.
    """


@dataclass(frozen=True)
class RecordObligation:
    """What a reviewer accepted that one record must actually carry.

    Element-set equality already rejects a projection whose contents differ
    from the accepted inventory. Obligations exist because equality alone
    cannot say *why* a projection is wrong, and because they are the accepted
    claim in reviewable form: "this record is represented by structured
    authority of these families, and these components remain prose-bound".

    That shape is what makes two specific defects fail by name rather than as
    an anonymous set difference:

    * **all-prose under-extraction** — a record whose facts were dropped and
      re-described as prose fails ``structured_fact_families``; and
    * **reference-only coverage** — a record covered by references alone
      satisfies no obligation at all, because a reference is not a fact.

    ``prose_bound_components`` names components whose accepted handling is
    ``PROSE_BOUND`` or ``MIXED``; each must still carry exact governing prose.
    """

    record_key: str
    kind: RecordKind
    structured_fact_families: frozenset[FactFamily]
    prose_bound_components: frozenset[str]


@dataclass(frozen=True)
class AcceptedOracle:
    """The complete accepted authority one projection is judged against.

    ``binding`` is the exact 5c release the accepted semantics were reviewed
    over. A projection bound to any other release is judged by nothing and
    fails as mismatched rather than being compared anyway.
    """

    binding: ReleaseBinding
    policy_version: str
    policy_hash: str
    #: The closed representation contract this accepted authority was reviewed
    #: under. Committed alongside the semantics it governs, so an artifact
    #: cannot be replayed under a union that means something else.
    schema_version: str
    schema_hash: str
    spans: tuple[SemanticSpan, ...]
    representation: RepresentationDraft
    obligations: tuple[RecordObligation, ...]


@dataclass(frozen=True)
class AcceptedInputs:
    """One committed artifact: the accepted result *and* the review evidence.

    The two halves are deliberately separable. :attr:`oracle` is the accepted
    semantics the publication gate judges against, and it excludes evidence
    because review process is not identity-bearing. :attr:`batches` and
    :attr:`acceptances` are the auditable record of the explicit acceptance
    action — exact scope, full semantic diff, who accepted it and when — which
    the build carries into persistence so the gate can see that every span was
    actually acted on.

    Keeping them in one file means they cannot drift apart; keeping them in
    separate fields means the evidence cannot leak into identity.
    """

    oracle: AcceptedOracle
    batches: tuple[AcceptanceBatch, ...]
    acceptances: tuple[AcceptanceRecord, ...]
    #: Schema successions this artifact was carried across, oldest first.
    #: Evidence, never identity: which contract an artifact was lifted through is
    #: migration process, and process does not remint a projection (#137
    #: acceptance criterion 11), so this sits beside the acceptance batches
    #: rather than inside :class:`AcceptedOracle`.
    lifts: tuple[SchemaLiftRecord, ...] = ()

    def classification(self) -> ClassificationLedger:
        """The complete accepted ledger, result and evidence together."""
        return ClassificationLedger(
            package_uuid=self.oracle.binding.package_uuid,
            release_version=self.oracle.binding.release_version,
            policy_version=self.oracle.policy_version,
            policy_hash=self.oracle.policy_hash,
            spans=self.oracle.spans,
            batches=self.batches,
            acceptances=self.acceptances,
        )


#: Handlings whose accepted meaning is carried, wholly or partly, by governing
#: prose — so the component must still resolve to exact prose.
_PROSE_BOUND_HANDLINGS = frozenset(
    {ComponentHandling.PROSE_BOUND, ComponentHandling.MIXED}
)


def derive_obligations(
    representation: RepresentationDraft,
) -> tuple[RecordObligation, ...]:
    """The exact obligations one accepted representation states, one per record.

    The single definition of "what this accepted authority claims about record
    R", used twice for one reason: :func:`load_oracle` requires a committed
    file's declared obligations to equal it exactly, and :mod:`gate` evaluates
    obligations against *persisted* state. Deriving the expectation in one place
    means an obligation that loads is an obligation the gate can actually
    satisfy — two hand-written derivations would eventually disagree and produce
    an oracle nothing can pass.

    Requiring equality does not make obligations redundant. The independence
    that matters is oracle-versus-projection, and it is untouched; what this
    forecloses is a committed file whose per-record claim silently understates
    or overstates the representation it ships with, which would let the gate
    report satisfied obligations that assert less than the accepted authority.
    """
    families: dict[str, set[FactFamily]] = {}
    prose: dict[str, set[str]] = {}
    for component in representation.components:
        for fact in component.all_facts():
            family = getattr(fact, "FAMILY", None)
            if isinstance(family, FactFamily):
                families.setdefault(component.record_key, set()).add(family)
        if component.handling in _PROSE_BOUND_HANDLINGS:
            prose.setdefault(component.record_key, set()).add(component.semantic_key)
    return tuple(
        RecordObligation(
            record_key=record.semantic_key,
            kind=record.kind,
            structured_fact_families=frozenset(families.get(record.semantic_key, ())),
            prose_bound_components=frozenset(prose.get(record.semantic_key, ())),
        )
        for record in representation.records
    )


def obligation_payload(obligation: RecordObligation) -> dict[str, object]:
    """Canonical payload of one accepted per-record obligation."""
    return {
        "record_key": obligation.record_key,
        "kind": obligation.kind.value,
        "structured_fact_families": sorted(
            f.value for f in obligation.structured_fact_families
        ),
        "prose_bound_components": sorted(obligation.prose_bound_components),
    }


def oracle_payload(oracle: AcceptedOracle) -> dict[str, object]:
    """Canonical payload of the accepted oracle.

    Reuses the projection's own payload builders for spans and representation,
    so "the oracle and the projection agree" is a comparison of one canonical
    form rather than of two hand-written serializations that could drift.
    """
    return {
        "release_binding": {
            "package_uuid": oracle.binding.package_uuid,
            "release_version": oracle.binding.release_version,
            "authoritative_source_hash": oracle.binding.authoritative_source_hash,
            "transform_config_hash": oracle.binding.transform_config_hash,
            "bundle_root_hash": oracle.binding.bundle_root_hash,
            "persisted_corpus_digest": oracle.binding.persisted_corpus_digest,
        },
        "semantic_policy_version": oracle.policy_version,
        "semantic_policy_hash": oracle.policy_hash,
        "representation_schema": {
            "version": oracle.schema_version,
            "hash": oracle.schema_hash,
        },
        "spans": span_payload(oracle.spans),
        # Under the schema this ACCEPTED AUTHORITY declares, never the one the
        # build happens to implement. The two coincided until schema 4 existed,
        # which is why defaulting here was invisible: a schema-3 artifact loaded
        # by a schema-4 build would have been canonicalized under schema-4 keys
        # and silently re-identified — the same failure Owner Decision
        # 2026-08-20 addressed for components, reappearing at this seam.
        "representation": representation_payload(
            oracle.representation, schema_version=oracle.schema_version
        ),
        "obligations": canonical_order(
            obligation_payload(o) for o in oracle.obligations
        ),
    }


def oracle_identity(oracle: AcceptedOracle) -> str:
    """Content-derived identity of the accepted oracle.

    Recorded in the evidence report and on the published projection, so an
    audit can name which accepted authority passed the gate — and detect a
    later oracle edit, because an edited oracle is a different identity.
    """
    return hash_obj(oracle_payload(oracle))


# ---------------------------------------------------------------------------
# Committed-file loading
# ---------------------------------------------------------------------------
#
# Strict throughout, in the same spirit as fact reconstruction: a missing key,
# an unknown enum value, or an extra key is rejected rather than defaulted.
# An oracle that silently accepts an unrecognised shape would let a typo widen
# what publication tolerates.


def _require(
    payload: object,
    keys: tuple[str, ...],
    where: str,
    optional: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Check a payload's key set exactly.

    ``optional`` names keys that may be absent *and* may be present. It is used
    only where absence is an unambiguous real state rather than lost content —
    a component with no applicability and no options is exactly a schema-1
    component. Everything else stays strict: an unknown key is still rejected,
    so a misspelling cannot enter as silently ignored.
    """
    if not isinstance(payload, dict):
        raise OracleLoadError(
            f"{where}: expected an object, got {type(payload).__name__}"
        )
    supplied = set(payload)
    if missing := sorted(set(keys) - supplied):
        raise OracleLoadError(f"{where}: missing {missing}")
    if extra := sorted(supplied - set(keys) - set(optional)):
        raise OracleLoadError(f"{where}: unexpected {extra}")
    return payload


def _string(value: object, where: str) -> str:
    """A JSON string, exactly. No coercion — ``0`` is not ``"0"``."""
    if type(value) is not str:
        raise OracleLoadError(
            f"{where}: expected a string, got {type(value).__name__} {value!r}"
        )
    return value


def _optional_string(value: object, where: str) -> str | None:
    """A JSON string or ``null``, for a declared ``str | None`` field."""
    return None if value is None else _string(value, where)


def _offset(value: object, where: str) -> int:
    """A non-negative JSON integer character offset.

    ``bool`` is rejected explicitly: it is an ``int`` subclass, so ``true``
    would otherwise load as the offset ``1``. Floats are rejected too — ``0.0``
    is not the integer the span contract declares.

    Negativity is a *type-domain* violation and belongs here. Ordering, gap-free
    coverage, and whether a span partitions its leaf belong to the semantic
    validator, which already owns partition validity; this boundary does not
    state a second opinion about it.
    """
    if type(value) is not int:
        raise OracleLoadError(
            f"{where}: expected an integer, got {type(value).__name__} {value!r}"
        )
    if value < 0:
        raise OracleLoadError(
            f"{where}: character offsets cannot be negative ({value})"
        )
    return value


def _list(value: object, where: str) -> list[Any]:
    """A JSON array, exactly. A string is not an array of its characters."""
    if not isinstance(value, list):
        raise OracleLoadError(
            f"{where}: expected an array, got {type(value).__name__} {value!r}"
        )
    return value


def _string_list(value: object, where: str) -> list[str]:
    """A JSON array of strings.

    Guards the constructors that would otherwise manufacture accepted authority
    out of a bare string: ``tuple("abc")`` and ``frozenset("abc")`` both succeed
    and silently invent three elements.
    """
    return [
        _string(item, f"{where}[{i}]") for i, item in enumerate(_list(value, where))
    ]


def _recurrence(raw: object, where: str) -> Recurrence | None:
    """Load one stored recurrence, or ``None``.

    Absent is the declared default: the canonical payload omits this key when
    the component states no recurrence, which is what keeps a schema-3 component
    byte-identical under schema 4. Present is held to the same typed invariants
    the build side uses.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise OracleLoadError(f"{where}: recurrence must be an object or null")
    payload = _require(raw, ("boundary",), where, optional=("whose",))
    built = Recurrence(
        boundary=_enum(RecurrenceBoundary, payload["boundary"], f"{where}.boundary"),
        whose=(
            None
            if payload.get("whose") is None
            else _enum(RollActor, payload["whose"], f"{where}.whose")
        ),
    )
    if findings := recurrence_violations(built):
        raise OracleLoadError(f"{where}: {'; '.join(findings)}")
    return built


def _applicability(raw: object, where: str) -> Applicability | None:
    """Load one stored applicability, or ``None``.

    Delegates the shape contract to the same invariant checker the build side
    uses, so a payload the builder would have refused cannot enter through the
    loader instead.
    """
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise OracleLoadError(f"{where}: applicability must be an object or null")
    # The key set first: a misspelled or missing key never reaches the typed
    # invariants as the field it was meant to be, so it has to be refused
    # before anything is constructed.
    if shape := applicability_payload_violations(raw):
        raise OracleLoadError(f"{where}: {'; '.join(shape)}")
    try:
        built = Applicability(
            kind=ApplicabilityKind(raw["kind"]),
            # Carried through exactly as stored, never coerced: ``bool("false")``
            # is ``True``, so coercion here would publish the opposite
            # applicability from what the malformed input states. The exact-type
            # rule is stated once, by the invariant checker below.
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
                for c in _object_list(raw["any_of"], f"{where}.any_of")
            ),
            trigger=(
                None if raw["trigger"] is None else RecoveryTrigger(raw["trigger"])
            ),
            phase=None if raw["phase"] is None else Phase(raw["phase"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise OracleLoadError(f"{where}: {exc}") from exc
    violations = applicability_violations(built)
    if violations:
        raise OracleLoadError(f"{where}: {'; '.join(violations)}")
    return built


def _component_option(raw: object, where: str) -> ComponentOption:
    """Load one option of an exhaustive actor choice."""
    if not isinstance(raw, dict):
        raise OracleLoadError(f"{where}: option must be an object")
    o = _require(raw, ("semantic_key", "facts"), where, optional=("applies_when",))
    try:
        facts = tuple(
            fact_from_payload(f) for f in _object_list(o["facts"], f"{where}.facts")
        )
    except (MalformedFactPayloadError, UnknownFactFamilyError) as exc:
        raise OracleLoadError(f"{where}: {exc}") from exc
    return ComponentOption(
        semantic_key=_string(o["semantic_key"], f"{where}.semantic_key"),
        facts=facts,
        applies_when=_applicability(o.get("applies_when"), f"{where}.applies_when"),
    )


def _fact_qualifier(raw: object, where: str) -> FactQualifier:
    """Load one fact's own condition.

    ``applies_when`` is required here, unlike on a component or an option: a
    qualifier whose condition is absent states nothing and would be a row of
    pure noise, where an absent component qualifier is the real, meaningful
    state "applies unconditionally".
    """
    if not isinstance(raw, dict):
        raise OracleLoadError(f"{where}: fact qualifier must be an object")
    q = _require(raw, ("fact_key", "applies_when"), where, optional=("option_key",))
    applies_when = _applicability(q["applies_when"], f"{where}.applies_when")
    if applies_when is None:
        raise OracleLoadError(f"{where}.applies_when: a fact qualifier states none")
    return FactQualifier(
        fact_key=_string(q["fact_key"], f"{where}.fact_key"),
        option_key=_string(q.get("option_key", ""), f"{where}.option_key"),
        applies_when=applies_when,
    )


def _object_list(value: object, where: str) -> list[dict[str, Any]]:
    """A JSON array of objects, checked before anything indexes an element."""
    items = _list(value, where)
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise OracleLoadError(
                f"{where}[{i}]: expected an object, got {type(item).__name__} {item!r}"
            )
    return items


def _enum[E: StrEnum](enum_cls: type[E], value: object, where: str) -> E:
    """Read one closed enum out of a committed file, or reject the file.

    The stored value must be a plain string naming a declared member. No
    coercion: a number, a null, or a look-alike is a file a reviewer did not
    write in the accepted shape, and guessing what it meant would be this
    layer inventing accepted authority.
    """
    if type(value) is not str:
        raise OracleLoadError(
            f"{where}: expected a string {enum_cls.__name__}, got "
            f"{type(value).__name__} {value!r}"
        )
    try:
        return enum_cls(value)
    except ValueError:
        raise OracleLoadError(
            f"{where}: {value!r} is not a declared {enum_cls.__name__}"
        ) from None


def _span(payload: object, index: int) -> SemanticSpan:
    where = f"spans[{index}]"
    p = _require(
        payload,
        (
            "span_id",
            "leaf_id",
            "char_start",
            "char_end",
            "disposition",
            "non_mechanical_reason_code",
        ),
        where,
    )
    return SemanticSpan(
        span_id=_string(p["span_id"], f"{where}.span_id"),
        leaf_id=_string(p["leaf_id"], f"{where}.leaf_id"),
        char_start=_offset(p["char_start"], f"{where}.char_start"),
        char_end=_offset(p["char_end"], f"{where}.char_end"),
        disposition=_enum(SemanticDisposition, p["disposition"], where),
        # An oracle span is accepted authority by construction: an unaccepted
        # claim has no business in a committed oracle, so the review state is
        # not a field a file may set to something else.
        review_state=ReviewState.ACCEPTED,
        non_mechanical_reason_code=_optional_string(
            p["non_mechanical_reason_code"], f"{where}.non_mechanical_reason_code"
        ),
    )


def _representation(payload: object) -> RepresentationDraft:
    p = _require(
        payload,
        (
            "records",
            "components",
            "prose_bindings",
            "relationships",
            "references",
            "provenance",
        ),
        "representation",
    )

    records = []
    for i, raw in enumerate(_object_list(p["records"], "representation.records")):
        where = f"representation.records[{i}]"
        r = _require(raw, ("semantic_key", "kind", "parent_key"), where)
        records.append(
            RecordDraft(
                semantic_key=_string(r["semantic_key"], f"{where}.semantic_key"),
                kind=_enum(RecordKind, r["kind"], where),
                parent_key=_optional_string(r["parent_key"], f"{where}.parent_key"),
            )
        )

    components = []
    for i, raw in enumerate(_object_list(p["components"], "representation.components")):
        where = f"representation.components[{i}]"
        c = _require(
            raw,
            (
                "record_key",
                "semantic_key",
                "handling",
                "irreducibility_reason_code",
                "facts",
            ),
            where,
            optional=("applies_when", "options", "fact_qualifiers", "recurs"),
        )
        # The fact list is shape-checked here *before* delegation, because the
        # closed-union parser reads a mapping and a non-object element would
        # reach it as an unclassified AttributeError rather than this loader's
        # documented error. Family validation itself stays where it is owned.
        raw_facts = _object_list(c["facts"], f"{where}.facts")
        try:
            facts = tuple(fact_from_payload(f) for f in raw_facts)
        except (MalformedFactPayloadError, UnknownFactFamilyError) as exc:
            # Both halves of the closed union's rejection: a payload that will
            # not rebuild its declared family, and a family outside the union.
            # The second is a TypeError, so catching ValueError alone would let
            # an undeclared family escape as an unclassified crash.
            raise OracleLoadError(f"{where}: {exc}") from exc
        components.append(
            ComponentDraft(
                record_key=_string(c["record_key"], f"{where}.record_key"),
                semantic_key=_string(c["semantic_key"], f"{where}.semantic_key"),
                handling=_enum(ComponentHandling, c["handling"], where),
                irreducibility_reason_code=_optional_string(
                    c["irreducibility_reason_code"],
                    f"{where}.irreducibility_reason_code",
                ),
                facts=facts,
                # Optional, unlike the required keys above, and deliberately:
                # absence is an unambiguous real state — a component with no
                # applicability and no options is exactly a schema-1 component,
                # which remains valid schema-2 content. Nothing is hidden by
                # the leniency: ``projection_payload`` always emits both keys,
                # and the gate rebuilds and re-hashes the payload, so a key
                # dropped or misspelled anywhere upstream fails there rather
                # than loading as silently empty.
                recurs=_recurrence(c.get("recurs"), f"{where}.recurs"),
                applies_when=_applicability(
                    c.get("applies_when"), f"{where}.applies_when"
                ),
                options=tuple(
                    _component_option(o, f"{where}.options[{j}]")
                    for j, o in enumerate(
                        _object_list(c.get("options", []), f"{where}.options")
                    )
                ),
                fact_qualifiers=tuple(
                    _fact_qualifier(q, f"{where}.fact_qualifiers[{j}]")
                    for j, q in enumerate(
                        _object_list(
                            c.get("fact_qualifiers", []), f"{where}.fact_qualifiers"
                        )
                    )
                ),
            )
        )

    prose_bindings = []
    for i, raw in enumerate(
        _object_list(p["prose_bindings"], "representation.prose_bindings")
    ):
        where = f"representation.prose_bindings[{i}]"
        b = _require(
            raw,
            (
                "record_key",
                "component_key",
                "chunk_id",
                "span_id",
                "chunk_char_start",
                "chunk_char_end",
                "irreducibility_reason_code",
            ),
            where,
        )
        prose_bindings.append(
            ProseBindingDraft(
                record_key=_string(b["record_key"], f"{where}.record_key"),
                component_key=_string(b["component_key"], f"{where}.component_key"),
                chunk_id=_string(b["chunk_id"], f"{where}.chunk_id"),
                span_id=_string(b["span_id"], f"{where}.span_id"),
                chunk_char_start=_offset(
                    b["chunk_char_start"], f"{where}.chunk_char_start"
                ),
                chunk_char_end=_offset(b["chunk_char_end"], f"{where}.chunk_char_end"),
                irreducibility_reason_code=_string(
                    b["irreducibility_reason_code"],
                    f"{where}.irreducibility_reason_code",
                ),
            )
        )

    relationships = []
    for i, raw in enumerate(
        _object_list(p["relationships"], "representation.relationships")
    ):
        where = f"representation.relationships[{i}]"
        rel = _require(raw, ("source_record_key", "target_record_key", "kind"), where)
        relationships.append(
            RelationshipDraft(
                source_record_key=_string(
                    rel["source_record_key"], f"{where}.source_record_key"
                ),
                target_record_key=_string(
                    rel["target_record_key"], f"{where}.target_record_key"
                ),
                kind=_enum(RelationshipKind, rel["kind"], where),
            )
        )

    references = []
    reference_fields = (
        "from_record_key",
        "from_component_key",
        "source_text",
        "scope_key",
        "target_record_key",
    )
    for i, raw in enumerate(_object_list(p["references"], "representation.references")):
        where = f"representation.references[{i}]"
        ref = _require(raw, reference_fields, where)
        references.append(
            ReferenceDraft(
                **{k: _string(ref[k], f"{where}.{k}") for k in reference_fields}
            )
        )

    provenance = []
    for i, raw in enumerate(_object_list(p["provenance"], "representation.provenance")):
        where = f"representation.provenance[{i}]"
        pr = _require(raw, ("target_kind", "target_key", "span_id", "role"), where)
        provenance.append(
            ProvenanceClaim(
                target_kind=_enum(ProvenanceTargetKind, pr["target_kind"], where),
                target_key=tuple(_string_list(pr["target_key"], f"{where}.target_key")),
                span_id=_string(pr["span_id"], f"{where}.span_id"),
                role=_enum(ProvenanceRole, pr["role"], where),
            )
        )

    return RepresentationDraft(
        records=tuple(records),
        components=tuple(components),
        prose_bindings=tuple(prose_bindings),
        relationships=tuple(relationships),
        references=tuple(references),
        provenance=tuple(provenance),
    )


def _obligation(payload: object, index: int) -> RecordObligation:
    where = f"obligations[{index}]"
    o = _require(
        payload,
        ("record_key", "kind", "structured_fact_families", "prose_bound_components"),
        where,
    )
    return RecordObligation(
        record_key=_string(o["record_key"], f"{where}.record_key"),
        kind=_enum(RecordKind, o["kind"], where),
        structured_fact_families=frozenset(
            _enum(FactFamily, f, f"{where}.structured_fact_families")
            for f in _list(
                o["structured_fact_families"], f"{where}.structured_fact_families"
            )
        ),
        # A bare string here would become a frozenset of its characters, which
        # is accepted authority invented out of a typo.
        prose_bound_components=frozenset(
            _string_list(o["prose_bound_components"], f"{where}.prose_bound_components")
        ),
    )


def _check_obligations_closed(
    representation: RepresentationDraft,
    obligations: tuple[RecordObligation, ...],
    where: str,
) -> None:
    """Reject a committed oracle whose obligation relation is not total and exact.

    Shape validation cannot catch this. A file that parses perfectly but omits
    an obligation — or all of them — yields an oracle the gate evaluates against
    an emptier claim than the reviewer accepted, and an otherwise-matching
    projection then passes with less per-record evidence than ADR-005d
    Decision 5 requires. So the relation must be *closed*: exactly one
    obligation per accepted record, each reconciling exactly with what that
    record's accepted representation states.
    """
    accepted = {o.record_key: o for o in derive_obligations(representation)}
    seen: set[str] = set()
    for obligation in obligations:
        if obligation.record_key in seen:
            raise OracleLoadError(
                f"{where}: duplicate obligation for record "
                f"{obligation.record_key!r}"
            )
        seen.add(obligation.record_key)
        expected = accepted.get(obligation.record_key)
        if expected is None:
            raise OracleLoadError(
                f"{where}: obligation targets record {obligation.record_key!r}, "
                "which the accepted representation does not declare"
            )
        if obligation != expected:
            raise OracleLoadError(
                f"{where}: obligation for record {obligation.record_key!r} does "
                f"not reconcile with the accepted representation: declared "
                f"{obligation_payload(obligation)}, accepted "
                f"{obligation_payload(expected)}"
            )
    if uncovered := sorted(set(accepted) - seen):
        raise OracleLoadError(
            f"{where}: accepted records carry no obligation: {uncovered}"
        )


# ---------------------------------------------------------------------------
# Acceptance evidence and the committed accepted-inputs artifact
# ---------------------------------------------------------------------------
#
# **Why one artifact and not two.** #137 contract 4 names five committed
# meaning-bearing inputs the production build consumes; the oracle carries four
# of them but deliberately omits the fifth, acceptance evidence, because review
# process is not identity-bearing (:mod:`accounting`). Something still has to
# supply that evidence to the build, or the gate reports UNREVIEWED_RESIDUE
# against reconstructed state that no committed input could have filled in.
#
# Two files — build inputs and oracle — would need a third mechanism to prove
# they still describe the same accepted semantics. One file cannot disagree with
# itself, so the drift check has nothing to check and the whole class of
# input/oracle skew stops existing. The independence that actually matters is
# untouched: this is committed bytes a reviewer accepted, never something
# derived from a candidate or from persisted output, and the oracle projected
# out of it drops the evidence before identity is computed.


def _acceptance(payload: object, where: str) -> tuple[
    tuple[AcceptanceBatch, ...],
    tuple[AcceptanceRecord, ...],
    tuple[SchemaLiftRecord, ...],
]:
    """Load the review evidence half of a committed accepted-inputs file."""
    p = _require(payload, ("batches", "records"), where, optional=("lifts",))

    lifts = []
    for i, raw_lift in enumerate(_object_list(p.get("lifts", []), f"{where}.lifts")):
        at = f"{where}.lifts[{i}]"
        entry = _require(
            raw_lift,
            (
                "lift_id",
                "from_version",
                "from_hash",
                "to_version",
                "to_hash",
                "verified_counts",
            ),
            at,
        )
        counts = []
        for j, raw_count in enumerate(
            _object_list(entry["verified_counts"], f"{at}.verified_counts")
        ):
            cat = f"{at}.verified_counts[{j}]"
            c = _require(raw_count, ("collection", "elements"), cat)
            counts.append(
                (
                    _string(c["collection"], f"{cat}.collection"),
                    _offset(c["elements"], f"{cat}.elements"),
                )
            )
        lifts.append(
            SchemaLiftRecord(
                lift_id=_string(entry["lift_id"], f"{at}.lift_id"),
                from_version=_string(entry["from_version"], f"{at}.from_version"),
                from_hash=_string(entry["from_hash"], f"{at}.from_hash"),
                to_version=_string(entry["to_version"], f"{at}.to_version"),
                to_hash=_string(entry["to_hash"], f"{at}.to_hash"),
                verified_counts=tuple(counts),
            )
        )

    batches = []
    for i, raw in enumerate(_object_list(p["batches"], f"{where}.batches")):
        at = f"{where}.batches[{i}]"
        b = _require(
            raw,
            (
                "batch_id",
                "rule",
                "resolved_scope",
                "diff",
                "semantic_diff_hash",
                "proposal_identity",
            ),
            at,
        )
        diff = []
        for j, raw_entry in enumerate(_object_list(b["diff"], f"{at}.diff")):
            entry_at = f"{at}.diff[{j}]"
            d = _require(
                raw_entry,
                (
                    "span_id",
                    "prior_disposition",
                    "prior_reason_code",
                    "accepted_disposition",
                    "accepted_reason_code",
                ),
                entry_at,
            )
            prior = d["prior_disposition"]
            diff.append(
                SemanticDiffEntry(
                    span_id=_string(d["span_id"], f"{entry_at}.span_id"),
                    prior_disposition=(
                        None
                        if prior is None
                        else _enum(SemanticDisposition, prior, entry_at)
                    ),
                    prior_reason_code=_optional_string(
                        d["prior_reason_code"], f"{entry_at}.prior_reason_code"
                    ),
                    accepted_disposition=_enum(
                        SemanticDisposition, d["accepted_disposition"], entry_at
                    ),
                    accepted_reason_code=_optional_string(
                        d["accepted_reason_code"], f"{entry_at}.accepted_reason_code"
                    ),
                )
            )
        batches.append(
            AcceptanceBatch(
                batch_id=_string(b["batch_id"], f"{at}.batch_id"),
                rule=_string(b["rule"], f"{at}.rule"),
                resolved_scope=tuple(
                    _string_list(b["resolved_scope"], f"{at}.resolved_scope")
                ),
                diff=tuple(diff),
                semantic_diff_hash=_string(
                    b["semantic_diff_hash"], f"{at}.semantic_diff_hash"
                ),
                proposal_identity=_string(
                    b["proposal_identity"], f"{at}.proposal_identity"
                ),
            )
        )

    records = []
    for i, raw in enumerate(_object_list(p["records"], f"{where}.records")):
        at = f"{where}.records[{i}]"
        r = _require(raw, ("span_id", "batch_id", "reviewer", "accepted_at"), at)
        records.append(
            AcceptanceRecord(
                span_id=_string(r["span_id"], f"{at}.span_id"),
                batch_id=_optional_string(r["batch_id"], f"{at}.batch_id"),
                reviewer=_string(r["reviewer"], f"{at}.reviewer"),
                accepted_at=_string(r["accepted_at"], f"{at}.accepted_at"),
            )
        )
    return tuple(batches), tuple(records), tuple(lifts)


def load_accepted_inputs(path: Path) -> AcceptedInputs:
    """Load one committed accepted-inputs artifact from JSON.

    The whole input is the file. Nothing is read from the database, from a
    candidate, or from the current semantic policy.

    ``artifact_kind`` is checked first and must be exactly
    :data:`ACCEPTED_ARTIFACT_KIND`. That check is a fast, legible rejection of a
    machine proposal — but it is not what makes a proposal unloadable. A
    proposal has a different key set at every level (see
    :mod:`afterworlds.ingestion.mechanical.proposal`), so it fails ``_require``
    in several places even if someone edits its ``artifact_kind`` to lie.
    Structural incompatibility, not a flag and not a directory.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OracleLoadError(f"{path.name}: {exc}") from exc

    if isinstance(raw, dict) and raw.get("artifact_kind") != ACCEPTED_ARTIFACT_KIND:
        raise OracleLoadError(
            f"{path.name}: artifact_kind {raw.get('artifact_kind')!r} is not "
            f"{ACCEPTED_ARTIFACT_KIND!r}; this file is not accepted authority"
        )

    p = _require(
        raw,
        (
            "artifact_kind",
            "release_binding",
            "semantic_policy_version",
            "semantic_policy_hash",
            "representation_schema",
            "spans",
            "acceptance",
            "representation",
            "obligations",
        ),
        path.name,
    )
    binding_fields = (
        "package_uuid",
        "release_version",
        "authoritative_source_hash",
        "transform_config_hash",
        "bundle_root_hash",
        "persisted_corpus_digest",
    )
    binding = _require(p["release_binding"], binding_fields, "release_binding")
    schema = _require(
        p["representation_schema"], ("version", "hash"), "representation_schema"
    )
    representation = _representation(p["representation"])
    obligations = tuple(
        _obligation(o, i)
        for i, o in enumerate(_object_list(p["obligations"], "obligations"))
    )
    _check_obligations_closed(representation, obligations, path.name)
    spans = tuple(_span(s, i) for i, s in enumerate(_object_list(p["spans"], "spans")))
    batches, acceptances, lifts = _acceptance(p["acceptance"], "acceptance")

    oracle = AcceptedOracle(
        binding=ReleaseBinding(
            **{k: _string(binding[k], f"release_binding.{k}") for k in binding_fields}
        ),
        policy_version=_string(p["semantic_policy_version"], "semantic_policy_version"),
        policy_hash=_string(p["semantic_policy_hash"], "semantic_policy_hash"),
        schema_version=_string(schema["version"], "representation_schema.version"),
        schema_hash=_string(schema["hash"], "representation_schema.hash"),
        spans=spans,
        representation=representation,
        obligations=obligations,
    )
    inputs = AcceptedInputs(
        oracle=oracle, batches=batches, acceptances=acceptances, lifts=lifts
    )

    # Evidence is validated as strictly as the result it justifies. A file whose
    # batch retains a digest but not the diff it names, or that accepts a span
    # nobody acted on, is not a weaker acceptance — it is a claim of acceptance
    # with the acceptance missing.
    if violations := validate_acceptance(inputs.classification()):
        raise OracleLoadError(
            f"{path.name}: acceptance evidence is not complete: "
            f"{'; '.join(violations)}"
        )
    return inputs


def load_oracle(path: Path) -> AcceptedOracle:
    """Load one committed accepted oracle from JSON.

    The oracle is the accepted-inputs artifact with its review evidence dropped:
    two files that reviewed their way to the same accepted classification are
    the same authority, so reviewer, timestamp, batch grouping, and diff never
    reach projection identity (#137 acceptance criterion 11).
    """
    return load_accepted_inputs(path).oracle


def candidate_from_accepted_inputs(inputs: AcceptedInputs) -> ProjectionCandidate:
    """The build candidate one committed accepted-inputs artifact states.

    This is the *input* direction: committed bytes a reviewer accepted become
    the candidate that is persisted, reconstructed, and then judged. It is not
    the forbidden direction — nothing here derives accepted authority from a
    candidate or from persisted output, and :func:`load_oracle` reads the same
    committed bytes rather than anything this function produced.

    Unlike the oracle, the candidate *does* carry the acceptance evidence: the
    publication gate requires an explicit acceptance record for every span in
    reconstructed persisted state, and that evidence has to reach persistence
    from a committed input or no build could ever satisfy it.
    """
    return ProjectionCandidate(
        binding=inputs.oracle.binding,
        classification=inputs.classification(),
        representation=inputs.oracle.representation,
        schema_version=inputs.oracle.schema_version,
        schema_hash=inputs.oracle.schema_hash,
    )


def committed_oracle_for(
    package_uuid: str, release_version: str
) -> AcceptedOracle | None:
    """Return the committed oracle for one 5c release, or ``None``.

    Resolves from :data:`COMMITTED_ORACLE_DIR` and nowhere else. There is no
    directory argument, because an exported helper that accepts one is the same
    bypass as a publication entry that accepts one: a caller could resolve a
    self-authored oracle from a writable directory and hand it to the gate as
    committed authority.

    ``None`` here means "no accepted authority is committed for this release",
    which callers turn into a typed ``ABSENT`` publication outcome. It is never
    an empty oracle: an empty oracle would compare equal to an empty projection
    and publish nothing as if it were everything.
    """
    inputs = _resolve_committed_inputs(
        package_uuid, release_version, COMMITTED_ORACLE_DIR
    )
    return None if inputs is None else inputs.oracle


def committed_inputs_for(
    package_uuid: str, release_version: str
) -> AcceptedInputs | None:
    """Return the committed accepted inputs for one 5c release, or ``None``.

    Same resolution and same directory as :func:`committed_oracle_for`; this is
    the build-side view, which additionally carries the acceptance evidence.
    """
    return _resolve_committed_inputs(
        package_uuid, release_version, COMMITTED_ORACLE_DIR
    )


def _resolve_committed_inputs(
    package_uuid: str, release_version: str, directory: Path
) -> AcceptedInputs | None:
    """Resolution semantics, parameterized by directory for tests only.

    Two committed artifacts for one release is a rejection, not a choice.
    Picking one would make publication depend on filesystem ordering.
    """
    matches = [
        inputs
        for inputs in (
            load_accepted_inputs(p) for p in sorted(directory.glob("*.json"))
        )
        if inputs.oracle.binding.package_uuid == package_uuid
        and inputs.oracle.binding.release_version == release_version
    ]
    if len(matches) > 1:
        raise OracleLoadError(
            f"{len(matches)} committed oracles claim release "
            f"{package_uuid}/{release_version}"
        )
    return matches[0] if matches else None


def _resolve_committed_oracle(
    package_uuid: str, release_version: str, directory: Path
) -> AcceptedOracle | None:
    """Directory-parameterized oracle resolution, for tests only."""
    inputs = _resolve_committed_inputs(package_uuid, release_version, directory)
    return None if inputs is None else inputs.oracle


# ---------------------------------------------------------------------------
# Writing committed artifacts
# ---------------------------------------------------------------------------


def accepted_inputs_payload(inputs: AcceptedInputs) -> dict[str, object]:
    """Canonical JSON payload of one accepted-inputs artifact.

    Reuses :func:`oracle_payload` for the accepted result and
    :func:`accounting.acceptance_evidence_payload` for the evidence, so the file
    a reviewer commits is written in the same canonical form the loader expects
    and the identity functions already agree on.
    """
    payload: dict[str, object] = {"artifact_kind": ACCEPTED_ARTIFACT_KIND}
    payload.update(oracle_payload(inputs.oracle))
    evidence = acceptance_evidence_payload(inputs.classification())
    acceptance: dict[str, object] = {
        "batches": evidence["batches"],
        "records": evidence["acceptances"],
    }
    if inputs.lifts:
        # Emitted only when there is one, so an artifact that never crossed a
        # succession keeps the exact bytes it was committed with. Same
        # omit-when-empty discipline the post-schema-3 fields follow, and the
        # reason the committed conditions-1 file still round-trips unchanged.
        acceptance["lifts"] = [
            {
                "lift_id": lift.lift_id,
                "from_version": lift.from_version,
                "from_hash": lift.from_hash,
                "to_version": lift.to_version,
                "to_hash": lift.to_hash,
                "verified_counts": [
                    {"collection": name, "elements": count}
                    for name, count in lift.verified_counts
                ],
            }
            for lift in inputs.lifts
        ]
    payload["acceptance"] = acceptance
    return payload
