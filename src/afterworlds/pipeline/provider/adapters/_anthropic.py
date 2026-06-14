"""Anthropic direct adapter — CRD Issue 14a.

Adapts the Anthropic Messages API to the provider-neutral ``ProviderAdapter``
protocol.  Owns:

  - Pass→model selection from a configurable capability profile (model strings
    live in config, not code — Issue 9 pattern).
  - Messages API payload construction from ``ProviderCallRequest.rendered_blocks``.
  - Cache marker realization: ``cache_control: {"type": "ephemeral", "ttl": ttl}``
    on the breakpoint block (extended 1h by default — CLAUDE.md economic invariant).
  - Token usage extraction → the four ``*_token_count`` fields.
  - Provider SDK exception wrapping → ``ProviderRefusalError`` (content-policy) or
    ``ProviderCallError`` (operational).

Model strings confirmed against Anthropic pricing page (2026-06-09) and
documented in ADR-014a.  The capability profile maps passes to tiers that
MUST agree with ``PASS_TIER_DEFAULTS`` in ``entitlement/policy.py``.

Extended-TTL (1h) cache_control is applied to any block that carries
``has_cache_breakpoint=True``.  No marker if no block is so marked.

SDK ``max_retries=0``: transient errors surface as ``ProviderCallError``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import anthropic
from anthropic.types import (
    CacheControlEphemeralParam,
    MessageParam,
    TextBlockParam,
    ToolUseBlock,
)

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.pipeline._refusal import (
    PassIdentifier,
    ProviderRefusal,
    ProviderRefusalError,
    RefusalCategory,
)
from afterworlds.pipeline._stable_prefix_renderer import RenderedBlock
from afterworlds.pipeline.provider._errors import ProviderCallError
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderContentPart,
    ProviderTextPart,
    ProviderToolCallPart,
)

# ---------------------------------------------------------------------------
# Known dynamic alias prefixes — a static deny-set for 14a
# (catalog-driven detection is 14b)
# ---------------------------------------------------------------------------

_OPENROUTER_ALIAS_PREFIXES: frozenset[str] = frozenset(
    [
        "openrouter/auto",
        "openrouter/free",
    ]
)

# ---------------------------------------------------------------------------
# Capability profile — pass→model and pass→tier
# ---------------------------------------------------------------------------

#: Model confirmed 2026-06-09 against Anthropic model listing.
#: Must agree with PASS_TIER_DEFAULTS in entitlement/policy.py.
_DEFAULT_HAIKU_MODEL: str = "claude-haiku-4-5-20251001"
_DEFAULT_SONNET_MODEL: str = "claude-sonnet-4-5"

#: Pass→(model, tier) mapping for the Anthropic direct adapter.
#: Sonnet for Writer/Extractor; Haiku for everything else.
#: Extractor is Sonnet per PASS_TIER_DEFAULTS (the ExtractorConfig default of
#: Haiku is a known discrepancy flagged in Architecture Notes).
_PASS_PROFILE: dict[PipelinePassId, tuple[str, ModelTier]] = {
    PipelinePassId.PLANNER: (_DEFAULT_HAIKU_MODEL, ModelTier.HAIKU),
    PipelinePassId.WRITER: (_DEFAULT_SONNET_MODEL, ModelTier.SONNET),
    PipelinePassId.EXTRACTOR: (_DEFAULT_SONNET_MODEL, ModelTier.SONNET),
    PipelinePassId.CONTRADICTION: (_DEFAULT_HAIKU_MODEL, ModelTier.HAIKU),
    PipelinePassId.INPUT_SAFETY: (_DEFAULT_HAIKU_MODEL, ModelTier.HAIKU),
    PipelinePassId.OUTPUT_SAFETY: (_DEFAULT_HAIKU_MODEL, ModelTier.HAIKU),
}


@dataclass
class AnthropicCapabilityProfile:
    """Configurable pass→model mapping.  Model strings live in config, not code."""

    pass_model_overrides: dict[PipelinePassId, str] = field(default_factory=dict)

    def model_for(self, pass_id: PipelinePassId) -> str:
        if pass_id in self.pass_model_overrides:
            return self.pass_model_overrides[pass_id]
        model, _ = _PASS_PROFILE[pass_id]
        return model

    def tier_for(self, pass_id: PipelinePassId) -> ModelTier:
        _, tier = _PASS_PROFILE[pass_id]
        return tier


# ---------------------------------------------------------------------------
# Refusal detection helpers
# ---------------------------------------------------------------------------

_REFUSAL_PHRASES: tuple[str, ...] = (
    "i cannot assist",
    "i can't assist",
    "i'm unable to",
    "i cannot help",
    "i can't help",
    "i'm not able to",
    "i must decline",
    "i cannot comply",
    "against my guidelines",
    "against anthropic's",
    "violates my",
)


def _classify_stop_reason_and_text(
    stop_reason: str | None,
    text_content: str,
) -> RefusalCategory | None:
    """Return a RefusalCategory if the response looks like a content-policy refusal.

    Returns None for normal stop reasons that are not refusals.
    """
    if stop_reason in ("end_turn", "stop_sequence"):
        lower = text_content.lower()
        for phrase in _REFUSAL_PHRASES:
            if phrase in lower:
                return RefusalCategory.CONTENT_POLICY
    return None


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class AnthropicDirectAdapter:
    """Anthropic direct adapter implementing ``ProviderAdapter``.

    Extended-TTL (1h) caching is enabled by default on all passes via
    ``cache_control`` on blocks that carry ``has_cache_breakpoint=True``.

    Args:
        api_key: Raw API key.  Never stored in SQLite, logs, or telemetry.
            Owned by the credential store; passed in at resolution time.
        profile: Capability profile for pass→model mapping.  Defaults to
            the v1 profile with Haiku for Planner/Safety/Contradiction and
            Sonnet for Writer/Extractor.
    """

    def __init__(
        self,
        api_key: str,
        profile: AnthropicCapabilityProfile | None = None,
    ) -> None:
        self._api_key = api_key
        self._profile = profile or AnthropicCapabilityProfile()

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        """Execute one Anthropic Messages API call and return a typed result.

        Raises:
            ProviderRefusalError: for content-policy refusals.
            ProviderCallError: for operational failures.
        """
        model = self._profile.model_for(request.pass_id)
        tier = self._profile.tier_for(request.pass_id)

        client = anthropic.Anthropic(api_key=self._api_key, max_retries=0)

        system_blocks, user_blocks = self._build_payload_blocks(request)

        tools = None
        tool_choice = None
        if request.tool_definitions:
            tools = [
                {
                    "name": td.name,
                    "description": td.description,
                    "input_schema": td.input_schema,
                }
                for td in request.tool_definitions
            ]
            if request.forced_tool_name:
                tool_choice = {
                    "type": "tool",
                    "name": request.forced_tool_name,
                }

        start = time.monotonic()
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "max_tokens": request.max_output_tokens,
                "messages": [MessageParam(role="user", content=user_blocks)],
                "stream": False,
            }
            if system_blocks:
                kwargs["system"] = system_blocks
            if request.temperature is not None:
                kwargs["temperature"] = request.temperature
            if tools:
                kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

            response = client.messages.create(**kwargs)
        except anthropic.APIStatusError as exc:
            sanitized = _sanitize_sdk_error(str(exc), self._api_key)
            raise ProviderCallError(sanitized) from exc
        except anthropic.APIConnectionError as exc:
            raise ProviderCallError(
                f"Anthropic connection error: {type(exc).__name__}"
            ) from exc
        except anthropic.APITimeoutError as exc:
            raise ProviderCallError("Anthropic API timeout") from exc
        except Exception as exc:
            sanitized = _sanitize_sdk_error(str(exc), self._api_key)
            raise ProviderCallError(f"Anthropic unexpected error: {sanitized}") from exc
        finally:
            latency_ms = int((time.monotonic() - start) * 1000)

        content_parts, refusal_cat, coarse_reason = self._parse_response(response)

        usage = response.usage
        cache_read = usage.cache_read_input_tokens if usage else None
        cache_creation = usage.cache_creation_input_tokens if usage else None
        cache_warmed = cache_read is not None and cache_read > 0

        if refusal_cat is not None:
            excerpt_raw = _extract_excerpt(response)
            excerpt = _sanitize_sdk_error(excerpt_raw, self._api_key)
            pass_identifier = _pass_id_to_pass_identifier(request.pass_id)
            raise ProviderRefusalError(
                ProviderRefusal(
                    provider=self.provider_name,
                    model=model,
                    pass_identifier=pass_identifier,
                    coarse_reason=coarse_reason,
                    raw_response_excerpt=excerpt[:1024] if excerpt else None,
                    refusal_category=refusal_cat,
                )
            )

        return ProviderCallResult(
            pass_id=request.pass_id,
            provider_name=self.provider_name,
            model_identifier=model,
            model_tier=tier,
            content_parts=content_parts,
            input_token_count=usage.input_tokens if usage else None,
            output_token_count=usage.output_tokens if usage else None,
            cache_read_token_count=cache_read,
            cache_creation_token_count=cache_creation,
            cache_warmed=cache_warmed,
            latency_ms=latency_ms,
            sojourner_id=request.sojourner_id,
            turn_id=request.turn_id,
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _build_payload_blocks(
        self,
        request: ProviderCallRequest,
    ) -> tuple[list[TextBlockParam], list[TextBlockParam]]:
        """Return (system_blocks, user_blocks) for the Anthropic payload.

        ``request.system_blocks`` maps to the Anthropic ``system`` parameter.
        ``request.rendered_blocks`` maps to user-message content.
        Cache markers are realized only on blocks with ``has_cache_breakpoint=True``.
        """
        system_blocks = [self._realize_block(b) for b in request.system_blocks]
        user_blocks = [self._realize_block(b) for b in request.rendered_blocks]
        return system_blocks, user_blocks

    @staticmethod
    def _realize_block(block: RenderedBlock) -> TextBlockParam:
        """Convert a RenderedBlock to an Anthropic TextBlockParam."""
        if block.has_cache_breakpoint and block.ttl is not None:
            return TextBlockParam(
                type="text",
                text=block.text,
                cache_control=CacheControlEphemeralParam(
                    type="ephemeral",
                    ttl=block.ttl,
                ),
            )
        return TextBlockParam(type="text", text=block.text)

    @staticmethod
    def _parse_response(
        response: object,
    ) -> tuple[list[ProviderContentPart], RefusalCategory | None, str | None]:
        """Extract content parts and detect refusals from an Anthropic Message."""
        from anthropic.types import Message, TextBlock

        if not isinstance(response, Message):
            raise ProviderCallError("Anthropic returned unexpected response type")

        parts: list[ProviderContentPart] = []
        text_content = ""
        coarse_reason: str | None = None

        for block in response.content:
            if isinstance(block, TextBlock):
                text_content += block.text
                parts.append(ProviderTextPart(text=block.text))
            elif isinstance(block, ToolUseBlock):
                parts.append(
                    ProviderToolCallPart(
                        tool_name=block.name,
                        tool_input=block.input,
                    )
                )

        if not parts:
            raise ProviderCallError("Anthropic returned empty content")

        # Detect content-policy refusal on text-only responses
        has_tool = any(isinstance(p, ProviderToolCallPart) for p in parts)
        refusal_cat: RefusalCategory | None = None
        if not has_tool and text_content:
            refusal_cat = _classify_stop_reason_and_text(
                response.stop_reason, text_content
            )
            if refusal_cat is not None:
                coarse_reason = text_content[:200]

        return parts, refusal_cat, coarse_reason


def _pass_id_to_pass_identifier(pass_id: PipelinePassId) -> PassIdentifier:
    """Map a PipelinePassId to the 12c PassIdentifier for ProviderRefusal."""
    _MAP: dict[PipelinePassId, PassIdentifier] = {
        PipelinePassId.PLANNER: PassIdentifier.PLANNER,
        PipelinePassId.WRITER: PassIdentifier.WRITER,
        PipelinePassId.EXTRACTOR: PassIdentifier.EXTRACTOR,
        PipelinePassId.CONTRADICTION: PassIdentifier.CONTRADICTION,
        PipelinePassId.INPUT_SAFETY: PassIdentifier.PLANNER,  # Safety→PIPELINE_ERROR
        PipelinePassId.OUTPUT_SAFETY: PassIdentifier.PLANNER,  # see note below
    }
    return _MAP.get(pass_id, PassIdentifier.PLANNER)


def _extract_excerpt(response: object) -> str:
    """Extract a short in-memory excerpt from the response for audit context."""
    from anthropic.types import Message, TextBlock

    if not isinstance(response, Message):
        return ""
    for block in response.content:
        if isinstance(block, TextBlock):
            return block.text[:500]
    return ""


def _sanitize_sdk_error(message: str, api_key: str) -> str:
    """Remove any key substring from an error message before logging or storage."""
    if api_key and api_key in message:
        return message.replace(api_key, "[REDACTED]")
    if len(api_key) > 12:
        prefix = api_key[:6]
        if prefix in message:
            return message.replace(prefix, "[REDACTED]")
    return message


__all__ = [
    "AnthropicCapabilityProfile",
    "AnthropicDirectAdapter",
]
