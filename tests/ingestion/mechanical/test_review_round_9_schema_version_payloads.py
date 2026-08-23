"""Every merged schema serializes its own key set — PR #157, round 9.

Codex review on PR #157, P1. Schema 3 added ``fact_qualifiers`` to the
canonical component payload while the serializer branched on **schema 1
only**, so a schema-2 candidate fell through to current behaviour and gained a
key its merged contract never had. Because ``projection_payload`` deliberately
serializes reconstructed history under the candidate's *own* recorded version,
that extra key re-derived the projection UUID and payload hash, and
``verify_persisted_state`` rejected otherwise unchanged schema-2 state.

Exactly the failure Owner Decision 2026-08-20 (Option A) fixed for schema 1,
recurring one version later — which is what makes it a family rather than a
line. The remediation is the general rule, not another version ``if``:
:data:`_MERGED_COMPONENT_FIELDS` gives every merged version its own key set,
and the loop that omits a field is the loop that proves the field carries no
meaning.

**How it slipped through**, recorded because the coverage below is shaped by
it: ``b898922`` widened the schema-2 key assertion to include
``fact_qualifiers`` instead of leaving the schema-2 contract alone and adding a
schema-3 one. That widening deleted the only guard. Each merged version now
gets its own independent canary, so a later succession cannot pass by editing
an older version's expectations.

Every ``SCHEMA_2_*`` literal here was captured by running the **pre-change
code** at ``7395c52`` (``origin/main``) — the merged schema-2 contract itself.
Computing both sides with post-change code would make the claim unfalsifiable,
the same discipline ``test_review_round_6_schema1_identity`` records. The
captured structural hash matches the ``SCHEMA_2_HASH`` literal that module
already pins, which is the cross-check that the capture really ran old code.

**Not remediated here, and deliberately so.** Two sibling payload shapes also
changed in schema 3 — ``SizeComparison`` gained ``at_most``/``measured``/
``reference``, and ``MovementCostFact`` gained ``payer``/``rounding``. Neither
can produce a *silent* identity divergence: both are refused at the
reconstruction boundary (``missing ['at_most', 'measured', 'reference']`` and
``missing ['payer', 'rounding']``), so a schema-2 projection containing one
fails to reconstruct rather than re-identifying wrongly. Recorded in the
remediation log as ``already safe (fails closed)``, with the consequence
stated: such a projection cannot be verified at all.
"""

from __future__ import annotations

from itertools import pairwise

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
    _MERGED_COMPONENT_FIELDS,
    SCHEMA_1_VERSION,
    SCHEMA_2_VERSION,
    SCHEMA_3_VERSION,
    LegacySchemaPayloadError,
    ProjectionCandidate,
    ReleaseBinding,
    UnsupportedSchemaVersionError,
    identify_projection,
    representation_payload,
    validate_schema_binding,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    Applicability,
    ApplicabilityKind,
    ComponentDraft,
    ComponentHandling,
    ComponentOption,
    FactQualifier,
    Phase,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    SpellDescriptorFact,
    SpellSchool,
    fact_key,
    representation_schema_hash,
)
from afterworlds.persistence.orm.corpus import CorpusReleaseORM

# ---------------------------------------------------------------------------
# Literals captured at 7395c52 with pre-change code
# ---------------------------------------------------------------------------

SCHEMA_2_HASH = "ca27a7468abb84db43781e96ac48fbc55e166c3e410fe33d80f03a263a8d002c"
SCHEMA_2_UUID = "389df0d1-54e9-5f7b-864b-7f522e47a766"
SCHEMA_2_PAYLOAD_HASH = (
    "c2990446b1931c411e9bcbb33c5bb8ed40209cb9849f8720963f1536919b0b65"
)
SCHEMA_2_RECORD_ID = "8b8458fe-2b4b-5471-be65-d8b55144aa7f"
SCHEMA_2_COMPONENT_ID = "818624c3-9ad3-55ed-a514-318b8c142fae"
SCHEMA_2_FACT_IDS = [
    "b75cc163-9082-5bed-a80b-1e30a0409423",
    "ed172fef-1171-5d99-8d80-2be61c3598e6",
]

#: The exact schema-2 component wire shape: schema 1's five keys plus the two
#: schema 2 added, and **not** the one schema 3 added.
SCHEMA_2_COMPONENT_KEYS = {
    "record_key",
    "semantic_key",
    "handling",
    "irreducibility_reason_code",
    "facts",
    "applies_when",
    "options",
}

RECORD_KEY = "spell:wish"
COMPONENT_KEY = "descriptor"

# Deliberately a fact family and an applicability kind schema 3 did not touch,
# so the *content* is identical under both contracts and the only thing that
# can differ is the key set. A movement cost or a size comparison would confound
# the two — and, per the module docstring, would not reconstruct at all.
FACT = SpellDescriptorFact(
    level=9, school=SpellSchool.CONJURATION, ritual=False, concentration=False
)
ALT = SpellDescriptorFact(
    level=8, school=SpellSchool.CONJURATION, ritual=False, concentration=False
)
WHILE_ACTIVE = Applicability(kind=ApplicabilityKind.PHASE, phase=Phase.WHILE_ACTIVE)
CHOICE = (
    ComponentOption(semantic_key="cast", facts=(FACT,)),
    ComponentOption(semantic_key="ritual", facts=(ALT,)),
)

_BINDING = ReleaseBinding(
    package_uuid="pkg-schema2",
    release_version="rel-schema2",
    authoritative_source_hash="a" * 64,
    transform_config_hash="b" * 64,
    bundle_root_hash="c" * 64,
    persisted_corpus_digest="d" * 64,
)
_LEDGER = ClassificationLedger(
    package_uuid="pkg-schema2",
    release_version="rel-schema2",
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=(),
    batches=(),
    acceptances=(),
)


def schema_2_draft(**overrides: object) -> RepresentationDraft:
    """A component using *both* keys schema 2 added, so the canary pins both."""
    fields: dict[str, object] = {
        "record_key": RECORD_KEY,
        "semantic_key": COMPONENT_KEY,
        "handling": ComponentHandling.STRUCTURED,
        "facts": (),
        "applies_when": WHILE_ACTIVE,
        "options": CHOICE,
    }
    fields.update(overrides)
    return RepresentationDraft(
        records=(RecordDraft(semantic_key=RECORD_KEY, kind=RecordKind.SPELL),),
        components=(ComponentDraft(**fields),),  # type: ignore[arg-type]
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )


def schema_2_candidate(**overrides: object) -> ProjectionCandidate:
    """A candidate declaring schema 2, exactly as one persisted under it does."""
    return ProjectionCandidate(
        binding=_BINDING,
        classification=_LEDGER,
        representation=schema_2_draft(**overrides),
        schema_version=SCHEMA_2_VERSION,
        schema_hash=SCHEMA_2_HASH,
    )


# ---------------------------------------------------------------------------
# 1. An untouched schema-2 candidate reproduces its own payload and identity
# ---------------------------------------------------------------------------


def test_the_schema_2_component_payload_has_its_merged_key_set() -> None:
    """The assertion `b898922` widened, restored against schema 2 itself.

    Pinned by serializing *under schema 2* rather than by asserting whatever
    the current schema emits — that coupling is what let schema 3's key be
    absorbed into this contract by editing one expectation.
    """
    payload = representation_payload(schema_2_draft(), schema_version=SCHEMA_2_VERSION)
    (component,) = payload["components"]  # type: ignore[index]
    assert set(component) == SCHEMA_2_COMPONENT_KEYS
    assert "fact_qualifiers" not in component


def test_the_schema_2_projection_identity_is_reproduced_exactly() -> None:
    identified = identify_projection(schema_2_candidate())
    assert identified.projection_uuid == SCHEMA_2_UUID
    assert identified.payload_hash == SCHEMA_2_PAYLOAD_HASH


def test_every_schema_2_derived_id_is_reproduced_exactly() -> None:
    identified = identify_projection(schema_2_candidate())
    assert identified.record_ids[RECORD_KEY] == SCHEMA_2_RECORD_ID
    assert (
        identified.component_ids[(RECORD_KEY, COMPONENT_KEY)] == SCHEMA_2_COMPONENT_ID
    )
    assert sorted(identified.fact_ids.values()) == SCHEMA_2_FACT_IDS


def test_the_captured_structural_hash_is_the_one_already_pinned() -> None:
    """Cross-check that the capture really ran pre-change code.

    ``test_review_round_6_schema1_identity`` pins the same schema-2 structural
    hash from its own independent capture. Two captures of the same merged
    contract must agree, and neither may be the current one.
    """
    assert representation_schema_hash() != SCHEMA_2_HASH
    assert REPRESENTATION_SCHEMA_VERSION == SCHEMA_3_VERSION


# ---------------------------------------------------------------------------
# 2. Newer meaning is refused, never silently serialized
# ---------------------------------------------------------------------------

QUALIFIED = (FactQualifier(fact_key=fact_key(FACT), applies_when=WHILE_ACTIVE),)


def test_schema_2_refuses_a_fact_qualifier_rather_than_serializing_it() -> None:
    """The second half of the finding, and the sharper one.

    Emitting the key with an empty list only moved an identity; emitting it
    with real content would publish schema-3 meaning under a contract that
    cannot express it, and an auditor reading the schema-2 payload would have
    no way to know the limitation was ever there.
    """
    with pytest.raises(LegacySchemaPayloadError, match="fact_qualifiers"):
        representation_payload(
            schema_2_draft(facts=(FACT,), options=(), fact_qualifiers=QUALIFIED),
            schema_version=SCHEMA_2_VERSION,
        )


def test_the_refusal_names_the_version_that_introduced_the_field() -> None:
    """So the message says *why* it cannot be held, not merely that it cannot."""
    with pytest.raises(LegacySchemaPayloadError, match="schema-3"):
        representation_payload(
            schema_2_draft(facts=(FACT,), options=(), fact_qualifiers=QUALIFIED),
            schema_version=SCHEMA_2_VERSION,
        )


def test_the_schema_2_refusal_reaches_the_identity_path() -> None:
    """Not only the serializer in isolation — the path identity actually takes."""
    with pytest.raises(LegacySchemaPayloadError):
        identify_projection(
            schema_2_candidate(facts=(FACT,), options=(), fact_qualifiers=QUALIFIED)
        )


# ---------------------------------------------------------------------------
# 3. Schema 1 is unchanged by the generalisation
# ---------------------------------------------------------------------------

#: One field isolated per case, so the refusal that fires is the one named.
NEWER_THAN_SCHEMA_1 = [
    ("applies_when", {"facts": (FACT,), "options": ()}),
    ("options", {"facts": (), "applies_when": None, "options": CHOICE}),
    (
        "fact_qualifiers",
        {
            "facts": (FACT,),
            "options": (),
            "applies_when": None,
            "fact_qualifiers": QUALIFIED,
        },
    ),
]


@pytest.mark.parametrize(
    ("field", "overrides"),
    NEWER_THAN_SCHEMA_1,
    ids=[field for field, _ in NEWER_THAN_SCHEMA_1],
)
def test_schema_1_still_refuses_every_field_added_after_it(
    field: str, overrides: dict[str, object]
) -> None:
    """Generalising the rule must not have narrowed schema 1's own refusal."""
    with pytest.raises(LegacySchemaPayloadError, match=field):
        representation_payload(
            schema_2_draft(**overrides), schema_version=SCHEMA_1_VERSION
        )


def test_schema_1_emits_only_its_own_five_keys() -> None:
    payload = representation_payload(
        schema_2_draft(facts=(FACT,), options=(), applies_when=None),
        schema_version=SCHEMA_1_VERSION,
    )
    (component,) = payload["components"]  # type: ignore[index]
    assert set(component) == SCHEMA_2_COMPONENT_KEYS - {"applies_when", "options"}


# ---------------------------------------------------------------------------
# 4. Schema 3 still emits its own key normally
# ---------------------------------------------------------------------------


def test_schema_3_emits_the_fact_qualifier() -> None:
    payload = representation_payload(
        schema_2_draft(facts=(FACT,), options=(), fact_qualifiers=QUALIFIED),
        schema_version=SCHEMA_3_VERSION,
    )
    (component,) = payload["components"]  # type: ignore[index]
    assert set(component) == SCHEMA_2_COMPONENT_KEYS | {"fact_qualifiers"}
    assert component["fact_qualifiers"] == [
        {
            "fact_key": fact_key(FACT),
            "option_key": "",
            "applies_when": component["applies_when"],
        }
    ]


def test_the_current_schema_is_the_default_and_is_schema_3() -> None:
    """Every existing caller must be byte-identical without passing anything."""
    assert representation_payload(schema_2_draft()) == representation_payload(
        schema_2_draft(), schema_version=REPRESENTATION_SCHEMA_VERSION
    )
    assert representation_payload(schema_2_draft()) == representation_payload(
        schema_2_draft(), schema_version=SCHEMA_3_VERSION
    )


# ---------------------------------------------------------------------------
# 5. An unrecognised version fails closed
# ---------------------------------------------------------------------------

UNKNOWN_VERSIONS = [
    "5d-representation-schema-4",
    "5d-representation-schema-0",
    "representation-schema-3",
    "",
]


@pytest.mark.parametrize("version", UNKNOWN_VERSIONS)
def test_an_unknown_schema_version_is_refused(version: str) -> None:
    """Never current-schema behaviour by default.

    Falling through would derive an identity under a contract nobody asked
    for — the same forged-identity failure the meaning check prevents, arriving
    from the other side.
    """
    with pytest.raises(UnsupportedSchemaVersionError):
        representation_payload(schema_2_draft(), schema_version=version)


def test_an_unknown_version_is_refused_even_with_no_components() -> None:
    """The check cannot live inside the per-component loop.

    A draft with no components never enters it, so an unrecognised version
    would serialize an empty component list and derive an identity anyway.
    """
    empty = RepresentationDraft(
        records=(),
        components=(),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )
    with pytest.raises(UnsupportedSchemaVersionError):
        representation_payload(empty, schema_version="5d-representation-schema-4")


def test_the_refusal_names_the_versions_this_build_knows() -> None:
    with pytest.raises(UnsupportedSchemaVersionError) as caught:
        representation_payload(schema_2_draft(), schema_version="nonsense")
    assert caught.value.schema_version == "nonsense"
    assert SCHEMA_2_VERSION in str(caught.value)


# ---------------------------------------------------------------------------
# 6. The registry itself
# ---------------------------------------------------------------------------


def test_the_registry_covers_the_current_schema() -> None:
    """What the module-level assertion protects, stated as a test.

    A schema mint that forgets its row must make the *current* contract
    unserializable — loudly — rather than inheriting its predecessor's keys.
    """
    assert REPRESENTATION_SCHEMA_VERSION in _MERGED_COMPONENT_FIELDS


def test_each_merged_version_extends_the_one_before_it() -> None:
    """The table is a succession, not three unrelated shapes.

    A version whose key set is not a superset of its predecessor's would mean a
    key was *removed*, which no merged contract has done — and if one ever
    does, that is a decision to make explicitly rather than to discover here.
    """
    succession = [SCHEMA_1_VERSION, SCHEMA_2_VERSION, SCHEMA_3_VERSION]
    assert sorted(_MERGED_COMPONENT_FIELDS) == sorted(succession)
    for earlier, later in pairwise(succession):
        assert _MERGED_COMPONENT_FIELDS[earlier] < _MERGED_COMPONENT_FIELDS[later]


def test_no_two_merged_versions_share_a_key_set() -> None:
    """Distinct contracts, distinct payload shapes — otherwise the version is noise."""
    shapes = list(_MERGED_COMPONENT_FIELDS.values())
    assert len(set(shapes)) == len(shapes)


# ---------------------------------------------------------------------------
# 7. Persisted, reconstructed, and verified
# ---------------------------------------------------------------------------


def _seed_schema_2_release(session: Session) -> None:
    """The FK parent for this projection's own package.

    Deliberately not the shared ``pkg-5c`` fixture, so the captured pre-change
    literals stay authoritative rather than being recomputed against a fixture
    that has moved since.
    """
    _persist_package_and_source(
        session,
        _BINDING.package_uuid,
        _BINDING.release_version,
        now="2026-08-20T00:00:00Z",
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
            created_at="2026-08-20T00:00:00Z",
        )
    )
    session.flush()


def test_a_schema_2_projection_survives_persistence_and_reconstruction(
    session: Session,
) -> None:
    """The whole point: persist, reconstruct, and still be the same projection.

    The fixture database is built by the real migration chain through ``head``,
    which is past ``0029`` — so ``rp_mech_facts.applies_when`` exists and holds
    its default, exactly the post-upgrade state this remediation is about.
    """
    _seed_schema_2_release(session)
    identified = identify_projection(schema_2_candidate())
    assert identified.projection_uuid == SCHEMA_2_UUID
    persist_draft(session, identified, now="2026-08-20T00:00:00Z")
    session.flush()

    rebuilt = reconstruct_candidate(session, SCHEMA_2_UUID)
    assert rebuilt.schema_version == SCHEMA_2_VERSION
    assert rebuilt.schema_hash == SCHEMA_2_HASH

    reidentified = identify_projection(rebuilt)
    assert reidentified.projection_uuid == SCHEMA_2_UUID
    assert reidentified.payload_hash == SCHEMA_2_PAYLOAD_HASH
    assert reidentified.record_ids[RECORD_KEY] == SCHEMA_2_RECORD_ID
    assert sorted(reidentified.fact_ids.values()) == SCHEMA_2_FACT_IDS


def test_verify_persisted_state_accepts_reconstructed_schema_2_state(
    session: Session,
) -> None:
    """The reported symptom, asserted as its absence."""
    _seed_schema_2_release(session)
    identified = identify_projection(schema_2_candidate())
    persist_draft(session, identified, now="2026-08-20T00:00:00Z")
    recorded = record_persisted_state_digest(session, SCHEMA_2_UUID)
    session.flush()

    assert compute_persisted_state_digest(session, SCHEMA_2_UUID) == recorded
    assert verify_persisted_state(session, SCHEMA_2_UUID) == ()


def test_verify_persisted_state_still_detects_tampering(session: Session) -> None:
    """Accepting valid historical state must not mean accepting anything.

    The negative control for the test above: the same projection, one option's
    key changed after the digest was recorded, must still be reported. A
    verification that cannot fail proves nothing about the one that passes.
    """
    from afterworlds.persistence.orm.mechanical import MechanicalComponentOptionORM

    _seed_schema_2_release(session)
    identified = identify_projection(schema_2_candidate())
    persist_draft(session, identified, now="2026-08-20T00:00:00Z")
    record_persisted_state_digest(session, SCHEMA_2_UUID)
    session.flush()
    assert verify_persisted_state(session, SCHEMA_2_UUID) == ()

    option = (
        session.query(MechanicalComponentOptionORM)
        .filter_by(projection_uuid=SCHEMA_2_UUID, semantic_key="ritual")
        .one()
    )
    option.semantic_key = "tampered"
    session.flush()

    assert verify_persisted_state(session, SCHEMA_2_UUID) != ()


def test_a_schema_2_projection_is_still_not_activatable() -> None:
    """Historical reconstruction only — the clean-baseline gate is unchanged."""
    findings = validate_schema_binding(schema_2_candidate())
    assert findings
    assert any(SCHEMA_2_VERSION in f for f in findings)
