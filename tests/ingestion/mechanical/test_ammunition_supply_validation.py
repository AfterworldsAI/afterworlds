"""Schema 20 ``ammunition_supply``: the relational rule (CRD Issue 15c C7).

A narrowed supply must name accepted Ammunition weapons of its own kind, and
no weapon may be claimed by two narrowed rows of one kind. Shaped on raw
candidate C7's five Ammunition table rows and the weapon rows they cite.
"""

from __future__ import annotations

import pytest

from afterworlds.ingestion.mechanical.representation import (
    AmmunitionKind,
    AmmunitionSupplyFact,
    ComponentDraft,
    ComponentHandling,
    ComponentReference,
    RecordDraft,
    RecordKind,
    RepresentationDraft,
    WeaponProperty,
    WeaponPropertyFact,
)
from afterworlds.ingestion.mechanical.validation import (
    _validate_ammunition_supplies,
    validate_representation,
)
from tests.ingestion.mechanical.conftest import bound_corpus, build_ledger

KIND = {"sling": "bullet", "musket": "bullet", "pistol": "bullet", "shortbow": "arrow"}


def _weapon(name: str) -> ComponentDraft:
    return ComponentDraft(
        record_key=f"equipment.weapons.{name}",
        semantic_key=name,
        handling=ComponentHandling.STRUCTURED,
        facts=(
            WeaponPropertyFact(
                weapon_property=WeaponProperty.AMMUNITION,
                ammunition=AmmunitionKind(KIND[name]),
                ammunition_range_normal_feet=30,
                ammunition_range_long_feet=120,
            ),
        ),
    )


def _ref(name: str) -> ComponentReference:
    return ComponentReference(
        record_key=f"equipment.weapons.{name}", component_key=name
    )


def _supply(name: str, kind: str, weapons: tuple[str, ...] | None) -> ComponentDraft:
    return ComponentDraft(
        record_key=f"equipment.adventuring_gear.{name}",
        semantic_key=name,
        handling=ComponentHandling.STRUCTURED,
        facts=(
            AmmunitionSupplyFact(
                kind=AmmunitionKind(kind),
                for_weapons=(
                    None if weapons is None else tuple(_ref(w) for w in weapons)
                ),
            ),
        ),
    )


DAGGER = ComponentDraft(
    record_key="equipment.weapons.dagger",
    semantic_key="dagger",
    handling=ComponentHandling.STRUCTURED,
    facts=(WeaponPropertyFact(weapon_property=WeaponProperty.FINESSE),),
)
WEAPONS = (*(_weapon(n) for n in KIND), DAGGER)
C7_SUPPLIES = (
    _supply("arrows", "arrow", None),
    _supply("bullets_sling", "bullet", ("sling",)),
    _supply("bullets_firearm", "bullet", ("musket", "pistol")),
)


def _draft(*supplies: ComponentDraft) -> RepresentationDraft:
    components = (*WEAPONS, *supplies)
    return RepresentationDraft(
        records=tuple(
            RecordDraft(semantic_key=c.record_key, kind=RecordKind.EQUIPMENT)
            for c in components
        ),
        components=components,
        prose_bindings=(),
        relationships=(),
        references=(),
        provenance=(),
    )


def test_c7_shaped_supplies_validate() -> None:
    assert _validate_ammunition_supplies(_draft(*C7_SUPPLIES)) == []


def test_a_weapon_without_the_ammunition_property_is_refused() -> None:
    (f,) = _validate_ammunition_supplies(
        _draft(_supply("arrows", "arrow", ("dagger",)))
    )
    assert "has no Ammunition weapon property" in f


def test_a_weapon_of_another_ammunition_kind_is_refused() -> None:
    (f,) = _validate_ammunition_supplies(
        _draft(_supply("bolts", "bolt", ("shortbow",)))
    )
    assert "not bolt" in f


def test_an_unresolved_reference_is_refused() -> None:
    (f,) = _validate_ammunition_supplies(
        _draft(_supply("needles", "needle", ("blowgun",)))
    )
    assert "not a component of this draft" in f


def test_two_narrowed_rows_of_one_kind_may_not_share_a_weapon() -> None:
    overlap = _supply("bullets_sling", "bullet", ("musket", "sling"))
    (f,) = _validate_ammunition_supplies(
        _draft(overlap, _supply("bullets_firearm", "bullet", ("musket", "pistol")))
    )
    assert "two bullet rows may not both claim one weapon" in f


def test_the_rule_runs_inside_validate_representation() -> None:
    """Wired into the candidate validation path, not only callable."""

    def supply_findings(draft: RepresentationDraft) -> list[str]:
        found = validate_representation(draft, build_ledger(), bound_corpus())
        return [f for f in found if "ammunition_supply" in f]

    assert supply_findings(_draft(*C7_SUPPLIES)) == []
    assert supply_findings(_draft(_supply("arrows", "arrow", ("dagger",))))


class _Tuple(tuple):  # type: ignore[type-arg]
    pass


def _malformed_supply(for_weapons: object) -> ComponentDraft:
    return ComponentDraft(
        record_key="equipment.adventuring_gear.bullets_sling",
        semantic_key="bullets_sling",
        handling=ComponentHandling.STRUCTURED,
        facts=(
            AmmunitionSupplyFact(
                kind=AmmunitionKind.BULLET,
                for_weapons=for_weapons,  # type: ignore[arg-type]
            ),
        ),
    )


def _malformed_weapon() -> ComponentDraft:
    return ComponentDraft(
        record_key="equipment.weapons.sling",
        semantic_key="sling",
        handling=ComponentHandling.STRUCTURED,
        facts=(
            WeaponPropertyFact(
                weapon_property=WeaponProperty.AMMUNITION,
                ammunition="bullet",  # type: ignore[arg-type]
            ),
        ),
    )


@pytest.mark.parametrize(
    ("draft", "refused"),
    [
        (_draft(_malformed_supply((0,))), "for_weapons[0] must be ComponentReference"),
        (
            _draft(_malformed_supply(_Tuple((_ref("sling"),)))),
            "for_weapons must be a tuple",
        ),
        (
            RepresentationDraft(
                records=(
                    RecordDraft(
                        semantic_key="equipment.weapons.sling",
                        kind=RecordKind.EQUIPMENT,
                    ),
                    RecordDraft(
                        semantic_key="equipment.adventuring_gear.bullets_sling",
                        kind=RecordKind.EQUIPMENT,
                    ),
                ),
                components=(
                    _malformed_weapon(),
                    _supply("bullets_sling", "bullet", ("sling",)),
                ),
                prose_bindings=(),
                relationships=(),
                references=(),
                provenance=(),
            ),
            "ammunition must be AmmunitionKind",
        ),
    ],
)
def test_refused_structure_is_reported_and_never_read_relationally(
    draft: RepresentationDraft, refused: str
) -> None:
    """The structural refusal is kept; the relational rule neither crashes
    on the refused value nor reports on it."""
    found = validate_representation(draft, build_ledger(), bound_corpus())
    assert any(refused in f for f in found), found
    assert not [f for f in found if "ammunition_supply names" in f]
    assert not [f for f in _validate_ammunition_supplies(draft) if refused in f]
