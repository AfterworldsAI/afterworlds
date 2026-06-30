"""WritingVisibleStateService — CRD Issue 17.

Builds the WritingVisibleState DTO surfaced in OrchestrationResult on every
DELIVERED WRITING-mode turn. Resolves persona UI metadata from the registry
at assembly time; session state is the authoritative source of config fields.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from afterworlds.models.enums import WritingForm
from afterworlds.modes.personas.registry import JsonPersonaRegistry, SupportedMode
from afterworlds.pipeline.writing.context import render_writing_system_prompt_appendix
from afterworlds.pipeline.writing.models import (
    WritingVersionPointer,
    WritingVisibleState,
)

if TYPE_CHECKING:
    from afterworlds.models.session import WritingSessionState


class WritingVisibleStateService:
    """Builds WritingVisibleState from session state and the persona registry."""

    def __init__(self, registry: JsonPersonaRegistry) -> None:
        self._registry = registry

    @property
    def registry(self) -> JsonPersonaRegistry:
        """Expose the registry for callers that need persona profile lookups."""
        return self._registry

    def render_context_appendix(self, session_state: WritingSessionState) -> str:
        """Return the persona + authoring-controls block to append to the system prompt.

        Returns an empty string when no persona is set or the persona is not found.
        """
        return render_writing_system_prompt_appendix(session_state, self._registry)

    def build(self, session_state: WritingSessionState) -> WritingVisibleState:
        """Return the Sojourner-visible Writing session snapshot.

        Args:
            session_state: Current WritingSessionState.

        Returns:
            WritingVisibleState with registry UI metadata resolved from
            ``persona_id``.

        Raises:
            ValueError: if ``session_state.persona_id`` is None (session not
                yet configured with a persona).
        """
        if session_state.persona_id is None:
            raise ValueError(
                "WritingVisibleStateService.build called with persona_id=None;"
                " persona must be selected before building visible state."
            )

        try:
            profile = self._registry.get_profile(
                session_state.persona_id, SupportedMode.WRITING
            )
        except (KeyError, ValueError) as exc:
            raise ValueError(
                f"WritingVisibleStateService: persona_id {session_state.persona_id!r}"
                f" not found in registry: {exc}"
            ) from exc

        version_pointers: list[WritingVersionPointer] = []
        for raw in session_state.version_pointers:
            with contextlib.suppress(Exception):
                version_pointers.append(WritingVersionPointer.model_validate(raw))

        return WritingVisibleState(
            story_id=session_state.story_id,
            persona_id=profile.persona_id,
            persona_display_name=profile.display_name,
            relationship_orientation=profile.orientation,
            ui_short_description=profile.ui_short_description,
            ui_long_description=profile.ui_long_description,
            signature_move=profile.signature_move,
            demeanor_tags=profile.demeanor_tags,
            play_status=session_state.play_status.value,
            specific_goals=session_state.specific_goals,
            critique_intensity=session_state.critique_intensity,
            form=session_state.form,
            form_other=(
                session_state.form_other
                if session_state.form is WritingForm.OTHER
                else None
            ),
            tense=session_state.tense,
            pov=session_state.pov,
            style_density=session_state.style_density,
            dialogue_narration_ratio=session_state.dialogue_narration_ratio,
            genre_conventions=session_state.genre_conventions,
            beat_constraints=session_state.beat_constraints,
            version_pointers=version_pointers,
            acceptable_content=session_state.acceptable_content,
        )


__all__ = ["WritingVisibleStateService"]
