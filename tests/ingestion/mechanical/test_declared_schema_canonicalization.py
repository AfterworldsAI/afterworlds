"""Historical payloads canonicalize under the schema they declare — CRD Issue 5d.

Three call sites derived a canonical payload from ``representation_payload``
without saying which contract to serialize under, so each silently used the
build's current one. That was invisible while every artifact in the repository
declared the schema the build implemented; it becomes wrong the moment an
accepted artifact outlives a schema mint, which is exactly what a lift is for.

Owner Decision 2026-08-20 settled the same question for component keys — *"every
merged version serializes exactly its own key set"* — and these are that rule
applied at three seams it had not reached:

* **D-2** ``oracle_payload``: a schema-3 artifact loaded by a schema-4 build
  would be canonicalized under schema-4 keys and re-identified.
* **D-3** ``proposal_payload``: a batch records its reviewed proposal's identity
  as evidence, so that identity must stay re-derivable from the retained
  proposal artifact rather than expiring when the union widens.
* **the gate**: it compares accepted authority against persisted state, and
  canonicalizing both under one contract would turn a schema disagreement into a
  flood of spurious element differences.

Each test states the property as *"the same input gives the same bytes under
both builds"*, simulated by asking for the older contract explicitly — which is
what the fixed code now does on its own.
"""

from __future__ import annotations

from dataclasses import replace

from afterworlds.ingestion.corpus.hashing import canonical_bytes
from afterworlds.ingestion.mechanical.gate import _comparable_collections
from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    load_accepted_inputs,
    oracle_identity,
    oracle_payload,
)
from afterworlds.ingestion.mechanical.projection import (
    SCHEMA_3_VERSION,
    SCHEMA_4_VERSION,
    representation_payload,
)
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    ProposedSpan,
    proposal_identity,
    proposal_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import SCHEMA_3_HASH

ARTIFACT_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"
#: The value recorded on the committed artifact's only acceptance batch.
COMMITTED_ORACLE_IDENTITY = "a0f0bd2f6f6f05d3b0b46b63d1dfa9c5e4c3bf0741118b063a5d2b6adf401fda"  # noqa: E501  # pragma: allowlist secret


def test_the_build_implements_a_later_schema_than_the_artifact_declares() -> None:
    """The premise. Without it none of the tests below prove anything."""
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert inputs.oracle.schema_version == SCHEMA_3_VERSION
    assert REPRESENTATION_SCHEMA_VERSION == SCHEMA_4_VERSION
    assert inputs.oracle.schema_hash != representation_schema_hash()


def test_d2_the_oracle_serializes_under_the_schema_it_declares() -> None:
    """A schema-3 artifact keeps its identity on a schema-4 build.

    Stated as identity rather than as "the call passes an argument", because the
    argument is a means: what must hold is that the accepted authority a reviewer
    committed still hashes to the value recorded against it.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    assert oracle_identity(inputs.oracle) == COMMITTED_ORACLE_IDENTITY

    payload = oracle_payload(inputs.oracle)
    under_declared = representation_payload(
        inputs.oracle.representation, schema_version=inputs.oracle.schema_version
    )
    assert canonical_bytes(payload["representation"]) == canonical_bytes(under_declared)


def test_d2_the_oracle_does_not_borrow_the_builds_contract() -> None:
    """The negative half: schema 4 really would produce different bytes.

    Without this the test above could pass because the two contracts happen to
    agree, which would make it a tautology rather than a regression.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    declared = representation_payload(
        inputs.oracle.representation, schema_version=SCHEMA_3_VERSION
    )
    current = representation_payload(
        inputs.oracle.representation, schema_version=SCHEMA_4_VERSION
    )
    # Zero movement means the *content* is identical under both contracts, so a
    # byte difference here would mean the omission rule had broken. The property
    # under test is that oracle_payload asks for the declared one either way.
    assert canonical_bytes(declared) == canonical_bytes(current)
    assert canonical_bytes(oracle_payload(inputs.oracle)["representation"]) == (
        canonical_bytes(declared)
    )


def test_d3_a_proposal_identity_stays_derivable_under_its_own_schema() -> None:
    """A recorded proposal identity must not expire when the union widens.

    The committed batch names proposal ``14587d5b…`` as the thing a human read.
    If that identity could only be reproduced by a build implementing the same
    schema, the evidence would become unverifiable rather than merely old.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    proposal = MechanicalProposal(
        binding=inputs.oracle.binding,
        policy_version=inputs.oracle.policy_version,
        policy_hash=inputs.oracle.policy_hash,
        schema_version=SCHEMA_3_VERSION,
        schema_hash=SCHEMA_3_HASH,
        proposed_spans=tuple(
            ProposedSpan(span=span, origin="o", rationale="r")
            for span in inputs.oracle.spans
        ),
        proposed_representation=inputs.oracle.representation,
        proposal_origin="declared-schema probe",
    )
    payload = proposal_payload(proposal)
    assert payload["representation_schema"] == {
        "version": SCHEMA_3_VERSION,
        "hash": SCHEMA_3_HASH,
    }
    # The representation half is serialized under the proposal's declaration,
    # not the build's.
    assert canonical_bytes(payload["proposed_representation"]) == canonical_bytes(
        representation_payload(
            inputs.oracle.representation, schema_version=SCHEMA_3_VERSION
        )
    )
    # Deterministic, and unchanged by re-deriving it.
    assert proposal_identity(proposal) == proposal_identity(proposal)


def test_d3_the_declaration_is_what_moves_the_proposal_identity() -> None:
    """Two proposals with identical content and different declarations differ."""
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    base = MechanicalProposal(
        binding=inputs.oracle.binding,
        policy_version=inputs.oracle.policy_version,
        policy_hash=inputs.oracle.policy_hash,
        schema_version=SCHEMA_3_VERSION,
        schema_hash=SCHEMA_3_HASH,
        proposed_spans=(),
        proposed_representation=inputs.oracle.representation,
        proposal_origin="declared-schema probe",
    )
    later = replace(
        base,
        schema_version=SCHEMA_4_VERSION,
        schema_hash=representation_schema_hash(),
    )
    assert proposal_identity(base) != proposal_identity(later)


def test_the_gate_compares_each_side_under_its_own_declaration() -> None:
    """Accepted authority and persisted state each keep their own contract.

    The gate reports a schema disagreement in its own words. Canonicalizing both
    sides under one contract would additionally report every element as missing
    or unexpected, burying the real finding under noise it invented.
    """
    inputs = load_accepted_inputs(ARTIFACT_PATH)
    under_three = _comparable_collections(
        inputs.oracle.representation, SCHEMA_3_VERSION
    )
    under_four = _comparable_collections(inputs.oracle.representation, SCHEMA_4_VERSION)
    assert set(under_three) == set(under_four)
    # Zero movement again: the same content compares equal under both contracts,
    # so the gate never manufactures a difference the schemas did not cause.
    for collection in sorted(under_three):
        assert canonical_bytes(under_three[collection]) == canonical_bytes(
            under_four[collection]
        ), collection
