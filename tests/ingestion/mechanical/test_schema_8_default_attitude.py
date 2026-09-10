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
* **the delta is real in both directions** — schema 7 refuses the fact and
  schema 8 admits it, which is what the registered ``5d-lift-schema-7-to-8``
  crossing exists to carry;
* **the wire contract holds** — canonical round trip, and an attitude outside
  the closure is *refused* rather than repaired; and
* **a consumer reads a vocabulary member** — through ``_base_records``, the
  function every reader of mechanical authority goes through, off a
  ``STRUCTURED`` component with no governing prose to parse.

**Limits, stated so this is not read for more than it proves.** This is a
demonstration against the contract schema 8 now states — not a proposal and not
an acceptance. The ``attitudes-1`` proposal is separately reviewable material;
the fixture coordinates below are this module's own and are no part of it. What
the family does *not* model is equally deliberate: an attitude a creature
currently holds would be runtime state, and Friendly's and Hostile's
influence-check bias stays ``condition.charmed``'s accepted ``AdvantageFact``
shape on a ``MIXED`` component, untouched by this addition.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.representation import (
    Attitude,
    ComponentDraft,
    ComponentHandling,
    DefaultAttitudeFact,
    FactFamily,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    fact_from_payload,
    fact_invariant_violations,
    fact_payload,
    fact_target_key,
    introduction_manifest,
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
from afterworlds.services.rules_authority.application import _base_records
from tests.ingestion.mechanical.conftest import (
    RELEASE_BINDING,
    SPELL_KEY,
    SPELL_SPAN,
    bound_corpus,
    build_ledger,
    build_representation,
    candidate_of,
)

#: The printed sentence, as the source prints it.
SOURCE = "Indifferent is the default attitude of a monster."

COMPONENT_KEY = "default_attitude"
FACT = DefaultAttitudeFact(attitude=Attitude.INDIFFERENT)


def _draft() -> object:
    """The fixture draft with its typed component replaced by this family.

    The prose-bound sibling stays, because the fixture's prose binding claims
    it; only the ``STRUCTURED`` arm and the fact's own provenance edge move.
    """
    base = build_representation()
    return build_representation(
        components=(
            ComponentDraft(
                record_key=SPELL_KEY,
                semantic_key=COMPONENT_KEY,
                handling=ComponentHandling.STRUCTURED,
                facts=(FACT,),
            ),
            base.components[1],
        ),
        provenance=tuple(
            (
                ProvenanceClaim(
                    ProvenanceTargetKind.FACT,
                    fact_target_key(SPELL_KEY, COMPONENT_KEY, FACT),
                    SPELL_SPAN,
                    ProvenanceRole.PRIMARY,
                )
                if claim.target_kind is ProvenanceTargetKind.FACT
                else claim
            )
            for claim in base.provenance
        ),
    )


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
# The consumer boundary
# ---------------------------------------------------------------------------


def test_the_composition_validates_as_the_source_states_it() -> None:
    assert validate_representation(_draft(), build_ledger(), bound_corpus()) == ()


def test_a_consumer_reads_a_vocabulary_member_off_the_projection() -> None:
    """Not prose to parse, and not an inference — a closed enum member.

    ``_base_records`` is the function every reader of mechanical authority goes
    through, so this is the addition's entire consumer-visible effect.
    """
    records = _base_records(candidate_of(RELEASE_BINDING, build_ledger(), _draft()))
    component = next(
        c for c in records[SPELL_KEY].components if c.semantic_key == COMPONENT_KEY
    )
    assert component.handling is ComponentHandling.STRUCTURED
    assert component.irreducibility_reason_code is None
    assert component.governing_prose == ()

    (entry,) = component.facts
    assert entry.fact == FACT
    assert entry.fact.attitude is Attitude.INDIFFERENT
    assert entry.span_ids == (SPELL_SPAN,)
