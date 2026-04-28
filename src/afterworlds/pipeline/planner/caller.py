"""Planner model caller protocol and default Anthropic implementation.

CRD Issue 12a.  The Planner pass uses Anthropic tool use to obtain a
structured ``PlannerOutput``.
``tool_choice={"type": "tool", "name": PRODUCE_PLAN_TOOL_NAME}`` forces the
model to always call the plan tool, eliminating prose-parsing ambiguity.
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
from afterworlds.pipeline.planner.config import PlannerConfig

# ---------------------------------------------------------------------------
# Tool specification
# ---------------------------------------------------------------------------

PRODUCE_PLAN_TOOL_NAME: str = "produce_plan"

PRODUCE_PLAN_TOOL_SPEC: dict[str, Any] = {
    "name": PRODUCE_PLAN_TOOL_NAME,
    "description": (
        "Produce a structured plan for the Writer pass: scene goal, next beat,"
        " facts needed, and optional notes. Call this tool exactly once."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "scene_goal": {
                "type": "string",
                "description": (
                    "The overarching goal for the current scene — what the"
                    " narrative is trying to accomplish this turn. Non-empty."
                ),
            },
            "next_beat": {
                "type": "string",
                "description": (
                    "The specific next story beat the Writer should deliver:"
                    " one concrete narrative event or moment. Non-empty."
                ),
            },
            "facts_needed": {
                "type": "array",
                "description": (
                    "Story Bible facts the Writer must respect when writing"
                    " this beat. Empty array when no specific facts are"
                    " critical beyond general canon."
                ),
                "items": {"type": "string"},
            },
            "notes": {
                "type": "string",
                "description": (
                    "Optional guidance to the Writer: tone, pacing, or"
                    " constraints not captured elsewhere. Omit the field"
                    " (or pass null) when there is nothing to add."
                ),
            },
        },
        "required": ["scene_goal", "next_beat", "facts_needed"],
    },
}

# ---------------------------------------------------------------------------
# Payload type alias
# ---------------------------------------------------------------------------

PlannerPayload = dict[str, object]


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


class PlannerModelCaller(Protocol):
    """Protocol for the Planner pass model invocation seam."""

    def __call__(self, payload: PlannerPayload) -> Message:
        """Invoke the model with the planner payload and return the response."""
        ...


# ---------------------------------------------------------------------------
# Default Anthropic implementation
# ---------------------------------------------------------------------------


class AnthropicPlannerCaller:
    """Default PlannerModelCaller wired to the Anthropic Python SDK.

    Forces tool use via ``tool_choice={"type": "tool", "name": ...}`` so the
    model always returns a structured ToolUseBlock rather than prose.
    """

    def __init__(self, config: PlannerConfig) -> None:
        self._config = config

    def __call__(self, payload: PlannerPayload) -> Message:
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
    caller: PlannerModelCaller,
    payload: PlannerPayload,
) -> tuple[Message, int]:
    """Call the model caller and return (response, latency_ms)."""
    start = time.monotonic()
    response = caller(payload)
    latency_ms = int((time.monotonic() - start) * 1000)
    return response, latency_ms


def parse_tool_input(response: Message) -> dict[str, Any]:
    """Extract the tool-use input dict from an Anthropic Message.

    Delegates to the shared ``parse_tool_use_block`` utility and wraps any
    ``ValueError`` as a ``PlannerPassError``.

    Raises:
        PlannerPassError: if no matching tool-use block is found or the
            response envelope is malformed.
    """
    from afterworlds.pipeline.planner.models import PlannerPassError

    try:
        return parse_tool_use_block(response, PRODUCE_PLAN_TOOL_NAME)
    except ValueError as exc:
        raise PlannerPassError(str(exc)) from exc


__all__ = [
    "PRODUCE_PLAN_TOOL_NAME",
    "PRODUCE_PLAN_TOOL_SPEC",
    "PlannerPayload",
    "PlannerModelCaller",
    "AnthropicPlannerCaller",
    "timed_call",
    "parse_tool_input",
    "TextBlockParam",
    "MessageParam",
]
