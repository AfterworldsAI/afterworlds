"""The finite-reference-routes recording, read through the production reader.

CRD Issue 5d (#132, #137). The Owner accepted the routes drafted by
``.claude/review-notes/issue-5d-finite-reference-routes-REPLACEMENT.py`` and
its combat-damage-breaking replacement;
``issue-5d-finite-reference-routes-ACCEPT.py`` recorded them in the committed
oracle (unpublished; the partial-publication block stays). The recorded
oracle is persisted as a draft into a private copy of the release, and read
back through
:meth:`~afterworlds.services.rules_authority.service.RulesAuthorityService.citation_view`.
Only binding resolution is stood in, as in the other draft-read tests.
Reconstruction, override application, selection and the GameMaster view are
the production path.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType
from uuid import UUID

import pytest

from afterworlds.ingestion.mechanical.oracle import (
    candidate_from_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import persist_draft
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.reference_resolution import (
    AlternativeSelection,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RuleSliceRequest, RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.services.rules_authority.binding import BindingResolution
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import (
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
)
from afterworlds.services.rules_authority.service import RulesAuthorityService
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)
from tests.ingestion.mechanical._replacement_chain import current

HARNESS = (
    Path(__file__).resolve().parents[3]
    / ".claude/review-notes/issue-5d-finite-reference-routes-REPLACEMENT.py"
)
NOW = "2026-10-01T00:00:00Z"
MONSTERS = "srd-5.2.1/monsters"
GEM = ("magic_items.elemental_gem", "elemental_gem", "Monsters", MONSTERS)
MOUNTS = ("equipment.mounts_and_vehicles", "mounts", "Monsters", MONSTERS)
ATTACKS = (
    "monsters.parts_of_a_stat_block",
    "attack_notation",
    "Playing the Game",
    "srd-5.2.1/playing-the-game",
)
READING = (
    "magic_items.magic_items_a_z",
    "magic_items_a_z",
    'How to read and use a stat block is explained in "Monsters."',
    MONSTERS,
)
FOCUS = (
    "spells.components",
    "component_pouch_and_focus",
    'see "Equipment" for descriptions',
    "srd-5.2.1/equipment",
)
INSTRUMENT = (
    "Musical Instrument: a Bard can use it as a Spellcasting Focus for Bard spells"
)
ANY = AlternativeSelection()
WIZARD = AlternativeSelection(class_levels={"classes.wizard": 5})


def _harness() -> ModuleType:
    name = "finite_reference_routes_replacement"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db):  # type: ignore[no-untyped-def]
    """The current committed oracle, persisted into a private copy of the
    current release (the superseded file is not persisted into it)."""
    final = current()
    path = tmp_path_factory.mktemp("finite-routes") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(candidate_from_accepted_inputs(final))
        persist_draft(s, identified, now=NOW)
        s.commit()
        yield s, identified.projection_uuid, final.oracle.binding
    engine.dispose()


def _disable(record_key: str) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
        override_id=f"disable-{record_key}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.RECORD, record_key=record_key
        ),
        operation=OverrideOperationEnum.DISABLE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={"patch": "disable"},
    )


def _read(  # type: ignore[no-untyped-def]
    persisted,
    monkeypatch,
    citation: tuple[str, str, str, str],
    selection: AlternativeSelection,
    *entries: EffectiveOverrideEntry,
):
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
    request = RuleSliceRequest(
        package_id=UUID(release.package_uuid), whole_package=True
    )
    return service.citation_view(request, citation=citation, selection=selection)


def _order(result) -> list[tuple[str, str]]:  # type: ignore[no-untyped-def]
    return [(c.record_key, c.component_key) for c in result.gamemaster_view.components]


def _text(result, record: str, component: str) -> str:  # type: ignore[no-untyped-def]
    (found,) = [
        c
        for c in result.gamemaster_view.components
        if (c.record_key, c.component_key) == (record, component)
    ]
    return " ".join(e.text or "" for e in found.governing_prose)


@pytest.mark.parametrize("row", sorted({row for row, _ in _harness().DRAFTS.values()}))
def test_every_route_reads_as_drafted(persisted, monkeypatch, row: str) -> None:  # type: ignore[no-untyped-def]
    """Unknown reader state: every labelled route, in drafted order."""
    ((citation, (_, destinations)),) = [
        (c, v) for c, v in _harness().DRAFTS.items() if v[0] == row
    ]
    result = _read(persisted, monkeypatch, citation, ANY)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    drafted: dict[str, list[tuple[str, str]]] = {}
    for d in destinations:
        drafted.setdefault(d.alternative_label, []).append(
            (d.target_record_key, d.target_component_key)
        )
    assert [(label, list(ds)) for label, ds in result.routes] == list(drafted.items())


def test_a_class_selection_does_not_choose_a_gem(persisted, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """The gem, card, roll and list labels are not class conditions."""
    result = _read(persisted, monkeypatch, GEM, WIZARD)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert [label for label, _ in result.routes] == [
        "Blue sapphire: Air Elemental",
        "Emerald: Water Elemental",
        "Red corundum: Fire Elemental",
        "Yellow diamond: Earth Elemental",
    ]


def test_melee_or_ranged_reads_both_in_order(persisted, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    result = _read(persisted, monkeypatch, ATTACKS, ANY)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    combined = dict(result.routes)[
        "Melee or Ranged attack: Ranged Attacks and Melee Attacks"
    ]
    assert [c for _, c in combined] == [
        "ranged",
        "range",
        "long_range",
        "close_combat",
        "melee",
        "reach",
        "opportunity_attacks",
    ]
    ranged = dict(result.routes)["Ranged attack: Ranged Attacks"]
    assert list(ranged) == list(combined[:4])
    # The section introduction, whole, then every Ranged and Melee rule.
    assert _text(result, "play.combat", "ranged") == _harness().RANGED_INTRO
    assert "single range" in _text(result, "play.combat", "range")
    assert "beyond long range" in _text(result, "play.combat", "long_range")
    assert "Disadvantage" in _text(result, "play.combat", "close_combat")
    assert "reach" in _text(result, "play.combat", "melee")
    assert "5-foot reach" in _text(result, "play.combat", "reach")
    assert _text(result, "play.combat", "opportunity_attacks")


@pytest.mark.parametrize("selection", [ANY, WIZARD], ids=["any", "wizard"])
def test_the_instrument_route_keeps_the_bard_grant(  # type: ignore[no-untyped-def]
    persisted, monkeypatch, selection: AlternativeSelection
) -> None:
    """The Bard feature carries the condition; no class selection removes it."""
    result = _read(persisted, monkeypatch, FOCUS, selection)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    routes = dict(result.routes)
    assert list(routes)[0] == INSTRUMENT
    assert list(routes[INSTRUMENT]) == [
        ("equipment.tools.musical_instrument", ""),
        ("classes.bard.spellcasting", "spellcasting_focus"),
    ]
    assert ("equipment.tools.musical_instrument", "musical_instrument") in _order(
        result
    )
    grant = _text(result, "classes.bard.spellcasting", "spellcasting_focus")
    assert "Musical Instrument as a Spellcasting Focus for your Bard spells" in grant


def test_reading_a_stat_block_lands_on_the_overview(persisted, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    result = _read(persisted, monkeypatch, READING, ANY)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    records = list(dict.fromkeys(r for r, _ in _order(result)))
    assert records[0] == "monsters.stat_block_overview"
    # Challenge Rating is reached one CATALOGUE_MEMBER hop from the parts.
    assert "monsters.parts_of_a_stat_block.challenge_rating" in records


def test_a_disabled_destination_refuses_and_an_unrelated_one_does_not(  # type: ignore[no-untyped-def]
    persisted, monkeypatch
) -> None:
    gone = _read(persisted, monkeypatch, MOUNTS, ANY, _disable("animals.camel"))
    assert gone.outcome is AuthorityOutcome.INVALID_REFERENCE
    other = _disable("animals.tiger")
    kept = _read(persisted, monkeypatch, MOUNTS, ANY, other)
    assert kept.outcome is AuthorityOutcome.RESOLVED, kept.detail
    assert [a.override_id for a in kept.gamemaster_view.applied_overrides] == [
        other.override_id
    ]


def test_the_other_stat_block_occurrence_stays_unresolved() -> None:
    """Out of this batch: no draft names it."""
    other = (*READING[:2], 'the stat block is in "Monsters."', MONSTERS)
    assert other not in _harness().DRAFTS
