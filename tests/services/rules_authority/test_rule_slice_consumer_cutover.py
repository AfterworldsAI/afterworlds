"""The production rule-slice consumer reads exact typed authority — #137 contract 6.

Final CRD Issue 5d cutover, blocker 1. Before it, ``ContextBuilderService``
forwarded only the package, the legacy subsystem/entity selectors and the
draft flag to ``RulesPackageService.get_active_rule_slice``, which read legacy
chunks and ``MechanicalEntity`` rows. Record, component and whole-package
selection and the recorded binding were dropped, the slice carried no binding,
and the 10 October runtime smoke showed valid typed requests (1 record /
1,835 records / ``STALE``) coming back as empty legacy slices.

These tests drive the real production consumer — ``ContextBuilderService``
with a real ``RulesPackageService``, and the app's ``_PerTurnContextBuilder``
wiring — over an activated projection reached through the genuine
publish/activate path (see ``conftest.py``), and check each slice against
``RulesAuthorityService`` itself for the same request.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import select

from afterworlds.api.pipeline_wiring import _PerTurnContextBuilder
from afterworlds.models.context import StablePrefix
from afterworlds.models.enums import IntentType, OverrideOperationEnum, StoryMode
from afterworlds.models.intent_classification import IntentClassificationResult
from afterworlds.models.rules_package import (
    ActiveRuleSlice,
    RuleSliceRequest,
    RulesPackageBinding,
)
from afterworlds.persistence.database import create_session_factory
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.quarantine import (
    QUARANTINED_PACKAGE_UUIDS,
    QUARANTINED_PROJECTION_UUIDS,
    QuarantinedAuthorityError,
)
from afterworlds.services.context_builder import (
    ContextBuilderService,
    NullRetrievalMemoryProvider,
)
from afterworlds.services.rules_authority import (
    AuthorityOutcome,
    RulesAuthorityService,
    package_slug,
)
from afterworlds.services.rules_package import (
    RuleSliceResolutionError,
    RulesPackageService,
)
from afterworlds.services.story_bible import StoryBibleService
from tests.services.rules_authority.conftest import (
    CHECK_KEY,
    CREATURE_KEY,
    DESCRIPTOR_FACT_KEY,
    DESCRIPTOR_FACT_TARGET,
    DESCRIPTOR_KEY,
    DISABLE_PAYLOAD,
    NOW,
    PACKAGE_NAME,
    PROSE_TEXT,
    RIVAL_PACKAGE_UUID,
    SPELL_KEY,
    RuntimeFixture,
    author_override,
)

_STORY = UUID("00000000-0000-4000-8000-0000000005d0")


class _NoSummary:
    def get_current_summary(self, story_id: UUID) -> None:
        return None


class _NoTurns:
    def get_recent_turns(
        self, story_id: UUID, limit: int, *, exclude_ooc: bool = True
    ) -> list[object]:
        return []


def _intent() -> IntentClassificationResult:
    return IntentClassificationResult(
        intent_type=IntentType.IN_CHARACTER_ACTION,
        confidence=0.95,
        raw_input="I read the scroll.",
        ambiguous=False,
        secondary_intent=None,
    )


def _prefix(runtime: RuntimeFixture, request: RuleSliceRequest) -> StablePrefix:
    """The production consumer: a real Context Builder over a real service."""
    builder = ContextBuilderService(
        story_bible_service=StoryBibleService(runtime.session),
        rolling_summary_service=_NoSummary(),
        recent_turns_provider=_NoTurns(),  # type: ignore[arg-type]
        retrieval_memory=NullRetrievalMemoryProvider(),
        rules_package_service=RulesPackageService(runtime.session, now=NOW),
    )
    return builder.build_stable_prefix(
        _STORY, StoryMode.RPG, _intent(), rule_slice_request=request
    )


def _slice(runtime: RuntimeFixture, request: RuleSliceRequest) -> ActiveRuleSlice:
    sliced = _prefix(runtime, request).rules_package_slice
    assert sliced is not None
    return sliced


def _typed(runtime: RuntimeFixture, request: RuleSliceRequest):  # type: ignore[no-untyped-def]
    """The same request straight through the typed authority service."""
    service = RulesAuthorityService(runtime.session, now=NOW)
    return service.rule_slice(request), service.gamemaster_view(request)


def _assert_consistent(runtime: RuntimeFixture, request: RuleSliceRequest) -> None:
    """Supplied-request consistency: the consumer and the service agree."""
    sliced = _slice(runtime, request)
    typed, gm = _typed(runtime, request)
    assert typed.outcome is AuthorityOutcome.RESOLVED
    assert gm.gamemaster_view is not None
    assert sliced.request is request
    assert sliced.binding == typed.binding == gm.binding
    assert sliced.components == tuple(
        (c.record_key, c.component_key) for c in gm.gamemaster_view.components
    )
    assert {r for r, _ in sliced.components} <= {
        r.semantic_key for r in typed.slice.records
    }


# ---------------------------------------------------------------------------
# Selection keeps its meaning
# ---------------------------------------------------------------------------


def test_a_record_selector_reads_that_record_and_names_the_binding(
    runtime: RuntimeFixture,
) -> None:
    request = RuleSliceRequest(
        package_id=runtime.package_uuid, record_selectors=(SPELL_KEY,)
    )
    sliced = _slice(runtime, request)
    binding = sliced.binding
    assert binding.package_uuid == runtime.package_uuid
    assert binding.release_version == runtime.release_version
    assert binding.mechanical_projection_uuid == runtime.projection_uuid
    assert sliced.components
    assert {record for record, _ in sliced.components} == {SPELL_KEY}
    # The rendered authority states the exact binding and the exact source prose.
    assert str(binding.override_set_uuid) in sliced.authority_text
    assert str(binding.mechanical_projection_uuid) in sliced.authority_text
    assert PROSE_TEXT in sliced.authority_text
    assert DESCRIPTOR_FACT_KEY in sliced.authority_text
    _assert_consistent(runtime, request)


def test_a_component_selector_narrows_to_exactly_that_component(
    runtime: RuntimeFixture,
) -> None:
    request = RuleSliceRequest(
        package_id=runtime.package_uuid,
        component_selectors=((SPELL_KEY, DESCRIPTOR_KEY),),
    )
    sliced = _slice(runtime, request)
    assert sliced.components == ((SPELL_KEY, DESCRIPTOR_KEY),)
    assert PROSE_TEXT not in sliced.authority_text
    _assert_consistent(runtime, request)


def test_whole_package_reads_every_record_explicitly(runtime: RuntimeFixture) -> None:
    request = RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
    sliced = _slice(runtime, request)
    records = {record for record, _ in sliced.components}
    assert {SPELL_KEY, CREATURE_KEY} <= records
    assert (CREATURE_KEY, CHECK_KEY) in sliced.components
    _assert_consistent(runtime, request)


def test_a_slug_request_binds_exactly_as_the_uuid_request(
    runtime: RuntimeFixture,
) -> None:
    rival = runtime.session.execute(
        select(RulesPackageORM).where(
            RulesPackageORM.rules_package_id == RIVAL_PACKAGE_UUID
        )
    ).scalar_one()
    rival.name = "Unrelated corpus"
    runtime.session.flush()
    by_slug = _slice(
        runtime,
        RuleSliceRequest(package_slug=package_slug(PACKAGE_NAME), whole_package=True),
    )
    by_uuid = _slice(
        runtime, RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
    )
    assert by_slug.binding == by_uuid.binding
    assert by_slug.components == by_uuid.components
    assert by_slug.authority_text == by_uuid.authority_text


def test_the_rendering_is_deterministic_for_the_cached_prefix(
    runtime: RuntimeFixture,
) -> None:
    request = RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
    first = _prefix(runtime, request)
    second = _prefix(runtime, request)
    assert first.render() == second.render()
    assert first.rules_package_slice is not None
    assert first.rules_package_slice.authority_text in first.render()


# ---------------------------------------------------------------------------
# Typed fail-closed refusals through the consumer
# ---------------------------------------------------------------------------


def test_a_stale_recorded_binding_is_refused_not_re_resolved(
    runtime: RuntimeFixture,
) -> None:
    """A binding recorded before an override changed is ``STALE`` at runtime."""
    recorded = _slice(
        runtime,
        RuleSliceRequest(
            package_id=runtime.package_uuid, record_selectors=(SPELL_KEY,)
        ),
    ).binding
    author_override(
        runtime.session,
        override_id="cutover-disable-descriptor-fact",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    request = RuleSliceRequest(
        package_id=runtime.package_uuid,
        record_selectors=(SPELL_KEY,),
        recorded_binding=recorded,
    )
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        _slice(runtime, request)
    assert excinfo.value.outcome is AuthorityOutcome.STALE
    # The typed service gives the same answer for the same request.
    typed, _ = _typed(runtime, request)
    assert typed.outcome is AuthorityOutcome.STALE
    # And without the recorded binding the current authority still reads.
    current = _slice(
        runtime,
        RuleSliceRequest(
            package_id=runtime.package_uuid, record_selectors=(SPELL_KEY,)
        ),
    )
    assert current.binding.override_set_uuid != recorded.override_set_uuid


def test_a_current_recorded_binding_is_accepted(runtime: RuntimeFixture) -> None:
    recorded = _slice(
        runtime, RuleSliceRequest(package_id=runtime.package_uuid, whole_package=True)
    ).binding
    again = _slice(
        runtime,
        RuleSliceRequest(
            package_id=runtime.package_uuid,
            whole_package=True,
            recorded_binding=recorded,
        ),
    )
    assert again.binding == recorded


def test_a_selector_naming_nothing_in_the_projection_is_refused(
    runtime: RuntimeFixture,
) -> None:
    """Never widened and never an empty slice."""
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        _slice(
            runtime,
            RuleSliceRequest(
                package_id=runtime.package_uuid, record_selectors=("spell:absent",)
            ),
        )
    assert excinfo.value.outcome is AuthorityOutcome.INVALID_REFERENCE


def test_an_unpublished_package_is_refused(runtime: RuntimeFixture) -> None:
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        _slice(
            runtime,
            RuleSliceRequest(package_id=runtime.bare_package_uuid, whole_package=True),
        )
    assert excinfo.value.outcome is AuthorityOutcome.UNPUBLISHED


def test_an_ambiguous_slug_is_refused(runtime: RuntimeFixture) -> None:
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        _slice(
            runtime,
            RuleSliceRequest(
                package_slug=package_slug(PACKAGE_NAME), whole_package=True
            ),
        )
    assert excinfo.value.outcome is AuthorityOutcome.AMBIGUOUS


def test_a_retired_identity_is_refused_by_the_quarantine(
    runtime: RuntimeFixture,
) -> None:
    (retired,) = QUARANTINED_PACKAGE_UUIDS
    with pytest.raises(QuarantinedAuthorityError):
        _slice(runtime, RuleSliceRequest(package_id=UUID(retired), whole_package=True))
    # A recorded binding naming the retired projection is refused the same way,
    # even beside a current package reference.
    (retired_projection,) = QUARANTINED_PROJECTION_UUIDS
    smuggled = RulesPackageBinding(
        package_uuid=runtime.package_uuid,
        release_version=runtime.release_version,
        mechanical_projection_uuid=UUID(retired_projection),
        override_set_uuid=UUID("00000000-0000-5000-8000-000000000000"),
    )
    with pytest.raises(QuarantinedAuthorityError):
        _slice(
            runtime,
            RuleSliceRequest(
                package_id=runtime.package_uuid,
                whole_package=True,
                recorded_binding=smuggled,
            ),
        )


def test_an_empty_selector_cannot_reach_the_consumer(runtime: RuntimeFixture) -> None:
    with pytest.raises(ValueError, match="selects nothing"):
        RuleSliceRequest(package_id=runtime.package_uuid)


# ---------------------------------------------------------------------------
# The app's production wiring
# ---------------------------------------------------------------------------


def test_the_app_wiring_commits_the_binding_it_names_so_it_replays(
    runtime: RuntimeFixture,
) -> None:
    """``_PerTurnContextBuilder`` keeps the slice's override-set version.

    Binding resolution retains the version in the context session and the
    caller owns the commit (ADR-005d Decision 9). With a typed override in
    force — so the version is not the shared empty one — a fresh session must
    replay the exact binding the stable prefix named.
    """
    author_override(
        runtime.session,
        override_id="cutover-disable-descriptor-fact",
        target=DESCRIPTOR_FACT_TARGET,
        operation=OverrideOperationEnum.DISABLE,
        payload=DISABLE_PAYLOAD,
    )
    runtime.session.commit()

    wiring = _PerTurnContextBuilder(
        create_session_factory(runtime.engine), NullRetrievalMemoryProvider()
    )
    request = RuleSliceRequest(
        package_id=runtime.package_uuid, record_selectors=(SPELL_KEY,)
    )
    assembled = wiring.assemble(
        _STORY, StoryMode.RPG, "I read the scroll.", _intent(), request
    )
    sliced = assembled.stable_prefix.rules_package_slice
    assert sliced is not None
    assert sliced.request is request
    assert DESCRIPTOR_FACT_KEY not in sliced.authority_text

    with create_session_factory(runtime.engine)() as fresh:
        replayed = RulesAuthorityService(fresh, now=NOW).replay(sliced.binding)
    assert replayed.binding == sliced.binding
    assert any(
        o.override_id == "cutover-disable-descriptor-fact" and o.applied
        for o in replayed.applied_overrides
    )


def test_the_app_wiring_refuses_rather_than_assembling_without_rules(
    runtime: RuntimeFixture,
) -> None:
    runtime.session.commit()
    wiring = _PerTurnContextBuilder(
        create_session_factory(runtime.engine), NullRetrievalMemoryProvider()
    )
    stale = RulesPackageBinding(
        package_uuid=runtime.package_uuid,
        release_version=runtime.release_version,
        mechanical_projection_uuid=runtime.projection_uuid,
        override_set_uuid=UUID("00000000-0000-5000-8000-000000000000"),
    )
    with pytest.raises(RuleSliceResolutionError) as excinfo:
        wiring.assemble(
            _STORY,
            StoryMode.RPG,
            "I read the scroll.",
            _intent(),
            RuleSliceRequest(
                package_id=runtime.package_uuid,
                whole_package=True,
                recorded_binding=stale,
            ),
        )
    assert excinfo.value.outcome is AuthorityOutcome.STALE
