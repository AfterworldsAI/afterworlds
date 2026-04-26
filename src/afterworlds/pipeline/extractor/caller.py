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

EXTRACT_TOOL_NAME: str = "propose_canon_updates"

_SOFT_TRANSIENT_PROPERTIES: dict[str, Any] = {
    "target_domain": {
        "type": "string",
        "enum": ["character", "world", "relationship"],
        "description": "Entity domain the update targets.",
    },
    "target_natural_key": {
        "type": "string",
        "description": (
            "Character name for the 'character' domain; "
            "'<Subject> -> <Object>' for the 'relationship' domain."
        ),
    },
    "target_field": {
        "type": "string",
        "description": (
            "Field to update.  "
            "Character allowlist: current_location, current_status, is_alive, notes.  "
            "Relationship allowlist: current_status_description."
        ),
    },
    "proposed_value": {
        "oneOf": [{"type": "string"}, {"type": "boolean"}],
        "description": (
            "New field value. "
            "Use a string for text fields (current_location, current_status, notes); "
            "use a JSON boolean (true/false) for is_alive."
        ),
    },
    "rationale": {
        "type": "string",
        "description": "Why this change is warranted.",
    },
}

_SOFT_TRANSIENT_REQUIRED: list[str] = [
    "kind",
    "target_domain",
    "target_natural_key",
    "target_field",
    "proposed_value",
]

#: Tool specification passed to the Anthropic API.
EXTRACT_TOOL_SPEC: dict[str, Any] = {
    "name": EXTRACT_TOOL_NAME,
    "description": (
        "Report all narrative canon updates proposed for this turn as a single "
        "discriminated-union array.  Call this tool exactly once.  Use an empty "
        "proposals array when nothing was extracted."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "proposals": {
                "type": "array",
                "description": "All narrative canon updates proposed for this turn.",
                "items": {
                    "oneOf": [
                        {
                            "type": "object",
                            "description": (
                                "An irreversible fact established this beat.  "
                                "Requires Sojourner confirmation before becoming canon."
                            ),
                            "properties": {
                                "kind": {"type": "string", "const": "locked_fact"},
                                "fact_text": {
                                    "type": "string",
                                    "description": (
                                        "The irreversible fact, stated plainly."
                                    ),
                                },
                                "rationale": {
                                    "type": "string",
                                    "description": "Why this fact is irreversible.",
                                },
                            },
                            "required": ["kind", "fact_text"],
                        },
                        {
                            "type": "object",
                            "description": (
                                "A character or world state change proposed with a "
                                "low-confidence flag for Sojourner review."
                            ),
                            "properties": {
                                "kind": {"type": "string", "const": "soft_fact"},
                                **_SOFT_TRANSIENT_PROPERTIES,
                            },
                            "required": _SOFT_TRANSIENT_REQUIRED,
                        },
                        {
                            "type": "object",
                            "description": (
                                "A volatile state change that auto-commits immediately "
                                "without a Sojourner review flag."
                            ),
                            "properties": {
                                "kind": {"type": "string", "const": "transient_state"},
                                **_SOFT_TRANSIENT_PROPERTIES,
                            },
                            "required": _SOFT_TRANSIENT_REQUIRED,
                        },
                        {
                            "type": "object",
                            "description": (
                                "A new unresolved plot thread introduced this beat."
                            ),
                            "properties": {
                                "kind": {
                                    "type": "string",
                                    "const": "unresolved_thread",
                                },
                                "description": {
                                    "type": "string",
                                    "description": (
                                        "Brief description of the open thread."
                                    ),
                                },
                                "rationale": {"type": "string"},
                            },
                            "required": ["kind", "description"],
                        },
                        {
                            "type": "object",
                            "description": (
                                "A significant narrative moment for the Events Ledger."
                            ),
                            "properties": {
                                "kind": {"type": "string", "const": "event"},
                                "event_kind": {
                                    "type": "string",
                                    "enum": [
                                        "location_change",
                                        "inventory_gain",
                                        "inventory_loss",
                                        "npc_introduction",
                                        "status_change",
                                        "relationship_change",
                                        "scene_transition",
                                        "plot_reveal",
                                        "oath_or_promise",
                                        "death",
                                        "routine",
                                    ],
                                    "description": (
                                        "Functional classification of the event."
                                    ),
                                },
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
                                    "description": (
                                        "Significance for tiered inclusion policy."
                                    ),
                                },
                                "related_entity_natural_keys": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": (
                                        "Character names or 'Subject -> Object' keys "
                                        "involved in this event."
                                    ),
                                },
                                "rationale": {"type": "string"},
                            },
                            "required": [
                                "kind",
                                "event_kind",
                                "description",
                                "significance",
                            ],
                        },
                    ]
                },
            }
        },
        "required": ["proposals"],
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

    matching = [
        block
        for block in response.content
        if isinstance(block, ToolUseBlock) and block.name == EXTRACT_TOOL_NAME
    ]
    if not matching:
        raise ExtractorPassError(
            f"Provider response contains no '{EXTRACT_TOOL_NAME}' tool-use block. "
            "stop_reason was: "
            f"{getattr(response, 'stop_reason', '<unknown>')!r}"
        )
    if len(matching) > 1:
        raise ExtractorPassError(
            f"Provider response contains {len(matching)} '{EXTRACT_TOOL_NAME}' "
            "tool-use blocks; expected exactly one."
        )
    raw: Any = matching[0].input
    if not isinstance(raw, dict):
        raise ExtractorPassError(f"Tool input is not a dict; got {type(raw).__name__}")
    return raw


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
