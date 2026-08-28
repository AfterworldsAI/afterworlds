"""Authorized representation-schema succession for accepted authority — CRD Issue 5d.

Accepted authority is committed under the representation schema it was reviewed
under. When a later content batch needs a wider schema, the two have to meet:
``accept_proposal`` refuses a proposal whose schema differs from the prior
accepted artifact's, and that refusal is correct — a proposal built under a
union that means something else is not extending the reviewed authority, it is
replacing it.

This module supplies the one authorized way through, and nothing else.

**What a lift is, and what it is deliberately not.**

Owner Decision 2026-08-24 settled that a previously accepted fact key or
provenance coordinate may not move. :mod:`representation` implements that by
omitting a post-schema-3 field from the canonical payload when it carries no
meaning, so a schema-3 element's canonical form *is already* its schema-4
canonical form. A lift therefore never rewrites content. It:

1. **authorizes** the exact ``(version, hash) -> (version, hash)`` transition;
2. **proves** every inherited element is byte-identical under the new schema; and
3. **records** that it happened, as evidence rather than as identity.

That is a stronger guarantee than a transforming lift could give. A transforming
lift has to argue that its mapping preserved meaning; this one demonstrates that
nothing moved.

**Compatibility is declared, never inferred.** The registry is keyed by the exact
source pair and names its destination pair literally. Version ordering is not
evidence: "schema 4 is newer than schema 3" says nothing about whether schema 4
can carry schema 3's accepted content, and a build that reasoned that way would
authorize every future succession in advance. An unregistered pair fails closed.

The destination hash is written as a literal rather than computed from
``representation_schema_hash()``. Computing it would make the registry agree with
whatever the union currently is — so an unrelated later edit to the type surface
would silently re-authorize a transition nobody reviewed, which is exactly the
restamping this module exists to refuse.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from afterworlds.ingestion.corpus.hashing import canonical_bytes
from afterworlds.ingestion.mechanical.projection import representation_payload
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_COLLECTIONS,
    RepresentationDraft,
    held_structure_violations,
    post_schema_3_violations,
)

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from afterworlds.ingestion.mechanical.oracle import AcceptedInputs

__all__ = [
    "SCHEMA_LIFTS",
    "lift_accepted_inputs",
    "SchemaLift",
    "SchemaLiftError",
    "SchemaLiftRecord",
    "UnknownSchemaLiftError",
    "lift_for",
    "lift_chain_violations",
    "verify_lift",
]

SCHEMA_3_VERSION = "5d-representation-schema-3"
SCHEMA_3_HASH = "43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05"  # noqa: E501  # pragma: allowlist secret
SCHEMA_4_VERSION = "5d-representation-schema-4"
#: Pinned literally. See the module docstring for why this is not derived.
SCHEMA_4_HASH = "e1fed378a23e5984ddcc7f0fc08e03118fe05db1594e31b449facdf12fdadbc9"  # noqa: E501  # pragma: allowlist secret


class SchemaLiftError(ValueError):
    """An authorized lift did not hold when it was checked."""


class UnknownSchemaLiftError(SchemaLiftError):
    """No lift is registered for this exact transition."""

    def __init__(self, source: tuple[str, str], target: tuple[str, str]) -> None:
        super().__init__(
            f"no authorized representation-schema lift from {source[0]!r} "
            f"({source[1]}) to {target[0]!r} ({target[1]}). A schema succession "
            "must be registered for its exact version and hash pair; a later "
            "version is not evidence that it can carry earlier accepted content"
        )
        self.source = source
        self.target = target


@dataclass(frozen=True)
class SchemaLift:
    """One authorized succession, keyed by the exact source pair.

    ``rationale`` is retained so the registry states *why* a transition was
    authorized, not merely that it was. It is evidence and never participates in
    any identity.
    """

    lift_id: str
    from_version: str
    from_hash: str
    to_version: str
    to_hash: str
    rationale: str


@dataclass(frozen=True)
class SchemaLiftRecord:
    """Evidence that an accepted artifact crossed a schema succession.

    Lives on the evidence half of ``AcceptedInputs``, beside the acceptance
    batches, and never on ``AcceptedOracle``: which schema an artifact was
    carried across is review and migration process, and process is not
    identity-bearing (#137 acceptance criterion 11).
    """

    lift_id: str
    from_version: str
    from_hash: str
    to_version: str
    to_hash: str
    #: The collections proved byte-identical across the succession — every one
    #: of them, or :func:`verify_lift` raised instead of returning, because a
    #: partial proof is not a lift.
    #:
    #: Retained as *names*, and deliberately not as element counts. A count is a
    #: claim about content that no longer exists in isolation: the artifact holds
    #: the inherited elements merged with everything accepted after the crossing,
    #: one committed file supersedes its predecessor, and no record here anchors
    #: the crossing to a point in the batch sequence. A loader can therefore
    #: neither re-derive the historical extent nor bound it to anything better
    #: than "no larger than the collection it is now" — so a fabricated number
    #: would validate exactly as well as a true one. Evidence a reader cannot
    #: check is not evidence, and stating it as though it were made this audit
    #: surface say more than the build could support (#137 round 3).
    verified_collections: tuple[str, ...]


#: Every authorized succession. Explicit rows, never a rule over version order.
SCHEMA_LIFTS: dict[tuple[str, str], SchemaLift] = {
    (SCHEMA_3_VERSION, SCHEMA_3_HASH): SchemaLift(
        lift_id="5d-lift-schema-3-to-4",
        from_version=SCHEMA_3_VERSION,
        from_hash=SCHEMA_3_HASH,
        to_version=SCHEMA_4_VERSION,
        to_hash=SCHEMA_4_HASH,
        rationale=(
            "Schema 4 is strictly additive to schema 3's type surface, and every "
            "field it adds is omitted from the canonical payload when it carries "
            "no meaning. A schema-3 element therefore has the same canonical form "
            "under both, which verify_lift proves element by element rather than "
            "asserting."
        ),
    ),
}


def lift_for(source: tuple[str, str], target: tuple[str, str]) -> SchemaLift:
    """The authorized lift from *source* to *target*, or fail closed.

    Both pairs are matched exactly. A registered lift whose destination is not
    the requested target is refused rather than applied — that case is a
    proposal built under a schema nobody authorized this artifact to reach, and
    it is the reverse/skipped transition the tests exercise.
    """
    lift = SCHEMA_LIFTS.get(source)
    if lift is None or (lift.to_version, lift.to_hash) != target:
        raise UnknownSchemaLiftError(source, target)
    return lift


def verify_lift(lift: SchemaLift, prior: RepresentationDraft) -> SchemaLiftRecord:
    """Prove *prior* survives *lift* unchanged, or raise.

    The proof is byte-identity of the canonical payload under both the source
    and the destination schema, collection by collection. Nothing is normalized,
    reshaped, or defaulted on the way through: a difference is a semantic change
    the reviewer never saw, so it raises rather than being reconciled.

    The legality check runs first and separately. An inherited element already
    carrying post-schema-3 meaning would be an artifact whose declared schema and
    content disagree — a restamp — and it must be refused as such rather than
    reported as a payload difference.
    """
    if illegal := post_schema_3_violations(prior, lift.from_version):
        raise SchemaLiftError(
            f"the prior representation declares {lift.from_version!r} but carries "
            "content only a later schema can state, so it was not accepted under "
            "the schema it names: " + "; ".join(illegal)
        )
    # A subclassed nested value object would survive the byte-identity proof
    # below for exactly the reason it survives everywhere else: it canonicalizes
    # to its declared base's payload. Proving that such a prior is "unchanged"
    # would be proving the wrong thing.
    if drift := held_structure_violations(prior):
        raise SchemaLiftError(
            "the prior representation holds a structure outside its closed "
            "declaration, so its canonical payload does not represent what it "
            "carries: " + "; ".join(drift)
        )

    before = representation_payload(prior, schema_version=lift.from_version)
    after = representation_payload(prior, schema_version=lift.to_version)
    if set(before) != set(after):
        raise SchemaLiftError(
            "the two schemas do not serialize the same collections: "
            f"{sorted(set(before) ^ set(after))}"
        )

    for collection in sorted(before):
        if canonical_bytes(before[collection]) != canonical_bytes(after[collection]):
            raise SchemaLiftError(
                f"{collection}: inherited accepted authority does not survive "
                f"{lift.lift_id} unchanged. A lift may authorize a wider schema; "
                "it may never move a semantic identity the Owner already accepted"
            )
    return SchemaLiftRecord(
        lift_id=lift.lift_id,
        from_version=lift.from_version,
        from_hash=lift.from_hash,
        to_version=lift.to_version,
        to_hash=lift.to_hash,
        # Every collection, because the loop above returns only when all of
        # them held. The extent is therefore a property of the contract rather
        # than a number the record asks to be believed.
        verified_collections=tuple(sorted(before)),
    )


def lift_chain_violations(
    lifts: Sequence[SchemaLiftRecord], declared: tuple[str, str]
) -> list[str]:
    """Violations of a loaded lift chain against the registry and *declared*.

    Loaded evidence is *read from a file*, so nothing about it is self-proving.
    The wire-shape checks in the loader establish that each record is
    well-formed; they say nothing about whether the succession it claims was
    ever authorized, ever happened, or could have happened. Without this, an
    artifact loads clean while asserting a transition no registry contains and a
    proof extent over collections the representation does not have — an audit
    surface that states more than the build ever did.

    Six properties, in the order a reader would check them:

    1. **Registered.** Each record's source pair is a key in :data:`SCHEMA_LIFTS`,
       and the registered lift's ``lift_id``, destination version and
       destination hash all match the record. That single check subsumes
       "invented", "reversed", and "hash-mismatched": none of those has a
       registry row whose destination agrees.
    2. **Continuous, oldest first.** Each record's destination pair is the next
       record's source pair. Reordering or omitting a step breaks the join, so
       neither needs a rule of its own.
    3. **Terminal.** The last record's destination is the schema the artifact
       *declares*. Evidence that ends somewhere else describes a different
       artifact.
    4. **Non-repeating.** No transition appears twice. A succession is crossed
       once; a repeat is either a duplicated record or a cycle, and both are
       impossible histories rather than redundant ones.
    5. **Exactly the representation's collections, each named once.** A proof
       extent is a claim about what was verified, so it must range over the
       collections that exist — no invented name, none missing, none repeated.
       It is a claim about *names* only; :class:`SchemaLiftRecord` records why
       the element counts a lift produces in process are not carried, and a set
       comparison alone let a duplicated row through (#137 round 3).
    6. **Empty is legal.** An artifact that never crossed a succession has no
       evidence to carry, and property 3 does not apply to it. The committed
       ``conditions-1`` artifact is exactly this case.
    """
    findings: list[str] = []
    if not lifts:
        return findings

    seen: set[tuple[str, str, str, str]] = set()
    for index, record in enumerate(lifts):
        at = f"lifts[{index}] ({record.lift_id})"
        source = (record.from_version, record.from_hash)
        registered = SCHEMA_LIFTS.get(source)
        if registered is None:
            findings.append(
                f"{at}: no lift is registered from {record.from_version!r} "
                f"({record.from_hash}); this succession was never authorized"
            )
        elif (registered.lift_id, registered.to_version, registered.to_hash) != (
            record.lift_id,
            record.to_version,
            record.to_hash,
        ):
            findings.append(
                f"{at}: the registered lift from {record.from_version!r} is "
                f"{registered.lift_id!r} to {registered.to_version!r} "
                f"({registered.to_hash}), not {record.lift_id!r} to "
                f"{record.to_version!r} ({record.to_hash})"
            )

        transition = (*source, record.to_version, record.to_hash)
        if transition in seen:
            findings.append(
                f"{at}: this transition is already recorded; a succession is "
                "crossed once"
            )
        seen.add(transition)

        if index:
            previous = lifts[index - 1]
            if (previous.to_version, previous.to_hash) != source:
                findings.append(
                    f"{at}: does not continue the previous record, which ended "
                    f"at {previous.to_version!r} ({previous.to_hash}); lift "
                    "evidence is an ordered chain, oldest first"
                )

        names = record.verified_collections
        # Checked before the set comparison, and separately from it: a set
        # discards the duplicate, so comparing sets alone accepted an extent
        # that names one collection twice.
        if len(names) != len(set(names)):
            findings.append(
                f"{at}: proof extent names a collection more than once "
                f"({sorted(names)}); each collection is proved exactly once"
            )
        if set(names) != REPRESENTATION_COLLECTIONS:
            findings.append(
                f"{at}: proof extent covers {sorted(set(names))}, not the "
                f"representation's collections {sorted(REPRESENTATION_COLLECTIONS)}"
            )

    last = lifts[-1]
    if (last.to_version, last.to_hash) != declared:
        findings.append(
            f"lifts[{len(lifts) - 1}] ({last.lift_id}): the chain ends at "
            f"{last.to_version!r} ({last.to_hash}), but the artifact declares "
            f"{declared[0]!r} ({declared[1]})"
        )
    return findings


def lift_accepted_inputs(
    inputs: AcceptedInputs, target: tuple[str, str]
) -> tuple[AcceptedInputs, SchemaLiftRecord]:
    """Re-declare *inputs* under *target*, having proved nothing moved.

    The whole-artifact form of :func:`verify_lift`, and the shape
    ``accept_proposal`` uses when a proposal extends accepted authority across a
    schema succession.

    What changes is exactly one thing: the oracle's declared
    ``(schema_version, schema_hash)``. Every span, record, component, option,
    fact, qualifier, prose binding, reference, relationship and provenance claim
    is carried through **by identity, not by transformation** — they are the same
    objects, and :func:`verify_lift` has already proved their canonical payloads
    are byte-identical under both contracts before this returns.

    The acceptance evidence is untouched for the same reason it is untouched by
    an ordinary extension: ``batches``, ``acceptances``, each batch's
    ``proposal_identity``, reviewer, timestamp, rule, scope and diff record what
    a human reviewed and when. A schema succession is not a review, so it may not
    edit them.
    """
    lift = lift_for((inputs.oracle.schema_version, inputs.oracle.schema_hash), target)
    record = verify_lift(lift, inputs.oracle.representation)
    lifted = replace(
        inputs,
        oracle=replace(
            inputs.oracle,
            schema_version=lift.to_version,
            schema_hash=lift.to_hash,
        ),
    )
    return lifted, record
