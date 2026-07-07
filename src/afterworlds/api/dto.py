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

from afterworlds.models.enums import StoryMode


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
