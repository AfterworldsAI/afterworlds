"""RPG Adjudication pass tool specification — CRD Issue 15.

The adjudication pass uses forced tool use to obtain a structured
``AdjudicationProposalOutput``.  The tool schema enforces the roll-authorship
invariant at the schema level: ``RollProposal`` carries no result, DC, or
numeric modifier field, making it structurally impossible for the model to
embed a trust-relevant number in a proposal.
"""

from __future__ import annotations

from typing import Any

from afterworlds.ingestion.mechanical.representation import (
    AbilityScore,
    Difficulty,
    Skill,
    ToolActivity,
)
from afterworlds.pipeline.rpg.capability import (
    FIXED_DC_CHECKS,
    TOOL_COMPONENTS,
    Operation,
)


def _selection(values: list[str], description: str) -> dict[str, Any]:
    return {
        "oneOf": [{"type": "string", "enum": values}, {"type": "null"}],
        "description": description,
    }


PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME: str = "produce_adjudication_proposals"

PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC: dict[str, Any] = {
    "name": PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME,
    "description": (
        "Identify which dice rolls are mechanically required this turn and"
        " propose them for resolution by the d20 adjudication engine."
        " Call this tool exactly once.  Never embed a roll result, DC, or"
        " numeric modifier value in any field — the engine resolves all"
        " numbers from the character sheet and rules package."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "rolls": {
                "type": "array",
                "description": (
                    "Ordered list of roll proposals for this turn.  Empty array"
                    " when no mechanical roll is required."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "check_label": {
                            "type": "string",
                            "description": (
                                "Short human-readable label for this check"
                                " (e.g. 'Stealth Check', 'Dexterity Save')."
                                " Non-empty."
                            ),
                        },
                        "subsystem_tag": {
                            "type": "string",
                            "description": (
                                "Mechanical subsystem tag used by the adapter to"
                                " route resolution (e.g. 'skill_check',"
                                " 'saving_throw', 'attack_roll',"
                                " 'skill_check advantage')."
                            ),
                        },
                        "skill_or_attribute_label": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "null"},
                            ],
                            "description": (
                                "The specific skill or ability score governing"
                                " this check (e.g. 'stealth', 'dexterity')."
                                " Null when not applicable."
                            ),
                        },
                        "visible_modifier_note": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "null"},
                            ],
                            "description": (
                                "Non-authoritative narrative note about visible"
                                " modifiers (e.g. 'proficient').  The engine"
                                " computes the actual modifier; this is for"
                                " narrative context only.  Null when absent."
                            ),
                        },
                        "difficulty_reference_note": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "null"},
                            ],
                            "description": (
                                "Non-authoritative narrative hint about"
                                " difficulty (e.g. 'moderate task').  NEVER"
                                " used as a DC by the engine.  Null when"
                                " absent."
                            ),
                        },
                        "operation": {
                            "type": "string",
                            "enum": [o.value for o in Operation],
                            "description": (
                                "The roster operation this roll is. Required"
                                " for every mechanical roll: the engine runs"
                                " only a named, admitted operation and refuses"
                                " anything else visibly."
                            ),
                        },
                        "check_identity": {
                            "oneOf": [
                                {
                                    "type": "string",
                                    "enum": [
                                        "/".join(i)
                                        for i in (*FIXED_DC_CHECKS, *TOOL_COMPONENTS)
                                    ],
                                },
                                {"type": "null"},
                            ],
                            "description": (
                                "For fixed_dc_check: the source rule whose"
                                " printed check applies. For tool_check: the"
                                " tool. The engine reads the ability and DC"
                                " from the source. Null otherwise."
                            ),
                        },
                        "ability": _selection(
                            [a.value for a in AbilityScore],
                            "For difficulty_check: the ability the check uses.",
                        ),
                        "skill": _selection(
                            [k.value for k in Skill],
                            "For difficulty_check: the skill that applies, if any;"
                            " it must be one the ability governs.",
                        ),
                        "difficulty": _selection(
                            [d.value for d in Difficulty],
                            "For difficulty_check: the Typical DC you select. The"
                            " engine reads the DC from the rules.",
                        ),
                        "tool_activity": _selection(
                            [t.value for t in ToolActivity],
                            "For tool_check: the tool's printed activity.",
                        ),
                        "visibility": {
                            "type": "string",
                            "enum": ["shown", "hidden", "player"],
                            "description": (
                                "Who sees the result."
                                " 'shown' — AI roll, result shown to player."
                                " 'hidden' — backend only; result nulled in"
                                " player-facing output."
                                " 'player' — player rolls physically and"
                                " reports the total next turn."
                            ),
                        },
                    },
                    "required": [
                        "check_label",
                        "subsystem_tag",
                        "operation",
                        "visibility",
                    ],
                },
            },
            "reasoning_note": {
                "oneOf": [{"type": "string"}, {"type": "null"}],
                "description": (
                    "Optional brief reasoning note for why these rolls are"
                    " required.  Not forwarded to the Writer.  Null when absent."
                ),
            },
        },
        "required": ["rolls"],
    },
}


__all__ = [
    "PRODUCE_ADJUDICATION_PROPOSALS_TOOL_NAME",
    "PRODUCE_ADJUDICATION_PROPOSALS_TOOL_SPEC",
]
