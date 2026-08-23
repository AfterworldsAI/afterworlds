"""The real CRD Issue 5c release, through the runtime authority path.

Everything else in this suite runs against a bounded fixture. This module runs
against the *actual* published SRD 5.2.1 corpus — built from the committed PDF
and finalized through CRD Issue 5c's own lifecycle — and proves the claim this
PR must not overstate.

The runtime binding path resolves the real release's package and reports
``UNPUBLISHED``: no accepted oracle is committed for that release, so no
mechanical projection over it has been published, so there is no active
mechanical authority to bind. That is the honest state, and it is asserted here
as a *typed* outcome rather than as an absence — a resolver that answered
"nothing" would be indistinguishable from one that had lost the release.

It also re-confirms the exact production release identity from current ``main``
rather than restating a previously reported value.

Session-scoped 5c fixtures are shared with the CRD Issue 5c and 5d suites
through ``tests/ingestion/conftest.py``, so this costs no second corpus build.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import select

from afterworlds.ingestion.corpus.persistence import persist_release
from afterworlds.ingestion.corpus.pipeline import ReleaseArtifacts
from afterworlds.ingestion.mechanical.oracle import committed_oracle_for
from afterworlds.models.rules_package import RuleSliceRequest
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from afterworlds.services.rules_authority import (
    EMPTY_OVERRIDE_SET_UUID,
    AuthorityOutcome,
    RulesAuthorityService,
    collect_current_override_state,
    resolve_package_reference,
)

NOW = "2026-08-08T00:00:00Z"

#: The production identity last verified on ``main``. A drift canary, not
#: authority: the assertions below read the identity from the release the
#: committed source actually builds, and this constant only makes an unexpected
#: change legible in the failure message.
EXPECTED_PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"
EXPECTED_RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"


@pytest.fixture(scope="module")
def production(full_release: ReleaseArtifacts):  # type: ignore[no-untyped-def]
    """The real release re-persisted into a private store, marked published."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with create_session_factory(engine)() as session:
        persist_release(session, full_release, now=NOW)
        package_uuid = full_release.release.package_uuid
        session.execute(
            select(CorpusReleaseORM).where(
                CorpusReleaseORM.package_uuid == package_uuid
            )
        ).scalar_one().publication_status = "published"
        package = session.execute(
            select(RulesPackageORM).where(
                RulesPackageORM.rules_package_id == package_uuid
            )
        ).scalar_one()
        package.publication_status = "published"
        package.published_at = NOW
        session.flush()
        yield session, full_release
    engine.dispose()


def test_the_production_release_identity(production) -> None:  # type: ignore[no-untyped-def]
    """Re-confirmed from the release the committed source builds."""
    _session, release = production
    assert release.release.package_uuid == EXPECTED_PACKAGE_UUID
    assert release.release.release_version == EXPECTED_RELEASE_VERSION


def test_accepted_authority_resolves_but_nothing_is_published(
    production,  # type: ignore[no-untyped-def]
) -> None:
    """Accepted authority exists for the real release; none of it is active.

    Acceptance and publication are separate acts. Committing a reviewed
    artifact records what a human accepted; it publishes no rules package and
    activates no release, which the sibling test below asserts directly.
    """
    _session, release = production
    assert (
        committed_oracle_for(
            release.release.package_uuid, release.release.release_version
        )
        is not None
    )


def test_the_production_binding_resolves_to_unpublished(
    production,  # type: ignore[no-untyped-def]
) -> None:
    """Typed, not empty: this PR publishes no production mechanical authority."""
    session, release = production
    resolution = RulesAuthorityService(session, now=NOW).resolve(
        package_uuid=UUID(release.release.package_uuid)
    )
    assert resolution.outcome is AuthorityOutcome.UNPUBLISHED
    assert resolution.binding is None
    assert "no active mechanical projection" in resolution.detail


def test_the_production_package_reference_still_resolves(
    production,  # type: ignore[no-untyped-def]
) -> None:
    """Package resolution and authority resolution are different questions.

    The package is found; what it has no published mechanical projection for is
    the authority. Collapsing the two would make "this package does not exist"
    and "this package has no typed authority yet" the same answer.
    """
    session, release = production
    resolved = resolve_package_reference(session, release.release.package_uuid)
    assert resolved.outcome is AuthorityOutcome.RESOLVED
    assert resolved.package_uuid == UUID(release.release.package_uuid)


def test_the_production_package_has_the_empty_override_state(
    production,  # type: ignore[no-untyped-def]
) -> None:
    """No typed overrides are authored against production authority here."""
    session, release = production
    state = collect_current_override_state(
        session,
        release.release.package_uuid,
        release.release.release_version,
    )
    assert state.entries == ()
    assert state.override_set_uuid == EMPTY_OVERRIDE_SET_UUID


def test_a_production_rule_slice_is_typed_not_empty(
    production,  # type: ignore[no-untyped-def]
) -> None:
    """A whole-package request over the real release refuses explicitly."""
    session, release = production
    result = RulesAuthorityService(session, now=NOW).rule_slice(
        RuleSliceRequest(
            package_id=UUID(release.release.package_uuid), whole_package=True
        )
    )
    assert result.outcome is AuthorityOutcome.UNPUBLISHED
    assert result.slice is None
