"""Schema and migration tests for CRD Issue 14a provider tables."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import afterworlds.pipeline.provider._refusal_log  # noqa: F401
import afterworlds.pipeline.provider._route_config  # noqa: F401
import afterworlds.pipeline.provider.credentials._metadata  # noqa: F401
from afterworlds.persistence.orm.base import Base
from afterworlds.pipeline.provider._refusal_log import ProviderRefusalEvent
from afterworlds.pipeline.provider._route_config import ProviderRouteConfigORM
from afterworlds.pipeline.provider.credentials._metadata import (
    ProviderCredentialMetadata,
)

# ---------------------------------------------------------------------------
# Table existence
# ---------------------------------------------------------------------------


def test_provider_credential_metadata_table_exists(session: Session) -> None:
    """Migration creates the provider_credential_metadata table."""
    inspector = inspect(session.bind)
    assert "provider_credential_metadata" in inspector.get_table_names()


def test_provider_route_config_table_exists(session: Session) -> None:
    """Migration creates the provider_route_config table."""
    inspector = inspect(session.bind)
    assert "provider_route_config" in inspector.get_table_names()


def test_provider_refusal_log_table_exists(session: Session) -> None:
    """Migration creates the provider_refusal_log table."""
    inspector = inspect(session.bind)
    assert "provider_refusal_log" in inspector.get_table_names()


# ---------------------------------------------------------------------------
# INTEGER PRIMARY KEY (SQLite rowid alias)
# ---------------------------------------------------------------------------


def test_provider_refusal_log_id_is_integer_primary_key(session: Session) -> None:
    """provider_refusal_log.id is INTEGER PRIMARY KEY (SQLite rowid alias)."""
    inspector = inspect(session.bind)
    cols = {c["name"]: c for c in inspector.get_columns("provider_refusal_log")}
    assert "id" in cols
    assert "INT" in str(cols["id"]["type"]).upper()


# ---------------------------------------------------------------------------
# UniqueConstraints
# ---------------------------------------------------------------------------


def test_credential_metadata_unique_sojourner_provider(session: Session) -> None:
    """Duplicate (sojourner_id, provider_name) on credential_metadata raises."""
    from datetime import datetime

    sid = "11111111-1111-1111-1111-111111111111"
    now = datetime(2026, 6, 10)
    row1 = ProviderCredentialMetadata(
        sojourner_id=sid,
        provider_name="anthropic",
        is_active=True,
        validation_status="untested",
        created_at=now,
        updated_at=now,
    )
    session.add(row1)
    session.commit()

    row2 = ProviderCredentialMetadata(
        sojourner_id=sid,
        provider_name="anthropic",
        is_active=True,
        validation_status="untested",
        created_at=now,
        updated_at=now,
    )
    session.add(row2)
    with pytest.raises(IntegrityError):
        session.commit()


def test_credential_metadata_allows_different_providers(session: Session) -> None:
    """Different provider_names for the same sojourner_id are allowed."""
    from datetime import datetime

    sid = "22222222-2222-2222-2222-222222222222"
    now = datetime(2026, 6, 10)
    session.add_all(
        [
            ProviderCredentialMetadata(
                sojourner_id=sid,
                provider_name="anthropic",
                is_active=True,
                validation_status="untested",
                created_at=now,
                updated_at=now,
            ),
            ProviderCredentialMetadata(
                sojourner_id=sid,
                provider_name="openrouter",
                is_active=True,
                validation_status="untested",
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    session.commit()  # must not raise


def test_route_config_unique_sojourner_provider(session: Session) -> None:
    """Duplicate (sojourner_id, provider_name) on route_config raises."""
    sid = "33333333-3333-3333-3333-333333333333"
    row1 = ProviderRouteConfigORM(
        sojourner_id=sid,
        provider_name="anthropic",
        is_active=True,
    )
    session.add(row1)
    session.commit()

    row2 = ProviderRouteConfigORM(
        sojourner_id=sid,
        provider_name="anthropic",
        is_active=True,
    )
    session.add(row2)
    with pytest.raises(IntegrityError):
        session.commit()


# ---------------------------------------------------------------------------
# Append-only triggers on provider_refusal_log
# ---------------------------------------------------------------------------


def _make_refusal_event(session: Session) -> ProviderRefusalEvent:
    from datetime import datetime

    event = ProviderRefusalEvent(
        pass_id="WRITER",
        primary_provider_name="anthropic",
        primary_model_identifier="claude-sonnet-4-6",
        refusal_category="CONTENT_POLICY",
        fallback_outcome="NO_FALLBACK_CONFIGURED",
        created_at=datetime(2026, 6, 10),
    )
    session.add(event)
    session.commit()
    return event


def test_trigger_blocks_update_on_refusal_log(session: Session) -> None:
    """SQLite trigger prevents UPDATE on provider_refusal_log."""
    event = _make_refusal_event(session)
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "UPDATE provider_refusal_log SET refusal_category = 'x'"
                " WHERE id = :id"
            ),
            {"id": event.id},
        )
        session.commit()


def test_trigger_blocks_delete_on_refusal_log(session: Session) -> None:
    """SQLite trigger prevents DELETE on provider_refusal_log."""
    event = _make_refusal_event(session)
    with pytest.raises(IntegrityError):
        session.execute(
            text("DELETE FROM provider_refusal_log WHERE id = :id"),
            {"id": event.id},
        )
        session.commit()


def test_refusal_log_id_monotonically_increases(session: Session) -> None:
    """SQLite assigns id monotonically on insert to provider_refusal_log."""
    from datetime import datetime

    def _event() -> ProviderRefusalEvent:
        return ProviderRefusalEvent(
            pass_id="WRITER",
            primary_provider_name="anthropic",
            primary_model_identifier="claude-sonnet-4-6",
            refusal_category="CONTENT_POLICY",
            fallback_outcome="NO_FALLBACK_CONFIGURED",
            created_at=datetime(2026, 6, 10),
        )

    e1 = _event()
    e2 = _event()
    session.add_all([e1, e2])
    session.commit()

    assert e1.id is not None
    assert e2.id is not None
    assert e2.id > e1.id


# ---------------------------------------------------------------------------
# ORM registration in Base.metadata
# ---------------------------------------------------------------------------


def test_provider_tables_in_base_metadata() -> None:
    """Provider ORM imports register all three tables in Base.metadata.

    Regression for the alembic/env.py bootstrap gap: autogenerate/create_all
    omits provider tables if the ORM modules are never imported.
    """
    import afterworlds.pipeline.provider._refusal_log  # noqa: F401
    import afterworlds.pipeline.provider._route_config  # noqa: F401
    import afterworlds.pipeline.provider.credentials._metadata  # noqa: F401

    assert "provider_credential_metadata" in Base.metadata.tables
    assert "provider_route_config" in Base.metadata.tables
    assert "provider_refusal_log" in Base.metadata.tables
