"""The UNACCEPTED Equipment cited-targets candidate through the consumer path.

CRD Issue 5d Equipment cited-targets packet (#132, #137). The candidate
``issue-5d-equipment-cited-targets-PROPOSAL.json`` gives each cited Equipment
item or rule its own record. These tests hold its bytes and drafts, and read
the 67 new members through the production service over a private draft copy
of the release: directly, through their section, combined (dedup), disabled
and replaced. Nothing here accepts, records, publishes or activates anything;
``issue-5d-equipment-cited-targets-REPLACEMENT.py`` holds the in-memory chain.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.persistence import persist_draft
from afterworlds.ingestion.mechanical.projection import identify_projection
from afterworlds.ingestion.mechanical.proposal import (
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
)
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.services.rules_authority.application import AuthoredProse, SourceProse
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from tests.ingestion.mechanical import test_equipment_proposal as EQ
from tests.ingestion.mechanical._replacement_chain import current
from tests.ingestion.mechanical.test_character_origins_feats_proposal import (
    _disable,
    _request,
    _service,
    _sliced,
)

NOTES = Path(__file__).resolve().parents[3] / ".claude" / "review-notes"
PROPOSAL = NOTES / "issue-5d-equipment-cited-targets-PROPOSAL.json"
PROPOSAL_SHA256 = "13271e035f76316a6f78cf90ccca1f68ec233738ce31a93c7303052bc5bb02e0"
IDENTITY = "309e4405a4dc630b477adac0e83e2bc86bae0e2e6f76550775e5dae2b1bc1680"
DRAFTS = NOTES / "issue-5d-equipment-cited-targets-resolutions-DRAFTS.json"
DRAFTS_SHA256 = "bfbf5a7ac78fa96fd568148d26bd2690415a4add9196d8ca393ef7b4f0c139eb"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load(
    "equipment_cited_targets", NOTES / "issue-5d-equipment-cited-targets-generator.py"
)
#: The records the candidate adds, in its order; the accepted generator's
#: named records stay, unchanged and in their order, among them.
NEW = [
    (k, e)
    for k, _, e in GEN.batch().records
    if (k, e) not in {(a, b) for a, _, b in EQ.GEN.batch().records}
]


@pytest.fixture(scope="module")
def session(source_release_db: Path):  # type: ignore[no-untyped-def]
    engine = create_engine(f"sqlite:///{source_release_db}")
    with create_session_factory(engine)() as s:
        yield s
    engine.dispose()


@pytest.fixture(scope="module")
def built(session):  # type: ignore[no-untyped-def]
    return GEN.build(session)


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db, built):  # type: ignore[no-untyped-def]
    path = tmp_path_factory.mktemp("equipment-cited") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(EQ._candidate(built))
        persist_draft(s, identified, now="2026-09-28T00:00:00Z")
        s.commit()
        yield s, identified.projection_uuid
    engine.dispose()


def test_the_candidate_bytes_and_drafts_are_the_recorded_ones(built) -> None:  # type: ignore[no-untyped-def]
    # The recorded candidate is the superseded release's; the build here is
    # the current release's, so their byte equality is retired.
    raw = PROPOSAL.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PROPOSAL_SHA256
    recorded = load_proposal(PROPOSAL, expected_identity=IDENTITY)
    assert proposal_identity(recorded) == IDENTITY
    assert recorded.binding != built.binding == current().oracle.binding
    drafts = DRAFTS.read_bytes()
    assert hashlib.sha256(drafts).hexdigest() == DRAFTS_SHA256
    assert json.loads(drafts) == list(
        reference_resolution_payload(GEN.draft_cited_resolutions(recorded.binding))
    )
    assert b"\r" not in raw + drafts


def test_the_accepted_named_records_are_kept_and_67_are_added() -> None:
    accepted = EQ.GEN.batch().records
    assert [r for r in GEN.batch().records if r in set(accepted)] == list(accepted)
    assert len(NEW) == 67
    assert {e for _, e in NEW} == {
        "weapons",
        "armor",
        "tools",
        "adventuring_gear",
        "mounts_and_vehicles",
    }


@pytest.mark.parametrize("section", sorted({f"equipment.{e}" for _, e in NEW}))
def test_a_section_reads_every_member_once_where_printed(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch, section
) -> None:
    service = _service(persisted, built, monkeypatch)
    members = sorted(
        (min(EQ._owned(built, k)), k)
        for k, _, e in GEN.batch().records
        if f"equipment.{e}" == section
    )
    assert _sliced(service, _request(built, section)) == [
        section,
        *(k for _, k in members),
    ]
    records = {section, *(k for _, k in members)}
    view = EQ._read(service, built, section)
    assert EQ._sequence(built, view) == sorted(
        p for (r, _, _), p in EQ._primary(built).items() if r in records
    )
    spans = [e.span_id for c in view for e in c.governing_prose]
    assert len(spans) == len(set(spans))


def test_each_new_member_reads_directly_its_own_passages_and_context(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    primary = EQ._primary(built)
    for record, entry in NEW:
        view = EQ._read(service, built, record)
        assert {c.record_key for c in view} == {record}
        own = [
            (c.record_key, c.component_key, e.span_id)
            for c in view
            for e in c.governing_prose
            if (c.record_key, c.component_key, e.span_id) in primary
        ]
        # Every passage it owns, once, in printed order.
        assert [primary[o] for o in own] == sorted(EQ._owned(built, record)), record
        # Combined with its section it is the section's reading, member once.
        section = f"equipment.{entry}"
        both = EQ._read(service, built, section, record)
        assert both == EQ._read(service, built, section)


def test_the_cited_rows_read_under_their_table_head_and_group(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    assert EQ._direct(service, built, "equipment.weapons.longsword") == [
        *GEN.MARTIAL_MELEE,
        GEN.WEAPON_ROWS["Longsword"],
    ]
    assert EQ._direct(service, built, "equipment.armor.chain_mail") == [
        GEN.ARMOR_HEAD,
        GEN.ARMOR_GROUPS["Heavy Armor"],
        GEN.ARMOR_ROWS["Chain Mail"],
        *GEN.ARMOR_RULES,
    ]
    assert EQ._direct(service, built, "equipment.mounts_and_vehicles.keelboat") == [
        # In printed order: the Speed note is printed before the table.
        GEN.clause("mounts_and_vehicles", "large_vehicles")[0],
        *GEN.clause("mounts_and_vehicles", "speed"),
        GEN.VEHICLES_HEAD,
        GEN.VEHICLE_ROWS["Keelboat"],
        *(
            t
            for k in ("crew", "passengers", "damage_threshold", "ship_repair")
            for t in GEN.clause("mounts_and_vehicles", k)
        ),
    ]
    assert EQ._direct(service, built, "equipment.tools.smiths_tools") == [
        *GEN.TOOL_RULES,
        *GEN.clause("tools", "artisans_tools"),
        *GEN.clause("tools", "smiths_tools"),
    ]
    # The rows the accepted section read as its own are now their members'.
    rows = {
        name: c.record_key
        for c in EQ._read(service, built, "equipment.weapons")
        for e in c.governing_prose
        for name in ("Greatclub", "Longsword", "Pistol")
        if e.text == GEN.WEAPON_ROWS[name]
    }
    assert rows == {
        "Greatclub": "equipment.weapons.greatclub",
        "Longsword": "equipment.weapons.longsword",
        "Pistol": "equipment.weapons.pistol",
    }


def test_the_wand_row_is_the_wands_and_arcane_focus_still_reads_it(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    section = "equipment.adventuring_gear"
    wand, focus = f"{section}.wand", f"{section}.arcane_focus"
    # The Wand reads its row under the Arcane Focus rule and the table head.
    assert EQ._direct(service, built, wand) == [*GEN.WAND_CONTEXT, GEN.WAND_ROW]
    # Arcane Focus still reads its whole entry, in printed order ...
    context, rows = GEN.ROWS_OF[("adventuring_gear", "arcane_focus")]
    assert EQ._direct(service, built, focus) == [
        *context,
        *rows,
        *GEN.clause("adventuring_gear", "arcane_focus")[:2],
        *GEN.ARCANE_FOCUSES_PIECES,
    ]

    # ... but owns the Wand row only as context: it is the Wand's. The
    # table's close, cut from the Wand row, stays the table's (other sections'
    # tables print the same close).
    def owners(text: str) -> set[str]:
        return {
            r
            for r, _, s in EQ._primary(built)
            if r.startswith(section) and _span_text(built, s) == text
        }

    assert owners(GEN.WAND_ROW) == {wand}
    assert owners(GEN.ARCANE_FOCUSES_CLOSE) == {focus}
    assert GEN.ARCANE_FOCUSES_PIECES[-2:] == (GEN.WAND_ROW, GEN.ARCANE_FOCUSES_CLOSE)
    # Read together or through the section, each passage is read once.
    assert EQ._read(service, built, section, focus, wand) == EQ._read(
        service, built, section
    )
    both = [
        e.span_id
        for c in EQ._read(service, built, focus, wand)
        for e in c.governing_prose
    ]
    assert len(both) == len(set(both))

    # Disabled or replaced, only the Wand row goes: Arcane Focus keeps its
    # rule, the table head, the other rows and the table's close, directly and
    # in the section.
    def in_section(svc) -> list[str | None]:  # type: ignore[no-untyped-def]
        return [
            e.text
            for c in EQ._read(svc, built, section)
            if c.record_key == focus
            for e in c.governing_prose
        ]

    kept = [t for t in EQ._direct(service, built, focus) if t != GEN.WAND_ROW]
    focus_in_section = in_section(service)
    assert GEN.ARCANE_FOCUSES_CLOSE in focus_in_section
    for overrides in (_disable(wand), EQ._replaced(wand, "wand", "House text.")):
        overridden = _service(persisted, built, monkeypatch, overrides)
        assert EQ._direct(overridden, built, focus) == kept
        assert in_section(overridden) == focus_in_section


def _span_text(built: Built, span_id: str) -> str:
    span = next(s for s in built.ledger.spans if s.span_id == span_id)
    return built.leaf_rows[span.leaf_id].content[span.char_start : span.char_end]


@pytest.mark.parametrize(
    "record",
    [
        "equipment.weapons.longsword",
        "equipment.weapons.heavy",
        "equipment.armor.chain_mail",
        "equipment.adventuring_gear.rope",
        "equipment.adventuring_gear.wand",
        "equipment.tools.smiths_tools",
        "equipment.mounts_and_vehicles.keelboat",
    ],
)
def test_a_disabled_or_replaced_new_member_leaves_its_section_whole(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch, record
) -> None:
    section = ".".join(record.split(".")[:2])
    key = record.split(".")[-1]
    whole = EQ._read(_service(persisted, built, monkeypatch), built, section)
    owned = set(EQ._owned(built, record))
    printed = {
        e.text for c in whole if c.record_key == record for e in c.governing_prose
    }
    assert printed
    disabled_service = _service(persisted, built, monkeypatch, _disable(record))
    disabled = EQ._read(disabled_service, built, section)
    assert record not in {c.record_key for c in disabled}
    assert not printed & {e.text for c in disabled for e in c.governing_prose}
    assert EQ._sequence(built, disabled) == [
        p for p in EQ._sequence(built, whole) if p not in owned
    ]
    direct = disabled_service.rule_slice(_request(built, record))
    assert direct.outcome is AuthorityOutcome.INVALID_REFERENCE
    replaced = EQ._read(
        _service(
            persisted, built, monkeypatch, EQ._replaced(record, key, "House text.")
        ),
        built,
        section,
    )
    (at,) = EQ._runs(replaced, record)
    (entry,) = replaced[at].governing_prose
    assert isinstance(entry, AuthoredProse) and entry.text == "House text."
    assert not printed & {
        e.text
        for c in replaced
        for e in c.governing_prose
        if isinstance(e, SourceProse)
    }
    assert EQ._sequence(built, replaced) == EQ._sequence(built, disabled)


def test_a_component_selector_on_a_section_reads_no_new_member(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    for section, key in (
        ("equipment.weapons", "properties"),
        ("equipment.tools", "tools"),
        ("equipment.mounts_and_vehicles", "large_vehicles"),
    ):
        narrowed = EQ._read(service, built, components=((section, key),))
        assert [(c.record_key, c.component_key) for c in narrowed] == [(section, key)]
