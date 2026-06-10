"""Provider adapter error types — CRD Issue 14a.

``ProviderRefusalError`` and ``ProviderRefusal`` are reused from Issue 12c
(_refusal.py) — they are NOT redefined here.  This module adds only the new
operational-failure and configuration-failure types.
"""

from __future__ import annotations


class ProviderCallError(Exception):
    """Raised by adapters for operational provider failures.

    Covers: context length exceeded, empty or malformed response, authentication
    failure, rate limit, network error, timeout.  These are never refusals and
    are never fallback-eligible.

    The ``detail`` message must be sanitized — verify ``str(e)`` contains no key
    material before constructing.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class ProviderConfigError(Exception):
    """Raised when provider resolution fails.

    Examples: BYOK with zero configured credentials; BYOK OpenRouter with a
    configured credential but no ``preferred_model_identifier``; dynamic alias
    rejected for a core narrative pass.

    No key material in the message.
    """


class CredentialValidationError(Exception):
    """Raised when a credential fails structural validation.

    Structural validation only (empty, whitespace, obviously malformed).
    No live API call is made during this check.  No key material in the message.
    """


__all__ = [
    "ProviderCallError",
    "ProviderConfigError",
    "CredentialValidationError",
]
