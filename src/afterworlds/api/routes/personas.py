"""GET /api/personas -- Persona Registry gallery, Mentor/Peer split.

Personas are Writing-only, and Writing is not released in v1 (ADR-017b), so
the gallery is empty: no persona is selectable and none stands in as a
fallback. The registry and its six profiles stay intact behind the gate.
"""

from __future__ import annotations

from fastapi import APIRouter

from afterworlds.api.deps import AdmittedWorkerRoute
from afterworlds.api.dto import PersonaDTO, PersonaGalleryResponse
from afterworlds.models.enums import StoryMode
from afterworlds.modes.availability import is_mode_released
from afterworlds.modes.personas.registry import (
    PersonaOrientation,
    PersonaProfile,
    SupportedMode,
    get_default_registry,
)

router = APIRouter(prefix="/api", tags=["personas"], route_class=AdmittedWorkerRoute)


def _to_dto(profile: PersonaProfile) -> PersonaDTO:
    return PersonaDTO(
        persona_id=profile.persona_id,
        display_name=profile.display_name,
        orientation=profile.orientation.value,
        ui_short_description=profile.ui_short_description,
        ui_long_description=profile.ui_long_description,
        demeanor_tags=list(profile.demeanor_tags),
        signature_move=profile.signature_move,
    )


@router.get("/personas", response_model=PersonaGalleryResponse)
def list_personas() -> PersonaGalleryResponse:
    if not is_mode_released(StoryMode.WRITING):
        return PersonaGalleryResponse(mentors=[], peers=[])
    registry = get_default_registry()
    profiles = registry.list_active(SupportedMode.WRITING)
    mentors = [
        _to_dto(p) for p in profiles if p.orientation is PersonaOrientation.MENTOR
    ]
    peers = [_to_dto(p) for p in profiles if p.orientation is PersonaOrientation.PEER]
    return PersonaGalleryResponse(mentors=mentors, peers=peers)
