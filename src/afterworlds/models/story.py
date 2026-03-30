"""Story object hierarchy: Story → Arc → Chapter."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from afterworlds.models.enums import StoryMode


class Story(BaseModel):
    """Top-level container for a complete narrative."""

    story_id: UUID = Field(default_factory=uuid4)
    title: str
    mode: StoryMode
    created_at: datetime
    updated_at: datetime
    arc_ids: list[UUID] = Field(default_factory=list)


class Arc(BaseModel):
    """Major narrative division within a Story."""

    arc_id: UUID = Field(default_factory=uuid4)
    story_id: UUID
    title: str
    order: int
    chapter_ids: list[UUID] = Field(default_factory=list)


class Chapter(BaseModel):
    """Subdivision within an Arc."""

    chapter_id: UUID = Field(default_factory=uuid4)
    arc_id: UUID
    title: str
    order: int
    node_ids: list[UUID] = Field(default_factory=list)
