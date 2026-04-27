"""Contradiction pass configuration — CRD Issue 11."""

from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_CONTRADICTION_MODEL: str = "claude-haiku-4-5-20251001"

CONTRADICTION_MAX_TOKENS: int = 1024


@dataclass
class ContradictionConfig:
    model: str = _DEFAULT_CONTRADICTION_MODEL
    api_key_env: str = "ANTHROPIC_API_KEY"
    extended_ttl: bool = True  # CRD invariant — must default True

    @classmethod
    def from_env(cls) -> ContradictionConfig:
        model = os.environ.get(
            "AFTERWORLDS_CONTRADICTION_MODEL", _DEFAULT_CONTRADICTION_MODEL
        )
        api_key_env = os.environ.get(
            "AFTERWORLDS_CONTRADICTION_API_KEY_ENV", "ANTHROPIC_API_KEY"
        )
        ttl_str = os.environ.get(
            "AFTERWORLDS_CONTRADICTION_EXTENDED_TTL", "true"
        ).lower()
        extended_ttl = ttl_str not in ("0", "false", "no")
        return cls(model=model, api_key_env=api_key_env, extended_ttl=extended_ttl)

    def get_api_key(self) -> str:
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise ValueError(
                f"Anthropic API key env var {self.api_key_env!r} is not set. "
                "Set the environment variable or use"
                " AFTERWORLDS_CONTRADICTION_API_KEY_ENV "
                "to point to a different variable name."
            )
        return key


__all__ = [
    "ContradictionConfig",
    "CONTRADICTION_MAX_TOKENS",
]
