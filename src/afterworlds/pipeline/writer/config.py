"""Writer pass configuration — CRD Issue 9.

Configuration is read from environment variables at call time via
``WriterConfig.from_env()``.  No global singleton — callers construct a config
object and pass it into the service.

Dev-time note: Issue 9 reads the API key from a named environment variable as a
development convenience.  This is not the production BYOK key path, which is
owned by Issue 14 (BYOK API key management / provider routing).  The
``api_key_env`` field names the env var that holds the key; the key itself is
never stored in config state.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Default model identifier — lives in config, not code, so it can roll forward
# without a code change.  Issue 14 is the place where provider routing reopens.
# ---------------------------------------------------------------------------
_DEFAULT_MODEL: str = "claude-sonnet-4-5"

#: Max tokens for a Writer response.  4096 is a reasonable prose budget for
#: a single narrative beat without imposing a hard ceiling during proof-of-life.
WRITER_MAX_TOKENS: int = 4096


@dataclass
class WriterConfig:
    """Configuration for the Writer pass.

    Attributes:
        model: Anthropic model identifier string.  Must be a Sonnet-tier
            model per the v1 proof-of-life choice in Issue 9.  Issue 14
            reopens model routing.
        api_key_env: Name of the environment variable that holds the Anthropic
            API key.  The key is read at call time; it is never stored here.
        extended_ttl: When True, the cache breakpoint uses ``ttl="1h"``
            (extended TTL).  Must be True by default — CRD Item 14 invariant #9.
    """

    model: str = _DEFAULT_MODEL
    api_key_env: str = "ANTHROPIC_API_KEY"
    extended_ttl: bool = True

    @classmethod
    def from_env(cls) -> WriterConfig:
        """Build a WriterConfig from environment variables.

        Environment variables:
            AFTERWORLDS_WRITER_MODEL: overrides the default model identifier.
            AFTERWORLDS_WRITER_API_KEY_ENV: overrides the default env-var name
                that holds the Anthropic API key.
            AFTERWORLDS_WRITER_EXTENDED_TTL: set to "false", "0", or "no" to
                disable extended TTL (not recommended; defaults to True).
        """
        model = os.environ.get("AFTERWORLDS_WRITER_MODEL", _DEFAULT_MODEL)
        api_key_env = os.environ.get(
            "AFTERWORLDS_WRITER_API_KEY_ENV", "ANTHROPIC_API_KEY"
        )
        ttl_str = os.environ.get("AFTERWORLDS_WRITER_EXTENDED_TTL", "true").lower()
        extended_ttl = ttl_str not in ("0", "false", "no")
        return cls(model=model, api_key_env=api_key_env, extended_ttl=extended_ttl)

    def get_api_key(self) -> str:
        """Return the API key from the configured environment variable.

        Raises:
            ValueError: if the configured env var is not set or empty.
        """
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise ValueError(
                f"Anthropic API key env var {self.api_key_env!r} is not set. "
                "Set it before calling the Writer service."
            )
        return key
