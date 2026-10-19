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


#: Hashed against whenever there is no usable stored verifier (no principal,
#: a pending enrollment's unusable ``!`` marker, an unknown scheme or a
#: malformed value), so every failure costs the same work as a real check.
_DUMMY_SALT = secrets.token_bytes(16)


def _parse(verifier: str) -> tuple[bytes, int, int, int, str] | None:
    """The scrypt parameters of a well-formed verifier, else ``None``."""
    try:
        scheme, n, r, p, salt, digest = verifier.split("$")
        if scheme != "scrypt":
            return None
        bytes.fromhex(digest)
        cost, block, parallel = int(n), int(r), int(p)
        if cost < 2 or cost & (cost - 1) or block < 1 or parallel < 1:
            return None  # not valid scrypt parameters
        return bytes.fromhex(salt), cost, block, parallel, digest
    except ValueError:
        return None


def verify_password(password: str, verifier: str | None) -> bool:
    """Constant-work check. Anything but a usable verifier -- missing, empty,
    unusable, unknown scheme, malformed or with invalid parameters -- costs
    one dummy scrypt at the standard parameters and fails closed."""
    parsed = _parse(verifier) if verifier else None
    if parsed is not None:
        salt, n, r, p, digest = parsed
        try:
            candidate = _scrypt(password, salt, n, r, p)
        except ValueError:  # parameters hashlib rejects before hashing
            parsed = None
        else:
            return hmac.compare_digest(candidate.hex(), digest)
    _scrypt(password, _DUMMY_SALT, _N, _R, _P)  # same work; result unused
    return False


def new_token() -> str:
    """A 256-bit opaque bearer value (session token or one-time code)."""
    return secrets.token_urlsafe(32)


def token_verifier(token: str) -> str:
    """The only form of a session token or one-time code that is stored."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
