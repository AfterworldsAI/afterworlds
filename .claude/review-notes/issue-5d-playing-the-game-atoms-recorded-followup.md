# CRD Issue 5d — Playing the Game atoms: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept the exact two Playing the Game replacement proposals, retaining 49 reference findings, zero uncovered leaves, and the partial-publication block.

**Approval time:** the statement preceded the parent's fresh verification at 2026-09-30T04:58:23Z. No more precise message time is claimed. The recorded action carries its real execution UTC time. No renewed Owner approval was sought; a Codex complementary review follows.

**Owner files.** `playing-the-game-atoms-owner-manifest.json` (Codex task directory, SHA-256 `27271be7f3b14f7b6111da5f46d26751f842c2eb6773894ed253f7bbd10a679d`, rechecked on disk by this task before the write) lists the five files below, 49 expected reference findings, 0 uncovered leaves and the partial-publication block. The ACCEPT script asserts the constructor pin at import, the two PROPOSAL pins (and identities) and the DELTA and review pins on every run. The manifest sha is a documentary pin in the script; it is not asserted, because the manifest is outside the repository.

| File | SHA-256 |
|---|---|
| `issue-5d-playing-the-game-atoms-REPLACEMENT.py` (constructor) | `23a9442c19eb0a39e01a351da1b89a41b62730f0940983a1f93547b77bcc8ea9` |
| `issue-5d-core-play-dependencies-playing-the-game-atoms-PROPOSAL.json` (identity `9aa7d0097fcf4cd64cbed630828eeca72606fc9c1818cde42a44f106accf6eac`) | `7a2344959a133319b60d720b7eab9d407c5c34907b5c585952a969bec510d210` |
| `issue-5d-monsters-playing-the-game-atoms-PROPOSAL.json` (identity `d6eff4f4858efd5da983dbdbbce85c2b9ddd6d20ed810c10d044087b3b66f91d`) | `69de9bc2875f0fed9483654d296a3ff3480f13da8a87345143d4a90d3640b633` |
| `issue-5d-playing-the-game-atoms-DELTA.txt` (42 lines) | `e34690675925d6a08ff233e479104a531255e4e7c2fda06dee4045ebf28ef8b9` |
| `issue-5d-playing-the-game-atoms-review.md` (packet) | `cc90bad0ae7a14dbe5487dd0151eafe03aaa5af5a803c609064f09763fa9a8f5` |

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Batches / records / spans / units / resolutions | Reference / uncovered-leaf findings |
|---|---|---|---|
| prior (finite-reference atoms recording) | `005768c282669c3acf564b3efd70d1c54aa7307f4e47505b77b67e8612d73b84` | 24 / 1835 / 10492 / 1476 / 1440 | 52 / 0 |
| **recorded (final, on disk)** | **`92b7a68fcd6ea622ac3ef79b1dacd939f7be52fa445fcbdafd5adc8c77352e19`** | **24 / 1835 / 10492 / 1476 / 1440** | **49 / 0** |

Other findings: 0. Reference-resolution violations: 0. The partial-publication block stands.

**Simulated state.** `7254578d708261c14e3a33935e505af01a4a0b0c15b8c73c84e23db134d25a08` is the reviewed packet's composition under the simulated reviewer. `_precheck` asserted the ACCEPT script reproduces it byte for byte before the write. It was never written.

## Recorded action (real UTC)

Script: `.claude/review-notes/issue-5d-playing-the-game-atoms-ACCEPT.py`, final sha `25b2ab8eadd8901b54ccfdb39e1f197641cb45505f31625a06f039313bcb67fd`. Logs: `.claude/_sp/pga/rec/`; exit codes captured from the process object into `*.exit`.

| Action | Log | Result |
|---|---|---|
| `record-playing-the-game-atoms` (log opened 05:06:04Z) | `record.txt`, `record.err` (empty) | EXIT 0; `accepted_at` **2026-09-30T05:09:01Z**; `92b7a68f…`; the pre-write `_precheck` and the post-write `_state()` and `verify` pass |
| `--verify` against the pins, over the replayed prior | `verify.txt`, `verify.err` (empty) | EXIT 0 |
| finite-reference atoms `--verify` | `fra-verify.err` | EXIT 1: `AssertionError` in `_read_back` (two of its five identities are no longer the file's): expected refusal |
| actual vs simulated comparison | `sim-vs-recorded.txt` (`sim_vs_rec.py`) | EXIT 0 |

No separate `--simulate` was run; `_precheck` inside the record path is that gate. Before the write the prior bytes were copied to `.claude/_sp/pga/rec/prior-005768c2.json` (scratch, sha `005768c2…`). Nothing was re-recorded. `RECORDED_AT` and `RECORDED_SHA256["recorded"]` were pinned after the write, from the values the run printed and read back, then Black, Ruff and `mypy --strict` were rerun on the script (all EXIT 0).

**Recording shape.**
- One native write. There is no supersession, so the whole chain is re-composed over no prior exactly as the reviewed constructor composes it: the twenty-four batches in recorded order at recorded evidence (the four other finite-reference batches at `2026-09-30T00:18:19Z` under their statement), every recorded resolution step re-applied verbatim, and the two candidates `accept_proposal`-ed at their existing positions with `rule` = the verbatim statement, `reviewer` = `Ravenlok (Owner)`, `accepted_at` = the UTC clock read once.
- No resolution drafted, re-keyed or dropped. (The `re-keyed recorded resolutions dropped from steps …` stdout line is the reviewed constructor's step builder reporting the already-recorded re-keys it skips, as in every prior replay.)
- **Prior.** The oracle is untracked, so after the write `005768c2…` exists only as a replay: `FINITE_REFERENCE.composed(OWNER, 2026-09-30T00:18:19Z)`, sha-asserted. `--verify` and the tests use it.

**Actual vs simulated approval** (`sim-vs-recorded.txt`, keyed by batch/span/unit/resolution id, not serialized position): 7262 differing leaves, all on the two changed batches; batch order identical; no resolution record differs. The only differences:

| Batch | `rule` | span records (`reviewer`, `accepted_at`) | review-unit records (`reviewer`, `accepted_at`) |
|---|---|---|---|
| core-play-dependencies | 1 | 66 | 11 |
| monsters | 1 | 3139 | 414 |

`rule`: `SIMULATION ONLY: in-memory composition check; records no acceptance` → the statement. `reviewer`: `SIMULATION - not an Owner approval` → `Ravenlok (Owner)`. `accepted_at`: `2026-09-26T00:00:00Z` → `2026-09-30T05:09:01Z`.

## Preservation and replay evidence

From `record.txt` and `verify.txt`:

- **Twenty-two unchanged batches and all resolutions.** `_kept(prior, final)` over batches, span records, review-unit records, resolution records and resolutions, outside the two batches, as multisets with evidence: empty. Resolutions verbatim and in order (1440).
- **Batches.** Same batch set; the twenty-two other identities unchanged; the two identities are the pinned candidates. Acceptance order equals the recorded chain's.
- **Findings.** Compared as multisets, exactly three cleared — `srd-5.2.1/playing-the-game:'Playing the Game'` ×3 (#68/#69/#70) — nothing new. 49 / 0, other 0.
- **Source and meaning.** `RR.owned` (prose bindings) and `RR.expectations` unchanged; consumer reading unchanged with no override and under both reviewed overrides (`disable-glossary.stat_block-record`, `disable-monsters.parts_of_a_stat_block-ability_scores`).
- **Delta.** `REPL.Delta(prior, final).report()` equals the reviewed DELTA line for line (42 lines): the three retired *Playing the Game* pointers and the seven new atom citations only. The existing #70 singular `saving throw` glossary citation is not in the delta, so it is kept unchanged, as is every other identity and its provenance.
- **Reload.** The recorded file reloads to the same bytes.

The candidate, source, projection and native-contract evidence was reused as reviewed and not rerun.

## Moved pins (historical checks kept)

| File | Change |
|---|---|
| `tests/ingestion/mechanical/_replacement_chain.py` | Loads `PLAYING_THE_GAME` (module `playing_the_game_atoms_accept`). `COMMITTED_SHA256` now points to its recorded sha. Adds `finite_reference_recorded()` (the replayed prior). Docstring updated. |
| `test_animals_proposal.py` | The live finite-reference test becomes the historical `test_the_finite_reference_atoms_recording_rebuilds` (replay = `005768c2…`, `FINITE_REFERENCE._check`, 52 / 0). New: `test_the_committed_oracle_records_playing_the_game_atoms` (49 / 0). |
| `test_committed_accepted_authority.py` | The named identity set drops the two replaced identities (remaining-references core-play-dependencies, finite-reference monsters) and adds the two accepted ones. |
| `src/.../oracles/README.md` | Current state (`92b7a68f…`, 49) and history entry. |

`test_classes_proposal.py` and the other committed-oracle tests needed no change (classes and the other batches are kept).

## Gates (raw)

- **ACCEPT script.** Black 0, Ruff 0, `mypy --strict` (`MYPYPATH=src`) 0, before and after pinning.
- **Black `--check` and Ruff, rerun at 06:03:30Z** on the ACCEPT script and the three edited test files: EXIT 0 (4 files unchanged), EXIT 0.
- **Last writes.** ACCEPT script 05:10:59Z, `_replacement_chain.py` 05:19:10Z, `test_committed_accepted_authority.py` 05:19:53Z, README 05:20:01Z, `test_animals_proposal.py` 05:20:15Z (Black); all before the pytest start.
- **Focused pytest `pytest.txt`** (15 node ids, `-p no:cacheprovider`, 05:20:48Z–06:03:13Z): **15 passed in 2525.58s**, EXIT 1. The exit 1 is only the repo-wide `--cov-fail-under=80` (44.09%); no test failed. `pytest.err` empty.
  - `test_animals_proposal`: `test_the_character_creation_catalogue_recording_rebuilds`, `test_the_finite_reference_atoms_recording_rebuilds`, `test_the_committed_oracle_records_playing_the_game_atoms`;
  - `test_character_origins_feats_acceptance::test_the_recorded_bytes_are_what_the_two_seams_record`;
  - `test_gameplay_toolbox_proposal`, `test_monsters_proposal`, `test_classes_proposal`, `test_spell_descriptions_proposal`, `test_rules_glossary_completion_proposal`: `::test_the_committed_oracle_records_the_owner_acceptance`;
  - `test_magic_items_proposal::test_accepted_then_resolved_in_memory_preserves_everything` and `::test_the_committed_oracle_records_the_owner_acceptance`;
  - `test_committed_accepted_authority::test_no_refused_candidate_is_selectable`;
  - `test_source_release_readiness::test_the_replacement_release_has_only_the_two_pilot_authorities`;
  - `test_checks_actions_rests_proposal::test_once_accepted_the_draft_resolves_through_the_native_seam`;
  - `test_reference_resolution::test_the_accepted_corpus_is_untouched_by_this_capability`.
- **Reused, not rerun:** the candidate write/verify logs (identical 38 lines, empty stderr, final assertion reached; process exit codes not captured), constructor Black/Ruff/strict mypy, and the candidate's two hook runs (EXIT 0) and baseline change `cd0c2177…` → `bda93756…`.
- **Not run: broad suite.** Not green is claimed.
- **Deferred, not green:** pip-audit and expanded mypy.
- **detect-secrets.**
  - A scoped scan with `PYTHONUTF8=1` covered the seven files of `.claude/_sp/pga/rec/bl/files.txt`: the ACCEPT script, this note, the oracle (1013 findings scanned, so it was not skipped), the README and the three edited test files.
  - It found 12 new public hashes, and every value was recovered with its name:
    - the ACCEPT script's 10: the constructor, the two identities and two PROPOSAL shas, the DELTA, review, simulated, owner-manifest and recorded shas;
    - the oracle's 2: the two accepted `proposal_identity` values.
  - It found 2 obsolete oracle entries, on the same lines (23406, 62425): the replaced identities `8fce546d…` (remaining-references core-play-dependencies) and `e39e6221…` (finite-reference monsters), confirmed by SHA-1 against the prior copy. They were pruned.
  - 822 line numbers were refreshed (819 oracle, 3 `test_animals_proposal.py`). Settings, filters, `generated_at` and the other 157 files are identical; keys stay backslash-only.
  - The baseline went from `bda93756…` to `377dc292cb49de9976604039fc29cc49f53f63b070b8a07006c7544941c5203a`, staged by name.
  - The hook (relative paths, `PYTHONUTF8=1`) ran twice after the update: EXIT 0, EXIT 0, no output, baseline sha unchanged. It was rerun twice after this note was finalized; those final runs are in the report and `.claude/_sp/pga/rec/bl/final-hook*.log`.

## Limits

- Nothing is committed, pushed, merged, published or activated.
- The release order is scheduled for one bounded pass after the packets, before publication.
- The other 49 reference findings stay; held rows are as the packet dispositions them.
- No source errata were encountered.
