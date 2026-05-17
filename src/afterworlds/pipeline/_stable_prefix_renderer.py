"""Shared stable-prefix block renderer — CRD Issue 12c.

Single pure utility used by every provider-backed pass (Planner, Writer,
Input/Output Safety, Extractor, Contradiction) to render the already-built
``StablePrefix`` into the ordered list of provider-facing user-message text
blocks with the cache breakpoint placed on the final emitted stable block.

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

This module is a pure callable.  It performs no Context Builder calls, holds
no sessions, makes no orchestration decisions, and never mutates its inputs.
"""

from __future__ import annotations

from typing import Literal

from anthropic.types import (
    CacheControlEphemeralParam,
    TextBlockParam,
)

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
) -> list[TextBlockParam]:
    """Return the user-message stable-prefix content blocks for one pass.

    Wraps :func:`collect_stable_prefix_texts` and applies the cache breakpoint
    marker (``cache_control: {"type": "ephemeral", "ttl": ttl}``) to the final
    emitted block.  When the collected text list is empty (which would only
    occur for an unusual empty Story Bible), the returned block list is also
    empty and the caller's downstream payload is unaffected.

    Args:
        stable_prefix: already-built stable prefix from the Context Builder.
        ttl: caller-supplied ephemeral cache TTL.  Defaults to extended 1h
            per CRD Item 14 invariant #9.  Only changes the breakpoint TTL;
            the stable block text and order are independent of this value.

    Returns:
        Ordered list of ``TextBlockParam`` ready to insert into a provider
        payload.  Pass-specific surrounding blocks (system parameter, pass
        forward ledger, volatile suffix, evaluated text, etc.) are not
        produced here — each pass continues to own those.
    """
    texts = collect_stable_prefix_texts(stable_prefix)
    if not texts:
        return []

    cache_control = CacheControlEphemeralParam(type="ephemeral", ttl=ttl)

    blocks: list[TextBlockParam] = []
    for text in texts[:-1]:
        blocks.append(TextBlockParam(type="text", text=text))
    blocks.append(
        TextBlockParam(
            type="text",
            text=texts[-1],
            cache_control=cache_control,
        )
    )
    return blocks
