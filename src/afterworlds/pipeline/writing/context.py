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

from afterworlds.models.enums import WritingForm
from afterworlds.models.session import WritingSessionState
from afterworlds.modes.personas.registry import (
    JsonPersonaRegistry,
    PersonaProfile,
    SupportedMode,
)


def _resolve_form_label(session_state: WritingSessionState) -> str | None:
    """Return the display label for the configured form, or ``None`` if unset.

    ``form_other`` is meaningful only when ``form is WritingForm.OTHER``.  A stale
    ``form_other`` left over from a previous OTHER selection must never govern the
    label of a concrete form; render the concrete form's own value instead.
    """
    if session_state.form is None:
        return None
    if session_state.form is WritingForm.OTHER:
        return session_state.form_other or session_state.form.value
    return session_state.form.value


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

    form_label = _resolve_form_label(session_state)
    if form_label is not None:
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

    if session_state.reading_interests:
        controls.append(f"Reading interests: {session_state.reading_interests}")

    if session_state.writing_interests:
        controls.append(f"Writing interests: {session_state.writing_interests}")

    if session_state.acceptable_content:
        controls.append(f"Acceptable content: {session_state.acceptable_content}")

    if session_state.beat_constraints:
        beats = "; ".join(session_state.beat_constraints)
        controls.append(f"Beat constraints: {beats}")

    parts.append("\n".join(f"- {c}" for c in controls))

    return "\n\n".join(parts)


def render_writing_ooc_state_block(session_state: WritingSessionState) -> str:
    """Return a factual Writing session state summary for OOC context injection.

    Injected into the pass-forward ledger after the OOC system-prompt swap so
    the OOC handler can answer configuration questions truthfully.

    This block carries NO behavioral persona instructions (no prompt_fragment,
    no negative_constraints, no registry lookup) — only current config facts.
    The model must not treat this block as authoritative for durable state;
    it is read-only context for this turn only.
    """
    parts: list[str] = ["## Writing Session State"]
    parts.append(f"play_status: {session_state.play_status.value}")

    if session_state.persona_id is not None:
        parts.append(f"persona: {session_state.persona_id}")
    else:
        parts.append("persona: not set")

    parts.append(f"critique_intensity: {session_state.critique_intensity.value}")
    parts.append(f"style_density: {session_state.style_density.value}")

    form_label = _resolve_form_label(session_state)
    if form_label is not None:
        parts.append(f"form: {form_label}")

    if session_state.tense:
        parts.append(f"tense: {session_state.tense}")

    if session_state.pov:
        parts.append(f"pov: {session_state.pov}")

    if session_state.dialogue_narration_ratio is not None:
        parts.append(
            f"dialogue_narration_ratio: {session_state.dialogue_narration_ratio}%"
        )

    if session_state.genre_conventions:
        parts.append(f"genre_conventions: {session_state.genre_conventions}")

    if session_state.reading_interests:
        parts.append(f"reading_interests: {session_state.reading_interests}")

    if session_state.writing_interests:
        parts.append(f"writing_interests: {session_state.writing_interests}")

    if session_state.specific_goals:
        parts.append(f"specific_goals: {session_state.specific_goals}")

    if session_state.acceptable_content:
        parts.append(f"acceptable_content: {session_state.acceptable_content}")

    if session_state.beat_constraints:
        parts.append(f"beat_constraints: {'; '.join(session_state.beat_constraints)}")

    return "\n".join(parts)


__all__ = ["render_writing_ooc_state_block", "render_writing_system_prompt_appendix"]
