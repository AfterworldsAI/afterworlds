"""OpenRouter model catalog provider — CRD Issue 14b.

Provides model capability data from either a static fixture (CI default, no
network) or the live OpenRouter /models API (opt-in for @pytest.mark.live tests).

This module is the only boundary for network I/O in the registry layer.  The
``OpenRouterCapabilityRegistry`` consumes an ``OpenRouterModelCatalogProvider``
and never calls the network directly.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class OpenRouterCatalogModel(BaseModel, extra="forbid"):
    """One model entry from the OpenRouter /models catalog.

    All capability fields are tri-state (True / False / None):
      - True:  API reports the capability is present.
      - False: API reports the capability is absent (route may be rejected).
      - None:  capability not reported or unknown (fail-safe: do not reject).

    ``context_length=None`` means the API did not report one.
    ``is_dynamic_router=True`` marks routing aliases (auto/free) that should
    not be used as leaf models.
    """

    id: str
    name: str = ""
    context_length: int | None = None
    supports_text_output: bool | None = None
    supports_tool_use: bool | None = None
    supports_structured_output: bool | None = None
    is_dynamic_router: bool = False
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


@runtime_checkable
class OpenRouterModelCatalogProvider(Protocol):
    """Protocol for objects that supply an OpenRouter model catalog."""

    def fetch_catalog(self) -> Sequence[OpenRouterCatalogModel]: ...


class FixtureOpenRouterCatalogProvider:
    """Static fixture catalog for CI and offline testing.

    Returns a caller-supplied list of entries; defaults to empty (all OpenRouter
    models are catalog misses, so Safety always runs).  No network I/O.
    This is the default catalog provider for ``OpenRouterCapabilityRegistry``
    when no provider is specified.
    """

    def __init__(
        self,
        entries: Sequence[OpenRouterCatalogModel] | None = None,
    ) -> None:
        self._entries: Sequence[OpenRouterCatalogModel] = (
            entries if entries is not None else []
        )

    def fetch_catalog(self) -> Sequence[OpenRouterCatalogModel]:
        return self._entries


class LiveOpenRouterCatalogProvider:
    """Catalog provider that fetches live data from the OpenRouter /models endpoint.

    Opt-in for integration tests decorated with ``@pytest.mark.live``.
    Not used in CI.  Requires a valid OpenRouter API key.

    The raw API response is mapped to ``OpenRouterCatalogModel`` on a best-effort
    basis: unknown fields are ignored, missing capability flags default to None.
    """

    _MODELS_URL = "https://openrouter.ai/api/v1/models"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def fetch_catalog(self) -> Sequence[OpenRouterCatalogModel]:
        req = urllib.request.Request(
            self._MODELS_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            payload = json.loads(resp.read().decode())

        fetched_at = datetime.now(UTC)
        models: list[OpenRouterCatalogModel] = []
        for entry in payload.get("data", []):
            model_id: str = entry.get("id", "")
            if not model_id:
                continue
            arch = entry.get("architecture") or {}
            output_modalities: list[str] = arch.get("output_modalities") or []
            supports_text: bool | None = True if "text" in output_modalities else None
            models.append(
                OpenRouterCatalogModel(
                    id=model_id,
                    name=entry.get("name") or "",
                    context_length=entry.get("context_length"),
                    supports_text_output=supports_text,
                    supports_tool_use=entry.get("supports_tool_use"),
                    supports_structured_output=entry.get("supports_structured_output"),
                    is_dynamic_router=bool(entry.get("is_dynamic_router", False)),
                    fetched_at=fetched_at,
                )
            )
        return models


__all__ = [
    "FixtureOpenRouterCatalogProvider",
    "LiveOpenRouterCatalogProvider",
    "OpenRouterCatalogModel",
    "OpenRouterModelCatalogProvider",
]
