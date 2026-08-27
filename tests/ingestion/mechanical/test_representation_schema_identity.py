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

import importlib.util
import json
import sys
from dataclasses import dataclass, field, fields, is_dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any, Optional, cast, get_args, get_type_hints

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from afterworlds.ingestion.corpus.hashing import canonical_bytes
from afterworlds.ingestion.mechanical import representation
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
    SCHEMA_2_VERSION,
    UnsupportedSchemaVersionError,
    identify_projection,
    projection_payload,
    representation_payload,
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
    FactFamily,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    RollActor,
    RollContext,
    RollSpec,
    UnsupportedRepresentationShapeError,
    _wire_fields,
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

#: A declaration this build does not implement. Used only where nothing is
#: serialized *under* it — an arbitrary version must still move a projection
#: identity, which does not ask this build to produce a component payload shaped
#: for a union it has never seen.
#:
#: It is NOT usable against ``oracle_payload`` any more. Since D-2 that
#: canonicalizes under the artifact's own declaration, so an unimplemented
#: version fails closed there rather than quietly borrowing the current shape —
#: asserted by
#: ``test_an_oracle_declaring_a_union_this_build_cannot_serialize_fails_closed``.
OTHER_VERSION = "5d-representation-schema-99"
OTHER_HASH = "9" * 64

#: The real contract schema 3 succeeded, for everything that does serialize.
#: Since PR #157 round 9 a payload can only be produced under a version this
#: build has a component key set for — a fabricated one fails closed rather
#: than silently borrowing the current shape, which is what it used to do.
#: Schema 2 is the truer stand-in anyway: an actual superseded union, not a
#: hypothetical one.
PRIOR_VERSION = SCHEMA_2_VERSION
PRIOR_HASH = "ca27a7468abb84db43781e96ac48fbc55e166c3e410fe33d80f03a263a8d002c"  # noqa: E501  # pragma: allowlist secret


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
    added or reshaped: the records block and the component's own facts
    serialize byte-identically under both contracts. Without the schema
    declaration in the payload, that would carry the same UUID under two
    different unions.

    The whole-payload equality this once asserted was only ever satisfiable
    because a fabricated version silently borrowed the current component
    shape — the borrowing that PR #157 round 9 removed. Every merged version
    now has a distinct component key set by construction
    (``test_no_two_merged_versions_share_a_key_set``), which is a stronger
    guarantee than the one this test needed: content alone can no longer
    collide across contracts even before the declaration is consulted.
    """
    here = candidate_of(RELEASE_BINDING, build_ledger(), UNAFFECTED_ONLY)
    there = replace(here, schema_version=PRIOR_VERSION, schema_hash=PRIOR_HASH)
    here_repr = projection_payload(here)["representation"]
    there_repr = projection_payload(there)["representation"]

    # The content really is identical — this is what made the omission
    # invisible. Asserted where it holds: the records, and the facts inside the
    # component, are the same bytes under both unions.
    assert here_repr["records"] == there_repr["records"]  # type: ignore[index]
    (here_component,) = here_repr["components"]  # type: ignore[index]
    (there_component,) = there_repr["components"]  # type: ignore[index]
    assert here_component["facts"] == there_component["facts"]

    assert (
        identify_projection(here).projection_uuid
        != identify_projection(there).projection_uuid
    )


def test_two_schema_versions_reidentify_the_bounded_fixture() -> None:
    base = candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    other = replace(base, schema_version=PRIOR_VERSION, schema_hash=PRIOR_HASH)
    assert (
        identify_projection(base).projection_uuid
        != identify_projection(other).projection_uuid
    )


def test_the_version_and_the_hash_each_move_the_identity() -> None:
    """Both halves are identity-bearing, not just whichever one a test perturbs."""
    base = candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    uuid_ = identify_projection(base).projection_uuid
    # The version half must name a contract this build can serialize; the hash
    # half is free to be arbitrary, because nothing is serialized under it.
    only_version = replace(base, schema_version=PRIOR_VERSION)
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
        schema_version=PRIOR_VERSION,
        schema_hash=PRIOR_HASH,
    )
    identified = identify_projection(stale)
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert (rebuilt.schema_version, rebuilt.schema_hash) == (PRIOR_VERSION, PRIOR_HASH)
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
            schema_version=PRIOR_VERSION,
            schema_hash=PRIOR_HASH,
        )
    )
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.classification.policy_version  # policy still stated
    assert rebuilt.schema_version == PRIOR_VERSION  # and now the union too


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
        .values(representation_schema_version=PRIOR_VERSION)
    )
    session.flush()

    assert compute_persisted_state_digest(session, identified.projection_uuid) != before
    assert verify_persisted_state(session, identified.projection_uuid)


def test_tampering_the_declaration_to_an_unknown_union_is_reported_not_raised(
    session: Session,
) -> None:
    """The other tamper shape, and it must still come back as a finding.

    Since PR #157 round 9 a payload cannot be produced under a version this
    build has no key set for. That is deliberate — no identity is derived under
    an unrecognised contract — but ``verify_persisted_state`` collects findings
    for a caller, so raising past it would destroy the rest of the report. The
    refusal and the report are the same act here.
    """
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), build_representation())
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()
    assert not verify_persisted_state(session, identified.projection_uuid)

    session.execute(
        update(MechanicalProjectionORM)
        .where(MechanicalProjectionORM.projection_uuid == identified.projection_uuid)
        .values(representation_schema_version=OTHER_VERSION)
    )
    session.flush()

    findings = verify_persisted_state(session, identified.projection_uuid)
    assert findings
    assert any(OTHER_VERSION in f for f in findings)


# ---------------------------------------------------------------------------
# 5. Oracle comparison covers the declaration
# ---------------------------------------------------------------------------


def test_the_declaration_is_identity_bearing_in_the_oracle() -> None:
    """Two declarations over one accepted content are two oracle payloads.

    The perturbed declaration is a **real superseded union**, not a fabricated
    one. It used to be ``OTHER_VERSION`` — an arbitrary string — on the reasoning
    that "nothing is serialized under it". That reasoning ended when
    ``oracle_payload`` began canonicalizing under the artifact's own declaration
    (D-2): the version is no longer inert here, so a version this build cannot
    serialize now fails closed instead of quietly borrowing the current shape.

    That refusal is asserted too, immediately below, because it is the property
    D-2 exists to give.
    """
    oracle = load_accepted_inputs(BOUNDED_ORACLE_PATH).oracle
    assert oracle_payload(oracle)["representation_schema"] == {
        "version": SCHEMA_VERSION,
        "hash": SCHEMA_HASH,
    }
    superseded = replace(oracle, schema_version=PRIOR_VERSION, schema_hash=PRIOR_HASH)
    assert oracle_payload(superseded) != oracle_payload(oracle)
    assert oracle_payload(superseded)["representation_schema"] == {
        "version": PRIOR_VERSION,
        "hash": PRIOR_HASH,
    }


def test_an_oracle_declaring_a_union_this_build_cannot_serialize_fails_closed() -> None:
    """D-2's fail-closed half.

    An accepted artifact naming a contract this build has never seen cannot be
    canonicalized honestly, and the alternative — serializing it under whatever
    the build currently implements — is exactly the silent re-identification
    Owner Decision 2026-08-20 refused for components.
    """
    oracle = load_accepted_inputs(BOUNDED_ORACLE_PATH).oracle
    with pytest.raises(UnsupportedSchemaVersionError):
        oracle_payload(replace(oracle, schema_version=OTHER_VERSION))


def test_the_gate_refuses_a_projection_whose_union_differs_from_the_oracle(
    session: Session, committed_oracle
) -> None:  # type: ignore[no-untyped-def]
    """Oracle and projection must name one union, and it must be this build's."""
    identified = identify_projection(
        candidate_of(
            RELEASE_BINDING,
            build_ledger(),
            build_representation(),
            schema_version=PRIOR_VERSION,
            schema_hash=PRIOR_HASH,
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


def _facts() -> list[dict[str, Any]]:
    return cast("list[dict[str, Any]]", representation_schema_payload()["facts"])


def _family(name: str) -> dict[str, Any]:
    return next(f for f in _facts() if f["family"] == name)


def _field(holder: dict[str, Any], name: str) -> dict[str, Any]:
    return next(f for f in holder["fields"] if f["name"] == name)


def _draft_vocabularies() -> list[dict[str, Any]]:
    payload = representation_schema_payload()
    return cast("list[dict[str, Any]]", payload["draft_vocabularies"])


def test_the_schema_payload_describes_the_serialized_contract() -> None:
    """Derived from the declared types, rendered as what a payload can show."""
    families = {f["family"] for f in _facts()}
    assert "advantage" in families and "state_effect" in families

    roll = _field(_family("advantage"), "roll")
    # A nested value object appears *inlined*, carrying its own structure —
    # adding a field to RollSpec must change the contract, and there is no
    # class name standing in for it.
    assert roll["shape"]["kind"] == "object"
    assert {f["name"] for f in roll["shape"]["fields"]} == {
        "actor",
        "context",
        "ability",
        "skill",
    }
    # A post-schema-3 field states its omission rule in the contract itself.
    # The rule is part of the serialized grammar — a reader has to know that
    # this key's absence is a declared state rather than lost content — so
    # changing it has to move the identity rather than pass unnoticed.
    skill = _field(roll["shape"], "skill")
    assert skill["omitted_when_empty"] is True
    assert skill["introduced_in"] == "5d-representation-schema-4"
    # Fields that predate schema 4 carry no such flag: their unconditional
    # emission is what holds the committed conditions-1 identities still.
    assert "omitted_when_empty" not in _field(roll["shape"], "ability")
    # The enum inside is its admitted value set, and its optionality is a flag
    # rather than the Python spelling ``| None``.
    ability = _field(roll["shape"], "ability")
    assert ability["shape"]["kind"] == "enum"
    assert ability["shape"]["nullable"] is True
    assert "charisma" in ability["shape"]["values"]

    # Vocabularies the drafts use directly appear at their serialized path,
    # which is what a reader of a payload actually has.
    assert {v["path"] for v in _draft_vocabularies()} == {
        "components[].handling",
        "provenance[].role",
        "provenance[].target_kind",
        "records[].kind",
        "relationships[].kind",
    }


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
#: Updated deliberately in review round 4. Rendering the payload as the
#: canonical *wire* contract — no class names, explicit nullability, arrays
#: instead of ``tuple``, vocabularies keyed by serialized path — changed its
#: byte representation without changing the contract it describes, so the value
#: moves and the version does not: this is still the unmerged initial contract,
#: and nothing accepted, persisted, or published exists under it.
EXPECTED_SCHEMA_HASH = "e1fed378a23e5984ddcc7f0fc08e03118fe05db1594e31b449facdf12fdadbc9"  # noqa: E501  # pragma: allowlist secret


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
    rendered = json.dumps(representation_schema_payload())
    # The declared contract names the family and its field...
    assert "critical_hit_rule" in rendered
    assert "threshold" in rendered
    # ...and says nothing about which values that field may take.
    assert "19" not in rendered and "ordinary" not in rendered
    # The vacuity fix that prompted this note left the hash untouched.
    assert representation_schema_hash() == EXPECTED_SCHEMA_HASH


# ---------------------------------------------------------------------------
# The identity describes the canonical wire contract, not the Python that
# expresses it
# ---------------------------------------------------------------------------
#
# Review round 4 (Codex P2). The rule has two halves and both are load-bearing:
# a change no payload can observe must leave identity untouched, and a change
# any payload *can* observe must move it. Failing the first half remints stored
# authority for a refactor — and, because the version must be bumped whenever
# the hash moves, does it under a bump asserting a contract change that never
# happened. Failing the second half is worse: two different contracts sharing
# one identity is the defect the whole mechanism exists to prevent.
#
# Invariance is proved with locally declared doubles whose Python *names* differ
# and whose wire contract does not; sensitivity is proved against those doubles
# and, where it can be, against the real union.


class _WireVocab(StrEnum):
    X = "x"
    Y = "y"


class _WireVocabRenamed(StrEnum):
    """The same admitted values under a different Python name."""

    X = "x"
    Y = "y"


class _WireVocabWidened(StrEnum):
    X = "x"
    Y = "y"
    Z = "z"


@dataclass(frozen=True)
class _WireNested:
    alpha: int
    beta: _WireVocab | None = None


@dataclass(frozen=True)
class _WireNestedRenamed:
    """The same nested contract; only the class and its enum are renamed."""

    alpha: int
    beta: _WireVocabRenamed | None = None


@dataclass(frozen=True)
class _WireNestedReshaped:
    """A field added *inside* the nested object — invisible to a name."""

    alpha: int
    beta: _WireVocab | None = None
    added: int = 0


@dataclass(frozen=True)
class _Holder:
    flag: bool
    nested: _WireNested
    tags: tuple[_WireVocab, ...] = ()


@dataclass(frozen=True)
class _HolderRenamed:
    """Every class in reach renamed; not one serialized name changed."""

    flag: bool
    nested: _WireNestedRenamed
    tags: tuple[_WireVocabRenamed, ...] = ()


@dataclass(frozen=True)
class _HolderReordered:
    """The same named-field contract, declared the other way round."""

    nested: _WireNested = _WireNested(0)
    tags: tuple[_WireVocab, ...] = ()
    flag: bool = False


@dataclass(frozen=True)
class _HolderListSpelled:
    """``list[X]`` where the original says ``tuple[X, ...]`` — one JSON array."""

    flag: bool
    nested: _WireNested
    tags: list[_WireVocab] = field(default_factory=list)


@dataclass(frozen=True)
class _HolderOptionalSpelled:
    """``Optional[X]`` where the original says ``X | None``."""

    alpha: int
    beta: Optional[_WireVocab] = None  # noqa: UP045 - the point of the test


@dataclass(frozen=True)
class _HolderNestedReshaped:
    flag: bool
    nested: _WireNestedReshaped
    tags: tuple[_WireVocab, ...] = ()


@dataclass(frozen=True)
class _HolderFieldAdded:
    flag: bool
    nested: _WireNested
    tags: tuple[_WireVocab, ...] = ()
    added: int = 0


@dataclass(frozen=True)
class _HolderFieldRenamed:
    banner: bool
    nested: _WireNested
    tags: tuple[_WireVocab, ...] = ()


@dataclass(frozen=True)
class _HolderFieldRetyped:
    flag: str
    nested: _WireNested
    tags: tuple[_WireVocab, ...] = ()


@dataclass(frozen=True)
class _HolderFieldNullable:
    flag: bool | None
    nested: _WireNested
    tags: tuple[_WireVocab, ...] = ()


@dataclass(frozen=True)
class _HolderScalarNotArray:
    flag: bool
    nested: _WireNested
    tags: _WireVocab = _WireVocab.X


@dataclass(frozen=True)
class _HolderVocabWidened:
    flag: bool
    nested: _WireNested
    tags: tuple[_WireVocabWidened, ...] = ()


# --- must be invariant -----------------------------------------------------


def test_renaming_every_python_class_in_reach_leaves_the_contract() -> None:
    """I1/I2/I3, the reported defect.

    ``_HolderRenamed`` renames the holder, the nested value object, and the
    enum. No serialized name changes, so no payload could tell the two apart —
    and neither may the identity.
    """
    assert _wire_fields(_Holder) == _wire_fields(_HolderRenamed)


def test_a_family_entry_has_nowhere_to_put_a_class_name() -> None:
    """I1 on the real union: the entry *is* its discriminator plus its fields.

    The old payload carried ``fact_families[].type``, the fact class's Python
    name, which nothing serialized and nothing read back. There is no such slot
    now, so a fact class rename cannot reach identity through one.
    """
    for entry in _facts():
        assert set(entry) == {"family", "fields"}


def test_declaration_order_does_not_reach_the_contract() -> None:
    """I4/I5: fields sorted by name, vocabulary values sorted by value."""
    assert _wire_fields(_Holder) == _wire_fields(_HolderReordered)
    # DieSize is declared d4, d6, d8, d10, d12, d20, d100 — not value order — so
    # it is the real vocabulary that proves the payload no longer follows it.
    die = _field(_family("resource_recovery"), "recharge_die")["shape"]["values"]
    assert die == sorted(die)
    assert die != [d.value for d in DieSize]


def test_tuple_and_list_are_the_same_array_contract() -> None:
    """I6, grounded rather than asserted.

    The claim is only true because the canonical serializer maps both to the
    same JSON array, so that is checked here alongside the descriptor.
    """
    assert canonical_bytes((_WireVocab.X,)) == canonical_bytes([_WireVocab.X])
    assert _wire_fields(_Holder) == _wire_fields(_HolderListSpelled)


def test_optional_spellings_agree() -> None:
    """I7: ``Optional[X]`` and ``X | None`` are one nullable shape."""
    assert _wire_fields(_WireNested) == _wire_fields(_HolderOptionalSpelled)


def test_prose_only_edits_leave_the_hash(tmp_path: Path) -> None:
    """I8: a docstring or comment edit is not a contract change.

    Proved by rebuilding the descriptor from a copy of the module whose
    docstrings and comments differ, rather than by asserting the hash is stable
    across a run in which nothing was edited at all.
    """
    source = (
        Path(__file__).resolve().parents[3]
        / "src/afterworlds/ingestion/mechanical/representation.py"
    ).read_text(encoding="utf-8")
    edited = source.replace(
        '"""SHA-256 of the closed representation contract."""',
        '"""SHA-256 of the closed representation contract. Reworded."""',
        1,
    )
    assert edited != source
    module_path = tmp_path / "edited_representation.py"
    module_path.write_text(edited, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("edited_representation", module_path)
    assert spec is not None and spec.loader is not None
    edited_module = importlib.util.module_from_spec(spec)
    # Registered before execution because ``@dataclass`` resolves its own
    # module through ``sys.modules``; removed after, so nothing else sees it.
    sys.modules[spec.name] = edited_module
    try:
        spec.loader.exec_module(edited_module)
        assert (
            edited_module.representation_schema_hash() == representation_schema_hash()
        )
    finally:
        del sys.modules[spec.name]


# --- must move identity ----------------------------------------------------


def test_a_changed_family_discriminator_moves_the_contract() -> None:
    """M1. The discriminator is what ``fact_from_payload`` dispatches on."""
    payload = representation_schema_payload()
    assert any(f["family"] == "advantage" for f in _facts())
    moved = json.loads(json.dumps(payload))
    for entry in moved["facts"]:
        if entry["family"] == "advantage":
            entry["family"] = "advantage_renamed"
    assert canonical_bytes(moved) != canonical_bytes(payload)


@pytest.mark.parametrize(
    ("other", "what"),
    [
        (_HolderFieldAdded, "M2 field added"),
        (_HolderFieldRenamed, "M3 field renamed"),
        (_HolderFieldRetyped, "M4 field retyped"),
        (_HolderFieldNullable, "M5 nullability added"),
        (_HolderScalarNotArray, "M6 array became a scalar"),
        (_HolderNestedReshaped, "M7 nested value object reshaped"),
        (_HolderVocabWidened, "M8 vocabulary value added"),
    ],
)
def test_an_observable_change_still_moves_the_contract(other: type, what: str) -> None:
    assert _wire_fields(_Holder) != _wire_fields(other), what


def test_a_removed_field_moves_the_contract() -> None:
    """M2, the other direction."""
    assert _wire_fields(_WireNested) != _wire_fields(_WireNestedReshaped)


def test_changing_a_draft_vocabulary_moves_the_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M9: the admitted values behind a draft path."""
    before = representation_schema_hash()
    monkeypatch.setitem(
        representation._DRAFT_VOCABULARIES, "records[].kind", _WireVocab
    )
    assert representation_schema_hash() != before


def test_changing_a_draft_path_moves_the_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M10: the path is the wire role, so moving it is a contract change."""
    before = representation_schema_hash()
    patched = dict(representation._DRAFT_VOCABULARIES)
    patched["records[].record_kind"] = patched.pop("records[].kind")
    monkeypatch.setattr(representation, "_DRAFT_VOCABULARIES", patched)
    assert representation_schema_hash() != before


# --- structural integrity --------------------------------------------------


def test_every_collection_in_the_payload_is_canonically_ordered() -> None:
    """S1, over the real contract rather than a fixture."""
    payload = representation_schema_payload()
    families = [f["family"] for f in _facts()]
    assert families == sorted(families)

    paths = [v["path"] for v in _draft_vocabularies()]
    assert paths == sorted(paths)
    for entry in _draft_vocabularies():
        assert entry["shape"]["values"] == sorted(entry["shape"]["values"])

    def walk(shape: dict[str, Any]) -> None:
        if shape["kind"] == "enum":
            assert shape["values"] == sorted(shape["values"]), shape
        elif shape["kind"] == "object":
            names = [f["name"] for f in shape["fields"]]
            assert names == sorted(names), shape
            for nested in shape["fields"]:
                walk(nested["shape"])
        elif shape["kind"] == "array":
            walk(shape["items"])

    for entry in _facts():
        names = [f["name"] for f in entry["fields"]]
        assert names == sorted(names), entry
        for declared in entry["fields"]:
            walk(declared["shape"])
    assert payload["representation_schema_version"] == REPRESENTATION_SCHEMA_VERSION


def test_no_python_class_name_appears_in_the_contract() -> None:
    """S2, the canary that would have caught this finding.

    Supplementary to the behavioural rename tests above, not a substitute for
    them: a substring scan proves today's names are absent, while
    ``test_renaming_every_python_class_in_reach_leaves_the_contract`` proves the
    property that makes tomorrow's absent too.
    """
    rendered = json.dumps(representation_schema_payload())
    names = {
        obj.__name__
        for obj in vars(representation).values()
        if isinstance(obj, type) and (issubclass(obj, StrEnum) or is_dataclass(obj))
    }
    assert len(names) > 50, "the scan found almost nothing; it is not looking"
    assert sorted(n for n in names if n in rendered) == []


def test_every_family_is_described_exactly_once() -> None:
    """S3."""
    families = [f["family"] for f in _facts()]
    assert sorted(families) == sorted(f.value for f in FactFamily)
    assert len(families) == len(set(families))


def test_every_declared_draft_path_resolves_in_a_real_payload() -> None:
    """S4: the guard that makes the hand-written path table honest.

    The table lives in ``representation.py`` and the payload is built in
    ``projection.py``, so nothing but this test stops the two from drifting —
    a moved key would otherwise leave the descriptor naming a path nothing
    emits, silently. Each collection must be non-empty and every element must
    carry the key, or the resolution would pass by describing nothing.
    """
    payload = representation_payload(build_representation())
    for entry in _draft_vocabularies():
        collection, _, key = entry["path"].partition("[].")
        items = cast("list[dict[str, Any]]", payload[collection])
        assert items, f"{entry['path']}: {collection} is empty; nothing is proved"
        for item in items:
            assert key in item, f"{entry['path']}: absent from {sorted(item)}"
            assert (
                item[key] in entry["shape"]["values"]
            ), f"{entry['path']}: {item[key]!r} is outside the declared values"


@pytest.mark.parametrize(
    "annotation",
    [float, dict[str, int], int | str, tuple[int, str], set[int]],
)
def test_an_undescribable_annotation_fails_closed(annotation: object) -> None:
    """S5. The alternative is a silent fallback to a Python name."""
    with pytest.raises(UnsupportedRepresentationShapeError):
        representation._shape(annotation)


def test_primitives_are_matched_by_exact_type_not_by_subclass() -> None:
    """S5's companion: the two collapses that would fail silently.

    ``bool`` is a subclass of ``int`` and every ``StrEnum`` is a subclass of
    ``str``, so a subclass test would render 33 distinct closed vocabularies as
    one unconstrained string — different contracts sharing one identity, with
    no error raised anywhere.
    """
    assert representation._shape(bool) == {"kind": "boolean"}
    assert representation._shape(int) == {"kind": "integer"}
    assert representation._shape(str) == {"kind": "string"}
    assert representation._shape(_WireVocab) == {"kind": "enum", "values": ["x", "y"]}


def test_no_two_closed_shapes_currently_collide() -> None:
    """S6: a change-detector, deliberately not an invariant.

    Structural identity means two vocabularies admitting the same values, or
    two value objects with the same fields, render identically — which is
    *wire-correct*, since neither carries a type tag and nothing reading a
    payload could distinguish them either. Today none collide. If that changes,
    this surfaces it as a decision to make rather than a silent merge; the
    answer may well be that the collision is fine.
    """
    vocabularies: dict[str, set[str]] = {}
    objects: dict[str, set[str]] = {}

    def collect(cls: type) -> None:
        hints = get_type_hints(cls)
        for declared in fields(cls):
            for part in (
                hints[declared.name],
                *get_args(hints[declared.name]),
            ):
                if not isinstance(part, type):
                    continue
                if issubclass(part, StrEnum):
                    vocabularies.setdefault(part.__name__, set()).update(
                        m.value for m in part
                    )
                elif is_dataclass(part) and part.__name__ not in objects:
                    objects[part.__name__] = {f.name for f in fields(part)}
                    collect(part)

    for family in FactFamily:
        collect(representation._FACT_TYPES[family])

    def duplicates(catalog: dict[str, set[str]]) -> list[str]:
        seen: dict[tuple[str, ...], str] = {}
        clashes = []
        for name, members in catalog.items():
            key = tuple(sorted(members))
            if key in seen:
                clashes.append(f"{seen[key]} vs {name}: {key}")
            seen[key] = name
        return clashes

    assert len(vocabularies) > 20 and len(objects) > 5, "the walk found too little"
    assert duplicates(vocabularies) == []
    assert duplicates(objects) == []
    # Two *families* do share a field shape; they stay distinct because
    # families are keyed by their discriminator. That pair is the concrete
    # reason the discriminator belongs in the descriptor.
    economy = _family("action_economy")["fields"]
    restriction = _family("action_restriction")["fields"]
    assert economy == restriction
    assert _family("action_economy") != _family("action_restriction")


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
    """The property the fix exists to restore, under the schema-4 serializer.

    This test used to assert the opposite serialization: ``asdict`` walked the
    *instance's* fields, so the subclass's extra key entered the canonical
    payload, and validation reported nothing while ``fact_from_payload`` refused
    the same fact.

    Schema 4's walker resolves an instance to the closed class it extends and
    emits only that class's declared fields, so undeclared state no longer
    reaches a payload at all. That is strictly narrower: an undeclared class can
    no longer inject a key into an identity. The property under test is
    unchanged and now holds from both directions — the payload carries only
    declared keys, and the gate still refuses the value rather than letting it
    persist as something reconstruction would reject.
    """
    fact = AdvantageFact(
        AdvantageState.DISADVANTAGE,
        _RollSpecSubclass(RollActor.SUBJECT, RollContext.ATTACK_ROLL),
    )
    payload = fact_payload(fact)
    # Undeclared state is invisible to identity rather than smuggled into it.
    assert "smuggled" not in payload["roll"]  # type: ignore[operator]
    assert set(payload["roll"]) == {"actor", "context", "ability"}  # type: ignore[arg-type]
    # ...and the gate is what stops the value reaching persistence at all.
    assert fact_invariant_violations(fact)
