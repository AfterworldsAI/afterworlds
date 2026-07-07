"""GET /api/personas -- Persona Registry gallery, Mentor/Peer split."""

from __future__ import annotations

from fastapi import APIRouter

from afterworlds.api.dto import PersonaDTO, PersonaGalleryResponse
from afterworlds.modes.personas.registry import (
    PersonaOrientation,
    PersonaProfile,
    SupportedMode,
    get_default_registry,
)

router = APIRouter(prefix="/api", tags=["personas"])


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
    registry = get_default_registry()
    profiles = registry.list_active(SupportedMode.WRITING)
    mentors = [
        _to_dto(p) for p in profiles if p.orientation is PersonaOrientation.MENTOR
    ]
    peers = [_to_dto(p) for p in profiles if p.orientation is PersonaOrientation.PEER]
    return PersonaGalleryResponse(mentors=mentors, peers=peers)
