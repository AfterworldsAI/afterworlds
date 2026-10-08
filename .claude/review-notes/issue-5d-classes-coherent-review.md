# CRD Issue 5d — Classes — coherent review handoff (consolidated correction)

**Status.** This revision corrects the UNACCEPTED Classes packet on the four consolidated findings.
- Nothing is accepted, recorded, committed, pushed or published.
- The only newly staged file is `.secrets.baseline`.
- The full evidence is in `issue-5d-classes-REVIEW-PACKET.md`.

## For independent coordinating Codex review

| Artifact | Identity | File SHA-256 |
|---|---|---|
| `issue-5d-classes-PROPOSAL.json` | `025016704fbca10a7673e0040309a772d56780da434013588cd34fcafd4ffc87` | `08c8c91d…2ba7` |
| `issue-5d-class-option-catalogues-PROPOSAL.json` | `3dae09105c4f2e30f0c1c902fef76155974f61320f8283904c2ef241072a3293` | `7172ae1a…cf82` |
| `issue-5d-classes-resolutions-DRAFTS.json` | 1 draft, unchanged: Elf "Wizard spell list" → `classes.wizard` | `516e141f…f63c` |

**Coverage:** 1174 of 1175 leaves; the one left out is `# Classes`. **The accepted oracle is untouched**
(`962d6aee…18b8`). The composition preserves exactly 295 records and 50 resolutions.

## What changed

1. ***Defensive Tactics*.** It is now a *Hunter* member. It reads `#### Level 7: Defensive Tactics` first,
   is one record, and the Hunter read reaches it. Ranger does not reach it (settled one-hop reach). This
   uses a bounded helper extension, `record_containers`, and the membership and exact-source checks are
   kept.
2. **Entry headings.** All 77 placement headings are now read by the record they name: class, subclass,
   multiclass, *Defensive Tactics*, and catalogue and option names. Only the 12 subclass mottos stay
   excluded. There are no duplicate reads, and a disabled subclass is not read back.
3. **References.** A reference goes to an exact record or stays unresolved; it is never widened.
   - 44 equipment references are now unresolved: 42 named items without records and the 2
     "(see Equipment)" pointers. "(see Playing the Game)" is also unresolved.
   - The "Starting Equipment" label references were removed.
   - The spurious "Temporary Hit Points" → `hit_points` references were fixed.
4. **Progression (B6).** Each class has a MIXED `progression` component carrying facts with the existing
   types: 752 `ProgressionEntryFact` and 680 `SpellSlotProgressionFact`. These meet Canary 5 (*level-indexed
   entitlements and feature references reconstruct correctly*), and a test proves the reconstruction.
   - The Proficiency Bonus, dice, damage and distance columns and the Mystic Arcanum spell level stay as
     prose.
   - The reason is `no_identified_structured_use`, and the evidence is recorded.

**Unresolved: 1088.** Spells 1026, equipment 44, monsters 9, animals 5, class-list phrases 3, Playing the
Game 1. The previous count was 1043.

**B labels reclassified.**
- **Fixed:** B3, B3a, B8.
- **Supplied:** B6.
- **Retained findings:**
  - B1 and the absent Monster, Animal and item records;
  - B9/B10, the ambiguous references;
  - B7's release-marker defect, recorded separately.
- **Settled:** B2, B4, B5, B11, B12, the Channel Divinity split, and the floated tables.

**Helper change.** `authoring.py` already carried uncommitted modifications. This run's own delta is
+60/−10 against `.claude/_sp/cls/authoring-before.py`, in `.claude/_sp/cls/authoring-mine.diff`.

## Gates on the final head

| Gate | Result |
|---|---|
| `test_classes_proposal.py` (final bytes) | 26 passed. An earlier run had 2 test-expectation errors, now corrected (see the packet). |
| Helper regression (the 18 other test files importing `authoring`) | 495 passed |
| Generator re-run after Black | byte-identical |
| Black, Ruff, mypy strict | clean |
| CR check | 0 CR |
| pip-audit | **deferred, not green** (31 findings in 11 packages) |

Broad accepted-material, *Casting Spells* and shared-coverage suites were not run; they are scheduled
after 5d.

### Secrets baseline (scoped maintenance)

| | Before | After |
|---|---|---|
| SHA-256 | `81560f20…f76f` | `d3751292…8fd7` |
| Files / entries | 70 / 1584 | 70 / 2161 |

**Delta: 579 added, 13 line-refreshed, 2 pruned.** It is in `.claude/_sp/cls/baseline-delta2.json`, and
the verification is in `bl_verify2.json`.
- **Added:**
  - 577 fact keys in the Classes proposal's fact provenance. Each was recomputed natively with
    `representation.fact_key`, and each sits in a `"target_kind": "fact"` provenance. The accepted oracle
    has the same kind of baselined entries.
  - The 2 new proposal identities in the test, recomputed natively.
- **Pruned:** the 2 superseded identities (old classes and options), each matched by SHA-1.
- **Preserved and asserted:**
  - `version`, `plugins_used`, `filters_used` and `generated_at` are unchanged;
  - every untouched file is identical;
  - the key order is kept;
  - every `is_verified` flag is kept.

The scan used the baseline's own plugins and filters on a private copy, deleted afterwards. It never ran
`detect-secrets scan --baseline`, and added no pragmas. `.secrets.baseline` was staged by name.

**Hook** (`detect-secrets-hook` v1.5.0, `--baseline .secrets.baseline`):
- the staged set, twice: exit 0, exit 0. The staged added or modified set is `.secrets.baseline` only; the pre-existing staged deletions have no content to scan.
- the 9 candidates plus the baseline, twice: exit 0, exit 0. The baseline hash was stable across the runs (`d3751292…8fd7`), and a re-probe shows 0 new, 0 obsolete and 0 moved findings.
- After the final test-comment edit, one more run each: candidates exit 0, staged exit 0. The re-probe again shows 0 new, 0 obsolete and 0 moved.

## Untouched

- `issue-5d-source-correction-REPLACEMENT-PACKET.md`
- the quarantined oracle
- the pre-existing staged deletions
- the unrelated ` M` files
- the 4 stashes

## Next

1. Independent coordinating Codex review.
2. Owner semantic acceptance.
3. Only after that: native recording.
