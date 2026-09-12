"""Speed, end to end, under representation schema 11 — CRD Issue 5d (#137).

The batch is ``speed-1`` and the source population is the two defining sites the
bound 5.2.1 release prints: *Rules Glossary > Rules Definitions > Speed* (p188)
and *Playing the Game > Combat > Movement and Position* (p14). Sixteen leaves,
thirty-six clauses, reviewed and committed as
``.claude/review-notes/issue-5d-speed-1-source-manifest.json``, and read out of
that file here rather than retyped.

**What schema 11 adds, and why it had to.** Schema 10 could already state that a
creature *may* move by a mode (``MovementPermissionFact``) and that an allowance
exists (``MovementAllowanceFact``), and could not state what a Speed *is*, that
spending draws an allowance down, which speed is used when several exist, what
switching costs and when it is forbidden, how a change to Speed reaches the
special speeds, that a special speed is named in an open list, or that a mode
may compose with regular movement or constitute the whole move. Seven families
over eleven new closed vocabularies — plus one member, ``jump``, widening the
``MovementMode`` vocabulary schema 8 minted — state all of it, and one
registered crossing carries the frozen six-batch prior across.

**The allowance is reused, not replaced.** ``MovementAllowanceFact`` already
carries *"a distance equal to your Speed or less"*: the basis is
``own_speed`` and schema 11 adds only the optional ``window`` that says the
allowance is per turn. *"Or you can decide not to move"* is the bottom of that
same ceiling, not a second rule — ``Ready`` already represents *"up to"* — so no
zero-movement fact is invented for it. Depletion is a separate family because a
ceiling and the drawing-down of a ceiling are different statements: conflating
them would make an unspent allowance indistinguishable from an exhausted one.

**Nine outgoing references, and why the four special speeds are among them.**
Five come from the *See also* leaf. Four more come from *"each of which is
defined in this glossary"* — an explicit pointer, printed by the source, at
``Burrow Speed``, ``Climb Speed``, ``Fly Speed`` and ``Swim Speed``. ``Fly
Speed`` is printed across a leaf boundary and therefore carries two provenance
claims, one per printed part. All nine dangle: none of those entries is in this
batch, and inventing a record to close one would publish a definition no clause
here states.

**What this module does not claim.** It computes no distance, sums nothing,
halves nothing and moves no creature. Every gap is a named closed member; the
propagation examples (*reduced to 0*, *halved*) are carried as supporting
authority bounding the rule they illustrate, never as arithmetic. Grid rules,
the neighbouring glossary entries and the special-speed definitions themselves
stay outside this batch and remain accountable for later representation.
"""

from __future__ import annotations

import json
import pathlib
from itertools import groupby
from uuid import NAMESPACE_URL, uuid5

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.bound_corpus import BoundCorpusSnapshot
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.oracle import (
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    oracle_identity,
)
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import (
    UnsupportedSchemaVersionError,
    identify_projection,
    representation_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    RECORD_OWNED_REFERENCE,
    REPRESENTATION_SCHEMA_VERSION,
    ComponentDraft,
    ComponentHandling,
    DistanceUnit,
    FactFamily,
    MalformedFactPayloadError,
    MechanicalFact,
    MovementAllowanceBasis,
    MovementAllowanceFact,
    MovementComposition,
    MovementCompositionFact,
    MovementDepletionFact,
    MovementDepletionResolution,
    MovementDepletionTerminator,
    MovementMode,
    MovementPermissionFact,
    MovementWindow,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RepresentationDraft,
    SpecialSpeedFact,
    SpecialSpeedListing,
    SpeedChangePropagationFact,
    SpeedDefinitionFact,
    SpeedPropagationDuration,
    SpeedPropagationMagnitude,
    SpeedPropagationScope,
    SpeedSelection,
    SpeedSelectionFact,
    SpeedSwitchAccounting,
    SpeedSwitchLimitFact,
    SpeedSwitchOutcome,
    UnknownFactFamilyError,
    component_target_key,
    declared_meaning_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
    fact_target_key,
    introduction_manifest,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_8_VERSION,
    SCHEMA_10_HASH,
    SCHEMA_10_VERSION,
    SCHEMA_11_HASH,
    SCHEMA_11_VERSION,
    lift_accepted_inputs,
    lift_path,
)
from afterworlds.ingestion.mechanical.validation import validate_representation
from afterworlds.services.rules_authority.application import (
    EffectiveAuthority,
    _base_records,
)
from afterworlds.services.rules_authority.binding import RulesPackageBinding
from afterworlds.services.rules_authority.views import (
    build_gamemaster_view,
    build_typed_view,
)
from tests.ingestion.mechanical.conftest import (
    NOW,
    RELEASE_BINDING,
    bound_corpus,
    build_ledger,
    candidate_of,
    coverage,
)
from tests.ingestion.mechanical.test_speed_1_frozen_prior import (
    UNRESOLVED_TARGETS,
)

# ---------------------------------------------------------------------------
# The reviewed inventory, read rather than retyped
# ---------------------------------------------------------------------------

#: The committed discovery manifest. Reading the clauses out of it is what ties
#: this module to the inventory that passed independent review: the leaf ids,
#: the half-open char ranges and the clause text are all the source's, and a
#: clause that moved would change the assertions below rather than silently
#: become whatever this module happened to type.
MANIFEST_PATH = (
    pathlib.Path(__file__).resolve().parents[3]
    / ".claude"
    / "review-notes"
    / "issue-5d-speed-1-source-manifest.json"
)
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

#: ``leaf_id -> printed leaf text``, and one chunk per leaf covering it whole,
#: so chunk offsets are leaf offsets and a chunk-locality finding means what it
#: says.
LEAVES: dict[str, str] = {
    leaf["leaf_id"]: leaf["content"]
    for site in MANIFEST["source_sites"]
    for leaf in site["leaves"]
}
CHUNKS = {leaf_id: f"chunk-{leaf_id}" for leaf_id in LEAVES}

#: ``clause_id -> the manifest's clause row``, keyed by the reviewed clause id.
CLAUSE = {clause["clause_id"]: clause for clause in MANIFEST["clauses"]}

SCOPE = "srd-5.2.1/rules-glossary"

#: The one record this batch defines. Accepted authority already cites it by
#: name: ``action.dash`` carries a reference at ``glossary.speed`` that the
#: frozen prior records as unresolved, and this batch is what closes it.
SPEED = "glossary.speed"


def _leaf(clause_id: str) -> str:
    return str(CLAUSE[clause_id]["leaf_id"])


def _extent(clause_id: str) -> tuple[int, int]:
    row = CLAUSE[clause_id]
    return int(row["char_start"]), int(row["char_end"])


def _span_id(clause_id: str) -> str:
    return derive_span_id(_leaf(clause_id), *_extent(clause_id))


# ---------------------------------------------------------------------------
# The sixteen substantive clauses, as nine components and seventeen facts
# ---------------------------------------------------------------------------
#
# One component per rule the source states about Speed, named for that rule.
# Three of them hold several facts that one sentence states together — the four
# special speeds it lists, the four modes it names, the two ways a mode may
# compose with regular movement. For those the sentence claims the *component*,
# because a span may carry only one PRIMARY owner and the sentence is about the
# whole group rather than about any one member of it; each fact then carries the
# same span at CONTEXTUAL. That is the shape ``action.attack``'s
# ``attack_equipment_change`` already uses in accepted authority.

DEFINITION = "speed_definition"
ALLOWANCE = "movement_allowance"
DEPLETION = "movement_depletion"
SELECTION = "speed_selection"
SWITCH = "speed_switch_limit"
PROPAGATION = "speed_change_propagation"
SPECIAL = "special_speeds"
MODES = "movement_modes"
COMPOSING = "movement_composition"

COMPONENTS = (
    DEFINITION,
    ALLOWANCE,
    DEPLETION,
    SELECTION,
    SWITCH,
    PROPAGATION,
    SPECIAL,
    MODES,
    COMPOSING,
)

LISTED = SpecialSpeedListing.NAMED_IN_A_NON_EXHAUSTIVE_LIST

#: ``(component, fact, clause ids)`` — every fact, with the clauses that
#: ``PRIMARY``-claim it. An empty tuple means the sentence claims the component
#: instead, and the fact's own citation of it is in :data:`FACT_DETAIL`.
COMPOSITION: tuple[tuple[str, MechanicalFact, tuple[str, ...]], ...] = (
    # G1. "A creature has a Speed, which is the distance in feet the creature
    # can cover when it moves on its turn." The unit and the window are the
    # whole of what the definition states; no number is printed, so none is
    # represented.
    (
        DEFINITION,
        SpeedDefinitionFact(unit=DistanceUnit.FOOT, window=MovementWindow.OWN_TURN),
        ("glossary/1/1",),
    ),
    # G2. "On your turn, you can move a distance equal to your Speed or less."
    # + "Or you can decide not to move." One ceiling, stated across a leaf
    # boundary and then restated at its floor. ``MovementAllowanceFact`` already
    # carries the basis; schema 11 adds the per-turn window.
    (
        ALLOWANCE,
        MovementAllowanceFact(
            basis=MovementAllowanceBasis.OWN_SPEED, window=MovementWindow.OWN_TURN
        ),
        ("combat/1/0", "combat/2/0", "combat/2/1"),
    ),
    # G3. "However you're moving with your Speed, you deduct the distance of
    # each part of your move from it until it is used up or until you are done
    # moving, whichever comes first."
    (
        DEPLETION,
        MovementDepletionFact(
            depletes=MovementAllowanceBasis.OWN_SPEED,
            until=(
                MovementDepletionTerminator.ALLOWANCE_USED_UP,
                MovementDepletionTerminator.DONE_MOVING,
            ),
            resolution=MovementDepletionResolution.WHICHEVER_COMES_FIRST,
        ),
        ("combat/3/2",),
    ),
    # G4a. "If you have more than one speed, choose which one to use when you
    # move;"
    (
        SELECTION,
        SpeedSelectionFact(permits=SpeedSelection.CHOOSE_BEFORE_MOVING),
        ("glossary/7/1",),
    ),
    # G4b. "you can switch between the speeds during your move."
    (
        SELECTION,
        SpeedSelectionFact(permits=SpeedSelection.SWITCH_DURING_MOVE),
        ("glossary/7/2",),
    ),
    # G4c. "Whenever you switch, subtract the distance already moved from the
    # new speed." + "The result determines how much farther you can move." +
    # "If the result is 0 or less, you can't use the new speed during the
    # current move." One rule: the accounting and what its nonpositive result
    # prohibits. Nothing is subtracted here.
    (
        SWITCH,
        SpeedSwitchLimitFact(
            accounting=SpeedSwitchAccounting.SUBTRACT_DISTANCE_ALREADY_MOVED,
            when_nonpositive=SpeedSwitchOutcome.FORBIDS_USING_THE_NEW_SPEED,
        ),
        ("glossary/7/3", "glossary/7/4", "glossary/7/5"),
    ),
    # G5. "If an effect increases or decreases your Speed for a time, any
    # special speed you have increases or decreases by an equal amount for the
    # same duration."
    (
        PROPAGATION,
        SpeedChangePropagationFact(
            to=SpeedPropagationScope.EVERY_SPECIAL_SPEED,
            magnitude=SpeedPropagationMagnitude.EQUAL_AMOUNT,
            duration=SpeedPropagationDuration.SAME_DURATION,
        ),
        ("glossary/9/0",),
    ),
    # G6a. "Some creatures have special speeds, such as a Burrow Speed, Climb
    # Speed, Fly Speed, or Swim Speed, each of which is defined in this
    # glossary." Four named members of an open list; "such as" stays open
    # because ``listing`` says the list is non-exhaustive rather than the
    # vocabulary being closed to these four.
    (SPECIAL, SpecialSpeedFact(mode=MovementMode.BURROW, listing=LISTED), ()),
    (SPECIAL, SpecialSpeedFact(mode=MovementMode.CLIMB, listing=LISTED), ()),
    (SPECIAL, SpecialSpeedFact(mode=MovementMode.FLY, listing=LISTED), ()),
    (SPECIAL, SpecialSpeedFact(mode=MovementMode.SWIM, listing=LISTED), ()),
    # G6b. "Your movement can include climbing, crawling, jumping, and swimming
    # (each explained in "Rules Glossary")." Four modes in one sentence, on the
    # family schema 8 already minted for exactly this.
    (MODES, MovementPermissionFact(mode=MovementMode.CLIMB), ()),
    (MODES, MovementPermissionFact(mode=MovementMode.CRAWL), ()),
    (MODES, MovementPermissionFact(mode=MovementMode.JUMP), ()),
    (MODES, MovementPermissionFact(mode=MovementMode.SWIM), ()),
    # G6c. "These different modes of movement can be combined with your regular
    # movement, or they can constitute your entire move."
    (
        COMPOSING,
        MovementCompositionFact(
            composes=MovementComposition.COMBINED_WITH_REGULAR_MOVEMENT
        ),
        (),
    ),
    (COMPOSING, MovementCompositionFact(composes=MovementComposition.ENTIRE_MOVE), ()),
)

#: Substantive clauses that claim a *component* rather than a fact. Each states
#: something about a whole group of facts, and a span admits one PRIMARY owner.
COMPONENT_PRIMARY: tuple[tuple[str, str], ...] = (
    (SPECIAL, "glossary/5/0"),
    (SPECIAL, "glossary/6/0"),
    (SPECIAL, "glossary/7/0"),
    (MODES, "combat/3/0"),
    (COMPOSING, "combat/3/1"),
)

#: Every substantive clause id, derived from the composition rather than listed
#: beside it, so a clause represented twice or not at all is visible.
SUBSTANTIVE_CLAUSES = tuple(
    clause for _, _, clauses in COMPOSITION for clause in clauses
) + tuple(clause for _, clause in COMPONENT_PRIMARY)


# ---------------------------------------------------------------------------
# The nine outgoing references
# ---------------------------------------------------------------------------

#: ``(source text, target record, clause ids)``. Five come from the *See also*
#: leaf. Four more come from *"each of which is defined in this glossary"*,
#: which is an explicit printed pointer at the four entries the sentence names;
#: ``Fly Speed`` is printed across a leaf boundary and so cites two clauses.
#:
#: ``action.dash``'s bare *"such as a Fly Speed or Swim Speed"* is not this
#: pointer and its accepted artifact is unchanged by any of it.
CITATIONS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Climbing", "glossary.climbing", ("glossary/3/0",)),
    ("Crawling", "glossary.crawling", ("glossary/3/1",)),
    ("Flying", "glossary.flying", ("glossary/3/2",)),
    ("Jumping", "glossary.jumping", ("glossary/3/3",)),
    ("Swimming", "glossary.swimming", ("glossary/3/4",)),
    ("Burrow Speed", "glossary.burrow_speed", ("glossary/5/0",)),
    ("Climb Speed", "glossary.climb_speed", ("glossary/5/0",)),
    ("Fly Speed", "glossary.fly_speed", ("glossary/5/0", "glossary/6/0")),
    ("Swim Speed", "glossary.swim_speed", ("glossary/6/0",)),
)

REFERENCES = tuple(
    ReferenceDraft(
        from_record_key=SPEED,
        from_component_key=RECORD_OWNED_REFERENCE,
        source_text=text,
        scope_key=SCOPE,
        target_record_key=target,
    )
    for text, target, _ in CITATIONS
)


# ---------------------------------------------------------------------------
# The twenty supporting clauses, each linked to what it actually supports
# ---------------------------------------------------------------------------

#: Supporting clauses the *record* carries: the three headings at the glossary
#: site, the combat heading, the possession clause, the *See also* label, the
#: two sourcing sentences, and the two chapter navigations.
#:
#: The navigations emit nothing. *"and "Playing the Game" ("Combat")."* names a
#: chapter — for which there is no record — and names this record's own second
#: site; *"See "Rules Glossary" for more about Speed as well as about special
#: speeds, such as a Climb Speed, Fly Speed, or Swim Speed."* points back at
#: this very entry and re-names three targets the glossary site already cites.
#: Record-owned supporting authority is the honest scope for both.
RECORD_CONTEXT: tuple[str, ...] = (
    "glossary/0/0",
    "glossary/1/0",
    "glossary/2/0",
    "glossary/3/5",
    "glossary/4/0",
    "glossary/8/0",
    "combat/0/0",
    "combat/3/3",
    "combat/3/4",
    "combat/3/5",
)

#: Supporting clauses a *fact* carries, because they bound that fact and state
#: no rule of their own. The switch example works one case of the switch limit;
#: the four propagation clauses are the printed zero and halving illustrations,
#: the second of them spanning three leaves. Represented as evidence for the
#: rule rather than as arithmetic: no number here becomes a value.
FACT_CONTEXT: tuple[tuple[str, MechanicalFact, str], ...] = tuple(
    (SWITCH, _f, "glossary/7/6") for _c, _f, _cl in COMPOSITION if _c == SWITCH
) + tuple(
    (PROPAGATION, _f, clause)
    for _c, _f, _cl in COMPOSITION
    if _c == PROPAGATION
    for clause in ("glossary/9/1", "glossary/9/2", "glossary/10/0", "glossary/11/0")
)

#: CONTEXTUAL fact claims on clauses that are already *substantive*: each fact
#: in a group cites the part of the group's sentence that names it, while the
#: sentence as a whole claims the component. ``Fly Speed`` is named across two
#: leaves, so its fact cites both.
FACT_DETAIL: tuple[tuple[str, MechanicalFact, str], ...] = (
    (
        (
            SPECIAL,
            SpecialSpeedFact(mode=MovementMode.BURROW, listing=LISTED),
            "glossary/5/0",
        ),
        (
            SPECIAL,
            SpecialSpeedFact(mode=MovementMode.CLIMB, listing=LISTED),
            "glossary/5/0",
        ),
        (
            SPECIAL,
            SpecialSpeedFact(mode=MovementMode.FLY, listing=LISTED),
            "glossary/5/0",
        ),
        (
            SPECIAL,
            SpecialSpeedFact(mode=MovementMode.FLY, listing=LISTED),
            "glossary/6/0",
        ),
        (
            SPECIAL,
            SpecialSpeedFact(mode=MovementMode.SWIM, listing=LISTED),
            "glossary/6/0",
        ),
    )
    + tuple((_c, _f, "combat/3/0") for _c, _f, _cl in COMPOSITION if _c == MODES)
    + tuple((_c, _f, "combat/3/1") for _c, _f, _cl in COMPOSITION if _c == COMPOSING)
)

#: A citation printed inside a *substantive* clause does not make that clause
#: supporting authority: the sentence still states a rule. Only the five
#: *See also* clauses, whose whole content is the citation, land here.
SUPPORTING_CLAUSES = (
    RECORD_CONTEXT
    + tuple(
        clause
        for _, _, clauses in CITATIONS
        for clause in clauses
        if clause not in SUBSTANTIVE_CLAUSES
    )
    + tuple(clause for _, _, clause in FACT_CONTEXT)
)


# ---------------------------------------------------------------------------
# The composed draft, ledger and corpus
# ---------------------------------------------------------------------------

#: ``component -> its facts, in printed order``.
FACTS_BY_COMPONENT: dict[str, tuple[MechanicalFact, ...]] = {
    component: tuple(f for c, f, _ in COMPOSITION if c == component)
    for component in COMPONENTS
}


def _component(component_key: str) -> ComponentDraft:
    return ComponentDraft(
        record_key=SPEED,
        semantic_key=component_key,
        handling=ComponentHandling.STRUCTURED,
        facts=FACTS_BY_COMPONENT[component_key],
    )


def _draft() -> RepresentationDraft:
    """One entry, two sites, as one draft with every element's own provenance."""
    components = tuple(_component(key) for key in COMPONENTS)
    by_key = {c.semantic_key: c for c in components}
    provenance = (
        tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (SPEED,),
                _span_id(clause),
                ProvenanceRole.CONTEXTUAL,
            )
            for clause in RECORD_CONTEXT
        )
        + tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.COMPONENT,
                component_target_key(by_key[component_key]),
                _span_id(clause),
                ProvenanceRole.PRIMARY,
            )
            for component_key, clause in COMPONENT_PRIMARY
        )
        + tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(SPEED, component_key, fact),
                _span_id(clause),
                ProvenanceRole.PRIMARY,
            )
            for component_key, fact, clauses in COMPOSITION
            for clause in clauses
        )
        + tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(SPEED, component_key, fact),
                _span_id(clause),
                ProvenanceRole.CONTEXTUAL,
            )
            for component_key, fact, clause in FACT_DETAIL + FACT_CONTEXT
        )
        + tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.REFERENCE,
                reference_target_key(reference),
                _span_id(clause),
                ProvenanceRole.CONTEXTUAL,
            )
            for reference, (_, _, clauses) in zip(REFERENCES, CITATIONS, strict=True)
            for clause in clauses
        )
    )
    return RepresentationDraft(
        records=(RecordDraft(semantic_key=SPEED, kind=RecordKind.GLOSSARY_RULE),),
        components=components,
        prose_bindings=(),
        relationships=(),
        references=REFERENCES,
        provenance=provenance,
    )


def _ledger() -> ClassificationLedger:
    """The batch's own accepted spans, one per printed clause, all thirty-six."""
    dispositions = [
        (clause, SemanticDisposition.SUBSTANTIVE) for clause in SUBSTANTIVE_CLAUSES
    ] + [
        (clause, SemanticDisposition.SUPPORTING_AUTHORITY)
        for clause in SUPPORTING_CLAUSES
    ]
    return build_ledger(
        spans=tuple(
            SemanticSpan(
                span_id=_span_id(clause),
                leaf_id=_leaf(clause),
                char_start=_extent(clause)[0],
                char_end=_extent(clause)[1],
                disposition=disposition,
                review_state=ReviewState.ACCEPTED,
            )
            for clause, disposition in sorted(set(dispositions))
        )
    )


def _corpus() -> BoundCorpusSnapshot:
    return bound_corpus(
        leaf_lengths={leaf: len(text) for leaf, text in LEAVES.items()},
        chunk_coverage=tuple(
            coverage(CHUNKS[leaf], leaf, 0, len(text)) for leaf, text in LEAVES.items()
        ),
    )


def _authority() -> EffectiveAuthority:
    records = _base_records(candidate_of(RELEASE_BINDING, _ledger(), _draft()))
    return EffectiveAuthority(
        binding=RulesPackageBinding(
            package_uuid=uuid5(NAMESPACE_URL, "pkg-5d"),
            release_version="rel-5d",
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "proj-speed-1"),
            override_set_uuid=uuid5(NAMESPACE_URL, "ovs-speed-1"),
        ),
        records=tuple(records.values()),
        applied_overrides=(),
    )


#: The authoritative chunk text a GameMaster view resolves prose against.
PROSE = {CHUNKS[leaf]: text for leaf, text in LEAVES.items()}

#: The frozen six-batch prior this build must carry across the crossing.
FROZEN_PRIOR = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / (
        "accepted_prior_conditions_1_hazards_1_actions_1"
        "_attitudes_1_areas_of_effect_1_cover_1.json"
    )
)


# ---------------------------------------------------------------------------
# The inventory this module stands on
# ---------------------------------------------------------------------------


def test_every_clause_is_the_text_at_the_extent_the_manifest_records() -> None:
    """The reviewed inventory, checked against the leaves it was cut from.

    Thirty-six clauses partitioning sixteen leaves end to end. Slicing each leaf
    at the recorded extent has to give back the recorded text, and the extents
    have to tile each leaf without a gap or an overlap — which is what makes
    "the printed clause" a checkable phrase rather than a claim about retyping.
    """
    assert len(CLAUSE) == 36
    assert len(LEAVES) == 16

    by_leaf: dict[str, list[dict[str, object]]] = {}
    for clause in MANIFEST["clauses"]:
        text = LEAVES[clause["leaf_id"]][clause["char_start"] : clause["char_end"]]
        assert text == clause["text"], clause["clause_id"]
        by_leaf.setdefault(str(clause["leaf_id"]), []).append(clause)

    for leaf_id, clauses in by_leaf.items():
        cursor = 0
        for clause in sorted(clauses, key=lambda c: int(str(c["char_start"]))):
            assert clause["char_start"] == cursor, clause["clause_id"]
            cursor = int(str(clause["char_end"]))
        assert cursor == len(LEAVES[leaf_id]), leaf_id


def test_the_entry_is_composed_clause_for_clause_with_nothing_left_over() -> None:
    """Sixteen substantive clauses, seventeen facts, twenty supporting clauses.

    The counts are derived from the composition and the manifest independently
    and then compared, so a clause represented twice, a clause dropped, or a
    clause silently reclassified fails by name.
    """
    assert len(SUBSTANTIVE_CLAUSES) == 16
    assert len(set(SUBSTANTIVE_CLAUSES)) == 16
    assert len(COMPOSITION) == 17
    assert len(set(SUPPORTING_CLAUSES)) == 20
    assert set(SUBSTANTIVE_CLAUSES) | set(SUPPORTING_CLAUSES) == set(CLAUSE)
    assert not set(SUBSTANTIVE_CLAUSES) & set(SUPPORTING_CLAUSES)

    # Both sites are load-bearing: neither the glossary entry nor the combat
    # section can state the batch alone.
    by_site: dict[str, set[str]] = {}
    for clause in SUBSTANTIVE_CLAUSES:
        by_site.setdefault(str(CLAUSE[clause]["site"]), set()).add(clause)
    assert set(by_site) == {"glossary", "combat"}
    assert len(by_site["glossary"]) == 10
    assert len(by_site["combat"]) == 6


#: The one reconstruction that states no rule of its own. Its parts are the
#: zero-and-halving examples for the propagation rule glossary/9/0 states, so
#: they are cited to that fact rather than owning anything.
TAIL_OF_A_RULE_STATED_EARLIER = {
    ("glossary/9/2", "glossary/10/0", "glossary/11/0"),
}


def test_the_three_cross_leaf_sentences_are_each_one_statement() -> None:
    """A sentence the release split across leaves is still one sentence.

    The manifest records each reconstruction; this checks that the parts
    concatenate to it, and that each reconstruction's parts end up claiming a
    single target rather than becoming as many rules as the layout has leaves.
    """
    draft = _draft()
    reconstructions = {
        tuple(row["clause_ids"]): str(row["reconstructed_sentence"])
        for row in MANIFEST["cross_leaf_sentences"]
    }
    assert len(reconstructions) == 3

    for clause_ids, sentence in reconstructions.items():
        # Clauses inside one leaf abut; a leaf boundary is a line break, and the
        # word it splits is rejoined with the space the break stood for.
        parts = [
            "".join(str(CLAUSE[c]["text"]) for c in group)
            for _, group in groupby(clause_ids, key=_leaf)
        ]
        assert " ".join(parts).split() == sentence.split(), clause_ids
        assert len({_leaf(c) for c in clause_ids}) > 1, clause_ids

        spans = {_span_id(c) for c in clause_ids}
        claims = [c for c in draft.provenance if c.span_id in spans]
        assert claims, clause_ids
        owners = {
            (c.target_kind, c.target_key)
            for c in claims
            if c.role is ProvenanceRole.PRIMARY
        }
        if clause_ids in TAIL_OF_A_RULE_STATED_EARLIER:
            # This one owns nothing, so a bare owner-count bound would pass
            # here for the wrong reason. What it does hold is exactly one
            # fact target, at CONTEXTUAL: the sentence is the worked example
            # for a rule the leaf before it already stated.
            assert not owners, clause_ids
            assert {
                c.target_key
                for c in claims
                if c.target_kind is ProvenanceTargetKind.FACT
            } == {
                fact_target_key(
                    SPEED,
                    PROPAGATION,
                    FACTS_BY_COMPONENT[PROPAGATION][0],
                )
            }, clause_ids
        else:
            assert len(owners) == 1, clause_ids


def test_every_span_is_claimed_at_the_role_its_disposition_allows() -> None:
    """The span side of the partition, stated rather than left to be inferred.

    ``validate_representation`` already refuses a substantive span nothing
    owns and a supporting span nothing cites, so the nine-finding result
    proves this indirectly. Stating it here lets a reviewer read the claim
    without reading ``validation.py``: every substantive clause is owned by
    exactly one target, and every supporting clause is cited and owns
    nothing.
    """
    draft = _draft()
    by_span: dict[str, list[ProvenanceClaim]] = {}
    for claim in draft.provenance:
        by_span.setdefault(claim.span_id, []).append(claim)
    assert len(by_span) == len(CLAUSE)

    for clause in set(SUBSTANTIVE_CLAUSES):
        owners = {
            (c.target_kind, c.target_key)
            for c in by_span[_span_id(clause)]
            if c.role is ProvenanceRole.PRIMARY
        }
        assert len(owners) == 1, clause

    for clause in set(SUPPORTING_CLAUSES):
        claims = by_span[_span_id(clause)]
        assert claims, clause
        assert not [c for c in claims if c.role is ProvenanceRole.PRIMARY], clause


def test_the_fly_speed_reference_carries_both_printed_halves() -> None:
    """One citation, split by the layout, cited to both parts it is printed in.

    *"... Climb Speed, Fly"* ends one leaf and *"Speed, or Swim Speed, ..."*
    begins the next. The reference is one reference — the entry it points at is
    one entry — and the validator admits two provenance claims on it because
    only an exact duplicate edge is rejected. Dropping either claim would cite
    half a printed name.
    """
    (fly,) = [r for r in REFERENCES if r.source_text == "Fly Speed"]
    draft = _draft()
    claims = [
        c
        for c in draft.provenance
        if c.target_kind is ProvenanceTargetKind.REFERENCE
        and c.target_key == reference_target_key(fly)
    ]
    assert {c.span_id for c in claims} == {
        _span_id("glossary/5/0"),
        _span_id("glossary/6/0"),
    }
    assert {c.role for c in claims} == {ProvenanceRole.CONTEXTUAL}
    assert "Fly" in str(CLAUSE["glossary/5/0"]["text"])
    assert str(CLAUSE["glossary/6/0"]["text"]).startswith("Speed,")


def test_a_group_sentence_claims_the_component_and_its_members_cite_it() -> None:
    """Where one clause states several facts, the component is the PRIMARY owner.

    A span admits one PRIMARY owner, and *"such as a Burrow Speed, Climb Speed,
    Fly Speed, or Swim Speed"* states four. Making one of the four the owner
    would rank it above its siblings; making the clause supporting authority
    would lose that it states a rule. The component-level PRIMARY claim is the
    carrier that already exists, and ``action.attack``'s
    ``attack_equipment_change`` uses exactly this shape in accepted authority.
    """
    draft = _draft()
    for component_key in (SPECIAL, MODES, COMPOSING):
        facts = FACTS_BY_COMPONENT[component_key]
        assert len(facts) > 1, component_key
        for fact in facts:
            target = fact_target_key(SPEED, component_key, fact)
            roles = {c.role for c in draft.provenance if c.target_key == target}
            assert roles == {ProvenanceRole.CONTEXTUAL}, (component_key, fact)

    for component_key, clause in COMPONENT_PRIMARY:
        (owner,) = [
            c
            for c in draft.provenance
            if c.span_id == _span_id(clause) and c.role is ProvenanceRole.PRIMARY
        ]
        assert owner.target_kind is ProvenanceTargetKind.COMPONENT
        assert owner.target_key == (SPEED, component_key)

    # And the validator agrees the whole arrangement is well formed.
    assert validate_representation(draft, _ledger(), _corpus()) == DANGLING_FINDINGS


def test_the_sourcing_sentences_state_where_a_speed_comes_from_not_what_it_is() -> None:
    """No number is printed here, so no number is represented.

    ``CreatureSpeedFact`` exists and requires ``feet``. *"A character's Speed is
    determined during character creation."* and *"A monster's Speed is noted in
    the monster's stat block."* name a *source* for a value and print no value,
    so representing them as a creature speed would require inventing one. They
    are record-level supporting authority instead.
    """
    for clause in ("combat/3/3", "combat/3/4"):
        assert clause in RECORD_CONTEXT
        text = str(CLAUSE[clause]["text"])
        assert "Speed" in text
        assert not any(ch.isdigit() for ch in text), clause

    seen = {type(fact) for _, fact, _ in COMPOSITION}
    assert all(t.__name__ != "CreatureSpeedFact" for t in seen)


def test_the_chapter_navigations_are_supporting_authority_not_references() -> None:
    """Two citations that emit nothing, and the reason is printed in them.

    *"and "Playing the Game" ("Combat")."* names a chapter, for which there is
    no record, and points at this record's own second site. *"See "Rules
    Glossary" for more about Speed as well as about special speeds, such as a
    Climb Speed, Fly Speed, or Swim Speed."* points back at this entry and
    re-names three targets the glossary site already cites, so a reference from
    it would duplicate a citation rather than add one.
    """
    draft = _draft()
    for clause in ("glossary/3/5", "combat/3/5"):
        assert clause in RECORD_CONTEXT
        (claim,) = [c for c in draft.provenance if c.span_id == _span_id(clause)]
        assert claim.target_kind is ProvenanceTargetKind.RECORD
        assert claim.role is ProvenanceRole.CONTEXTUAL

    assert "Playing the Game" in str(CLAUSE["glossary/3/5"]["text"])
    assert "Rules Glossary" in str(CLAUSE["combat/3/5"]["text"])
    # The three speeds combat/3/5 re-names are already cited from the glossary.
    assert {"glossary.climb_speed", "glossary.fly_speed", "glossary.swim_speed"} <= {
        r.target_record_key for r in REFERENCES
    }


def test_the_mint_declares_seven_families_twelve_vocabularies_and_one_member() -> None:
    """The extension claim, stated where the schema hash covers it.

    Emitted by the schema payload, so this is not prose about the delta — an
    eighth family, a thirteenth vocabulary or any other widened accepted
    vocabulary would land a row here and fail. ``MovementMode`` is the one
    vocabulary schema 11 widens rather than mints, and it appears with exactly
    the one member it gains.
    """
    rows = [
        row
        for row in introduction_manifest()
        if row["introduced_in"] == SCHEMA_11_VERSION
    ]
    assert {row["name"] for row in rows if row["kind"] == "fact_family"} == {
        family.value
        for family in (
            FactFamily.SPEED_DEFINITION,
            FactFamily.MOVEMENT_DEPLETION,
            FactFamily.SPEED_SELECTION,
            FactFamily.SPEED_SWITCH_LIMIT,
            FactFamily.SPEED_CHANGE_PROPAGATION,
            FactFamily.SPECIAL_SPEED,
            FactFamily.MOVEMENT_COMPOSITION,
        )
    }, rows
    members = [row for row in rows if row["kind"] == "vocabulary_member"]
    vocabularies = {tuple(row["vocabulary"]) for row in members}
    assert len(vocabularies) == 12, sorted(vocabularies)
    assert {row["kind"] for row in rows} == {"fact_family", "vocabulary_member"}, rows

    # ``jump`` alone, against the whole ``MovementMode`` closure — a widening of
    # the vocabulary schema 3 admitted, not a second declaration of it. Schema 3
    # predates the introduction manifest, so the other six get no row at all.
    (widened,) = [row for row in members if row["name"] == "jump"]
    assert tuple(widened["vocabulary"]) == tuple(
        sorted(member.value for member in MovementMode)
    )
    assert MovementMode.JUMP in {
        fact.mode
        for _, fact, _ in COMPOSITION
        if isinstance(fact, MovementPermissionFact)
    }

    # This module is written against live authority.
    assert REPRESENTATION_SCHEMA_VERSION == SCHEMA_11_VERSION
    assert representation_schema_hash() == SCHEMA_11_HASH


def test_the_crossing_from_schema_10_is_exactly_one_registered_step() -> None:
    """One step, looked up rather than named, in the direction it applies."""
    steps = lift_path(
        (SCHEMA_10_VERSION, SCHEMA_10_HASH),
        (SCHEMA_11_VERSION, SCHEMA_11_HASH),
    )
    assert [step.lift_id for step in steps] == ["5d-lift-schema-10-to-11"]


# ---------------------------------------------------------------------------
# The six gaps, one case each
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fact",
    [entry[1] for entry in COMPOSITION],
    ids=[
        f"{entry[0]}-{entry[1].FAMILY.value}-{i}" for i, entry in enumerate(COMPOSITION)
    ],
)
def test_each_fact_is_well_formed_and_round_trips(fact: MechanicalFact) -> None:
    """Every fact, through the canonical payload and back."""
    assert fact_invariant_violations(fact) == ()
    payload = fact_payload(fact)
    rebuilt = fact_from_payload(payload)
    assert rebuilt == fact
    assert fact_payload(rebuilt) == payload


def test_g1_a_speed_is_a_distance_in_feet_per_turn_and_not_a_number() -> None:
    """*"the distance in feet the creature can cover when it moves on its turn."*

    The unit and the window are what the sentence states. The distance itself is
    a creature's, not the rule's — the definition says a Speed *is* a distance,
    never which one — so nothing here carries a value.
    """
    (fact,) = FACTS_BY_COMPONENT[DEFINITION]
    assert isinstance(fact, SpeedDefinitionFact)
    assert fact.unit is DistanceUnit.FOOT
    assert fact.window is MovementWindow.OWN_TURN
    assert set(fact_payload(fact)) == {"family", "unit", "window"}


def test_g2_the_ceiling_and_the_option_not_to_move_are_one_allowance() -> None:
    """*"a distance equal to your Speed or less"* + *"Or you can decide not to move."*

    Both clauses describe the same ceiling — *"or less"* already reaches zero,
    and ``Ready`` represents *"up to"* the same way. A second fact stating
    zero-movement would be the same permission written twice, which is what
    ADR-005d Decision 5 forbids. The window is what schema 11 adds; the basis
    was already there.
    """
    (fact,) = FACTS_BY_COMPONENT[ALLOWANCE]
    assert isinstance(fact, MovementAllowanceFact)
    assert fact.basis is MovementAllowanceBasis.OWN_SPEED
    assert fact.window is MovementWindow.OWN_TURN
    assert fact.FAMILY is FactFamily.MOVEMENT_ALLOWANCE

    _, _, clauses = [entry for entry in COMPOSITION if entry[0] == ALLOWANCE][0]
    assert clauses == ("combat/1/0", "combat/2/0", "combat/2/1")
    assert "or less" in "".join(
        str(CLAUSE[c]["text"]) for c in ("combat/1/0", "combat/2/0")
    )
    assert "decide not to move" in str(CLAUSE["combat/2/1"]["text"])

    # Schema 10 already had the family. The window is the whole of the delta,
    # and an allowance without it is what the earlier contract can state.
    assert (
        declared_meaning_violations(
            _single(
                ALLOWANCE, MovementAllowanceFact(basis=MovementAllowanceBasis.OWN_SPEED)
            ),
            SCHEMA_10_VERSION,
        )
        == []
    )
    assert declared_meaning_violations(_single(ALLOWANCE, fact), SCHEMA_10_VERSION)


def test_g3_depletion_names_both_terminators_and_the_race_between_them() -> None:
    """*"until it is used up or until you are done moving, whichever comes first."*

    Two terminators, and a resolution that is a statement *about the pair*. One
    terminator per fact would leave each half asserting a race against an
    opponent it does not name, so ``until`` carries both in printed order and
    ``resolution`` says the order does not decide the outcome.
    """
    (fact,) = FACTS_BY_COMPONENT[DEPLETION]
    assert isinstance(fact, MovementDepletionFact)
    assert fact.until == (
        MovementDepletionTerminator.ALLOWANCE_USED_UP,
        MovementDepletionTerminator.DONE_MOVING,
    )
    assert fact.resolution is MovementDepletionResolution.WHICHEVER_COMES_FIRST
    assert fact.depletes is MovementAllowanceBasis.OWN_SPEED

    # Depletion is a different statement from the ceiling, so they are different
    # components and neither can stand in for the other.
    assert DEPLETION != ALLOWANCE
    assert fact_payload(fact)["until"] == ["allowance_used_up", "done_moving"]

    # The distance deducted is never represented.
    assert "distance" in str(CLAUSE["combat/3/2"]["text"])
    assert set(fact_payload(fact)) == {"family", "depletes", "until", "resolution"}


def test_g4_selection_and_switching_keep_the_nonpositive_prohibition() -> None:
    """*"choose which one to use"*, *"switch ... during your move"*, and the limit.

    Two permissions and one limit, because the source states them as three
    things: which speed applies, that it may change mid-move, and what switching
    costs. The nonpositive case is a *prohibition* carried on the limit, not a
    computed result: *"If the result is 0 or less, you can't use the new speed"*.
    Nothing subtracts.
    """
    permits = {f.permits for f in FACTS_BY_COMPONENT[SELECTION]}
    assert permits == {
        SpeedSelection.CHOOSE_BEFORE_MOVING,
        SpeedSelection.SWITCH_DURING_MOVE,
    }

    (limit,) = FACTS_BY_COMPONENT[SWITCH]
    assert isinstance(limit, SpeedSwitchLimitFact)
    assert limit.accounting is SpeedSwitchAccounting.SUBTRACT_DISTANCE_ALREADY_MOVED
    assert limit.when_nonpositive is SpeedSwitchOutcome.FORBIDS_USING_THE_NEW_SPEED
    assert "0 or less" in str(CLAUSE["glossary/7/5"]["text"])

    # The worked example bounds the limit and becomes no second rule with a 30
    # and a 40 in it.
    assert (SWITCH, limit, "glossary/7/6") in FACT_CONTEXT
    assert "30" in str(CLAUSE["glossary/7/6"]["text"])


def test_g5_a_change_reaches_every_special_speed_and_the_examples_bound_it() -> None:
    """*"any special speed ... by an equal amount for the same duration."*

    Scope, magnitude and duration are the three things the sentence states. The
    two illustrations — reduced to 0, and halved — are what makes this checkable
    as *evidence*: they are carried as supporting authority on the rule, so no
    zero and no halving becomes a number the projection holds.
    """
    (fact,) = FACTS_BY_COMPONENT[PROPAGATION]
    assert isinstance(fact, SpeedChangePropagationFact)
    assert fact.to is SpeedPropagationScope.EVERY_SPECIAL_SPEED
    assert fact.magnitude is SpeedPropagationMagnitude.EQUAL_AMOUNT
    assert fact.duration is SpeedPropagationDuration.SAME_DURATION

    examples = [c for key, f, c in FACT_CONTEXT if (key, f) == (PROPAGATION, fact)]
    assert examples == [
        "glossary/9/1",
        "glossary/9/2",
        "glossary/10/0",
        "glossary/11/0",
    ]
    assert "reduced to 0" in str(CLAUSE["glossary/9/1"]["text"])
    assert "halved" in "".join(
        str(CLAUSE[c]["text"]) for c in ("glossary/10/0", "glossary/11/0")
    )
    # No arithmetic reaches the payload.
    assert set(fact_payload(fact)) == {"family", "to", "magnitude", "duration"}


def test_g6_modes_categories_and_composition_keep_such_as_open() -> None:
    """Four special speeds, four modes, two ways of composing a move.

    *"such as"* stays open because ``listing`` says the printed list is
    non-exhaustive — the openness is a property the fact states, not something
    inferred from a vocabulary that happens to hold more members. The modes come
    from the family schema 8 already minted, and the two compositions are the
    disjunction the sentence prints.
    """
    assert {f.mode for f in FACTS_BY_COMPONENT[SPECIAL]} == {
        MovementMode.BURROW,
        MovementMode.CLIMB,
        MovementMode.FLY,
        MovementMode.SWIM,
    }
    assert {f.listing for f in FACTS_BY_COMPONENT[SPECIAL]} == {LISTED}
    assert "such as" in str(CLAUSE["glossary/5/0"]["text"])

    assert {f.mode for f in FACTS_BY_COMPONENT[MODES]} == {
        MovementMode.CLIMB,
        MovementMode.CRAWL,
        MovementMode.JUMP,
        MovementMode.SWIM,
    }
    assert {type(f) for f in FACTS_BY_COMPONENT[MODES]} == {MovementPermissionFact}

    assert {f.composes for f in FACTS_BY_COMPONENT[COMPOSING]} == {
        MovementComposition.COMBINED_WITH_REGULAR_MOVEMENT,
        MovementComposition.ENTIRE_MOVE,
    }
    assert "entire move" in str(CLAUSE["combat/3/1"]["text"])

    # Burrowing is a special speed here and not a mode: the combat sentence
    # names four modes and burrow is not among them.
    assert MovementMode.BURROW not in {f.mode for f in FACTS_BY_COMPONENT[MODES]}


# ---------------------------------------------------------------------------
# Fail-closed probes
# ---------------------------------------------------------------------------


def _single(component_key: str, fact: MechanicalFact) -> RepresentationDraft:
    """One record, one component, one fact — no provenance, no ledger."""
    return RepresentationDraft(
        records=(RecordDraft(semantic_key=SPEED, kind=RecordKind.GLOSSARY_RULE),),
        components=(
            ComponentDraft(
                record_key=SPEED,
                semantic_key=component_key,
                handling=ComponentHandling.STRUCTURED,
                facts=(fact,),
            ),
        ),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("unit", "metre"),
        ("window", "your_turn"),
    ],
)
def test_a_member_outside_the_definition_closure_is_refused(
    field: str, value: str
) -> None:
    """A near-miss member is refused rather than coerced to the nearest one."""
    payload = dict(fact_payload(FACTS_BY_COMPONENT[DEFINITION][0])) | {field: value}
    with pytest.raises(MalformedFactPayloadError) as raised:
        fact_from_payload(payload)
    assert field in str(raised.value), raised.value


@pytest.mark.parametrize(
    ("until", "why"),
    [
        ("allowance_used_up", "a bare string is not the printed pair"),
        (["until_you_stop"], "a terminator outside the closure"),
    ],
    ids=["scalar", "unknown"],
)
def test_a_mistyped_terminator_list_is_refused_at_the_builder(
    until: object, why: str
) -> None:
    """The wire seam refuses what it cannot type, and names the field."""
    payload = dict(fact_payload(FACTS_BY_COMPONENT[DEPLETION][0])) | {"until": until}
    with pytest.raises(MalformedFactPayloadError) as raised:
        fact_from_payload(payload)
    assert "until" in str(raised.value), why


@pytest.mark.parametrize(
    ("until", "why"),
    [
        ([], "a depletion that never stops states no rule"),
        (["allowance_used_up", "allowance_used_up"], "the same terminator twice"),
    ],
    ids=["empty", "repeat"],
)
def test_a_correctly_typed_terminator_list_that_states_nothing_is_refused(
    until: list[str], why: str
) -> None:
    """Well-typed and still not a rule, so the intrinsic contract is what refuses it.

    Both cases rebuild without complaint: every element is a declared member, and
    an empty list has no element to be wrong. They are refused by the invariants
    the schema declares, which is the same split ``suspended_by_any_of`` already
    uses — the builder types a payload, the invariants say what a typed value
    has to mean.
    """
    payload = dict(fact_payload(FACTS_BY_COMPONENT[DEPLETION][0])) | {"until": until}
    rebuilt = fact_from_payload(payload)
    assert isinstance(rebuilt, MovementDepletionFact)
    assert fact_invariant_violations(rebuilt), why


def test_an_unknown_family_is_refused_rather_than_guessed() -> None:
    """A family name that is not declared has no builder and gets none."""
    payload = dict(fact_payload(FACTS_BY_COMPONENT[DEPLETION][0])) | {
        "family": "movement_exhaustion"
    }
    with pytest.raises(UnknownFactFamilyError):
        fact_from_payload(payload)


def test_schema_10_cannot_state_the_seven_new_families() -> None:
    """The succession is real in the refusing direction too.

    Every fact from a family schema 11 mints is meaning schema 10's declared
    contract cannot carry, and the composed draft as a whole is refused under
    it. ``MovementPermissionFact`` is deliberately *not* in this list: schema 8
    minted that family, and asserting it refused would claim a delta the mint
    does not have. What schema 10 cannot state about it is the ``jump`` member,
    which the next test isolates.
    """
    minted = {
        FactFamily.SPEED_DEFINITION,
        FactFamily.MOVEMENT_DEPLETION,
        FactFamily.SPEED_SELECTION,
        FactFamily.SPEED_SWITCH_LIMIT,
        FactFamily.SPEED_CHANGE_PROPAGATION,
        FactFamily.SPECIAL_SPEED,
        FactFamily.MOVEMENT_COMPOSITION,
    }
    for component_key, fact, _ in COMPOSITION:
        if fact.FAMILY not in minted:
            continue
        assert declared_meaning_violations(
            _single(component_key, fact), SCHEMA_10_VERSION
        ), fact
    assert declared_meaning_violations(_draft(), SCHEMA_10_VERSION)
    assert declared_meaning_violations(_draft(), REPRESENTATION_SCHEMA_VERSION) == []


@pytest.mark.parametrize("version", [SCHEMA_8_VERSION, SCHEMA_10_VERSION])
def test_an_earlier_contract_refuses_the_jump_member_it_never_registered(
    version: str,
) -> None:
    """The widening is refused by *member*, on a family and field that predate it.

    ``MovementPermissionFact.mode`` arrived at schema 8 and neither schema 8 nor
    schema 10 registered ``jump``. That is what makes the schema-8 registry row
    a frozen closure rather than whatever the live enum happens to hold: the
    same field, the same family, and the member is the only thing refused.
    """
    jumping = _single(MODES, MovementPermissionFact(mode=MovementMode.JUMP))
    assert declared_meaning_violations(jumping, version)
    # A member both contracts did register passes the same shape.
    climbing = _single(MODES, MovementPermissionFact(mode=MovementMode.CLIMB))
    assert declared_meaning_violations(climbing, version) == []
    assert declared_meaning_violations(jumping, REPRESENTATION_SCHEMA_VERSION) == []


def test_an_unminted_version_is_refused() -> None:
    """Schema 12 does not exist, and the payload seam says so rather than guessing.

    Version legality is not ``declared_meaning_violations``'s question — it
    answers what a *recognised* schema can state. The emitter is where an
    unrecognised version is refused, and it stays refused now that ``…-11`` is
    real: the probe moves to the next unminted string rather than the assertion
    being retired.
    """
    with pytest.raises(UnsupportedSchemaVersionError):
        representation_payload(_draft(), schema_version="5d-representation-schema-12")
    assert representation_payload(
        _draft(), schema_version=REPRESENTATION_SCHEMA_VERSION
    ) == representation_payload(_draft())


# ---------------------------------------------------------------------------
# Validation, persistence, identity
# ---------------------------------------------------------------------------

#: The batch's honest residue: nine citations whose entries are not in this cut.
#: Pinned as the exact tuple the validator emits, in its own order, so a tenth
#: finding cannot hide behind a filter.
DANGLING_FINDINGS = tuple(
    f"reference {SCOPE}:{text!r}: unknown target record {target}"
    for text, target, _ in CITATIONS
)


def test_the_composition_validates_with_only_the_nine_citations_outstanding() -> None:
    """One entry, thirty-six clauses, and exactly nine named residues.

    Everything internal is clean — record, components, facts, provenance claims
    and the span partition — and the only findings are the citations this batch
    is not allowed to close. Each clears when the cited entry is ingested, never
    by editing the record that cites it.
    """
    findings = validate_representation(_draft(), _ledger(), _corpus())
    assert findings == DANGLING_FINDINGS
    assert len(findings) == 9


def test_the_ten_combined_unresolved_targets_are_what_this_batch_leaves() -> None:
    """Speed closes one prior citation and opens nine, leaving ten in all.

    This is arithmetic over two pinned residues rather than a seam: nothing
    merges an accepted prior with a new batch's draft, so the honest statement
    is that the prior's recorded residue minus what this batch defines, plus
    this batch's own dangling targets, is ten. ``glossary.concentration`` is the
    one the prior carries that Speed does not touch.
    """
    prior = load_accepted_inputs(FROZEN_PRIOR).oracle.representation
    prior_dangling = {
        reference.target_record_key
        for reference in prior.references
        if reference.target_record_key
        not in {record.semantic_key for record in prior.records}
    }
    # The pinned residue, not a restatement of it: the freeze owns that set.
    assert prior_dangling == UNRESOLVED_TARGETS

    draft = _draft()
    defined = {record.semantic_key for record in draft.records}
    assert defined == {SPEED}
    mine = {
        reference.target_record_key
        for reference in draft.references
        if reference.target_record_key not in defined
    }
    assert len(mine) == 9

    combined = (prior_dangling - defined) | mine
    assert combined == {"glossary.concentration"} | mine
    assert len(combined) == 10


def test_the_whole_composition_survives_persistence_and_reconstruction(
    session: Session,
) -> None:
    """Typed rows in, typed rows out, and the same identity on the far side.

    Reconstruction reads the database and nothing else, so a family the store
    cannot round trip fails here rather than the first time a real corpus
    carries it. The multi-fact components are the load-bearing part — fact order
    inside a component has to survive — and so is ``until``, the first tuple
    field this batch adds: a pair that came back reordered would be a different
    printed sentence.
    """
    identified = identify_projection(candidate_of(RELEASE_BINDING, _ledger(), _draft()))
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    by_key = {
        (c.record_key, c.semantic_key): c for c in rebuilt.representation.components
    }
    for component_key in COMPONENTS:
        assert (
            by_key[(SPEED, component_key)].facts == FACTS_BY_COMPONENT[component_key]
        ), component_key

    (depletion,) = by_key[(SPEED, DEPLETION)].facts
    assert isinstance(depletion, MovementDepletionFact)
    assert depletion.until == (
        MovementDepletionTerminator.ALLOWANCE_USED_UP,
        MovementDepletionTerminator.DONE_MOVING,
    )

    assert rebuilt.representation.references == REFERENCES
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid


@pytest.mark.parametrize(
    ("component_key", "changed", "why"),
    [
        (
            DEPLETION,
            (
                MovementDepletionFact(
                    depletes=MovementAllowanceBasis.OWN_SPEED,
                    until=(
                        MovementDepletionTerminator.DONE_MOVING,
                        MovementDepletionTerminator.ALLOWANCE_USED_UP,
                    ),
                    resolution=MovementDepletionResolution.WHICHEVER_COMES_FIRST,
                ),
            ),
            "reordering the terminators is not the sentence the source printed",
        ),
        (
            ALLOWANCE,
            (MovementAllowanceFact(basis=MovementAllowanceBasis.OWN_SPEED),),
            "dropping the per-turn window widens the ceiling to every turn",
        ),
        (
            ALLOWANCE,
            (
                MovementAllowanceFact(
                    basis=MovementAllowanceBasis.OWN_SPECIAL_SPEED,
                    window=MovementWindow.OWN_TURN,
                ),
            ),
            "the allowance is the creature's Speed, not one of its special speeds",
        ),
        (
            COMPOSING,
            (
                MovementCompositionFact(
                    composes=MovementComposition.COMBINED_WITH_REGULAR_MOVEMENT
                ),
            ),
            "dropping the second half of a disjunction is a different rule",
        ),
        (
            SPECIAL,
            tuple(
                SpecialSpeedFact(mode=mode, listing=LISTED)
                for mode in (
                    MovementMode.BURROW,
                    MovementMode.CLIMB,
                    MovementMode.FLY,
                    MovementMode.SWIM,
                    MovementMode.WALK,
                )
            ),
            "adding a special speed the source never listed",
        ),
    ],
)
def test_a_changed_meaning_changes_the_projection_identity(
    component_key: str, changed: tuple[MechanicalFact, ...], why: str
) -> None:
    """Each perturbation is a different rule, so each is a different identity.

    Identity is computed over the canonical payload, so this is the mechanism
    that stops any of these from passing as a reformat of the accepted one. The
    first case is the one this schema's tuple field makes possible: printed
    order is preserved rather than sorted, so reordering it moves the hash.
    """
    draft = _draft()
    perturbed = RepresentationDraft(
        records=draft.records,
        components=tuple(
            (
                ComponentDraft(
                    record_key=c.record_key,
                    semantic_key=c.semantic_key,
                    handling=c.handling,
                    facts=changed,
                )
                if c.semantic_key == component_key
                else c
            )
            for c in draft.components
        ),
        prose_bindings=draft.prose_bindings,
        relationships=draft.relationships,
        references=draft.references,
        provenance=draft.provenance,
    )
    original = identify_projection(candidate_of(RELEASE_BINDING, _ledger(), draft))
    moved = identify_projection(candidate_of(RELEASE_BINDING, _ledger(), perturbed))
    assert moved.payload_hash != original.payload_hash, why
    assert moved.projection_uuid != original.projection_uuid, why


# ---------------------------------------------------------------------------
# The frozen prior, across the registered crossing
# ---------------------------------------------------------------------------


def test_the_frozen_prior_crosses_with_every_accepted_element_preserved() -> None:
    """Six batches, their acceptances, their provenance and their anchors.

    The crossing rebinds and does not rebuild. Schema 11 widens
    ``MovementMode`` — a vocabulary ``actions-1`` already consumes through
    ``MovementPermissionFact`` — so a lift that re-derived anchors would erase
    the record of what each batch was accepted under. Each anchor keeps the
    version and hash it was accepted at, and the only thing that moves is the
    oracle's own binding.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    before_identity = oracle_identity(inputs.oracle)
    target = (SCHEMA_11_VERSION, SCHEMA_11_HASH)
    lifted, records = lift_accepted_inputs(inputs, target)
    assert [r.lift_id for r in records] == ["5d-lift-schema-10-to-11"]

    # Collections cross by identity, not by rebuild.
    assert lifted.batches is inputs.batches
    assert lifted.acceptances is inputs.acceptances
    assert lifted.schema_anchors is inputs.schema_anchors
    assert lifted.oracle.representation is inputs.oracle.representation
    assert lifted.oracle.spans is inputs.oracle.spans
    assert lifted.oracle.obligations is inputs.oracle.obligations

    # The six anchors keep the six declarations they were accepted under — none
    # of which is schema 11.
    anchored = {
        a.batch_id: (a.schema_version, a.schema_hash) for a in lifted.schema_anchors
    }
    assert set(anchored) == {
        "conditions-1",
        "hazards-1",
        "actions-1",
        "attitudes-1",
        "areas-of-effect-1",
        "cover-1",
    }
    assert anchored["cover-1"] == (SCHEMA_10_VERSION, SCHEMA_10_HASH)
    assert SCHEMA_11_VERSION not in {version for version, _ in anchored.values()}

    # Acceptance metadata is untouched, reviewer and timestamp included.
    assert [
        (a.span_id, a.batch_id, a.reviewer, a.accepted_at) for a in lifted.acceptances
    ] == [
        (a.span_id, a.batch_id, a.reviewer, a.accepted_at) for a in inputs.acceptances
    ]

    # The frozen file on disk is untouched by asking.
    assert oracle_identity(inputs.oracle) == before_identity
    assert (
        candidate_from_accepted_inputs(lifted).representation
        is inputs.oracle.representation
    )


# ---------------------------------------------------------------------------
# The consumer boundary
# ---------------------------------------------------------------------------


def test_the_entry_reaches_a_consumer_as_closed_vocabulary_members() -> None:
    """``_base_records`` is what every reader of mechanical authority goes through.

    One record, nine structured components, no governing prose anywhere: the
    whole entry arrives as declared enum members with span ids for provenance,
    which is the entire consumer-visible effect of this mint.
    """
    records = _base_records(candidate_of(RELEASE_BINDING, _ledger(), _draft()))
    assert set(records) == {SPEED}
    by_key = {c.semantic_key: c for c in records[SPEED].components}
    assert set(by_key) == set(COMPONENTS)

    for component_key in COMPONENTS:
        component = by_key[component_key]
        assert component.handling is ComponentHandling.STRUCTURED
        assert component.irreducibility_reason_code is None
        assert component.governing_prose == ()
        assert [entry.fact for entry in component.facts] == list(
            FACTS_BY_COMPONENT[component_key]
        )

    # Each fact carries the spans that state it, whether it claims them or cites
    # them beneath a component that does.
    for component_key, fact, clauses in COMPOSITION:
        (entry,) = [e for e in by_key[component_key].facts if e.fact == fact]
        expected = {_span_id(c) for c in clauses} | {
            _span_id(c)
            for key, f, c in FACT_DETAIL + FACT_CONTEXT
            if (key, f) == (component_key, fact)
        }
        assert set(entry.span_ids) == expected, (component_key, fact)


def test_the_typed_view_carries_every_family_and_every_fact() -> None:
    """The deterministic consumer's whole reading of the entry."""
    typed = {r.semantic_key: r for r in build_typed_view(_authority()).records}
    assert set(typed) == {SPEED}
    seen = [
        entry.fact
        for record in typed.values()
        for component in record.components
        for entry in component.facts
    ]
    assert len(seen) == 17
    assert {fact.FAMILY for fact in seen} == {
        FactFamily.SPEED_DEFINITION,
        FactFamily.MOVEMENT_ALLOWANCE,
        FactFamily.MOVEMENT_DEPLETION,
        FactFamily.SPEED_SELECTION,
        FactFamily.SPEED_SWITCH_LIMIT,
        FactFamily.SPEED_CHANGE_PROPAGATION,
        FactFamily.SPECIAL_SPEED,
        FactFamily.MOVEMENT_PERMISSION,
        FactFamily.MOVEMENT_COMPOSITION,
    }
    for _, fact, _ in COMPOSITION:
        assert fact in seen


def test_the_gamemaster_view_names_the_clauses_without_delivering_them() -> None:
    """Structured components have no prose to resolve, and that is the point.

    Every component here is ``STRUCTURED``, so the GameMaster view resolves no
    governing prose at all: each rule arrives as its vocabulary members, and the
    sentence it came from arrives as a span id a reader can look up. The printed
    clause text is never carried in the view — which is what keeps licensed
    source text out of a projection that only needs to cite it, and it matters
    more here than in any previous batch because five of these clauses are
    worked examples a view would be tempted to quote.
    """
    view = build_gamemaster_view(_authority(), PROSE)
    assert {c.record_key for c in view.components} == {SPEED}
    assert len(view.components) == 9
    for component in view.components:
        assert component.governing_prose == ()
        assert component.structured_context != ()
        for entry in component.structured_context:
            assert entry.span_ids != ()

    # Exactly the three group components carry component-level spans, and they
    # arrive as ids, never as text.
    assert {c.component_key for c in view.components if c.span_ids} == {
        SPECIAL,
        MODES,
        COMPOSING,
    }
    # Every printed *sentence* is absent from the view. The headings are not
    # checked: "Speed" is one word and also the name of half this schema's
    # vocabulary, so its absence could not be evidence of anything.
    rendered = str(view)
    sentences = [
        clause_id
        for clause_id in set(CLAUSE)
        if len(str(CLAUSE[clause_id]["text"]).split()) >= 4
    ]
    assert len(sentences) == 24
    for clause_id in sentences:
        assert str(CLAUSE[clause_id]["text"]).strip() not in rendered, clause_id
