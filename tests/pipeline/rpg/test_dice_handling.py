"""Tests for dice-handling enforcement — CRD Issues 15 and 15b.

Covers _effective_visibility: model-emitted visibility is advisory; the
story's dice handling is authoritative. Under PLAYER_ROLLS a visible proposal
is the Sojourner's to roll for the acting character's own dice (CRD Issue
15b); the single-pending-roll overflow rule of CRD Issue 15 is retired with
the persisted action-resolution sequence, so it has no input here.
"""

from __future__ import annotations

import pytest

from afterworlds.models.enums import DiceHandling, RollVisibility
from afterworlds.pipeline.rpg.service import _effective_visibility


@pytest.mark.parametrize(
    ("proposal_vis", "dice_handling", "expected"),
    [
        # AI_ROLLS: PLAYER → SHOWN (the backend rolls); others unchanged.
        (RollVisibility.PLAYER, DiceHandling.AI_ROLLS, RollVisibility.SHOWN),
        (RollVisibility.SHOWN, DiceHandling.AI_ROLLS, RollVisibility.SHOWN),
        (RollVisibility.HIDDEN, DiceHandling.AI_ROLLS, RollVisibility.HIDDEN),
        # PLAYER_ROLLS: every visible proposal → PLAYER; HIDDEN stays HIDDEN
        # and is always rolled by the backend.
        (RollVisibility.SHOWN, DiceHandling.PLAYER_ROLLS, RollVisibility.PLAYER),
        (RollVisibility.PLAYER, DiceHandling.PLAYER_ROLLS, RollVisibility.PLAYER),
        (RollVisibility.HIDDEN, DiceHandling.PLAYER_ROLLS, RollVisibility.HIDDEN),
    ],
)
def test_effective_visibility_matrix(
    proposal_vis: RollVisibility,
    dice_handling: DiceHandling,
    expected: RollVisibility,
) -> None:
    assert _effective_visibility(proposal_vis, dice_handling) is expected
