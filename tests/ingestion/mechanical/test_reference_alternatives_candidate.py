"""The reference-routes candidate, read through the production reader.

CRD Issue 5d (#132, #137). The candidate drafted by
``.claude/review-notes/issue-5d-reference-alternatives-REPLACEMENT.py``, lifted
and resolved in one native action, is now the Owner-accepted recording
(``issue-5d-reference-alternatives-ACCEPT.py``); the committed oracle is
persisted as a draft into a private copy of the release, and read back through
:meth:`~afterworlds.services.rules_authority.service.RulesAuthorityService.citation_view`.
Only binding resolution is stood in, as in the other draft-read tests:
publishing or activating it is out of scope (the order pass and the
partial-publication block stand).
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
from afterworlds.ingestion.mechanical.representation import ReferenceSituation
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
    / ".claude/review-notes/issue-5d-reference-alternatives-REPLACEMENT.py"
)
NOW = "2026-10-01T00:00:00Z"
LA = "character_creation.level_advancement"
MC = "character_creation.multiclassing"
ARCHERY = ("feats.archery", "category", "Fighting Style Feature", "srd-5.2.1/classes")
PROFICIENCY = (LA, "proficiency_bonus", "Classes", "srd-5.2.1/classes")
FEATURES = (
    "character_creation.create_your_character",
    "class_features",
    "Classes",
    "srd-5.2.1/classes",
)
ORIGIN = (
    "gameplay_toolbox.creating_a_background",
    "step_2_choose_a_feat",
    "Origin Feats",
    "srd-5.2.1/feats",
)


def _harness() -> ModuleType:
    name = "reference_alternatives_replacement"
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
    path = tmp_path_factory.mktemp("reference-routes") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(candidate_from_accepted_inputs(final))
        persist_draft(s, identified, now=NOW)
        s.commit()
        yield s, identified.projection_uuid, final.oracle.binding
    engine.dispose()


def _disable(record_key: str) -> EffectiveOverrideEntry:
    return _entry(MechanicalTargetKind.RECORD, record_key)


def _entry(
    kind: MechanicalTargetKind,
    record_key: str,
    component_key: str | None = None,
    operation: OverrideOperationEnum = OverrideOperationEnum.DISABLE,
    payload: dict[str, object] | None = None,
) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
        override_id=f"{operation.value}-{kind.value}-{record_key}-{component_key}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=kind, record_key=record_key, component_key=component_key
        ),
        operation=operation,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload=payload or {"patch": "disable"},
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


def _text(result, record: str, component: str) -> str:  # type: ignore[no-untyped-def]
    (found,) = [
        c
        for c in result.gamemaster_view.components
        if (c.record_key, c.component_key) == (record, component)
    ]
    return " ".join(e.text or "" for e in found.governing_prose)


def test_a_class_level_route_reads_its_feature_text(persisted, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Paladin 1 / Ranger 3: the Ranger route alone, with its prose."""
    split = AlternativeSelection(
        class_levels={"classes.fighter": 0, "classes.paladin": 1, "classes.ranger": 3}
    )
    result = _read(persisted, monkeypatch, ARCHERY, split)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert result.routes == (
        (
            "Ranger level 2: Fighting Style",
            (("classes.ranger.fighting_style", "fighting_style"),),
        ),
    )
    assert "Fighting Style" in _text(
        result, "classes.ranger.fighting_style", "fighting_style"
    )


def test_the_multiclass_route_reads_the_table_with_its_caveat(
    persisted, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    multi = AlternativeSelection(
        situations={
            ReferenceSituation.SINGLE_CLASS: False,
            ReferenceSituation.MULTICLASS: True,
        }
    )
    result = _read(persisted, monkeypatch, PROFICIENCY, multi)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    ((_, destinations),) = result.routes
    assert destinations == ((LA, "character_advancement"), (MC, "proficiency_bonus"))
    assert "total character level" in _text(result, MC, "proficiency_bonus")
    assert _text(result, LA, "character_advancement")


def test_entering_a_class_reads_its_instructions_and_features(
    persisted, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    entering = AlternativeSelection(
        situations={
            ReferenceSituation.INITIAL_CHARACTER: False,
            ReferenceSituation.ENTERING_CLASS: True,
        },
        class_record_keys=frozenset({"classes.paladin"}),
    )
    result = _read(persisted, monkeypatch, FEATURES, entering)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    ((label, destinations),) = result.routes
    assert label == "Paladin: entering as a multiclass character"
    assert destinations == (
        ("classes.paladin.as_a_multiclass_character", "as_a_multiclass_character"),
        ("classes.paladin", ""),
    )
    read = {c.record_key for c in result.gamemaster_view.components}
    # The whole class reaches its Level N feature records one hop away.
    assert len({k for k in read if k.startswith("classes.paladin.")}) > 2


def test_the_origin_feats_group_reads_as_one_route(persisted, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    result = _read(persisted, monkeypatch, ORIGIN, AlternativeSelection())
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    ((label, destinations),) = result.routes
    assert label.startswith("Origin Feats")
    assert [r for r, _ in destinations] == [
        "feats.alert",
        "feats.magic_initiate",
        "feats.savage_attacker",
        "feats.skilled",
    ]
    assert "Origin Feat" in _text(result, "feats.alert", "category")


def test_an_override_applies_and_a_disabled_destination_refuses(
    persisted, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    ranger = AlternativeSelection(class_record_keys=frozenset({"classes.ranger"}))
    off = _disable("classes.fighter.fighting_style")
    result = _read(persisted, monkeypatch, ARCHERY, ranger, off)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert [a.override_id for a in result.gamemaster_view.applied_overrides] == [
        off.override_id
    ]
    stale = _read(persisted, monkeypatch, ARCHERY, AlternativeSelection(), off)
    assert stale.outcome is AuthorityOutcome.INVALID_REFERENCE
    gone = _read(
        persisted, monkeypatch, ORIGIN, AlternativeSelection(), _disable("feats.alert")
    )
    assert gone.outcome is AuthorityOutcome.INVALID_REFERENCE


def test_an_unstated_or_ruled_out_citation_is_refused(persisted, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    unknown = (*ARCHERY[:3], "srd-5.2.1/nowhere")
    result = _read(persisted, monkeypatch, unknown, AlternativeSelection())
    assert result.outcome is AuthorityOutcome.INVALID_REFERENCE
    nobody = AlternativeSelection(class_record_keys=frozenset({"classes.wizard"}))
    result = _read(persisted, monkeypatch, ARCHERY, nobody)
    assert result.outcome is AuthorityOutcome.INVALID_SELECTOR


# -- the effective source and the route order --------------------------------

PROFICIENCIES = (
    "character_creation.create_your_character",
    "class_proficiencies",
    "Classes",
    "srd-5.2.1/classes",
)
PALADIN_ENTRY = "classes.paladin.as_a_multiclass_character"
RANGER = AlternativeSelection(class_record_keys=frozenset({"classes.ranger"}))
PROSE = MechanicalTargetKind.PROSE


def _order(result) -> list[tuple[str, str]]:  # type: ignore[no-untyped-def]
    return [(c.record_key, c.component_key) for c in result.gamemaster_view.components]


@pytest.mark.parametrize(
    "override",
    [
        pytest.param(_disable("feats.archery"), id="record-disabled"),
        pytest.param(
            _entry(MechanicalTargetKind.COMPONENT, "feats.archery", "category"),
            id="component-disabled",
        ),
        pytest.param(_entry(PROSE, "feats.archery", "category"), id="prose-disabled"),
        pytest.param(
            _entry(
                PROSE,
                "feats.archery",
                "category",
                OverrideOperationEnum.REPLACE,
                {"patch": "replace_prose", "text": "A house prerequisite."},
            ),
            id="prose-replaced",
        ),
    ],
)
def test_a_citation_whose_source_is_gone_is_refused(  # type: ignore[no-untyped-def]
    persisted, monkeypatch, override
) -> None:
    result = _read(persisted, monkeypatch, ARCHERY, RANGER, override)
    assert result.outcome is AuthorityOutcome.INVALID_REFERENCE
    assert "effective source" in (result.detail or "")


def test_an_edit_that_keeps_the_citing_passage_keeps_the_citation(  # type: ignore[no-untyped-def]
    persisted, monkeypatch
) -> None:
    appended = _entry(
        PROSE,
        "feats.archery",
        "category",
        OverrideOperationEnum.APPEND,
        {"patch": "append_prose", "text": "A house note."},
    )
    unrelated = _disable("feats.defense")
    result = _read(persisted, monkeypatch, ARCHERY, RANGER, appended, unrelated)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert [a.override_id for a in result.gamemaster_view.applied_overrides] == [
        appended.override_id,
        unrelated.override_id,
    ]
    assert _order(result) == [("classes.ranger.fighting_style", "fighting_style")]


def test_a_route_reads_its_landing_before_its_support(  # type: ignore[no-untyped-def]
    persisted, monkeypatch
) -> None:
    """Key order would put ``classes.paladin`` before the entry instructions."""
    entering = AlternativeSelection(
        situations={
            ReferenceSituation.INITIAL_CHARACTER: False,
            ReferenceSituation.ENTERING_CLASS: True,
        },
        class_record_keys=frozenset({"classes.paladin"}),
    )
    result = _read(persisted, monkeypatch, PROFICIENCIES, entering)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert _order(result) == [
        (PALADIN_ENTRY, "as_a_multiclass_character"),
        ("classes.paladin", "core_traits"),
    ]
    whole = _read(persisted, monkeypatch, FEATURES, entering)
    assert whole.outcome is AuthorityOutcome.RESOLVED, whole.detail
    order = _order(whole)
    assert order[0] == (PALADIN_ENTRY, "as_a_multiclass_character")
    assert all(r.startswith("classes.paladin") for r, _ in order)


def test_several_routes_read_in_their_stated_order(  # type: ignore[no-untyped-def]
    persisted, monkeypatch
) -> None:
    paladin = AlternativeSelection(class_record_keys=frozenset({"classes.paladin"}))
    result = _read(persisted, monkeypatch, PROFICIENCIES, paladin)
    assert result.outcome is AuthorityOutcome.RESOLVED, result.detail
    assert len(result.routes) == 2
    stated = list(dict.fromkeys(d for _, ds in result.routes for d in ds))
    assert _order(result) == stated
    group = _read(persisted, monkeypatch, ORIGIN, AlternativeSelection())
    assert list(dict.fromkeys(r for r, _ in _order(group))) == [
        "feats.alert",
        "feats.magic_initiate",
        "feats.savage_attacker",
        "feats.skilled",
    ]
