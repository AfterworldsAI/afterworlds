"""Author the **proficiency-destinations-1** proposal: the four destinations the
accepted Proficiency section cites.

REVIEW MATERIAL. Emits an *unaccepted* ``5d-proposal-2`` artifact next to this
file. It accepts nothing, publishes nothing, and writes nothing under
``oracles/``.

**Why these four and no others.** ``proficiency-1`` (merged PR #171) committed
four references. Two name Rules Glossary entries no accepted batch had minted
(``glossary.challenge_rating``, ``glossary.expertise``); two carry an empty
``target_record_key`` because their destinations inside *Playing the Game* -- the
Skills table and the ``Actions`` section -- had not been reviewed. This batch
reviews all four destinations from source and completes the links.

**Four review units, one batch.** ``accept_proposal`` checks the accumulated
review inventory against the *merged* representation and requires the batch's
resolved scope to be disjoint from what is already accepted; it runs no
reference validation, so reference resolution is a property of the merged
representation proved separately (``_merged_resolution`` below, and the
proportionate tests). The two glossary entries are ``ENTRY`` units because that
is how the Rules Glossary presents them; the Skills table is a ``TABLE`` unit so
that an omitted row is a missing expected rule; the ``Actions`` section is a
``SECTION`` unit including its three subsections, its exceptions and its
qualifications.

**The Skills table lives inside the Actions container.** 5c files it under
``['Playing the Game', 'Actions', 'Skill | Ability | Example Uses']``, so the
two *Playing the Game* units partition one 5c container: 38 leaves for the
section, 58 for the table, 96 of the container's 97 represented leaves, the
97th being the running footer 5c itself excludes. Reported, not repaired -- no
5c change is in scope, and the source really does print the Skills table in the
middle of the Actions section. Keeping them as two records is what the citing
prose requires: *"the Skills table"* and *"'Actions' later in 'Playing the
Game'"* are two destinations, and one record for both would resolve two
distinct pointers to the same place.

**No schema change, and nothing minted.** Schema 15 is preserved exactly.
``ExpectedRule(fact_family=None)`` is the first-class home for a rule carried as
exact governing prose, and ``no_identified_structured_use`` is the closed
retention reason for meaning that is reducible but has no identified code-owned
use. The brief gates new typed fields on identified uses under governing
authority, and sheet/adapter execution is out of scope, so no fact family is
minted here: Expertise's doubling factor, the Skills table's per-row pairing
(already carried by ``Skill``, ``AbilityScore`` and ``SKILL_ABILITY`` as
accepted schema content, cross-checked below) and the Action table's summaries
all stay prose. The only typed facts are two ``ActionAllowanceFact`` instances
that the existing family states exactly, in the shape ``glossary.action``
already uses it.

**When a pointer becomes a reference.** A reference is minted only where the
destination record exists in accepted data or in this batch's own chain:

* the 12 Action-table name cells -> the 12 accepted ``action.*`` records, in the
  glossary scope 284 names in its own words (*"defined in more detail in 'Rules
  Glossary'"*); identical ``(scope, source_text, target)`` triples to the ones
  ``glossary.action`` already publishes, so they resolve uniquely rather than
  ambiguously, and a different ``from_record_key`` keeps them out of the
  duplicated-citation rule;
* Expertise's *"See also 'Playing the Game' ('Proficiency')"* -> the
  ``play.proficiency`` record ``proficiency-1`` proposes, as a record-owned
  reference because the entry states it and no one of its rule components does.

Every other pointer stays exact governing prose: ``"Stat Block."``, *"Gameplay
Toolbox" ("Combat Encounters")*, *"Combat"*, ``Opportunity Attack`` and
``Cunning Action`` all name destinations no accepted or in-flight batch has
minted. That is ``proficiency-1``'s own precedent -- it left *"(described in
'Character Creation')"* as prose rather than minting an unresolvable pointer --
and it means this batch opens no new outstanding obligation while closing four.
Illustrative mentions of named actions inside prose (``Influence``, ``Search``,
``Help``, ``Utilize`` in *One Thing at a Time*) are likewise not definitional
pointers, exactly as ``proficiency-1`` minted nothing for ``D20 Test``,
``Advantage`` or ``Athletics``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[1]
assert OUT.name == "review-notes" and OUT.parent.name == ".claude", OUT
sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.corpus.pipeline import build_candidate  # noqa: E402
from afterworlds.ingestion.corpus.policy import exclusion_reason_for  # noqa: E402
from afterworlds.ingestion.corpus.reconcile import _full_coverage_edges  # noqa: E402
from afterworlds.ingestion.mechanical.accounting import (  # noqa: E402
    derive_span_id,
    validate_partition,
    validate_reason_codes,
)
from afterworlds.ingestion.mechanical.bound_corpus import (  # noqa: E402
    BoundCorpusSnapshot,
    ChunkCoverage,
)
from afterworlds.ingestion.mechanical.models import (  # noqa: E402
    ClassificationLedger,
    ExcludedGroup,
    ExpectedRule,
    ReviewState,
    ReviewUnit,
    ReviewUnitKind,
    SemanticDisposition,
    SemanticSpan,
    SupportingGroup,
)
from afterworlds.ingestion.mechanical.oracle import load_accepted_inputs  # noqa: E402
from afterworlds.ingestion.mechanical.policy import (  # noqa: E402
    SEMANTIC_POLICY_VERSION,
    semantic_policy_hash,
)
from afterworlds.ingestion.mechanical.projection import (  # noqa: E402
    ReleaseBinding,
    review_unit_violations,
)
from afterworlds.ingestion.mechanical.proposal import (  # noqa: E402
    PROPOSAL_SCHEMA_VERSION_2,
    MechanicalProposal,
    ProposedSpan,
    proposal_identity,
    proposal_payload,
)
from afterworlds.ingestion.mechanical.representation import (  # noqa: E402
    RECORD_OWNED_REFERENCE,
    REPRESENTATION_SCHEMA_VERSION,
    SKILL_ABILITY,
    AbilityScore,
    ActionAllowanceFact,
    ActionCost,
    AllowanceScope,
    ComponentDraft,
    ComponentHandling,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RepresentationDraft,
    Skill,
    fact_target_key,
    prose_binding_target_key,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402

BATCH_ID = "proficiency-destinations-1"
ORIGIN = "issue-5d-batch-proficiency-destinations-1-generator.py"
PROPOSAL_FILE = "issue-5d-batch-proficiency-destinations-1-PROPOSAL.json"
SOURCE_PDF = REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"
ARTIFACT = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json"
)

CR = "glossary.challenge_rating"
EXP = "glossary.expertise"
SKILLS = "play.skills"
ACTIONS = "play.actions"
#: The record ``proficiency-1`` proposes. Named here only as a reference target;
#: this batch declares no component of it and re-accepts nothing of it.
PROFICIENCY = "play.proficiency"

#: The two committed resolution scopes ``proficiency-1`` used, unchanged.
GLOSSARY_SCOPE = "srd-5.2.1/rules-glossary"
PLAYING_THE_GAME_SCOPE = "srd-5.2.1/playing-the-game"

# ---------------------------------------------------------------------------
# The reviewed source
# ---------------------------------------------------------------------------
# Playing the Game > Actions, reading order 283-379 (the Skills table occupies
# 292-348 inside it, and 349 is the running footer 5c excludes).
HEAD_ACTIONS = "abee3b23-cb97-5a09-9270-cdd4bd69c4ae"
INTRO = "a417357c-5868-5c8e-a5fe-2694d0e208d3"
CAPTION_SKILLS = "707fa349-3d5c-54b0-bcc5-4fb284f353e4"
IMPROVISED = "c05db2e7-6378-5a61-b32c-bc2f5ce7232b"
HEAD_ONE_THING = "c3d0f853-4b97-5ce8-bdd4-847f6c630331"
ONE_THING = "7de88c77-ebcd-5d6e-a67e-b2a5ae191390"
HEAD_BONUS = "41963047-b661-58f4-a5ea-a75ac114e4b8"
BONUS_A = "b837da82-c466-5a90-aae1-983828335347"
BONUS_B = "2b508d04-01b6-5978-beec-ec3dc03c46db"
HEAD_REACTIONS = "16344390-d779-57cb-bcdd-a39878c7feaf"
REACTIONS = "680dedb4-66df-573a-aece-22c645ff85f3"
RUNNING_FOOTER = "fb25f796-eb4d-5eee-9da3-0b6043f3db4a"
ACTION_TABLE = "507658ab-020f-5085-b0fd-55a8c1234cb6"
SKILLS_TABLE = "d818241d-7639-55ee-9b9e-840139baae77"

# Rules Glossary > Challenge Rating, reading order 13015-13021, printed page 178.
HEAD_CR = "571a52eb-f575-5936-ae92-afd073130e4c"
CR_A = "5468f170-63be-55a4-a5d3-a7beeb13eb92"
CR_B = "b28983f8-4762-525f-9912-e47ca2c74a8e"
CR_C = "abdc1b9d-7895-52c2-ac09-a97541667b9e"
CR_D = "b6e98c19-4f03-58bc-a006-9e05857999af"
CR_SEE_ALSO = "6111b141-5229-5c07-a3af-16d421f7e058"
CR_STAT_BLOCK = "a5c8fb2b-9278-55d9-9028-836a14783e7b"

# Rules Glossary > Expertise, reading order 13223-13226, printed page 182.
HEAD_EXPERTISE = "b77603de-fb7c-5b28-9b79-fa4e9a5d9c4f"
EXPERTISE = "f17fb7e0-57fc-567e-8f96-3a8bac917a94"
EXP_SEE_ALSO = "8f6717a9-e8d7-57df-885d-1ad018fb1473"
EXP_POINTER = "f3d54e2e-5c6b-59e4-8f00-020548a1f33a"

HEADINGS = (HEAD_ACTIONS, HEAD_ONE_THING, HEAD_BONUS, HEAD_REACTIONS)

# ---------------------------------------------------------------------------
# The bound release, through 5c's own pipeline
# ---------------------------------------------------------------------------
CAND = build_candidate(SOURCE_PDF, retrieval_config=RetrievalMemoryConfig())
LABELS = {c.container_id: c.label for c in CAND.ledger.containers}
LEAF_BY_ID = {leaf.leaf_id: leaf for leaf in CAND.ledger.leaves}
REPRESENTED = {
    leaf.leaf_id
    for leaf in CAND.ledger.leaves
    if exclusion_reason_for(leaf, LABELS) is None
}
assert RUNNING_FOOTER not in REPRESENTED

EDGES = _full_coverage_edges(CAND.members.chunks, LEAF_BY_ID)

PRIOR = load_accepted_inputs(ARTIFACT)
BINDING: ReleaseBinding = PRIOR.oracle.binding
assert BINDING.package_uuid == CAND.package_uuid, BINDING.package_uuid
assert BINDING.release_version == CAND.release_version, BINDING.release_version
assert BINDING.authoritative_source_hash == CAND.authoritative_source_hash
assert BINDING.transform_config_hash == CAND.transform_config_hash
assert BINDING.bundle_root_hash == CAND.bundle.bundle_root_hash

CORPUS = BoundCorpusSnapshot(
    package_uuid=CAND.package_uuid,
    release_version=CAND.release_version,
    leaf_lengths={lid: len(LEAF_BY_ID[lid].content) for lid in REPRESENTED},
    chunk_coverage=tuple(
        ChunkCoverage(
            chunk_id=e.chunk_id,
            leaf_id=e.leaf_id,
            cover_start=e.cover_start,
            cover_end=e.cover_end,
            role=e.role,
            projection_id=e.projection_id,
        )
        for e in EDGES
    ),
)
CHUNKS_BY_LEAF: dict[str, list[str]] = {}
for _e in EDGES:
    CHUNKS_BY_LEAF.setdefault(_e.leaf_id, []).append(_e.chunk_id)

# ---------------------------------------------------------------------------
# The two tables, read out of the ledger by position
# ---------------------------------------------------------------------------
# Cells are not written down as leaf ids: they are read from the bound release
# by ``(table_id, segment, row, column)`` and their shape is asserted. That is a
# stronger claim than a list of ids -- it proves the table really is 13 rows by
# 2 columns and 19 rows by 3 columns -- and the release binding asserted above
# is what makes the read reproducible.
def _cells(table_id: str) -> dict[tuple[int, int], str]:
    """Every cell of one table, keyed by ``(printed row, column)``."""
    cells: dict[tuple[int, int], str] = {}
    for leaf in CAND.ledger.leaves:
        if leaf.table_id != table_id:
            continue
        assert leaf.leaf_id in REPRESENTED, leaf.leaf_id
        # A table split across a page break repeats its header row as segment 1
        # row 0. Row numbers are per segment, so the header appears twice and
        # the data rows do not collide.
        key = (-1 - leaf.table_segment, leaf.table_col) if leaf.table_row == 0 else (
            leaf.table_row,
            leaf.table_col,
        )
        assert key not in cells, (table_id, key)
        cells[key] = leaf.leaf_id
    return cells


ACTION_CELLS = _cells(ACTION_TABLE)
SKILL_CELLS = _cells(SKILLS_TABLE)
#: Two header rows (one per page segment) and twelve data rows of two columns.
ACTION_HEADER = tuple(ACTION_CELLS[(seg, col)] for seg in (-1, -2) for col in (0, 1))
ACTION_ROWS = tuple(
    (ACTION_CELLS[(row, 0)], ACTION_CELLS[(row, 1)]) for row in range(1, 13)
)
assert len(ACTION_CELLS) == 28, len(ACTION_CELLS)
assert len(ACTION_HEADER) == 4 and len(ACTION_ROWS) == 12
#: One header row and eighteen data rows of three columns.
SKILL_HEADER = tuple(SKILL_CELLS[(-1, col)] for col in range(3))
SKILL_ROWS = tuple(
    (SKILL_CELLS[(row, 0)], SKILL_CELLS[(row, 1)], SKILL_CELLS[(row, 2)])
    for row in range(1, 19)
)
assert len(SKILL_CELLS) == 57, len(SKILL_CELLS)
assert len(SKILL_HEADER) == 3 and len(SKILL_ROWS) == 18


def _text(leaf_id: str) -> str:
    return LEAF_BY_ID[leaf_id].content


assert [_text(c) for c in ACTION_HEADER] == ["Action", "Summary", "Action", "Summary"]
assert [_text(c) for c in SKILL_HEADER] == ["Skill", "Ability", "Example Uses"]

#: The twelve action names, in the order the table prints them, each resolving
#: to the accepted ``action.*`` record of the same name. The record keys are not
#: guessed: every one is asserted present in the committed accepted artifact
#: below.
ACTION_NAMES = tuple(_text(name) for name, _summary in ACTION_ROWS)
assert ACTION_NAMES == (
    "Attack",
    "Dash",
    "Disengage",
    "Dodge",
    "Help",
    "Hide",
    "Influence",
    "Magic",
    "Ready",
    "Search",
    "Study",
    "Utilize",
), ACTION_NAMES
ACTION_TARGETS = {name: f"action.{name.lower()}" for name in ACTION_NAMES}
_ACCEPTED_RECORDS = {r.semantic_key for r in PRIOR.oracle.representation.records}
assert set(ACTION_TARGETS.values()) <= _ACCEPTED_RECORDS, sorted(
    set(ACTION_TARGETS.values()) - _ACCEPTED_RECORDS
)

#: The eighteen printed ``(Skill, Ability)`` pairs, cross-checked against the
#: accepted schema's own encoding of this table. ``SKILL_ABILITY`` is documented
#: as carrying the pairing *"exactly as the Skills table prints it"* and
#: ``roll_spec_violations`` enforces it, which is why this record carries the
#: rows as exact governing prose rather than minting a per-row fact family: the
#: pairing is already accepted schema content, and a second copy would be an
#: unconsumed duplicate of it.
SKILL_PAIRS = tuple(
    (_text(name), _text(ability)) for name, ability, _uses in SKILL_ROWS
)
for _name, _ability in SKILL_PAIRS:
    _skill = Skill(_name.lower().replace(" ", "_"))
    assert SKILL_ABILITY[_skill] == AbilityScore(_ability.lower()), (_name, _ability)
assert len(SKILL_PAIRS) == 18, len(SKILL_PAIRS)

# ---------------------------------------------------------------------------
# Review-unit membership
# ---------------------------------------------------------------------------
CR_LEAVES = (HEAD_CR, CR_A, CR_B, CR_C, CR_D, CR_SEE_ALSO, CR_STAT_BLOCK)
EXP_LEAVES = (HEAD_EXPERTISE, EXPERTISE, EXP_SEE_ALSO, EXP_POINTER)
SKILLS_LEAVES = (CAPTION_SKILLS,) + SKILL_HEADER + tuple(
    cell for row in SKILL_ROWS for cell in row
)
ACTIONS_LEAVES = (
    (HEAD_ACTIONS, INTRO)
    + ACTION_HEADER
    + tuple(cell for row in ACTION_ROWS for cell in row)
    + (IMPROVISED, HEAD_ONE_THING, ONE_THING)
    + (HEAD_BONUS, BONUS_A, BONUS_B, HEAD_REACTIONS, REACTIONS)
)
assert len(set(CR_LEAVES)) == 7, len(set(CR_LEAVES))
assert len(set(EXP_LEAVES)) == 4, len(set(EXP_LEAVES))
assert len(set(SKILLS_LEAVES)) == 58, len(set(SKILLS_LEAVES))
assert len(set(ACTIONS_LEAVES)) == 38, len(set(ACTIONS_LEAVES))
ALL_LEAVES = set(CR_LEAVES) | set(EXP_LEAVES) | set(SKILLS_LEAVES) | set(ACTIONS_LEAVES)
assert len(ALL_LEAVES) == 107, len(ALL_LEAVES)
assert ALL_LEAVES <= REPRESENTED
assert RUNNING_FOOTER not in ALL_LEAVES
#: The two *Playing the Game* units partition one 5c container: every represented
#: leaf of the ``Actions`` container is in exactly one of them.
_CONTAINER = LEAF_BY_ID[INTRO].container_path
_CONTAINED = {
    leaf.leaf_id
    for leaf in CAND.ledger.leaves
    if leaf.leaf_id in REPRESENTED
    and tuple(leaf.container_path[: len(_CONTAINER)]) == tuple(_CONTAINER)
}
assert _CONTAINED == set(SKILLS_LEAVES) | set(ACTIONS_LEAVES), len(_CONTAINED)
assert not (set(SKILLS_LEAVES) & set(ACTIONS_LEAVES))

# ---------------------------------------------------------------------------
# Clauses: the exact governing text, resolved to offsets by search
# ---------------------------------------------------------------------------
SUB, SUP = "substantive", "supporting"

#: ``(key, leaf, kind, exact text[, preceding anchor])`` -- the same shape
#: ``proficiency-1`` used. Offsets are never written down: each text is located
#: in its leaf and asserted to occur exactly once, so a clause that drifts fails
#: loudly instead of binding the wrong extent.
CLAUSES: list[tuple[str, ...]] = [
    # --- Rules Glossary > Challenge Rating -------------------------------
    (
        "cr.meaning",
        CR_A,
        SUB,
        "Challenge Rating (CR) summarizes the threat a monster poses to a "
        "group of four player characters.",
    ),
    (
        "cr.compare_a",
        CR_A,
        SUB,
        "Compare a monster’s CR to the characters’ level. If the CR is higher, "
        "the monster is likely a danger. If the",
    ),
    ("cr.compare_b", CR_B, SUB, "CR is lower, the monster likely poses little threat."),
    (
        "cr.circumstances",
        CR_C,
        SUB,
        "But circumstances and the number of player characters can "
        "significantly alter how threatening a monster is in actual play.",
    ),
    (
        "cr.toolbox_a",
        CR_C,
        SUP,
        "“Gameplay Toolbox” (“Combat Encounters”) provides guidance to the GM "
        "on using",
    ),
    ("cr.toolbox_b", CR_D, SUP, "CR while planning potential combat encounters."),
    ("cr.see_also", CR_SEE_ALSO, SUP, "See also"),
    ("cr.stat_block", CR_STAT_BLOCK, SUP, "“Stat Block.”"),
    # --- Rules Glossary > Expertise --------------------------------------
    (
        "exp.definition",
        EXPERTISE,
        SUB,
        "Expertise is a feature that enhances your use of a skill proficiency.",
    ),
    (
        "exp.doubling",
        EXPERTISE,
        SUB,
        "When you make an ability check with a skill proficiency in which you "
        "have Expertise, your Proficiency Bonus is doubled for that check "
        "unless the bonus is doubled by another feature.",
    ),
    (
        "exp.one_skill",
        EXPERTISE,
        SUB,
        "If you gain Expertise, you gain it in one skill in which you have "
        "proficiency.",
    ),
    (
        "exp.not_twice",
        EXPERTISE,
        SUB,
        "You can’t have Expertise in the same skill proficiency more than once.",
    ),
    ("exp.see_also", EXP_SEE_ALSO, SUP, "See also"),
    ("exp.pointer", EXP_POINTER, SUP, "“Playing the Game” (“Proficiency”)."),
    # --- Playing the Game > Actions --------------------------------------
    (
        "act.default",
        INTRO,
        SUB,
        "When you do something other than moving or communicating, you "
        "typically take an action.",
    ),
    (
        "act.table_pointer",
        INTRO,
        SUB,
        "The Action table lists the game’s main actions, which are defined in "
        "more detail in “Rules Glossary.”",
    ),
    # 5c absorbed the Action table's printed caption into the end of this
    # paragraph, exactly as it did the Proficiency Bonus table's. Reported as a
    # 5c artifact, not repaired here.
    ("act.caption", INTRO, SUP, "Actions"),
    (
        "act.also_do",
        IMPROVISED,
        SUB,
        "Player characters and monsters can also do things not covered by "
        "these actions. Many class features and other abilities provide "
        "additional action options, and you can improvise other actions.",
    ),
    (
        "act.gm_call",
        IMPROVISED,
        SUB,
        "When you describe an action not detailed elsewhere in the rules, the "
        "Game Master tells you whether that action is possible and what kind "
        "of D20 Test you need to make, if any.",
    ),
    (
        "act.one_thing",
        ONE_THING,
        SUB,
        "The game uses actions to govern how much you can do at one time. You "
        "can take only one action at a time.",
    ),
    (
        "act.one_thing_combat",
        ONE_THING,
        SUP,
        "This principle is most important in combat, as explained in “Combat” "
        "later in “Playing the Game.”",
    ),
    (
        "act.one_thing_examples",
        ONE_THING,
        SUP,
        "Actions can come up in other situations, too: in a social "
        "interaction, you can try to Influence a creature or use the Search "
        "action to read the creature’s body language, but you can’t do both at "
        "the same time. And when you’re exploring a dungeon, you can’t "
        "simultaneously use the Search action to look for traps and use the "
        "Help action to aid another character who’s trying to open a stuck "
        "door (with the Utilize action).",
    ),
    (
        "act.bonus_grant",
        BONUS_A,
        SUB,
        "Various class features, spells, and other abilities let you take an "
        "additional action on your turn called a Bonus Action.",
    ),
    ("act.bonus_example_a", BONUS_A, SUP, "The Cunning Action feature, for"),
    (
        "act.bonus_example_b",
        BONUS_B,
        SUP,
        "example, allows a Rogue to take a Bonus Action.",
    ),
    (
        "act.bonus_only_when",
        BONUS_B,
        SUB,
        "You can take a Bonus Action only when a special ability, a spell, or "
        "another feature of the game states that you can do something as a "
        "Bonus Action. You otherwise don’t have a Bonus Action to take.",
    ),
    (
        "act.bonus_one",
        BONUS_B,
        SUB,
        "You can take only one Bonus Action on your turn, so you must choose "
        "which Bonus Action to use if you have more than one available.",
    ),
    (
        "act.bonus_timing",
        BONUS_B,
        SUB,
        "You choose when to take a Bonus Action during your turn unless the "
        "Bonus Action’s timing is specified.",
    ),
    (
        "act.bonus_deprived",
        BONUS_B,
        SUB,
        "Anything that deprives you of your ability to take actions also "
        "prevents you from taking a Bonus Action.",
    ),
    (
        "act.reaction_def",
        REACTIONS,
        SUB,
        "Certain special abilities, spells, and situations allow you to take a "
        "special action called a Reaction. A Reaction is an instant response "
        "to a trigger of some kind, which can occur on your turn or on "
        "someone else’s.",
    ),
    (
        "act.reaction_opportunity",
        REACTIONS,
        SUP,
        "The Opportunity Attack, described later in “Playing the Game,” is the "
        "most common type of Reaction.",
    ),
    (
        "act.reaction_one",
        REACTIONS,
        SUB,
        "When you take a Reaction, you can’t take another one until the start "
        "of your next turn.",
    ),
    (
        "act.reaction_interrupt",
        REACTIONS,
        SUB,
        "If the reaction interrupts another creature’s turn, that creature can "
        "continue its turn right after the Reaction.",
    ),
    (
        "act.reaction_timing",
        REACTIONS,
        SUB,
        "In terms of timing, a Reaction takes place immediately after its "
        "trigger unless the Reaction’s description says otherwise.",
    ),
]

#: Every table cell is one whole-leaf clause. A name cell is the row's subject
#: and is substantive; a Summary cell summarizes the accepted ``action.*``
#: record the name cell resolves to, so it is supporting authority rather than a
#: second copy of accepted Action content; an Example Uses cell is what its own
#: column header calls it.
for _i, (_name, _summary) in enumerate(ACTION_ROWS):
    CLAUSES.append((f"act.row.{_i}.name", _name, SUB, _text(_name)))
    CLAUSES.append((f"act.row.{_i}.summary", _summary, SUP, _text(_summary)))
for _i, _cell in enumerate(ACTION_HEADER):
    CLAUSES.append((f"act.header.{_i}", _cell, SUP, _text(_cell)))
CLAUSES.append(("skills.caption", CAPTION_SKILLS, SUP, _text(CAPTION_SKILLS)))
for _i, _cell in enumerate(SKILL_HEADER):
    CLAUSES.append((f"skills.header.{_i}", _cell, SUP, _text(_cell)))
for _i, (_name, _ability, _uses) in enumerate(SKILL_ROWS):
    CLAUSES.append((f"skills.row.{_i}.name", _name, SUB, _text(_name)))
    CLAUSES.append((f"skills.row.{_i}.ability", _ability, SUB, _text(_ability)))
    CLAUSES.append((f"skills.row.{_i}.uses", _uses, SUP, _text(_uses)))

_DISPOSITION = {
    SUB: SemanticDisposition.SUBSTANTIVE,
    SUP: SemanticDisposition.SUPPORTING_AUTHORITY,
}
_RATIONALE = {
    SUB: "states a rule of this review unit that the representation carries",
    SUP: "identifies, exemplifies or contextualizes a rule stated elsewhere "
    "in this review unit",
}

SPANS: dict[str, SemanticSpan] = {}
PROPOSED: list[ProposedSpan] = []
for _row in CLAUSES:
    _key, _leaf, _kind, _clause = _row[0], _row[1], _row[2], _row[3]
    _anchor = _row[4] if len(_row) > 4 else ""
    _content = _text(_leaf)
    assert _content.count(_anchor + _clause) == 1, (
        _key,
        _content.count(_anchor + _clause),
    )
    _start = _content.index(_anchor + _clause) + len(_anchor)
    _span = SemanticSpan(
        span_id=derive_span_id(_leaf, _start, _start + len(_clause)),
        leaf_id=_leaf,
        char_start=_start,
        char_end=_start + len(_clause),
        disposition=_DISPOSITION[_kind],
        review_state=ReviewState.PROPOSED,
        non_mechanical_reason_code=None,
    )
    assert _key not in SPANS, _key
    SPANS[_key] = _span
    PROPOSED.append(
        ProposedSpan(span=_span, origin=ORIGIN, rationale=_RATIONALE[_kind])
    )

assert len(SPANS) == 120, len(SPANS)


def sid(key: str) -> str:
    """The proposed span id of one clause."""
    return SPANS[key].span_id


def _bind(key: str) -> tuple[str, int, int]:
    """Resolve one clause to the single chunk that unambiguously contains it."""
    span = SPANS[key]
    hits = [
        (cid, rng)
        for cid in dict.fromkeys(CHUNKS_BY_LEAF.get(span.leaf_id, ()))
        if (
            rng := CORPUS.chunk_relative_range(
                cid, span.leaf_id, span.char_start, span.char_end
            )
        )
        is not None
    ]
    assert len(hits) == 1, (key, [c for c, _ in hits])
    chunk_id, (start, end) = hits[0]
    return chunk_id, start, end


# ---------------------------------------------------------------------------
# The two typed facts
# ---------------------------------------------------------------------------
# ``glossary.action`` already carries *"On your turn, you can take one action"*
# as ``ActionAllowanceFact(count=1, per=TURN, cost=ACTION)``. These two are the
# same family in the same shape, read from the two sentences that state the same
# kind of limit for the other two slots the section defines. Neither is a second
# copy of accepted authority: no accepted record represents Bonus Actions or
# Reactions, and both clauses are read from their own spans.
BONUS_ACTION_ALLOWANCE = ActionAllowanceFact(
    count=1, per=AllowanceScope.TURN, cost=ActionCost.BONUS_ACTION
)
#: *"you can't take another one until the start of your next turn"* -- the
#: allowance renews at the start of each of the subject's turns, which is what
#: ``AllowanceScope.TURN`` counts per. The exact wording stays bound beside the
#: fact because "until the start of your next turn" also says *when* the
#: renewal happens, which a count does not.
REACTION_ALLOWANCE = ActionAllowanceFact(
    count=1, per=AllowanceScope.TURN, cost=ActionCost.REACTION
)

# Three clauses this batch deliberately leaves untyped, because typing them
# would state something the source does not:
#
# * *"You can take only one action at a time"* is not *per turn*. Outside
#   combat there are no turns, and ``AllowanceScope`` has no member for
#   simultaneity, so flattening it to ``TURN`` would record a narrower rule
#   than the one printed.
# * *"You otherwise don't have a Bonus Action to take"* is a default absence
#   conditioned on no feature granting one. ``ActionRestrictionFact`` states a
#   slot the subject *cannot* use, and stating it here unconditionally would
#   assert that a Bonus Action is never available.
# * *"a Reaction takes place immediately after its trigger unless the
#   Reaction's description says otherwise"* would need
#   ``TriggeredResolutionFact``, whose ``optional`` field is documented as
#   stated *"because the source states its own negative arm outright"*. This
#   sentence states no negative arm, so either value would be an invention.

# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------
NO_USE = "no_identified_structured_use"
GM = "gamemaster_latitude"
JUDGMENT = "subjective_judgment"
CONTEXT = "contextual_applicability"
EXCEPTION = "natural_language_exception"
OPEN_ENDED = "open_ended_effect"

#: ``(record, component_key, handling, irreducibility, retention, clauses)``.
COMPONENTS: tuple[
    tuple[
        str, str, ComponentHandling, str | None, str | None, tuple[str, ...]
    ],
    ...,
] = (
    # --- glossary.challenge_rating ---------------------------------------
    (
        CR,
        "challenge_rating_meaning",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("cr.meaning",),
    ),
    # The comparison is printed with "likely" in both arms: it tells the reader
    # what to expect, not what follows. That is a judgement call rather than a
    # computation, which is the closed reason this component states.
    (
        CR,
        "threat_comparison",
        ComponentHandling.PROSE_BOUND,
        JUDGMENT,
        None,
        ("cr.compare_a", "cr.compare_b"),
    ),
    # Whether the rating describes the actual threat depends on circumstances
    # and party size in play -- fiction the projection cannot enumerate.
    (
        CR,
        "encounter_circumstances",
        ComponentHandling.PROSE_BOUND,
        CONTEXT,
        None,
        ("cr.circumstances",),
    ),
    # --- glossary.expertise ----------------------------------------------
    (
        EXP,
        "expertise_definition",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("exp.definition",),
    ),
    # The doubling carries its own exception -- "unless the bonus is doubled by
    # another feature" -- which is why this component states the exception
    # reason rather than the retention one. The arithmetic limit it points at is
    # already accepted authority on ``play.proficiency/bonus_does_not_stack``,
    # read from that section's own spans; restating it here would publish one
    # source rule as two copies.
    (
        EXP,
        "expertise_doubling",
        ComponentHandling.PROSE_BOUND,
        EXCEPTION,
        None,
        ("exp.doubling",),
    ),
    (
        EXP,
        "expertise_grant",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("exp.one_skill", "exp.not_twice"),
    ),
    # --- play.skills -----------------------------------------------------
    # One component, thirty-six bindings: each row's Skill and Ability cells.
    # The pairing is accepted schema content already (``SKILL_ABILITY``), so no
    # identified code-owned use needs a separate structured field for it.
    (
        SKILLS,
        "skills_table",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        tuple(
            f"skills.row.{i}.{part}"
            for i in range(18)
            for part in ("name", "ability")
        ),
    ),
    # --- play.actions ----------------------------------------------------
    (
        ACTIONS,
        "action_default",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("act.default",),
    ),
    # The table pointer and the twelve rows the pointer describes. The twelve
    # references hang off this component.
    (
        ACTIONS,
        "action_table",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("act.table_pointer",)
        + tuple(f"act.row.{i}.name" for i in range(12)),
    ),
    # Split for the reason ``proficiency-1`` split skill relevance: a component
    # states exactly one reason why its meaning is prose, and these two clauses
    # do not share one. The effect space of "other abilities provide additional
    # action options" is unbounded; the next sentence hands the decision to the
    # GM in the source's own words.
    (
        ACTIONS,
        "improvised_action_options",
        ComponentHandling.PROSE_BOUND,
        OPEN_ENDED,
        None,
        ("act.also_do",),
    ),
    (
        ACTIONS,
        "improvised_action_judgment",
        ComponentHandling.PROSE_BOUND,
        GM,
        None,
        ("act.gm_call",),
    ),
    (
        ACTIONS,
        "one_action_at_a_time",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("act.one_thing",),
    ),
    (
        ACTIONS,
        "bonus_action_availability",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("act.bonus_grant", "act.bonus_only_when"),
    ),
    # MIXED: the one-per-turn limit is typed, and the two clauses stay bound
    # beside it -- "you must choose which Bonus Action to use" and the timing
    # freedom with its own exception are meaning the count does not carry.
    (
        ACTIONS,
        "bonus_action_allowance",
        ComponentHandling.MIXED,
        None,
        NO_USE,
        ("act.bonus_one", "act.bonus_timing"),
    ),
    (
        ACTIONS,
        "bonus_action_deprivation",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("act.bonus_deprived",),
    ),
    (
        ACTIONS,
        "reaction_definition",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("act.reaction_def",),
    ),
    (
        ACTIONS,
        "reaction_allowance",
        ComponentHandling.MIXED,
        None,
        NO_USE,
        ("act.reaction_one",),
    ),
    (
        ACTIONS,
        "reaction_interruption",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("act.reaction_interrupt",),
    ),
    (
        ACTIONS,
        "reaction_timing",
        ComponentHandling.PROSE_BOUND,
        EXCEPTION,
        None,
        ("act.reaction_timing",),
    ),
)

_FACTS = {
    (ACTIONS, "bonus_action_allowance"): (BONUS_ACTION_ALLOWANCE,),
    (ACTIONS, "reaction_allowance"): (REACTION_ALLOWANCE,),
}

COMPONENT_DRAFTS: list[ComponentDraft] = []
BINDINGS: list[ProseBindingDraft] = []
for record, ckey, handling, irreducible, retention, bound in COMPONENTS:
    COMPONENT_DRAFTS.append(
        ComponentDraft(
            record_key=record,
            semantic_key=ckey,
            handling=handling,
            irreducibility_reason_code=irreducible,
            prose_retention_reason_code=retention,
            facts=_FACTS.get((record, ckey), ()),
        )
    )
    for clause in bound:
        chunk_id, cstart, cend = _bind(clause)
        BINDINGS.append(
            ProseBindingDraft(
                component_key=ckey,
                record_key=record,
                chunk_id=chunk_id,
                span_id=sid(clause),
                chunk_char_start=cstart,
                chunk_char_end=cend,
                irreducibility_reason_code=irreducible,
                prose_retention_reason_code=retention,
            )
        )
assert len(COMPONENT_DRAFTS) == 19, len(COMPONENT_DRAFTS)
assert len(BINDINGS) == 70, len(BINDINGS)

# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------
REFERENCES: tuple[ReferenceDraft, ...] = tuple(
    ReferenceDraft(
        from_record_key=ACTIONS,
        from_component_key="action_table",
        source_text=name,
        scope_key=GLOSSARY_SCOPE,
        target_record_key=ACTION_TARGETS[name],
    )
    for name in ACTION_NAMES
) + (
    # Record-owned: the entry states this pointer, and none of its three rule
    # components does. Scoped to *Playing the Game* because that is where the
    # destination is, which is also what keeps it distinct from the glossary's
    # own ``Proficiency`` entry.
    ReferenceDraft(
        from_record_key=EXP,
        from_component_key=RECORD_OWNED_REFERENCE,
        source_text="Proficiency",
        scope_key=PLAYING_THE_GAME_SCOPE,
        target_record_key=PROFICIENCY,
    ),
)
assert len(REFERENCES) == 13, len(REFERENCES)
REFERENCE_SPANS = {
    (ACTIONS, name): f"act.row.{i}.name" for i, name in enumerate(ACTION_NAMES)
}
REFERENCE_SPANS[(EXP, "Proficiency")] = "exp.pointer"

# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
PROVENANCE: list[ProvenanceClaim] = []

#: Each typed fact claims the clause it was read from CONTEXTUAL, for the reason
#: ``proficiency-1``'s typed inputs do: the clause's primary home is the prose
#: binding that governs it, and one span carries one primary claim.
for _record, _ckey, _fact, _clause in (
    (ACTIONS, "bonus_action_allowance", BONUS_ACTION_ALLOWANCE, "act.bonus_one"),
    (ACTIONS, "reaction_allowance", REACTION_ALLOWANCE, "act.reaction_one"),
):
    PROVENANCE.append(
        ProvenanceClaim(
            ProvenanceTargetKind.FACT,
            fact_target_key(_record, _ckey, _fact),
            sid(_clause),
            ProvenanceRole.CONTEXTUAL,
        )
    )

for binding in BINDINGS:
    PROVENANCE.append(
        ProvenanceClaim(
            ProvenanceTargetKind.PROSE_BINDING,
            prose_binding_target_key(binding),
            binding.span_id,
            ProvenanceRole.PRIMARY,
        )
    )

#: Supporting clauses, and which component each one supports.
SUPPORTING_CLAIMS: tuple[tuple[str, str, str], ...] = (
    ("cr.toolbox_a", CR, "encounter_circumstances"),
    ("cr.toolbox_b", CR, "encounter_circumstances"),
    ("act.one_thing_combat", ACTIONS, "one_action_at_a_time"),
    ("act.one_thing_examples", ACTIONS, "one_action_at_a_time"),
    ("act.bonus_example_a", ACTIONS, "bonus_action_availability"),
    ("act.bonus_example_b", ACTIONS, "bonus_action_availability"),
    ("act.reaction_opportunity", ACTIONS, "reaction_definition"),
) + tuple(
    (f"act.header.{i}", ACTIONS, "action_table") for i in range(4)
) + tuple(
    (f"act.row.{i}.summary", ACTIONS, "action_table") for i in range(12)
) + tuple(
    (f"skills.header.{i}", SKILLS, "skills_table") for i in range(3)
) + tuple(
    (f"skills.row.{i}.uses", SKILLS, "skills_table") for i in range(18)
)
for clause, record, ckey in SUPPORTING_CLAIMS:
    PROVENANCE.append(
        ProvenanceClaim(
            ProvenanceTargetKind.COMPONENT,
            (record, ckey),
            sid(clause),
            ProvenanceRole.CONTEXTUAL,
        )
    )
assert len(SUPPORTING_CLAIMS) == 44, len(SUPPORTING_CLAIMS)

#: A "See also" and a printed table caption identify the *record*, not one of
#: its components: they say what this entry is and where else to look, which is
#: why they are claimed at record level rather than assigned to a rule.
RECORD_CLAIMS: tuple[tuple[str, str], ...] = (
    ("cr.see_also", CR),
    ("cr.stat_block", CR),
    ("exp.see_also", EXP),
    ("skills.caption", SKILLS),
    ("act.caption", ACTIONS),
)
for clause, record in RECORD_CLAIMS:
    PROVENANCE.append(
        ProvenanceClaim(
            ProvenanceTargetKind.RECORD,
            (record,),
            sid(clause),
            ProvenanceRole.CONTEXTUAL,
        )
    )

for ref in REFERENCES:
    PROVENANCE.append(
        ProvenanceClaim(
            ProvenanceTargetKind.REFERENCE,
            reference_target_key(ref),
            sid(REFERENCE_SPANS[(ref.from_record_key, ref.source_text)]),
            ProvenanceRole.CONTEXTUAL,
        )
    )
assert len(PROVENANCE) == 134, len(PROVENANCE)

DRAFT = RepresentationDraft(
    records=(
        RecordDraft(semantic_key=CR, kind=RecordKind.GLOSSARY_RULE),
        RecordDraft(semantic_key=EXP, kind=RecordKind.GLOSSARY_RULE),
        RecordDraft(semantic_key=SKILLS, kind=RecordKind.GENERAL_RULE),
        RecordDraft(semantic_key=ACTIONS, kind=RecordKind.GENERAL_RULE),
    ),
    components=tuple(COMPONENT_DRAFTS),
    prose_bindings=tuple(BINDINGS),
    relationships=(),
    references=REFERENCES,
    provenance=tuple(PROVENANCE),
)

# ---------------------------------------------------------------------------
# The four review units
# ---------------------------------------------------------------------------
HEADING_REASON = (
    "section and entry headings: each names the rules stated below it and "
    "states no rule itself"
)

CR_UNIT = ReviewUnit(
    unit_id="proficiency-destinations-1-challenge-rating",
    kind=ReviewUnitKind.ENTRY,
    leaf_ids=CR_LEAVES,
    expected_rules=(
        ExpectedRule(CR, "challenge_rating_meaning", None, (sid("cr.meaning"),)),
        ExpectedRule(
            CR,
            "threat_comparison",
            None,
            (sid("cr.compare_a"), sid("cr.compare_b")),
        ),
        ExpectedRule(
            CR, "encounter_circumstances", None, (sid("cr.circumstances"),)
        ),
    ),
    supporting_groups=(
        SupportingGroup((CR_D,), CR, "encounter_circumstances"),
        SupportingGroup((CR_SEE_ALSO, CR_STAT_BLOCK), CR),
    ),
    excluded_groups=(ExcludedGroup((HEAD_CR,), HEADING_REASON),),
)

EXP_UNIT = ReviewUnit(
    unit_id="proficiency-destinations-1-expertise",
    kind=ReviewUnitKind.ENTRY,
    leaf_ids=EXP_LEAVES,
    expected_rules=(
        ExpectedRule(EXP, "expertise_definition", None, (sid("exp.definition"),)),
        ExpectedRule(EXP, "expertise_doubling", None, (sid("exp.doubling"),)),
        ExpectedRule(
            EXP,
            "expertise_grant",
            None,
            (sid("exp.one_skill"), sid("exp.not_twice")),
        ),
    ),
    supporting_groups=(SupportingGroup((EXP_SEE_ALSO, EXP_POINTER), EXP),),
    excluded_groups=(ExcludedGroup((HEAD_EXPERTISE,), HEADING_REASON),),
)

#: One expected rule per printed row, which is what ``TABLE`` means: an omitted
#: row leaves a named span unbound and is reported rather than absorbed.
SKILLS_UNIT = ReviewUnit(
    unit_id="proficiency-destinations-1-skills-table",
    kind=ReviewUnitKind.TABLE,
    leaf_ids=SKILLS_LEAVES,
    expected_rules=tuple(
        ExpectedRule(
            SKILLS,
            "skills_table",
            None,
            (sid(f"skills.row.{i}.name"), sid(f"skills.row.{i}.ability")),
        )
        for i in range(18)
    ),
    supporting_groups=(
        SupportingGroup(
            (CAPTION_SKILLS,)
            + SKILL_HEADER
            + tuple(uses for _n, _a, uses in SKILL_ROWS),
            SKILLS,
            "skills_table",
        ),
    ),
    excluded_groups=(),
)

ACTION_ROW_RULES = tuple(
    ExpectedRule(ACTIONS, "action_table", None, (sid(f"act.row.{i}.name"),))
    for i in range(12)
)
ACTION_PROSE_RULES = tuple(
    ExpectedRule(ACTIONS, ckey, None, tuple(sid(c) for c in clauses))
    for ckey, clauses in (
        ("action_default", ("act.default",)),
        ("action_table", ("act.table_pointer",)),
        ("improvised_action_options", ("act.also_do",)),
        ("improvised_action_judgment", ("act.gm_call",)),
        ("one_action_at_a_time", ("act.one_thing",)),
        ("bonus_action_availability", ("act.bonus_grant", "act.bonus_only_when")),
        ("bonus_action_allowance", ("act.bonus_one", "act.bonus_timing")),
        ("bonus_action_deprivation", ("act.bonus_deprived",)),
        ("reaction_definition", ("act.reaction_def",)),
        ("reaction_allowance", ("act.reaction_one",)),
        ("reaction_interruption", ("act.reaction_interrupt",)),
        ("reaction_timing", ("act.reaction_timing",)),
    )
)
ACTION_FACT_RULES = (
    ExpectedRule(
        ACTIONS,
        "bonus_action_allowance",
        ActionAllowanceFact.FAMILY.value,
        (sid("act.bonus_one"),),
    ),
    ExpectedRule(
        ACTIONS,
        "reaction_allowance",
        ActionAllowanceFact.FAMILY.value,
        (sid("act.reaction_one"),),
    ),
)
ACTIONS_UNIT = ReviewUnit(
    unit_id="proficiency-destinations-1-actions-section",
    kind=ReviewUnitKind.SECTION,
    leaf_ids=ACTIONS_LEAVES,
    expected_rules=ACTION_PROSE_RULES + ACTION_ROW_RULES + ACTION_FACT_RULES,
    supporting_groups=(
        SupportingGroup(
            ACTION_HEADER + tuple(summary for _n, summary in ACTION_ROWS),
            ACTIONS,
            "action_table",
        ),
    ),
    excluded_groups=(ExcludedGroup(HEADINGS, HEADING_REASON),),
)

UNITS = (CR_UNIT, EXP_UNIT, SKILLS_UNIT, ACTIONS_UNIT)
assert [len(u.expected_rules) for u in UNITS] == [3, 3, 18, 26], [
    len(u.expected_rules) for u in UNITS
]
assert sum(len(u.leaf_ids) for u in UNITS) == 107

# ---------------------------------------------------------------------------
# Batch-scoped validation
# ---------------------------------------------------------------------------
LEDGER = ClassificationLedger(
    package_uuid=BINDING.package_uuid,
    release_version=BINDING.release_version,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    spans=tuple(SPANS.values()),
    batches=(),
    acceptances=(),
)

partition: list[str] = []
for lid in sorted({s.leaf_id for s in LEDGER.spans}):
    partition.extend(
        validate_partition(
            lid,
            CORPUS.leaf_lengths[lid],
            tuple(s for s in LEDGER.spans if s.leaf_id == lid),
            require_complete=False,
        )
    )
assert partition == [], partition
assert validate_reason_codes(LEDGER.spans) == (), validate_reason_codes(LEDGER.spans)

units = review_unit_violations(UNITS, DRAFT, SEMANTIC_POLICY_VERSION, LEDGER.spans)
assert units == [], units

standalone = list(validate_representation(DRAFT, LEDGER, CORPUS))
#: Standalone, this batch's thirteen references name records it does not declare
#: itself: twelve accepted ``action.*`` records and the ``play.proficiency``
#: record ``proficiency-1`` proposes. That is the honest and detectable state --
#: the same ``unknown target record`` finding ``proficiency-1`` reported for the
#: two glossary entries this batch now mints -- and every one of them resolves
#: in the merged representation, proved below.
EXPECTED_FINDINGS = tuple(
    sorted(
        f"reference {ref.scope_key}:{ref.source_text!r}: "
        f"unknown target record {ref.target_record_key}"
        for ref in REFERENCES
    )
)
assert tuple(sorted(standalone)) == EXPECTED_FINDINGS, standalone

#: Dropping any one Skills-table row must be *reported*, not absorbed: the
#: ``TABLE`` contract is what makes an omitted row a missing expected rule.
_short_bindings = tuple(
    b for b in BINDINGS if b.span_id != sid("skills.row.17.ability")
)
_short_draft = RepresentationDraft(
    records=DRAFT.records,
    components=DRAFT.components,
    prose_bindings=_short_bindings,
    relationships=DRAFT.relationships,
    references=DRAFT.references,
    provenance=tuple(
        c
        for c in DRAFT.provenance
        if not (
            c.target_kind is ProvenanceTargetKind.PROSE_BINDING
            and c.span_id == sid("skills.row.17.ability")
        )
    ),
)
_dropped = review_unit_violations(
    UNITS, _short_draft, SEMANTIC_POLICY_VERSION, LEDGER.spans
)
assert _dropped, "dropping the Survival row's ability cell produced no violation"
assert all("skills_table" in f for f in _dropped), _dropped

#: Disjoint from the seven accepted batches: this batch re-accepts nothing and
#: touches none of their leaves.
_accepted_spans = {s.span_id for s in PRIOR.oracle.spans}
_accepted_leaves = {s.leaf_id for s in PRIOR.oracle.spans}
assert not (_accepted_spans & {s.span_id for s in LEDGER.spans})
assert not (_accepted_leaves & ALL_LEAVES)
assert not (_ACCEPTED_RECORDS & {r.semantic_key for r in DRAFT.records})

# ---------------------------------------------------------------------------
# The proposal
# ---------------------------------------------------------------------------
PROPOSAL = MechanicalProposal(
    binding=BINDING,
    policy_version=SEMANTIC_POLICY_VERSION,
    policy_hash=semantic_policy_hash(),
    schema_version=REPRESENTATION_SCHEMA_VERSION,
    schema_hash=representation_schema_hash(),
    proposed_spans=tuple(PROPOSED),
    proposed_representation=DRAFT,
    proposal_origin=(
        f"{ORIGIN} (CRD Issue 5d batch {BATCH_ID}, representation schema 15)"
    ),
    proposal_schema_version=PROPOSAL_SCHEMA_VERSION_2,
    proposed_review_units=UNITS,
)
payload = proposal_payload(PROPOSAL)
identity = proposal_identity(PROPOSAL)

assert {p.span.review_state for p in PROPOSAL.proposed_spans} == {
    ReviewState.PROPOSED
}

text = json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False)
path = OUT / PROPOSAL_FILE
path.write_text(text, encoding="utf-8", newline="\n")
written = path.read_bytes()
assert b"\r" not in written, "the proposal was written with a carriage return"

print(f"batch            {BATCH_ID}")
print(f"proposal         {PROPOSAL_FILE}  ({len(written)} bytes)")
print(f"proposal_identity {identity}")
print(f"file_sha256      {hashlib.sha256(written).hexdigest()}")
print(f"schema           {REPRESENTATION_SCHEMA_VERSION}")
print(f"records          {len(DRAFT.records)}   review units {len(UNITS)}")
for _u in UNITS:
    print(
        f"  {_u.unit_id:<52} {_u.kind.value:<8} "
        f"{len(_u.leaf_ids):>3} leaves {len(_u.expected_rules):>3} rules"
    )
print(f"leaves           {len(ALL_LEAVES)} represented, 1 excluded by 5c")
print(f"spans            {len(SPANS)}")
print(f"components       {len(COMPONENT_DRAFTS)}   bindings {len(BINDINGS)}")
print(f"typed facts      2 action allowances (bonus action, reaction)")
print(f"provenance       {len(PROVENANCE)}   references {len(REFERENCES)}")
print(f"partition        {len(partition)} findings")
print(f"review units     {len(units)} findings")
print(f"representation   {len(standalone)} findings (all thirteen citations)")
for finding in sorted(standalone):
    print(f"  - {finding}")
