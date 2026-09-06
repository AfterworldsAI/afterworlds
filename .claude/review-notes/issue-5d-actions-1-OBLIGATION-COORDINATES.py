"""Bound-source coordinates for the CRD Issue 5d `actions-1` obligation ledger.

DISCOVERY EVIDENCE, not a generator. This script resolves every obligation in
`issue-5d-actions-1-SCHEMA-STOP-CHECKPOINT.md` to exact `(leaf_id, char_start,
char_end)` coordinates in the bound CRD Issue 5c release, and fails loudly if a
quoted phrase is not present verbatim in the leaf it claims.

It also measures coverage as a **full partition** of every non-heading leaf:
every character is either claimed by an obligation or reported as an unassigned
run, and an unassigned run containing a word character fails the run rather than
being counted and passed over.

It emits no proposal, no audit, and no representation. It never writes to
`oracles/`, never calls `accept_proposal`, never touches the database, and never
publishes or activates anything. The batch payload is deliberately absent: the
only thing produced here is coordinates and the source text at them, so the
ledger's quotations are checkable rather than trusted.

Run:  venv/Scripts/python .claude/review-notes/issue-5d-actions-1-OBLIGATION-COORDINATES.py

Determinism: the repository root is derived from this file's own location, every
input is a committed file beneath it, and no absolute checkout path enters the
output. Output is UTF-8 with LF endings.

Lint: `black` clean; `ruff check` reports only E501 on the ledger rows, where a
quoted phrase must stay on one line because splitting it would change the string
being matched against the source. Review-note scripts are outside the repository
gates' scope (`ruff check src/ tests/`, `mypy files = ["src"]`), as the accepted
`issue-5d-hazards-1-schema5-REGEN-generator.py` is.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_PATH = REPO / ".claude/review-notes/issue-5d-actions-1-obligation-coordinates.json"
SOURCE_PDF = REPO / "docs/sources/DnD5_5e_SRD_CC_v5_2_1.pdf"
PACKAGE_ROOT = REPO / "src/afterworlds"
for _required in (SOURCE_PDF, PACKAGE_ROOT):
    if not _required.exists():  # pragma: no cover - guard
        raise SystemExit(f"missing required input: {_required}")

sys.path.insert(0, str(REPO / "src"))

from afterworlds.ingestion.corpus.pipeline import build_candidate  # noqa: E402
from afterworlds.ingestion.corpus.policy import exclusion_reason_for  # noqa: E402
from afterworlds.pipeline.retrieval.config import RetrievalMemoryConfig  # noqa: E402

import afterworlds  # noqa: E402  # isort: skip

assert Path(afterworlds.__file__).resolve().parent == PACKAGE_ROOT.resolve()

SOURCE_SHA256 = "8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87"  # pragma: allowlist secret
RELEASE_VERSION = "5.2.1-corpus.36b786d8-fa2"
PACKAGE_UUID = "4458fa10-4a66-5e0e-9ecc-ea37530ad2b4"

CAND = build_candidate(SOURCE_PDF, retrieval_config=RetrievalMemoryConfig())
assert CAND.authoritative_source_hash == SOURCE_SHA256, CAND.authoritative_source_hash
assert CAND.release_version == RELEASE_VERSION, CAND.release_version
assert CAND.package_uuid == PACKAGE_UUID, CAND.package_uuid

LEDGER = CAND.ledger
LABELS = {c.container_id: c.label for c in LEDGER.containers}
CONTAINERS = {c.container_id: c for c in LEDGER.containers}
REPRESENTED = {
    leaf.leaf_id for leaf in LEDGER.leaves if exclusion_reason_for(leaf, LABELS) is None
}


def _ancestry(container_id: str) -> list[str]:
    out, cur = [], CONTAINERS.get(container_id)
    while cur:
        out.append(cur.container_id)
        cur = CONTAINERS.get(cur.parent_id) if cur.parent_id else None
    return out


RULES_DEFINITIONS = next(
    c.container_id for c in LEDGER.containers if c.label == "Rules Definitions"
)
ENTRY_BY_LABEL = {
    c.label: c.container_id
    for c in LEDGER.containers
    if c.container_type == "entry" and RULES_DEFINITIONS in _ancestry(c.container_id)
}

_by_container: dict[str, list] = defaultdict(list)
for _leaf in LEDGER.leaves:
    if _leaf.leaf_id not in REPRESENTED:
        continue
    for _cid in _leaf.container_path:
        _by_container[_cid].append(_leaf)
for _group in _by_container.values():
    _group.sort(key=lambda x: (x.page_index, x.char_start))

# --- Boundary, re-derived rather than asserted -----------------------------
ACTION_LABELS = sorted(lab for lab in ENTRY_BY_LABEL if lab.endswith(" [Action]"))
UMBRELLA = _by_container[ENTRY_BY_LABEL["Action"]]
NAMED = [lab.split(" [")[0] for lab in ACTION_LABELS]
_umbrella_names = " ".join(leaf.content for leaf in UMBRELLA[4:8])
for _n in NAMED:
    assert _n in _umbrella_names, f"{_n} not named by the umbrella list"
assert len(ACTION_LABELS) == 12, ACTION_LABELS

BATCH = {lab: _by_container[ENTRY_BY_LABEL[lab]] for lab in [*ACTION_LABELS, "Action"]}
assert sum(len(v) for v in BATCH.values()) == 92, sum(len(v) for v in BATCH.values())

# Curly punctuation the PDF prints, normalized 1:1 so offsets are preserved.
_FOLD = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def fold(text: str) -> str:
    return text.translate(_FOLD)


# ---------------------------------------------------------------------------
# The ledger: (obligation id, entry label, leaf index, quoted phrase)
#
# A phrase is matched against the *folded* leaf content, so a straight quote in
# the table finds the PDF's curly one at the same offset. A phrase that is not
# present, or present more than once in its leaf, is a hard error: an ambiguous
# coordinate is not a coordinate.
# ---------------------------------------------------------------------------

#: A phrase given as ``(phrase, "last")`` selects the final occurrence in its
#: leaf. Used only where the source itself repeats the wording inside one leaf:
#: a table's title trails the paragraph that introduces it, so "Influence
#: Checks" and "Search" each appear twice. Selecting the trailing occurrence is
#: a statement about which one the obligation is, not a loosening of the
#: uniqueness rule — every other phrase must still be unique in its leaf.
LEDGER_SPEC: list[tuple[str, str, int, str | tuple[str, str]]] = [
    # --- Action (umbrella) --------------------------------------------------
    ("A1", "Action", 1, "On your turn, you can take one action."),
    (
        "A2",
        "Action",
        1,
        "Choose which action to take from those below or from the special actions provided by your features.",
    ),
    ("A3", "Action", 2, "See also"),
    ("A3", "Action", 3, '"Playing the Game" ("Actions").'),
    ("A4", "Action", 3, "These actions are defined elsewhere in this glossary:"),
    ("A4", "Action", 4, "Attack Dash Disengage"),
    ("A4", "Action", 5, "Dodge Help Hide"),
    ("A4", "Action", 6, "Influence Magic Ready"),
    ("A4", "Action", 7, "Search Study Utilize"),
    # --- Dash ---------------------------------------------------------------
    ("D8", "Dash [Action]", 1, "When you take the Dash action,"),
    ("D1", "Dash [Action]", 1, "you gain extra movement"),
    (
        "D2",
        "Dash [Action]",
        1,
        "The increase equals your Speed after applying any modifiers.",
    ),
    ("D3", "Dash [Action]", 1, "for the current turn"),
    ("D4", "Dash [Action]", 1, "With a"),
    ("D4", "Dash [Action]", 2, "Speed of 30 feet, for example, you can move up to"),
    (
        "D4",
        "Dash [Action]",
        3,
        "60 feet on your turn if you Dash. If your Speed of 30 feet is reduced to 15 feet, you can move up to 30 feet this turn if you Dash.",
    ),
    (
        "D5",
        "Dash [Action]",
        3,
        "If you have a special speed, such as a Fly Speed or Swim Speed, you can use that speed instead of your",
    ),
    ("D5", "Dash [Action]", 4, "Speed when you take this action."),
    ("D6", "Dash [Action]", 4, "You choose which"),
    ("D6", "Dash [Action]", 5, "speed to use each time you take it."),
    ("D7", "Dash [Action]", 6, "See also"),
    ("D7", "Dash [Action]", 7, '"Speed."'),
    # --- Disengage ----------------------------------------------------------
    (
        "E1",
        "Disengage [Action]",
        1,
        "your movement doesn't provoke Opportunity Attacks",
    ),
    ("E2", "Disengage [Action]", 1, "for the rest of the current turn"),
    ("E3", "Disengage [Action]", 1, "If you take the Disengage action,"),
    # --- Dodge --------------------------------------------------------------
    ("G1", "Dodge [Action]", 1, "any attack roll made against you has Disadvantage"),
    ("G2", "Dodge [Action]", 1, "if you can see the attacker"),
    ("G3", "Dodge [Action]", 1, "you make Dexterity saving throws with Advantage"),
    ("G4", "Dodge [Action]", 1, "until the start of your next turn"),
    (
        "G5",
        "Dodge [Action]",
        1,
        "You lose these benefits if you have the Incapacitated condition or if your Speed is 0.",
    ),
    (
        "G6",
        "Dodge [Action]",
        1,
        "If you take the Dodge action, you gain the following benefits:",
    ),
    ("G7", "Dodge [Action]", 1, ", and "),
    # --- Help ---------------------------------------------------------------
    (
        "H1",
        "Help [Action]",
        1,
        "When you take the Help action, you do one of the following.",
    ),
    ("H1", "Help [Action]", 2, "Assist an Ability Check."),
    ("H1", "Help [Action]", 5, "Assist an Attack Roll."),
    (
        "H2",
        "Help [Action]",
        3,
        "Choose one of your skill or tool proficiencies and one ally who is near",
    ),
    (
        "H2",
        "Help [Action]",
        4,
        "enough for you to assist verbally or physically when they make an ability check.",
    ),
    (
        "H3",
        "Help [Action]",
        4,
        "That ally has Advantage on the next ability check they make with the chosen skill or tool.",
    ),
    (
        "H4",
        "Help [Action]",
        4,
        "This benefit expires if the ally doesn't use it before the start of your next turn.",
    ),
    (
        "H5",
        "Help [Action]",
        4,
        "The GM has final say on whether your assistance is possible.",
    ),
    (
        "H6",
        "Help [Action]",
        6,
        "You momentarily distract an enemy within 5 feet of you, giving Advantage to the next attack roll by one of your allies against that enemy.",
    ),
    ("H7", "Help [Action]", 6, "This benefit expires at the start of your next turn."),
    # --- Hide ---------------------------------------------------------------
    ("I1", "Hide [Action]", 1, "you must succeed on a DC 15 Dexterity (Stealth) check"),
    (
        "I2",
        "Hide [Action]",
        1,
        "while you're Heavily Obscured or behind Three-Quarters Cover or Total Cover",
    ),
    ("I3", "Hide [Action]", 1, "and you must be out of any enemy's line of sight"),
    (
        "I4",
        "Hide [Action]",
        1,
        "if you can see a creature, you can discern whether it can see you",
    ),
    (
        "I5",
        "Hide [Action]",
        1,
        "On a successful check, you have the Invisible condition while hidden.",
    ),
    (
        "I6",
        "Hide [Action]",
        1,
        "Make note of your check's total, which is the DC for a creature to find you with a Wisdom (Perception) check.",
    ),
    (
        "I7",
        "Hide [Action]",
        1,
        "You stop being hidden immediately after any of the following occurs: you make a sound louder than a whisper, an enemy finds you, you make an attack roll, or you cast a spell with a Verbal component.",
    ),
    ("I9", "Hide [Action]", 1, "With the Hide action, you try to hide yourself."),
    ("I10", "Hide [Action]", 1, " To do so, "),
    # --- Influence ----------------------------------------------------------
    (
        "J1",
        "Influence [Action]",
        1,
        "With the Influence action, you urge a monster to do something. Describe or roleplay how you're communicating with the monster. Are you trying to deceive, intimidate, amuse, or gently persuade?",
    ),
    (
        "J2",
        "Influence [Action]",
        1,
        "The GM then determines whether the monster feels willing, unwilling, or hesitant due to your interaction; this determination establishes whether an ability check is necessary, as explained below.",
    ),
    ("J3", "Influence [Action]", 2, "Willing."),
    (
        "J3",
        "Influence [Action]",
        3,
        "If your urging aligns with the monster's desires, no ability check is necessary; the monster fulfills your request in a way it prefers.",
    ),
    ("J4", "Influence [Action]", 4, "Unwilling."),
    (
        "J4",
        "Influence [Action]",
        5,
        "If your urging is repugnant to the monster or counter to its alignment, no ability check is necessary; it doesn't comply.",
    ),
    (
        "J5",
        "Influence [Action]",
        7,
        "which is affected by the monster's attitude: Indifferent, Friendly, or Hostile, each of which is defined in this glossary.",
    ),
    ("J6", "Influence [Action]", 6, "Hesitant."),
    (
        "J6",
        "Influence [Action]",
        7,
        "If you urge the monster to do something that it is hesitant to do, you must make an ability check,",
    ),
    (
        "J7",
        "Influence [Action]",
        7,
        "The Influence Checks table suggests which ability check to make based on how you're interacting with the monster.",
    ),
    ("J7", "Influence [Action]", 7, ("Influence Checks", "last")),
    ("J7", "Influence [Action]", 8, "Ability Check"),
    ("J7", "Influence [Action]", 9, "Interaction"),
    ("J7", "Influence [Action]", 10, "Charisma (Deception)"),
    ("J7", "Influence [Action]", 11, "Deceiving a monster that understands you"),
    ("J7", "Influence [Action]", 12, "Charisma (Intimidation)"),
    ("J7", "Influence [Action]", 13, "Intimidating a monster"),
    ("J7", "Influence [Action]", 14, "Charisma (Performance)"),
    ("J7", "Influence [Action]", 15, "Amusing a monster"),
    ("J7", "Influence [Action]", 16, "Charisma (Persuasion)"),
    ("J7", "Influence [Action]", 17, "Persuading a monster that understands you"),
    ("J7", "Influence [Action]", 18, "Wisdom (Animal Handling)"),
    ("J7", "Influence [Action]", 19, "Gently coaxing a Beast or Monstrosity"),
    ("J8", "Influence [Action]", 7, "The GM chooses the check,"),
    (
        "J9",
        "Influence [Action]",
        7,
        "which has a default DC equal to 15 or the monster's Intelligence score, whichever is higher.",
    ),
    (
        "J10",
        "Influence [Action]",
        7,
        "On a successful check, the monster does as urged.",
    ),
    (
        "J11",
        "Influence [Action]",
        7,
        "On a failed check, you must wait 24 hours (or a duration set by the GM) before urging it in the same way again.",
    ),
    # --- Magic --------------------------------------------------------------
    (
        "K1",
        "Magic [Action]",
        1,
        "When you take the Magic action, you cast a spell that has a casting time of an action or use a feature or magic item that requires a Magic action to be activated.",
    ),
    (
        "K2",
        "Magic [Action]",
        2,
        "If you cast a spell that has a casting time of 1 minute or longer, you must take the Magic action on each turn of that casting,",
    ),
    ("K3", "Magic [Action]", 2, "and you must maintain Concentration while you do so."),
    (
        "K4",
        "Magic [Action]",
        2,
        "If your Concentration is broken, the spell fails, but you don't expend a spell slot.",
    ),
    ("K5", "Magic [Action]", 3, "See also"),
    ("K5", "Magic [Action]", 4, '"Concentration."'),
    # --- Ready --------------------------------------------------------------
    (
        "L1",
        "Ready [Action]",
        1,
        "You take the Ready action to wait for a particular circumstance before you act. To do so, you take this action on your turn,",
    ),
    (
        "L2",
        "Ready [Action]",
        1,
        "which lets you act by taking a Reaction before the start of your next turn.",
    ),
    (
        "L3",
        "Ready [Action]",
        1,
        "First, you decide what perceivable circumstance will trigger your Reaction.",
    ),
    (
        "L4",
        "Ready [Action]",
        1,
        "Then, you choose the action you will take in response to that trigger, or you choose to move up to your Speed in response to it.",
    ),
    ("L5", "Ready [Action]", 1, 'Examples include "If the cultist steps on the'),
    (
        "L5",
        "Ready [Action]",
        2,
        'trapdoor, I\'ll pull the lever that opens it," and "If the zombie steps next to me, I move away."',
    ),
    (
        "L6",
        "Ready [Action]",
        2,
        "When the trigger occurs, you can either take your Reaction right after the trigger finishes or ignore the trigger.",
    ),
    (
        "L7",
        "Ready [Action]",
        2,
        "When you Ready a spell, you cast it as normal (expending any resources used to cast it) but hold its energy, which you release with your Reaction when the trigger occurs.",
    ),
    (
        "L8",
        "Ready [Action]",
        2,
        "To be readied, a spell must have a casting time of an action,",
    ),
    (
        "L9",
        "Ready [Action]",
        2,
        "and holding on to the spell's magic requires Concentration, which you can maintain up to the start of your next turn.",
    ),
    (
        "L10",
        "Ready [Action]",
        2,
        "If your Concentration is broken, the spell dissipates without taking effect.",
    ),
    # --- Search -------------------------------------------------------------
    (
        "M1",
        "Search [Action]",
        1,
        "When you take the Search action, you make a Wisdom check",
    ),
    ("M2", "Search [Action]", 1, "to discern something that isn't obvious."),
    (
        "M3",
        "Search [Action]",
        1,
        "The Search table suggests which skills are applicable when you take this action, depending on what you're trying to detect.",
    ),
    ("M3", "Search [Action]", 1, ("Search", "last")),
    ("M3", "Search [Action]", 2, "Skill"),
    ("M3", "Search [Action]", 3, "Thing to Detect"),
    ("M3", "Search [Action]", 4, "Insight"),
    ("M3", "Search [Action]", 5, "Creature's state of mind"),
    ("M3", "Search [Action]", 6, "Medicine"),
    ("M3", "Search [Action]", 7, "Creature's ailment or cause of death"),
    ("M3", "Search [Action]", 8, "Perception"),
    ("M3", "Search [Action]", 9, "Concealed creature or object"),
    ("M3", "Search [Action]", 10, "Survival"),
    ("M3", "Search [Action]", 11, "Tracks or food"),
    # --- Study --------------------------------------------------------------
    (
        "N1",
        "Study [Action]",
        1,
        "When you take the Study action, you make an Intelligence check to study your memory, a book, a clue, or another source of knowledge and call to mind an important piece of information about it.",
    ),
    (
        "N2",
        "Study [Action]",
        1,
        "The Areas of Knowledge table suggests which skills are applicable to various areas of knowledge.",
    ),
    ("N2", "Study [Action]", 2, "Areas of Knowledge"),
    ("N2", "Study [Action]", 3, "Skill"),
    ("N2", "Study [Action]", 4, "Areas"),
    ("N2", "Study [Action]", 5, "Arcana"),
    (
        "N2",
        "Study [Action]",
        6,
        "Spells, magic items, eldritch symbols, magical traditions, planes of existence, and certain creatures (Aberrations, Constructs, Elementals, Fey, and Monstrosities)",
    ),
    ("N2", "Study [Action]", 7, "History"),
    (
        "N2",
        "Study [Action]",
        8,
        "Historic events and people, ancient civilizations, wars, and certain creatures (Giants and Humanoids)",
    ),
    ("N2", "Study [Action]", 9, "Investigation"),
    ("N2", "Study [Action]", 10, "Traps, ciphers, riddles, and gadgetry"),
    ("N2", "Study [Action]", 11, "Nature"),
    (
        "N2",
        "Study [Action]",
        12,
        "Terrain, flora, weather, and certain creatures (Beasts, Dragons, Oozes, and Plants)",
    ),
    ("N2", "Study [Action]", 13, "Religion"),
    (
        "N2",
        "Study [Action]",
        14,
        "Deities, religious hierarchies and rites, holy symbols, cults, and certain creatures (Celestials, Fiends, and Undead)",
    ),
    # --- Utilize ------------------------------------------------------------
    (
        "O1",
        "Utilize [Action]",
        1,
        "You normally interact with an object while doing something else, such as when you draw a sword as part of the Attack action.",
    ),
    (
        "O2",
        "Utilize [Action]",
        1,
        "When an object requires an action for its use, you take the Utilize action.",
    ),
    # --- Attack -------------------------------------------------------------
    (
        "B1",
        "Attack [Action]",
        1,
        "When you take the Attack action, you can make one attack roll",
    ),
    ("B2", "Attack [Action]", 1, "with a weapon or an Unarmed Strike."),
    ("B3", "Attack [Action]", 2, "Equipping and Unequipping Weapons."),
    (
        "B3",
        "Attack [Action]",
        3,
        "You can either equip or unequip one weapon when you make an attack as part of this action.",
    ),
    ("B4", "Attack [Action]", 3, "You do so either before or after the attack."),
    (
        "B5",
        "Attack [Action]",
        3,
        "If you equip a weapon before an attack, you don't need to use it for that attack.",
    ),
    (
        "B6",
        "Attack [Action]",
        3,
        "Equipping a weapon includes drawing it from a sheath or picking it up. Unequipping a weapon includes sheathing, stowing, or dropping it.",
    ),
    ("B7", "Attack [Action]", 4, "Moving between Attacks."),
    (
        "B7",
        "Attack [Action]",
        5,
        "If you move on your turn and have a feature, such as Extra Attack, that gives you more than one attack as part of the Attack action, you can use some or all of that movement to move between those attacks.",
    ),
]

# Headings are each record's own identifying leaf. They are accounted as
# record-owned supporting authority — the `W = [(None, "R", None)]` shape the
# accepted `hazards-1` generator uses for exactly this — so they carry no
# obligation of their own and are excluded from the obligation table by design,
# not by omission. Listed here so leaf coverage is checkable rather than assumed.
HEADING_LEAVES = {lab: 0 for lab in BATCH}

# ---------------------------------------------------------------------------
# Disposition of each obligation, and the gap family it belongs to
# ---------------------------------------------------------------------------
#
# Every tally the checkpoint reports is derived from this table, so a count in
# the prose cannot drift from the ledger it describes.
#
#   T   typed under representation schema 5
#   P   affirmatively prose-bound under a closed irreducibility reason
#   S   supporting authority
#   R   a source-authored mechanical reference
#   X   UNRESOLVED — substantive, no typed home, and no catalog reason is
#       affirmatively true of it. Blocks publication (SemanticDisposition
#       docstring), which is what makes this batch a stop rather than a
#       lower-fidelity proposal.
#
# An obligation may carry more than one letter where it states more than one
# thing; the gap column names the families that block it.
DISPOSITION: dict[str, tuple[str, tuple[str, ...]]] = {
    "A1": ("X", ("F1",)),
    "A2": ("P", ()),
    "A3": ("S", ()),
    "A4": ("R", ()),
    "D8": ("S", ()),
    "D1": ("X", ("F1", "F2")),
    "D2": ("X", ("F2",)),
    "D3": ("X", ("F3",)),
    "D4": ("S", ()),
    "D5": ("X", ("F2",)),
    "D6": ("T", ()),
    "D7": ("R", ()),
    "E1": ("X", ("F5",)),
    "E2": ("X", ("F3",)),
    "E3": ("S", ()),
    "G1": ("T", ()),
    "G2": ("P", ()),
    "G3": ("T", ()),
    "G4": ("X", ("F3",)),
    "G5": ("X", ("F6a", "F6b")),
    "G6": ("S", ()),
    "G7": ("S", ()),
    "H1": ("X", ("F17", "F18")),
    # Option-scoped governing prose: it states arm 1's selection and proximity
    # judgement, and `gamemaster_latitude`/`contextual_applicability` is true of
    # it - but bound at component grain it would govern the attack-roll arm too.
    # Same defect as H5, so the same family and the same disposition.
    "H2": ("X", ("F19",)),
    "H3": ("X", ("F17", "F18")),
    "H4": ("X", ("F3",)),
    "H5": ("X", ("F19",)),
    "H6": ("X", ("F17", "F18", "F19")),
    "H7": ("X", ("F3",)),
    "I1": ("T", ()),
    "I2": ("X", ("F6b", "F6c")),
    "I3": ("P", ()),
    "I4": ("P", ()),
    "I5": ("T", ()),
    # Revision 4. F7 named the DC source and stopped there. The check the DC
    # is stated for is made by the *finder* - "the DC for a creature to find
    # you" - and `AbilityCheckFact` had no axis for that, so a fact carrying
    # only the new DC source would read as the subject making a Perception
    # check to find themselves. False rather than lossy, and the same
    # beneficiary defect family as F17. Recorded as F22 beside F7.
    "I6": ("X", ("F7", "F22")),
    "I7": ("P", ()),
    "I9": ("S", ()),
    "I10": ("S", ()),
    "J1": ("P", ()),
    "J2": ("P", ()),
    "J3": ("P", ()),
    "J4": ("P", ()),
    "J5": ("R", ()),
    "J6": ("X", ("F8",)),
    "J7": ("P", ()),
    "J8": ("P", ()),
    "J9": ("X", ("F10",)),
    "J10": ("TP", ()),
    "J11": ("X", ("F11",)),
    "K1": ("TP", ()),
    "K2": ("X", ("F12",)),
    "K3": ("X", ("F20",)),
    "K4": ("X", ("F6a", "F13")),
    "K5": ("R", ()),
    "L1": ("T", ()),
    "L2": ("X", ("F1", "F3")),
    "L3": ("P", ()),
    # Revision 5 keeps Revision 4's disposition and replaces its reason, which
    # was wrong in a way that mattered. Revision 4 said arm 1 is untypeable
    # because no closed vocabulary reaches *which* action the subject chooses,
    # and read "an option must state at least one typed fact" as "every fact" -
    # neither of which is the rule.
    #
    # The real limitation is narrower and harder. Arm 1 states a *designation*:
    # the subject chooses, in advance, what the already-granted Reaction will
    # be spent on. `ActionAllowanceFact.cost` names a slot the owning effect
    # *grants* - that is the family's whole claim - so typing arm 1 as an
    # Action allowance would publish two grants (an Action, and L2's Reaction)
    # where the source states one. `option_set_violations` would admit the
    # pair, because structural authorability is not truth.
    #
    # So the set is not authorable, and the honest form is one MIXED component:
    # the own-Speed allowance typed under F2, and the whole "you choose the
    # action ... or" clause bound under `open_ended_effect`, which is
    # affirmatively true of the open action space. F19 is not claimed - with no
    # option rows there is no option grain to bind at. Composed and shown in
    # `test_schema_6_source_compositions`; the unrepresented meaning is named
    # in the checkpoint's 14.6.
    "L4": ("X", ("F2",)),
    "L5": ("S", ()),
    "L6": ("X", ("F16",)),
    "L7": ("X", ("F13",)),
    # Revision 4. Revision 3 had this as supporting authority; it is
    # substantive eligibility. A spell's casting time is a printed, enumerable
    # SpellDescriptorFact field, so nothing here is unenumerable fiction, and
    # what the clause states is *which spells the mechanic reaches*. The sweep
    # for comparable clauses found two - K1's "a spell that has a casting time
    # of an action" and O2's "an object requires an action for its use" - and
    # both were already typed rather than misclassified, so only this one moved.
    # They are the family's confirming siblings and stay TP; a family may be
    # named only on an UNRESOLVED row here, which is why they carry none.
    "L8": ("X", ("F21",)),
    "L9": ("X", ("F3",)),
    "L10": ("X", ("F6a",)),
    "M1": ("T", ()),
    "M2": ("P", ()),
    "M3": ("P", ()),
    "N1": ("TP", ()),
    "N2": ("P", ()),
    "O1": ("S", ()),
    "O2": ("TP", ()),
    "B1": ("X", ("F1",)),
    # Revision 4. Recorded as blocked only because it was modelled as an
    # option set, and it is not one: both arms would state B1's identical
    # entitlement, which `option_set_violations` refuses as two options a
    # consumer could not tell apart. The clause is the instrument qualification
    # on that single entitlement, and `contextual_applicability` is
    # affirmatively true of it - which weapons qualify is not determined by this
    # record. Honest prose on a MIXED component beside the allowance.
    "B2": ("P", ()),
    "B3": ("X", ("F1", "F14")),
    "B4": ("X", ("F14",)),
    "B5": ("S", ()),
    "B6": ("S", ()),
    "B7": ("X", ("F16",)),
}

#: Families whose motivating cases are all representable, or which name an
#: enrichment rather than a blocker. Recorded rather than deleted so the
#: correction is legible against the previous revision.
NON_BLOCKING = {
    "F4": "never defined; the identifier was unused",
    "F9": (
        "prose-bound under contract 3's second branch. Revision 4 removes the "
        "scope claim: the suggested skill tables do not evidence random-table "
        "selection - they state what the GM *may* choose and nothing follows "
        "from them by itself - so this batch surfaces no instance of that "
        "contract-3 group. The prose bindings are justified and stay; the "
        "full-corpus obligation for random-table selection stands on its own "
        "and is not discharged or advanced by these three tables"
    ),
    "F15": "withdrawn - both motivating cases are representable as authored",
    "F19": (
        "Help alone. Revision 4 narrowed it there by withdrawing L4 and "
        "Revision 5 confirms the withdrawal on a corrected reason: L4 is not "
        "an option set because arm 1 designates rather than grants, so there "
        "are no option rows to bind at. H2, H5 and H6 remain, and "
        "component-grain binding is false for them rather than lossy"
    ),
}

rows: list[dict[str, object]] = []
errors: list[str] = []
covered: dict[str, set[int]] = defaultdict(set)

for oid, label, leaf_index, spec in LEDGER_SPEC:
    phrase, which = spec if isinstance(spec, tuple) else (spec, "unique")
    leaves = BATCH[label]
    if not 0 <= leaf_index < len(leaves):
        errors.append(f"{oid}: {label} has no leaf {leaf_index}")
        continue
    leaf = leaves[leaf_index]
    hay = fold(leaf.content)
    needle = fold(phrase)
    first = hay.find(needle)
    if first < 0:
        errors.append(f"{oid}: phrase not present in {label}[{leaf_index}]: {phrase!r}")
        continue
    repeated = hay.find(needle, first + 1) >= 0
    if which == "unique" and repeated:
        errors.append(
            f"{oid}: phrase occurs more than once in {label}[{leaf_index}]: {phrase!r}"
        )
        continue
    if which == "last":
        if not repeated:
            errors.append(
                f"{oid}: 'last' selector but only one occurrence in "
                f"{label}[{leaf_index}]: {phrase!r}"
            )
            continue
        first = hay.rfind(needle)
    end = first + len(needle)
    covered[label].add(leaf_index)
    rows.append(
        {
            "obligation": oid,
            "entry": label,
            "leaf_index": leaf_index,
            "leaf_id": leaf.leaf_id,
            "leaf_type": leaf.leaf_type,
            "printed_page": leaf.page_index + 1,
            "char_start": first,
            "char_end": end,
            # Sliced back out of the leaf, so the ledger's quotation is the
            # source's text at these offsets rather than a transcription of it.
            "source_text": leaf.content[first:end],
        }
    )

# Overlap: two obligations claiming the same characters of one leaf would make
# the eventual per-leaf partition impossible, so it is checked here rather than
# discovered at proposal time.
claimed: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
for row in rows:
    claimed[str(row["leaf_id"])].append(
        (int(row["char_start"]), int(row["char_end"]), str(row["obligation"]))
    )
for _lid, _spans in claimed.items():
    _spans.sort()
    for (_s1, _e1, _o1), (_s2, _e2, _o2) in zip(_spans, _spans[1:], strict=False):
        if _s2 < _e1:
            errors.append(
                f"overlap in leaf {_lid}: {_o1}[{_s1}:{_e1}] and {_o2}[{_s2}:{_e2}]"
            )

# Leaf coverage: which represented leaves carry no obligation row at all.
uncovered: dict[str, list[dict[str, object]]] = {}
for label, leaves in BATCH.items():
    missing = [
        {
            "leaf_index": i,
            "leaf_id": leaf.leaf_id,
            "leaf_type": leaf.leaf_type,
            "content": leaf.content,
        }
        for i, leaf in enumerate(leaves)
        if i not in covered[label] and i != HEADING_LEAVES[label]
    ]
    if missing:
        uncovered[label] = missing

missing_disposition = sorted({r["obligation"] for r in rows} - set(DISPOSITION))
extra_disposition = sorted(set(DISPOSITION) - {r["obligation"] for r in rows})
if missing_disposition:
    errors.append(f"obligations with no disposition: {missing_disposition}")
if extra_disposition:
    errors.append(f"dispositions with no obligation: {extra_disposition}")

tally: dict[str, int] = defaultdict(int)
for _code, _ in DISPOSITION.values():
    tally[_code] += 1
blocking_families: dict[str, list[str]] = defaultdict(list)
for _oid, (_code, _fams) in sorted(DISPOSITION.items()):
    for _f in _fams:
        blocking_families[_f].append(_oid)
    if _code == "X" and not _fams:
        errors.append(f"{_oid}: UNRESOLVED with no family named")
    if _code != "X" and _fams:
        errors.append(f"{_oid}: names a blocking family but is not UNRESOLVED")

# ---------------------------------------------------------------------------
# Full per-leaf coverage
# ---------------------------------------------------------------------------
#
# The previous revision measured only the gaps *between* consecutive claims and
# reported 74 characters. That understated the residue by ignoring the head of a
# leaf (before the first claim) and its tail (after the last), which is where a
# whole clause can hide: Dash's trigger, "When you take the Dash action, ", is a
# 31-character head run that no obligation claimed.
#
# Coverage is therefore measured as a partition of every represented leaf. A run
# no obligation claims is classified, not merely counted:
#
#   separator  - only whitespace and inter-clause punctuation. Real residue an
#                exact partition still has to assign, but it states nothing.
#   SUBSTANTIVE - contains a word character. This is source meaning nobody
#                accounted, and it FAILS the run.
#
# Heading leaves are excluded from the partition by the same rule that excludes
# them from the obligation table: they are record-owned supporting authority.
_SEPARATOR_CHARS = set(" \t\r\n.,;:()[]\u2019'\u201c\u201d\"\u2014-\u2013/")


def _classify(run: str) -> str:
    """A run is separator-only, or it is substantive source text."""
    return "separator" if set(run) <= _SEPARATOR_CHARS else "SUBSTANTIVE"


unassigned_total = 0
unassigned_runs: list[dict[str, object]] = []
partition: list[dict[str, object]] = []
for label, leaves in BATCH.items():
    for index, leaf in enumerate(leaves):
        if index == HEADING_LEAVES[label]:
            continue
        spans = sorted((s, e, o) for s, e, o in claimed.get(leaf.leaf_id, []))
        cursor = 0
        runs: list[tuple[int, int]] = []
        for s, e, _o in spans:
            if s > cursor:
                runs.append((cursor, s))
            cursor = max(cursor, e)
        if cursor < len(leaf.content):
            runs.append((cursor, len(leaf.content)))
        leaf_unassigned = 0
        for s, e in runs:
            run = leaf.content[s:e]
            kind = _classify(run)
            leaf_unassigned += e - s
            unassigned_total += e - s
            unassigned_runs.append(
                {
                    "entry": label,
                    "leaf_index": index,
                    "leaf_id": leaf.leaf_id,
                    "start": s,
                    "end": e,
                    "kind": kind,
                    "text": run,
                }
            )
            if kind == "SUBSTANTIVE":
                errors.append(
                    f"unaccounted source text in {label}[{index}] "
                    f"{leaf.leaf_id[:8]}[{s}:{e}]: {run!r}"
                )
        partition.append(
            {
                "entry": label,
                "leaf_index": index,
                "leaf_id": leaf.leaf_id,
                "length": len(leaf.content),
                "claimed_characters": len(leaf.content) - leaf_unassigned,
                "unassigned_characters": leaf_unassigned,
            }
        )

report = {
    "release_version": CAND.release_version,
    "package_uuid": CAND.package_uuid,
    "authoritative_source_hash": CAND.authoritative_source_hash,
    "transform_config_hash": CAND.transform_config_hash,
    "bundle_root_hash": CAND.bundle.bundle_root_hash,
    "records": len(BATCH),
    "represented_leaves": sum(len(v) for v in BATCH.values()),
    "obligation_rows": len(rows),
    "distinct_obligations": len({r["obligation"] for r in rows}),
    "leaves_carrying_an_obligation": sum(len(v) for v in covered.values()),
    "overlapping_claims": 0,
    "disposition_tally": dict(sorted(tally.items())),
    "blocking_families": {k: v for k, v in sorted(blocking_families.items())},
    "blocking_family_count": len(blocking_families),
    "unresolved_obligations": sorted(
        o for o, (c, _) in DISPOSITION.items() if c == "X"
    ),
    "records_with_an_unresolved_obligation": 0,
    "non_blocking_families": NON_BLOCKING,
    "non_heading_leaves": len(partition),
    "unassigned_characters": unassigned_total,
    "substantive_unassigned_runs": sum(
        1 for r in unassigned_runs if r["kind"] == "SUBSTANTIVE"
    ),
    "unassigned_runs": unassigned_runs,
    "leaf_partition": partition,
    "coordinates": rows,
    "leaves_without_an_obligation_row": uncovered,
}

_rec_of = {r["obligation"]: r["entry"] for r in rows}
report["records_with_an_unresolved_obligation"] = len(
    {_rec_of[o] for o in report["unresolved_obligations"]}
)

OUT_PATH.write_text(
    json.dumps(report, indent=1, ensure_ascii=False, sort_keys=False) + "\n",
    encoding="utf-8",
    newline="\n",
)

print(f"records={report['records']} leaves={report['represented_leaves']}")
print(
    f"dispositions={report['disposition_tally']} "
    f"unresolved={len(report['unresolved_obligations'])} "
    f"in {report['records_with_an_unresolved_obligation']} records"
)
print(
    f"blocking families={report['blocking_family_count']}: "
    f"{sorted(report['blocking_families'])}"
)
print(
    f"unassigned characters={report['unassigned_characters']} "
    f"across {len(report['unassigned_runs'])} run(s); "
    f"substantive={report['substantive_unassigned_runs']}"
)
print(
    f"obligations={report['distinct_obligations']} "
    f"rows={report['obligation_rows']} "
    f"leaves_with_an_obligation={report['leaves_carrying_an_obligation']}"
)
for label, missing in uncovered.items():
    for m in missing:
        print(
            f"  NO OBLIGATION  {label}[{m['leaf_index']}] {m['leaf_type']}: {m['content'][:70]!r}"
        )
print(f"wrote {OUT_PATH.relative_to(REPO).as_posix()}")
if errors:
    for e in errors:
        print(f"  ERROR {e}")
    raise SystemExit(f"{len(errors)} coordinate(s) did not resolve")
