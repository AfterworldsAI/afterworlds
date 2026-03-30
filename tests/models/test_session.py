"""Unit tests for mode-specific session state models.

Key invariants tested:
- RPG session state does not own HP or spell slots (source-of-truth test)
- RPG session state fields are not present on base Node
- BranchingSessionState has branch_tree as a distinct structured model
- BranchingSessionState has plot_thread_tracker as a distinct structured field
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from afterworlds.models.enums import DiceHandling, PacingStage, WritingPersona
from afterworlds.models.node import Node
from afterworlds.models.session import (
    BranchingSessionState,
    BranchNode,
    BranchTree,
    CombatContext,
    PlotThread,
    RpgSessionState,
    WritingSessionState,
)


class TestCombatContext:
    def test_defaults(self) -> None:
        ctx = CombatContext()
        assert ctx.is_in_combat is False
        assert ctx.initiative_order == []
        assert ctx.active_conditions == {}
        assert ctx.round_number == 0

    def test_populated(self) -> None:
        ctx = CombatContext(
            is_in_combat=True,
            initiative_order=["Elowen", "Goblin"],
            active_conditions={"Elowen": ["poisoned"]},
            round_number=3,
        )
        assert ctx.is_in_combat is True
        assert "Elowen" in ctx.initiative_order
        assert ctx.round_number == 3


class TestRpgSessionState:
    def _make(self, **kwargs: object) -> RpgSessionState:
        defaults: dict[str, object] = {
            "story_id": uuid4(),
            "character_sheet_id": uuid4(),
            "dice_handling": DiceHandling.AI_ROLLS,
        }
        defaults.update(kwargs)
        return RpgSessionState(**defaults)  # type: ignore[arg-type]

    def test_instantiation_valid(self) -> None:
        state = self._make()
        assert state.dice_handling == DiceHandling.AI_ROLLS
        assert state.active_quests == []
        assert isinstance(state.combat_context, CombatContext)

    def test_session_id_auto_generated(self) -> None:
        s1 = self._make()
        s2 = self._make()
        assert s1.session_id != s2.session_id

    def test_invalid_dice_handling(self) -> None:
        with pytest.raises(ValidationError):
            self._make(dice_handling="both")  # type: ignore[arg-type]

    def test_no_hp_field(self) -> None:
        """HP lives on the character sheet, not in RPG session state."""
        state = self._make()
        assert not hasattr(state, "current_hp")
        assert not hasattr(state, "maximum_hp")
        assert not hasattr(state, "hp")

    def test_no_spell_slots_field(self) -> None:
        """Spell slots live on the character sheet, not in RPG session state."""
        state = self._make()
        assert not hasattr(state, "spell_slots")

    def test_no_ability_scores_field(self) -> None:
        """Ability scores live on the character sheet, not in session state."""
        state = self._make()
        assert not hasattr(state, "ability_scores")
        assert not hasattr(state, "strength")
        assert not hasattr(state, "dexterity")

    def test_rpg_session_fields_not_on_base_node(self) -> None:
        """Mode-specific session state must not bleed into base Node schema."""
        from afterworlds.models.enums import IntentType

        node = Node(chapter_id=uuid4(), content="x", intent_type=IntentType.ACTION)
        assert not hasattr(node, "dice_handling")
        assert not hasattr(node, "active_quests")
        assert not hasattr(node, "combat_context")
        assert not hasattr(node, "character_sheet_id")


class TestBranchNode:
    def test_instantiation_valid(self) -> None:
        uid = uuid4()
        bn = BranchNode(node_id=uid)
        assert bn.node_id == uid
        assert bn.next_node_ids == []

    def test_with_next_nodes(self) -> None:
        n1, n2 = uuid4(), uuid4()
        bn = BranchNode(node_id=uuid4(), next_node_ids=[n1, n2])
        assert n1 in bn.next_node_ids


class TestBranchTree:
    def test_defaults(self) -> None:
        tree = BranchTree()
        assert tree.nodes == {}
        assert tree.root_node_id is None

    def test_with_nodes(self) -> None:
        uid = uuid4()
        bn = BranchNode(node_id=uid)
        tree = BranchTree(nodes={str(uid): bn}, root_node_id=uid)
        assert str(uid) in tree.nodes
        assert tree.root_node_id == uid


class TestPlotThread:
    def test_defaults(self) -> None:
        thread = PlotThread(description="Who killed the merchant?")
        assert thread.is_resolved is False
        assert thread.related_node_ids == []

    def test_populated(self) -> None:
        uid = uuid4()
        thread = PlotThread(
            description="The key's origin",
            is_resolved=True,
            related_node_ids=[uid],
        )
        assert thread.is_resolved is True
        assert uid in thread.related_node_ids


class TestBranchingSessionState:
    def _make(self, **kwargs: object) -> BranchingSessionState:
        defaults: dict[str, object] = {
            "story_id": uuid4(),
            "pacing_stage": PacingStage.SETUP,
        }
        defaults.update(kwargs)
        return BranchingSessionState(**defaults)  # type: ignore[arg-type]

    def test_instantiation_valid(self) -> None:
        state = self._make()
        assert state.pacing_stage == PacingStage.SETUP
        assert isinstance(state.branch_tree, BranchTree)
        assert state.plot_thread_tracker == []
        assert state.current_node_id is None

    def test_has_branch_tree_as_structured_model(self) -> None:
        """branch_tree must be a distinct structured model, not a plain dict."""
        state = self._make()
        assert hasattr(state, "branch_tree")
        assert isinstance(state.branch_tree, BranchTree)

    def test_has_plot_thread_tracker(self) -> None:
        """plot_thread_tracker is a distinct structured field."""
        thread = PlotThread(description="Open thread")
        state = self._make(plot_thread_tracker=[thread])
        assert len(state.plot_thread_tracker) == 1
        assert isinstance(state.plot_thread_tracker[0], PlotThread)

    def test_all_pacing_stages_valid(self) -> None:
        for stage in PacingStage:
            s = self._make(pacing_stage=stage)
            assert s.pacing_stage == stage

    def test_invalid_pacing_stage(self) -> None:
        with pytest.raises(ValidationError):
            self._make(pacing_stage="invalid")  # type: ignore[arg-type]

    def test_session_id_auto_generated(self) -> None:
        s1 = self._make()
        s2 = self._make()
        assert s1.session_id != s2.session_id


class TestWritingSessionState:
    def _make(self, **kwargs: object) -> WritingSessionState:
        defaults: dict[str, object] = {"story_id": uuid4()}
        defaults.update(kwargs)
        return WritingSessionState(**defaults)  # type: ignore[arg-type]

    def test_instantiation_valid(self) -> None:
        state = self._make()
        assert state.beat_constraints == []
        assert state.version_history_pointers == []
        assert state.persona is None

    def test_with_beat_constraints(self) -> None:
        state = self._make(beat_constraints=["protagonist learns the truth"])
        assert "protagonist learns the truth" in state.beat_constraints

    def test_with_version_pointers(self) -> None:
        uid = uuid4()
        state = self._make(version_history_pointers=[uid])
        assert uid in state.version_history_pointers

    def test_persona_optional(self) -> None:
        state = self._make(persona=None)
        assert state.persona is None

    def test_persona_set(self) -> None:
        state = self._make(persona=WritingPersona.CHIRON)
        assert state.persona == WritingPersona.CHIRON

    def test_all_personas_valid(self) -> None:
        for persona in WritingPersona:
            s = self._make(persona=persona)
            assert s.persona == persona

    def test_invalid_persona(self) -> None:
        with pytest.raises(ValidationError):
            self._make(persona="unknown_persona")  # type: ignore[arg-type]

    def test_session_id_auto_generated(self) -> None:
        s1 = self._make()
        s2 = self._make()
        assert s1.session_id != s2.session_id
