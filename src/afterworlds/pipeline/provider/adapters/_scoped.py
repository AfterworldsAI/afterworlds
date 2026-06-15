"""Scoped provider adapter — CRD Issue 14a.

Injects sojourner_id and turn_id into ProviderCallRequest before delegating
to the underlying adapter, so refusal log entries carry correct request scope.
"""

from __future__ import annotations

from uuid import UUID

from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
)
from afterworlds.pipeline.provider._protocol import ProviderAdapter


class ScopedProviderAdapter:
    """Wraps a ProviderAdapter, filling sojourner_id/turn_id on every call.

    Used by the orchestrator at each pass call site so that any refusal written
    to provider_refusal_log carries the Sojourner and (where known) Turn context.
    """

    def __init__(
        self,
        delegate: ProviderAdapter,
        sojourner_id: UUID,
        turn_id: UUID | None = None,
    ) -> None:
        self._delegate = delegate
        self._sojourner_id = sojourner_id
        self._turn_id = turn_id

    @property
    def provider_name(self) -> str:
        return self._delegate.provider_name

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        scoped = request.model_copy(
            update={"sojourner_id": self._sojourner_id, "turn_id": self._turn_id}
        )
        return self._delegate.call(scoped)


__all__ = ["ScopedProviderAdapter"]
