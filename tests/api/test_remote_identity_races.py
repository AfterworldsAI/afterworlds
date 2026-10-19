"""Prerequisite #205 §1: identity transitions are concurrency-safe.

Real threads on a file-backed control store. A pause point is held open with
an Event while the competing transition runs; bounded joins, no sleeps.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from afterworlds.remote import identity as identity_module
from afterworlds.remote.control_orm import AuthSessionORM
from afterworlds.remote.control_store import open_control_store
from afterworlds.remote.identity import (
    IdentityError,
    IdentityErrorKind,
    IdentityService,
    SessionContext,
)

PASSWORD = "correct horse battery staple"  # pragma: allowlist secret
NEW_PASSWORD = "replacement passphrase one"  # pragma: allowlist secret
OTHER_PASSWORD = "replacement passphrase two"  # pragma: allowlist secret
ADDRESS = "a@example.test"


class _Notices:
    def __init__(self) -> None:
        self.codes: dict[tuple[str, str], str] = {}

    def send(self, *, contact_address: str, kind: str, code: str) -> None:
        self.codes[(contact_address, kind)] = code


@pytest.fixture()
def svc(tmp_path: Path) -> tuple[IdentityService, _Notices]:
    notices = _Notices()
    service = IdentityService(
        open_control_store(f"sqlite:///{tmp_path / 'control.db'}"),
        notices,
        deliver_in_background=False,
    )
    service.register(ADDRESS)
    service.complete_enrollment(
        ADDRESS, notices.codes[(ADDRESS, "enrollment")], PASSWORD
    )
    return service, notices


def _run(fn: Callable[[], Any], results: list[Any]) -> threading.Thread:
    def target() -> None:
        try:
            results.append(fn())
        except IdentityError as exc:
            results.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread


def test_old_password_sign_in_racing_recovery_mints_no_session(
    svc: tuple[IdentityService, _Notices], monkeypatch: pytest.MonkeyPatch
) -> None:
    service, notices = svc
    verified, release = threading.Event(), threading.Event()
    real_verify = identity_module.verify_password

    def paused_verify(password: str, verifier: str | None) -> bool:
        ok = real_verify(password, verifier)
        if password == PASSWORD and threading.current_thread().name == "signin":
            verified.set()
            assert release.wait(10)
        return ok

    monkeypatch.setattr(identity_module, "verify_password", paused_verify)
    results: list[Any] = []
    signin = threading.Thread(
        target=lambda: results.append(
            _catch(lambda: service.sign_in(ADDRESS, PASSWORD, SessionContext.SOJOURNER))
        ),
        name="signin",
        daemon=True,
    )
    signin.start()
    assert verified.wait(10)  # old password proven, session not yet issued
    service.begin_recovery(ADDRESS)
    service.complete_recovery(
        ADDRESS, notices.codes[(ADDRESS, "recovery")], NEW_PASSWORD
    )
    release.set()
    signin.join(10)
    assert not signin.is_alive()
    [outcome] = results
    assert isinstance(outcome, IdentityError)
    assert outcome.kind is IdentityErrorKind.AUTHENTICATION_FAILED
    with service._factory() as s:  # noqa: SLF001
        active = s.query(AuthSessionORM).filter(AuthSessionORM.revoked_at.is_(None))
        assert active.count() == 0


def test_a_recovery_code_is_consumed_exactly_once_under_concurrency(
    svc: tuple[IdentityService, _Notices], monkeypatch: pytest.MonkeyPatch
) -> None:
    service, notices = svc
    service.begin_recovery(ADDRESS)
    code = notices.codes[(ADDRESS, "recovery")]
    consumed, release = threading.Event(), threading.Event()
    real_consume = IdentityService._consume_code

    def paused_consume(*args: Any, **kwargs: Any) -> bool:
        ok = real_consume(*args, **kwargs)
        if threading.current_thread().name == "first":
            consumed.set()
            assert release.wait(10)
        return ok

    monkeypatch.setattr(IdentityService, "_consume_code", staticmethod(paused_consume))
    results: list[Any] = []
    first = threading.Thread(
        target=lambda: results.append(
            _catch(lambda: service.complete_recovery(ADDRESS, code, NEW_PASSWORD))
        ),
        name="first",
        daemon=True,
    )
    first.start()
    assert consumed.wait(10)  # first consumed the code, not yet committed
    second = _run(
        lambda: service.complete_recovery(ADDRESS, code, OTHER_PASSWORD), results
    )
    second.join(1.0)  # blocked on the write lock (or already refused)
    release.set()
    first.join(10)
    second.join(10)
    assert not first.is_alive() and not second.is_alive()
    successes = [r for r in results if not isinstance(r, IdentityError)]
    assert len(successes) == 1
    # Exactly one password took effect, and it was the first one.
    service.sign_in(ADDRESS, NEW_PASSWORD, SessionContext.SOJOURNER)
    with pytest.raises(IdentityError):
        service.sign_in(ADDRESS, OTHER_PASSWORD, SessionContext.SOJOURNER)


def test_concurrent_registration_of_one_address_is_safe(tmp_path: Path) -> None:
    notices = _Notices()
    service = IdentityService(
        open_control_store(f"sqlite:///{tmp_path / 'control.db'}"),
        notices,
        deliver_in_background=False,
    )
    barrier = threading.Barrier(4)
    errors: list[BaseException] = []

    def register() -> None:
        barrier.wait(10)
        try:
            service.register("new@example.test")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=register, daemon=True) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    assert errors == []
    code = notices.codes[("new@example.test", "enrollment")]
    service.complete_enrollment("new@example.test", code, PASSWORD)


def test_a_stale_staff_actor_cannot_act(
    svc: tuple[IdentityService, _Notices], tmp_path: Path
) -> None:
    service, notices = svc
    assert (
        service.bootstrap_owner_administrator(ADDRESS, PASSWORD).value == "provisioned"
    )
    target = service.sign_in(ADDRESS, PASSWORD, SessionContext.SOJOURNER)
    staff = service.sign_in(ADDRESS, PASSWORD, SessionContext.STAFF)
    service.sign_out(staff.token)
    with pytest.raises(IdentityError) as exc:
        service.revoke_account_sessions(staff.actor, target.actor.account_id, "stale")
    assert exc.value.kind is IdentityErrorKind.AUTHENTICATION_REQUIRED
    # The target's session is untouched.
    assert service.resolve(target.token, SessionContext.SOJOURNER).account_id == (
        target.actor.account_id
    )
    assert not service.actor_is_current(staff.actor)


def test_a_forged_actor_cannot_close_an_account(
    svc: tuple[IdentityService, _Notices],
) -> None:
    from dataclasses import replace

    service, _ = svc
    real = service.sign_in(ADDRESS, PASSWORD, SessionContext.SOJOURNER)
    forged = replace(real.actor, session_id="00000000-0000-0000-0000-000000000000")
    with pytest.raises(IdentityError):
        service.close_account(forged, PASSWORD)
    assert service.actor_is_current(real.actor)


def _catch(fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except IdentityError as exc:
        return exc


class _AllNotices:
    """Keeps every notice (a dict would overwrite the earlier code)."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    def send(self, *, contact_address: str, kind: str, code: str) -> None:
        self.sent.append((contact_address, kind, code))


def test_overlapping_recovery_requests_leave_one_open_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review 5574344603 r4316052830: eligibility, supersession and the new
    code are one serialized transition. Two overlapping requests leave one
    open recovery code; the superseded code fails; the survivor works once."""
    import sqlalchemy as sa

    from afterworlds.remote.control_orm import VerificationOperationORM
    from afterworlds.remote.verifiers import token_verifier

    notices = _AllNotices()
    control = open_control_store(f"sqlite:///{tmp_path / 'control.db'}")
    service = IdentityService(control, notices, deliver_in_background=False)
    service.register(ADDRESS)
    service.complete_enrollment(ADDRESS, notices.sent[-1][2], PASSWORD)

    # Each issuance pauses after reading the open codes and before inserting
    # its own until the other arrives (bounded): unserialized issuance
    # interleaves there; serialized issuance cannot, so the wait times out.
    arrived: list[int] = []
    both = threading.Event()
    real_token = identity_module.new_token

    def coordinated_token() -> str:
        arrived.append(1)
        if len(arrived) >= 2:
            both.set()
        both.wait(1.5)
        return real_token()

    monkeypatch.setattr(identity_module, "new_token", coordinated_token)
    results: list[Any] = []
    threads = [_run(lambda: service.begin_recovery(ADDRESS), results) for _ in "ab"]
    for thread in threads:
        thread.join(30)
        assert not thread.is_alive()
    monkeypatch.undo()
    assert results == [None, None]
    codes = [code for _, kind, code in notices.sent if kind == "recovery"]
    assert len(codes) == 2  # both requests issued (and notified) a code

    with control() as s:
        open_ops = s.scalars(
            sa.select(VerificationOperationORM).where(
                VerificationOperationORM.kind == "recovery",
                VerificationOperationORM.used_at.is_(None),
                VerificationOperationORM.revoked_at.is_(None),
            )
        ).all()
    assert len(open_ops) == 1  # serialized: the later issuance superseded
    [survivor] = [c for c in codes if token_verifier(c) == open_ops[0].code_verifier]
    [superseded] = [c for c in codes if c != survivor]

    with pytest.raises(IdentityError):
        service.complete_recovery(ADDRESS, superseded, NEW_PASSWORD)
    service.complete_recovery(ADDRESS, survivor, NEW_PASSWORD)
    for code in (survivor, superseded):  # neither resets again
        with pytest.raises(IdentityError):
            service.complete_recovery(ADDRESS, code, OTHER_PASSWORD)
    service.sign_in(ADDRESS, NEW_PASSWORD, SessionContext.SOJOURNER)
