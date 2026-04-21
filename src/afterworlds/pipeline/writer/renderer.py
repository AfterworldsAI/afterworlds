"""Prompt renderer for the Writer pass — CRD Issue 9.

Transforms an AssembledContext into an Anthropic Messages API payload per the
rendering structure fixed in Issue 9:

  1. System prompt + mode contract → ``system`` parameter as a list of
     TextBlockParam content blocks.
  2. Stable-prefix sections → ordered content blocks in the first user message,
     in the canonical Issue 8 order:
       a. Story Bible active context
       b. Rolling Summary (omitted cleanly if absent — no placeholder block)
       c. Rules Package slice (omitted if absent)
       d. Retrieval Memory (omitted when empty; named seam field is always
          present on StablePrefix per Issue 8's contract, but an empty payload
          produces no content block)
  3. Cache breakpoint → ``cache_control: {"type": "ephemeral", "ttl": "1h"}``
     on the FINAL stable-prefix content block.  This is the authoritative
     architectural boundary.  Nothing in the PassForwardLedger or
     VolatileSuffix is inside the cacheable region.
  4. PassForwardLedger → content blocks after the cache breakpoint; present
     when non-empty (Issue 9 always produces an empty ledger; Issues 10–12
     populate it without rewriting this renderer).
  5. VolatileSuffix → content blocks last, after the ledger, carrying no
     cache_control marker:
       a. Recent turns verbatim (one block per turn pair)
       b. Current Sojourner input
       c. Structured intent classification block

This renderer is single-provider by design in Issue 9.  Issue 14 reopens
provider routing; the interface is narrow and typed so a second provider can be
wired without gutting this module.
"""

from __future__ import annotations

from typing import Literal

from anthropic.types import (
    CacheControlEphemeralParam,
    MessageParam,
    TextBlockParam,
)

from afterworlds.models.context import (
    AssembledContext,
    _render_retrieval_memory,
    _render_rule_slice,
    _render_story_bible_context,
)
from afterworlds.pipeline.writer.caller import AnthropicMessagesPayload
from afterworlds.pipeline.writer.config import WriterConfig

# ---------------------------------------------------------------------------
# TTL constants
# ---------------------------------------------------------------------------

_TTL_EXTENDED: Literal["1h"] = "1h"
_TTL_DEFAULT: Literal["5m"] = "5m"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_cache_control(extended_ttl: bool) -> CacheControlEphemeralParam:
    """Return a CacheControlEphemeralParam with the correct TTL setting."""
    if extended_ttl:
        return CacheControlEphemeralParam(type="ephemeral", ttl=_TTL_EXTENDED)
    return CacheControlEphemeralParam(type="ephemeral", ttl=_TTL_DEFAULT)


def _text_block(text: str) -> TextBlockParam:
    """Return a plain TextBlockParam (no cache_control)."""
    return TextBlockParam(type="text", text=text)


def _cached_text_block(text: str, extended_ttl: bool) -> TextBlockParam:
    """Return a TextBlockParam with a cache breakpoint marker."""
    return TextBlockParam(
        type="text",
        text=text,
        cache_control=_make_cache_control(extended_ttl),
    )


def _render_intent_block(assembled: AssembledContext) -> str:
    """Render the intent classification as a compact structured block.

    The intent is rendered as a structured (not prose) block so downstream
    pipeline passes can parse the classification contract without ambiguity.
    This matches the Issue 9 requirement: "a compact structured block that
    preserves the typed contract" — not stringified into prose.
    """
    icr = assembled.volatile_suffix.classified_intent
    lines = [
        "[INTENT CLASSIFICATION]",
        f"intent_type: {icr.intent_type.value}",
        f"confidence: {icr.confidence:.3f}",
        f"ambiguous: {icr.ambiguous}",
    ]
    if icr.secondary_intent is not None:
        lines.append(f"secondary_intent: {icr.secondary_intent.value}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PromptRenderer
# ---------------------------------------------------------------------------


class PromptRenderer:
    """Renders an AssembledContext into an Anthropic Messages API payload.

    The rendering structure is fixed per the Issue 9 spec.  The renderer is
    instantiated once and reused across calls; it holds no mutable state.

    Args:
        config: WriterConfig controlling the model identifier, TTL mode, etc.
    """

    def __init__(self, config: WriterConfig) -> None:
        self._config = config

    def render(self, assembled: AssembledContext) -> AnthropicMessagesPayload:
        """Render an AssembledContext into an Anthropic Messages API payload.

        Cache breakpoint sits on the final stable-prefix content block.
        PassForwardLedger blocks (when non-empty) appear after the breakpoint.
        VolatileSuffix blocks appear last with no cache_control marker.

        Args:
            assembled: The full assembled context for this pipeline turn.

        Returns:
            AnthropicMessagesPayload dict ready to pass to the caller.
        """
        system_blocks = self._render_system(assembled)
        user_content = self._render_user_message(assembled)

        return {
            "model": self._config.model,
            "max_tokens": 4096,
            "system": system_blocks,
            "messages": [MessageParam(role="user", content=user_content)],
        }

    def _render_system(self, assembled: AssembledContext) -> list[TextBlockParam]:
        """Render the system parameter: system prompt + mode contract.

        The system prompt is rendered as a list of content blocks, matching the
        Anthropic API's preferred format for prompt caching.  A cache_control
        marker on the last system block is acceptable per the Issue 9 spec as
        an API-level implementation detail, but it is NOT the authoritative
        architectural cache boundary — that sits on the final stable-prefix
        user message block.
        """
        return [_text_block(assembled.stable_prefix.system_prompt)]

    def _render_user_message(self, assembled: AssembledContext) -> list[TextBlockParam]:
        """Render all user message content blocks in canonical order."""
        blocks: list[TextBlockParam] = []
        stable_texts: list[str] = self._collect_stable_prefix_texts(assembled)

        # Place cache breakpoint on the last stable-prefix block.
        if stable_texts:
            for text in stable_texts[:-1]:
                blocks.append(_text_block(text))
            blocks.append(
                _cached_text_block(stable_texts[-1], self._config.extended_ttl)
            )

        # PassForwardLedger — after the cache breakpoint; empty in Issue 9.
        ledger_text = assembled.pass_forward_ledger.render()
        if ledger_text:
            blocks.append(_text_block(ledger_text))

        # VolatileSuffix — recent turns, then current input, then intent.
        for turn in assembled.volatile_suffix.recent_turns:
            blocks.append(
                _text_block(
                    f"Player: {turn.user_input}\n" f"Narrator: {turn.assistant_output}"
                )
            )
        blocks.append(_text_block(assembled.volatile_suffix.current_input))
        blocks.append(_text_block(_render_intent_block(assembled)))

        return blocks

    def _collect_stable_prefix_texts(self, assembled: AssembledContext) -> list[str]:
        """Return stable-prefix section texts in canonical Issue 8 order.

        Sections that are absent are omitted entirely — no placeholder block
        that would pollute the cache key or shift the breakpoint position.

        Order:
          1. Story Bible active context
          2. Rolling Summary (omitted if None)
          3. Rules Package slice (omitted if None)
          4. Retrieval Memory (omitted when empty)
        """
        texts: list[str] = []
        sp = assembled.stable_prefix

        texts.append(_render_story_bible_context(sp.story_bible_context))

        if sp.rolling_summary_text is not None:
            texts.append(sp.rolling_summary_text)

        if sp.rules_package_slice is not None:
            texts.append(_render_rule_slice(sp.rules_package_slice))

        retrieval_text = _render_retrieval_memory(sp.retrieval_memory)
        if retrieval_text:
            texts.append(retrieval_text)

        return texts
