"""GET /api/stories/{story_id}/visible-state -- mode-discriminated read."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from afterworlds.api.deps import get_session
from afterworlds.api.dto import VisibleStateResponse
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.api.visible_state import build_visible_state
from afterworlds.persistence.crud.story import get_story

router = APIRouter(prefix="/api/stories", tags=["visible-state"])


@router.get("/{story_id}/visible-state", response_model=VisibleStateResponse)
def get_visible_state(
    story_id: UUID, session: Session = Depends(get_session)
) -> VisibleStateResponse:
    story = get_story(session, story_id)
    if story is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
        )
    visible_state = build_visible_state(session, story.story_id, story.mode)
    return VisibleStateResponse(visible_state=visible_state)
