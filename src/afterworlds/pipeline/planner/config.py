"""Planner pass configuration — CRD Issue 12a."""

from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_PLANNER_MODEL: str = "claude-haiku-4-5-20251001"

PLANNER_MAX_TOKENS: int = 1024


@dataclass
class PlannerConfig:
    model: str = _DEFAULT_PLANNER_MODEL
    api_key_env: str = "ANTHROPIC_API_KEY"
    extended_ttl: bool = True  # CRD invariant — must default True

    @classmethod
    def from_env(cls) -> PlannerConfig:
        model = os.environ.get("AFTERWORLDS_PLANNER_MODEL", _DEFAULT_PLANNER_MODEL)
        api_key_env = os.environ.get(
            "AFTERWORLDS_PLANNER_API_KEY_ENV", "ANTHROPIC_API_KEY"
        )
        ttl_str = os.environ.get("AFTERWORLDS_PLANNER_EXTENDED_TTL", "true").lower()
        extended_ttl = ttl_str not in ("0", "false", "no")
        return cls(model=model, api_key_env=api_key_env, extended_ttl=extended_ttl)

    def get_api_key(self) -> str:
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise ValueError(
                f"Anthropic API key env var {self.api_key_env!r} is not set. "
                "Set the environment variable or use"
                " AFTERWORLDS_PLANNER_API_KEY_ENV "
                "to point to a different variable name."
            )
        return key


__all__ = [
    "PlannerConfig",
    "PLANNER_MAX_TOKENS",
]
