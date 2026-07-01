"""CRUD operations for mode-specific session states."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.models.enums import (
    BranchCountRange,
    BranchingCadence,
    BranchingPlayStatus,
    CritiqueIntensity,
    DiceHandling,
    InteractionStyle,
    LengthPreference,
    RpgPlayStatus,
    RpgSessionType,
    RpgSetupPhase,
    RpgTone,
    StyleDensity,
    WritingForm,
    WritingPlayStatus,
)
from afterworlds.models.session import (
    BranchingSessionState,
    BranchTree,
    CombatContext,
    PlotThread,
    RpgSessionState,
    WritingSessionState,
)
from afterworlds.persistence.orm.session_state import (
    BranchingSessionStateORM,
    RpgSessionStateORM,
    WritingSessionStateORM,
)

# ---------------------------------------------------------------------------
# RpgSessionState
# ---------------------------------------------------------------------------


def _rpg_orm_to_model(row: RpgSessionStateORM) -> RpgSessionState:
    return RpgSessionState(
        session_id=UUID(row.session_id),
        story_id=UUID(row.story_id),
        character_sheet_id=UUID(row.character_sheet_id),
        dice_handling=DiceHandling(row.dice_handling),
        play_status=RpgPlayStatus(row.play_status),
        setup_phase=RpgSetupPhase(row.setup_phase),
        gm_cheating=bool(row.gm_cheating),
        tone=RpgTone(row.tone),
        session_type=RpgSessionType(row.session_type),
        genre_flavor=row.genre_flavor,
        house_rules=row.house_rules,
        acceptable_content=row.acceptable_content,
        active_quests=list(row.active_quests),
        combat_context=CombatContext.model_validate(row.combat_context),
    )


def create_rpg_session_state(
    session: Session, state: RpgSessionState
) -> RpgSessionState:
    """Persist a new RpgSessionState and return it."""
    row = RpgSessionStateORM(
        session_id=str(state.session_id),
        story_id=str(state.story_id),
        character_sheet_id=str(state.character_sheet_id),
        dice_handling=state.dice_handling.value,
        play_status=state.play_status.value,
        setup_phase=state.setup_phase.value,
        gm_cheating=state.gm_cheating,
        tone=state.tone.value,
        session_type=state.session_type.value,
        genre_flavor=state.genre_flavor,
        house_rules=state.house_rules,
        acceptable_content=state.acceptable_content,
        active_quests=list(state.active_quests),
        combat_context=state.combat_context.model_dump(),
    )
    session.add(row)
    session.flush()
    return _rpg_orm_to_model(row)


def get_rpg_session_state(session: Session, session_id: UUID) -> RpgSessionState | None:
    """Return an RpgSessionState by primary key, or None."""
    row = session.get(RpgSessionStateORM, str(session_id))
    if row is None:
        return None
    return _rpg_orm_to_model(row)


def get_rpg_session_state_by_story(
    session: Session, story_id: UUID
) -> RpgSessionState | None:
    """Return the RpgSessionState for a story, or None."""
    row = session.scalars(
        select(RpgSessionStateORM).where(RpgSessionStateORM.story_id == str(story_id))
    ).first()
    if row is None:
        return None
    return _rpg_orm_to_model(row)


def update_rpg_session_state(
    session: Session, state: RpgSessionState
) -> RpgSessionState | None:
    """Update mutable fields on an existing RpgSessionState."""
    row = session.get(RpgSessionStateORM, str(state.session_id))
    if row is None:
        return None
    row.dice_handling = state.dice_handling.value
    row.play_status = state.play_status.value
    row.setup_phase = state.setup_phase.value
    row.gm_cheating = state.gm_cheating
    row.tone = state.tone.value
    row.session_type = state.session_type.value
    row.genre_flavor = state.genre_flavor
    row.house_rules = state.house_rules
    row.acceptable_content = state.acceptable_content
    row.active_quests = list(state.active_quests)
    row.combat_context = state.combat_context.model_dump()
    session.flush()
    return _rpg_orm_to_model(row)


def delete_rpg_session_state(session: Session, session_id: UUID) -> bool:
    """Delete an RpgSessionState.  Returns True if deleted."""
    row = session.get(RpgSessionStateORM, str(session_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


# ---------------------------------------------------------------------------
# BranchingSessionState
# ---------------------------------------------------------------------------


def _branching_orm_to_model(row: BranchingSessionStateORM) -> BranchingSessionState:
    plot_threads: list[PlotThread] = [
        PlotThread.model_validate(pt) for pt in row.plot_thread_tracker
    ]
    return BranchingSessionState(
        session_id=UUID(row.session_id),
        story_id=UUID(row.story_id),
        pacing_stage=row.pacing_stage,  # type: ignore[arg-type]
        branch_tree=BranchTree.model_validate(row.branch_tree),
        plot_thread_tracker=plot_threads,
        current_node_id=(
            UUID(row.current_node_id) if row.current_node_id is not None else None
        ),
        # Issue 16: interaction configuration fields — nullable, read as enum or None.
        interaction_style=(
            InteractionStyle(row.interaction_style)
            if row.interaction_style is not None
            else None
        ),
        branching_cadence=(
            BranchingCadence(row.branching_cadence)
            if row.branching_cadence is not None
            else None
        ),
        length_preference=(
            LengthPreference(row.length_preference)
            if row.length_preference is not None
            else None
        ),
        branch_count_range=(
            BranchCountRange(row.branch_count_range)
            if row.branch_count_range is not None
            else None
        ),
        play_status=BranchingPlayStatus(row.play_status),
        world_summary=row.world_summary,
        story_seeds=row.story_seeds,
        character_concept=row.character_concept,
        supporting_cast=row.supporting_cast,
        world_constraints=row.world_constraints,
        pacing_notes=row.pacing_notes,
        acceptable_content=row.acceptable_content,
    )


def _branching_tree_to_dict(bt: BranchTree) -> dict[str, Any]:
    return bt.model_dump(mode="json")


def create_branching_session_state(
    session: Session, state: BranchingSessionState
) -> BranchingSessionState:
    """Persist a new BranchingSessionState and return it."""
    row = BranchingSessionStateORM(
        session_id=str(state.session_id),
        story_id=str(state.story_id),
        pacing_stage=state.pacing_stage.value,
        branch_tree=_branching_tree_to_dict(state.branch_tree),
        plot_thread_tracker=[
            pt.model_dump(mode="json") for pt in state.plot_thread_tracker
        ],
        current_node_id=(
            str(state.current_node_id) if state.current_node_id is not None else None
        ),
        interaction_style=(
            state.interaction_style.value
            if state.interaction_style is not None
            else None
        ),
        branching_cadence=(
            state.branching_cadence.value
            if state.branching_cadence is not None
            else None
        ),
        length_preference=(
            state.length_preference.value
            if state.length_preference is not None
            else None
        ),
        branch_count_range=(
            state.branch_count_range.value
            if state.branch_count_range is not None
            else None
        ),
        play_status=state.play_status.value,
        world_summary=state.world_summary,
        story_seeds=state.story_seeds,
        character_concept=state.character_concept,
        supporting_cast=state.supporting_cast,
        world_constraints=state.world_constraints,
        pacing_notes=state.pacing_notes,
        acceptable_content=state.acceptable_content,
    )
    session.add(row)
    session.flush()
    return _branching_orm_to_model(row)


def get_branching_session_state(
    session: Session, session_id: UUID
) -> BranchingSessionState | None:
    """Return a BranchingSessionState by primary key, or None."""
    row = session.get(BranchingSessionStateORM, str(session_id))
    if row is None:
        return None
    return _branching_orm_to_model(row)


def get_branching_session_state_by_story(
    session: Session, story_id: UUID
) -> BranchingSessionState | None:
    """Return the BranchingSessionState for a story, or None."""
    row = session.scalars(
        select(BranchingSessionStateORM).where(
            BranchingSessionStateORM.story_id == str(story_id)
        )
    ).first()
    if row is None:
        return None
    return _branching_orm_to_model(row)


def update_branching_session_state(
    session: Session, state: BranchingSessionState
) -> BranchingSessionState | None:
    """Update mutable fields on an existing BranchingSessionState."""
    row = session.get(BranchingSessionStateORM, str(state.session_id))
    if row is None:
        return None
    row.pacing_stage = state.pacing_stage.value
    row.branch_tree = _branching_tree_to_dict(state.branch_tree)
    row.plot_thread_tracker = [
        pt.model_dump(mode="json") for pt in state.plot_thread_tracker
    ]
    row.current_node_id = (
        str(state.current_node_id) if state.current_node_id is not None else None
    )
    row.interaction_style = (
        state.interaction_style.value if state.interaction_style is not None else None
    )
    row.branching_cadence = (
        state.branching_cadence.value if state.branching_cadence is not None else None
    )
    row.length_preference = (
        state.length_preference.value if state.length_preference is not None else None
    )
    row.branch_count_range = (
        state.branch_count_range.value if state.branch_count_range is not None else None
    )
    row.play_status = state.play_status.value
    row.world_summary = state.world_summary
    row.story_seeds = state.story_seeds
    row.character_concept = state.character_concept
    row.supporting_cast = state.supporting_cast
    row.world_constraints = state.world_constraints
    row.pacing_notes = state.pacing_notes
    row.acceptable_content = state.acceptable_content
    session.flush()
    return _branching_orm_to_model(row)


def apply_branching_config_update(
    session: Session,
    story_id: UUID,
    interaction_style: InteractionStyle | None = None,
    branching_cadence: BranchingCadence | None = None,
    branch_count_range: BranchCountRange | None = None,
    length_preference: LengthPreference | None = None,
    *,
    clear_branch_count_range: bool = False,
) -> bool:
    """Apply non-None config fields to the BranchingSessionState ORM row for a story.

    Only updates the fields that are non-None.  Returns True when the row was
    found and flushed; False when no row exists for the given story_id.

    ``clear_branch_count_range=True`` explicitly sets ``branch_count_range`` to
    NULL regardless of the ``branch_count_range`` argument (use when switching to
    FREEFORM_ONLY, which has no valid range).  When ``False``, the usual
    "non-None means set, None means leave unchanged" semantics apply.
    """
    row = session.scalars(
        select(BranchingSessionStateORM).where(
            BranchingSessionStateORM.story_id == str(story_id)
        )
    ).first()
    if row is None:
        return False
    if interaction_style is not None:
        row.interaction_style = interaction_style.value
    if branching_cadence is not None:
        row.branching_cadence = branching_cadence.value
    if clear_branch_count_range:
        row.branch_count_range = None
    elif branch_count_range is not None:
        row.branch_count_range = branch_count_range.value
    if length_preference is not None:
        row.length_preference = length_preference.value
    session.flush()
    return True


def delete_branching_session_state(session: Session, session_id: UUID) -> bool:
    """Delete a BranchingSessionState.  Returns True if deleted."""
    row = session.get(BranchingSessionStateORM, str(session_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True


# ---------------------------------------------------------------------------
# WritingSessionState
# ---------------------------------------------------------------------------


def _writing_orm_to_model(row: WritingSessionStateORM) -> WritingSessionState:
    return WritingSessionState(
        session_id=UUID(row.session_id),
        story_id=UUID(row.story_id),
        persona_id=row.persona_id,
        persona_registry_version=row.persona_registry_version,
        persona_profile_version=row.persona_profile_version,
        persona_prompt_fingerprint=row.persona_prompt_fingerprint,
        play_status=WritingPlayStatus(row.play_status),
        reading_interests=row.reading_interests,
        writing_interests=row.writing_interests,
        form=WritingForm(row.form) if row.form is not None else None,
        form_other=row.form_other,
        specific_goals=row.specific_goals or "",
        critique_intensity=CritiqueIntensity(row.critique_intensity),
        tense=row.tense,
        pov=row.pov,
        style_density=StyleDensity(row.style_density),
        dialogue_narration_ratio=row.dialogue_narration_ratio,
        genre_conventions=row.genre_conventions,
        beat_constraints=list(row.beat_constraints),
        version_pointers=list(row.version_pointers),
        acceptable_content=row.acceptable_content,
    )


def create_writing_session_state(
    session: Session, state: WritingSessionState
) -> WritingSessionState:
    """Persist a new WritingSessionState and return it."""
    row = WritingSessionStateORM(
        session_id=str(state.session_id),
        story_id=str(state.story_id),
        persona_id=state.persona_id,
        persona_registry_version=state.persona_registry_version,
        persona_profile_version=state.persona_profile_version,
        persona_prompt_fingerprint=state.persona_prompt_fingerprint,
        play_status=state.play_status.value,
        reading_interests=state.reading_interests,
        writing_interests=state.writing_interests,
        form=state.form.value if state.form is not None else None,
        form_other=state.form_other,
        specific_goals=state.specific_goals,
        critique_intensity=state.critique_intensity.value,
        tense=state.tense,
        pov=state.pov,
        style_density=state.style_density.value,
        dialogue_narration_ratio=state.dialogue_narration_ratio,
        genre_conventions=state.genre_conventions,
        beat_constraints=list(state.beat_constraints),
        version_pointers=list(state.version_pointers),
        acceptable_content=state.acceptable_content,
    )
    session.add(row)
    session.flush()
    return _writing_orm_to_model(row)


def get_writing_session_state(
    session: Session, session_id: UUID
) -> WritingSessionState | None:
    """Return a WritingSessionState by primary key, or None."""
    row = session.get(WritingSessionStateORM, str(session_id))
    if row is None:
        return None
    return _writing_orm_to_model(row)


def get_writing_session_state_by_story(
    session: Session, story_id: UUID
) -> WritingSessionState | None:
    """Return the WritingSessionState for a story, or None."""
    row = session.scalars(
        select(WritingSessionStateORM).where(
            WritingSessionStateORM.story_id == str(story_id)
        )
    ).first()
    if row is None:
        return None
    return _writing_orm_to_model(row)


def update_writing_session_state(
    session: Session, state: WritingSessionState
) -> WritingSessionState | None:
    """Update mutable fields on an existing WritingSessionState."""
    row = session.get(WritingSessionStateORM, str(state.session_id))
    if row is None:
        return None
    row.persona_id = state.persona_id
    row.persona_registry_version = state.persona_registry_version
    row.persona_profile_version = state.persona_profile_version
    row.persona_prompt_fingerprint = state.persona_prompt_fingerprint
    row.play_status = state.play_status.value
    row.reading_interests = state.reading_interests
    row.writing_interests = state.writing_interests
    row.form = state.form.value if state.form is not None else None
    row.form_other = state.form_other
    row.specific_goals = state.specific_goals
    row.critique_intensity = state.critique_intensity.value
    row.tense = state.tense
    row.pov = state.pov
    row.style_density = state.style_density.value
    row.dialogue_narration_ratio = state.dialogue_narration_ratio
    row.genre_conventions = state.genre_conventions
    row.beat_constraints = list(state.beat_constraints)
    row.version_pointers = list(state.version_pointers)
    row.acceptable_content = state.acceptable_content
    session.flush()
    return _writing_orm_to_model(row)


def apply_writing_config_update(
    session: Session,
    story_id: UUID,
    persona_id: str | None = None,
    persona_registry_version: int | None = None,
    persona_profile_version: int | None = None,
    persona_prompt_fingerprint: str | None = None,
    critique_intensity: CritiqueIntensity | None = None,
    form: WritingForm | None = None,
    form_other: str | None = None,
    tense: str | None = None,
    pov: str | None = None,
    style_density: StyleDensity | None = None,
    dialogue_narration_ratio: int | None = None,
    genre_conventions: str | None = None,
    specific_goals: str | None = None,
    acceptable_content: str | None = None,
    beat_constraints: list[str] | None = None,
    version_pointers: list[Any] | None = None,
    play_status: WritingPlayStatus | None = None,
) -> bool:
    """Apply non-None config fields to the WritingSessionState ORM row for a story.

    Only updates fields that are non-None. Returns True when the row was found
    and flushed; False when no row exists for the given story_id.

    ``form``/``form_other`` integrity guard: if the post-update form would be
    ``other`` but neither the update nor the existing row supplies ``form_other``,
    the form change is silently skipped to prevent an unreadable row.

    ``specific_goals``/``play_status`` integrity guard: if the post-update
    play_status is (or remains) ``IN_PLAY`` but the new ``specific_goals``
    value is blank/whitespace, the goals write is silently skipped to prevent
    an unreadable row (mirrors the form/form_other guard; also complements the
    play_status guard below, which independently prevents *newly persisting*
    IN_PLAY without nonblank persona_id/specific_goals).

    ``beat_constraints`` replaces the full constraint list (replace semantics,
    consistent with WritingSessionState validator behaviour).  Unlike
    ``form``/``form_other`` and ``specific_goals``/``play_status``,
    ``beat_constraints`` and ``dialogue_narration_ratio`` validity does not
    depend on another field or on existing row state — ``WritingConfigUpdate``
    (the only production caller's DTO) fully validates both at construction
    time, so no CRUD-level guard is needed for them.

    ``version_pointers`` are appended to the existing list, deduped by
    ``pointer_id`` so idempotent re-extraction doesn't grow the list unboundedly.

    Used by the OOC config extractor — all writes are inside the OOC transaction
    and roll back if OOC_HANDLED does not commit.
    """
    row = session.scalars(
        select(WritingSessionStateORM).where(
            WritingSessionStateORM.story_id == str(story_id)
        )
    ).first()
    if row is None:
        return False
    if persona_id is not None:
        row.persona_id = persona_id
    if persona_registry_version is not None:
        row.persona_registry_version = persona_registry_version
    if persona_profile_version is not None:
        row.persona_profile_version = persona_profile_version
    if persona_prompt_fingerprint is not None:
        row.persona_prompt_fingerprint = persona_prompt_fingerprint

    # form/form_other integrity: skip form change if it would leave form=OTHER
    # without a form_other value (which would make the row unreadable).
    if form is not None:
        effective_form_other = form_other if form_other is not None else row.form_other
        if form is WritingForm.OTHER and not effective_form_other:
            pass  # skip to avoid unreadable row
        elif form is not WritingForm.OTHER:
            # Concrete form: ``form_other`` is meaningful only for OTHER, so a
            # concrete form update clears any stale custom-form label outright —
            # even when the caller did not pass form_other.  This prevents a stale
            # label from later governing prompts, OOC state, or metadata snapshots.
            row.form = form.value
            row.form_other = None
        else:
            row.form = form.value
            if form_other is not None:
                row.form_other = form_other
    elif form_other is not None:
        # Guard: if the persisted row already has form=OTHER, a blank form_other
        # would make it unreadable on the next CRUD read (_writing_orm_to_model
        # constructs WritingSessionState whose validator rejects form=OTHER +
        # falsey form_other).
        if not (row.form == WritingForm.OTHER.value and not form_other):
            row.form_other = form_other

    if critique_intensity is not None:
        row.critique_intensity = critique_intensity.value
    if tense is not None:
        row.tense = tense
    if pov is not None:
        row.pov = pov
    if style_density is not None:
        row.style_density = style_density.value
    if dialogue_narration_ratio is not None:
        row.dialogue_narration_ratio = dialogue_narration_ratio
    if genre_conventions is not None:
        row.genre_conventions = genre_conventions
    if specific_goals is not None:
        # Cross-field integrity guard (mirrors the form/form_other guard
        # above): specific_goals validity depends on play_status, a
        # different field, and the *existing* row's play_status when this
        # call does not touch play_status.  A row already IN_PLAY — or one
        # this same call is promoting to IN_PLAY — must never end up with a
        # blank specific_goals; that violates WritingSessionState's IN_PLAY
        # construction invariant and makes the row unreadable on the next
        # fetch.  Effective play_status is the requested value if supplied,
        # else the row's current value.  A goal-clearing update paired with
        # an explicit transition to SETUP is unaffected.
        _effective_status_for_goal = (
            play_status
            if play_status is not None
            else WritingPlayStatus(row.play_status)
        )
        if (
            _effective_status_for_goal is WritingPlayStatus.IN_PLAY
            and not specific_goals.strip()
        ):
            pass  # skip: cannot blank specific_goals while (or becoming) IN_PLAY
        else:
            row.specific_goals = specific_goals
    if acceptable_content is not None:
        row.acceptable_content = acceptable_content
    if beat_constraints is not None:
        row.beat_constraints = list(beat_constraints)
    if version_pointers is not None and len(version_pointers) > 0:
        existing = list(row.version_pointers) if row.version_pointers else []
        existing_ids = {
            str(p.get("pointer_id")) for p in existing if isinstance(p, dict)
        }
        for ptr in version_pointers:
            ptr_dict = ptr if isinstance(ptr, dict) else ptr
            ptr_id = str(ptr_dict.get("pointer_id", ""))
            if ptr_id and ptr_id not in existing_ids:
                existing.append(ptr_dict)
                existing_ids.add(ptr_id)
        row.version_pointers = existing
    if play_status is not None:
        # Boundary (PR #116 remediation, owner decision): this generic CRUD
        # helper enforces local persisted-state *shape* only — nonblank
        # persona_id and nonblank specific_goals — never registry-aware
        # validity/selectability.  It has no persona registry dependency and
        # must not gain one: this module is generic persistence, not a
        # registry-aware service, and importing the registry here would
        # couple low-level CRUD to a mode-specific registry.  A caller could
        # in principle pass an unknown/hidden/deprecated persona_id here and
        # this guard would not catch it — registry verification is the
        # responsibility of the caller (currently the orchestrator's OOC
        # persona-selection path), applied before this call.  ``row`` here
        # reflects the effective values after any persona_id/specific_goals
        # updates above.
        if play_status is WritingPlayStatus.IN_PLAY and (
            not row.persona_id or not (row.specific_goals or "").strip()
        ):
            pass  # skip: cannot enter IN_PLAY without persona_id + a goal
        else:
            row.play_status = play_status.value
    session.flush()
    return True


def delete_writing_session_state(session: Session, session_id: UUID) -> bool:
    """Delete a WritingSessionState.  Returns True if deleted."""
    row = session.get(WritingSessionStateORM, str(session_id))
    if row is None:
        return False
    session.delete(row)
    session.flush()
    return True
