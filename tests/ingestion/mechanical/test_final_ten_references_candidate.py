"""The final-ten reference candidate, read back.

CRD Issues 5c/5d (#132, #137). The candidate drafted by
``.claude/review-notes/issue-5d-final-ten-references/candidate/CANDIDATE.py`` is
Owner-accepted and recorded (``issue-5d-final-ten-references-ACCEPT.py``), then
carried unchanged into the current release's recording, still unpublished. The
current committed oracle is persisted as a draft into a private copy of the
current release and read back through
:meth:`~afterworlds.services.rules_authority.service.RulesAuthorityService.citation_view`
as in ``test_equipment_spell_references_candidate``. The control is that
oracle without the ten resolutions the final-ten recording appended over the
equipment-spell-references recording, persisted the same way into a second copy.
Both sides are the current release; the superseded release's file is not
persisted into it.

Each citation's unfiltered read of the immutable candidate is taken once and
shared by the content assertions; changed selections, overrides and the control
are fresh native reads.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Any
from uuid import UUID

import pytest

from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import persist_draft
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.services.rules_authority.application import (
    AuthoredProse,
    SourceProse,
)
from afterworlds.services.rules_authority.binding import BindingResolution
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import (
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
)
from afterworlds.services.rules_authority.service import RulesAuthorityService
from afterworlds.services.rules_authority.targets import MechanicalTargetKind
from tests.ingestion.mechanical._replacement_chain import (
    current,
    equipment_spell_references_recorded,
)
from tests.ingestion.mechanical.test_finite_reference_routes_candidate import (
    ANY,
    NOW,
    WIZARD,
    _disable,
    _order,
    _read,
)

REPO = Path(__file__).resolve().parents[3]
HARNESS = (
    REPO / ".claude/review-notes/issue-5d-final-ten-references/candidate/CANDIDATE.py"
)
HOUSE_RULE = Path(__file__).resolve().parent / "data/awakened-plant-house-rule.md"
AWAKEN = ("spells.awaken", "effect")
FIGURINE = "Figurine of Wondrous Power"


def _harness() -> ModuleType:
    name = "final_ten_references_candidate"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


H = _harness()
ROWS = {row: citation for citation, (row, _) in H.DRAFTS.items()}


def _persist(tmp_path_factory, source_release_db, inputs: AcceptedInputs, name: str):  # type: ignore[no-untyped-def]
    path = tmp_path_factory.mktemp(name) / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(candidate_from_accepted_inputs(inputs))
        persist_draft(s, identified, now=NOW)
        s.commit()
        yield s, identified.projection_uuid, inputs.oracle.binding
    engine.dispose()


@pytest.fixture(scope="module")
def accepted() -> AcceptedInputs:
    """The prior: the current oracle without the ten appended resolutions.

    Which ten is read from the recordings: the resolutions the final-ten
    recording holds beyond the equipment-spell-references recording it appended
    over. Resolution ids do not name a release.
    """
    final = current()
    prior_ids = {
        r.resolution_id
        for r in equipment_spell_references_recorded().oracle.reference_resolutions
    }
    final_ids = {
        r.resolution_id
        for r in load_accepted_inputs(H.ACCEPTED_PATH).oracle.reference_resolutions
    }
    assert len(final_ids - prior_ids) == 10 and prior_ids < final_ids
    assert final_ids == {r.resolution_id for r in final.oracle.reference_resolutions}
    kept = tuple(
        r for r in final.oracle.reference_resolutions if r.resolution_id in prior_ids
    )
    return replace(final, oracle=replace(final.oracle, reference_resolutions=kept))


@pytest.fixture(scope="module")
def candidate(tmp_path_factory, source_release_db):  # type: ignore[no-untyped-def]
    """The current committed oracle, persisted into a private release copy."""
    yield from _persist(tmp_path_factory, source_release_db, current(), "final-ten")


@pytest.fixture(scope="module")
def control(tmp_path_factory, source_release_db, accepted):  # type: ignore[no-untyped-def]
    """The prior: the ten resolutions absent."""
    yield from _persist(
        tmp_path_factory, source_release_db, accepted, "final-ten-control"
    )


@pytest.fixture(scope="module")
def views(candidate):  # type: ignore[no-untyped-def]
    """Each citation's unfiltered read of the immutable candidate, read once."""
    out = {}
    with pytest.MonkeyPatch.context() as mp:
        for row in sorted(ROWS):
            result = _read(candidate, mp, ROWS[row], ANY)
            assert result.outcome is AuthorityOutcome.RESOLVED, (row, result.detail)
            out[row] = result
    return out


def _records(result) -> list[str]:  # type: ignore[no-untyped-def]
    return list(dict.fromkeys(r for r, _ in _order(result)))


def _record_text(result, record: str) -> str:  # type: ignore[no-untyped-def]
    return " ".join(
        e.text or ""
        for c in result.gamemaster_view.components
        if c.record_key == record
        for e in c.governing_prose
    )


def _route(result, label: str) -> list[str]:  # type: ignore[no-untyped-def]
    return [r for r, _ in dict(result.routes)[label]]


def _gamemaster(persisted, monkeypatch, record: str, *entries):  # type: ignore[no-untyped-def]
    """One record's GameMaster view, bound as ``_read`` binds a citation."""
    session, projection_uuid, release = persisted
    state = EffectiveOverrideSet(release.package_uuid, release.release_version, entries)
    binding = RulesPackageBinding(
        package_uuid=UUID(release.package_uuid),
        release_version=release.release_version,
        mechanical_projection_uuid=UUID(projection_uuid),
        override_set_uuid=UUID(state.override_set_uuid),
    )
    service = RulesAuthorityService(session, now=NOW)
    monkeypatch.setattr(
        service,
        "resolve",
        lambda **_: BindingResolution(
            AuthorityOutcome.RESOLVED, binding=binding, override_state=state
        ),
    )
    return service.gamemaster_view(
        RuleSliceRequest(
            package_id=UUID(release.package_uuid), record_selectors=(record,)
        )
    )


def _awakened_plant() -> EffectiveOverrideEntry:
    """The Owner's supplement as one house-rule prose addition to Awaken."""
    # The Owner-authored prose of docs/house-rules/awakened-plant.md, verbatim.
    text = HOUSE_RULE.read_text(encoding="utf-8").rstrip()
    disabled = _disable(AWAKEN[0])
    return replace(
        disabled,
        override_id="house-rule-awakened-plant",
        target=replace(
            disabled.target, kind=MechanicalTargetKind.PROSE, component_key=AWAKEN[1]
        ),
        operation=OverrideOperationEnum.APPEND,
        payload={"patch": "append_prose", "text": text},
    )


@pytest.mark.parametrize("row", sorted(ROWS))
def test_the_control_refuses_every_drafted_citation(control, monkeypatch, row) -> None:  # type: ignore[no-untyped-def]
    """Without the proposed resolutions the reader fails closed."""
    result = _read(control, monkeypatch, ROWS[row], ANY)
    assert result.outcome is AuthorityOutcome.INVALID_REFERENCE


@pytest.mark.parametrize("row", sorted(ROWS))
def test_every_route_reads_as_drafted(views, row) -> None:  # type: ignore[no-untyped-def]
    """Every labelled route and destination, in drafted order."""
    _, destinations = H.DRAFTS[ROWS[row]]
    drafted: dict[str, list[tuple[str, str]]] = {}
    for d in destinations:
        # One destination is a plain target: the reader reports no label.
        label = d.alternative_label if len(destinations) > 1 else ""
        drafted.setdefault(label, []).append((d.target_record_key, ""))
    assert [(label, list(ds)) for label, ds in views[row].routes] == list(
        drafted.items()
    )
    assert {d.target_record_key for d in destinations} <= set(_records(views[row]))


def test_a_class_selection_chooses_nothing(candidate, monkeypatch, views) -> None:  # type: ignore[no-untyped-def]
    """No new route declares a class condition; one representative suffices."""
    wizard = _read(candidate, monkeypatch, ROWS["#54"], WIZARD)
    assert wizard.outcome is AuthorityOutcome.RESOLVED, wizard.detail
    assert wizard.routes == views["#54"].routes


def test_34_exposes_priced_equipment_including_food_and_drink(views) -> None:  # type: ignore[no-untyped-def]
    result = views["#34"]
    ((label, _),) = result.routes
    assert label.endswith("and the priced goods of Food, Drink, and Lodging")
    records = _records(result)
    assert records.index("equipment.mounts_and_vehicles") < records.index(
        "equipment.food_drink_and_lodging"
    )
    # Glaive has no item record: its 20 GP is the Weapons table's row.
    weapons = _record_text(result, "equipment.weapons")
    assert "<td>Glaive</td>" in weapons and "<td>20 GP</td>" in weapons
    plate = _record_text(result, "equipment.armor.plate_armor")
    assert "<td>Plate Armor</td>" in plate and "<td>1,500 GP</td>" in plate
    food = _record_text(result, "equipment.food_drink_and_lodging")
    for good, cost in (
        ("Ale (mug)", "4 CP"),
        ("Bread (loaf)", "2 CP"),
        ("Cheese (wedge)", "1 SP"),
    ):
        assert f"<td>{good}</td>\n      <td>{cost}</td>" in food, good
    assert "Wine (bottle)" in food and "<td>10 GP</td>" in food
    # The service rows stay in their own table sections, with their prose.
    assert "Inn Stay per Day" in food and "<em>Meal</em>" in food
    assert "included in your lifestyle's expenses" in food
    assert "equipment.lifestyle_expenses" not in records


def test_36_wand_reads_its_arcane_focus_row(views) -> None:  # type: ignore[no-untyped-def]
    result = views["#36"]
    assert len(result.routes) == 39
    assert _route(result, "Gear: Wand") == [
        "equipment.adventuring_gear.wand",
        "equipment.adventuring_gear.arcane_focus",
    ]
    # The Arcane Focuses table's Wand row is the Wand record's own price.
    wand = _record_text(result, "equipment.adventuring_gear.wand")
    assert "<td>Wand</td>" in wand and "<td>10 GP</td>" in wand
    focus = _record_text(result, "equipment.adventuring_gear.arcane_focus")
    assert "can use such an item as a Spellcasting Focus" in focus


def test_39_reads_the_wizard_owned_spellbook(views) -> None:  # type: ignore[no-untyped-def]
    result = views["#39"]
    assert _records(result) == ["classes.wizard.spellcasting"]
    book = _record_text(result, "classes.wizard.spellcasting")
    assert "your spellbook. It is a Tiny object that weighs 3 pounds" in book
    assert "your spellbook as a Spellcasting Focus" in book


@pytest.mark.parametrize("row", ["#48", "#60"])
def test_familiar_forms_keep_the_local_giant_fly(views, row) -> None:  # type: ignore[no-untyped-def]
    result = views[row]
    labels = [label for label, _ in result.routes]
    assert sum(label.startswith("Normal form: ") for label in labels) == 25
    assert len(labels) == (32 if row == "#48" else 25)
    fly = "magic_items.figurine_of_wondrous_power.giant_fly"
    assert _route(result, "Normal form: Giant Fly (Magic Items stat block)") == [fly]
    assert "##### Giant Fly _Large Beast, Unaligned_" in _record_text(result, fly)
    if row == "#48":
        # The Pact also keeps its seven named special forms.
        assert sum(label.startswith("Special form: ") for label in labels) == 7
    # The Pact reads its own forms, not Find Familiar's citation.
    assert "spells.find_familiar" not in _records(result)


def test_54_reads_bestiary_statistics_with_local_modifications(views) -> None:  # type: ignore[no-untyped-def]
    result = views["#54"]
    assert len(result.routes) == 42
    fly = "magic_items.figurine_of_wondrous_power.giant_fly"
    assert _route(result, f"{FIGURINE}: Ebony Fly: Giant Fly (local stat block)") == [
        fly,
        "magic_items.figurine_of_wondrous_power",
    ]
    assert _route(result, f"{FIGURINE}: Onyx Dog: Mastiff") == [
        "animals.mastiff",
        "magic_items.figurine_of_wondrous_power",
    ]
    assert "Mastiff" in _record_text(result, "animals.mastiff")
    figurine = _record_text(result, "magic_items.figurine_of_wondrous_power")
    assert "The mastiff has an Intelligence of 8 and can speak Common" in figurine
    skull = "magic_items.mysterious_deck.avatar_of_death"
    assert (
        _route(result, "Mysterious Deck: Skull: Avatar of Death (local stat block)")[0]
        == skull
    )
    assert "##### Avatar of Death _Medium Undead, Neutral Evil_" in _record_text(
        result, skull
    )


def test_57_reads_the_srd_examples_only(views) -> None:  # type: ignore[no-untyped-def]
    result = views["#57"]
    assert [label for label, _ in result.routes] == [
        "GM's choice, SRD example: Awakened Shrub",
        "GM's choice, SRD example: Awakened Tree",
    ]
    assert "**_Rake._**" in _record_text(
        result, "monsters.awakened_plants.awakened_shrub"
    )
    assert "### Awakened Tree _Huge Plant, Neutral_" in _record_text(
        result, "monsters.awakened_plants.awakened_tree"
    )
    assert "**Awakened Plant**" not in " ".join(
        _record_text(result, r) for r in _records(result)
    )


def test_76_distinguishes_selection_modifier_and_examples(views) -> None:  # type: ignore[no-untyped-def]
    result = views["#76"]
    assert [label for label, _ in result.routes] == [
        "Which ability: D20 Test, Ability Check, Saving Throw and Attack Roll",
        "Applying the modifier: Ability Score and Modifier",
        "Specific rules naming their ability (examples): Hide, Search, Study, "
        "Unarmed Strike",
    ]
    # Proficiency stays the component's separate accepted pointer.
    assert "glossary.proficiency" not in _records(result)
    assert "play.proficiency" not in _records(result)


@pytest.mark.parametrize("row", ["#87", "#88"])
def test_cantrips_and_rituals_read_general_casting_rules(views, row) -> None:  # type: ignore[no-untyped-def]
    result = views[row]
    assert _records(result)[0] == "spells.casting_spells"
    text = _record_text(result, "spells.casting_spells")
    assert "**Cantrips.** A cantrip is cast without a spell slot." in text
    assert "The Ritual version of a spell takes 10 minutes longer to cast" in text


def test_a_disabled_destination_refuses_and_an_unrelated_one_does_not(  # type: ignore[no-untyped-def]
    candidate, monkeypatch
) -> None:
    gone = _read(
        candidate, monkeypatch, ROWS["#87"], ANY, _disable("spells.casting_spells")
    )
    assert gone.outcome is AuthorityOutcome.INVALID_REFERENCE
    kept = _read(
        candidate, monkeypatch, ROWS["#39"], ANY, _disable("magic_items.berserker_axe")
    )
    assert kept.outcome is AuthorityOutcome.RESOLVED, kept.detail


def test_the_awakened_plant_house_rule_appends_in_isolation(  # type: ignore[no-untyped-def]
    candidate, monkeypatch, views
) -> None:
    """Draft presentation only: an isolated house-rule prose addition to Awaken.

    Nothing is installed or activated. The supplement is authored prose with
    Afterworlds house-rule provenance after Awaken's unchanged SRD prose; it is
    not an SRD creature, record or citation destination.
    """
    plant = _awakened_plant()
    text = plant.payload["text"]
    assert isinstance(text, str)
    assert "**Hit Points:** 3 (1d6)" in text and "2 (1d6)" not in text
    assert "**False Appearance.**" in text and "None. Non-combatant." in text

    def effect(result: Any) -> tuple[Any, ...]:
        assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
        (found,) = [
            c
            for c in result.gamemaster_view.components
            if (c.record_key, c.component_key) == AWAKEN
        ]
        return tuple(found.governing_prose)

    base = effect(_gamemaster(candidate, monkeypatch, AWAKEN[0]))
    house = _gamemaster(candidate, monkeypatch, AWAKEN[0], plant)
    *source, added = effect(house)
    assert tuple(source) == base
    assert all(isinstance(e, SourceProse) for e in source)
    assert "such as the statistics for the **Awakened Shrub**" in " ".join(
        e.text or "" for e in source
    )
    assert added == AuthoredProse(
        text=text,
        supplied_by_override_id=plant.override_id,
        supplied_by_origin=OverrideOriginEnum.HOUSE_RULE,
    )
    assert [a.override_id for a in house.gamemaster_view.applied_overrides] == [
        plant.override_id
    ]
    # No SRD record or citation destination: reference 57 reads as before.
    with_plant = _read(candidate, monkeypatch, ROWS["#57"], ANY, plant)
    assert with_plant.outcome is AuthorityOutcome.RESOLVED, with_plant.detail
    assert with_plant.routes == views["#57"].routes
    assert _records(with_plant) == _records(views["#57"])
