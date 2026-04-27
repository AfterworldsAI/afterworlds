"""Shared tool-use response parser for Anthropic structured-output passes.

Extracted from extractor/caller.py so that the Contradiction pass (and future
passes) can reuse the same parse logic without forking it.
"""

from __future__ import annotations

from typing import Any

from anthropic.types import Message, ToolUseBlock


def parse_tool_use_block(response: Message, tool_name: str) -> dict[str, Any]:
    """Extract the tool-use input dict from an Anthropic Message.

    Scans the content blocks for a ToolUseBlock whose name matches *tool_name*
    and returns its ``input`` dict.

    Args:
        response: The Anthropic Message returned by the API.
        tool_name: The expected tool name to match.

    Raises:
        ValueError: if no matching tool-use block is found, if multiple
            matching blocks are found, or if the input is not a dict.
    """
    if not isinstance(response, Message):
        raise ValueError(
            f"Unexpected response type from provider: {type(response).__name__}"
        )

    matching = [
        block
        for block in response.content
        if isinstance(block, ToolUseBlock) and block.name == tool_name
    ]
    if not matching:
        raise ValueError(
            f"Provider response contains no '{tool_name}' tool-use block. "
            "stop_reason was: "
            f"{getattr(response, 'stop_reason', '<unknown>')!r}"
        )
    if len(matching) > 1:
        raise ValueError(
            f"Provider response contains {len(matching)} '{tool_name}' "
            "tool-use blocks; expected exactly one."
        )
    raw: Any = matching[0].input
    if not isinstance(raw, dict):
        raise ValueError(f"Tool input is not a dict; got {type(raw).__name__}")
    return raw


__all__ = ["parse_tool_use_block"]
