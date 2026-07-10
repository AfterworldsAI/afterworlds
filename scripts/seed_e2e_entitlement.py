#!/usr/bin/env python
"""CLI script -- seed hosted entitlement for the local Sojourner, for E2E only.

CRD Issue 19: the Playwright minimal-spine E2E suite needs at least one
scenario where a turn actually reaches the orchestrator (DELIVERED /
INTERACTION_REJECTED rendering), which requires a runnable access path.
Production `create_app()` never auto-grants entitlement (Issue 20/23's
territory) -- this script exists only for frontend/e2e/global-setup.ts to
call against the E2E-only sqlite file, using the same typed
`receive_entitlement_event` mutation path `tests/entitlement/` already uses.

Usage
-----
    python scripts/seed_e2e_entitlement.py --db-url sqlite:///./_e2e.db
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-url", required=True)
    args = parser.parse_args()

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

    from afterworlds.entitlement.enums import EntitlementEventType, HostedAccessPlan
    from afterworlds.entitlement.payloads import (
        HostedAccessActivatedPayload,
        SubscriptionCreditGrantPayload,
    )
    from afterworlds.entitlement.service import EntitlementService
    from afterworlds.persistence.crud.identity import get_or_create_sojourner_identity
    from afterworlds.persistence.database import create_engine, create_session_factory
    from afterworlds.persistence.orm.identity import SojournerIdentityORM  # noqa: F401

    engine = create_engine(args.db_url)
    session_factory = create_session_factory(engine)
    session = session_factory()
    try:
        identity = get_or_create_sojourner_identity(session)
        session.commit()

        service = EntitlementService(session)
        service.receive_entitlement_event(
            identity.sojourner_id,
            EntitlementEventType.HOSTED_ACCESS_ACTIVATED,
            HostedAccessActivatedPayload(
                plan=HostedAccessPlan.SUBSCRIPTION, effective_at=datetime.now(UTC)
            ),
        )
        service.receive_entitlement_event(
            identity.sojourner_id,
            EntitlementEventType.SUBSCRIPTION_CREDIT_GRANT,
            SubscriptionCreditGrantPayload(hosted_credit_delta=Decimal("1000")),
        )
        session.commit()
        print(f"Seeded hosted entitlement for sojourner {identity.sojourner_id}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
