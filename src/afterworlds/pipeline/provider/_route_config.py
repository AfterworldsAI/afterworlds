"""ProviderRouteConfig — SQLite-backed non-secret routing configuration.

CRD Issue 14a.  This table answers exactly one question: which model id should
this provider surface use for this Sojourner?  It is NOT a routing-policy table.

No secrets are stored here.  Model identifiers are non-sensitive configuration.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class ProviderRouteConfigORM(Base):
    """SQLAlchemy ORM for provider_route_config table."""

    __tablename__ = "provider_route_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    sojourner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    preferred_model_identifier: Mapped[str | None] = mapped_column(
        String(256), nullable=True
    )
    fallback_model_identifier: Mapped[str | None] = mapped_column(
        String(256), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        UniqueConstraint(
            "sojourner_id",
            "provider_name",
            name="uq_route_config_sojourner_provider",
        ),
    )

    @property
    def sojourner_uuid(self) -> UUID:
        return UUID(self.sojourner_id)


__all__ = ["ProviderRouteConfigORM"]
