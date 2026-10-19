"""Remote identity authority -- prerequisite #205 §1 (ADR-021 D2/D3).

Owns hosted accounts, principals, sessions, enrollment verification, recovery,
closure and the sole Owner administrator binding, all in the control store.
Every public method returns or raises typed results; failures that could
reveal whether an address or account exists collapse to one generic kind.

Contexts are distinct: a ``sojourner`` session never resolves as ``staff`` and
vice versa, even for the same principal and browser.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from afterworlds.remote.control_orm import (
    AdminBindingORM,
    AuthSessionORM,
    DeletionSuppressionORM,
    HostedAccountORM,
    IdentityAuditEventORM,
    IdentityPrincipalORM,
    VerificationOperationORM,
)
from afterworlds.remote.control_store import POLICY_VERSION, iso, parse_iso, utc_now
from afterworlds.remote.fence import AccountFence, FenceBusy
from afterworlds.remote.notices import NoticeTransport
from afterworlds.remote.verifiers import (
    hash_password,
    new_token,
    token_verifier,
    verify_password,
)

logger = logging.getLogger("afterworlds.remote.identity")

SOJOURNER_SESSION_LIFETIME = timedelta(hours=24)
STAFF_SESSION_LIFETIME = timedelta(hours=1)
CODE_LIFETIME = timedelta(minutes=15)
CODE_MAX_ATTEMPTS = 5
OWNER_ADMIN_ROLE = "owner_administrator"
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 1024
REASON_MAX_LENGTH = 280
#: Never verifies: a principal enrolled but not yet given a password.
_UNUSABLE_VERIFIER = "!"
_ADDRESS = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}$")


class SessionContext(StrEnum):
    SOJOURNER = "sojourner"
    STAFF = "staff"


class ActorKind(StrEnum):
    LOCAL = "local"
    SOJOURNER = "sojourner"
    STAFF = "staff"


@dataclass(frozen=True)
class Actor:
    """The trusted acting identity for one request, from server state only."""

    kind: ActorKind
    account_id: UUID
    principal_ref: str | None = None
    session_id: str | None = None


class IdentityErrorKind(StrEnum):
    #: Wrong address/password/code, unverified, closed or unknown -- one kind.
    AUTHENTICATION_FAILED = "authentication_failed"
    #: No valid session of the required context.
    AUTHENTICATION_REQUIRED = "authentication_required"
    STAFF_AUTHORITY_REQUIRED = "staff_authority_required"
    INVALID_INPUT = "invalid_input"
    TARGET_NOT_FOUND = "target_not_found"
    BOOTSTRAP_REFUSED = "bootstrap_refused"


class IdentityError(Exception):
    def __init__(self, kind: IdentityErrorKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class AccountRecord:
    account_id: UUID
    status: str
    created_at: datetime
    closed_at: datetime | None


@dataclass(frozen=True)
class SignInResult:
    token: str
    actor: Actor
    expires_at: datetime


class BootstrapOutcome(StrEnum):
    PROVISIONED = "provisioned"
    ALREADY_PROVISIONED = "already_provisioned"


def normalize_address(address: str) -> str:
    normalized = address.strip().lower()
    if len(normalized) > 320 or not _ADDRESS.match(normalized):
        raise IdentityError(IdentityErrorKind.INVALID_INPUT, "Invalid contact address.")
    return normalized


def _check_password(password: str) -> None:
    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        raise IdentityError(
            IdentityErrorKind.INVALID_INPUT,
            f"Password must be {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} characters.",
        )


#: ``actor_ref`` of a receipt whose submitted identity was never proven: an
#: opaque system value, never a principal reference or anything address-derived.
UNAUTHENTICATED_ACTOR = "unauthenticated"


def _withheld(kind: str, reason: str) -> None:
    """A delayed notice that is no longer current is not sent (sanitized)."""
    logger.info(
        "notice withheld: category=notice_withheld reason=%s kind=%s correlation=%s",
        reason,
        kind,
        uuid4().hex,
    )


def _prepare_unsent_code() -> None:
    """The code generation and hashing an issuance does, for a request that
    issues nothing -- so eligible and ineligible requests prepare alike."""
    token_verifier(new_token())


def _failed() -> IdentityError:
    return IdentityError(
        IdentityErrorKind.AUTHENTICATION_FAILED, "Authentication failed."
    )


class IdentityService:
    """The remote identity authority over the control store."""

    def __init__(
        self,
        control_factory: sessionmaker[Session],
        notices: NoticeTransport,
        *,
        now: Callable[[], datetime] = utc_now,
        fence: AccountFence | None = None,
        deliver_in_background: bool = True,
    ) -> None:
        self._factory = control_factory
        self._notices = notices
        #: Notices go out after the committed issuance on this single worker,
        #: off the public response path (#205 §6); None = synchronously.
        self._delivery = (
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="afterworlds-notice")
            if deliver_in_background
            else None
        )
        self._now = now
        #: The process's account fence (ADR-021 D6); closure takes it exclusive.
        self.fence = fence or AccountFence()
        #: Bounded wait for an account's in-flight effects at closure.
        self.close_fence_timeout = 30.0

    # -- enrollment --------------------------------------------------------

    def register(self, contact_address: str) -> None:
        """Start enrollment. Same observable result whether or not the address
        is already enrolled; only an unverified address receives a code."""
        address = normalize_address(contact_address)
        now = self._now()
        with self._locked() as s:
            principal = self._principal_by_address(s, address)
            if principal is not None and principal.address_verified_at is not None:
                _prepare_unsent_code()  # comparable preparation; nothing sent
                return
            if principal is None:
                principal = IdentityPrincipalORM(
                    principal_ref=str(uuid4()),
                    contact_address=address,
                    password_verifier=_UNUSABLE_VERIFIER,
                    created_at=iso(now),
                    updated_at=iso(now),
                )
                s.add(principal)
                s.flush()
            code, operation = self._issue_code(
                s, principal.principal_ref, "enrollment", now
            )
        self._deliver(address, "enrollment", code, operation, None)

    def complete_enrollment(
        self, contact_address: str, code: str, password: str
    ) -> None:
        """Prove the address with its code, set the password, open the account."""
        _check_password(password)
        address = normalize_address(contact_address)
        verifier = hash_password(password)  # outside the write lock
        now = self._now()
        with self._locked() as s:
            principal = self._principal_by_address(s, address)
            if principal is None or principal.address_verified_at is not None:
                raise _failed()
            if not self._consume_code(
                s, principal.principal_ref, "enrollment", code, now
            ):
                s.commit()  # keep the counted attempt
                raise _failed()
            account_id = str(uuid4())
            s.add(
                HostedAccountORM(
                    account_id=account_id,
                    identity_subject_ref=principal.principal_ref,
                    status="active",
                    created_at=iso(now),
                    updated_at=iso(now),
                    policy_version=POLICY_VERSION,
                )
            )
            s.flush()
            principal.account_id = account_id
            principal.password_verifier = verifier
            principal.address_verified_at = iso(now)
            principal.updated_at = iso(now)
            self._audit(
                s,
                actor_ref=principal.principal_ref,
                action_code="account_enrolled",
                target_ref=account_id,
                now=now,
            )

    # -- sessions ----------------------------------------------------------

    def sign_in(
        self, contact_address: str, password: str, context: SessionContext
    ) -> SignInResult:
        """Issue a session for a proven credential.

        scrypt runs outside the write lock against the verifier read first;
        under the lock the verifier must be unchanged, so a sign-in racing a
        completed recovery (or closure) can never mint a usable session."""
        try:
            address = normalize_address(contact_address)
        except IdentityError:
            verify_password(password, None)
            raise _failed() from None
        with self._factory() as s:
            principal = self._principal_by_address(s, address)
            proven = principal.password_verifier if principal else None
        if not verify_password(password, proven) or proven is None:
            raise _failed()
        now = self._now()
        with self._locked() as s:
            principal = self._principal_by_address(s, address)
            if principal is None or principal.password_verifier != proven:
                raise _failed()
            account = self._active_account(s, principal)
            if account is None:
                raise _failed()
            if context is SessionContext.STAFF and not self._has_binding(
                s, principal.principal_ref
            ):
                # The password was right; say only that staff authority is absent.
                raise IdentityError(
                    IdentityErrorKind.STAFF_AUTHORITY_REQUIRED,
                    "Staff authority is required.",
                )
            lifetime = (
                STAFF_SESSION_LIFETIME
                if context is SessionContext.STAFF
                else SOJOURNER_SESSION_LIFETIME
            )
            token = new_token()
            session_id = str(uuid4())
            expires = now + lifetime
            s.add(
                AuthSessionORM(
                    session_id=session_id,
                    principal_ref=principal.principal_ref,
                    account_id=account.account_id,
                    context=context.value,
                    token_verifier=token_verifier(token),
                    issued_at=iso(now),
                    expires_at=iso(expires),
                    status_code="active",
                )
            )
            if context is SessionContext.STAFF:
                self._audit(
                    s,
                    actor_ref=principal.principal_ref,
                    action_code="staff_session_opened",
                    target_ref=session_id,
                    now=now,
                )
            actor = Actor(
                kind=ActorKind(context.value),
                account_id=UUID(account.account_id),
                principal_ref=principal.principal_ref,
                session_id=session_id,
            )
        return SignInResult(token=token, actor=actor, expires_at=expires)

    def resolve(self, token: str | None, context: SessionContext) -> Actor:
        """Resolve a presented session token to its trusted actor, or raise
        ``AUTHENTICATION_REQUIRED``. Rechecks account status and, for staff,
        the active binding on every call."""
        if not token:
            raise self._required()
        now = self._now()
        with self._factory() as s:
            row = s.scalar(
                sa.select(AuthSessionORM).where(
                    AuthSessionORM.token_verifier == token_verifier(token)
                )
            )
            if (
                row is None
                or row.context != context.value
                or row.revoked_at is not None
                or parse_iso(row.expires_at) <= now
            ):
                raise self._required()
            principal = s.get(IdentityPrincipalORM, row.principal_ref)
            if principal is None or self._active_account(s, principal) is None:
                raise self._required()
            if context is SessionContext.STAFF and not self._has_binding(
                s, row.principal_ref
            ):
                raise self._required()
            return Actor(
                kind=ActorKind(context.value),
                account_id=UUID(row.account_id),
                principal_ref=row.principal_ref,
                session_id=row.session_id,
            )

    def sign_out(self, token: str | None) -> None:
        """Revoke the presented session; unknown tokens are a quiet no-op."""
        if not token:
            return
        now = self._now()
        with self._factory.begin() as s:
            row = s.scalar(
                sa.select(AuthSessionORM).where(
                    AuthSessionORM.token_verifier == token_verifier(token)
                )
            )
            if row is not None and row.revoked_at is None:
                row.revoked_at = iso(now)
                row.status_code = "signed_out"

    # -- recovery and closure ----------------------------------------------

    def begin_recovery(self, contact_address: str) -> None:
        """Send a recovery code to a verified, active address; otherwise do
        nothing. The caller's observable result is the same either way."""
        try:
            address = normalize_address(contact_address)
        except IdentityError:
            return
        now = self._now()
        # Eligibility, supersession of every open code and the new code are
        # one serialized transition: overlapping requests leave one open code.
        with self._locked() as s:
            principal = s.scalar(
                sa.select(IdentityPrincipalORM).where(
                    IdentityPrincipalORM.contact_address == address
                )
            )
            if principal is None or self._active_account(s, principal) is None:
                _prepare_unsent_code()  # comparable preparation; nothing sent
                return
            account_id = principal.account_id
            code, operation = self._issue_code(
                s, principal.principal_ref, "recovery", now
            )
        self._deliver(address, "recovery", code, operation, account_id)

    def complete_recovery(
        self, contact_address: str, code: str, new_password: str
    ) -> None:
        """Set a new password after proving the address; revoke every session.

        Never touches ownership, provenance, closure or the administrator
        binding, and refuses a closed account. Code consumption, the verifier
        change and revocation happen under one write lock, so a code is
        consumed once and no session issued before it survives."""
        _check_password(new_password)
        address = normalize_address(contact_address)
        verifier = hash_password(new_password)  # outside the write lock
        now = self._now()
        with self._locked() as s:
            principal = self._principal_by_address(s, address)
            if principal is None or self._active_account(s, principal) is None:
                raise _failed()
            if not self._consume_code(
                s, principal.principal_ref, "recovery", code, now
            ):
                s.commit()  # keep the counted attempt
                raise _failed()
            principal.password_verifier = verifier
            principal.updated_at = iso(now)
            revoked = self._revoke_principal_sessions(
                s, principal.principal_ref, now, "recovered"
            )
            self._audit(
                s,
                actor_ref=principal.principal_ref,
                action_code="account_recovered",
                target_ref=principal.account_id,
                reason_code=f"sessions_revoked_{revoked}",
                now=now,
            )

    def close_account(self, actor: Actor, password: str) -> None:
        """Self-service closure: re-authenticate, close, revoke every session.

        Holds the account's fence exclusive, whoever calls it: it waits
        (bounded) for every admitted request or scoped service call of the
        account, so none of their effects lands after closure returns; on
        timeout it raises :class:`FenceBusy` and changes nothing. The Actor is
        revalidated against the store under the write lock; a stale or forged
        Actor is refused."""
        self._require_kind(actor, ActorKind.SOJOURNER)
        with self._factory() as s:
            principal = s.get(IdentityPrincipalORM, actor.principal_ref)
            proven = principal.password_verifier if principal else None
        if not verify_password(password, proven) or proven is None:
            raise _failed()
        with self.fence.exclusive(actor.account_id, timeout=self.close_fence_timeout):
            self._close(actor, proven)

    def _close(self, actor: Actor, proven: str) -> None:
        now = self._now()
        with self._locked() as s:
            principal = self._require_current(s, actor, SessionContext.SOJOURNER)
            if principal.password_verifier != proven:
                raise _failed()
            account = self._active_account(s, principal)
            assert account is not None  # _require_current checked it
            account.status = "closed"
            account.closed_at = iso(now)
            account.updated_at = iso(now)
            self._revoke_principal_sessions(
                s, principal.principal_ref, now, "account_closed"
            )
            self._audit(
                s,
                actor_ref=principal.principal_ref,
                action_code="account_closed",
                target_ref=account.account_id,
                now=now,
            )

    # -- administration ----------------------------------------------------

    def revoke_account_sessions(
        self, actor: Actor, target_account_id: UUID, reason_text: str
    ) -> int:
        """Staff action: revoke every session of the targeted hosted account.

        The staff Actor is revalidated (session current, binding active)
        under the same write lock as the effect."""
        self._require_kind(actor, ActorKind.STAFF)
        reason = reason_text.strip()
        if not reason or len(reason) > REASON_MAX_LENGTH:
            raise IdentityError(
                IdentityErrorKind.INVALID_INPUT,
                f"A reason of 1-{REASON_MAX_LENGTH} characters is required.",
            )
        now = self._now()
        with self._locked() as s:
            staff = self._require_current(s, actor, SessionContext.STAFF)
            account = s.get(HostedAccountORM, str(target_account_id))
            if account is None:
                raise IdentityError(
                    IdentityErrorKind.TARGET_NOT_FOUND, "Account not found."
                )
            revoked = self._revoke_principal_sessions(
                s, account.identity_subject_ref, now, "revoked_by_administrator"
            )
            self._audit(
                s,
                actor_ref=staff.principal_ref,
                action_code="account_sessions_revoked",
                target_ref=account.account_id,
                reason_code="administrator",
                reason_text=reason,
                now=now,
            )
        return revoked

    def actor_is_current(self, actor: Actor) -> bool:
        """Whether *actor*'s session is still current right now (not revoked
        or expired, account active, staff binding active for staff)."""
        context = (
            SessionContext.STAFF
            if actor.kind is ActorKind.STAFF
            else SessionContext.SOJOURNER
        )
        with self._factory() as s:
            try:
                self._require_current(s, actor, context)
            except IdentityError:
                return False
        return True

    def get_account(self, account_id: UUID) -> AccountRecord | None:
        with self._factory() as s:
            row = s.get(HostedAccountORM, str(account_id))
            if row is None:
                return None
            return AccountRecord(
                account_id=UUID(row.account_id),
                status=row.status,
                created_at=parse_iso(row.created_at),
                closed_at=parse_iso(row.closed_at) if row.closed_at else None,
            )

    def active_account_ids(self, account_ids: set[str]) -> set[str]:
        """The subset of *account_ids* that are currently active."""
        if not account_ids:
            return set()
        with self._factory() as s:
            return set(
                s.scalars(
                    sa.select(HostedAccountORM.account_id).where(
                        HostedAccountORM.account_id.in_(account_ids),
                        HostedAccountORM.status == "active",
                    )
                )
            )

    def contact_address_for(self, actor: Actor) -> str | None:
        with self._factory() as s:
            principal = s.get(IdentityPrincipalORM, actor.principal_ref)
            return principal.contact_address if principal else None

    def bootstrap_owner_administrator(
        self, contact_address: str, password: str
    ) -> BootstrapOutcome:
        """Server-side, operator-run provisioning of the sole Owner administrator.

        The principal must re-authenticate and have a verified address and an
        active account. Idempotent for that principal; refuses any other while
        an active binding exists. No HTTP route reaches this method.

        Every attempt leaves a committed receipt. A refusal before the
        submitted identity is proven is recorded as ``UNAUTHENTICATED_ACTOR``
        with a reason code only -- never the address or any credential -- and
        committed before the typed refusal is raised; if the receipt cannot be
        committed the store error propagates instead, and nothing is granted.
        """
        now = self._now()
        try:
            address = normalize_address(contact_address)
        except IdentityError:
            self._refuse_bootstrap(now, "invalid_input")
            raise
        with self._locked() as s:
            principal = s.scalar(
                sa.select(IdentityPrincipalORM).where(
                    IdentityPrincipalORM.contact_address == address
                )
            )
            verifier = principal.password_verifier if principal else None
            if (
                not verify_password(password, verifier)
                or principal is None
                or self._active_account(s, principal) is None
            ):
                self._audit_unauthenticated_bootstrap(s, now, "authentication_failed")
                s.commit()
                raise _failed()
            existing = s.scalar(
                sa.select(AdminBindingORM).where(
                    AdminBindingORM.role_code == OWNER_ADMIN_ROLE,
                    AdminBindingORM.revoked_at.is_(None),
                )
            )
            operation = str(uuid4())
            if existing is not None:
                same = existing.principal_ref == principal.principal_ref
                self._audit(
                    s,
                    actor_ref=principal.principal_ref,
                    action_code="owner_admin_bootstrap",
                    target_ref=existing.binding_id,
                    outcome_code="already_provisioned" if same else "refused",
                    operation_id=operation,
                    now=now,
                )
                s.commit()
                if same:
                    return BootstrapOutcome.ALREADY_PROVISIONED
                raise IdentityError(
                    IdentityErrorKind.BOOTSTRAP_REFUSED,
                    "An Owner administrator is already provisioned.",
                )
            binding_id = str(uuid4())
            s.add(
                AdminBindingORM(
                    binding_id=binding_id,
                    principal_ref=principal.principal_ref,
                    role_code=OWNER_ADMIN_ROLE,
                    provisioned_at=iso(now),
                    provisioning_operation_ref=operation,
                    policy_version=POLICY_VERSION,
                )
            )
            self._audit(
                s,
                actor_ref=principal.principal_ref,
                action_code="owner_admin_bootstrap",
                target_ref=binding_id,
                outcome_code="provisioned",
                operation_id=operation,
                now=now,
            )
            s.commit()
        return BootstrapOutcome.PROVISIONED

    # -- internals ---------------------------------------------------------

    def drain_notices(self, timeout: float = 30.0) -> None:
        """Wait until every notice handed off so far has been attempted."""
        if self._delivery is not None:
            self._delivery.submit(lambda: None).result(timeout)

    def _deliver(
        self,
        address: str,
        kind: str,
        code: str,
        operation_id: str,
        account_id: str | None,
    ) -> None:
        """Hand a committed code to the notice transport -- in the background,
        so the public answer never waits on (or reveals) delivery. The job
        carries its trusted scope (operation, account) and rechecks it when it
        runs."""
        if self._delivery is None:
            self._send(address, kind, code)
            return
        try:
            self._delivery.submit(
                self._send_in_background,
                address,
                kind,
                code,
                operation_id,
                account_id,
            )
        except RuntimeError as exc:
            # The runner refused the handoff (shut down, or no thread could
            # start -- CPython may already have queued the item). The code is
            # committed either way; the request answers like any other and the
            # operator sees a distinct category, without the notice.
            logger.error(
                "notice delivery failed: category=notice_handoff_failed type=%s "
                "kind=%s delivery=uncertain correlation=%s",
                type(exc).__name__,
                kind,
                uuid4().hex,
            )

    def _send_in_background(
        self,
        address: str,
        kind: str,
        code: str,
        operation_id: str,
        account_id: str | None,
    ) -> None:
        """The delayed notice effect (#205 §5): it holds the account's fence
        for the whole effect -- so a closure or deletion suppression that has
        completed can never be followed by it -- and sends only if its
        operation and account are still current."""
        release = None
        try:
            if account_id is not None:
                try:
                    release = self.fence.lease(UUID(account_id))
                except FenceBusy:
                    _withheld(kind, "account_operation_in_progress")
                    return
            if not self._notice_still_current(operation_id, kind, account_id):
                _withheld(kind, "no_longer_current")
                return
            self._send(address, kind, code)
        except Exception as exc:
            # No request is left to fail: an unexpected runner error is
            # recorded under its own category (type only -- its text may carry
            # the notice) rather than lost.
            logger.error(
                "notice delivery failed: category=notice_runner_error type=%s "
                "kind=%s correlation=%s",
                type(exc).__name__,
                kind,
                uuid4().hex,
            )
        finally:
            if release is not None:
                release()

    def _notice_still_current(
        self, operation_id: str, kind: str, account_id: str | None
    ) -> bool:
        """The issued code is still open and its recipient still eligible:
        enrollment for a still-unverified principal; recovery for the same,
        still-active account with no account-scope deletion suppression."""
        with self._factory() as s:
            op = s.get(VerificationOperationORM, operation_id)
            if (
                op is None
                or op.used_at is not None
                or op.revoked_at is not None
                or parse_iso(op.expires_at) <= self._now()
            ):
                return False
            principal = s.get(IdentityPrincipalORM, op.principal_ref)
            if principal is None:
                return False
            if kind == "enrollment":
                return principal.address_verified_at is None
            account = self._active_account(s, principal)
            if account is None or account.account_id != account_id:
                return False
            suppressed = s.scalar(
                sa.select(DeletionSuppressionORM.suppression_id).where(
                    DeletionSuppressionORM.status == "active",
                    DeletionSuppressionORM.scope == "account",
                    DeletionSuppressionORM.subject_ref == account_id,
                )
            )
            return suppressed is None

    def _send(self, address: str, kind: str, code: str) -> None:
        """An expected delivery failure (the outbox cannot be written) is
        recorded for the operator with a fixed category and an opaque
        correlation id only -- never the address, code or exception text; the
        request answered the same ``accepted`` as for an ineligible address
        (#205 §6), and the code stays issued and simply expires."""
        try:
            self._notices.send(contact_address=address, kind=kind, code=code)
        except OSError:
            logger.error(
                "notice delivery failed: category=notice_outbox_unwritable "
                "kind=%s correlation=%s",
                kind,
                uuid4().hex,
            )

    def _refuse_bootstrap(self, now: datetime, reason_code: str) -> None:
        with self._locked() as s:
            self._audit_unauthenticated_bootstrap(s, now, reason_code)

    @classmethod
    def _audit_unauthenticated_bootstrap(
        cls, s: Session, now: datetime, reason_code: str
    ) -> None:
        cls._audit(
            s,
            actor_ref=UNAUTHENTICATED_ACTOR,
            action_code="owner_admin_bootstrap",
            reason_code=reason_code,
            outcome_code="refused",
            now=now,
        )

    @contextmanager
    def _locked(self) -> Iterator[Session]:
        """A control-store transaction holding SQLite's write lock from its
        first read, so a decision and its effect cannot interleave with
        another identity transition. Commits on normal exit."""
        with self._factory() as s:
            s.connection().exec_driver_sql("BEGIN IMMEDIATE")
            yield s
            s.commit()

    @staticmethod
    def _principal_by_address(s: Session, address: str) -> IdentityPrincipalORM | None:
        return s.scalar(
            sa.select(IdentityPrincipalORM).where(
                IdentityPrincipalORM.contact_address == address
            )
        )

    def _require_current(
        self, s: Session, actor: Actor, context: SessionContext
    ) -> IdentityPrincipalORM:
        """Revalidate *actor* against stored state; never trust its fields."""
        row = s.get(AuthSessionORM, actor.session_id) if actor.session_id else None
        if (
            row is None
            or row.context != context.value
            or row.principal_ref != actor.principal_ref
            or row.account_id != str(actor.account_id)
            or row.revoked_at is not None
            or parse_iso(row.expires_at) <= self._now()
        ):
            raise self._required()
        principal = s.get(IdentityPrincipalORM, row.principal_ref)
        if principal is None or self._active_account(s, principal) is None:
            raise self._required()
        if context is SessionContext.STAFF and not self._has_binding(
            s, row.principal_ref
        ):
            raise IdentityError(
                IdentityErrorKind.STAFF_AUTHORITY_REQUIRED,
                "Staff authority is required.",
            )
        return principal

    @staticmethod
    def _required() -> IdentityError:
        return IdentityError(
            IdentityErrorKind.AUTHENTICATION_REQUIRED, "Authentication required."
        )

    @staticmethod
    def _require_kind(actor: Actor, kind: ActorKind) -> None:
        if actor.kind is not kind or actor.principal_ref is None:
            raise IdentityError(
                (
                    IdentityErrorKind.STAFF_AUTHORITY_REQUIRED
                    if kind is ActorKind.STAFF
                    else IdentityErrorKind.AUTHENTICATION_REQUIRED
                ),
                "This action requires a different session context.",
            )

    @staticmethod
    def _active_account(
        s: Session, principal: IdentityPrincipalORM
    ) -> HostedAccountORM | None:
        if principal.account_id is None or principal.address_verified_at is None:
            return None
        account = s.get(HostedAccountORM, principal.account_id)
        return account if account is not None and account.status == "active" else None

    @staticmethod
    def _has_binding(s: Session, principal_ref: str) -> bool:
        return (
            s.scalar(
                sa.select(AdminBindingORM.binding_id).where(
                    AdminBindingORM.principal_ref == principal_ref,
                    AdminBindingORM.role_code == OWNER_ADMIN_ROLE,
                    AdminBindingORM.revoked_at.is_(None),
                )
            )
            is not None
        )

    def _issue_code(
        self, s: Session, principal_ref: str, kind: str, now: datetime
    ) -> tuple[str, str]:
        """Issue a code (returned with its operation id)."""
        # A new code supersedes every earlier open one of the same kind.
        for op in s.scalars(
            sa.select(VerificationOperationORM).where(
                VerificationOperationORM.principal_ref == principal_ref,
                VerificationOperationORM.kind == kind,
                VerificationOperationORM.used_at.is_(None),
                VerificationOperationORM.revoked_at.is_(None),
            )
        ):
            op.revoked_at = iso(now)
        code = new_token()
        operation_id = str(uuid4())
        s.add(
            VerificationOperationORM(
                operation_id=operation_id,
                principal_ref=principal_ref,
                kind=kind,
                code_verifier=token_verifier(code),
                issued_at=iso(now),
                expires_at=iso(now + CODE_LIFETIME),
                attempts=0,
            )
        )
        return code, operation_id

    @staticmethod
    def _consume_code(
        s: Session, principal_ref: str, kind: str, code: str, now: datetime
    ) -> bool:
        op = s.scalar(
            sa.select(VerificationOperationORM).where(
                VerificationOperationORM.principal_ref == principal_ref,
                VerificationOperationORM.kind == kind,
                VerificationOperationORM.used_at.is_(None),
                VerificationOperationORM.revoked_at.is_(None),
            )
        )
        if op is None or parse_iso(op.expires_at) <= now:
            return False
        op.attempts += 1
        if op.attempts > CODE_MAX_ATTEMPTS:
            op.revoked_at = iso(now)
            return False
        if op.code_verifier != token_verifier(code):
            return False
        op.used_at = iso(now)
        return True

    @staticmethod
    def _revoke_principal_sessions(
        s: Session, principal_ref: str, now: datetime, status: str
    ) -> int:
        rows = list(
            s.scalars(
                sa.select(AuthSessionORM).where(
                    AuthSessionORM.principal_ref == principal_ref,
                    AuthSessionORM.revoked_at.is_(None),
                )
            )
        )
        for row in rows:
            row.revoked_at = iso(now)
            row.status_code = status
        return len(rows)

    @staticmethod
    def _audit(
        s: Session,
        *,
        actor_ref: str,
        action_code: str,
        now: datetime,
        target_ref: str | None = None,
        reason_code: str | None = None,
        reason_text: str | None = None,
        outcome_code: str = "succeeded",
        operation_id: str | None = None,
    ) -> None:
        s.add(
            IdentityAuditEventORM(
                event_id=str(uuid4()),
                operation_id=operation_id or str(uuid4()),
                actor_ref=actor_ref,
                action_code=action_code,
                target_ref=target_ref,
                reason_code=reason_code,
                reason_text=reason_text,
                outcome_code=outcome_code,
                recorded_at=iso(now),
                policy_version=POLICY_VERSION,
            )
        )
