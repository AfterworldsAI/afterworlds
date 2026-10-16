"""Disposable in-memory ``keyring`` backend — tests and E2E only (CRD Issue 20).

Installed with ``keyring.set_keyring(MemoryKeyring())`` so the production
``OSKeychainCredentialStore`` code path runs unchanged while nothing reaches
the real platform credential manager. Never used by ``create_app``.

``fail_with`` makes every operation raise ``keyring.errors.KeyringError``
carrying that text, so tests can prove backend failure text (e.g. a synthetic
secret echoed by a keychain) never reaches responses or logs.
"""

from __future__ import annotations

from typing import Any

import keyring
import keyring.errors
from keyring.backend import KeyringBackend


class MemoryKeyring(KeyringBackend):
    priority: Any = 1

    def __init__(self) -> None:
        super().__init__()
        self.secrets: dict[tuple[str, str], str] = {}
        self.fail_with: str | None = None

    def _maybe_fail(self) -> None:
        if self.fail_with is not None:
            raise keyring.errors.KeyringError(self.fail_with)

    def get_password(self, service: str, username: str) -> str | None:
        self._maybe_fail()
        return self.secrets.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._maybe_fail()
        self.secrets[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self._maybe_fail()
        if self.secrets.pop((service, username), None) is None:
            raise keyring.errors.PasswordDeleteError("not found")


def install() -> MemoryKeyring:
    """Install a fresh backend and prove it is the active one."""
    backend = MemoryKeyring()
    keyring.set_keyring(backend)
    assert keyring.get_keyring() is backend, "in-memory keyring not active"
    return backend
