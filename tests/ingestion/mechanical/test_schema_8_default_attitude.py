"""Schema 8's one addition, against the clause that forced it — CRD Issue 5d.

``attitudes-1`` returned a bounded schema stop, S-2: *"Indifferent is the
default attitude of a monster."* (``Indifferent``, p184) states which member of
a closed class applies when nothing else has been specified, and schema 7 had
no shape for it. No composition of accepted families says it either — a default
is not an effect, a duration, an allowance, a roll, or a state transition — and
contract 3's other branch is unavailable, because none of the six closed
irreducibility reasons is affirmatively true of the clause.

So schema 8 adds exactly one family, :class:`DefaultAttitudeFact`, over exactly
one closed vocabulary, :class:`Attitude`, and this module is the executable half
of that decision:

* **the value is stated, not inferred** — the fact names ``INDIFFERENT``; the
  record key ``attitude.indifferent`` is a name, and reading the member off it
  is the by-convention inference the union refuses elsewhere;
* **the vocabulary is the printed closure** — all three members, because
  ``Attitude`` (p177) enumerates the class in one line, not the one member this
  batch uses;
* **the delta is real in both directions** — the registered
  ``5d-lift-schema-7-to-8`` crossing is looked up here rather than named; the
  refusal under schema 7 and the admission under schema 8 that make it a real
  succession are proved in ``test_schema_version_legality``, against the same
  fact;
* **the wire contract holds** — canonical round trip, and an attitude outside
  the closure is *refused* rather than repaired; and
* **the printed composition survives both consumer views** — the four Rules
  Glossary entries on their own coordinates, through ``_base_records`` and then
  through the typed and GameMaster views, with Friendly's and Hostile's
  influence qualification beside the default as the bounded sibling check.

**Limits, stated so this is not read for more than it proves.** This is a
demonstration against the contract schema 8 now states — not a proposal and not
an acceptance. The ``attitudes-1`` proposal is separately reviewable material;
the leaf ids, chunk ids and release binding below are this module's own and are
no part of it, even though the clause text is the printed clause text. What
the family does *not* model is equally deliberate: an attitude a creature
currently holds would be runtime state, and Friendly's and Hostile's
influence-check bias stays ``condition.charmed``'s accepted ``AdvantageFact``
shape on a ``MIXED`` component, untouched by this addition.
"""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

import pytest

from afterworlds.ingestion.mechanical.accounting import derive_span_id
from afterworlds.ingestion.mechanical.bound_corpus import BoundCorpusSnapshot
from afterworlds.ingestion.mechanical.models import (
    ClassificationLedger,
    ReviewState,
    SemanticDisposition,
    SemanticSpan,
)
from afterworlds.ingestion.mechanical.representation import (
    AdvantageFact,
    AdvantageState,
    Attitude,
    ComponentDraft,
    ComponentHandling,
    DefaultAttitudeFact,
    FactFamily,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    RollActor,
    RollContext,
    RollSpec,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
    fact_target_key,
    introduction_manifest,
    prose_binding_target_key,
)
from afterworlds.ingestion.mechanical.schema_lift import (
    SCHEMA_7_HASH,
    SCHEMA_7_VERSION,
    SCHEMA_8_HASH,
    SCHEMA_8_VERSION,
    SCHEMA_LIFTS,
    lift_path,
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
    RELEASE_BINDING,
    bound_corpus,
    build_ledger,
    candidate_of,
    coverage,
)

#: The printed sentence, as the source prints it.
SOURCE = "Indifferent is the default attitude of a monster."

COMPONENT_KEY = "default_attitude"
FACT = DefaultAttitudeFact(attitude=Attitude.INDIFFERENT)


# ---------------------------------------------------------------------------
# The printed composition — the four entries, as the Rules Glossary prints them
# ---------------------------------------------------------------------------
#
# Native coordinates, not the shared Wish fixture: the point of this section is
# that the *actual* Attitude clauses compose and reach both consumer views with
# the provenance the source gives them. Leaf text is the printed text, so every
# span extent below is derived from the sentence rather than declared.

UMBRELLA_KEY = "glossary.attitude"
FRIENDLY_KEY = "attitude.friendly"
HOSTILE_KEY = "attitude.hostile"
INDIFFERENT_KEY = "attitude.indifferent"

#: The umbrella's closure sentence (``Attitude``, p177). It states the class,
#: which the vocabulary manifest carries; the umbrella owns **no component**.
T2 = (
    "A monster has a starting attitude toward a player character: "
    "Friendly, Hostile, or Indifferent."
)
#: ``Friendly`` (p182): a definition, a typed bias, and the qualification that
#: says *which* check the bias applies to.
F1 = "A Friendly creature views you favorably."
F2 = " You have Advantage on an ability check"
F3 = " to influence a Friendly creature."
#: ``Hostile`` (p183), the same three clauses with the polarity flipped.
H1 = "A Hostile creature views you unfavorably."
H2 = " You have Disadvantage on an ability check"
H3 = " to influence a Hostile creature."
#: ``Indifferent`` (p184): a definition, and S-2 itself.
I1 = "An Indifferent creature has no desire to help or hinder you."
I2 = f" {SOURCE}"

UMBRELLA_LEAF = "leaf-glossary-attitude"
FRIENDLY_LEAF = "leaf-attitude-friendly"
HOSTILE_LEAF = "leaf-attitude-hostile"
INDIFFERENT_LEAF = "leaf-attitude-indifferent"

LEAVES = {
    UMBRELLA_LEAF: T2,
    FRIENDLY_LEAF: F1 + F2 + F3,
    HOSTILE_LEAF: H1 + H2 + H3,
    INDIFFERENT_LEAF: I1 + I2,
}
CHUNKS = {leaf: f"chunk-{leaf}" for leaf in LEAVES}


def _extent(leaf: str, clause: str) -> tuple[int, int]:
    """*clause*'s half-open offsets in *leaf*, read off the printed text."""
    start = LEAVES[leaf].index(clause)
    return start, start + len(clause)


def _span_id(leaf: str, clause: str) -> str:
    return derive_span_id(leaf, *_extent(leaf, clause))


#: Every clause, with the disposition the batch classified it under: the three
#: definitions and the umbrella's closure are supporting authority owned by
#: their records; the two influence clauses and S-2 are substantive.
CLAUSES: tuple[tuple[str, str, SemanticDisposition], ...] = (
    (UMBRELLA_LEAF, T2, SemanticDisposition.SUPPORTING_AUTHORITY),
    (FRIENDLY_LEAF, F1, SemanticDisposition.SUPPORTING_AUTHORITY),
    (FRIENDLY_LEAF, F2, SemanticDisposition.SUBSTANTIVE),
    (FRIENDLY_LEAF, F3, SemanticDisposition.SUBSTANTIVE),
    (HOSTILE_LEAF, H1, SemanticDisposition.SUPPORTING_AUTHORITY),
    (HOSTILE_LEAF, H2, SemanticDisposition.SUBSTANTIVE),
    (HOSTILE_LEAF, H3, SemanticDisposition.SUBSTANTIVE),
    (INDIFFERENT_LEAF, I1, SemanticDisposition.SUPPORTING_AUTHORITY),
    (INDIFFERENT_LEAF, I2, SemanticDisposition.SUBSTANTIVE),
)

#: ``condition.charmed``'s accepted shape, twice, with the polarity flipped.
#: The purpose restriction — *which* ability check — is applicability prose on
#: a ``MIXED`` component, not a widened ``RollContext``.
INFLUENCE_ROLL = RollSpec(
    actor=RollActor.AGAINST_SUBJECT, context=RollContext.ABILITY_CHECK
)
FRIENDLY_ADV = AdvantageFact(state=AdvantageState.ADVANTAGE, roll=INFLUENCE_ROLL)
HOSTILE_DIS = AdvantageFact(state=AdvantageState.DISADVANTAGE, roll=INFLUENCE_ROLL)

FRIENDLY_COMPONENT = "influence_advantage"
HOSTILE_COMPONENT = "influence_disadvantage"
CONTEXTUAL = "contextual_applicability"


def _binding(record: str, component: str, leaf: str, clause: str) -> ProseBindingDraft:
    """The influence qualification, bound at the extent its span accepted."""
    start, end = _extent(leaf, clause)
    return ProseBindingDraft(
        component_key=component,
        record_key=record,
        chunk_id=CHUNKS[leaf],
        span_id=derive_span_id(leaf, start, end),
        chunk_char_start=start,
        chunk_char_end=end,
        irreducibility_reason_code=CONTEXTUAL,
    )


FRIENDLY_BINDING = _binding(FRIENDLY_KEY, FRIENDLY_COMPONENT, FRIENDLY_LEAF, F3)
HOSTILE_BINDING = _binding(HOSTILE_KEY, HOSTILE_COMPONENT, HOSTILE_LEAF, H3)


def _draft() -> RepresentationDraft:
    """The four entries as one draft, with every element's own provenance."""
    return RepresentationDraft(
        records=(
            RecordDraft(semantic_key=UMBRELLA_KEY, kind=RecordKind.GLOSSARY_RULE),
            RecordDraft(semantic_key=FRIENDLY_KEY, kind=RecordKind.GLOSSARY_RULE),
            RecordDraft(semantic_key=HOSTILE_KEY, kind=RecordKind.GLOSSARY_RULE),
            RecordDraft(semantic_key=INDIFFERENT_KEY, kind=RecordKind.GLOSSARY_RULE),
        ),
        components=(
            # The umbrella owns none: it states what an attitude is and cites
            # its members. That is why it contributes no GameMaster component.
            ComponentDraft(
                record_key=FRIENDLY_KEY,
                semantic_key=FRIENDLY_COMPONENT,
                handling=ComponentHandling.MIXED,
                irreducibility_reason_code=CONTEXTUAL,
                facts=(FRIENDLY_ADV,),
            ),
            ComponentDraft(
                record_key=HOSTILE_KEY,
                semantic_key=HOSTILE_COMPONENT,
                handling=ComponentHandling.MIXED,
                irreducibility_reason_code=CONTEXTUAL,
                facts=(HOSTILE_DIS,),
            ),
            ComponentDraft(
                record_key=INDIFFERENT_KEY,
                semantic_key=COMPONENT_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(FACT,),
            ),
        ),
        prose_bindings=(FRIENDLY_BINDING, HOSTILE_BINDING),
        relationships=(),
        references=(),
        provenance=(
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (UMBRELLA_KEY,),
                _span_id(UMBRELLA_LEAF, T2),
                ProvenanceRole.CONTEXTUAL,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (FRIENDLY_KEY,),
                _span_id(FRIENDLY_LEAF, F1),
                ProvenanceRole.CONTEXTUAL,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (HOSTILE_KEY,),
                _span_id(HOSTILE_LEAF, H1),
                ProvenanceRole.CONTEXTUAL,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.RECORD,
                (INDIFFERENT_KEY,),
                _span_id(INDIFFERENT_LEAF, I1),
                ProvenanceRole.CONTEXTUAL,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(FRIENDLY_KEY, FRIENDLY_COMPONENT, FRIENDLY_ADV),
                _span_id(FRIENDLY_LEAF, F2),
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(HOSTILE_KEY, HOSTILE_COMPONENT, HOSTILE_DIS),
                _span_id(HOSTILE_LEAF, H2),
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(INDIFFERENT_KEY, COMPONENT_KEY, FACT),
                _span_id(INDIFFERENT_LEAF, I2),
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.PROSE_BINDING,
                prose_binding_target_key(FRIENDLY_BINDING),
                FRIENDLY_BINDING.span_id,
                ProvenanceRole.PRIMARY,
            ),
            ProvenanceClaim(
                ProvenanceTargetKind.PROSE_BINDING,
                prose_binding_target_key(HOSTILE_BINDING),
                HOSTILE_BINDING.span_id,
                ProvenanceRole.PRIMARY,
            ),
        ),
    )


def _ledger() -> ClassificationLedger:
    """The batch's own accepted spans, one per printed clause."""
    return build_ledger(
        spans=tuple(
            SemanticSpan(
                span_id=_span_id(leaf, clause),
                leaf_id=leaf,
                char_start=_extent(leaf, clause)[0],
                char_end=_extent(leaf, clause)[1],
                disposition=disposition,
                review_state=ReviewState.ACCEPTED,
            )
            for leaf, clause, disposition in CLAUSES
        )
    )


def _corpus() -> BoundCorpusSnapshot:
    """One chunk per leaf, covering it whole, so chunk offsets are leaf offsets."""
    return bound_corpus(
        leaf_lengths={leaf: len(text) for leaf, text in LEAVES.items()},
        chunk_coverage=tuple(
            coverage(CHUNKS[leaf], leaf, 0, len(text)) for leaf, text in LEAVES.items()
        ),
    )


def _authority() -> EffectiveAuthority:
    """The composed batch as the authority a consumer is handed."""
    records = _base_records(candidate_of(RELEASE_BINDING, _ledger(), _draft()))
    return EffectiveAuthority(
        binding=RulesPackageBinding(
            package_uuid=uuid5(NAMESPACE_URL, "pkg-5d"),
            release_version="rel-5d",
            mechanical_projection_uuid=uuid5(NAMESPACE_URL, "proj-attitudes-1"),
            override_set_uuid=uuid5(NAMESPACE_URL, "ovs-attitudes-1"),
        ),
        records=tuple(records.values()),
        applied_overrides=(),
    )


#: The authoritative chunk text a GameMaster view resolves prose against.
PROSE = {CHUNKS[leaf]: text for leaf, text in LEAVES.items()}


# ---------------------------------------------------------------------------
# What the mint declared, and what it did not move
# ---------------------------------------------------------------------------


def test_the_mint_declares_one_family_and_one_vocabulary_and_nothing_else() -> None:
    """The smallest extension claim, stated where the schema hash covers it.

    The manifest is emitted by the schema payload, so this is not prose about
    the delta — a second family or a widened accepted vocabulary would land a
    row here and fail.
    """
    rows = [
        row
        for row in introduction_manifest()
        if row["introduced_in"] == SCHEMA_8_VERSION
    ]
    assert [row["name"] for row in rows if row["kind"] == "fact_family"] == [
        FactFamily.DEFAULT_ATTITUDE.value
    ], rows
    members = [row for row in rows if row["kind"] == "vocabulary_member"]
    assert [row["name"] for row in members] == [m.value for m in Attitude], rows
    assert {tuple(row["vocabulary"]) for row in members} == {
        tuple(m.value for m in Attitude)
    }, rows
    # One vocabulary and one family, and no other kind of row at all: an
    # ownership form, a nullable field or a required field would be a different
    # `kind` and would fail here rather than in prose.
    assert {row["kind"] for row in rows} == {"fact_family", "vocabulary_member"}, rows


def test_the_vocabulary_is_admitted_at_its_printed_closure() -> None:
    """Three members, because the source enumerates three in one line.

    *"A monster has a starting attitude toward a player character: Friendly,
    Hostile, or Indifferent."* This batch states one of them; admitting only
    that one would make the closure a property of what happened to be
    represented first, which is ``MovementMode``'s accepted reasoning.
    """
    assert [m.value for m in Attitude] == ["friendly", "hostile", "indifferent"]


def test_the_crossing_from_schema_7_is_exactly_one_registered_step() -> None:
    """One step, looked up rather than named, in the direction it applies."""
    steps = lift_path(
        (SCHEMA_7_VERSION, SCHEMA_7_HASH), (SCHEMA_8_VERSION, SCHEMA_8_HASH)
    )
    assert [step.lift_id for step in steps] == ["5d-lift-schema-7-to-8"]
    assert (SCHEMA_7_VERSION, SCHEMA_7_HASH) in SCHEMA_LIFTS


# ---------------------------------------------------------------------------
# The fact itself
# ---------------------------------------------------------------------------


def test_the_attitude_is_stated_rather_than_read_off_the_record_key() -> None:
    """The whole reason the field is a value and not ``is_default: bool``.

    A boolean would leave the *which* to whoever reads the record's semantic
    key — a by-convention inference, and one that would silently produce a
    different mechanic on a record named differently.
    """
    assert FACT.attitude is Attitude.INDIFFERENT
    assert FACT.FAMILY is FactFamily.DEFAULT_ATTITUDE
    assert fact_invariant_violations(FACT) == ()


def test_the_fact_round_trips_through_its_canonical_payload() -> None:
    payload = fact_payload(FACT)
    assert payload["family"] == FactFamily.DEFAULT_ATTITUDE.value
    assert payload["attitude"] == Attitude.INDIFFERENT.value
    rebuilt = fact_from_payload(payload)
    assert rebuilt == FACT
    assert fact_payload(rebuilt) == payload


@pytest.mark.parametrize("value", ["", "neutral", "INDIFFERENT", "friendly "])
def test_an_attitude_outside_the_closure_is_refused_rather_than_repaired(
    value: str,
) -> None:
    """A closed vocabulary that coerced its input would not be closed."""
    payload = dict(fact_payload(FACT)) | {"attitude": value}
    with pytest.raises(Exception) as raised:
        fact_from_payload(payload)
    assert "attitude" in str(raised.value), raised.value


# ---------------------------------------------------------------------------
# The consumer boundary — the printed composition, through both views
# ---------------------------------------------------------------------------


def test_the_composition_validates_as_the_source_states_it() -> None:
    """The four entries, on their own coordinates, with nothing left over."""
    assert validate_representation(_draft(), _ledger(), _corpus()) == ()


def test_the_default_reaches_a_consumer_as_a_vocabulary_member() -> None:
    """Not prose to parse, and not an inference — a closed enum member.

    ``_base_records`` is the function every reader of mechanical authority goes
    through, and this is S-2's entire consumer-visible effect: one ``STRUCTURED``
    component, one fact, no governing prose, and the printed clause named as the
    fact's own provenance rather than delivered as text.
    """
    records = _base_records(candidate_of(RELEASE_BINDING, _ledger(), _draft()))
    component = next(
        c
        for c in records[INDIFFERENT_KEY].components
        if c.semantic_key == COMPONENT_KEY
    )
    assert component.handling is ComponentHandling.STRUCTURED
    assert component.irreducibility_reason_code is None
    assert component.governing_prose == ()

    (entry,) = component.facts
    assert entry.fact == FACT
    assert entry.fact.attitude is Attitude.INDIFFERENT
    assert entry.span_ids == (_span_id(INDIFFERENT_LEAF, I2),)


def test_the_typed_view_carries_the_default_and_the_two_polarities() -> None:
    """The deterministic consumer's whole reading of the three entries.

    The polarity check is the bounded sibling: Friendly and Hostile are one
    accepted ``AdvantageFact`` shape with the sign flipped over the *same*
    :class:`RollSpec`, so a widened roll vocabulary or a copied roll would fail
    here rather than pass unnoticed beside the family this schema added.
    """
    typed = {r.semantic_key: r for r in build_typed_view(_authority()).records}
    assert set(typed) == {UMBRELLA_KEY, FRIENDLY_KEY, HOSTILE_KEY, INDIFFERENT_KEY}

    def _fact(record_key: str, component_key: str) -> object:
        component = next(
            c for c in typed[record_key].components if c.semantic_key == component_key
        )
        (entry,) = component.facts
        return entry.fact

    default = _fact(INDIFFERENT_KEY, COMPONENT_KEY)
    assert default == FACT
    assert default.attitude is Attitude.INDIFFERENT

    friendly = _fact(FRIENDLY_KEY, FRIENDLY_COMPONENT)
    hostile = _fact(HOSTILE_KEY, HOSTILE_COMPONENT)
    assert friendly.state is AdvantageState.ADVANTAGE
    assert hostile.state is AdvantageState.DISADVANTAGE
    assert friendly.roll == hostile.roll == INFLUENCE_ROLL
    # The default is a different family from the bias, not a stronger version
    # of one: nothing in either sibling states an attitude a creature holds.
    assert {friendly.FAMILY, hostile.FAMILY} == {FactFamily.ADVANTAGE}
    assert default.FAMILY is FactFamily.DEFAULT_ATTITUDE


def test_the_gamemaster_view_resolves_the_qualification_but_not_the_default() -> None:
    """What each record actually contributes, and what it does not.

    Three components for four records: the umbrella states no mechanic and owns
    no component, so it contributes nothing here — which is why the *"of a
    monster"* scope cannot be read as carried by the umbrella's supporting
    authority. Friendly and Hostile resolve exactly their influence
    qualification, sliced to the span that accepted it. Indifferent resolves no
    prose at all, because a ``STRUCTURED`` component has none to resolve: the
    attitude arrives as the declared vocabulary member and its provenance
    arrives as a span id.
    """
    view = build_gamemaster_view(_authority(), PROSE)
    by_record = {c.record_key: c for c in view.components}
    assert len(view.components) == 3
    assert set(by_record) == {FRIENDLY_KEY, HOSTILE_KEY, INDIFFERENT_KEY}
    assert UMBRELLA_KEY not in by_record

    for record_key, clause in ((FRIENDLY_KEY, F3), (HOSTILE_KEY, H3)):
        component = by_record[record_key]
        assert component.handling is ComponentHandling.MIXED
        assert component.irreducibility_reason_code == CONTEXTUAL
        (prose,) = component.governing_prose
        assert isinstance(prose, SourceProse)
        assert prose.text == clause

    indifferent = by_record[INDIFFERENT_KEY]
    assert indifferent.governing_prose == ()
    # The component owns no span of its own; the clause is the *fact's*
    # provenance, which is where a reader has to look to find it.
    assert indifferent.span_ids == ()
    (fact,) = indifferent.structured_context
    assert fact.fact == FACT
    assert fact.fact.attitude is Attitude.INDIFFERENT
    assert fact.span_ids == (_span_id(INDIFFERENT_LEAF, I2),)
    # The clause itself is named, never delivered: a span id, not the sentence.
    assert SOURCE not in str(indifferent)
