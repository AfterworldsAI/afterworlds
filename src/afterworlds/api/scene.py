"""The mapper's typed seam for route handlers (issue #211, Binding Decision 2).

Route modules stay thin: they translate HTTP to these calls and never import
the RPG pipeline directly.
"""

from __future__ import annotations

from afterworlds.api.dto import MovePathDTO, SceneViewResponse
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.models.enums import StoryMode
from afterworlds.models.story import Story
from afterworlds.pipeline.orchestrator.service import OrchestratorService
from afterworlds.pipeline.rpg.movement import STALE
from afterworlds.pipeline.rpg.spatial_turn import DrawnRoute, RouteRefused


def drawn_route(move_path: MovePathDTO | None) -> DrawnRoute | None:
    if move_path is None:
        return None
    return DrawnRoute(
        squares=tuple(move_path.squares),
        dash=move_path.dash,
        disengage=move_path.disengage,
        view_hash=move_path.view_hash,
    )


def precheck_route(
    orchestrator: OrchestratorService, story: Story, drawn: DrawnRoute
) -> None:
    """Refuse a drawn route before the Turn exists, with a player-safe
    reason, so it reaches no provider and no settlement. Checks ownership,
    shape, staleness and what the mover could know; hidden things never
    refuse a route (they only stop it, inside the Turn)."""
    spatial = orchestrator.spatial_turn_service
    if story.mode is not StoryMode.RPG or spatial is None:
        raise ApiErrorResponse(
            422,
            ApiErrorCode.VALIDATION_FAILED,
            "A drawn route needs an RPG story with a scene map.",
        )
    try:
        spatial.check(story.story_id, drawn)
    except RouteRefused as exc:
        detail = {"reason": exc.reason}
        if exc.at is not None:
            detail["at"] = exc.at
        if exc.reason == STALE:
            raise ApiErrorResponse(
                409, ApiErrorCode.ROUTE_STALE, exc.reason, detail=detail
            ) from exc
        raise ApiErrorResponse(
            422, ApiErrorCode.ROUTE_REFUSED, exc.reason, detail=detail
        ) from exc


def scene_view(orchestrator: OrchestratorService, story: Story) -> SceneViewResponse:
    """The player view of the story's active scene (read-only), or 404."""
    spatial = orchestrator.spatial_turn_service
    view = (
        spatial.view(story.story_id)
        if spatial is not None and story.mode is StoryMode.RPG
        else None
    )
    if view is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story.story_id} has no active scene"
        )
    return SceneViewResponse.model_validate(view)
