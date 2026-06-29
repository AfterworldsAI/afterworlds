"""Branch-selection validation service — CRD Issue 16.

Validates a Sojourner's BRANCH_CHOICE input against the set of options
presented on the current beat.  Pure-Python — no LLM call.

Resolution algorithm (in order, first match wins):
1. Exact option_id match: raw_input contains "opt_N" verbatim.
2. Explicit numeric phrase: "option N" / "choice N" maps to "opt_N".
3. Ordinal word: "first" → opt_1, "second" → opt_2, … (up to opt_5).
4. Bare number: a lone "N" maps to "opt_N", but only when it is the operative
   selection token — either it leads the input ("2, but I do it cautiously")
   or it trails it with nothing further ("I pick 2").  An incidental number
   embedded in prose ("take 2 torches") is not a selection.
5. No match → INVALID_BRANCH_SELECTION.

Explicit forms outrank bare numbers: "I use my 2 torches and choose option 1"
resolves to opt_1, never opt_2.

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
# Explicit numeric selection phrase: "option 2" / "choice 3".  Outranks bare
# numbers so an incidental quantity ("my 2 torches") cannot pre-empt an explicit
# later selection ("choose option 1").
_EXPLICIT_NUM_RE = re.compile(r"\b(?:option|choice)\s+(\d+)\b", re.IGNORECASE)
# An ordinal may be followed by a neutral selection noun ("option"/"choice");
# when present it is part of the selection phrase, not a trailing annotation, so
# the whole match (group 0) is consumed.  Group 1 holds the ordinal word.
_ORDINAL_RE = re.compile(
    r"\b(first|second|third|fourth|fifth)\b(?:\s+(?:option|choice)\b)?",
    re.IGNORECASE,
)
# Bare number, accepted only as a last resort and only when it is the operative
# selection token: either it leads the input ("2, but I do it cautiously") or it
# trails it with nothing further ("I pick 2").  An incidental number embedded in
# prose ("take 2 torches") is neither and is not a selection.
_BARE_NUMBER_RE = re.compile(r"\b(\d+)\b")
_WORD_RE = re.compile(r"\w")
# Leading connectors / punctuation stripped from a captured annotation.  Word
# connectors ("but"/"and") are only stripped on a word boundary so real words
# ("butter", "andes") are preserved.
_ANNOTATION_CONNECTORS: tuple[str, ...] = ("but", "and", ",", ";", "—", "-", ".")


def _extract_annotation(tail: str) -> str | None:
    """Return the trailing annotation text after a selection token, or None.

    ``tail`` is the raw substring following the consumed match span.  Leading
    connectors and punctuation are stripped repeatedly so that stacked
    connectors collapse — e.g. "2, but I do it cautiously" yields the tail
    ", but I do it cautiously", which reduces to "I do it cautiously" (both the
    comma and "but" are removed), not "but I do it cautiously".
    """
    tail = tail.strip()
    changed = True
    while changed:
        changed = False
        for prefix in _ANNOTATION_CONNECTORS:
            if not tail.lower().startswith(prefix):
                continue
            if prefix.isalpha():
                # Only strip a word connector on a word boundary, so that
                # "butter"/"andes" are not truncated to "ter"/"es".
                after = tail[len(prefix) :]
                if after[:1].isalnum():
                    continue
            tail = tail[len(prefix) :].strip()
            changed = True
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
        consumed_end: int = -1

        # 1. Explicit opt_N match
        m = _OPT_ID_RE.search(raw_input)
        if m:
            candidate = f"opt_{m.group(1)}"
            if candidate in opt_map:
                resolved_id = candidate
                consumed_end = m.end()

        # 2. Explicit numeric phrase ("option 2", "choice 3")
        if resolved_id is None:
            for m in _EXPLICIT_NUM_RE.finditer(raw_input):
                n = int(m.group(1))
                candidate = f"opt_{n}"
                if 1 <= n <= max_index and candidate in opt_map:
                    resolved_id = candidate
                    consumed_end = m.end()
                    break

        # 3. Ordinal word
        if resolved_id is None:
            m = _ORDINAL_RE.search(raw_input)
            if m:
                n = _ORDINALS.get(m.group(1).lower(), 0)
                candidate = f"opt_{n}"
                if 1 <= n <= max_index and candidate in opt_map:
                    resolved_id = candidate
                    consumed_end = m.end()

        # 4. Bare number — lowest precedence, and only when it is the operative
        #    selection token.  A bare number qualifies when it *leads* the input
        #    (only whitespace precedes it, so trailing annotation is allowed:
        #    "2, but I do it cautiously") or when it *trails* the input with
        #    nothing further ("I pick 2").  A number embedded mid-prose with
        #    words on both sides ("take 2 torches") is an incidental quantity,
        #    not a branch choice, and is skipped.
        if resolved_id is None:
            for m in _BARE_NUMBER_RE.finditer(raw_input):
                is_leading = raw_input[: m.start()].strip() == ""
                is_trailing = not _WORD_RE.search(raw_input[m.end() :])
                if not (is_leading or is_trailing):
                    continue
                n = int(m.group(1))
                candidate = f"opt_{n}"
                if 1 <= n <= max_index and candidate in opt_map:
                    resolved_id = candidate
                    consumed_end = m.end()
                    break

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
        annotation = _extract_annotation(raw_input[consumed_end:])

        return BranchSelectionValidationResult(
            verdict=BranchSelectionValidationVerdict.ACCEPT,
            selected_context=SelectedBranchContext(
                option_id=resolved_id,
                action_text=matched_option.action_text,
                annotation=annotation,
            ),
        )


__all__ = ["BranchSelectionValidationService"]
