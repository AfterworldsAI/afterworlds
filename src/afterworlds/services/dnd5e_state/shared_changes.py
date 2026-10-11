"""Shared rule changes, held until affected events resolve — CRD Issue 2b.

The only production writer of ``rp_mech_overrides``. A requested change never
touches the current override rows while it is held; it waits in
``rp_mech_shared_changes`` with the exact override-set identity its
activation must produce.

**Affected events.** A change to (package, release) affects every story with
a character or creature bound to that package and release, or a party whose
items that package governs. Its events are
that story's pending rolls (``pending_roll_requests.status = 'pending'``) and
in-flight adjudicating turns (:mod:`.leases`). Existing events finish under
the rules they started with; the change activates only when none remain.

**Races.** :func:`activate` claims SQLite's single write lock with its first
statement, then reads events and current override state and inserts the rows,
all in one transaction. A turn commits its lease before reading any binding, so
either activation sees the lease and holds, or the turn sees the new binding
and refuses. Nothing is cancelled or expired; a change that keeps finding new
events stays visibly ``held`` with its blocking count.

**Exact target.** The target identity is computed at request time over the
then-current rows plus the requested ones. Activation must reproduce exactly
that identity. If the current rows moved in between, the change is refused,
and no newer target is substituted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.persistence.orm.dnd5e_state import (
    Dnd5eCharacterStateORM,
    Dnd5eCreatureORM,
    RpgPartyORM,
    RpgTurnLeaseORM,
)
from afterworlds.persistence.orm.rpg import PendingRollRequestORM
from afterworlds.persistence.orm.rules_authority import (
    MechanicalOverrideORM,
    SharedRuleChangeORM,
)
from afterworlds.services.dnd5e_state.errors import StateServiceError
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import (
    OverrideStateError,
    collect_current_override_state,
)
from afterworlds.services.rules_authority.service import RulesAuthorityService
from afterworlds.services.rules_authority.targets import MechanicalTarget

__all__ = [
    "ActivationResult",
    "ChangeStatus",
    "OverrideSpec",
    "SharedChangeError",
    "activate",
    "affected_stories",
    "blocking_events",
    "reject",
    "request_change",
    "withdraw",
]


class ChangeStatus(StrEnum):
    HELD = "held"
    ACTIVE = "active"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class SharedChangeError(StateServiceError):
    pass


@dataclass(frozen=True)
class OverrideSpec:
    """One override row a shared change will insert on activation."""

    override_id: str
    target: MechanicalTarget
    operation: OverrideOperationEnum
    payload: dict[str, Any]
    precedence: int = 100
    origin: OverrideOriginEnum = OverrideOriginEnum.HOUSE_RULE
    is_enabled: bool = True
    note: str | None = None

    def row(self, package_uuid: str, release_version: str) -> dict[str, Any]:
        return {
            "override_id": self.override_id,
            "package_uuid": package_uuid,
            "release_version": release_version,
            "target_kind": self.target.kind.value,
            "target_record_key": self.target.record_key,
            "target_component_key": self.target.component_key,
            "target_fact_key": self.target.fact_key,
            "target_option_key": self.target.option_key,
            "override_origin": self.origin.value,
            "override_operation": self.operation.value,
            "payload": self.payload,
            "precedence": self.precedence,
            "is_enabled": self.is_enabled,
            "note": self.note,
        }


@dataclass(frozen=True)
class ActivationResult:
    status: ChangeStatus
    #: Pending rolls plus in-flight leases still blocking a held change.
    blocking: int = 0
    detail: str = ""


def _current_identity(session: Session, package_uuid: str, release: str) -> str:
    return collect_current_override_state(
        session, package_uuid, release
    ).override_set_uuid


def affected_stories(session: Session, package_uuid: str, release: str) -> set[str]:
    """Stories that use (package, release) as authority.

    A character or creature bound to it, or a party whose held items are
    governed by the package. A party records the package, not a release (its
    items are validated under whatever binding is current), so it counts for
    every release of its package: conservatively held, never under-held.
    """
    stories: set[str] = set()
    for table in (Dnd5eCharacterStateORM, Dnd5eCreatureORM):
        stories |= set(
            session.execute(
                sa.select(table.story_id)
                .where(table.package_uuid == package_uuid)
                .where(table.release_version == release)
                .distinct()
            ).scalars()
        )
    stories |= set(
        session.execute(
            sa.select(RpgPartyORM.story_id)
            .where(RpgPartyORM.package_uuid == package_uuid)
            .distinct()
        ).scalars()
    )
    return stories


def blocking_events(session: Session, stories: set[str]) -> int:
    """Pending rolls and in-flight turn leases in *stories*."""
    if not stories:
        return 0
    pending = session.execute(
        sa.select(sa.func.count())
        .select_from(PendingRollRequestORM)
        .where(PendingRollRequestORM.story_id.in_(stories))
        .where(PendingRollRequestORM.status == "pending")
    ).scalar_one()
    leases = session.execute(
        sa.select(sa.func.count())
        .select_from(RpgTurnLeaseORM)
        .where(RpgTurnLeaseORM.story_id.in_(stories))
    ).scalar_one()
    return int(pending) + int(leases)


def request_change(
    session: Session,
    package_uuid: UUID,
    release_version: str,
    overrides: tuple[OverrideSpec, ...],
    *,
    requested_by: str,
    now: str,
) -> str:
    """Hold a shared change and fix the exact identity it must activate to.

    The target is computed by trial: the rows are inserted inside a SAVEPOINT,
    the package resolved through the one code-owned resolver and its whole
    effective authority applied (so an invalid, cross-release or inapplicable
    override is refused here, with its own outcome, rather than at
    activation), and the savepoint rolled back. The current rows are
    unchanged when this returns.
    """
    if not overrides:
        raise SharedChangeError("a shared change states at least one override")
    pkg = str(package_uuid)
    base = _current_identity(session, pkg, release_version)
    savepoint = session.begin_nested()
    try:
        for spec in overrides:
            session.add(
                MechanicalOverrideORM(
                    **spec.row(pkg, release_version),
                    created_at=now,
                    created_by=requested_by,
                )
            )
        session.flush()
        try:
            target = _current_identity(session, pkg, release_version)
        except OverrideStateError as exc:
            raise SharedChangeError(
                f"{AuthorityOutcome.INVALID_OVERRIDE.value}: {exc}"
            ) from exc
        authority = RulesAuthorityService(session, now=now)
        trial = authority.resolve(
            package_uuid=package_uuid, expected_release=release_version
        )
        if trial.outcome is not AuthorityOutcome.RESOLVED:
            raise SharedChangeError(f"{trial.outcome.value}: {trial.detail}")
        # Resolution checks identity; applying the set to the projection is
        # what proves every override can take effect. Refuse here, not after
        # the change has been held and activated.
        applied = authority.rule_slice(
            RuleSliceRequest(package_id=package_uuid, whole_package=True)
        )
        if applied.outcome is not AuthorityOutcome.RESOLVED:
            raise SharedChangeError(f"{applied.outcome.value}: {applied.detail}")
    finally:
        savepoint.rollback()
    change_id = str(uuid4())
    session.add(
        SharedRuleChangeORM(
            change_id=change_id,
            package_uuid=pkg,
            release_version=release_version,
            entries=[spec.row(pkg, release_version) for spec in overrides],
            base_override_set_uuid=base,
            target_override_set_uuid=target,
            status=ChangeStatus.HELD.value,
            requested_by=requested_by,
            requested_at=now,
        )
    )
    session.flush()
    return change_id


def _claim(session: Session, change_id: str) -> SharedRuleChangeORM:
    """Claim the write lock with the first statement, then read the change."""
    session.execute(
        sa.update(SharedRuleChangeORM)
        .where(SharedRuleChangeORM.change_id == change_id)
        .values(status=SharedRuleChangeORM.status)
        .execution_options(synchronize_session=False)
    )
    row = session.get(SharedRuleChangeORM, change_id, populate_existing=True)
    if row is None:
        raise SharedChangeError(f"no shared change {change_id}")
    return row


def _finish(
    session: Session,
    row: SharedRuleChangeORM,
    status: ChangeStatus,
    note: str,
    now: str,
) -> ActivationResult:
    row.status = status.value
    row.resolved_at = now
    row.resolution_note = note
    session.flush()
    return ActivationResult(status, detail=note)


def activate(session: Session, change_id: str, *, now: str) -> ActivationResult:
    """Activate a held change if no affected event remains; else keep it held.

    Runs inside the caller's transaction, which must commit for the result to
    stand. Idempotent: a change that is no longer held reports its status.
    """
    row = _claim(session, change_id)
    if row.status != ChangeStatus.HELD.value:
        return ActivationResult(
            ChangeStatus(row.status), detail=row.resolution_note or ""
        )
    pkg, release = row.package_uuid, row.release_version
    blocking = blocking_events(session, affected_stories(session, pkg, release))
    if blocking:
        return ActivationResult(ChangeStatus.HELD, blocking=blocking)
    current = _current_identity(session, pkg, release)
    if current != row.base_override_set_uuid:
        return _finish(
            session,
            row,
            ChangeStatus.REJECTED,
            f"the package's overrides moved from {row.base_override_set_uuid} to "
            f"{current} after this change was requested; its exact target "
            "cannot be produced. Request the change again.",
            now,
        )
    for entry in row.entries:
        session.add(
            MechanicalOverrideORM(**entry, created_at=now, created_by=row.requested_by)
        )
    session.flush()
    produced = _current_identity(session, pkg, release)
    if produced != row.target_override_set_uuid:
        raise SharedChangeError(
            f"activation produced {produced}, not the requested exact target "
            f"{row.target_override_set_uuid}"
        )
    return _finish(session, row, ChangeStatus.ACTIVE, "activated", now)


def reject(
    session: Session, change_id: str, reason: str, *, now: str
) -> ActivationResult:
    return _resolve_without_activation(
        session, change_id, ChangeStatus.REJECTED, reason, now
    )


def withdraw(
    session: Session, change_id: str, reason: str, *, now: str
) -> ActivationResult:
    return _resolve_without_activation(
        session, change_id, ChangeStatus.WITHDRAWN, reason, now
    )


def _resolve_without_activation(
    session: Session, change_id: str, status: ChangeStatus, reason: str, now: str
) -> ActivationResult:
    row = _claim(session, change_id)
    if row.status != ChangeStatus.HELD.value:
        raise SharedChangeError(f"change {change_id} is {row.status}, not held")
    return _finish(session, row, status, reason, now)
