"""Retained immutable override-set versions — CRD Issue 5d, Decision 9.

ADR-005d rejected "record the override-set identity but retain only current
override rows": the identifier would name state that no longer exists once an
override is edited, disabled, reprioritized, retargeted, or deleted, leaving
audit and replay able to detect divergence but not to reconstruct the authority
actually applied. This module is the retention that closes that gap.

The shape chosen here is a **content-addressed snapshot**: one immutable version
row keyed by the ``override_set_uuid``, plus its complete ordered entries. ADR-
005d explicitly leaves the shape open (snapshot, append-only version records, or
an event log that reconstructs the canonical version); a snapshot is the
lowest-complexity option that is already content-addressed, so its reconstructed
canonical version reproducing the recorded identity is a property of how it is
stored rather than a second mechanism to verify.

Two operations, and they are deliberately different:

* :func:`retain_override_set` is called at binding-resolution time. It is
  idempotent by construction — the identity *is* the primary key, so recording
  the same state twice writes nothing the second time. When a version already
  exists it is verified rather than trusted: its retained entries must still
  reproduce the identity they are stored under.
* :func:`load_override_set_version` is the audit and replay read. It resolves
  the retained version and must succeed. ``STALE`` is not a valid answer here —
  a failure to reconstruct is a retention defect, which is why it raises
  :class:`OverrideSetRetentionError` rather than returning an outcome a caller
  could mistake for ordinary divergence.

Retention writes into the caller's transaction and flushes rather than commits.
The caller owns the commit boundary, so a resolution that is part of a larger
failed unit of work does not leave a half-retained version behind.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.persistence.orm.rules_authority import (
    OverrideSetEntryORM,
    OverrideSetVersionORM,
)
from afterworlds.services.rules_authority.override_set import (
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
    override_set_identity,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
    TargetShapeError,
)

__all__ = [
    "OverrideSetRetentionError",
    "load_override_set_version",
    "retain_override_set",
]


class OverrideSetRetentionError(RuntimeError):
    """Raised when a retained override-set version cannot be reconstructed.

    This is never a divergence signal. It means the replay evidence a recorded
    binding depends on is missing, incomplete, or no longer derives its own
    identity — a defect in retention, reported as such so it cannot be mistaken
    for the ordinary "current overrides have moved on" case.
    """


def retain_override_set(
    session: Session, state: EffectiveOverrideSet, *, now: str
) -> str:
    """Record *state* as an immutable version, returning its identity.

    Idempotent: an identical state is the *same* identity, so re-recording it
    verifies the existing version instead of writing a second one. The
    verification is not ceremony — a version whose retained entries no longer
    reproduce their own identity would silently answer replay reads with the
    wrong authority.
    """
    identity = state.override_set_uuid
    existing = session.execute(
        select(OverrideSetVersionORM).where(
            OverrideSetVersionORM.override_set_uuid == identity
        )
    ).scalar_one_or_none()
    if existing is not None:
        # Reconstruct rather than trust: this is the read path replay will take,
        # so proving it here means a retention defect surfaces at the write that
        # could still have fixed it.
        load_override_set_version(session, identity)
        return identity

    session.add(
        OverrideSetVersionORM(
            override_set_uuid=identity,
            package_uuid=state.package_uuid,
            release_version=state.release_version,
            entry_count=len(state.entries),
            recorded_at=now,
        )
    )
    # Flushed before its entries: they carry a foreign key to it, and the unit
    # of work is free to order two pending inserts either way.
    session.flush()
    for entry in state.entries:
        session.add(
            OverrideSetEntryORM(
                override_set_uuid=identity,
                apply_order=entry.apply_order,
                override_id=entry.override_id,
                override_origin=entry.origin.value,
                target_kind=entry.target.kind.value,
                target_record_key=entry.target.record_key,
                target_component_key=entry.target.component_key,
                target_fact_key=entry.target.fact_key,
                override_operation=entry.operation.value,
                precedence=entry.precedence,
                is_enabled=entry.is_enabled,
                payload=entry.payload,
            )
        )
    session.flush()
    return identity


def _entry_from_row(row: OverrideSetEntryORM) -> EffectiveOverrideEntry:
    try:
        origin = OverrideOriginEnum(row.override_origin)
        operation = OverrideOperationEnum(row.override_operation)
        kind = MechanicalTargetKind(row.target_kind)
        target = MechanicalTarget(
            kind=kind,
            record_key=row.target_record_key,
            component_key=row.target_component_key,
            fact_key=row.target_fact_key,
        )
    except (ValueError, TargetShapeError) as exc:
        raise OverrideSetRetentionError(
            f"retained override-set entry {row.override_set_uuid}/{row.apply_order} "
            f"does not parse: {exc}"
        ) from exc
    if not isinstance(row.payload, dict):
        raise OverrideSetRetentionError(
            f"retained override-set entry {row.override_set_uuid}/{row.apply_order} "
            "has no payload object"
        )
    return EffectiveOverrideEntry(
        override_id=row.override_id,
        origin=origin,
        target=target,
        operation=operation,
        precedence=row.precedence,
        apply_order=row.apply_order,
        is_enabled=bool(row.is_enabled),
        payload=dict(row.payload),
    )


def load_override_set_version(
    session: Session, override_set_uuid: str
) -> EffectiveOverrideSet:
    """Resolve one retained override-set version for audit or replay.

    Reads only the retained tables. Current ``rp_mech_overrides`` rows are never
    consulted — they are the authoring surface, and an implementation that
    re-derived from them would reconstruct today's authority while claiming to
    reconstruct the recorded one.

    Raises :class:`OverrideSetRetentionError` when the version is absent, its
    entry count disagrees with what was retained, its apply order is not a
    contiguous sequence, or its entries no longer derive the identity they are
    stored under.
    """
    version = session.execute(
        select(OverrideSetVersionORM).where(
            OverrideSetVersionORM.override_set_uuid == override_set_uuid
        )
    ).scalar_one_or_none()
    if version is None:
        raise OverrideSetRetentionError(
            f"no retained override-set version {override_set_uuid}"
        )

    rows = (
        session.execute(
            select(OverrideSetEntryORM)
            .where(OverrideSetEntryORM.override_set_uuid == override_set_uuid)
            .order_by(OverrideSetEntryORM.apply_order)
        )
        .scalars()
        .all()
    )
    if len(rows) != version.entry_count:
        raise OverrideSetRetentionError(
            f"retained override-set version {override_set_uuid} records "
            f"{version.entry_count} entries, {len(rows)} are present"
        )
    if [r.apply_order for r in rows] != list(range(len(rows))):
        raise OverrideSetRetentionError(
            f"retained override-set version {override_set_uuid} has a broken "
            "apply order"
        )

    entries = tuple(_entry_from_row(row) for row in rows)
    rederived = override_set_identity(entries)
    if rederived != override_set_uuid:
        raise OverrideSetRetentionError(
            f"retained override-set version {override_set_uuid} reconstructs as "
            f"{rederived}"
        )
    return EffectiveOverrideSet(
        package_uuid=version.package_uuid,
        release_version=version.release_version,
        entries=entries,
    )
