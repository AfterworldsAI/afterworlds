"""Representation-schema identity — CRD Issue 5d, ADR-005d Decisions 4 and 6.

The closed union is versioned and identity-bound, for the same reason the
semantic policy is. Without that binding a projection whose facts all belong to
families a schema change did not touch keeps exactly the same UUID across two
different union contracts, and a recorded binding cannot say which contract
governs the authority it names.

The canary that matters is the **unaffected family**: it is easy to believe the
representation payload already covers this, because a change to a family the
candidate uses does move the payload. A candidate that uses none of the changed
families is the case that silently kept its identity, and it is the first test
here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.models import ComponentHandling
from afterworlds.ingestion.mechanical.oracle import (
    OracleLoadError,
    load_accepted_inputs,
    oracle_payload,
)
from afterworlds.ingestion.mechanical.persistence import (
    compute_persisted_state_digest,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    projection_payload,
    validate_schema_binding,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    AbilityCheckFact,
    AbilityScore,
    AdvantageFact,
    AdvantageState,
    ComponentDraft,
    DcKind,
    DieSize,
    MalformedFactPayloadError,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    RollActor,
    RollContext,
    RollSpec,
    _declared_fields,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
    representation_schema_hash,
    representation_schema_payload,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.persistence.orm.mechanical import MechanicalProjectionORM
from tests.ingestion.mechanical.conftest import (
    BOUNDED_ORACLE_PATH,
    NOW,
    RELEASE_BINDING,
    SCHEMA_HASH,
    SCHEMA_VERSION,
    bound_corpus,
    build_ledger,
    build_representation,
    candidate_of,
)

OTHER_VERSION = "5d-representation-schema-99"
OTHER_HASH = "9" * 64


# ---------------------------------------------------------------------------
# 1. Two schema versions, identical content, different identities
# ---------------------------------------------------------------------------

#: A record whose only fact belongs to a family this expansion did not touch.
#: ``AbilityCheckFact`` was neither added nor reshaped, so this candidate's
#: representation payload is byte-identical before and after the union changed.
UNAFFECTED_ONLY = RepresentationDraft(
    records=(
        RecordDraft(semantic_key="rule:untouched", kind=RecordKind.GLOSSARY_RULE),
    ),
    components=(
        ComponentDraft(
            record_key="rule:untouched",
            semantic_key="check",
            handling=ComponentHandling.STRUCTURED,
            facts=(AbilityCheckFact(AbilityScore.WISDOM, DcKind.SPELL_SAVE_DC),),
        ),
    ),
    prose_bindings=(),
    relationships=(),
    references=(),
    provenance=(),
)


def test_a_candidate_of_only_unaffected_families_still_reidentifies() -> None:
    """The exact defect this identity exists for.

    Nothing about this candidate's content mentions a family the expansion
    added or reshaped, so without the schema declaration it would carry the
    same UUID under both union contracts.
    """
    here = candidate_of(RELEASE_BINDING, build_ledger(), UNAFFECTED_ONLY)
    there = replace(here, schema_version=OTHER_VERSION, schema_hash=OTHER_HASH)

    # The content really is identical — this is what made the omission invisible.
    assert projection_payload(here)["representation"] == (
        projection_payload(there)["representation"]
    )
    assert (
        identify_projection(here).projection_uuid
        != identify_projection(there).projection_uuid
    )


def test_two_schema_versions_reidentify_the_bounded_fixture() -> None:
    base = candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    other = replace(base, schema_version=OTHER_VERSION, schema_hash=OTHER_HASH)
    assert (
        identify_projection(base).projection_uuid
        != identify_projection(other).projection_uuid
    )


def test_the_version_and_the_hash_each_move_the_identity() -> None:
    """Both halves are identity-bearing, not just whichever one a test perturbs."""
    base = candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    uuid_ = identify_projection(base).projection_uuid
    only_version = replace(base, schema_version=OTHER_VERSION)
    only_hash = replace(base, schema_hash=OTHER_HASH)
    assert identify_projection(only_version).projection_uuid != uuid_
    assert identify_projection(only_hash).projection_uuid != uuid_
    # ...and they are not the same perturbation wearing two names.
    assert (
        identify_projection(only_version).projection_uuid
        != identify_projection(only_hash).projection_uuid
    )


# ---------------------------------------------------------------------------
# 2. Identical content and schema reproduce the identity
# ---------------------------------------------------------------------------


def test_identical_content_and_schema_reproduce_the_same_uuid() -> None:
    first = candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    second = candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    assert (
        identify_projection(first).projection_uuid
        == identify_projection(second).projection_uuid
    )
    assert identify_projection(first).payload_hash == (
        identify_projection(second).payload_hash
    )


# ---------------------------------------------------------------------------
# 3. The persisted declaration round-trips, and reconstruction does not
#    substitute current constants
# ---------------------------------------------------------------------------


def test_the_declaration_round_trips_through_persistence(session: Session) -> None:
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    )
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.schema_version == SCHEMA_VERSION
    assert rebuilt.schema_hash == SCHEMA_HASH
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid


def test_reconstruction_reads_the_stored_declaration_not_current_code(
    session: Session,
) -> None:
    """A projection built under another union reconstructs as what it was.

    Substituting the module constants here would erase exactly the divergence
    the declaration exists to make visible: the row would reconstruct as
    "current", and a stale projection would look fresh.
    """
    stale = candidate_of(
        RELEASE_BINDING,
        build_ledger(),
        build_representation(),
        schema_version=OTHER_VERSION,
        schema_hash=OTHER_HASH,
    )
    identified = identify_projection(stale)
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert (rebuilt.schema_version, rebuilt.schema_hash) == (OTHER_VERSION, OTHER_HASH)
    assert rebuilt.schema_version != REPRESENTATION_SCHEMA_VERSION
    # And the stale declaration is *reported*, not silently accepted.
    assert validate_schema_binding(rebuilt)


def test_audit_retrieval_of_a_historical_projection_states_its_union(
    session: Session,
) -> None:
    """Audit and replay resolve through the same reconstruction seam.

    The runtime binding does not expose the semantic policy either; historical
    projection authority is read back through ``reconstruct_candidate``, and the
    representation declaration rides exactly where the policy declaration does.
    """
    identified = identify_projection(
        candidate_of(
            RELEASE_BINDING,
            build_ledger(),
            build_representation(),
            schema_version=OTHER_VERSION,
            schema_hash=OTHER_HASH,
        )
    )
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.classification.policy_version  # policy still stated
    assert rebuilt.schema_version == OTHER_VERSION  # and now the union too


# ---------------------------------------------------------------------------
# 4. Missing, unknown, mismatched, and tampered declarations fail closed
# ---------------------------------------------------------------------------


def test_a_committed_artifact_without_the_declaration_is_refused(
    tmp_path: Path,
) -> None:
    payload = json.loads(BOUNDED_ORACLE_PATH.read_text(encoding="utf-8"))
    del payload["representation_schema"]
    path = tmp_path / "no_schema.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OracleLoadError, match=r"missing \['representation_schema'\]"):
        load_accepted_inputs(path)


@pytest.mark.parametrize(
    ("block", "fragment"),
    [
        ({"version": SCHEMA_VERSION}, "missing"),
        ({"hash": SCHEMA_HASH}, "missing"),
        ({"version": None, "hash": SCHEMA_HASH}, "representation_schema.version"),
        ({"version": SCHEMA_VERSION, "hash": 17}, "representation_schema.hash"),
    ],
    ids=["no-hash", "no-version", "null-version", "non-string-hash"],
)
def test_a_malformed_declaration_is_refused(
    tmp_path: Path, block: dict[str, object], fragment: str
) -> None:
    payload = json.loads(BOUNDED_ORACLE_PATH.read_text(encoding="utf-8"))
    payload["representation_schema"] = block
    path = tmp_path / "bad_schema.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(OracleLoadError, match=fragment):
        load_accepted_inputs(path)


@pytest.mark.parametrize(
    ("version", "hash_", "fragment"),
    [
        (OTHER_VERSION, SCHEMA_HASH, "build implements"),
        (SCHEMA_VERSION, OTHER_HASH, "committed union hashes to"),
        ("", "", "build implements"),
    ],
    ids=["unknown-version", "tampered-hash", "blank"],
)
def test_an_unsupported_declaration_is_reported(
    version: str, hash_: str, fragment: str
) -> None:
    candidate = candidate_of(
        RELEASE_BINDING,
        build_ledger(),
        build_representation(),
        schema_version=version,
        schema_hash=hash_,
    )
    assert any(fragment in v for v in validate_schema_binding(candidate))


def test_tampering_with_the_persisted_declaration_is_detected(
    session: Session,
) -> None:
    """The header columns are covered by verification and by the digest.

    A tampered declaration leaves every semantic row untouched, so without this
    coverage the projection would verify and digest identically while claiming a
    different union.
    """
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()
    before = compute_persisted_state_digest(session, identified.projection_uuid)
    assert not verify_persisted_state(session, identified.projection_uuid)

    session.execute(
        update(MechanicalProjectionORM)
        .where(MechanicalProjectionORM.projection_uuid == identified.projection_uuid)
        .values(representation_schema_version=OTHER_VERSION)
    )
    session.flush()

    assert compute_persisted_state_digest(session, identified.projection_uuid) != before
    assert verify_persisted_state(session, identified.projection_uuid)


# ---------------------------------------------------------------------------
# 5. Oracle comparison covers the declaration
# ---------------------------------------------------------------------------


def test_the_declaration_is_identity_bearing_in_the_oracle() -> None:
    oracle = load_accepted_inputs(BOUNDED_ORACLE_PATH).oracle
    assert oracle_payload(oracle)["representation_schema"] == {
        "version": SCHEMA_VERSION,
        "hash": SCHEMA_HASH,
    }
    assert oracle_payload(replace(oracle, schema_version=OTHER_VERSION)) != (
        oracle_payload(oracle)
    )


def test_the_gate_refuses_a_projection_whose_union_differs_from_the_oracle(
    session: Session, committed_oracle
) -> None:  # type: ignore[no-untyped-def]
    """Oracle and projection must name one union, and it must be this build's."""
    identified = identify_projection(
        candidate_of(
            RELEASE_BINDING,
            build_ledger(),
            build_representation(),
            schema_version=OTHER_VERSION,
            schema_hash=OTHER_HASH,
        )
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()

    result = run_publication_gate(
        session, identified.projection_uuid, oracle=committed_oracle
    )
    assert not result.passed
    assert GateFailureCategory.SCHEMA_MISMATCH in {f.category for f in result.failures}


# ---------------------------------------------------------------------------
# 6. Audit-only metadata stays outside identity; the payload is structural
# ---------------------------------------------------------------------------


def test_the_schema_payload_describes_the_declared_contract() -> None:
    """Derived from the declared types, so it moves only when they do."""
    payload = representation_schema_payload()
    families = {f["family"] for f in payload["fact_families"]}  # type: ignore[union-attr]
    assert "advantage" in families and "state_effect" in families
    # Nested value objects appear with their own structure, not just a name:
    # adding a field to RollSpec must change the contract.
    rollspec = next(
        v
        for v in payload["value_objects"]  # type: ignore[union-attr]
        if v["name"] == "RollSpec"
    )
    assert {f["name"] for f in rollspec["fields"]} == {"actor", "context", "ability"}
    # Vocabularies the drafts use directly are included even though no fact
    # field reaches them.
    names = {v["name"] for v in payload["vocabularies"]}  # type: ignore[union-attr]
    assert {"RecordKind", "RelationshipKind", "ComponentHandling"} <= names


def test_the_schema_hash_is_a_declared_contract_not_a_file_digest() -> None:
    """Two calls agree, and the value is not the module's bytes.

    A source-file hash would remint every projection for a comment, a docstring,
    or a rename. This is derived from the declared families, fields, nested
    value objects, and closed vocabularies instead.
    """
    assert representation_schema_hash() == representation_schema_hash()
    source = (
        Path(__file__).resolve().parents[3]
        / "src/afterworlds/ingestion/mechanical/representation.py"
    ).read_bytes()
    assert representation_schema_hash() not in source.decode("utf-8", "ignore")


#: Change-detector, not authority: the tests above prove the *behaviour*, and
#: this makes an unintended union change legible in one failure message instead
#: of as a wall of moved identities.
#:
#: Updated deliberately in review round 3. Canonicalizing the payload by
#: semantic key changed its byte representation without changing the contract it
#: describes, so the value moves and the version does not: this is still the
#: unmerged initial contract, and nothing accepted, persisted, or published
#: exists under it.
EXPECTED_SCHEMA_HASH = (
    "09dcd290ba6b24b80f6f74c922103f8b39865f609f8b9407271c92c0aac39066"
)


def test_the_committed_union_still_hashes_to_its_recorded_value() -> None:
    assert representation_schema_hash() == EXPECTED_SCHEMA_HASH, (
        "the closed representation contract changed; bump "
        "REPRESENTATION_SCHEMA_VERSION and update this canary deliberately"
    )


def test_audit_metadata_stays_outside_the_schema_identity(session: Session) -> None:
    """Reviewer, timestamp, and batch evidence still reach no identity.

    The new declaration must not have widened what identity covers: a
    re-review that changes nothing semantic still cannot remint a projection.
    """
    base = candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    reviewed_again = replace(
        base,
        classification=replace(
            base.classification,
            acceptances=tuple(
                replace(a, reviewer="someone-else", accepted_at="2030-01-01T00:00:00Z")
                for a in base.classification.acceptances
            ),
        ),
    )
    assert (
        identify_projection(reviewed_again).projection_uuid
        == identify_projection(base).projection_uuid
    )


def test_the_schema_hash_does_not_cover_invariant_behaviour() -> None:
    """Why the version carries a manual obligation the hash cannot.

    The hash is derived from declared structure, deliberately: hashing checker
    implementations would remint authority for a refactor. The cost is that an
    invariant change which narrows the admitted value set — rejecting a
    ``THRESHOLD_LOWERED`` threshold of 20, say — leaves every family, field, and
    vocabulary identical and therefore leaves the hash identical too.

    This test states that gap as a fact rather than leaving it to be discovered:
    two builds admitting different value sets can share a hash, so
    ``REPRESENTATION_SCHEMA_VERSION`` must be bumped by hand when an invariant
    changes meaning. Nothing here can enforce that; what it can do is stop the
    gap from being invisible.
    """
    payload = representation_schema_payload()
    rendered = json.dumps(payload)
    # The declared contract mentions the family and its field...
    assert "critical_hit_rule" in rendered
    assert "threshold" in rendered
    # ...and says nothing about which values that field may take.
    assert "19" not in rendered and "ordinary" not in rendered
    # The vacuity fix that prompted this note left the hash untouched.
    assert representation_schema_hash() == EXPECTED_SCHEMA_HASH


# ---------------------------------------------------------------------------
# Canonicalization — the schema describes a contract, not a source layout
# ---------------------------------------------------------------------------
#
# Review round 3 (Codex P2). Every collection in the schema payload is named or
# set-like in meaning, so each is ordered by its own semantic key. The rule has
# two halves and both are load-bearing: reordering declarations must leave the
# contract identical, and changing what the contract *admits* must still move
# it. Failing the first half would remint stored authority for an edit that
# changed no meaning — and, because the version must be bumped whenever the hash
# moves, would do it under a version bump that says nothing changed.


@dataclass(frozen=True)
class _Declared:
    alpha: int
    beta: str | None = None


@dataclass(frozen=True)
class _Reordered:
    """The same named-field contract, declared the other way round."""

    beta: str | None = None
    alpha: int = 0


@dataclass(frozen=True)
class _Renamed:
    alpha: int
    gamma: str | None = None


@dataclass(frozen=True)
class _Retyped:
    alpha: str
    beta: str | None = None


@dataclass(frozen=True)
class _Widened:
    alpha: int
    beta: str | None = None
    delta: int = 0


def test_field_declaration_order_does_not_reach_the_contract() -> None:
    """The defect: the field builder preserved dataclass declaration order."""
    assert _declared_fields(_Declared) == _declared_fields(_Reordered)


@pytest.mark.parametrize(
    ("other", "what"),
    [(_Renamed, "rename"), (_Retyped, "retype"), (_Widened, "added field")],
)
def test_a_real_field_change_still_moves_the_contract(other: type, what: str) -> None:
    assert _declared_fields(_Declared) != _declared_fields(other), what


class _Vocab(StrEnum):
    X = "x"
    Y = "y"


class _VocabReordered(StrEnum):
    """The same admissible values, declared the other way round."""

    Y = "y"
    X = "x"


class _VocabWidened(StrEnum):
    X = "x"
    Y = "y"
    Z = "z"


def _vocab_members(name: str) -> list[str]:
    return next(
        v["members"]
        for v in representation_schema_payload()["vocabularies"]  # type: ignore[union-attr]
        if v["name"] == name
    )


def test_vocabulary_declaration_order_does_not_reach_the_contract() -> None:
    """The analogous defect on the vocabulary half of the payload."""
    assert sorted(m.value for m in _Vocab) == sorted(m.value for m in _VocabReordered)
    # DieSize is declared d4, d6, d8, d10, d12, d20, d100 — not value order — so
    # it is the real vocabulary that proves the payload no longer follows it.
    assert _vocab_members("DieSize") == sorted(_vocab_members("DieSize"))
    assert _vocab_members("DieSize") != [d.value for d in DieSize]


def test_adding_or_removing_a_vocabulary_value_still_moves_the_contract() -> None:
    base = sorted(m.value for m in _Vocab)
    assert base != sorted(m.value for m in _VocabWidened)
    assert base != base[:-1]


def test_every_collection_in_the_payload_is_canonically_ordered() -> None:
    """The rule stated once, over the real contract rather than a fixture."""
    payload = representation_schema_payload()

    families = [f["family"] for f in payload["fact_families"]]  # type: ignore[union-attr]
    assert families == sorted(families)

    vocab_names = [v["name"] for v in payload["vocabularies"]]  # type: ignore[union-attr]
    assert vocab_names == sorted(vocab_names)
    for entry in payload["vocabularies"]:  # type: ignore[union-attr]
        assert entry["members"] == sorted(entry["members"])

    object_names = [v["name"] for v in payload["value_objects"]]  # type: ignore[union-attr]
    assert object_names == sorted(object_names)

    for holder in (*payload["fact_families"], *payload["value_objects"]):  # type: ignore[misc]
        names = [f["name"] for f in holder["fields"]]
        assert names == sorted(names), holder


def test_the_rendered_type_survives_the_field_sort() -> None:
    """Sorting is by name; the declared type must still travel with it."""
    rollspec = next(
        v
        for v in representation_schema_payload()["value_objects"]  # type: ignore[union-attr]
        if v["name"] == "RollSpec"
    )
    assert {f["name"]: f["type"] for f in rollspec["fields"]} == {
        "ability": "AbilityScore|None",
        "actor": "RollActor",
        "context": "RollContext",
    }


# ---------------------------------------------------------------------------
# Closed value objects validate the exact declared runtime type
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _RollSpecSubclass(RollSpec):
    """A dataclass subclass carrying a field the closed contract never declared."""

    smuggled: str = "extra"


def test_an_exact_rollspec_validates() -> None:
    assert not fact_invariant_violations(
        AdvantageFact(
            AdvantageState.DISADVANTAGE,
            RollSpec(
                RollActor.SUBJECT, RollContext.SAVING_THROW, AbilityScore.DEXTERITY
            ),
        )
    )


def test_a_rollspec_subclass_is_rejected() -> None:
    """``isinstance`` accepted it; the closed contract does not.

    Every sibling value object routes its type test through the shared
    exact-type seam. ``RollSpec`` was the one that did not.
    """
    violations = fact_invariant_violations(
        AdvantageFact(
            AdvantageState.DISADVANTAGE,
            _RollSpecSubclass(
                RollActor.SUBJECT, RollContext.SAVING_THROW, AbilityScore.DEXTERITY
            ),
        )
    )
    assert any("must be RollSpec" in v for v in violations), violations


def test_a_subclass_is_rejected_during_representation_validation() -> None:
    """Through the production validator, not only the family checker."""
    draft = replace(
        UNAFFECTED_ONLY,
        components=(
            replace(
                UNAFFECTED_ONLY.components[0],
                facts=(
                    AdvantageFact(
                        AdvantageState.DISADVANTAGE,
                        _RollSpecSubclass(RollActor.SUBJECT, RollContext.ATTACK_ROLL),
                    ),
                ),
            ),
        ),
    )
    findings = validate_representation(draft, build_ledger(), bound_corpus())
    assert any("must be RollSpec" in f for f in findings), findings


def test_validation_cannot_approve_what_reconstruction_cannot_rebuild() -> None:
    """The property the fix exists to restore.

    The subclass serializes its extra field, so before the fix validation
    reported nothing while ``fact_from_payload`` refused the same fact — a
    candidate that could persist and then fail to reconstruct.
    """
    fact = AdvantageFact(
        AdvantageState.DISADVANTAGE,
        _RollSpecSubclass(RollActor.SUBJECT, RollContext.ATTACK_ROLL),
    )
    payload = fact_payload(fact)
    assert "smuggled" in payload["roll"]  # type: ignore[operator]
    with pytest.raises(MalformedFactPayloadError):
        fact_from_payload(payload)
    # Validation now refuses it too, so the two halves agree.
    assert fact_invariant_violations(fact)
