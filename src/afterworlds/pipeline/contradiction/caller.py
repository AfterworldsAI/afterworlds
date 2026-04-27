"""Contradiction model caller protocol and default Anthropic implementation.

CRD Issue 11.  The Contradiction pass uses Anthropic tool use to obtain a
structured ``ContradictionReport``.
``tool_choice={"type": "tool", "name": REPORT_TOOL_NAME}`` forces the model
to always call the report tool, eliminating prose-parsing ambiguity.
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
)

from afterworlds.pipeline._tool_use import parse_tool_use_block
from afterworlds.pipeline.contradiction.config import ContradictionConfig

# ---------------------------------------------------------------------------
# Tool specification
# ---------------------------------------------------------------------------

REPORT_TOOL_NAME: str = "report_contradictions"

#: Flat violations array — no discriminated union needed for the Contradiction pass.
REPORT_TOOL_SPEC: dict[str, Any] = {
    "name": REPORT_TOOL_NAME,
    "description": (
        "Report all contradictions found between the Writer's prose and the"
        " Story Bible. Call this tool exactly once.  Use an empty violations"
        " array when the prose is clear."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "violations": {
                "type": "array",
                "description": (
                    "Every contradiction found between the Writer's prose"
                    " and the Story Bible. Use an empty array when the"
                    " prose is clear."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": [
                                "dead_character_acting",
                                "item_never_acquired",
                                "locked_fact_violated",
                                "location_drift",
                                "name_drift",
                                "pov_tense_shift",
                                "other",
                            ],
                            "description": (
                                "Functional classification of the contradiction."
                            ),
                        },
                        "description": {
                            "type": "string",
                            "description": (
                                "What the prose says, stated plainly.  Non-empty."
                            ),
                        },
                        "canon_reference": {
                            "type": "string",
                            "description": (
                                "The specific Story Bible fact that is"
                                " violated.  Non-empty."
                            ),
                        },
                    },
                    "required": ["category", "description", "canon_reference"],
                },
            }
        },
        "required": ["violations"],
    },
}

# ---------------------------------------------------------------------------
# Payload type alias
# ---------------------------------------------------------------------------

ContradictionPayload = dict[str, object]


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class ContradictionModelCaller(Protocol):
    """Protocol for the Contradiction pass model invocation seam."""

    def __call__(self, payload: ContradictionPayload) -> Message:
        """Invoke the model with the contradiction payload and return the response."""
        ...


# ---------------------------------------------------------------------------
# Default Anthropic implementation
# ---------------------------------------------------------------------------


class AnthropicContradictionCaller:
    """Default ContradictionModelCaller wired to the Anthropic Python SDK.

    Forces tool use via ``tool_choice={"type": "tool", "name": ...}`` so the
    model always returns a structured ToolUseBlock rather than prose.
    """

    def __init__(self, config: ContradictionConfig) -> None:
        self._config = config

    def __call__(self, payload: ContradictionPayload) -> Message:
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
    caller: ContradictionModelCaller,
    payload: ContradictionPayload,
) -> tuple[Message, int]:
    """Call the model caller and return (response, latency_ms)."""
    start = time.monotonic()
    response = caller(payload)
    latency_ms = int((time.monotonic() - start) * 1000)
    return response, latency_ms


def parse_tool_input(response: Message) -> dict[str, Any]:
    """Extract the tool-use input dict from an Anthropic Message.

    Delegates to the shared ``parse_tool_use_block`` utility and wraps any
    ``ValueError`` as a ``ContradictionPassError``.

    Raises:
        ContradictionPassError: if no matching tool-use block is found or the
            response envelope is malformed.
    """
    from afterworlds.pipeline.contradiction.models import ContradictionPassError

    try:
        return parse_tool_use_block(response, REPORT_TOOL_NAME)
    except ValueError as exc:
        raise ContradictionPassError(str(exc)) from exc


__all__ = [
    "REPORT_TOOL_NAME",
    "REPORT_TOOL_SPEC",
    "ContradictionPayload",
    "ContradictionModelCaller",
    "AnthropicContradictionCaller",
    "timed_call",
    "parse_tool_input",
    "CacheControlEphemeralParam",
    "TextBlockParam",
    "MessageParam",
]
