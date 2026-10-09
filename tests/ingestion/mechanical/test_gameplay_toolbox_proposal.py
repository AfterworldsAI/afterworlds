"""The ``gameplay-toolbox`` proposal, offered for review -- CRD Issue 5d.

The *Gameplay Toolbox* part below its heading, pp192-203, proposed by
``.claude/review-notes/issue-5d-gameplay-toolbox-generator.py`` from the
release 5c actually publishes, with its one resolution draft. The Owner
accepted both over the superseded release (``issue-5d-gameplay-toolbox-ACCEPT.py``,
historical). On the Monsters-corrected release the regenerated proposal and
draft are batch nineteen of the replacement chain the Owner accepted, which
``issue-5d-monsters-corrections-ACCEPT.py`` recorded; the eighteen batches before
it are rebuilt here from that recording.

What is pinned, and why:

* the committed artifact is the superseded release's recorded proposal, by
  shape, and the drafts are what the generator drafts over the committed
  authority; the generator builds over the current release (that it no longer
  derives the recorded bytes is retired, see
  ``.claude/review-notes/issue-5c-release-readiness/correction-followup.md``);
* scope is the part's 285 leaves, in printed order, and no leaf or record is
  an accepted one's;
* grain: eight section records and their 25 catalogue members, with
  *Troubleshooting* its own review unit read into *Combat Encounters*, where
  the source sets it; every component prose-bound and reading its reviewed
  texts, every word of every spanned leaf claimed, and GM latitude exactly
  where the text delegates the ruling;
* references name exact accepted records or stay unresolved, the Net's
  "Adventuring Gear" citation among them;
* the recorded proposal, composed in memory over the recorded chain (both the
  superseded release's): it accepts, then the draft resolves, and every
  accepted byte is preserved. Judging that composition against a corpus needs
  the superseded release's, which is not rebuilt; that check is retired;
* the committed oracle keeps the chain through this batch whole, under the
  Owner's decision and recorded time, the Magic Items batch's reviewed
  obligation enlargement aside;
* through the production rules-authority service, over the current accepted
  authority persisted as one draft into the current release: a
  section reads in printed position and reaches its members once, a disabled
  member is gone from it, and a replaced member reads replaced; *Combat
  Encounters* reads its *Troubleshooting* after *Step 3*, and a component of
  it is selected alone or replaced in place.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

from afterworlds.ingestion.mechanical.acceptance import (
    accept_proposal,
    resolve_references,
)
from afterworlds.ingestion.mechanical.authoring import Built
from afterworlds.ingestion.mechanical.models import ComponentHandling, ReviewState
from afterworlds.ingestion.mechanical.oracle import (
    AcceptedInputs,
    OracleLoadError,
    accepted_inputs_payload,
    candidate_from_accepted_inputs,
    load_accepted_inputs,
    serialize_accepted_inputs,
)
from afterworlds.ingestion.mechanical.persistence import persist_draft
from afterworlds.ingestion.mechanical.projection import (
    ProjectionCandidate,
    identify_projection,
)
from afterworlds.ingestion.mechanical.proposal import (
    MechanicalProposal,
    load_proposal,
)
from afterworlds.ingestion.mechanical.reference_resolution import (
    reference_resolution_payload,
    reference_resolution_violations,
)
from afterworlds.ingestion.mechanical.representation import (
    RecordKind,
    RelationshipKind,
)
from afterworlds.ingestion.mechanical.validation import (
    relationship_and_reference_violations,
)
from afterworlds.models.enums import OverrideOperationEnum, OverrideOriginEnum
from afterworlds.persistence.database import create_engine, create_session_factory
from afterworlds.persistence.orm.corpus import LedgerLeafORM
from afterworlds.services.rules_authority.application import AuthoredProse
from afterworlds.services.rules_authority.outcomes import AuthorityOutcome
from afterworlds.services.rules_authority.override_set import EffectiveOverrideEntry
from afterworlds.services.rules_authority.targets import (
    MechanicalTarget,
    MechanicalTargetKind,
)
from tests.ingestion.mechanical._replacement_chain import (
    BATCHES,
    COMMITTED_SHA256,
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
ORACLES = REPO / "src/afterworlds/ingestion/mechanical/oracles"
ORACLE = REPLACEMENT.ACCEPTED_PATH
TOOLBOX = "srd-5.2.1/gameplay-toolbox"
BATCH = "gameplay-toolbox"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their own module
    spec.loader.exec_module(module)
    return module


GEN = _load(
    "gameplay_toolbox_generator", NOTES / "issue-5d-gameplay-toolbox-generator.py"
)
PROPOSAL = proposal_path(BATCH)
DRAFTS = REPLACEMENT.drafts_path(BATCH)
IDENTITY = identity(BATCH)
PROPOSAL_SHA256 = BATCHES[BATCH][1]
DRAFTS_SHA256 = REPLACEMENT.DRAFTS[BATCH][0]
#: The draft's id, as the regenerated draft names it.
RESOLUTION_ID = (
    "resolve-glossary-challenge-rating-record-combat-encounters-gameplay-toolbox-1"
)
SECTION_KEYS = [
    "gameplay_toolbox.travel_pace",
    "gameplay_toolbox.creating_a_background",
    "gameplay_toolbox.curses_and_magical_contagions",
    "gameplay_toolbox.environmental_effects",
    "gameplay_toolbox.fear_and_mental_stress",
    "gameplay_toolbox.poison",
    "gameplay_toolbox.traps",
    "gameplay_toolbox.combat_encounters",
]
ENCOUNTERS = "gameplay_toolbox.combat_encounters"
POISON = "gameplay_toolbox.poison"


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
    """The eighteen-batch chain this packet is composed over, as recorded."""
    inputs = through("spell-descriptions")
    assert [b.batch_id for b in inputs.batches] == list(BATCHES)[:18]
    return inputs


@pytest.fixture(scope="module")
def recorded() -> MechanicalProposal:
    """The committed proposal: the superseded release's, as the Owner accepted it."""
    return load_proposal(PROPOSAL, expected_identity=IDENTITY)


def _texts(b: Built, record: str, key: str) -> list[str]:
    """The source texts one component's prose bindings are read from."""
    spans = {s.span_id: s for s in b.ledger.spans}
    return [
        b.leaf_rows[spans[x.span_id].leaf_id].content[
            spans[x.span_id].char_start : spans[x.span_id].char_end
        ]
        for x in b.proposal.proposed_representation.prose_bindings
        if (x.record_key, x.component_key) == (record, key)
    ]


def _refs(b: Built) -> list[tuple[str, str, str, str, str]]:
    return [
        (
            r.from_record_key,
            r.from_component_key,
            r.source_text,
            r.scope_key,
            r.target_record_key,
        )
        for r in b.proposal.proposed_representation.references
    ]


# ---------------------------------------------------------------------------
# The artifacts
# ---------------------------------------------------------------------------


def test_the_committed_artifact_is_the_recorded_proposal_by_shape(built) -> None:  # type: ignore[no-untyped-def]
    data = PROPOSAL.read_bytes()
    assert hashlib.sha256(data).hexdigest() == PROPOSAL_SHA256
    assert b"\r" not in data
    proposal = load_proposal(PROPOSAL, expected_identity=IDENTITY)
    assert json.loads(data)["artifact_kind"] == "machine_proposal"
    assert {p.span.review_state for p in proposal.proposed_spans} == {
        ReviewState.PROPOSED
    }
    with pytest.raises(OracleLoadError):
        load_accepted_inputs(PROPOSAL)
    # The generator builds over the current release.
    assert built.binding == current().oracle.binding


def test_the_one_draft_names_the_section_the_glossary_cites(prior) -> None:  # type: ignore[no-untyped-def]
    data = DRAFTS.read_bytes()
    assert hashlib.sha256(data).hexdigest() == DRAFTS_SHA256 and b"\r" not in data
    drafts = GEN.draft_resolutions(prior.oracle.binding, prior=prior)
    assert json.loads(data) == reference_resolution_payload(drafts)
    assert [
        (
            d.from_record_key,
            d.from_component_key,
            d.source_text,
            d.scope_key,
            d.target_record_key,
        )
        for d in drafts
    ] == [
        (
            "glossary.challenge_rating",
            "",
            "Combat Encounters",
            TOOLBOX,
            "gameplay_toolbox.combat_encounters",
        )
    ]
    # The part pointers name no record: none is guessed.
    _, left = GEN.draft_targets(prior)
    assert sorted(left) == [
        ("equipment.adventuring_gear", "bedroll", "Gameplay Toolbox"),
        ("equipment.adventuring_gear", "blanket", "Gameplay Toolbox"),
        ("play.exploration", "travel_pace", "Gameplay Toolbox"),
    ]


# ---------------------------------------------------------------------------
# Scope and grain
# ---------------------------------------------------------------------------


def test_scope_is_the_part_s_285_leaves(session, built) -> None:  # type: ignore[no-untyped-def]
    rows = (
        session.query(LedgerLeafORM)
        .filter(LedgerLeafORM.package_uuid == built.binding.package_uuid)
        .order_by(LedgerLeafORM.occurrence_index)
        .all()
    )
    (head,) = [i for i, r in enumerate(rows) if r.content == "# Gameplay Toolbox"]
    part = rows[head + 1 : head + 1 + len(GEN.LEAVES)]
    assert [r.content for r in part] == [t for _, t in GEN.LEAVES]
    # The part runs to the next part heading.
    assert rows[head + 1 + len(GEN.LEAVES)].content.startswith("# ")
    mine = [leaf for u in built.proposal.proposed_review_units for leaf in u.leaf_ids]
    assert len(mine) == len(set(mine)) == 285
    assert set(mine) == {r.leaf_id for r in part}
    assert rows[head].leaf_id not in mine
    keys = [r.semantic_key for r in built.proposal.proposed_representation.records]
    assert len(keys) == len(set(keys))


def test_no_recorded_leaf_or_record_is_an_accepted_one(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    # Both sides are the superseded release's: the recorded chain and proposal.
    mine = [leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids]
    assert len(mine) == len(set(mine)) == 285
    owned = {leaf for u in prior.oracle.review_units for leaf in u.leaf_ids}
    assert not owned & set(mine)
    accepted = {r.semantic_key for r in prior.oracle.representation.records}
    keys = [r.semantic_key for r in recorded.proposed_representation.records]
    assert len(keys) == len(set(keys)) and not accepted & set(keys)


def test_the_records_are_eight_sections_and_their_catalogue_members(built) -> None:  # type: ignore[no-untyped-def]
    rep = built.proposal.proposed_representation
    assert {r.kind for r in rep.records} == {RecordKind.GAMEPLAY_TOOL}
    keys = [r.semantic_key for r in rep.records]
    assert [k for k in keys if k.count(".") == 1] == SECTION_KEYS
    assert len(keys) == 33 and not [k for k in keys if "troubleshooting" in k]
    # Troubleshooting is reviewed alone over its own container: 34 units.
    units = {u.unit_id: u for u in built.proposal.proposed_review_units}
    assert len(units) == 34
    ts = units["gameplay-toolbox/troubleshooting"]
    assert ts.kind.value == "section"
    assert [built.leaf_rows[x].content for x in ts.leaf_ids] == _printed(
        "Troubleshooting"
    )
    assert {r.record_key for r in ts.expected_rules} == {ENCOUNTERS}
    edges = [
        (r.kind, r.source_record_key, r.target_record_key) for r in rep.relationships
    ]
    assert {k for k, _, _ in edges} == {RelationshipKind.CATALOGUE_MEMBER}
    assert Counter(t for _, _, t in edges) == {
        "gameplay_toolbox.curses_and_magical_contagions": 3,
        POISON: 14,
        "gameplay_toolbox.traps": 8,
    }
    # Each member is its section's, in printed order.
    for section, members in GEN.MEMBERS.items():
        assert [s for _, s, t in edges if t == GEN.section_key(section)] == [
            GEN.member_key(m) for m in members
        ]
    # A printed price is not part of a member's identity.
    assert f"{POISON}.assassins_blood" in keys
    # Read into Combat Encounters without an edge: none touches it.
    assert not [e for e in edges if ENCOUNTERS in e[1:]]


def test_each_section_reads_its_subheadings_in_printed_order(built) -> None:  # type: ignore[no-untyped-def]
    components = built.proposal.proposed_representation.components
    by = {
        k: [c.semantic_key for c in components if c.record_key == k]
        for k in SECTION_KEYS
    }
    assert by["gameplay_toolbox.travel_pace"] == [
        "travel_pace",
        "good_roads",
        "slower_travelers",
        "extended_travel",
        "special_movement",
        "vehicles",
        "travel_terrain",
    ]
    assert by["gameplay_toolbox.creating_a_background"][1] == "step_1_choose_abilities"
    # Troubleshooting follows Step 3, as the PDF sets it (pp202-203).
    assert by[ENCOUNTERS] == [
        "combat_encounters",
        "combat_encounter_difficulty",
        "step_1_choose_a_difficulty",
        "step_2_determine_your_xp_budget",
        "step_3_spend_your_budget",
        "troubleshooting",
        "many_creatures",
        "adjustments",
        "cr_0_creatures",
        "number_of_stat_blocks",
        "powerful_creatures",
        "unusual_features",
    ]
    # The Travel Terrain table the Vehicles container prints is its own.
    (table,) = _texts(built, "gameplay_toolbox.travel_pace", "travel_terrain")
    assert table.startswith("**Travel Terrain**") and "Maximum Pace" in table
    vehicles = GEN.texts_at(("Gameplay Toolbox", "Travel Pace", "Vehicles"))
    assert _texts(built, "gameplay_toolbox.travel_pace", "vehicles") == vehicles[:-1]
    assert vehicles[-1] == table


# ---------------------------------------------------------------------------
# Fidelity
# ---------------------------------------------------------------------------


def _residue(b: Built) -> dict[str, str]:
    """Text of a spanned leaf no span covers."""
    out = {}
    for lid in {s.leaf_id for s in b.ledger.spans}:
        text = list(b.leaf_rows[lid].content)
        for s in b.ledger.spans:
            if s.leaf_id == lid:
                text[s.char_start : s.char_end] = " " * (s.char_end - s.char_start)
        if left := "".join(text).strip():
            out[lid] = left
    return out


def test_every_component_reads_its_reviewed_texts_as_prose(built) -> None:  # type: ignore[no-untyped-def]
    chunk = GEN.TOOLBOX_CHUNK
    components = built.proposal.proposed_representation.components
    assert {c.handling for c in components} == {ComponentHandling.PROSE_BOUND}
    assert not [c for c in components if c.all_facts()]
    clauses = {(e, k): texts for e, k, _, texts in chunk.clauses}
    for c in chunk.components:
        record = chunk.placements[c.entry].record_key
        assert _texts(built, record, c.key) == list(clauses[(c.entry, c.key)])
    assert _residue(built) == {}
    assert not [
        g for u in built.proposal.proposed_review_units for g in u.excluded_groups
    ]
    # Each placed entry's first clause reads its own heading.
    for entry, placement in chunk.placements.items():
        first = next(texts for e, _, _, texts in chunk.clauses if e == entry)
        assert first[0] == placement.heading
    # A section's components never bind a member's leaves.
    member_texts = {
        t for ms in GEN.MEMBERS.values() for m in ms for t in GEN.texts_at(m)
    }
    for k in SECTION_KEYS:
        for c in [c for c in components if c.record_key == k]:
            assert not member_texts & set(_texts(built, k, c.semantic_key))


#: (record, component) -> the words by which the source leaves the ruling to
#: whoever runs the game.
CURSES = "gameplay_toolbox.curses_and_magical_contagions"
FEAR = "gameplay_toolbox.fear_and_mental_stress"
LATITUDE = {
    (CURSES, "cursed_creatures"): "You decide how a spell like _Remove Curse_",
    (CURSES, "narrative_curses"): "is up to you",
    (FEAR, "fear_and_mental_stress"): "If you plan to use any of these rules",
    (FEAR, "fear_effects"): "At your discretion",
    (FEAR, "mental_stress_effects"): "at your discretion",
    (POISON, "poison"): "You may decide that a partial dose",
    (ENCOUNTERS, "adjustments"): "You can adjust an encounter on the fly",
}


def test_latitude_is_exactly_where_the_text_delegates_the_ruling(built) -> None:  # type: ignore[no-untyped-def]
    rep = built.proposal.proposed_representation
    got = {}
    for c in rep.components:
        # Exactly one reason: latitude is irreducible, the rest retained.
        assert (c.irreducibility_reason_code is None) != (
            c.prose_retention_reason_code is None
        )
        assert c.irreducibility_reason_code in (None, GEN.GM)
        assert c.prose_retention_reason_code in (None, GEN.NO_USE)
        if c.irreducibility_reason_code == GEN.GM:
            got[(c.record_key, c.semantic_key)] = " ".join(
                _texts(built, c.record_key, c.semantic_key)
            )
    assert set(got) == set(LATITUDE)
    assert all(words in got[k] for k, words in LATITUDE.items())
    # Each prose binding carries its component's reason.
    reasons = {
        (c.record_key, c.semantic_key): (
            c.irreducibility_reason_code,
            c.prose_retention_reason_code,
        )
        for c in rep.components
    }
    for b in rep.prose_bindings:
        assert reasons[(b.record_key, b.component_key)] == (
            b.irreducibility_reason_code,
            b.prose_retention_reason_code,
        )
    # Second person alone is not delegation: a trap's scaling table, the
    # encounter-budget procedure and the background steps stay reducible.
    for k in [
        ("gameplay_toolbox.traps.hidden_pit", "hidden_pit"),
        (ENCOUNTERS, "step_3_spend_your_budget"),
        (ENCOUNTERS, "cr_0_creatures"),
        ("gameplay_toolbox.creating_a_background", "creating_a_background"),
    ]:
        assert k not in got and "you" in " ".join(_texts(built, *k)).lower(), k


def test_references_name_exact_records_or_stay_unresolved(built) -> None:  # type: ignore[no-untyped-def]
    refs = _refs(built)
    eq = "srd-5.2.1/equipment"
    traps = "gameplay_toolbox.traps"
    for ref in (
        ("gameplay_toolbox.curses_and_magical_contagions", "bestow_curse",
         "Bestow Curse", "srd-5.2.1/spells", "spells.bestow_curse"),
        (f"{traps}.falling_net", "falling_net", "Adventuring Gear", eq, ""),
        (f"{traps}.falling_net", "falling_net", "Thieves' Tools", eq,
         "equipment.tools.thieves_tools"),
        (f"{traps}.falling_net", "falling_net", "Net", eq, ""),
        (f"{traps}.hidden_pit", "hidden_pit", "Iron Spike", eq, ""),
        (POISON, "harvesting_poison", "Poisoner's Kit", eq, ""),
        ("gameplay_toolbox.curses_and_magical_contagions.sight_rot", "sight_rot",
         "Herbalism Kit", eq, "equipment.tools.herbalism_kit"),
        ("gameplay_toolbox.environmental_effects", "high_altitude", "Travel Pace",
         TOOLBOX, "gameplay_toolbox.travel_pace"),
        ("gameplay_toolbox.travel_pace", "special_movement", "Carpet of Flying",
         "srd-5.2.1/magic-items", ""),
        ("gameplay_toolbox.creating_a_background", "step_2_choose_a_feat",
         "Origin Feats", "srd-5.2.1/feats", ""),
        (ENCOUNTERS, "powerful_creatures", "Ogre",
         "srd-5.2.1/monsters", ""),
        ("gameplay_toolbox.combat_encounters", "step_3_spend_your_budget",
         "Bugbear Warrior", "srd-5.2.1/monsters", ""),
        (f"{traps}.rolling_stone", "rolling_stone", "Damage Threshold",
         "srd-5.2.1/rules-glossary", "glossary.damage_threshold"),
    ):  # fmt: skip
        assert ref in refs, ref
    # The Net's statistics hold no record: no section is guessed for them.
    assert not [r for r in refs if r[4] == "equipment.adventuring_gear"]
    # A pointer inside its own record is not a reference; none points at itself.
    assert not {"Vehicles", "Frigid Water"} & {r[2] for r in refs}
    assert not [r for r in refs if r[0] == r[4]]
    # Monster, magic-item, feat and part targets are never guessed.
    assert {
        r[4]
        for r in refs
        if r[3] in ("srd-5.2.1/monsters", "srd-5.2.1/magic-items", "srd-5.2.1/feats")
    } == {""}
    creatures = {r[2] for r in refs if r[3] == "srd-5.2.1/monsters"}
    assert creatures == GEN.CREATURE_NAMES


#: The packet's own unresolved pointers, by scope.
UNRESOLVED_SCOPES = {
    "srd-5.2.1/equipment": 9,
    "srd-5.2.1/feats": 1,
    "srd-5.2.1/magic-items": 2,
    "srd-5.2.1/monsters": 11,
    "srd-5.2.1/playing-the-game": 1,
}


def test_the_batch_checks_report_only_the_out_of_batch_targets(built) -> None:  # type: ignore[no-untyped-def]
    found = GEN.batch_findings(built)
    assert found["partition"] == [] and found["review_units"] == []
    assert found["representation"] == GEN.expected_representation_findings(
        GEN.TOOLBOX_CHUNK
    )
    assert (
        Counter(
            f.split(":")[0].split(" ")[1]
            for f in found["representation"]
            if "unresolved reference" in f
        )
        == UNRESOLVED_SCOPES
    )


# ---------------------------------------------------------------------------
# Test-only composition with the committed oracle
# ---------------------------------------------------------------------------


def _accepted(prior: AcceptedInputs, proposal: MechanicalProposal) -> AcceptedInputs:
    return accept_proposal(
        proposal,
        batch_id="gameplay-toolbox",
        rule="test-only",
        resolved_scope=tuple(p.span.span_id for p in proposal.proposed_spans),
        resolved_review_units=tuple(u.unit_id for u in proposal.proposed_review_units),
        reviewer="test",
        accepted_at="2026-09-27T00:00:00Z",
        prior=prior,
    )


def _covered(inputs: AcceptedInputs) -> set[str]:
    oracle = inputs.oracle
    return {s.leaf_id for s in oracle.spans} | {
        leaf for u in oracle.review_units for leaf in u.leaf_ids
    }


def _references(inputs: AcceptedInputs) -> list[str]:
    # The effective representation's own relationship and reference findings
    # (resolutions applied): no corpus, so none of the superseded release's is
    # needed.
    return relationship_and_reference_violations(
        candidate_from_accepted_inputs(lifted(inputs)).representation
    )


#: Reference findings left after accepting and resolving, all unresolved: the
#: committed 143, less the one drafted, plus the packet's own.
REMAINING = 143 - 1 + sum(UNRESOLVED_SCOPES.values())


def test_accepted_then_resolved_in_memory_preserves_everything(recorded, prior) -> None:  # type: ignore[no-untyped-def]
    on_disk = {p.name: p.read_bytes() for p in ORACLES.iterdir()}
    base = prior.oracle
    # Both sides are the superseded release's: the recorded chain and proposal.
    assert recorded.binding == base.binding
    assert (
        len(prior.batches),
        len(base.representation.records),
        len(base.spans),
        len(base.review_units),
        len(base.reference_resolutions),
    ) == (18, 947, 4826, 645, 1097)
    refs_before = _references(prior)
    assert len(refs_before) == 143
    accepted = _accepted(prior, recorded)
    drafts = GEN.draft_resolutions(base.binding, prior=prior)
    resolved = resolve_references(
        accepted,
        resolutions=drafts,
        authorized_by="test",
        authorization_reference="test-only",
        reviewer="test",
        resolved_at="2026-09-27T00:00:01Z",
    )
    final = resolved.oracle
    # Append-only: every accepted byte the authority holds is still held.
    assert not REPLACEMENT._preserved(
        accepted_inputs_payload(prior), accepted_inputs_payload(resolved)
    )
    assert resolved.batches[: len(prior.batches)] == prior.batches
    assert (
        len(final.representation.records),
        len(final.spans),
        len(final.review_units),
        len(final.reference_resolutions),
    ) == (947 + 33, 4826 + 285, 645 + 34, 1097 + 1)
    assert (
        reference_resolution_violations(
            final.representation, final.reference_resolutions, final.binding
        )
        == []
    )
    # Exactly the part's leaves gain coverage.
    mine = {leaf for u in recorded.proposed_review_units for leaf in u.leaf_ids}
    assert _covered(resolved) - _covered(prior) == mine
    assert len(mine) == 285
    # Every accepted target closes; only unresolved pointers remain: the
    # committed ones less the drafted, plus the packet's own.
    rest = _references(resolved)
    assert all(f.startswith("reference ") and "unresolved" in f for f in rest)
    packet = [
        f
        for f in GEN.expected_representation_findings(GEN.TOOLBOX_CHUNK)
        if "unresolved" in f
    ]
    drafted = f"reference {TOOLBOX}:'Combat Encounters': unresolved reference"
    assert drafted in refs_before
    assert sorted(rest) == sorted([*(f for f in refs_before if f != drafted), *packet])
    assert len(rest) == REMAINING == 166
    # The committed directory is untouched.
    assert {p.name: p.read_bytes() for p in ORACLES.iterdir()} == on_disk


def test_the_committed_oracle_records_the_owner_acceptance(prior) -> None:  # type: ignore[no-untyped-def]
    # The recorded chain through this batch is the Owner's steps over the
    # eighteen batches before it, which it keeps whole.
    recorded = through(BATCH)
    assert not REPLACEMENT._preserved(
        accepted_inputs_payload(prior), accepted_inputs_payload(recorded)
    )
    # The Animals recording keeps it whole, times and all, but for the Magic
    # Items batch's reviewed obligation enlargement of the two shared Equipment
    # records; the committed oracle keeps that outside the replaced Equipment
    # batch.
    # The superseded release's committed file, read by path: the production
    # resolver refuses its binding.
    committed = load_accepted_inputs(ORACLE)
    data = ORACLE.read_bytes()
    assert serialize_accepted_inputs(committed) == data
    assert hashlib.sha256(data).hexdigest() == COMMITTED_SHA256
    assert {b.batch_id for b in committed.batches} == {
        b.batch_id for b in recorded.batches
    } | {
        "magic-items",
        "monsters",
        "animals",
        "framing-coverage",
        "character-creation-catalogue",
    }
    assert not kept_whole(recorded, animals_recorded())
    (batch,) = [b for b in recorded.batches if b.batch_id == BATCH]
    assert (batch.proposal_identity, batch.rule) == (IDENTITY, REPLACEMENT.APPROVAL)
    mine = [a for a in recorded.acceptances if a.batch_id == BATCH]
    assert len(mine) == len(recorded.acceptances) - len(prior.acceptances)
    assert {(a.reviewer, a.accepted_at) for a in mine} == {
        (REPLACEMENT.OWNER, REPLACEMENT.ACCEPTED_AT)
    }
    new = [
        a
        for a in recorded.reference_resolution_acceptances
        if a.resolution_id.endswith("-gameplay-toolbox-1")
    ]
    assert [
        (a.resolution_id, a.authorized_by, a.reviewer, a.resolved_at) for a in new
    ] == [
        (
            RESOLUTION_ID,
            REPLACEMENT.OWNER,
            REPLACEMENT.OWNER,
            REPLACEMENT.ACCEPTED_AT,
        )
    ]
    assert new[0].authorization_reference == REPLACEMENT.AUTHORIZATION_REFERENCE
    assert REPLACEMENT.OWNER_REVIEW_SHA256 in REPLACEMENT.AUTHORIZATION_REFERENCE
    # The one resolution is the reviewed draft, byte for byte.
    (resolution,) = [
        r
        for r in recorded.oracle.reference_resolutions
        if r.resolution_id == RESOLUTION_ID
    ]
    assert list(reference_resolution_payload((resolution,))) == json.loads(
        DRAFTS.read_bytes()
    )


# ---------------------------------------------------------------------------
# Through the production rules-authority service
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def persisted(tmp_path_factory, source_release_db):  # type: ignore[no-untyped-def]
    """The current accepted authority, persisted as one draft into a private
    copy of the current release."""
    candidate = candidate_from_accepted_inputs(current())
    assert isinstance(candidate, ProjectionCandidate)
    path = tmp_path_factory.mktemp("toolbox") / "release.db"
    shutil.copyfile(source_release_db, path)
    engine = create_engine(f"sqlite:///{path}")
    with create_session_factory(engine)() as s:
        identified = identify_projection(candidate)
        persist_draft(s, identified, now="2026-09-27T00:00:00Z")
        s.commit()
        yield s, identified.projection_uuid
    engine.dispose()


def _view(service, built, *records: str) -> list[tuple[str, str, object]]:  # type: ignore[no-untyped-def]
    view = service.gamemaster_view(_request(built, *records))
    assert view.outcome is AuthorityOutcome.RESOLVED, view.detail
    return [
        (c.record_key, c.component_key, e)
        for c in view.gamemaster_view.components
        for e in c.governing_prose
    ]


def _printed(section: str) -> list[str]:
    return [t for p, t in GEN.LEAVES if p[:2] == ("Gameplay Toolbox", section)]


def test_a_section_reads_in_printed_position_and_reaches_its_members_once(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    members = [f"{POISON}.{GEN.key_of(m[-1])}" for m in GEN.MEMBERS["Poison"]]
    assert _sliced(service, _request(built, POISON)) == [POISON, *members]
    read = _view(service, built, POISON)
    assert [e.text for _, _, e in read] == _printed("Poison")  # type: ignore[attr-defined]
    # Selecting the section and a member returns the member once.
    both = _sliced(service, _request(built, POISON, members[0]))
    assert both.count(members[0]) == 1 and len(both) == 15
    # A section without members reads its whole subtree in printed order.
    travel = _view(service, built, "gameplay_toolbox.travel_pace")
    assert [e.text for _, _, e in travel] == _printed("Travel Pace")  # type: ignore[attr-defined]


def test_a_disabled_member_is_gone_from_its_section(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    gone = f"{POISON}.malice"
    service = _service(persisted, built, monkeypatch, _disable(gone))
    reached = _sliced(service, _request(built, POISON))
    assert gone not in reached and len(reached) == 14
    assert gone not in {r for r, _, _ in _view(service, built, POISON)}
    refused = service.rule_slice(_request(built, gone))
    assert refused.outcome is AuthorityOutcome.INVALID_REFERENCE


def test_a_replaced_member_reads_replaced_in_its_section(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    member = f"{POISON}.torpor"
    printed = _view(_service(persisted, built, monkeypatch), built, POISON)
    house = EffectiveOverrideEntry(
        override_id="replace-torpor",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=member,
            component_key="torpor",
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
                "authored_prose": "A house Torpor.",
            },
        },
    )
    after = _view(_service(persisted, built, monkeypatch, house), built, POISON)
    assert [x for x in after if x[0] != member] == [
        x for x in printed if x[0] != member
    ]
    (replaced,) = [e for r, _, e in after if r == member]
    assert isinstance(replaced, AuthoredProse) and replaced.text == "A house Torpor."
    # It keeps its printed position among the members.
    records = list(dict.fromkeys(r for r, _, _ in after))
    assert records == list(dict.fromkeys(r for r, _, _ in printed))


def test_combat_encounters_reads_its_troubleshooting_after_step_3(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    service = _service(persisted, built, monkeypatch)
    assert _sliced(service, _request(built, ENCOUNTERS)) == [ENCOUNTERS]
    read = _view(service, built, ENCOUNTERS)
    assert [e.text for _, _, e in read] == [  # type: ignore[attr-defined]
        *_printed("Combat Encounters"),
        *_printed("Troubleshooting"),
    ]
    # Each Troubleshooting component is selected alone, and selecting it with
    # its record reads it once.
    adjustments = GEN.texts_at(("Gameplay Toolbox", "Troubleshooting", "Adjustments"))
    alone = service.gamemaster_view(
        _request(built, components=((ENCOUNTERS, "adjustments"),))
    )
    assert alone.outcome is AuthorityOutcome.RESOLVED, alone.detail
    assert [
        e.text for c in alone.gamemaster_view.components for e in c.governing_prose  # type: ignore[attr-defined]
    ] == adjustments
    both = service.gamemaster_view(
        _request(built, ENCOUNTERS, components=((ENCOUNTERS, "adjustments"),))
    )
    assert [
        (c.record_key, c.component_key) for c in both.gamemaster_view.components
    ] == list(dict.fromkeys((r, k) for r, k, _ in read))


def test_a_replaced_troubleshooting_component_reads_replaced_in_place(  # type: ignore[no-untyped-def]
    persisted, built, monkeypatch
) -> None:
    printed = _view(_service(persisted, built, monkeypatch), built, ENCOUNTERS)
    house = EffectiveOverrideEntry(
        override_id="replace-adjustments",
        origin=OverrideOriginEnum.HOUSE_RULE,
        target=MechanicalTarget(
            kind=MechanicalTargetKind.COMPONENT,
            record_key=ENCOUNTERS,
            component_key="adjustments",
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
                "authored_prose": "House adjustments.",
            },
        },
    )
    after = _view(_service(persisted, built, monkeypatch, house), built, ENCOUNTERS)
    assert [x for x in after if x[1] != "adjustments"] == [
        x for x in printed if x[1] != "adjustments"
    ]
    (replaced,) = [e for _, k, e in after if k == "adjustments"]
    assert isinstance(replaced, AuthoredProse) and replaced.text == "House adjustments."
    keys = list(dict.fromkeys(k for _, k, _ in after))
    assert keys == list(dict.fromkeys(k for _, k, _ in printed))
    assert keys.index("adjustments") == keys.index("step_3_spend_your_budget") + 3
