"""Safety pass configuration — CRD Issue 12b."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

_DEFAULT_SAFETY_MODEL: str = "claude-haiku-4-5-20251001"
SAFETY_MAX_TOKENS: int = 1024


@dataclass
class SafetyConfig:
    """Configuration for the Safety pass.

    Attributes:
        model: Anthropic model identifier.
        api_key_env: Environment variable name holding the Anthropic API key.
        extended_ttl: Enable extended (1 h) cache TTL.  Must default True per
            CRD Item 14 invariant #9 (economic requirement, not preference).
    """

    model: str = field(default=_DEFAULT_SAFETY_MODEL)
    api_key_env: str = field(default="ANTHROPIC_API_KEY")
    extended_ttl: bool = field(default=True)

    @classmethod
    def from_env(cls) -> SafetyConfig:
        """Build a SafetyConfig from environment variables."""
        model = os.environ.get("SAFETY_MODEL", _DEFAULT_SAFETY_MODEL)
        api_key_env = os.environ.get("SAFETY_API_KEY_ENV", "ANTHROPIC_API_KEY")
        extended_ttl_raw = os.environ.get("SAFETY_EXTENDED_TTL", "true")
        extended_ttl = extended_ttl_raw.lower() not in {"false", "0", "no"}
        return cls(model=model, api_key_env=api_key_env, extended_ttl=extended_ttl)

    def get_api_key(self) -> str:
        """Read the API key from the configured environment variable."""
        value = os.environ.get(self.api_key_env)
        if not value:
            raise RuntimeError(
                f"Environment variable '{self.api_key_env}' is not set or empty"
            )
        return value
