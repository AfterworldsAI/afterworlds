"""Migration and schema tests — AC 1–7."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from afterworlds.entitlement.orm import EntitlementEvent, RuntimeEntitlementState


def test_entitlement_event_table_exists(session: Session) -> None:
    """AC 1: migration creates the entitlement_event table."""
    inspector = inspect(session.bind)
    assert "entitlement_event" in inspector.get_table_names()


def test_runtime_entitlement_state_table_exists(session: Session) -> None:
    """AC 1: migration creates the runtime_entitlement_state table."""
    inspector = inspect(session.bind)
    assert "runtime_entitlement_state" in inspector.get_table_names()


def test_global_sequence_is_integer_primary_key(session: Session) -> None:
    """AC 2: global_sequence is INTEGER PRIMARY KEY (SQLite rowid alias)."""
    inspector = inspect(session.bind)
    cols = {c["name"]: c for c in inspector.get_columns("entitlement_event")}
    assert "global_sequence" in cols
    # SQLite rowid alias: type must be INTEGER
    col_type = str(cols["global_sequence"]["type"]).upper()
    assert "INT" in col_type


def test_event_id_unique_constraint(session: Session) -> None:
    """AC 3: event_id has a UNIQUE constraint."""
    inspector = inspect(session.bind)
    indexes = inspector.get_indexes("entitlement_event")
    unique_cols = {
        col for idx in indexes if idx.get("unique") for col in idx["column_names"]
    }
    assert "event_id" in unique_cols, "event_id must have a UNIQUE index"


def test_trigger_blocks_update(session: Session) -> None:
    """AC 6: SQLite trigger prevents UPDATE on entitlement_event."""
    from datetime import datetime
    from uuid import uuid4

    from afterworlds.entitlement.enums import EntitlementEventType

    event = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=uuid4(),
        event_type=EntitlementEventType.BYOK_LICENSE_ACTIVATED,
        payload_json='{"schema_version": 1, "purchased_at": "2026-01-01T00:00:00"}',
        created_at=datetime(2026, 6, 5),
    )
    session.add(event)
    session.commit()

    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "UPDATE entitlement_event SET payload_json = 'x' "
                "WHERE global_sequence = :seq"
            ),
            {"seq": event.global_sequence},
        )
        session.commit()


def test_trigger_blocks_delete(session: Session) -> None:
    """AC 6: SQLite trigger prevents DELETE on entitlement_event."""
    from datetime import datetime
    from uuid import uuid4

    from afterworlds.entitlement.enums import EntitlementEventType

    event = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=uuid4(),
        event_type=EntitlementEventType.BYOK_LICENSE_ACTIVATED,
        payload_json='{"schema_version": 1, "purchased_at": "2026-01-01T00:00:00"}',
        created_at=datetime(2026, 6, 5),
    )
    session.add(event)
    session.commit()

    with pytest.raises(IntegrityError):
        session.execute(
            text("DELETE FROM entitlement_event WHERE global_sequence = :seq"),
            {"seq": event.global_sequence},
        )
        session.commit()


def test_global_sequence_monotonically_increases(session: Session) -> None:
    """AC 2: SQLite assigns global_sequence monotonically on insert."""
    from datetime import datetime
    from uuid import uuid4

    from afterworlds.entitlement.enums import EntitlementEventType

    def _event() -> EntitlementEvent:
        return EntitlementEvent(
            event_id=uuid4(),
            sojourner_id=uuid4(),
            event_type=EntitlementEventType.BYOK_LICENSE_ACTIVATED,
            payload_json='{"schema_version": 1, "purchased_at": "2026-01-01T00:00:00"}',
            created_at=datetime(2026, 6, 5),
        )

    e1 = _event()
    e2 = _event()
    session.add_all([e1, e2])
    session.commit()

    assert e1.global_sequence is not None
    assert e2.global_sequence is not None
    assert e2.global_sequence > e1.global_sequence


def test_last_entitlement_event_id_updated_after_event(
    service: EntitlementService,
    sojourner_id: UUID,
    session: Session,
) -> None:
    """AC 7: last_entitlement_event_id equals the most recent event_id."""
    from tests.entitlement.conftest import activate_hosted

    activate_hosted(service, sojourner_id)
    state = session.get(RuntimeEntitlementState, sojourner_id)
    assert state is not None

    from sqlalchemy import select

    from afterworlds.entitlement.orm import EntitlementEvent

    last_event = session.scalars(
        select(EntitlementEvent)
        .where(EntitlementEvent.sojourner_id == sojourner_id)
        .order_by(EntitlementEvent.global_sequence.desc())
        .limit(1)
    ).first()
    assert last_event is not None
    assert state.last_entitlement_event_id == last_event.event_id


def test_idempotency_key_partial_unique_rejects_duplicate(session: Session) -> None:
    """Partial unique index: duplicate non-null idempotency_key raises."""
    from datetime import datetime
    from uuid import uuid4

    from afterworlds.entitlement.enums import EntitlementEventType

    now = datetime(2026, 6, 5)
    key = f"ik-test-{uuid4().hex}"
    e1 = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=uuid4(),
        event_type=EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        idempotency_key=key,
        payload_json='{"schema_version": 1, "hosted_credit_delta": "10"}',
        created_at=now,
    )
    session.add(e1)
    session.commit()

    e2 = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=uuid4(),
        event_type=EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        idempotency_key=key,
        payload_json='{"schema_version": 1, "hosted_credit_delta": "20"}',
        created_at=now,
    )
    session.add(e2)
    with pytest.raises(IntegrityError):
        session.commit()


def test_idempotency_key_null_allows_multiple_rows(session: Session) -> None:
    """Partial unique index: NULL idempotency_key allows multiple rows."""
    from datetime import datetime
    from uuid import uuid4

    from afterworlds.entitlement.enums import EntitlementEventType

    now = datetime(2026, 6, 5)
    e1 = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=uuid4(),
        event_type=EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        idempotency_key=None,
        payload_json='{"schema_version": 1, "hosted_credit_delta": "10"}',
        created_at=now,
    )
    e2 = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=uuid4(),
        event_type=EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        idempotency_key=None,
        payload_json='{"schema_version": 1, "hosted_credit_delta": "20"}',
        created_at=now,
    )
    session.add_all([e1, e2])
    session.commit()  # must not raise


def test_credit_deduction_partial_unique_rejects_duplicate_turn(
    session: Session,
) -> None:
    """Partial unique: duplicate (sojourner_id, turn_id) for credit_deduction raises."""
    from datetime import datetime
    from uuid import uuid4

    from afterworlds.entitlement.enums import EntitlementEventType

    sid = uuid4()
    turn = uuid4()
    now = datetime(2026, 6, 5)
    payload = (
        '{"schema_version": 1, "hosted_credit_delta": "-1", "top_up_credit_delta": "0"}'
    )

    e1 = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=sid,
        event_type=EntitlementEventType.CREDIT_DEDUCTION,
        turn_id=turn,
        payload_json=payload,
        created_at=now,
    )
    session.add(e1)
    session.commit()

    e2 = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=sid,
        event_type=EntitlementEventType.CREDIT_DEDUCTION,
        turn_id=turn,
        payload_json=payload,
        created_at=now,
    )
    session.add(e2)
    with pytest.raises(IntegrityError):
        session.commit()


def test_credit_deduction_partial_unique_allows_different_turns(
    session: Session,
) -> None:
    """Partial unique index: different turn_ids for same sojourner are allowed."""
    from datetime import datetime
    from uuid import uuid4

    from afterworlds.entitlement.enums import EntitlementEventType

    sid = uuid4()
    now = datetime(2026, 6, 5)
    payload = (
        '{"schema_version": 1, "hosted_credit_delta": "-1", "top_up_credit_delta": "0"}'
    )

    e1 = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=sid,
        event_type=EntitlementEventType.CREDIT_DEDUCTION,
        turn_id=uuid4(),
        payload_json=payload,
        created_at=now,
    )
    e2 = EntitlementEvent(
        event_id=uuid4(),
        sojourner_id=sid,
        event_type=EntitlementEventType.CREDIT_DEDUCTION,
        turn_id=uuid4(),
        payload_json=payload,
        created_at=now,
    )
    session.add_all([e1, e2])
    session.commit()  # must not raise


def test_entitlement_tables_in_base_metadata() -> None:
    """entitlement ORM import registers both tables in Base.metadata.

    Regression for the alembic/env.py bootstrap gap: autogenerate/create_all
    omits entitlement tables if afterworlds.entitlement.orm is never imported.
    The conftest already imports it, but this test makes the registration
    requirement explicit and survives conftest refactors.
    """
    import afterworlds.entitlement.orm  # noqa: F401 — ensure registration
    from afterworlds.persistence.orm.base import Base

    assert "runtime_entitlement_state" in Base.metadata.tables
    assert "entitlement_event" in Base.metadata.tables


# Avoid "undefined name" in type hints in test functions above
from uuid import UUID  # noqa: E402

from afterworlds.entitlement.service import EntitlementService  # noqa: E402
