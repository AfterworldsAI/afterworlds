"""The fresh ``conditions-pilot`` proposal is unaccepted evidence — CRD Issue 5d.

The pilot is *Rules Glossary > Conditions*: the fifteen ``[Condition]`` entries
plus ``Condition`` and ``Grappling``, proposed by
``.claude/review-notes/issue-5d-conditions-pilot-generator.py`` from the release
5c actually publishes. Nothing here accepts it; no acceptance is recorded,
nothing is written under ``oracles/``, and nothing is published.

What is pinned, and why:

* the committed bytes are the recorded proposal under its recorded identity. The
  generator now builds over the current release, so its output is no longer
  those bytes; that cross-release equality is retired
  (``correction-followup.md``);
* the artifact is a proposal by shape: loadable only as one, refused as
  accepted authority, every span ``PROPOSED``;
* the three batch checks report exactly the one honest out-of-scope target
  (``glossary.unarmed_strike``) and nothing else;
* the checklist semantics a review most easily gets wrong are asserted as
  exact facts (Exhaustion formulas and death at 6, the Grappled drag
  exception, Unconscious as a peer, Petrified's condition immunity and its
  hedged "(usually stone)" kept as governing prose); and
* each negative control is reported by a production check, proved by mutation
  -- including omissions made while *authoring*, before the build, which the
  source review (``CLAUSES``, ``FRAMING``) keeps visible to those checks.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.models import ComponentHandling, ReviewState
from afterworlds.ingestion.mechanical.oracle import (
    OracleLoadError,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import review_unit_violations
from afterworlds.ingestion.mechanical.proposal import (
    ProposalLoadError,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import (
    ApplicabilityKind,
    Comparison,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    ConditionLevelFact,
    MovementCostFact,
    MovementTransportFact,
    Phase,
    QuantityMultiplierFact,
    RepresentationDraft,
    ScalingEffect,
    ScalingFact,
    StateEffectFact,
    StateEffectKind,
    TransformationFact,
    fact_key,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.quarantine import (
    QUARANTINED_PACKAGE_UUIDS,
    QUARANTINED_RELEASE_VERSIONS,
    QuarantinedAuthorityError,
)
from tests.ingestion.mechanical._replacement_chain import (
    BATCHES,
    current,
    identity,
    proposal_path,
)

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
GENERATOR = NOTES / "issue-5d-conditions-pilot-generator.py"
BATCH = "conditions-pilot"
PROPOSAL = proposal_path(BATCH)
IDENTITY = identity(BATCH)
UNKNOWN_UNARMED_STRIKE = (
    "reference srd-5.2.1/rules-glossary:'Unarmed Strike': "
    "unknown target record glossary.unarmed_strike"
)


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("conditions_pilot", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _generator()


@pytest.fixture(scope="module")
def session(source_release_db: Path):  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{source_release_db}")
    with create_session_factory(engine)() as s:
        yield s
    engine.dispose()


@pytest.fixture(scope="module")
def built(session):  # type: ignore[no-untyped-def]
    return GEN.build(session)


def _component(built, record: str, key: str):  # type: ignore[no-untyped-def]
    draft = built.proposal.proposed_representation
    (c,) = [
        c
        for c in draft.components
        if (c.record_key, c.semantic_key) == (f"glossary.{record}", key)
    ]
    return c


def _with(
    built: Built, draft: RepresentationDraft
) -> tuple[list[str], RepresentationDraft]:
    return sorted(validate_representation(draft, built.ledger, built.corpus)), draft


# ---------------------------------------------------------------------------
# The artifact
# ---------------------------------------------------------------------------


def test_the_committed_bytes_are_the_recorded_proposal(built) -> None:  # type: ignore[no-untyped-def]
    assert proposal_identity(load_proposal(PROPOSAL, expected_identity=IDENTITY)) == (
        IDENTITY
    )
    assert b"\r" not in PROPOSAL.read_bytes()
    # The generator builds over the current release.
    assert built.binding == current().oracle.binding


def test_the_artifact_is_an_unaccepted_proposal_by_shape() -> None:
    proposal = load_proposal(PROPOSAL, expected_identity=IDENTITY)
    assert (
        json.loads(PROPOSAL.read_text("utf-8"))["artifact_kind"] == "machine_proposal"
    )
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(PROPOSAL)


def test_a_tampered_file_does_not_load_under_the_reviewed_identity(
    tmp_path: Path,
) -> None:
    tampered = tmp_path / "p.json"
    text = PROPOSAL.read_text("utf-8").replace('"feet": 0', '"feet": 5', 1)
    tampered.write_text(text, encoding="utf-8")
    with pytest.raises(ProposalLoadError, match="this caller named"):
        load_proposal(tampered, expected_identity=IDENTITY)


def test_scope_is_the_seventeen_peer_entries(built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert len(units) == 17
    assert sum(len(u.leaf_ids) for u in units) == 87
    assert {r.semantic_key for r in built.proposal.proposed_representation.records} == {
        f"glossary.{slug}" for slug, _, _ in GEN.ENTRIES
    }


def test_the_batch_checks_report_only_the_honest_outstanding_target(built) -> None:  # type: ignore[no-untyped-def]
    assert GEN.batch_findings(built) == {
        "partition": [],
        "review_units": [],
        "representation": [UNKNOWN_UNARMED_STRIKE],
    }


# ---------------------------------------------------------------------------
# Checklist semantics
# ---------------------------------------------------------------------------


def test_exhaustion_is_cumulative_with_formulas_and_death_at_six(built) -> None:  # type: ignore[no-untyped-def]
    levels = _component(built, "exhaustion", "exhaustion_levels")
    gain, dies = levels.facts
    assert isinstance(gain, ConditionLevelFact) and gain.cumulative and gain.amount == 1
    assert dies == StateEffectFact(effect=StateEffectKind.DIES)
    (q,) = levels.fact_qualifiers
    assert q.fact_key == fact_key(dies)
    assert (q.applies_when.comparison, q.applies_when.value) == (Comparison.EQUALS, 6)
    scaling = {
        f.effect: f.amount
        for key in ("d20_tests_affected", "speed_reduced")
        for f in _component(built, "exhaustion", key).facts
        if isinstance(f, ScalingFact)
    }
    assert scaling == {ScalingEffect.D20_TEST: 2, ScalingEffect.SPEED: 5}
    # No six-row effects table: exactly the four printed components.
    assert {
        c.semantic_key
        for c in built.proposal.proposed_representation.components
        if c.record_key == "glossary.exhaustion"
    } == {
        "exhaustion_levels",
        "d20_tests_affected",
        "speed_reduced",
        "removing_exhaustion_levels",
    }


def test_the_drag_exception_limits_the_surcharge_only(built) -> None:  # type: ignore[no-untyped-def]
    movable = _component(built, "grappled", "movable")
    transport, surcharge = movable.facts
    assert isinstance(transport, MovementTransportFact)
    assert isinstance(surcharge, MovementCostFact) and surcharge.feet == 1
    (q,) = movable.fact_qualifiers
    assert q.fact_key == fact_key(surcharge)
    assert q.applies_when.kind is ApplicabilityKind.SIZE_COMPARISON
    assert q.applies_when.negated and len(q.applies_when.any_of) == 2


def test_unconscious_is_a_peer_that_leaves_you_prone(built) -> None:  # type: ignore[no-untyped-def]
    remains = _component(built, "unconscious", "remains_prone")
    assert remains.applies_when.phase is Phase.ON_END
    assert remains.facts == (
        ConditionEffectFact(
            condition=ConditionKind.PRONE, effect=ConditionEffectKind.APPLIES
        ),
    )
    unit = next(
        u
        for u in built.proposal.proposed_review_units
        if u.unit_id == "conditions-pilot/unconscious"
    )
    assert len(unit.expected_rules) >= 7


def test_petrified_is_immune_to_the_poisoned_condition_not_poison_damage(built) -> None:  # type: ignore[no-untyped-def]
    assert _component(built, "petrified", "poison_immunity").facts == (
        ConditionEffectFact(
            condition=ConditionKind.POISONED, effect=ConditionEffectKind.IMMUNITY
        ),
    )


def test_petrifieds_hedged_substance_stays_governing_prose(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "petrified", "turned_to_inanimate_substance")
    assert c.handling is ComponentHandling.MIXED
    assert c.irreducibility_reason_code == "fiction_dependent_consequence"
    # The consequences the source states outright stay typed.
    assert {type(f) for f in c.facts} == {
        TransformationFact,
        QuantityMultiplierFact,
        StateEffectFact,
    }
    (binding,) = [
        b
        for b in built.proposal.proposed_representation.prose_bindings
        if (b.record_key, b.component_key)
        == ("glossary.petrified", "turned_to_inanimate_substance")
    ]
    ((text,),) = [
        texts
        for entry, key, _, texts in GEN.CLAUSES
        if (entry, key) == ("petrified", "turned_to_inanimate_substance")
    ]
    span = built.spans[("petrified", text)]
    assert binding.span_id == span.span_id
    assert (
        built.leaf_rows[span.leaf_id].content[span.char_start : span.char_end] == text
    )
    assert "a solid inanimate substance (usually stone)" in text


def test_every_index_cell_names_its_entry(built) -> None:  # type: ignore[no-untyped-def]
    targets = {
        r.target_record_key
        for r in built.proposal.proposed_representation.references
        if r.from_record_key == "glossary.condition"
    }
    assert targets == {f"glossary.{n.lower()}" for n in GEN.CONDITION_NAMES}


# ---------------------------------------------------------------------------
# Negative controls: each is reported by a production check
# ---------------------------------------------------------------------------


def test_a_quarantined_release_is_refused(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    real = GEN.published_release_binding(session)
    monkeypatch.setattr(
        GEN,
        "published_release_binding",
        lambda _s: dataclasses.replace(
            real,
            package_uuid=next(iter(QUARANTINED_PACKAGE_UUIDS)),
            release_version=next(iter(QUARANTINED_RELEASE_VERSIONS)),
        ),
    )
    with pytest.raises(QuarantinedAuthorityError):
        GEN.build(session)


def test_an_off_by_one_prose_offset_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    draft = built.proposal.proposed_representation
    first, *rest = draft.prose_bindings
    shifted = dataclasses.replace(
        first,
        chunk_char_start=first.chunk_char_start + 1,
        chunk_char_end=first.chunk_char_end + 1,
    )
    found, _ = _with(built, dataclasses.replace(draft, prose_bindings=(shifted, *rest)))
    assert found == [
        f"prose binding glossary.blinded/cant_see: declared chunk extent "
        f"[{shifted.chunk_char_start},{shifted.chunk_char_end}) "
        f"is not the bound span's extent "
        f"[{first.chunk_char_start}, {first.chunk_char_end}]",
        UNKNOWN_UNARMED_STRIKE,
    ]


def test_a_fabricated_reference_target_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    draft = built.proposal.proposed_representation
    refs = draft.references
    i = next(i for i, r in enumerate(refs) if r.target_record_key == "glossary.prone")
    forged = dataclasses.replace(refs[i], target_record_key="glossary.not_an_entry")
    found, _ = _with(
        built,
        dataclasses.replace(draft, references=(*refs[:i], forged, *refs[i + 1 :])),
    )
    assert any("unknown target record glossary.not_an_entry" in f for f in found)


def test_dropping_the_exhaustion_speed_formula_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    p = built.proposal
    draft = p.proposed_representation
    kept = tuple(
        c
        for c in draft.components
        if (c.record_key, c.semantic_key) != ("glossary.exhaustion", "speed_reduced")
    )
    mutated = dataclasses.replace(draft, components=kept)
    found = review_unit_violations(
        p.proposed_review_units, mutated, p.policy_version, built.ledger.spans
    )
    assert any("speed_reduced" in f for f in found)


def _authoring_findings(session, monkeypatch, **tables) -> list[str]:  # type: ignore[no-untyped-def]
    """Build after changing the generator's literal tables, as an author would."""
    for name, keep in tables.items():
        monkeypatch.setattr(GEN, name, tuple(filter(keep, getattr(GEN, name))))
    found = GEN.batch_findings(GEN.build(session))
    return [f for v in found.values() for f in v if f != UNKNOWN_UNARMED_STRIKE]


@pytest.mark.parametrize(
    ("entry", "key"),
    [
        # Alone on its leaf.
        ("exhaustion", "speed_reduced"),
        # Shares its leaf with a sibling clause, so leaf coverage cannot see it.
        ("prone", "own_attacks_affected"),
    ],
)
def test_a_component_omitted_while_authoring_is_reported(
    session: Session, monkeypatch: pytest.MonkeyPatch, entry: str, key: str
) -> None:
    found = _authoring_findings(
        session, monkeypatch, COMPONENTS=lambda c: (c.entry, c.key) != (entry, key)
    )
    assert len(found) == 2, found
    assert found[0] == (
        f"review unit conditions-pilot/{entry}: expected rule "
        f"glossary.{entry}/{key} has no component"
    )
    assert found[1].endswith(": substantive but unclaimed")


def test_a_fact_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def without_check_failure(c):  # type: ignore[no-untyped-def]
        if (c.entry, c.key) != ("blinded", "cant_see"):
            return c
        return dataclasses.replace(c, facts=c.facts[:1])

    monkeypatch.setattr(
        GEN, "COMPONENTS", tuple(map(without_check_failure, GEN.COMPONENTS))
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found and all(
        "glossary.blinded/cant_see" in f and "automatic_outcome" in f for f in found
    ), found


def test_a_clause_and_its_component_omitted_together_leave_the_leaf_unaccounted(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    omitted = ("exhaustion", "speed_reduced")
    found = _authoring_findings(
        session,
        monkeypatch,
        CLAUSES=lambda r: r[:2] != omitted,
        COMPONENTS=lambda c: (c.entry, c.key) != omitted,
    )
    assert len(found) == 1 and found[0].startswith(
        "review unit conditions-pilot/exhaustion: leaf "
    )
    assert found[0].endswith(
        "is reviewed by this unit but named by no expected rule, "
        "supporting group or excluded group"
    )


def test_omitted_framing_leaves_the_leaf_unaccounted(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    found = _authoring_findings(
        session, monkeypatch, FRAMING=lambda f: f[0] != "exhaustion"
    )
    assert len(found) == 1 and "conditions-pilot/exhaustion: leaf" in found[0]


def test_a_component_without_a_reviewed_clause_is_refused(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(r for r in GEN.CLAUSES if r[:2] != ("exhaustion", "speed_reduced")),
    )
    with pytest.raises(ValueError, match="represents no reviewed clause"):
        GEN.build(session)


def test_an_unaccounted_unit_leaf_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    p = built.proposal
    units = list(p.proposed_review_units)
    i = next(
        i for i, u in enumerate(units) if u.unit_id == "conditions-pilot/grappling"
    )
    units[i] = dataclasses.replace(units[i], excluded_groups=())
    found = review_unit_violations(
        tuple(units), p.proposed_representation, p.policy_version, built.ledger.spans
    )
    assert found and all("conditions-pilot/grappling" in f for f in found)


def test_the_committed_file_digest_is_stable() -> None:
    assert hashlib.sha256(PROPOSAL.read_bytes()).hexdigest() == BATCHES[BATCH][1]
