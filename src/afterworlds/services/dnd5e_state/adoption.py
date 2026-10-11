"""Deliberate per-subject adoption of an exact target binding — CRD Issue 2b.

A subject (character or creature) moves from its recorded binding to an exact
target binding of the **same Rules Package** only when its player asks, and
only after fresh validation:

* The target is named exactly: either a binding, or the shared change whose
  activation produces it. A newer binding is never substituted. A target that
  is no longer the package's current binding is refused.
* While the subject's story has a pending roll or an in-flight turn, or the
  referenced change is still held, the request is **held**. It is processed
  again after each of those resolves (:func:`process_held`), and is
  revalidated then against the subject's *current* revision. Ordinary changes
  the resolved event made (hit points, resources, conditions) are inputs to
  that validation, not failures.
* The request is refused visibly, and nothing changes, when the target is
  incompatible or cannot be proven compatible, when the target or intent
  drifted, when the referenced change was rejected or withdrawn, or when a
  conflicting write lands during the final commit.
* Compatibility covers the items the subject holds: an item identity, item
  component or applied poison the target no longer states refuses the
  adoption rather than leaving equipment the target removed.
* On success the subject is rebound: its state document is untouched and its
  binding history gains a row. Adopting a character never adopts its
  creatures.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.orm.dnd5e_state import Dnd5eAdoptionRequestORM
from afterworlds.persistence.orm.rules_authority import SharedRuleChangeORM
from afterworlds.services.dnd5e_state import store
from afterworlds.services.dnd5e_state.authority import (
    AuthorityIndex,
    authority_index,
    current_binding,
)
from afterworlds.services.dnd5e_state.errors import (
    BindingRefusedError,
    FailureCode,
    StaleRevisionError,
    StateFailure,
    StateServiceError,
    SubjectNotFoundError,
)
from afterworlds.services.dnd5e_state.holdings import (
    Holder,
    HolderKind,
    item_identity_failure,
    items_held_by,
)
from afterworlds.services.dnd5e_state.shared_changes import (
    ChangeStatus,
    blocking_events,
)
from afterworlds.services.dnd5e_state.validation import (
    validate_character,
    validate_creature,
)

__all__ = [
    "AdoptionError",
    "AdoptionStatus",
    "process",
    "process_held",
    "request_adoption",
    "status_of",
    "withdraw_adoption",
]


class AdoptionStatus(StrEnum):
    HELD = "held"
    APPLIED = "applied"
    REFUSED = "refused"
    WITHDRAWN = "withdrawn"


class AdoptionError(StateServiceError):
    pass


@dataclass(frozen=True)
class AdoptionOutcome:
    request_id: str
    status: AdoptionStatus
    reason: str | None


def _subject(
    session: Session, kind: str, subject_id: UUID
) -> store.StoredCharacter | store.StoredCreature:
    stored = (
        store.get_character(session, subject_id)
        if kind == "character"
        else store.get_creature(session, subject_id) if kind == "creature" else None
    )
    if stored is None:
        raise SubjectNotFoundError(f"no {kind} state for {subject_id}")
    return stored


def _binding(prefix: str, row: Dnd5eAdoptionRequestORM) -> RulesPackageBinding:
    return RulesPackageBinding(
        package_uuid=UUID(getattr(row, f"{prefix}_package_uuid")),
        release_version=getattr(row, f"{prefix}_release_version"),
        mechanical_projection_uuid=UUID(getattr(row, f"{prefix}_projection_uuid")),
        override_set_uuid=UUID(getattr(row, f"{prefix}_override_set_uuid")),
    )


def _columns(prefix: str, b: RulesPackageBinding) -> dict[str, str]:
    return {
        f"{prefix}_package_uuid": str(b.package_uuid),
        f"{prefix}_release_version": b.release_version,
        f"{prefix}_projection_uuid": str(b.mechanical_projection_uuid),
        f"{prefix}_override_set_uuid": str(b.override_set_uuid),
    }


def request_adoption(
    session: Session,
    kind: str,
    subject_id: UUID,
    *,
    now: str,
    target: RulesPackageBinding | None = None,
    change_id: str | None = None,
    request_id: str | None = None,
) -> AdoptionOutcome:
    """Record a deliberate adoption request, then process it once.

    Exactly one of *target* (an exact binding) or *change_id* (the shared change
    whose activation produces the target). *request_id* makes a retry of the
    same request idempotent.
    """
    if (target is None) == (change_id is None):
        raise AdoptionError("name exactly one of an exact target binding or a change")
    if request_id is not None:
        existing = session.get(Dnd5eAdoptionRequestORM, request_id)
        if existing is not None:
            return process(session, request_id, now=now)
    stored = _subject(session, kind, subject_id)
    if change_id is not None:
        change = session.get(SharedRuleChangeORM, change_id)
        if change is None:
            raise AdoptionError(f"no shared change {change_id}")
        target = RulesPackageBinding(
            package_uuid=UUID(change.package_uuid),
            release_version=change.release_version,
            mechanical_projection_uuid=stored.binding.mechanical_projection_uuid,
            override_set_uuid=UUID(change.target_override_set_uuid),
        )
    assert target is not None
    if target.package_uuid != stored.binding.package_uuid:
        raise AdoptionError(
            "adoption stays within the subject's Rules Package; "
            f"{target.package_uuid} is not {stored.binding.package_uuid}"
        )
    if target == stored.binding:
        raise AdoptionError("the subject is already bound to that exact target")
    request_id = request_id or str(uuid4())
    session.add(
        Dnd5eAdoptionRequestORM(
            request_id=request_id,
            subject_kind=kind,
            subject_id=str(subject_id),
            story_id=str(stored.story_id),
            change_id=change_id,
            status=AdoptionStatus.HELD.value,
            requested_at=now,
            **_columns("from", stored.binding),
            **_columns("target", target),
        )
    )
    session.flush()
    return process(session, request_id, now=now)


def _finish(
    row: Dnd5eAdoptionRequestORM, status: AdoptionStatus, reason: str | None, now: str
) -> AdoptionOutcome:
    row.status = status.value
    row.reason = reason
    row.resolved_at = now
    return AdoptionOutcome(row.request_id, status, reason)


def _held_item_failures(
    session: Session, index: AuthorityIndex, kind: str, subject_id: UUID
) -> tuple[StateFailure, ...]:
    """Items the subject holds that the target authority cannot represent."""
    out = []
    for item in items_held_by(session, Holder(HolderKind(kind), subject_id)):
        failure = item_identity_failure(
            index, item.record_key, item.component_key, item.applied_poison_record_key
        )
        if failure is not None:
            out.append(
                StateFailure(
                    FailureCode.INVALID_IDENTITY, f"items[{item.item_id}]", failure
                )
            )
    return tuple(out)


def process(session: Session, request_id: str, *, now: str) -> AdoptionOutcome:
    """Advance one request as far as current state allows. Idempotent.

    Claims SQLite's single write lock with its first statement (as shared-change
    activation does), so no turn lease or activation can commit between the
    event check and the rebind.
    """
    session.execute(
        sa.update(Dnd5eAdoptionRequestORM)
        .where(Dnd5eAdoptionRequestORM.request_id == request_id)
        .values(status=Dnd5eAdoptionRequestORM.status)
        .execution_options(synchronize_session=False)
    )
    row = session.get(Dnd5eAdoptionRequestORM, request_id, populate_existing=True)
    if row is None:
        raise AdoptionError(f"no adoption request {request_id}")
    if row.status != AdoptionStatus.HELD.value:
        return AdoptionOutcome(row.request_id, AdoptionStatus(row.status), row.reason)
    if row.change_id is not None:
        change = session.get(SharedRuleChangeORM, row.change_id, populate_existing=True)
        status = None if change is None else ChangeStatus(change.status)
        if status in (ChangeStatus.REJECTED, ChangeStatus.WITHDRAWN, None):
            label = status.value if status else "removed"
            note = change.resolution_note if change else None
            reason = f"the referenced shared change was {label}"
            return _finish(
                row,
                AdoptionStatus.REFUSED,
                reason + (f": {note}" if note else ""),
                now,
            )
        if status is ChangeStatus.HELD:
            return AdoptionOutcome(row.request_id, AdoptionStatus.HELD, None)
    if blocking_events(session, {row.story_id}):
        return AdoptionOutcome(row.request_id, AdoptionStatus.HELD, None)

    kind, subject_id = row.subject_kind, UUID(row.subject_id)
    stored = _subject(session, kind, subject_id)
    origin, target = _binding("from", row), _binding("target", row)
    if stored.binding != origin:
        return _finish(
            row,
            AdoptionStatus.REFUSED,
            "the subject's binding changed since the request; request again",
            now,
        )
    try:
        current = current_binding(session, target.package_uuid, now=now)
    except BindingRefusedError as exc:
        return _finish(row, AdoptionStatus.REFUSED, f"target unavailable: {exc}", now)
    if current != target:
        return _finish(
            row,
            AdoptionStatus.REFUSED,
            f"the requested target is no longer the package's current binding "
            f"(now {current.override_set_uuid}); no newer target is substituted",
            now,
        )
    try:
        index = authority_index(session, target, now=now)
    except Exception as exc:  # noqa: BLE001 - any unprovable target refuses
        return _finish(
            row, AdoptionStatus.REFUSED, f"compatibility cannot be proven: {exc}", now
        )
    failures = (
        validate_character(index, stored.state)
        if isinstance(stored, store.StoredCharacter)
        else validate_creature(index, stored.state)
    ) + _held_item_failures(session, index, kind, subject_id)
    if failures:
        return _finish(
            row,
            AdoptionStatus.REFUSED,
            "incompatible with the target: " + "; ".join(str(f) for f in failures),
            now,
        )
    try:
        with session.begin_nested():
            store.rebind(
                session,
                kind,
                subject_id,
                stored.story_id,
                expected_revision=stored.revision,
                from_binding=origin,
                to_binding=target,
                request_id=row.request_id,
                now=now,
            )
    except StaleRevisionError as exc:
        return _finish(row, AdoptionStatus.REFUSED, f"conflicting write: {exc}", now)
    return _finish(row, AdoptionStatus.APPLIED, None, now)


def process_held(
    session: Session, story_id: UUID | None = None, *, now: str
) -> list[AdoptionOutcome]:
    """Process every held request (of one story, if given)."""
    query = sa.select(Dnd5eAdoptionRequestORM.request_id).where(
        Dnd5eAdoptionRequestORM.status == AdoptionStatus.HELD.value
    )
    if story_id is not None:
        query = query.where(Dnd5eAdoptionRequestORM.story_id == str(story_id))
    ids = list(
        session.execute(query.order_by(Dnd5eAdoptionRequestORM.requested_at)).scalars()
    )
    return [process(session, request_id, now=now) for request_id in ids]


def withdraw_adoption(
    session: Session, request_id: str, *, now: str
) -> AdoptionOutcome:
    row = session.get(Dnd5eAdoptionRequestORM, request_id)
    if row is None:
        raise AdoptionError(f"no adoption request {request_id}")
    if row.status != AdoptionStatus.HELD.value:
        raise AdoptionError(f"request {request_id} is {row.status}, not held")
    return _finish(row, AdoptionStatus.WITHDRAWN, "withdrawn by the player", now)


def status_of(session: Session, request_id: str) -> AdoptionOutcome:
    row = session.get(Dnd5eAdoptionRequestORM, request_id, populate_existing=True)
    if row is None:
        raise AdoptionError(f"no adoption request {request_id}")
    return AdoptionOutcome(row.request_id, AdoptionStatus(row.status), row.reason)
