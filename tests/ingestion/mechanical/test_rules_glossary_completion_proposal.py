"""The ``rules-glossary-completion`` proposal, offered for review -- CRD Issue 5d.

Every *Rules Definitions* entry no accepted batch authors -- sixty entries,
*Improvised Weapons* among them -- proposed by
``.claude/review-notes/issue-5d-rules-glossary-completion-generator.py`` from
the release 5c actually publishes. The Owner has since accepted it,
regenerated on the corrected release, as part of the replacement chain that
``issue-5d-class-spell-tables-REPLACEMENT-ACCEPT.py`` recorded in the
committed oracle; that acceptance is pinned at the end of this module.

What is pinned, and why:

* the generator, run on the current release, derives the batch the current
  committed oracle accepted; the committed artifact is the superseded
  release's proposal, a proposal by shape;
* scope is one entry unit and one ``glossary_rule`` record per unauthored
  entry, in printed order, inside the current release's *Rules Definitions*;
  in the recorded proposal no leaf or record is an accepted one's;
* the batch checks report the accepted out-of-batch targets and the eight
  unresolved part-level citations ("Spells", "Casting Spells", "Character
  Creation"), and nothing else;
* fidelity: every component stays prose-bound; the *Action* table is the
  release's own rows after its prose; a GameMaster reads every passage in
  printed order;
* references: see-alsos are record-owned supporting spans; glossary terms are
  cited from prose only; examples are not references;
* every word of every spanned leaf is claimed, only headings are excluded, and
  a dropped table, rule or component is reported;
* the recorded proposal, composed *in this test only* with the recorded
  fourteen-batch chain rebuilt natively (both the superseded release's): the
  fifty recorded resolutions still apply, and the proposal accepts in memory.
  The superseded oracle, read by path, records the Owner's acceptance. Judging
  that composition against a corpus needs the superseded release's, which is
  not rebuilt; that check is retired (see
  ``.claude/review-notes/issue-5c-release-readiness/correction-followup.md``);
* through the production rules-authority service, an entry reads its rules
  in printed order, a disabled record stays gone, a replaced component reads
  replaced where it is printed, an authored addition reads after the source,
  and narrowing to some components keeps their printed order.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from afterworlds.ingestion.mechanical.acceptance import accept_proposal
from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReviewState,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    OracleLoadError,
    load_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import persist_draft
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    identify_projection,
)
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    load_proposal,
    proposal_identity,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordKind,
    prose_binding_target_key,
    representation_schema_hash,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.models.rules_package import RulesPackageBinding
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.corpus import LedgerLeafORM
from afterworlds.persistence.orm.rules_package import RuleChunkORM
from afterworlds.services.rules_authority.application import (
    AuthoredProse,
    SourceProse,
    apply_override_set,
)
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import (
    EffectiveOverrideEntry,
    EffectiveOverrideSet,
)
from afterworlds.services.rules_authority.service import source_leaf_order
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)
from afterworlds.services.rules_authority.views import build_gamemaster_view
from tests.ingestion.mechanical._replacement_chain import (
    BATCHES,
    REPLACEMENT,
    animals_recorded,
    current,
    identity,
    kept_whole,
    proposal_path,
    through,
)
from tests.ingestion.mechanical._schema_pins import lifted
from tests.ingestion.mechanical.test_character_origins_feats_proposal import (
    _disable,
    _request,
    _service,
    _sliced,
)

REPO = Path(__file__).resolve().parents[3]
NOTES = REPO / ".claude" / "review-notes"
GENERATOR = NOTES / "issue-5d-rules-glossary-completion-generator.py"
BATCH = "rules-glossary-completion"
PROPOSAL = proposal_path(BATCH)
IDENTITY = identity(BATCH)
#: The superseded release's committed oracle, read by path as historical
#: evidence; it preserves the fourteen-batch state reviewed against.
ORACLE = REPLACEMENT.ACCEPTED_PATH

GLOSSARY = "srd-5.2.1/rules-glossary"
SPELLS = "srd-5.2.1/spells"
EQUIPMENT = "srd-5.2.1/equipment"
PLAY = "srd-5.2.1/playing-the-game"
CHARACTER_CREATION = "srd-5.2.1/character-creation"
#: *Rules Definitions* in the current release: its heading, its one-line
#: introduction, then entries.
RULES_DEFINITIONS = range(4383, 4867)


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load("rules_glossary_completion", GENERATOR)
AUTHORED = [slug for slug, _, _ in GEN.ENTRIES]


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
def prior() -> AcceptedInputs:
    """The recorded fourteen-batch chain, rebuilt natively.

    The Animals recording extends it and keeps it whole. It is bound to the
    superseded release, so it composes only with the recorded proposal.
    """
    order = list(BATCHES)
    rebuilt = through(order[order.index(BATCH) - 1])
    assert not kept_whole(rebuilt, animals_recorded())
    return rebuilt


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


def _texts(built, record: str, key: str) -> list[str]:  # type: ignore[no-untyped-def]
    """The source texts one component's prose bindings are read from."""
    spans = {s.span_id: s for s in built.ledger.spans}
    out = []
    for b in built.proposal.proposed_representation.prose_bindings:
        if (b.record_key, b.component_key) == (record, key):
            s = spans[b.span_id]
            out.append(built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end])
    return out


def _record(entry: str) -> str:
    return GEN.batch().record_key(entry)


# ---------------------------------------------------------------------------
# The artifact
# ---------------------------------------------------------------------------


def test_the_current_release_derives_the_batch_its_oracle_accepted(built) -> None:  # type: ignore[no-untyped-def]
    (batch,) = [b for b in current().batches if b.batch_id == BATCH]
    assert proposal_identity(built.proposal) == batch.proposal_identity
    # The committed file is the superseded release's proposal, not this one.
    assert batch.proposal_identity != IDENTITY
    assert b"\r" not in PROPOSAL.read_bytes()


def test_the_artifact_is_an_unaccepted_proposal_by_shape() -> None:
    proposal = load_proposal(PROPOSAL, expected_identity=IDENTITY)
    assert (
        json.loads(PROPOSAL.read_text("utf-8"))["artifact_kind"] == "machine_proposal"
    )
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(PROPOSAL)


def test_scope_is_every_unauthored_entry_one_record_each(session, built) -> None:  # type: ignore[no-untyped-def]
    units = built.proposal.proposed_review_units
    assert len(units) == 60
    assert [(u.unit_id, u.kind) for u in units] == [
        (f"rules-glossary-completion/{s}", ReviewUnitKind.ENTRY) for s in AUTHORED
    ]
    records = built.proposal.proposed_representation.records
    assert [(r.semantic_key, r.kind) for r in records] == [
        (f"glossary.{s}", RecordKind.GLOSSARY_RULE) for s in AUTHORED
    ]
    assert not built.proposal.proposed_representation.relationships
    assert "improvised_weapons" in AUTHORED
    heading = (
        session.query(LedgerLeafORM.content)
        .filter(
            LedgerLeafORM.package_uuid == built.binding.package_uuid,
            LedgerLeafORM.occurrence_index == RULES_DEFINITIONS[0],
        )
        .scalar()
    )
    assert heading == "## Rules Definitions"
    # Each unit's leaves are its own, in printed order, inside Rules Definitions.
    assert sum(len(u.leaf_ids) for u in units) == 133
    for u in units:
        order = [built.leaf_rows[leaf].occurrence_index for leaf in u.leaf_ids]
        assert order == sorted(order), u.unit_id
        assert set(order) <= set(RULES_DEFINITIONS[2:]), u.unit_id
    first = [built.leaf_rows[u.leaf_ids[0]].occurrence_index for u in units]
    assert first == sorted(first)


def test_no_leaf_or_record_is_an_accepted_one(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    # Both sides are the superseded release's: the recorded chain and proposal.
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert len(mine) == 133 and not owned & mine
    accepted = {r.semantic_key for r in prior.oracle.representation.records}
    assert not accepted & {
        r.semantic_key for r in recorded.proposed_representation.records
    }
    glossary = {k for k in accepted if k.startswith("glossary.")}
    assert len(glossary) == 95


UNRESOLVED = [
    *[f"reference {CHARACTER_CREATION}:'Character Creation': unresolved reference"] * 3,
    *[f"reference {SPELLS}:'Casting Spells': unresolved reference"] * 2,
    *[f"reference {SPELLS}:'Spells': unresolved reference"] * 3,
]


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings()
    assert [f for f in found["representation"] if "unresolved" in f] == UNRESOLVED
    unknown = {
        f.rsplit(" ", 1)[1]
        for f in found["representation"]
        if "unknown target record" in f
    }
    assert not unknown & {f"glossary.{s}" for s in AUTHORED}
    assert {k.split(".")[0] for k in unknown} == {
        "glossary",
        "play",
        "equipment",
        "spells",
    }
    assert len(found["representation"]) == 90


# ---------------------------------------------------------------------------
# Fidelity
# ---------------------------------------------------------------------------


def test_every_component_stays_faithful_prose(built) -> None:  # type: ignore[no-untyped-def]
    components = built.proposal.proposed_representation.components
    assert len(components) == 72
    assert {c.handling for c in components} == {ComponentHandling.PROSE_BOUND}
    assert not [c for c in components if c.all_facts()]
    # Each component reads its reviewed clause, whole and in order.
    for entry, key, _, texts in GEN.CLAUSES:
        assert _texts(built, _record(entry), key) == list(texts), (entry, key)


def test_latitude_and_context_are_only_where_the_rule_leaves_them(built) -> None:  # type: ignore[no-untyped-def]
    by_reason: dict[str, list[tuple[str, str]]] = {}
    for c in built.proposal.proposed_representation.components:
        reason = c.irreducibility_reason_code or c.prose_retention_reason_code
        by_reason.setdefault(reason, []).append((c.record_key, c.semantic_key))
    assert Counter({k: len(v) for k, v in by_reason.items()}) == {
        "no_identified_structured_use": 65,
        "contextual_applicability": 2,
        "gamemaster_latitude": 5,
    }
    assert sorted(by_reason["gamemaster_latitude"]) == [
        ("glossary.ally", "ally"),
        ("glossary.d20_test", "d20_test"),
        ("glossary.enemy", "enemy"),
        ("glossary.improvised_weapons", "damage"),
        ("glossary.improvised_weapons", "weapon_equivalents"),
    ]
    assert sorted(by_reason["contextual_applicability"]) == [
        ("glossary.illusions", "illusions_in_space"),
        ("glossary.improvised_weapons", "improvised_weapons"),
    ]


def test_the_action_table_is_the_release_s_own_rows_after_its_prose(built) -> None:  # type: ignore[no-untyped-def]
    table = GEN.ACTIONS_TABLE
    first, second, read = _texts(built, "glossary.action", "action")
    assert read == table and table.count("<tr>") == 3 and table.count("<td>") == 12
    assert "<" not in first + second
    spans = {s.span_id: s for s in built.ledger.spans}
    leaves = [
        built.leaf_rows[spans[b.span_id].leaf_id]
        for b in built.proposal.proposed_representation.prose_bindings
        if (b.record_key, b.component_key) == ("glossary.action", "action")
    ]
    assert leaves[2].content == table
    assert leaves[2].occurrence_index == leaves[0].occurrence_index + 1


def _candidate(built: Built) -> ProjectionCandidate:
    return ProjectionCandidate(
        binding=built.binding,
        classification=built.ledger,
        representation=built.proposal.proposed_representation,
        schema_version=REPRESENTATION_SCHEMA_VERSION,
        schema_hash=representation_schema_hash(),
    )


def _primary(built) -> dict[tuple[str, str, str], tuple[int, int]]:  # type: ignore[no-untyped-def]
    """Each span a component owns, at its printed position."""
    spans = {s.span_id: s for s in built.ledger.spans}
    rep = built.proposal.proposed_representation
    bindings = {prose_binding_target_key(b): b for b in rep.prose_bindings}
    out = {}
    for c in rep.provenance:
        if (
            c.target_kind is ProvenanceTargetKind.PROSE_BINDING
            and c.role is ProvenanceRole.PRIMARY
        ):
            b = bindings[c.target_key]
            span = spans[c.span_id]
            out[(b.record_key, b.component_key, c.span_id)] = (
                built.leaf_rows[span.leaf_id].occurrence_index,
                span.char_start,
            )
    return out


def _clause(rk: tuple[str, str]):  # type: ignore[no-untyped-def]
    (clause,) = [c for c in GEN.CLAUSES if (_record(c[0]), c[1]) == rk]
    return clause


def test_a_gamemaster_reads_every_component_in_printed_order(session, built) -> None:  # type: ignore[no-untyped-def]
    candidate = _candidate(built)
    state = EffectiveOverrideSet(
        built.binding.package_uuid, built.binding.release_version, ()
    )
    authority = apply_override_set(
        candidate,
        state,
        RulesPackageBinding(
            package_uuid=UUID(built.binding.package_uuid),
            release_version=built.binding.release_version,
            mechanical_projection_uuid=UUID(
                identify_projection(candidate).projection_uuid
            ),
            override_set_uuid=UUID(state.override_set_uuid),
        ),
        leaf_order=source_leaf_order(session, candidate),
    )
    prose = {
        row.chunk_id: row.content
        for row in session.query(RuleChunkORM).filter(
            RuleChunkORM.rules_package_id == str(built.binding.package_uuid)
        )
    }
    view = list(build_gamemaster_view(authority, prose).components)
    assert [(c.record_key, c.component_key) for c in view] == sorted(
        ((_record(e), k) for e, k, _, _ in GEN.CLAUSES),
        key=lambda rk: (rk[0], GEN.CLAUSES.index(_clause(rk))),
    )
    primary = _primary(built)
    for c in view:
        passages = [e for e in c.governing_prose if isinstance(e, SourceProse)]
        printed = [
            primary[(c.record_key, c.component_key, e.span_id)] for e in passages
        ]
        assert printed == sorted(printed)
        assert [e.text for e in passages] == list(
            _clause((c.record_key, c.component_key))[3]
        )
        assert c.structured_context == ()


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------


def _refs(built) -> list[tuple[str, str, str, str, str]]:  # type: ignore[no-untyped-def]
    return [
        (
            r.from_record_key,
            r.from_component_key,
            r.source_text,
            r.scope_key,
            r.target_record_key,
        )
        for r in built.proposal.proposed_representation.references
    ]


def test_part_level_pointers_stay_unresolved_and_name_no_record(built) -> None:  # type: ignore[no-untyped-def]
    assert sorted(r for r in _refs(built) if not r[4]) == [
        ("glossary.cantrip", "", "Spells", SPELLS, ""),
        (
            "glossary.character_sheet",
            "",
            "Character Creation",
            CHARACTER_CREATION,
            "",
        ),
        (
            "glossary.hit_point_dice",
            "hit_point_dice",
            "Character Creation",
            CHARACTER_CREATION,
            "",
        ),
        (
            "glossary.player_character",
            "",
            "Character Creation",
            CHARACTER_CREATION,
            "",
        ),
        ("glossary.ritual", "", "Spells", SPELLS, ""),
        ("glossary.spell", "spell", "Spells", SPELLS, ""),
        ("glossary.spell_attack", "", "Casting Spells", SPELLS, ""),
        ("glossary.spellcasting_focus", "", "Casting Spells", SPELLS, ""),
    ]
    # Casting Spells is narrower in the release than the section the pointer
    # names; the batch does not substitute it.
    assert "spells.casting_spells" not in {r[4] for r in _refs(built)}


def test_cross_part_pointers_name_the_accepted_records_printed(built) -> None:  # type: ignore[no-untyped-def]
    outside = sorted(r for r in _refs(built) if r[3] in (EQUIPMENT, SPELLS) and r[4])
    assert outside == [
        ("glossary.armor_training", "", "Armor", EQUIPMENT, "equipment.armor"),
        (
            "glossary.armor_training",
            "armor_training",
            "Light",
            EQUIPMENT,
            "equipment.armor.category",
        ),
        (
            "glossary.armor_training",
            "armor_training",
            "Shield",
            EQUIPMENT,
            "equipment.armor.shield",
        ),
        (
            "glossary.attunement",
            "",
            "Magic Items",
            EQUIPMENT,
            "equipment.magic_items",
        ),
        (
            "glossary.improvised_weapons",
            "improvised_weapons",
            "Ranged weapon",
            EQUIPMENT,
            "equipment.weapons.melee_or_ranged",
        ),
        (
            "glossary.improvised_weapons",
            "improvised_weapons",
            "Simple",
            EQUIPMENT,
            "equipment.weapons.category",
        ),
        (
            "glossary.improvised_weapons",
            "improvised_weapons",
            "Thrown property",
            EQUIPMENT,
            "equipment.weapons.thrown",
        ),
        (
            "glossary.improvised_weapons",
            "weapon_equivalents",
            "Simple",
            EQUIPMENT,
            "equipment.weapons.category",
        ),
        (
            "glossary.spellcasting_focus",
            "spellcasting_focus",
            "Material components",
            SPELLS,
            "spells.components",
        ),
        ("glossary.weapon", "", "Weapons", EQUIPMENT, "equipment.weapons"),
        (
            "glossary.weapon",
            "weapon",
            "Simple",
            EQUIPMENT,
            "equipment.weapons.category",
        ),
    ]


def test_the_npc_pointer_names_the_entry_that_defines_it(built) -> None:  # type: ignore[no-untyped-def]
    assert (
        "glossary.monster",
        "",
        "NPC",
        GLOSSARY,
        "glossary.nonplayer_character",
    ) in (_refs(built))


def test_glossary_terms_are_cited_from_prose_only(built) -> None:  # type: ignore[no-untyped-def]
    refs = _refs(built)
    # An entry never cites itself, and the Action table cites its twelve.
    assert not [r for r in refs if r[0] == r[4]]
    assert [r[2] for r in refs if r[:2] == ("glossary.action", "action")] == [
        "Attack",
        "Dodge",
        "Influence",
        "Search",
        "Dash",
        "Help",
        "Magic",
        "Study",
        "Disengage",
        "Hide",
        "Ready",
        "Utilize",
    ]
    # A compound term is cited whole, never truncated inside a longer name.
    assert [r[2:] for r in refs if r[0] == "glossary.hit_point_dice"] == [
        ("Character Creation", CHARACTER_CREATION, ""),
        ("Hit Point maximum", GLOSSARY, "glossary.hit_points"),
        ("Short Rest", GLOSSARY, "glossary.short_rest"),
    ]
    assert "Hit Point" not in {r[2] for r in refs}
    texts = {r[2] for r in refs}
    # Examples and terms the rules only use are not references.
    for example in (
        "Club",
        "Remove Curse",
        "Greater Restoration",
        "Polymorph",
        "Wild Shape",
        "Proficiency Bonus",
        "creature",
        "object",
        "spell",
    ):
        assert example not in texts


def test_see_also_pointers_are_supporting_and_record_owned(built) -> None:  # type: ignore[no-untyped-def]
    supporting = sorted(
        built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end]
        for s in built.ledger.spans
        if s.disposition.name == "SUPPORTING_AUTHORITY"
    )
    assert supporting == sorted(text for _, text, _ in GEN.SEE_ALSO)
    assert len(supporting) == 42
    record_owned = {(r[0], r[2], r[4]) for r in _refs(built) if not r[1]}
    for entry, _, pointers in GEN.SEE_ALSO:
        for printed, target in pointers:
            key = GEN.scoped(target)[1]
            stated = any(
                r[0] == _record(entry) and r[1] and (r[2], r[4]) == (printed, key)
                for r in _refs(built)
            )
            assert stated or (_record(entry), printed, key) in record_owned


# ---------------------------------------------------------------------------
# Coverage and omission
# ---------------------------------------------------------------------------


def test_only_headings_are_excluded(built) -> None:  # type: ignore[no-untyped-def]
    excluded = [
        built.leaf_rows[leaf].content
        for u in built.proposal.proposed_review_units
        for g in u.excluded_groups
        for leaf in g.leaf_ids
    ]
    assert all(e.startswith("#### ") and "\n" not in e for e in excluded)
    assert len(excluded) == 60
    assert not [
        leaf
        for u in built.proposal.proposed_review_units
        for g in u.supporting_groups
        for leaf in g.leaf_ids
    ]


def _residue(built) -> dict[str, str]:  # type: ignore[no-untyped-def]
    """Text of a spanned leaf no span covers, blockquote markers aside."""
    out = {}
    for lid in {s.leaf_id for s in built.ledger.spans}:
        text = list(built.leaf_rows[lid].content)
        for s in built.ledger.spans:
            if s.leaf_id == lid:
                text[s.char_start : s.char_end] = " " * (s.char_end - s.char_start)
        if left := "".join(text).replace(">", "").strip():
            out[lid] = left
    return out


def test_every_spanned_leaf_is_claimed_to_the_last_word(built) -> None:  # type: ignore[no-untyped-def]
    assert _residue(built) == {}


def _drop(monkeypatch, entry: str, key: str, text: str | None = None) -> None:  # type: ignore[no-untyped-def]
    """Drop a whole clause, or one text of it, from the review and its component."""
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(
            (e, k, f, tuple(t for t in ts if t != text))
            for e, k, f, ts in GEN.CLAUSES
            if text is not None or (e, k) != (entry, key)
        ),
    )
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(
            c
            for c in GEN.COMPONENTS
            if text is not None or (c.entry, c.key) != (entry, key)
        ),
    )


@pytest.mark.parametrize(
    ("entry", "key", "text"),
    [
        ("improvised_weapons", "range", None),
        ("teleportation", "occupied_destination", None),
        ("telepathy", "non_telepaths", None),
        ("ally", "ally", None),
    ],
)
def test_a_dropped_table_or_rule_is_reported(  # type: ignore[no-untyped-def]
    session, monkeypatch, entry, key, text
) -> None:
    _drop(monkeypatch, entry, key, getattr(GEN, text) if text else None)
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found and all(
        f.startswith(f"review unit rules-glossary-completion/{entry}: leaf ")
        for f in found
    ), found


def test_a_dropped_action_table_is_a_loud_failure(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # The twelve actions it lists are cited from it; without it they cite nothing.
    _drop(monkeypatch, "action", "action", GEN.ACTIONS_TABLE)
    with pytest.raises(ValueError, match="'Attack' of \\('action', 'action'\\) cites"):
        GEN.build(session)


def test_a_rule_dropped_beside_its_see_also_is_left_as_residue(  # type: ignore[no-untyped-def]
    session, monkeypatch
) -> None:
    # The shared review-unit check counts a leaf a supporting span touches as
    # claimed; the words a dropped rule leaves beside it are residue, caught here.
    _drop(monkeypatch, "weapon_attack", "weapon_attack")
    dropped = GEN.build(session)
    assert GEN.batch_findings(dropped)["review_units"] == []
    (left,) = _residue(dropped).values()
    assert left.startswith("A weapon attack is an attack roll made with a weapon")


def test_a_table_missing_a_row_is_a_loud_locate_failure(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    table = GEN.ACTIONS_TABLE
    row = (
        "    <tr>\n      <td>Dash</td>\n      <td>Help</td>\n"
        "      <td>Magic</td>\n      <td>Study</td>\n    </tr>\n"
    )
    shorter = table.replace(row, "")
    assert shorter != table
    monkeypatch.setattr(
        GEN,
        "CLAUSES",
        tuple(
            (e, k, f, tuple(shorter if t == table else t for t in ts))
            for e, k, f, ts in GEN.CLAUSES
        ),
    )
    with pytest.raises(ValueError, match="occurs 0 times"):
        GEN.build(session)


def test_a_component_omitted_while_authoring_is_reported(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        GEN,
        "COMPONENTS",
        tuple(
            c
            for c in GEN.COMPONENTS
            if (c.entry, c.key) != ("improvised_weapons", "damage")
        ),
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert (
        "review unit rules-glossary-completion/improvised_weapons: expected rule "
        "glossary.improvised_weapons/damage has no component"
    ) in found


# ---------------------------------------------------------------------------
# Test-only composition with the recorded fourteen-batch chain
# ---------------------------------------------------------------------------


def _composed(prior: AcceptedInputs, proposal: MechanicalProposal) -> AcceptedInputs:
    oracle, accepted = prior.oracle, prior.oracle.representation
    proposed = proposal.proposed_representation
    return dataclasses.replace(
        prior,
        oracle=dataclasses.replace(
            oracle,
            spans=(*oracle.spans, *(p.span for p in proposal.proposed_spans)),
            review_units=(*oracle.review_units, *proposal.proposed_review_units),
            representation=dataclasses.replace(
                accepted,
                **{
                    f.name: (*getattr(accepted, f.name), *getattr(proposed, f.name))
                    for f in dataclasses.fields(accepted)
                },
            ),
        ),
    )


def test_the_recorded_chain_is_the_state_the_proposal_extends(  # type: ignore[no-untyped-def]
    recorded, prior
) -> None:
    # Both the superseded release's. Judging the composition against a corpus
    # needs that release's, which is not rebuilt: that check is retired.
    assert recorded.binding == prior.oracle.binding
    prior = lifted(prior)
    assert prior.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert len(prior.oracle.representation.records) == 235
    assert len(prior.oracle.spans) == 1497
    assert len(prior.batches) == 14
    assert len(prior.oracle.reference_resolutions) == 50
    assert IDENTITY not in {b.proposal_identity for b in prior.batches}
    assert not {s.span_id for s in prior.oracle.spans} & {
        p.span.span_id for p in recorded.proposed_spans
    }


def test_the_recorded_resolutions_still_apply_composed(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    composed = _composed(prior, recorded)
    assert (
        reference_resolution_violations(
            composed.oracle.representation,
            prior.oracle.reference_resolutions,
            prior.oracle.binding,
        )
        == []
    )


def test_it_accepts_through_the_native_seam_in_memory_only(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    oracle = REPO / "src/afterworlds/ingestion/mechanical/oracles"
    on_disk = {p.name: p.read_bytes() for p in oracle.glob("*.json")}
    proposal = recorded
    accepted = accept_proposal(
        proposal,
        batch_id="rules-glossary-completion",
        rule="test-only",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer="test",
        accepted_at="2026-09-25T00:00:00Z",
        prior=prior,
    )
    assert [b.batch_id for b in accepted.batches][-1] == "rules-glossary-completion"
    assert len(accepted.oracle.representation.records) == 235 + 60
    assert accepted.oracle.reference_resolutions == prior.oracle.reference_resolutions
    assert {p.name: p.read_bytes() for p in oracle.glob("*.json")} == on_disk


# ---------------------------------------------------------------------------
# Through the production rules-authority service
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db, built):  # type: ignore[no-untyped-def]
    """The proposal persisted as a draft into a private copy of the release."""
    path = tmp_path_factory.mktemp("rules_glossary_completion") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(_candidate(built))
        persist_draft(s, identified, now="2026-09-25T00:00:00Z")
        s.commit()
        yield s, identified.projection_uuid
    engine.dispose()


def _read(service, built, *records: str, components=()):  # type: ignore[no-untyped-def]
    view = service.gamemaster_view(_request(built, *records, components=components))
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    return view.gamemaster_view.components


def _printed(entry: str) -> list[str]:
    return [k for e, k, _, _ in GEN.CLAUSES if e == entry]


def test_an_entry_reads_its_rules_as_the_source_prints_them(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    for entry in ("improvised_weapons", "teleportation", "telepathy", "action"):
        view = _read(service, built, _record(entry))
        clauses = {k: ts for e, k, _, ts in GEN.CLAUSES if e == entry}
        assert [c.component_key for c in view] == _printed(entry)
        for c in view:
            assert [e.text for e in c.governing_prose] == list(clauses[c.component_key])
    # Key order would put the damage rule before the definition it qualifies.
    assert _printed("improvised_weapons")[0] == "improvised_weapons"
    assert _printed("improvised_weapons") != sorted(_printed("improvised_weapons"))


def test_narrowing_to_some_rules_keeps_their_printed_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    record = "glossary.improvised_weapons"
    wanted = ("weapon_equivalents", "range", "improvised_weapons")
    view = _read(service, built, components=tuple((record, k) for k in wanted))
    assert [c.component_key for c in view] == [
        k for k in _printed("improvised_weapons") if k in wanted
    ]


def test_a_disabled_record_stays_gone(persisted, built, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _service(persisted, built, monkeypatch, _disable("glossary.ally"))
    records = ("glossary.enemy", "glossary.weapon", "glossary.target")
    assert _sliced(service, _request(built, *records)) == sorted(records)
    view = _read(service, built, *records)
    assert "glossary.ally" not in {c.record_key for c in view}
    direct = service.rule_slice(_request(built, "glossary.ally"))
    assert direct.outcome is AuthorityOutcome.INVALID_REFERENCE


def test_a_replaced_component_reads_replaced_in_its_place(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    record, key = "glossary.improvised_weapons", "damage"
    replaced_entry = EffectiveOverrideEntry(
        override_id=f"replace-{record}-{key}",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT, record_key=record, component_key=key
        ),
        operation=OverrideOperationEnum.REPLACE,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={
            "patch": "replace_component",
            "component": {
                "handling": "prose_bound",
                "facts": [],
                "authored_prose": "A house damage rule.",
            },
        },
    )
    service = _service(persisted, built, monkeypatch, replaced_entry)
    view = _read(service, built, record)
    keys = [c.component_key for c in view]
    assert keys == _printed("improvised_weapons")
    replaced = view[keys.index(key)]
    assert keys.index(key) == 2
    (entry,) = replaced.governing_prose
    assert isinstance(entry, AuthoredProse) and entry.text == "A house damage rule."
    assert all(
        isinstance(e, SourceProse)
        for c in view
        if c is not replaced
        for e in c.governing_prose
    )


def test_an_authored_rule_reads_after_the_source_s(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    appended = EffectiveOverrideEntry(
        override_id="append-glossary-improvised-weapons-house",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.RECORD, record_key="glossary.improvised_weapons"
        ),
        operation=OverrideOperationEnum.APPEND,
        precedence=100,
        apply_order=0,
        is_enabled=True,
        payload={
            "patch": "append_component",
            "component": {
                "semantic_key": "aaa_house_rule",
                "handling": "prose_bound",
                "facts": [],
                "authored_prose": "A house improvised-weapon rule.",
            },
        },
    )
    service = _service(persisted, built, monkeypatch, appended)
    view = _read(service, built, "glossary.improvised_weapons")
    assert [c.component_key for c in view] == [
        *_printed("improvised_weapons"),
        "aaa_house_rule",
    ]
    (entry,) = view[-1].governing_prose
    assert (
        isinstance(entry, AuthoredProse)
        and entry.text == "A house improvised-weapon rule."
    )


def test_a_session_is_the_published_release(session: Session, built) -> None:  # type: ignore[no-untyped-def]
    assert (
        built.binding.package_uuid,
        built.binding.release_version,
    ) == (
        current().oracle.binding.package_uuid,
        current().oracle.binding.release_version,
    )


# ---------------------------------------------------------------------------
# The recorded acceptance
# ---------------------------------------------------------------------------


def test_the_committed_oracle_records_the_owner_acceptance(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    # The superseded release's committed oracle, read by path: the production
    # resolver refuses its binding.
    committed = load_accepted_inputs(ORACLE)
    # The fifteen-batch state the Classes chunks were accepted over; the
    # Animals recording keeps it whole (the committed file keeps that outside
    # the replaced Equipment batch).
    replayed = through(BATCH)
    assert not kept_whole(replayed, animals_recorded())
    (batch,) = [b for b in committed.batches if b.batch_id == BATCH]
    assert (batch.proposal_identity, batch.rule) == (IDENTITY, REPLACEMENT.APPROVAL)
    mine = [a for a in committed.acceptances if a.batch_id == BATCH]
    assert set(batch.resolved_scope) == {a.span_id for a in mine}
    assert set(batch.resolved_scope) == {
        p.span.span_id for p in recorded.proposed_spans
    }
    assert {(a.reviewer, a.accepted_at) for a in mine} == {
        (REPLACEMENT.OWNER, REPLACEMENT.ACCEPTED_AT)
    }
    final = replayed.oracle
    assert (
        len(replayed.batches),
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (15, 295, 1613, 229, 50)
    # A loaded file holds them in canonical order, not recorded order.
    assert set(final.reference_resolutions) == set(prior.oracle.reference_resolutions)
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )
