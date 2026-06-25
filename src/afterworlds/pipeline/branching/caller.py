"""Branching Writer pass tool specification — CRD Issue 16.

The Branching Writer pass uses forced tool use to obtain a structured
``BranchingWriterProposal``.  The tool schema enforces the code-owns-affordances
invariant at the schema level:

- ``option_id`` is absent from the schema — code assigns sequential IDs.
- ``interaction_style``, ``branching_cadence``, ``freeform_available``, and
  ``branch_count_range`` are absent — all stamped from session state by code.
- Branch option count is NOT specified in the schema — code validates the count
  against the session's ``branch_count_range``; the model must propose within
  the configured range but the schema cannot enforce the exact numeric bounds
  without knowing the session configuration at schema-build time.

The model proposes:
- narrative prose (``narrative_text``)
- branch option labels only (``branch_options_text``, list of strings)
- presentation state for this beat (``branch_presentation_state``)
- an optional advisory pacing hint (``pacing_stage_hint``)
"""

from __future__ import annotations

from typing import Any

PRODUCE_BRANCH_OUTPUT_TOOL_NAME: str = "produce_branch_output"

PRODUCE_BRANCH_OUTPUT_TOOL_SPEC: dict[str, Any] = {
    "name": PRODUCE_BRANCH_OUTPUT_TOOL_NAME,
    "description": (
        "Produce the narrative text and branch option labels for this beat."
        " Call this tool exactly once."
        " You propose narrative prose and action-text labels only."
        " Do NOT propose option IDs, branch counts, interaction style,"
        " freeform availability, or cadence — those are code-owned from the"
        " session configuration and are stamped by the system after validation."
        " The number of branch options you propose must match the configured"
        " branch_count_range for this session."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "narrative_text": {
                "type": "string",
                "description": (
                    "The prose narrative for this beat."
                    " Respond as the story architect — third-person present"
                    " or the mode-appropriate voice."
                    " Non-empty."
                ),
            },
            "branch_options_text": {
                "type": "array",
                "description": (
                    "Ordered list of branch option labels for this beat."
                    " Each entry is a short action phrase that the Sojourner"
                    " could select (e.g. 'Cross the rope bridge')."
                    " The count must match the configured branch_count_range."
                    " Omit this array entirely (or set to []) only when"
                    " branch_presentation_state is 'held' or 'omitted'."
                ),
                "items": {
                    "type": "string",
                    "description": "Short action phrase for one branch option.",
                },
            },
            "branch_presentation_state": {
                "type": "string",
                "enum": ["shown", "held", "omitted"],
                "description": (
                    "'shown' — present branch options to the Sojourner now."
                    " 'held' — narrative tension warrants withholding options"
                    " until this beat resolves; options come in the next beat."
                    " 'omitted' — no branch options this beat (pacing decision)."
                    " Use 'shown' for the majority of beats."
                ),
            },
            "pacing_stage_hint": {
                "oneOf": [{"type": "string"}, {"type": "null"}],
                "description": (
                    "Optional advisory hint about the current arc stage"
                    " (e.g. 'escalation', 'climax')."
                    " Non-authoritative — code does not use this for routing."
                    " Null when absent."
                ),
            },
        },
        "required": [
            "narrative_text",
            "branch_options_text",
            "branch_presentation_state",
        ],
    },
}


__all__ = [
    "PRODUCE_BRANCH_OUTPUT_TOOL_NAME",
    "PRODUCE_BRANCH_OUTPUT_TOOL_SPEC",
]
