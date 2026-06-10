"""Provider adapter DTOs — CRD Issue 14a.

All models use ``extra="forbid"`` and never coerce ``None`` token metrics to 0.
The only permitted ``None`` → ``0`` collapse is at ``extract_snapshots`` in
Issue 13 settlement.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from afterworlds.entitlement.enums import ModelTier, PipelinePassId
from afterworlds.pipeline._stable_prefix_renderer import RenderedBlock

# ---------------------------------------------------------------------------
# Content part types
# ---------------------------------------------------------------------------


class ProviderTextPart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text"] = "text"
    text: str


class ProviderToolCallPart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["tool_use"] = "tool_use"
    tool_name: str
    tool_input: dict  # type: ignore[type-arg]


ProviderContentPart = Annotated[
    ProviderTextPart | ProviderToolCallPart,
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------


class ProviderToolDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    input_schema: dict  # type: ignore[type-arg]


# ---------------------------------------------------------------------------
# Call request / result
# ---------------------------------------------------------------------------


class ProviderCallRequest(BaseModel):
    """Provider-neutral call request built by a pass service.

    No ``access_path``.  No model id — the adapter selects the model from
    ``pass_id``.  No cache fields — cache realization is wholly adapter-owned.

    ``system_blocks`` carries system-parameter content (pass contract + mode
    contract).  ``rendered_blocks`` carries user-message content: stable-prefix
    blocks from the shared 12c renderer plus pass-specific volatile suffix blocks.
    The cache breakpoint sits on the final stable-prefix block in
    ``rendered_blocks``; ``system_blocks`` carry no breakpoint.
    """

    model_config = ConfigDict(extra="forbid")

    pass_id: PipelinePassId
    system_blocks: list[RenderedBlock] = Field(default_factory=list)
    rendered_blocks: list[RenderedBlock]
    max_output_tokens: int
    temperature: float | None = None
    tool_definitions: list[ProviderToolDefinition] = Field(default_factory=list)
    forced_tool_name: str | None = None
    sojourner_id: UUID | None = None
    turn_id: UUID | None = None


class ProviderCallResult(BaseModel):
    """Provider-neutral call result returned by an adapter.

    All four token count fields use ``int | None``.  ``None`` means the
    provider did not report the metric — adapters never coerce ``None`` to 0.
    ``cache_warmed`` is True iff ``cache_read_token_count`` is not None and > 0.
    """

    model_config = ConfigDict(extra="forbid")

    pass_id: PipelinePassId
    provider_name: str
    model_identifier: str
    model_tier: ModelTier
    content_parts: list[ProviderContentPart]
    input_token_count: int | None
    output_token_count: int | None
    cache_read_token_count: int | None
    cache_creation_token_count: int | None
    cache_warmed: bool
    latency_ms: int
    sojourner_id: UUID | None = None
    turn_id: UUID | None = None


__all__ = [
    "ProviderTextPart",
    "ProviderToolCallPart",
    "ProviderContentPart",
    "ProviderToolDefinition",
    "ProviderCallRequest",
    "ProviderCallResult",
]
