# CRD Issue 5d (#132, #137): Playing the Game atoms — UNACCEPTED candidate

Status: **UNACCEPTED review material.** Nothing is accepted, recorded,
published or activated, and no Owner approval exists for it. Recording needs
a fresh, exact Owner acceptance naming these candidates.

## Authority and scope

- ADR-005d Decisions 5 and 7. A citation is identified by its source record,
  owning component, exact printed wording and scope. The source prose keeps
  its qualifications. References are for navigation; they do not decide
  eligibility.
- The accepted finite-reference-atoms precedent
  (`issue-5d-finite-reference-atoms-review.md`, recorded as `005768c2…`).
  When a pointer sentence names a finite list of destinations, each printed
  destination gets its own identity in the same component and the same scope,
  authored with its target. The unresolved chapter pointer is then retired.
- The accepted Monsters singular qualifiers
  (`issue-5d-monsters-generator.py` `QUALIFIED`, lines 539–558; the three below at 546–551) already
  target these exact rules under a Playing the Game pointer:
  - "A monster's Armor Class (AC)" → `play.d20_tests`;
  - "If you don't want to roll a monster's Initiative" → `play.combat`;
  - "For more on Hit Points" → `play.damage_and_healing`.

  These are the narrowest accepted records that own those rules. They are not
  a parent fallback.
- Scope: inventory rows #68, #69 and #70 only. Every other one of the 52
  residue rows stays held.

## Artifacts

| File | SHA-256 |
|---|---|
| `issue-5d-playing-the-game-atoms-REPLACEMENT.py` (constructor) | `23a9442c19eb0a39e01a351da1b89a41b62730f0940983a1f93547b77bcc8ea9` |
| `issue-5d-core-play-dependencies-playing-the-game-atoms-PROPOSAL.json` | `7a2344959a133319b60d720b7eab9d407c5c34907b5c585952a969bec510d210` |
| `issue-5d-monsters-playing-the-game-atoms-PROPOSAL.json` | `69de9bc2875f0fed9483654d296a3ff3480f13da8a87345143d4a90d3640b633` |
| `issue-5d-playing-the-game-atoms-DELTA.txt` (42 lines) | `e34690675925d6a08ff233e479104a531255e4e7c2fda06dee4045ebf28ef8b9` |

| Batch | Candidate identity | Recorded identity (replaced) |
|---|---|---|
| core-play-dependencies | `9aa7d0097fcf4cd64cbed630828eeca72606fc9c1818cde42a44f106accf6eac` | `8fce546dfc78d37dfd98c68e1f4fe801602bdd0c84fe31d6a06ade6ad03e6c2b` (`issue-5d-core-play-dependencies-remaining-references-PROPOSAL.json`) |
| monsters | `d6eff4f4858efd5da983dbdbbce85c2b9ddd6d20ed810c10d044087b3b66f91d` | `e39e622107d443713d17e25bc64f73210241af3f83d4cd86cf73132eaf4de327` (`issue-5d-monsters-finite-reference-atoms-PROPOSAL.json`) |

- Accepted oracle: `005768c282669c3acf564b3efd70d1c54aa7307f4e47505b77b67e8612d73b84`.
  Counts are 24 / 1835 / 10492 / 1476 / 1440, with 52 reference findings and
  0 uncovered leaves. The oracle is byte-unchanged.
- Simulated composition (never recorded): `7254578d708261c14e3a33935e505af01a4a0b0c15b8c73c84e23db134d25a08`.

## Construction

There is no supersession. The constructor recomposes the recorded
finite-reference chain using the `ACC.composed` loop, as follows:

- The recorded batches keep their recorded evidence.
- The four unchanged finite-reference batches keep the Owner's recorded
  acceptance (`APPROVAL` at `2026-09-30T00:18:19Z`).
- The two changed batches take the simulated reviewer, in their recorded
  places.

Build path:

- core-play-dependencies: `generator.batch()` → `RR.candidate_batch` → the
  #68/#69 edits.
- monsters: `generator.batch()` → `RR.candidate_batch` → `FRA.edited`, so the
  recorded speed and spellcasting atoms are kept → the #70 edit.

Controls, each asserted:

- Each rebuild without the edits reproduces its recorded proposal file byte
  for byte.
- The chain with no candidate reproduces the committed `005768c2…` byte for
  byte.

What does not change:

- No resolution is drafted, re-keyed or dropped.
- No schema, ownership, prose, span, binding or expectation changes.
- No generator or accepted file is edited.

## Changes (3 retired, 7 added)

| Row | Record / component | Span | Retired | New identity → target |
|---|---|---|---|---|
| #68 | `glossary.stat_block` / `ability_scores` | 295ea07b | `Playing the Game` (PLAY, unresolved) | `ability scores, modifiers` → `play.six_abilities`; `saving throw modifiers` → `play.d20_tests` |
| #69 | `glossary.stat_block` / `ac_initiative_hp` | 92a3a2c3 | `Playing the Game` (PLAY, unresolved) | `Armor Class` → `play.d20_tests`; `Initiative` → `play.combat`; `Hit Points` → `play.damage_and_healing` |
| #70 | `monsters.parts_of_a_stat_block` / `ability_scores` | 87bd3a1f | `Playing the Game` (PLAY, unresolved) | `ability scores` → `play.six_abilities`; `saving throws` → `play.d20_tests` |

Every new identity has scope `srd-5.2.1/playing-the-game`. Each new atom
replaces the retired pointer in place, so no empty identity stays beside the
new edges.

## Source and target proof

Source sentences (exact):

- **#68:** '_Ability Scores._ A table provides the monster's ability scores,
  modifiers, and saving throw modifiers, all of which are detailed in
  "Playing the Game."'
- **#69:** '_AC, Initiative, and HP._ These entries give the monster's Armor
  Class, Initiative, and Hit Points, which are detailed in "Playing the
  Game." In parentheses after the Hit Points, the monster's Hit Point Dice are
  provided, along with the contribution of its Constitution, if any, to its Hit
  Points. Following the Initiative modifier is an Initiative score. Some
  creatures that are created by magic lack Hit Dice and Initiative
  information.'
- **#70:** 'Every monster has six ability scores along with corresponding
  ability score modifiers and saving throw modifiers. For more information on
  ability scores and saving throws, see "Playing the Game."'

Each target owns the rule it is cited for. The constructor asserts this
through `RR.owned_by_component` on the composed state:

| Target | Components owning the rule (span) | Chapter heading |
|---|---|---|
| `play.six_abilities` | `ability_scores` (2bafc091, e7777d46 "Ability Scores" table), `ability_modifiers` (4a53259e, 5f623b22 "Ability Modifiers" table) | The Six Abilities |
| `play.d20_tests` | `saving_throws` 6dc0a896, `save_ability_modifier` 9abc0d0b, `save_proficiency` 2bcc9239, `armor_class` 4e1f6ecf | D20 Tests › Saving Throws; Attack Rolls › Armor Class |
| `play.combat` | `initiative_roll` 9ec20dc2, `initiative_order` 89b2df16 | Combat › Initiative |
| `play.damage_and_healing` | `hit_points` 590bff37 | Damage and Healing › Hit Points |

- The constructor also asserts that no target has a nested `play.` record.
  Among the `play.*` records, only `play.exploration.*` and `play.proficiency.*`
  are nested. So no accepted record narrower than these four owns saving
  throws, Armor Class, Initiative, Hit Points, ability scores or ability
  modifiers.
- Each new atom's provenance cites exactly its sentence's span. Every new
  text is printed in that span, which is asserted.

## Disclosures (the accepted contract settles each; none is a boundary)

- **Glossary records with the same words.** Elsewhere the same wording
  resolves to glossary records:
  - `Armor Class` → `glossary.armor_class` (30 citations);
  - `Initiative` → `glossary.initiative` (41);
  - `Hit Points` → `glossary.hit_points` (182);
  - `saving throws` → `glossary.saving_throw` (69).

  Here, though, each sentence says "detailed in / see 'Playing the Game'". The
  printed scope is therefore Playing the Game, and the target must be a
  `play.*` record, exactly as the accepted `QUALIFIED` mappings do for AC,
  Initiative and Hit Points.
- **#68 compound literal.** `ability scores, modifiers` is one literal with
  one target, because a single record owns both the Ability Scores and the
  Ability Modifiers components. This follows the Owner lead to avoid a bare
  `modifiers`, which would also fall inside "saving throw modifiers".
- **#70 and the existing glossary atom.** The component already has
  `saving throw` → `glossary.saving_throw`, which is kept. The new
  `saving throws` → `play.d20_tests` is different exact wording in a
  different scope with a different target (the FRA #28 precedent). The
  constructor asserts that every kept identity keeps its exact provenance.
- **Substrings.** `saving throw` is a substring of `saving throws` and of
  `saving throw modifiers`. In #70's first sentence ("…and saving throw
  modifiers") the kept glossary atom `saving throw` also matches, which is
  why the constructor asserts its provenance is unchanged. The identities stay
  distinct by exact wording.
- **Repeated occurrences coalesce** under one identity with one target, as
  the finite-reference `Bard` atom does:
  - In 92a3a2c3, `Initiative` is printed 5 times: the heading, the list, the
    Initiative modifier, the Initiative score, and "Initiative information".
    `Hit Points` is printed 3 times. All of these belong to the Combat
    Initiative rules and the Hit Points rules.
  - `ability scores` is printed twice in 87bd3a1f.
- **Uncited wording.** `Hit Point Dice`, `Hit Dice`, `Constitution` and
  `ability score modifiers` are not destinations of the pointer sentence, so
  they are not cited.

## Evidence (asserted by the constructor)

- **Proposal delta:**
  - core-play-dependencies: references −2/+5, provenance −2/+5;
  - monsters: references −1/+2, provenance −1/+2;
  - every other collection is empty.
- **State delta** (`DELTA.txt`):
  - `representation.references` −3 +7 and `representation.provenance` −3 +7;
  - `acceptance.batches` −2 +2 and `acceptance.schema_anchors` −2 +2. These
    differ only in `proposal_identity`, `semantic_diff_hash` and `diff`, and
    each new `proposal_identity` equals its candidate file's;
  - records, spans, units and resolutions are unchanged. Counts stay
    (24, 1835, 10492, 1476, 1440), with 0 violations.
- **Resolutions:** all 1440 are payload-equal and in order. There are 0
  drafts.
- **Findings** (compared as multisets): 52 / 0 → 49 / 0. Exactly 3 were
  cleared, each `reference srd-5.2.1/playing-the-game:'Playing the Game':
  unresolved reference`. No finding is new.
- **Identities:**
  - For each edit, the retired key exists before and is gone after.
  - Each new key is absent before and has a single target after.
  - The other 8043 citation identities keep their targets and provenance.
- **Native projection:** `candidate_from_accepted_inputs(final)` projects all
  7 new atoms to their target records. `identify_projection` →
  `bd83f2e2-fed0-5015-a201-32718b99c948`.
- **Preservation:**
  - `RR.owned` (prose bindings) and `RR.expectations` are equal before and
    after.
  - The consumer reading (members, readings, direct) is equal in three cases:
    with no override, with `disable-glossary.stat_block-record`, and with
    `disable-monsters.parts_of_a_stat_block-ability_scores`.
  - Under the last override, that component's spans are absent from the
    direct reads.
- **Recorded atoms kept:** the monsters speed and spellcasting atoms that
  finite-reference recorded are kept, through the monsters control plus the
  identity check.

## Remaining findings (49) dispositioned

| Rows | Count | Disposition |
|---|---|---|
| #79–86 "See Spells for rules on spellcasting" | 8 | Held (unchanged) |
| #37, #34, #38 | 3 | Held (unchanged) |
| #54 | 2 | Held (unchanged) |
| M-list retained: #13, #16, #21, #48, #71, #73 | 6 | As in the finite-reference review |
| M-set: #17–20, #22, #46, #49, #76, #89 | 9 | Retained (unchanged) |
| M-dynamic: #4, #8–12, #23, #36, #51–53, #55, #57, #60 | 14 | Retained (unchanged) |
| U-part: #7, #24, #35, #87, #88 | 5 | Retained (unchanged) |
| #39 Spellbook | 1 | Held deferral |
| #40 Origin Feats | 1 | Held (K-contract) |
| **Total** | **49** | |

Rows #68, #69 and #70 were "Retained (held), not reassessed" in the
finite-reference review. They are reassessed here under the Owner lead.

## Gates

- **Constructor checks:** Black, Ruff and `mypy --strict` (`MYPYPATH=src`)
  all passed.
- **Constructor runs:**
  - The `--write` run completed through its final assertion (`committed
    artifact unchanged`) with empty stderr (`.claude/_sp/pga/write.txt`). The
    process exit code was not captured.
  - The verify-only run on the final constructor bytes completed with empty
    stderr. Its 38 lines are identical to the `--write` run's
    (`.claude/_sp/pga/verify.txt`).
- **Not run, and not claimed green:** pytest, the broad suite, pip-audit and
  expanded mypy.
  - No test names these proposal files; `git grep` over `tests/` finds no
    `playing-the-game-atoms`, `finite-reference-atoms-PROPOSAL` or
    `remaining-references-PROPOSAL`.
  - No accepted artifact changed.
- **detect-secrets:** a scoped rescan (`PYTHONUTF8=1`, using the baseline's
  own plugins and filters) of the five new files.
  - Baseline `cd0c21770f941ae5a53bb3c4ce0c84ed91299e406440dc4e6d73adfec7b7a1ba`
    → `bda93756b6eb59b5c9c94bc506d1a94818e7ab8bdf79775c09d68123c1418a5a`:
    added 31, pruned 0, moved 0. Settings, filters, `generated_at` and every
    other file's entries are identical (`bl/cmp.py`).
  - Per file: the constructor 1 (`ACCEPTED_SHA256`). The core-play candidate
    17, exactly the set baselined for
    `…core-play-dependencies-remaining-references-PROPOSAL.json`. The monsters
    candidate 6, exactly the set baselined for
    `…monsters-finite-reference-atoms-PROPOSAL.json` (`bl/check.py`); these
    public binding hashes cover the 11 whose names the scan could not
    recover. The DELTA 7 (`proposal_identity`, `schema_hash`,
    `semantic_diff_hash`). This packet 0.
  - Staged by name. The hook ran twice on the five relative paths, EXIT 0
    both times, with the baseline hash stable (`bl/hook1.log`,
    `bl/hook2.log`; final runs `bl/hook3.log`, `bl/hook4.log`).

## Not done

- No recording, acceptance, commits, push, publication or activation.
- No reordering.
- No source errata encountered.
