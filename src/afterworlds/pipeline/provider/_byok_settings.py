"""BYOK credential settings — CRD Issue 20 (credential/provider layer).

The owning-service interface behind the Sojourner's BYOK settings surface:
read credential/configuration state, add/replace and remove a key,
enable/disable a provider, set the exact OpenRouter model the resolver uses,
and explicitly validate a stored key.

Ownership stays here, in the credential layer. Raw keys go only to the
``CredentialStore``; SQLite gets non-secret metadata. No operation except
``validate`` contacts a provider, and none returns key material.

Ordering, so a partial failure never reports better state than exists:

- Replace resets the metadata to ``untested`` under a fresh
  ``credential_revision`` *before* writing the key. If the key write then
  fails, the stored state is "untested", never the previous key's verdict.
- Remove deletes the metadata row *before* the key. Without a row a key is
  ineligible for the resolver, so a failed key deletion never leaves a
  runnable credential behind; retrying the removal completes it.
- Validate captures (row id, revision, key) together, checks outside the
  lock, then records the verdict only if that row still carries that
  revision. A late result can therefore neither validate a replacement nor
  revive a removed key (a re-added key is a new row with a new revision).
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from afterworlds.pipeline.provider._readiness import (
    _BYOK_PROVIDER_NAMES,
    _fetch_openrouter_preferred_model,
)
from afterworlds.pipeline.provider._route_config import ProviderRouteConfigORM
from afterworlds.pipeline.provider.credentials._metadata import (
    ProviderCredentialMetadata,
    ValidationStatus,
)
from afterworlds.pipeline.provider.credentials._store import CredentialStore
from afterworlds.pipeline.provider.credentials._validator import CredentialValidator

logger = logging.getLogger("afterworlds.provider.credentials")

#: (provider_name, raw_key) -> (status, sanitized detail). The detail is
#: discarded: no provider text reaches API responses.
CredentialChecker = Callable[[str, str], tuple[ValidationStatus, str | None]]

_MAX_KEY_LENGTH = 512
_MAX_MODEL_LENGTH = 256  # provider_route_config.preferred_model_identifier


class CredentialSettingsErrorKind(StrEnum):
    INVALID_INPUT = "invalid_input"
    STORE_READ_ONLY = "store_read_only"
    STORE_UNAVAILABLE = "store_unavailable"
    METADATA_UNAVAILABLE = "metadata_unavailable"
    NOT_CONFIGURED = "not_configured"
    VALIDATION_SUPERSEDED = "validation_superseded"
    VALIDATION_UNAVAILABLE = "validation_unavailable"


class CredentialSettingsError(Exception):
    """Typed settings failure. ``message`` is fixed text — never key material,
    keyring/provider exception text, or the submitted value."""

    def __init__(self, kind: CredentialSettingsErrorKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


@dataclass(frozen=True)
class ProviderCredentialState:
    """Non-secret per-provider state. ``credential_present`` is None when the
    store could not be read — unknown, never reported as absent."""

    provider_name: str
    credential_present: bool | None
    enabled: bool | None
    validation_status: ValidationStatus | None
    last_validated_at: datetime | None


@dataclass(frozen=True)
class ByokSettingsState:
    store_writable: bool
    providers: tuple[ProviderCredentialState, ...]
    openrouter_model: str | None


class ByokSettingsService:
    """Owning-service interface for BYOK credential settings (CRD Issue 20)."""

    def __init__(
        self,
        credential_store: CredentialStore,
        session_factory: Callable[[], Session],
        checker: CredentialChecker | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = credential_store
        self._session_factory = session_factory
        self._check = checker or CredentialValidator().check
        self._clock = clock or (lambda: datetime.now(UTC))
        # ponytail: one process-wide lock (single uvicorn worker, Binding
        # Decision 8); the revision compare-and-set still guards any other
        # writer process. Never held across the provider call.
        self._lock = threading.Lock()

    @property
    def store_writable(self) -> bool:
        return not getattr(self._store, "read_only", False)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(self, sojourner_id: UUID) -> ByokSettingsState:
        with self._db() as session:
            rows = {
                row.provider_name: row
                for row in session.scalars(
                    select(ProviderCredentialMetadata).where(
                        ProviderCredentialMetadata.sojourner_id == str(sojourner_id)
                    )
                )
            }
        with self._db_errors():
            # The resolver's own lookup, so the shown model is the one used.
            model = _fetch_openrouter_preferred_model(
                self._session_factory, sojourner_id
            )
        providers = []
        for name in _BYOK_PROVIDER_NAMES:
            row = rows.get(name)
            providers.append(
                ProviderCredentialState(
                    provider_name=name,
                    credential_present=self._probe_presence(sojourner_id, name),
                    enabled=row.is_active if row else None,
                    validation_status=(
                        ValidationStatus(row.validation_status) if row else None
                    ),
                    last_validated_at=row.last_validated_at if row else None,
                )
            )
        return ByokSettingsState(
            store_writable=self.store_writable,
            providers=tuple(providers),
            openrouter_model=model,
        )

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def set_credential(self, sojourner_id: UUID, provider_name: str, key: str) -> None:
        """Add or replace a key. The credential starts ``untested``; a
        replacement never inherits the previous key's validation."""
        _require_provider(provider_name)
        if (
            not key
            or len(key) > _MAX_KEY_LENGTH
            or any(ch.isspace() or not ch.isprintable() for ch in key)
        ):
            raise CredentialSettingsError(
                CredentialSettingsErrorKind.INVALID_INPUT,
                "The API key must be a single line of printable characters "
                f"without spaces, at most {_MAX_KEY_LENGTH} long.",
            )
        self._require_writable()
        with self._lock:
            with self._db() as session:
                now = self._clock()
                row = _metadata_row(session, sojourner_id, provider_name)
                if row is None:
                    row = ProviderCredentialMetadata(
                        sojourner_id=str(sojourner_id),
                        provider_name=provider_name,
                        is_active=True,
                        created_at=now,
                    )
                    session.add(row)
                row.validation_status = ValidationStatus.UNTESTED.value
                row.last_validated_at = None
                row.credential_revision = str(uuid4())
                row.updated_at = now
                session.commit()
            with self._store_errors():
                self._store.set(sojourner_id, provider_name, key)

    def remove_credential(self, sojourner_id: UUID, provider_name: str) -> None:
        _require_provider(provider_name)
        self._require_writable()
        with self._lock:
            with self._db() as session:
                session.execute(
                    delete(ProviderCredentialMetadata).where(
                        ProviderCredentialMetadata.sojourner_id == str(sojourner_id),
                        ProviderCredentialMetadata.provider_name == provider_name,
                    )
                )
                session.commit()
            with self._store_errors():
                self._store.delete(sojourner_id, provider_name)

    def set_enabled(
        self, sojourner_id: UUID, provider_name: str, enabled: bool
    ) -> None:
        """Enable/disable a configured provider. Does not touch the key or its
        validation verdict and makes no provider call."""
        _require_provider(provider_name)
        with self._lock, self._db() as session:
            row = _metadata_row(session, sojourner_id, provider_name)
            if row is None:
                raise _not_configured()
            row.is_active = enabled
            row.updated_at = self._clock()
            session.commit()

    def set_openrouter_model(self, sojourner_id: UUID, model: str | None) -> None:
        """Set (or clear, with None) the exact OpenRouter model the BYOK
        resolver binds. Dynamic aliases are rejected exactly as
        ``OpenRouterAdapter`` would reject them."""
        from afterworlds.pipeline.provider.adapters._openrouter import (
            _is_dynamic_alias,
        )

        if model is not None:
            model = model.strip()
            if not model or len(model) > _MAX_MODEL_LENGTH or _is_dynamic_alias(model):
                raise CredentialSettingsError(
                    CredentialSettingsErrorKind.INVALID_INPUT,
                    "Enter an exact OpenRouter model identifier (not a dynamic "
                    f"alias), at most {_MAX_MODEL_LENGTH} characters.",
                )
        with self._lock, self._db() as session:
            row = session.scalars(
                select(ProviderRouteConfigORM).where(
                    ProviderRouteConfigORM.sojourner_id == str(sojourner_id),
                    ProviderRouteConfigORM.provider_name == "openrouter",
                )
            ).one_or_none()
            if row is None:
                if model is None:
                    return
                row = ProviderRouteConfigORM(
                    sojourner_id=str(sojourner_id), provider_name="openrouter"
                )
                session.add(row)
            row.preferred_model_identifier = model
            row.is_active = True
            session.commit()

    # ------------------------------------------------------------------
    # Explicit validation — the only provider-contact operation
    # ------------------------------------------------------------------

    def validate(self, sojourner_id: UUID, provider_name: str) -> ValidationStatus:
        _require_provider(provider_name)
        with self._lock:
            with self._db() as session:
                row = _metadata_row(session, sojourner_id, provider_name)
                if row is None:
                    raise _not_configured()
                row_id, revision = row.id, row.credential_revision
            with self._store_errors():
                key = self._store.get(sojourner_id, provider_name)
            if not key:
                raise _not_configured()

        try:
            status, _detail = self._check(provider_name, key)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "credential validation check failed",
                extra={"provider": provider_name, "error_class": type(exc).__name__},
            )
            raise CredentialSettingsError(
                CredentialSettingsErrorKind.VALIDATION_UNAVAILABLE,
                "Validation could not be completed; nothing was recorded.",
            ) from None
        finally:
            del key

        with self._lock, self._db() as session:
            now = self._clock()
            result = session.execute(
                update(ProviderCredentialMetadata)
                .where(
                    ProviderCredentialMetadata.id == row_id,
                    ProviderCredentialMetadata.credential_revision == revision,
                )
                .values(
                    validation_status=status.value,
                    last_validated_at=now,
                    updated_at=now,
                )
            )
            session.commit()
        if result.rowcount == 0:  # type: ignore[attr-defined]
            raise CredentialSettingsError(
                CredentialSettingsErrorKind.VALIDATION_SUPERSEDED,
                "The credential changed while it was being validated; the "
                "result was discarded. Validate the current key again.",
            )
        return status

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _require_writable(self) -> None:
        if not self.store_writable:
            raise CredentialSettingsError(
                CredentialSettingsErrorKind.STORE_READ_ONLY,
                "This installation's credential store is read-only; keys "
                "cannot be added or removed here.",
            )

    def _probe_presence(self, sojourner_id: UUID, provider_name: str) -> bool | None:
        try:
            return self._store.has(sojourner_id, provider_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "credential store read failed",
                extra={"provider": provider_name, "error_class": type(exc).__name__},
            )
            return None

    @contextmanager
    def _db(self) -> Iterator[Session]:
        with self._db_errors(), self._session_factory() as session:
            yield session

    @staticmethod
    @contextmanager
    def _db_errors() -> Iterator[None]:
        try:
            yield
        except SQLAlchemyError as exc:
            logger.warning(
                "credential settings database failure",
                extra={"error_class": type(exc).__name__},
            )
            raise CredentialSettingsError(
                CredentialSettingsErrorKind.METADATA_UNAVAILABLE,
                "Credential settings could not be read or saved; try again.",
            ) from None

    @contextmanager
    def _store_errors(self) -> Iterator[None]:
        try:
            yield
        except NotImplementedError:
            raise CredentialSettingsError(
                CredentialSettingsErrorKind.STORE_READ_ONLY,
                "This installation's credential store is read-only; keys "
                "cannot be added or removed here.",
            ) from None
        except Exception as exc:  # noqa: BLE001
            # Error class only: keyring payloads may echo what they were given.
            logger.warning(
                "credential store operation failed",
                extra={"error_class": type(exc).__name__},
            )
            raise CredentialSettingsError(
                CredentialSettingsErrorKind.STORE_UNAVAILABLE,
                "The platform credential store is unavailable; the change was "
                "not completed.",
            ) from None


def _require_provider(provider_name: str) -> None:
    if provider_name not in _BYOK_PROVIDER_NAMES:
        raise CredentialSettingsError(
            CredentialSettingsErrorKind.INVALID_INPUT, "Unsupported BYOK provider."
        )


def _not_configured() -> CredentialSettingsError:
    return CredentialSettingsError(
        CredentialSettingsErrorKind.NOT_CONFIGURED,
        "No key is configured for this provider.",
    )


def _metadata_row(
    session: Session, sojourner_id: UUID, provider_name: str
) -> ProviderCredentialMetadata | None:
    return session.scalars(
        select(ProviderCredentialMetadata).where(
            ProviderCredentialMetadata.sojourner_id == str(sojourner_id),
            ProviderCredentialMetadata.provider_name == provider_name,
        )
    ).one_or_none()


__all__ = [
    "ByokSettingsService",
    "ByokSettingsState",
    "CredentialChecker",
    "CredentialSettingsError",
    "CredentialSettingsErrorKind",
    "ProviderCredentialState",
]
