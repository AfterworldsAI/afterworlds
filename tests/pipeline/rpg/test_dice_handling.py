"""Tests for dice-handling enforcement — CRD Issue 15 remediation.

Covers _effective_visibility: model-emitted visibility is advisory;
dice_handling mode is authoritative.
"""

from __future__ import annotations

import pytest

from afterworlds.models.enums import DiceHandling, RollVisibility
from afterworlds.pipeline.rpg.service import _effective_visibility

# ---------------------------------------------------------------------------
# AI_ROLLS mode
# ---------------------------------------------------------------------------


def test_ai_rolls_coerces_player_to_shown() -> None:
    """AI_ROLLS + model emits PLAYER → coerce to SHOWN; no pending roll."""
    result = _effective_visibility(RollVisibility.PLAYER, DiceHandling.AI_ROLLS, False)
    assert result is RollVisibility.SHOWN


def test_ai_rolls_coerces_player_even_when_pending_exists() -> None:
    """AI_ROLLS always coerces PLAYER to SHOWN regardless of pending state."""
    result = _effective_visibility(RollVisibility.PLAYER, DiceHandling.AI_ROLLS, True)
    assert result is RollVisibility.SHOWN


def test_ai_rolls_preserves_shown() -> None:
    """AI_ROLLS + SHOWN proposal stays SHOWN."""
    result = _effective_visibility(RollVisibility.SHOWN, DiceHandling.AI_ROLLS, False)
    assert result is RollVisibility.SHOWN


def test_ai_rolls_preserves_hidden() -> None:
    """AI_ROLLS + HIDDEN proposal stays HIDDEN (hidden rolls are always AI-resolved)."""
    result = _effective_visibility(RollVisibility.HIDDEN, DiceHandling.AI_ROLLS, False)
    assert result is RollVisibility.HIDDEN


# ---------------------------------------------------------------------------
# PLAYER_ROLLS mode
# ---------------------------------------------------------------------------


def test_player_rolls_first_shown_becomes_player() -> None:
    """PLAYER_ROLLS + first SHOWN proposal → coerce to PLAYER (create pending)."""
    result = _effective_visibility(
        RollVisibility.SHOWN, DiceHandling.PLAYER_ROLLS, False
    )
    assert result is RollVisibility.PLAYER


def test_player_rolls_shown_stays_shown_when_pending_exists() -> None:
    """PLAYER_ROLLS + SHOWN + pending already exists → stays SHOWN (AI-resolved)."""
    result = _effective_visibility(
        RollVisibility.SHOWN, DiceHandling.PLAYER_ROLLS, True
    )
    assert result is RollVisibility.SHOWN


def test_player_rolls_preserves_player_proposal_first() -> None:
    """PLAYER_ROLLS + model emits PLAYER when no pending → stays PLAYER."""
    result = _effective_visibility(
        RollVisibility.PLAYER, DiceHandling.PLAYER_ROLLS, False
    )
    assert result is RollVisibility.PLAYER


def test_player_rolls_preserves_hidden() -> None:
    """PLAYER_ROLLS + HIDDEN → stays HIDDEN (hidden rolls are always AI-resolved)."""
    result = _effective_visibility(
        RollVisibility.HIDDEN, DiceHandling.PLAYER_ROLLS, False
    )
    assert result is RollVisibility.HIDDEN


def test_player_rolls_hidden_unchanged_even_when_no_pending() -> None:
    """PLAYER_ROLLS + HIDDEN + no pending → still HIDDEN."""
    result = _effective_visibility(
        RollVisibility.HIDDEN, DiceHandling.PLAYER_ROLLS, False
    )
    assert result is RollVisibility.HIDDEN


# ---------------------------------------------------------------------------
# Exhaustive matrix check
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("proposal_vis", "dice_handling", "has_pending", "expected"),
    [
        # AI_ROLLS: PLAYER → SHOWN; others unchanged
        (RollVisibility.PLAYER, DiceHandling.AI_ROLLS, False, RollVisibility.SHOWN),
        (RollVisibility.PLAYER, DiceHandling.AI_ROLLS, True, RollVisibility.SHOWN),
        (RollVisibility.SHOWN, DiceHandling.AI_ROLLS, False, RollVisibility.SHOWN),
        (RollVisibility.SHOWN, DiceHandling.AI_ROLLS, True, RollVisibility.SHOWN),
        (RollVisibility.HIDDEN, DiceHandling.AI_ROLLS, False, RollVisibility.HIDDEN),
        (RollVisibility.HIDDEN, DiceHandling.AI_ROLLS, True, RollVisibility.HIDDEN),
        # PLAYER_ROLLS: SHOWN+no-pending → PLAYER; otherwise unchanged
        (RollVisibility.SHOWN, DiceHandling.PLAYER_ROLLS, False, RollVisibility.PLAYER),
        (RollVisibility.SHOWN, DiceHandling.PLAYER_ROLLS, True, RollVisibility.SHOWN),
        (
            RollVisibility.PLAYER,
            DiceHandling.PLAYER_ROLLS,
            False,
            RollVisibility.PLAYER,
        ),
        (RollVisibility.PLAYER, DiceHandling.PLAYER_ROLLS, True, RollVisibility.PLAYER),
        (
            RollVisibility.HIDDEN,
            DiceHandling.PLAYER_ROLLS,
            False,
            RollVisibility.HIDDEN,
        ),
        (RollVisibility.HIDDEN, DiceHandling.PLAYER_ROLLS, True, RollVisibility.HIDDEN),
    ],
)
def test_effective_visibility_matrix(
    proposal_vis: RollVisibility,
    dice_handling: DiceHandling,
    has_pending: bool,
    expected: RollVisibility,
) -> None:
    assert _effective_visibility(proposal_vis, dice_handling, has_pending) is expected
