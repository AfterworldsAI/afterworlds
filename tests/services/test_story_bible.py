"""Tests for the Story Bible service — Issue 4 acceptance criteria."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from itertools import count
from uuid import UUID

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from afterworlds.models.enums import (
    EventSignificance,
    ProposalStatus,
    ProposalType,
    StoryMode,
)
from afterworlds.models.story import Story
from afterworlds.models.story_bible import (
    ProvisionalProposal,
    StoryBibleContext,
)
from afterworlds.persistence.crud.story import create_story
from afterworlds.persistence.orm.story_bible import (
    SBDynamicFieldHistoryORM,
    SBEventORM,
    SBProvisionalStagingORM,
)
from afterworlds.services.story_bible import (
    ALWAYS_INCLUDE_SIGNIFICANCE,
    EVENTS_LEDGER_N,
    ConfirmationRequiredError,
    EntityNotFoundError,
    StoryBibleService,
)
from tests.services.conftest import (
    make_cast_entry,
    make_event,
    make_forbidden_fact,
    make_locked_fact,
    make_relationship,
    make_setting,
)


def _cast_proposal(
    service: StoryBibleService,
    story_id: UUID,
    proposed_value: dict[str, object],
    proposal_type: ProposalType = ProposalType.SOFT_FACT,
) -> ProvisionalProposal:
    """Return a contract-valid generic proposal targeting a new cast entry (#51)."""
    entry = service.add_cast_entry(story_id, make_cast_entry(story_id))
    return ProvisionalProposal(
        story_id=story_id,
        proposal_type=proposal_type,
        target_entity_type="cast_entry",
        target_entity_id=str(entry.cast_id),
        proposed_value=proposed_value,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


# ---------------------------------------------------------------------------
# Significance enum
# ---------------------------------------------------------------------------


class TestSignificanceEnum:
    def test_all_required_values_present(self) -> None:
        required = {
            EventSignificance.ROUTINE,
            EventSignificance.CHARACTER_DEATH,
            EventSignificance.LOCKED_FACT_ESTABLISHED,
            EventSignificance.MAJOR_PLOT_TURN,
            EventSignificance.RELATIONSHIP_CHANGE,
        }
        for v in required:
            assert v in EventSignificance

    def test_always_include_values_defined_in_service(self) -> None:
        """The always-include set must be defined in the service, not in tests."""
        assert len(ALWAYS_INCLUDE_SIGNIFICANCE) > 0
        assert EventSignificance.CHARACTER_DEATH in ALWAYS_INCLUDE_SIGNIFICANCE
        assert EventSignificance.LOCKED_FACT_ESTABLISHED in ALWAYS_INCLUDE_SIGNIFICANCE
        assert EventSignificance.MAJOR_PLOT_TURN in ALWAYS_INCLUDE_SIGNIFICANCE
        assert EventSignificance.RELATIONSHIP_CHANGE in ALWAYS_INCLUDE_SIGNIFICANCE

    def test_routine_not_always_include(self) -> None:
        assert EventSignificance.ROUTINE not in ALWAYS_INCLUDE_SIGNIFICANCE

    def test_unrecognised_value_raises(self) -> None:
        with pytest.raises(ValueError):
            EventSignificance("not_a_real_value")


# ---------------------------------------------------------------------------
# Tiered inclusion policy
# ---------------------------------------------------------------------------


class TestTieredInclusionPolicy:
    def test_returns_n_most_recent_when_no_always_include(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """When no events qualify for always-include, return exactly N recent."""
        total = EVENTS_LEDGER_N + 5
        for i in range(total):
            e = make_event(
                story_id,
                desc=f"Event {i}",
                significance=EventSignificance.ROUTINE,
            )
            # stagger timestamps so ordering is deterministic
            e = e.model_copy(
                update={"created_at": datetime(2026, 1, 1, i + 1, tzinfo=UTC)}
            )
            service.add_event(story_id, e)

        ctx = service.get_active_context_window(story_id)
        assert len(ctx.events) == EVENTS_LEDGER_N

    def test_always_include_events_outside_n_window_are_included(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """An always-include event older than N must appear in the window."""
        # Add one high-significance event at t=1 (oldest)
        old_event = make_event(
            story_id,
            desc="The king died.",
            significance=EventSignificance.CHARACTER_DEATH,
        )
        old_event = old_event.model_copy(
            update={"created_at": datetime(2026, 1, 1, 1, tzinfo=UTC)}
        )
        service.add_event(story_id, old_event)

        # Fill N more ROUTINE events after the old one
        for i in range(EVENTS_LEDGER_N):
            e = make_event(
                story_id,
                desc=f"Routine {i}",
                significance=EventSignificance.ROUTINE,
            )
            e = e.model_copy(
                update={"created_at": datetime(2026, 1, 2, i + 1, tzinfo=UTC)}
            )
            service.add_event(story_id, e)

        ctx = service.get_active_context_window(story_id)
        # N routine + 1 always-include = N+1
        assert len(ctx.events) == EVENTS_LEDGER_N + 1
        descriptions = {ev.description for ev in ctx.events}
        assert "The king died." in descriptions

    def test_event_window_is_stable_with_identical_timestamps(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """N-window must be deterministic when events share a timestamp."""
        shared_ts = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        for i in range(EVENTS_LEDGER_N + 3):
            e = make_event(
                story_id,
                desc=f"Event {i}",
                significance=EventSignificance.ROUTINE,
            )
            e = e.model_copy(update={"created_at": shared_ts})
            service.add_event(story_id, e)

        ctx1 = service.get_active_context_window(story_id)
        ctx2 = service.get_active_context_window(story_id)
        ids1 = [str(ev.event_id) for ev in ctx1.events]
        ids2 = [str(ev.event_id) for ev in ctx2.events]
        assert ids1 == ids2
        assert len(ids1) == EVENTS_LEDGER_N

    def test_n_is_configurable_not_hardcoded(self) -> None:
        """EVENTS_LEDGER_N is a module-level constant, not embedded in logic."""
        assert isinstance(EVENTS_LEDGER_N, int)
        assert EVENTS_LEDGER_N == 15  # starting value per known_unknowns.md

    def test_always_include_policy_not_reimplemented_in_tests(self) -> None:
        """Callers use the service constant — not a local reimplementation."""
        # This test asserts the frozenset is imported from the service.
        assert isinstance(ALWAYS_INCLUDE_SIGNIFICANCE, frozenset)

    def test_always_include_event_within_n_window_not_duplicated(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """An always-include event that also falls in the N window appears once."""
        e = make_event(
            story_id,
            desc="Major plot turn.",
            significance=EventSignificance.MAJOR_PLOT_TURN,
        )
        service.add_event(story_id, e)

        ctx = service.get_active_context_window(story_id)
        descriptions = [ev.description for ev in ctx.events]
        assert descriptions.count("Major plot turn.") == 1


def _seed_tiered_layout(
    service: StoryBibleService, session: Session, story_id: UUID
) -> tuple[list[UUID], set[UUID]]:
    """Seed events whose tiered selection is known by construction.

    Returns the expected output ids in order and the ids of the active
    older routine rows that the selection must never load.
    """
    base = datetime(2026, 1, 1, tzinfo=UTC)
    ids = (UUID(int=i) for i in count(1))

    def add(sid: UUID, minute: int, significance: EventSignificance, eid: UUID) -> UUID:
        new = make_event(sid, desc=f"m{minute}", significance=significance)
        service.add_event(
            sid,
            new.model_copy(
                update={
                    "event_id": eid,
                    "created_at": base + timedelta(minutes=minute),
                }
            ),
        )
        return eid

    routine = EventSignificance.ROUTINE
    older_routine: set[UUID] = set()

    # Many older significant events (three per always-include category),
    # interleaved with older routine events.
    older_significant: list[UUID] = []
    categories = sorted(ALWAYS_INCLUDE_SIGNIFICANCE)
    for j in range(3 * len(categories)):
        older_significant.append(
            add(story_id, 2 * j, categories[j % len(categories)], next(ids))
        )
        older_routine.add(add(story_id, 2 * j + 1, routine, next(ids)))

    # Older significant events sharing a timestamp: event_id ASC breaks the tie
    # regardless of insertion order.
    tie_a, tie_b = next(ids), next(ids)
    add(story_id, 60, EventSignificance.WORLD_STATE_CHANGE, tie_b)
    add(story_id, 60, EventSignificance.CHARACTER_DEATH, tie_a)

    # Timestamp tie straddling the N boundary: event_id decides the cut.
    t0, t1, t2, t3 = (next(ids) for _ in range(4))
    add(story_id, 100, routine, t3)
    add(story_id, 100, EventSignificance.CHARACTER_DEATH, t2)
    add(story_id, 100, routine, t1)
    add(story_id, 100, routine, t0)
    older_routine.add(t3)

    # Recent window: N-2 newer events, one significant (overlap/dedup).
    recent: list[UUID] = []
    for k in range(EVENTS_LEDGER_N - 2):
        sig = EventSignificance.MAJOR_PLOT_TURN if k == 3 else routine
        recent.append(add(story_id, 101 + k, sig, next(ids)))

    # Newest rows are inactive or belong to another story; neither may take a
    # recent-N slot or appear in the output.
    for sig in (routine, EventSignificance.CHARACTER_DEATH):
        service.soft_delete("event", add(story_id, 500, sig, next(ids)))
    now = datetime(2026, 1, 1, tzinfo=UTC)
    other = Story(title="Other", mode=StoryMode.RPG, created_at=now, updated_at=now)
    create_story(session, other)
    for sig in (routine, EventSignificance.CHARACTER_DEATH):
        add(other.story_id, 500, sig, next(ids))
    add(other.story_id, 0, EventSignificance.MAJOR_PLOT_TURN, next(ids))
    session.commit()

    expected = recent[::-1] + [t0, t1] + [t2, tie_a, tie_b] + older_significant[::-1]
    return expected, older_routine


class TestTieredEventSelection:
    """CRD Issue 4 / #45: selection runs in SQL with the ADR-0005 policy."""

    def test_selection_matches_policy(
        self, service: StoryBibleService, session: Session, story_id: UUID
    ) -> None:
        expected, _ = _seed_tiered_layout(service, session, story_id)

        ctx = service.get_active_context_window(story_id)

        assert [ev.event_id for ev in ctx.events] == expected
        assert all(ev.story_id == story_id and ev.is_active for ev in ctx.events)
        recent_segment = ctx.events[:EVENTS_LEDGER_N]
        older_segment = ctx.events[EVENTS_LEDGER_N:]
        assert len(older_segment) == 3 * len(ALWAYS_INCLUDE_SIGNIFICANCE) + 3
        assert all(
            ev.significance in ALWAYS_INCLUDE_SIGNIFICANCE for ev in older_segment
        )
        assert any(
            ev.significance in ALWAYS_INCLUDE_SIGNIFICANCE for ev in recent_segment
        )

    def test_older_routine_rows_are_not_materialized(
        self, service: StoryBibleService, session: Session, story_id: UUID
    ) -> None:
        expected, older_routine = _seed_tiered_layout(service, session, story_id)
        session.expunge_all()  # force rows to be loaded from SQL, not the map
        loaded: list[UUID] = []

        def on_load(target: SBEventORM, _context: object) -> None:
            loaded.append(UUID(target.event_id))

        event.listen(SBEventORM, "load", on_load)
        try:
            ctx = service.get_active_context_window(story_id)
        finally:
            event.remove(SBEventORM, "load", on_load)

        assert loaded == expected == [ev.event_id for ev in ctx.events]
        assert older_routine.isdisjoint(loaded)

    def test_no_events_and_fewer_than_n(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        assert service.get_active_context_window(story_id).events == ()

        added: list[UUID] = []
        for hour, sig in enumerate(
            (EventSignificance.ROUTINE, EventSignificance.RELATIONSHIP_CHANGE)
        ):
            e = make_event(story_id, significance=sig).model_copy(
                update={"created_at": datetime(2026, 1, 1, hour, tzinfo=UTC)}
            )
            added.append(service.add_event(story_id, e).event_id)

        ctx = service.get_active_context_window(story_id)
        assert [ev.event_id for ev in ctx.events] == added[::-1]


# ---------------------------------------------------------------------------
# Partition isolation
# ---------------------------------------------------------------------------


class TestPartitionIsolation:
    def test_static_field_update_raises_without_confirmation(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        with pytest.raises(ConfirmationRequiredError):
            service.update_static_field(story_id, entry.cast_id, "name", "NewName")

    def test_static_field_update_succeeds_with_confirmation(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        updated = service.update_static_field(
            story_id, entry.cast_id, "name", "NewName", confirmed=True
        )
        assert updated.name == "NewName"

    def test_dynamic_field_update_requires_no_confirmation(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        updated = service.update_dynamic_field(
            story_id, entry.cast_id, "current_location", "Castle Dungeon"
        )
        assert updated.current_location == "Castle Dungeon"

    def test_provisional_entries_not_returned_as_ratified_canon(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        proposal = _cast_proposal(service, story_id, {"current_status": "Sky is green"})
        service.stage_proposed_update(story_id, proposal)

        # The context window must not include staging entries as canon
        ctx = service.get_active_context_window(story_id)
        # Locked facts and forbidden facts should be empty
        assert ctx.locked_facts == ()
        assert ctx.forbidden_facts == ()


# ---------------------------------------------------------------------------
# Dynamic field versioning
# ---------------------------------------------------------------------------


class TestDynamicVersioning:
    def test_prior_value_preserved_after_update(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        service.update_dynamic_field(
            story_id, entry.cast_id, "current_location", "Old Location"
        )
        service.update_dynamic_field(
            story_id, entry.cast_id, "current_location", "New Location"
        )

        history = service.get_dynamic_field_history("cast_entry", entry.cast_id)
        field_history = [h for h in history if h.field_name == "current_location"]
        # Two updates → two history records
        assert len(field_history) == 2

    def test_history_records_old_value(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        service.update_dynamic_field(
            story_id, entry.cast_id, "current_location", "First Place"
        )
        service.update_dynamic_field(
            story_id, entry.cast_id, "current_location", "Second Place"
        )

        history = service.get_dynamic_field_history("cast_entry", entry.cast_id)
        locations = {h.old_value for h in history if h.field_name == "current_location"}
        # First update had old_value=None; second had old_value="First Place"
        assert "First Place" in locations

    def test_invalid_dynamic_value_raises_before_persisting(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """An invalid dynamic value must raise without persisting the bad state.

        Validates the fix for the validate-before-flush bug: prior to the fix,
        the ORM row mutation and history row were flushed before model
        validation ran, leaving invalid canon in the session even when the
        method raised.
        """
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        with pytest.raises(ValueError):
            service.update_dynamic_field(
                story_id, entry.cast_id, "is_alive", "not_a_bool"
            )

        # Live canon must be unchanged
        refreshed = service.get_character(story_id, entry.cast_id)
        assert refreshed is not None
        assert refreshed.is_alive is True

        # No history row must have been written for the failed update
        history = service.get_dynamic_field_history("cast_entry", entry.cast_id)
        failed = [h for h in history if h.field_name == "is_alive"]
        assert failed == []


# ---------------------------------------------------------------------------
# Locked facts
# ---------------------------------------------------------------------------


class TestLockedFacts:
    def test_locked_facts_queryable_as_distinct_set(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        fact = make_locked_fact(story_id, "The king is dead.")
        service.add_locked_fact(story_id, fact)

        result = service.get_locked_facts(story_id)
        assert len(result) == 1
        assert result[0].fact_text == "The king is dead."

    def test_proposed_locked_fact_stages_correctly(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.LOCKED_FACT,
            proposed_value={"fact_text": "The heir is cursed."},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        staged = service.stage_proposed_update(story_id, proposal)
        assert staged.status == ProposalStatus.PENDING
        assert staged.requires_confirmation is True

    def test_locked_fact_proposal_requires_confirmation_to_ratify(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.LOCKED_FACT,
            proposed_value={"fact_text": "The heir is cursed."},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        staged = service.stage_proposed_update(story_id, proposal)

        with pytest.raises(ConfirmationRequiredError):
            service.ratify_update(staged.proposal_id)

    def test_locked_fact_proposal_ratified_with_confirmation(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.LOCKED_FACT,
            proposed_value={"fact_text": "The heir is cursed."},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        staged = service.stage_proposed_update(story_id, proposal)
        ratified = service.ratify_update(staged.proposal_id, confirmed=True)

        assert ratified.status == ProposalStatus.RATIFIED
        # The locked fact should now be in the canon table
        facts = service.get_locked_facts(story_id)
        assert any("cursed" in f.fact_text for f in facts)


# ---------------------------------------------------------------------------
# Forbidden facts
# ---------------------------------------------------------------------------


class TestForbiddenFacts:
    def test_forbidden_facts_queryable_as_distinct_set(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        fact = make_forbidden_fact(story_id)
        service.add_forbidden_fact(story_id, fact)

        result = service.get_forbidden_facts(story_id)
        assert len(result) == 1
        assert result[0].fact_text == fact.fact_text

    def test_empty_forbidden_facts_is_valid(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        result = service.get_forbidden_facts(story_id)
        assert result == []


# ---------------------------------------------------------------------------
# Relationship Ledger
# ---------------------------------------------------------------------------


class TestRelationshipLedger:
    def test_directional_entries_queryable_per_subject(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        aldric = make_cast_entry(story_id, "Aldric")
        serena = make_cast_entry(story_id, "Serena")
        service.add_cast_entry(story_id, aldric)
        service.add_cast_entry(story_id, serena)

        rel = make_relationship(story_id, aldric.cast_id, serena.cast_id)
        service.add_relationship(story_id, rel)

        ctx = service.get_active_context_window(story_id)
        subjects = [r.subject_cast_id for r in ctx.relationship_ledger]
        assert aldric.cast_id in subjects

    def test_context_window_cast_order_is_deterministic(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Cast list in context window must be in stable created_at ASC order."""
        for i, name in enumerate(["Zara", "Aldric", "Mira"]):
            e = make_cast_entry(story_id, name)
            e = e.model_copy(
                update={"created_at": datetime(2026, 1, i + 1, tzinfo=UTC)}
            )
            service.add_cast_entry(story_id, e)

        ctx1 = service.get_active_context_window(story_id)
        ctx2 = service.get_active_context_window(story_id)
        names1 = [c.name for c in ctx1.cast]
        names2 = [c.name for c in ctx2.cast]
        assert names1 == names2
        assert names1 == ["Zara", "Aldric", "Mira"]

    def test_asymmetric_relationships_representable(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Aldric→Serena (ally) and Serena→Aldric (enemy) can coexist."""
        from afterworlds.models.enums import RelationshipType

        aldric = make_cast_entry(story_id, "Aldric")
        serena = make_cast_entry(story_id, "Serena")
        service.add_cast_entry(story_id, aldric)
        service.add_cast_entry(story_id, serena)

        now = datetime(2026, 1, 1, tzinfo=UTC)
        from afterworlds.models.story_bible import RelationshipLedger

        ally = RelationshipLedger(
            story_id=story_id,
            subject_cast_id=aldric.cast_id,
            object_cast_id=serena.cast_id,
            relationship_type=RelationshipType.ALLY,
            created_at=now,
            updated_at=now,
        )
        enemy = RelationshipLedger(
            story_id=story_id,
            subject_cast_id=serena.cast_id,
            object_cast_id=aldric.cast_id,
            relationship_type=RelationshipType.ENEMY,
            created_at=now,
            updated_at=now,
        )
        service.add_relationship(story_id, ally)
        service.add_relationship(story_id, enemy)

        ctx = service.get_active_context_window(story_id)
        types = {r.relationship_type for r in ctx.relationship_ledger}
        assert RelationshipType.ALLY in types
        assert RelationshipType.ENEMY in types


# ---------------------------------------------------------------------------
# Staging area
# ---------------------------------------------------------------------------


class TestStagingArea:
    def test_stage_proposed_update_does_not_touch_ratified_canon(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        proposal = _cast_proposal(service, story_id, {"current_status": "sky is green"})
        service.stage_proposed_update(story_id, proposal)
        # Nothing in locked or forbidden facts
        assert service.get_locked_facts(story_id) == []
        assert service.get_forbidden_facts(story_id) == []

    def test_ratify_update_promotes_correctly(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.UNRESOLVED_THREAD,
            proposed_value={"description": "Who killed the vizier?"},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        staged = service.stage_proposed_update(story_id, proposal)
        ratified = service.ratify_update(staged.proposal_id)

        assert ratified.status == ProposalStatus.RATIFIED
        ctx = service.get_active_context_window(story_id)
        thread_descs = [t.description for t in ctx.active_plot_threads]
        assert "Who killed the vizier?" in thread_descs

    def test_reject_update_marks_correctly_without_deleting(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        proposal = _cast_proposal(service, story_id, {"notes": "dragons are friendly"})
        staged = service.stage_proposed_update(story_id, proposal)
        rejected = service.reject_update(staged.proposal_id)

        assert rejected.status == ProposalStatus.REJECTED
        # The record must still exist — check via the ORM directly
        row = service._session.get(SBProvisionalStagingORM, str(staged.proposal_id))
        assert row is not None
        assert row.status == "rejected"

    def test_reject_soft_deleted_proposal_raises(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """A soft-deleted proposal must not be rejectable."""
        proposal = _cast_proposal(service, story_id, {"notes": "the kingdom fell"})
        staged = service.stage_proposed_update(story_id, proposal)
        service.soft_delete("proposal", staged.proposal_id)

        with pytest.raises(EntityNotFoundError, match="soft-deleted"):
            service.reject_update(staged.proposal_id)

    def test_double_ratify_raises(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Ratifying an already-RATIFIED proposal must raise ValueError."""
        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.UNRESOLVED_THREAD,
            proposed_value={"description": "Thread once."},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        staged = service.stage_proposed_update(story_id, proposal)
        service.ratify_update(staged.proposal_id)

        with pytest.raises(ValueError, match="already"):
            service.ratify_update(staged.proposal_id)

    def test_ratify_soft_deleted_proposal_raises(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """A soft-deleted (inactive) proposal must not be ratified."""
        proposal = _cast_proposal(service, story_id, {"notes": "sky is purple"})
        staged = service.stage_proposed_update(story_id, proposal)
        service.soft_delete("proposal", staged.proposal_id)

        with pytest.raises(EntityNotFoundError):
            service.ratify_update(staged.proposal_id)

    def test_ratify_after_reject_raises(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """A REJECTED proposal must not be re-ratified."""
        proposal = _cast_proposal(service, story_id, {"notes": "sky is purple"})
        staged = service.stage_proposed_update(story_id, proposal)
        service.reject_update(staged.proposal_id)

        with pytest.raises(ValueError, match="already"):
            service.ratify_update(staged.proposal_id)

    def test_reject_after_ratify_raises(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """A RATIFIED proposal must not be silently downgraded to REJECTED."""
        proposal = _cast_proposal(service, story_id, {"is_alive": False})
        staged = service.stage_proposed_update(story_id, proposal)
        service.ratify_update(staged.proposal_id)

        with pytest.raises(ValueError, match="already"):
            service.reject_update(staged.proposal_id)

    def test_ratify_locked_fact_with_missing_fact_text_raises(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """A locked_fact proposal missing fact_text must raise; no blank canon."""
        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.LOCKED_FACT,
            proposed_value={},  # fact_text absent
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        staged = service.stage_proposed_update(story_id, proposal)

        with pytest.raises(ValueError, match="fact_text"):
            service.ratify_update(staged.proposal_id, confirmed=True)

        # No blank locked fact should have been written
        assert service.get_locked_facts(story_id) == []

    def test_ratify_unresolved_thread_with_missing_description_raises(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Unresolved_thread proposal missing description must raise; no blank canon."""
        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.UNRESOLVED_THREAD,
            proposed_value={},  # description absent
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        staged = service.stage_proposed_update(story_id, proposal)

        with pytest.raises(ValueError, match="description"):
            service.ratify_update(staged.proposal_id)

        ctx = service.get_active_context_window(story_id)
        assert ctx.active_plot_threads == ()

    def test_soft_fact_ratification_marks_proposal_ratified(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Ratifying a soft_fact proposal sets status RATIFIED.

        Generic ratification records approval only (#51); no path applies a
        generic proposal to live canon, so the cast entry must be unchanged.
        """
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)
        original_location = entry.current_location

        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.SOFT_FACT,
            target_entity_type="cast_entry",
            target_entity_id=str(entry.cast_id),
            proposed_value={"current_location": "The Iron Tower"},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        staged = service.stage_proposed_update(story_id, proposal)
        ratified = service.ratify_update(staged.proposal_id)

        assert ratified.status == ProposalStatus.RATIFIED
        # Regression: canon must NOT be modified at ratification
        unchanged = service.get_character(story_id, entry.cast_id)
        assert unchanged is not None
        assert unchanged.current_location == original_location

    def test_transient_state_ratification_marks_proposal_ratified(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Ratifying a transient_state proposal sets status RATIFIED.

        Generic ratification records approval only (#51); no path applies a
        generic proposal to live canon, so the cast entry must be unchanged.
        """
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.TRANSIENT_STATE,
            target_entity_type="cast_entry",
            target_entity_id=str(entry.cast_id),
            proposed_value={"is_alive": False},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        staged = service.stage_proposed_update(story_id, proposal)
        ratified = service.ratify_update(staged.proposal_id)

        assert ratified.status == ProposalStatus.RATIFIED
        # Regression: canon must NOT be modified at ratification
        unchanged = service.get_character(story_id, entry.cast_id)
        assert unchanged is not None
        assert unchanged.is_alive is True

    def test_soft_fact_ratification_does_not_apply_to_canon(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Regression: soft_fact ratification must not auto-apply to live canon.

        Generic ratification is approval/status-only (#51).  Typed Extractor
        routing applies its own changes and never consumes generic rows.
        This test guards against future drift that re-introduces auto-apply
        inside ratify_update.
        """
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.SOFT_FACT,
            target_entity_type="cast_entry",
            target_entity_id=str(entry.cast_id),
            proposed_value={"is_alive": False},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        staged = service.stage_proposed_update(story_id, proposal)
        ratified = service.ratify_update(staged.proposal_id)

        assert ratified.status == ProposalStatus.RATIFIED
        # Live canon is unchanged — generic ratification never applies canon
        character = service.get_character(story_id, entry.cast_id)
        assert character is not None
        assert character.is_alive is True

    def test_all_four_proposal_types_representable(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        for ptype in ProposalType:
            if ptype in (ProposalType.SOFT_FACT, ProposalType.TRANSIENT_STATE):
                proposal = _cast_proposal(service, story_id, {"notes": "x"}, ptype)
            else:
                proposal = ProvisionalProposal(
                    story_id=story_id,
                    proposal_type=ptype,
                    proposed_value={"data": ptype.value},
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                )
            staged = service.stage_proposed_update(story_id, proposal)
            assert staged.proposal_type == ptype


# ---------------------------------------------------------------------------
# Soft delete
# ---------------------------------------------------------------------------


class TestSoftDelete:
    def test_soft_deleted_entry_is_inactive_not_removed(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        service.soft_delete("cast_entry", entry.cast_id)

        # Inactive entries are not returned by get_character
        result = service.get_character(story_id, entry.cast_id)
        assert result is None

    def test_soft_deleted_entry_remains_in_sqlite(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        service.soft_delete("cast_entry", entry.cast_id)

        from afterworlds.persistence.orm.story_bible import SBCastEntryORM

        row = service._session.get(SBCastEntryORM, str(entry.cast_id))
        assert row is not None
        assert row.is_active is False

    def test_no_hard_delete_path_in_service_code(self) -> None:
        """Service must not expose any hard-delete method."""
        # Introspection: the service class must not have a delete or
        # hard_delete method.
        methods = [m for m in dir(StoryBibleService) if "delete" in m.lower()]
        # soft_delete is the only delete method
        assert all(
            "soft" in m for m in methods
        ), f"Found non-soft delete method(s): {methods}"


# ---------------------------------------------------------------------------
# Setting confirmation guard
# ---------------------------------------------------------------------------


class TestSettingConfirmationGuard:
    def test_first_setting_requires_no_confirmation(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Creating the first setting needs no confirmation."""
        s = make_setting(story_id)
        result = service.create_setting(story_id, s)
        assert result.is_active is True

    def test_second_setting_raises_without_confirmation(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Replacing an active setting without confirmed=True must raise."""
        service.create_setting(story_id, make_setting(story_id))

        with pytest.raises(ConfirmationRequiredError):
            service.create_setting(story_id, make_setting(story_id))

    def test_second_setting_with_confirmation_deactivates_prior(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """A confirmed replacement deactivates the previous active setting."""
        first = make_setting(story_id)
        service.create_setting(story_id, first)

        second = make_setting(story_id)
        second = second.model_copy(update={"summary": "New world order."})
        service.create_setting(story_id, second, confirmed=True)

        from afterworlds.persistence.orm.story_bible import SBSettingORM

        first_row = service._session.get(SBSettingORM, str(first.setting_id))
        assert first_row is not None
        assert first_row.is_active is False

    def test_only_one_active_setting_after_confirmed_replacement(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """After a confirmed replacement, exactly one active setting exists."""
        service.create_setting(story_id, make_setting(story_id))
        service.create_setting(story_id, make_setting(story_id), confirmed=True)

        ctx = service.get_active_context_window(story_id)
        assert ctx.setting is not None
        assert ctx.setting.summary == "A dark fantasy realm."

    def test_confirmed_replacement_deactivates_all_prior_active_settings(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """All pre-existing active settings are deactivated, not just one."""
        from sqlalchemy import select as sa_select

        from afterworlds.persistence.orm.story_bible import SBSettingORM

        # Bypass the guard to force two active rows (simulates stale data)
        s1 = make_setting(story_id)
        s2 = make_setting(story_id)
        for s in (s1, s2):
            service._session.add(
                SBSettingORM(
                    setting_id=str(s.setting_id),
                    story_id=str(story_id),
                    summary=s.summary,
                    world_rules=s.world_rules,
                    geography=s.geography,
                    time_period=s.time_period,
                    is_active=True,
                    created_at=s.created_at.isoformat(),
                )
            )
        service._session.flush()

        # Confirmed replacement must deactivate both stale rows
        new_setting = make_setting(story_id)
        new_setting = new_setting.model_copy(update={"summary": "Brand new world."})
        service.create_setting(story_id, new_setting, confirmed=True)

        active_rows = (
            service._session.execute(
                sa_select(SBSettingORM).where(
                    SBSettingORM.story_id == str(story_id),
                    SBSettingORM.is_active.is_(True),
                )
            )
            .scalars()
            .all()
        )
        assert len(active_rows) == 1
        assert active_rows[0].summary == "Brand new world."


# ---------------------------------------------------------------------------
# Relationship cast ID validation
# ---------------------------------------------------------------------------


class TestRelationshipCastValidation:
    def test_add_relationship_with_unknown_subject_raises(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """subject_cast_id that doesn't exist must raise EntityNotFoundError."""
        from uuid import uuid4

        from afterworlds.services.story_bible import EntityNotFoundError

        serena = make_cast_entry(story_id, "Serena")
        service.add_cast_entry(story_id, serena)

        rel = make_relationship(story_id, uuid4(), serena.cast_id)
        with pytest.raises(EntityNotFoundError):
            service.add_relationship(story_id, rel)

    def test_add_relationship_with_unknown_object_raises(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """object_cast_id that doesn't exist must raise EntityNotFoundError."""
        from uuid import uuid4

        from afterworlds.services.story_bible import EntityNotFoundError

        aldric = make_cast_entry(story_id, "Aldric")
        service.add_cast_entry(story_id, aldric)

        rel = make_relationship(story_id, aldric.cast_id, uuid4())
        with pytest.raises(EntityNotFoundError):
            service.add_relationship(story_id, rel)

    def test_add_relationship_with_cross_story_cast_raises(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Cast entry belonging to a different story must raise EntityNotFoundError."""
        from datetime import UTC, datetime

        from afterworlds.models.enums import StoryMode
        from afterworlds.models.story import Story
        from afterworlds.persistence.crud.story import create_story
        from afterworlds.services.story_bible import EntityNotFoundError

        # Create a second story so the FK constraint is satisfied
        now = datetime(2026, 1, 1, tzinfo=UTC)
        other_story = Story(
            title="Other Story", mode=StoryMode.RPG, created_at=now, updated_at=now
        )
        create_story(service._session, other_story)

        stranger = make_cast_entry(other_story.story_id, "Stranger")
        service.add_cast_entry(other_story.story_id, stranger)

        aldric = make_cast_entry(story_id, "Aldric")
        service.add_cast_entry(story_id, aldric)

        rel = make_relationship(story_id, aldric.cast_id, stranger.cast_id)
        with pytest.raises(EntityNotFoundError):
            service.add_relationship(story_id, rel)


# ---------------------------------------------------------------------------
# Relationship / inactive cast consistency
# ---------------------------------------------------------------------------


class TestRelationshipActivecastConsistency:
    def test_relationship_excluded_when_subject_is_soft_deleted(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Soft-deleting a cast member must remove their relationships from context."""
        aldric = make_cast_entry(story_id, "Aldric")
        serena = make_cast_entry(story_id, "Serena")
        service.add_cast_entry(story_id, aldric)
        service.add_cast_entry(story_id, serena)

        rel = make_relationship(story_id, aldric.cast_id, serena.cast_id)
        service.add_relationship(story_id, rel)

        service.soft_delete("cast_entry", aldric.cast_id)

        ctx = service.get_active_context_window(story_id)
        # Aldric is inactive; the relationship must not appear
        assert ctx.relationship_ledger == ()

    def test_relationship_excluded_when_object_is_soft_deleted(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Soft-deleting the object cast member removes it from context."""
        aldric = make_cast_entry(story_id, "Aldric")
        serena = make_cast_entry(story_id, "Serena")
        service.add_cast_entry(story_id, aldric)
        service.add_cast_entry(story_id, serena)

        rel = make_relationship(story_id, aldric.cast_id, serena.cast_id)
        service.add_relationship(story_id, rel)

        service.soft_delete("cast_entry", serena.cast_id)

        ctx = service.get_active_context_window(story_id)
        assert ctx.relationship_ledger == ()

    def test_relationship_retained_when_both_cast_members_active(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """Relationship is included when both cast members remain active."""
        aldric = make_cast_entry(story_id, "Aldric")
        serena = make_cast_entry(story_id, "Serena")
        service.add_cast_entry(story_id, aldric)
        service.add_cast_entry(story_id, serena)

        rel = make_relationship(story_id, aldric.cast_id, serena.cast_id)
        service.add_relationship(story_id, rel)

        ctx = service.get_active_context_window(story_id)
        assert len(ctx.relationship_ledger) == 1
        assert ctx.relationship_ledger[0].subject_cast_id == aldric.cast_id


# ---------------------------------------------------------------------------
# Static field validation before flush
# ---------------------------------------------------------------------------


class TestStaticFieldValidation:
    def test_invalid_role_value_raises_before_persisting(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """An invalid CastRole value must raise ValueError without persisting."""
        from afterworlds.persistence.orm.story_bible import SBCastEntryORM

        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        with pytest.raises(ValueError):
            service.update_static_field(
                story_id, entry.cast_id, "role", "not_a_valid_role", confirmed=True
            )

        # The ORM row must still hold the original valid role
        row = service._session.get(SBCastEntryORM, str(entry.cast_id))
        assert row is not None
        assert row.static_role == "protagonist"

    def test_valid_role_value_persists_correctly(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        """A valid role update must succeed and return the updated entry."""
        from afterworlds.models.enums import CastRole

        entry = make_cast_entry(story_id)
        service.add_cast_entry(story_id, entry)

        updated = service.update_static_field(
            story_id, entry.cast_id, "role", "antagonist", confirmed=True
        )
        assert updated.role == CastRole.ANTAGONIST


# ---------------------------------------------------------------------------
# get_active_context_window return type
# ---------------------------------------------------------------------------


class TestContextWindowPayload:
    def test_returns_typed_payload_not_raw_result_set(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        ctx = service.get_active_context_window(story_id)
        assert isinstance(ctx, StoryBibleContext)
        assert isinstance(ctx.cast, tuple)
        assert isinstance(ctx.locked_facts, tuple)
        assert isinstance(ctx.forbidden_facts, tuple)
        assert isinstance(ctx.relationship_ledger, tuple)
        assert isinstance(ctx.active_plot_threads, tuple)
        assert isinstance(ctx.events, tuple)

    def test_context_window_excludes_provisional_entries(
        self, service: StoryBibleService, story_id: UUID
    ) -> None:
        proposal = ProvisionalProposal(
            story_id=story_id,
            proposal_type=ProposalType.LOCKED_FACT,
            proposed_value={"fact_text": "Pending fact"},
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        service.stage_proposed_update(story_id, proposal)

        ctx = service.get_active_context_window(story_id)
        fact_texts = [f.fact_text for f in ctx.locked_facts]
        assert "Pending fact" not in fact_texts


# ---------------------------------------------------------------------------
# Generic soft/transient staging validation (#51)
# ---------------------------------------------------------------------------


def _staging_and_history_counts(session: Session) -> tuple[int, int]:
    return (
        session.query(SBProvisionalStagingORM).count(),
        session.query(SBDynamicFieldHistoryORM).count(),
    )


_CAST = "<cast>"
_REL = "<rel>"


class TestGenericStagingValidation:
    @pytest.fixture()
    def targets(self, service: StoryBibleService, story_id: UUID) -> dict[str, str]:
        """Map placeholder -> id of a cast entry / relationship in ``story_id``."""
        aldric = service.add_cast_entry(story_id, make_cast_entry(story_id))
        mira = service.add_cast_entry(story_id, make_cast_entry(story_id, "Mira"))
        rel = service.add_relationship(
            story_id, make_relationship(story_id, aldric.cast_id, mira.cast_id)
        )
        return {_CAST: str(aldric.cast_id), _REL: str(rel.relationship_id)}

    @pytest.fixture()
    def other_targets(self, session: Session) -> dict[str, str]:
        """Map placeholder -> id of a cast entry / relationship in another Story."""
        now = datetime(2026, 1, 1, tzinfo=UTC)
        other = Story(title="Other", mode=StoryMode.RPG, created_at=now, updated_at=now)
        create_story(session, other)
        svc = StoryBibleService(session)
        a = svc.add_cast_entry(other.story_id, make_cast_entry(other.story_id))
        b = svc.add_cast_entry(other.story_id, make_cast_entry(other.story_id, "B"))
        rel = svc.add_relationship(
            other.story_id, make_relationship(other.story_id, a.cast_id, b.cast_id)
        )
        return {_CAST: str(a.cast_id), _REL: str(rel.relationship_id)}

    @staticmethod
    def _proposal(
        story_id: UUID,
        entity_type: str | None,
        entity_id: str | None,
        value: dict[str, object],
        ptype: ProposalType = ProposalType.SOFT_FACT,
    ) -> ProvisionalProposal:
        return ProvisionalProposal(
            story_id=story_id,
            proposal_type=ptype,
            target_entity_type=entity_type,
            target_entity_id=entity_id,
            proposed_value=value,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    @pytest.mark.parametrize(
        ("entity_type", "entity_id", "value", "exc", "match"),
        [
            # Missing / unsupported target types
            (None, _CAST, {"notes": "x"}, ValueError, "Unsupported"),
            ("world", _CAST, {"notes": "x"}, ValueError, "Unsupported"),
            ("CAST_ENTRY", _CAST, {"notes": "x"}, ValueError, "Unsupported"),
            # Missing / malformed IDs
            ("cast_entry", None, {"notes": "x"}, ValueError, "valid UUID"),
            ("cast_entry", "", {"notes": "x"}, ValueError, "valid UUID"),
            ("cast_entry", "not-a-uuid", {"notes": "x"}, ValueError, "valid UUID"),
            # Nonexistent / wrong-type targets
            (
                "cast_entry",
                "00000000-0000-0000-0000-000000000000",
                {"notes": "x"},
                EntityNotFoundError,
                "not found",
            ),
            (
                "relationship_ledger",
                _CAST,
                {"current_status_description": "x"},
                EntityNotFoundError,
                "not found",
            ),
            ("cast_entry", _REL, {"notes": "x"}, EntityNotFoundError, "not found"),
            # Empty payloads
            ("cast_entry", _CAST, {}, ValueError, "nonempty"),
            ("relationship_ledger", _REL, {}, ValueError, "nonempty"),
            # Non-writable fields (including one bad field among good ones)
            ("cast_entry", _CAST, {"name": "X"}, ValueError, "not writable"),
            ("cast_entry", _CAST, {"fact": "x"}, ValueError, "not writable"),
            (
                "cast_entry",
                _CAST,
                {"notes": "ok", "role": "villain"},
                ValueError,
                "not writable",
            ),
            (
                "cast_entry",
                _CAST,
                {"current_status_description": "x"},
                ValueError,
                "not writable",
            ),
            (
                "relationship_ledger",
                _REL,
                {"current_location": "x"},
                ValueError,
                "not writable",
            ),
            # Wrong value types (including nested, non-flat values)
            ("cast_entry", _CAST, {"is_alive": "no"}, ValueError, "bool"),
            ("cast_entry", _CAST, {"is_alive": 0}, ValueError, "bool"),
            ("cast_entry", _CAST, {"is_alive": None}, ValueError, "bool"),
            ("cast_entry", _CAST, {"notes": None}, ValueError, "str"),
            ("cast_entry", _CAST, {"notes": False}, ValueError, "str"),
            ("cast_entry", _CAST, {"notes": {"a": "b"}}, ValueError, "str"),
            ("cast_entry", _CAST, {"current_location": ["x"]}, ValueError, "str"),
            (
                "relationship_ledger",
                _REL,
                {"current_status_description": 3},
                ValueError,
                "str",
            ),
        ],
    )
    @pytest.mark.parametrize(
        "ptype", [ProposalType.SOFT_FACT, ProposalType.TRANSIENT_STATE]
    )
    def test_invalid_proposal_rejected_before_staging(
        self,
        service: StoryBibleService,
        session: Session,
        story_id: UUID,
        targets: dict[str, str],
        entity_type: str | None,
        entity_id: str | None,
        value: dict[str, object],
        exc: type[Exception],
        match: str,
        ptype: ProposalType,
    ) -> None:
        resolved = targets.get(entity_id or "", entity_id)
        canon_before = service.get_active_context_window(story_id)
        before = _staging_and_history_counts(session)

        with pytest.raises(exc, match=match):
            service.stage_proposed_update(
                story_id, self._proposal(story_id, entity_type, resolved, value, ptype)
            )

        assert before[0] == 0
        assert _staging_and_history_counts(session) == before
        assert service.get_active_context_window(story_id) == canon_before

    @pytest.mark.parametrize(
        ("entity_type", "entity_id", "value"),
        [
            ("cast_entry", _CAST, {"notes": "x"}),
            ("relationship_ledger", _REL, {"current_status_description": "x"}),
        ],
    )
    def test_other_story_target_rejected(
        self,
        service: StoryBibleService,
        session: Session,
        story_id: UUID,
        targets: dict[str, str],
        other_targets: dict[str, str],
        entity_type: str,
        entity_id: str,
        value: dict[str, object],
    ) -> None:
        canon_before = service.get_active_context_window(story_id)
        before = _staging_and_history_counts(session)

        with pytest.raises(EntityNotFoundError, match="not found for story"):
            service.stage_proposed_update(
                story_id,
                self._proposal(story_id, entity_type, other_targets[entity_id], value),
            )

        assert _staging_and_history_counts(session) == before
        assert service.get_active_context_window(story_id) == canon_before
        # The same target kind in the supplied Story is accepted.
        staged = service.stage_proposed_update(
            story_id, self._proposal(story_id, entity_type, targets[entity_id], value)
        )
        assert staged.status == ProposalStatus.PENDING

    @pytest.mark.parametrize(
        "value",
        [
            {"is_alive": False},
            {"current_location": ""},
            {
                "current_location": "The Iron Tower",
                "current_status": "",
                "is_alive": False,
                "notes": "wounded",
            },
        ],
    )
    @pytest.mark.parametrize(
        "ptype", [ProposalType.SOFT_FACT, ProposalType.TRANSIENT_STATE]
    )
    def test_valid_cast_proposal_stages_and_ratifies_without_canon(
        self,
        service: StoryBibleService,
        session: Session,
        story_id: UUID,
        targets: dict[str, str],
        value: dict[str, object],
        ptype: ProposalType,
    ) -> None:
        cast_id = targets[_CAST]
        canon_before = service.get_active_context_window(story_id)
        _, history_before = _staging_and_history_counts(session)

        staged = service.stage_proposed_update(
            story_id, self._proposal(story_id, "cast_entry", cast_id, value, ptype)
        )
        assert staged.status == ProposalStatus.PENDING
        assert staged.requires_confirmation is False
        assert staged.target_entity_type == "cast_entry"
        assert staged.target_entity_id == cast_id
        assert staged.proposed_value == value

        ratified = service.ratify_update(staged.proposal_id)
        assert ratified.status == ProposalStatus.RATIFIED
        assert service.get_active_context_window(story_id) == canon_before
        assert _staging_and_history_counts(session) == (1, history_before)

    @pytest.mark.parametrize("description", ["strained", ""])
    @pytest.mark.parametrize(
        "ptype", [ProposalType.SOFT_FACT, ProposalType.TRANSIENT_STATE]
    )
    def test_valid_relationship_proposal_stages_and_ratifies_without_canon(
        self,
        service: StoryBibleService,
        session: Session,
        story_id: UUID,
        targets: dict[str, str],
        description: str,
        ptype: ProposalType,
    ) -> None:
        rel_id = targets[_REL]
        value: dict[str, object] = {"current_status_description": description}
        canon_before = service.get_active_context_window(story_id)
        _, history_before = _staging_and_history_counts(session)

        staged = service.stage_proposed_update(
            story_id,
            self._proposal(story_id, "relationship_ledger", rel_id, value, ptype),
        )
        assert staged.status == ProposalStatus.PENDING
        assert staged.target_entity_type == "relationship_ledger"
        assert staged.target_entity_id == rel_id
        assert staged.proposed_value == value

        ratified = service.ratify_update(staged.proposal_id)
        assert ratified.status == ProposalStatus.RATIFIED
        canon_after = service.get_active_context_window(story_id)
        assert canon_after == canon_before
        assert [
            r.current_status_description for r in canon_after.relationship_ledger
        ] == ["Trusted comrade"]
        assert _staging_and_history_counts(session) == (1, history_before)

    def test_target_id_stored_in_canonical_form(
        self, service: StoryBibleService, story_id: UUID, targets: dict[str, str]
    ) -> None:
        cast_id = targets[_CAST]
        staged = service.stage_proposed_update(
            story_id,
            self._proposal(story_id, "cast_entry", cast_id.upper(), {"notes": "x"}),
        )
        assert staged.target_entity_id == cast_id
