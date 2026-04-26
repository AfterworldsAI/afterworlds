"""Extractor pass configuration — CRD Issue 10.

The Extractor is a small/fast model pass per the CRD cost model (Item 8).
Configuration follows the same env-var pattern as WriterConfig.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_EXTRACTOR_MODEL: str = "claude-haiku-4-5-20251001"

#: Max tokens for an Extractor response.  The tool-use output is structured JSON,
#: so 1024 tokens is generous; the prose budget is not relevant here.
EXTRACTOR_MAX_TOKENS: int = 1024


@dataclass
class ExtractorConfig:
    """Configuration for the Extractor pass.

    Attributes:
        model: Anthropic model identifier.  Defaults to the Haiku-tier model per
            the CRD small/fast model assignment for the Extractor pass.
        api_key_env: Name of the environment variable holding the Anthropic API key.
        extended_ttl: When True, the cache breakpoint uses ``ttl="1h"``.
            Must be True by default — CRD Item 14 invariant #9.
    """

    model: str = _DEFAULT_EXTRACTOR_MODEL
    api_key_env: str = "ANTHROPIC_API_KEY"
    extended_ttl: bool = True

    @classmethod
    def from_env(cls) -> ExtractorConfig:
        """Build an ExtractorConfig from environment variables.

        Environment variables:
            AFTERWORLDS_EXTRACTOR_MODEL: overrides the default model identifier.
            AFTERWORLDS_EXTRACTOR_API_KEY_ENV: overrides the env-var name for the key.
            AFTERWORLDS_EXTRACTOR_EXTENDED_TTL: set to "false", "0", or "no" to
                disable extended TTL (not recommended; defaults to True).
        """
        model = os.environ.get("AFTERWORLDS_EXTRACTOR_MODEL", _DEFAULT_EXTRACTOR_MODEL)
        api_key_env = os.environ.get(
            "AFTERWORLDS_EXTRACTOR_API_KEY_ENV", "ANTHROPIC_API_KEY"
        )
        ttl_str = os.environ.get("AFTERWORLDS_EXTRACTOR_EXTENDED_TTL", "true").lower()
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
                "Set it before calling the Extractor service."
            )
        return key
