"""NormalizationFactorProvider implementations — CRD Issue 14a.

v1: returns ``Decimal("1.0")`` for known providers; raises ``ValueError`` for
unexpected provider strings.  Calibration inputs are documented in ADR-014a for
the owner's pricing lock; they are not applied here.

Issue 13's ``TurnCostPolicyConfig`` defaults are not modified in Issue 14a.
"""

from __future__ import annotations

from decimal import Decimal

from afterworlds.entitlement.enums import ModelTier


class AnthropicNormalizationFactorProvider:
    """Normalization factor for Anthropic direct usage."""

    def get_factor(self, provider: str, model_tier: ModelTier) -> Decimal:
        if provider != "anthropic":
            raise ValueError(
                "AnthropicNormalizationFactorProvider: unexpected provider"
                f" {provider!r}"
            )
        return Decimal("1.0")


class OpenRouterNormalizationFactorProvider:
    """Normalization factor for OpenRouter usage."""

    def get_factor(self, provider: str, model_tier: ModelTier) -> Decimal:
        if provider != "openrouter":
            raise ValueError(
                "OpenRouterNormalizationFactorProvider: unexpected provider"
                f" {provider!r}"
            )
        return Decimal("1.0")


__all__ = [
    "AnthropicNormalizationFactorProvider",
    "OpenRouterNormalizationFactorProvider",
]
