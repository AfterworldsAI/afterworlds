"""Raw persisted state and its closure proof — CRD Issue 5d, Decision 8.

Reconstruction used to read persisted rows straight into the semantic model.
That order hides two things. A child row whose parent does not exist is simply
never joined, so it vanishes from the candidate *and* from the digest computed
over that candidate — retained database state outside the audit proof. And a
corrupted typed column raises whatever the enum constructor happens to raise,
so a verification API whose contract is to *report* tamper crashes instead.

So the pipeline is now two explicit stages:

``load complete raw row set → prove raw closure → reconstruct semantic candidate``

Every projection-scoped row is loaded once, into one structure, before any
semantic meaning is imposed on it. Closure is then proven over that inventory:
every row either contributes to the reconstructed candidate and its proof, or
it fails reconstruction with a typed error naming the table, the row, the
field, and the rejected value. Nothing is dropped, defaulted, or repaired.

This layer owns *persistence* relationships — parentage, uniqueness,
reconstructability, typed columns. It deliberately does not re-check semantic
honesty: whether the accepted classification is coherent, whether provenance
satisfies its obligations, and whether a reference resolves are the candidate
validators' job, and duplicating them here would create two places to disagree.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.persistence.orm.mechanical import (
    MechanicalAcceptanceBatchORM,
    MechanicalAcceptanceORM,
    MechanicalBatchDiffORM,
    MechanicalBatchScopeORM,
    MechanicalComponentORM,
    MechanicalFactORM,
    MechanicalProjectionORM,
    MechanicalProseBindingORM,
    MechanicalProvenanceORM,
    MechanicalRecordORM,
    MechanicalReferenceORM,
    MechanicalRelationshipORM,
    MechanicalSpanORM,
)

__all__ = [
    "PersistedStateReconstructionError",
    "RawProjectionState",
    "load_raw_state",
    "parse_enum",
    "validate_raw_closure",
]


class PersistedStateReconstructionError(ValueError):
    """Persisted state that cannot honestly reconstruct.

    One closed family for every way the database can fail to describe a
    projection: a malformed fact payload, an unknown fact family, an invalid
    typed column, an orphan child row, a malformed target key, or a duplicate
    that makes a parent ambiguous. Verification catches exactly this family and
    reports it as a finding — a deliberately narrow target, so an ordinary
    implementation bug still surfaces as a crash instead of being misreported
    as database corruption.
    """


def parse_enum[E: StrEnum](
    enum_cls: type[E], value: str, table: str, row: str, field: str
) -> E:
    """Convert one persisted string into its closed enum, or fail explicitly.

    No coercion and no fallback: an unrecognised value means the column no
    longer says what it said when it was written, and guessing which member was
    intended would be repair rather than reconstruction.
    """
    try:
        return enum_cls(value)
    except ValueError:
        raise PersistedStateReconstructionError(
            f"{table} {row}: {field} {value!r} is not a valid " f"{enum_cls.__name__}"
        ) from None


@dataclass(frozen=True)
class RawProjectionState:
    """Every projection-scoped row, loaded once from one transaction state.

    The header is separate because it is the projection's own row rather than
    one scoped beneath it.
    """

    projection_uuid: str
    header: MechanicalProjectionORM
    spans: Sequence[MechanicalSpanORM]
    batches: Sequence[MechanicalAcceptanceBatchORM]
    batch_scope: Sequence[MechanicalBatchScopeORM]
    batch_diff: Sequence[MechanicalBatchDiffORM]
    acceptances: Sequence[MechanicalAcceptanceORM]
    records: Sequence[MechanicalRecordORM]
    components: Sequence[MechanicalComponentORM]
    facts: Sequence[MechanicalFactORM]
    prose_bindings: Sequence[MechanicalProseBindingORM]
    relationships: Sequence[MechanicalRelationshipORM]
    references: Sequence[MechanicalReferenceORM]
    provenance: Sequence[MechanicalProvenanceORM]


def load_raw_state(
    session: Session, projection_uuid: str, header: MechanicalProjectionORM
) -> RawProjectionState:
    """Load every row scoped to *projection_uuid* in one pass."""

    def rows(model: Any) -> list[Any]:
        return list(
            session.execute(
                select(model).where(model.projection_uuid == projection_uuid)
            )
            .scalars()
            .all()
        )

    return RawProjectionState(
        projection_uuid=projection_uuid,
        header=header,
        spans=rows(MechanicalSpanORM),
        batches=rows(MechanicalAcceptanceBatchORM),
        batch_scope=rows(MechanicalBatchScopeORM),
        batch_diff=rows(MechanicalBatchDiffORM),
        acceptances=rows(MechanicalAcceptanceORM),
        records=rows(MechanicalRecordORM),
        components=rows(MechanicalComponentORM),
        facts=rows(MechanicalFactORM),
        prose_bindings=rows(MechanicalProseBindingORM),
        relationships=rows(MechanicalRelationshipORM),
        references=rows(MechanicalReferenceORM),
        provenance=rows(MechanicalProvenanceORM),
    )


def _valid_target_key(value: object) -> bool:
    """A persisted provenance target key must be a list of plain strings.

    The column is JSON, so it can hold anything. Only a list of strings can
    become the declared immutable tuple; a nested structure or a number would
    have to be coerced, and a coerced key addresses an element nobody declared.
    """
    return isinstance(value, list) and all(type(v) is str for v in value)


def validate_raw_closure(raw: RawProjectionState) -> None:
    """Prove the raw row set is a closed, relationally valid aggregate.

    Raises :class:`PersistedStateReconstructionError` listing every violation
    found, rather than the first — a corrupted projection usually breaks in
    more than one place, and reporting one at a time turns diagnosis into a
    guessing game.
    """
    problems: list[str] = []

    # Batch headers own a logical identity of (projection_uuid, batch_id); a
    # duplicate makes every child's parent ambiguous.
    batch_ids: set[str] = set()
    for batch in raw.batches:
        if batch.batch_id in batch_ids:
            problems.append(
                f"rp_mech_acceptance_batches: duplicate batch_id "
                f"{batch.batch_id!r} in one projection"
            )
        batch_ids.add(batch.batch_id)

    # Children are matched on (projection_uuid, batch_id). Because the raw set
    # is already scoped to this projection, a same-named batch in a *different*
    # projection cannot adopt these rows.
    for scope in raw.batch_scope:
        if scope.batch_id not in batch_ids:
            problems.append(
                f"rp_mech_batch_scope row {scope.row_id}: names batch "
                f"{scope.batch_id!r} with no header in this projection"
            )
    for diff in raw.batch_diff:
        if diff.batch_id not in batch_ids:
            problems.append(
                f"rp_mech_batch_diff row {diff.row_id}: names batch "
                f"{diff.batch_id!r} with no header in this projection"
            )

    # Scope order must be unambiguous: retained reviewer order is evidence, and
    # two rows claiming one position destroy it.
    ordinals: dict[tuple[str, int], int] = {}
    for scope in raw.batch_scope:
        slot = (scope.batch_id, scope.ordinal)
        ordinals[slot] = ordinals.get(slot, 0) + 1
    for (batch_id, ordinal), count in sorted(ordinals.items()):
        if count > 1:
            problems.append(
                f"rp_mech_batch_scope: batch {batch_id!r} has {count} rows at "
                f"ordinal {ordinal}"
            )

    seen_diff: set[tuple[str, str]] = set()
    for diff in raw.batch_diff:
        diff_key = (diff.batch_id, diff.span_id)
        if diff_key in seen_diff:
            problems.append(
                f"rp_mech_batch_diff: batch {diff.batch_id!r} has duplicate "
                f"diff rows for span {diff.span_id}"
            )
        seen_diff.add(diff_key)

    for acceptance in raw.acceptances:
        if acceptance.batch_id is not None and acceptance.batch_id not in batch_ids:
            problems.append(
                f"rp_mech_acceptances row {acceptance.row_id}: names batch "
                f"{acceptance.batch_id!r} with no header in this projection"
            )

    record_keys = {r.semantic_key for r in raw.records}
    if len(record_keys) != len(raw.records):
        problems.append("rp_mech_records: duplicate semantic_key in one projection")

    component_keys: set[tuple[str, str]] = set()
    for component in raw.components:
        component_key = (component.record_key, component.semantic_key)
        if component_key in component_keys:
            problems.append(
                f"rp_mech_components: duplicate component "
                f"{list(component_key)} in one projection"
            )
        component_keys.add(component_key)
        if component.record_key not in record_keys:
            problems.append(
                f"rp_mech_components row {component.row_id}: names record "
                f"{component.record_key!r} with no row in this projection"
            )

    # Facts are selected while iterating components during reconstruction, so
    # an unparented fact would simply never be visited.
    for fact in raw.facts:
        if (fact.record_key, fact.component_key) not in component_keys:
            problems.append(
                f"rp_mech_facts row {fact.row_id}: names component "
                f"{[fact.record_key, fact.component_key]} with no row in this "
                "projection"
            )

    for binding in raw.prose_bindings:
        if (binding.record_key, binding.component_key) not in component_keys:
            problems.append(
                f"rp_mech_prose_bindings row {binding.row_id}: names component "
                f"{[binding.record_key, binding.component_key]} with no row in "
                "this projection"
            )

    for relationship in raw.relationships:
        for field, related in (
            ("source_record_key", relationship.source_record_key),
            ("target_record_key", relationship.target_record_key),
        ):
            if related not in record_keys:
                problems.append(
                    f"rp_mech_relationships row {relationship.row_id}: {field} "
                    f"{related!r} has no record row in this projection"
                )

    # Reference *resolution* is a semantic question owned by the candidate
    # validator; what persistence owns is that the row attaches to real
    # persisted structure rather than dangling.
    for reference in raw.references:
        if (
            reference.from_record_key,
            reference.from_component_key,
        ) not in component_keys:
            problems.append(
                f"rp_mech_references row {reference.row_id}: names source "
                f"component {[reference.from_record_key, reference.from_component_key]}"
                " with no row in this projection"
            )

    for claim in raw.provenance:
        if not _valid_target_key(claim.target_key):
            problems.append(
                f"rp_mech_provenance row {claim.row_id}: target_key "
                f"{claim.target_key!r} is not a list of strings"
            )

    if problems:
        raise PersistedStateReconstructionError(
            f"projection {raw.projection_uuid}: " + "; ".join(problems)
        )
