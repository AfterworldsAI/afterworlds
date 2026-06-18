"""Provider credential metadata SQLAlchemy ORM — CRD Issue 14a.

Non-secret only: sojourner_id, provider_name, validation status, timestamps.
NO key/hash/secret/token column.  Keychain coordinates are derived, never stored.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from afterworlds.persistence.orm.base import Base


class ValidationStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    UNTESTED = "untested"
    ERROR = "error"


class ProviderCredentialMetadata(Base):
    """Non-secret credential metadata row — one per Sojourner + provider.

    The actual key lives in the OS keychain; this table stores only
    observability metadata.  No key/hash/secret/token column exists here or
    should ever be added.
    """

    __tablename__ = "provider_credential_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    sojourner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    validation_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ValidationStatus.UNTESTED
    )
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "sojourner_id", "provider_name", name="uq_credential_sojourner_provider"
        ),
    )

    @property
    def sojourner_uuid(self) -> UUID:
        return UUID(self.sojourner_id)


__all__ = [
    "ProviderCredentialMetadata",
    "ValidationStatus",
]
