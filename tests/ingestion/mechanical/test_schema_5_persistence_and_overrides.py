"""Schema 5's additions survive storage, reconstruction, and the digest — CRD Issue 5d.

Schema 5 adds no *component* key, so nothing here needs a migration: the roll
context and the damage interval ride the family-keyed fact payload, and the
consumption band rides the existing ``rp_mech_components.applies_when`` JSON
column. That is a claim about storage, so it is proved against a real session
rather than asserted from the column types.

Four properties per addition, the same four ``test_recurrence_persistence``
established for schema 4's one column:

* a stated value reconstructs as the same value object;
* an absent optional one reconstructs as ``None`` — absence is a real state;
* the value is identity-bearing, so a different one is a different projection
  *and* moves the persisted-state digest; and
* a stored value outside the declared contract fails reconstruction rather than
  silently becoming a different value.

**And all three applicability loaders, together.** Schema 5 consolidated
``oracle.py``, ``persistence.py`` and ``services/rules_authority/patches.py``
onto one ``build_consumption_band``, so what has to be proved is that each of
them really reaches it — three copies of a wire contract is how they drift, and
a shared implementation nothing exercises through two of its callers is the same
risk wearing a tidier shape. The last section is therefore not about storage at
all: it is the committed-accepted-authority ingress path, the one that reads
what the Owner signed off, exercised against a real file through
``load_accepted_inputs``.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.oracle import (
    COMMITTED_ORACLE_DIR,
    OracleLoadError,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import (
    PersistedStateReconstructionError,
    compute_persisted_state_digest,
    persist_draft,
    reconstruct_candidate,
    record_persisted_state_digest,
    verify_persisted_state,
)
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.representation import (
    AbilityCheckFact,
    AbilityScore,
    Applicability,
    ApplicabilityKind,
    ConsumptionBand,
    DamageFact,
    DamageInterval,
    DamageType,
    DcKind,
    DiceExpression,
    DieSize,
    DistanceUnit,
    MalformedFactPayloadError,
    Rational,
    RequiredQuantity,
    RollContext,
    ScalingBasis,
    TimePeriod,
    TimeUnit,
    fact_from_payload,
    fact_payload,
)
from afterworlds.ingestion.mechanical.schema_lift import SCHEMA_5_HASH, SCHEMA_5_VERSION
from afterworlds.persistence.orm.mechanical import (
    MechanicalComponentORM,
    MechanicalFactORM,
)
from afterworlds.services.rules_authority.patches import InvalidPatchError
from tests.ingestion.mechanical.conftest import (
    NOW,
    RELEASE_BINDING,
    build_ledger,
    build_representation,
    candidate_of,
)

ARTIFACT_PATH = COMMITTED_ORACLE_DIR / "srd-5-2-1-corpus-36b786d8-fa2.json"
D6 = DiceExpression(count=1, die=DieSize.D6)
FALL_INTERVAL = DamageInterval(
    basis=ScalingBasis.DISTANCE_FALLEN, amount=10, unit=DistanceUnit.FOOT
)
FALLING = DamageFact(
    damage_type=DamageType.BLUDGEONING, dice=D6, maximum_dice=20, per=FALL_INTERVAL
)
PLAIN = DamageFact(damage_type=DamageType.BLUDGEONING, dice=D6, maximum_dice=20)
CON_SAVE = AbilityCheckFact(
    ability=AbilityScore.CONSTITUTION,
    dc_kind=DcKind.FIXED,
    dc_value=10,
    context=RollContext.SAVING_THROW,
)
CON_CHECK = AbilityCheckFact(
    ability=AbilityScore.CONSTITUTION,
    dc_kind=DcKind.FIXED,
    dc_value=10,
    context=RollContext.ABILITY_CHECK,
)
NO_FOOD = Applicability(
    kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
    band=ConsumptionBand(
        quantity=RequiredQuantity.FOOD,
        period=TimePeriod.DAY,
        lower=Rational(0, 1),
        lower_inclusive=True,
        upper=Rational(0, 1),
        upper_inclusive=True,
        sustained_at_least=5,
        sustained_unit=TimeUnit.DAY,
    ),
)
PARTIAL_FOOD = Applicability(
    kind=ApplicabilityKind.CONSUMPTION_THRESHOLD,
    band=ConsumptionBand(
        quantity=RequiredQuantity.FOOD,
        period=TimePeriod.DAY,
        lower=Rational(0, 1),
        upper=Rational(1, 2),
    ),
)


def _with_first_component(**changes: object):
    representation = build_representation()
    components = list(representation.components)
    components[0] = replace(components[0], **changes)  # type: ignore[arg-type]
    return replace(representation, components=tuple(components))


def _persist(session: Session, representation):
    identified = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), representation)
    )
    persist_draft(session, identified, now=NOW)
    record_persisted_state_digest(session, identified.projection_uuid)
    session.flush()
    return identified


def _with_fact(fact):
    """The bounded fixture with one extra fact on its first component."""
    representation = build_representation()
    components = list(representation.components)
    components[0] = replace(components[0], facts=(*components[0].facts, fact))
    return replace(representation, components=tuple(components))


# ---------------------------------------------------------------------------
# The roll context
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fact", [CON_SAVE, CON_CHECK], ids=["save", "check"])
def test_a_roll_context_survives_the_round_trip(
    session: Session, fact: AbilityCheckFact
) -> None:
    identified = _persist(session, _with_fact(fact))
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    stored = [
        f
        for c in rebuilt.representation.components
        for f in c.facts
        if isinstance(f, AbilityCheckFact)
    ]
    assert stored == [fact]
    assert stored[0].context is fact.context
    assert verify_persisted_state(session, identified.projection_uuid) == ()


def test_the_roll_context_is_identity_bearing_in_storage(session: Session) -> None:
    """A save and a check are two projections and two persisted digests.

    The point of the whole succession, asserted where it finally has to hold: if
    storage could not tell them apart, the typed distinction would be lost the
    first time authority was written down.
    """
    save = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with_fact(CON_SAVE))
    )
    check = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with_fact(CON_CHECK))
    )
    assert save.projection_uuid != check.projection_uuid

    persist_draft(session, save, now=NOW)
    record_persisted_state_digest(session, save.projection_uuid)
    persist_draft(session, check, now=NOW)
    record_persisted_state_digest(session, check.projection_uuid)
    session.flush()
    assert compute_persisted_state_digest(
        session, save.projection_uuid
    ) != compute_persisted_state_digest(session, check.projection_uuid)


def test_a_stored_context_outside_the_vocabulary_fails_reconstruction(
    session: Session,
) -> None:
    identified = _persist(session, _with_fact(CON_SAVE))
    row = session.scalars(
        select(MechanicalFactORM).where(MechanicalFactORM.family == "ability_check")
    ).one()
    payload = dict(row.payload)
    payload["context"] = "vibes"
    session.execute(
        update(MechanicalFactORM)
        .where(MechanicalFactORM.fact_id == row.fact_id)
        .values(payload=payload)
    )
    session.flush()
    with pytest.raises(PersistedStateReconstructionError):
        reconstruct_candidate(session, identified.projection_uuid)


def test_a_stored_fact_missing_its_context_fails_reconstruction(
    session: Session,
) -> None:
    """Required means required in storage too: no silent default on the way back."""
    payload = dict(fact_payload(CON_SAVE))
    del payload["context"]
    with pytest.raises(MalformedFactPayloadError, match="missing"):
        fact_from_payload(payload)


# ---------------------------------------------------------------------------
# The damage interval
# ---------------------------------------------------------------------------


def test_a_damage_interval_survives_the_round_trip(session: Session) -> None:
    identified = _persist(session, _with_fact(FALLING))
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    stored = [
        f
        for c in rebuilt.representation.components
        for f in c.facts
        if isinstance(f, DamageFact) and f.per is not None
    ]
    assert stored == [FALLING]
    assert stored[0].per == FALL_INTERVAL
    assert verify_persisted_state(session, identified.projection_uuid) == ()


def test_a_damage_without_an_interval_reconstructs_as_none(session: Session) -> None:
    """Absence is a real state — most damage is not dealt per anything."""
    identified = _persist(session, _with_fact(PLAIN))
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    stored = [
        f
        for c in rebuilt.representation.components
        for f in c.facts
        if isinstance(f, DamageFact)
    ]
    assert stored == [PLAIN]
    assert stored[0].per is None


def test_the_interval_is_identity_bearing_in_storage(session: Session) -> None:
    """1d6 per 10 feet is not 1d6, and the two must not share a projection."""
    per = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with_fact(FALLING))
    )
    flat = identify_projection(
        candidate_of(RELEASE_BINDING, build_ledger(), _with_fact(PLAIN))
    )
    assert per.projection_uuid != flat.projection_uuid


def test_a_stored_interval_outside_the_vocabulary_fails_reconstruction(
    session: Session,
) -> None:
    identified = _persist(session, _with_fact(FALLING))
    row = session.scalars(
        select(MechanicalFactORM).where(MechanicalFactORM.family == "damage")
    ).one()
    payload = dict(row.payload)
    payload["per"] = {"basis": "character_level", "amount": 10, "unit": "foot"}
    session.execute(
        update(MechanicalFactORM)
        .where(MechanicalFactORM.fact_id == row.fact_id)
        .values(payload=payload)
    )
    session.flush()
    with pytest.raises(PersistedStateReconstructionError):
        reconstruct_candidate(session, identified.projection_uuid)


# ---------------------------------------------------------------------------
# The consumption band
# ---------------------------------------------------------------------------


def test_a_consumption_band_survives_the_round_trip(session: Session) -> None:
    identified = _persist(session, _with_first_component(applies_when=NO_FOOD))
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.representation.components[0].applies_when == NO_FOOD
    band = rebuilt.representation.components[0].applies_when.band  # type: ignore[union-attr]
    assert band is not None
    assert band.sustained_at_least == 5
    assert band.lower_inclusive is True
    assert verify_persisted_state(session, identified.projection_uuid) == ()


def test_no_applicability_reconstructs_as_none(session: Session) -> None:
    identified = _persist(session, _with_first_component(applies_when=None))
    rebuilt = reconstruct_candidate(session, identified.projection_uuid)
    assert rebuilt.representation.components[0].applies_when is None


def test_the_band_is_identity_bearing_and_moves_the_digest(session: Session) -> None:
    """The two Malnutrition paths are two projections in storage.

    Under schema 4 both reduced to ``< 1/2`` and shared one payload, so this is
    the collapse closing where it would otherwise have been written down.
    """
    none = identify_projection(
        candidate_of(
            RELEASE_BINDING, build_ledger(), _with_first_component(applies_when=NO_FOOD)
        )
    )
    partial = identify_projection(
        candidate_of(
            RELEASE_BINDING,
            build_ledger(),
            _with_first_component(applies_when=PARTIAL_FOOD),
        )
    )
    assert none.projection_uuid != partial.projection_uuid

    persist_draft(session, none, now=NOW)
    record_persisted_state_digest(session, none.projection_uuid)
    persist_draft(session, partial, now=NOW)
    record_persisted_state_digest(session, partial.projection_uuid)
    session.flush()
    assert compute_persisted_state_digest(
        session, none.projection_uuid
    ) != compute_persisted_state_digest(session, partial.projection_uuid)


def test_a_stored_band_missing_a_key_fails_reconstruction(session: Session) -> None:
    """Every band key is required on the wire: an omitted bound would rebuild as
    unbounded, which is a wider band than the one that was written."""
    identified = _persist(session, _with_first_component(applies_when=NO_FOOD))
    row = session.scalars(
        select(MechanicalComponentORM).where(
            MechanicalComponentORM.applies_when.isnot(None)
        )
    ).first()
    assert row is not None
    stored = dict(row.applies_when)
    band = dict(stored["band"])
    del band["upper"]
    stored["band"] = band
    session.execute(
        update(MechanicalComponentORM)
        .where(MechanicalComponentORM.component_id == row.component_id)
        .values(applies_when=stored)
    )
    session.flush()
    with pytest.raises(PersistedStateReconstructionError):
        reconstruct_candidate(session, identified.projection_uuid)


def test_a_stored_band_that_names_no_share_fails_reconstruction(
    session: Session,
) -> None:
    """The typed invariant is enforced on the way back in, not only on the way out."""
    identified = _persist(session, _with_first_component(applies_when=NO_FOOD))
    row = session.scalars(
        select(MechanicalComponentORM).where(
            MechanicalComponentORM.applies_when.isnot(None)
        )
    ).first()
    assert row is not None
    stored = dict(row.applies_when)
    band = dict(stored["band"])
    band["lower"] = {"numerator": 1, "denominator": 1}
    band["upper"] = {"numerator": 1, "denominator": 2}
    stored["band"] = band
    session.execute(
        update(MechanicalComponentORM)
        .where(MechanicalComponentORM.component_id == row.component_id)
        .values(applies_when=stored)
    )
    session.flush()
    with pytest.raises(PersistedStateReconstructionError):
        reconstruct_candidate(session, identified.projection_uuid)


# ---------------------------------------------------------------------------
# The override patch seam reads the same contract
# ---------------------------------------------------------------------------


def test_the_patch_loader_rebuilds_a_band(session: Session) -> None:
    """Three loaders read an applicability; the band has one implementation.

    A second spelling in the patch path is how the committed loader and the
    override loader would come to disagree about what a stored band means.
    """
    from afterworlds.ingestion.mechanical.projection import applicability_payload
    from afterworlds.services.rules_authority.patches import _build_applicability

    rebuilt = _build_applicability(applicability_payload(NO_FOOD), "fixture")
    assert rebuilt == NO_FOOD


def test_the_patch_loader_refuses_a_malformed_band() -> None:
    from afterworlds.ingestion.mechanical.projection import applicability_payload
    from afterworlds.services.rules_authority.patches import _build_applicability

    payload = applicability_payload(NO_FOOD)
    payload["band"] = dict(payload["band"])  # type: ignore[arg-type]
    payload["band"]["sustained_unit"] = "fortnight"  # type: ignore[index]
    with pytest.raises(InvalidPatchError):
        _build_applicability(payload, "fixture")


# ---------------------------------------------------------------------------
# The committed-accepted-authority loader reads the same band contract
# ---------------------------------------------------------------------------
#
# Three loaders rebuild an applicability, and schema 5 consolidated all three
# onto one ``build_consumption_band`` so they cannot drift. Two are proved
# above — persistence by round trip, the patch path by its own case. This is
# the third, and the one that reads what the Owner actually signed off, so it
# is exercised against a real file through ``load_accepted_inputs`` rather than
# by calling the shared builder again.


def _artifact_with_band(band: object, tmp_path: object, name: str) -> Path:
    """The committed artifact carrying one band, declared under schema 5.

    A band *is* schema-5 meaning, so the declaration has to move with it or the
    legality guard refuses the file before the key shape is ever read — and the
    test would then pass for the wrong reason. Moving the declaration means
    anchoring the batches, which is the shape the evidence rules admit.
    """
    raw = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    raw["representation"]["components"][0]["applies_when"] = {
        "kind": "consumption_threshold",
        "negated": False,
        "quantity": None,
        "comparison": None,
        "value": None,
        "any_of": [],
        "trigger": None,
        "phase": None,
        "band": band,
    }
    raw["representation_schema"] = {
        "version": SCHEMA_5_VERSION,
        "hash": SCHEMA_5_HASH,
    }
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


HONEST_BAND: dict[str, object] = {
    "quantity": "food",
    "period": "day",
    "lower": {"numerator": 0, "denominator": 1},
    "lower_inclusive": True,
    "upper": {"numerator": 0, "denominator": 1},
    "upper_inclusive": True,
    "sustained_at_least": 5,
    "sustained_unit": "day",
}


def test_the_committed_loader_rebuilds_a_band(tmp_path: object) -> None:
    """Every bound, both inclusivities, and the sustained duration come back."""
    loaded = load_accepted_inputs(
        _artifact_with_band(HONEST_BAND, tmp_path, "band.json")
    )
    applies_when = loaded.oracle.representation.components[0].applies_when
    assert applies_when is not None
    band = applies_when.band
    assert band is not None
    assert band.quantity is RequiredQuantity.FOOD
    assert band.period is TimePeriod.DAY
    assert (band.lower, band.lower_inclusive) == (Rational(0, 1), True)
    assert (band.upper, band.upper_inclusive) == (Rational(0, 1), True)
    assert (band.sustained_at_least, band.sustained_unit) == (5, TimeUnit.DAY)


@pytest.mark.parametrize(
    ("name", "band", "expected"),
    [
        (
            "an omitted bound",
            {k: v for k, v in HONEST_BAND.items() if k != "upper"},
            "missing",
        ),
        (
            "an undeclared unit",
            {**HONEST_BAND, "sustained_unit": "fortnight"},
            "sustained_unit",
        ),
        (
            "a band that names no share",
            {
                **HONEST_BAND,
                "lower": {"numerator": 1, "denominator": 1},
                "upper": {"numerator": 1, "denominator": 2},
            },
            "above its upper bound",
        ),
        ("an extra key", {**HONEST_BAND, "extra": 1}, "extra"),
    ],
)
def test_the_committed_loader_refuses_a_malformed_band(
    name: str, band: dict[str, object], expected: str, tmp_path: object
) -> None:
    """An omitted bound would rebuild as *unbounded* — a wider band than the one
    that was written, which is the silent widening this succession exists to
    stop. Every failure is the loader's own typed error, not a raw exception."""
    path = _artifact_with_band(band, tmp_path, "malformed.json")
    with pytest.raises(OracleLoadError) as raised:
        load_accepted_inputs(path)
    assert expected in str(raised.value), (name, raised.value)
