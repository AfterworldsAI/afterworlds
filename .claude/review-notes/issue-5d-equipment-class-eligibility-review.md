# CRD Issue 5d (#132, #137): Equipment class eligibility — UNACCEPTED candidate

Status: **UNACCEPTED review material.** Nothing is accepted, recorded,
published or activated, and no Owner approval exists for it. Recording needs
Codex review and then a fresh, exact Owner acceptance naming this candidate.
The partial-publication block remains.

## Authority and scope

- ADR-005d Decision 7 (`docs/decisions/adr-005d-complete-typed-mechanical-authority.md`,
  line 1282): "Unique destination names alone do not establish source
  intent."
- Inventory rows #13, #16 and #21 only
  (`issue-5d-remaining-references-review.md` lines 479, 482 and 487). The
  finite-reference review held them (line 200). Every other one of the 49
  residue rows stays as it is.

## Source intent

Each sentence (`docs/sources/community/dnd-5e-srd-markdown/equipment.md`) is a
self-contained statement of who may use the focus:

| Row | Line | Span | Sentence |
|---|---|---|---|
| #21 | 1261 | 99385f2f | "An Arcane Focus … A Sorcerer, Warlock, or Wizard can use such an item as a Spellcasting Focus." |
| #16 | 1404 | bdaf8271 | "A Druidic Focus … A Druid or Ranger can use such an object as a Spellcasting Focus." |
| #13 | 1461 | 0c3ee4b4 | "A Holy Symbol … A Cleric or Paladin can use a Holy Symbol as a Spellcasting Focus." |

The class names are the subjects of an eligibility statement. No sentence
directs the reader to a class section. Under Decision 7, the fact that each
name matches a class record does not make it a citation. So each accepted
empty-target classes-scope reference is removed together with its one
provenance entry. None of them is resolved or retargeted.

## Artifacts

| File | SHA-256 |
|---|---|
| `issue-5d-equipment-class-eligibility-REPLACEMENT.py` (constructor) | `bdc8a24e87614ef98c0545d81dd52a36b397396e11daa0408f8f6c9dae4a062b` |
| `issue-5d-equipment-class-eligibility-PROPOSAL.json` | `2cafbccec28990a93270bdd09c7546782448df2dd52376fbc7e1f4079457aa08` |
| `issue-5d-equipment-class-eligibility-DELTA.txt` (17 lines) | `9e29c197f09657a9d48447753cd8bec7ac90eb1e47291ff73844ce358784d908` |

- Equipment batch identity: the candidate is
  `d7c012dfc96aad5c34e1630a8acedee83b6626311167f5ed256e3126d74456f3`. It
  replaces the recorded `309e4405a4dc630b477adac0e83e2bc86bae0e2e6f76550775e5dae2b1bc1680`
  (`issue-5d-equipment-cited-targets-PROPOSAL.json`, sha `13271e03…`).
- Accepted oracle: `92b7a68fcd6ea622ac3ef79b1dacd939f7be52fa445fcbdafd5adc8c77352e19`
  (Playing the Game recorded at `2026-09-30T05:09:01Z`). It is byte-unchanged.
- Simulated composition (never recorded):
  `dc2931f86e4bf83202a3c5c3a6fcdb1c73f409d8ededfbe8ee846811d69403e5`.

## Construction

There is no supersession. The constructor loads the Playing the Game ACCEPT
script as `playing_the_game_atoms_accept` and recomposes the recorded chain
with the `ACC.composed` loop:

- Every recorded batch keeps its recorded evidence. That includes the
  remaining-references, animals-catalogue, finite-reference and Playing the
  Game acceptances, and all 1440 resolution steps.
- Only equipment takes the simulated reviewer, in its recorded place.

Build path: `issue-5d-equipment-cited-targets-generator.py` `batch()` → drop
the three refs → `build_entry_batch` → `render`. Equipment is in none of the
later candidate sets (`RR.CHANGED`, `FRA.EDITS`, the Playing the Game
proposals).

Controls, both asserted:

- The rebuild without the edit reproduces
  `issue-5d-equipment-cited-targets-PROPOSAL.json` byte for byte.
- The chain with no candidate reproduces the committed `92b7a68f…` byte for
  byte.

What does not change:

- No resolution is drafted, re-keyed or dropped.
- No generator or accepted file is edited.
- No prose, span, binding, ownership, expectation, focus rule or class record
  changes.

## Changes (3 removed, 0 added)

| Row | Record / component | Span | Removed (scope `srd-5.2.1/classes`, target `""`) | Kept in the component |
|---|---|---|---|---|
| #13 | `equipment.adventuring_gear.holy_symbol` / `holy_symbol` | 0c3ee4b4 | `Cleric or Paladin` | `Shield` → `equipment.armor.shield` |
| #16 | `equipment.adventuring_gear.druidic_focus` / `druidic_focus` | bdaf8271 | `Druid or Ranger` | `Quarterstaff` → `equipment.weapons.quarterstaff` |
| #21 | `equipment.adventuring_gear.arcane_focus` / `arcane_focus` | 99385f2f | `Sorcerer, Warlock, or Wizard` | `Quarterstaff` → `equipment.weapons.quarterstaff` |

Qualification was done on the accepted oracle before editing:

- Exactly these three equipment references have classes scope and an empty
  target.
- Each has exactly one provenance entry (`contextual`), on the span prefix
  named above.
- No resolution names any of the three components.

## Evidence (asserted by the constructor)

- **Proposal delta:** references −3/+0 and provenance −3/+0. Every other
  collection is empty.
- **State delta** (`DELTA.txt`):
  - `representation.references` −3 +0 and `representation.provenance` −3 +0;
  - `acceptance.batches` −1 +1 and `acceptance.schema_anchors` −1 +1. These
    differ only in `proposal_identity`, `semantic_diff_hash` and `diff`, and
    the new `proposal_identity` equals the candidate's;
  - counts stay (24, 1835, 10492, 1476, 1440), with 0 violations.
- **Resolutions:** all 1440 are payload-equal and in order. There are 0
  drafts.
- **Findings** (compared as multisets): 49 / 0 → **46 / 0**. Exactly 3 were
  cleared, the `reference srd-5.2.1/classes:…: unresolved reference` finding
  for each removed text. No finding is new.
- **Identities:**
  - Each removed key exists before (target `""`) and is gone after.
  - Its sole provenance is the named span, which prints the class names and
    "Spellcasting Focus".
  - No identity is added.
  - The other 8047 citation identities keep their targets and provenance.
- **Native projection:** `candidate_from_accepted_inputs` loses exactly the 3
  removed references and adds none. `identify_projection` →
  `7cb9d5f7-82d9-5a3d-ad07-0b2db954e09b`.
- **Preservation:**
  - `RR.owned` (prose bindings) and `RR.expectations` are equal before and
    after.
  - The consumer reading (members, readings, direct) is equal in three cases:
    with no override, with
    `disable-equipment.adventuring_gear.arcane_focus-record`, and with
    `disable-equipment.adventuring_gear.druidic_focus-druidic_focus`.

## Remaining findings (46)

The table is the Playing the Game packet's 49, with the M-list row reduced by
#13, #16 and #21.

| Rows | Count | Disposition |
|---|---|---|
| #79–86 "See Spells for rules on spellcasting" | 8 | Held (unchanged) |
| #37, #34, #38 | 3 | Held (unchanged) |
| #54 | 2 | Held (unchanged) |
| M-list retained: #48, #71, #73 | 3 | As in the finite-reference review |
| M-set: #17–20, #22, #46, #49, #76, #89 | 9 | Retained (unchanged) |
| M-dynamic: #4, #8–12, #23, #36, #51–53, #55, #57, #60 | 14 | Retained (unchanged) |
| U-part: #7, #24, #35, #87, #88 | 5 | Retained (unchanged) |
| #39 Spellbook | 1 | Held deferral |
| #40 Origin Feats | 1 | Held (K-contract) |
| **Total** | **46** | |

## Gates

- **Constructor checks:** Black 0, Ruff 0, `mypy --strict` (`MYPYPATH=src`)
  0, all on the final bytes. The first strict mypy run flagged one unused
  `type: ignore`, which was removed.
- **Constructor runs** (`RTK_DISABLED=1`, `PYTHONUTF8=1`, venv Python):
  - `--write`: EXIT 0, empty stderr (`.claude/_sp/ece/write.txt`).
  - Check-only run on the final constructor bytes: EXIT 0, empty stderr. Its
    29 lines are byte-identical to the `--write` run's
    (`.claude/_sp/ece/check2.txt`).
- **Not run, and not claimed green:** pytest, the broad suite, pip-audit,
  expanded mypy and coverage.
  - No test or source file names these files.
  - No accepted artifact changed.
- **detect-secrets:** a scoped rescan (`PYTHONUTF8=1`, using the baseline's
  own plugins and filters) of the four new files.
  - Baseline `377dc292cb49de9976604039fc29cc49f53f63b070b8a07006c7544941c5203a`
    → `d780f37e301b7e3d5b6a4c16ef910c366b46e2d1cf33429611dbf28ef0362aa0`:
    added 11, pruned 0, moved 0. Settings, filters, `generated_at` and every
    other file's entries are identical.
  - Per file:
    - the constructor: 1 (`ACCEPTED_SHA256`);
    - the proposal: 6 public release-binding hashes, exactly the set
      baselined for `issue-5d-equipment-cited-targets-PROPOSAL.json`;
    - the DELTA: 4 (`proposal_identity` ×2, `semantic_diff_hash`,
      `schema_hash`);
    - this packet: 0.
  - Staged by name. The hook ran twice on the four relative paths plus
    `.secrets.baseline`, EXIT 0 both times, with the baseline hash stable
    (`.claude/_sp/ece/bl/hook1.log`, `hook2.log`).

## Not done

- No recording, acceptance, commits, push, publication or activation.
- No reordering.
- No source errata encountered.
