"""CRUD for the single local Sojourner identity — DoR-A (CRD Issue 19)."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from afterworlds.models.identity import SojournerIdentity
from afterworlds.persistence.orm.identity import SojournerIdentityORM

_SINGLETON_ID = 1


def get_or_create_sojourner_identity(session: Session) -> SojournerIdentity:
    """Return the local Sojourner identity, creating it on first run.

    Idempotent: subsequent calls always return the same ``sojourner_id``.
    Single uvicorn worker (Binding Decision 8) means no startup race to
    guard against here.
    """
    row = session.get(SojournerIdentityORM, _SINGLETON_ID)
    if row is None:
        row = SojournerIdentityORM(id=_SINGLETON_ID, sojourner_id=str(uuid4()))
        session.add(row)
        session.flush()
    return SojournerIdentity(sojourner_id=UUID(row.sojourner_id))
