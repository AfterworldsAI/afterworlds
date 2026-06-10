"""ProviderAdapter protocol — CRD Issue 14a."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
)


@runtime_checkable
class ProviderAdapter(Protocol):
    """Protocol for provider/platform adapter implementations.

    Implementations must satisfy this protocol under mypy strict with no
    ``type: ignore`` annotations.

    The adapter owns all of:
      - model selection (from ``request.pass_id``)
      - provider-specific payload construction from ``request.rendered_blocks``
      - cache marker realization (adapters realize markers; never choose placement)
      - token usage extraction
      - wrapping provider SDK exceptions into ``ProviderRefusalError`` (content-policy
        refusals) or ``ProviderCallError`` (operational failures)
    """

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        """Execute one provider call and return a typed result.

        Raises:
            ProviderRefusalError: for content-policy refusals only.
            ProviderCallError: for operational failures (auth, rate limit,
                context length, malformed response, network, timeout).
        """
        ...

    @property
    def provider_name(self) -> str:
        """Stable identifier for this provider surface (e.g. ``"anthropic"``)."""
        ...


__all__ = ["ProviderAdapter"]
