"""Sojourner identity — DoR-A (CRD Issue 19).

A single local, server-owned identity. Not a user/account table and not the
start of one: no credentials, no profile, no multi-user semantics.
"""

from uuid import UUID

from pydantic import BaseModel


class SojournerIdentity(BaseModel):
    """The single local Sojourner identity row."""

    sojourner_id: UUID
