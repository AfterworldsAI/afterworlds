"""Whole printed mechanics, composed — CRD Issue 5d, batch actions-1.

The source-case module proves each schema-6 shape against the clause it came
from, one fact at a time. That is necessary and it is not sufficient: a
mechanic is a *composition*, and the defects this module exists to catch are
all defects of composition rather than of shape.

* ``Help``'s two arms are governed by two different clauses of one paragraph.
  Every fact in it is valid in isolation and the component is valid too — and
  the effective view was still wrong, because it discarded which arm each
  clause governs. Nothing that looks at one fact can see that.
* ``Ready`` states an allowance, a trigger resolution, an eligibility
  restriction, a duration and an expenditure in one component, and the question
  is whether they survive together and reach a consumer together.
* A scope rule reads a *component*, not a fact. ``ANY_OF`` gave a refused
  condition a place to hide inside one, and only a composed component shows it.

Every rejection here is stated beside the **valid sibling** it is one edit away
from, because a refusal that fires on everything proves nothing about the rule
it claims to state.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import replace
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest

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
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    AbilityCheckFact,
    AbilityScore,
    ActionAllowanceFact,
    ActionCost,
    ActionEconomyFact,
    AllowanceScope,
    Applicability,
    ApplicabilityKind,
    AutomaticOutcome,
    ComponentDraft,
    ComponentOption,
    ConditionKind,
    DcKind,
    EligibilitySubject,
    FactQualifier,
    MalformedFactPayloadError,
    MovementTransportFact,
    ParticipantRole,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RollContext,
    SizeComparison,
    SizeRelation,
    TransportKind,
    applicability_violations,
    component_participant_violations,
    component_roll_outcome_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_key,
    option_set_violations,
    prose_binding_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_5_HASH,
    SCHEMA_5_VERSION,
    schema_binding_violations,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.services.rules_authority.application import (
    EffectiveAuthority,
    SourceProse,
    _base_records,
)
from afterworlds.services.rules_authority.binding import RulesPackageBinding
from afterworlds.services.rules_authority.views import (
    build_gamemaster_view,
    build_typed_view,
)
from tests.ingestion.mechanical.conftest import (
    OPEN_ENDED_KEY,
    PROSE_LEAF,
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
    HIDE_PREREQUISITE,
    _canonical,
)

LEGACY_PATH = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "legacy_conditions_1_unanchored_schema3.json"
)

#: A substantive span carries exactly one **primary** owner, so a composition
#: needs one span per element it wants to own text — not one per element it
#: states, since evidence may also be contextual. These compositions give every
#: fact its own primary span because the fixture leaf has no printed structure
#: to say otherwise; `test_schema_6_ready_source_provenance` shows what the
#: distinction is worth on real coordinates, where the shared Reaction is
#: evidenced contextually on the clause that prints it. The fixture ledger is a
#: shape to work in rather than a constant to assert against.
_LEAF_LENGTH = 40


def _spans(count: int) -> tuple[str, ...]:
    """*count* consecutive substantive spans partitioning the spell leaf."""
    edges = [round(_LEAF_LENGTH * i / count) for i in range(count + 1)]
    return tuple(
        derive_span_id(SPELL_LEAF, start, end)
        for start, end in zip(edges[:-1], edges[1:], strict=True)
    )


def _accepted(leaf: str, extents: tuple[tuple[int, int], ...]):
    return tuple(
        SemanticSpan(
            span_id=derive_span_id(leaf, start, end),
            leaf_id=leaf,
            char_start=start,
            char_end=end,
            disposition=SemanticDisposition.SUBSTANTIVE,
            review_state=ReviewState.ACCEPTED,
        )
        for start, end in extents
    )


def _ledger(
    count: int, prose: bool = False, prose_parts: int = 2
) -> ClassificationLedger:
    """The fixture ledger with the spell leaf partitioned *count* ways.

    *prose* partitions the prose leaf too, which is what a component whose arms
    are governed by different clauses of one paragraph needs: one accepted span
    per clause, and one primary claim per span.
    """
    dropped = {SPELL_LEAF, PROSE_LEAF} if prose else {SPELL_LEAF}
    kept = tuple(s for s in build_ledger().spans if s.leaf_id not in dropped)
    edges = [round(_LEAF_LENGTH * i / count) for i in range(count + 1)]
    spans = _accepted(SPELL_LEAF, tuple(zip(edges[:-1], edges[1:], strict=True)))
    if prose:
        spans += _accepted(PROSE_LEAF, _prose_extents(prose_parts))
    return build_ledger(spans=kept + spans)


#: The prose leaf, and the two halves ``Help``'s arms are actually governed
#: by. One paragraph, two clauses: the extent is what
#: ``_validate_prose_extent`` checks against the accepted span, so a binding
#: cannot claim a scope its span did not accept.
_PROSE_LENGTH = 30


def _prose_extents(count: int) -> tuple[tuple[int, int], ...]:
    """*count* consecutive clauses partitioning the prose leaf."""
    edges = [round(_PROSE_LENGTH * i / count) for i in range(count + 1)]
    return tuple(zip(edges[:-1], edges[1:], strict=True))


_PROSE_HALVES = _prose_extents(2)


def _prose(
    option_key: str,
    extent: tuple[int, int] = (0, _PROSE_LENGTH),
    component_key: str = OPEN_ENDED_KEY,
) -> ProseBindingDraft:
    start, end = extent
    return ProseBindingDraft(
        component_key=component_key,
        record_key=SPELL_KEY,
        chunk_id=build_representation().prose_bindings[0].chunk_id,
        span_id=derive_span_id(PROSE_LEAF, start, end),
        chunk_char_start=start,
        chunk_char_end=end,
        irreducibility_reason_code="open_ended_effect",
        option_key=option_key,
    )


def _composed(
    components: ComponentDraft | tuple[ComponentDraft, ...],
    bindings: tuple[ProseBindingDraft, ...],
    fact_spans: tuple[tuple[tuple[str, ...], str], ...],
) -> object:
    """The fixture draft carrying one composed component and its provenance."""
    base = build_representation()
    kept = tuple(
        claim
        for claim in base.provenance
        if claim.target_kind
        not in (ProvenanceTargetKind.PROSE_BINDING, ProvenanceTargetKind.FACT)
    )
    # The retained relationship claim named the leaf's whole span, which the
    # partition above replaced.
    kept = tuple(
        (
            replace(claim, span_id=fact_spans[0][1])
            if claim.span_id == SPELL_SPAN
            else claim
        )
        for claim in kept
    )
    if isinstance(components, ComponentDraft):
        components = (components,)
    return replace(
        base,
        components=components,
        prose_bindings=bindings,
        provenance=(
            *kept,
            *(
                ProvenanceClaim(
                    ProvenanceTargetKind.FACT, key, span, ProvenanceRole.PRIMARY
                )
                for key, span in fact_spans
            ),
            *(
                ProvenanceClaim(
                    ProvenanceTargetKind.PROSE_BINDING,
                    prose_binding_target_key(binding),
                    binding.span_id,
                    ProvenanceRole.PRIMARY,
                )
                for binding in bindings
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Help, pp182-183 — one component, two arms, two governing clauses
# ---------------------------------------------------------------------------
#
#   "you momentarily aid an ally ... That ally has Advantage on the next
#   ability check they make with the chosen skill or tool."   (arm 1, H3)
#   "you feint, distract the target, or in some other way team up ...
#   giving Advantage to the next attack roll by one of your allies against
#   that enemy"                                               (arm 2, H6)
#
# Two arms of one exhaustive choice, each with its own typed benefit and its
# own printed clause. Binding either clause at component grain would say it
# governs both arms, which is false about the arm it does not describe - not
# merely imprecise - so the scope is authority, not decoration.
#
# The two clauses here are halves of the fixture's 30-character prose leaf, not
# `Help`'s printed extents: this composition proves that a per-arm scope
# survives every path, and it makes no claim about where `Help` is printed.

ABILITY_ARM = "aid-an-ally-arm"
ATTACK_ARM = "team-up-arm"
_HELP_SPANS = _spans(2)


def _help_component() -> ComponentDraft:
    return ComponentDraft(
        record_key=SPELL_KEY,
        semantic_key=OPEN_ENDED_KEY,
        handling=ComponentHandling.MIXED,
        irreducibility_reason_code="open_ended_effect",
        options=(
            ComponentOption(semantic_key=ABILITY_ARM, facts=(CASES["H3"][1],)),
            ComponentOption(semantic_key=ATTACK_ARM, facts=(CASES["H6"][1],)),
        ),
    )


def _help_draft(first: str = ABILITY_ARM, second: str = ATTACK_ARM) -> object:
    """Help, with arm 1's clause bound to *first* and arm 2's to *second*."""
    return _composed(
        _help_component(),
        (
            _prose(first, _PROSE_HALVES[0]),
            _prose(second, _PROSE_HALVES[1]),
        ),
        (
            (
                (SPELL_KEY, OPEN_ENDED_KEY, fact_key(CASES["H3"][1]), ABILITY_ARM),
                _HELP_SPANS[0],
            ),
            (
                (SPELL_KEY, OPEN_ENDED_KEY, fact_key(CASES["H6"][1]), ATTACK_ARM),
                _HELP_SPANS[1],
            ),
        ),
    )


def test_help_composes_and_validates_as_printed() -> None:
    """The whole mechanic, not one fact of it, passes the build contract."""
    assert (
        validate_representation(_help_draft(), _ledger(2, prose=True), bound_corpus())
        == ()
    )


def test_help_publishes_each_clause_against_the_arm_it_governs() -> None:
    """The defect this module was written for.

    Two clauses of one paragraph, so two accepted spans and two extents — one
    primary claim per span is the provenance rule, and a binding may not claim
    an extent its span did not accept. What the scope adds is which *arm* each
    clause governs, which no extent states.
    """
    records = _base_records(
        candidate_of(RELEASE_BINDING, _ledger(2, prose=True), _help_draft())
    )
    prose = records[SPELL_KEY].components[0].governing_prose
    assert all(isinstance(entry, SourceProse) for entry in prose)
    assert sorted(entry.option_key for entry in prose) == sorted(  # type: ignore[union-attr]
        [ABILITY_ARM, ATTACK_ARM]
    )


def test_moving_a_clause_between_arms_changes_the_effective_record() -> None:
    """Two arms, two clauses, and swapping them is a different mechanic.

    Before the scope was carried, both arrangements produced byte-identical
    effective records: the view said "this paragraph governs this component"
    twice, and which benefit each clause described was gone.
    """

    def prose_of(draft: object) -> tuple[SourceProse, ...]:
        records = _base_records(
            candidate_of(RELEASE_BINDING, _ledger(2, prose=True), draft)
        )
        return records[SPELL_KEY].components[0].governing_prose  # type: ignore[return-value]

    def governed_by(draft: object) -> dict[tuple[int, int], str]:
        return {
            (entry.char_start, entry.char_end): entry.option_key
            for entry in prose_of(draft)
        }

    printed = governed_by(_help_draft())
    swapped = governed_by(_help_draft(first=ATTACK_ARM, second=ABILITY_ARM))
    # Keyed by extent so the difference is the *scope* and nothing else: both
    # arrangements bind the same two clauses of the same chunk, and an
    # assertion on the entries as a whole would still hold if the scope were
    # dropped and only the offsets compared.
    assert set(printed) == set(swapped)
    assert printed != swapped


def test_component_wide_prose_stays_distinguishable_from_an_arm_s_own() -> None:
    """The two scopes are different authority, and the view says which.

    A component-wide clause governs whichever arm is taken; an arm's own clause
    governs only that arm. Collapsing them in either direction publishes a
    claim the source does not make.
    """
    component_wide = _composed(
        _help_component(),
        (_prose(""),),
        (
            (
                (SPELL_KEY, OPEN_ENDED_KEY, fact_key(CASES["H3"][1]), ABILITY_ARM),
                _HELP_SPANS[0],
            ),
            (
                (SPELL_KEY, OPEN_ENDED_KEY, fact_key(CASES["H6"][1]), ATTACK_ARM),
                _HELP_SPANS[1],
            ),
        ),
    )
    assert validate_representation(component_wide, _ledger(2), bound_corpus()) == ()
    records = _base_records(candidate_of(RELEASE_BINDING, _ledger(2), component_wide))
    entries = records[SPELL_KEY].components[0].governing_prose
    assert [e.option_key for e in entries] == [""]  # type: ignore[union-attr]

    scoped = (
        _base_records(candidate_of(RELEASE_BINDING, _ledger(2), _help_draft()))[
            SPELL_KEY
        ]
        .components[0]
        .governing_prose
    )
    assert entries != scoped


def test_the_gamemaster_view_keeps_each_clause_bound_to_its_arm() -> None:
    """The scope survives text resolution, which is the last thing that reads it.

    ``_resolve_prose`` slices a chunk to the accepted extent and returns a
    replaced entry; a resolution that rebuilt the entry field by field would
    drop a field it did not know about, and the GameMaster — who is reading
    this to adjudicate — would get two passages and no way to tell which
    benefit each one describes.
    """
    records = _base_records(
        candidate_of(RELEASE_BINDING, _ledger(2, prose=True), _help_draft())
    )
    authority = EffectiveAuthority(
        binding=RulesPackageBinding(
            package_uuid=uuid5(NAMESPACE_URL, "pkg-5c"),
            release_version="rel-5c",
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "proj-1"),
            override_set_uuid=uuid5(NAMESPACE_URL, "ovs-1"),
        ),
        records=tuple(records.values()),
        applied_overrides=(),
    )
    view = build_gamemaster_view(
        authority, {build_representation().prose_bindings[0].chunk_id: "x" * 30}
    )
    entries = view.components[0].governing_prose
    assert sorted(e.option_key for e in entries) == sorted(  # type: ignore[union-attr]
        [ABILITY_ARM, ATTACK_ARM]
    )
    assert all(e.text for e in entries)  # type: ignore[union-attr]

    # And the typed view, which hands a deterministic consumer the same
    # records: one path, two audiences, and the scope reaches both.
    typed = build_typed_view(authority)
    assert sorted(
        e.option_key  # type: ignore[union-attr]
        for e in typed.records[0].components[0].governing_prose
    ) == sorted([ABILITY_ARM, ATTACK_ARM])


def test_help_refuses_a_clause_bound_to_an_arm_it_does_not_state() -> None:
    """The valid sibling is one identifier away, and it is the test above."""
    findings = validate_representation(
        _help_draft(first="no-such-arm"), _ledger(2, prose=True), bound_corpus()
    )
    assert any("names no option of its component" in f for f in findings), findings


# ---------------------------------------------------------------------------
# Ready, pp186-187 — the whole action, composed
# ---------------------------------------------------------------------------
#
#   L2  "...lets you act by taking a Reaction before the start of your next turn"
#   L4  "Then, you choose the action you will take in response to that trigger,
#        or you choose to move up to your Speed in response to it."
#   L6  "you can either take your Reaction right after the trigger finishes or
#        ignore the trigger"
#   L7  "you cast it as normal (expending any resources used to cast it)"
#   L8  "To be readied, a spell must have a casting time of an action"
#   L9  "holding on to the spell's magic requires Concentration, which you can
#        maintain up to the start of your next turn"
#
# **L4 is an exhaustive actor choice, and both arms are authorable.** Two
# earlier readings said otherwise — that both arms are factless, and then that
# arm 1 designates rather than grants so no family reaches it. Both looked only
# at the *allowance* families, where `cost` names a slot the owning effect
# grants; typing arm 1 there would publish an Action grant beside L2's
# Reaction grant, which is why that route was refused and the refusal was
# right.
#
# It is not the only route. `ActionEconomyFact` states what a component's
# effect **consumes**, and the source says plainly what both arms consume:
# *"lets you act by taking a Reaction"* (L2) and *"you can either take your
# Reaction right after the trigger finishes"* (L6). Each arm therefore states
# one true typed fact — `ActionEconomyFact(REACTION)` — and arm 2 states the
# own-Speed allowance beside it. No grant is invented, and the family is not
# new: `ACTION_ECONOMY` predates schema 6, so L4's genuinely new dependencies
# were only ever F2 (the movement allowance) and F19 (option-grain prose).
#
# What the encoding costs, stated rather than left to be discovered: the
# Reaction consumption is **printed once and carried twice**, once per arm,
# because a component is a conjunction or a choice and never both — there is no
# place to state a cost the arms share. It is redundant, and it is true of each
# arm.
#
# What *which* action the subject chooses remains prose, now bound at option
# grain: one clause governs one arm and says nothing about its sibling.
#
# **This is the shape, on the fixture record.** Its spans are a synthetic
# partition of a 40-character leaf, and its provenance gives every fact a
# primary claim because nothing in the fixture says where anything is printed.
# `test_schema_6_ready_source_provenance` maps the same choice onto `Ready`'s
# real leaf ids and extents, where L4 splits once at its printed `or` and the
# shared Reaction is evidenced *contextually* on L2. Read that module for what
# the source supports; read this one for what the composition paths do.

RESPONSE_KEY = "ready-response"
CHOICE_KEY = "readied-choice"
SPELL_COMPONENT_KEY = "ready-a-spell"
ACTION_ARM = "take-the-chosen-action"
MOVE_ARM = "move-up-to-your-speed"

#: What taking the readied response spends, whichever arm is taken. Not a
#: grant: `ActionEconomyFact` is the consumption side of the same slot L2's
#: allowance establishes, which is the pairing the two families exist for.
READIED_REACTION = ActionEconomyFact(cost=ActionCost.REACTION)

#: Arm 1 typed as an *allowance* — the route two earlier readings tested and
#: rejected. Kept as a named value because the rejection is still correct and
#: worth pinning: it is structurally valid and states a grant the source does
#: not make.
_ARM_ONE_AS_A_GRANT = ActionAllowanceFact(
    count=1, per=AllowanceScope.OWNING_EFFECT, cost=ActionCost.ACTION
)

_READY_FACT_SPANS = _spans(9)
_READY_PROSE = _prose_extents(3)


def _ready_components() -> tuple[ComponentDraft, ...]:
    return (
        ComponentDraft(
            record_key=SPELL_KEY,
            semantic_key=RESPONSE_KEY,
            handling=ComponentHandling.STRUCTURED,
            facts=(CASES["L2"][1], CASES["L6"][1]),
        ),
        ComponentDraft(
            record_key=SPELL_KEY,
            semantic_key=CHOICE_KEY,
            handling=ComponentHandling.MIXED,
            irreducibility_reason_code="open_ended_effect",
            options=(
                ComponentOption(semantic_key=ACTION_ARM, facts=(READIED_REACTION,)),
                ComponentOption(
                    semantic_key=MOVE_ARM,
                    facts=(READIED_REACTION, CASES["L4"][1]),
                ),
            ),
        ),
        ComponentDraft(
            record_key=SPELL_KEY,
            semantic_key=SPELL_COMPONENT_KEY,
            handling=ComponentHandling.MIXED,
            irreducibility_reason_code="open_ended_effect",
            facts=(
                CASES["L7"][1],
                CASES["L8"][1],
                CASES["K3"][1],
                CASES["L9"][1],
            ),
        ),
    )


def _ready_draft(
    action_arm_prose: str = ACTION_ARM, move_arm_prose: str = MOVE_ARM
) -> object:
    response, choice, spell = _ready_components()
    spans = iter(_READY_FACT_SPANS)
    keyed: list[tuple[tuple[str, ...], str]] = [
        ((SPELL_KEY, RESPONSE_KEY, fact_key(fact)), next(spans))
        for fact in response.facts
    ]
    keyed += [
        ((SPELL_KEY, CHOICE_KEY, fact_key(fact), option.semantic_key), next(spans))
        for option in choice.options
        for fact in option.facts
    ]
    keyed += [
        ((SPELL_KEY, SPELL_COMPONENT_KEY, fact_key(fact)), next(spans))
        for fact in spell.facts
    ]
    return _composed(
        (response, choice, spell),
        (
            _prose(action_arm_prose, _READY_PROSE[0], CHOICE_KEY),
            _prose(move_arm_prose, _READY_PROSE[1], CHOICE_KEY),
            # L10's dissipation clause governs the spell component as a whole.
            _prose("", _READY_PROSE[2], SPELL_COMPONENT_KEY),
        ),
        tuple(keyed),
    )


def _ready_ledger() -> ClassificationLedger:
    return _ledger(9, prose=True, prose_parts=3)


def test_ready_composes_and_validates_as_printed() -> None:
    """The whole action, the choice included, passes the build contract."""
    assert (
        validate_representation(_ready_draft(), _ready_ledger(), bound_corpus()) == ()
    )


def test_the_readied_choice_is_an_exhaustive_actor_choice() -> None:
    """Two arms, each stating one true typed fact.

    ``option_set_violations`` is what decides authorability, so it is asked
    rather than asserted around: at least two options, each with at least one
    typed fact, and no two arms a consumer could not tell apart.
    """
    _, choice, _ = _ready_components()
    assert option_set_violations(choice.facts, choice.options, "ready/choice") == []
    assert [o.semantic_key for o in choice.options] == [ACTION_ARM, MOVE_ARM]


def test_both_arms_state_the_reaction_and_only_one_states_the_movement() -> None:
    """Exclusivity, cost and movement, as the source states them.

    Both arms spend the Reaction; only the second grants movement. An
    encoding that put the movement on the component would say it is available
    whichever arm is taken, and one that put the cost on only one arm would say
    the other is free.
    """
    records = _base_records(
        candidate_of(RELEASE_BINDING, _ready_ledger(), _ready_draft())
    )
    choice = next(
        c for c in records[SPELL_KEY].components if c.semantic_key == CHOICE_KEY
    )
    by_arm = {o.semantic_key: [f.fact for f in o.facts] for o in choice.options}
    assert by_arm[ACTION_ARM] == [READIED_REACTION]
    assert by_arm[MOVE_ARM] == [READIED_REACTION, CASES["L4"][1]]
    # The arms are the only place facts live here: a choice states no
    # conjunction of its own, which is what makes them mutually exclusive.
    assert choice.facts == ()
    assert all(f.span_ids for o in choice.options for f in o.facts)


def test_each_arm_s_clause_is_bound_to_that_arm() -> None:
    """The advance choice, at the grain where it is true.

    *Which* action the subject readies is open, so it stays prose — but it is
    arm 1's prose. A component-grain binding would say the clause governs the
    movement arm too, which is false about the arm it does not describe.
    """
    records = _base_records(
        candidate_of(RELEASE_BINDING, _ready_ledger(), _ready_draft())
    )
    choice = next(
        c for c in records[SPELL_KEY].components if c.semantic_key == CHOICE_KEY
    )
    assert sorted(
        e.option_key for e in choice.governing_prose  # type: ignore[union-attr]
    ) == sorted([ACTION_ARM, MOVE_ARM])
    assert choice.irreducibility_reason_code == "open_ended_effect"


def test_swapping_the_two_clauses_changes_the_effective_record() -> None:
    """The scope is authority, not decoration — keyed by extent so only it moves."""

    def governed(draft: object) -> dict[tuple[int, int], str]:
        records = _base_records(candidate_of(RELEASE_BINDING, _ready_ledger(), draft))
        choice = next(
            c for c in records[SPELL_KEY].components if c.semantic_key == CHOICE_KEY
        )
        return {
            (e.char_start, e.char_end): e.option_key  # type: ignore[union-attr]
            for e in choice.governing_prose
        }

    printed = governed(_ready_draft())
    swapped = governed(
        _ready_draft(action_arm_prose=MOVE_ARM, move_arm_prose=ACTION_ARM)
    )
    assert set(printed) == set(swapped)
    assert printed != swapped


def test_the_choice_reaches_the_gamemaster_with_both_arms_and_both_clauses() -> None:
    """The view a GameMaster adjudicates from carries the whole alternation."""
    records = _base_records(
        candidate_of(RELEASE_BINDING, _ready_ledger(), _ready_draft())
    )
    authority = EffectiveAuthority(
        binding=RulesPackageBinding(
            package_uuid=uuid5(NAMESPACE_URL, "pkg-5c"),
            release_version="rel-5c",
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "proj-1"),
            override_set_uuid=uuid5(NAMESPACE_URL, "ovs-1"),
        ),
        records=tuple(records.values()),
        applied_overrides=(),
    )
    view = build_gamemaster_view(
        authority, {build_representation().prose_bindings[0].chunk_id: "x" * 30}
    )
    choice = next(c for c in view.components if c.component_key == CHOICE_KEY)
    assert [o.semantic_key for o in choice.options] == [ACTION_ARM, MOVE_ARM]
    assert all(e.text for e in choice.governing_prose)
    assert sorted(
        e.option_key for e in choice.governing_prose  # type: ignore[union-attr]
    ) == sorted([ACTION_ARM, MOVE_ARM])

    typed = build_typed_view(authority)
    typed_choice = next(
        c for r in typed.records for c in r.components if c.semantic_key == CHOICE_KEY
    )
    assert [o.semantic_key for o in typed_choice.options] == [ACTION_ARM, MOVE_ARM]


def test_a_readied_spell_s_requirements_do_not_reach_the_movement_arm() -> None:
    """The scope that makes Ready three components.

    *"When you Ready a spell"* qualifies one way of readying, not the action.
    Stated beside the arms, the expenditure, the casting-time eligibility and
    the Concentration duty would read as requirements of the choice itself — so
    a subject who readied a **move** would appear to expend casting resources.
    """
    records = _base_records(
        candidate_of(RELEASE_BINDING, _ready_ledger(), _ready_draft())
    )
    by_key = {c.semantic_key: c for c in records[SPELL_KEY].components}
    spell_facts = {e.fact for e in by_key[SPELL_COMPONENT_KEY].facts}
    assert spell_facts == {
        CASES["L7"][1],
        CASES["L8"][1],
        CASES["K3"][1],
        CASES["L9"][1],
    }
    choice = by_key[CHOICE_KEY]
    assert not spell_facts & {f.fact for o in choice.options for f in o.facts}
    assert not spell_facts & {e.fact for e in by_key[RESPONSE_KEY].facts}
    assert CASES["L8"][1].subject is EligibilitySubject.SPELL


def test_ready_publishes_every_clause_it_states() -> None:
    """Each fact reaches a consumer under its own key and its own provenance."""
    records = _base_records(
        candidate_of(RELEASE_BINDING, _ready_ledger(), _ready_draft())
    )
    published = [
        entry
        for component in records[SPELL_KEY].components
        for entry in (
            *component.facts,
            *(f for o in component.options for f in o.facts),
        )
    ]
    assert {entry.fact for entry in published} == {
        CASES[k][1] for k in ("L2", "L4", "L6", "L7", "L8", "L9", "K3")
    } | {READIED_REACTION}
    # The shared consumption appears once per arm and the two are distinct
    # targets, which is what keeps a repeated fact from collapsing to one id.
    assert len({entry.fact_key for entry in published}) == len(published) - 1
    assert all(entry.span_ids for entry in published)


def test_arm_one_still_may_not_be_typed_as_a_grant() -> None:
    """The route that was rejected stays rejected, and for the stated reason.

    Nothing structural refuses it — the fact is valid and the option set it
    forms is admitted — so the reason is a claim about the record: `Ready`
    grants one slot, L2 states it, and an Action allowance beside it would be a
    second grant the source never makes. Pinned because no component-scoped
    rule can see it: L2 and the arms live in different components.
    """
    assert list(fact_invariant_violations(_ARM_ONE_AS_A_GRANT)) == []
    as_a_grant = (
        ComponentOption(semantic_key=ACTION_ARM, facts=(_ARM_ONE_AS_A_GRANT,)),
        ComponentOption(semantic_key=MOVE_ARM, facts=(CASES["L4"][1],)),
    )
    assert option_set_violations((), as_a_grant, "ready/choice") == []
    assert CASES["L2"][1].cost is ActionCost.REACTION
    assert _ARM_ONE_AS_A_GRANT.cost is ActionCost.ACTION
    # The encoding this module uses states a consumption instead, which is the
    # one difference that matters.
    assert isinstance(READIED_REACTION, ActionEconomyFact)


# ---------------------------------------------------------------------------
# A disjunction is not a place to hide a condition from its scope rule
# ---------------------------------------------------------------------------

_ON_A_SUCCESS = Applicability(
    kind=ApplicabilityKind.ROLL_OUTCOME, outcome=AutomaticOutcome.SUCCESS
)
_PRONE = Applicability(
    kind=ApplicabilityKind.CONDITION_STATE, condition=ConditionKind.PRONE
)
_TWO_SIZES_SMALLER = Applicability(
    kind=ApplicabilityKind.SIZE_COMPARISON,
    any_of=(
        SizeComparison(
            measured=ParticipantRole.SUBJECT,
            reference=ParticipantRole.COUNTERPART,
            relation=SizeRelation.SMALLER,
            at_least=2,
        ),
    ),
)
_DRAGGED = MovementTransportFact(
    carrier=ParticipantRole.COUNTERPART,
    carried=ParticipantRole.SUBJECT,
    kind=TransportKind.PERMITTED,
)


def _wrapped(inner: Applicability) -> Applicability:
    return Applicability(
        kind=ApplicabilityKind.ANY_OF,
        any_of_terms=_canonical(inner, _PRONE),
    )


@pytest.mark.parametrize("held", [_ON_A_SUCCESS, _wrapped(_ON_A_SUCCESS)])
@pytest.mark.parametrize("scope", ["component", "option", "qualifier"])
def test_a_roll_outcome_answers_to_a_roll_in_every_scope_and_wrapping(
    held: Applicability, scope: str
) -> None:
    """One rule, four scopes, and a disjunction changes none of it.

    ``ANY_OF`` states no operand of its own — each *term* is a condition — so a
    scope rule that read only the outer value saw a disjunction as stating
    nothing at all. Wrapping is then a way to make a refused condition legal,
    which is strictly worse than the refusal it evades: any term suffices, so
    the outcome still governs.
    """
    facts, options, applies_when, qualifiers = (), (), None, ()
    if scope == "component":
        applies_when = held
    elif scope == "option":
        options = (ComponentOption(semantic_key="arm", applies_when=held),)
    else:
        qualifiers = (
            FactQualifier(fact_key=fact_key(CASES["L2"][1]), applies_when=held),
        )
    findings = component_roll_outcome_violations(
        facts, options, applies_when, "t", qualifiers
    )
    assert any("outcome of nothing" in f for f in findings), findings


def test_a_roll_outcome_in_a_disjunction_is_admitted_where_a_roll_is_stated() -> None:
    """The valid sibling: the same disjunction, one roll established.

    Without this, the assertions above would pass just as well against a rule
    that refused every disjunction.
    """
    assert (
        component_roll_outcome_violations(
            (CASES["I6"][1],), (), _wrapped(_ON_A_SUCCESS), "t"
        )
        == []
    )


@pytest.mark.parametrize("held", [_TWO_SIZES_SMALLER, _wrapped(_TWO_SIZES_SMALLER)])
def test_a_counterpart_comparison_needs_establishment_however_it_is_held(
    held: Applicability,
) -> None:
    """The same defect family, one rule over: a size comparison in a term."""
    findings = component_participant_violations((), (), held, "t")
    assert any("establishes one" in f for f in findings), findings


def test_a_counterpart_comparison_in_a_disjunction_is_admitted_when_established() -> (
    None
):
    """The valid sibling: Grappled's shape, with the transport that states it."""
    assert (
        component_participant_violations(
            (_DRAGGED,), (), _wrapped(_TWO_SIZES_SMALLER), "t"
        )
        == []
    )


@pytest.mark.parametrize("terms", [None, 7, "prone"], ids=["null", "int", "str"])
@pytest.mark.parametrize("scope", ["component", "option", "qualifier"])
def test_a_malformed_disjunction_container_is_reported_not_raised(
    terms: object, scope: str
) -> None:
    """A collecting validator may not lose its report to a ``TypeError``.

    ``any_of_terms`` is a declared field, not a validated one, so a draft can
    hold ``None`` or an integer there. ``applicability_violations`` already
    names it as the malformed container it is — and the scope rules, reading
    the same value one step later, iterated it and raised out of the middle of
    the collection, taking that finding and every other one with them.

    The string case is here because it does not raise: iterating it yields
    characters, each declined for the right reason by accident, so the rule
    would have looked correct while checking nothing.
    """
    held = Applicability(kind=ApplicabilityKind.ANY_OF, any_of_terms=terms)
    assert applicability_violations(held), "the intrinsic finding is the premise"

    component = ComponentDraft(
        record_key=SPELL_KEY,
        semantic_key=OPEN_ENDED_KEY,
        handling=ComponentHandling.MIXED,
        irreducibility_reason_code="open_ended_effect",
        facts=(CASES["L2"][1],),
    )
    if scope == "component":
        component = replace(component, applies_when=held)
    elif scope == "option":
        component = replace(
            component,
            facts=(),
            options=(
                ComponentOption(
                    semantic_key="arm-a",
                    facts=(CASES["L2"][1],),
                    applies_when=held,
                ),
                ComponentOption(semantic_key="arm-b", facts=(CASES["L6"][1],)),
            ),
        )
    else:
        component = replace(
            component,
            fact_qualifiers=(
                FactQualifier(fact_key=fact_key(CASES["L2"][1]), applies_when=held),
            ),
        )
    facts = component.facts or tuple(
        f for option in component.options for f in option.facts
    )
    draft = _composed(
        component,
        (_prose(""),),
        tuple(
            ((SPELL_KEY, OPEN_ENDED_KEY, *_scope_key(component, fact)), span)
            for fact, span in zip(facts, _spans(len(facts)), strict=True)
        ),
    )
    findings = validate_representation(draft, _ledger(len(facts)), bound_corpus())
    assert any("any_of_terms must be tuple" in f for f in findings), findings


def _scope_key(component: ComponentDraft, fact: object) -> tuple[str, ...]:
    """A fact's coordinate tail — its key, plus its option when it has one."""
    for option in component.options:
        if fact in option.facts:
            return (fact_key(fact), option.semantic_key)
    return (fact_key(fact),)


@pytest.mark.parametrize("scope", ["component", "option", "qualifier"])
def test_a_well_formed_disjunction_is_still_admitted_in_every_scope(
    scope: str,
) -> None:
    """The valid sibling, and the reason the guard is a check and not a refusal.

    The same three scopes, carrying a disjunction whose prerequisite holds:
    Hide's, which states no roll outcome and names no counterpart, so nothing
    in either scope rule has anything to object to.
    """
    component = ComponentDraft(
        record_key=SPELL_KEY,
        semantic_key=OPEN_ENDED_KEY,
        handling=ComponentHandling.MIXED,
        irreducibility_reason_code="open_ended_effect",
        facts=(CASES["L2"][1],),
    )
    if scope == "component":
        component = replace(component, applies_when=HIDE_PREREQUISITE)
    elif scope == "option":
        component = replace(
            component,
            facts=(),
            options=(
                ComponentOption(
                    semantic_key="arm-a",
                    facts=(CASES["L2"][1],),
                    applies_when=HIDE_PREREQUISITE,
                ),
                ComponentOption(semantic_key="arm-b", facts=(CASES["L6"][1],)),
            ),
        )
    else:
        component = replace(
            component,
            fact_qualifiers=(
                FactQualifier(
                    fact_key=fact_key(CASES["L2"][1]),
                    applies_when=HIDE_PREREQUISITE,
                ),
            ),
        )
    facts = component.facts or tuple(
        f for option in component.options for f in option.facts
    )
    # A qualifier is its own authority and carries its own edge, so the valid
    # sibling states one. The malformed cases above assert on a finding rather
    # than on emptiness, so they need no such claim.
    needed = len(facts) + len(component.fact_qualifiers)
    spans = _spans(needed)
    claims = tuple(
        ((SPELL_KEY, OPEN_ENDED_KEY, *_scope_key(component, fact)), span)
        for fact, span in zip(facts, spans, strict=False)
    )
    draft = _composed(component, (_prose(""),), claims)
    if component.fact_qualifiers:
        qualifier = component.fact_qualifiers[0]
        draft = replace(
            draft,  # type: ignore[type-var]
            provenance=(
                *draft.provenance,  # type: ignore[attr-defined]
                ProvenanceClaim(
                    ProvenanceTargetKind.FACT_QUALIFIER,
                    (
                        SPELL_KEY,
                        OPEN_ENDED_KEY,
                        qualifier.fact_key,
                        qualifier.option_key,
                    ),
                    spans[-1],
                    ProvenanceRole.PRIMARY,
                ),
            ),
        )
    assert validate_representation(draft, _ledger(needed), bound_corpus()) == ()


def test_a_composed_component_refuses_a_wrapped_outcome_through_validation() -> None:
    """End to end, through the entry point the build actually calls."""
    component = replace(
        ComponentDraft(
            record_key=SPELL_KEY,
            semantic_key=OPEN_ENDED_KEY,
            handling=ComponentHandling.MIXED,
            irreducibility_reason_code="open_ended_effect",
            facts=(CASES["L2"][1],),
        ),
        applies_when=_wrapped(_ON_A_SUCCESS),
    )
    draft = _composed(
        component,
        (_prose(""),),
        (((SPELL_KEY, OPEN_ENDED_KEY, fact_key(CASES["L2"][1])), _spans(1)[0]),),
    )
    findings = validate_representation(draft, _ledger(1), bound_corpus())
    assert any("outcome of nothing" in f for f in findings), findings


# ---------------------------------------------------------------------------
# Every applicability ingress refuses depth before it recurses
# ---------------------------------------------------------------------------

_FLAT_TERM: dict[str, object] = {
    "kind": "condition_state",
    "negated": False,
    "quantity": None,
    "comparison": None,
    "value": None,
    "any_of": [],
    "trigger": None,
    "phase": None,
    "condition": "prone",
}


def _nested(depth: int) -> dict[str, object]:
    payload: dict[str, object] = dict(_FLAT_TERM)
    for _ in range(depth):
        payload = {
            **{k: v for k, v in _FLAT_TERM.items() if k != "condition"},
            "kind": "any_of",
            "any_of_terms": [payload],
        }
    return payload


def _removal_payload(until: object) -> dict[str, object]:
    return {
        "family": "condition_removal_restriction",
        "condition": "exhaustion",
        "until": until,
        "cause_scoped": True,
    }


def test_a_fact_held_applicability_refuses_depth_before_it_recurses() -> None:
    """``ConditionRemovalRestrictionFact.until`` is an ingress like any other.

    It is reached through ``fact_from_payload``, so it is also the override
    seam for this family. A 600-level payload is JSON-decodable and was
    rebuilt term by term until the interpreter stopped it — a ``RecursionError``
    out of the one layer whose contract is to report malformed input.
    """
    with pytest.raises(MalformedFactPayloadError) as raised:
        fact_from_payload(_removal_payload(_nested(600)))
    assert "terms of its own" in str(raised.value), raised.value


def test_a_fact_held_disjunction_of_flat_terms_is_still_admitted() -> None:
    """The valid sibling: depth 1 is the contract, and it still builds."""
    terms = _canonical(_PRONE, _TWO_SIZES_SMALLER)
    disjunction = Applicability(kind=ApplicabilityKind.ANY_OF, any_of_terms=terms)
    from afterworlds.ingestion.mechanical.projection import applicability_payload

    rebuilt = fact_from_payload(_removal_payload(applicability_payload(disjunction)))
    assert rebuilt.until == disjunction  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# A schema-6 null is not a null a schema-5 declaration can state
# ---------------------------------------------------------------------------


def _artifact_with_ability(ability: object, tmp_path: object, name: str) -> Path:
    """The frozen specimen carrying one ability check, declared at schema 5."""
    raw = json.loads(LEGACY_PATH.read_text(encoding="utf-8"))
    component = raw["representation"]["components"][0]
    component["facts"] = [
        {
            "family": "ability_check",
            "ability": ability,
            "dc_kind": "fixed",
            "dc_value": 10,
            "skill": None,
            "alternatives": [],
            "context": "ability_check",
        }
    ]
    # The accepted obligation states which families the record publishes, and
    # the loader reconciles the two. Moving the content without moving the
    # obligation would fail on *that* mismatch, and the test would then pass
    # for a reason unrelated to version legality.
    for obligation in raw["obligations"]:
        if obligation["record_key"] == component["record_key"]:
            obligation["structured_fact_families"] = sorted(
                {*obligation["structured_fact_families"], "ability_check"}
            )
    raw["representation_schema"] = {"version": SCHEMA_5_VERSION, "hash": SCHEMA_5_HASH}
    raw["acceptance"]["schema_anchors"] = [
        {
            "batch_id": batch["batch_id"],
            "proposal_identity": batch["proposal_identity"],
            "schema_version": SCHEMA_5_VERSION,
            "schema_hash": SCHEMA_5_HASH,
        }
        for batch in raw["acceptance"]["batches"]
    ]
    path = Path(str(tmp_path)) / name
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def test_a_schema_5_artifact_may_not_state_an_ability_less_check(
    tmp_path: object,
) -> None:
    """The declared contract is enforced, not merely recorded.

    ``ability`` is a schema-1 key, so it is emitted under every contract and the
    payload is *complete* either way: only the value is one schema 5 never
    admitted. Nothing downstream of the key set has any reason to look twice,
    which is exactly why version legality has to say it.
    """
    path = _artifact_with_ability(None, tmp_path, "null-ability.json")
    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(path)
    assert "ability" in str(raised.value), raised.value


def test_a_schema_5_artifact_stating_an_ability_still_loads(
    tmp_path: object,
) -> None:
    """The valid sibling, and the shape every accepted ability check has."""
    path = _artifact_with_ability("strength", tmp_path, "stated-ability.json")
    loaded = load_accepted_inputs(path)
    assert loaded.oracle.representation.components[0].facts


def _ability_check_draft(ability: object) -> object:
    """The fixture draft holding one ability check with *ability*."""
    component = ComponentDraft(
        record_key=SPELL_KEY,
        semantic_key=OPEN_ENDED_KEY,
        handling=ComponentHandling.MIXED,
        irreducibility_reason_code="open_ended_effect",
        facts=(
            AbilityCheckFact(
                ability=ability,  # type: ignore[arg-type]
                dc_kind=DcKind.FIXED,
                dc_value=15,
                context=RollContext.ABILITY_CHECK,
            ),
        ),
    )
    return _composed(
        component,
        (_prose(""),),
        (((SPELL_KEY, OPEN_ENDED_KEY, fact_key(component.facts[0])), _spans(1)[0]),),
    )


@pytest.mark.parametrize(
    ("declared", "admitted"),
    [
        ((SCHEMA_5_VERSION, SCHEMA_5_HASH), False),
        ((REPRESENTATION_SCHEMA_VERSION, representation_schema_hash()), True),
    ],
    ids=["schema-5", "schema-6"],
)
def test_the_shared_admission_seam_refuses_an_ability_less_check_before_schema_6(
    declared: tuple[str, str], admitted: bool
) -> None:
    """One function guards every seam that admits authority, so assert on it.

    ``schema_binding_violations`` is what ``load_accepted_inputs``,
    ``verify_lift`` and ``accept_proposal`` all run — a restamped prior reaches
    acceptance through the last two, never through the loader, so asserting
    only the loader would leave the attack this row exists to stop untested.
    """
    findings = schema_binding_violations(_ability_check_draft(None), declared)
    assert (findings == []) is admitted, findings


def test_the_shared_admission_seam_still_admits_a_stated_ability_at_schema_5() -> None:
    """The valid sibling: a row here refuses a value, never a shape."""
    assert (
        schema_binding_violations(
            _ability_check_draft(AbilityScore.STRENGTH),
            (SCHEMA_5_VERSION, SCHEMA_5_HASH),
        )
        == []
    )
