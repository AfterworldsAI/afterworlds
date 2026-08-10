"""Persisted-state proof covers retained review evidence — CRD Issue 5d.

The two identities answer different questions and must keep answering them
separately:

* the **projection UUID** — is this the same authority? Review path excluded.
* the **persisted-state digest** — is this the same persisted state, including
  how it was reviewed? Review evidence included.

Every test below edits one retained row and asserts exactly that split, plus
the persistence-side strictness that stops a rewritten fact row from
reconstructing into apparently valid authority.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.persistence import (
    compute_persisted_state_digest,
    persist_draft,
    reconstruct_candidate,
    verify_reconstruction,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.representation import (
    MalformedFactPayloadError,
    UnknownFactFamilyError,
    fact_from_payload,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.base import Base
from afterworlds.persistence.orm.corpus import CorpusReleaseORM
from afterworlds.persistence.orm.mechanical import (
    MechanicalAcceptanceBatchORM,
    MechanicalAcceptanceORM,
    MechanicalBatchDiffORM,
    MechanicalBatchScopeORM,
    MechanicalFactORM,
    MechanicalSpanORM,
)
from afterworlds.persistence.orm.rules_package import RulesPackageORM
from tests.ingestion.mechanical.conftest import (
    batch_accepted_ledger,
    build_candidate,
    build_ledger,
)

NOW = "2026-07-31T00:00:00Z"


@pytest.fixture()
def session(tmp_path) -> Iterator[Session]:  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{tmp_path / 'evidence.db'}")
    Base.metadata.create_all(engine)
    with create_session_factory(engine)() as s:
        s.add(
            RulesPackageORM(
                rules_package_id="pkg-5c",
                name="SRD 5.2.1",
                system="dnd5e",
                version="5.2.1",
                is_enabled=True,
                publication_status="published",
                created_at=NOW,
                updated_at=NOW,
            )
        )
        s.flush()
        s.add(
            CorpusReleaseORM(
                package_uuid="pkg-5c",
                release_version="rel-5c",
                authoritative_source_hash="a" * 64,
                transform_config_hash="b" * 64,
                bundle_root_hash="c" * 64,
                ledger_hash="1" * 64,
                policy_hash="2" * 64,
                reconciliation_hash="3" * 64,
                transform_config={},
                publication_status="published",
                created_at=NOW,
            )
        )
        s.flush()
        yield s


def _persist_batch_reviewed(session: Session):  # type: ignore[no-untyped-def]
    identified = identify_projection(build_candidate(ledger=batch_accepted_ledger()))
    persist_draft(session, identified, now=NOW)
    return identified


def _identity_and_digest(session: Session, uuid_: str) -> tuple[str, str]:
    """The two answers, recomputed from persisted state."""
    rebuilt = reconstruct_candidate(session, uuid_)
    return (
        identify_projection(rebuilt).projection_uuid,
        compute_persisted_state_digest(session, uuid_),
    )


def _assert_evidence_only_change(
    session: Session, uuid_: str, before: tuple[str, str]
) -> None:
    """Digest moves, projection identity does not."""
    after = _identity_and_digest(session, uuid_)
    assert after[0] == before[0], "review evidence must not change the authority"
    assert after[1] != before[1], "review evidence must be covered by the digest"


# -- evidence changes: digest moves, identity does not ------------------------


def test_changed_reviewer_changes_only_the_digest(session: Session) -> None:
    identified = _persist_batch_reviewed(session)
    before = _identity_and_digest(session, identified.projection_uuid)
    row = session.execute(select(MechanicalAcceptanceORM)).scalars().first()
    assert row is not None
    row.reviewer = "someone-else"
    session.flush()
    _assert_evidence_only_change(session, identified.projection_uuid, before)


def test_changed_acceptance_timestamp_changes_only_the_digest(
    session: Session,
) -> None:
    identified = _persist_batch_reviewed(session)
    before = _identity_and_digest(session, identified.projection_uuid)
    row = session.execute(select(MechanicalAcceptanceORM)).scalars().first()
    assert row is not None
    row.accepted_at = "2026-08-09T09:09:09Z"
    session.flush()
    _assert_evidence_only_change(session, identified.projection_uuid, before)


def test_changed_batch_rule_changes_only_the_digest(session: Session) -> None:
    identified = _persist_batch_reviewed(session)
    before = _identity_and_digest(session, identified.projection_uuid)
    row = session.execute(select(MechanicalAcceptanceBatchORM)).scalars().one()
    row.rule = "a rule nobody applied"
    session.flush()
    _assert_evidence_only_change(session, identified.projection_uuid, before)


def test_changed_scope_membership_changes_only_the_digest(session: Session) -> None:
    identified = _persist_batch_reviewed(session)
    before = _identity_and_digest(session, identified.projection_uuid)
    row = session.execute(select(MechanicalBatchScopeORM)).scalars().first()
    assert row is not None
    row.span_id = "span-substituted"
    session.flush()
    _assert_evidence_only_change(session, identified.projection_uuid, before)


def test_reordered_scope_changes_only_the_digest(session: Session) -> None:
    # The reviewer's recorded scope order is evidence of what they reviewed, so
    # a reshuffle is a different record even though the set is unchanged.
    identified = _persist_batch_reviewed(session)
    before = _identity_and_digest(session, identified.projection_uuid)
    rows = (
        session.execute(
            select(MechanicalBatchScopeORM).order_by(MechanicalBatchScopeORM.ordinal)
        )
        .scalars()
        .all()
    )
    assert len(rows) >= 2
    rows[0].ordinal, rows[-1].ordinal = rows[-1].ordinal, rows[0].ordinal
    session.flush()
    _assert_evidence_only_change(session, identified.projection_uuid, before)


def test_rewritten_diff_evidence_changes_only_the_digest(session: Session) -> None:
    identified = _persist_batch_reviewed(session)
    before = _identity_and_digest(session, identified.projection_uuid)
    row = session.execute(select(MechanicalBatchDiffORM)).scalars().first()
    assert row is not None
    row.prior_disposition = "non_mechanical"
    row.prior_reason_code = "navigation_only"
    session.flush()
    _assert_evidence_only_change(session, identified.projection_uuid, before)


def test_changed_batch_digest_column_changes_the_persisted_digest(
    session: Session,
) -> None:
    identified = _persist_batch_reviewed(session)
    before = _identity_and_digest(session, identified.projection_uuid)
    row = session.execute(select(MechanicalAcceptanceBatchORM)).scalars().one()
    row.semantic_diff_hash = "f" * 64
    session.flush()
    _assert_evidence_only_change(session, identified.projection_uuid, before)


def test_changed_review_state_changes_the_digest(session: Session) -> None:
    identified = _persist_batch_reviewed(session)
    before = _identity_and_digest(session, identified.projection_uuid)
    row = session.execute(select(MechanicalSpanORM)).scalars().first()
    assert row is not None
    row.review_state = "proposed"
    session.flush()
    _assert_evidence_only_change(session, identified.projection_uuid, before)


# -- the identity boundary still holds ---------------------------------------


def test_individual_and_batch_review_share_one_identity(session: Session) -> None:
    individually = identify_projection(build_candidate(ledger=build_ledger()))
    by_batch = identify_projection(build_candidate(ledger=batch_accepted_ledger()))
    assert individually.projection_uuid == by_batch.projection_uuid

    # ...and the persisted proofs differ, because the retained evidence differs.
    persist_draft(session, by_batch, now=NOW)
    batch_digest = compute_persisted_state_digest(session, by_batch.projection_uuid)
    assert verify_reconstruction(session, by_batch) == ()
    assert batch_digest


# -- persisted fact payloads are strict --------------------------------------


def test_missing_payload_field_is_rejected() -> None:
    with pytest.raises(MalformedFactPayloadError, match="missing"):
        fact_from_payload({"family": "spell_descriptor", "level": 9})


def test_extra_payload_field_is_rejected() -> None:
    with pytest.raises(MalformedFactPayloadError, match="extra"):
        fact_from_payload(
            {
                "family": "creature_ability_score",
                "ability": "strength",
                "score": 12,
                "modifier": None,
                "save_modifier": None,
                "smuggled": {"dc": 15},
            }
        )


def test_discriminator_disagreement_is_rejected() -> None:
    with pytest.raises(MalformedFactPayloadError, match="disagrees"):
        fact_from_payload(
            {
                "family": "creature_ability_score",
                "ability": "strength",
                "score": 12,
            },
            declared_family="spell_descriptor",
        )


def test_unknown_persisted_family_is_rejected() -> None:
    with pytest.raises(UnknownFactFamilyError):
        fact_from_payload({"family": "improvised", "anything": 1})


def test_bad_enum_value_is_rejected() -> None:
    with pytest.raises(MalformedFactPayloadError, match="does not rebuild"):
        fact_from_payload(
            {
                "family": "creature_ability_score",
                "ability": "luck",
                "score": 12,
                "modifier": None,
                "save_modifier": None,
            }
        )


def test_tampered_family_column_is_reported_not_reconstructed(
    session: Session,
) -> None:
    identified = _persist_batch_reviewed(session)
    row = session.execute(select(MechanicalFactORM)).scalars().one()
    row.family = "progression_entry"
    session.flush()
    findings = verify_reconstruction(session, identified)
    assert any("does not reconstruct" in f for f in findings)


def test_tampered_fact_key_column_is_reported(session: Session) -> None:
    identified = _persist_batch_reviewed(session)
    row = session.execute(select(MechanicalFactORM)).scalars().one()
    row.fact_key = "0" * 16
    session.flush()
    findings = verify_reconstruction(session, identified)
    assert any("does not reconstruct" in f for f in findings)
