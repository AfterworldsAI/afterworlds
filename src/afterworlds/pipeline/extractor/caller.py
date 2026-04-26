"""Extractor model caller protocol and default Anthropic implementation — CRD Issue 10.

The Extractor uses Anthropic tool use to obtain structured proposal output.
``tool_choice={"type": "tool", "name": EXTRACT_TOOL_NAME}`` forces the model
to always call the extraction tool, eliminating prose-parsing ambiguity.
"""

from __future__ import annotations

import time
from typing import Any, Protocol

import anthropic
from anthropic.types import (
    CacheControlEphemeralParam,
    Message,
    MessageParam,
    TextBlockParam,
    ToolUseBlock,
)

from afterworlds.pipeline.extractor.config import ExtractorConfig

# ---------------------------------------------------------------------------
# Tool specification
# ---------------------------------------------------------------------------

EXTRACT_TOOL_NAME: str = "propose_story_bible_updates"

#: Tool specification passed to the Anthropic API.
EXTRACT_TOOL_SPEC: dict[str, Any] = {
    "name": EXTRACT_TOOL_NAME,
    "description": (
        "Report all narrative canon updates proposed for this turn. "
        "Call this tool exactly once, reporting every update you identify. "
        "Use empty arrays for categories where nothing was found."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "locked_facts": {
                "type": "array",
                "description": (
                    "Irreversible facts established in this beat that require "
                    "Sojourner confirmation before becoming permanent canon."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "fact_text": {
                            "type": "string",
                            "description": "The irreversible fact, stated plainly.",
                        }
                    },
                    "required": ["fact_text"],
                },
            },
            "soft_facts": {
                "type": "array",
                "description": (
                    "Character or world state changes that auto-commit with a "
                    "low-confidence flag so the Sojourner can review them."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "character_name": {
                            "type": "string",
                            "description": (
                                "Exact character name from the Story Bible cast list."
                            ),
                        },
                        "field_name": {
                            "type": "string",
                            "enum": [
                                "current_location",
                                "current_status",
                                "is_alive",
                                "notes",
                            ],
                            "description": "Which dynamic field changed.",
                        },
                        "new_value": {
                            "description": "The new field value.",
                        },
                    },
                    "required": ["character_name", "field_name", "new_value"],
                },
            },
            "transient_states": {
                "type": "array",
                "description": (
                    "Volatile state changes (current location, active quest, etc.) "
                    "that auto-commit immediately without a review flag."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "character_name": {
                            "type": "string",
                            "description": (
                                "Exact character name from the Story Bible cast list."
                            ),
                        },
                        "field_name": {
                            "type": "string",
                            "enum": [
                                "current_location",
                                "current_status",
                                "is_alive",
                                "notes",
                            ],
                            "description": "Which dynamic field changed.",
                        },
                        "new_value": {
                            "description": "The new field value.",
                        },
                    },
                    "required": ["character_name", "field_name", "new_value"],
                },
            },
            "unresolved_threads": {
                "type": "array",
                "description": (
                    "New plot threads or open questions introduced in the prose "
                    "that are not resolved within this beat."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Brief description of the open thread.",
                        }
                    },
                    "required": ["description"],
                },
            },
            "events": {
                "type": "array",
                "description": "Significant narrative moments for the Events Ledger.",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "What happened, stated plainly.",
                        },
                        "significance": {
                            "type": "string",
                            "enum": [
                                "routine",
                                "character_death",
                                "locked_fact_established",
                                "major_plot_turn",
                                "relationship_change",
                                "world_state_change",
                                "forbidden_fact_established",
                            ],
                            "description": "Significance for tiered inclusion policy.",
                        },
                    },
                    "required": ["description", "significance"],
                },
            },
        },
        "required": [],
    },
}

# ---------------------------------------------------------------------------
# Payload type alias
# ---------------------------------------------------------------------------

ExtractorPayload = dict[str, object]


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class ExtractorModelCaller(Protocol):
    """Protocol for the Extractor model invocation seam."""

    def __call__(self, payload: ExtractorPayload) -> Message:
        """Invoke the model with the extraction payload and return the response."""
        ...


# ---------------------------------------------------------------------------
# Default Anthropic implementation
# ---------------------------------------------------------------------------


class AnthropicExtractorCaller:
    """Default ExtractorModelCaller wired to the Anthropic Python SDK.

    Forces tool use via ``tool_choice={"type": "tool", "name": ...}`` so the
    model always returns a structured ToolUseBlock rather than prose.
    """

    def __init__(self, config: ExtractorConfig) -> None:
        self._config = config

    def __call__(self, payload: ExtractorPayload) -> Message:
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
# Timing wrapper
# ---------------------------------------------------------------------------


def timed_call(
    caller: ExtractorModelCaller,
    payload: ExtractorPayload,
) -> tuple[Message, int]:
    """Call the model caller and return (response, latency_ms)."""
    start = time.monotonic()
    response = caller(payload)
    latency_ms = int((time.monotonic() - start) * 1000)
    return response, latency_ms


def parse_tool_input(response: Message) -> dict[str, Any]:
    """Extract the tool-use input dict from an Anthropic Message.

    Scans the content blocks for a ToolUseBlock whose name matches
    ``EXTRACT_TOOL_NAME`` and returns its ``input`` dict.

    Raises:
        ExtractorPassError: if no matching tool-use block is found or the
            response envelope is malformed.
    """
    from afterworlds.pipeline.extractor.models import ExtractorPassError

    if not isinstance(response, Message):
        raise ExtractorPassError(
            f"Unexpected response type from provider: {type(response).__name__}"
        )

    for block in response.content:
        if isinstance(block, ToolUseBlock) and block.name == EXTRACT_TOOL_NAME:
            raw: Any = block.input
            if not isinstance(raw, dict):
                raise ExtractorPassError(
                    f"Tool input is not a dict; got {type(raw).__name__}"
                )
            return raw

    raise ExtractorPassError(
        f"Provider response contains no '{EXTRACT_TOOL_NAME}' tool-use block. "
        "stop_reason was: "
        f"{getattr(response, 'stop_reason', '<unknown>')!r}"
    )


__all__ = [
    "EXTRACT_TOOL_NAME",
    "EXTRACT_TOOL_SPEC",
    "ExtractorPayload",
    "ExtractorModelCaller",
    "AnthropicExtractorCaller",
    "timed_call",
    "parse_tool_input",
    "CacheControlEphemeralParam",
    "TextBlockParam",
    "MessageParam",
]
