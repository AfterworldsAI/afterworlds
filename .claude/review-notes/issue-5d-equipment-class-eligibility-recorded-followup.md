# CRD Issue 5d — Equipment class eligibility: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept the exact Equipment class-eligibility replacement proposal, retaining 46 reference findings, zero uncovered leaves, and the partial-publication block.

**Approval time:** the statement preceded the parent's fresh verification at 2026-09-30T07:43:59Z. No more precise approval time is claimed; `APPROVAL_BEFORE` in the script is documentary and is never recorded. The recorded action carries its real execution UTC time. No renewed Owner approval was sought; a Codex complementary review follows.

**Owner files.** `equipment-class-eligibility-owner-manifest.json` (Codex task directory, SHA-256 `c7daa098c17d5e0c2f9b13e8fa9309be8d4e07c7952d6497a98c5dc3e9ca19ce`, rechecked on disk before the write and again after it) lists the four files below, 46 expected reference findings, 0 uncovered leaves and the partial-publication block. The ACCEPT script asserts the constructor pin at import, and the PROPOSAL pin (and identity) and the DELTA and review pins on every run. The manifest sha is a documentary pin in the script; it is not asserted, because the manifest is outside the repository.

| File | SHA-256 |
|---|---|
| `issue-5d-equipment-class-eligibility-REPLACEMENT.py` (constructor) | `bdc8a24e87614ef98c0545d81dd52a36b397396e11daa0408f8f6c9dae4a062b` |
| `issue-5d-equipment-class-eligibility-PROPOSAL.json` (identity `d7c012dfc96aad5c34e1630a8acedee83b6626311167f5ed256e3126d74456f3`) | `2cafbccec28990a93270bdd09c7546782448df2dd52376fbc7e1f4079457aa08` |
| `issue-5d-equipment-class-eligibility-DELTA.txt` (17 lines) | `9e29c197f09657a9d48447753cd8bec7ac90eb1e47291ff73844ce358784d908` |
| `issue-5d-equipment-class-eligibility-review.md` (packet) | `78ce2284b0432c1c29d2aa3a1fc6e1a33b5f6095d31d9d608896701455f515a6` |

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Batches / records / spans / units / resolutions | Reference / uncovered-leaf findings |
|---|---|---|---|
| prior (Playing the Game atoms recording) | `92b7a68fcd6ea622ac3ef79b1dacd939f7be52fa445fcbdafd5adc8c77352e19` | 24 / 1835 / 10492 / 1476 / 1440 | 49 / 0 |
| **recorded (final, on disk)** | **`5f37fb080a8493a1acb6584ef9bd2297c388d34683200bd7f486007ade668676`** | **24 / 1835 / 10492 / 1476 / 1440** | **46 / 0** |

Other findings: 0. Reference-resolution violations: 0. The partial-publication block stands.

**Simulated state.** `dc2931f86e4bf83202a3c5c3a6fcdb1c73f409d8ededfbe8ee846811d69403e5` is the reviewed packet's composition under the simulated reviewer. `_precheck` asserted the ACCEPT script reproduces it byte for byte, in `--simulate` and again in the record path before the write. It was never written.

## Recorded action (real UTC)

Script: `.claude/review-notes/issue-5d-equipment-class-eligibility-ACCEPT.py`, final sha `4b7a0705fc251fa3bb7b46260d1a9880fb5e01c0e9b65dafece4757fe3826c26`. Logs: `.claude/_sp/ece/rec/`; exit codes captured from the process object into `*.exit`.

| Action | Log | Result |
|---|---|---|
| `--simulate` (in memory, nothing written) | `simulate.txt`, `simulate.err` (empty) | EXIT 0; prior 49 / 0; simulated bytes `dc2931f8…`; every post-write check passes at the placeholder time |
| `record-equipment-class-eligibility` (launched 07:52:54Z, returned 07:57:40Z) | `record.txt`, `record.err` (empty) | EXIT 0; `accepted_at` **2026-09-30T07:55:56Z**; `5f37fb08…`; the pre-write `_precheck` and the post-write `_state()` and `verify` pass |
| `--verify` against the pins, over the replayed prior | `verify.txt`, `verify.err` (empty) | EXIT 0 |
| Playing the Game atoms `--verify` | `pga-verify.err` | EXIT 1: `AssertionError: drifted` in `_state` (the file's equipment identity is no longer its chain's): expected refusal |
| actual vs simulated comparison | `sim-vs-recorded.txt` (`sim_vs_rec.py`) | EXIT 0 |

Before the write the prior bytes were copied to `.claude/_sp/ece/rec/prior-oracle.json` (scratch, sha `92b7a68f…`). Nothing was re-recorded. `RECORDED_AT` and `RECORDED_SHA256["recorded"]` were pinned after the write, from the values the run printed and read back, then Black, Ruff and `mypy --strict` were rerun on the script (all EXIT 0).

**Recording shape.**
- One native write. There is no supersession, so the whole chain is re-composed over no prior exactly as the reviewed constructor composes it: the twenty-four batches in recorded order at recorded evidence (the finite-reference batches at `2026-09-30T00:18:19Z` and the Playing the Game batches at `2026-09-30T05:09:01Z`, each under its own statement), every recorded resolution step re-applied verbatim, and the Equipment candidate `accept_proposal`-ed at its existing position with `rule` = the verbatim statement, `reviewer` = `Ravenlok (Owner)`, `accepted_at` = the UTC clock read once.
- No resolution drafted, re-keyed or dropped. (The `re-keyed recorded resolutions dropped from steps …` stdout line is the reviewed step builder reporting the already-recorded re-keys it skips, as in every prior replay.)
- **Prior.** The oracle is untracked, so after the write `92b7a68f…` exists only as a replay: `PLAYING_THE_GAME.composed(OWNER, 2026-09-30T05:09:01Z)`, sha-asserted. `--verify` and the tests use it.

**Actual vs simulated approval** (`sim-vs-recorded.txt`, keyed by batch/span/unit/resolution id, not serialized position): 967 differing leaves, all on the equipment batch; batch order identical; no resolution record differs (the 161 equipment-cited resolutions keep their recorded evidence). The only differences:

| Batch | `rule` | span records (`reviewer`, `accepted_at`) | review-unit records (`reviewer`, `accepted_at`) |
|---|---|---|---|
| equipment | 1 | 469 | 14 |

`rule`: `SIMULATION ONLY: in-memory composition check; records no acceptance` → the statement. `reviewer`: `SIMULATION - not an Owner approval` → `Ravenlok (Owner)`. `accepted_at`: `2026-09-26T00:00:00Z` → `2026-09-30T07:55:56Z`.

## Preservation and replay evidence

From `record.txt` and `verify.txt`:

- **Twenty-three unchanged batches and all resolutions.** `_kept(prior, final)` over batches, span records, review-unit records, resolution records and resolutions, outside equipment, as multisets with evidence: empty. Resolutions verbatim and in order (1440). Playing the Game's historical evidence is kept unchanged.
- **Batches.** Same batch set; the twenty-three other identities unchanged; the equipment identity is the pinned candidate. Acceptance order equals the recorded chain's.
- **Findings.** Compared as multisets, exactly three cleared — `srd-5.2.1/classes:'Cleric or Paladin'` (#13), `'Druid or Ranger'` (#16), `'Sorcerer, Warlock, or Wizard'` (#21) — nothing new. 46 / 0, other 0.
- **Source and meaning.** `RR.owned` (prose bindings) and `RR.expectations` unchanged; consumer reading unchanged with no override and under both reviewed overrides (`disable-equipment.adventuring_gear.arcane_focus-record`, `disable-equipment.adventuring_gear.druidic_focus-druidic_focus`). The eligibility prose, focus rules, ownership and source order are untouched.
- **Delta.** `REPL.Delta(prior, final).report()` equals the reviewed DELTA line for line (17 lines): the three removed references and their three provenance entries, plus the equipment `acceptance.batches` and `acceptance.schema_anchors` entries, which differ only in `proposal_identity`, `semantic_diff_hash` and `diff`. Every other citation identity (8047) and its provenance is kept, as reviewed.
- **Reload.** The recorded file reloads to the same bytes.

The candidate, source, projection and native-contract evidence was reused as reviewed and not rerun.

## Moved pins (historical checks kept)

| File | Change |
|---|---|
| `tests/ingestion/mechanical/_replacement_chain.py` | Loads `EQUIPMENT_CLASS_ELIGIBILITY` (module `equipment_class_eligibility_accept`). `COMMITTED_SHA256` now points to its recorded sha. Adds `playing_the_game_recorded()` (the replayed prior). Docstring updated. |
| `test_animals_proposal.py` | The live Playing the Game test becomes the historical `test_the_playing_the_game_atoms_recording_rebuilds` (replay = `92b7a68f…`, `PLAYING_THE_GAME._check` over the finite-reference replay, 49 / 0). New: `test_the_committed_oracle_records_equipment_class_eligibility` (46 / 0). |
| `test_committed_accepted_authority.py` | The named identity set replaces the cited-targets equipment identity with the accepted class-eligibility one. |
| `src/.../oracles/README.md` | Current state (`5f37fb08…`, 46) and history entry; Playing the Game atoms added to the scripts whose `--verify` now refuses. |

`test_equipment_proposal.py::test_unauthored_parts_stay_explicit_unresolved_references` still lists the three class phrases: it checks the historical Equipment generator's output, which is unchanged, so it was left as historical evidence.

## Gates (raw)

- **ACCEPT script.** Black 0, Ruff 0, `mypy --strict` (`MYPYPATH=src`) 0, before and after pinning.
- **Black `--check` and Ruff**, rerun on the ACCEPT script and the three edited test files after Black's one blank-line fix to `_replacement_chain.py` (08:13:56Z) and before the pytest start: EXIT 0 (4 files unchanged), EXIT 0. LF only (0 CRLF) in the five edited code/doc files.
- **Last writes.** ACCEPT script 07:57:44Z, `test_animals_proposal.py` 07:58:32Z, `test_committed_accepted_authority.py` 07:58:46Z, README 07:58:55Z, `_replacement_chain.py` 08:13:56Z; all before the pytest start. Two earlier pytest launches (a whole-file run and a first node-id run) were stopped unfinished, the second because the Black fix landed after it began; neither is claimed.
- **Focused pytest `pytest.txt`** (16 node ids in `pytest.ids`, the Playing the Game recording's 15 plus the new historical Playing the Game rebuild, `-p no:cacheprovider`, run by `run_pytest.py`, 08:14:10Z–09:03:57Z): **16 passed in 2980.57s**, EXIT 1 (`pytest.exit`). The exit 1 is only the repo-wide `--cov-fail-under=80` (44.09%); no test failed. It is not green. `pytest.err` empty.
  - `test_animals_proposal`: `test_the_character_creation_catalogue_recording_rebuilds`, `test_the_finite_reference_atoms_recording_rebuilds`, `test_the_playing_the_game_atoms_recording_rebuilds`, `test_the_committed_oracle_records_equipment_class_eligibility`;
  - `test_character_origins_feats_acceptance::test_the_recorded_bytes_are_what_the_two_seams_record`;
  - `test_gameplay_toolbox_proposal`, `test_monsters_proposal`, `test_classes_proposal`, `test_spell_descriptions_proposal`, `test_rules_glossary_completion_proposal`: `::test_the_committed_oracle_records_the_owner_acceptance`;
  - `test_magic_items_proposal::test_accepted_then_resolved_in_memory_preserves_everything` and `::test_the_committed_oracle_records_the_owner_acceptance`;
  - `test_committed_accepted_authority::test_no_refused_candidate_is_selectable`;
  - `test_source_release_readiness::test_the_replacement_release_has_only_the_two_pilot_authorities`;
  - `test_checks_actions_rests_proposal::test_once_accepted_the_draft_resolves_through_the_native_seam`;
  - `test_reference_resolution::test_the_accepted_corpus_is_untouched_by_this_capability`.
- **Reused, not rerun:** the candidate write/check logs, constructor Black/Ruff/strict mypy, and the candidate's two hook runs (EXIT 0) and baseline change `377dc292…` → `d780f37e…`.
- **Not run: broad suite.** No green is claimed.
- **Deferred, not green:** pip-audit, expanded mypy and coverage.
- **detect-secrets.** A scoped scan with `PYTHONUTF8=1` over the seven files of `.claude/_sp/ece/rec/bl/files.txt` (the ACCEPT script, this note, the oracle, the README and the three edited test files), using the baseline's own plugins and filters. The oracle's 1013 findings were scanned, so it was not skipped.
  - 9 new public hashes, every value recovered: the ACCEPT script's 8 (the constructor sha, the equipment identity and PROPOSAL sha, the DELTA, review, simulated, owner-manifest and recorded shas) and the oracle's 1 (the accepted equipment `proposal_identity` `d7c012df…`).
  - 1 obsolete oracle entry on the same line (26903), pruned: the replaced cited-targets identity `309e4405…`, confirmed by SHA-1 against the prior copy.
  - 915 line numbers refreshed (912 oracle, 3 `test_animals_proposal.py`). Settings, filters, `generated_at` and the other files' entries are identical; keys stay backslash-only.
  - The baseline went from `d780f37e…` to `fbe8ebc6129689e90aede91197b0b6d82cd66243047049125ddbb1b802c02967`, staged by name. This note was rescanned after its final edit; the hook runs are in the final report and `.claude/_sp/ece/rec/bl/hook*.log`.

## Limits

- Nothing is committed, pushed, merged, published or activated.
- The release order is scheduled for one bounded pass after the packets, before publication.
- The other 46 reference findings stay; held rows are as the packet dispositions them.
- No source errata were encountered.
- The target-contract proposal remains unaccepted.
