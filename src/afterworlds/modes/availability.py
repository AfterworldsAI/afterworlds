"""Release availability of story modes (ADR-017b, Writing v1 deferral).

``StoryMode`` lists every mode the internal model can represent; this module
names the subset the released application offers. Writing stays represented
(enums, schema, prompts, persona registry, pipeline) but is not released for
v1, so product entry points must refuse it before any effect.
"""

from __future__ import annotations

from afterworlds.models.enums import StoryMode

#: The v1 release offers RPG and Branching on both access paths.
RELEASED_STORY_MODES: frozenset[StoryMode] = frozenset(
    {StoryMode.RPG, StoryMode.BRANCHING}
)


def is_mode_released(mode: StoryMode) -> bool:
    return mode in RELEASED_STORY_MODES
