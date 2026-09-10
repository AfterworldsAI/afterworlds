"""Schema 7's one addition, against the clause that forced it — CRD Issue 5d.

``actions-1`` returned a bounded schema stop, S-1: *"If you cast a spell that
has a casting time of 1 minute or longer"* (``Magic``, p185) is a threshold over
a spell's **printed** casting-time descriptor, and schema 6 had no shape for it.
``ApplicabilityKind.ELAPSED_DURATION`` would have said something false — time
already spent casting — and ``ActivationCostEligibilityFact`` ranges over
``ActionCost``, which prints no amount and no unit. So Magic K2, K3 and K4 were
left unresolved, and the recurring action, the Concentration duty and the
failure/resource consequences all waited on that gate.

Schema 7 adds exactly one kind, ``SPELL_CASTING_TIME``, over exactly one closed
value object, :class:`CastingTimeThreshold`. This module is the executable half
of that decision:

* **the threshold itself** — a 1-minute casting and a longer timed casting both
  qualify *from the instant the casting begins*, and the immediate cases
  (Action, Bonus Action, Reaction) do not satisfy it, because the cost arm
  states no amount to compare rather than because a comparison came out false;
* **the composition** — the gate scopes ``magic_long_casting`` and
  ``magic_concentration_break`` alike, mapped to the printed coordinates the
  pinned evidence artifact records, with the concentration-break consequences
  staying conditional through ``FactQualifier`` rather than merged into the
  gate;
* **why applicability and not a fact** — a repeated gate *fact* is refused by
  ``_validate_duplicated_fact_authority``; a repeated *applicability* is
  admitted, and that asymmetry is what makes applicability the scope-preserving
  carrier;
* **the seams** — the canonical round trip, and the three sibling rebuilders
  (stored state, accepted authority, the override patch layer) that each read
  the same wire contract; and
* **the succession** — accepted schema-3..6 payloads are unchanged by the mint,
  because a component that states no gate omits the key entirely.

**Limits, stated so this is not read for more than it proves.**

* This is a demonstration against the contract schema 7 now states — not a
  proposal and not an acceptance. ``actions-1`` has since been accepted, from a
  separately reviewed schema-7 proposal; the spans below are this module's own
  fixtures and were no part of that review.
* The ledger carries the **six spans this demonstration claims**, the partition
  of K2, K3 and K4, not ``Magic``'s whole leaf partition. K1 is compared as a
  *value* here rather than composed, because
  ``test_schema_6_actions_1_source_cases`` already owns its shape.
* Chunk ids are local to this module, exactly as
  ``test_schema_6_ready_source_provenance`` records: one chunk per whole leaf,
  which is the shape the production projection has, with identifiers that are
  not the release's own.
* :func:`casting_time_meets` compares the two stated durations by magnitude,
  across the calendar units whose length is fixed (second, minute, hour, day).
  A round or a turn has no fixed length, so it is **refused** — the function
  raises rather than returning ``False``, which would claim a comparison it
  never made. No SRD casting time is printed in rounds or turns, so nothing in
  the corpus is reached by that refusal; the residue is recorded in
  ``known_unknowns.md``.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ComponentHandling,
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
from afterworlds.ingestion.mechanical.representation import (
    ActionCost,
    Applicability,
    ApplicabilityKind,
    CastingTimeThreshold,
    ComponentDraft,
    EffectTerminationFact,
    EligibilitySubject,
    ExpendableResource,
    FactQualifier,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RecurringActionRequirementFact,
    RepresentationDraft,
    ResourceExpenditureFact,
    SpellCastingTime,
    StateEffectKind,
    SustainedState,
    SustainedStateRequirementFact,
    TerminationScope,
    TimeUnit,
    UncomparableCastingTimeError,
    applicability_violations,
    build_casting_time_threshold,
    casting_time_meets,
    component_target_key,
    fact_key,
    fact_qualifier_target_key,
    introduction_manifest,
    invariant_manifest,
)
from afterworlds.ingestion.mechanical.representation import (
    _build_applicability as _rebuild_applicability,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_7_HASH,
    SCHEMA_7_VERSION,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.services.rules_authority.patches import (
    InvalidPatchError,
    _build_applicability,
)
from tests.ingestion.mechanical.conftest import (
    NOW,
    RELEASE_BINDING,
    bound_corpus,
    build_ledger,
    build_representation,
    candidate_of,
    coverage,
)
from tests.ingestion.mechanical.test_schema_6_actions_1_source_cases import CASES

# ---------------------------------------------------------------------------
# The clause, at the coordinates the pinned evidence records
# ---------------------------------------------------------------------------

EVIDENCE_PATH = (
    Path(__file__).resolve().parents[3]
    / ".claude"
    / "review-notes"
    / "issue-5d-actions-1-obligation-coordinates.json"
)

#: The published SRD 5.2.1 content digest the discovery script pins. A source
#: fingerprint, not a credential.
PINNED_SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"  # noqa: E501  # pragma: allowlist secret

#: ``Magic [Action]``, leaf 2 of 2 — printed page 185. The whole of S-1.
K_LEAF = "b196aa1b-4e06-5e14-b1a5-1fd930e1d2da"
K_LEAF_LENGTH = 265

K2_START, K2_END = 0, 127
K2_TEXT = (
    "If you cast a spell that has a casting time of 1 minute or longer, "
    "you must take the Magic action on each turn of that casting,"
)

K3_START, K3_END = 128, 180
K3_TEXT = "and you must maintain Concentration while you do so."

K4_START, K4_END = 181, 265
K4_TEXT = (
    "If your Concentration is broken, the spell fails, but you don’t "
    "expend a spell slot."
)

#: Three boundaries, each derived from the printed sentence rather than written
#: down, so no offset can be chosen to make a claim fit. K2 splits where the
#: conditional ends and the requirement begins; K4 splits its condition from
#: each of the two consequences that condition governs.
K2_BOUNDARY = K2_START + K2_TEXT.index("you must take")
K4_FAILS = K4_START + K4_TEXT.index("the spell fails")
K4_SLOT = K4_START + K4_TEXT.index("but you")

K2A_TEXT = K2_TEXT[: K2_BOUNDARY - K2_START]
K2B_TEXT = K2_TEXT[K2_BOUNDARY - K2_START :]

K2A_SPAN = derive_span_id(K_LEAF, K2_START, K2_BOUNDARY)
K2B_SPAN = derive_span_id(K_LEAF, K2_BOUNDARY, K2_END)
K3_SPAN = derive_span_id(K_LEAF, K3_START, K3_END)
K4A_SPAN = derive_span_id(K_LEAF, K4_START, K4_FAILS)
K4B_SPAN = derive_span_id(K_LEAF, K4_FAILS, K4_SLOT)
K4C_SPAN = derive_span_id(K_LEAF, K4_SLOT, K4_END)

#: Local to this module — see the docstring's third limit.
K_CHUNK = "chunk-magic-p185"

MAGIC_CORPUS = bound_corpus(
    leaf_lengths={K_LEAF: K_LEAF_LENGTH},
    chunk_coverage=(coverage(K_CHUNK, K_LEAF, 0, K_LEAF_LENGTH),),
)


# ---------------------------------------------------------------------------
# The gate, and the four mechanics it scopes
# ---------------------------------------------------------------------------

#: S-1's answer, and the whole of schema 7. Read off the spell's printed
#: descriptor before any time passes, which is why it is not
#: ``ELAPSED_DURATION``.
THRESHOLD = CastingTimeThreshold(at_least_amount=1, at_least_unit=TimeUnit.MINUTE)
LONG_CASTING = Applicability(
    kind=ApplicabilityKind.SPELL_CASTING_TIME, casting_time=THRESHOLD
)

#: ``Magic`` K4 and ``Ready`` L10 — *"If your Concentration is broken"*.
CONCENTRATION_BROKEN = Applicability(
    kind=ApplicabilityKind.EFFECT_STATE,
    effect_state=StateEffectKind.CONCENTRATION_BROKEN,
)

RECURRING = RecurringActionRequirementFact(cost=ActionCost.ACTION, per=TimeUnit.TURN)
SUSTAINED = SustainedStateRequirementFact(state=SustainedState.CONCENTRATION)
TERMINATION = EffectTerminationFact(scope=TerminationScope.OWNING_EFFECT)
EXPENDITURE = ResourceExpenditureFact(
    resource=ExpendableResource.SPELL_SLOT, expended=False
)

MAGIC_KEY = "gameplay_tool:magic"
LONG_KEY = "magic_long_casting"
BREAK_KEY = "magic_concentration_break"


def _components() -> tuple[ComponentDraft, ComponentDraft]:
    """The two components S-1 blocked, now gated rather than unresolved.

    Both carry the *same* gate on ``applies_when``. That is the scope
    preservation the stop was about: K4's consequences are consequences **of a
    long casting**, and a component stating only ``CONCENTRATION_BROKEN`` would
    reach every broken Concentration in the game.

    The break itself rides :class:`FactQualifier` rather than the component,
    because a component has exactly one ``applies_when`` and the gate is
    already there. Qualifiers compose conjunctively inward, which is the
    reading the source prints: *a long casting* whose *Concentration is
    broken*.
    """
    return (
        ComponentDraft(
            record_key=MAGIC_KEY,
            semantic_key=LONG_KEY,
            handling=ComponentHandling.STRUCTURED,
            facts=(RECURRING, SUSTAINED),
            applies_when=LONG_CASTING,
        ),
        ComponentDraft(
            record_key=MAGIC_KEY,
            semantic_key=BREAK_KEY,
            handling=ComponentHandling.STRUCTURED,
            facts=(TERMINATION, EXPENDITURE),
            applies_when=LONG_CASTING,
            fact_qualifiers=(
                FactQualifier(
                    fact_key=fact_key(TERMINATION),
                    applies_when=CONCENTRATION_BROKEN,
                ),
                FactQualifier(
                    fact_key=fact_key(EXPENDITURE),
                    applies_when=CONCENTRATION_BROKEN,
                ),
            ),
        ),
    )


LONG_COMPONENT, BREAK_COMPONENT = _components()


def _fact_edge(
    component_key: str, fact: object, span_id: str, role: ProvenanceRole
) -> ProvenanceClaim:
    return ProvenanceClaim(
        target_kind=ProvenanceTargetKind.FACT,
        target_key=(MAGIC_KEY, component_key, fact_key(fact)),
        span_id=span_id,
        role=role,
    )


#: One row per authoritative element, naming the span its evidence comes from
#: and the role that evidence carries.
MAGIC_PROVENANCE = (
    # K2a prints the gate once, and it is the gate of both components. The
    # component whose sentence continues into K2b owns it; the other restates
    # the same printed condition, because a component has one ``applies_when``
    # and there is no position for a condition two components share.
    ProvenanceClaim(
        target_kind=ProvenanceTargetKind.COMPONENT,
        target_key=component_target_key(LONG_COMPONENT),
        span_id=K2A_SPAN,
        role=ProvenanceRole.PRIMARY,
    ),
    ProvenanceClaim(
        target_kind=ProvenanceTargetKind.COMPONENT,
        target_key=component_target_key(BREAK_COMPONENT),
        span_id=K2A_SPAN,
        role=ProvenanceRole.CONTEXTUAL,
    ),
    _fact_edge(LONG_KEY, RECURRING, K2B_SPAN, ProvenanceRole.PRIMARY),
    _fact_edge(LONG_KEY, SUSTAINED, K3_SPAN, ProvenanceRole.PRIMARY),
    # K4a prints the break once, for both consequences, and a qualifier belongs
    # to one fact — so the same asymmetry appears again one level down.
    ProvenanceClaim(
        target_kind=ProvenanceTargetKind.FACT_QUALIFIER,
        target_key=fact_qualifier_target_key(
            MAGIC_KEY, BREAK_KEY, fact_key(TERMINATION)
        ),
        span_id=K4A_SPAN,
        role=ProvenanceRole.PRIMARY,
    ),
    ProvenanceClaim(
        target_kind=ProvenanceTargetKind.FACT_QUALIFIER,
        target_key=fact_qualifier_target_key(
            MAGIC_KEY, BREAK_KEY, fact_key(EXPENDITURE)
        ),
        span_id=K4A_SPAN,
        role=ProvenanceRole.CONTEXTUAL,
    ),
    _fact_edge(BREAK_KEY, TERMINATION, K4B_SPAN, ProvenanceRole.PRIMARY),
    _fact_edge(BREAK_KEY, EXPENDITURE, K4C_SPAN, ProvenanceRole.PRIMARY),
)


def magic_draft(
    components: tuple[ComponentDraft, ...] | None = None,
    provenance: tuple[ProvenanceClaim, ...] = MAGIC_PROVENANCE,
) -> RepresentationDraft:
    return RepresentationDraft(
        records=(RecordDraft(semantic_key=MAGIC_KEY, kind=RecordKind.GAMEPLAY_TOOL),),
        components=_components() if components is None else components,
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=provenance,
    )


def _span(span_id: str, start: int, end: int) -> SemanticSpan:
    return SemanticSpan(
        span_id=span_id,
        leaf_id=K_LEAF,
        char_start=start,
        char_end=end,
        disposition=SemanticDisposition.SUBSTANTIVE,
        review_state=ReviewState.ACCEPTED,
    )


MAGIC_SPANS = (
    _span(K2A_SPAN, K2_START, K2_BOUNDARY),
    _span(K2B_SPAN, K2_BOUNDARY, K2_END),
    _span(K3_SPAN, K3_START, K3_END),
    _span(K4A_SPAN, K4_START, K4_FAILS),
    _span(K4B_SPAN, K4_FAILS, K4_SLOT),
    _span(K4C_SPAN, K4_SLOT, K4_END),
)


def magic_ledger() -> ClassificationLedger:
    return build_ledger(spans=MAGIC_SPANS)


# ---------------------------------------------------------------------------
# The transcription, against evidence this module did not produce
# ---------------------------------------------------------------------------


def test_the_transcription_equals_the_pinned_source_evidence() -> None:
    """Every literal above, checked at the pinned SRD digest.

    Comparing hand-entered strings against hand-entered extents proves nothing:
    a same-length paraphrase would pass every other test in this file. This is
    the one that fails.
    """
    assert EVIDENCE_PATH.exists(), (
        f"pinned source evidence is missing: {EVIDENCE_PATH}. Re-derive it with "
        "the discovery script before reading anything below as source-grounded."
    )
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    assert evidence["authoritative_source_hash"] == PINNED_SOURCE_SHA256

    rows = {
        row["obligation"]: row
        for row in evidence["coordinates"]
        if row["entry"] == "Magic [Action]"
    }
    for name, start, end, text in (
        ("K2", K2_START, K2_END, K2_TEXT),
        ("K3", K3_START, K3_END, K3_TEXT),
        ("K4", K4_START, K4_END, K4_TEXT),
    ):
        row = rows[name]
        assert row["leaf_id"] == K_LEAF, name
        assert (row["char_start"], row["char_end"]) == (start, end), name
        assert row["source_text"] == text, name

    lengths = {row["leaf_id"]: row["length"] for row in evidence["leaf_partition"]}
    assert lengths[K_LEAF] == K_LEAF_LENGTH

    # And K1 is on the entry's other leaf, which is why a 1-minute spell
    # falling outside K1 says nothing about whether K2 reaches it.
    assert rows["K1"]["leaf_id"] != K_LEAF


def test_the_partition_is_the_printed_sentence_and_nothing_else() -> None:
    """Three derived boundaries, each reassembling the text it was cut from."""
    assert K2A_TEXT + K2B_TEXT == K2_TEXT
    assert K2_START < K2_BOUNDARY < K2_END
    assert K2A_TEXT.endswith("or longer, ")
    assert K4_START < K4_FAILS < K4_SLOT < K4_END
    assert K4_TEXT[: K4_FAILS - K4_START].endswith("is broken, ")
    assert K4_END <= K_LEAF_LENGTH


# ---------------------------------------------------------------------------
# What the threshold actually reaches
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "printed"),
    [
        (
            "the clause's own boundary case",
            SpellCastingTime(amount=1, unit=TimeUnit.MINUTE),
        ),
        (
            "a longer casting in the same unit",
            SpellCastingTime(amount=10, unit=TimeUnit.MINUTE),
        ),
        ("a longer unit at any amount", SpellCastingTime(amount=1, unit=TimeUnit.HOUR)),
        (
            "the ritual end of the range",
            SpellCastingTime(amount=24, unit=TimeUnit.HOUR),
        ),
        ("a whole day", SpellCastingTime(amount=1, unit=TimeUnit.DAY)),
    ],
)
def test_a_timed_casting_qualifies_from_the_instant_it_begins(
    label: str, printed: SpellCastingTime
) -> None:
    """*"1 minute or longer"*, the minute included.

    Nothing here consults elapsed time: the operand is the spell's printed
    descriptor, so the answer is the same before the casting starts as during
    it. That is the whole reason this is not ``ELAPSED_DURATION`` — which would
    have meant time already spent casting, and would have been false at the
    moment K2 first has to apply.
    """
    assert casting_time_meets(THRESHOLD, printed), label


@pytest.mark.parametrize(
    "cost",
    [ActionCost.ACTION, ActionCost.BONUS_ACTION, ActionCost.REACTION],
    ids=["action", "bonus-action", "reaction"],
)
def test_an_immediate_casting_does_not_satisfy_a_timed_threshold(
    cost: ActionCost,
) -> None:
    """Outside by structure, not by a comparison that came out false.

    :class:`SpellCastingTime` admits exactly one arm, so a spell cast as an
    Action states no amount and no unit at all. There is nothing for an amount
    threshold to meet, and no arithmetic that could be got wrong.
    """
    printed = SpellCastingTime(cost=cost)
    assert printed.amount is None and printed.unit is None
    assert not casting_time_meets(THRESHOLD, printed)


@pytest.mark.parametrize(
    ("least", "printed", "expected"),
    [
        # The three counterexamples the schema review reproduced against a
        # comparison that ranked unit *names* and dropped the amounts.
        ((120, TimeUnit.MINUTE), (1, TimeUnit.HOUR), False),
        ((1, TimeUnit.HOUR), (120, TimeUnit.MINUTE), True),
        ((1, TimeUnit.MINUTE), (60, TimeUnit.SECOND), True),
        # Equality across calendar units, in both directions.
        ((1, TimeUnit.HOUR), (60, TimeUnit.MINUTE), True),
        ((60, TimeUnit.MINUTE), (1, TimeUnit.HOUR), True),
        ((1, TimeUnit.DAY), (24, TimeUnit.HOUR), True),
        ((24, TimeUnit.HOUR), (1, TimeUnit.DAY), True),
        # A shorter unit that genuinely falls short, and the boundary beside it.
        ((1, TimeUnit.MINUTE), (59, TimeUnit.SECOND), False),
        ((1, TimeUnit.HOUR), (59, TimeUnit.MINUTE), False),
        # Same unit, at and either side of the boundary.
        ((10, TimeUnit.MINUTE), (9, TimeUnit.MINUTE), False),
        ((10, TimeUnit.MINUTE), (10, TimeUnit.MINUTE), True),
        ((10, TimeUnit.MINUTE), (11, TimeUnit.MINUTE), True),
    ],
    ids=[
        "two-hours-stated-in-minutes-vs-one-hour",
        "one-hour-vs-two-hours-stated-in-minutes",
        "one-minute-vs-sixty-seconds",
        "an-hour-equals-sixty-minutes",
        "sixty-minutes-equals-an-hour",
        "a-day-equals-twenty-four-hours",
        "twenty-four-hours-equals-a-day",
        "fifty-nine-seconds-falls-short",
        "fifty-nine-minutes-falls-short",
        "same-unit-below",
        "same-unit-at",
        "same-unit-above",
    ],
)
def test_a_casting_time_is_compared_by_magnitude_not_by_the_rank_of_its_unit(
    least: tuple[int, TimeUnit],
    printed: tuple[int, TimeUnit],
    expected: bool,
) -> None:
    """The correction: two stated durations, reduced to one scale.

    The first shape of this comparison ranked the unit *names* and dropped both
    amounts whenever the units differed, which was over-inclusive one way (a
    1-hour casting satisfied a 120-minute threshold) and under-inclusive the
    other (a 60-second casting failed a 1-minute one). Second, minute, hour and
    day have lengths the calendar fixes, so all of these are arithmetic and
    none of them is a ruling about the corpus.
    """
    threshold = CastingTimeThreshold(at_least_amount=least[0], at_least_unit=least[1])
    assert (
        casting_time_meets(
            threshold, SpellCastingTime(amount=printed[0], unit=printed[1])
        )
        is expected
    )


@pytest.mark.parametrize(
    ("least", "printed"),
    [
        ((1, TimeUnit.MINUTE), SpellCastingTime(amount=1, unit=TimeUnit.ROUND)),
        ((1, TimeUnit.MINUTE), SpellCastingTime(amount=100, unit=TimeUnit.ROUND)),
        ((1, TimeUnit.MINUTE), SpellCastingTime(amount=1, unit=TimeUnit.TURN)),
        # The threshold side too, reached only by a threshold the intrinsic
        # check would refuse — the function does not rely on that check having
        # run.
        ((1, TimeUnit.ROUND), SpellCastingTime(amount=1, unit=TimeUnit.MINUTE)),
    ],
    ids=["one-round", "a-hundred-rounds", "one-turn", "a-cadence-threshold"],
)
def test_a_cadence_of_the_initiative_cycle_is_refused_not_answered(
    least: tuple[int, TimeUnit], printed: SpellCastingTime
) -> None:
    """The supported forms end here, and the boundary is explicit.

    A round and a turn are slices of the initiative cycle; no printed casting
    time states how long one lasts, and this module may not decide it. So the
    comparison refuses rather than returning ``False`` — ``False`` would say
    *"this rule does not reach that spell"*, a substantive answer, for a
    question that was never asked. Nothing in the SRD prints a casting time in
    rounds or turns, so no corpus record reaches this; a batch that forces one
    is a schema question, and it is recorded as one.
    """
    threshold = CastingTimeThreshold(at_least_amount=least[0], at_least_unit=least[1])
    with pytest.raises(UncomparableCastingTimeError):
        casting_time_meets(threshold, printed)


def test_a_one_minute_spell_falls_outside_magic_k1_not_outside_the_action() -> None:
    """The distinction the checkpoint had to state precisely.

    K1's eligibility fact says which spells the **Magic action reaches** by the
    cost they print. A 1-minute spell prints no cost, so it matches no
    eligibility fact — it falls outside *K1*. K2 is a different clause about a
    different thing: a further requirement **inside** the action, which is why
    it needed a new structure rather than a wider ``ActionCost``.
    """
    eligibility = CASES["K1"][1]
    assert eligibility.subject is EligibilitySubject.SPELL
    assert eligibility.cost is ActionCost.ACTION
    # The two clauses range over different arms of the same printed descriptor,
    # and no ``ActionCost`` member denotes a duration.
    assert not hasattr(eligibility, "casting_time")
    assert all(not member.value[0].isdigit() for member in ActionCost)


# ---------------------------------------------------------------------------
# Why applicability, and not a fact
# ---------------------------------------------------------------------------


def test_the_gate_scopes_both_components_and_the_composition_validates() -> None:
    """The whole mapping, through the real validator, on the real extents."""
    assert LONG_COMPONENT.applies_when == LONG_CASTING
    assert BREAK_COMPONENT.applies_when == LONG_CASTING
    assert validate_representation(magic_draft(), magic_ledger(), MAGIC_CORPUS) == ()


def test_the_composed_facts_are_the_ones_the_source_cases_pinned() -> None:
    """The gate did not change what K2, K3 and K4 say — only their scope."""
    assert CASES["K2"][1] == RECURRING
    assert CASES["K3"][1] == SUSTAINED
    assert CASES["K4"][1] == EXPENDITURE


def test_the_break_stays_conditional_inside_the_gate() -> None:
    """Both consequences are qualified, and neither is merged into the gate.

    A consumer reading ``magic_concentration_break`` sees two scopes narrowing
    inward — a long casting, whose Concentration is broken — rather than one
    flattened condition that would make the spell fail whenever either held.
    """
    qualified = {q.fact_key: q.applies_when for q in BREAK_COMPONENT.fact_qualifiers}
    assert qualified == {
        fact_key(TERMINATION): CONCENTRATION_BROKEN,
        fact_key(EXPENDITURE): CONCENTRATION_BROKEN,
    }
    assert CONCENTRATION_BROKEN != LONG_CASTING
    # And the gate is not restated inside the qualifier, which would assert one
    # condition twice on a single path.
    assert all(q.applies_when != LONG_CASTING for q in BREAK_COMPONENT.fact_qualifiers)


def test_a_repeated_gate_fact_is_refused_where_a_repeated_gate_is_not() -> None:
    """The asymmetry that decided the shape.

    ``_validate_duplicated_fact_authority`` refuses two components of one
    record holding the same fact drawn from the same substantive span — which
    is exactly what a gate carried as a *fact* and restated on both components
    would be. Applicability carries no such rule, because a condition two
    structures share is one condition, not two claims. That is what makes it
    the scope-preserving carrier, and it is asserted here rather than argued.
    """
    # Admitted: one gate, two components, one span.
    assert validate_representation(magic_draft(), magic_ledger(), MAGIC_CORPUS) == ()

    # Refused: the same sharing expressed as a duplicated fact.
    doubled = tuple(
        (
            replace(component, facts=(*component.facts, SUSTAINED))
            if component.semantic_key == BREAK_KEY
            else component
        )
        for component in _components()
    )
    findings = validate_representation(
        magic_draft(
            components=doubled,
            provenance=(
                *MAGIC_PROVENANCE,
                _fact_edge(BREAK_KEY, SUSTAINED, K3_SPAN, ProvenanceRole.CONTEXTUAL),
            ),
        ),
        magic_ledger(),
        MAGIC_CORPUS,
    )
    assert any(
        "one source statement may not become two copies" in f for f in findings
    ), findings


def test_each_span_carries_exactly_one_primary_owner() -> None:
    """Six substantive spans, six primary owners, no span owned twice."""
    primary = [c for c in MAGIC_PROVENANCE if c.role is ProvenanceRole.PRIMARY]
    assert len({c.span_id for c in primary}) == len(primary) == len(MAGIC_SPANS)
    owners = {c.span_id: c.target_key for c in primary}
    assert owners[K2A_SPAN] == component_target_key(LONG_COMPONENT)
    assert owners[K2B_SPAN] == (MAGIC_KEY, LONG_KEY, fact_key(RECURRING))
    assert owners[K3_SPAN] == (MAGIC_KEY, LONG_KEY, fact_key(SUSTAINED))
    assert owners[K4A_SPAN] == fact_qualifier_target_key(
        MAGIC_KEY, BREAK_KEY, fact_key(TERMINATION)
    )
    assert owners[K4B_SPAN] == (MAGIC_KEY, BREAK_KEY, fact_key(TERMINATION))
    assert owners[K4C_SPAN] == (MAGIC_KEY, BREAK_KEY, fact_key(EXPENDITURE))


# ---------------------------------------------------------------------------
# The wire contract: round trip, refusals, and the sibling rebuilders
# ---------------------------------------------------------------------------


def test_the_gate_round_trips_through_its_canonical_payload() -> None:
    """``applicability_payload`` → ``build_applicability``, and back equal."""
    payload = applicability_payload(LONG_CASTING)
    assert payload is not None
    assert payload["casting_time"] == {"at_least_amount": 1, "at_least_unit": "minute"}
    assert _rebuild_applicability(payload, "magic/gate") == LONG_CASTING


def test_a_component_that_states_no_gate_omits_the_key() -> None:
    """The omission rule, which is what leaves accepted payloads unmoved.

    A post-schema-3 field carrying no meaning is absent from the canonical
    payload, so every applicability accepted under schemas 3 through 6 already
    has its schema-7 canonical form. Without this, minting a kind would rewrite
    every accepted component.
    """
    payload = applicability_payload(CONCENTRATION_BROKEN)
    assert payload is not None
    assert "casting_time" not in payload
    assert _rebuild_applicability(payload, "probe") == CONCENTRATION_BROKEN


@pytest.mark.parametrize(
    ("label", "threshold"),
    [
        (
            "a threshold of zero reaches every timed casting",
            CastingTimeThreshold(at_least_amount=0, at_least_unit=TimeUnit.MINUTE),
        ),
        (
            "a negative amount states no duration",
            CastingTimeThreshold(at_least_amount=-1, at_least_unit=TimeUnit.MINUTE),
        ),
        (
            "a round is a cadence of the initiative cycle",
            CastingTimeThreshold(at_least_amount=1, at_least_unit=TimeUnit.ROUND),
        ),
        (
            "and so is a turn",
            CastingTimeThreshold(at_least_amount=1, at_least_unit=TimeUnit.TURN),
        ),
    ],
)
def test_an_inadmissible_threshold_is_refused(
    label: str, threshold: CastingTimeThreshold
) -> None:
    """Both declared invariants, asked of the validator every seam calls."""
    findings = applicability_violations(
        Applicability(kind=ApplicabilityKind.SPELL_CASTING_TIME, casting_time=threshold)
    )
    assert findings, label


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("not an object", "1 minute"),
        ("missing the amount", {"at_least_unit": "minute"}),
        ("missing the unit", {"at_least_amount": 1}),
        ("an unknown unit", {"at_least_amount": 1, "at_least_unit": "fortnight"}),
        (
            "an extra key",
            {"at_least_amount": 1, "at_least_unit": "minute", "at_most": 2},
        ),
        (
            "an amount that is not an integer",
            {"at_least_amount": "1", "at_least_unit": "minute"},
        ),
        (
            "an amount that is a boolean",
            {"at_least_amount": True, "at_least_unit": "minute"},
        ),
        (
            "an inadmissible amount on the wire",
            {"at_least_amount": 0, "at_least_unit": "minute"},
        ),
    ],
)
def test_a_malformed_threshold_payload_is_refused_rather_than_repaired(
    label: str, value: object
) -> None:
    """No default rebuild, and no interpretation: the loader refuses."""
    with pytest.raises(ValueError):
        build_casting_time_threshold(value, "probe")


def test_the_kind_ranges_over_exactly_one_field() -> None:
    """``Applicability`` is not a predicate language.

    Each kind names exactly the field set it ranges over. A value carrying an
    operand its kind does not name is two claims wearing one shape, and a kind
    carrying none of its operands states nothing — both are refused rather than
    interpreted.
    """
    assert applicability_violations(LONG_CASTING) == []
    assert applicability_violations(Applicability(ApplicabilityKind.SPELL_CASTING_TIME))
    assert applicability_violations(
        Applicability(
            kind=ApplicabilityKind.EFFECT_STATE,
            effect_state=StateEffectKind.CONCENTRATION_BROKEN,
            casting_time=THRESHOLD,
        )
    )


def test_the_gate_survives_storage_and_reconstruction(session: Session) -> None:
    """The stored-state rebuilder reads back what the projection wrote."""
    base = build_representation()
    components = list(base.components)
    components[0] = replace(components[0], applies_when=LONG_CASTING)
    identified = identify_projection(
        candidate_of(
            RELEASE_BINDING,
            build_ledger(),
            replace(base, components=tuple(components)),
        )
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    stored = rebuilt.representation.components[0].applies_when
    assert stored is not None
    assert stored == LONG_CASTING
    assert stored.casting_time == THRESHOLD
    assert verify_persisted_state(session, identified.projection_uuid) == ()


def test_the_override_seam_rebuilds_the_gate() -> None:
    """The patch layer reads the same wire contract as every other seam."""
    payload = applicability_payload(LONG_CASTING)
    assert payload is not None
    assert _build_applicability(payload, "applies_when") == LONG_CASTING


def test_the_override_seam_refuses_a_malformed_gate() -> None:
    """And refuses through its own typed error, not an incidental one."""
    payload = applicability_payload(LONG_CASTING)
    assert payload is not None
    payload["casting_time"] = {"at_least_unit": "minute"}
    with pytest.raises(InvalidPatchError):
        _build_applicability(payload, "applies_when")


LEGACY_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "legacy_conditions_1_unanchored_schema3.json"
)


def _artifact_with(applies_when: object, tmp_path: object, name: str) -> Path:
    """The committed specimen carrying one applicability, declared at schema 7.

    A casting-time gate *is* schema-7 meaning, so the declaration and the batch
    anchors move with it — otherwise the legality guard refuses the file before
    its key shape is ever read, and the test would pass for the wrong reason.
    """
    raw: dict[str, Any] = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    raw["representation"]["components"][0]["applies_when"] = applies_when
    raw["representation_schema"] = {"version": SCHEMA_7_VERSION, "hash": SCHEMA_7_HASH}
    raw["acceptance"]["schema_anchors"] = [
        {
            "batch_id": batch["batch_id"],
            "proposal_identity": batch["proposal_identity"],
            "schema_version": SCHEMA_7_VERSION,
            "schema_hash": SCHEMA_7_HASH,
        }
        for batch in raw["acceptance"]["batches"]
    ]
    path = Path(str(tmp_path)) / name
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def test_the_committed_loader_rebuilds_the_gate(tmp_path: object) -> None:
    """Accepted authority carrying the gate loads with its threshold intact."""
    path = _artifact_with(applicability_payload(LONG_CASTING), tmp_path, "gate.json")
    loaded = load_accepted_inputs(path)
    assert loaded.oracle.representation.components[0].applies_when == LONG_CASTING


@pytest.mark.parametrize(
    ("label", "mangle"),
    [
        ("not an object", "1 minute"),
        ("missing a required key", {"at_least_amount": 1}),
        ("an unknown unit", {"at_least_amount": 1, "at_least_unit": "aeon"}),
        ("an inadmissible unit", {"at_least_amount": 1, "at_least_unit": "round"}),
    ],
)
def test_the_committed_loader_refuses_a_malformed_gate(
    label: str, mangle: object, tmp_path: object
) -> None:
    """Each failure is the loader's own typed error, naming the field at fault."""
    payload = applicability_payload(LONG_CASTING)
    assert payload is not None
    payload["casting_time"] = mangle
    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(_artifact_with(payload, tmp_path, "malformed.json"))
    assert "casting_time" in str(raised.value), (label, raised.value)


# ---------------------------------------------------------------------------
# What the mint declared, and what it did not move
# ---------------------------------------------------------------------------


def test_the_mint_declares_exactly_one_new_vocabulary_member() -> None:
    """One kind at schema 7 — no family, no ownership form, no nullable field.

    The manifest is emitted by the schema payload, so this is the smallest
    extension claim stated where the hash covers it rather than in prose.
    """
    rows = [
        row
        for row in introduction_manifest()
        if row["introduced_in"] == SCHEMA_7_VERSION
    ]
    assert len(rows) == 1, rows
    assert rows[0]["kind"] == "vocabulary_member"
    assert rows[0]["name"] == ApplicabilityKind.SPELL_CASTING_TIME.value


def test_the_two_new_invariants_are_declared_inside_the_schema_identity() -> None:
    """Declared where weakening one moves the hash and strands the lift."""
    declared = {row["id"] for row in invariant_manifest()}
    assert {
        "casting_time_threshold.at_least_amount.states-a-duration",
        "casting_time_threshold.at_least_unit.calendar-units-only",
    } <= declared
