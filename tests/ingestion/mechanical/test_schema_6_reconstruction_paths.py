"""Schema 6 through the paths that rebuild it — CRD Issue 5d, batch actions-1.

``test_schema_6_actions_1_source_cases`` proves the *shapes* against their
printed source: a fact is valid, it round-trips its own canonical payload, and
a malformed one fails closed. That is the representation's own contract, and it
is not the whole of what schema 6 changed.

Two of schema 6's additions are not fact payloads, so nothing above reaches
them:

* **the cross-kind disjunction** rides ``applies_when``, which is rebuilt by
  three sibling loaders — ``oracle.py`` for accepted authority, ``persistence``
  for stored state, and ``rules_authority.patches`` for overrides. Three
  readers of one wire contract is exactly how a new operand comes to be
  admitted by one and dropped by another, and ``Applicability`` is now
  self-nesting, so a loader that ignores ``any_of_terms`` rebuilds a bare
  ``ANY_OF`` rather than failing; and
* **``ProseBindingDraft.option_key``** crosses the draft validator, the raw
  projection's closure check, its own database column, and the provenance
  coordinate.

This module exercises those paths, and only those. A test here fails when a
loader, a column, or a validator has not been carried across the succession —
which is the failure the source-case module cannot see.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    OracleLoadError,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.projection import (
    applicability_payload,
    identify_projection,
)
from afterworlds.ingestion.mechanical.raw_state import (
    PersistedStateReconstructionError,
)
from afterworlds.ingestion.mechanical.representation import (
    COMPONENT_WIDE_PROSE,
    Applicability,
    ApplicabilityKind,
    ComponentHandling,
    ComponentOption,
    ConditionKind,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    fact_payload,
    prose_binding_target_key,
)
from afterworlds.ingestion.mechanical.schema_lift import SCHEMA_6_HASH, SCHEMA_6_VERSION
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.persistence.orm.mechanical import MechanicalProseBindingORM
from afterworlds.services.rules_authority.patches import (
    InvalidPatchError,
    _build_applicability,
    _build_fact,
)
from tests.ingestion.mechanical.conftest import (
    NOW,
    OPEN_ENDED_KEY,
    PROSE_SPAN,
    RELEASE_BINDING,
    SPELL_KEY,
    SPELL_LEAF,
    SPELL_SPAN,
    bound_corpus,
    build_ledger,
    build_representation,
    candidate_of,
)
from tests.ingestion.mechanical.test_schema_6_actions_1_source_cases import (
    CASES,
    DODGE_LOSS,
    HIDE_PREREQUISITE,
)

#: The frozen schema-3 specimen, reused the way ``test_schema_5_persistence_
#: and_overrides`` reuses it: a real committed artifact to re-declare, so the
#: committed loader is exercised on a file rather than by calling its own
#: helper back.
LEGACY_PATH = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "legacy_conditions_1_unanchored_schema3.json"
)


def _persist(session: Session, representation: object) -> object:
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), representation)
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()
    return identified


# ---------------------------------------------------------------------------
# The cross-kind disjunction reaches all three applicability loaders
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "applicability",
    [DODGE_LOSS, HIDE_PREREQUISITE],
    ids=["dodge-loss", "hide-prerequisite"],
)
def test_a_disjunction_survives_storage_and_reconstruction(
    session: Session, applicability: Applicability
) -> None:
    """Every term comes back, in order, as the same value objects.

    A loader that ignored ``any_of_terms`` would rebuild an ``ANY_OF`` with no
    terms — which is not a narrower condition but a meaningless one — so the
    assertion is on the terms, not merely on the kind.
    """
    base = build_representation()
    components = list(base.components)
    components[0] = replace(components[0], applies_when=applicability)
    identified = _persist(session, replace(base, components=tuple(components)))

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    stored = rebuilt.representation.components[0].applies_when
    assert stored == applicability
    assert stored is not None
    assert len(stored.any_of_terms) == len(applicability.any_of_terms)
    assert verify_persisted_state(session, identified.projection_uuid) == ()


@pytest.mark.parametrize(
    "applicability",
    [DODGE_LOSS, HIDE_PREREQUISITE],
    ids=["dodge-loss", "hide-prerequisite"],
)
def test_the_patch_loader_rebuilds_a_disjunction(
    applicability: Applicability,
) -> None:
    """The override seam reads the same operand the projection writes."""
    assert _build_applicability(applicability_payload(applicability), "f") == (
        applicability
    )


def test_the_patch_loader_refuses_a_malformed_term() -> None:
    """A nested term is a whole applicability, so it is checked like one.

    The term below names the *cover* kind while carrying no cover, which is
    valid JSON and a real vocabulary member — and refused, because the operand
    a term carries has to be the one its kind names.
    """
    payload = applicability_payload(DODGE_LOSS)
    terms = [dict(term) for term in payload["any_of_terms"]]  # type: ignore[union-attr]
    terms[0]["kind"] = ApplicabilityKind.COVER.value
    payload["any_of_terms"] = terms
    with pytest.raises(InvalidPatchError):
        _build_applicability(payload, "f")


def test_the_patch_loader_refuses_a_term_that_is_not_an_object() -> None:
    payload = applicability_payload(DODGE_LOSS)
    payload["any_of_terms"] = ["prone"]
    with pytest.raises(InvalidPatchError):
        _build_applicability(payload, "f")


def _artifact_with(applies_when: object, tmp_path: object, name: str) -> Path:
    """The committed specimen carrying one applicability, declared at schema 6.

    A cross-kind disjunction *is* schema-6 meaning, so the declaration and the
    batch anchors move with it — otherwise the legality guard refuses the file
    before its key shape is ever read and the test passes for the wrong reason.
    """
    raw = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    raw["representation"]["components"][0]["applies_when"] = applies_when
    raw["representation_schema"] = {"version": SCHEMA_6_VERSION, "hash": SCHEMA_6_HASH}
    raw["acceptance"]["schema_anchors"] = [
        {
            "batch_id": batch["batch_id"],
            "proposal_identity": batch["proposal_identity"],
            "schema_version": SCHEMA_6_VERSION,
            "schema_hash": SCHEMA_6_HASH,
        }
        for batch in raw["acceptance"]["batches"]
    ]
    path = Path(str(tmp_path)) / name
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def test_the_committed_loader_rebuilds_a_disjunction(tmp_path: object) -> None:
    """Accepted authority carrying a disjunction loads with all three terms."""
    path = _artifact_with(
        applicability_payload(HIDE_PREREQUISITE), tmp_path, "disjunction.json"
    )
    loaded = load_accepted_inputs(path)
    assert loaded.oracle.representation.components[0].applies_when == (
        HIDE_PREREQUISITE
    )


@pytest.mark.parametrize(
    ("name", "mangle", "expected"),
    [
        ("a term that is not an object", ["heavily_obscured"], "any_of_terms[0]"),
        ("a term missing a required key", [{"kind": "cover"}], "any_of_terms[0]"),
        ("terms that are not an array", "heavily_obscured", "any_of_terms"),
    ],
)
def test_the_committed_loader_refuses_a_malformed_disjunction(
    name: str, mangle: object, expected: str, tmp_path: object
) -> None:
    """Each failure is the loader's own typed error, naming the term at fault."""
    payload = applicability_payload(HIDE_PREREQUISITE)
    payload["any_of_terms"] = mangle
    path = _artifact_with(payload, tmp_path, "malformed.json")
    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(path)
    assert expected in str(raised.value), (name, raised.value)


def test_a_nested_disjunction_is_refused_by_every_loader(tmp_path: object) -> None:
    """Depth is a typed invariant, and all three loaders end at it.

    A disjunction of disjunctions has more than one reading of what negation
    and ordering mean, so the module admits exactly one level. What matters
    here is that no loader admits the deeper form by rebuilding it silently.
    """
    nested = Applicability(kind=ApplicabilityKind.ANY_OF, any_of_terms=(DODGE_LOSS,))
    payload = applicability_payload(
        Applicability(
            kind=ApplicabilityKind.ANY_OF,
            any_of_terms=(
                nested,
                Applicability(
                    kind=ApplicabilityKind.CONDITION_STATE,
                    condition=ConditionKind.PRONE,
                ),
            ),
        )
    )
    with pytest.raises(InvalidPatchError):
        _build_applicability(payload, "f")
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(_artifact_with(payload, tmp_path, "nested.json"))


# ---------------------------------------------------------------------------
# Option-scoped prose crosses the validator, the closure check, and the column
# ---------------------------------------------------------------------------
#
# The component below is ``Help``'s shape reduced to the fixture's keys: one
# MIXED component stating two arms, each with its own typed fact, and prose
# that governs one arm rather than the component. It is built here rather than
# in the conftest for the reason the conftest gives for the choice component —
# a great many tests assert the shared fixture's element counts.

ABILITY_ARM = "ability-check-arm"
ATTACK_ARM = "attack-roll-arm"

#: Two arms are two authorities, and the provenance rule admits exactly one
#: primary claim per span — so the spell leaf's accepted span is partitioned
#: into the two halves that actually state them. This is the same manoeuvre
#: ``test_prose_extent`` uses, for the same reason: the fixture ledger is a
#: shape to work in, not a constant to assert against.
ARM_A_SPAN = derive_span_id(SPELL_LEAF, 0, 20)
ARM_B_SPAN = derive_span_id(SPELL_LEAF, 20, 40)


def _ledger() -> ClassificationLedger:
    kept = tuple(s for s in build_ledger().spans if s.leaf_id != SPELL_LEAF)
    halves = tuple(
        SemanticSpan(
            span_id=span_id,
            leaf_id=SPELL_LEAF,
            char_start=start,
            char_end=end,
            disposition=SemanticDisposition.SUBSTANTIVE,
            review_state=ReviewState.ACCEPTED,
        )
        for span_id, start, end in (
            (ARM_A_SPAN, 0, 20),
            (ARM_B_SPAN, 20, 40),
        )
    )
    return build_ledger(spans=kept + halves)


def _option_scoped_draft(option_key: str) -> object:
    """The fixture draft with the prose-bound component stating two arms."""
    base = build_representation()
    component = replace(
        base.components[1],
        handling=ComponentHandling.MIXED,
        options=(
            ComponentOption(semantic_key=ABILITY_ARM, facts=(CASES["H3"][1],)),
            ComponentOption(semantic_key=ATTACK_ARM, facts=(CASES["H6"][1],)),
        ),
    )
    binding = ProseBindingDraft(
        component_key=OPEN_ENDED_KEY,
        record_key=SPELL_KEY,
        chunk_id=base.prose_bindings[0].chunk_id,
        span_id=PROSE_SPAN,
        chunk_char_start=0,
        chunk_char_end=30,
        irreducibility_reason_code="open_ended_effect",
        option_key=option_key,
    )
    # One primary claim per span, so the descriptor component makes way: its
    # fact owns ``SPELL_SPAN``, and the two arms need a span each. What this
    # module is about is the option scope, not the fixture's element counts.
    kept = tuple(
        claim
        for claim in base.provenance
        if claim.target_kind
        not in (ProvenanceTargetKind.PROSE_BINDING, ProvenanceTargetKind.FACT)
    )
    kept = tuple(
        replace(claim, span_id=ARM_A_SPAN) if claim.span_id == SPELL_SPAN else claim
        for claim in kept
    )
    option_claims = tuple(
        ProvenanceClaim(
            ProvenanceTargetKind.FACT,
            (SPELL_KEY, OPEN_ENDED_KEY, fact_key_, arm),
            span_id,
            ProvenanceRole.PRIMARY,
        )
        for arm, fact_key_, span_id in (
            (ABILITY_ARM, _fact_key(CASES["H3"][1]), ARM_A_SPAN),
            (ATTACK_ARM, _fact_key(CASES["H6"][1]), ARM_B_SPAN),
        )
    )
    return replace(
        base,
        components=(component,),
        prose_bindings=(binding,),
        provenance=(
            *kept,
            *option_claims,
            ProvenanceClaim(
                ProvenanceTargetKind.PROSE_BINDING,
                prose_binding_target_key(binding),
                PROSE_SPAN,
                ProvenanceRole.PRIMARY,
            ),
        ),
    )


def _fact_key(fact: object) -> str:
    from afterworlds.ingestion.mechanical.representation import fact_key

    return fact_key(fact)


def test_prose_scoped_to_a_stated_option_validates() -> None:
    """The case the field exists for: one arm's clause, bound to that arm."""
    assert (
        validate_representation(
            _option_scoped_draft(ABILITY_ARM), _ledger(), bound_corpus()
        )
        == ()
    )


def test_prose_scoped_to_an_option_the_component_does_not_state_is_refused() -> None:
    """An unresolvable option key governs *no* arm while reading as scoped.

    That is worse than an unscoped binding, which at least governs every arm,
    so it is refused rather than widened.
    """
    findings = validate_representation(
        _option_scoped_draft("no-such-arm"), _ledger(), bound_corpus()
    )
    assert any("names no option of its component" in f for f in findings), findings


def test_an_option_key_survives_storage_and_reconstruction(
    session: Session,
) -> None:
    """The column, the write, and the read — proved against a real session."""
    identified = _persist(session, _option_scoped_draft(ABILITY_ARM))
    stored = session.scalars(select(MechanicalProseBindingORM)).all()
    assert [row.option_key for row in stored] == [ABILITY_ARM]

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert [b.option_key for b in rebuilt.representation.prose_bindings] == [
        ABILITY_ARM
    ]
    assert verify_persisted_state(session, identified.projection_uuid) == ()


def test_component_wide_prose_still_stores_the_empty_scope(session: Session) -> None:
    """The unscoped binding is unchanged: absence is a real state, not a null.

    Every one of the twenty accepted prose bindings is this shape, so a
    reconstruction that turned the empty scope into ``None`` — or into the
    string ``"None"`` — would move accepted authority.
    """
    identified = _persist(session, build_representation())
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert [b.option_key for b in rebuilt.representation.prose_bindings] == [
        COMPONENT_WIDE_PROSE
    ]


def test_the_raw_closure_check_reports_a_binding_naming_no_option_row(
    session: Session,
) -> None:
    """One level below the validator, on the rows themselves.

    Reconstruction visits prose bindings by their component, so a binding whose
    *option* row is missing would simply resolve to nothing in silence. This is
    the check that turns that into a reported problem.
    """
    identified = _persist(session, _option_scoped_draft(ABILITY_ARM))
    row = session.scalars(select(MechanicalProseBindingORM)).one()
    row.option_key = "no-such-arm"
    session.flush()

    with pytest.raises(PersistedStateReconstructionError) as raised:
        reconstruct_candidate(session, identified.projection_uuid)
    assert "no-such-arm" in str(raised.value), raised.value


def test_the_committed_loader_reads_an_option_scoped_binding(
    tmp_path: object,
) -> None:
    """Accepted authority may state the scope, and a pre-6 file need not.

    The specimen's own twenty bindings carry no ``option_key`` at all, which is
    what an optional key has to mean: the loader supplies the component-wide
    scope rather than refusing the file.
    """
    raw = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    loaded = load_accepted_inputs(LEGACY_PATH)
    assert all("option_key" not in b for b in raw["representation"]["prose_bindings"])
    assert all(
        b.option_key == COMPONENT_WIDE_PROSE
        for b in loaded.oracle.representation.prose_bindings
    )


# ---------------------------------------------------------------------------
# The override seam reaches every new family
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("obligation", sorted(CASES))
def test_an_override_can_state_every_schema_6_family(obligation: str) -> None:
    """A typed override rebuilds what the projection writes, family by family.

    ``_build_fact`` dispatches through ``fact_from_payload`` rather than its own
    table, so a new family is patchable the moment it is declared — which is
    the property worth pinning, because the alternative failure is silent: a
    per-family table would refuse all twelve and no existing test would notice.
    """
    fact = CASES[obligation][1]
    assert _build_fact(fact_payload(fact), obligation) == fact


def test_an_override_stating_a_malformed_new_family_is_refused() -> None:
    payload = fact_payload(CASES["A1"][1])
    payload["count"] = 0
    with pytest.raises(InvalidPatchError):
        _build_fact(payload, "A1")
