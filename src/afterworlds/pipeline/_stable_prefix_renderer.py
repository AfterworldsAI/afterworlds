"""Shared stable-prefix block renderer — CRD Issue 12c / 14a.

Single pure utility used by every provider-backed pass (Planner, Writer,
Input/Output Safety, Extractor, Contradiction) to render the already-built
``StablePrefix`` into the ordered list of provider-neutral content blocks
with the cache breakpoint placed on the final emitted stable block.

Canonical stable block order (Issue 12c spec):

  1. Story Bible active context
  2. Rolling Summary — omit if absent/empty
  3. Rules Package slice — omit if absent/empty
  4. Retrieval Memory — omit if empty
  5. Cache breakpoint on the FINAL emitted stable-prefix block, not on a
     fixed ordinal position, using the caller-supplied TTL.

The mode contract (``StablePrefix.system_prompt``) is intentionally NOT in
this user-message region.  Each pass continues to own its pass-specific
``system`` parameter content; passes that want the active mode contract
should add it to their own ``system`` block list.  This matches the
Planner / Writer / Safety convention already in the codebase and removes
the divergent Extractor / Contradiction placement that previously included
``system_prompt`` as a stable-prefix user block.

Issue 14a rendering seam (Case 2 — formalized in this module):
  ``render_stable_prefix_blocks`` returns ``list[RenderedBlock]`` — a
  provider-neutral type carrying text + cache-breakpoint signal.  Adapters
  realize provider-specific cache markers from the breakpoint signal;
  adapters never choose breakpoint placement and never re-render context.
  Record in PR Architecture Notes: "formalized renderer output type in shared
  rendering module."

This module is a pure callable.  It performs no Context Builder calls, holds
no sessions, makes no orchestration decisions, and never mutates its inputs.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from afterworlds.models.context import (
    StablePrefix,
    _render_retrieval_memory,
    _render_rule_slice,
    _render_story_bible_context,
)

# ---------------------------------------------------------------------------
# Public TTL aliases
# ---------------------------------------------------------------------------

#: Caller-supplied TTL marker.  Matches the Anthropic ephemeral cache TTL set
#: that passes already use.  Extended TTL (1h) is the default architectural
#: choice (CRD Item 14 invariant #9).
StablePrefixTTL = Literal["1h", "5m"]

TTL_EXTENDED: StablePrefixTTL = "1h"
TTL_DEFAULT: StablePrefixTTL = "5m"


# ---------------------------------------------------------------------------
# RenderedBlock — provider-neutral stable-prefix block (Issue 14a, Case 2)
# ---------------------------------------------------------------------------


class RenderedBlock(BaseModel):
    """Provider-neutral stable-prefix block produced by the shared renderer.

    Adapters realize provider-specific cache markers from ``has_cache_breakpoint``
    and ``ttl``.  They never choose breakpoint placement or re-render content.

    Attributes:
        text: The plain-text content for this block.
        has_cache_breakpoint: True for the final stable-prefix block that
            carries the cache breakpoint signal.  Only one block per rendered
            list will have this set.
        ttl: Cache TTL intent, populated only when ``has_cache_breakpoint`` is
            True.  Anthropic adapters realize this as ``cache_control`` with the
            given TTL; other adapters may ignore or map it as appropriate.
    """

    model_config = ConfigDict(extra="forbid")

    text: str
    has_cache_breakpoint: bool = False
    ttl: StablePrefixTTL | None = None


# ---------------------------------------------------------------------------
# Public render contract
# ---------------------------------------------------------------------------


def collect_stable_prefix_texts(stable_prefix: StablePrefix) -> list[str]:
    """Return the canonical stable-prefix block texts in canonical order.

    Sections absent on the supplied ``StablePrefix`` are omitted entirely so
    the cache key does not include a placeholder block and the breakpoint
    naturally lands on the last present section.

    Args:
        stable_prefix: already-built stable prefix produced once per turn by
            the Context Builder (Issue 8).  Never mutated.

    Returns:
        Ordered list of plain-text section bodies for the user-message
        stable region: Story Bible, optional Rolling Summary, optional Rules
        Package slice, optional Retrieval Memory.
    """
    texts: list[str] = [_render_story_bible_context(stable_prefix.story_bible_context)]

    if stable_prefix.rolling_summary_text is not None:
        texts.append(stable_prefix.rolling_summary_text)

    if stable_prefix.rules_package_slice is not None:
        texts.append(_render_rule_slice(stable_prefix.rules_package_slice))

    retrieval_text = _render_retrieval_memory(stable_prefix.retrieval_memory)
    if retrieval_text:
        texts.append(retrieval_text)

    return texts


def render_stable_prefix_blocks(
    stable_prefix: StablePrefix,
    ttl: StablePrefixTTL = TTL_EXTENDED,
) -> list[RenderedBlock]:
    """Return the user-message stable-prefix content blocks for one pass.

    Wraps :func:`collect_stable_prefix_texts` and marks the cache breakpoint
    on the final emitted block via ``has_cache_breakpoint=True`` and the
    caller-supplied ``ttl``.  When the collected text list is empty (which
    would only occur for an unusual empty Story Bible), the returned block
    list is also empty.

    Adapters read ``has_cache_breakpoint`` and ``ttl`` to apply
    provider-specific cache markers.  The orchestrator's surrounding
    pass-specific blocks (system parameter, PassForwardLedger, volatile suffix,
    evaluated text, etc.) are not produced here — each pass owns those.

    Args:
        stable_prefix: already-built stable prefix from the Context Builder.
        ttl: caller-supplied ephemeral cache TTL.  Defaults to extended 1h
            per CRD Item 14 invariant #9.

    Returns:
        Ordered list of ``RenderedBlock`` ready to include in a
        ``ProviderCallRequest``.
    """
    texts = collect_stable_prefix_texts(stable_prefix)
    if not texts:
        return []

    blocks: list[RenderedBlock] = []
    for text in texts[:-1]:
        blocks.append(RenderedBlock(text=text))
    blocks.append(RenderedBlock(text=texts[-1], has_cache_breakpoint=True, ttl=ttl))
    return blocks
