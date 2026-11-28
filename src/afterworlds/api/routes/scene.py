"""GET /api/stories/{story_id}/scene -- the scene view (issue #211, M1).

Read-only: the player view of the story's active scene, built from the
committed revision. Opening, closing or auto-opening the view never reaches
a Turn and never writes; Sojourn consults the record on every Turn whether or
not the view is open.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from afterworlds.api.deps import AdmittedWorkerRoute, get_orchestrator, get_session
from afterworlds.api.dto import SceneViewResponse
from afterworlds.api.errors import API_ERROR_RESPONSES, ApiErrorCode, ApiErrorResponse
from afterworlds.api.scene import scene_view
from afterworlds.persistence.crud.story import get_story
from afterworlds.pipeline.orchestrator.service import OrchestratorService

router = APIRouter(
    prefix="/api/stories", tags=["scene"], route_class=AdmittedWorkerRoute
)


@router.get(
    "/{story_id}/scene",
    response_model=SceneViewResponse,
    responses=API_ERROR_RESPONSES,
)
def get_scene(
    story_id: UUID,
    session: Session = Depends(get_session),
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> SceneViewResponse:
    story = get_story(session, story_id)
    if story is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
        )
    return scene_view(orchestrator, story)
