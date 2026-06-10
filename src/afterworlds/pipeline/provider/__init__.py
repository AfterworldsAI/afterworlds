"""Provider/platform adapter layer — CRD Issue 14a."""

from afterworlds.pipeline.provider._errors import (
    CredentialValidationError,
    ProviderCallError,
    ProviderConfigError,
)
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderContentPart,
    ProviderTextPart,
    ProviderToolCallPart,
    ProviderToolDefinition,
)
from afterworlds.pipeline.provider._protocol import ProviderAdapter
from afterworlds.pipeline.provider._resolver import (
    HostedRoutingConfig,
    ProviderResolver,
)
from afterworlds.pipeline.provider._routing import (
    CapabilityProfileAwareSafetyPolicy,
    EligibleWriterRoute,
    SafetyPolicyContext,
    TurnProviderBinding,
)
from afterworlds.pipeline.provider.adapters import (
    AnthropicCapabilityProfile,
    AnthropicDirectAdapter,
    OpenRouterAdapter,
    RefusalFallbackRouter,
)
from afterworlds.pipeline.provider.normalization import (
    AnthropicNormalizationFactorProvider,
    OpenRouterNormalizationFactorProvider,
)

__all__ = [
    "AnthropicCapabilityProfile",
    "AnthropicDirectAdapter",
    "AnthropicNormalizationFactorProvider",
    "CapabilityProfileAwareSafetyPolicy",
    "CredentialValidationError",
    "EligibleWriterRoute",
    "HostedRoutingConfig",
    "OpenRouterAdapter",
    "OpenRouterNormalizationFactorProvider",
    "ProviderAdapter",
    "ProviderCallError",
    "ProviderCallRequest",
    "ProviderCallResult",
    "ProviderConfigError",
    "ProviderContentPart",
    "ProviderResolver",
    "ProviderTextPart",
    "ProviderToolCallPart",
    "ProviderToolDefinition",
    "RefusalFallbackRouter",
    "SafetyPolicyContext",
    "TurnProviderBinding",
]
