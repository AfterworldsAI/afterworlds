"""Unit tests for RollTerm validation — CRD Issue 15b."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from afterworlds.models.enums import DiceSelectionRule
from afterworlds.models.rpg import RollTerm


def _term(**overrides: object) -> RollTerm:
    defaults: dict[str, object] = {
        "term_id": uuid4(),
        "count": 4,
        "sides": 6,
        "selection_rule": DiceSelectionRule.KEEP_HIGHEST,
        "keep_count": 3,
    }
    defaults.update(overrides)
    return RollTerm(**defaults)  # type: ignore[arg-type]


def test_keep_highest_accepts_keep_count_within_bounds() -> None:
    term = _term(selection_rule=DiceSelectionRule.KEEP_HIGHEST, keep_count=3, count=4)
    assert term.keep_count == 3


def test_keep_lowest_accepts_keep_count_of_one() -> None:
    term = _term(selection_rule=DiceSelectionRule.KEEP_LOWEST, keep_count=1, count=2)
    assert term.keep_count == 1


def test_sum_all_accepts_no_keep_count() -> None:
    term = _term(selection_rule=DiceSelectionRule.SUM_ALL, keep_count=None, count=10)
    assert term.keep_count is None


def test_sum_all_rejects_keep_count_set() -> None:
    with pytest.raises(ValidationError, match="keep_count must be None"):
        _term(selection_rule=DiceSelectionRule.SUM_ALL, keep_count=1, count=10)


def test_keep_highest_rejects_missing_keep_count() -> None:
    with pytest.raises(ValidationError, match="keep_count is required"):
        _term(selection_rule=DiceSelectionRule.KEEP_HIGHEST, keep_count=None, count=4)


def test_keep_count_zero_rejected() -> None:
    with pytest.raises(ValidationError, match="must be between 1 and"):
        _term(selection_rule=DiceSelectionRule.KEEP_HIGHEST, keep_count=0, count=4)


def test_keep_count_exceeding_count_rejected() -> None:
    """The 4d6kh3-family regression Codex flagged: keep_count > count must fail."""
    with pytest.raises(ValidationError, match="must be between 1 and"):
        _term(selection_rule=DiceSelectionRule.KEEP_HIGHEST, keep_count=5, count=4)


def test_count_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        _term(count=0)


def test_sides_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        _term(sides=0)
