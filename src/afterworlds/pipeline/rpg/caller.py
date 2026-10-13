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

_SUBJECT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["character", "creature"]},
        "subject_id": {"type": "string", "format": "uuid"},
    },
    "required": ["kind", "subject_id"],
    "additionalProperties": False,
}
_LIGHT = ["bright", "dim", "darkness", "magical_darkness", "heavily_obscured"]
_CREATURE_ATTACK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "attacker": _SUBJECT_SCHEMA,
        "entry": {"type": "string"},
        "target": _SUBJECT_SCHEMA,
        "range": {
            "type": "string",
            "enum": [
                "within_reach",
                "within_normal_range",
                "beyond_normal_within_long_range",
                "beyond_long_range",
            ],
        },
        "cover": {
            "type": "string",
            "enum": ["none", "half", "three_quarters", "total"],
        },
        "attacker_light": {"type": "string", "enum": _LIGHT},
        "target_light": {"type": "string", "enum": _LIGHT},
        "hostile_within_5_feet": {"oneOf": [{"type": "boolean"}, {"type": "null"}]},
        "target_within_5_feet": {"oneOf": [{"type": "boolean"}, {"type": "null"}]},
        "ally_within_5_feet_of_target": {
            "oneOf": [{"type": "boolean"}, {"type": "null"}]
        },
        "multiattack": {"type": "boolean"},
    },
    "required": [
        "attacker",
        "entry",
        "target",
        "range",
        "cover",
        "attacker_light",
        "target_light",
    ],
    "additionalProperties": False,
}
_WEAPON_ATTACK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "weapon_item_id": {"type": "string", "format": "uuid"},
        "target": _SUBJECT_SCHEMA,
        "range": {
            "type": "string",
            "enum": [
                "within_reach",
                "within_normal_range",
                "beyond_normal_within_long_range",
                "beyond_long_range",
            ],
        },
        "cover": {
            "type": "string",
            "enum": ["none", "half", "three_quarters", "total"],
        },
        "attacker_light": {"type": "string", "enum": _LIGHT},
        "target_light": {"type": "string", "enum": _LIGHT},
        "hostile_within_5_feet": {"oneOf": [{"type": "boolean"}, {"type": "null"}]},
        "target_within_5_feet": {"oneOf": [{"type": "boolean"}, {"type": "null"}]},
        "two_handed": {"type": "boolean"},
        "knock_out": {"type": "boolean"},
        "mastery": {"type": "boolean"},
        "cleave": {"type": "boolean"},
        "extra": {
            "oneOf": [{"type": "string", "enum": ["light", "nick"]}, {"type": "null"}]
        },
        "cleave_within_5_feet": {"oneOf": [{"type": "boolean"}, {"type": "null"}]},
        "push_ft": {"oneOf": [{"type": "integer", "enum": [5, 10]}, {"type": "null"}]},
        "thrown": {"type": "boolean"},
        "ability": {
            "oneOf": [
                {"type": "string", "enum": [a.value for a in AbilityScore]},
                {"type": "null"},
            ]
        },
    },
    "required": [
        "weapon_item_id",
        "target",
        "range",
        "cover",
        "attacker_light",
        "target_light",
    ],
    "additionalProperties": False,
}


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
                        "weapon_attack": {
                            "oneOf": [_WEAPON_ATTACK_SCHEMA, {"type": "null"}],
                            "description": (
                                "For weapon_attack: the weapon (an item id the"
                                " attacker holds), the target, and the"
                                " contextual facts you select. The engine reads"
                                " every number from the rules and the sheets."
                            ),
                        },
                        "subject": {
                            "oneOf": [_SUBJECT_SCHEMA, {"type": "null"}],
                            "description": (
                                "For begin_turn and end_turn: the character or"
                                " creature whose turn begins or ends. Null"
                                " otherwise."
                            ),
                        },
                        "creature_attack": {
                            "oneOf": [_CREATURE_ATTACK_SCHEMA, {"type": "null"}],
                            "description": (
                                "For creature_attack: the attacking creature, one"
                                " of its attack entries from the scene, the target"
                                " and the contextual facts you select."
                            ),
                        },
                        "creature_save_effect": {
                            "oneOf": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "source": _SUBJECT_SCHEMA,
                                        "entry": {"type": "string"},
                                        "targets": {
                                            "type": "array",
                                            "items": _SUBJECT_SCHEMA,
                                            "minItems": 1,
                                        },
                                    },
                                    "required": ["source", "entry", "targets"],
                                    "additionalProperties": False,
                                },
                                {"type": "null"},
                            ],
                            "description": (
                                "For creature_save_effect: the creature, one of its"
                                " save-effect entries from the scene, and every"
                                " creature in its area."
                            ),
                        },
                        "attestation": {
                            "oneOf": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "instance_id": {"type": "string"},
                                        "elapsed_hours": {
                                            "oneOf": [
                                                {
                                                    "type": "integer",
                                                    "enum": [1, 2, 3, 4],
                                                },
                                                {"type": "null"},
                                            ]
                                        },
                                    },
                                    "required": ["instance_id"],
                                    "additionalProperties": False,
                                },
                                {"type": "null"},
                            ],
                            "description": (
                                "For stable_recovery: the recovery instance and the"
                                " total hours since it began (4 means four or more)."
                                " For knockout_recovery: the knockout's condition"
                                " instance, whose Short Rest was completed. Null"
                                " otherwise."
                            ),
                        },
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
