"""Schema-1 identity survives migration 0028 — PR #155, round 6, finding 2.

Codex review round 6. Schema 2 added ``applies_when`` and ``options`` to the
canonical component payload. A projection persisted under schema 1 has neither
in its stored rows, so reconstruction supplies the new fields' defaults — and
the serializer then emitted ``applies_when: null`` and ``options: []`` for it.
Those keys were absent from the original identity-bearing payload, so
``identify_projection(reconstruct_candidate(...))`` derived a *different* UUID
and payload hash, and ``verify_persisted_state`` rejected otherwise unchanged
historical state.

**Owner Decision 2026-08-20, Option A — narrow to the ``0027 -> 0028``
boundary.** A schema-1 projection persisted under 0027 must reconstruct after
the upgrade with its original projection UUID, payload hash, derived IDs, and
recorded persisted-state digest. This is a one-time schema-1 → schema-2
compatibility decision. It does **not** revoke #137's clean-baseline policy,
does not establish general legacy compatibility, and does not make a schema-1
projection activatable — ``validate_schema_binding`` still refuses one as
current authority, unchanged and asserted below.

Every schema-1 literal in this module was captured by running the **pre-change
code** at ``f6d2813~1`` in a detached worktree. Computing both sides with
post-change code would make the claim unfalsifiable.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.persistence import _persist_package_and_source
from afterworlds.ingestion.mechanical.models import ClassificationLedger
from afterworlds.ingestion.mechanical.persistence import (
    compute_persisted_state_digest,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.policy import (
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (
    SCHEMA_1_VERSION,
    LegacySchemaPayloadError,
    ProjectionCandidate,
    ReleaseBinding,
    identify_projection,
    projection_payload,
    representation_payload,
    validate_schema_binding,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    Applicability,
    ApplicabilityKind,
    Comparison,
    ComponentDraft,
    ComponentHandling,
    ComponentOption,
    MovementMode,
    MovementPermissionFact,
    Phase,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    SpellDescriptorFact,
    SpellSchool,
    TrackedQuantity,
    representation_schema_hash,
)
from afterworlds.persistence.orm.corpus import CorpusReleaseORM

# ---------------------------------------------------------------------------
# Literals captured from the pre-change code at f6d2813~1
# ---------------------------------------------------------------------------

SCHEMA_1_HASH = "44bf8519d57a28a193717219e276b329f0eaa30c56cf52284219f67916d09ff3"
#: Retained as a historical literal after schema 3 succeeded it. It is no
#: longer what the build computes, and it is kept so the succession itself can
#: be asserted: three merged contracts, three distinct identities.
SCHEMA_2_HASH = "ca27a7468abb84db43781e96ac48fbc55e166c3e410fe33d80f03a263a8d002c"

LEGACY_UUID = "5925934a-3692-551d-babe-2df5a6fa6752"
LEGACY_PAYLOAD_HASH = "0df49dee85b9b6ef26e7c4d862942dcadf721489da7dd9a0fbde42bd80f81bfe"
LEGACY_RECORD_ID = "96de01e9-61b7-56b1-8229-f97273d475e3"
LEGACY_COMPONENT_ID = "3377d6db-a35b-5f97-a75a-c39c5b2c4dd7"
LEGACY_FACT_ID = "919810ef-6f3b-54e9-904e-00681376621a"

#: The exact schema-1 component wire shape — five keys, and neither of the two
#: schema 2 added.
LEGACY_COMPONENT_KEYS = {
    "record_key",
    "semantic_key",
    "handling",
    "irreducibility_reason_code",
    "facts",
}

RECORD_KEY = "spell:wish"
COMPONENT_KEY = "descriptor"
FACT = SpellDescriptorFact(
    level=9, school=SpellSchool.CONJURATION, ritual=False, concentration=False
)

_BINDING = ReleaseBinding(
    package_uuid="pkg-schema1",
    release_version="rel-schema1",
    authoritative_source_hash="a" * 64,
    transform_config_hash="b" * 64,
    bundle_root_hash="c" * 64,
    persisted_corpus_digest="d" * 64,
)
_LEDGER = ClassificationLedger(
    package_uuid="pkg-schema1",
    release_version="rel-schema1",
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=(),
    batches=(),
    acceptances=(),
)


def legacy_draft(**overrides: object) -> RepresentationDraft:
    fields: dict[str, object] = {
        "record_key": RECORD_KEY,
        "semantic_key": COMPONENT_KEY,
        "handling": ComponentHandling.STRUCTURED,
        "facts": (FACT,),
    }
    fields.update(overrides)
    component = ComponentDraft(**fields)  # type: ignore[arg-type]
    return RepresentationDraft(
        records=(RecordDraft(semantic_key=RECORD_KEY, kind=RecordKind.SPELL),),
        components=(component,),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )


def legacy_candidate(**overrides: object) -> ProjectionCandidate:
    """A candidate declaring schema 1, exactly as one persisted under 0027 does."""
    return ProjectionCandidate(
        binding=_BINDING,
        classification=_LEDGER,
        representation=legacy_draft(**overrides),
        schema_version=SCHEMA_1_VERSION,
        schema_hash=SCHEMA_1_HASH,
    )


def current_candidate() -> ProjectionCandidate:
    return ProjectionCandidate(
        binding=_BINDING,
        classification=_LEDGER,
        representation=legacy_draft(),
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
    )


# ---------------------------------------------------------------------------
# 4a. The legacy wire shape and every derived identity are reproduced
# ---------------------------------------------------------------------------


def test_the_schema_1_component_payload_has_its_original_key_set() -> None:
    payload = representation_payload(legacy_draft(), schema_version=SCHEMA_1_VERSION)
    (component,) = payload["components"]  # type: ignore[index]
    assert set(component) == LEGACY_COMPONENT_KEYS
    assert "applies_when" not in component
    assert "options" not in component


def test_the_schema_1_projection_identity_is_reproduced_exactly() -> None:
    identified = identify_projection(legacy_candidate())
    assert identified.projection_uuid == LEGACY_UUID
    assert identified.payload_hash == LEGACY_PAYLOAD_HASH


def test_every_schema_1_derived_id_is_reproduced_exactly() -> None:
    identified = identify_projection(legacy_candidate())
    assert identified.record_ids[RECORD_KEY] == LEGACY_RECORD_ID
    assert identified.component_ids[(RECORD_KEY, COMPONENT_KEY)] == LEGACY_COMPONENT_ID
    # The derived fact *id* is unchanged. Its in-memory lookup key gained an
    # option slot in the schema-2 work, which is a dict-key shape, not an
    # identity — so the values are what this asserts.
    assert list(identified.fact_ids.values()) == [LEGACY_FACT_ID]


# ---------------------------------------------------------------------------
# 4b. Persisted under 0028's schema, reconstructed as historical state
# ---------------------------------------------------------------------------


def _seed_legacy_release(session: Session) -> None:
    """The FK parent for the legacy package.

    The shared fixture publishes ``pkg-5c``; this projection is deliberately
    its own package so the captured pre-change literals stay authoritative
    rather than being recomputed against a fixture that has moved since.
    """
    _persist_package_and_source(
        session,
        _BINDING.package_uuid,
        _BINDING.release_version,
        now="2026-08-08T00:00:00Z",
    )
    session.add(
        CorpusReleaseORM(
            package_uuid=_BINDING.package_uuid,
            release_version=_BINDING.release_version,
            authoritative_source_hash=_BINDING.authoritative_source_hash,
            transform_config_hash=_BINDING.transform_config_hash,
            bundle_root_hash=_BINDING.bundle_root_hash,
            ledger_hash="1" * 64,
            policy_hash="2" * 64,
            reconciliation_hash="3" * 64,
            transform_config={},
            publication_status="published",
            created_at="2026-08-08T00:00:00Z",
        )
    )
    session.flush()


def test_a_schema_1_projection_survives_persistence_and_reconstruction(
    session: Session,
) -> None:
    """The whole point: persist, reconstruct, and still be the same projection.

    The fixture database is built by the real migration chain through ``head``,
    which is *past* 0028 — so the schema-2 columns exist and hold their
    defaults, exactly the post-upgrade state this decision is about.
    """
    _seed_legacy_release(session)
    identified = identify_projection(legacy_candidate())
    assert identified.projection_uuid == LEGACY_UUID
    persist_draft(session, identified, now="2026-08-08T00:00:00Z")
    session.flush()

    rebuilt = reconstruct_candidate(session, LEGACY_UUID)
    assert rebuilt.schema_version == SCHEMA_1_VERSION
    assert rebuilt.schema_hash == SCHEMA_1_HASH

    reidentified = identify_projection(rebuilt)
    assert reidentified.projection_uuid == LEGACY_UUID
    assert reidentified.payload_hash == LEGACY_PAYLOAD_HASH
    assert reidentified.record_ids[RECORD_KEY] == LEGACY_RECORD_ID
    assert list(reidentified.fact_ids.values()) == [LEGACY_FACT_ID]


def test_the_recorded_digest_verifies_after_the_upgrade(session: Session) -> None:
    _seed_legacy_release(session)
    identified = identify_projection(legacy_candidate())
    persist_draft(session, identified, now="2026-08-08T00:00:00Z")
    recorded = record_persisted_state_digest(session, LEGACY_UUID)
    session.flush()

    assert compute_persisted_state_digest(session, LEGACY_UUID) == recorded
    assert verify_persisted_state(session, LEGACY_UUID) == ()


def test_a_schema_1_projection_is_still_not_activatable() -> None:
    """Historical reconstruction only — the clean-baseline gate is unchanged.

    This is what keeps Option A narrow: reconstructable, never current
    authority.
    """
    findings = validate_schema_binding(legacy_candidate())
    assert findings
    assert any(SCHEMA_1_VERSION in f for f in findings)
    assert validate_schema_binding(current_candidate()) == ()


# ---------------------------------------------------------------------------
# 5. Fail closed rather than omit meaning
# ---------------------------------------------------------------------------

QUALIFIER = Applicability(
    kind=ApplicabilityKind.QUANTITY_THRESHOLD,
    negated=True,
    quantity=TrackedQuantity.SPEED,
    comparison=Comparison.EQUALS,
    value=0,
)
CHOICE = (
    ComponentOption(
        semantic_key="crawl", facts=(MovementPermissionFact(mode=MovementMode.CRAWL),)
    ),
    ComponentOption(
        semantic_key="swim", facts=(MovementPermissionFact(mode=MovementMode.SWIM),)
    ),
)


@pytest.mark.parametrize(
    ("label", "overrides"),
    [
        ("a component-level qualifier", {"applies_when": QUALIFIER}),
        ("an option set", {"facts": (), "options": CHOICE}),
        (
            "a phase qualifier",
            {
                "applies_when": Applicability(
                    kind=ApplicabilityKind.PHASE, phase=Phase.WHILE_ACTIVE
                )
            },
        ),
    ],
    ids=["qualifier", "options", "phase-qualifier"],
)
def test_schema_1_state_carrying_schema_2_meaning_fails_closed(
    label: str, overrides: dict[str, object]
) -> None:
    """Omitting a *default* field is compatibility; omitting a meaning-bearing
    one would be forging an identity. This must never silently succeed."""
    with pytest.raises(LegacySchemaPayloadError, match="schema-2"):
        representation_payload(
            legacy_draft(**overrides), schema_version=SCHEMA_1_VERSION
        )


def test_the_fail_closed_check_reaches_the_identity_path() -> None:
    """Not only the serializer in isolation — the path identity actually takes."""
    with pytest.raises(LegacySchemaPayloadError):
        identify_projection(legacy_candidate(applies_when=QUALIFIER))


# ---------------------------------------------------------------------------
# The schema-1 boundary survives every later succession
# ---------------------------------------------------------------------------


def test_each_merged_schema_version_has_its_own_structural_identity() -> None:
    """Schema 3 succeeded schema 2; neither may reuse an earlier identity.

    This test previously pinned the current hash to schema 2's, asserting that
    the schema-1 work had not disturbed the then-current contract. Schema 3
    changes that contract deliberately, so what is asserted now is the property
    that outlives any one version: each merged contract has a distinct
    structural identity, and the schema-1 literal above is untouched by both
    successions.
    """
    current = representation_schema_hash()
    assert REPRESENTATION_SCHEMA_VERSION == "5d-representation-schema-3"
    assert len({SCHEMA_1_HASH, SCHEMA_2_HASH, current}) == 3


def test_the_current_component_payload_still_emits_both_schema_2_keys() -> None:
    payload = representation_payload(legacy_draft())
    (component,) = payload["components"]  # type: ignore[index]
    assert set(component) == LEGACY_COMPONENT_KEYS | {"applies_when", "options"}
    assert component["applies_when"] is None
    assert component["options"] == []


def test_schema_1_and_schema_2_are_different_projections() -> None:
    """Same content, different declared contract — and that is the point.

    ADR-005d Decision 6: a candidate whose facts belong to families a schema
    change did not touch produces byte-identical content, and must still not
    share a UUID across two union contracts.
    """
    assert (
        identify_projection(current_candidate()).projection_uuid
        != identify_projection(legacy_candidate()).projection_uuid
    )


def test_the_default_serializer_argument_is_the_current_schema() -> None:
    """Every existing caller must be byte-identical without passing anything."""
    assert representation_payload(legacy_draft()) == representation_payload(
        legacy_draft(), schema_version=REPRESENTATION_SCHEMA_VERSION
    )


def test_projection_payload_uses_the_candidates_own_declaration() -> None:
    legacy = projection_payload(legacy_candidate())
    current = projection_payload(current_candidate())
    (legacy_component,) = legacy["representation"]["components"]  # type: ignore[index]
    (current_component,) = current["representation"]["components"]  # type: ignore[index]
    assert "options" not in legacy_component
    assert "options" in current_component
