"""Release identity tests — Issue 5c, DF3 (PR #134).

A changed authoritative source with unchanged transform config must produce a
new ``package_uuid`` **and** a new ``release_version`` (not just a new UUID),
so it does not collide with the prior immutable release on the
``rp_packages (name, version, system)`` uniqueness constraint. Identical inputs
must remain byte-identical.
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from afterworlds.ingestion.corpus.bundle import (
    derive_package_uuid,
    derive_release_version,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.rules_package import RulesPackageORM

_NOW = "2026-01-01T00:00:00Z"
_TRANSFORM = "t" * 64
_SOURCE_A = "a" * 64
_SOURCE_B = "b" * 64


def test_identical_inputs_yield_identical_version_and_uuid():
    assert derive_release_version(_SOURCE_A, _TRANSFORM) == derive_release_version(
        _SOURCE_A, _TRANSFORM
    )
    assert derive_package_uuid(_SOURCE_A, _TRANSFORM) == derive_package_uuid(
        _SOURCE_A, _TRANSFORM
    )


def test_source_change_changes_both_uuid_and_version():
    # A changed source with the SAME transform config must move BOTH identities.
    assert derive_package_uuid(_SOURCE_A, _TRANSFORM) != derive_package_uuid(
        _SOURCE_B, _TRANSFORM
    )
    assert derive_release_version(_SOURCE_A, _TRANSFORM) != derive_release_version(
        _SOURCE_B, _TRANSFORM
    )


def test_transform_change_changes_both_uuid_and_version():
    assert derive_package_uuid(_SOURCE_A, "1" * 64) != derive_package_uuid(
        _SOURCE_A, "2" * 64
    )
    assert derive_release_version(_SOURCE_A, "1" * 64) != derive_release_version(
        _SOURCE_A, "2" * 64
    )


@pytest.fixture()
def session():  # type: ignore[no-untyped-def]
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    sess = create_session_factory(eng)()
    try:
        yield sess
    finally:
        sess.close()
        eng.dispose()


def _insert(session, uuid_, version):  # type: ignore[no-untyped-def]
    session.add(
        RulesPackageORM(
            rules_package_id=uuid_,
            name="SRD 5.2.1 Corpus",  # fixed corpus name (DF3 collision surface)
            system="d20",
            version=version,
            is_enabled=True,
            publication_status="published",
            created_at=_NOW,
            updated_at=_NOW,
        )
    )
    session.commit()


def test_source_changed_release_coexists_without_name_version_collision(session):
    """Two corpus releases differing only in authoritative source must persist
    side by side: the DF3-derived distinct versions keep their
    (name, version, system) keys distinct, and the prior release is untouched."""
    uuid_a = derive_package_uuid(_SOURCE_A, _TRANSFORM)
    ver_a = derive_release_version(_SOURCE_A, _TRANSFORM)
    _insert(session, uuid_a, ver_a)

    uuid_b = derive_package_uuid(_SOURCE_B, _TRANSFORM)
    ver_b = derive_release_version(_SOURCE_B, _TRANSFORM)
    # No IntegrityError: distinct version → distinct (name, version, system).
    _insert(session, uuid_b, ver_b)

    rows = session.query(RulesPackageORM).all()
    assert {r.rules_package_id for r in rows} == {uuid_a, uuid_b}
    # The predecessor is unchanged.
    pred = session.get(RulesPackageORM, uuid_a)
    assert pred is not None and pred.version == ver_a


def test_same_name_version_system_would_collide(session):
    """Guard: the constraint DF3 protects against is real — reusing the same
    version under the fixed corpus name/system does collide."""
    _insert(session, "uuid-1", "5.2.1-corpus.samever")
    with pytest.raises(IntegrityError):
        _insert(session, "uuid-2", "5.2.1-corpus.samever")
