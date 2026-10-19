"""Rolling Summary compression pass -- ADR-006b.

The provider-backed pass that writes a new Rolling Summary from the prior
summary and an eligible narrative window. It renders the turn's already
assembled stable prefix through the shared renderer (no replacement prefix)
followed by one volatile compression block, and never renders the
pass-forward ledger, so hidden RPG adjudication views are not source material.

Persistence, eligibility and windowing stay with ``RollingSummaryService``;
the orchestrator owns placement inside the turn's outer transaction.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from afterworlds.entitlement.enums import PipelinePassId
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
from afterworlds.prompt_contracts import PROMPT_DIR

if TYPE_CHECKING:
    from afterworlds.models.context import AssembledContext
    from afterworlds.pipeline.provider._protocol import ProviderAdapter

_PROMPT_PATH: Path = PROMPT_DIR / "rolling_summary.md"

RECORD_ROLLING_SUMMARY_TOOL_NAME = "record_rolling_summary"
ROLLING_SUMMARY_MAX_TOKENS = 1024

_TOOL_DEF = ProviderToolDefinition(
    name=RECORD_ROLLING_SUMMARY_TOOL_NAME,
    description="Record the complete new Rolling Summary for this story.",
    input_schema={
        "type": "object",
        "properties": {"summary": {"type": "string", "minLength": 1}},
        "required": ["summary"],
        "additionalProperties": False,
    },
)


class RollingSummaryPassResult(BaseModel):
    """Usage-carrying result of one compression call."""

    model_config = ConfigDict(extra="forbid")

    summary_text: str
    provider: str | None
    model_identifier: str | None
    model_tier: str | None
    latency_ms: int
    input_token_count: int | None
    output_token_count: int | None
    cache_read_token_count: int | None
    cache_creation_token_count: int | None


class RollingSummaryPassError(Exception):
    """Operational, malformed or blank compression output. ``usage`` keeps a
    completed provider call's usage for audit (never charged)."""

    def __init__(
        self, message: str, usage: RollingSummaryPassResult | None = None
    ) -> None:
        super().__init__(message)
        self.usage = usage


class RollingSummaryPassService:
    """Builds and validates one ``ROLLING_SUMMARY`` provider call."""

    def __init__(self) -> None:
        self._system_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

    def summarize(
        self,
        ctx: AssembledContext,
        prior_summary: str | None,
        window: list[str],
        *,
        provider: ProviderAdapter,
    ) -> RollingSummaryPassResult:
        compression = "\n\n".join(
            [
                "[Rolling Summary Compression]",
                f"prior_summary:\n{prior_summary or 'none'}",
                "window:",
                *(f"--- turn {i + 1} ---\n{text}" for i, text in enumerate(window)),
            ]
        )
        request = ProviderCallRequest(
            pass_id=PipelinePassId.ROLLING_SUMMARY,
            system_blocks=[RenderedBlock(text=self._system_prompt)],
            rendered_blocks=[
                *render_stable_prefix_blocks(ctx.stable_prefix, TTL_EXTENDED),
                RenderedBlock(text=compression),
            ],
            max_output_tokens=ROLLING_SUMMARY_MAX_TOKENS,
            tool_definitions=[_TOOL_DEF],
            forced_tool_name=RECORD_ROLLING_SUMMARY_TOOL_NAME,
        )
        try:
            result = provider.call(request)
        except ProviderRefusalError:
            raise
        except Exception as exc:
            raise RollingSummaryPassError(
                f"rolling summary provider call failed: {exc}"
            ) from exc

        tool = next(
            (p for p in result.content_parts if isinstance(p, ProviderToolCallPart)),
            None,
        )
        raw = tool.tool_input.get("summary") if tool is not None else None
        text = raw.strip() if isinstance(raw, str) else ""
        usage = RollingSummaryPassResult(
            summary_text=text,
            provider=result.provider_name,
            model_identifier=result.model_identifier,
            model_tier=result.model_tier.value if result.model_tier else None,
            latency_ms=result.latency_ms,
            input_token_count=result.input_token_count,
            output_token_count=result.output_token_count,
            cache_read_token_count=result.cache_read_token_count,
            cache_creation_token_count=result.cache_creation_token_count,
        )
        if tool is None or tool.tool_name != RECORD_ROLLING_SUMMARY_TOOL_NAME:
            raise RollingSummaryPassError(
                "rolling summary response missing record_rolling_summary tool call",
                usage,
            )
        if not text:
            raise RollingSummaryPassError("rolling summary output is empty", usage)
        return usage


__all__ = [
    "RECORD_ROLLING_SUMMARY_TOOL_NAME",
    "RollingSummaryPassError",
    "RollingSummaryPassResult",
    "RollingSummaryPassService",
]
