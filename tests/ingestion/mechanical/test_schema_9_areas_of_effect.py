"""Schema 9's seven families, against the class that forced them — CRD Issue 5d.

The Rules Glossary's **Area of Effect** class is seven entries — the umbrella
(p176) and the six shapes it names (pp178–187) — printing forty-three clauses.
Nineteen are supporting authority; twenty-four state mechanics schema 8 had no
shape for, and no composition of accepted families says any of them: a point of
origin is not an effect, a duration, an allowance, a roll, a state transition or
a default. Contract 3's other branch is unavailable too, because none of the six
closed irreducibility reasons is affirmatively true of any of the twenty-four.

So schema 9 adds seven families over eleven closed vocabularies, one family per
distinct printed rule, and this module is the executable half of that decision:

* **the inventory is the reviewed one** — every clause below is read out of the
  committed discovery manifest rather than retyped, and each one's extent is
  checked against the leaf text it was cut from, so a clause that drifted from
  the reviewed inventory fails here instead of being quietly re-authored;
* **the composition is exact** — twenty-three facts over the twenty-four
  substantive clauses, with the two that jointly state the blocked-line rule
  landing on one fact, and every supporting clause linked to the element it
  actually supports;
* **the distinctions the source prints survive** — per-shape placement and
  extent, Emanation's creature-or-object origin beside the general point of
  origin, parameter names and arity in printed order, creator-controlled
  inclusion, the Cone width relation, both Emanation movement exceptions, the
  *all*-lines quantifier with Total Cover as its threshold, and the
  unseen-origin conjunction with its near-side result;
* **the wire and the store hold** — canonical round trip per fact, and the whole
  composition persisted and reconstructed from typed rows alone;
* **meaning changes identity** — a different vocabulary member, a different
  cover degree, or the same two dimensions in the other order are each a
  different payload and a different projection identity; and
* **earlier and malformed declarations fail closed** — schema 8 refuses every
  one of the twenty-three facts, and the quantifier, the conjunction and the
  order-bearing tuples refuse the shapes that would blur them.

**Limits, stated so this is not read for more than it proves.** This is a
demonstration against the contract schema 9 now states — not a proposal and not
an acceptance. The chunk ids and release binding below are this module's own;
the leaf ids, clause extents and clause text are the source's, taken from the
manifest. No parameter *value*, unit, coordinate or grid semantic appears
anywhere here, because the source prints none: a Cone's maximum length is a
name the creating effect supplies, and this schema says only that. ``Cover`` is
cited and left unresolved — cover ingestion is not in this batch.
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
from afterworlds.ingestion.mechanical.persistence import (
    persist_draft,
    reconstruct_candidate,
)
from afterworlds.ingestion.mechanical.projection import (
    identify_projection,
    representation_payload,
)
from afterworlds.ingestion.mechanical.representation import (
    RECORD_OWNED_REFERENCE,
    REPRESENTATION_SCHEMA_VERSION,
    AreaDimension,
    AreaDimensionRequirementFact,
    AreaExtentPattern,
    AreaMovementSuspension,
    AreaOriginFact,
    AreaOriginInclusion,
    AreaOriginInclusionFact,
    AreaOriginKind,
    AreaOriginMovementFact,
    AreaOriginPlacement,
    AreaWidthRelation,
    AreaWidthRelationFact,
    BlockedLineExclusionFact,
    BlockedLineQuantifier,
    ComponentDraft,
    ComponentHandling,
    CoverDegree,
    FactFamily,
    InterveningObstruction,
    MechanicalFact,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RelocatedOrigin,
    RepresentationDraft,
    UnseenOriginRelocationFact,
    UnseenPlacement,
    declared_meaning_violations,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
    fact_target_key,
    introduction_manifest,
    reference_target_key,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_8_HASH,
    SCHEMA_8_VERSION,
    SCHEMA_9_HASH,
    SCHEMA_9_VERSION,
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
    / "issue-5d-areas-of-effect-1-source-manifest.json"
)
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

#: ``leaf_id -> printed leaf text``, and one chunk per leaf covering it whole,
#: so chunk offsets are leaf offsets and a chunk-locality finding means what it
#: says.
LEAVES: dict[str, str] = {
    leaf["leaf_id"]: leaf["content"]
    for record in MANIFEST["records"]
    for leaf in record["leaves"]
}
CHUNKS = {leaf_id: f"chunk-{leaf_id}" for leaf_id in LEAVES}

#: ``clause_id -> the manifest's clause row``. Keyed by the reviewed clause id,
#: which is how every composition below names the clause it is standing on.
CLAUSE = {clause["clause_id"]: clause for clause in MANIFEST["clauses"]}

SCOPE = "srd-5.2.1/rules-glossary"

UMBRELLA = "glossary.area_of_effect"
CONE = "area_of_effect.cone"
CUBE = "area_of_effect.cube"
CYLINDER = "area_of_effect.cylinder"
EMANATION = "area_of_effect.emanation"
LINE = "area_of_effect.line"
SPHERE = "area_of_effect.sphere"
COVER = "glossary.cover"

RECORDS = (UMBRELLA, CONE, CUBE, CYLINDER, EMANATION, LINE, SPHERE)


def _leaf(clause_id: str) -> str:
    return str(CLAUSE[clause_id]["leaf_id"])


def _extent(clause_id: str) -> tuple[int, int]:
    row = CLAUSE[clause_id]
    return int(row["char_start"]), int(row["char_end"])


def _span_id(clause_id: str) -> str:
    return derive_span_id(_leaf(clause_id), *_extent(clause_id))


# ---------------------------------------------------------------------------
# The twenty-four substantive clauses, as twenty-three facts
# ---------------------------------------------------------------------------
#
# One component per family per record, named for the rule it holds. Every fact
# names the clause ids it is the representation of; the blocked-line rule names
# two, because the source states the exclusion in one sentence and the
# threshold that makes a line blocked in the next.

ORIGIN = "area_origin"
DIMENSIONS = "area_dimension_requirement"
INCLUSION = "area_origin_inclusion"
WIDTH = "area_width_relation"
MOVEMENT = "area_origin_movement"
BLOCKED = "blocked_line_exclusion"
UNSEEN = "unseen_origin_relocation"

EXCLUDED = AreaOriginInclusion.EXCLUDED_UNLESS_ITS_CREATOR_DECIDES_OTHERWISE
ALL_BLOCKED = BlockedLineQuantifier.ALL_STRAIGHT_LINES_FROM_THE_POINT_OF_ORIGIN
LINE_EXTENT = (
    AreaExtentPattern.STRAIGHT_PATH_ALONG_ITS_LENGTH_COVERING_THE_AREA_ITS_WIDTH_DEFINES
)
CONE_WIDTH = AreaWidthRelation.EQUAL_TO_THAT_POINTS_DISTANCE_FROM_THE_POINT_OF_ORIGIN

#: ``(record, component, fact, clause ids)`` — the whole substantive
#: composition, in printed order, record by record.
COMPOSITION: tuple[tuple[str, str, MechanicalFact, tuple[str, ...]], ...] = (
    # -- Area of Effect (p176): the general rules every shape inherits --------
    # "An area of effect has a point of origin, a location from which the
    # effect's energy erupts." The umbrella states *that* there is a point of
    # origin and nothing about how it extends or where it sits, so extent and
    # placement are unstated here rather than guessed from the shapes.
    (
        UMBRELLA,
        ORIGIN,
        AreaOriginFact(origin=AreaOriginKind.POINT),
        ("Area of Effect/5/0",),
    ),
    # "If all straight lines extending from the point of origin to a location
    # in the area of effect are blocked, that location isn't included in the
    # area of effect." + "To block a line, an obstruction must provide Total
    # Cover." Two clauses, one rule: the quantifier and the threshold that
    # makes the quantifier mean anything.
    (
        UMBRELLA,
        BLOCKED,
        BlockedLineExclusionFact(blocked=ALL_BLOCKED, blocking_cover=CoverDegree.TOTAL),
        ("Area of Effect/5/2", "Area of Effect/5/3"),
    ),
    # "If the creator of an area of effect places it at an unseen point and an
    # obstruction—such as a wall— is between the creator and that point, the
    # point of origin comes into being on the near side of the obstruction."
    (
        UMBRELLA,
        UNSEEN,
        UnseenOriginRelocationFact(
            placement=UnseenPlacement.AT_AN_UNSEEN_POINT,
            obstruction=InterveningObstruction.BETWEEN_THE_CREATOR_AND_THE_POINT,
            relocated_to=RelocatedOrigin.NEAR_SIDE_OF_THE_OBSTRUCTION,
        ),
        ("Area of Effect/7/1",),
    ),
    # -- Cone (p178) ---------------------------------------------------------
    (
        CONE,
        ORIGIN,
        AreaOriginFact(
            origin=AreaOriginKind.POINT,
            extent=AreaExtentPattern.STRAIGHT_LINES_IN_A_DIRECTION_ITS_CREATOR_CHOOSES,
        ),
        ("Cone/1/0",),
    ),
    (
        CONE,
        WIDTH,
        AreaWidthRelationFact(relation=CONE_WIDTH),
        ("Cone/1/1",),
    ),
    (
        CONE,
        DIMENSIONS,
        AreaDimensionRequirementFact(dimensions=(AreaDimension.MAXIMUM_LENGTH,)),
        ("Cone/1/3",),
    ),
    (CONE, INCLUSION, AreaOriginInclusionFact(inclusion=EXCLUDED), ("Cone/1/4",)),
    # -- Cube (p178) ---------------------------------------------------------
    (
        CUBE,
        ORIGIN,
        AreaOriginFact(
            origin=AreaOriginKind.POINT,
            extent=AreaExtentPattern.STRAIGHT_LINES,
            placement=AreaOriginPlacement.ANYWHERE_ON_A_FACE_OF_THE_CUBE,
        ),
        ("Cube/1/0",),
    ),
    (
        CUBE,
        DIMENSIONS,
        AreaDimensionRequirementFact(
            dimensions=(AreaDimension.SIZE_THE_LENGTH_OF_EACH_SIDE,)
        ),
        ("Cube/1/1",),
    ),
    (CUBE, INCLUSION, AreaOriginInclusionFact(inclusion=EXCLUDED), ("Cube/1/2",)),
    # -- Cylinder (p179) -----------------------------------------------------
    (
        CYLINDER,
        ORIGIN,
        AreaOriginFact(
            origin=AreaOriginKind.POINT,
            extent=AreaExtentPattern.STRAIGHT_LINES,
            placement=AreaOriginPlacement.CENTER_OF_THE_CIRCULAR_TOP_OR_BOTTOM,
        ),
        ("Cylinder/1/0",),
    ),
    # Two parameters, in the order the sentence prints them.
    (
        CYLINDER,
        DIMENSIONS,
        AreaDimensionRequirementFact(
            dimensions=(AreaDimension.RADIUS_OF_THE_BASE, AreaDimension.HEIGHT)
        ),
        ("Cylinder/1/1",),
    ),
    (
        CYLINDER,
        INCLUSION,
        AreaOriginInclusionFact(inclusion=AreaOriginInclusion.INCLUDED),
        ("Cylinder/1/2",),
    ),
    # -- Emanation (p180) ----------------------------------------------------
    # The one shape whose origin is not a point: "extends in straight lines
    # from a creature or an object in all directions."
    (
        EMANATION,
        ORIGIN,
        AreaOriginFact(
            origin=AreaOriginKind.CREATURE_OR_OBJECT,
            extent=AreaExtentPattern.STRAIGHT_LINES_IN_ALL_DIRECTIONS,
        ),
        ("Emanation/1/0",),
    ),
    (
        EMANATION,
        DIMENSIONS,
        AreaDimensionRequirementFact(dimensions=(AreaDimension.DISTANCE_IT_EXTENDS,)),
        ("Emanation/1/1",),
    ),
    # Both printed exceptions, not one: "unless it is an instantaneous or a
    # stationary effect."
    (
        EMANATION,
        MOVEMENT,
        AreaOriginMovementFact(
            suspended_by_any_of=(
                AreaMovementSuspension.INSTANTANEOUS_EFFECT,
                AreaMovementSuspension.STATIONARY_EFFECT,
            )
        ),
        ("Emanation/1/2",),
    ),
    (
        EMANATION,
        INCLUSION,
        AreaOriginInclusionFact(inclusion=EXCLUDED),
        ("Emanation/1/3",),
    ),
    # -- Line (p183) ---------------------------------------------------------
    (
        LINE,
        ORIGIN,
        AreaOriginFact(origin=AreaOriginKind.POINT, extent=LINE_EXTENT),
        ("Line/1/0",),
    ),
    (
        LINE,
        DIMENSIONS,
        AreaDimensionRequirementFact(
            dimensions=(AreaDimension.LENGTH, AreaDimension.WIDTH)
        ),
        ("Line/1/1",),
    ),
    (LINE, INCLUSION, AreaOriginInclusionFact(inclusion=EXCLUDED), ("Line/1/2",)),
    # -- Sphere (p187) -------------------------------------------------------
    (
        SPHERE,
        ORIGIN,
        AreaOriginFact(
            origin=AreaOriginKind.POINT,
            extent=AreaExtentPattern.STRAIGHT_LINES_OUTWARD_IN_ALL_DIRECTIONS,
        ),
        ("Sphere/1/0",),
    ),
    (
        SPHERE,
        DIMENSIONS,
        AreaDimensionRequirementFact(
            dimensions=(AreaDimension.DISTANCE_IT_EXTENDS_AS_THE_RADIUS,)
        ),
        ("Sphere/1/1",),
    ),
    (
        SPHERE,
        INCLUSION,
        AreaOriginInclusionFact(inclusion=AreaOriginInclusion.INCLUDED),
        ("Sphere/1/2",),
    ),
)

#: Every substantive clause id, derived from the composition rather than listed
#: beside it, so a clause represented twice or not at all is visible.
SUBSTANTIVE_CLAUSES = tuple(
    clause for _, _, _, clauses in COMPOSITION for clause in clauses
)


# ---------------------------------------------------------------------------
# The nineteen supporting clauses, each linked to what it actually supports
# ---------------------------------------------------------------------------

#: The umbrella names the six shapes, one clause each, and cites ``Cover`` under
#: *See also*. These are record-owned references — no component of the umbrella
#: states the naming, the record does — which is ``glossary.hazard``'s accepted
#: shape.
CITATIONS: tuple[tuple[str, str, str], ...] = (
    ("Cone", CONE, "Area of Effect/2/0"),
    ("Cube", CUBE, "Area of Effect/2/1"),
    ("Cylinder", CYLINDER, "Area of Effect/3/0"),
    ("Emanation", EMANATION, "Area of Effect/3/1"),
    ("Line", LINE, "Area of Effect/4/0"),
    ("Sphere", SPHERE, "Area of Effect/4/1"),
    # Cited and not defined here: the blocked-line rule leans on Total Cover,
    # and the Cover entry is not in this batch.
    ("Cover", COVER, "Area of Effect/7/0"),
)

REFERENCES = tuple(
    ReferenceDraft(
        from_record_key=UMBRELLA,
        from_component_key=RECORD_OWNED_REFERENCE,
        source_text=text,
        scope_key=SCOPE,
        target_record_key=target,
    )
    for text, target, _ in CITATIONS
)

#: Supporting clauses the *record* carries: each entry's heading, the umbrella's
#: two framing sentences, and the *See also* label.
RECORD_CONTEXT: tuple[tuple[str, str], ...] = (
    (UMBRELLA, "Area of Effect/0/0"),
    (UMBRELLA, "Area of Effect/1/0"),
    (UMBRELLA, "Area of Effect/1/1"),
    (UMBRELLA, "Area of Effect/6/0"),
    (CONE, "Cone/0/0"),
    (CUBE, "Cube/0/0"),
    (CYLINDER, "Cylinder/0/0"),
    (EMANATION, "Emanation/0/0"),
    (LINE, "Line/0/0"),
    (SPHERE, "Sphere/0/0"),
)

#: Supporting clauses a *fact* carries, because they bound that fact and
#: nothing else. "The rules for each shape specify how to position its point of
#: origin." is what makes the umbrella's origin fact silent on placement; the
#: 15-foot worked example illustrates the Cone width relation and states no
#: rule of its own — which is why it is contextual rather than a second fact
#: with an invented value in it.
FACT_CONTEXT: tuple[tuple[str, str, str], ...] = (
    (UMBRELLA, ORIGIN, "Area of Effect/5/1"),
    (CONE, WIDTH, "Cone/1/2"),
)

SUPPORTING_CLAUSES = tuple(
    [clause for _, clause in RECORD_CONTEXT]
    + [clause for _, _, clause in FACT_CONTEXT]
    + [clause for _, _, clause in CITATIONS]
)


# ---------------------------------------------------------------------------
# The composed draft, ledger and corpus
# ---------------------------------------------------------------------------


def _fact_of(record_key: str, component_key: str) -> MechanicalFact:
    (fact,) = [
        f
        for rec, comp, f, _ in COMPOSITION
        if (rec, comp) == (record_key, component_key)
    ]
    return fact


def _draft() -> RepresentationDraft:
    """The seven entries as one draft, with every element's own provenance."""
    components = tuple(
        ComponentDraft(
            record_key=record_key,
            semantic_key=component_key,
            handling=ComponentHandling.STRUCTURED,
            facts=(fact,),
        )
        for record_key, component_key, fact, _ in COMPOSITION
    )
    provenance = (
        tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (record_key,),
                _span_id(clause),
                ProvenanceRole.CONTEXTUAL,
            )
            for record_key, clause in RECORD_CONTEXT
        )
        + tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(record_key, component_key, fact),
                _span_id(clause),
                ProvenanceRole.PRIMARY,
            )
            for record_key, component_key, fact, clauses in COMPOSITION
            for clause in clauses
        )
        + tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(
                    record_key, component_key, _fact_of(record_key, component_key)
                ),
                _span_id(clause),
                ProvenanceRole.CONTEXTUAL,
            )
            for record_key, component_key, clause in FACT_CONTEXT
        )
        + tuple(
            ProvenanceClaim(
                ProvenanceTargetKind.REFERENCE,
                reference_target_key(reference),
                _span_id(clause),
                ProvenanceRole.CONTEXTUAL,
            )
            for reference, (_, _, clause) in zip(REFERENCES, CITATIONS, strict=True)
        )
    )
    return RepresentationDraft(
        records=tuple(
            RecordDraft(semantic_key=key, kind=RecordKind.GLOSSARY_RULE)
            for key in RECORDS
        ),
        components=components,
        prose_bindings=(),
        relationships=(),
        references=REFERENCES,
        provenance=provenance,
    )


def _ledger() -> ClassificationLedger:
    """The batch's own accepted spans, one per printed clause, all forty-three."""
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
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "proj-areas-of-effect-1"),
            override_set_uuid=uuid5(NAMESPACE_URL, "ovs-areas-of-effect-1"),
        ),
        records=tuple(records.values()),
        applied_overrides=(),
    )


#: The authoritative chunk text a GameMaster view resolves prose against.
PROSE = {CHUNKS[leaf]: text for leaf, text in LEAVES.items()}


# ---------------------------------------------------------------------------
# The inventory this module stands on
# ---------------------------------------------------------------------------


def test_every_clause_is_the_text_at_the_extent_the_manifest_records() -> None:
    """The reviewed inventory, checked against the leaves it was cut from.

    Forty-three clauses partitioning twenty leaves end to end. Slicing each leaf
    at the recorded extent has to give back the recorded text, and the extents
    have to tile each leaf without a gap or an overlap — which is what makes
    "the printed clause" a checkable phrase rather than a claim about retyping.
    """
    assert len(CLAUSE) == 43
    assert len(LEAVES) == 20

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


def test_the_class_is_composed_clause_for_clause_with_nothing_left_over() -> None:
    """Twenty-four substantive clauses, twenty-three facts, nineteen supporting.

    The counts are derived from the composition and the manifest independently
    and then compared, so a clause represented twice, a clause dropped, or a
    clause silently reclassified fails by name. The one place the counts differ
    is the blocked-line rule, which the source states across two sentences and
    which is one fact.
    """
    assert len(SUBSTANTIVE_CLAUSES) == 24
    assert len(set(SUBSTANTIVE_CLAUSES)) == 24
    assert len(COMPOSITION) == 23
    assert len(SUPPORTING_CLAUSES) == 19
    assert len(set(SUPPORTING_CLAUSES)) == 19
    assert set(SUBSTANTIVE_CLAUSES) | set(SUPPORTING_CLAUSES) == set(CLAUSE)
    assert not set(SUBSTANTIVE_CLAUSES) & set(SUPPORTING_CLAUSES)

    # The two-clause fact, named rather than inferred from the arithmetic.
    (multi,) = [entry for entry in COMPOSITION if len(entry[3]) > 1]
    assert multi[3] == ("Area of Effect/5/2", "Area of Effect/5/3")

    # Each record composes only clauses the manifest assigns to it.
    owner = {c["clause_id"]: c["record_key"] for c in MANIFEST["clauses"]}
    for record_key, _, _, clauses in COMPOSITION:
        assert {owner[c] for c in clauses} == {record_key}, clauses


def test_the_mint_declares_seven_families_and_eleven_vocabularies() -> None:
    """The extension claim, stated where the schema hash covers it.

    Emitted by the schema payload, so this is not prose about the delta — an
    eighth family, a twelfth vocabulary or a widened accepted vocabulary would
    land a row here and fail. ``CoverDegree`` deliberately does not appear: the
    blocked-line rule reuses schema 6's vocabulary exactly as schema 6 declared
    it, and re-minting it would be a second declaration of the same closure.

    Filtered on ``SCHEMA_9_VERSION`` rather than on live authority, because
    this is schema 9's mint record and schema 10 has since been declared. The
    ``CoverDegree`` assertion is what that change makes load-bearing: schema 10
    widens that vocabulary with ``half``, and schema 9's rows must still be
    exactly the eleven it minted.
    """
    rows = [
        row
        for row in introduction_manifest()
        if row["introduced_in"] == SCHEMA_9_VERSION
    ]
    assert {row["name"] for row in rows if row["kind"] == "fact_family"} == {
        family.value
        for family in (
            FactFamily.AREA_ORIGIN,
            FactFamily.AREA_DIMENSION_REQUIREMENT,
            FactFamily.AREA_ORIGIN_INCLUSION,
            FactFamily.AREA_WIDTH_RELATION,
            FactFamily.AREA_ORIGIN_MOVEMENT,
            FactFamily.BLOCKED_LINE_EXCLUSION,
            FactFamily.UNSEEN_ORIGIN_RELOCATION,
        )
    }, rows
    members = [row for row in rows if row["kind"] == "vocabulary_member"]
    vocabularies = {tuple(row["vocabulary"]) for row in members}
    assert len(vocabularies) == 11, sorted(vocabularies)
    assert tuple(m.value for m in CoverDegree) not in vocabularies
    # Seven families and eleven vocabularies, and no other kind of row at all:
    # an ownership form or a changed field would be a different `kind` and
    # would fail here rather than in prose.
    assert {row["kind"] for row in rows} == {"fact_family", "vocabulary_member"}, rows


def test_the_crossing_from_schema_8_is_exactly_one_registered_step() -> None:
    """One step, looked up rather than named, in the direction it applies."""
    steps = lift_path(
        (SCHEMA_8_VERSION, SCHEMA_8_HASH),
        (SCHEMA_9_VERSION, SCHEMA_9_HASH),
    )
    assert [step.lift_id for step in steps] == ["5d-lift-schema-8-to-9"]


# ---------------------------------------------------------------------------
# The facts themselves
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fact",
    [entry[2] for entry in COMPOSITION],
    ids=[entry[3][0] for entry in COMPOSITION],
)
def test_each_fact_is_well_formed_and_round_trips(fact: MechanicalFact) -> None:
    """Every clause's fact, through the canonical payload and back."""
    assert fact_invariant_violations(fact) == ()
    payload = fact_payload(fact)
    rebuilt = fact_from_payload(payload)
    assert rebuilt == fact
    assert fact_payload(rebuilt) == payload


def test_the_general_origin_rule_and_the_emanation_rule_coexist() -> None:
    """Two facts, not one overriding the other.

    The umbrella says an area of effect has a *point* of origin; Emanation says
    its origin is a creature or an object. Both are printed, both are true of
    the class as the source states it, and collapsing either into the other
    would be this module inventing a precedence the source does not print. They
    are separate facts on separate records with separate provenance, so a
    consumer sees the general rule and the shape's own rule side by side.
    """
    umbrella = _fact_of(UMBRELLA, ORIGIN)
    emanation = _fact_of(EMANATION, ORIGIN)
    assert isinstance(umbrella, AreaOriginFact)
    assert isinstance(emanation, AreaOriginFact)
    assert umbrella.origin is AreaOriginKind.POINT
    assert emanation.origin is AreaOriginKind.CREATURE_OR_OBJECT
    assert fact_target_key(UMBRELLA, ORIGIN, umbrella) != fact_target_key(
        EMANATION, ORIGIN, emanation
    )
    # The umbrella states no extent and no placement, because the sentence
    # states none. The per-shape rules are where those live.
    assert (umbrella.extent, umbrella.placement) == (None, None)


def test_each_shape_keeps_its_own_extent_and_placement() -> None:
    """Six shapes, six distinct origin facts — no two are the same payload.

    Cube and Cylinder share an extent pattern and differ only in placement;
    Cone, Emanation, Line and Sphere each print their own extent and state no
    placement. A vocabulary that had merged any pair would show up as two equal
    payloads here.
    """
    origins = {
        record: _fact_of(record, ORIGIN)
        for record in (CONE, CUBE, CYLINDER, EMANATION, LINE, SPHERE)
    }
    payloads = {
        json.dumps(fact_payload(fact), sort_keys=True) for fact in origins.values()
    }
    assert len(payloads) == 6

    cube, cylinder = origins[CUBE], origins[CYLINDER]
    assert isinstance(cube, AreaOriginFact)
    assert isinstance(cylinder, AreaOriginFact)
    assert cube.extent is cylinder.extent is AreaExtentPattern.STRAIGHT_LINES
    assert cube.placement is not cylinder.placement
    for record in (CONE, EMANATION, LINE, SPHERE):
        fact = origins[record]
        assert isinstance(fact, AreaOriginFact)
        assert fact.placement is None, record


def test_the_dimension_parameters_are_names_in_printed_order() -> None:
    """Names and arity only — no value, no unit, no default.

    The source says *which* parameters a creating effect supplies and never
    what they are: "specifies the radius of the Cylinder's base and the
    Cylinder's height." Arity is meaning (Cylinder and Line take two, the rest
    take one) and so is order, which is why the invariant checker requires
    non-empty and unique but deliberately does not sort.
    """
    shapes = (CONE, CUBE, CYLINDER, EMANATION, LINE, SPHERE)
    dimensions: dict[str, AreaDimensionRequirementFact] = {}
    for record in shapes:
        fact = _fact_of(record, DIMENSIONS)
        assert isinstance(fact, AreaDimensionRequirementFact)
        dimensions[record] = fact

    arity = {record: len(fact.dimensions) for record, fact in dimensions.items()}
    assert arity == {CONE: 1, CUBE: 1, CYLINDER: 2, EMANATION: 1, LINE: 2, SPHERE: 1}

    cylinder = dimensions[CYLINDER]
    assert cylinder.dimensions == (
        AreaDimension.RADIUS_OF_THE_BASE,
        AreaDimension.HEIGHT,
    )
    # Printed order is meaning: the reversed tuple is a different payload.
    reversed_ = AreaDimensionRequirementFact(dimensions=cylinder.dimensions[::-1])
    assert fact_invariant_violations(reversed_) == ()
    assert fact_payload(reversed_) != fact_payload(cylinder)

    # No member carries a magnitude — each is the source's word for the
    # parameter, never a quantity, and nothing here supplies a unit.
    for fact in dimensions.values():
        for dimension in fact.dimensions:
            assert not any(ch.isdigit() for ch in dimension.value), dimension
            assert "feet" not in dimension.value and "foot" not in dimension.value


def test_the_inclusion_rule_keeps_its_creator_controlled_exception() -> None:
    """Four shapes exclude unless the creator says otherwise; two include.

    The exception is inside the excluded member rather than beside it, because
    the source prints one rule with a condition on it, not a rule and a
    separate override. Cylinder and Sphere print the bare inclusion with no
    exception at all, and that difference is the whole content of this family.
    """
    shapes = (CONE, CUBE, CYLINDER, EMANATION, LINE, SPHERE)
    inclusion: dict[str, AreaOriginInclusionFact] = {}
    for record in shapes:
        fact = _fact_of(record, INCLUSION)
        assert isinstance(fact, AreaOriginInclusionFact)
        inclusion[record] = fact

    assert {r for r, f in inclusion.items() if f.inclusion is EXCLUDED} == {
        CONE,
        CUBE,
        EMANATION,
        LINE,
    }
    assert {
        r for r, f in inclusion.items() if f.inclusion is AreaOriginInclusion.INCLUDED
    } == {CYLINDER, SPHERE}
    # A different member is a different payload, which is what stops the
    # exception from being dropped as a formatting detail.
    assert fact_payload(inclusion[CONE]) != fact_payload(inclusion[CYLINDER])


def test_both_emanation_movement_exceptions_are_stated() -> None:
    """Both arms of "unless it is an instantaneous or a stationary effect".

    One arm would be a narrower rule than the source prints: an Emanation that
    is a stationary effect would move with its origin. The checker requires the
    tuple non-empty and unique, so neither arm can be dropped silently and
    neither can be repeated to look like two.
    """
    fact = _fact_of(EMANATION, MOVEMENT)
    assert isinstance(fact, AreaOriginMovementFact)
    assert fact.suspended_by_any_of == (
        AreaMovementSuspension.INSTANTANEOUS_EFFECT,
        AreaMovementSuspension.STATIONARY_EFFECT,
    )
    single = AreaOriginMovementFact(
        suspended_by_any_of=(AreaMovementSuspension.INSTANTANEOUS_EFFECT,)
    )
    assert fact_payload(single) != fact_payload(fact)


def test_all_blocked_is_distinguished_from_some_blocked() -> None:
    """The quantifier is a stated value, because losing it inverts the rule.

    *"If **all** straight lines extending from the point of origin to a
    location in the area of effect are blocked, that location isn't included."*
    A representation that recorded only "a blocked line excludes" would exclude
    a location as soon as one line was blocked — the opposite reading of the
    same sentence, and the reason the quantifier is a closed vocabulary member
    rather than a boolean or an absence.
    """
    fact = _fact_of(UMBRELLA, BLOCKED)
    assert isinstance(fact, BlockedLineExclusionFact)
    assert fact.blocked is ALL_BLOCKED
    assert fact.blocked.value.startswith("all_straight_lines")
    # The vocabulary admits the printed quantifier and nothing weaker: there is
    # no "any", "some" or single-line member to reach for.
    assert [m.value for m in BlockedLineQuantifier] == [ALL_BLOCKED.value]


def test_total_cover_is_the_threshold_and_a_lesser_degree_is_a_different_rule() -> None:
    """*"To block a line, an obstruction must provide Total Cover."*

    ``blocking_cover`` is typed as the whole ``CoverDegree`` schema 6 already
    declared rather than pinned to ``TOTAL``, so the threshold is a value this
    clause states and not a constant the type forces. Three-Quarters Cover is
    therefore a representable — and different — rule, which is what makes
    stating Total Cover a claim about the source.
    """
    fact = _fact_of(UMBRELLA, BLOCKED)
    assert isinstance(fact, BlockedLineExclusionFact)
    assert fact.blocking_cover is CoverDegree.TOTAL
    weaker = BlockedLineExclusionFact(
        blocked=fact.blocked, blocking_cover=CoverDegree.THREE_QUARTERS
    )
    assert fact_invariant_violations(weaker) == ()
    assert fact_payload(weaker) != fact_payload(fact)


def test_the_unseen_origin_rule_keeps_its_conjunction_and_its_result() -> None:
    """Both conditions and the result, as three required fields.

    The sentence is a conjunction — placed at an unseen point **and** an
    obstruction between the creator and that point — and the relocation is what
    follows. ``ApplicabilityKind.ANY_OF`` is a flat disjunction with no
    nesting, conjunction or negation, so expressing this through it would state
    "either condition" and change the rule. Three required fields state it
    structurally, and none of them has a default.
    """
    fact = _fact_of(UMBRELLA, UNSEEN)
    assert isinstance(fact, UnseenOriginRelocationFact)
    assert fact.placement is UnseenPlacement.AT_AN_UNSEEN_POINT
    assert fact.obstruction is InterveningObstruction.BETWEEN_THE_CREATOR_AND_THE_POINT
    assert fact.relocated_to is RelocatedOrigin.NEAR_SIDE_OF_THE_OBSTRUCTION
    for field in ("placement", "obstruction", "relocated_to"):
        payload = {k: v for k, v in fact_payload(fact).items() if k != field}
        with pytest.raises(Exception) as raised:
            fact_from_payload(payload)
        assert field in str(raised.value), raised.value


# ---------------------------------------------------------------------------
# Fail closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "",
        "a_straight_line_from_the_point_of_origin",
        "any_straight_line_from_the_point_of_origin",
        "some_straight_lines_from_the_point_of_origin",
        "ALL_STRAIGHT_LINES_FROM_THE_POINT_OF_ORIGIN",
    ],
)
def test_a_quantifier_outside_the_closure_is_refused_rather_than_repaired(
    value: str,
) -> None:
    """The "all vs. some" distinction, proved by what the closure refuses.

    Every rejected value here is a reading a looser representation would have
    admitted, and each one states a different rule from the printed one.
    """
    payload = dict(fact_payload(_fact_of(UMBRELLA, BLOCKED))) | {"blocked": value}
    with pytest.raises(Exception) as raised:
        fact_from_payload(payload)
    assert "blocked" in str(raised.value), raised.value


def test_an_origin_placement_without_an_extent_is_refused() -> None:
    """Where the origin sits is meaningless without how the area extends.

    Only Cube and Cylinder print a placement, and both print it inside the
    sentence that states the extent. A placement on its own would publish half
    of a rule the source never states in halves.
    """
    orphan = AreaOriginFact(
        origin=AreaOriginKind.POINT,
        placement=AreaOriginPlacement.ANYWHERE_ON_A_FACE_OF_THE_CUBE,
    )
    assert fact_invariant_violations(orphan) != ()


@pytest.mark.parametrize(
    ("fact", "why"),
    [
        (
            AreaDimensionRequirementFact(dimensions=()),
            "an effect that supplies no parameter states no requirement",
        ),
        (
            AreaDimensionRequirementFact(
                dimensions=(AreaDimension.LENGTH, AreaDimension.LENGTH)
            ),
            "one parameter listed twice is not two parameters",
        ),
        (
            AreaOriginMovementFact(suspended_by_any_of=()),
            "no exception at all is a different rule from two",
        ),
        (
            AreaOriginMovementFact(
                suspended_by_any_of=(
                    AreaMovementSuspension.STATIONARY_EFFECT,
                    AreaMovementSuspension.STATIONARY_EFFECT,
                )
            ),
            "a repeated arm would look like both arms",
        ),
    ],
)
def test_a_malformed_collection_is_refused(fact: MechanicalFact, why: str) -> None:
    assert fact_invariant_violations(fact) != (), why


def test_schema_8_cannot_state_any_of_it() -> None:
    """The succession is real in the refusing direction too.

    Every one of the twenty-three facts is meaning schema 8's declared contract
    cannot carry, and the composed draft as a whole is refused under it. A
    family schema 8 could already have stated would pass here, and would mean
    the mint was unnecessary.
    """
    for record_key, component_key, fact, clauses in COMPOSITION:
        one = RepresentationDraft(
            records=(
                RecordDraft(semantic_key=record_key, kind=RecordKind.GLOSSARY_RULE),
            ),
            components=(
                ComponentDraft(
                    record_key=record_key,
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
        assert declared_meaning_violations(one, SCHEMA_8_VERSION), clauses
    assert declared_meaning_violations(_draft(), SCHEMA_8_VERSION)
    assert declared_meaning_violations(_draft(), REPRESENTATION_SCHEMA_VERSION) == []


# ---------------------------------------------------------------------------
# Validation, persistence, identity
# ---------------------------------------------------------------------------


#: The one finding this batch cannot clear on its own, quoted exactly. The
#: umbrella's *See also* cites ``Cover`` and cover ingestion is not in this
#: batch, so the citation has no target here and the validator says so. This is
#: the batch's honest residue, not a defect to be tuned away: the accepted
#: artifact carries two dangling citations of exactly this kind — ``Speed`` and
#: ``Concentration``, whose targets ``test_areas_of_effect_1_frozen_prior`` pins
#: as the recorded residue — and each clears when the cited entry is ingested,
#: never by editing the record that cites it.
COVER_FINDING = (
    "reference srd-5.2.1/rules-glossary:'Cover': "
    "unknown target record glossary.cover"
)


def test_the_composition_validates_with_only_the_cover_citation_outstanding() -> None:
    """Seven entries, forty-three clauses, and exactly one named residue.

    Everything internal is clean — every record, component, fact, provenance
    claim and span partition — and the sole finding is the citation this batch
    is not allowed to close. Asserting the tuple exactly, rather than filtering
    the Cover line out of it, is what keeps a second finding from hiding behind
    the first.
    """
    assert validate_representation(_draft(), _ledger(), _corpus()) == (COVER_FINDING,)


def test_the_only_reference_this_batch_cannot_resolve_is_cover() -> None:
    """The residue, pinned as a set rather than counted.

    The umbrella names six shapes and this batch defines all six; it also cites
    ``Cover`` under *See also*, and cover ingestion is not in this batch. That
    one dangling target is the honest state of the composition — inventing a
    ``glossary.cover`` record to close it would publish a definition no clause
    here states.
    """
    draft = _draft()
    defined = {record.semantic_key for record in draft.records}
    dangling = {
        reference.target_record_key
        for reference in draft.references
        if reference.target_record_key not in defined
    }
    assert dangling == {COVER}
    # Dangling is reported, not overlooked — and it is reported by the
    # validator, not by this module's own arithmetic about it.
    assert validate_representation(draft, _ledger(), _corpus()) == (COVER_FINDING,)
    # The six shapes the umbrella names are all defined here, so Cover is the
    # only one outstanding rather than one of seven guesses.
    assert {r.target_record_key for r in draft.references} - dangling == {
        CONE,
        CUBE,
        CYLINDER,
        EMANATION,
        LINE,
        SPHERE,
    }


def test_the_whole_composition_survives_persistence_and_reconstruction(
    session: Session,
) -> None:
    """Typed rows in, typed rows out, and the same identity on the far side.

    Reconstruction reads the database and nothing else, so a family the store
    cannot round trip fails here rather than the first time a real corpus
    carries it.
    """
    identified = identify_projection(candidate_of(RELEASE_BINDING, _ledger(), _draft()))
    persist_draft(session, identified, now=NOW)
    session.flush()

    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    by_key = {
        (c.record_key, c.semantic_key): c for c in rebuilt.representation.components
    }
    for record_key, component_key, fact, _ in COMPOSITION:
        assert by_key[(record_key, component_key)].facts == (fact,)
    assert identify_projection(rebuilt).projection_uuid == identified.projection_uuid


@pytest.mark.parametrize(
    ("record_key", "component_key", "changed", "why"),
    [
        (
            CONE,
            INCLUSION,
            AreaOriginInclusionFact(inclusion=AreaOriginInclusion.INCLUDED),
            "dropping the creator-controlled exception",
        ),
        (
            UMBRELLA,
            BLOCKED,
            BlockedLineExclusionFact(
                blocked=ALL_BLOCKED, blocking_cover=CoverDegree.THREE_QUARTERS
            ),
            "lowering the blocking threshold below Total Cover",
        ),
        (
            CYLINDER,
            DIMENSIONS,
            AreaDimensionRequirementFact(
                dimensions=(AreaDimension.HEIGHT, AreaDimension.RADIUS_OF_THE_BASE)
            ),
            "reversing the printed parameter order",
        ),
        (
            EMANATION,
            MOVEMENT,
            AreaOriginMovementFact(
                suspended_by_any_of=(AreaMovementSuspension.INSTANTANEOUS_EFFECT,)
            ),
            "dropping one of the two movement exceptions",
        ),
    ],
)
def test_a_changed_meaning_changes_the_projection_identity(
    record_key: str, component_key: str, changed: MechanicalFact, why: str
) -> None:
    """Each perturbation is a different rule, so each is a different identity.

    Identity is computed over the canonical payload, so this is the mechanism
    that stops any of these from passing as a reformat of the accepted one.
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
                    facts=(changed,),
                )
                if (c.record_key, c.semantic_key) == (record_key, component_key)
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
# The consumer boundary
# ---------------------------------------------------------------------------


def test_the_class_reaches_a_consumer_as_closed_vocabulary_members() -> None:
    """``_base_records`` is what every reader of mechanical authority goes through.

    Seven records, twenty-three structured components, no governing prose
    anywhere: the whole class arrives as declared enum members with span ids for
    provenance, which is the entire consumer-visible effect of this mint.
    """
    records = _base_records(candidate_of(RELEASE_BINDING, _ledger(), _draft()))
    assert set(records) == set(RECORDS)
    for record_key, component_key, fact, clauses in COMPOSITION:
        component = next(
            c for c in records[record_key].components if c.semantic_key == component_key
        )
        assert component.handling is ComponentHandling.STRUCTURED
        assert component.irreducibility_reason_code is None
        assert component.governing_prose == ()
        (entry,) = component.facts
        assert entry.fact == fact
        # Primary spans plus whatever supporting clause bounds this fact: the
        # umbrella's origin rule carries the sentence deferring placement to
        # the shapes, and Cone's width relation carries its worked example.
        expected = {_span_id(c) for c in clauses} | {
            _span_id(c)
            for rec, comp, c in FACT_CONTEXT
            if (rec, comp) == (record_key, component_key)
        }
        assert set(entry.span_ids) == expected


def test_the_typed_view_carries_every_family_and_every_fact() -> None:
    """The deterministic consumer's whole reading of the class."""
    typed = {r.semantic_key: r for r in build_typed_view(_authority()).records}
    assert set(typed) == set(RECORDS)
    seen = [
        entry.fact
        for record in typed.values()
        for component in record.components
        for entry in component.facts
    ]
    assert len(seen) == 23
    assert {fact.FAMILY for fact in seen} == {
        FactFamily.AREA_ORIGIN,
        FactFamily.AREA_DIMENSION_REQUIREMENT,
        FactFamily.AREA_ORIGIN_INCLUSION,
        FactFamily.AREA_WIDTH_RELATION,
        FactFamily.AREA_ORIGIN_MOVEMENT,
        FactFamily.BLOCKED_LINE_EXCLUSION,
        FactFamily.UNSEEN_ORIGIN_RELOCATION,
    }
    for _, _, fact, _ in COMPOSITION:
        assert fact in seen


def test_the_gamemaster_view_names_the_clauses_without_delivering_them() -> None:
    """Structured components have no prose to resolve, and that is the point.

    Every component here is ``STRUCTURED``, so the GameMaster view resolves no
    governing prose at all: each rule arrives as its vocabulary members, and the
    sentence it came from arrives as a span id a reader can look up. The printed
    clause text is never carried in the view — which is what keeps licensed
    source text out of a projection that only needs to cite it.
    """
    view = build_gamemaster_view(_authority(), PROSE)
    assert {c.record_key for c in view.components} == set(RECORDS)
    assert len(view.components) == 23
    for component in view.components:
        assert component.governing_prose == ()
        assert component.span_ids == ()
        (entry,) = component.structured_context
        assert entry.span_ids != ()
    rendered = str(view)
    for clause_id in SUBSTANTIVE_CLAUSES:
        assert CLAUSE[clause_id]["text"] not in rendered, clause_id


#: The proposal the generator wrote, next to this module in the review notes.
#: Read, never written: the test is an agreement check on committed bytes, so a
#: proposal regenerated from a changed composition fails here instead of landing
#: unnoticed.
PROPOSAL_PATH = (
    pathlib.Path(__file__).resolve().parents[3]
    / ".claude"
    / "review-notes"
    / "issue-5d-batch-areas-of-effect-1-PROPOSAL.json"
)


def test_the_committed_proposal_is_the_composition_this_module_states() -> None:
    """The artifact under review carries exactly this draft, element for element.

    The generator builds its own draft from the same reviewed inventory; this
    module builds one independently. If the two ever disagree, the committed
    proposal is no longer evidence for anything this module proves about the
    composition, and a reviewer reading the tests would be reading a different
    batch from the one in the artifact.

    Identity is deliberately not pinned here. The proposal identity belongs in
    the audit and the handoff, where it is reported at the scope it holds; a
    test that pinned it would make every honest regeneration look like a
    regression.
    """
    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    assert proposal["proposed_representation"] == representation_payload(_draft())
