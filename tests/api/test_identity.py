"""DoR-A: single local Sojourner identity provisioning."""

from __future__ import annotations

from uuid import uuid4

import afterworlds.persistence.orm.identity  # noqa: F401
from afterworlds.persistence.crud.identity import get_or_create_sojourner_identity
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base


def test_first_run_creates_identity_once(tmp_path) -> None:  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{tmp_path / 'id.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)

    session = factory()
    try:
        first = get_or_create_sojourner_identity(session)
        session.commit()
    finally:
        session.close()

    session2 = factory()
    try:
        second = get_or_create_sojourner_identity(session2)
        session2.commit()
    finally:
        session2.close()

    assert first.sojourner_id == second.sojourner_id


def test_client_supplied_sojourner_id_in_body_rejected(client) -> None:  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/stories",
        json={"title": "X", "mode": "writing", "sojourner_id": str(uuid4())},
    )
    assert resp.status_code == 422


def test_client_supplied_sojourner_id_in_header_ignored(client) -> None:  # type: ignore[no-untyped-def]
    spoofed = str(uuid4())
    resp = client.get("/api/health", headers={"X-Sojourner-Id": spoofed})
    assert resp.status_code == 200
    # The provisioned id is server-side only; no route echoes it back, but
    # confirm the app never adopted the header value as its identity.
    assert client.app.state.sojourner_id != spoofed
