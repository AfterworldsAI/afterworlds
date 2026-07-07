"""Backend-owned API view models — Binding Decision 9.

All DTOs: Pydantic, ``extra="forbid"``, ``schema_version: Literal[1]``, str
enums, no ORM rows. These are a deliberate, versioned contract distinct from
internal service/domain models.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from afterworlds.models.enums import (
    BranchCountRange,
    BranchingCadence,
    CritiqueIntensity,
    DiceHandling,
    IntentType,
    InteractionRejectionReason,
    InteractionStyle,
    LengthPreference,
    RpgSessionType,
    RpgTone,
    StoryMode,
    StyleDensity,
    WritingForm,
)
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
    # Refreshed visible-state for the story's mode: one fetch in the same
    # session/transaction as the turn, before commit -- avoids a client-side
    # read race after this turn's writes land. None whenever the owning mode
    # service has nothing to report yet (e.g. setup not started).
    visible_state: (
        RpgVisibleState | BranchingVisibleState | WritingVisibleState | None
    ) = None
    schema_version: Literal[1] = 1


class RpgSetupRequest(BaseModel):
    """RPG play-config form fields. Conversational setup (character creation,
    world-building) goes through ordinary turn submission, not this route --
    Issue 15's own pipeline owns setup_phase/play_status progression."""

    model_config = {"extra": "forbid"}

    mode: Literal["rpg"]
    dice_handling: DiceHandling | None = None
    gm_cheating: bool | None = None
    tone: RpgTone | None = None
    session_type: RpgSessionType | None = None
    genre_flavor: str | None = None
    house_rules: str | None = None
    acceptable_content: str | None = None


class BranchingSetupRequest(BaseModel):
    """Branching structured setup fields. The confirmation pass itself is an
    ordinary DELIVERED turn (ADR-016 Decision 3) -- submit it via
    POST .../turns after this call, not through this route."""

    model_config = {"extra": "forbid"}

    mode: Literal["branching"]
    interaction_style: InteractionStyle | None = None
    branching_cadence: BranchingCadence | None = None
    branch_count_range: BranchCountRange | None = None
    length_preference: LengthPreference | None = None
    clear_branch_count_range: bool = False


class WritingSetupRequest(BaseModel):
    """Writing setup fields. ``persona_id`` is required -- no default persona."""

    model_config = {"extra": "forbid"}

    mode: Literal["writing"]
    persona_id: str
    critique_intensity: CritiqueIntensity | None = None
    form: WritingForm | None = None
    form_other: str | None = None
    tense: str | None = None
    pov: str | None = None
    style_density: StyleDensity | None = None
    dialogue_narration_ratio: int | None = None
    genre_conventions: str | None = None
    specific_goals: str | None = None
    acceptable_content: str | None = None
    beat_constraints: list[str] | None = None


SetupRequest = Annotated[
    RpgSetupRequest | BranchingSetupRequest | WritingSetupRequest,
    Field(discriminator="mode"),
]


class SetupResponse(BaseModel):
    model_config = {"extra": "forbid"}

    visible_state: (
        RpgVisibleState | BranchingVisibleState | WritingVisibleState | None
    ) = None
    schema_version: Literal[1] = 1


class VisibleStateResponse(BaseModel):
    model_config = {"extra": "forbid"}

    visible_state: (
        RpgVisibleState | BranchingVisibleState | WritingVisibleState | None
    ) = None
    schema_version: Literal[1] = 1


class PersonaDTO(BaseModel):
    model_config = {"extra": "forbid"}

    persona_id: str
    display_name: str
    orientation: str
    ui_short_description: str
    ui_long_description: str
    demeanor_tags: list[str]
    signature_move: str


class PersonaGalleryResponse(BaseModel):
    model_config = {"extra": "forbid"}

    mentors: list[PersonaDTO]
    peers: list[PersonaDTO]
    schema_version: Literal[1] = 1


class TranscriptTurnDTO(BaseModel):
    model_config = {"extra": "forbid"}

    turn_id: UUID
    user_input: str
    assistant_output: str
    timestamp: datetime
    intent_classification: IntentType


class TranscriptResponse(BaseModel):
    model_config = {"extra": "forbid"}

    turns: list[TranscriptTurnDTO]
    schema_version: Literal[1] = 1
