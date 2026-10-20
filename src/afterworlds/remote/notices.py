"""Account notice transport (ADR-021 D2).

The identity service hands enrollment and recovery codes to a transport; it
never returns them in an HTTP response. The one implementation writes each
notice to a restricted operator outbox directory. A real email processor is an
open launch gate (Known Unknowns: remote launch gates).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol
from uuid import uuid4


class NoticeTransport(Protocol):
    def send(self, *, contact_address: str, kind: str, code: str) -> None: ...

    def purge(self, contact_address: str) -> int:
        """Remove every undelivered notice to *contact_address* (CRD Issue 22
        account erasure); returns how many. Raises ``OSError`` if any remains."""
        ...


class OutboxDirectoryTransport:
    """Writes one JSON file per notice; the directory is operator-restricted."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        directory.mkdir(parents=True, exist_ok=True)

    def send(self, *, contact_address: str, kind: str, code: str) -> None:
        path = self._directory / f"{kind}-{uuid4()}.json"
        # Owner-only: the code proves control of the address.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"to": contact_address, "kind": kind, "code": code}, handle)

    def purge(self, contact_address: str) -> int:
        removed = 0
        for path in sorted(self._directory.glob("*.json")):
            try:
                notice = json.loads(path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                continue  # the operator relay delivered and removed it
            except ValueError:
                continue  # not a notice this transport wrote
            if isinstance(notice, dict) and notice.get("to") == contact_address:
                path.unlink(missing_ok=True)
                removed += 1
        return removed
