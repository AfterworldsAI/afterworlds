"""Writing-mode OOC config extractor — CRD Issue 17.

Extracts ``WritingConfigUpdate`` from an OOC turn via forced tool use.
Called after the OOC prose Writer succeeds, inside the same transaction.

Responsibilities:
  1. Build a minimal ``ProviderCallRequest`` using the user's OOC message.
     No stable-prefix reuse (short extraction pass, no cache needed).
  2. Force-call the ``extract_writing_config_update`` tool.
  3. Parse and validate the tool output into ``WritingConfigUpdate``.
  4. Raise ``WritingPassError`` on provider failures before any result.
  5. Raise ``WritingOocExtractionUsageError`` on parse/schema failures
     after the provider returned (tokens consumed).

The caller (orchestrator ``_ooc_persist``) is responsible for:
  - Applying the update inside the OOC transaction via
    ``apply_writing_config_update``.
  - Treating failures as best-effort (skipping persistence on error).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.pipeline._stable_prefix_renderer import RenderedBlock
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderToolCallPart,
    ProviderToolDefinition,
)
from afterworlds.pipeline.writing.models import (
    WritingConfigUpdate,
    WritingOocConfigExtractorResult,
    WritingOocExtractionUsageError,
    WritingPassError,
)

if TYPE_CHECKING:
    from afterworlds.models.context import AssembledContext
    from afterworlds.pipeline.provider._protocol import ProviderAdapter


# ---------------------------------------------------------------------------
# Tool specification
# ---------------------------------------------------------------------------

EXTRACT_WRITING_CONFIG_TOOL_NAME: str = "extract_writing_config_update"

EXTRACT_WRITING_CONFIG_TOOL_SPEC: dict[str, Any] = {
    "name": EXTRACT_WRITING_CONFIG_TOOL_NAME,
    "description": (
        "Extract any Writing mode configuration changes the Sojourner explicitly"
        " requested in their out-of-character (OOC) message."
        " Set each field to null if the Sojourner did not explicitly request that"
        " field to change. Do not infer changes that were not stated."
        " Call this tool exactly once."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "persona_id": {
                "oneOf": [
                    {
                        "type": "string",
                        "description": (
                            "The slug of the requested writing persona"
                            " (e.g. 'chiron', 'athena', 'odin')."
                        ),
                    },
                    {"type": "null"},
                ],
                "description": "Null if the Sojourner did not request a persona change.",  # noqa: E501
            },
            "play_status": {
                "oneOf": [
                    {
                        "type": "string",
                        "enum": ["setup", "in_play"],
                        "description": (
                            "'in_play' when the Sojourner explicitly confirms"
                            " they are ready to begin writing."
                        ),
                    },
                    {"type": "null"},
                ],
                "description": "Null if play status was not explicitly changed.",
            },
            "critique_intensity": {
                "oneOf": [
                    {
                        "type": "string",
                        "enum": ["gentle", "balanced", "blunt", "ruthless"],
                        "description": (
                            "Requested critique intensity."
                            " 'gentle' = encouraging, minimal criticism."
                            " 'balanced' = mixed feedback."
                            " 'blunt' = direct, unvarnished."
                            " 'ruthless' = no softening."
                        ),
                    },
                    {"type": "null"},
                ],
                "description": "Null if not explicitly requested.",
            },
            "form": {
                "oneOf": [
                    {
                        "type": "string",
                        "enum": [
                            "short_story",
                            "novel",
                            "narrative_nonfiction",
                            "memoir",
                            "screenplay",
                            "other",
                        ],
                        "description": "The writing form/genre category.",
                    },
                    {"type": "null"},
                ],
                "description": "Null if not explicitly requested.",
            },
            "form_other": {
                "oneOf": [
                    {
                        "type": "string",
                        "description": "Free-text form description when form='other'.",
                    },
                    {"type": "null"},
                ],
                "description": "Null unless form is 'other'.",
            },
            "tense": {
                "oneOf": [
                    {
                        "type": "string",
                        "description": "Requested narrative tense (e.g. 'past', 'present').",  # noqa: E501
                    },
                    {"type": "null"},
                ],
                "description": "Null if not explicitly requested.",
            },
            "pov": {
                "oneOf": [
                    {
                        "type": "string",
                        "description": (
                            "Requested point of view"
                            " (e.g. 'first person', 'third limited', 'third omniscient')."  # noqa: E501
                        ),
                    },
                    {"type": "null"},
                ],
                "description": "Null if not explicitly requested.",
            },
            "style_density": {
                "oneOf": [
                    {
                        "type": "string",
                        "enum": ["sparse", "balanced", "lush", "literary", "pulp"],
                        "description": (
                            "Prose density preference."
                            " 'sparse' = minimal, lean."
                            " 'balanced' = moderate."
                            " 'lush' = rich description."
                            " 'literary' = elevated, complex."
                            " 'pulp' = fast-paced, genre-forward."
                        ),
                    },
                    {"type": "null"},
                ],
                "description": "Null if not explicitly requested.",
            },
            "dialogue_narration_ratio": {
                "oneOf": [
                    {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Percentage of dialogue vs. narration (0=all narration, 100=all dialogue).",  # noqa: E501
                    },
                    {"type": "null"},
                ],
                "description": "Null if not explicitly requested.",
            },
            "genre_conventions": {
                "oneOf": [
                    {
                        "type": "string",
                        "description": "Genre conventions or subgenre notes to follow.",
                    },
                    {"type": "null"},
                ],
                "description": "Null if not explicitly requested.",
            },
            "specific_goals": {
                "oneOf": [
                    {
                        "type": "string",
                        "description": "Sojourner's stated writing goals for this session.",  # noqa: E501
                    },
                    {"type": "null"},
                ],
                "description": "Null if not explicitly stated.",
            },
            "acceptable_content": {
                "oneOf": [
                    {
                        "type": "string",
                        "description": "Content rating or explicit content preferences.",  # noqa: E501
                    },
                    {"type": "null"},
                ],
                "description": "Null if not explicitly requested.",
            },
            "beat_constraints": {
                "oneOf": [
                    {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Full replacement list of beat constraints the Sojourner"
                            " explicitly stated (e.g. 'no deus ex machina',"
                            " 'protagonist must earn every victory')."
                            " Provide only constraints the Sojourner explicitly"
                            " named; do not infer structural rules."
                        ),
                    },
                    {"type": "null"},
                ],
                "description": (
                    "Null unless the Sojourner explicitly set or replaced"
                    " beat constraints."
                ),
            },
            "version_pointers": {
                "oneOf": [
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "kind": {
                                    "type": "string",
                                    "enum": [
                                        "turn",
                                        "node",
                                        "draft_label",
                                        "generated_candidate",
                                        "working_segment",
                                    ],
                                    "description": (
                                        "The kind of version reference."
                                        " Use 'draft_label' for named drafts,"
                                        " 'working_segment' for a named section."
                                    ),
                                },
                                "label": {
                                    "type": "string",
                                    "description": (
                                        "A short human-readable label"
                                        " (e.g. 'Chapter 1 v2', 'Opening draft')."
                                    ),
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Optional longer description.",
                                },
                            },
                            # pointer_id and created_at are NOT in required —
                            # the DTO default_factory fills them so the model is
                            # never invited to hallucinate UUIDs (ADR-017 Dec. 10
                            # v1 boundary: lightweight provenance only).
                            "required": ["kind", "label"],
                            "additionalProperties": False,
                        },
                        "description": (
                            "New version pointers to add to this session."
                            " Append-only; existing pointers are preserved."
                            " Only include pointers the Sojourner explicitly"
                            " named or labelled."
                        ),
                    },
                    {"type": "null"},
                ],
                "description": (
                    "Null unless the Sojourner explicitly created a version label"
                    " or reference."
                ),
            },
        },
        "required": [
            "persona_id",
            "play_status",
            "critique_intensity",
            "form",
            "form_other",
            "tense",
            "pov",
            "style_density",
            "dialogue_narration_ratio",
            "genre_conventions",
            "specific_goals",
            "acceptable_content",
            "beat_constraints",
            "version_pointers",
        ],
    },
}

_EXTRACT_TOOL_DEF = ProviderToolDefinition(
    name=EXTRACT_WRITING_CONFIG_TOOL_NAME,
    description=EXTRACT_WRITING_CONFIG_TOOL_SPEC["description"],
    input_schema=EXTRACT_WRITING_CONFIG_TOOL_SPEC["input_schema"],
)

_EXTRACTION_SYSTEM_PROMPT: str = (
    "You are a configuration extractor for a writing-collaboration system."
    " The Sojourner has sent an out-of-character (OOC) message requesting"
    " changes to their writing session configuration."
    " Your task is to identify and extract any explicit configuration changes"
    " the Sojourner requested."
    " Use the extract_writing_config_update tool to report what was requested."
    " Set all fields to null for anything the Sojourner did not explicitly ask to"
    " change."
    " Do not infer intent; only extract what was stated."
)

_MAX_OUTPUT_TOKENS: int = 512


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class WritingOocConfigExtractorService:
    """Extracts WritingConfigUpdate from a Writing OOC turn via forced tool use.

    Stateless — construct once and reuse.
    """

    def extract(
        self,
        ctx: AssembledContext,
        provider: ProviderAdapter,
    ) -> WritingOocConfigExtractorResult:
        """Run the config extraction pass and return a typed result with metrics.

        The ``config_update`` in the result may have all-None fields when the
        Sojourner's OOC message contained no config change request.

        Args:
            ctx: AssembledContext for the current OOC turn.
            provider: ProviderAdapter for the forced-tool LLM call.

        Returns:
            WritingOocConfigExtractorResult with config_update and provider
            usage metrics for entitlement settlement.

        Raises:
            WritingPassError: on a provider error raised before any result.
            WritingOocExtractionUsageError: on a missing tool block, tool name
                mismatch, or schema validation failure after the provider
                returned a result. Carries a usage-only result so already-
                consumed provider usage is preserved for settlement.
        """
        request = self._render(ctx)

        try:
            call_result = provider.call(request)
        except Exception as exc:
            raise WritingPassError(
                f"Writing OOC config extractor provider call failed: {exc}"
            ) from exc

        usage_only = WritingOocConfigExtractorResult(
            config_update=WritingConfigUpdate(),
            provider=call_result.provider_name,
            model_identifier=call_result.model_identifier,
            model_tier=call_result.model_tier.value if call_result.model_tier else None,
            latency_ms=call_result.latency_ms,
            input_token_count=call_result.input_token_count,
            output_token_count=call_result.output_token_count,
            cache_read_token_count=call_result.cache_read_token_count,
            cache_creation_token_count=call_result.cache_creation_token_count,
        )

        tool_parts = [
            p for p in call_result.content_parts if isinstance(p, ProviderToolCallPart)
        ]
        if not tool_parts:
            raise WritingOocExtractionUsageError(
                "Writing OOC config extractor response missing tool-use block",
                usage_only,
            )
        if tool_parts[0].tool_name != EXTRACT_WRITING_CONFIG_TOOL_NAME:
            raise WritingOocExtractionUsageError(
                f"Writing OOC config extractor unexpected tool name:"
                f" {tool_parts[0].tool_name!r};"
                f" expected {EXTRACT_WRITING_CONFIG_TOOL_NAME!r}",
                usage_only,
            )

        try:
            update = WritingConfigUpdate.model_validate(tool_parts[0].tool_input)
        except Exception as exc:
            raise WritingOocExtractionUsageError(
                "Writing OOC config extractor tool input failed schema"
                f" validation: {exc}",
                usage_only,
            ) from exc

        return usage_only.model_copy(update={"config_update": update})

    def _render(self, ctx: AssembledContext) -> ProviderCallRequest:
        """Build a minimal ProviderCallRequest for the extraction pass."""
        vs = ctx.volatile_suffix
        content_block = RenderedBlock(
            text=f"Sojourner (OOC): {vs.current_input}",
        )
        return ProviderCallRequest(
            pass_id=PipelinePassId.WRITING_OOC_CONFIG_EXTRACTOR,
            system_blocks=[RenderedBlock(text=_EXTRACTION_SYSTEM_PROMPT)],
            rendered_blocks=[content_block],
            max_output_tokens=_MAX_OUTPUT_TOKENS,
            tool_definitions=[_EXTRACT_TOOL_DEF],
            forced_tool_name=EXTRACT_WRITING_CONFIG_TOOL_NAME,
        )


__all__ = [
    "WritingOocConfigExtractorService",
    "EXTRACT_WRITING_CONFIG_TOOL_NAME",
    "EXTRACT_WRITING_CONFIG_TOOL_SPEC",
]
