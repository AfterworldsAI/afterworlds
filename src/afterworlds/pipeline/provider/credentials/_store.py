"""Sojourner-scoped BYOK credential store — CRD Issue 14a.

Raw API keys NEVER persist in SQLite, logs, telemetry, exports, or any other
durable path.  The OS keychain holds keys; SQLite holds only non-secret metadata
(``ProviderCredentialMetadata``).

``OSKeychainCredentialStore`` uses the ``keyring`` library.  On CI/CD runners
where the Windows Credential Manager is unavailable, swap to
``FallbackEnvCredentialStore`` by detecting ``AFTERWORLDS_CI=true``.

Keychain coordinates:
  service  = ``f"afterworlds_byok.{provider_name}"``
  username = ``str(sojourner_id)``

Per-Sojourner isolation prevents local profiles from colliding on one machine.
"""

from __future__ import annotations

import os
from typing import Protocol
from uuid import UUID

from afterworlds.pipeline.provider._errors import CredentialValidationError


def _keychain_service(provider_name: str) -> str:
    return f"afterworlds_byok.{provider_name}"


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class CredentialStore(Protocol):
    """Protocol for Sojourner-scoped BYOK credential storage."""

    def get(self, sojourner_id: UUID, provider_name: str) -> str | None:
        """Return the stored key for this Sojourner+provider, or None."""
        ...

    def set(self, sojourner_id: UUID, provider_name: str, key: str) -> None:
        """Store the key.  Raises ``CredentialValidationError`` for empty/whitespace."""
        ...

    def delete(self, sojourner_id: UUID, provider_name: str) -> None:
        """Remove the stored key.  No-op if absent."""
        ...

    def has(self, sojourner_id: UUID, provider_name: str) -> bool:
        """Return True iff a key is stored for this Sojourner+provider."""
        ...


# ---------------------------------------------------------------------------
# OS keychain implementation
# ---------------------------------------------------------------------------


class OSKeychainCredentialStore:
    """Credential store backed by the OS keychain via ``keyring``.

    ``set`` validates that the key is non-empty and non-whitespace before
    storing.  No raw key material is logged or emitted at any level.
    """

    def get(self, sojourner_id: UUID, provider_name: str) -> str | None:
        import keyring

        value = keyring.get_password(
            _keychain_service(provider_name), str(sojourner_id)
        )
        return value or None

    def set(self, sojourner_id: UUID, provider_name: str, key: str) -> None:
        if not key or not key.strip():
            raise CredentialValidationError(
                f"Credential for provider {provider_name!r} must be non-empty"
            )
        import keyring

        keyring.set_password(_keychain_service(provider_name), str(sojourner_id), key)

    def delete(self, sojourner_id: UUID, provider_name: str) -> None:
        import contextlib

        import keyring
        import keyring.errors

        with contextlib.suppress(keyring.errors.PasswordDeleteError):
            keyring.delete_password(_keychain_service(provider_name), str(sojourner_id))

    def has(self, sojourner_id: UUID, provider_name: str) -> bool:
        return self.get(sojourner_id, provider_name) is not None


# ---------------------------------------------------------------------------
# Fallback env-var implementation (dev / CI only)
# ---------------------------------------------------------------------------


class FallbackEnvCredentialStore:
    """Read-only credential store backed by environment variables.

    For dev and CI use only — ``set`` and ``delete`` raise ``NotImplementedError``.

    Env var names are derived as:
      ``AFTERWORLDS_BYOK_{PROVIDER_NAME.upper()}_{SID}``
      where ``SID = str(sojourner_id).upper().replace("-", "_")``

    or, if per-Sojourner precision is not needed in CI:
      ``AFTERWORLDS_BYOK_{PROVIDER_NAME.upper()}_KEY``
    """

    def get(self, sojourner_id: UUID, provider_name: str) -> str | None:
        # Per-Sojourner key takes precedence; fall back to generic key.
        sid = str(sojourner_id).upper().replace("-", "_")
        pn = provider_name.upper()
        per_sojourner = os.environ.get(f"AFTERWORLDS_BYOK_{pn}_{sid}")
        if per_sojourner:
            return per_sojourner
        generic = os.environ.get(f"AFTERWORLDS_BYOK_{pn}_KEY")
        return generic or None

    def set(self, sojourner_id: UUID, provider_name: str, key: str) -> None:
        raise NotImplementedError("FallbackEnvCredentialStore is read-only")

    def delete(self, sojourner_id: UUID, provider_name: str) -> None:
        raise NotImplementedError("FallbackEnvCredentialStore is read-only")

    def has(self, sojourner_id: UUID, provider_name: str) -> bool:
        return self.get(sojourner_id, provider_name) is not None


# ---------------------------------------------------------------------------
# Factory helper
# ---------------------------------------------------------------------------


def make_credential_store() -> CredentialStore:
    """Return the appropriate store for the current environment."""
    if os.environ.get("AFTERWORLDS_CI", "").lower() in ("1", "true", "yes"):
        return FallbackEnvCredentialStore()
    return OSKeychainCredentialStore()


__all__ = [
    "CredentialStore",
    "FallbackEnvCredentialStore",
    "OSKeychainCredentialStore",
    "make_credential_store",
]
