"""Story CRUD exposure — GET/POST /api/stories, GET /api/stories/{story_id}.

Thin handlers only (Binding Decision 2): translate HTTP <-> the typed Story
CRUD seam (Issue 3) plus the story-bootstrap helpers. No orchestration,
entitlement, or mode policy here.

Prerequisite #205: remotely, the list enumerates only the acting account's
owned Stories and creation records ownership in the Story's own transaction.
``story_router`` (the ``/{story_id}`` routes) is mounted behind the Story
ownership guard by ``create_app``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.api.deps import AdmittedWorkerRoute, get_session
from afterworlds.api.dto import (
    CreateStoryRequest,
    StoryDetailDTO,
    StoryListItemDTO,
    StoryListResponse,
    StoryPlayStatus,
)
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.api.remote_access import access_policy, get_actor
from afterworlds.api.story_bootstrap import (
    ensure_mode_session_state,
    ensure_story_turn_anchor_node,
    require_released_mode,
    resolve_play_status,
)
from afterworlds.models.enums import StoryMode
from afterworlds.models.story import Story
from afterworlds.persistence.crud.story import create_story, get_story
from afterworlds.persistence.orm.story import StoryORM
from afterworlds.remote.access import (
    AccessPolicy,
    owned_story_ids,
    record_story_owner,
)
from afterworlds.remote.identity import Actor

router = APIRouter(
    prefix="/api/stories", tags=["stories"], route_class=AdmittedWorkerRoute
)
story_router = APIRouter(
    prefix="/api/stories", tags=["stories"], route_class=AdmittedWorkerRoute
)


@router.get("", response_model=StoryListResponse)
def list_stories(
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_actor),
    policy: AccessPolicy = Depends(access_policy),
) -> StoryListResponse:
    query = select(StoryORM).order_by(StoryORM.updated_at.desc())
    if policy.remote:
        query = query.where(
            StoryORM.story_id.in_(owned_story_ids(session, actor.account_id))
        )
    rows = [
        row
        for row in session.scalars(query).all()
        if policy.actor_may_access(session, actor, UUID(row.story_id))
    ]
    items = [
        StoryListItemDTO(
            story_id=UUID(row.story_id),
            title=row.title,
            mode=StoryMode(row.mode),
            status=StoryPlayStatus(
                resolve_play_status(session, UUID(row.story_id), StoryMode(row.mode))
            ),
            updated_at=datetime.fromisoformat(row.updated_at),
        )
        for row in rows
    ]
    return StoryListResponse(stories=items)


@router.post("", response_model=StoryDetailDTO, status_code=201)
def create_story_route(
    body: CreateStoryRequest,
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_actor),
    policy: AccessPolicy = Depends(access_policy),
) -> StoryDetailDTO:
    require_released_mode(body.mode)
    now = datetime.now(UTC)
    story = create_story(
        session,
        Story(title=body.title, mode=body.mode, created_at=now, updated_at=now),
    )
    ensure_mode_session_state(
        session, story.story_id, body.mode, character_name=body.character_name
    )
    ensure_story_turn_anchor_node(session, story.story_id, body.mode)
    if policy.remote:
        record_story_owner(session, actor.account_id, story.story_id, now=now)
    session.commit()
    return StoryDetailDTO(
        story_id=story.story_id,
        title=story.title,
        mode=story.mode,
        status=StoryPlayStatus.SETUP,
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


@story_router.get("/{story_id}", response_model=StoryDetailDTO)
def get_story_route(
    story_id: UUID, session: Session = Depends(get_session)
) -> StoryDetailDTO:
    story = get_story(session, story_id)
    if story is None:
        raise ApiErrorResponse(
            404, ApiErrorCode.NOT_FOUND, f"Story {story_id} not found"
        )
    return StoryDetailDTO(
        story_id=story.story_id,
        title=story.title,
        mode=story.mode,
        status=StoryPlayStatus(
            resolve_play_status(session, story.story_id, story.mode)
        ),
        created_at=story.created_at,
        updated_at=story.updated_at,
    )
