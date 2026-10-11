"""The accepted replacement, published and resolved at runtime — CRD Issue 5d.

Obligation (5) of ``docs/architecture/issue-5c-5d-clean-restart.md`` §2.5: the
whole Owner-accepted authority for the replacement release
(``1299484e-c72d-509b-bd8d-d0169ee1f8d2`` / ``5.2.1-corpus.8781d4e0-a3b``)
travels the production lifecycle over the 5c state ``finalize_source_release``
actually published: persist the draft, publish through
:func:`publish_from_committed_oracle` (the oracle resolved from the packaged
committed directory, never supplied), activate, and resolve through
:class:`RulesAuthorityService`.

Nothing here supplies authority. The draft is
``candidate_from_accepted_inputs`` over the committed artifact, and the gate
judges it against that same committed artifact. The negative control is the
same full-corpus candidate with three real heading leaves removed from the
review units that alone accounted for them, so incompleteness is its only
defect.

Every store is a private copy of ``source_release_db`` (the shared published 5c
release), so nothing here can activate anything another module reads. Each
lifecycle stage runs once in a module fixture that records what it observed;
the tests assert those observations, so they do not depend on file order.
Committed visibility is observed through a separately opened engine and
session right after publication returns, including resolution by the source
package's human-facing slug.

The citation section reads the published projection's citations through
:meth:`RulesAuthorityService.citation_view`: each one whose citing text is
bound as no component's prose reads at runtime with no override, and is refused
once its original citing source is disabled or replaced (ADR-005d Decision 7).

Cost, measured: about 50 s to gate and publish the accepted projection, about
8 s per runtime reconstruction (a citation read reconstructs twice), about 14 s
to load the committed oracles. A full-corpus republication (another ~50 s) is
deliberately not repeated here: the publication seam did not change, and
idempotent reuse and re-proof refusal of tampered content are covered by
``test_publication.py`` on bounded fixtures.
"""

from __future__ import annotations

import dataclasses
import hashlib
import shutil
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.gate import GateFailureCategory
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    AcceptedInputs,
    candidate_from_accepted_inputs,
    committed_inputs_for,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    record_persisted_state_digest,
)
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    identify_projection,
)
from afterworlds.ingestion.mechanical.publication import (
    ActiveProjection,
    PublicationOutcome,
    PublicationResult,
    publish_from_committed_oracle,
    resolve_active_projection,
)
from afterworlds.ingestion.mechanical.reference_resolution import AlternativeSelection
from afterworlds.ingestion.mechanical.representation import (
    ProvenanceTargetKind,
    ReferenceDraft,
    reference_target_key,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.mechanical import (
    MechanicalActiveProjectionORM,
    MechanicalProjectionORM,
)
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.services.rules_authority import (
    EMPTY_OVERRIDE_SET_UUID,
    AuthorityOutcome,
    AuthorityResult,
    BindingResolution,
    PackageResolution,
    RulesAuthorityService,
    collect_current_override_state,
    resolve_package_reference,
)
from afterworlds.services.rules_authority.binding import package_slug
from afterworlds.services.rules_authority.override_set import (
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
)
from afterworlds.services.rules_authority.service import _citation_in_effect
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)

NOW = "2026-10-09T00:00:00Z"
PACKAGE = "1299484e-c72d-509b-bd8d-d0169ee1f8d2"
RELEASE = "5.2.1-corpus.8781d4e0-a3b"
#: The effective projection the accepted authority derives: the CRD Issue 2b G1
#: successor recorded 2026-10-11 (the restart's ``1f0db408-…`` was its
#: predecessor's, superseded by digest).
PROJECTION = "efab27a9-5d44-52ba-ad74-47940d5fd717"
ORACLE_FILE = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-8781d4e0-a3b-g1.json"
ORACLE_SHA256 = "2ccbaeba6de75d9787fbdd407e42dc2425fa20d4d26bcc298b681b550bd11258"
ACCEPTED_RECORDS = 1847

#: One real accepted record, read back with its exact provenance.
PROBE_RECORD = "glossary.blinded"

#: How many real leaves the negative control leaves unaccounted for. Small on
#: purpose: the point is that a full corpus missing *anything* is refused, and
#: refused per leaf.
DROPPED_LEAVES = 3


@pytest.fixture(scope="module")
def accepted() -> AcceptedInputs:
    """The committed accepted authority, resolved the way production resolves it."""
    inputs = committed_inputs_for(PACKAGE, RELEASE)
    assert inputs is not None
    return inputs


def _private_store(
    tmp_path_factory: pytest.TempPathFactory, source_release_db: Path, name: str
) -> Iterator[tuple[Session, Path]]:
    """A private copy of the published 5c release, so nothing here leaks."""
    path = tmp_path_factory.mktemp(name) / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as session:
        yield session, path
    engine.dispose()


def _persist(session: Session, candidate: ProjectionCandidate) -> str:
    identified = identify_projection(candidate)
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.commit()
    return identified.projection_uuid


def _whole_package() -> RuleSliceRequest:
    return RuleSliceRequest(package_id=UUID(PACKAGE), whole_package=True)


# ---------------------------------------------------------------------------
# The lifecycle, observed once
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Before:
    """What runtime said before anything was published."""

    package: PackageResolution
    active: ActiveProjection
    binding: BindingResolution
    slice: AuthorityResult


@dataclass(frozen=True)
class Fresh:
    """Runtime as an independently opened session saw it after publication.

    Opened on its own engine after ``publish_from_committed_oracle`` returned,
    so everything here is state the publication committed, not state still
    pending in the publishing session.
    """

    active: ActiveProjection
    binding: BindingResolution
    slice: AuthorityResult
    package_name: str
    slug: str
    slug_binding: BindingResolution
    slug_slice: AuthorityResult


@dataclass(frozen=True)
class Published:
    """Store A after the accepted projection went through the public path."""

    session: Session
    before: Before
    projection_uuid: str
    result: PublicationResult
    fresh: Fresh


def _observe_fresh(path: Path) -> Fresh:
    engine = create_engine(f"sqlite:///{path}")
    try:
        with create_session_factory(engine)() as session:
            service = RulesAuthorityService(session, now=NOW)
            name = session.execute(
                select(RulesPackageORM.name).where(
                    RulesPackageORM.rules_package_id == PACKAGE
                )
            ).scalar_one()
            slug = package_slug(name)
            probe = (PROBE_RECORD,)
            fresh = Fresh(
                active=resolve_active_projection(session, PACKAGE),
                binding=service.resolve(package_uuid=UUID(PACKAGE)),
                slice=service.rule_slice(
                    RuleSliceRequest(package_id=UUID(PACKAGE), record_selectors=probe)
                ),
                package_name=name,
                slug=slug,
                slug_binding=service.resolve(package_reference=slug),
                slug_slice=service.rule_slice(
                    RuleSliceRequest(package_slug=slug, record_selectors=probe)
                ),
            )
            # Resolution retains the override-set version; this read session
            # leaves the private store exactly as publication committed it.
            session.rollback()
            return fresh
    finally:
        engine.dispose()


@pytest.fixture(scope="module")
def published(
    tmp_path_factory: pytest.TempPathFactory,
    source_release_db: Path,
    accepted: AcceptedInputs,
) -> Iterator[Published]:
    for session, path in _private_store(
        tmp_path_factory, source_release_db, "accepted"
    ):
        service = RulesAuthorityService(session, now=NOW)
        before = Before(
            package=resolve_package_reference(session, PACKAGE),
            active=resolve_active_projection(session, PACKAGE),
            binding=service.resolve(package_uuid=UUID(PACKAGE)),
            slice=service.rule_slice(_whole_package()),
        )
        session.rollback()
        projection_uuid = _persist(session, candidate_from_accepted_inputs(accepted))
        result = publish_from_committed_oracle(session, projection_uuid, now=NOW)
        fresh = _observe_fresh(path)
        yield Published(session, before, projection_uuid, result, fresh)


def test_before_publication_runtime_answers_unpublished_not_empty(
    published: Published,
) -> None:
    """The package resolves; its mechanical authority is typed UNPUBLISHED."""
    before = published.before
    assert before.package.outcome is AuthorityOutcome.RESOLVED
    assert before.package.package_uuid == UUID(PACKAGE)
    assert before.active.outcome is PublicationOutcome.UNPUBLISHED
    assert before.active.projection_uuid is None
    assert before.binding.outcome is AuthorityOutcome.UNPUBLISHED
    assert before.binding.binding is None
    assert "no active mechanical projection" in before.binding.detail
    assert before.slice.outcome is AuthorityOutcome.UNPUBLISHED
    assert before.slice.slice is None


def test_the_public_path_publishes_exactly_the_accepted_projection(
    published: Published, accepted: AcceptedInputs
) -> None:
    """The committed oracle judges the draft and the gate passes outright."""
    result = published.result
    assert result.outcome is PublicationOutcome.PUBLISHED, (
        result.gate.categories() if result.gate else None
    )
    assert published.projection_uuid == PROJECTION
    assert result.gate is not None and result.gate.passed
    assert result.gate.failures == ()
    assert result.gate.expected_projection_uuid == PROJECTION
    assert result.gate.oracle_identity == oracle_identity(accepted.oracle)
    header = published.session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == PROJECTION
        )
    ).scalar_one()
    assert header.publication_status == "published"
    assert header.package_uuid == PACKAGE
    assert header.release_version == RELEASE
    assert header.oracle_identity == oracle_identity(accepted.oracle)
    assert header.evidence_report_hash == result.evidence_report_hash


def _expected_binding() -> RulesPackageBinding:
    return RulesPackageBinding(
        package_uuid=UUID(PACKAGE),
        release_version=RELEASE,
        mechanical_projection_uuid=UUID(PROJECTION),
        override_set_uuid=UUID(EMPTY_OVERRIDE_SET_UUID),
    )


def test_runtime_resolves_the_active_binding_with_empty_overrides(
    published: Published,
) -> None:
    session = published.session
    active = resolve_active_projection(session, PACKAGE)
    assert active.outcome is PublicationOutcome.PUBLISHED
    assert active.projection_uuid == PROJECTION
    state = collect_current_override_state(session, PACKAGE, RELEASE)
    assert state.entries == ()
    assert state.override_set_uuid == EMPTY_OVERRIDE_SET_UUID
    service = RulesAuthorityService(session, now=NOW)
    for resolution in (
        service.resolve(package_uuid=UUID(PACKAGE)),
        # A UUID-string reference; the human-facing slug is proved below.
        service.resolve(package_reference=PACKAGE),
        service.resolve(package_uuid=UUID(PACKAGE), expected_release=RELEASE),
    ):
        assert resolution.outcome is AuthorityOutcome.RESOLVED, resolution.detail
        assert resolution.binding == _expected_binding()
        assert resolution.override_state is not None
        assert resolution.override_state.entries == ()


def test_publication_is_committed_and_visible_to_a_fresh_session(
    published: Published,
) -> None:
    """After the durability boundary, an independent session sees the binding."""
    fresh = published.fresh
    assert fresh.active.outcome is PublicationOutcome.PUBLISHED
    assert fresh.active.projection_uuid == PROJECTION
    assert fresh.binding.outcome is AuthorityOutcome.RESOLVED, fresh.binding.detail
    assert fresh.binding.binding == _expected_binding()
    assert fresh.slice.outcome is AuthorityOutcome.RESOLVED, fresh.slice.detail
    assert fresh.slice.slice is not None
    assert fresh.slice.slice.binding == _expected_binding()
    assert [r.semantic_key for r in fresh.slice.slice.records] == [PROBE_RECORD]


def test_the_packages_human_facing_slug_resolves_to_the_same_binding(
    published: Published,
) -> None:
    """The source package's own name, slugified, is a real slug reference."""
    fresh = published.fresh
    assert fresh.slug == package_slug(fresh.package_name)
    with pytest.raises(ValueError):
        UUID(fresh.slug)
    assert (
        fresh.slug_binding.outcome is AuthorityOutcome.RESOLVED
    ), fresh.slug_binding.detail
    assert fresh.slug_binding.binding == _expected_binding()
    assert (
        fresh.slug_slice.outcome is AuthorityOutcome.RESOLVED
    ), fresh.slug_slice.detail
    assert fresh.slug_slice.slice is not None
    assert fresh.slug_slice.slice.binding == _expected_binding()
    assert [r.semantic_key for r in fresh.slug_slice.slice.records] == [PROBE_RECORD]


def test_the_runtime_slice_is_the_whole_accepted_authority(
    published: Published,
) -> None:
    result = RulesAuthorityService(published.session, now=NOW).rule_slice(
        _whole_package()
    )
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert result.slice is not None
    assert result.slice.whole_package
    assert result.slice.binding.mechanical_projection_uuid == UUID(PROJECTION)
    assert len(result.slice.records) == ACCEPTED_RECORDS
    assert all(r.supplied_by_override_id is None for r in result.slice.records)


def test_a_selected_record_carries_its_exact_accepted_provenance(
    published: Published, accepted: AcceptedInputs
) -> None:
    """One real record, with the spans the Owner accepted as its source."""
    service = RulesAuthorityService(published.session, now=NOW)
    result = service.rule_slice(
        RuleSliceRequest(package_id=UUID(PACKAGE), record_selectors=(PROBE_RECORD,))
    )
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert result.slice is not None
    (record,) = result.slice.records
    assert record.semantic_key == PROBE_RECORD
    assert record.components

    provenance = accepted.oracle.representation.provenance
    assert sorted(record.span_ids) == sorted(
        p.span_id
        for p in provenance
        if p.target_kind is ProvenanceTargetKind.RECORD
        and tuple(p.target_key) == (PROBE_RECORD,)
    )
    for component in record.components:
        assert sorted(component.span_ids) == sorted(
            p.span_id
            for p in provenance
            if p.target_kind is ProvenanceTargetKind.COMPONENT
            and tuple(p.target_key) == (PROBE_RECORD, component.semantic_key)
        )
    assert any(c.span_ids for c in record.components)

    unknown = service.rule_slice(
        RuleSliceRequest(
            package_id=UUID(PACKAGE), record_selectors=("glossary.not-a-record",)
        )
    )
    assert unknown.outcome is AuthorityOutcome.INVALID_REFERENCE
    assert unknown.slice is None


def test_runtime_refuses_stale_evidence_and_a_superseded_binding(
    published: Published,
) -> None:
    """Edited recorded evidence is STALE at runtime, and rolls back cleanly.

    The activation row is not authority on its own: runtime requires the
    projection it names to carry closed recorded evidence. Content re-proof of
    the persisted rows is publication's (``publish_from_committed_oracle``
    re-runs the full gate); runtime reads assert recorded-evidence closure and
    recorded-binding currency, per the ``resolve_active_projection`` contract.
    """
    session = published.session
    service = RulesAuthorityService(session, now=NOW)
    current = service.resolve(package_uuid=UUID(PACKAGE))
    assert current.binding is not None

    superseded = current.binding.model_copy(
        update={
            "mechanical_projection_uuid": UUID("00000000-0000-5000-8000-000000000000")
        }
    )
    stale_binding = service.resolve(package_uuid=UUID(PACKAGE), recorded=superseded)
    assert stale_binding.outcome is AuthorityOutcome.STALE
    assert stale_binding.current_binding == current.binding

    savepoint = session.begin_nested()
    header = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == PROJECTION
        )
    ).scalar_one()
    header.evidence_report_hash = "0" * 64
    session.flush()
    assert resolve_active_projection(session, PACKAGE).outcome is (
        PublicationOutcome.STALE
    )
    assert service.resolve(package_uuid=UUID(PACKAGE)).outcome is (
        AuthorityOutcome.STALE
    )
    savepoint.rollback()

    restored = service.resolve(package_uuid=UUID(PACKAGE))
    assert restored.outcome is AuthorityOutcome.RESOLVED
    assert restored.binding == current.binding
    session.rollback()


# ---------------------------------------------------------------------------
# Citation source retention (ADR-005d Decision 7)
# ---------------------------------------------------------------------------
#
# A citation is the source's: its destinations are readable while the effective
# citing record, component or prose still carries the accepted source, and it is
# refused once that source is disabled or replaced. Each family below cites
# through text bound as no component's prose, which the reader used to refuse
# even with no override at all.

#: Component-owned; governing prose plus unbound supporting text contextual to
#: sibling components (``check_proficiency``, ``attack_proficiency``).
PROFICIENCY = (
    "play.d20_tests",
    "add_modifiers",
    "Proficiency",
    "srd-5.2.1/playing-the-game",
)
#: Component-owned; unbound substantive text owned (PRIMARY) by the component.
INCAPACITATED = (
    "glossary.dodge",
    "benefits_lost",
    "Incapacitated",
    "srd-5.2.1/rules-glossary",
)
#: Component-owned; unbound substantive and supporting text.
EXHAUSTION = (
    "glossary.dehydration",
    "dehydration_exhaustion",
    "Exhaustion",
    "srd-5.2.1/rules-glossary",
)
#: Record-owned; unbound substantive text owned by ``grappled_condition`` and
#: unbound supporting text owned by the record.
GRAPPLED = ("glossary.grappling", "", "Grappled", "srd-5.2.1/rules-glossary")
DESTINATIONS = {
    PROFICIENCY: "play.proficiency",
    INCAPACITATED: "glossary.incapacitated",
    EXHAUSTION: "glossary.exhaustion",
    GRAPPLED: "glossary.grappled",
}

COMPONENT = MechanicalTargetKind.COMPONENT
PROSE = MechanicalTargetKind.PROSE
RECORD = MechanicalTargetKind.RECORD
DISABLE = OverrideOperationEnum.DISABLE
REPLACE = OverrideOperationEnum.REPLACE
APPEND = OverrideOperationEnum.APPEND


def _override(
    kind: MechanicalTargetKind,
    record_key: str,
    component_key: str | None = None,
    operation: OverrideOperationEnum = DISABLE,
    payload: dict[str, object] | None = None,
) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
        override_id=f"{operation.value}-{kind.value}-{record_key}-{component_key}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=kind, record_key=record_key, component_key=component_key
        ),
        operation=operation,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload=payload or {"patch": "disable"},
    )


def _replaced_component(record_key: str, component_key: str) -> EffectiveOverrideEntry:
    return _override(
        COMPONENT,
        record_key,
        component_key,
        REPLACE,
        {
            "patch": "replace_component",
            "component": {
                "handling": "prose_bound",
                "facts": [],
                "authored_prose": "A house rule.",
            },
        },
    )


def _replaced_record(record_key: str) -> EffectiveOverrideEntry:
    return _override(
        RECORD,
        record_key,
        None,
        REPLACE,
        {
            "patch": "replace_record",
            "record_kind": "glossary_rule",
            "components": [
                {
                    "semantic_key": "house",
                    "handling": "prose_bound",
                    "facts": [],
                    "authored_prose": "A house rule.",
                }
            ],
        },
    )


def _appended_prose(record_key: str, component_key: str) -> EffectiveOverrideEntry:
    return _override(
        PROSE,
        record_key,
        component_key,
        APPEND,
        {"patch": "append_prose", "text": "A house note."},
    )


def _cite(
    published: Published,
    monkeypatch: pytest.MonkeyPatch,
    citation: tuple[str, str, str, str],
    *entries: EffectiveOverrideEntry,
) -> AuthorityResult:
    """Read *citation* through the persisted reader, with *entries* in effect.

    With no entries this is the real runtime path: the published projection's
    actual resolution. With entries, the same active binding is resolved with
    that override set supplied, as the other persisted-reader suites do.
    """
    service = RulesAuthorityService(published.session, now=NOW)
    request = RuleSliceRequest(package_id=UUID(PACKAGE), whole_package=True)
    if entries:
        state = EffectiveOverrideSet(PACKAGE, RELEASE, entries)
        binding = _expected_binding().model_copy(
            update={"override_set_uuid": UUID(state.override_set_uuid)}
        )
        monkeypatch.setattr(
            service,
            "resolve",
            lambda **_: BindingResolution(
                AuthorityOutcome.RESOLVED, binding=binding, override_state=state
            ),
        )
    result = service.citation_view(
        request, citation=citation, selection=AlternativeSelection()
    )
    published.session.rollback()
    return result


def test_every_accepted_citation_is_in_effect_with_no_override(
    published: Published,
) -> None:
    """ADR-005d Decision 7 stated directly, over the whole accepted projection.

    With no override nothing is disabled or replaced, so no resolved citation
    may be refused. The retention predicate is evaluated once per citation over
    one reconstruction (the public reader would reconstruct per call); the four
    runtime reads above cover the public path. The family census pins which
    citations cite through text bound as no component's prose, so a silent
    change to the accepted metadata or the rule fails here by name.
    """
    session = published.session
    service = RulesAuthorityService(session, now=NOW)
    result, authority = service._resolve_authority(_whole_package())
    assert authority is not None and result.binding == _expected_binding()
    candidate = service._reconstruct(result.binding)
    session.rollback()
    representation = candidate.representation

    stated: dict[tuple[str, str, str, str], list[ReferenceDraft]] = {}
    for ref in representation.references:
        if ref.target_record_key:
            citation = (
                ref.from_record_key,
                ref.from_component_key,
                ref.source_text,
                ref.scope_key,
            )
            stated.setdefault(citation, []).append(ref)
    # The persisted projection carries the effective representation: 8,640
    # resolved reference rows under 8,104 distinct four-part citation keys --
    # the predecessor's 8,583 and 8,047 plus the 57 citations the CRD Issue 2b
    # G1 rows print. (The stored committed representation has 8,104 reference
    # rows and 1,486 recorded resolutions; different quantities.)
    assert sum(len(refs) for refs in stated.values()) == 8640
    assert len(stated) == 8104
    refused = [
        citation
        for citation, refs in stated.items()
        if not _citation_in_effect(citation, refs, candidate, authority)
    ]
    assert refused == []

    disposition = {
        s.span_id: s.disposition.value for s in candidate.classification.spans
    }
    bound = {b.span_id for b in representation.prose_bindings}
    cited: dict[tuple[str, ...], set[str]] = {}
    for claim in representation.provenance:
        if claim.target_kind is ProvenanceTargetKind.REFERENCE:
            cited.setdefault(tuple(claim.target_key), set()).add(claim.span_id)
    families: Counter[tuple[str, tuple[str, ...], bool]] = Counter()
    for citation, refs in stated.items():
        spans = set().union(*(cited[reference_target_key(r)] for r in refs))
        unbound = spans - bound
        if unbound:
            families[
                (
                    "component" if citation[1] else "record",
                    tuple(sorted({disposition[s] for s in unbound})),
                    bool(spans & bound),
                )
            ] += 1
    assert dict(families) == {
        ("record", ("supporting_authority",), False): 138,
        ("record", ("supporting_authority",), True): 1,
        ("component", ("supporting_authority",), True): 18,
        ("component", ("substantive",), False): 16,
        ("component", ("substantive", "supporting_authority"), False): 2,
        ("record", ("substantive", "supporting_authority"), False): 1,
    }


@pytest.mark.parametrize(
    "citation",
    [PROFICIENCY, INCAPACITATED, EXHAUSTION, GRAPPLED],
    ids=[
        "component-prose-supporting",
        "component-substantive",
        "component-substantive-supporting",
        "record-substantive-supporting",
    ],
)
def test_an_accepted_citation_reads_its_destination_at_runtime(
    published: Published,
    monkeypatch: pytest.MonkeyPatch,
    citation: tuple[str, str, str, str],
) -> None:
    """No override: the published authority states the citation, so it reads."""
    result = _cite(published, monkeypatch, citation)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert result.binding == _expected_binding()
    destinations = [r for _, members in result.routes for r, _ in members]
    assert DESTINATIONS[citation] in destinations


@pytest.mark.parametrize(
    ("citation", "override"),
    [
        pytest.param(
            PROFICIENCY,
            _override(PROSE, "play.d20_tests", "add_modifiers"),
            id="proficiency-prose-disabled",
        ),
        pytest.param(
            PROFICIENCY,
            _replaced_component("play.d20_tests", "add_modifiers"),
            id="proficiency-component-replaced",
        ),
        pytest.param(
            INCAPACITATED,
            _override(COMPONENT, "glossary.dodge", "benefits_lost"),
            id="incapacitated-owner-disabled",
        ),
        pytest.param(
            INCAPACITATED,
            _replaced_component("glossary.dodge", "benefits_lost"),
            id="incapacitated-owner-replaced",
        ),
        pytest.param(
            INCAPACITATED,
            _override(RECORD, "glossary.dodge"),
            id="incapacitated-record-disabled",
        ),
        pytest.param(
            EXHAUSTION,
            _replaced_record("glossary.dehydration"),
            id="exhaustion-record-replaced",
        ),
        pytest.param(
            GRAPPLED,
            _override(COMPONENT, "glossary.grappling", "grappled_condition"),
            id="grappled-substantive-owner-disabled",
        ),
        pytest.param(
            GRAPPLED,
            _replaced_record("glossary.grappling"),
            id="grappled-record-replaced",
        ),
    ],
)
def test_a_citation_whose_original_source_is_gone_is_refused(
    published: Published,
    monkeypatch: pytest.MonkeyPatch,
    citation: tuple[str, str, str, str],
    override: EffectiveOverrideEntry,
) -> None:
    result = _cite(published, monkeypatch, citation, override)
    assert result.outcome is AuthorityOutcome.INVALID_REFERENCE
    assert "effective source no longer states" in result.detail


@pytest.mark.parametrize(
    ("citation", "override"),
    [
        pytest.param(
            PROFICIENCY,
            _override(COMPONENT, "play.d20_tests", "check_proficiency"),
            id="proficiency-sibling-disabled",
        ),
        pytest.param(
            INCAPACITATED,
            _override(COMPONENT, "glossary.dodge", "dodge_benefits"),
            id="incapacitated-sibling-disabled",
        ),
        pytest.param(
            GRAPPLED,
            _appended_prose("glossary.grappling", "grapple_basis"),
            id="grappled-prose-appended",
        ),
    ],
)
def test_a_citation_survives_edits_that_leave_its_source(
    published: Published,
    monkeypatch: pytest.MonkeyPatch,
    citation: tuple[str, str, str, str],
    override: EffectiveOverrideEntry,
) -> None:
    """A sibling's contextual provenance is not a new dependency of the citation."""
    result = _cite(published, monkeypatch, citation, override)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert result.gamemaster_view is not None
    assert [a.override_id for a in result.gamemaster_view.applied_overrides] == [
        override.override_id
    ]


# ---------------------------------------------------------------------------
# Negative control: the full corpus, minus three leaves
# ---------------------------------------------------------------------------


def _without_leaves(
    candidate: ProjectionCandidate, count: int
) -> tuple[ProjectionCandidate, tuple[str, ...]]:
    """The accepted candidate with *count* real leaves left unaccounted for.

    Every leaf the accepted authority classifies by a span also has a span that
    provenance or a prose binding cites, so removing spans would break the
    representation rather than merely shrink the accounting. The leaves chosen
    here are the other kind: a heading leaf no span classifies, accounted for
    only by its review unit's excluded group ("entry heading: names the entry
    and states no rule"). Removing it from that unit and that group leaves the
    unit internally consistent and the leaf accounted for by nothing, so
    incompleteness is the only thing wrong.
    """
    span_leaves = {s.leaf_id for s in candidate.classification.spans}
    excluded_only = sorted(
        leaf
        for unit in candidate.review_units
        for group in unit.excluded_groups
        for leaf in group.leaf_ids
        if leaf not in span_leaves
    )
    dropped = tuple(excluded_only[:count])
    assert len(dropped) == count

    units = []
    for unit in candidate.review_units:
        if not set(unit.leaf_ids) & set(dropped):
            units.append(unit)
            continue
        groups = tuple(
            dataclasses.replace(
                group, leaf_ids=tuple(x for x in group.leaf_ids if x not in dropped)
            )
            for group in unit.excluded_groups
        )
        units.append(
            dataclasses.replace(
                unit,
                leaf_ids=tuple(x for x in unit.leaf_ids if x not in dropped),
                excluded_groups=tuple(g for g in groups if g.leaf_ids),
            )
        )
    return dataclasses.replace(candidate, review_units=tuple(units)), dropped


@dataclass(frozen=True)
class Refused:
    session: Session
    projection_uuid: str
    dropped_leaves: tuple[str, ...]
    result: PublicationResult


@pytest.fixture(scope="module")
def refused(
    tmp_path_factory: pytest.TempPathFactory,
    source_release_db: Path,
    accepted: AcceptedInputs,
) -> Iterator[Refused]:
    for session, _ in _private_store(tmp_path_factory, source_release_db, "incomplete"):
        candidate, dropped_leaves = _without_leaves(
            candidate_from_accepted_inputs(accepted), DROPPED_LEAVES
        )
        projection_uuid = _persist(session, candidate)
        result = publish_from_committed_oracle(session, projection_uuid, now=NOW)
        yield Refused(session, projection_uuid, dropped_leaves, result)


def test_a_full_corpus_missing_three_leaves_is_refused_per_leaf(
    refused: Refused,
) -> None:
    result = refused.result
    assert refused.projection_uuid != PROJECTION
    assert result.outcome is PublicationOutcome.INCOMPLETE
    assert result.gate is not None and not result.gate.passed
    # Exactly incompleteness, reported at both accounting layers and in the
    # oracle comparison: nothing stale, no other release or policy, no residue,
    # no schema disagreement.
    assert result.gate.categories() == {
        GateFailureCategory.POPULATION_MISMATCH,
        GateFailureCategory.SEMANTIC_VALIDATION,
        GateFailureCategory.MISSING_AUTHORITY,
        GateFailureCategory.UNEXPECTED_AUTHORITY,
        GateFailureCategory.IDENTITY_MISMATCH,
    }

    def details(category: GateFailureCategory) -> list[str]:
        assert result.gate is not None
        return sorted(f.detail for f in result.gate.failures if f.category is category)

    assert details(GateFailureCategory.POPULATION_MISMATCH) == [
        f"leaf {leaf}: represented by the bound 5c release, absent from the "
        "accepted classification and named by no accepted review unit"
        for leaf in refused.dropped_leaves
    ]
    assert details(GateFailureCategory.SEMANTIC_VALIDATION) == [
        f"leaf {leaf}: no semantic spans" for leaf in refused.dropped_leaves
    ]
    # The three edited review units: each accepted form missing, each edited
    # form unexpected.
    assert len(details(GateFailureCategory.MISSING_AUTHORITY)) == DROPPED_LEAVES
    assert len(details(GateFailureCategory.UNEXPECTED_AUTHORITY)) == DROPPED_LEAVES
    assert details(GateFailureCategory.IDENTITY_MISMATCH) == [
        f"accepted authority derives projection {PROJECTION}, persisted state is "
        f"{refused.projection_uuid}"
    ]


def test_the_refused_projection_left_nothing_active(refused: Refused) -> None:
    session = refused.session
    header = session.execute(
        select(MechanicalProjectionORM).where(
            MechanicalProjectionORM.projection_uuid == refused.projection_uuid
        )
    ).scalar_one()
    assert header.publication_status == "draft"
    assert header.evidence_report_hash is None
    assert session.execute(select(MechanicalActiveProjectionORM)).first() is None
    assert resolve_active_projection(session, PACKAGE).outcome is (
        PublicationOutcome.UNPUBLISHED
    )
    resolution = RulesAuthorityService(session, now=NOW).resolve(
        package_uuid=UUID(PACKAGE)
    )
    assert resolution.outcome is AuthorityOutcome.UNPUBLISHED


def test_the_committed_authority_bytes_are_unchanged() -> None:
    assert hashlib.sha256(ORACLE_FILE.read_bytes()).hexdigest() == ORACLE_SHA256
