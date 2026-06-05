"""EntitlementService — CRD Issue 13.

THE ONLY APPROVED MUTATION PATH for ``RuntimeEntitlementState`` is
``receive_entitlement_event``.  No shortcut writes.  All fixtures seed state via
this method.

``EntitlementEvent`` is append-only; corrections are new events.

``settle_hosted_turn_cost`` is idempotent on ``turn_id``: same turn + same amounts
returns the existing event; same turn + different amounts raises
``EntitlementSettlementConflictError``.

Race-safe duplicate handling: on ``IntegrityError``, call ``session.rollback()``
before any further queries, then refetch and compare.

``effective_at`` fields in payloads are metadata; they do not affect replay order.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from afterworlds.entitlement.enums import (
    EntitlementEventType,
    HostedUnavailableReason,
    RuntimeAccessPath,
)
from afterworlds.entitlement.errors import (
    EntitlementIdempotencyConflictError,
    EntitlementPayloadVersionError,
    EntitlementSettlementConflictError,
    EntitlementSettlementError,
)
from afterworlds.entitlement.models import AccessPathStatus
from afterworlds.entitlement.orm import EntitlementEvent, RuntimeEntitlementState
from afterworlds.entitlement.payloads import (
    ENTITLEMENT_PAYLOAD_CLASS_MAP,
    ByokLicenseActivatedPayload,
    CloudServicesActivatedPayload,
    CloudServicesLapsedPayload,
    CreditDeductionPayload,
    EntitlementEventPayload,
    HostedAccessActivatedPayload,
    HostedAccessDeactivatedPayload,
    ManualCreditAdjustmentPayload,
    SubscriptionCreditGrantPayload,
    TopUpCreditGrantPayload,
)
from afterworlds.entitlement.policy import TurnCostPolicy

# Event types that require hosted_access_plan to be set (i.e. hosted access
# must have been activated at least once before these events are accepted).
_CREDIT_MUTATION_EVENT_TYPES: frozenset[EntitlementEventType] = frozenset(
    {
        EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
        EntitlementEventType.TOP_UP_CREDIT_GRANT,
        EntitlementEventType.CREDIT_DEDUCTION,
        EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT,
    }
)


class EntitlementService:
    """Runtime entitlement state and enforcement service."""

    def __init__(
        self,
        session: Session,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._session = session
        self._clock: Callable[[], datetime] = (
            clock if clock is not None else datetime.utcnow
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_access_path_status(self, sojourner_id: UUID) -> AccessPathStatus:
        """Return the current access path status for a Sojourner.

        Returns a fully-false no-access status for an absent Sojourner; does
        NOT create a row.  Applies Owner Decision #5 for cloud_services_active.
        """
        state = self._session.get(RuntimeEntitlementState, sojourner_id)
        now = self._clock()
        return _build_access_path_status(sojourner_id, state, now)

    def check_hosted_turn_allowed(self, sojourner_id: UUID) -> bool:
        """Return True iff hosted_access_active=True AND total credits > 0."""
        state = self._session.get(RuntimeEntitlementState, sojourner_id)
        if state is None or not state.hosted_access_active:
            return False
        total = state.hosted_credit_balance + state.top_up_credit_balance
        return total > 0

    # ------------------------------------------------------------------
    # Settlement
    # ------------------------------------------------------------------

    def settle_hosted_turn_cost(
        self,
        sojourner_id: UUID,
        result: object,
        *,
        policy: TurnCostPolicy,
        access_path: RuntimeAccessPath,
    ) -> EntitlementEvent | None:
        """Deduct hosted credits for a DELIVERED or OOC_HANDLED turn.

        Raises ``EntitlementSettlementError`` immediately if
        ``access_path != HOSTED``.  Returns None for all dispositions except
        DELIVERED and OOC_HANDLED.

        For DELIVERED/OOC_HANDLED:
        - Raises ``EntitlementSettlementError`` if ``result.turn_id`` is None.
        - Computes deduction via policy; delegates write to
          ``receive_entitlement_event``.
        - Never mutates ``RuntimeEntitlementState`` directly.

        Idempotency on turn_id:
        - Existing event, matching payload → return existing event (silent).
        - Existing event, different amounts → raise
          ``EntitlementSettlementConflictError``.

        Hosted access state changes between preflight and settlement do not block
        settlement; balance may go negative (Owner Decision #3).
        """
        from afterworlds.pipeline.orchestrator.models import (  # noqa: PLC0415
            OrchestrationResult,
            PipelineDisposition,
        )

        if access_path != RuntimeAccessPath.HOSTED:
            raise EntitlementSettlementError(
                "settle_hosted_turn_cost requires HOSTED access path;"
                f" got {access_path!r}"
            )

        if not isinstance(result, OrchestrationResult):
            raise EntitlementSettlementError("result must be an OrchestrationResult")

        disposition = result.disposition

        if disposition not in (
            PipelineDisposition.DELIVERED,
            PipelineDisposition.OOC_HANDLED,
        ):
            return None

        if result.turn_id is None:
            raise EntitlementSettlementError(
                "DELIVERED/OOC_HANDLED result has turn_id=None; cannot settle"
            )

        turn_id = result.turn_id
        snapshots = TurnCostPolicy.extract_snapshots(result)
        total_deduction = policy.compute_deduction(snapshots)

        # Check for existing settlement on this turn_id (idempotency / conflict).
        existing = self._find_credit_deduction_for_turn(sojourner_id, turn_id)
        if existing is not None:
            existing_payload = _deserialize_payload(
                existing, EntitlementEventType.CREDIT_DEDUCTION
            )
            assert isinstance(existing_payload, CreditDeductionPayload)
            state = self._session.get(RuntimeEntitlementState, sojourner_id)
            if state is None:
                raise EntitlementSettlementError(
                    f"RuntimeEntitlementState absent for sojourner_id={sojourner_id} "
                    "during settlement idempotency check"
                )
            existing_total = abs(existing_payload.hosted_credit_delta) + abs(
                existing_payload.top_up_credit_delta
            )
            if existing_total != total_deduction:
                raise EntitlementSettlementConflictError(
                    f"turn_id={turn_id} already settled with deduction "
                    f"{existing_total!r}; new computation yields {total_deduction!r}"
                )
            return existing

        # Compute pool split from current balances.
        state = self._session.get(RuntimeEntitlementState, sojourner_id)
        if state is None:
            raise EntitlementSettlementError(
                f"RuntimeEntitlementState absent for sojourner_id={sojourner_id}; "
                "cannot settle without a prior entitlement event"
            )

        hosted_delta, top_up_delta = TurnCostPolicy.compute_pool_split(
            total_deduction,
            state.hosted_credit_balance,
            state.top_up_credit_balance,
        )

        payload = CreditDeductionPayload(
            hosted_credit_delta=hosted_delta,
            top_up_credit_delta=top_up_delta,
        )
        return self.receive_entitlement_event(
            sojourner_id=sojourner_id,
            event_type=EntitlementEventType.CREDIT_DEDUCTION,
            payload=payload,
            turn_id=turn_id,
        )

    # ------------------------------------------------------------------
    # Mutation — THE ONLY APPROVED PATH
    # ------------------------------------------------------------------

    def receive_entitlement_event(
        self,
        sojourner_id: UUID,
        event_type: EntitlementEventType,
        payload: EntitlementEventPayload,
        *,
        turn_id: UUID | None = None,
        idempotency_key: str | None = None,
    ) -> EntitlementEvent:
        """Append an entitlement event and apply its state effects atomically.

        THE ONLY APPROVED MUTATION PATH for ``RuntimeEntitlementState``.

        Precondition checks:
          Credit mutation events (SUBSCRIPTION_CREDIT_GRANT, TOP_UP_CREDIT_GRANT,
          CREDIT_DEDUCTION, MANUAL_CREDIT_ADJUSTMENT) raise
          ``EntitlementSettlementError`` if ``hosted_access_plan is None`` (hosted
          access has never been activated for this Sojourner).
          CREDIT_DEDUCTION additionally raises ``EntitlementSettlementError`` if
          ``turn_id is None`` — a NULL turn_id bypasses the DB partial-unique
          constraint that enforces one settlement per turn.

        Payload type check:
          payload class must match event_type via ENTITLEMENT_PAYLOAD_CLASS_MAP;
          raises ``EntitlementSettlementError`` if not.

        Idempotency key check (when idempotency_key is not None):
          No existing row → proceed normally.
          Existing row, same sojourner_id + event_type + turn_id + canonical
            payload fields → return existing event; do NOT re-apply state mutation.
          Existing row, any mismatch → raise
            ``EntitlementIdempotencyConflictError``.

        Race-safe duplicate handling:
          On IntegrityError: rollback, refetch, compare, return or raise.

        Happy path:
          1. Creates RuntimeEntitlementState row if absent (transactionally).
          2. Appends EntitlementEvent; global_sequence assigned by SQLite.
          3. Applies event application rules to RuntimeEntitlementState.
          4. Updates last_entitlement_event_id and updated_at.
          5. All in one transaction.
        """
        # 1. Payload type check (early, before any DB work).
        expected_class = ENTITLEMENT_PAYLOAD_CLASS_MAP.get(event_type)
        if expected_class is None or not isinstance(payload, expected_class):
            raise EntitlementSettlementError(
                f"payload class {type(payload).__name__!r} does not match "
                f"event_type {event_type!r}"
            )

        # 2. Read existing state for precondition check.
        current_state = self._session.get(RuntimeEntitlementState, sojourner_id)

        # 3. Precondition: credit mutation events require hosted access to have
        #    been activated at least once.
        if event_type in _CREDIT_MUTATION_EVENT_TYPES and (
            current_state is None or current_state.hosted_access_plan is None
        ):
            raise EntitlementSettlementError(
                f"event_type={event_type!r} requires hosted_access_plan to be "
                "set (hosted access must have been activated at least once); "
                f"sojourner_id={sojourner_id}"
            )

        # 3b. Precondition: CREDIT_DEDUCTION must carry a turn_id.  A NULL
        #     turn_id means the DB partial-unique index cannot enforce
        #     per-turn deduplication, creating a silent duplicate-settle risk.
        if event_type == EntitlementEventType.CREDIT_DEDUCTION and turn_id is None:
            raise EntitlementSettlementError(
                "CREDIT_DEDUCTION requires turn_id; turn_id=None is not permitted"
            )

        # 4. Idempotency pre-check.
        if idempotency_key is not None:
            existing_by_key = self._find_by_idempotency_key(idempotency_key)
            if existing_by_key is not None:
                _check_idempotency_match(
                    existing_by_key,
                    sojourner_id,
                    event_type,
                    turn_id,
                    payload,
                )
                return existing_by_key

        # 5. Insert attempt with race-safe IntegrityError handling.
        now = self._clock()
        try:
            if current_state is None:
                current_state = RuntimeEntitlementState(
                    sojourner_id=sojourner_id,
                    created_at=now,
                    updated_at=now,
                )
                self._session.add(current_state)

            new_event = EntitlementEvent(
                event_id=uuid4(),
                sojourner_id=sojourner_id,
                event_type=event_type,
                turn_id=turn_id,
                idempotency_key=idempotency_key,
                payload_json=payload.model_dump_json(),
                created_at=now,
            )
            self._session.add(new_event)

            _apply_event_application_rules(current_state, event_type, payload)
            current_state.last_entitlement_event_id = new_event.event_id
            current_state.updated_at = now

            self._session.commit()
            return new_event

        except IntegrityError:
            # IMPORTANT: rollback before any further queries — SQLAlchemy leaves
            # the session in an invalid state after an unhandled IntegrityError.
            self._session.rollback()

            # Refetch to determine idempotency or conflict.
            if idempotency_key is not None:
                refetched = self._find_by_idempotency_key(idempotency_key)
                if refetched is not None:
                    _check_idempotency_match(
                        refetched, sojourner_id, event_type, turn_id, payload
                    )
                    return refetched

            if turn_id is not None:
                refetched_by_turn = self._find_by_turn_event_type(
                    sojourner_id, turn_id, event_type
                )
                if refetched_by_turn is not None:
                    _check_idempotency_match(
                        refetched_by_turn, sojourner_id, event_type, turn_id, payload
                    )
                    return refetched_by_turn

            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_by_idempotency_key(self, idempotency_key: str) -> EntitlementEvent | None:
        stmt = select(EntitlementEvent).where(
            EntitlementEvent.idempotency_key == idempotency_key
        )
        return self._session.scalars(stmt).first()

    def _find_credit_deduction_for_turn(
        self, sojourner_id: UUID, turn_id: UUID
    ) -> EntitlementEvent | None:
        return self._find_by_turn_event_type(
            sojourner_id, turn_id, EntitlementEventType.CREDIT_DEDUCTION
        )

    def _find_by_turn_event_type(
        self,
        sojourner_id: UUID,
        turn_id: UUID,
        event_type: EntitlementEventType,
    ) -> EntitlementEvent | None:
        stmt = select(EntitlementEvent).where(
            EntitlementEvent.sojourner_id == sojourner_id,
            EntitlementEvent.turn_id == turn_id,
            EntitlementEvent.event_type == event_type,
        )
        return self._session.scalars(stmt).first()


# ------------------------------------------------------------------
# Module-level helpers (not public API)
# ------------------------------------------------------------------


def _build_access_path_status(
    sojourner_id: UUID,
    state: RuntimeEntitlementState | None,
    now: datetime,
) -> AccessPathStatus:
    """Build AccessPathStatus from a (possibly absent) state row."""
    if state is None:
        return AccessPathStatus(
            sojourner_id=sojourner_id,
            hosted_turn_available=False,
            byok_turn_available=False,
            cloud_services_active=False,
            hosted_credit_balance=None,
            top_up_credit_balance=None,
            total_hosted_credit_balance=None,
            hosted_unavailable_reason=HostedUnavailableReason.NO_SUBSCRIPTION,
        )

    # Hosted availability.
    hosted_available: bool
    unavailable_reason: HostedUnavailableReason | None = None
    cloud_services_lapsed: bool = False

    if state.hosted_access_plan is None:
        # Never activated.
        hosted_available = False
        unavailable_reason = HostedUnavailableReason.NO_SUBSCRIPTION
        hosted_credit: Decimal | None = None
        top_up_credit: Decimal | None = None
        total_credit: Decimal | None = None
    else:
        hosted_credit = state.hosted_credit_balance
        top_up_credit = state.top_up_credit_balance
        total_credit = hosted_credit + top_up_credit

        if not state.hosted_access_active:
            hosted_available = False
            unavailable_reason = HostedUnavailableReason.SUBSCRIPTION_INACTIVE
        elif total_credit <= 0:
            hosted_available = False
            unavailable_reason = HostedUnavailableReason.CREDITS_EXHAUSTED
        else:
            hosted_available = True

    # Cloud Services: Owner Decision #5.
    cloud_effective = (
        state.cloud_services_active
        and state.cloud_services_expires_at is not None
        and state.cloud_services_expires_at > now
    )
    if state.cloud_services_active and not cloud_effective:
        cloud_services_lapsed = True

    # BYOK availability: independent of Cloud Services.
    byok_available = state.byok_license_active

    return AccessPathStatus(
        sojourner_id=sojourner_id,
        hosted_turn_available=hosted_available,
        byok_turn_available=byok_available,
        cloud_services_active=cloud_effective,
        hosted_credit_balance=hosted_credit,
        top_up_credit_balance=top_up_credit,
        total_hosted_credit_balance=total_credit,
        hosted_unavailable_reason=unavailable_reason,
        cloud_services_lapsed=cloud_services_lapsed,
    )


def _apply_event_application_rules(
    state: RuntimeEntitlementState,
    event_type: EntitlementEventType,
    payload: EntitlementEventPayload,
) -> None:
    """Apply the spec's event application table to a live state row."""
    if event_type == EntitlementEventType.HOSTED_ACCESS_ACTIVATED:
        assert isinstance(payload, HostedAccessActivatedPayload)
        state.hosted_access_active = True
        state.hosted_access_plan = payload.plan

    elif event_type == EntitlementEventType.HOSTED_ACCESS_DEACTIVATED:
        assert isinstance(payload, HostedAccessDeactivatedPayload)
        state.hosted_access_active = False
        # hosted_access_plan intentionally preserved.

    elif event_type == EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT:
        assert isinstance(payload, SubscriptionCreditGrantPayload)
        state.hosted_credit_balance += payload.hosted_credit_delta

    elif event_type == EntitlementEventType.TOP_UP_CREDIT_GRANT:
        assert isinstance(payload, TopUpCreditGrantPayload)
        state.top_up_credit_balance += payload.top_up_credit_delta

    elif event_type == EntitlementEventType.CREDIT_DEDUCTION:
        assert isinstance(payload, CreditDeductionPayload)
        state.hosted_credit_balance += payload.hosted_credit_delta
        state.top_up_credit_balance += payload.top_up_credit_delta

    elif event_type == EntitlementEventType.BYOK_LICENSE_ACTIVATED:
        assert isinstance(payload, ByokLicenseActivatedPayload)
        state.byok_license_active = True
        state.byok_license_purchased_at = payload.purchased_at

    elif event_type == EntitlementEventType.CLOUD_SERVICES_ACTIVATED:
        assert isinstance(payload, CloudServicesActivatedPayload)
        state.cloud_services_active = True
        state.cloud_services_expires_at = payload.expires_at

    elif event_type == EntitlementEventType.CLOUD_SERVICES_LAPSED:
        assert isinstance(payload, CloudServicesLapsedPayload)
        state.cloud_services_active = False

    elif event_type == EntitlementEventType.MANUAL_CREDIT_ADJUSTMENT:
        assert isinstance(payload, ManualCreditAdjustmentPayload)
        hd = payload.hosted_credit_delta or Decimal("0")
        td = payload.top_up_credit_delta or Decimal("0")
        state.hosted_credit_balance += hd
        state.top_up_credit_balance += td


def _deserialize_payload(
    event: EntitlementEvent,
    event_type: EntitlementEventType,
) -> EntitlementEventPayload:
    payload_class = ENTITLEMENT_PAYLOAD_CLASS_MAP[event_type]
    raw = json.loads(event.payload_json)
    seen_version = raw.get("schema_version")
    if seen_version != 1:
        raise EntitlementPayloadVersionError(
            f"Unsupported schema_version {seen_version!r} for event_id="
            f"{event.event_id} event_type={event_type!r}"
        )
    return payload_class.model_validate_json(event.payload_json)  # type: ignore[return-value]


def _check_idempotency_match(
    existing: EntitlementEvent,
    sojourner_id: UUID,
    event_type: EntitlementEventType,
    turn_id: UUID | None,
    payload: EntitlementEventPayload,
) -> None:
    """Raise EntitlementIdempotencyConflictError if the existing event does not
    match the submitted request.  Comparison uses model_dump(), not raw JSON.
    """
    mismatch: list[str] = []

    if existing.sojourner_id != sojourner_id:
        mismatch.append(
            f"sojourner_id: existing={existing.sojourner_id!r} new={sojourner_id!r}"
        )
    if existing.event_type != event_type:
        mismatch.append(
            f"event_type: existing={existing.event_type!r} new={event_type!r}"
        )
    if existing.turn_id != turn_id:
        mismatch.append(f"turn_id: existing={existing.turn_id!r} new={turn_id!r}")

    if not mismatch:
        # Compare payload field values using model_dump() (not raw JSON).
        try:
            existing_payload = _deserialize_payload(existing, event_type)
        except Exception:
            mismatch.append("payload: could not deserialize existing payload")
        else:
            if existing_payload.model_dump() != payload.model_dump():
                mismatch.append("payload: field values differ")

    if mismatch:
        raise EntitlementIdempotencyConflictError(
            f"idempotency_key={existing.idempotency_key!r} conflict: "
            + "; ".join(mismatch)
        )
