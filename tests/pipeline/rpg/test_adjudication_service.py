"""Service-level tests for RpgAdjudicationPassService — CRD Issues 15 and 15c.

CRD Issue 15c: the pass resolves backend shown/hidden rolls only. A proposal
the story's dice handling would hand to the player is refused before any
proposal is checked or rolled, so no pending request is created; proposals
beyond the per-turn bound are refused, never dropped; every proposal is
validated before any die.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.models.context import (
    AssembledContext,
    PassForwardLedger,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import (
    DiceHandling,
    IntentType,
    RollVisibility,
    RpgPlayStatus,
    RpgSetupPhase,
)
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.session import RpgSessionState
from afterworlds.models.story_bible import StoryBibleContext
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderCallResult,
    ProviderToolCallPart,
)
from afterworlds.pipeline.rpg.adapter import D20RulesSystemAdapter
from afterworlds.pipeline.rpg.caller import PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME
from afterworlds.pipeline.rpg.capability import AdjudicationRefusal, RefusalKind
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService
from afterworlds.services.dnd5e_state.turn import TurnCharacter
from tests.rpg_characters import srd_character

_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_STORY_ID: UUID = uuid4()
_TURN_ID: UUID = uuid4()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_sheet() -> TurnCharacter:
    return srd_character()


def _make_session(dice_handling: DiceHandling) -> RpgSessionState:  # type: ignore[no-untyped-def]
    return RpgSessionState(
        story_id=_STORY_ID,
        character_sheet_id=uuid4(),
        dice_handling=dice_handling,
        play_status=RpgPlayStatus.IN_PLAY,
        setup_phase=RpgSetupPhase.COMPLETE,
        gm_cheating=False,
    )


def _make_assembled() -> AssembledContext:  # type: ignore[no-untyped-def]
    sbc = StoryBibleContext(
        story_id=_STORY_ID,
        setting=None,
        cast=(),
        locked_facts=(),
        forbidden_facts=(),
        relationship_ledger=(),
        active_plot_threads=(),
        events=(),
    )
    prefix = StablePrefix(system_prompt="rpg mode test", story_bible_context=sbc)
    intent = IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.9,
        raw_input="I attack the goblin",
        ambiguous=False,
    )
    suffix = VolatileSuffix(
        recent_turns=[],
        current_input="I attack the goblin",
        classified_intent=intent,
    )
    return AssembledContext(
        stable_prefix=prefix,
        volatile_suffix=suffix,
        pass_forward_ledger=PassForwardLedger(),
    )


def _proposal_dict(
    check_label: str,
    visibility: RollVisibility,
    identity: str = "glossary.climbing/difficult_climb",
) -> dict:  # type: ignore[type-arg]
    return {
        "check_label": check_label,
        "subsystem_tag": "climb",
        "skill_or_attribute_label": None,
        "visible_modifier_note": None,
        "difficulty_reference_note": None,
        "visibility": visibility.value,
        "operation": "fixed_dc_check",
        "check_identity": identity,
    }


class _FakeProvider:
    """Stub ProviderAdapter that returns a fixed tool-call with given proposals."""

    def __init__(self, proposals: list) -> None:  # type: ignore[type-arg]
        self._proposals = proposals

    def call(self, request: ProviderCallRequest) -> ProviderCallResult:
        return ProviderCallResult(
            pass_id=PipelinePassId.RPG_ADJUDICATION,
            provider_name="fake",
            model_identifier="fake-model",
            model_tier=ModelTier.HAIKU,
            content_parts=[
                ProviderToolCallPart(
                    tool_name=PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME,
                    tool_input={"rolls": self._proposals, "reasoning_note": None},
                )
            ],
            input_token_count=100,
            output_token_count=50,
            cache_read_token_count=None,
            cache_creation_token_count=None,
            cache_warmed=False,
            latency_ms=10,
        )

    @property
    def provider_name(self) -> str:
        return "fake"


def _make_service() -> RpgAdjudicationPassService:  # type: ignore[no-untyped-def]
    return RpgAdjudicationPassService(adapter=D20RulesSystemAdapter())


def _make_dice_mock() -> MagicMock:  # type: ignore[no-untyped-def]
    """Return a MagicMock dice service that returns a valid DiceResult on roll()."""
    dice = MagicMock()
    dice.roll.return_value = MagicMock(chosen=10, raw_rolls=(10,))
    return dice


def _adjudicate(
    proposals: list,  # type: ignore[type-arg]
    dice_handling: DiceHandling = DiceHandling.AI_ROLLS,
    dice: MagicMock | None = None,
):  # type: ignore[no-untyped-def]
    return _make_service().adjudicate(
        _make_assembled(),
        _make_session(dice_handling),
        _make_sheet(),
        dice if dice is not None else _make_dice_mock(),
        provider=_FakeProvider(proposals),
        story_id=_STORY_ID,
        originating_turn_id=_TURN_ID,
    )


def _refusal(
    kind: RefusalKind,
    proposals: list,  # type: ignore[type-arg]
    dice_handling: DiceHandling = DiceHandling.AI_ROLLS,
) -> None:
    dice = _make_dice_mock()
    with pytest.raises(AdjudicationRefusal) as caught:
        _adjudicate(proposals, dice_handling, dice)
    assert caught.value.kind is kind
    dice.roll.assert_not_called()


# ---------------------------------------------------------------------------
# Backend rolls resolve; player rolls are refused before anything pends
# ---------------------------------------------------------------------------


def test_ai_rolls_resolve_every_shown_and_hidden_proposal() -> None:
    dice = _make_dice_mock()
    result = _adjudicate(
        [
            _proposal_dict("Climb", RollVisibility.SHOWN),
            _proposal_dict(
                "Jump", RollVisibility.HIDDEN, "glossary.long_jump/low_obstacle"
            ),
        ],
        dice=dice,
    )
    assert result.pending_roll_request is None
    assert [r.dc for r in result.proposals] == [15, 10]
    assert [r.source for r in result.proposals] == ["ai", "hidden"]
    assert dice.roll.call_count == 2
    assert result.writer_views[1].check_label == ""  # hidden scrubbed


def test_a_player_proposal_in_ai_rolls_mode_is_rolled_by_the_backend() -> None:
    result = _adjudicate([_proposal_dict("Climb", RollVisibility.PLAYER)])
    assert result.proposals[0].visibility is RollVisibility.SHOWN
    assert result.pending_roll_request is None


@pytest.mark.parametrize("visibility", [RollVisibility.SHOWN, RollVisibility.PLAYER])
def test_player_roll_configuration_refuses_before_any_pending_request(
    visibility: RollVisibility,
) -> None:
    _refusal(
        RefusalKind.PLAYER_ROLL_UNSUPPORTED,
        [
            _proposal_dict("Jump", RollVisibility.HIDDEN),
            _proposal_dict("Climb", visibility),
        ],
        DiceHandling.PLAYER_ROLLS,
    )


def test_hidden_rolls_still_resolve_under_player_roll_configuration() -> None:
    result = _adjudicate(
        [_proposal_dict("Climb", RollVisibility.HIDDEN)], DiceHandling.PLAYER_ROLLS
    )
    assert result.pending_roll_request is None
    assert len(result.proposals) == 1


def test_proposals_beyond_the_bound_are_refused_not_dropped() -> None:
    _refusal(
        RefusalKind.UNSUPPORTED_CAPABILITY,
        [_proposal_dict(f"Climb {n}", RollVisibility.SHOWN) for n in range(6)],
    )


def test_an_empty_proposal_list_is_a_non_mechanical_turn() -> None:
    result = _adjudicate([])
    assert (result.proposals, result.writer_views) == ((), ())


@pytest.mark.parametrize(
    "dice_handling",
    [DiceHandling.AI_ROLLS, DiceHandling.PLAYER_ROLLS],
)
def test_an_unsupported_proposal_refuses_before_any_earlier_one_rolls(
    dice_handling: DiceHandling,
) -> None:
    """Every proposal is checked before dice or a record."""
    supported = _proposal_dict("Climb", RollVisibility.HIDDEN)
    held = {
        **_proposal_dict("Longsword", RollVisibility.HIDDEN),
        "operation": "saving_throw",
        "check_identity": None,
    }
    _refusal(RefusalKind.UNSUPPORTED_CAPABILITY, [supported, held], dice_handling)


def test_a_label_only_proposal_refuses_rather_than_rolling() -> None:
    proposal = {**_proposal_dict("Stealth", RollVisibility.SHOWN)}
    del proposal["operation"], proposal["check_identity"]
    _refusal(RefusalKind.UNSUPPORTED_CAPABILITY, [proposal])
