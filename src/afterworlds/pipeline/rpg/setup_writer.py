"""RPG setup Writer envelope -- ADR-015c.

While an RPG story is in setup, its Writer turn returns a versioned envelope
through the forced tool ``produce_rpg_setup_turn``: the visible GM text plus
one phase-specific result (world confirmation, character proposal,
configuration summary or clarification). Same ``WRITER`` pass id and the
turn's one stable prefix, rendered by the shared renderer -- a typed writer in
the ADR-016 Decision 1 pattern, not an extra provider pass.

Code validates the envelope against the phase. Every phase transition and
confirmation stays with ``services.rpg_setup``; this module only produces and
parses the proposal.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from afterworlds.entitlement.enums import PipelinePassId
from afterworlds.models.enums import RpgSetupPhase
from afterworlds.pipeline._refusal import ProviderRefusalError
from afterworlds.pipeline._stable_prefix_renderer import (
    TTL_EXTENDED,
    RenderedBlock,
    render_stable_prefix_blocks,
)
from afterworlds.pipeline.provider._models import (
    ProviderCallRequest,
    ProviderToolCallPart,
    ProviderToolDefinition,
)
from afterworlds.pipeline.writer.config import WRITER_MAX_TOKENS

if TYPE_CHECKING:
    from afterworlds.models.context import AssembledContext
    from afterworlds.pipeline.provider._protocol import ProviderAdapter

PRODUCE_RPG_SETUP_TURN_TOOL_NAME = "produce_rpg_setup_turn"

_PROMPT_PATH: Path = (
    Path(__file__).parents[4] / "docs" / "prompts" / "rpg_setup_writer.md"
)

_TOOL_DEF = ProviderToolDefinition(
    name=PRODUCE_RPG_SETUP_TURN_TOOL_NAME,
    description=(
        "Return this setup turn's visible GM text and exactly one result whose"
        " kind is allowed for the current setup phase. Call exactly once."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "enum": [1]},
            "gm_text": {"type": "string", "minLength": 1},
            "result": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": [
                            "world_confirmation",
                            "character_proposal",
                            "configuration_summary",
                            "clarification",
                        ],
                    },
                    "understanding": {"type": "string"},
                    "path": {"type": "string", "enum": ["gm_led", "completed_sheet"]},
                    "character": {
                        "type": "object",
                        "description": (
                            "The character in the schema given in [RPG Setup];"
                            " omit anything not yet supplied."
                        ),
                    },
                    "unresolved": {"type": "array", "items": {"type": "string"}},
                    "questions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["kind"],
            },
        },
        "required": ["schema_version", "gm_text", "result"],
    },
)


class WorldConfirmationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kind: Literal["world_confirmation"]
    understanding: str = Field(min_length=1)


class CharacterProposalResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kind: Literal["character_proposal"]
    path: Literal["gm_led", "completed_sheet"]
    character: dict[str, Any]
    unresolved: list[str] = Field(default_factory=list)


class ConfigurationSummaryResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kind: Literal["configuration_summary"]


class ClarificationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kind: Literal["clarification"]
    questions: list[str] = Field(default_factory=list)


SetupResult = Annotated[
    WorldConfirmationResult
    | CharacterProposalResult
    | ConfigurationSummaryResult
    | ClarificationResult,
    Field(discriminator="kind"),
]


class RpgSetupEnvelope(BaseModel):
    """Version 1 of the setup Writer envelope."""

    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    gm_text: str = Field(min_length=1)
    result: SetupResult


def visible_output(envelope: RpgSetupEnvelope) -> str:
    """Every model-authored value this envelope can show the Sojourner.

    Output Safety audits this text instead of ``gm_text`` alone (PR #204
    P1): a world understanding, or a character proposal and its unresolved
    notes, is displayed for review and confirmation. It is the audit's input
    only -- never the transcript, canon or summary text. Clarification
    questions are neither stored nor shown; a configuration summary's
    displayed text is ``gm_text`` itself, and its settings are the
    Sojourner's own.
    """
    result = envelope.result
    parts = [envelope.gm_text]
    if isinstance(result, WorldConfirmationResult):
        parts.append(f"World understanding: {result.understanding}")
    elif isinstance(result, CharacterProposalResult):
        parts.append(
            "Proposed character: "
            + json.dumps(result.character, sort_keys=True, ensure_ascii=False)
        )
        parts += [f"Unresolved: {note}" for note in result.unresolved]
    return "\n\n".join(parts)


#: Which result kinds each setup phase admits.
ALLOWED_RESULTS: dict[RpgSetupPhase, frozenset[str]] = {
    RpgSetupPhase.WORLD_SETUP: frozenset({"world_confirmation", "clarification"}),
    RpgSetupPhase.CHARACTER_CREATION: frozenset(
        {"character_proposal", "clarification"}
    ),
    RpgSetupPhase.PLAY_CONFIGURATION: frozenset(
        {"configuration_summary", "clarification"}
    ),
}


class RpgSetupWriterError(Exception):
    """Operational, malformed or phase-invalid setup Writer output."""


class RpgSetupWriterResult(BaseModel):
    """The parsed envelope plus usage, for the thin downstream WriterResult."""

    envelope: RpgSetupEnvelope
    provider: str | None
    model_identifier: str | None
    model_tier: str | None
    latency_ms: int
    input_token_count: int | None
    output_token_count: int | None
    cache_read_token_count: int | None
    cache_creation_token_count: int | None


class RpgSetupWriterService:
    """Produces and validates one setup-turn envelope."""

    def __init__(self) -> None:
        self._system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    def write(
        self,
        ctx: AssembledContext,
        phase: RpgSetupPhase,
        setup_block: str,
        *,
        provider: ProviderAdapter,
    ) -> RpgSetupWriterResult:
        allowed = ALLOWED_RESULTS.get(phase)
        if allowed is None:
            raise RpgSetupWriterError(f"no setup Writer turn in phase {phase.value}")
        try:
            result = provider.call(self._render(ctx, setup_block))
        except ProviderRefusalError:
            raise
        except Exception as exc:
            raise RpgSetupWriterError(
                f"setup writer provider call failed: {exc}"
            ) from exc

        tool = next(
            (p for p in result.content_parts if isinstance(p, ProviderToolCallPart)),
            None,
        )
        if tool is None or tool.tool_name != PRODUCE_RPG_SETUP_TURN_TOOL_NAME:
            raise RpgSetupWriterError(
                "setup writer response missing produce_rpg_setup_turn tool call"
            )
        try:
            envelope = RpgSetupEnvelope.model_validate(tool.tool_input)
        except ValidationError as exc:
            raise RpgSetupWriterError(
                f"setup writer envelope failed validation: {exc}"
            ) from exc
        if envelope.result.kind not in allowed:
            raise RpgSetupWriterError(
                f"setup writer result {envelope.result.kind!r} is not allowed in"
                f" phase {phase.value}"
            )
        return RpgSetupWriterResult(
            envelope=envelope,
            provider=result.provider_name,
            model_identifier=result.model_identifier,
            model_tier=result.model_tier.value if result.model_tier else None,
            latency_ms=result.latency_ms,
            input_token_count=result.input_token_count,
            output_token_count=result.output_token_count,
            cache_read_token_count=result.cache_read_token_count,
            cache_creation_token_count=result.cache_creation_token_count,
        )

    def _render(self, ctx: AssembledContext, setup_block: str) -> ProviderCallRequest:
        blocks: list[RenderedBlock] = list(
            render_stable_prefix_blocks(ctx.stable_prefix, TTL_EXTENDED)
        )
        ledger = ctx.pass_forward_ledger.render()
        if ledger:
            blocks.append(RenderedBlock(text=ledger))
        for turn in ctx.volatile_suffix.recent_turns:
            blocks.append(
                RenderedBlock(
                    text=f"Player: {turn.user_input}\nNarrator: {turn.assistant_output}"
                )
            )
        blocks.append(RenderedBlock(text=setup_block))
        blocks.append(
            RenderedBlock(text=f"Player: {ctx.volatile_suffix.current_input}")
        )
        return ProviderCallRequest(
            pass_id=PipelinePassId.WRITER,
            system_blocks=[
                RenderedBlock(text=self._system_prompt),
                RenderedBlock(text=ctx.stable_prefix.system_prompt),
            ],
            rendered_blocks=blocks,
            max_output_tokens=WRITER_MAX_TOKENS,
            tool_definitions=[_TOOL_DEF],
            forced_tool_name=PRODUCE_RPG_SETUP_TURN_TOOL_NAME,
        )


__all__ = [
    "ALLOWED_RESULTS",
    "PRODUCE_RPG_SETUP_TURN_TOOL_NAME",
    "RpgSetupEnvelope",
    "RpgSetupWriterError",
    "RpgSetupWriterResult",
    "RpgSetupWriterService",
]
