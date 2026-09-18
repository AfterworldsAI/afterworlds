"""Retained prose, under representation schema 12 — CRD Issue 5d (#137).

Schema 12 carries the Owner Decision of 2026-09-16 into the serialized grammar
and nothing else. It mints no fact family, no vocabulary, no vocabulary member
and no ownership form, so there is no batch to represent here and no source
manifest to read: what it adds is a **distinction**, and this module is where
that distinction is asserted.

**The distinction.** Prose may be retained because applying the meaning
requires judgement — an :class:`IrreducibilityReason`, which every schema since
1 could state — or because the meaning is reducible and no identified
code-owned use in play, explanation or correction needs a separate structured
field for it. Schema 11 had a shape for only the first, so recording the second
meant labelling reducible meaning with an irreducibility code, which ADR-005d
forbids in those words. ``prose_retention_reason_code`` on ``ComponentDraft``
and ``ProseBindingDraft`` states the second, and
``ProseBindingDraft.irreducibility_reason_code`` becomes nullable so a binding
retained for a reducibility reason states *no* irreducibility reason rather
than a false one.

**Exactly one of the two, never both and never neither.** Silence is the
backlog state ``PROSE_BOUND`` must never become, and stating both claims that
one passage is simultaneously irreducible and reducible. Each side — component
and binding — is checked independently rather than inferred from the other,
because a binding may name a component the draft does not carry.

**Two versioned contracts, not one.** The schema says a retention key may be
written; the semantic policy says which codes it may hold.
``5d-semantic-policy-2`` mints the catalog, and a schema-12 artifact declaring
``5d-semantic-policy-1`` is perfectly legal — it may simply state no retention
reason at all. Both halves are asserted here, at each seam that reads them.

**What this module does not claim.** No accepted authority moved. The seven
accepted batches state no retention reason, the key is omitted when unset, and
the identity of every accepted component, binding, fact and provenance
coordinate is unchanged under both contracts — asserted below as the payload
equality the registered ``5d-lift-schema-11-to-12`` rationale asserts in prose.
Nothing has been persisted under schema 12 either: migration 0032 adds the two
retention columns and relaxes the binding's nullability, and NULL on every
existing row is what those rows already meant.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.acceptance import (
    AcceptanceError,
    accept_proposal,
)
from afterworlds.ingestion.mechanical.gate import (
    GateFailureCategory,
    run_publication_gate,
)
from afterworlds.ingestion.mechanical.models import ClassificationLedger
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedOracle,
    OracleLoadError,
    load_oracle,
)
from afterworlds.ingestion.mechanical.persistence import (
    identify_projection,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.policy import (
    POLICY_1_HASH,
    POLICY_1_VERSION,
    SEMANTIC_POLICY_VERSION,
    policy_meaning_violations,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (
    LegacySchemaPayloadError,
    representation_payload,
    validate_candidate,
)
from afterworlds.ingestion.mechanical.proposal import MechanicalProposal, ProposedSpan
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ComponentHandling,
    RepresentationDraft,
    declared_meaning_violations,
    introduction_manifest,
    prose_binding_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_11_HASH,
    SCHEMA_11_VERSION,
    SCHEMA_12_HASH,
    SCHEMA_12_VERSION,
    SCHEMA_13_VERSION,
    SCHEMA_14_VERSION,
    SCHEMA_15_VERSION,
    accepted_schema_contracts,
    lift_path,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from tests.ingestion.mechanical.conftest import (
    BOUNDED_ORACLE_PATH,
    DESCRIPTOR_KEY,
    NOW,
    OPEN_ENDED_KEY,
    RELEASE_BINDING,
    SCHEMA_HASH,
    SCHEMA_VERSION,
    WISH_BINDING,
    accepted_oracle,
    binding_claim,
    bound_corpus,
    build_candidate,
    build_ledger,
    build_representation,
)

#: The one code ``5d-semantic-policy-2`` admits, and the irreducibility code the
#: bounded fixture has always stated. Named rather than repeated so a test that
#: swaps one for the other reads as the swap it is.
RETENTION = "no_identified_structured_use"
IRREDUCIBLE = "open_ended_effect"

#: Every contract this build accepts authority under, except the one being
#: introduced. Derived from the succession registry rather than transcribed:
#: registering a lift is what admits a contract, so a version list kept by hand
#: here would be a second statement of the same fact, free to drift.
#: Every recognised contract that predates schema 12. Schemas 13, 14 and 15
#: are subtracted beside 12 itself rather than left in: a later succession
#: states every earlier one's meaning, so each admits the shapes this module is
#: about and would fail the refusal parametrization for the right reason. Written
#: out rather than derived from version order, for the reason every registry
#: in this area is written out: an unreviewed inheritance is the failure.
EARLIER_CONTRACTS = sorted(
    {version for version, _ in accepted_schema_contracts()}
    - {
        SCHEMA_12_VERSION,
        SCHEMA_13_VERSION,
        SCHEMA_14_VERSION,
        SCHEMA_15_VERSION,
    }
)


def _representation(
    *,
    component_irreducibility: str | None,
    component_retention: str | None,
    binding_irreducibility: str | None = None,
    binding_retention: str | None = None,
    agree: bool = True,
) -> RepresentationDraft:
    """The bounded fixture with its prose-bound component's reasons restated.

    ``agree`` is the default because the two sides genuinely are one decision
    about one passage; a test that wants them to disagree says so by passing
    the binding's own codes. The provenance claim is rebuilt rather than
    inherited: :func:`prose_binding_target_key` names the stated reason, so a
    binding whose reason changes is a *different* coordinate and the original
    claim would dangle — which is itself asserted below.
    """
    base = build_representation()
    component = dataclasses.replace(
        next(c for c in base.components if c.semantic_key == OPEN_ENDED_KEY),
        irreducibility_reason_code=component_irreducibility,
        prose_retention_reason_code=component_retention,
    )
    binding = dataclasses.replace(
        WISH_BINDING,
        irreducibility_reason_code=(
            component_irreducibility if agree else binding_irreducibility
        ),
        prose_retention_reason_code=(
            component_retention if agree else binding_retention
        ),
    )
    return build_representation(
        components=tuple(
            component if c.semantic_key == OPEN_ENDED_KEY else c
            for c in base.components
        ),
        prose_bindings=(binding,),
        provenance=tuple(
            (
                binding_claim(binding)
                if claim.target_kind.value == "prose_binding"
                else claim
            )
            for claim in base.provenance
        ),
    )


def _retained() -> RepresentationDraft:
    """The specimen this module is about: reducible meaning, honestly labelled."""
    return _representation(component_irreducibility=None, component_retention=RETENTION)


def _findings(draft: RepresentationDraft) -> tuple[str, ...]:
    return validate_representation(draft, build_ledger(), bound_corpus())


# ---------------------------------------------------------------------------
# What schema 12 mints, and what it does not
# ---------------------------------------------------------------------------


def test_schema_12_is_still_a_recognised_contract() -> None:
    """The pin this module is written against, read from the registry.

    It was live authority until the proficiency-1 pilot minted schema 13.
    It is still a recognised contract and still the source of a registered
    crossing, and schema 12's own delta is what this module asserts, so the
    pin comes from the registry rather than from live authority.
    """
    assert (SCHEMA_12_VERSION, SCHEMA_12_HASH) in accepted_schema_contracts()
    assert REPRESENTATION_SCHEMA_VERSION != SCHEMA_12_VERSION
    assert representation_schema_hash() != SCHEMA_12_HASH


def test_schema_12_is_reached_by_exactly_one_registered_crossing() -> None:
    """One additive step from schema 11, not a restamp and not a rebuild."""
    path = lift_path(
        (SCHEMA_11_VERSION, SCHEMA_11_HASH), (SCHEMA_12_VERSION, SCHEMA_12_HASH)
    )
    assert [lift.lift_id for lift in path] == ["5d-lift-schema-11-to-12"]


def test_schema_12_mints_one_nullability_and_nothing_else() -> None:
    """The manifest is the claim, and it is short on purpose.

    Every other succession since schema 4 appears here as families and
    vocabulary members. Schema 12 has exactly one row — the binding code
    becoming nullable — because its other addition is an omit-when-empty key,
    which is registered in the post-schema-3 field table instead and therefore
    refused by ``declared_meaning_violations`` rather than by the manifest. The
    two tests below are what assert *that* half; this one asserts that nothing
    else was minted along the way.
    """
    assert [
        row
        for row in introduction_manifest()
        if row["introduced_in"] == SCHEMA_12_VERSION
    ] == [
        {
            "kind": "nullable_field",
            "vocabulary": None,
            "name": "irreducibility_reason_code",
            "introduced_in": SCHEMA_12_VERSION,
        }
    ]


# ---------------------------------------------------------------------------
# Every earlier contract refuses both new shapes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("version", EARLIER_CONTRACTS)
def test_a_retention_reason_is_refused_under_every_earlier_contract(
    version: str,
) -> None:
    """Refused on the key, on both owners, and named as arriving at schema 12.

    Not "unknown field, ignored": omitting a stated retention reason to make a
    draft fit an older contract would reproduce that contract's identity while
    silently dropping the reviewer's judgement about why this passage is prose.
    """
    findings = declared_meaning_violations(_retained(), version)
    assert any(
        "components[" in f and "prose_retention_reason_code" in f for f in findings
    ), findings
    assert any(
        "prose_bindings[" in f and "prose_retention_reason_code" in f for f in findings
    ), findings
    assert all(SCHEMA_12_VERSION in f for f in findings), findings


@pytest.mark.parametrize("version", EARLIER_CONTRACTS)
def test_a_binding_stating_no_irreducibility_reason_is_refused_before_schema_12(
    version: str,
) -> None:
    """The nullable half, and the reason it is a *separate* refusal.

    Under schema 11 a binding that states no irreducibility reason is a binding
    whose mandatory reason is missing, not one retained for a different reason.
    Reading the schema-12 meaning out of a schema-11 declaration is exactly the
    inference the nullability registry exists to refuse.
    """
    binding_only = _representation(
        component_irreducibility=None,
        component_retention=RETENTION,
        agree=False,
        binding_irreducibility=None,
        binding_retention=None,
    )
    assert any(
        "prose_bindings[" in f and "irreducibility_reason_code" in f
        for f in declared_meaning_violations(binding_only, version)
    )


def test_schema_12_admits_both_shapes() -> None:
    """The other direction, so the rule is not "refuse everything newer"."""
    assert declared_meaning_violations(_retained(), SCHEMA_12_VERSION) == []


def test_the_payload_seam_refuses_a_retention_reason_under_schema_11() -> None:
    """A legacy payload is not produced by dropping what the legacy shape lacks."""
    with pytest.raises(LegacySchemaPayloadError):
        representation_payload(_retained(), schema_version=SCHEMA_11_VERSION)


def test_schema_12_emits_the_null_and_the_retention_key_together() -> None:
    """Both halves are visible on the wire, so neither is inferred from silence.

    ``irreducibility_reason_code`` stays a mandatory *key* and carries ``null``
    rather than being omitted: "retained for a reducibility reason" and
    "written before this distinction existed" must never share a payload shape.
    """
    payload = representation_payload(_retained(), schema_version=SCHEMA_12_VERSION)
    binding = payload["prose_bindings"][0]
    assert binding["irreducibility_reason_code"] is None
    assert binding["prose_retention_reason_code"] == RETENTION


def test_accepted_content_has_the_same_payload_under_both_contracts() -> None:
    """The lift's rationale, made checkable rather than asserted in prose.

    No accepted component or binding states a retention reason and the key is
    omitted when unset, so the bytes — and therefore every component key, fact
    key and provenance coordinate derived from them — are identical on both
    sides of the crossing.
    """
    accepted = build_representation()
    assert representation_payload(
        accepted, schema_version=SCHEMA_11_VERSION
    ) == representation_payload(accepted, schema_version=SCHEMA_12_VERSION)


# ---------------------------------------------------------------------------
# Exactly one reason, on each side independently
# ---------------------------------------------------------------------------


def test_a_retention_reason_alone_is_a_complete_answer() -> None:
    """The whole point: reducible meaning may be retained, honestly labelled."""
    assert _findings(_retained()) == ()


def test_neither_reason_is_refused_on_both_sides() -> None:
    findings = _findings(
        _representation(component_irreducibility=None, component_retention=None)
    )
    assert (
        "component spell:wish/open-ended-clause: prose_bound handling with no "
        "irreducibility reason and no prose retention reason" in findings
    )
    assert (
        "prose binding spell:wish/open-ended-clause: no irreducibility reason "
        "and no prose retention reason" in findings
    )


def test_both_reasons_are_refused_on_both_sides() -> None:
    """A passage cannot be irreducible *and* reducible-with-no-structured-use."""
    findings = _findings(
        _representation(
            component_irreducibility=IRREDUCIBLE, component_retention=RETENTION
        )
    )
    assert any("states both" in f and f.startswith("component ") for f in findings)
    assert any("states both" in f and f.startswith("prose binding ") for f in findings)


def test_a_retention_reason_outside_the_catalog_is_refused() -> None:
    findings = _findings(
        _representation(
            component_irreducibility=None, component_retention="because_i_said_so"
        )
    )
    assert any("'because_i_said_so' is not closed" in f for f in findings)


def test_structured_handling_may_state_no_retention_reason() -> None:
    """Retention explains prose. A component with typed facts has none to explain."""
    base = build_representation()
    structured = dataclasses.replace(
        next(c for c in base.components if c.semantic_key == DESCRIPTOR_KEY),
        prose_retention_reason_code=RETENTION,
    )
    assert structured.handling is ComponentHandling.STRUCTURED
    findings = _findings(
        build_representation(
            components=tuple(
                structured if c.semantic_key == DESCRIPTOR_KEY else c
                for c in base.components
            )
        )
    )
    assert (
        "component spell:wish/descriptor: structured handling with a prose "
        "retention reason" in findings
    )


def test_a_binding_may_not_disagree_with_its_component_about_why() -> None:
    """Two sides of one decision, and the disagreement is named, not resolved.

    Compared against the component's *same-kind* code only. A binding claiming
    irreducibility under a component that states a retention reason is already
    reported by the exactly-one rule on each side; matching it across catalogs
    would report the same contradiction again in terms naming the wrong field.
    """
    findings = _findings(
        _representation(
            component_irreducibility=None,
            component_retention=RETENTION,
            agree=False,
            binding_irreducibility=IRREDUCIBLE,
            binding_retention=None,
        )
    )
    assert (
        "prose binding spell:wish/open-ended-clause: reason 'open_ended_effect' "
        "disagrees with its component's None" in findings
    )


def test_the_binding_coordinate_names_whichever_reason_is_stated() -> None:
    """One slot, filled by the reason that actually applies.

    A retained-for-reducibility binding is a different element from an
    irreducible one over the same prose, and its provenance claim has to say
    so — which is why the specimen's claim is rebuilt rather than inherited.
    """
    retained = _retained().prose_bindings[0]
    assert prose_binding_target_key(WISH_BINDING)[-1] == IRREDUCIBLE
    assert prose_binding_target_key(retained)[-1] == RETENTION
    assert (
        prose_binding_target_key(retained)[:-1]
        == prose_binding_target_key(WISH_BINDING)[:-1]
    )


# ---------------------------------------------------------------------------
# The policy half: which codes the declared policy may hold
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _artifact(*, policy_version: str, retention: bool) -> dict[str, object]:
    """The committed bounded artifact, optionally restated as retained prose."""
    payload = json.loads(BOUNDED_ORACLE_PATH.read_text(encoding="utf-8"))
    payload["semantic_policy_version"] = policy_version
    if retention:
        representation = payload["representation"]
        for component in representation["components"]:
            if component["semantic_key"] == OPEN_ENDED_KEY:
                component["irreducibility_reason_code"] = None
                component["prose_retention_reason_code"] = RETENTION
        for binding in representation["prose_bindings"]:
            binding["irreducibility_reason_code"] = None
            binding["prose_retention_reason_code"] = RETENTION
    return payload


def test_a_retention_reason_under_policy_1_is_refused_at_load(tmp_path: Path) -> None:
    """The schema admits the key; the declared policy has no catalog for it."""
    with pytest.raises(OracleLoadError) as exc:
        load_oracle(
            _write(tmp_path, _artifact(policy_version=POLICY_1_VERSION, retention=True))
        )
    assert "whose retention catalog does not admit" in str(exc.value)


def test_policy_1_without_a_retention_reason_still_loads(tmp_path: Path) -> None:
    """The legal combination, and the reason the two contracts are versioned apart.

    Schema 12 does not oblige an artifact to use what it added. An artifact
    declaring the older policy and stating no retention reason is unaffected by
    this whole succession, which is what keeps historical schemas readable with
    their original meanings.
    """
    loaded = load_oracle(
        _write(tmp_path, _artifact(policy_version=POLICY_1_VERSION, retention=False))
    )
    assert loaded.policy_version == POLICY_1_VERSION


def test_an_unrecognized_policy_is_reported_not_raised(tmp_path: Path) -> None:
    """A version this build does not know is answered in those exact terms.

    Reported rather than crashed, because a file declares its own policy and
    the loader's job is to report honestly what it says. Nothing is waved
    through: with no catalog to read, every stated retention code is
    unconfirmable — which is a violation, but not the false claim that a known
    catalog excluded it.
    """
    with pytest.raises(OracleLoadError) as exc:
        load_oracle(
            _write(
                tmp_path,
                _artifact(policy_version="5d-semantic-policy-0", retention=True),
            )
        )
    assert "does not recognize" in str(exc.value)


def test_an_unrecognized_policy_over_stated_prose_is_silent() -> None:
    """No retention code, nothing to confirm, nothing to report.

    This is why a schema-11 artifact under a policy nobody recognizes still
    loads exactly as it did before schema 12 existed.
    """
    assert (
        policy_meaning_violations(build_representation(), "5d-semantic-policy-0") == []
    )


def _ledger(policy_version: str, policy_hash: str) -> ClassificationLedger:
    return dataclasses.replace(
        build_ledger(), policy_version=policy_version, policy_hash=policy_hash
    )


def test_a_retention_reason_under_policy_1_is_refused_at_validation() -> None:
    """The projection seam, reached before anything is persisted."""
    candidate = build_candidate(
        representation=_retained(),
        ledger=_ledger(POLICY_1_VERSION, POLICY_1_HASH),
    )
    assert any(
        "whose retention catalog does not admit" in f
        for f in validate_candidate(candidate, bound_corpus())
    )


def test_a_retention_reason_under_the_current_policy_validates_clean() -> None:
    candidate = build_candidate(representation=_retained())
    assert validate_candidate(candidate, bound_corpus()) == ()


def _proposal(
    policy_version: str, policy_hash: str, retention: bool
) -> MechanicalProposal:
    return MechanicalProposal(
        binding=RELEASE_BINDING,
        policy_version=policy_version,
        policy_hash=policy_hash,
        schema_version=SCHEMA_VERSION,
        schema_hash=SCHEMA_HASH,
        proposed_spans=tuple(
            ProposedSpan(span, "tool:classifier@0", "stated basis")
            for span in build_ledger().spans
        ),
        proposed_representation=_retained() if retention else build_representation(),
        proposal_origin="tool:proposer@0",
    )


def _accept(proposal: MechanicalProposal) -> object:
    return accept_proposal(
        proposal,
        batch_id="batch-12",
        rule="every span of the bounded fixture, reviewed together",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        reviewer="owner",
        accepted_at="2026-09-16T00:00:00Z",
    )


def test_a_retention_reason_under_policy_1_is_refused_at_acceptance() -> None:
    """Acceptance is the seam an artifact is *created* at, so it refuses too.

    A passing loader on an artifact that should never have been written is a
    proof about the file, not about the decision that produced it.
    """
    with pytest.raises(AcceptanceError) as exc:
        _accept(_proposal(POLICY_1_VERSION, POLICY_1_HASH, retention=True))
    assert "carries meaning that policy cannot state" in str(exc.value)


def test_a_retention_reason_under_the_current_policy_is_accepted() -> None:
    accepted = _accept(
        _proposal(SEMANTIC_POLICY_VERSION, semantic_policy_hash(), retention=True)
    )
    binding = accepted.oracle.representation.prose_bindings[0]  # type: ignore[attr-defined]
    assert binding.irreducibility_reason_code is None
    assert binding.prose_retention_reason_code == RETENTION


# ---------------------------------------------------------------------------
# The persistence half, and the gate seam it makes reachable
# ---------------------------------------------------------------------------


def _persist(session: Session, ledger: ClassificationLedger | None = None) -> str:
    candidate = build_candidate(representation=_retained())
    if ledger is not None:
        candidate = dataclasses.replace(candidate, classification=ledger)
    identified = identify_projection(candidate)
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    return identified.projection_uuid


def _retained_oracle(policy_version: str, policy_hash: str) -> AcceptedOracle:
    return dataclasses.replace(
        accepted_oracle(),
        representation=_retained(),
        policy_version=policy_version,
        policy_hash=policy_hash,
    )


def test_a_retention_reason_survives_storage_and_reconstruction(
    session: Session,
) -> None:
    """Migration 0032's two columns, read back through the ORM that writes them.

    Both sides are asserted, because they are two columns on two tables and a
    migration that added one would leave the other silently dropping its reason
    on every round trip.
    """
    uuid = _persist(session)
    session.flush()
    rebuilt = reconstruct_candidate(session, uuid)
    component = next(
        c for c in rebuilt.representation.components if c.semantic_key == OPEN_ENDED_KEY
    )
    assert component.irreducibility_reason_code is None
    assert component.prose_retention_reason_code == RETENTION
    binding = rebuilt.representation.prose_bindings[0]
    assert binding.irreducibility_reason_code is None
    assert binding.prose_retention_reason_code == RETENTION


def test_the_persisted_state_proof_holds_over_a_retention_reason(
    session: Session,
) -> None:
    """The digest is recorded and verifies, so the new columns are inside the proof.

    ``compute_persisted_state_digest`` serializes through ``projection_payload``
    at the row's own recorded schema version, which is why a NULL column does
    not re-identify anything already stored — and why a *stated* one is covered
    rather than invisible.
    """
    uuid = _persist(session)
    session.flush()
    assert verify_persisted_state(session, uuid) == ()


def test_a_forged_retention_reason_breaks_the_persisted_state_proof(
    session: Session,
) -> None:
    """Covered, not merely stored: an edit under the digest is caught."""
    uuid = _persist(session)
    session.flush()
    session.execute(
        sa.text(
            "UPDATE rp_mech_prose_bindings SET prose_retention_reason_code = "
            ":code WHERE projection_uuid = :uuid"
        ),
        {"code": "forged_reason", "uuid": uuid},
    )
    session.flush()
    assert verify_persisted_state(session, uuid) != ()


def test_the_gate_passes_over_a_retention_reason_under_the_current_policy(
    session: Session,
) -> None:
    """The whole round trip, judged against independently accepted authority."""
    result = run_publication_gate(
        session,
        _persist(session),
        _retained_oracle(SEMANTIC_POLICY_VERSION, semantic_policy_hash()),
    )
    assert result.passed, result.failures


def test_the_gate_refuses_a_retention_reason_under_policy_1(
    session: Session,
) -> None:
    """The fourth seam, and the one that was unreachable until 0032 landed.

    The oracle and the projection are made to *agree* on policy 1 so the paired
    declaration check stays silent: what fires here is the meaning check alone,
    which is the claim being asserted rather than the category.
    """
    uuid = _persist(session, ledger=_ledger(POLICY_1_VERSION, POLICY_1_HASH))
    result = run_publication_gate(
        session, uuid, _retained_oracle(POLICY_1_VERSION, POLICY_1_HASH)
    )
    assert not result.passed
    assert GateFailureCategory.POLICY_MISMATCH in result.categories()
    assert any(
        "whose retention catalog does not admit" in f.detail for f in result.failures
    )
