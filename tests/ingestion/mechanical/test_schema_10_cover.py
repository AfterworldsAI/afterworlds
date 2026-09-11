"""Cover, end to end, under representation schema 10 — CRD Issue 5d (#137).

The batch is ``cover-1`` and the source population is the two ``Cover`` entry
containers the bound 5.2.1 release prints: one under *Rules Glossary > Rules
Definitions*, one under *Playing the Game > Combat*. Sixteen leaves, twenty-eight
clauses, reviewed and committed as
``.claude/review-notes/issue-5d-cover-1-source-manifest.json``, and read out of
that file here rather than retyped.

**What schema 10 adds, and why it had to.** Schema 9 could already *consume* a
degree of cover — ``Applicability.cover`` and
``BlockedLineExclusionFact.blocking_cover`` both read one — and could not
*define* what a degree is. Six printed meanings had no carrier: the ``half``
member itself, a degree's defensive bonus, Total Cover's targeting prohibition,
what offers each degree and how much of the target it must cover, the rule that
a benefit applies only against something originating on the far side, and the
rule that multiple applicable degrees resolve to the most protective one without
summing. Five families over eight closed vocabularies state all six, and one
registered crossing carries the frozen five-batch prior across.

**Two printings, one set of rules.** Four rules are printed at both sites — the
three degree benefits and non-stacking. They are represented once each, with
``PRIMARY`` provenance from both sites' spans, because that is what the source
did: it printed one rule twice. Provenance is per span, so several spans
claiming one target is the ordinary case, not a workaround. Where the second
printing *defers* rather than states — *"As detailed in the Cover table"* — it
is supporting authority linked to what it defers to, and the asymmetry between
the two is deliberate.

**What this module does not claim.** It computes no geometry, states no rank
over the three degrees, and claims no attack resolution or adapter ownership.
Every gap is a named closed member; measuring how much of a target an obstacle
covers, deciding which side an effect came from, and choosing a degree for a
scene all stay outside. The excluded work is the computation, not the subject
matter.
"""

from __future__ import annotations

import json
import pathlib
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
    REPRESENTATION_SCHEMA_VERSION,
    AbilityScore,
    Applicability,
    ApplicabilityKind,
    BenefitOriginSide,
    BlockedLineExclusionFact,
    BlockedLineQuantifier,
    ComponentDraft,
    ComponentHandling,
    CoverageThreshold,
    CoverBenefitOriginFact,
    CoverDefense,
    CoverDefensiveBonusFact,
    CoverDegree,
    CoverDegreeCombination,
    CoverDegreeSelection,
    CoverDegreeSelectionFact,
    CoveredInteraction,
    CoverOfferor,
    CoverProvisionFact,
    CoverTargetingProhibitionFact,
    FactFamily,
    MechanicalFact,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    TargetingProhibition,
    UnknownFactFamilyError,
    component_target_key,
    declared_meaning_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
    fact_target_key,
    introduction_manifest,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_6_VERSION,
    SCHEMA_9_HASH,
    SCHEMA_9_VERSION,
    SCHEMA_10_HASH,
    SCHEMA_10_VERSION,
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
    / "issue-5d-cover-1-source-manifest.json"
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

#: The one record this batch defines. Settled in the checkpoint on evidence
#: rather than taste: accepted authority already cites ``glossary.cover`` by
#: name, the three degrees are untagged table rows with no entry of their own,
#: and ``CoverDegree`` is already consumed as a vocabulary by two accepted
#: facts — so a degree is a member, not a record.
COVER = "glossary.cover"


def _leaf(clause_id: str) -> str:
    return str(CLAUSE[clause_id]["leaf_id"])


def _extent(clause_id: str) -> tuple[int, int]:
    row = CLAUSE[clause_id]
    return int(row["char_start"]), int(row["char_end"])


def _span_id(clause_id: str) -> str:
    return derive_span_id(_leaf(clause_id), *_extent(clause_id))


# ---------------------------------------------------------------------------
# The sixteen substantive clauses, as four components and eight facts
# ---------------------------------------------------------------------------
#
# The table prints two columns of rule — what each degree *does* and what
# *offers* it — and the prose prints two more rules that qualify every degree.
# That is the grouping: one component per column, one per qualifying rule, and
# a fact per degree inside the two that have one. Grouping the degrees rather
# than giving each its own component is what lets the sentence that states the
# vocabulary's closure — "there are three degrees of cover" — claim a component
# as a whole, which is the carrier the schema actually has for a statement that
# is about no single fact.

BENEFIT = "degree_benefit"
PROVISION = "degree_provision"
ORIGIN = "benefit_origin"
SELECTION = "degree_selection"

#: ``(component, fact, clause ids)`` — the whole substantive composition, in
#: printed order. A fact naming two clauses is one rule the source printed at
#: both sites, or one rule the table splits across a degree cell and its row.
COMPOSITION: tuple[tuple[str, MechanicalFact, tuple[str, ...]], ...] = (
    # -- What each degree does -----------------------------------------------
    # "Half Cover (+2 bonus to AC and Dexterity saving throws)," in the
    # glossary and "+2 bonus to AC and Dexterity saving throws" in the table.
    # One printed benefit that is two modifications at once, so the conjunction
    # lives inside the fact: a shape that could stateonly the saving-throw half
    # would silently drop AC.
    (
        BENEFIT,
        CoverDefensiveBonusFact(
            degree=CoverDegree.HALF,
            bonus=2,
            to_defense=CoverDefense.ARMOR_CLASS,
            to_saving_throw=AbilityScore.DEXTERITY,
        ),
        ("glossary/1/2", "combat/6/0"),
    ),
    # The same rule at +5, printed the same way at both sites.
    (
        BENEFIT,
        CoverDefensiveBonusFact(
            degree=CoverDegree.THREE_QUARTERS,
            bonus=5,
            to_defense=CoverDefense.ARMOR_CLASS,
            to_saving_throw=AbilityScore.DEXTERITY,
        ),
        ("glossary/1/3", "combat/8/0"),
    ),
    # "and Total Cover (can't be targeted directly)." Total Cover is the one
    # degree whose benefit is not a bonus, which is why it is a different
    # family rather than a bonus of zero. "Directly" is printed and load
    # bearing: the prohibition is on direct targeting, not on all effects.
    (
        BENEFIT,
        CoverTargetingProhibitionFact(
            degree=CoverDegree.TOTAL,
            prohibits=TargetingProhibition.DIRECT_TARGETING,
        ),
        ("glossary/1/4", "combat/11/0"),
    ),
    # -- What offers each degree ---------------------------------------------
    # "Half" / "Another creature or an object that covers at least half of the
    # target". Half is the only degree a creature can offer; the other two name
    # an object, and that asymmetry is printed rather than inferred.
    (
        PROVISION,
        CoverProvisionFact(
            degree=CoverDegree.HALF,
            offered_by=CoverOfferor.ANOTHER_CREATURE_OR_AN_OBJECT,
            coverage=CoverageThreshold.AT_LEAST_HALF,
        ),
        ("combat/5/0", "combat/6/1"),
    ),
    # "ThreeQuarters" / "An object that covers at least three-quarters of the
    # target". The degree cell arrives unhyphenated from the bound release; the
    # extraction artifact is carried verbatim rather than repaired here.
    (
        PROVISION,
        CoverProvisionFact(
            degree=CoverDegree.THREE_QUARTERS,
            offered_by=CoverOfferor.AN_OBJECT,
            coverage=CoverageThreshold.AT_LEAST_THREE_QUARTERS,
        ),
        ("combat/7/0", "combat/9/0"),
    ),
    # "Total" / "An object that covers the whole target". "The whole" is not
    # "at least the whole": it is its own printed phrase, and one closed member
    # states it directly. An exact numeric pair would have been admissible here
    # too; three members are enough.
    (
        PROVISION,
        CoverProvisionFact(
            degree=CoverDegree.TOTAL,
            offered_by=CoverOfferor.AN_OBJECT,
            coverage=CoverageThreshold.WHOLE_TARGET,
        ),
        ("combat/10/0", "combat/11/1"),
    ),
    # -- The two rules that qualify every degree -----------------------------
    # "A target can benefit from cover only when an attack or other effect
    # originates on the opposite side of the cover." Printed once, in the
    # combat chapter only, and it is a precondition on the benefit rather than
    # a property of any one degree — which is why a degree-only record would
    # have lost it entirely.
    (
        ORIGIN,
        CoverBenefitOriginFact(
            interaction=CoveredInteraction.AN_ATTACK_OR_OTHER_EFFECT,
            requires_origin=BenefitOriginSide.OPPOSITE_SIDE_OF_THE_COVER,
        ),
        ("combat/1/2",),
    ),
    # "a target benefits only from the most protective degree" (glossary) and
    # "only the most protective degree of cover applies; the degrees aren't
    # added together" (combat). The glossary prints the selection half alone,
    # so the restatement the combat printing adds is a second field on one
    # fact, not a second fact.
    (
        SELECTION,
        CoverDegreeSelectionFact(
            selects=CoverDegreeSelection.MOST_PROTECTIVE,
            combination=CoverDegreeCombination.NOT_ADDED_TOGETHER,
        ),
        ("glossary/1/5", "combat/1/3"),
    ),
)

#: The one substantive clause no fact represents. It states the *closure of a
#: vocabulary* — three degrees, no more — and ``ProvenanceTargetKind`` has no
#: vocabulary member to claim. The carrier that does exist is a component-level
#: ``PRIMARY`` claim: a span stating something about a component as a whole
#: rather than about any one of its facts. That is the shape the frozen prior
#: already uses nineteen times.
CLOSURE_CLAUSE = "glossary/1/1"

#: Every substantive clause id, derived from the composition rather than listed
#: beside it, so a clause represented twice or not at all is visible.
SUBSTANTIVE_CLAUSES = (CLOSURE_CLAUSE,) + tuple(
    clause for _, _, clauses in COMPOSITION for clause in clauses
)


# ---------------------------------------------------------------------------
# The twelve supporting clauses, each linked to what it actually supports
# ---------------------------------------------------------------------------

#: Supporting clauses the *record* carries: both headings, the two framing
#: sentences, the table caption, the ``Degree`` column header, and the
#: glossary's chapter navigation.
#:
#: The navigation is the reason this batch adds no reference at all. Every
#: accepted reference targets a record key, and *"Playing the Game" ("Combat")*
#: names a chapter — for which there is no record — and names this record's own
#: second site, so a reference would be self-directed even if a target existed.
#: Record-owned supporting authority is the honest scope for it.
RECORD_CONTEXT: tuple[str, ...] = (
    "glossary/0/0",
    "glossary/1/0",
    "glossary/2/0",
    "glossary/3/0",
    "combat/0/0",
    "combat/1/0",
    "combat/1/5",
    "combat/2/0",
)

#: Supporting clauses a *component* carries, because they are about that whole
#: column rather than about one degree in it. ``combat/1/1`` is here and
#: ``glossary/1/1`` is substantive for one reason: the glossary *states* the
#: three degrees, while the combat printing *defers* — "As detailed in the
#: Cover table" — and a deferral is supporting authority for what it defers to.
COMPONENT_CONTEXT: tuple[tuple[str, str], ...] = (
    (BENEFIT, "combat/1/1"),
    (BENEFIT, "combat/3/0"),
    (PROVISION, "combat/4/0"),
)

#: The worked example. It illustrates the selection rule with a creature and a
#: tree trunk and states no rule of its own, so it bounds that fact rather than
#: becoming a second one with invented participants in it.
FACT_CONTEXT: tuple[tuple[str, MechanicalFact, str], ...] = (
    (
        SELECTION,
        CoverDegreeSelectionFact(
            selects=CoverDegreeSelection.MOST_PROTECTIVE,
            combination=CoverDegreeCombination.NOT_ADDED_TOGETHER,
        ),
        "combat/1/4",
    ),
)

SUPPORTING_CLAUSES = (
    RECORD_CONTEXT
    + tuple(clause for _, clause in COMPONENT_CONTEXT)
    + tuple(clause for _, _, clause in FACT_CONTEXT)
)


# ---------------------------------------------------------------------------
# The composed draft, ledger and corpus
# ---------------------------------------------------------------------------

#: ``component -> its facts, in printed order``.
FACTS_BY_COMPONENT: dict[str, tuple[MechanicalFact, ...]] = {
    component: tuple(f for c, f, _ in COMPOSITION if c == component)
    for component in (BENEFIT, PROVISION, ORIGIN, SELECTION)
}

COMPONENTS = (BENEFIT, PROVISION, ORIGIN, SELECTION)


def _component(component_key: str) -> ComponentDraft:
    return ComponentDraft(
        record_key=COVER,
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
                (COVER,),
                _span_id(clause),
                ProvenanceRole.CONTEXTUAL,
            )
            for clause in RECORD_CONTEXT
        )
        + (
            ProvenanceClaim(
                ProvenanceTargetKind.COMPONENT,
                component_target_key(by_key[BENEFIT]),
                _span_id(CLOSURE_CLAUSE),
                ProvenanceRole.PRIMARY,
            ),
        )
        + tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.COMPONENT,
                component_target_key(by_key[component_key]),
                _span_id(clause),
                ProvenanceRole.CONTEXTUAL,
            )
            for component_key, clause in COMPONENT_CONTEXT
        )
        + tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(COVER, component_key, fact),
                _span_id(clause),
                ProvenanceRole.PRIMARY,
            )
            for component_key, fact, clauses in COMPOSITION
            for clause in clauses
        )
        + tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(COVER, component_key, fact),
                _span_id(clause),
                ProvenanceRole.CONTEXTUAL,
            )
            for component_key, fact, clause in FACT_CONTEXT
        )
    )
    return RepresentationDraft(
        records=(RecordDraft(semantic_key=COVER, kind=RecordKind.GLOSSARY_RULE),),
        components=components,
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=provenance,
    )


def _ledger() -> ClassificationLedger:
    """The batch's own accepted spans, one per printed clause, all twenty-eight."""
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
            for clause, disposition in sorted(dispositions)
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
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "proj-cover-1"),
            override_set_uuid=uuid5(NAMESPACE_URL, "ovs-cover-1"),
        ),
        records=tuple(records.values()),
        applied_overrides=(),
    )


#: The authoritative chunk text a GameMaster view resolves prose against.
PROSE = {CHUNKS[leaf]: text for leaf, text in LEAVES.items()}

#: The frozen five-batch prior this build must carry across the crossing.
FROZEN_PRIOR = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / (
        "accepted_prior_conditions_1_hazards_1_actions_1"
        "_attitudes_1_areas_of_effect_1.json"
    )
)


# ---------------------------------------------------------------------------
# The inventory this module stands on
# ---------------------------------------------------------------------------


def test_every_clause_is_the_text_at_the_extent_the_manifest_records() -> None:
    """The reviewed inventory, checked against the leaves it was cut from.

    Twenty-eight clauses partitioning sixteen leaves end to end. Slicing each
    leaf at the recorded extent has to give back the recorded text, and the
    extents have to tile each leaf without a gap or an overlap — which is what
    makes "the printed clause" a checkable phrase rather than a claim about
    retyping.
    """
    assert len(CLAUSE) == 28
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
    """Sixteen substantive clauses, eight facts plus one closure, twelve supporting.

    The counts are derived from the composition and the manifest independently
    and then compared, so a clause represented twice, a clause dropped, or a
    clause silently reclassified fails by name.
    """
    assert len(SUBSTANTIVE_CLAUSES) == 16
    assert len(set(SUBSTANTIVE_CLAUSES)) == 16
    assert len(COMPOSITION) == 8
    assert len(SUPPORTING_CLAUSES) == 12
    assert len(set(SUPPORTING_CLAUSES)) == 12
    assert set(SUBSTANTIVE_CLAUSES) | set(SUPPORTING_CLAUSES) == set(CLAUSE)
    assert not set(SUBSTANTIVE_CLAUSES) & set(SUPPORTING_CLAUSES)

    # Both printings are represented, and neither site is decorative: the
    # glossary alone cannot state the batch and neither can the combat chapter.
    sites = {clause: CLAUSE[clause]["site"] for clause in SUBSTANTIVE_CLAUSES}
    assert set(sites.values()) == {"glossary", "combat"}


def test_the_doubly_printed_rules_are_one_fact_with_both_sites_claiming_it() -> None:
    """Four rules printed twice, represented once, and cited to both printings.

    This is the distinction the whole composition turns on. The source printed
    one rule in two chapters; representing it twice would publish two claims
    where the source made one, and representing it once from a single site
    would drop half its authority. Provenance is per span, so one target
    claimed by two spans is the ordinary shape rather than a workaround.
    """
    both = {
        clauses
        for _, _, clauses in COMPOSITION
        if {CLAUSE[c]["site"] for c in clauses} == {"glossary", "combat"}
    }
    assert both == {
        ("glossary/1/2", "combat/6/0"),
        ("glossary/1/3", "combat/8/0"),
        ("glossary/1/4", "combat/11/0"),
        ("glossary/1/5", "combat/1/3"),
    }

    # Each of those eight spans is a PRIMARY claim on the same fact target, and
    # the validator is the thing that says so rather than this arithmetic.
    draft = _draft()
    for clauses in sorted(both):
        targets = {
            claim.target_key
            for claim in draft.provenance
            if claim.span_id in {_span_id(c) for c in clauses}
            and claim.role is ProvenanceRole.PRIMARY
        }
        assert len(targets) == 1, clauses
    assert validate_representation(draft, _ledger(), _corpus()) == ()


def test_the_closure_statement_is_carried_by_a_component_not_a_fact() -> None:
    """ "There are three degrees of cover" is about no single fact, and says so.

    The sentence states the closure of a vocabulary. There is no vocabulary
    target kind, so read as substantive with nothing to claim it the span would
    trip the unclaimed-substantive rule; invented as a cardinality fact it
    would put a second, weaker statement of the enum next to the enum itself.
    A component-level PRIMARY claim is the carrier that already exists, and the
    closure it names is the closure ``CoverDegree`` actually has.
    """
    draft = _draft()
    (claim,) = [
        c
        for c in draft.provenance
        if c.span_id == _span_id(CLOSURE_CLAUSE) and c.role is ProvenanceRole.PRIMARY
    ]
    assert claim.target_kind is ProvenanceTargetKind.COMPONENT
    assert claim.target_key == (COVER, BENEFIT)

    # Three degrees, and the component it claims carries exactly three
    # benefits — one per degree, no degree twice and none missing.
    assert {member.value for member in CoverDegree} == {
        "half",
        "three_quarters",
        "total",
    }
    benefits = FACTS_BY_COMPONENT[BENEFIT]
    assert len(benefits) == 3
    assert {f.degree for f in benefits} == set(CoverDegree)

    # And the combat printing defers rather than states, so it supports the
    # same component instead of claiming it.
    assert (BENEFIT, "combat/1/1") in COMPONENT_CONTEXT
    assert "As detailed in the Cover table" in str(CLAUSE["combat/1/1"]["text"])


def test_the_mint_declares_five_families_eight_vocabularies_and_one_member() -> None:
    """The extension claim, stated where the schema hash covers it.

    Emitted by the schema payload, so this is not prose about the delta — a
    sixth family, a ninth vocabulary or any other widened accepted vocabulary
    would land a row here and fail. ``CoverDegree`` is the one vocabulary
    schema 10 widens rather than mints, and it appears with exactly the one
    member it gains.
    """
    rows = [
        row
        for row in introduction_manifest()
        if row["introduced_in"] == SCHEMA_10_VERSION
    ]
    assert {row["name"] for row in rows if row["kind"] == "fact_family"} == {
        family.value
        for family in (
            FactFamily.COVER_DEFENSIVE_BONUS,
            FactFamily.COVER_TARGETING_PROHIBITION,
            FactFamily.COVER_PROVISION,
            FactFamily.COVER_BENEFIT_ORIGIN,
            FactFamily.COVER_DEGREE_SELECTION,
        )
    }, rows
    members = [row for row in rows if row["kind"] == "vocabulary_member"]
    vocabularies = {tuple(row["vocabulary"]) for row in members}
    assert len(vocabularies) == 9, sorted(vocabularies)

    # Eight closed vocabularies minted whole, plus ``CoverDegree`` contributing
    # ``half`` alone — schema 6 minted the other two and this is a widening,
    # not a second declaration of the same closure.
    (widened,) = [row for row in members if tuple(row["vocabulary"]) == ("half",)] or [
        row for row in members if row["name"] == "half"
    ]
    assert widened["name"] == "half"
    assert {row["kind"] for row in rows} == {"fact_family", "vocabulary_member"}, rows

    # The pin this module is written against is the live one.
    assert REPRESENTATION_SCHEMA_VERSION == SCHEMA_10_VERSION
    assert representation_schema_hash() == SCHEMA_10_HASH


def test_the_crossing_from_schema_9_is_exactly_one_registered_step() -> None:
    """One step, looked up rather than named, in the direction it applies."""
    steps = lift_path(
        (SCHEMA_9_VERSION, SCHEMA_9_HASH),
        (SCHEMA_10_VERSION, SCHEMA_10_HASH),
    )
    assert [step.lift_id for step in steps] == ["5d-lift-schema-9-to-10"]


# ---------------------------------------------------------------------------
# The six gaps, one case each
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fact",
    [entry[1] for entry in COMPOSITION],
    ids=[entry[2][0] for entry in COMPOSITION],
)
def test_each_fact_is_well_formed_and_round_trips(fact: MechanicalFact) -> None:
    """Every clause's fact, through the canonical payload and back."""
    assert fact_invariant_violations(fact) == ()
    payload = fact_payload(fact)
    rebuilt = fact_from_payload(payload)
    assert rebuilt == fact
    assert fact_payload(rebuilt) == payload


def test_g1_half_is_a_member_of_the_vocabulary_accepted_authority_consumes() -> None:
    """The widening, in the one place it has to be true: the same enum.

    ``Applicability.cover`` and ``BlockedLineExclusionFact.blocking_cover``
    already read ``CoverDegree`` in accepted authority. Adding ``half`` as a
    second vocabulary — or as a record — would put one distinction in two
    places at once, so the test that matters is that the consumers see the
    widened enum and nothing else changed about them.
    """
    assert CoverDegree.HALF.value == "half"
    applicability = Applicability(kind=ApplicabilityKind.COVER, cover=CoverDegree.HALF)
    assert applicability.cover is CoverDegree.HALF
    blocked = BlockedLineExclusionFact(
        blocked=BlockedLineQuantifier.ALL_STRAIGHT_LINES_FROM_THE_POINT_OF_ORIGIN,
        blocking_cover=CoverDegree.HALF,
    )
    assert fact_invariant_violations(blocked) == ()

    # The two members the accepted batches were accepted under are untouched.
    assert CoverDegree.THREE_QUARTERS.value == "three_quarters"
    assert CoverDegree.TOTAL.value == "total"


def test_g2_the_defensive_benefit_keeps_its_conjunction_and_its_amount() -> None:
    """ "+2 bonus to AC **and** Dexterity saving throws" is one rule, not two.

    Both halves are keyed to the degree in one fact. A shape that stated only
    the saving-throw half — the one ``RollSpec`` could already have carried —
    would have dropped AC silently, and a shape that split them into two facts
    with no shared degree would have let one drift from the other.
    """
    half, three_quarters = (
        f for _, f, _ in COMPOSITION if f.FAMILY is FactFamily.COVER_DEFENSIVE_BONUS
    )
    assert (half.degree, half.bonus) == (CoverDegree.HALF, 2)
    assert (three_quarters.degree, three_quarters.bonus) == (
        CoverDegree.THREE_QUARTERS,
        5,
    )
    for fact in (half, three_quarters):
        assert fact.to_defense is CoverDefense.ARMOR_CLASS
        assert fact.to_saving_throw is AbilityScore.DEXTERITY

    # The amounts are the printed ones and the degrees are distinguished by
    # them, so a swap is a different composition rather than a reformat.
    assert fact_payload(half) != fact_payload(three_quarters)


def test_g3_total_covers_benefit_is_a_prohibition_on_direct_targeting() -> None:
    """Not a bonus of zero, and not a prohibition on everything.

    "Directly" is printed and load bearing. A family that dropped it would
    state a stronger rule than the source — that a target behind Total Cover
    cannot be affected at all — and a bonus-shaped encoding would claim Total
    Cover modifies AC, which it does not.
    """
    (fact,) = (
        f
        for _, f, _ in COMPOSITION
        if f.FAMILY is FactFamily.COVER_TARGETING_PROHIBITION
    )
    assert fact.degree is CoverDegree.TOTAL
    assert fact.prohibits is TargetingProhibition.DIRECT_TARGETING
    assert TargetingProhibition.DIRECT_TARGETING.value == "direct_targeting"
    assert [m.value for m in TargetingProhibition] == ["direct_targeting"]

    # No degree carries both a bonus and the prohibition, and no degree carries
    # neither: each of the three has exactly one benefit.
    benefits = FACTS_BY_COMPONENT[BENEFIT]
    assert [f.degree for f in benefits] == [
        CoverDegree.HALF,
        CoverDegree.THREE_QUARTERS,
        CoverDegree.TOTAL,
    ]


def test_g4_the_offeror_asymmetry_and_the_three_thresholds_are_preserved() -> None:
    """Half admits a creature or an object; the other two admit an object only.

    The asymmetry is printed, in three separate table cells, and a shared
    offeror member would have erased it. The thresholds are the source's three
    printed phrases, which is sufficient rather than obligatory: an exact
    numeric pair would state them faithfully too, but the page prints exactly
    three, each carries its comparison inside the phrase, and "the whole" is
    not "at least the whole".
    """
    provisions = {f.degree: f for f in FACTS_BY_COMPONENT[PROVISION]}
    assert set(provisions) == set(CoverDegree)
    assert (
        provisions[CoverDegree.HALF].offered_by
        is CoverOfferor.ANOTHER_CREATURE_OR_AN_OBJECT
    )
    assert provisions[CoverDegree.THREE_QUARTERS].offered_by is CoverOfferor.AN_OBJECT
    assert provisions[CoverDegree.TOTAL].offered_by is CoverOfferor.AN_OBJECT

    assert provisions[CoverDegree.HALF].coverage is CoverageThreshold.AT_LEAST_HALF
    assert (
        provisions[CoverDegree.THREE_QUARTERS].coverage
        is CoverageThreshold.AT_LEAST_THREE_QUARTERS
    )
    assert provisions[CoverDegree.TOTAL].coverage is CoverageThreshold.WHOLE_TARGET

    # Three thresholds, three degrees, and no fourth of either: the vocabulary
    # is closed at what the table prints.
    assert len(set(CoverageThreshold)) == 3
    assert len(set(CoverOfferor)) == 2


def test_g5_the_benefit_applies_only_against_the_opposite_side() -> None:
    """Printed at one site only, and it qualifies every degree rather than one.

    The combat chapter states it; the glossary does not. That is why the fact
    carries a single clause id and why it lives in its own component instead of
    being attached to a degree — attaching it to one would have implied the
    other two benefit regardless of where an attack came from.
    """
    (fact,) = FACTS_BY_COMPONENT[ORIGIN]
    assert fact.interaction is CoveredInteraction.AN_ATTACK_OR_OTHER_EFFECT
    assert fact.requires_origin is BenefitOriginSide.OPPOSITE_SIDE_OF_THE_COVER

    (entry,) = [c for c, _, _ in COMPOSITION if c == ORIGIN]
    (clauses,) = [cl for c, _, cl in COMPOSITION if c == ORIGIN]
    assert entry == ORIGIN
    assert clauses == ("combat/1/2",)
    assert CLAUSE["combat/1/2"]["site"] == "combat"
    assert not any(
        CLAUSE[c]["site"] == "glossary"
        for _, f, cl in COMPOSITION
        if f.FAMILY is FactFamily.COVER_BENEFIT_ORIGIN
        for c in cl
    )


def test_g6_the_most_protective_degree_applies_and_degrees_do_not_sum() -> None:
    """One rule with two printed halves, and no rank invented to implement it.

    The glossary prints the selection; the combat chapter prints the selection
    *and* the non-summing restatement. Both are the same rule, so both fields
    sit on one fact and both spans claim it. What the record does not do is
    order the three degrees: "most protective" is named, not computed, and
    deciding which degrees apply in a scene is runtime.
    """
    (fact,) = FACTS_BY_COMPONENT[SELECTION]
    assert fact.selects is CoverDegreeSelection.MOST_PROTECTIVE
    assert fact.combination is CoverDegreeCombination.NOT_ADDED_TOGETHER
    assert [m.value for m in CoverDegreeSelection] == ["most_protective"]
    assert [m.value for m in CoverDegreeCombination] == ["not_added_together"]

    # No rank, no ordinal, no comparison: the payload names members and nothing
    # that could be evaluated.
    payload = fact_payload(fact)
    assert set(payload) == {"family", "selects", "combination"}

    # The worked example bounds the fact rather than becoming a second one.
    assert [clause for _, _, clause in FACT_CONTEXT] == ["combat/1/4"]
    assert "For example" in str(CLAUSE["combat/1/4"]["text"])


# ---------------------------------------------------------------------------
# Fail closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "",
        "quarter",
        "three_quarter",
        "HALF",
        "at_least_half",
        "Half",
    ],
)
def test_a_degree_outside_the_closure_is_refused_rather_than_repaired(
    value: str,
) -> None:
    """The printed vocabulary has three members and admits nothing adjacent.

    ``at_least_half`` is in the list on purpose: it is a real member of a
    *different* schema-10 vocabulary, and the two closing over similar words is
    exactly the confusion a closed enum has to refuse rather than coerce.
    """
    payload = dict(fact_payload(FACTS_BY_COMPONENT[PROVISION][0])) | {"degree": value}
    with pytest.raises(Exception) as raised:
        fact_from_payload(payload)
    assert "degree" in str(raised.value), raised.value


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("offered_by", "a_creature"),
        ("offered_by", "another_creature"),
        ("coverage", "at_least_the_whole_target"),
        ("coverage", "half"),
        ("prohibits", "targeting"),
        ("to_defense", "armour_class"),
        ("to_saving_throw", "dexterity_saving_throw"),
        ("interaction", "an_attack"),
        ("requires_origin", "the_other_side"),
        ("selects", "the_best"),
        ("combination", "added_together"),
    ],
)
def test_a_member_outside_any_closure_is_refused(field: str, value: str) -> None:
    """Every schema-10 vocabulary, probed with a plausible near-miss.

    Each rejected value is a reading a looser representation would have
    admitted, and each states a different rule from the printed one —
    ``an_attack`` drops "or other effect", ``added_together`` inverts the rule
    it is named after, ``at_least_the_whole_target`` weakens a threshold the
    source prints as exact.
    """
    fact = next(f for _, f, _ in COMPOSITION if field in fact_payload(f))
    payload = dict(fact_payload(fact)) | {field: value}
    with pytest.raises(Exception) as raised:
        fact_from_payload(payload)
    assert field in str(raised.value), raised.value


def test_a_bonus_that_is_not_an_integer_is_refused() -> None:
    """The amount is a printed integer, and the payload door is typed for it."""
    payload = dict(fact_payload(FACTS_BY_COMPONENT[BENEFIT][0])) | {"bonus": "+2"}
    with pytest.raises(Exception) as raised:
        fact_from_payload(payload)
    assert "bonus" in str(raised.value), raised.value


def test_an_unknown_family_is_refused_rather_than_guessed() -> None:
    """A family name that is not declared has no builder and gets none."""
    payload = dict(fact_payload(FACTS_BY_COMPONENT[SELECTION][0])) | {
        "family": "cover_degree_ranking"
    }
    with pytest.raises(UnknownFactFamilyError):
        fact_from_payload(payload)


def test_schema_9_cannot_state_any_of_it() -> None:
    """The succession is real in the refusing direction too.

    Every one of the eight facts is meaning schema 9's declared contract cannot
    carry, and the composed draft as a whole is refused under it. A family
    schema 9 could already have stated would pass here, and would mean the mint
    was unnecessary.
    """
    for component_key, fact, clauses in COMPOSITION:
        one = RepresentationDraft(
            records=(RecordDraft(semantic_key=COVER, kind=RecordKind.GLOSSARY_RULE),),
            components=(
                ComponentDraft(
                    record_key=COVER,
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
        assert declared_meaning_violations(one, SCHEMA_9_VERSION), clauses
    assert declared_meaning_violations(_draft(), SCHEMA_9_VERSION)
    assert declared_meaning_violations(_draft(), REPRESENTATION_SCHEMA_VERSION) == []


@pytest.mark.parametrize("version", [SCHEMA_6_VERSION, SCHEMA_9_VERSION])
def test_an_earlier_contract_refuses_the_half_member_it_never_registered(
    version: str,
) -> None:
    """The widening is refused by *member*, on the fields that already existed.

    Both shapes use a field an earlier contract already declared, and they do
    not come from the same one: ``Applicability.cover`` arrived at schema 6,
    ``BlockedLineExclusionFact.blocking_cover`` at schema 9. Neither earlier
    contract may admit ``half``, because schema 6 registered
    ``three_quarters`` and ``total`` and nothing else and schema 9 added no
    member to that vocabulary. This is what makes the schema-6 registry row a
    frozen pair rather than whatever the live enum happens to hold.
    """
    blocked = BlockedLineExclusionFact(
        blocked=BlockedLineQuantifier.ALL_STRAIGHT_LINES_FROM_THE_POINT_OF_ORIGIN,
        blocking_cover=CoverDegree.HALF,
    )
    draft = RepresentationDraft(
        records=(RecordDraft(semantic_key=COVER, kind=RecordKind.GLOSSARY_RULE),),
        components=(
            ComponentDraft(
                record_key=COVER,
                semantic_key="blocked_lines",
                handling=ComponentHandling.STRUCTURED,
                facts=(blocked,),
                applies_when=Applicability(
                    kind=ApplicabilityKind.COVER, cover=CoverDegree.HALF
                ),
            ),
        ),
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )
    assert declared_meaning_violations(draft, version)
    # And schema 10 admits exactly the same shape, so the refusal above is
    # about the member rather than about the fields carrying it.
    assert declared_meaning_violations(draft, REPRESENTATION_SCHEMA_VERSION) == []


def test_an_unminted_version_is_refused() -> None:
    """Schema 11 does not exist, and the payload seam says so rather than guessing.

    Version legality is not ``declared_meaning_violations``'s question — it
    answers what a *recognised* schema can state. The emitter is where an
    unrecognised version is refused, and it has to stay refused now that
    ``…-10`` is real: the probe moves to the next unminted string rather than
    the assertion being retired.
    """
    with pytest.raises(UnsupportedSchemaVersionError):
        representation_payload(_draft(), schema_version="5d-representation-schema-11")
    # And the live version is emitted without complaint.
    assert representation_payload(
        _draft(), schema_version=REPRESENTATION_SCHEMA_VERSION
    ) == representation_payload(_draft())


# ---------------------------------------------------------------------------
# Validation, persistence, identity
# ---------------------------------------------------------------------------


def test_the_composition_validates_with_no_residue_at_all() -> None:
    """One entry, twenty-eight clauses, and nothing outstanding.

    ``areas-of-effect-1`` left one finding behind — its *See also* cited
    ``Cover`` and cover ingestion was not in that batch. This batch closes that
    target and opens none of its own: its only citation names a chapter, for
    which there is no record, so it is record-owned supporting authority rather
    than a reference that could dangle. Asserting the empty tuple exactly is
    what keeps a finding from hiding behind a filter.
    """
    assert validate_representation(_draft(), _ledger(), _corpus()) == ()
    assert _draft().references == ()


def test_the_chapter_navigation_is_supporting_authority_not_a_reference() -> None:
    """The one citation the population prints, at the scope it actually holds.

    *"Playing the Game" ("Combat")* names a section and a subsection. Every
    accepted reference targets a record key and there is no record for a
    chapter; it also points at this record's own second site, so a reference
    would be self-directed even if a target existed. It is carried as
    record-level supporting authority, with the *See also* label beside it.
    """
    assert "glossary/3/0" in RECORD_CONTEXT
    assert "glossary/2/0" in RECORD_CONTEXT
    assert str(CLAUSE["glossary/2/0"]["text"]) == "See also"
    navigation = str(CLAUSE["glossary/3/0"]["text"])
    assert "Playing the Game" in navigation and "Combat" in navigation

    # Both are claimed, at CONTEXTUAL, by the record and by nothing else.
    draft = _draft()
    for clause in ("glossary/2/0", "glossary/3/0"):
        (claim,) = [c for c in draft.provenance if c.span_id == _span_id(clause)]
        assert claim.target_kind is ProvenanceTargetKind.RECORD
        assert claim.role is ProvenanceRole.CONTEXTUAL


def test_the_whole_composition_survives_persistence_and_reconstruction(
    session: Session,
) -> None:
    """Typed rows in, typed rows out, and the same identity on the far side.

    Reconstruction reads the database and nothing else, so a family the store
    cannot round trip fails here rather than the first time a real corpus
    carries it. The multi-fact components are the load-bearing part: fact order
    inside a component has to survive, because two bonuses that swapped degrees
    would be a different rule.
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
            by_key[(COVER, component_key)].facts == FACTS_BY_COMPONENT[component_key]
        ), component_key
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid


@pytest.mark.parametrize(
    ("component_key", "changed", "why"),
    [
        (
            BENEFIT,
            (
                CoverDefensiveBonusFact(
                    degree=CoverDegree.HALF,
                    bonus=5,
                    to_defense=CoverDefense.ARMOR_CLASS,
                    to_saving_throw=AbilityScore.DEXTERITY,
                ),
            ),
            "giving Half Cover the Three-Quarters bonus",
        ),
        (
            BENEFIT,
            (
                CoverDefensiveBonusFact(
                    degree=CoverDegree.HALF,
                    bonus=2,
                    to_defense=CoverDefense.ARMOR_CLASS,
                    to_saving_throw=AbilityScore.STRENGTH,
                ),
            ),
            "moving the saving-throw half off Dexterity",
        ),
        (
            PROVISION,
            (
                CoverProvisionFact(
                    degree=CoverDegree.THREE_QUARTERS,
                    offered_by=CoverOfferor.ANOTHER_CREATURE_OR_AN_OBJECT,
                    coverage=CoverageThreshold.AT_LEAST_THREE_QUARTERS,
                ),
            ),
            "letting a creature offer Three-Quarters Cover",
        ),
        (
            PROVISION,
            (
                CoverProvisionFact(
                    degree=CoverDegree.TOTAL,
                    offered_by=CoverOfferor.AN_OBJECT,
                    coverage=CoverageThreshold.AT_LEAST_THREE_QUARTERS,
                ),
            ),
            "lowering Total Cover's threshold below the whole target",
        ),
        (
            SELECTION,
            (
                CoverDegreeSelectionFact(
                    selects=CoverDegreeSelection.MOST_PROTECTIVE,
                    combination=CoverDegreeCombination.NOT_ADDED_TOGETHER,
                ),
                CoverDegreeSelectionFact(
                    selects=CoverDegreeSelection.MOST_PROTECTIVE,
                    combination=CoverDegreeCombination.NOT_ADDED_TOGETHER,
                ),
            ),
            "stating the same rule twice because it is printed twice",
        ),
    ],
)
def test_a_changed_meaning_changes_the_projection_identity(
    component_key: str, changed: tuple[MechanicalFact, ...], why: str
) -> None:
    """Each perturbation is a different rule, so each is a different identity.

    Identity is computed over the canonical payload, so this is the mechanism
    that stops any of these from passing as a reformat of the accepted one.
    The last case is the composition decision itself: representing a
    doubly-printed rule twice is a different projection, not a presentation
    choice.
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
    """Five batches, their acceptances, their provenance and their anchors.

    The crossing rebinds and does not rebuild. What matters most for *this*
    succession is the anchors: schema 10 is the first step since schema 6 to
    widen a vocabulary an accepted batch already uses — ``areas-of-effect-1``
    states ``CoverDegree.TOTAL`` under schema 9 — so a lift that re-derived
    anchors would erase the record of what each batch was accepted under. Each
    anchor keeps the version and hash it was accepted at, and the only thing
    that moves is the oracle's own binding.
    """
    inputs = load_accepted_inputs(FROZEN_PRIOR)
    before_identity = oracle_identity(inputs.oracle)
    current = (REPRESENTATION_SCHEMA_VERSION, representation_schema_hash())
    lifted, records = lift_accepted_inputs(inputs, current)
    assert [r.lift_id for r in records] == ["5d-lift-schema-9-to-10"]

    # Collections cross by identity, not by rebuild.
    assert lifted.batches is inputs.batches
    assert lifted.acceptances is inputs.acceptances
    assert lifted.schema_anchors is inputs.schema_anchors
    assert lifted.oracle.representation is inputs.oracle.representation
    assert lifted.oracle.spans is inputs.oracle.spans
    assert lifted.oracle.obligations is inputs.oracle.obligations

    # The five anchors keep the five declarations they were accepted under —
    # none of which is schema 10.
    anchored = {
        a.batch_id: (a.schema_version, a.schema_hash) for a in lifted.schema_anchors
    }
    assert set(anchored) == {
        "conditions-1",
        "hazards-1",
        "actions-1",
        "attitudes-1",
        "areas-of-effect-1",
    }
    assert anchored["areas-of-effect-1"] == (SCHEMA_9_VERSION, SCHEMA_9_HASH)
    assert SCHEMA_10_VERSION not in {version for version, _ in anchored.values()}

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

    One record, four structured components, no governing prose anywhere: the
    whole entry arrives as declared enum members with span ids for provenance,
    which is the entire consumer-visible effect of this mint.
    """
    records = _base_records(candidate_of(RELEASE_BINDING, _ledger(), _draft()))
    assert set(records) == {COVER}
    by_key = {c.semantic_key: c for c in records[COVER].components}
    assert set(by_key) == set(COMPONENTS)

    for component_key in COMPONENTS:
        component = by_key[component_key]
        assert component.handling is ComponentHandling.STRUCTURED
        assert component.irreducibility_reason_code is None
        assert component.governing_prose == ()
        assert [entry.fact for entry in component.facts] == list(
            FACTS_BY_COMPONENT[component_key]
        )

    # Each fact carries the spans that state it — both sites where the source
    # printed it twice, plus whatever supporting clause bounds it.
    for component_key, fact, clauses in COMPOSITION:
        (entry,) = [e for e in by_key[component_key].facts if e.fact == fact]
        expected = {_span_id(c) for c in clauses} | {
            _span_id(c)
            for key, f, c in FACT_CONTEXT
            if (key, f) == (component_key, fact)
        }
        assert set(entry.span_ids) == expected, clauses


def test_the_typed_view_carries_every_family_and_every_fact() -> None:
    """The deterministic consumer's whole reading of the entry."""
    typed = {r.semantic_key: r for r in build_typed_view(_authority()).records}
    assert set(typed) == {COVER}
    seen = [
        entry.fact
        for record in typed.values()
        for component in record.components
        for entry in component.facts
    ]
    assert len(seen) == 8
    assert {fact.FAMILY for fact in seen} == {
        FactFamily.COVER_DEFENSIVE_BONUS,
        FactFamily.COVER_TARGETING_PROHIBITION,
        FactFamily.COVER_PROVISION,
        FactFamily.COVER_BENEFIT_ORIGIN,
        FactFamily.COVER_DEGREE_SELECTION,
    }
    for _, fact, _ in COMPOSITION:
        assert fact in seen


def test_the_gamemaster_view_names_the_clauses_without_delivering_them() -> None:
    """Structured components have no prose to resolve, and that is the point.

    Every component here is ``STRUCTURED``, so the GameMaster view resolves no
    governing prose at all: each rule arrives as its vocabulary members, and
    the sentence it came from arrives as a span id a reader can look up. The
    printed clause text is never carried in the view — which is what keeps
    licensed source text out of a projection that only needs to cite it, and it
    matters more here than in any previous batch because two of these clauses
    are worked examples a view would be tempted to quote.
    """
    view = build_gamemaster_view(_authority(), PROSE)
    assert {c.record_key for c in view.components} == {COVER}
    assert len(view.components) == 4
    for component in view.components:
        assert component.governing_prose == ()
        assert component.structured_context != ()
        for entry in component.structured_context:
            assert entry.span_ids != ()
    # Two components carry component-level spans -- the benefit column, which
    # the closure sentence and its header claim, and the provision column with
    # its header -- and they arrive as ids, never as text.
    assert {c.component_key for c in view.components if c.span_ids} == {
        BENEFIT,
        PROVISION,
    }
    rendered = str(view)
    for clause_id in SUBSTANTIVE_CLAUSES:
        assert str(CLAUSE[clause_id]["text"]).strip() not in rendered, clause_id
    assert str(CLAUSE["combat/1/4"]["text"]).strip() not in rendered
