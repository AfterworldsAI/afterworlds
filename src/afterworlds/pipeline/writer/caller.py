"""Writer model caller protocol and default Anthropic implementation — CRD Issue 9.

The WriterModelCaller protocol is the injectable seam between the Writer service
and the underlying provider.  Unit tests substitute a fake; the default
AnthropicModelCaller wires the official Anthropic Python SDK.

Issue 9 supports exactly one provider (Anthropic Sonnet-tier).  The seam is
structured so Issue 14 (provider routing) can add a second provider without
gutting this module — a narrow, typed interface is the target, not a premature
provider-agnostic abstraction layer.
"""

from __future__ import annotations

import time
from typing import Protocol

import anthropic
from anthropic.types import (
    CacheControlEphemeralParam,
    Message,
    MessageParam,
    TextBlockParam,
)

from afterworlds.pipeline.writer.config import WriterConfig

# ---------------------------------------------------------------------------
# Payload type alias
# ---------------------------------------------------------------------------

#: Payload passed from the renderer to the caller.  Mirrors the kwargs accepted
#: by anthropic.Anthropic().messages.create(), structured as a dict so the
#: renderer and caller can be tested independently.
AnthropicMessagesPayload = dict[str, object]
"""Type alias for the Anthropic Messages API payload dict.

Keys:
    model: str — Anthropic model identifier.
    max_tokens: int — maximum output token budget.
    system: list[TextBlockParam] — system prompt content blocks.
    messages: list[MessageParam] — conversation turns (user + optional assistant).
"""


# ---------------------------------------------------------------------------
# WriterModelCaller protocol
# ---------------------------------------------------------------------------


class WriterModelCaller(Protocol):
    """Protocol for the model invocation seam.

    The default implementation (AnthropicModelCaller) calls the Anthropic
    Messages API.  Tests substitute a fake that returns a pre-configured
    anthropic.types.Message without making a network call.
    """

    def __call__(self, payload: AnthropicMessagesPayload) -> Message:
        """Invoke the model with the rendered payload and return the response.

        Args:
            payload: Rendered message payload as produced by PromptRenderer.

        Returns:
            anthropic.types.Message — the raw provider response.

        Raises:
            Any exception from the provider is allowed to propagate.  The
            Writer service wraps it in WriterPassError.
        """
        ...


# ---------------------------------------------------------------------------
# Default Anthropic implementation
# ---------------------------------------------------------------------------


class AnthropicModelCaller:
    """Default WriterModelCaller implementation wired to the Anthropic SDK.

    The API key is read at call time from the config's named env var; it is
    never stored on the instance.  This is a dev-time convenience for Issue 9.
    Issue 14 (BYOK API key management) is the production key path.

    Attributes:
        _config: WriterConfig holding the model identifier and API key source.
    """

    def __init__(self, config: WriterConfig) -> None:
        self._config = config

    def __call__(self, payload: AnthropicMessagesPayload) -> Message:
        """Call anthropic.Anthropic().messages.create() with the payload."""
        api_key = self._config.get_api_key()
        client = anthropic.Anthropic(api_key=api_key)

        system_blocks: list[TextBlockParam] = payload["system"]  # type: ignore[assignment]
        messages: list[MessageParam] = payload["messages"]  # type: ignore[assignment]
        model: str = payload["model"]  # type: ignore[assignment]
        max_tokens: int = payload["max_tokens"]  # type: ignore[assignment]

        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_blocks,
            messages=messages,
            stream=False,
        )


# ---------------------------------------------------------------------------
# Timing wrapper helper (used by WriterService)
# ---------------------------------------------------------------------------


def timed_call(
    caller: WriterModelCaller,
    payload: AnthropicMessagesPayload,
) -> tuple[Message, int]:
    """Call the model caller and return (response, latency_ms).

    Args:
        caller: The WriterModelCaller to invoke.
        payload: Rendered Anthropic Messages payload.

    Returns:
        Tuple of (Message, wall-clock latency in milliseconds).
    """
    start = time.monotonic()
    response = caller(payload)
    latency_ms = int((time.monotonic() - start) * 1000)
    return response, latency_ms


__all__ = [
    "AnthropicMessagesPayload",
    "WriterModelCaller",
    "AnthropicModelCaller",
    "timed_call",
    "CacheControlEphemeralParam",
    "Message",
    "MessageParam",
    "TextBlockParam",
]
