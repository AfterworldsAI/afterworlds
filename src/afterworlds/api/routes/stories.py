"""Story CRUD exposure — GET/POST /api/stories, GET /api/stories/{story_id}.

Thin handlers only (Binding Decision 2): translate HTTP <-> the typed Story
CRUD seam (Issue 3) plus the story-bootstrap helpers. No orchestration,
entitlement, or mode policy here.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.api.deps import get_session
from afterworlds.api.dto import (
    CreateStoryRequest,
    StoryDetailDTO,
    StoryListItemDTO,
    StoryListResponse,
    StoryPlayStatus,
)
from afterworlds.api.errors import ApiErrorCode, ApiErrorResponse
from afterworlds.api.story_bootstrap import (
    ensure_mode_session_state,
    ensure_story_turn_anchor_node,
    resolve_play_status,
)
from afterworlds.models.enums import StoryMode
from afterworlds.models.story import Story
from afterworlds.persistence.crud.story import create_story, get_story
from afterworlds.persistence.orm.story import StoryORM

router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.get("", response_model=StoryListResponse)
def list_stories(session: Session = Depends(get_session)) -> StoryListResponse:
    rows = session.scalars(select(StoryORM).order_by(StoryORM.updated_at.desc())).all()
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
    body: CreateStoryRequest, session: Session = Depends(get_session)
) -> StoryDetailDTO:
    now = datetime.now(UTC)
    story = create_story(
        session,
        Story(title=body.title, mode=body.mode, created_at=now, updated_at=now),
    )
    ensure_mode_session_state(
        session, story.story_id, body.mode, character_name=body.character_name
    )
    ensure_story_turn_anchor_node(session, story.story_id, body.mode)
    session.commit()
    return StoryDetailDTO(
        story_id=story.story_id,
        title=story.title,
        mode=story.mode,
        status=StoryPlayStatus.SETUP,
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


@router.get("/{story_id}", response_model=StoryDetailDTO)
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
