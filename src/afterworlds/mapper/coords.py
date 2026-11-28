"""``A1`` coordinates: column letters, row numbers, A1 at the top left.

The store keeps zero-based ``(col, row)`` integers; the view, the Writer and
words in a Turn use letters and numbers.
"""

from __future__ import annotations

import re

from afterworlds.mapper.models import Square

_LABEL = re.compile(r"^([A-Za-z]{1,2})(\d{1,3})$")


def label(square: Square) -> str:
    col, row = square
    letters = ""
    n = col + 1
    while n:
        n, rem = divmod(n - 1, 26)
        letters = chr(ord("A") + rem) + letters
    return f"{letters}{row + 1}"


def parse(text: str) -> Square:
    """``"C3"`` -> ``(2, 2)``; ``ValueError`` for anything else."""
    m = _LABEL.match(text.strip())
    if not m:
        raise ValueError(f"not a square: {text!r}")
    col = 0
    for ch in m.group(1).upper():
        col = col * 26 + (ord(ch) - ord("A") + 1)
    row = int(m.group(2))
    if row < 1:
        raise ValueError(f"not a square: {text!r}")
    return col - 1, row - 1


def is_label(text: str) -> bool:
    return _LABEL.match(text.strip()) is not None
