"""The ``spellcasting`` proposal, offered for review -- CRD Issue 5d.

The general spellcasting rules of the *Spells* part -- gaining, preparing and
always-prepared spells; spell level, slots, casting without slots and
higher-level slots; schools and class spell lists; casting time and triggers;
range, components, duration, effects, targets, saving throws, attack rolls
and combining effects -- and the Rules Glossary entries they point at (*Area
of Effect*, its six shapes and *Cover*), proposed by
``.claude/review-notes/issue-5d-spellcasting-generator.py`` from the release
5c actually publishes. Nothing here records it.

What is pinned, and why:

* the committed bytes are the recorded proposal under its recorded identity, and
  the artifact is a proposal by shape. The generator now builds over the current
  release, so its output is no longer those bytes; that cross-release equality
  is retired (``correction-followup.md``);
* scope is the eleven sections before *Spell Descriptions*, less the part
  title, and the eight glossary entries, one record each, and no leaf is owned
  by an accepted unit;
* the batch checks report the accepted out-of-batch targets and the pouch's
  two unresolved citations, and nothing else;
* fidelity: every component stays prose-bound; each table is the release's
  own rows after the prose that introduces it; a GameMaster reads every
  passage in printed order;
* references: in-batch pointers name the record they cite, accepted glossary
  terms are cited from prose only, the Component Pouch and the Equipment
  it is described in stay unresolved under the Equipment scope -- no
  accepted record is that item -- and nothing names the *Classes* part;
* every word of every spanned leaf is claimed, only headings are excluded, and
  a dropped table, rule or component is reported;
* composed *in this test only* with the thirteen-batch state of the recorded
  replacement chain, rebuilt natively and kept whole in the committed oracle:
  every target
  out of the batch closes, exactly its 104 leaves gain coverage and the forty-nine
  recorded resolutions still apply;
* the one resolution draft names an accepted citation exactly, cannot apply
  while its target is unaccepted, and -- in memory only -- resolves once the
  batch is accepted, leaving the other twenty-five "Spells" citations;
* through the production rules-authority service, a section reads its rules
  in printed order, a disabled record stays gone, a replaced component reads
  replaced where it is printed, an authored addition reads after the source,
  and narrowing to some components keeps their printed order.
"""

from __future__ import annotations

import dataclasses
import hashlib
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

from afterworlds.ingestion.mechanical.acceptance import (
    AcceptanceError,
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.accounting import validate_acceptance
from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.models import (
    ComponentHandling,
    ReferenceResolution,
    ReviewState,
    ReviewUnitKind,
)
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    OracleLoadError,
    candidate_from_accepted_inputs,
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
    effective_representation,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import (
    REPRESENTATION_SCHEMA_VERSION,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordKind,
    ReferenceDraft,
    prose_binding_target_key,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
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
GENERATOR = NOTES / "issue-5d-spellcasting-generator.py"
BATCH = "spellcasting"
PROPOSAL = proposal_path(BATCH)
IDENTITY = identity(BATCH)
DRAFTS = REPLACEMENT.drafts_path(BATCH)

GLOSSARY = "srd-5.2.1/rules-glossary"
SPELLS = "srd-5.2.1/spells"
EQUIPMENT = "srd-5.2.1/equipment"
PLAY = "srd-5.2.1/playing-the-game"
#: Accepted glossary entries this batch cites; each is an unknown target to
#: the batch alone and closes composed.
GLOSSARY_TARGETS = {
    "attack_roll",
    "concentration",
    "hostile",
    "incapacitated",
    "long_rest",
    "magic",
    "reach",
    "study",
}
#: The glossary entries this batch authors.
AUTHORED = ["area_of_effect", "cone", "cover", "cube", "cylinder", "emanation"]
AUTHORED += ["line", "sphere"]


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load("spellcasting", GENERATOR)


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
    """The recorded thirteen-batch state, rebuilt natively.

    The Animals recording extends it and keeps it whole (a loaded file holds
    its batches in canonical order, so it is compared as a multiset); the
    committed oracle keeps that outside the replaced Equipment batch.
    """
    order = list(BATCHES)
    rebuilt = through(order[order.index(BATCH) - 1])
    assert not kept_whole(rebuilt, animals_recorded())
    return rebuilt


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
    key: str = GEN.batch().record_key(entry)
    return key


# ---------------------------------------------------------------------------
# The artifact
# ---------------------------------------------------------------------------


def test_the_committed_bytes_are_the_recorded_proposal(built) -> None:  # type: ignore[no-untyped-def]
    assert proposal_identity(load_proposal(PROPOSAL, expected_identity=IDENTITY)) == (
        IDENTITY
    )
    assert b"\r" not in PROPOSAL.read_bytes()
    # The generator builds over the current release.
    assert built.binding == current().oracle.binding


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


SECTION_UNITS = [
    ("gaining_spells", 8),
    ("casting_spells", 22),
    ("casting_time", 8),
    ("range", 7),
    ("components", 9),
    ("duration", 5),
    ("effects", 2),
    ("targets", 8),
    ("saving_throws", 3),
    ("attack_rolls", 3),
    ("combining_spell_effects", 3),
]
GLOSSARY_UNITS = [
    ("area_of_effect", 5),
    ("cone", 3),
    ("cover", 2),
    ("cube", 3),
    ("cylinder", 3),
    ("emanation", 4),
    ("line", 3),
    ("sphere", 3),
]


def test_scope_is_the_rules_before_spell_descriptions_and_their_glossary_entries(  # type: ignore[no-untyped-def]
    session, built
) -> None:
    units = built.proposal.proposed_review_units
    assert [(u.unit_id, u.kind, len(u.leaf_ids)) for u in units] == [
        *((f"spellcasting/{s}", ReviewUnitKind.SECTION, n) for s, n in SECTION_UNITS),
        *((f"spellcasting/{s}", ReviewUnitKind.ENTRY, n) for s, n in GLOSSARY_UNITS),
    ]
    records = built.proposal.proposed_representation.records
    assert [(r.semantic_key, r.kind) for r in records] == [
        *((f"spells.{s}", RecordKind.GENERAL_RULE) for s, _ in SECTION_UNITS),
        *((f"glossary.{s}", RecordKind.GLOSSARY_RULE) for s in AUTHORED),
    ]
    assert not built.proposal.proposed_representation.relationships
    # The sections are contiguous, in printed order, and the part title before
    # them is owned by no unit; *Spell Descriptions* follows, unauthored.
    flat = [
        built.leaf_rows[leaf].occurrence_index
        for u in units[: len(SECTION_UNITS)]
        for leaf in u.leaf_ids
    ]
    assert sorted(flat) == list(range(flat[0], flat[0] + 78))

    def content(occurrence: int) -> str:
        (row,) = session.query(LedgerLeafORM.content).filter(
            LedgerLeafORM.package_uuid == built.binding.package_uuid,
            LedgerLeafORM.occurrence_index == occurrence,
        )
        return str(row.content)

    assert content(min(flat) - 1) == "# Spells"
    assert content(max(flat) + 1) == "## Spell Descriptions"
    # Each unit's leaves are its own, in printed order.
    for u in units:
        order = [built.leaf_rows[leaf].occurrence_index for leaf in u.leaf_ids]
        assert order == sorted(order), u.unit_id


def test_no_leaf_is_owned_by_an_accepted_unit(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    # Both sides are the superseded release's state, never mixed with the current.
    assert recorded.binding == prior.oracle.binding
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert len(mine) == 104
    assert not owned & mine
    accepted = {r.semantic_key for r in prior.oracle.representation.records}
    assert not accepted & {
        r.semantic_key for r in recorded.proposed_representation.records
    }


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings()
    assert [f for f in found["representation"] if "unresolved" in f] == [
        f"reference {EQUIPMENT}:'Component Pouch': unresolved reference",
        f"reference {EQUIPMENT}:'Equipment': unresolved reference",
    ]
    unknown = {
        f.rsplit(" ", 1)[1]
        for f in found["representation"]
        if "unknown target record" in f
    }
    assert unknown == {f"glossary.{g}" for g in GLOSSARY_TARGETS} | {"play.combat"}
    assert len(found["representation"]) == 14


# ---------------------------------------------------------------------------
# Fidelity
# ---------------------------------------------------------------------------


def test_every_component_stays_faithful_prose(built) -> None:  # type: ignore[no-untyped-def]
    components = built.proposal.proposed_representation.components
    assert len(components) == 55
    assert {c.handling for c in components} == {ComponentHandling.PROSE_BOUND}
    assert not [c for c in components if c.all_facts()]
    text = PROPOSAL.read_text("utf-8")
    for family in (
        "SpellDescriptorFact",
        "SpellSlotProgressionFact",
        "ProficiencyBonusUseFact",
        "ResourceRecoveryFact",
    ):
        assert family not in text
    # Each component reads its reviewed clause, whole and in order.
    for entry, key, _, texts in GEN.CLAUSES:
        assert _texts(built, _record(entry), key) == list(texts), (entry, key)


def test_latitude_and_context_are_only_where_the_rule_leaves_them(built) -> None:  # type: ignore[no-untyped-def]
    by_reason: dict[str, list[tuple[str, str]]] = {}
    for c in built.proposal.proposed_representation.components:
        reason = c.irreducibility_reason_code or c.prose_retention_reason_code
        by_reason.setdefault(reason, []).append((c.record_key, c.semantic_key))
    assert Counter({k: len(v) for k, v in by_reason.items()}) == {
        "no_identified_structured_use": 52,
        "contextual_applicability": 1,
        "gamemaster_latitude": 2,
    }
    assert sorted(by_reason["gamemaster_latitude"]) == [
        ("spells.effects", "effects"),
        ("spells.gaining_spells", "monster_prepared_spells"),
    ]
    assert by_reason["contextual_applicability"] == [
        ("spells.targets", "awareness_of_being_targeted")
    ]


@pytest.mark.parametrize(
    ("entry", "key", "name", "rows"),
    [
        ("gaining_spells", "preparing_spells", "SPELL_PREPARATION_TABLE", 9),
        ("casting_spells", "school_of_magic", "SCHOOLS_OF_MAGIC_TABLE", 9),
        ("area_of_effect", "area_of_effect", "AREA_SHAPES_TABLE", 2),
    ],
)
def test_each_table_is_the_release_s_own_rows_after_its_prose(  # type: ignore[no-untyped-def]
    built, entry, key, name, rows
) -> None:
    table = getattr(GEN, name)
    prose, read = _texts(built, _record(entry), key)
    assert read == table
    assert table.count("<tr>") == rows
    assert "<" not in prose
    # The table is a whole leaf of the release, after the prose that
    # introduces it.
    spans = {s.span_id: s for s in built.ledger.spans}
    leaves = [
        built.leaf_rows[spans[b.span_id].leaf_id]
        for b in built.proposal.proposed_representation.prose_bindings
        if (b.record_key, b.component_key) == (_record(entry), key)
    ]
    assert leaves[1].content == table
    assert leaves[1].occurrence_index == leaves[0].occurrence_index + 1


def test_the_spell_preparation_table_keeps_every_class_in_printed_order() -> None:
    import re

    classes = re.findall(r"<tr>\s*<td>([^<]+)</td>", GEN.SPELL_PREPARATION_TABLE)
    assert classes == [
        "Bard",
        "Cleric",
        "Druid",
        "Paladin",
        "Ranger",
        "Sorcerer",
        "Warlock",
        "Wizard",
    ]
    assert "<th>Change When You…</th>" in GEN.SPELL_PREPARATION_TABLE


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
    # Every component once; records in key order (ADR-005d Decision 9), and
    # within a record its rules as the source prints them.
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
        (texts,) = [
            ts
            for e, k, _, ts in GEN.CLAUSES
            if (_record(e), k) == (c.record_key, c.component_key)
        ]
        assert [e.text for e in passages] == list(texts)
        assert c.structured_context == ()


# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------


def _refs(built) -> set[tuple[str, str, str, str, str]]:  # type: ignore[no-untyped-def]
    return {
        (
            r.from_record_key,
            r.from_component_key,
            r.source_text,
            r.scope_key,
            r.target_record_key,
        )
        for r in built.proposal.proposed_representation.references
    }


def test_in_batch_pointers_name_the_record_they_cite(built) -> None:  # type: ignore[no-untyped-def]
    records = {r.semantic_key for r in built.proposal.proposed_representation.records}
    refs = _refs(built)
    in_batch = {r for r in refs if r[4] in records}
    shapes = [("Cone", "cone"), ("Cube", "cube"), ("Cylinder", "cylinder")]
    shapes += [("Emanation", "emanation"), ("Line", "line"), ("Sphere", "sphere")]
    assert in_batch == {
        # "each of which is detailed below"
        ("spells.effects", "effects", "targets", SPELLS, "spells.targets"),
        ("spells.effects", "effects", "saving throws", SPELLS, "spells.saving_throws"),
        ("spells.effects", "effects", "attack rolls", SPELLS, "spells.attack_rolls"),
        # "defined in "Rules Glossary"", and the shapes it names
        (
            "spells.targets",
            "areas_of_effect",
            "area of effect",
            GLOSSARY,
            "glossary.area_of_effect",
        ),
        *(
            ("spells.targets", "areas_of_effect", text, GLOSSARY, f"glossary.{s}")
            for text, s in shapes
        ),
        ("spells.targets", "clear_path", "Total Cover", GLOSSARY, "glossary.cover"),
        # The entry's list of shapes "defined elsewhere in this glossary"
        *(
            (
                "glossary.area_of_effect",
                "area_of_effect",
                text,
                GLOSSARY,
                f"glossary.{s}",
            )
            for text, s in shapes
        ),
        (
            "glossary.area_of_effect",
            "point_of_origin",
            "Total Cover",
            GLOSSARY,
            "glossary.cover",
        ),
        ("glossary.area_of_effect", "", "Cover", GLOSSARY, "glossary.cover"),
        *(
            (
                f"glossary.{s}",
                s,
                "area of effect",
                GLOSSARY,
                "glossary.area_of_effect",
            )
            for _, s in shapes
        ),
    }
    assert len(refs) == 39


def test_pointers_outside_the_batch_are_accepted_or_left_unresolved(built) -> None:  # type: ignore[no-untyped-def]
    refs = _refs(built)
    # The Component Pouch is a named item no accepted record is; the whole
    # Adventuring Gear section does not stand in for it.
    pouch = ("spells.components", "component_pouch_and_focus")
    assert {r for r in refs if r[3] in (EQUIPMENT, PLAY)} == {
        (*pouch, "Component Pouch", EQUIPMENT, ""),
        (*pouch, "Equipment", EQUIPMENT, ""),
        ("glossary.cover", "", "Combat", PLAY, "play.combat"),
    }
    # Nothing names the *Classes* part, and only the pouch is unresolved.
    assert {r[:3] for r in refs if not r[4]} == {
        (*pouch, "Component Pouch"),
        (*pouch, "Equipment"),
    }
    assert {r[3] for r in refs} == {GLOSSARY, SPELLS, EQUIPMENT, PLAY}


def test_accepted_glossary_terms_are_cited_from_prose_only(built) -> None:  # type: ignore[no-untyped-def]
    authored = {f"glossary.{s}" for s in AUTHORED}
    cited = {
        r.target_record_key.removeprefix("glossary.")
        for r in built.proposal.proposed_representation.references
        if r.scope_key == GLOSSARY and r.target_record_key not in authored
    }
    assert cited == GLOSSARY_TARGETS
    texts = {r.source_text for r in built.proposal.proposed_representation.references}
    # Examples and terms the rules only use are not references.
    for example in (
        "Spell Scroll",
        "Spell Scrolls",
        "Magic Missile",
        "Cure Wounds",
        "Thunderwave",
        "Bless",
        "Wizard",
        "Clerics",
        "Bonus Action",
        "Reaction",
        "Proficiency Bonus",
        "Spellcasting Focus",
        "saving throw",
    ):
        assert example not in texts
    # "reach into it" is a verb: only Touch's "within their reach" is Reach.
    assert [
        (r.from_record_key, r.from_component_key)
        for r in built.proposal.proposed_representation.references
        if r.target_record_key == "glossary.reach"
    ] == [("spells.range", "touch")]


def test_see_also_pointers_are_supporting_and_record_owned(built) -> None:  # type: ignore[no-untyped-def]
    groups = {
        u.unit_id: u.supporting_groups for u in built.proposal.proposed_review_units
    }
    assert groups["spellcasting/area_of_effect"] == ()
    assert groups["spellcasting/cover"] == ()
    supporting = {
        built.leaf_rows[s.leaf_id].content[s.char_start : s.char_end]
        for s in built.ledger.spans
        if s.disposition.name == "SUPPORTING_AUTHORITY"
    }
    assert supporting == {GEN.AREA_SEE_ALSO, GEN.COVER_SEE_ALSO}


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
    assert all(e.startswith("#") and "\n" not in e for e in excluded)
    assert len(excluded) == 19 + sum(len(h) for _, h, _ in GEN.EXCLUDED) == 33
    framing = [
        built.leaf_rows[leaf].content
        for u in built.proposal.proposed_review_units
        for g in u.supporting_groups
        for leaf in g.leaf_ids
    ]
    assert [f.split(" ", 3)[:3] for f in framing] == [["Each", "spell", "description"]]
    # An excluded heading's rule stays readable: the introductions that
    # qualify what follows are components, not framing.
    assert _texts(built, "spells.casting_spells", "casting_without_slots") == [
        "There are several ways to cast a spell without expending a spell slot:"
    ]
    assert "A range usually takes one of the following forms:" in _texts(
        built, "spells.range", "range"
    )


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
        ("gaining_spells", "preparing_spells", "SPELL_PREPARATION_TABLE"),
        ("casting_spells", "school_of_magic", "SCHOOLS_OF_MAGIC_TABLE"),
        ("saving_throws", "spell_save_dc", None),
        ("casting_time", "one_slot_per_turn", None),
        ("combining_spell_effects", "identifying_an_ongoing_spell", None),
        ("emanation", "emanation", None),
    ],
)
def test_a_dropped_table_or_rule_is_reported(  # type: ignore[no-untyped-def]
    session, monkeypatch, entry, key, text
) -> None:
    _drop(monkeypatch, entry, key, getattr(GEN, text) if text else None)
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert found and all(
        f.startswith(f"review unit spellcasting/{entry}: leaf ") for f in found
    ), found


def test_a_table_missing_a_row_is_a_loud_locate_failure(session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    table = GEN.SCHOOLS_OF_MAGIC_TABLE
    row = (
        "    <tr>\n      <td>Divination</td>\n"
        "      <td>Reveals information</td>\n    </tr>\n"
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
            c for c in GEN.COMPONENTS if (c.entry, c.key) != ("components", "material")
        ),
    )
    found = GEN.batch_findings(GEN.build(session))["review_units"]
    assert (
        "review unit spellcasting/components: expected rule "
        "spells.components/material has no component"
    ) in found


# ---------------------------------------------------------------------------
# Test-only composition with the thirteen-batch acceptance
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


def _composed(prior: AcceptedInputs, recorded: MechanicalProposal) -> AcceptedInputs:
    oracle, accepted = prior.oracle, prior.oracle.representation
    proposed = recorded.proposed_representation
    return dataclasses.replace(
        prior,
        oracle=dataclasses.replace(
            oracle,
            spans=(*oracle.spans, *(p.span for p in recorded.proposed_spans)),
            review_units=(*oracle.review_units, *recorded.proposed_review_units),
            representation=dataclasses.replace(
                accepted,
                **{
                    f.name: (*getattr(accepted, f.name), *getattr(proposed, f.name))
                    for f in dataclasses.fields(accepted)
                },
            ),
        ),
    )


def _covered(inputs: AcceptedInputs) -> set[str]:
    oracle = inputs.oracle
    return {s.leaf_id for s in oracle.spans} | {
        leaf for u in oracle.review_units for leaf in u.leaf_ids
    }


def _acceptance(inputs: AcceptedInputs) -> list[str]:
    # Native acceptance evidence (#137 contract 2) reads only the
    # classification ledger: no corpus either.
    return sorted(
        validate_acceptance(candidate_from_accepted_inputs(inputs).classification)
    )


def _references(inputs: AcceptedInputs) -> list[str]:
    # The effective representation's own relationship and reference findings
    # (resolutions applied): no corpus, so none of the superseded release's is
    # needed.
    return relationship_and_reference_violations(
        candidate_from_accepted_inputs(inputs).representation
    )


def test_composed_every_target_closes_and_104_leaves_gain_coverage(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    assert prior.oracle.binding == recorded.binding
    # The replayed chain keeps the schema it was accepted under; it is
    # judged, and composed, at the build's.
    prior = lifted(prior)
    assert prior.oracle.schema_version == REPRESENTATION_SCHEMA_VERSION
    assert len(prior.oracle.representation.records) == 216
    assert len(prior.oracle.spans) == 1425
    assert len(prior.batches) == 13
    assert len(prior.oracle.reference_resolutions) == 49
    assert IDENTITY not in {b.proposal_identity for b in prior.batches}
    assert len(recorded.proposed_spans) == 72
    assert not {s.span_id for s in prior.oracle.spans} & {
        p.span.span_id for p in recorded.proposed_spans
    }
    composed = _composed(prior, recorded)

    # Every reference the batch drafts closes: the retained findings are
    # the accepted ones, the twenty-six "Spells" citations among them, and
    # the Component Pouch's two, unresolved.
    rest_before = sorted(_references(prior))
    assert len([f for f in rest_before if f"reference {SPELLS}:" in f]) == 26
    # Unfiltered and representation-only: nothing else is reported.
    assert sorted(_references(composed)) == sorted(
        [
            *rest_before,
            f"reference {EQUIPMENT}:'Component Pouch': unresolved reference",
            f"reference {EQUIPMENT}:'Equipment': unresolved reference",
        ]
    )
    # The accepted prior's acceptance evidence is clean; composed, each
    # proposed span lacks only its approval, which this proposal never had.
    assert _acceptance(prior) == []
    assert _acceptance(composed) == sorted(
        f"span {p.span.span_id}: no acceptance record" for p in recorded.proposed_spans
    )
    # Exactly the batch's leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(composed) - _covered(prior) == mine
    assert len(mine) == 104


def test_the_recorded_resolutions_still_apply_composed(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    composed = _composed(prior, recorded)
    assert (
        reference_resolution_violations(
            composed.oracle.representation,
            prior.oracle.reference_resolutions,
            prior.oracle.binding,
        )
        == []
    )


# ---------------------------------------------------------------------------
# The "Spells" resolution draft, unrecorded
# ---------------------------------------------------------------------------


def _key(r: ReferenceDraft | ReferenceResolution) -> tuple[str, str, str, str]:
    return (r.from_record_key, r.from_component_key, r.source_text, r.scope_key)


def test_the_committed_drafts_are_what_the_generator_drafts(prior) -> None:  # type: ignore[no-untyped-def]
    from afterworlds.ingestion.mechanical.reference_resolution import (
        reference_resolution_payload,
    )

    drafts = GEN.draft_resolutions(prior.oracle.binding)
    assert json.loads(DRAFTS.read_text("utf-8")) == reference_resolution_payload(drafts)
    assert b"\r" not in DRAFTS.read_bytes()
    assert hashlib.sha256(DRAFTS.read_bytes()).hexdigest() == (
        REPLACEMENT.DRAFTS[BATCH][0]
    )


def test_the_draft_names_an_accepted_citation_exactly(prior) -> None:  # type: ignore[no-untyped-def]
    (draft,) = GEN.draft_resolutions(prior.oracle.binding)
    assert draft.resolution_id not in {
        r.resolution_id for r in prior.oracle.reference_resolutions
    }
    assert (draft.scope_key, draft.target_record_key) == (SPELLS, "spells.attack_rolls")
    accepted = prior.oracle.representation
    (ref,) = [r for r in accepted.references if _key(r) == _key(draft)]
    assert ref.target_record_key == ""
    cited = sorted(
        {
            c.span_id
            for c in accepted.provenance
            if c.target_kind is ProvenanceTargetKind.REFERENCE
            and c.target_key == reference_target_key(ref)
        }
    )
    assert tuple(cited) == draft.provenance_span_ids


def test_every_accepted_spells_citation_is_drafted_or_left_explicit(prior) -> None:  # type: ignore[no-untyped-def]
    cited = sorted(
        _key(r) for r in prior.oracle.representation.references if r.scope_key == SPELLS
    )
    assert len(cited) == 26
    drafted = [_key(d) for d in GEN.draft_resolutions(prior.oracle.binding)]
    left = [(*c, SPELLS) for c in GEN.UNRESOLVED_CITATIONS]
    spells = [c for c in cited if c[2] != "Spells"]
    assert len(spells) == 24
    assert sorted(drafted + left + spells) == cited


def test_the_draft_cannot_apply_to_the_accepted_authority_as_it_stands(prior) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(AcceptanceError, match="states no record for"):
        resolve_references(
            prior,
            resolutions=GEN.draft_resolutions(prior.oracle.binding),
            authorized_by="test",
            authorization_reference="test",
            reviewer="test",
            resolved_at="2026-09-25T00:00:00Z",
        )


def test_once_accepted_the_draft_resolves_through_the_native_seam(
    recorded: MechanicalProposal, prior: AcceptedInputs
) -> None:
    # In memory only: nothing is written and no decision is recorded. The
    # recorded proposal over its recorded prior: both the superseded release's.
    oracle = REPO / "src/afterworlds/ingestion/mechanical/oracles"
    on_disk = {p.name: p.read_bytes() for p in oracle.glob("*.json")}
    proposal = recorded
    accepted = accept_proposal(
        proposal,
        batch_id="spellcasting",
        rule="test-only",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer="test",
        accepted_at="2026-09-25T00:00:00Z",
        prior=prior,
    )
    assert [lift.lift_id for lift in accepted.lifts] == [
        lift.lift_id for lift in prior.lifts
    ]
    drafts = GEN.draft_resolutions(prior.oracle.binding)
    resolved = resolve_references(
        accepted,
        resolutions=drafts,
        authorized_by="test",
        authorization_reference="test",
        reviewer="test",
        resolved_at="2026-09-25T00:00:00Z",
    )
    assert [r.resolution_id for r in resolved.oracle.reference_resolutions] == [
        *(r.resolution_id for r in prior.oracle.reference_resolutions),
        *(d.resolution_id for d in drafts),
    ]
    effective = effective_representation(
        resolved.oracle.representation, resolved.oracle.reference_resolutions
    )
    outside = [
        r
        for r in effective.references
        if r.scope_key == SPELLS and not r.from_record_key.startswith("spells.")
    ]
    assert [
        (r.from_record_key, r.from_component_key, r.source_text, r.target_record_key)
        for r in outside
        if r.target_record_key
    ] == [
        ("play.d20_tests", "attack_ability_modifier", "Spells", "spells.attack_rolls")
    ]
    assert len([r for r in outside if not r.target_record_key]) == 25
    # Every accepted record's own references, and the whole candidate, hold.
    assert (
        reference_resolution_violations(
            resolved.oracle.representation,
            resolved.oracle.reference_resolutions,
            resolved.oracle.binding,
        )
        == []
    )
    # Representation-only: the superseded release's corpus is not available.
    findings = _references(resolved)
    # The one "Spells" citation left is Damage and Healing's, undrafted.
    assert not [f for f in findings if "spells.attack_rolls" in f]
    assert [f for f in findings if "'Spells'" in f] == [
        "reference srd-5.2.1/spells:'Spells': unresolved reference"
    ]
    assert resolved.oracle.representation == accepted.oracle.representation
    assert {p.name: p.read_bytes() for p in oracle.glob("*.json")} == on_disk


# ---------------------------------------------------------------------------
# Through the production rules-authority service
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db, built):  # type: ignore[no-untyped-def]
    """The proposal persisted as a draft into a private copy of the release."""
    path = tmp_path_factory.mktemp("spellcasting") / "release.db"
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


def _replaced(record: str, key: str, text: str) -> EffectiveOverrideEntry:
    return EffectiveOverrideEntry(
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
                "authored_prose": text,
            },
        },
    )


def _printed(entry: str) -> list[str]:
    return [k for e, k, _, _ in GEN.CLAUSES if e == entry]


def test_a_section_reads_its_rules_as_the_source_prints_them(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    for entry in ("components", "casting_spells", "range", "targets", "area_of_effect"):
        view = _read(service, built, _record(entry))
        clauses = {k: ts for e, k, _, ts in GEN.CLAUSES if e == entry}
        assert [c.component_key for c in view] == _printed(entry)
        for c in view:
            assert [e.text for e in c.governing_prose] == list(clauses[c.component_key])
    # Key order would put the pouch before the rule that governs it, and
    # cantrips before the slots they are cast without.
    assert _printed("components")[0] == "components"
    assert _printed("components") != sorted(_printed("components"))
    printed = _printed("casting_spells")
    assert printed.index("casting_without_slots") < printed.index("cantrips")
    assert printed.index("spell_level") < printed.index("cantrips")


def test_narrowing_to_some_rules_keeps_their_printed_order(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    record = "spells.components"
    wanted = ("component_pouch_and_focus", "material", "components")
    view = _read(service, built, components=tuple((record, k) for k in wanted))
    assert [c.component_key for c in view] == [
        k for k in _printed("components") if k in wanted
    ]


def test_a_disabled_record_stays_gone(persisted, built, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    service = _service(persisted, built, monkeypatch, _disable("glossary.cone"))
    records = ("spells.targets", "glossary.area_of_effect", "glossary.cube")
    assert _sliced(service, _request(built, *records)) == sorted(records)
    view = _read(service, built, *records)
    assert "glossary.cone" not in {c.record_key for c in view}
    direct = service.rule_slice(_request(built, "glossary.cone"))
    assert direct.outcome is AuthorityOutcome.INVALID_REFERENCE


def test_a_replaced_component_reads_replaced_in_its_place(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(
        persisted,
        built,
        monkeypatch,
        _replaced("spells.components", "material", "A house material rule."),
    )
    view = _read(service, built, "spells.components")
    keys = [c.component_key for c in view]
    assert keys == _printed("components")
    replaced = view[keys.index("material")]
    assert keys.index("material") == 3
    (entry,) = replaced.governing_prose
    assert isinstance(entry, AuthoredProse) and entry.text == "A house material rule."
    (material,) = [
        ts for e, k, _, ts in GEN.CLAUSES if (e, k) == ("components", "material")
    ]
    assert not set(material) & {e.text for c in view for e in c.governing_prose}
    # The other rules are the source's, unchanged.
    assert all(
        isinstance(e, SourceProse)
        for c in view
        if c is not replaced
        for e in c.governing_prose
    )


def test_an_authored_rule_reads_after_the_source_s(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    # Authored text has no printed position; it is never read as if the
    # source printed it among its rules, even where its key sorts first.
    appended = EffectiveOverrideEntry(
        override_id="append-spells-components-house",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.RECORD, record_key="spells.components"
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
                "authored_prose": "A house component rule.",
            },
        },
    )
    service = _service(persisted, built, monkeypatch, appended)
    view = _read(service, built, "spells.components")
    assert [c.component_key for c in view] == [
        *_printed("components"),
        "aaa_house_rule",
    ]
    (entry,) = view[-1].governing_prose
    assert isinstance(entry, AuthoredProse) and entry.text == "A house component rule."


def test_a_session_is_the_published_release(  # type: ignore[no-untyped-def]
    session: Session, built, recorded: MechanicalProposal
) -> None:
    # The session is the current release; the recorded proposal keeps the
    # superseded one the Owner accepted it on.
    assert built.binding == current().oracle.binding
    assert (
        recorded.binding.package_uuid,
        recorded.binding.release_version,
    ) == REPLACEMENT.RELEASE
