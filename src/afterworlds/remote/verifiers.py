"""Password verifiers and opaque tokens -- stdlib only (ADR-021 D2)."""

from __future__ import annotations

import hashlib
import hmac
import secrets

_N, _R, _P, _DKLEN = 2**14, 8, 1, 32
_MAXMEM = 64 * 1024 * 1024


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=_DKLEN, maxmem=_MAXMEM
    )


def hash_password(password: str) -> str:
    """Return a self-describing scrypt verifier for *password*."""
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt, _N, _R, _P)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


#: Verified against when no principal matches, so a miss costs the same time.
_DUMMY_VERIFIER = hash_password(secrets.token_urlsafe(16))


def verify_password(password: str, verifier: str | None) -> bool:
    """Constant-work check; ``None`` verifies against a dummy and fails."""
    stored = verifier or _DUMMY_VERIFIER
    try:
        scheme, n, r, p, salt, digest = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    candidate = _scrypt(password, bytes.fromhex(salt), int(n), int(r), int(p))
    return verifier is not None and hmac.compare_digest(candidate.hex(), digest)


def new_token() -> str:
    """A 256-bit opaque bearer value (session token or one-time code)."""
    return secrets.token_urlsafe(32)


def token_verifier(token: str) -> str:
    """The only form of a session token or one-time code that is stored."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
