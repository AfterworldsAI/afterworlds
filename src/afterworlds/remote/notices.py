"""Account notice transport (ADR-021 D2).

The identity service hands enrollment and recovery codes to a transport; it
never returns them in an HTTP response. The one implementation writes each
notice to a restricted operator outbox directory. A real email processor is an
open launch gate (Known Unknowns: remote launch gates).
"""

from __future__ import annotations

import hashlib
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


def _recipient_tag(contact_address: str) -> str:
    """Names a notice's recipient in its in-progress file name, so a torn
    write can still be attributed (CRD Issue 22 review round 2, F6)."""
    return hashlib.sha256(contact_address.encode("utf-8")).hexdigest()[:16]


class OutboxDirectoryTransport:
    """Writes one JSON file per notice; the directory is operator-restricted.

    A notice is written in full under ``<name>.<recipient tag>.partial`` and
    published as ``<name>.json`` by one atomic rename, so a final notice is
    always complete and an interrupted one is still attributable."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        directory.mkdir(parents=True, exist_ok=True)

    def send(self, *, contact_address: str, kind: str, code: str) -> None:
        name = f"{kind}-{uuid4()}"
        partial = self._directory / f"{name}.{_recipient_tag(contact_address)}.partial"
        # Owner-only: the code proves control of the address.
        fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"to": contact_address, "kind": kind, "code": code}, handle)
        os.replace(partial, self._directory / f"{name}.json")

    def purge(self, contact_address: str) -> int:
        removed = 0
        tag = _recipient_tag(contact_address)
        for path in sorted(self._directory.glob(f"*.{tag}.partial")):
            path.unlink(missing_ok=True)  # an interrupted write to this address
            removed += 1
        for path in sorted(self._directory.glob("*.json")):
            try:
                notice = json.loads(path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                continue  # the operator relay delivered and removed it
            except ValueError:
                # A final notice is always complete, so this one cannot be
                # attributed: erasure must not report it gone.
                raise OSError(f"unattributable notice {path.name}") from None
            if isinstance(notice, dict) and notice.get("to") == contact_address:
                path.unlink(missing_ok=True)
                removed += 1
        return removed
