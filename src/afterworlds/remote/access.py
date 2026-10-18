"""Account-to-Story authorization -- prerequisite #205 §2/§5 (ADR-021 D8).

One policy, consulted by the API Story guard, the Retrieval Memory guard and
delayed work. A local deployment authorizes every Story to its single local
owner (unchanged CRD Issue 19 behavior); a remote one requires an active
ownership row for an active account and no active deletion suppression.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.persistence.orm.ownership import AccountResourceORM
from afterworlds.remote.control_store import iso
from afterworlds.remote.identity import Actor, ActorKind, IdentityService
from afterworlds.remote.storage import is_suppressed

STORY = "story"


class StoryAccessDenied(Exception):
    """The Story is not accessible to this caller/job (no disclosure why)."""


@dataclass(frozen=True)
class DelayedWorkScope:
    """Trusted scope carried by a delayed job and rechecked when it runs."""

    account_id: UUID
    story_id: UUID
    operation: str


def record_story_owner(
    session: Session, account_id: UUID, story_id: UUID, *, now: datetime
) -> None:
    """Add the ownership row in the caller's transaction (commits with the Story)."""
    session.add(
        AccountResourceORM(
            mapping_id=str(uuid4()),
            account_id=str(account_id),
            resource_type=STORY,
            resource_id=str(story_id),
            ownership_revision=1,
            created_at=iso(now),
            source_operation_ref=str(uuid4()),
        )
    )


def story_owner(session: Session, story_id: UUID) -> str | None:
    return session.scalar(
        sa.select(AccountResourceORM.account_id).where(
            AccountResourceORM.resource_type == STORY,
            AccountResourceORM.resource_id == str(story_id),
            AccountResourceORM.retired_at.is_(None),
        )
    )


def owned_story_ids(session: Session, account_id: UUID) -> list[str]:
    """Every Story the account actively owns (independent of Story rows)."""
    return list(
        session.scalars(
            sa.select(AccountResourceORM.resource_id).where(
                AccountResourceORM.account_id == str(account_id),
                AccountResourceORM.resource_type == STORY,
                AccountResourceORM.retired_at.is_(None),
            )
        )
    )


class AccessPolicy:
    """Remote ownership policy; ``identity is None`` means a local deployment."""

    def __init__(
        self,
        identity: IdentityService | None = None,
        control: sessionmaker[Session] | None = None,
    ) -> None:
        self._identity = identity
        self._control = control

    @property
    def remote(self) -> bool:
        return self._identity is not None

    def actor_may_access(self, session: Session, actor: Actor, story_id: UUID) -> bool:
        if actor.kind is ActorKind.LOCAL:
            return not self.remote
        if actor.kind is not ActorKind.SOJOURNER:
            return False
        owner = story_owner(session, story_id)
        return owner == str(actor.account_id) and self._servable(owner, story_id)

    def story_servable(self, session: Session, story_id: UUID) -> bool:
        """For seams without an actor (Retrieval Memory): owned by an active,
        unsuppressed account. Always true locally."""
        if not self.remote:
            return True
        owner = story_owner(session, story_id)
        return owner is not None and self._servable(owner, story_id)

    def check_delayed_work(self, session: Session, scope: DelayedWorkScope) -> None:
        """Recheck a delayed job's trusted scope when it executes."""
        if not self.remote:
            return
        owner = story_owner(session, scope.story_id)
        if owner != str(scope.account_id) or not self._servable(owner, scope.story_id):
            raise StoryAccessDenied(scope.operation)

    def _servable(self, owner: str, story_id: UUID) -> bool:
        assert self._identity is not None and self._control is not None
        if not self._identity.active_account_ids({owner}):
            return False
        return not is_suppressed(
            self._control, story_id=str(story_id), account_id=owner
        )
