"""Author the **proficiency-1** proposal: Playing the Game > Proficiency.

REVIEW MATERIAL. Emits an *unaccepted* ``5d-proposal-2`` artifact next to this
file. It accepts nothing, publishes nothing, and writes nothing under
``oracles/``.

The first regular-section pilot under CRD Issue 5d (#137), and deliberately
small: everything below is a literal table plus the merged common services
(``build_candidate``, ``exclusion_reason_for``, ``_full_coverage_edges``,
``derive_span_id``, ``validate_partition``, ``validate_reason_codes``,
``validate_representation``, ``review_unit_violations``, ``proposal_payload``,
``proposal_identity``). No acceptance machinery is reimplemented here.

**Scope.** The whole subsection: 31 leaves, one of which 5c excludes as a
running header/footer, so 30 represented leaves reviewed as one ``SECTION``
unit. A ``TABLE`` unit over the table container alone would have omitted levels
17-30, which 5c represents in a paragraph *outside* that container
(``f848a0fb``); the section boundary is what keeps the progression whole.

**Batch scope, not publication scope.** ``validate_candidate`` iterates the
whole represented population, so it is not this batch's gate. The evidence here
is the three scoped checks speed-1 used: per-leaf ``validate_partition`` with
``require_complete=False`` for the leaves the unit accounts for,
``review_unit_violations``, and standalone ``validate_representation``.
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
    REPRESENTATION_SCHEMA_VERSION,
    AdvantageFact,
    AdvantageState,
    ComponentDraft,
    ComponentHandling,
    ProficiencyBonusBandFact,
    ProseBindingDraft,
    ProvenanceClaim,
    ProvenanceRole,
    ProvenanceTargetKind,
    RecordDraft,
    RecordKind,
    ReferenceDraft,
    RepresentationDraft,
    RollActor,
    RollContext,
    RollSpec,
    fact_target_key,
    prose_binding_target_key,
    reference_target_key,
    representation_schema_hash,
)
from afterworlds.ingestion.mechanical.validation import (  # noqa: E402
    validate_representation,
)
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402

BATCH_ID = "proficiency-1"
RECORD = "play.proficiency"
ORIGIN = "issue-5d-batch-proficiency-1-generator.py"
PROPOSAL_FILE = "issue-5d-batch-proficiency-1-PROPOSAL.json"
SOURCE_PDF = REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"
ARTIFACT = (
    REPO
    / "src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json"
)
#: The glossary is the only resolution scope this batch cites into, and it is
#: the scope the seven accepted batches already committed. Nothing new is minted.
GLOSSARY_SCOPE = "srd-5.2.1/rules-glossary"

# ---------------------------------------------------------------------------
# The reviewed source: 31 leaves, reading order 252-282
# ---------------------------------------------------------------------------
HEAD_PROFICIENCY = "e00cea37-87da-5103-9b72-724563a15fd7"
MAIN = "ce26a9f7-06dd-5002-b65b-ca1916eb6296"
CELL_LEVEL_OR_CR = "34cf6220-418b-5317-9f49-6864c136fee4"
CELL_BONUS = "2a6af63f-16e0-5a4c-9f94-b34da743d312"
CELL_UPTO4 = "b002753c-b2d1-5946-9c75-df58cdcfe1da"
CELL_P2 = "69ae5a1b-93b0-5a16-ad68-8a52e3b7e050"
CELL_5_8 = "8a6fc1a5-d66c-55ab-b579-0539e7c547ca"
CELL_P3 = "d58940db-afa7-58ee-9af1-9e5338530676"
CELL_9_12 = "515f45ef-455b-5042-993e-397bb177e44c"
CELL_P4 = "19340146-e933-556d-bd1b-da74b35919ae"
CELL_13_16 = "9b1cee59-6bba-5749-b8f0-b525adc93f78"
CELL_P5 = "df4629be-e31e-57d3-a15d-41904c0a98ac"
LATER_ROWS = "f848a0fb-fc22-55c3-a187-e983c38c4b08"
HEAD_STACK = "fcf9878a-1534-517e-beba-fe427702adaf"
STACK = "940239fe-1faa-5fee-8b16-87ea5d9e4f69"
HEAD_SKILL_PROF = "192c232c-9837-5567-877c-5bac035a0eef"
SKILL_A = "5954cb89-5bd9-5890-968d-479b175c1f14"
RUNNING_FOOTER = "bda26fa3-3c42-57a6-93bf-69506f41b67c"
SKILL_B = "e45739f5-cfc8-5e7b-b28c-9ce4b01c9e5d"
HEAD_SKILL_LIST = "bddf4800-60b4-5c84-afbc-a7010382da6a"
SKILL_LIST = "9b012d75-1a8a-5698-8a77-d51b41211e8c"
HEAD_DETERMINING = "491ef243-9c16-5de4-8078-cc3b1108fe55"
DETERMINING = "91e1341f-eda5-5cb1-baa0-59013201538d"
HEAD_SAVES = "6269641e-d6ae-5cc3-a697-eb1913e05fe1"
SAVES = "6b6df866-c964-5555-824c-111bce1374b2"
HEAD_EQUIPMENT = "8a9c1d4c-70b9-5325-bbd9-f4aa076e6007"
EQUIPMENT = "b1d1ef1a-8725-5321-a4ca-7e1b42451c25"
LABEL_WEAPONS = "6c8871c3-a159-54b1-8789-6c18f42a7662"
WEAPONS = "3576be8e-7f79-5007-afe3-0d110f7dbbfd"
LABEL_TOOLS = "df4e6013-c3be-5cb3-98bf-e0d7431475fd"
TOOLS = "e9d9f35f-226b-5c61-b7cd-bb05ffeb1c67"

HEADINGS = (
    HEAD_PROFICIENCY,
    HEAD_STACK,
    HEAD_SKILL_PROF,
    HEAD_SKILL_LIST,
    HEAD_DETERMINING,
    HEAD_SAVES,
    HEAD_EQUIPMENT,
)
SECTION_LEAVES = (
    HEAD_PROFICIENCY,
    MAIN,
    CELL_LEVEL_OR_CR,
    CELL_BONUS,
    CELL_UPTO4,
    CELL_P2,
    CELL_5_8,
    CELL_P3,
    CELL_9_12,
    CELL_P4,
    CELL_13_16,
    CELL_P5,
    LATER_ROWS,
    HEAD_STACK,
    STACK,
    HEAD_SKILL_PROF,
    SKILL_A,
    SKILL_B,
    HEAD_SKILL_LIST,
    SKILL_LIST,
    HEAD_DETERMINING,
    DETERMINING,
    HEAD_SAVES,
    SAVES,
    HEAD_EQUIPMENT,
    EQUIPMENT,
    LABEL_WEAPONS,
    WEAPONS,
    LABEL_TOOLS,
    TOOLS,
)
assert len(set(SECTION_LEAVES)) == 30, len(set(SECTION_LEAVES))
assert RUNNING_FOOTER not in SECTION_LEAVES

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
#: The footer is excluded *by 5c*, not by a judgement made here — which is why
#: the review unit must not name it and why it is absent from ``leaf_lengths``.
assert RUNNING_FOOTER not in REPRESENTED
assert set(SECTION_LEAVES) <= REPRESENTED

EDGES = _full_coverage_edges(CAND.members.chunks, LEAF_BY_ID)

#: Read from the committed accepted artifact rather than restated here: the
#: sixth part (``persisted_corpus_digest``) digests persisted corpus state --
#: SQL ledger, members, reconciliation, sources and read-back vector logical
#: state -- none of which this run reads or touches.
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
# Clauses: the exact governing text, resolved to offsets by search
# ---------------------------------------------------------------------------
# One row per reviewed clause. Offsets are never written down: each text is
# located in its leaf and asserted to occur exactly once, so a clause that
# drifts fails loudly instead of binding the wrong extent.
#
# ``kind`` is the accepted disposition. ``flavor`` is the one non-mechanical
# clause in the section and carries the closed reason the catalog states.
SUB, SUP, NON = "substantive", "supporting", "non_mechanical"

# A fifth element is the exact text that must immediately precede the clause,
# used only where the clause wording repeats inside its own leaf. It is an
# anchor, never an offset: the pair still has to occur exactly once.
CLAUSES: tuple[tuple[str, ...], ...] = (
    # ce26a9f7 - the opening paragraph
    (
        "main.flavor",
        MAIN,
        NON,
        "Characters and monsters are good at various things. Some are skilled "
        "with many weapons, while others can use only a few. Some are better "
        "at understanding people’s motives, and others are better at "
        "unlocking the secrets of the multiverse.",
    ),
    (
        "main.all_creatures",
        MAIN,
        SUB,
        "All creatures have a Proficiency Bonus, which reflects the impact "
        "that training has on the creature’s capabilities.",
    ),
    (
        "main.character_levels",
        MAIN,
        SUB,
        "A character’s Proficiency Bonus increases as the character gains "
        "levels (described in “Character Creation”).",
    ),
    (
        "main.monster_cr",
        MAIN,
        SUB,
        "A monster’s Proficiency Bonus is based on its Challenge Rating "
        "(see “Rules Glossary”).",
    ),
    (
        "main.table_pointer",
        MAIN,
        SUP,
        "The Proficiency Bonus table shows how the bonus is determined.",
    ),
    (
        "main.d20_test",
        MAIN,
        SUB,
        "This bonus is applied to a D20 Test when the creature has proficiency "
        "in a skill, in a saving throw, or with an item that the creature uses "
        "to make the D20 Test.",
    ),
    (
        "main.spells",
        MAIN,
        SUB,
        "The bonus is also used for spell attacks and for calculating the DC "
        "of saving throws for spells.",
    ),
    # 5c absorbed the table's printed caption into the end of this paragraph.
    # It is the table's title, so it is supporting authority for the table
    # rather than a rule of its own - and it is reported as a 5c artifact, not
    # repaired here.
    ("main.caption", MAIN, SUP, "Proficiency Bonus", "for spells. "),
    # The table container: one whole-leaf clause per data cell.
    ("cell.upto4", CELL_UPTO4, SUB, "Up to 4"),
    ("cell.p2", CELL_P2, SUB, "+2"),
    ("cell.5_8", CELL_5_8, SUB, "5–8"),
    ("cell.p3", CELL_P3, SUB, "+3"),
    ("cell.9_12", CELL_9_12, SUB, "9–12"),
    ("cell.p4", CELL_P4, SUB, "+4"),
    ("cell.13_16", CELL_13_16, SUB, "13–16"),
    ("cell.p5", CELL_P5, SUB, "+5"),
    # f848a0fb - levels 17-30, represented OUTSIDE the table container. The
    # repeated column header came with them.
    ("later.header", LATER_ROWS, SUP, "Level or CR Bonus"),
    ("later.17_20", LATER_ROWS, SUB, "17–20 +6"),
    ("later.21_24", LATER_ROWS, SUB, "21–24 +7"),
    ("later.25_28", LATER_ROWS, SUB, "25–28 +8"),
    ("later.29_30", LATER_ROWS, SUB, "29–30 +9"),
    # 940239fe - The Bonus Doesn't Stack
    (
        "stack.once",
        STACK,
        SUB,
        "Your Proficiency Bonus can’t be added to a die roll or another "
        "number more than once.",
    ),
    (
        "stack.example",
        STACK,
        SUP,
        "For example, if a rule allows you to make a Charisma (Deception or "
        "Persuasion) check, you add your Proficiency Bonus if you’re "
        "proficient in either skill, but you don’t add it twice if "
        "you’re proficient in both skills.",
    ),
    (
        "stack.scaling",
        STACK,
        SUB,
        "Occasionally, a Proficiency Bonus might be multiplied or divided "
        "(doubled or halved, for example) before being added.",
    ),
    (
        "stack.expertise",
        STACK,
        SUP,
        "For example, the Expertise feature (see “Rules Glossary”) "
        "doubles the Proficiency Bonus for certain ability checks.",
    ),
    (
        "stack.once_each",
        STACK,
        SUB,
        "Whenever the bonus is used, it can be multiplied only once and "
        "divided only once.",
    ),
    # 5954cb89 / e45739f5 - Skill Proficiencies, across a page break
    (
        "skill.definition",
        SKILL_A,
        SUP,
        "Most ability checks involve using a skill, which represents a "
        "category of things creatures try to do with an ability check.",
    ),
    (
        "skill.sources",
        SKILL_A,
        SUB,
        "The descriptions of the actions you take (see “Actions” "
        "later in “Playing the Game”) specify which skill applies if "
        "you make an ability check for that action, and many other rules note "
        "when a skill is relevant.",
    ),
    (
        "skill.gm_say",
        SKILL_A,
        SUB,
        "The GM has the ultimate say on whether a skill is relevant in a "
        "situation.",
    ),
    (
        "skill.proficient",
        SKILL_A,
        SUB,
        "If a creature is proficient in a skill, the creature applies its "
        "Proficiency Bonus to ability checks involving that skill.",
    ),
    (
        "skill.without_a",
        SKILL_A,
        SUB,
        "Without proficiency in a skill, a creature can still make ability "
        "checks involving",
    ),
    (
        "skill.without_b",
        SKILL_B,
        SUB,
        "that skill but doesn’t add its Proficiency Bonus.",
    ),
    (
        "skill.example",
        SKILL_B,
        SUP,
        "For example, if a character tries to climb a cliff, the GM might ask "
        "for a Strength (Athletics) check. If the character has Athletics "
        "proficiency, the character adds their Proficiency Bonus to the "
        "Strength check. If the character lacks that proficiency, they make "
        "the check without adding their Proficiency Bonus.",
    ),
    # 9b012d75 - Skill List
    (
        "list.skills_table",
        SKILL_LIST,
        SUB,
        "The skills are shown on the Skills table, which notes example uses "
        "for each skill proficiency as well as the ability check the skill "
        "most often applies to.",
    ),
    # 91e1341f - Determining Skills
    (
        "determining.sources",
        DETERMINING,
        SUB,
        "A character’s starting skill proficiencies are determined at "
        "character creation, and a monster’s skill proficiencies appear "
        "in its stat block.",
    ),
    # 6b6df866 - Saving Throw Proficiencies
    (
        "saves.bonus",
        SAVES,
        SUB,
        "Proficiency in a saving throw lets a character add their Proficiency "
        "Bonus to saves that use a particular ability.",
    ),
    (
        "saves.example",
        SAVES,
        SUP,
        "For example, proficiency in Wisdom saves lets you add your "
        "Proficiency Bonus to your Wisdom saves.",
    ),
    (
        "saves.monsters",
        SAVES,
        SUB,
        "Some monsters also have saving throw proficiencies, as noted in their "
        "stat blocks.",
    ),
    (
        "saves.class_minimum",
        SAVES,
        SUB,
        "Each class gives proficiency in at least two saving throws, "
        "representing that class’s training in evading or resisting "
        "certain threats.",
    ),
    (
        "saves.wizard_example",
        SAVES,
        SUP,
        "Wizards, for example, are proficient in Intelligence and Wisdom "
        "saves; they train to resist mental assault.",
    ),
    # b1d1ef1a / 3576be8e / e9d9f35f - Equipment Proficiencies
    (
        "equipment.sources",
        EQUIPMENT,
        SUB,
        "A character gains proficiency with various weapons and tools from "
        "their class and background.",
    ),
    (
        "equipment.two_categories",
        EQUIPMENT,
        SUP,
        "There are two categories of equipment proficiency:",
    ),
    (
        "weapon.anyone",
        WEAPONS,
        SUB,
        "Anyone can wield a weapon, but proficiency makes you better at "
        "wielding it.",
    ),
    (
        "weapon.attack_rolls",
        WEAPONS,
        SUB,
        "If you have proficiency with a weapon, you add your Proficiency Bonus "
        "to attack rolls you make with it.",
    ),
    (
        "tool.checks",
        TOOLS,
        SUB,
        "If you have proficiency with a tool, you can add your Proficiency "
        "Bonus to any ability check you make that uses the tool.",
    ),
    (
        "tool.advantage",
        TOOLS,
        SUB,
        "If you have proficiency in the skill that’s also used with that "
        "check, you have Advantage on the check too.",
    ),
    (
        "tool.both",
        TOOLS,
        SUP,
        "This means you can benefit from both skill proficiency and tool "
        "proficiency on the same ability check.",
    ),
)

_DISPOSITION = {
    SUB: SemanticDisposition.SUBSTANTIVE,
    SUP: SemanticDisposition.SUPPORTING_AUTHORITY,
    NON: SemanticDisposition.NON_MECHANICAL,
}
_RATIONALE = {
    SUB: "states a rule of this section that the representation carries",
    SUP: "identifies, exemplifies or contextualizes a rule stated elsewhere "
    "in this section",
    NON: "flavour prose that neither states nor contextualizes a mechanic",
}

SPANS: dict[str, SemanticSpan] = {}
PROPOSED: list[ProposedSpan] = []
for _row in CLAUSES:
    _key, _leaf, _kind, _text = _row[0], _row[1], _row[2], _row[3]
    _anchor = _row[4] if len(_row) > 4 else ""
    _content = LEAF_BY_ID[_leaf].content
    assert _content.count(_anchor + _text) == 1, (
        _key,
        _content.count(_anchor + _text),
    )
    _start = _content.index(_anchor + _text) + len(_anchor)
    _span = SemanticSpan(
        span_id=derive_span_id(_leaf, _start, _start + len(_text)),
        leaf_id=_leaf,
        char_start=_start,
        char_end=_start + len(_text),
        disposition=_DISPOSITION[_kind],
        review_state=ReviewState.PROPOSED,
        non_mechanical_reason_code="flavor_setting" if _kind == NON else None,
    )
    assert _key not in SPANS, _key
    SPANS[_key] = _span
    PROPOSED.append(
        ProposedSpan(span=_span, origin=ORIGIN, rationale=_RATIONALE[_kind])
    )

assert len(SPANS) == 47, len(SPANS)
#: Levels 17-30 really are outside the table container, and the four later rows
#: really are in ``f848a0fb``. Asserted rather than trusted to the note.
assert (
    LEAF_BY_ID[LATER_ROWS].container_path == LEAF_BY_ID[MAIN].container_path
), LEAF_BY_ID[LATER_ROWS].container_path
assert (
    LEAF_BY_ID[CELL_UPTO4].container_path != LEAF_BY_ID[LATER_ROWS].container_path
), LEAF_BY_ID[CELL_UPTO4].container_path


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
# The eight Proficiency Bonus bands
# ---------------------------------------------------------------------------
# Four printed rows in the table container, four in ``f848a0fb``. The opening
# row states "Up to 4", which names no lower bound, so the band is open below
# rather than starting at 1 - ``minimum=None`` is the source's own claim, not a
# default.
BANDS: tuple[tuple[int, int | None, int, tuple[str, ...]], ...] = (
    (2, None, 4, ("cell.upto4", "cell.p2")),
    (3, 5, 8, ("cell.5_8", "cell.p3")),
    (4, 9, 12, ("cell.9_12", "cell.p4")),
    (5, 13, 16, ("cell.13_16", "cell.p5")),
    (6, 17, 20, ("later.17_20",)),
    (7, 21, 24, ("later.21_24",)),
    (8, 25, 28, ("later.25_28",)),
    (9, 29, 30, ("later.29_30",)),
)
assert len(BANDS) == 8, len(BANDS)
BAND_FACTS = tuple(
    ProficiencyBonusBandFact(bonus=b, minimum=lo, maximum=hi) for b, lo, hi, _ in BANDS
)

TOOL_ADVANTAGE = AdvantageFact(
    state=AdvantageState.ADVANTAGE,
    roll=RollSpec(actor=RollActor.SUBJECT, context=RollContext.ABILITY_CHECK),
)

# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------
# ``NO_USE`` is the reducible-but-unmodelled case: the meaning could be
# structured, and no identified code-owned use in play, explanation or
# correction needs a separate field for it today. It is never spelled as an
# irreducibility reason, which is the relabelling ADR-005d forbids.
NO_USE = "no_identified_structured_use"
#: The one genuinely irreducible clause here: the source hands the decision to
#: the GM in its own words.
GM = "gamemaster_latitude"

#: ``(component_key, handling, irreducibility, retention, bound clause keys)``.
COMPONENTS: tuple[
    tuple[str, ComponentHandling, str | None, str | None, tuple[str, ...]], ...
] = (
    (
        "proficiency_bonus_table",
        ComponentHandling.STRUCTURED,
        None,
        None,
        (),
    ),
    (
        "proficiency_bonus_basis",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("main.all_creatures", "main.character_levels", "main.monster_cr"),
    ),
    (
        "proficiency_bonus_application",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("main.d20_test", "main.spells"),
    ),
    (
        "bonus_does_not_stack",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("stack.once", "stack.scaling", "stack.once_each"),
    ),
    (
        "skill_relevance_sources",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("skill.sources",),
    ),
    # Split from ``skill_relevance_sources`` on purpose. A component states
    # exactly one reason why its meaning is prose, and these two clauses do not
    # share one: the first is reducible and unmodelled, the second is the GM's
    # call by the source's own words.
    (
        "skill_relevance_judgment",
        ComponentHandling.PROSE_BOUND,
        GM,
        None,
        ("skill.gm_say",),
    ),
    (
        "skill_proficiency_application",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("skill.proficient", "skill.without_a", "skill.without_b"),
    ),
    (
        "skill_list",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("list.skills_table",),
    ),
    (
        "determining_skills",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("determining.sources",),
    ),
    (
        "saving_throw_proficiency",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("saves.bonus", "saves.monsters", "saves.class_minimum"),
    ),
    (
        "equipment_proficiency",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("equipment.sources",),
    ),
    (
        "weapon_proficiency",
        ComponentHandling.PROSE_BOUND,
        None,
        NO_USE,
        ("weapon.anyone", "weapon.attack_rolls"),
    ),
    # MIXED: the advantage is typed, and the condition that triggers it - "the
    # skill that's also used with that check" - is not in any closed
    # applicability vocabulary, so the clause stays exact governing prose and
    # the fact claims it CONTEXTUAL rather than displacing it.
    (
        "tool_proficiency",
        ComponentHandling.MIXED,
        None,
        NO_USE,
        ("tool.checks", "tool.advantage"),
    ),
)

_FACTS = {
    "proficiency_bonus_table": BAND_FACTS,
    "tool_proficiency": (TOOL_ADVANTAGE,),
}

COMPONENT_DRAFTS: list[ComponentDraft] = []
BINDINGS: list[ProseBindingDraft] = []
for ckey, handling, irreducible, retention, bound in COMPONENTS:
    COMPONENT_DRAFTS.append(
        ComponentDraft(
            record_key=RECORD,
            semantic_key=ckey,
            handling=handling,
            irreducibility_reason_code=irreducible,
            prose_retention_reason_code=retention,
            facts=_FACTS.get(ckey, ()),
        )
    )
    for clause in bound:
        chunk_id, cstart, cend = _bind(clause)
        BINDINGS.append(
            ProseBindingDraft(
                component_key=ckey,
                record_key=RECORD,
                chunk_id=chunk_id,
                span_id=sid(clause),
                chunk_char_start=cstart,
                chunk_char_end=cend,
                irreducibility_reason_code=irreducible,
                prose_retention_reason_code=retention,
            )
        )
assert len(COMPONENT_DRAFTS) == 13, len(COMPONENT_DRAFTS)
assert len(BINDINGS) == 23, len(BINDINGS)

# ---------------------------------------------------------------------------
# References
# ---------------------------------------------------------------------------
# A reference is authored exactly where the printed pointer names a **record**
# under a key convention the accepted batches already committed. Both of these
# do: the source says (see "Rules Glossary") in its own words, and the glossary
# scope is the one the seven accepted batches resolve into.
#
# The section prints three further pointers - the Skills table, "Actions" later
# in "Playing the Game", and "Character Creation". None of them names a record:
# a table and two section titles have no record key under any convention this
# build has committed, and minting one here would pin a naming decision the
# Owner has not made and silently widen the pilot. Their wording is preserved
# verbatim inside the bound governing prose, and the review packet carries the
# concrete recommendation for each.
REFERENCES = (
    ReferenceDraft(
        from_record_key=RECORD,
        from_component_key="proficiency_bonus_basis",
        source_text="Challenge Rating",
        scope_key=GLOSSARY_SCOPE,
        target_record_key="glossary.challenge_rating",
    ),
    ReferenceDraft(
        from_record_key=RECORD,
        from_component_key="bonus_does_not_stack",
        source_text="Expertise",
        scope_key=GLOSSARY_SCOPE,
        target_record_key="glossary.expertise",
    ),
)
REFERENCE_SPANS = {
    "glossary.challenge_rating": "main.monster_cr",
    "glossary.expertise": "stack.expertise",
}

# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------
PROVENANCE: list[ProvenanceClaim] = []

# Every band fact claims PRIMARY on **each** cell it was read from. A row is
# two cells - the level band and the bonus - and a claim to only one of them
# would certify the half nobody looked at.
for fact, (_b, _lo, _hi, clause_keys) in zip(BAND_FACTS, BANDS, strict=True):
    for clause in clause_keys:
        PROVENANCE.append(
            ProvenanceClaim(
                ProvenanceTargetKind.FACT,
                fact_target_key(RECORD, "proficiency_bonus_table", fact),
                sid(clause),
                ProvenanceRole.PRIMARY,
            )
        )

PROVENANCE.append(
    ProvenanceClaim(
        ProvenanceTargetKind.FACT,
        fact_target_key(RECORD, "tool_proficiency", TOOL_ADVANTAGE),
        sid("tool.advantage"),
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
SUPPORTING_CLAIMS: tuple[tuple[str, str], ...] = (
    ("main.table_pointer", "proficiency_bonus_table"),
    ("main.caption", "proficiency_bonus_table"),
    ("later.header", "proficiency_bonus_table"),
    ("stack.example", "bonus_does_not_stack"),
    ("stack.expertise", "bonus_does_not_stack"),
    ("skill.definition", "skill_relevance_sources"),
    ("skill.example", "skill_proficiency_application"),
    ("saves.example", "saving_throw_proficiency"),
    ("saves.wizard_example", "saving_throw_proficiency"),
    ("equipment.two_categories", "equipment_proficiency"),
    ("tool.both", "tool_proficiency"),
)
for clause, ckey in SUPPORTING_CLAIMS:
    PROVENANCE.append(
        ProvenanceClaim(
            ProvenanceTargetKind.COMPONENT,
            (RECORD, ckey),
            sid(clause),
            ProvenanceRole.CONTEXTUAL,
        )
    )

for ref in REFERENCES:
    PROVENANCE.append(
        ProvenanceClaim(
            ProvenanceTargetKind.REFERENCE,
            reference_target_key(ref),
            sid(REFERENCE_SPANS[ref.target_record_key]),
            ProvenanceRole.CONTEXTUAL,
        )
    )

PROVENANCE.append(
    ProvenanceClaim(
        ProvenanceTargetKind.RECORD,
        (RECORD,),
        sid("main.all_creatures"),
        ProvenanceRole.CONTEXTUAL,
    )
)

DRAFT = RepresentationDraft(
    records=(RecordDraft(semantic_key=RECORD, kind=RecordKind.GENERAL_RULE),),
    components=tuple(COMPONENT_DRAFTS),
    prose_bindings=tuple(BINDINGS),
    relationships=(),
    references=REFERENCES,
    provenance=tuple(PROVENANCE),
)

# ---------------------------------------------------------------------------
# The review unit
# ---------------------------------------------------------------------------
# ONE SECTION unit over all thirty represented leaves. Every table row is an
# expected rule, so an omitted row is a reported violation rather than an
# unnoticed gap - which is the whole reason the later-rows paragraph could not
# be left to a TABLE unit over the table container.
BAND_RULES = tuple(
    ExpectedRule(
        RECORD,
        "proficiency_bonus_table",
        ProficiencyBonusBandFact.FAMILY.value,
        tuple(sid(c) for c in clause_keys),
    )
    for _b, _lo, _hi, clause_keys in BANDS
)
PROSE_RULES = tuple(
    ExpectedRule(RECORD, ckey, None, tuple(sid(c) for c in clauses))
    for ckey, clauses in (
        (
            "proficiency_bonus_basis",
            ("main.all_creatures", "main.character_levels", "main.monster_cr"),
        ),
        ("proficiency_bonus_application", ("main.d20_test", "main.spells")),
        ("bonus_does_not_stack", ("stack.once",)),
        ("bonus_does_not_stack", ("stack.scaling", "stack.once_each")),
        ("skill_relevance_sources", ("skill.sources",)),
        ("skill_relevance_judgment", ("skill.gm_say",)),
        (
            "skill_proficiency_application",
            ("skill.proficient", "skill.without_a", "skill.without_b"),
        ),
        ("skill_list", ("list.skills_table",)),
        ("determining_skills", ("determining.sources",)),
        (
            "saving_throw_proficiency",
            ("saves.bonus", "saves.monsters", "saves.class_minimum"),
        ),
        ("equipment_proficiency", ("equipment.sources",)),
        ("weapon_proficiency", ("weapon.anyone", "weapon.attack_rolls")),
        ("tool_proficiency", ("tool.checks", "tool.advantage")),
    )
)
ADVANTAGE_RULE = ExpectedRule(
    RECORD,
    "tool_proficiency",
    AdvantageFact.FAMILY.value,
    (sid("tool.advantage"),),
)

UNIT = ReviewUnit(
    unit_id="proficiency-1-section",
    kind=ReviewUnitKind.SECTION,
    leaf_ids=SECTION_LEAVES,
    expected_rules=BAND_RULES + PROSE_RULES + (ADVANTAGE_RULE,),
    supporting_groups=(
        SupportingGroup(
            (CELL_LEVEL_OR_CR, CELL_BONUS),
            RECORD,
            "proficiency_bonus_table",
        ),
        SupportingGroup((LABEL_WEAPONS,), RECORD, "weapon_proficiency"),
        SupportingGroup((LABEL_TOOLS,), RECORD, "tool_proficiency"),
    ),
    excluded_groups=(
        ExcludedGroup(
            HEADINGS,
            "section and entry headings: each names the rules stated below it "
            "and states no rule itself",
        ),
    ),
)
assert len(UNIT.expected_rules) == 22, len(UNIT.expected_rules)

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

units = review_unit_violations(
    (UNIT,), DRAFT, SEMANTIC_POLICY_VERSION, LEDGER.spans
)
assert units == [], units

standalone = list(validate_representation(DRAFT, LEDGER, CORPUS))
#: The only findings this batch may produce standalone are its two cross-batch
#: citations, whose glossary entries no accepted batch has minted yet. Asserted
#: as an exact tuple so a third finding of any kind fails here.
EXPECTED_FINDINGS = tuple(
    sorted(
        f"reference {GLOSSARY_SCOPE}:{ref.source_text!r}: unknown target record "
        f"{ref.target_record_key}"
        for ref in REFERENCES
    )
)
assert tuple(sorted(standalone)) == EXPECTED_FINDINGS, standalone

#: Dropping any one band row must be *reported*, not absorbed. Proved on the
#: later-rows paragraph, which is the row set a table-shaped review would have
#: missed entirely.
_short_facts = tuple(f for f in BAND_FACTS if f.minimum != 29)
_short_draft = RepresentationDraft(
    records=DRAFT.records,
    components=tuple(
        ComponentDraft(
            record_key=c.record_key,
            semantic_key=c.semantic_key,
            handling=c.handling,
            irreducibility_reason_code=c.irreducibility_reason_code,
            prose_retention_reason_code=c.prose_retention_reason_code,
            facts=_short_facts if c.semantic_key == "proficiency_bonus_table" else c.facts,
        )
        for c in DRAFT.components
    ),
    prose_bindings=DRAFT.prose_bindings,
    relationships=DRAFT.relationships,
    references=DRAFT.references,
    provenance=DRAFT.provenance,
)
_dropped = review_unit_violations(
    (UNIT,), _short_draft, SEMANTIC_POLICY_VERSION, LEDGER.spans
)
assert _dropped, "dropping the 29-30 band produced no violation"
assert all("proficiency_bonus_table" in f for f in _dropped), _dropped

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
        f"{ORIGIN} (CRD Issue 5d batch {BATCH_ID}, representation schema 13)"
    ),
    proposal_schema_version=PROPOSAL_SCHEMA_VERSION_2,
    proposed_review_units=(UNIT,),
)
payload = proposal_payload(PROPOSAL)
identity = proposal_identity(PROPOSAL)

#: Read back off the object: ``span_payload`` omits review state on purpose, so
#: the artifact cannot carry this claim and the object must. Nothing here is
#: accepted.
assert {p.span.review_state for p in PROPOSAL.proposed_spans} == {
    ReviewState.PROPOSED
}
#: Disjoint from the seven accepted batches: this batch re-accepts nothing and
#: touches none of their leaves.
_accepted_spans = {s.span_id for s in PRIOR.oracle.spans}
_accepted_leaves = {s.leaf_id for s in PRIOR.oracle.spans}
assert not (_accepted_spans & {s.span_id for s in LEDGER.spans})
assert not (_accepted_leaves & set(SECTION_LEAVES))

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
print(f"leaves           {len(SECTION_LEAVES)} represented, 1 excluded by 5c")
print(f"spans            {len(SPANS)}")
print(f"components       {len(COMPONENT_DRAFTS)}   bindings {len(BINDINGS)}")
print(f"bands            {len(BAND_FACTS)}   expected rules {len(UNIT.expected_rules)}")
print(f"provenance       {len(PROVENANCE)}   references {len(REFERENCES)}")
print(f"partition        {len(partition)} findings")
print(f"review units     {len(units)} findings")
print(f"representation   {len(standalone)} findings (both unresolved citations)")
for finding in sorted(standalone):
    print(f"  - {finding}")
