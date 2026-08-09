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
failed unit of work does not leave a half-retained version behind. Within that
transaction the whole unit — version, entries, and scope association — is written
under one savepoint, so a partial failure unwinds all of it rather than leaving
an orphan snapshot the next reader would have to reason about.

That guarantee needs a physical transaction underneath it, which a read-only
prelude does not produce: under ``sqlite3``'s legacy transaction control a
session that has only read is still in SQLite autocommit, and a savepoint opened
there is the outermost one — releasing it *commits*. Binding resolution reads
before it retains, so this was exactly the shape that occurred. Retention
therefore calls :func:`~afterworlds.persistence.database.ensure_physical_transaction`
first, which makes the savepoint genuinely nested and leaves the commit boundary
where the caller expects it.

**Concurrency.** Retention runs on every binding resolution, so two sessions
resolving the same package at the same time both try to retain the same content.
That is the expected case, not an error, and it is handled by writing through
``INSERT ... ON CONFLICT DO NOTHING`` against content-aware immutability guards
rather than by querying for absence first and racing into the gap. See
:func:`_insert_or_ignore` — the guard shape and the insert shape are one design
and neither is safe alone.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import Insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.persistence.database import ensure_physical_transaction
from afterworlds.persistence.orm.rules_authority import (
    OverrideSetEntryORM,
    OverrideSetScopeORM,
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


def _insert_or_ignore(model: type) -> Insert:
    """An insert that treats an already-present identical row as done.

    This is the idempotent half of a mechanism whose other half is the
    content-aware ``BEFORE INSERT`` guards in migration ``0024``, and the two
    only work together.

    Query-then-insert cannot be made concurrency-safe here: two sessions both
    observe absence, both insert, and the loser takes a uniqueness violation for
    doing exactly what it was asked to. ``ON CONFLICT DO NOTHING`` removes that
    race at the source instead of catching it afterwards — nothing is suppressed,
    because for the loser there is genuinely nothing left to do.

    It only works because the guards reject a re-insert that would *change*
    retained content rather than one that merely repeats it. An existence-based
    guard aborts the statement before conflict resolution is ever reached, which
    was verified against the engine rather than assumed; under such a guard this
    upsert would fail exactly where it needs to succeed.
    """
    return sqlite_insert(model).on_conflict_do_nothing()


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

    Never commits. Everything written here is pending in the caller's
    transaction and disappears if the caller rolls back, so a retention that
    belongs to a larger unit of work cannot outlive that unit's failure.
    """
    identity = state.override_set_uuid

    # Before the savepoint, not inside it. Resolution reads before it retains, so
    # without this the savepoint below would be the outermost one and releasing
    # it would commit these rows out of the caller's control.
    ensure_physical_transaction(session)

    # One savepoint around the whole unit. Version, entries, and scope are one
    # piece of evidence: a version without its entries, or content without the
    # association proving whose it is, is not partial evidence but unusable
    # evidence. A failure part-way therefore unwinds all of it and leaves the
    # caller's transaction usable, rather than leaving an orphan snapshot behind
    # for the next reader to trip over.
    with session.begin_nested():
        session.execute(
            _insert_or_ignore(OverrideSetVersionORM).values(
                override_set_uuid=identity,
                entry_count=len(state.entries),
                recorded_at=now,
            )
        )
        # Flushed before its entries: they carry a foreign key to it, and the
        # unit of work is free to order two pending inserts either way.
        session.flush()
        for entry in state.entries:
            session.execute(
                _insert_or_ignore(OverrideSetEntryORM).values(
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
        # The content may already be retained while *this* scope is not: shared
        # content is the normal case, so a second package reaching the same
        # identity still records its own association before it may replay.
        session.execute(
            _insert_or_ignore(OverrideSetScopeORM).values(
                override_set_uuid=identity,
                package_uuid=state.package_uuid,
                release_version=state.release_version,
                first_recorded_at=now,
            )
        )
        session.flush()

    # Verify whatever is now there, whoever wrote it. This is the read path
    # replay will take, so proving it at the write means a retention defect
    # surfaces while it could still have been fixed — and after a lost race it
    # is what confirms the winner's evidence is the valid one this caller can
    # rely on, rather than assuming so because no error was raised.
    load_override_set_version(
        session,
        identity,
        package_uuid=state.package_uuid,
        release_version=state.release_version,
    )
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
    session: Session,
    override_set_uuid: str,
    *,
    package_uuid: str,
    release_version: str,
) -> EffectiveOverrideSet:
    """Resolve one retained override-set version for audit or replay.

    Reads only the retained tables. Current ``rp_mech_overrides`` rows are never
    consulted — they are the authoring surface, and an implementation that
    re-derived from them would reconstruct today's authority while claiming to
    reconstruct the recorded one.

    *package_uuid* and *release_version* come from the binding being replayed
    rather than from the version row, because the version is content-addressed
    and package-independent: identical override state across packages is one
    row, and the empty set is shared by every package.

    They are **verified, not trusted.** A retained version may only be applied
    under a scope it was actually retained for, proven against
    ``rp_override_set_scopes``. Without that check the caller's binding would be
    self-certifying, and since semantic keys are stable across SRD-derived
    releases by design, an override set retained for one package finds live
    targets in another and replays with the wrong provenance rather than
    failing.

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

    scope = session.execute(
        select(OverrideSetScopeORM).where(
            OverrideSetScopeORM.override_set_uuid == override_set_uuid,
            OverrideSetScopeORM.package_uuid == package_uuid,
            OverrideSetScopeORM.release_version == release_version,
        )
    ).scalar_one_or_none()
    if scope is None:
        raise OverrideSetRetentionError(
            f"retained override-set version {override_set_uuid} was never retained "
            f"for package {package_uuid} release {release_version!r}"
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
        package_uuid=package_uuid,
        release_version=release_version,
        entries=entries,
    )
