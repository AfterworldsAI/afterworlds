"""Safety pass model caller protocol and default Anthropic implementation.

CRD Issue 12b.  The Safety pass uses Anthropic tool use to obtain a structured
``SafetyReport``.  ``tool_choice={"type": "tool", "name": REPORT_SAFETY_TOOL_NAME}``
forces the model to always call the assessment tool, eliminating prose-parsing
ambiguity.
"""

from __future__ import annotations

import time
from typing import Any, Protocol

import anthropic
from anthropic.types import (
    Message,
    MessageParam,
    TextBlockParam,
)

from afterworlds.pipeline._tool_use import parse_tool_use_block
from afterworlds.pipeline.safety.config import SafetyConfig

# ---------------------------------------------------------------------------
# Tool specification
# ---------------------------------------------------------------------------

REPORT_SAFETY_TOOL_NAME: str = "report_safety_assessment"

REPORT_SAFETY_TOOL_SPEC: dict[str, Any] = {
    "name": REPORT_SAFETY_TOOL_NAME,
    "description": (
        "Report the safety assessment for the evaluated text. "
        "Call this tool exactly once. "
        "Pass an empty concerns array when no threshold is clearly crossed."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "concerns": {
                "type": "array",
                "description": (
                    "List of safety concerns identified in the text. "
                    "Empty array when the text is safe."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": [
                                "SEXUAL_MINOR",
                                "REAL_PERSON_TARGETED_HARM",
                                "HATE_TARGETED",
                                "SELF_HARM_INSTRUCTIONAL",
                                "DANGEROUS_OPERATIONAL",
                                "OTHER",
                            ],
                            "description": (
                                "The safety category this concern falls under."
                            ),
                        },
                        "description": {
                            "type": "string",
                            "description": (
                                "Brief explanation of why this is a concern."
                            ),
                        },
                        "evidence_summary": {
                            "type": "string",
                            "description": (
                                "Direct quote or precise paraphrase of the offending "
                                "content. Must be ≤ 300 characters."
                            ),
                        },
                    },
                    "required": ["category", "description", "evidence_summary"],
                },
            },
        },
        "required": ["concerns"],
    },
}

# ---------------------------------------------------------------------------
# Payload type alias
# ---------------------------------------------------------------------------

SafetyPayload = dict[str, object]


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class SafetyModelCaller(Protocol):
    """Protocol for the Safety pass model invocation seam."""

    def __call__(self, payload: SafetyPayload) -> Message:
        """Invoke the model with the safety payload and return the response."""
        ...


# ---------------------------------------------------------------------------
# Default Anthropic implementation
# ---------------------------------------------------------------------------


class AnthropicSafetyCaller:
    """Default SafetyModelCaller wired to the Anthropic Python SDK."""

    def __init__(self, config: SafetyConfig) -> None:
        self._config = config

    def __call__(self, payload: SafetyPayload) -> Message:
        api_key = self._config.get_api_key()
        client = anthropic.Anthropic(api_key=api_key)

        system_blocks: list[TextBlockParam] = payload["system"]  # type: ignore[assignment]
        messages: list[MessageParam] = payload["messages"]  # type: ignore[assignment]
        model: str = payload["model"]  # type: ignore[assignment]
        max_tokens: int = payload["max_tokens"]  # type: ignore[assignment]
        tools: list[Any] = payload["tools"]  # type: ignore[assignment]
        tool_choice: dict[str, Any] = payload["tool_choice"]  # type: ignore[assignment]

        return client.messages.create(  # type: ignore[call-overload, no-any-return]
            model=model,
            max_tokens=max_tokens,
            system=system_blocks,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            stream=False,
        )


# ---------------------------------------------------------------------------
# Timing wrapper and response parsing
# ---------------------------------------------------------------------------


def timed_call(
    caller: SafetyModelCaller,
    payload: SafetyPayload,
) -> tuple[Message, int]:
    """Call the model caller and return (response, latency_ms)."""
    start = time.monotonic()
    response = caller(payload)
    latency_ms = int((time.monotonic() - start) * 1000)
    return response, latency_ms


def parse_tool_input(response: Message) -> dict[str, Any]:
    """Extract the tool-use input dict from an Anthropic Message.

    Raises:
        SafetyPassError: if no matching tool-use block is found or the
            response envelope is malformed.
    """
    from afterworlds.pipeline.safety.models import SafetyPassError

    try:
        return parse_tool_use_block(response, REPORT_SAFETY_TOOL_NAME)
    except ValueError as exc:
        raise SafetyPassError(str(exc), cause=exc) from exc


__all__ = [
    "REPORT_SAFETY_TOOL_NAME",
    "REPORT_SAFETY_TOOL_SPEC",
    "SafetyPayload",
    "SafetyModelCaller",
    "AnthropicSafetyCaller",
    "timed_call",
    "parse_tool_input",
    "TextBlockParam",
    "MessageParam",
]
