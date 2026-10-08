# CRD Issue 5d — finite reference atoms: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept the exact five finite-reference replacement proposals, retaining 52 reference findings, zero uncovered leaves, and the partial-publication block.

**Approval time:** the statement preceded the parent's verification at 2026-09-30T00:02:27Z. No more precise message time is claimed. The recorded action carries its real execution UTC time.

**Owner files.** The parent verified all eight files of `finite-reference-atoms-owner-manifest.json` (SHA-256 `14d5716d5cd52f9e208dbd677069bc5c021435b3351ae8c1aacf817040e1c235`, rechecked by this task) against disk. The ACCEPT script pins every one of them and asserts the pins on every run:

| File | SHA-256 |
|---|---|
| `issue-5d-finite-reference-atoms-REPLACEMENT.py` (constructor) | `01b5d7669769c361bb17ee57bebfabf474e45614f6b60580cf70830044b34a12` |
| `issue-5d-classes-finite-reference-atoms-PROPOSAL.json` (identity `45c355850a7e74283f4556b0ab980244935c7a2e3d313a5fbb9cc7dc0a6a8b60`) | `89061117d1b13c2823056a23e72720374e94b13c92f156b4b6d8703e11a73b54` |
| `issue-5d-character-origins-feats-finite-reference-atoms-PROPOSAL.json` (identity `17ed7fd338d2d52e77c227215e5f095aadfa0c50e918edd26d7b25277c87c813`) | `8e5db24b651a53cf8da4300b8ab5d592d23a5670b4b4f81bcd0e2860ee023c83` |
| `issue-5d-spell-descriptions-finite-reference-atoms-PROPOSAL.json` (identity `20ee428e126b8b33b1399ebddc21f27212609658672a0fdb4b5a6b6dabc955ca`) | `fddde0cfbee8e8a4d2bc616bf553e90b648f56cd14a805c55cb1f087761659e6` |
| `issue-5d-magic-items-finite-reference-atoms-PROPOSAL.json` (identity `48cb3c4726d395f06dd2ca639a50d001e5491b307fa3176618850d04ce04ca71`) | `4aa393a42f93942f358e3012964b0b65432fd544be80fd3c2c2a2adeae3f97eb` |
| `issue-5d-monsters-finite-reference-atoms-PROPOSAL.json` (identity `e39e622107d443713d17e25bc64f73210241af3f83d4cd86cf73132eaf4de327`) | `f6ec2a0e7618e3267d95fa9343848b528a2b823e36e5ab02733867051a396c8c` |
| `issue-5d-finite-reference-atoms-DELTA.txt` (102 lines) | `50c2f78cf324eb7dac30b94591c8e6c0f3658caee1b539ea0241f334442cda25` |
| `issue-5d-finite-reference-atoms-review.md` (packet) | `0dae267a3cdfda79c0638f5ab456506eca17241ba89ee6a2963493862e15a33c` |

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Batches / records / spans / units / resolutions | Reference / uncovered-leaf findings |
|---|---|---|---|
| prior (Character Creation catalogue recording) | `ea0c219feec8571142c797ebd127713d55595db7309c64670a1436756b4413de` | 24 / 1835 / 10492 / 1476 / 1440 | 62 / 0 |
| **recorded (final, on disk)** | **`005768c282669c3acf564b3efd70d1c54aa7307f4e47505b77b67e8612d73b84`** | **24 / 1835 / 10492 / 1476 / 1440** | **52 / 0** |

Other findings: 0. Reference-resolution violations: 0. The partial-publication block stands. #48 "Monsters" stays unresolved among the 52.

**Simulated state.** `490ac660f7bb8e01cbed2053cb10ac46b00c2276ab4182ebe4bf626e30139b47` is the reviewed packet's composition under the simulated reviewer. `_precheck` asserts the ACCEPT script's composition reproduces it byte for byte before any write. It was never written.

## Recorded action (real UTC)

Script: `.claude/review-notes/issue-5d-finite-reference-atoms-ACCEPT.py`, final sha `89b5bac0954c594d1e46862e3526cb9e030c72113940db85c42d86f5062b1152`. Logs: `.claude/_sp/fra/rec/`.

| Action | Log | Result |
|---|---|---|
| first `--simulate` (no log kept) | — | Failed before any write: the batch-order check compared a loaded file (batches listed by id) with the in-memory chain (acceptance order). Fixed by checking order on the in-memory replay in `_precheck` and comparing by id in `_check` |
| `--simulate`, final | `simulate.txt` (00:15:17Z) | EXIT 0; nothing written |
| `record-finite-reference-atoms` | `record.txt` (end 00:19:54Z) | EXIT 0; `accepted_at` **2026-09-30T00:18:19Z**; `005768c2…`; post-write `_state()` and `verify` pass |
| `--verify` against the pins, over the replayed prior | `verify.txt` (00:22:31Z) | EXIT 0 |
| Character Creation catalogue `--verify` | `cc-verify.txt` | EXIT 1: `recorded artifact drifted` (expected refusal) |

Before the write the prior bytes were copied to `.claude/_sp/fra/rec/prior-ea0c219f.json` (scratch, sha `ea0c219f…`). Nothing was re-recorded. `RECORDED_AT` and `RECORDED_SHA256` were pinned after the write, from the values the run printed and read back.

**Recording shape.**
- One native write. There is no supersession, so the whole chain is re-composed over no prior exactly as the reviewed constructor composes it: the twenty-four batches in recorded order at recorded evidence, every recorded resolution step re-applied verbatim, and the five candidates `accept_proposal`-ed at their existing positions with `rule` = the verbatim statement, `reviewer` = the Owner, `accepted_at` = the UTC clock read once.
- No resolution drafted, re-keyed or dropped.
- **Prior.** The oracle is untracked, so after the write `ea0c219f…` exists only as a replay: `CC.resolved(CC.composed(CC.prior(), OWNER, 18:51:30Z), OWNER, 18:51:34Z)`, sha-asserted. `--verify` and the tests use it.
- `_precheck` runs every post-write check on the Owner's composition at a placeholder time; `verify` refuses the placeholder time and the simulated bytes; `_approvals` requires each changed batch's rule to be the statement and every span and unit acceptance of it to name the Owner.

**Actual vs simulated approval** (`sim-vs-recorded.txt`, keyed by batch/span/unit/resolution id): every non-acceptance section and every other acceptance key is identical. The only differences are on the five changed batches: 5 batch `rule`s (simulation text → the statement), and `reviewer` (`SIMULATION - not an Owner approval` → `Ravenlok (Owner)`) and `accepted_at` (`2026-09-26T00:00:00Z` → `2026-09-30T00:18:19Z`) on 7728 span records (classes 1028, character-origins-feats 172, spell-descriptions 2050, magic-items 1339, monsters 3139) and 1094 review-unit records (36, 33, 340, 271, 414). No resolution record differs.

## Preservation and replay evidence

From `record.txt` and `verify.txt`:

- **Nineteen unchanged batches and all resolutions.** `_kept(prior, final)` over batches, span records, review-unit records, resolution records and resolutions, outside the five batches, as multisets with evidence: empty. Resolutions are also verbatim and in order (1440).
- **Batches.** Same batch set; the nineteen other identities unchanged; the five identities are the pinned candidates. Acceptance order equals the recorded chain's (`_precheck`).
- **Findings.** Compared as multisets, exactly ten cleared — `classes:'Bard, Cleric, Druid, and Wizard spell lists'` 1, `classes:'Cleric, Druid, or Wizard spell list'` 2, `equipment:'Equipment'` 3, `monsters:'Monsters'` 2, `rules-glossary:'Rules Glossary'` 2 — nothing new. 52 / 0, other 0.
- **Source and meaning.** `RR.owned` (prose bindings) and `RR.expectations` unchanged; consumer reading unchanged with no override and under both reviewed overrides.
- **Delta.** `REPL.Delta(prior, final).report()` equals the reviewed DELTA line for line (102 lines); the report blanks reviewer, times and rule, and there is no new resolution, so no authorizer normalization was needed.
- **Reload.** The recorded file reloads to the same bytes.

The candidate, source, projection and native-contract evidence was reused as reviewed and not rerun.

## Moved pins (historical checks kept)

| File | Change |
|---|---|
| `tests/ingestion/mechanical/_replacement_chain.py` | Loads `FINITE_REFERENCE`. `COMMITTED_SHA256` now points to its recorded sha. Adds `character_creation_recorded()` (the replayed prior). Docstring updated. |
| `test_animals_proposal.py` | The live CC test becomes the historical `test_the_character_creation_catalogue_recording_rebuilds` (replay = `ea0c219f…`, `CC._check`). New test: `test_the_committed_oracle_records_finite_reference_atoms`. |
| `test_committed_accepted_authority.py` | The named identity set drops the five replaced identities and adds the five accepted ones. The explicit character-origins-feats and classes `proposal_identity` entries are removed; those batches are now named by the finite-reference proposals. |
| `test_classes_proposal.py` | The committed classes batch must be the finite-reference candidate with the statement as its rule. The historical classes / class-option-catalogues identity, rule and acceptance checks read `character_creation_recorded()` instead of the committed file; the resolution-authorization check still reads the committed file. |
| `src/.../oracles/README.md` | Current state and history entry updated. |

## Gates (raw)

- **ACCEPT script.** Black 0, Ruff 0, `mypy --strict` (`MYPYPATH=src`) 0.
- **Black and Ruff, rerun at 01:43:42Z–01:43:43Z** on the ACCEPT script and the four edited test files: `black --check` EXIT 0 (5 files unchanged), `ruff check` EXIT 0.
- **Last writes.** ACCEPT script 00:20:01Z, `_replacement_chain.py` 00:22:49Z, `test_animals_proposal.py` 00:51:45Z (a Black blank-line insertion only, 27 s after `pytest2` started), `test_committed_accepted_authority.py` 01:29:00Z, `test_classes_proposal.py` 01:29:17Z.
- **`pytest1.txt`: interrupted, no evidence.** The run was cut off by the app restart with a 0-byte log and no result, and is not counted.
- **Focused pytest `pytest2.txt`** (15 node ids, `-p no:cacheprovider`, 00:51:18Z–01:28:26Z): **2 failed, 13 passed in 2222.26s**, EXIT 1 (coverage 44.09%).
  - The ids:
    - `test_animals_proposal`: the Animals, Character Creation catalogue (historical) and finite-reference tests;
    - `test_character_origins_feats_acceptance::test_the_recorded_bytes_are_what_the_two_seams_record`;
    - `test_gameplay_toolbox_proposal`, `test_monsters_proposal`, `test_classes_proposal`, `test_spell_descriptions_proposal` and `test_rules_glossary_completion_proposal`: `::test_the_committed_oracle_records_the_owner_acceptance`;
    - `test_magic_items_proposal::test_accepted_then_resolved_in_memory_preserves_everything` and `::test_the_committed_oracle_records_the_owner_acceptance`;
    - `test_committed_accepted_authority::test_no_refused_candidate_is_selectable`;
    - `test_source_release_readiness::test_the_replacement_release_has_only_the_two_pilot_authorities`;
    - `test_checks_actions_rests_proposal::test_once_accepted_the_draft_resolves_through_the_native_seam`;
    - `test_reference_resolution::test_the_accepted_corpus_is_untouched_by_this_capability`.
  - The two failures were unmoved pins:
    - `test_classes_proposal::test_the_committed_oracle_records_the_owner_acceptance`: the committed classes identity is now `45c35585…`, not `c98ed194…`;
    - `test_committed_accepted_authority::test_no_refused_candidate_is_selectable`: the explicit origins-feats and classes identities (`8ce96240…`, `c98ed194…`) were still named.
  - Both were fixed as in the Moved pins table.
- **Rerun of the two failed ids, `pytest3.txt`** (01:29:29Z–01:43:23Z, after both fixes): **2 passed in 830.04s**, EXIT 1.
  - The exit 1 is only the repo-wide `--cov-fail-under=80` (42.63%); no test failed.
  - The thirteen that passed in `pytest2` were not rerun: none of their files changed after it started, apart from the blank line above.
- **Not run: broad suite.** Not green is claimed.
- **Deferred, not green:** pip-audit and expanded mypy.
- **detect-secrets.**
  - A scoped scan with `PYTHONUTF8=1` covered the ACCEPT script, the oracle, the four edited test files, the README and this note.
  - It found 21 new public hashes, and every value was recovered with its name:
    - the ACCEPT script's 16: the constructor, the five identities and five PROPOSAL shas, the DELTA, review, simulated, owner-manifest and recorded shas;
    - the oracle's 5: the five accepted `proposal_identity` values.
  - It found 5 obsolete oracle entries, on the same five lines: the replaced identities, which are no longer in the file. They were pruned.
  - The baseline went from `1c08091d…` to `cd0c21770f941ae5a53bb3c4ce0c84ed91299e406440dc4e6d73adfec7b7a1ba`.
    - The line numbers of 790 oracle entries and 3 `test_animals_proposal.py` entries were refreshed.
    - Settings, filters, `generated_at` and the other 152 files are identical.
  - The baseline is staged by name. Evidence is in `.claude/_sp/fra/rec/bl/`, including the logs of both hook runs.

## Limits

- Nothing is committed, pushed, merged, published or activated.
- The release order is scheduled for one bounded pass after the packets, before publication.
- The other 52 reference findings, #48 among them, stay; held rows are as the packet dispositions them.
- No source errata were encountered.
