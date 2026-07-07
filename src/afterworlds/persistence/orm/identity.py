"""ORM model for the single local Sojourner identity row — DoR-A (CRD Issue 19)."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class SojournerIdentityORM(Base):
    """Singleton row holding the local Sojourner's identity.

    ``id`` is a constant primary key (always 1) so a second identity row is
    structurally impossible — there is exactly one local Sojourner in v1.
    """

    __tablename__ = "sojourner_identity"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    sojourner_id: Mapped[str] = mapped_column(sa.String(36), nullable=False)
