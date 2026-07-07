"""Backend-owned API view models — Binding Decision 9.

All DTOs: Pydantic, ``extra="forbid"``, ``schema_version: Literal[1]``, str
enums, no ORM rows. These are a deliberate, versioned contract distinct from
internal service/domain models.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from afterworlds.models.enums import InteractionRejectionReason, StoryMode
from afterworlds.models.rpg import RpgVisibleState
from afterworlds.pipeline.branching.models import BranchingVisibleState
from afterworlds.pipeline.orchestrator.models import PipelineDisposition
from afterworlds.pipeline.writing.models import WritingVisibleState


class StoryPlayStatus(StrEnum):
    """API-facing setup/play status, shared shape across all three modes."""

    SETUP = "setup"
    IN_PLAY = "in_play"


class HealthResponse(BaseModel):
    model_config = {"extra": "forbid"}

    status: Literal["ok"]
    db_reachable: bool
    schema_version: Literal[1] = 1


class StoryListItemDTO(BaseModel):
    model_config = {"extra": "forbid"}

    story_id: UUID
    title: str
    mode: StoryMode
    status: StoryPlayStatus
    updated_at: datetime
    schema_version: Literal[1] = 1


class StoryListResponse(BaseModel):
    model_config = {"extra": "forbid"}

    stories: list[StoryListItemDTO]
    schema_version: Literal[1] = 1


class StoryDetailDTO(BaseModel):
    model_config = {"extra": "forbid"}

    story_id: UUID
    title: str
    mode: StoryMode
    status: StoryPlayStatus
    created_at: datetime
    updated_at: datetime
    schema_version: Literal[1] = 1


class CreateStoryRequest(BaseModel):
    model_config = {"extra": "forbid"}

    title: str
    mode: StoryMode
    # RPG only; ignored for other modes. No default per-mode business
    # meaning is inferred here -- this is presentation-form input only.
    character_name: str | None = None


class TurnSubmissionRequest(BaseModel):
    model_config = {"extra": "forbid"}

    user_input: str


class ProviderRefusalSummaryDTO(BaseModel):
    """Advisory only -- never authoritative policy (mirrors ProviderRefusal).

    Deliberately excludes ``raw_response_excerpt``, ``pass_identifier``, and
    ``refusal_category``: internal routing/audit detail, not a client
    contract (Binding Decision 9).
    """

    model_config = {"extra": "forbid"}

    provider: str
    coarse_reason: str | None = None


class TurnSubmissionResponse(BaseModel):
    """The turn-submission envelope (Binding Decisions 3, 6, 10, 11)."""

    model_config = {"extra": "forbid"}

    disposition: PipelineDisposition
    turn_id: UUID | None
    delivered_output: str | None = None
    stable_prefix_cache_warmed: bool = False
    interaction_rejection_reason: InteractionRejectionReason | None = None
    interaction_rejection_message: str | None = None
    pipeline_error_summary: str | None = None
    provider_refusal: ProviderRefusalSummaryDTO | None = None
    pending_roll_redirect_message: str | None = None
    settlement_warning: str | None = None
    # Refreshed visible-state for the story's mode, from this same turn's
    # result -- a single fetch, avoiding a read race after commit. Populated
    # starting Phase 3 (mode surfaces); None until then and whenever the
    # owning mode service has nothing to report yet (e.g. setup not started).
    visible_state: (
        RpgVisibleState | BranchingVisibleState | WritingVisibleState | None
    ) = None
    schema_version: Literal[1] = 1
