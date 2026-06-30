"""Writing-mode DTOs.

Turn request, version pointer, authoring controls, metadata, visible state.
All models use extra="forbid". Durable/UI-facing payloads carry schema_version.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from afterworlds.models.enums import (
    CritiqueIntensity,
    StyleDensity,
    WritingCanonEligibility,
    WritingForm,
    WritingPlayStatus,
    WritingVersionPointerKind,
    WritingWorkProductKind,
)
from afterworlds.modes.personas.registry import PersonaOrientation

# ---------------------------------------------------------------------------
# Canon-eligible work-product kinds
# ---------------------------------------------------------------------------

_EXTRACTOR_ELIGIBLE_KINDS: frozenset[WritingWorkProductKind] = frozenset(
    {
        WritingWorkProductKind.PROSE_CONTINUATION,
        WritingWorkProductKind.DRAFT_PROSE,
        WritingWorkProductKind.REVISION,
    }
)


# ---------------------------------------------------------------------------
# WritingTurnRequest
# ---------------------------------------------------------------------------


class WritingTurnRequest(BaseModel):
    """Per-turn Writing-mode request payload.

    This is the only v1 carrier that can explicitly promote a turn to
    EXTRACTOR_ELIGIBLE. If canon_eligibility_override is absent or None, the
    turn defaults to NON_CANON_SUPPORT.

    Invalid combinations (EXTRACTOR_ELIGIBLE for non-prose kinds) are rejected
    at construction.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    work_product_kind: WritingWorkProductKind
    canon_eligibility_override: WritingCanonEligibility | None = None

    @model_validator(mode="after")
    def _validate_canon_eligibility(self) -> WritingTurnRequest:
        if (
            self.canon_eligibility_override
            is WritingCanonEligibility.EXTRACTOR_ELIGIBLE
            and self.work_product_kind not in _EXTRACTOR_ELIGIBLE_KINDS
        ):
            raise ValueError(
                f"EXTRACTOR_ELIGIBLE is not valid for work_product_kind="
                f"{self.work_product_kind!r}. Only PROSE_CONTINUATION, "
                f"DRAFT_PROSE, and REVISION may be promoted to EXTRACTOR_ELIGIBLE."
            )
        return self

    @property
    def effective_canon_eligibility(self) -> WritingCanonEligibility:
        """Resolve the effective eligibility, defaulting to NON_CANON_SUPPORT."""
        if self.canon_eligibility_override is not None:
            return self.canon_eligibility_override
        return WritingCanonEligibility.NON_CANON_SUPPORT


# ---------------------------------------------------------------------------
# WritingVersionPointer
# ---------------------------------------------------------------------------


class WritingVersionPointer(BaseModel):
    """Lightweight provenance reference to a writing artifact.

    A signpost — not a time machine. No parent pointer, diff payload, snapshot
    payload, branch ID, restore target, or is_current semantics.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    pointer_id: UUID = Field(default_factory=uuid4)
    kind: WritingVersionPointerKind
    label: str
    source_turn_id: UUID | None = None
    source_node_id: UUID | None = None
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("label")
    @classmethod
    def _label_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("label must be non-empty after stripping whitespace")
        return v

    @model_validator(mode="after")
    def _at_least_one_source(self) -> WritingVersionPointer:
        if (
            self.source_turn_id is None
            and self.source_node_id is None
            and not (self.label.strip())
            and not self.description
        ):
            raise ValueError(
                "At least one of source_turn_id, source_node_id, label, or "
                "description must identify what the pointer refers to."
            )
        return self


# ---------------------------------------------------------------------------
# AuthoringControlsSnapshot
# ---------------------------------------------------------------------------


class AuthoringControlsSnapshot(BaseModel):
    """Typed snapshot of authoring controls for a given Writing turn.

    Used in WritingModeMetadata — not the durable session state. The session
    state row is authoritative; this snapshot preserves what governed the turn.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    critique_intensity: CritiqueIntensity
    form: WritingForm
    tense: str | None = None
    pov: str | None = None
    style_density: StyleDensity
    dialogue_narration_ratio: int | None = None
    genre_conventions: str | None = None
    acceptable_content: str | None = None

    @field_validator("dialogue_narration_ratio")
    @classmethod
    def _ratio_range(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("dialogue_narration_ratio must be between 0 and 100")
        return v


# ---------------------------------------------------------------------------
# WritingModeMetadata
# ---------------------------------------------------------------------------


class WritingModeMetadata(BaseModel):
    """Per-turn Writing metadata persisted on Node/Turn mode_metadata.writing.

    Records what governed the turn. Not the source of truth for durable config;
    the session-state row is. Orientation is snapshotted here from the profile
    resolved at turn time for historical provenance.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1

    persona_id: str
    persona_display_name: str
    relationship_orientation: PersonaOrientation
    persona_registry_version: int
    persona_profile_version: int
    persona_prompt_fingerprint: str | None = None

    work_product_kind: WritingWorkProductKind
    canon_eligibility: WritingCanonEligibility

    beat_constraints_snapshot: list[str] = Field(default_factory=list)
    version_pointer_refs: list[UUID] = Field(default_factory=list)
    authoring_controls_snapshot: AuthoringControlsSnapshot


# ---------------------------------------------------------------------------
# WritingVisibleState
# ---------------------------------------------------------------------------


class WritingVisibleState(BaseModel):
    """Backend DTO for Writing-mode state consumed by Issue 19's HTTP layer.

    Registry UI metadata (description, signature move, demeanor) is resolved
    from persona_id at assembly time; it is not stored in session state.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    story_id: UUID

    persona_id: str
    persona_display_name: str
    relationship_orientation: PersonaOrientation
    ui_short_description: str
    ui_long_description: str
    signature_move: str
    demeanor_tags: list[str]

    play_status: str
    specific_goals: str
    critique_intensity: CritiqueIntensity
    form: WritingForm
    tense: str | None
    pov: str | None
    style_density: StyleDensity
    dialogue_narration_ratio: int | None
    genre_conventions: str | None
    beat_constraints: list[str]
    version_pointers: list[WritingVersionPointer]
    acceptable_content: str | None


# ---------------------------------------------------------------------------
# WritingPassError and OOC config extractor types
# ---------------------------------------------------------------------------


class WritingPassError(Exception):
    """Raised when a Writing-mode pipeline pass fails unrecoverably.

    Covers provider errors raised before any result is available and
    local failures where no provider tokens were consumed.
    """


class WritingConfigUpdate(BaseModel):
    """Config changes extracted from a Writing-mode OOC turn.

    All fields are optional; only non-None fields are applied.
    ``persona_id`` triggers a registry lookup and provenance snapshot update.
    ``beat_constraints`` replaces the full constraint list (replace semantics).
    ``version_pointers`` are appended to the existing list, deduped by pointer_id.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    persona_id: str | None = None
    play_status: WritingPlayStatus | None = None
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
    version_pointers: list[WritingVersionPointer] | None = None

    @field_validator("dialogue_narration_ratio")
    @classmethod
    def _ratio_range(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("dialogue_narration_ratio must be between 0 and 100")
        return v

    @field_validator("beat_constraints")
    @classmethod
    def _constraints_nonempty(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for constraint in v:
                if not constraint.strip():
                    raise ValueError("beat_constraints must not contain empty strings")
        return v


class WritingOocConfigExtractorResult(BaseModel):
    """Result from the Writing-mode OOC config extractor pass.

    Wraps the extracted config update with provider usage metrics so the
    entitlement layer can include this pass in credit settlement.
    """

    model_config = ConfigDict(extra="forbid")

    config_update: WritingConfigUpdate
    provider: str | None = None
    model_identifier: str | None = None
    model_tier: str | None = None
    latency_ms: int = 0
    input_token_count: int | None = None
    output_token_count: int | None = None
    cache_read_token_count: int | None = None
    cache_creation_token_count: int | None = None


class WritingOocExtractionUsageError(WritingPassError):
    """OOC config extraction failed *after* the provider returned a result.

    Raised when the provider call succeeded (tokens consumed) but local
    validation rejected the response. Carries a usage-only result so the
    orchestrator can settle provider usage before treating config update as
    best-effort.
    """

    def __init__(
        self, message: str, usage_result: WritingOocConfigExtractorResult
    ) -> None:
        super().__init__(message)
        self.usage_result = usage_result
