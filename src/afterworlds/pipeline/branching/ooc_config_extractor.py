"""Branching OOC config extractor — CRD Issue 16 Phase F.

Extracts ``BranchingConfigUpdate`` from an OOC turn via forced tool use.
Called after the OOC prose Writer succeeds, inside the same transaction.

Responsibilities:
  1. Build a minimal ``ProviderCallRequest`` using the user's OOC message as
     content.  No stable-prefix reuse (short extraction pass, no cache needed).
  2. Force-call the ``extract_branching_config_update`` tool.
  3. Parse and validate the tool output into ``BranchingConfigUpdate``.
  4. Raise ``BranchingPassError`` on provider, parse, or schema failures.

The caller (orchestrator ``_ooc_persist``) is responsible for:
  - Validating the result against ``ALLOWED_RANGES_BY_STYLE``.
  - Applying the update inside the OOC transaction via
    ``apply_branching_config_update``.
  - Treating failures as best-effort (skipping persistence on error).

V1 scope: extracts from user's OOC message only; does not see the writer's
prose response.  Writer/validation reconciliation is deferred to v2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.pipeline._stable_prefix_renderer import RenderedBlock
from afterworlds.pipeline.branching.models import (
    BranchingConfigUpdate,
    BranchingPassError,
)
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderToolCallPart,
    ProviderToolDefinition,
)

if TYPE_CHECKING:
    from afterworlds.models.context import AssembledContext
    from afterworlds.pipeline.provider._protocol import ProviderAdapter


# ---------------------------------------------------------------------------
# Tool specification
# ---------------------------------------------------------------------------

EXTRACT_CONFIG_UPDATE_TOOL_NAME: str = "extract_branching_config_update"

EXTRACT_CONFIG_UPDATE_TOOL_SPEC: dict[str, Any] = {
    "name": EXTRACT_CONFIG_UPDATE_TOOL_NAME,
    "description": (
        "Extract any branching story configuration changes the player explicitly"
        " requested in their out-of-character (OOC) message."
        " Set each field to null if the player did not explicitly request that"
        " field to change.  Do not infer changes that were not stated."
        " Call this tool exactly once."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "interaction_style": {
                "oneOf": [
                    {
                        "type": "string",
                        "enum": ["freeform_only", "hybrid", "true_cyoa"],
                        "description": (
                            "The requested interaction style."
                            " 'freeform_only' = no branch cards, pure narrative prose."
                            " 'hybrid' = narrative prose plus optional branch cards."
                            " 'true_cyoa' = branch cards required every beat."
                        ),
                    },
                    {"type": "null"},
                ],
                "description": "Null if the player did not request a style change.",
            },
            "branching_cadence": {
                "oneOf": [
                    {
                        "type": "string",
                        "enum": ["interactive", "balanced", "immersive"],
                        "description": (
                            "'interactive' = branch cards every beat."
                            " 'balanced' = branch cards most beats."
                            " 'immersive' = branch cards selectively."
                        ),
                    },
                    {"type": "null"},
                ],
                "description": "Null if the player did not request a cadence change.",
            },
            "branch_count_range": {
                "oneOf": [
                    {
                        "type": "string",
                        "enum": ["1-2", "2-3", "3-4", "2-4", "2-5"],
                        "description": (
                            "Range of branch options per beat."
                            " Hybrid supports: 1-2, 2-3, 3-4."
                            " True CYOA supports: 2-3, 2-4, 2-5."
                        ),
                    },
                    {"type": "null"},
                ],
                "description": (
                    "Null if the player did not request a branch count change."
                ),
            },
            "length_preference": {
                "oneOf": [
                    {
                        "type": "string",
                        "enum": ["short_story", "novella", "novel"],
                        "description": (
                            "Preferred narrative response length per beat."
                            " 'short_story' = concise."
                            " 'novella' = moderate."
                            " 'novel' = detailed."
                        ),
                    },
                    {"type": "null"},
                ],
                "description": ("Null if the player did not request a length change."),
            },
        },
        "required": [
            "interaction_style",
            "branching_cadence",
            "branch_count_range",
            "length_preference",
        ],
    },
}

_EXTRACT_TOOL_DEF = ProviderToolDefinition(
    name=EXTRACT_CONFIG_UPDATE_TOOL_NAME,
    description=EXTRACT_CONFIG_UPDATE_TOOL_SPEC["description"],
    input_schema=EXTRACT_CONFIG_UPDATE_TOOL_SPEC["input_schema"],
)

_EXTRACTION_SYSTEM_PROMPT: str = (
    "You are a configuration extractor for a branching interactive story system."
    " The player has sent an out-of-character (OOC) message."
    " Your task is to identify and extract any explicit branching configuration"
    " changes the player requested."
    " Use the extract_branching_config_update tool to report what was requested."
    " Set fields to null for anything the player did not explicitly ask to change."
)

_MAX_OUTPUT_TOKENS: int = 256


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class BranchingOocConfigExtractorService:
    """Extracts BranchingConfigUpdate from an OOC turn via forced tool use.

    Stateless — construct once and reuse.
    """

    def extract(
        self,
        ctx: AssembledContext,
        provider: ProviderAdapter,
    ) -> BranchingConfigUpdate:
        """Run the config extraction pass and return a structured update.

        The returned ``BranchingConfigUpdate`` may have all-None fields when
        the player's OOC message contained no config change request.

        Args:
            ctx: AssembledContext for the current OOC turn.
            provider: ProviderAdapter for the forced-tool LLM call.

        Returns:
            BranchingConfigUpdate with non-None fields for each change requested.

        Raises:
            BranchingPassError: on provider error, missing tool block, tool name
                mismatch, or schema validation failure.
        """
        request = self._render(ctx)

        try:
            result = provider.call(request)
        except Exception as exc:
            raise BranchingPassError(
                f"Branching OOC config extractor provider call failed: {exc}"
            ) from exc

        tool_parts = [
            p for p in result.content_parts if isinstance(p, ProviderToolCallPart)
        ]
        if not tool_parts:
            raise BranchingPassError(
                "Branching OOC config extractor response missing tool-use block"
            )
        if tool_parts[0].tool_name != EXTRACT_CONFIG_UPDATE_TOOL_NAME:
            raise BranchingPassError(
                f"Branching OOC config extractor unexpected tool name:"
                f" {tool_parts[0].tool_name!r};"
                f" expected {EXTRACT_CONFIG_UPDATE_TOOL_NAME!r}"
            )

        try:
            update = BranchingConfigUpdate.model_validate(tool_parts[0].tool_input)
        except Exception as exc:
            raise BranchingPassError(
                f"Branching OOC config extractor tool input failed schema validation:"
                f" {exc}"
            ) from exc

        return update

    def _render(self, ctx: AssembledContext) -> ProviderCallRequest:
        """Build a minimal ProviderCallRequest for the extraction pass."""
        vs = ctx.volatile_suffix
        content_block = RenderedBlock(
            text=f"Player (OOC): {vs.current_input}",
        )
        return ProviderCallRequest(
            pass_id=PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR,
            system_blocks=[RenderedBlock(text=_EXTRACTION_SYSTEM_PROMPT)],
            rendered_blocks=[content_block],
            max_output_tokens=_MAX_OUTPUT_TOKENS,
            tool_definitions=[_EXTRACT_TOOL_DEF],
            forced_tool_name=EXTRACT_CONFIG_UPDATE_TOOL_NAME,
        )


__all__ = [
    "BranchingOocConfigExtractorService",
    "EXTRACT_CONFIG_UPDATE_TOOL_NAME",
    "EXTRACT_CONFIG_UPDATE_TOOL_SPEC",
]
