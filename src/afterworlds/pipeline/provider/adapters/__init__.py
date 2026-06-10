"""Provider adapters — CRD Issue 14a."""

from afterworlds.pipeline.provider.adapters._anthropic import (
    AnthropicCapabilityProfile,
    AnthropicDirectAdapter,
)
from afterworlds.pipeline.provider.adapters._fallback import RefusalFallbackRouter
from afterworlds.pipeline.provider.adapters._openrouter import (
    OpenRouterAdapter,
    OpenRouterAdapterConfig,
)

__all__ = [
    "AnthropicCapabilityProfile",
    "AnthropicDirectAdapter",
    "OpenRouterAdapter",
    "OpenRouterAdapterConfig",
    "RefusalFallbackRouter",
]
