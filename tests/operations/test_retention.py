"""CRD Issue 22 D4 schedule: exact boundaries with controlled clocks over
the real migrated stores (content chain and control chain)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.api.db_bootstrap import upgrade_to_head
from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
from afterworlds.entitlement.inspection import list_events, replay_check
from afterworlds.entitlement.orm import EntitlementEvent
from afterworlds.entitlement.payloads import (
    HostedAccessActivatedPayload,
    SubscriptionCreditGrantPayload,
)
from afterworlds.entitlement.service import EntitlementService
from afterworlds.operations.orm import (
    DataRequestORM,
    EntitlementExpiryORM,
    ExportArtifactORM,
    RightsEvidenceORM,
    SupportActionEventORM,
)
from afterworlds.operations.policy import add_calendar_months
from afterworlds.operations.requests import (
    RequestActor,
    RequestKind,
    RequestScope,
    RequestState,
    RequestStore,
)
from afterworlds.operations.retention import (
    reapply_ledger_expiries,
    release_suppression,
    reviews_due,
    sweep,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.remote.control_orm import HostedAccountORM
from afterworlds.remote.control_store import iso, open_control_store
from afterworlds.remote.storage import record_suppression, register_backup

T0 = datetime(2026, 1, 31, 12, 0, tzinfo=UTC)


@pytest.fixture()
def stores(tmp_path: Path) -> tuple[sessionmaker[Session], sessionmaker[Session]]:
    url = f"sqlite:///{tmp_path / 'content.db'}"
    upgrade_to_head(url)
    content = create_session_factory(create_engine(url))
    control = open_control_store(f"sqlite:///{tmp_path / 'control.db'}")
    yield content, control
    content.kw["bind"].dispose()
    control.kw["bind"].dispose()


def test_calendar_month_arithmetic_clamps_and_keeps_time() -> None:
    assert add_calendar_months(T0, 1) == datetime(2026, 2, 28, 12, 0, tzinfo=UTC)
    leap = datetime(2028, 2, 29, 8, 30, tzinfo=UTC)
    assert add_calendar_months(leap, 24) == datetime(2030, 2, 28, 8, 30, tzinfo=UTC)
    assert add_calendar_months(T0, 24) == datetime(2028, 1, 31, 12, 0, tzinfo=UTC)
    assert add_calendar_months(datetime(2026, 11, 30, tzinfo=UTC), 3) == datetime(
        2027, 2, 28, tzinfo=UTC
    )


def _artifact(
    ops: sessionmaker[Session], tmp: Path, *, status: str, created: datetime
) -> tuple[str, Path]:
    store = RequestStore(ops, now=lambda: created)
    rid = store.create(
        RequestActor("requester", "p", "remote", str(uuid.uuid4())),
        kind=RequestKind.EXPORT,
        scope=RequestScope.ACCOUNT,
        story_refs=[],
    )
    path = tmp / f"{uuid.uuid4()}.zip"
    path.write_bytes(b"artifact")
    aid = str(uuid.uuid4())
    with ops.begin() as s:
        s.add(
            ExportArtifactORM(
                artifact_id=aid,
                request_id=rid,
                attempt_id=str(uuid.uuid4()),
                storage_locator=str(path),
                status=status,
                created_at=iso(created),
                available_at=iso(created) if status == "available" else None,
                expires_at=iso(
                    created
                    + (
                        timedelta(days=7)
                        if status == "available"
                        else timedelta(hours=24)
                    )
                ),
            )
        )
    return aid, path


def test_artifact_availability_and_staging_cleanup_boundaries(
    stores: tuple[sessionmaker[Session], sessionmaker[Session]], tmp_path: Path
) -> None:
    content, control = stores
    available, a_path = _artifact(control, tmp_path, status="available", created=T0)
    staging, s_path = _artifact(control, tmp_path, status="staging", created=T0)
    edge = T0 + timedelta(hours=24)
    result = sweep(
        ops=control, content=content, control=control, now=edge - timedelta(seconds=1)
    )
    assert result.staging_removed == 0 and s_path.exists()
    result = sweep(ops=control, content=content, control=control, now=edge)
    assert result.staging_removed == 1 and not s_path.exists()
    week = T0 + timedelta(days=7)
    sweep(
        ops=control, content=content, control=control, now=week - timedelta(seconds=1)
    )
    assert a_path.exists()
    result = sweep(ops=control, content=content, control=control, now=week)
    assert result.artifacts_expired == 1 and not a_path.exists()
    with control() as s:
        row = s.get(ExportArtifactORM, available)
        assert row is not None and row.status == "expired" and row.removed_at


def test_request_records_expire_24_months_after_closure_only(
    stores: tuple[sessionmaker[Session], sessionmaker[Session]],
) -> None:
    content, control = stores
    clock = {"now": T0}
    store = RequestStore(control, now=lambda: clock["now"])
    actor = RequestActor("requester", "p", "remote", str(uuid.uuid4()))
    closed = store.create(
        actor, kind=RequestKind.EXPORT, scope=RequestScope.ACCOUNT, story_refs=[]
    )
    admin = RequestActor("administrator", "owner", "remote")
    store.approve(admin, closed, expected_revision=1, reason=None)
    attempt = store.begin_attempt(admin, closed, expected_revision=2)
    store.end_attempt(closed, attempt, RequestState.COMPLETED)
    still_open = store.create(
        RequestActor("requester", "q", "remote", str(uuid.uuid4())),
        kind=RequestKind.EXPORT,
        scope=RequestScope.ACCOUNT,
        story_refs=[],
    )
    boundary = add_calendar_months(T0, 24)
    sweep(
        ops=control,
        content=content,
        control=control,
        now=boundary - timedelta(seconds=1),
    )
    with control() as s:
        assert s.get(DataRequestORM, closed) is not None
    result = sweep(ops=control, content=content, control=control, now=boundary)
    assert result.requests_expired == 1
    with control() as s:
        assert s.get(DataRequestORM, closed) is None
        assert s.get(DataRequestORM, still_open) is not None
    sweep(
        ops=control,
        content=content,
        control=control,
        now=boundary + timedelta(days=3650),
    )
    with control() as s:
        assert s.get(DataRequestORM, still_open) is not None


def _support_row(op: str, outcome: str, recorded: datetime) -> SupportActionEventORM:
    return SupportActionEventORM(
        event_id=str(uuid.uuid4()),
        schema_version=1,
        operation_id=op,
        subject_ref=str(uuid.uuid4()),
        actor_ref="owner",
        action_code="manual_credit_adjustment",
        target_type="hosted_account",
        target_ref=str(uuid.uuid4()),
        reason_code="administrator",
        requested_at=iso(recorded),
        recorded_at=iso(recorded),
        outcome_code=outcome,
        idempotency_ref="x",
        policy_version="v",
    )


def test_support_operations_expire_after_closure_unresolved_never(
    stores: tuple[sessionmaker[Session], sessionmaker[Session]],
) -> None:
    content, control = stores
    closed, uncertain = str(uuid.uuid4()), str(uuid.uuid4())
    with control.begin() as s:
        s.add(_support_row(closed, "requested", T0))
        s.add(_support_row(closed, "committed", T0))
        s.add(_support_row(uncertain, "requested", T0))
    boundary = add_calendar_months(T0, 24)
    sweep(
        ops=control,
        content=content,
        control=control,
        now=boundary - timedelta(seconds=1),
    )
    with control() as s:
        assert s.scalar(sa.select(sa.func.count(SupportActionEventORM.event_id))) == 3
    sweep(ops=control, content=content, control=control, now=boundary)
    with control() as s:
        left = set(s.scalars(sa.select(SupportActionEventORM.operation_id)))
    assert left == {uncertain}


def test_content_free_refusal_rows_expire_after_30_days(
    stores: tuple[sessionmaker[Session], sessionmaker[Session]],
) -> None:
    content, control = stores
    with content.kw["bind"].begin() as conn:
        for row_id, created in ((1, T0), (2, T0 + timedelta(days=1))):
            conn.execute(
                sa.text(
                    "INSERT INTO provider_refusal_log (id, pass_id,"
                    " primary_provider_name, primary_model_identifier,"
                    " refusal_category, fallback_outcome,"
                    " created_at) VALUES (:i, 'writer', 'x', 'm', 'policy', 'none', :c)"
                ),
                {"i": row_id, "c": created.replace(tzinfo=None)},
            )
    result = sweep(
        ops=control, content=content, control=control, now=T0 + timedelta(days=30)
    )
    assert result.refusal_rows_expired == 1
    with content() as s:
        assert s.scalar(sa.text("SELECT id FROM provider_refusal_log")) == 2


def test_closed_account_ledger_keeps_replay_then_expires_whole_subject(
    stores: tuple[sessionmaker[Session], sessionmaker[Session]],
) -> None:
    content, control = stores
    subject = uuid.uuid4()
    with content() as s:
        service = EntitlementService(s)
        service.receive_entitlement_event(
            subject,
            EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
            HostedAccessActivatedPayload(
                plan=HostedAccessPlan.SUBSCRIPTION, effective_at=T0
            ),
        )
        service.receive_entitlement_event(
            subject,
            EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
            SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("12.5")),
        )
        before = list_events(s, subject, after_sequence=0, limit=50)
        assert replay_check(s, subject).status.value == "consistent"
    with control.begin() as s:
        s.add(
            HostedAccountORM(
                account_id=str(subject),
                identity_subject_ref=str(uuid.uuid4()),
                status="closed",
                created_at=iso(T0),
                updated_at=iso(T0),
                closed_at=iso(T0),
                policy_version="v",
            )
        )
        s.add(
            RightsEvidenceORM(
                rights_id=str(uuid.uuid4()),
                subject_ref=str(subject),
                right_kind="byok_perpetual_license",
                status="active",
                purchased_at=iso(T0),
                source_event_id=str(uuid.uuid4()),
                recorded_at=iso(T0),
                annual_review_at=iso(T0 + timedelta(days=365)),
            )
        )
    boundary = add_calendar_months(T0, 24)
    sweep(
        ops=control,
        content=content,
        control=control,
        now=boundary - timedelta(seconds=1),
    )
    with content() as s:
        # Throughout the retained lifetime: identical, replay-valid history.
        assert list_events(s, subject, after_sequence=0, limit=50) == before
        assert replay_check(s, subject).status.value == "consistent"
    result = sweep(ops=control, content=content, control=control, now=boundary)
    assert result.entitlement_subjects_expired == 1
    with content() as s:
        assert replay_check(s, subject).status.value == "absent"
    with control() as s:
        assert s.get(EntitlementExpiryORM, str(subject)) is not None
        assert s.scalar(sa.select(sa.func.count(RightsEvidenceORM.rights_id))) == 1
    # A restore bringing the events back is expired again before serving.
    with content.kw["bind"].begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO entitlement_event (event_id, sojourner_id, event_type,"
                " payload_json, created_at) VALUES (:e, :s, 'top_up_credit_grant',"
                " '{}', '2026-01-01 00:00:00')"
            ),
            {"e": uuid.uuid4().hex, "s": subject.hex},
        )
    assert reapply_ledger_expiries(control, content) == 1
    with content() as s:
        assert (
            s.scalar(
                sa.select(sa.func.count()).where(
                    EntitlementEvent.sojourner_id == subject
                )
            )
            == 0
        )


def test_suppression_release_requires_verified_end_conditions(
    stores: tuple[sessionmaker[Session], sessionmaker[Session]], tmp_path: Path
) -> None:
    _content, control = stores
    sup = record_suppression(
        control,
        subject_ref=str(uuid.uuid4()),
        story_refs=["s"],
        request_id=str(uuid.uuid4()),
        scope="story",
        effective_boundary_at=T0,
        now=T0,
    )
    backup = register_backup(
        control,
        store_id="x",
        storage_locator=str(tmp_path / "b"),
        original_capture_at=T0 - timedelta(days=1),
    )
    # Annual review is a calendar prompt, not permission to release.
    review = T0 + timedelta(days=366)
    assert sup in reviews_due(control, control, now=review)["suppressions"]
    assert not release_suppression(control, sup, now=review)
    from afterworlds.remote.control_orm import BackupInventoryORM

    with control.begin() as s:
        row = s.get(BackupInventoryORM, backup)
        assert row is not None
        row.disposed_at = iso(T0 + timedelta(days=20))
        row.disposal_evidence = "removed"
    assert not release_suppression(control, sup, now=T0 + timedelta(days=29))
    assert release_suppression(control, sup, now=T0 + timedelta(days=30))
