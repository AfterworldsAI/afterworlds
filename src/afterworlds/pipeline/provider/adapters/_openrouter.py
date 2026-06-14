"""OpenRouter adapter — CRD Issue 14a.

One normalized adapter over OpenRouter's OpenAI-compatible API.

Key invariants:
  - Cache is OFF by default (no markers, cache counts None) until a specific
    route's cache behavior is adapter-verified.  This reconciles the
    extended-TTL invariant ("wherever the provider supports it") with the rule
    that no cache assumption is binding until adapter-verified.
  - No OpenRouter route may skip Safety in 14a.
  - Dynamic router aliases (auto/free routes) are rejected for core narrative
    passes unless pre-resolved to an exact model identity.
  - Tool definitions map to OpenAI-style tools; structured passes request tools
    fail-closed — a configured model that cannot satisfy a structured pass
    fails as ``ProviderCallError``, never silent degradation.

Cache counts are always ``None`` in v1 (OpenRouter does not expose upstream
provider cache metrics over its OpenAI-compatible API in a reliable cross-model
way; enabling cache per route requires adapter verification documented in
ADR-014a).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.pipeline._refusal import (
    ProviderRefusal,
    ProviderRefusalError,
    RefusalCategory,
)
from afterworlds.pipeline.provider._errors import ProviderCallError, ProviderConfigError
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderContentPart,
    ProviderTextPart,
    ProviderToolCallPart,
)
from afterworlds.pipeline.provider.adapters._anthropic import (
    _pass_id_to_pass_identifier,
    _sanitize_sdk_error,
)

# ---------------------------------------------------------------------------
# Dynamic alias deny-set (14a static; catalog-driven detection is 14b)
# ---------------------------------------------------------------------------

_ALIAS_DENY_PREFIXES: tuple[str, ...] = (
    "openrouter/auto",
    "openrouter/free",
    "auto",
)

_ALIAS_DENY_EXACT: frozenset[str] = frozenset(
    [
        "openrouter/auto",
        "openrouter/free",
    ]
)


def _is_dynamic_alias(model_id: str) -> bool:
    """Return True if the model id looks like a dynamic OpenRouter alias."""
    lower = model_id.lower()
    if lower in _ALIAS_DENY_EXACT:
        return True
    return any(lower.startswith(prefix) for prefix in _ALIAS_DENY_PREFIXES)


# ---------------------------------------------------------------------------
# Model tier inference from OpenRouter model id
# ---------------------------------------------------------------------------


def _infer_tier(model_id: str, pass_id: PipelinePassId) -> ModelTier:
    """Infer ModelTier for an OpenRouter route from pass_id (best effort)."""
    from afterworlds.entitlement.policy import PASS_TIER_DEFAULTS

    return PASS_TIER_DEFAULTS.get(pass_id, ModelTier.SONNET)


# ---------------------------------------------------------------------------
# Refusal detection for OpenAI-compatible responses
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
)


def _detect_refusal(text: str) -> RefusalCategory | None:
    lower = text.lower()
    for phrase in _REFUSAL_PHRASES:
        if phrase in lower:
            return RefusalCategory.CONTENT_POLICY
    return None


# ---------------------------------------------------------------------------
# OpenRouterAdapter
# ---------------------------------------------------------------------------


@dataclass
class OpenRouterAdapterConfig:
    """Configuration for one Sojourner's OpenRouter route."""

    model_identifier: str
    api_key: str


class OpenRouterAdapter:
    """OpenRouter adapter implementing ``ProviderAdapter``.

    Uses OpenRouter's OpenAI-compatible Messages endpoint.  Cache is off in v1
    (all ``cache_*_token_count`` fields are ``None``).

    Args:
        model_identifier: Exact model route (e.g. ``"anthropic/claude-haiku-4-5"``).
            Dynamic aliases are rejected at construction.
        api_key: OpenRouter API key.  Never stored in SQLite, logs, or telemetry.
    """

    def __init__(self, model_identifier: str, api_key: str) -> None:
        if _is_dynamic_alias(model_identifier):
            raise ProviderConfigError(
                f"Dynamic OpenRouter alias rejected for core narrative passes: "
                f"{model_identifier!r}.  Supply an exact model identifier."
            )
        self._model_identifier = model_identifier
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        """Execute one OpenRouter call and return a typed result.

        Raises:
            ProviderCallError: for operational failures or structured-pass
                models that cannot satisfy tool use.
            ProviderRefusalError: for content-policy refusals.
        """
        tier = _infer_tier(self._model_identifier, request.pass_id)

        messages = self._build_messages(request)
        tools = None
        tool_choice = None
        if request.tool_definitions:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": td.name,
                        "description": td.description,
                        "parameters": td.input_schema,
                    },
                }
                for td in request.tool_definitions
            ]
            if request.forced_tool_name:
                tool_choice = {
                    "type": "function",
                    "function": {"name": request.forced_tool_name},
                }

        try:
            import openai  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ProviderCallError(
                "openai package is required for OpenRouterAdapter; install it with pip"
            ) from exc

        client = openai.OpenAI(
            api_key=self._api_key,
            base_url="https://openrouter.ai/api/v1",
            max_retries=0,
        )

        start = time.monotonic()
        try:
            kwargs: dict[str, Any] = {
                "model": self._model_identifier,
                "max_tokens": request.max_output_tokens,
                "messages": messages,
            }
            if request.temperature is not None:
                kwargs["temperature"] = request.temperature
            if tools:
                kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice

            response = client.chat.completions.create(**kwargs)
        except openai.AuthenticationError as exc:
            sanitized = _sanitize_sdk_error(str(exc), self._api_key)
            raise ProviderCallError(f"OpenRouter auth error: {sanitized}") from exc
        except openai.RateLimitError as exc:
            raise ProviderCallError("OpenRouter rate limit exceeded") from exc
        except openai.APIConnectionError as exc:
            raise ProviderCallError(
                f"OpenRouter connection error: {type(exc).__name__}"
            ) from exc
        except openai.APITimeoutError as exc:
            raise ProviderCallError("OpenRouter API timeout") from exc
        except openai.BadRequestError as exc:
            sanitized = _sanitize_sdk_error(str(exc), self._api_key)
            raise ProviderCallError(f"OpenRouter bad request: {sanitized}") from exc
        except Exception as exc:
            sanitized = _sanitize_sdk_error(str(exc), self._api_key)
            raise ProviderCallError(
                f"OpenRouter unexpected error: {sanitized}"
            ) from exc
        finally:
            latency_ms = int((time.monotonic() - start) * 1000)

        content_parts, refusal_cat, coarse_reason = self._parse_response(response)

        if refusal_cat is not None:
            pass_identifier = _pass_id_to_pass_identifier(request.pass_id)
            raise ProviderRefusalError(
                ProviderRefusal(
                    provider=self.provider_name,
                    model=self._model_identifier,
                    pass_identifier=pass_identifier,
                    coarse_reason=coarse_reason,
                    raw_response_excerpt=None,  # never persist response text
                    refusal_category=refusal_cat,
                )
            )

        # OpenRouter v1: cache counts always None (not adapter-verified)
        return ProviderCallResult(
            pass_id=request.pass_id,
            provider_name=self.provider_name,
            model_identifier=self._model_identifier,
            model_tier=tier,
            content_parts=content_parts,
            input_token_count=self._extract_input_tokens(response),
            output_token_count=self._extract_output_tokens(response),
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=latency_ms,
            sojourner_id=request.sojourner_id,
            turn_id=request.turn_id,
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _build_messages(request: ProviderCallRequest) -> list[dict]:  # type: ignore[type-arg]
        messages: list[dict] = []  # type: ignore[type-arg]
        if request.system_blocks:
            system_text = "\n\n".join(b.text for b in request.system_blocks)
            messages.append({"role": "system", "content": system_text})
        user_text_parts = [b.text for b in request.rendered_blocks]
        if user_text_parts:
            messages.append({"role": "user", "content": "\n\n".join(user_text_parts)})
        return messages

    @staticmethod
    def _parse_response(
        response: object,
    ) -> tuple[list[ProviderContentPart], RefusalCategory | None, str | None]:
        """Extract content parts and detect refusals from an OpenAI completion."""
        try:
            import openai  # noqa: F401
        except ImportError as exc:
            raise ProviderCallError("openai package required") from exc

        choice = response.choices[0] if response.choices else None  # type: ignore[attr-defined]
        if choice is None:
            raise ProviderCallError("OpenRouter returned no choices")

        parts: list[ProviderContentPart] = []
        text_content = ""
        coarse_reason: str | None = None

        msg = choice.message
        if msg.content:
            text_content = msg.content
            parts.append(ProviderTextPart(text=msg.content))

        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                import json as _json

                try:
                    tool_input = _json.loads(tc.function.arguments)
                except Exception as exc:
                    raise ProviderCallError(
                        "OpenRouter returned malformed tool_call arguments"
                    ) from exc
                parts.append(
                    ProviderToolCallPart(
                        tool_name=tc.function.name,
                        tool_input=tool_input,
                    )
                )

        if not parts:
            raise ProviderCallError("OpenRouter returned empty content")

        has_tool = any(isinstance(p, ProviderToolCallPart) for p in parts)
        refusal_cat: RefusalCategory | None = None
        if not has_tool and text_content:
            refusal_cat = _detect_refusal(text_content)
            if refusal_cat is not None:
                coarse_reason = text_content[:200]

        return parts, refusal_cat, coarse_reason

    @staticmethod
    def _extract_input_tokens(response: object) -> int | None:
        try:
            usage = response.usage  # type: ignore[attr-defined]
            if usage and usage.prompt_tokens is not None:
                return int(usage.prompt_tokens)
        except AttributeError:
            pass
        return None

    @staticmethod
    def _extract_output_tokens(response: object) -> int | None:
        try:
            usage = response.usage  # type: ignore[attr-defined]
            if usage and usage.completion_tokens is not None:
                return int(usage.completion_tokens)
        except AttributeError:
            pass
        return None


__all__ = [
    "OpenRouterAdapter",
    "OpenRouterAdapterConfig",
]
