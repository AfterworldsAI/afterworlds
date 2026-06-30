"""Writing-mode context renderer — CRD Issue 17.

Renders the per-turn persona fragment and authoring-controls block that are
appended to the Writing mode contract (system_prompt) in the StablePrefix.
Called once per turn (not once per pass) so the result is part of the stable
prefix shared across all provider-backed passes.

Architectural invariant: this renderer is purely functional — no DB access,
no provider calls, no side effects.  It receives already-loaded objects and
returns a string.
"""

from __future__ import annotations

from afterworlds.models.session import WritingSessionState
from afterworlds.modes.personas.registry import (
    JsonPersonaRegistry,
    PersonaProfile,
    SupportedMode,
)


def render_writing_system_prompt_appendix(
    session_state: WritingSessionState,
    registry: JsonPersonaRegistry,
) -> str:
    """Return the persona + authoring-controls block for the Writing system prompt.

    Returns an empty string when ``persona_id`` is not set (SETUP phase with
    no persona chosen yet) — the base mode contract remains unchanged.

    The returned text is meant to be appended to the Writing mode contract
    string before it is frozen into the StablePrefix.
    """
    if session_state.persona_id is None:
        return ""

    try:
        profile: PersonaProfile = registry.get_profile(
            session_state.persona_id, SupportedMode.WRITING
        )
    except (KeyError, ValueError):
        return ""

    parts: list[str] = []

    parts.append("## Writing Persona")
    parts.append(
        f"You are acting as **{profile.display_name}**"
        f" ({profile.orientation.value} orientation)."
    )
    parts.append(profile.prompt_fragment)

    if profile.negative_constraints:
        constraints_text = "; ".join(profile.negative_constraints)
        parts.append(f"Avoid: {constraints_text}.")

    parts.append("## Authoring Controls")

    controls: list[str] = []
    controls.append(f"Critique intensity: {session_state.critique_intensity.value}")
    controls.append(f"Style density: {session_state.style_density.value}")

    if session_state.form is not None:
        form_label = session_state.form_other or session_state.form.value
        controls.append(f"Form: {form_label}")

    if session_state.tense:
        controls.append(f"Tense: {session_state.tense}")

    if session_state.pov:
        controls.append(f"POV: {session_state.pov}")

    if session_state.dialogue_narration_ratio is not None:
        controls.append(
            f"Dialogue/narration ratio:"
            f" {session_state.dialogue_narration_ratio}% dialogue"
        )

    if session_state.genre_conventions:
        controls.append(f"Genre conventions: {session_state.genre_conventions}")

    if session_state.specific_goals:
        controls.append(f"Session goals: {session_state.specific_goals}")

    if session_state.acceptable_content:
        controls.append(f"Acceptable content: {session_state.acceptable_content}")

    if session_state.beat_constraints:
        beats = "; ".join(session_state.beat_constraints)
        controls.append(f"Beat constraints: {beats}")

    parts.append("\n".join(f"- {c}" for c in controls))

    return "\n\n".join(parts)


__all__ = ["render_writing_system_prompt_appendix"]
