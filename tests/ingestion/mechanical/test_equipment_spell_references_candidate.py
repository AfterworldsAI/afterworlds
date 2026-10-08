"""The Equipment, cursed-item and spell references, read back.

CRD Issue 5d (#132, #137). The candidate drafted by
``.claude/review-notes/issue-5d-equipment-spell-references-CANDIDATE.py`` is
Owner-accepted and recorded (``issue-5d-equipment-spell-references-ACCEPT.py``),
then carried unchanged into the current release's recording, still
unpublished. The current committed oracle is persisted as a draft into a private
copy of the current release and read back through
:meth:`~afterworlds.services.rules_authority.service.RulesAuthorityService.citation_view`
as in ``test_final_ten_references_candidate``. The control is an in-memory
counterfactual, not an accepted artifact: that oracle without exactly the
thirteen resolutions the equipment-spell-references recording appended over the
finite-reference-routes recording, persisted the same way into a second copy.
Both sides are the current release; the superseded release's replayed
recordings only name which thirteen, and are not persisted into it.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from types import ModuleType

import pytest

from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    candidate_from_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import persist_draft
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.models.enums import OverrideOperationEnum
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import EffectiveOverrideEntry
from afterworlds.services.rules_authority.targets import MechanicalTargetKind
from tests.ingestion.mechanical._replacement_chain import (
    current,
    equipment_spell_references_recorded,
    finite_reference_routes_recorded,
)
from tests.ingestion.mechanical.test_finite_reference_routes_candidate import (
    ANY,
    NOW,
    WIZARD,
    _disable,
    _order,
    _read,
)

HARNESS = (
    Path(__file__).resolve().parents[3]
    / ".claude/review-notes/issue-5d-equipment-spell-references-CANDIDATE.py"
)


def _harness() -> ModuleType:
    name = "equipment_spell_references_candidate"
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
EQUIPMENT_ROWS = ("#24", "#35", "#37")
SPELL_ROWS = tuple(f"#{n}" for n in range(79, 87))


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
    """The current committed authority the candidate persists."""
    return current()


@pytest.fixture(scope="module")
def counterfactual(accepted: AcceptedInputs) -> AcceptedInputs:
    """The current oracle without exactly the thirteen appended resolutions.

    Which thirteen is read from the recordings: the resolutions the
    equipment-spell-references recording holds beyond the
    finite-reference-routes recording it appended over. Resolution ids do not
    name a release. In memory only; never an accepted artifact.
    """
    prior_ids = {
        r.resolution_id
        for r in finite_reference_routes_recorded().oracle.reference_resolutions
    }
    appended = {
        r.resolution_id
        for r in equipment_spell_references_recorded().oracle.reference_resolutions
    } - prior_ids
    held = {r.resolution_id for r in accepted.oracle.reference_resolutions}
    assert len(appended) == 13 and appended <= held
    kept = tuple(
        r
        for r in accepted.oracle.reference_resolutions
        if r.resolution_id not in appended
    )
    assert len(kept) == len(held) - 13
    return replace(
        accepted, oracle=replace(accepted.oracle, reference_resolutions=kept)
    )


@pytest.fixture(scope="module")
def candidate(tmp_path_factory, source_release_db, accepted):  # type: ignore[no-untyped-def]
    """The current committed oracle, persisted into a private release copy."""
    yield from _persist(tmp_path_factory, source_release_db, accepted, "esr-candidate")


@pytest.fixture(scope="module")
def control(tmp_path_factory, source_release_db, counterfactual):  # type: ignore[no-untyped-def]
    """The counterfactual: the thirteen resolutions absent."""
    yield from _persist(
        tmp_path_factory, source_release_db, counterfactual, "esr-control"
    )


def _records(result) -> list[str]:  # type: ignore[no-untyped-def]
    return list(dict.fromkeys(r for r, _ in _order(result)))


@pytest.mark.parametrize("row", sorted(ROWS))
def test_the_control_refuses_every_drafted_citation(control, monkeypatch, row) -> None:  # type: ignore[no-untyped-def]
    """Without the proposed resolutions the reader fails closed."""
    result = _read(control, monkeypatch, ROWS[row], ANY)
    assert result.outcome is AuthorityOutcome.INVALID_REFERENCE


@pytest.mark.parametrize("row", sorted(ROWS))
def test_every_route_reads_as_drafted(candidate, monkeypatch, row) -> None:  # type: ignore[no-untyped-def]
    _, destinations = H.DRAFTS[ROWS[row]]
    result = _read(candidate, monkeypatch, ROWS[row], ANY)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    targets = [(r, c) for _, route in result.routes for r, c in route]
    assert targets == [(d.target_record_key, "") for d in destinations]
    if len(destinations) > 1:
        drafted: dict[str, list[tuple[str, str]]] = {}
        for d in destinations:
            drafted.setdefault(d.alternative_label, []).append(
                (d.target_record_key, "")
            )
        assert [(label, list(ds)) for label, ds in result.routes] == list(
            drafted.items()
        )


@pytest.mark.parametrize("row", EQUIPMENT_ROWS)
def test_equipment_reads_the_whole_chapter(  # type: ignore[no-untyped-def]
    candidate, monkeypatch, accepted, row
) -> None:
    """Every equipment record: the sections, landing first, and their members."""
    result = _read(candidate, monkeypatch, ROWS[row], ANY)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    records = _records(result)
    equipment = {
        r.semantic_key
        for r in accepted.oracle.representation.records
        if r.semantic_key.startswith("equipment.")
    }
    assert set(records) == equipment and len(equipment) == 147
    assert records[0] == "equipment.coins"
    sections = [r for r in records if r in H.EQUIPMENT_SECTIONS]
    assert sections == list(H.EQUIPMENT_SECTIONS)
    for member in (
        "equipment.weapons.longsword",
        "equipment.armor.shield",
        "equipment.tools.thieves_tools",
        "equipment.adventuring_gear.potion_of_healing",
        "equipment.mounts_and_vehicles.rowboat",
    ):
        assert member in records, member


def test_cursed_items_are_the_four_descriptions(candidate, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    result = _read(candidate, monkeypatch, ROWS["#46"], WIZARD)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert [label for label, _ in result.routes] == [
        f"Cursed item: {name}" for name, _ in H.CURSED
    ]
    assert _records(result) == [key for _, key in H.CURSED]
    assert "magic_items.deck_of_many_things" not in _records(result)


@pytest.mark.parametrize("row", SPELL_ROWS)
def test_spellcasting_reads_gaining_then_casting(  # type: ignore[no-untyped-def]
    candidate, monkeypatch, accepted, row
) -> None:
    result = _read(candidate, monkeypatch, ROWS[row], ANY)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    casting = H.members(accepted)["spells.casting_spells"]
    assert len(casting) == 9
    records = _records(result)
    assert records[0] == "spells.gaining_spells"
    assert set(records) == {"spells.gaining_spells", "spells.casting_spells", *casting}
    assert "spells.spell_descriptions" not in records
    components = set(_order(result))
    for component in ("preparing_spells", "always_prepared_spells"):
        assert ("spells.gaining_spells", component) in components
    for component in ("spell_level", "spell_slots", "rituals", "cantrips"):
        assert ("spells.casting_spells", component) in components


def test_spell_characteristics_read_casting_only(  # type: ignore[no-untyped-def]
    candidate, monkeypatch, accepted
) -> None:
    result = _read(candidate, monkeypatch, ROWS["#89"], ANY)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    casting = H.members(accepted)["spells.casting_spells"]
    records = _records(result)
    assert records[0] == "spells.casting_spells"
    assert set(records) == {"spells.casting_spells", *casting}


def test_a_disabled_destination_refuses_and_an_unrelated_one_does_not(  # type: ignore[no-untyped-def]
    candidate, monkeypatch
) -> None:
    gone = _read(candidate, monkeypatch, ROWS["#24"], ANY, _disable("equipment.coins"))
    assert gone.outcome is AuthorityOutcome.INVALID_REFERENCE
    gone = _read(
        candidate, monkeypatch, ROWS["#79"], ANY, _disable("spells.gaining_spells")
    )
    assert gone.outcome is AuthorityOutcome.INVALID_REFERENCE
    other = _disable("magic_items.berserker_axe")
    kept = _read(candidate, monkeypatch, ROWS["#24"], ANY, other)
    assert kept.outcome is AuthorityOutcome.RESOLVED, kept.detail
    assert [a.override_id for a in kept.gamemaster_view.applied_overrides] == [
        other.override_id
    ]


def test_the_deferred_gear_citation_is_not_among_the_thirteen(  # type: ignore[no-untyped-def]
    candidate, control, monkeypatch, accepted, counterfactual
) -> None:
    """Row 36 shares #35's record, text and scope; this batch did not draft it.

    A later batch's resolution routes it in the current authority, outside the
    thirteen: their absence leaves its reading unchanged.
    """
    assert H.DEFERRED_GEAR not in H.DRAFTS
    (later,) = [
        r
        for r in accepted.oracle.reference_resolutions
        if (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)
        == H.DEFERRED_GEAR
    ]
    assert later.resolution_id == "cited-36-monsters.parts_of_a_stat_block-gear"
    assert later in counterfactual.oracle.reference_resolutions
    held = _read(candidate, monkeypatch, H.DEFERRED_GEAR, ANY)
    assert held.outcome is AuthorityOutcome.RESOLVED, held.detail
    absent = _read(control, monkeypatch, H.DEFERRED_GEAR, ANY)
    assert absent.outcome is AuthorityOutcome.RESOLVED, absent.detail
    assert held.routes == absent.routes


# -- the citing passage: record-owned supporting text and component prose ------
#
# Row 37 is read from supporting text of ``play.exploration`` that no
# component's prose binds (ADR-005d Decision 7): it stands while the record
# does. ``glossary.grappling`` / "Unarmed Strike" (accepted) is record-owned but
# read from ``grapple_basis`` prose as well, so that prose must survive too; #24
# is component-owned and read from ``starting_equipment`` prose only.

EXPLORATION = ROWS["#37"]
UNARMED = (
    "glossary.grappling",
    "",
    "Unarmed Strike",
    "srd-5.2.1/rules-glossary",
)
COMPONENT = MechanicalTargetKind.COMPONENT
PROSE = MechanicalTargetKind.PROSE
REPLACE = OverrideOperationEnum.REPLACE


def _override(
    kind: MechanicalTargetKind,
    record_key: str,
    component_key: str | None = None,
    operation: OverrideOperationEnum = OverrideOperationEnum.DISABLE,
    payload: dict[str, object] | None = None,
) -> EffectiveOverrideEntry:
    disabled = _disable(record_key)
    return replace(
        disabled,
        override_id=f"{operation.value}-{kind.value}-{record_key}-{component_key}",
        target=replace(disabled.target, kind=kind, component_key=component_key),
        operation=operation,
        payload=payload or {"patch": "disable"},
    )


def _replaced(record_key: str, kind: str) -> EffectiveOverrideEntry:
    """The same key, supplied again: the record keeps its span_ids, not its text."""
    body = {
        "semantic_key": "house",
        "handling": "prose_bound",
        "facts": [],
        "authored_prose": "A house rule.",
    }
    payload: dict[str, object] = {
        "patch": "replace_record",
        "record_kind": kind,
        "components": [body],
    }
    return _override(MechanicalTargetKind.RECORD, record_key, None, REPLACE, payload)


@pytest.mark.parametrize(
    ("citation", "override"),
    [
        pytest.param(
            EXPLORATION, _disable("play.exploration"), id="37-record-disabled"
        ),
        pytest.param(
            EXPLORATION,
            _replaced("play.exploration", "general_rule"),
            id="37-record-replaced",
        ),
        pytest.param(UNARMED, _disable("glossary.grappling"), id="unarmed-record"),
        pytest.param(
            UNARMED,
            _replaced("glossary.grappling", "glossary_rule"),
            id="unarmed-record-replaced",
        ),
        pytest.param(
            UNARMED,
            _override(COMPONENT, "glossary.grappling", "grapple_basis"),
            id="unarmed-component",
        ),
        pytest.param(
            UNARMED,
            _override(PROSE, "glossary.grappling", "grapple_basis"),
            id="unarmed-prose",
        ),
        pytest.param(
            ROWS["#24"],
            _override(
                COMPONENT,
                "character_creation.create_your_character",
                "starting_equipment",
            ),
            id="24-component",
        ),
        pytest.param(
            ROWS["#24"],
            _override(
                PROSE,
                "character_creation.create_your_character",
                "starting_equipment",
                REPLACE,
                {"patch": "replace_prose", "text": "A house note."},
            ),
            id="24-prose-replaced",
        ),
    ],
)
def test_a_citation_whose_source_is_gone_is_refused(  # type: ignore[no-untyped-def]
    candidate, monkeypatch, citation, override
) -> None:
    assert _read(candidate, monkeypatch, citation, ANY).outcome is (
        AuthorityOutcome.RESOLVED
    )
    result = _read(candidate, monkeypatch, citation, ANY, override)
    assert result.outcome is AuthorityOutcome.INVALID_REFERENCE
    assert "effective source" in (result.detail or "")


@pytest.mark.parametrize("citation", [EXPLORATION, UNARMED], ids=["37", "unarmed"])
def test_an_unrelated_override_keeps_a_record_owned_citation(  # type: ignore[no-untyped-def]
    candidate, monkeypatch, citation
) -> None:
    appended = _override(
        PROSE,
        citation[0],
        "equipment_help" if citation == EXPLORATION else "grapple_basis",
        OverrideOperationEnum.APPEND,
        {"patch": "append_prose", "text": "A house note."},
    )
    unrelated = _disable("magic_items.berserker_axe")
    result = _read(candidate, monkeypatch, citation, ANY, appended, unrelated)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert [a.override_id for a in result.gamemaster_view.applied_overrides] == [
        appended.override_id,
        unrelated.override_id,
    ]
