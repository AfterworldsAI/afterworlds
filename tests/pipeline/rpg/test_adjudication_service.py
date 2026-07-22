"""Service-level tests for RpgAdjudicationPassService multi-roll enforcement.

CRD Issue 15 remediation Round 9: PLAYER_ROLLS mode must not AI-resolve overflow
visible proposals; additional SHOWN proposals are deferred (not resolved, not a
second pending).
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.models.character_sheet import Dnd5eAbilityScores, Dnd5eCharacterSheet
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
from afterworlds.pipeline.rpg.service import RpgAdjudicationPassService

_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_STORY_ID: UUID = uuid4()
_TURN_ID: UUID = uuid4()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_sheet() -> Dnd5eCharacterSheet:  # type: ignore[no-untyped-def]
    return Dnd5eCharacterSheet(
        story_id=_STORY_ID,
        rules_package_id="dnd5e_v1",
        character_name="Test Fighter",
        created_at=_NOW,
        updated_at=_NOW,
        character_class="Fighter",
        background="Soldier",
        level=3,
        ability_scores=Dnd5eAbilityScores(
            strength=16,
            dexterity=12,
            constitution=14,
            intelligence=10,
            wisdom=10,
            charisma=8,
        ),
        current_hp=28,
        maximum_hp=28,
    )


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


def _proposal_dict(check_label: str, visibility: RollVisibility) -> dict:  # type: ignore[type-arg]
    return {
        "check_label": check_label,
        "subsystem_tag": "attack",
        "skill_or_attribute_label": "strength",
        "visible_modifier_note": None,
        "difficulty_reference_note": None,
        "visibility": visibility.value,
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


# ---------------------------------------------------------------------------
# PLAYER_ROLLS: two visible proposals → one pending, zero resolved, no dice call
# ---------------------------------------------------------------------------


class TestMultipleVisibleProposalsPlayerRolls:
    """Two SHOWN proposals in PLAYER_ROLLS → 1 pending, 0 resolved, no dice call."""

    def _adjudicate(self):  # type: ignore[no-untyped-def]
        dice = _make_dice_mock()
        proposals = [
            _proposal_dict("Attack Roll", RollVisibility.SHOWN),
            _proposal_dict("Damage Roll", RollVisibility.SHOWN),
        ]
        result = _make_service().adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.PLAYER_ROLLS),
            _make_sheet(),
            dice,
            provider=_FakeProvider(proposals),
        )
        return result, dice

    def test_one_pending_request_created(self) -> None:
        result, _ = self._adjudicate()
        assert result.player_proposal is not None
        assert result.player_proposal.check_label == "Attack Roll"

    def test_no_resolved_records(self) -> None:
        result, _ = self._adjudicate()
        assert len(result.proposals) == 0

    def test_dice_service_not_called(self) -> None:
        _, dice = self._adjudicate()
        dice.roll.assert_not_called()

    def test_one_writer_view(self) -> None:
        result, _ = self._adjudicate()
        assert len(result.writer_views) == 1


# ---------------------------------------------------------------------------
# PLAYER_ROLLS: SHOWN + HIDDEN → one pending + one resolved, dice called once
# ---------------------------------------------------------------------------


class TestHiddenPreservationWithPendingVisible:
    """PLAYER_ROLLS + SHOWN then HIDDEN → pending announced, hidden code-resolved."""

    def _adjudicate(self):  # type: ignore[no-untyped-def]
        dice = _make_dice_mock()
        proposals = [
            _proposal_dict("Attack Roll", RollVisibility.SHOWN),
            _proposal_dict("Hidden Saving Throw", RollVisibility.HIDDEN),
        ]
        result = _make_service().adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.PLAYER_ROLLS),
            _make_sheet(),
            dice,
            provider=_FakeProvider(proposals),
        )
        return result, dice

    def test_pending_and_one_resolved(self) -> None:
        result, _ = self._adjudicate()
        assert result.player_proposal is not None
        assert len(result.proposals) == 1

    def test_dice_called_once_for_hidden(self) -> None:
        _, dice = self._adjudicate()
        assert dice.roll.call_count == 1


# ---------------------------------------------------------------------------
# AI_ROLLS regression: two SHOWN → zero pending, two resolved, dice called twice
# ---------------------------------------------------------------------------


class TestAiRollsRegression:
    """AI_ROLLS mode: two SHOWN proposals → 0 pending, 2 resolved, dice called twice."""

    def _adjudicate(self):  # type: ignore[no-untyped-def]
        dice = _make_dice_mock()
        proposals = [
            _proposal_dict("Attack Roll", RollVisibility.SHOWN),
            _proposal_dict("Damage Roll", RollVisibility.SHOWN),
        ]
        result = _make_service().adjudicate(
            _make_assembled(),
            _make_session(DiceHandling.AI_ROLLS),
            _make_sheet(),
            dice,
            provider=_FakeProvider(proposals),
        )
        return result, dice

    def test_no_pending_two_resolved(self) -> None:
        result, _ = self._adjudicate()
        assert result.player_proposal is None
        assert len(result.proposals) == 2

    def test_dice_called_twice(self) -> None:
        _, dice = self._adjudicate()
        assert dice.roll.call_count == 2
