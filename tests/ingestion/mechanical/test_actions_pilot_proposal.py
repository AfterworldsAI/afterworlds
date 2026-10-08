"""The ``actions-pilot`` proposal, as it was reviewed — CRD Issue 5d.

The batch is the twelve ``[Action]`` glossary entries plus ``Unarmed Strike``,
proposed by ``.claude/review-notes/issue-5d-actions-pilot-generator.py`` from
the release 5c actually publishes. Nothing here accepts it: no acceptance is
recorded, nothing is written under ``oracles/``, and nothing is published.

What is pinned, and why:

* the committed bytes are the recorded proposal, under its recorded identity,
  and the artifact is a proposal by shape. The generator now builds over the
  current release, so its output is no longer those bytes; that cross-release
  equality is retired (``correction-followup.md``) and the emit gate is pinned
  against the current build instead;
* the batch checks report exactly the out-of-batch targets and nothing else;
* the checklist semantics a review most easily gets wrong are exact facts
  (who rolls, what triggers, what is limited, what stays governing prose);
* omissions made while authoring are reported by production checks; and
* composed *in this test only* with the accepted conditions pilot (the
  recorded proposal and its own recorded prior, representation-only: the
  superseded release's physical source is not available), the new
  ``glossary.unarmed_strike`` record closes that pilot's one missing-target
  finding, the accepted-context targets resolve, and the rest stay explicit.
  This composition is of the proposal as reviewed, against the Conditions-only
  acceptance it was reviewed beside. The Owner has since accepted it over that
  acceptance; the combined artifact, the Unarmed Strike closure through it and
  the five remaining targets are pinned by ``test_actions_pilot_acceptance``
  (historical since the reference-closure batch extended the artifact).
"""

from __future__ import annotations

import dataclasses
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
    AcceptedInputs,
    OracleLoadError,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.projection import (
    review_unit_violations,
)
from afterworlds.ingestion.mechanical.proposal import (
    ProposalLoadError,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AdvantageFact,
    AdvantageState,
    ApplicabilityKind,
    BenefitUseLimit,
    ConditionEffectFact,
    ConditionEffectKind,
    ConditionKind,
    DcKind,
    EffectTerminationFact,
    ExpendableResource,
    ResourceExpenditureFact,
    RollActor,
    RollContext,
    StateEffectKind,
    SustainedStateRequirementFact,
    TimeUnit,
    TriggeredResolutionFact,
    fact_key,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from tests.ingestion.mechanical._replacement_chain import (
    current,
    identity,
    proposal_path,
    through,
)

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
GENERATOR = NOTES / "issue-5d-actions-pilot-generator.py"
BATCH = "actions-pilot"
PROPOSAL = proposal_path(BATCH)
IDENTITY = identity(BATCH)


def _unknown(text: str, slug: str) -> str:
    return (
        f"reference srd-5.2.1/rules-glossary:'{text}': "
        f"unknown target record glossary.{slug}"
    )


UNKNOWN_UNARMED_STRIKE = _unknown("Unarmed Strike", "unarmed_strike")
OUTSTANDING = [
    _unknown("Concentration", "concentration"),
    _unknown("Friendly", "friendly"),
    _unknown("Hostile", "hostile"),
    _unknown("Indifferent", "indifferent"),
    _unknown("Speed", "speed"),
]
ACCEPTED_CONTEXT = [
    _unknown("Grappled", "grappled"),
    _unknown("Grappling", "grappling"),
    _unknown("Incapacitated", "incapacitated"),
    _unknown("Invisible", "invisible"),
    _unknown("Prone", "prone"),
]


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("actions_pilot", GENERATOR)
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
    (c,) = [
        c
        for c in built.proposal.proposed_representation.components
        if (c.record_key, c.semantic_key) == (f"glossary.{record}", key)
    ]
    return c


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


def test_the_artifact_is_an_unaccepted_proposal_by_shape(tmp_path: Path) -> None:
    proposal = load_proposal(PROPOSAL, expected_identity=IDENTITY)
    assert (
        json.loads(PROPOSAL.read_text("utf-8"))["artifact_kind"] == "machine_proposal"
    )
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(PROPOSAL)
    tampered = tmp_path / "p.json"
    tampered.write_text(
        PROPOSAL.read_text("utf-8").replace('"dc_value": 15', '"dc_value": 16', 1),
        encoding="utf-8",
    )
    with pytest.raises(ProposalLoadError, match="this caller named"):
        load_proposal(tampered, expected_identity=IDENTITY)


def test_scope_is_the_thirteen_peer_entries(built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert [u.unit_id for u in units] == sorted(
        f"actions-pilot/{slug}" for slug, _, _ in GEN.ENTRIES
    )
    assert sum(len(u.leaf_ids) for u in units) == 49
    assert {r.semantic_key for r in built.proposal.proposed_representation.records} == {
        f"glossary.{slug}" for slug, _, _ in GEN.ENTRIES
    }


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    assert GEN.batch_findings(built) == {
        "partition": [],
        "review_units": [],
        "representation": sorted(OUTSTANDING + ACCEPTED_CONTEXT),
    }


# ---------------------------------------------------------------------------
# Checklist semantics
# ---------------------------------------------------------------------------


def test_help_benefits_the_ally_once_and_each_arm_cites_only_its_own_text(
    built: Built,
) -> None:
    c = _component(built, "help", "assistance")
    assert c.handling is ComponentHandling.MIXED
    by_key = {o.semantic_key: o for o in c.options}
    for key, context in (
        ("assist_ability_check", RollContext.ABILITY_CHECK),
        ("assist_attack_roll", RollContext.ATTACK_ROLL),
    ):
        (adv,) = [f for f in by_key[key].facts if isinstance(f, AdvantageFact)]
        assert (adv.state, adv.roll.actor, adv.roll.context) == (
            AdvantageState.ADVANTAGE,
            RollActor.ALLY,
            context,
        )
        assert adv.use_limit is BenefitUseLimit.NEXT_QUALIFYING_ROLL
    # The GM's final say is its own governing prose, not an option's source.
    assert _component(built, "help", "gm_final_say").handling is (
        ComponentHandling.PROSE_BOUND
    )
    attack_leaf = built.spans[("help", GEN.HELP_ATTACK)]
    cited = {
        p.span_id
        for p in built.proposal.proposed_representation.provenance
        if "glossary.help" in p.target_key and "assist_ability_check" in p.target_key
    }
    assert cited and attack_leaf.span_id not in cited


def test_hide_sets_a_fixed_dc_and_records_the_finders_dc(built) -> None:  # type: ignore[no-untyped-def]
    (check,) = _component(built, "hide", "hide_check").facts
    assert isinstance(check, AbilityCheckFact)
    assert (check.dc_kind, check.dc_value) == (DcKind.FIXED, 15)
    hidden = _component(built, "hide", "hidden")
    invisible, finder = hidden.facts
    assert invisible == ConditionEffectFact(
        ConditionKind.INVISIBLE, ConditionEffectKind.APPLIES
    )
    assert finder.dc_kind is DcKind.RECORDED_CHECK_TOTAL and finder.against_subject
    assert hidden.applies_when.kind is ApplicabilityKind.ROLL_OUTCOME


def test_influences_dc_is_a_gm_default_and_the_wait_follows_failure(built) -> None:  # type: ignore[no-untyped-def]
    c = _component(built, "influence", "hesitant_check")
    assert c.irreducibility_reason_code == "gamemaster_latitude"
    check, retry = c.facts
    assert check.dc_kind is DcKind.HIGHER_OF_FIXED_OR_TARGET_ABILITY_SCORE
    assert check.ability is None  # the GM chooses the check
    assert retry.gamemaster_may_set_other
    (q,) = c.fact_qualifiers
    assert q.applies_when.kind is ApplicabilityKind.ROLL_OUTCOME


def test_the_readied_trigger_may_be_ignored(built) -> None:  # type: ignore[no-untyped-def]
    (fact,) = _component(built, "ready", "trigger_resolution").facts
    assert isinstance(fact, TriggeredResolutionFact) and fact.optional


def _prose(built, record: str, key: str) -> str:  # type: ignore[no-untyped-def]
    spans = {s.span_id: s for s in built.ledger.spans}
    out = []
    for b in built.proposal.proposed_representation.prose_bindings:
        if (b.record_key, b.component_key) == (f"glossary.{record}", key):
            s = spans[b.span_id]
            out.append(built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end])
    return " ".join(out)


def test_interrupted_long_casting_keeps_the_slot_a_readied_spell_spent(built) -> None:  # type: ignore[no-untyped-def]
    magic = _component(built, "magic", "long_casting")
    assert magic.handling is ComponentHandling.MIXED
    assert magic.applies_when.kind is ApplicabilityKind.SPELL_CASTING_TIME
    assert magic.applies_when.casting_time.at_least_amount == 1
    assert magic.applies_when.casting_time.at_least_unit is TimeUnit.MINUTE
    (kept,) = [f for f in magic.facts if isinstance(f, ResourceExpenditureFact)]
    assert (kept.resource, kept.expended) == (ExpendableResource.SPELL_SLOT, False)
    # Both consequences hold only once Concentration breaks, inside the casting.
    qualified = {q.fact_key for q in magic.fact_qualifiers}
    assert qualified == {
        fact_key(f)
        for f in magic.facts
        if isinstance(f, (ResourceExpenditureFact, EffectTerminationFact))
    }
    assert {q.applies_when.effect_state for q in magic.fact_qualifiers} == {
        StateEffectKind.CONCENTRATION_BROKEN
    }
    # The whole paragraph governs, naming the Magic action a bare cost cannot.
    prose = _prose(built, "magic", "long_casting")
    assert "1 minute or longer" in prose and "the Magic action" in prose
    assert "you don't expend a spell slot" in prose
    # No other Magic component states a slot consequence out of that scope.
    assert [
        c.semantic_key
        for c in built.proposal.proposed_representation.components
        if c.record_key == "glossary.magic"
        and any(isinstance(f, ResourceExpenditureFact) for f in c.facts)
    ] == ["long_casting"]

    ready = _component(built, "ready", "readied_spell")
    (spent,) = [f for f in ready.facts if isinstance(f, ResourceExpenditureFact)]
    assert (spent.resource, spent.expended) == (
        ExpendableResource.CASTING_RESOURCES,
        True,
    )
    assert ready.applies_when is None and ready.fact_qualifiers == ()
    dissipates = _component(built, "ready", "readied_spell_dissipates")
    assert not any(isinstance(f, ResourceExpenditureFact) for f in dissipates.facts)


def test_unarmed_strike_is_authored_and_its_effect_choice_stays_prose(built) -> None:  # type: ignore[no-untyped-def]
    keys = {
        c.semantic_key: c.handling
        for c in built.proposal.proposed_representation.components
        if c.record_key == "glossary.unarmed_strike"
    }
    assert keys == {
        "definition": ComponentHandling.PROSE_BOUND,
        "effect_choice": ComponentHandling.PROSE_BOUND,
        "damage_option": ComponentHandling.PROSE_BOUND,
        "grapple_option": ComponentHandling.MIXED,
        "shove_option": ComponentHandling.PROSE_BOUND,
    }
    assert _component(built, "unarmed_strike", "grapple_option").options == ()


# ---------------------------------------------------------------------------
# Negative controls: each is reported by a production check
# ---------------------------------------------------------------------------


def _authoring_findings(session, monkeypatch, **tables) -> list[str]:  # type: ignore[no-untyped-def]
    for name, keep in tables.items():
        monkeypatch.setattr(GEN, name, tuple(filter(keep, getattr(GEN, name))))
    found = GEN.batch_findings(GEN.build(session))
    expected = set(OUTSTANDING + ACCEPTED_CONTEXT)
    return [f for v in found.values() for f in v if f not in expected]


def test_a_component_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    found = _authoring_findings(
        session,
        monkeypatch,
        COMPONENTS=lambda c: (c.entry, c.key) != ("dodge", "benefits_lost"),
    )
    assert found[0] == (
        "review unit actions-pilot/dodge: expected rule "
        "glossary.dodge/benefits_lost has no component"
    )


def _residue(built) -> dict[str, str]:  # type: ignore[no-untyped-def]
    """Non-whitespace text of a spanned leaf that no span covers."""
    out = {}
    for lid in {s.leaf_id for s in built.ledger.spans}:
        text = list(built.leaf_rows[lid].content)
        for s in built.ledger.spans:
            if s.leaf_id == lid:
                text[s.char_start : s.char_end] = " " * (s.char_end - s.char_start)
        if "".join(text).strip():
            out[lid] = "".join(text).strip()
    return out


def test_every_spanned_leaf_is_claimed_to_the_last_word(built) -> None:  # type: ignore[no-untyped-def]
    assert _residue(built) == {}


def test_an_unlisted_example_is_caught_only_by_the_residue_check(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Known limit, not a fix: partition runs with require_complete=False for
    # review-unit leaves, and the leaf is still reached by its sibling rule, so
    # the production checks stay silent. The residue check above is what sees it.
    assert (
        _authoring_findings(session, monkeypatch, SUPPORTING=lambda s: s[0] != "ready")
        == []
    )
    (residue,) = _residue(GEN.build(session)).values()
    assert residue.startswith("Examples include")


def test_a_stray_option_source_is_refused(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def stray(c):  # type: ignore[no-untyped-def]
        if (c.entry, c.key) != ("help", "assistance"):
            return c
        return dataclasses.replace(
            c, option_sources=(("assist_attack_roll", ("not a clause",)),)
        )

    monkeypatch.setattr(GEN, "COMPONENTS", tuple(map(stray, GEN.COMPONENTS)))
    with pytest.raises(ValueError, match="cite unreviewed"):
        GEN.build(session)


def test_dropping_a_typed_fact_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    p = built.proposal
    draft = p.proposed_representation
    components = tuple(
        (
            dataclasses.replace(
                c,
                facts=tuple(
                    f
                    for f in c.facts
                    if not isinstance(f, SustainedStateRequirementFact)
                ),
            )
            if (c.record_key, c.semantic_key) == ("glossary.magic", "long_casting")
            else c
        )
        for c in draft.components
    )
    found = review_unit_violations(
        p.proposed_review_units,
        dataclasses.replace(draft, components=components),
        p.policy_version,
        built.ledger.spans,
    )
    assert found and all("sustained_state_requirement" in f for f in found), found


def test_dropping_the_governing_context_is_reported(built) -> None:  # type: ignore[no-untyped-def]
    # Structuring the long-casting paragraph without its prose would lose the
    # Magic action it names; the source-reviewed expectation refuses it.
    p = built.proposal
    draft = p.proposed_representation
    key = ("glossary.magic", "long_casting")
    found = review_unit_violations(
        p.proposed_review_units,
        dataclasses.replace(
            draft,
            prose_bindings=tuple(
                b
                for b in draft.prose_bindings
                if (b.record_key, b.component_key) != key
            ),
        ),
        p.policy_version,
        built.ledger.spans,
    )
    assert found and all("long_casting" in f for f in found), found


# ---------------------------------------------------------------------------
# Test-only composition with the accepted conditions pilot
# ---------------------------------------------------------------------------


def _accepted_inputs() -> AcceptedInputs:
    """The Conditions-only acceptance this proposal was composed against."""
    return through("conditions-pilot")


def test_composed_with_accepted_context_the_prior_missing_target_closes() -> None:
    # The recorded proposal and its own recorded prior: both are the superseded
    # release's. Representation-only, since that release's physical source is
    # not available; the prose and provenance checks it needs are retired.
    recorded = load_proposal(PROPOSAL, expected_identity=IDENTITY)
    inputs = _accepted_inputs()
    assert recorded.binding == inputs.oracle.binding
    accepted = inputs.oracle.representation
    proposed = recorded.proposed_representation
    composed = dataclasses.replace(
        accepted,
        **{
            f.name: (*getattr(accepted, f.name), *getattr(proposed, f.name))
            for f in dataclasses.fields(accepted)
        },
    )

    assert UNKNOWN_UNARMED_STRIKE in relationship_and_reference_violations(accepted)
    assert sorted(relationship_and_reference_violations(composed)) == OUTSTANDING


# ---------------------------------------------------------------------------
# Shared authoring: the emit gate and table naming
# ---------------------------------------------------------------------------


def test_html_table_names_the_exact_leaf_text() -> None:
    assert GEN.html_table("T", ("a", "b"), [("1", "2")]) == (
        "**T**\n\n<table>\n  <thead>\n    <tr>\n      <th>a</th>\n      <th>b</th>"
        "\n    </tr>\n  </thead>\n  <tbody>\n    <tr>\n      <td>1</td>\n"
        "      <td>2</td>\n    </tr>\n  </tbody>\n</table>"
    )


def test_emit_writes_only_what_its_gate_admits(
    built: Built,
    source_release_db: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from afterworlds.ingestion.mechanical.authoring import emit

    out = tmp_path / "p.json"
    expected = GEN.expected_representation_findings()
    assert emit(str(source_release_db), lambda _s: built, out, expected) == 0
    # The current build, under its current identity; not the recorded bytes.
    assert out.read_bytes() == GEN.render(built.proposal).encode("utf-8")
    assert proposal_identity(built.proposal) in capsys.readouterr().out

    refused = tmp_path / "refused.json"
    with pytest.raises(ValueError, match="glossary.concentration"):
        emit(str(source_release_db), lambda _s: built, refused, expected[1:])
    first, *rest = built.proposal.proposed_spans
    accepted = dataclasses.replace(
        first, span=dataclasses.replace(first.span, review_state=ReviewState.ACCEPTED)
    )
    forged = dataclasses.replace(
        built,
        proposal=dataclasses.replace(built.proposal, proposed_spans=(accepted, *rest)),
    )
    with pytest.raises(ValueError, match="only PROPOSED"):
        emit(str(source_release_db), lambda _s: forged, refused, expected)
    assert not refused.exists()
