"""Branch-selection validation service — CRD Issue 16.

Validates a Sojourner's BRANCH_CHOICE input against the set of options
presented on the current beat.  Pure-Python — no LLM call.

Resolution algorithm (in order, first match wins):
1. Exact option_id match: raw_input contains "opt_N" verbatim.
2. Positional numeric: raw_input contains a bare number or "option N" /
   "choice N" phrase that maps to "opt_N".
3. Ordinal word: "first" → opt_1, "second" → opt_2, … (up to opt_5).
4. No match → INVALID_BRANCH_SELECTION.

V1 scope note: material-rewrite detection (MATERIAL_BRANCH_REWRITE) requires
LLM judgment and is not implemented here.  The verdict is ACCEPT for any
resolved selection; annotation is recorded from any trailing text after the
selection token.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from afterworlds.models.enums import InteractionRejectionReason
from afterworlds.pipeline.branching.models import (
    BranchSelectionValidationResult,
    BranchSelectionValidationVerdict,
    SelectedBranchContext,
)

if TYPE_CHECKING:
    from afterworlds.models.node import PersistedBranchOption


# Ordinal → index (1-based)
_ORDINALS: dict[str, int] = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
}

_OPT_ID_RE = re.compile(r"\bopt_(\d+)\b", re.IGNORECASE)
_NUMERIC_PHRASE_RE = re.compile(
    r"\b(?:option|choice)\s+(\d+)\b|\b(\d+)\b", re.IGNORECASE
)
# An ordinal may be followed by a neutral selection noun ("option"/"choice");
# when present it is part of the selection phrase, not a trailing annotation, so
# the whole match (group 0) is consumed.  Group 1 holds the ordinal word.
_ORDINAL_RE = re.compile(
    r"\b(first|second|third|fourth|fifth)\b(?:\s+(?:option|choice)\b)?",
    re.IGNORECASE,
)


def _extract_annotation(raw_input: str, consumed_token: str) -> str | None:
    """Return any trailing text after the match token, stripped, or None."""
    idx = raw_input.lower().find(consumed_token.lower())
    if idx == -1:
        return None
    tail = raw_input[idx + len(consumed_token) :].strip()
    # Strip common connectors
    for prefix in ("but", "and", ",", ";", "—", "-"):
        if tail.lower().startswith(prefix):
            tail = tail[len(prefix) :].strip()
    return tail if tail else None


class BranchSelectionValidationService:
    """Validates a BRANCH_CHOICE input against the current beat's branch cards.

    Stateless — construct once and reuse across turns.
    """

    def validate(
        self,
        raw_input: str,
        presented_options: list[PersistedBranchOption],
    ) -> BranchSelectionValidationResult:
        """Resolve and validate the Sojourner's branch selection.

        Args:
            raw_input: The raw user input string (from IntentClassificationResult).
            presented_options: Branch options presented on the current beat,
                from ``Node.mode_metadata.branching.branch_options``.

        Returns:
            BranchSelectionValidationResult with ACCEPT (and SelectedBranchContext)
            or REJECT (with InteractionRejectionReason and rejection_message).
        """
        if not presented_options:
            return BranchSelectionValidationResult(
                verdict=BranchSelectionValidationVerdict.REJECT,
                rejection_reason=InteractionRejectionReason.INVALID_BRANCH_SELECTION,
                rejection_message=(
                    "No branch options were presented for the current beat."
                    " Branch selection is only valid after a branch card is shown."
                ),
            )

        opt_map: dict[str, PersistedBranchOption] = {
            o.option_id: o for o in presented_options
        }
        max_index = len(presented_options)

        resolved_id: str | None = None
        consumed_token: str = ""

        # 1. Explicit opt_N match
        m = _OPT_ID_RE.search(raw_input)
        if m:
            candidate = f"opt_{m.group(1)}"
            if candidate in opt_map:
                resolved_id = candidate
                consumed_token = m.group(0)

        # 2. Numeric phrase ("option 2", "choice 3", or bare "2")
        if resolved_id is None:
            for m in _NUMERIC_PHRASE_RE.finditer(raw_input):
                num_str = m.group(1) or m.group(2)
                if num_str is None:
                    continue
                n = int(num_str)
                candidate = f"opt_{n}"
                if 1 <= n <= max_index and candidate in opt_map:
                    resolved_id = candidate
                    consumed_token = m.group(0)
                    break

        # 3. Ordinal word
        if resolved_id is None:
            m = _ORDINAL_RE.search(raw_input)
            if m:
                n = _ORDINALS.get(m.group(1).lower(), 0)
                candidate = f"opt_{n}"
                if 1 <= n <= max_index and candidate in opt_map:
                    resolved_id = candidate
                    consumed_token = m.group(0)

        if resolved_id is None:
            opt_labels = ", ".join(
                f"{o.option_id}: {o.action_text!r}" for o in presented_options
            )
            return BranchSelectionValidationResult(
                verdict=BranchSelectionValidationVerdict.REJECT,
                rejection_reason=InteractionRejectionReason.INVALID_BRANCH_SELECTION,
                rejection_message=(
                    "Your input did not match any of the available branch options."
                    f" Please select one of: {opt_labels}."
                ),
            )

        matched_option = opt_map[resolved_id]
        annotation = _extract_annotation(raw_input, consumed_token)

        return BranchSelectionValidationResult(
            verdict=BranchSelectionValidationVerdict.ACCEPT,
            selected_context=SelectedBranchContext(
                option_id=resolved_id,
                action_text=matched_option.action_text,
                annotation=annotation,
            ),
        )


__all__ = ["BranchSelectionValidationService"]
