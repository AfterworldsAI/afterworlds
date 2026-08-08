"""Afterworlds core data models.

Public re-exports for convenient import by other modules.
"""

from afterworlds.models.character_sheet import (
    Dnd5eAbilityScores,
    Dnd5eActiveCondition,
    Dnd5eCharacterSheet,
    RpgCharacterSheetBase,
    SpellSlotLevel,
)
from afterworlds.models.context import (
    AssembledContext,
    PassForwardEntry,
    PassForwardLedger,
    StablePrefix,
    VolatileSuffix,
)
from afterworlds.models.enums import (
    ConditionVisibility,
    CritiqueIntensity,
    DiceHandling,
    IntentType,
    PacingStage,
    RollVisibility,
    RpgPlayStatus,
    RpgSessionType,
    RpgSetupPhase,
    RpgTone,
    StoryMode,
    StyleDensity,
    WritingCanonEligibility,
    WritingForm,
    WritingPlayStatus,
    WritingVersionPointerKind,
    WritingWorkProductKind,
)
from afterworlds.models.node import (
    BranchingNodeMetadata,
    ModeMetadata,
    Node,
    NodeMetadata,
    RpgNodeMetadata,
    StateDelta,
    WritingNodeMetadata,
)
from afterworlds.models.rpg import (
    AdjudicationProposalOutput,
    DiceResult,
    PendingRollRequest,
    ResolvedAdjudicationRecord,
    RollProposal,
    RpgVisibleState,
    SheetEffect,
    VisibleCharacterState,
    VisibleItem,
    VisibleLocation,
    VisibleRelationship,
    WriterAdjudicationView,
)
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.models.session import (
    BranchingSessionState,
    BranchNode,
    BranchTree,
    CombatContext,
    PlotThread,
    RpgSessionState,
    WritingSessionState,
)
from afterworlds.models.state import (
    CharacterState,
    CharacterStateDynamicPartition,
    CharacterStateStaticPartition,
    WorldState,
    WorldStateDynamicPartition,
    WorldStateStaticPartition,
)
from afterworlds.models.story import Arc, Chapter, Story
from afterworlds.models.turn import Turn

__all__ = [
    # enums
    "ConditionVisibility",
    "CritiqueIntensity",
    "DiceHandling",
    "IntentType",
    "PacingStage",
    "RollVisibility",
    "RpgPlayStatus",
    "RpgSessionType",
    "RpgSetupPhase",
    "RpgTone",
    "StoryMode",
    "StyleDensity",
    "WritingCanonEligibility",
    "WritingForm",
    "WritingPlayStatus",
    "WritingVersionPointerKind",
    "WritingWorkProductKind",
    # story hierarchy
    "Story",
    "Arc",
    "Chapter",
    # node
    "StateDelta",
    "NodeMetadata",
    "RpgNodeMetadata",
    "BranchingNodeMetadata",
    "WritingNodeMetadata",
    "ModeMetadata",
    "Node",
    # turn
    "Turn",
    # state
    "WorldStateStaticPartition",
    "WorldStateDynamicPartition",
    "WorldState",
    "CharacterStateStaticPartition",
    "CharacterStateDynamicPartition",
    "CharacterState",
    # session
    "CombatContext",
    "RpgSessionState",
    "BranchNode",
    "BranchTree",
    "PlotThread",
    "BranchingSessionState",
    "WritingSessionState",
    # context builder types
    "StablePrefix",
    "VolatileSuffix",
    "PassForwardEntry",
    "PassForwardLedger",
    "AssembledContext",
    # rules package
    "RuleSliceRequest",
    "RulesPackageBinding",
    # character sheet
    "Dnd5eAbilityScores",
    "Dnd5eActiveCondition",
    "SpellSlotLevel",
    "RpgCharacterSheetBase",
    "Dnd5eCharacterSheet",
    # RPG adjudication DTOs (Issue 15)
    "AdjudicationProposalOutput",
    "DiceResult",
    "PendingRollRequest",
    "ResolvedAdjudicationRecord",
    "RollProposal",
    "RpgVisibleState",
    "SheetEffect",
    "VisibleCharacterState",
    "VisibleItem",
    "VisibleLocation",
    "VisibleRelationship",
    "WriterAdjudicationView",
]
