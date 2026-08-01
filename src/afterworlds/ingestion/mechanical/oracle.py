"""The accepted completeness oracle — CRD Issue 5d, Decision 5.

The publication gate compares reconstructed persisted state against *this*, and
the only property that makes the comparison worth anything is independence: an
oracle derived from the projection it checks proves nothing but that the code
is self-consistent.

Independence is structural here, not a convention:

* this module imports no session, no ORM, and nothing from
  :mod:`persistence`, :mod:`raw_state`, or :mod:`gate`. There is no code path,
  public or private, that builds an ``AcceptedOracle`` from a persisted
  projection or from a :class:`ProjectionCandidate`;
* :func:`load_oracle` reads a committed JSON file and nothing else. Its whole
  input is bytes on disk that a reviewer accepted and a commit records; and
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

**What is committed today.** ``oracles/`` holds no production SRD oracle, so
the production 5c release resolves to no accepted authority and its projection
cannot be published. Later inactive-content PRs commit the accepted full-corpus
oracle; this PR builds the machinery that will judge it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from afterworlds.ingestion.corpus.hashing import hash_obj
from afterworlds.ingestion.mechanical.accounting import span_payload
from afterworlds.ingestion.mechanical.canonical import canonical_order
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.projection import (
    ReleaseBinding,
    representation_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    ComponentDraft,
    FactFamily,
    MalformedFactPayloadError,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RelationshipDraft,
    RelationshipKind,
    RepresentationDraft,
    UnknownFactFamilyError,
    fact_from_payload,
)

__all__ = [
    "COMMITTED_ORACLE_DIR",
    "AcceptedOracle",
    "OracleLoadError",
    "RecordObligation",
    "committed_oracle_for",
    "load_oracle",
    "obligation_payload",
    "oracle_identity",
    "oracle_payload",
]

#: Committed accepted oracles, one JSON file per published 5c release.
COMMITTED_ORACLE_DIR = Path(__file__).resolve().parent / "oracles"


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
    spans: tuple[SemanticSpan, ...]
    representation: RepresentationDraft
    obligations: tuple[RecordObligation, ...]


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
        "spans": span_payload(oracle.spans),
        "representation": representation_payload(oracle.representation),
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


def _require(payload: object, keys: tuple[str, ...], where: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise OracleLoadError(
            f"{where}: expected an object, got {type(payload).__name__}"
        )
    supplied = set(payload)
    if missing := sorted(set(keys) - supplied):
        raise OracleLoadError(f"{where}: missing {missing}")
    if extra := sorted(supplied - set(keys)):
        raise OracleLoadError(f"{where}: unexpected {extra}")
    return payload


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
        span_id=p["span_id"],
        leaf_id=p["leaf_id"],
        char_start=p["char_start"],
        char_end=p["char_end"],
        disposition=_enum(SemanticDisposition, p["disposition"], where),
        # An oracle span is accepted authority by construction: an unaccepted
        # claim has no business in a committed oracle, so the review state is
        # not a field a file may set to something else.
        review_state=ReviewState.ACCEPTED,
        non_mechanical_reason_code=p["non_mechanical_reason_code"],
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
    for i, raw in enumerate(p["records"]):
        where = f"representation.records[{i}]"
        r = _require(raw, ("semantic_key", "kind", "parent_key"), where)
        records.append(
            RecordDraft(
                semantic_key=r["semantic_key"],
                kind=_enum(RecordKind, r["kind"], where),
                parent_key=r["parent_key"],
            )
        )

    components = []
    for i, raw in enumerate(p["components"]):
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
        )
        try:
            facts = tuple(fact_from_payload(f) for f in c["facts"])
        except (MalformedFactPayloadError, UnknownFactFamilyError) as exc:
            # Both halves of the closed union's rejection: a payload that will
            # not rebuild its declared family, and a family outside the union.
            # The second is a TypeError, so catching ValueError alone would let
            # an undeclared family escape as an unclassified crash.
            raise OracleLoadError(f"{where}: {exc}") from exc
        components.append(
            ComponentDraft(
                record_key=c["record_key"],
                semantic_key=c["semantic_key"],
                handling=_enum(ComponentHandling, c["handling"], where),
                irreducibility_reason_code=c["irreducibility_reason_code"],
                facts=facts,
            )
        )

    prose_bindings = []
    for i, raw in enumerate(p["prose_bindings"]):
        where = f"representation.prose_bindings[{i}]"
        b = _require(
            raw,
            ("record_key", "component_key", "chunk_id", "irreducibility_reason_code"),
            where,
        )
        prose_bindings.append(
            ProseBindingDraft(
                record_key=b["record_key"],
                component_key=b["component_key"],
                chunk_id=b["chunk_id"],
                irreducibility_reason_code=b["irreducibility_reason_code"],
            )
        )

    relationships = []
    for i, raw in enumerate(p["relationships"]):
        where = f"representation.relationships[{i}]"
        rel = _require(raw, ("source_record_key", "target_record_key", "kind"), where)
        relationships.append(
            RelationshipDraft(
                source_record_key=rel["source_record_key"],
                target_record_key=rel["target_record_key"],
                kind=_enum(RelationshipKind, rel["kind"], where),
            )
        )

    references = []
    for i, raw in enumerate(p["references"]):
        where = f"representation.references[{i}]"
        ref = _require(
            raw,
            (
                "from_record_key",
                "from_component_key",
                "source_text",
                "scope_key",
                "target_record_key",
            ),
            where,
        )
        references.append(ReferenceDraft(**ref))

    provenance = []
    for i, raw in enumerate(p["provenance"]):
        where = f"representation.provenance[{i}]"
        pr = _require(raw, ("target_kind", "target_key", "span_id", "role"), where)
        provenance.append(
            ProvenanceClaim(
                target_kind=_enum(ProvenanceTargetKind, pr["target_kind"], where),
                target_key=tuple(pr["target_key"]),
                span_id=pr["span_id"],
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
        record_key=o["record_key"],
        kind=_enum(RecordKind, o["kind"], where),
        structured_fact_families=frozenset(
            _enum(FactFamily, f, where) for f in o["structured_fact_families"]
        ),
        prose_bound_components=frozenset(o["prose_bound_components"]),
    )


def load_oracle(path: Path) -> AcceptedOracle:
    """Load one committed accepted oracle from JSON.

    The whole input is the file. Nothing is read from the database, from a
    candidate, or from the current semantic policy.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OracleLoadError(f"{path.name}: {exc}") from exc

    p = _require(
        raw,
        (
            "release_binding",
            "semantic_policy_version",
            "semantic_policy_hash",
            "spans",
            "representation",
            "obligations",
        ),
        path.name,
    )
    binding = _require(
        p["release_binding"],
        (
            "package_uuid",
            "release_version",
            "authoritative_source_hash",
            "transform_config_hash",
            "bundle_root_hash",
            "persisted_corpus_digest",
        ),
        "release_binding",
    )
    return AcceptedOracle(
        binding=ReleaseBinding(**binding),
        policy_version=p["semantic_policy_version"],
        policy_hash=p["semantic_policy_hash"],
        spans=tuple(_span(s, i) for i, s in enumerate(p["spans"])),
        representation=_representation(p["representation"]),
        obligations=tuple(_obligation(o, i) for i, o in enumerate(p["obligations"])),
    )


def committed_oracle_for(
    package_uuid: str, release_version: str, *, directory: Path | None = None
) -> AcceptedOracle | None:
    """Return the committed oracle for one 5c release, or ``None``.

    ``None`` here means "no accepted authority is committed for this release",
    which callers turn into a typed ``ABSENT`` publication outcome. It is never
    an empty oracle: an empty oracle would compare equal to an empty projection
    and publish nothing as if it were everything.

    Two committed oracles for one release is a rejection, not a choice. Picking
    one would make publication depend on filesystem ordering.
    """
    directory = COMMITTED_ORACLE_DIR if directory is None else directory
    matches = [
        oracle
        for oracle in (load_oracle(p) for p in sorted(directory.glob("*.json")))
        if oracle.binding.package_uuid == package_uuid
        and oracle.binding.release_version == release_version
    ]
    if len(matches) > 1:
        raise OracleLoadError(
            f"{len(matches)} committed oracles claim release "
            f"{package_uuid}/{release_version}"
        )
    return matches[0] if matches else None
