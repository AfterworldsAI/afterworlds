"""Branching Writer pass configuration — CRD Issue 16."""

from __future__ import annotations

import os
from dataclasses import dataclass

from afterworlds.models.enums import BranchCountRange, InteractionStyle

_DEFAULT_BRANCHING_WRITER_MODEL: str = "claude-sonnet-4-6"

BRANCHING_WRITER_MAX_TOKENS: int = 1024

#: Maps branch_count_range string to (min_options, max_options) tuple.
#: Code uses this to validate proposal count — never clamp, pad, or truncate.
BRANCH_COUNT_RANGE_BOUNDS: dict[str, tuple[int, int]] = {
    "1-2": (1, 2),
    "2-3": (2, 3),
    "3-4": (3, 4),
    "2-4": (2, 4),
    "2-5": (2, 5),
}

#: Code-owned frozen mapping of which branch-count ranges are valid per
#: InteractionStyle.  FREEFORM_ONLY maps to None (no branch cards).
#: Validated by the OOC config-update path and setup flow.
ALLOWED_RANGES_BY_STYLE: dict[InteractionStyle, frozenset[BranchCountRange] | None] = {
    InteractionStyle.FREEFORM_ONLY: None,
    InteractionStyle.HYBRID: frozenset(
        {
            BranchCountRange.ONE_TO_TWO,
            BranchCountRange.TWO_TO_THREE,
            BranchCountRange.THREE_TO_FOUR,
        }
    ),
    InteractionStyle.TRUE_CYOA: frozenset(
        {
            BranchCountRange.TWO_TO_THREE,
            BranchCountRange.TWO_TO_FOUR,
            BranchCountRange.TWO_TO_FIVE,
        }
    ),
}


def true_cyoa_unplayable_reason(
    interaction_style: InteractionStyle | None,
    branch_count_range: BranchCountRange | None,
    committed_option_count: int,
) -> str | None:
    """Why an in-play story would be left with no valid next choice, or None.

    ADR-016b: True CYOA in play must always have a selectable committed card
    set, because freeform input is rejected. A configuration change cannot
    create cards (no new narrative is generated for it), so a change that
    would make an in-play story True CYOA without a committed set that fits
    its range is refused, keeping the current playable configuration.
    """
    if interaction_style is not InteractionStyle.TRUE_CYOA:
        return None
    if committed_option_count == 0:
        return (
            "True CYOA needs a current set of branch cards to choose from, and"
            " this story has none right now; continue a beat in Hybrid first"
        )
    bounds = (
        BRANCH_COUNT_RANGE_BOUNDS.get(branch_count_range.value)
        if branch_count_range is not None
        else None
    )
    if bounds is None or not bounds[0] <= committed_option_count <= bounds[1]:
        shown = branch_count_range.value if branch_count_range else "none"
        return (
            f"the current {committed_option_count} branch card(s) do not fit"
            f" the True CYOA range {shown}"
        )
    return None


@dataclass
class BranchingWriterConfig:
    model: str = _DEFAULT_BRANCHING_WRITER_MODEL
    api_key_env: str = "ANTHROPIC_API_KEY"
    extended_ttl: bool = True

    @classmethod
    def from_env(cls) -> BranchingWriterConfig:
        model = os.environ.get(
            "AFTERWORLDS_BRANCHING_WRITER_MODEL", _DEFAULT_BRANCHING_WRITER_MODEL
        )
        api_key_env = os.environ.get(
            "AFTERWORLDS_BRANCHING_WRITER_API_KEY_ENV", "ANTHROPIC_API_KEY"
        )
        ttl_str = os.environ.get(
            "AFTERWORLDS_BRANCHING_WRITER_EXTENDED_TTL", "true"
        ).lower()
        extended_ttl = ttl_str not in ("0", "false", "no")
        return cls(model=model, api_key_env=api_key_env, extended_ttl=extended_ttl)


__all__ = [
    "ALLOWED_RANGES_BY_STYLE",
    "BRANCH_COUNT_RANGE_BOUNDS",
    "BRANCHING_WRITER_MAX_TOKENS",
    "BranchingWriterConfig",
    "true_cyoa_unplayable_reason",
]
