"""RPG Adjudication pass configuration — CRD Issue 15."""

from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_ADJUDICATION_MODEL: str = "claude-haiku-4-5-20251001"

ADJUDICATION_MAX_TOKENS: int = 512

#: Maximum number of roll proposals the pass will accept per turn.
#: Proposals beyond this limit are silently dropped with a diagnostic note.
ADJUDICATION_MAX_ROLLS_PER_TURN: int = 5


@dataclass
class AdjudicationConfig:
    model: str = _DEFAULT_ADJUDICATION_MODEL
    api_key_env: str = "ANTHROPIC_API_KEY"
    extended_ttl: bool = True  # CRD invariant — must default True

    @classmethod
    def from_env(cls) -> AdjudicationConfig:
        model = os.environ.get(
            "AFTERWORLDS_ADJUDICATION_MODEL", _DEFAULT_ADJUDICATION_MODEL
        )
        api_key_env = os.environ.get(
            "AFTERWORLDS_ADJUDICATION_API_KEY_ENV", "ANTHROPIC_API_KEY"
        )
        ttl_str = os.environ.get(
            "AFTERWORLDS_ADJUDICATION_EXTENDED_TTL", "true"
        ).lower()
        extended_ttl = ttl_str not in ("0", "false", "no")
        return cls(model=model, api_key_env=api_key_env, extended_ttl=extended_ttl)

    def get_api_key(self) -> str:
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise ValueError(
                f"Anthropic API key env var {self.api_key_env!r} is not set. "
                "Set the environment variable or use"
                " AFTERWORLDS_ADJUDICATION_API_KEY_ENV "
                "to point to a different variable name."
            )
        return key


__all__ = [
    "AdjudicationConfig",
    "ADJUDICATION_MAX_TOKENS",
    "ADJUDICATION_MAX_ROLLS_PER_TURN",
]
