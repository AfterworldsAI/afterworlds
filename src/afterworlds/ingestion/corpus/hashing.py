"""Deterministic hashing and content-derived identity — CRD Issue 5c.

Completion Contract A requires byte-for-byte reproducibility (Component K) and
proof identities that are stable across clean checkouts (Component A). Every
identifier and every hash in the corpus pipeline is derived from content, never
from wall-clock time or ``uuid4()``. This module is the single source of truth
for how bytes become hashes and how content becomes UUIDs.

Rules enforced here:

* Canonical serialization is JSON with sorted keys, no insignificant
  whitespace, ``ensure_ascii=False`` (UTF-8), and ``\\n`` newlines. The same
  logical object always serializes to the same bytes.
* Hashes are SHA-256 hex over those canonical bytes.
* Identities are ``uuid5`` over a fixed namespace plus a canonical name, so an
  identity is *new* for new content yet *reproducible* for the same content
  (Owner Decision 1: a new-yet-deterministic package UUID).

No timestamp, absolute path, embedding byte, or environment value may enter a
hashed artifact — callers are responsible for excluding those before hashing.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID, uuid5

# Fixed root namespace for all Issue 5c content-derived identities. This UUID is
# itself a constant (uuid5 of the DNS namespace and a project string), chosen
# once and never regenerated — regenerating it would change every downstream
# identity and break historical proofs.
_ROOT_NAMESPACE = UUID("6f0d9d2e-2c4a-5b7e-9f1a-3c5d7e9b1a2f")

# Per-kind namespaces derived deterministically from the root. Distinct kinds
# (leaf, chunk, projection, package, ...) must never collide even on identical
# canonical names, so each kind gets its own namespace.
_KIND_NAMESPACES: dict[str, UUID] = {}


def _namespace_for(kind: str) -> UUID:
    ns = _KIND_NAMESPACES.get(kind)
    if ns is None:
        ns = uuid5(_ROOT_NAMESPACE, kind)
        _KIND_NAMESPACES[kind] = ns
    return ns


def canonical_bytes(obj: Any) -> bytes:
    """Serialize *obj* to canonical UTF-8 JSON bytes.

    Sorted keys, compact separators, ``\\n`` newlines, non-ASCII preserved.
    The result is stable across runs and platforms for the same logical value.
    """
    text = json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return text.encode("utf-8")


def canonical_json(obj: Any) -> str:
    """Return the canonical JSON *string* (for committed artifact files).

    Same discipline as :func:`canonical_bytes` but decoded, so a file written
    with ``encoding="utf-8", newline="\\n"`` round-trips to identical bytes.
    """
    return canonical_bytes(obj).decode("utf-8")


def sha256_hex(data: bytes) -> str:
    """SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def hash_obj(obj: Any) -> str:
    """SHA-256 hex digest of *obj*'s canonical serialization."""
    return sha256_hex(canonical_bytes(obj))


def content_id(kind: str, *parts: Any) -> str:
    """Return a deterministic ``uuid5`` string for *kind* over *parts*.

    ``parts`` are joined via their canonical serialization, so the identity is a
    pure function of the supplied content. The same content always yields the
    same UUID; different content (or a different *kind*) yields a different one.
    """
    name = canonical_json(list(parts))
    return str(uuid5(_namespace_for(kind), name))
