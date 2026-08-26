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

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from afterworlds.ingestion.corpus.hashing import canonical_bytes
from afterworlds.ingestion.mechanical.projection import representation_payload
from afterworlds.ingestion.mechanical.representation import (
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
    "verify_lift",
]

SCHEMA_3_VERSION = "5d-representation-schema-3"
SCHEMA_3_HASH = "43ed330d3b3630d37ed92122fd87cc2c170863bab4465e53c727f1b8c6b86e05"  # noqa: E501  # pragma: allowlist secret
SCHEMA_4_VERSION = "5d-representation-schema-4"
#: Pinned literally. See the module docstring for why this is not derived.
SCHEMA_4_HASH = "cddba5048a0f8e64dd289d3dd08b1c6f03e130120f89721288eb756b1f27011e"  # noqa: E501  # pragma: allowlist secret


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
    #: Inherited elements proved byte-identical across the succession, by
    #: collection. Retained so an audit can see the proof's extent rather than
    #: taking "it verified" on trust.
    verified_counts: tuple[tuple[str, int], ...]


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

    counts: list[tuple[str, int]] = []
    for collection in sorted(before):
        source_bytes = canonical_bytes(before[collection])
        target_bytes = canonical_bytes(after[collection])
        if source_bytes != target_bytes:
            raise SchemaLiftError(
                f"{collection}: inherited accepted authority does not survive "
                f"{lift.lift_id} unchanged. A lift may authorize a wider schema; "
                "it may never move a semantic identity the Owner already accepted"
            )
        item = before[collection]
        counts.append((collection, len(item) if isinstance(item, list) else 1))
    return SchemaLiftRecord(
        lift_id=lift.lift_id,
        from_version=lift.from_version,
        from_hash=lift.from_hash,
        to_version=lift.to_version,
        to_hash=lift.to_hash,
        verified_counts=tuple(counts),
    )


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
