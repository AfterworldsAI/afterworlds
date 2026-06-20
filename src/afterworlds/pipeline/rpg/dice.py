"""DiceService protocol and SystemRandomDiceService implementation — CRD Issue 15.

The DiceService owns all randomness for RPG adjudication.  Rolls are
deterministic under injection (seedable for tests; secrets/SystemRandom in
production).  There are no d20 semantics here — the dice service rolls and
keeps without knowledge of modifiers, DCs, or game rules.
"""

from __future__ import annotations

import re
import secrets
from typing import Protocol, runtime_checkable

from afterworlds.models.rpg import DiceResult

_EXPRESSION_RE = re.compile(
    r"^(\d+)d(\d+)(?:(kh|kl)(\d+))?(?:([+-])(\d+))?$",
    re.IGNORECASE,
)


def _parse_expression(expression: str) -> tuple[int, int, str | None, int | None]:
    """Parse a dice expression into (count, sides, keep_op, keep_n).

    Supported formats:
    - ``NdS`` — roll N dice of S sides, keep all
    - ``NdSkh1`` / ``NdSkl1`` — keep highest or lowest 1
    - Modifier (``+N`` / ``-N``) is stripped from the expression before
      rolling; the adapter applies modifiers separately.

    Returns (count, sides, keep_op, keep_n) where keep_op is ``"kh"`` or
    ``"kl"`` and keep_n is the number to keep (or None for straight roll).

    Raises ValueError for unrecognised formats.
    """
    m = _EXPRESSION_RE.match(expression.strip())
    if not m:
        raise ValueError(f"Unrecognised dice expression: {expression!r}")
    count = int(m.group(1))
    sides = int(m.group(2))
    keep_op: str | None = m.group(3).lower() if m.group(3) else None
    keep_n: int | None = int(m.group(4)) if m.group(4) else None
    if count < 1 or sides < 1:
        raise ValueError(
            f"Invalid dice expression (count or sides < 1): {expression!r}"
        )
    return count, sides, keep_op, keep_n


@runtime_checkable
class DiceService(Protocol):
    """Injectable dice service — no d20 semantics, no modifiers.

    ``roll`` parses the expression, rolls the dice, and applies keep-highest
    or keep-lowest selection.  Modifiers in the expression string are stripped
    before rolling; the adapter applies them separately so the raw die result
    is always auditable in isolation.
    """

    def roll(self, expression: str) -> DiceResult:
        """Roll the given dice expression and return an immutable DiceResult.

        Args:
            expression: a dice notation string (e.g. ``"1d20"``, ``"2d20kh1"``).

        Returns:
            Immutable DiceResult with raw_rolls and chosen value.

        Raises:
            ValueError: if the expression cannot be parsed.
        """
        ...


class SystemRandomDiceService:
    """Production DiceService using ``secrets.SystemRandom`` for CSPRNG rolls.

    Seedable constructor parameter for deterministic test usage:
    ``SystemRandomDiceService(seed=42)``.
    """

    def __init__(self, seed: int | None = None) -> None:
        if seed is not None:
            import random  # noqa: PLC0415

            self._rng = random.Random(seed)
        else:
            self._rng = secrets.SystemRandom()

    def roll(self, expression: str) -> DiceResult:
        """Roll the given dice expression.

        Modifiers (``+N`` or ``-N`` suffix) are stripped before rolling so
        the raw die values are captured without modifier inflation.  The
        adapter applies modifiers to ``total`` separately.
        """
        count, sides, keep_op, keep_n = _parse_expression(expression)

        raw = tuple(self._rng.randint(1, sides) for _ in range(count))

        if keep_op is None or keep_n is None:
            chosen = raw[0] if len(raw) == 1 else sum(raw)
        elif keep_op == "kh":
            chosen = sorted(raw, reverse=True)[:keep_n][0]
        else:
            chosen = sorted(raw)[:keep_n][0]

        return DiceResult(expression=expression, raw_rolls=raw, chosen=chosen)
