"""Provider/platform adapter layer — CRD Issue 14a/14b."""

from afterworlds.pipeline.provider._catalog import (
    FixtureOpenRouterCatalogProvider,
    LiveOpenRouterCatalogProvider,
    OpenRouterCatalogModel,
    OpenRouterModelCatalogProvider,
)
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
from afterworlds.pipeline.provider._registry import (
    OpenRouterCapabilityRegistry,
    WhitelistConfig,
    WhitelistEntry,
)
from afterworlds.pipeline.provider._resolver import (
    HostedRoutingConfig,
    ProviderResolver,
)
from afterworlds.pipeline.provider._routing import (
    CapabilityEvidenceSource,
    CapabilityProfileAwareSafetyPolicy,
    EligibleModelRoute,
    ModelRouteCapabilityProfile,
    SafetyPolicyContext,
    SafetyWhitelistStatus,
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
    "CapabilityEvidenceSource",
    "CapabilityProfileAwareSafetyPolicy",
    "CredentialValidationError",
    "EligibleModelRoute",
    "FixtureOpenRouterCatalogProvider",
    "HostedRoutingConfig",
    "LiveOpenRouterCatalogProvider",
    "ModelRouteCapabilityProfile",
    "OpenRouterAdapter",
    "OpenRouterCapabilityRegistry",
    "OpenRouterCatalogModel",
    "OpenRouterModelCatalogProvider",
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
    "SafetyWhitelistStatus",
    "TurnProviderBinding",
    "WhitelistConfig",
    "WhitelistEntry",
]
