"""Catalogue membership reads only ``catalogue_member`` edges -- CRD Issue 5d.

Owner Decision 2026-09-23 made three explicit catalogues reachable from their
sections. It did not change what ``scoped_within`` means. These pin that a
valid, pre-existing containment edge is still published, reconstructed and read
exactly as before: naming the container reaches nothing else, and the
contained record needs no prose binding for the projection to stay readable.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest

from afterworlds.ingestion.mechanical.persistence import reconstruct_candidate
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RelationshipDraft,
    RelationshipKind,
    RepresentationDraft,
    relationship_target_key,
)
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.services.rules_authority.application import apply_override_set
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import EffectiveOverrideSet
from afterworlds.services.rules_authority.service import (
    RulesAuthorityService,
    _select,
)
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)
from tests.ingestion.mechanical import conftest as mechanical
from tests.services.rules_authority import conftest as runtime_conftest
from tests.services.rules_authority.conftest import (
    CREATURE_KEY,
    NOW,
    SPELL_KEY,
    SPELL_SPAN,
    RuntimeFixture,
    author_override,
)

CONTAINED = RelationshipDraft(CREATURE_KEY, SPELL_KEY, RelationshipKind.SCOPED_WITHIN)


@pytest.fixture()
def scoped_runtime(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Iterator[RuntimeFixture]:
    """The published runtime, its projection carrying one ``scoped_within`` edge."""
    base = runtime_conftest._representation

    def with_containment(prefix: str = "") -> RepresentationDraft:
        rep = base(prefix)
        return dataclasses.replace(
            rep,
            relationships=(CONTAINED,),
            provenance=(
                *rep.provenance,
                ProvenanceClaim(
                    ProvenanceTargetKind.RELATIONSHIP,
                    relationship_target_key(CONTAINED),
                    SPELL_SPAN,
                    ProvenanceRole.CONTEXTUAL,
                ),
            ),
        )

    monkeypatch.setattr(runtime_conftest, "_representation", with_containment)
    yield request.getfixturevalue("runtime")


def _request(runtime: RuntimeFixture, *records: str) -> RuleSliceRequest:
    return RuleSliceRequest(package_id=runtime.package_uuid, record_selectors=records)


def test_published_containment_is_read_unexpanded(
    scoped_runtime: RuntimeFixture,
) -> None:
    service = RulesAuthorityService(scoped_runtime.session, now=NOW)
    _, authority = service._resolve_authority(_request(scoped_runtime, SPELL_KEY))
    assert authority is not None
    assert authority.members == ()
    rebuilt = reconstruct_candidate(
        scoped_runtime.session, str(scoped_runtime.projection_uuid)
    )
    assert rebuilt.representation.relationships == (CONTAINED,)

    sliced = service.rule_slice(_request(scoped_runtime, SPELL_KEY))
    assert sliced.outcome is AuthorityOutcome.RESOLVED, sliced.detail
    assert sliced.slice is not None
    assert [r.semantic_key for r in sliced.slice.records] == [SPELL_KEY]
    gm = service.gamemaster_view(_request(scoped_runtime, SPELL_KEY))
    assert gm.gamemaster_view is not None
    assert {c.record_key for c in gm.gamemaster_view.components} == {SPELL_KEY}

    both = service.rule_slice(_request(scoped_runtime, SPELL_KEY, CREATURE_KEY))
    assert both.slice is not None
    assert [r.semantic_key for r in both.slice.records] == sorted(
        [SPELL_KEY, CREATURE_KEY]
    )


def test_containment_survives_suppression_and_replay(
    scoped_runtime: RuntimeFixture,
) -> None:
    author_override(
        scoped_runtime.session,
        override_id="disable-creature",
        target=MechanicalTarget(
            kind=MechanicalTargetKind.RECORD, record_key=CREATURE_KEY
        ),
        operation=OverrideOperationEnum.DISABLE,
        payload={"patch": "disable"},
    )
    replays = [
        RulesAuthorityService(scoped_runtime.session, now=NOW).rule_slice(
            _request(scoped_runtime, SPELL_KEY)
        )
        for _ in range(2)
    ]
    for sliced in replays:
        assert sliced.outcome is AuthorityOutcome.RESOLVED, sliced.detail
        assert sliced.slice is not None
        assert [r.semantic_key for r in sliced.slice.records] == [SPELL_KEY]
    assert replays[0].slice == replays[1].slice
    refused = RulesAuthorityService(scoped_runtime.session, now=NOW).rule_slice(
        _request(scoped_runtime, CREATURE_KEY)
    )
    assert refused.outcome is AuthorityOutcome.INVALID_REFERENCE


def test_a_prose_less_contained_record_stays_readable() -> None:
    """The shared fixture's creature binds no prose and is scoped within a spell."""
    rep = mechanical.build_representation()
    assert rep.relationships == (mechanical.SCOPED_WITHIN,)
    assert CREATURE_KEY not in {b.record_key for b in rep.prose_bindings}
    ledger = mechanical.build_ledger()
    release = dataclasses.replace(
        mechanical.RELEASE_BINDING,
        package_uuid=str(uuid5(NAMESPACE_URL, "scoped-within-package")),
    )
    candidate = mechanical.candidate_of(release, ledger, rep)
    empty = EffectiveOverrideSet(
        candidate.binding.package_uuid, candidate.binding.release_version, ()
    )
    authority = apply_override_set(
        candidate,
        empty,
        RulesPackageBinding(
            package_uuid=UUID(candidate.binding.package_uuid),
            release_version=candidate.binding.release_version,
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "scoped-within"),
            override_set_uuid=UUID(empty.override_set_uuid),
        ),
        leaf_order={s.leaf_id: i for i, s in enumerate(ledger.spans)},
    )
    assert authority.members == ()
    request = RuleSliceRequest(
        package_id=UUID(candidate.binding.package_uuid),
        record_selectors=(mechanical.SPELL_KEY,),
    )
    selected, missing = _select(authority, request)
    assert missing == set()
    assert [r.semantic_key for r in selected] == [mechanical.SPELL_KEY]
