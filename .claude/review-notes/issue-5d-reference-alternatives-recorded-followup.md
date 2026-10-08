# CRD Issue 5d — Reference alternatives: recorded follow-up (#132, #137)

## Authorization

The Owner's statement, verbatim:

> I accept the exact 13-finding reference batch and its schema/route reconciliation, retaining 33 reference findings, zero uncovered leaves, and the partial-publication block.

**Approval time:** the statement preceded 2026-10-01T18:15:15Z. No more precise approval time is claimed; `APPROVAL_BEFORE` in the script is documentary and is never recorded. The recorded action carries its real execution UTC time. No renewed Owner approval was sought; a Codex complementary review follows.

**Write route.** Two earlier Write attempts for the ACCEPT script were denied by the permission layer and stopped there; neither created the script or recorded anything. The Owner then supplied a per-invocation `autoMode.allow` exception via `--settings`. Permanent settings, classifier rules and auto mode were not changed by this session, and no alternate write route or bypass flag was used.

**Owner files.** No owner manifest is pinned by sha for this batch. The ACCEPT script asserts the constructor pin at import, and the PROPOSAL, DELTA and review pins on every run.

| File | SHA-256 |
|---|---|
| `issue-5d-reference-alternatives-REPLACEMENT.py` (constructor) | `2d8f7094dc96120032aeae5c5bca7c3d4ca6c35e355ecbf9f1f7ee2baf152be8` |
| `issue-5d-reference-alternatives-PROPOSAL.json` | `17c5ac2562d5c67bd6434290fa3affddc86d6cd1721b4c654eb76bcbb677b7f0` |
| `issue-5d-reference-alternatives-DELTA.txt` | `7e5de293c33b91e80346d4b263cc90d76a6d9eb74efedd0fb2a3e8dddfaf9bf0` |
| `issue-5d-reference-alternatives-review.md` (packet) | `0a2ca621ec8ad36a2ca29cd7666b96caeacd8df9089d14add77d1f1ffd8b5166` |

## Final oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-3fe24ff6-4e3.json`

| State | SHA-256 | Schema | Batches / records / spans / units / resolutions | Reference / uncovered-leaf findings |
|---|---|---|---|---|
| prior (Equipment class-eligibility recording) | `5f37fb080a8493a1acb6584ef9bd2297c388d34683200bd7f486007ade668676` | 16 | 24 / 1835 / 10492 / 1476 / 1440 | 46 / 0 (as lifted to 17) |
| **recorded (final, on disk)** | **`cc994e1badee3baf733d2df5d5c88903ad96b4ddd0172f52111ecdf0b4c1f190`** | **17** (`4881e51fb2fa73e52f7ff951ad7d00b863188c1a22133fb0e2873c7d32d10ada`) | **24 / 1835 / 10492 / 1476 / 1453** | **33 / 0** |

Other findings: 0. Reference-resolution violations: 0. The partial-publication block stands.

**Simulated state.** `f5721870b057f6455b98ca17f9455ddfdab1c8207fa65b1181e98e6467dd0439` is the reviewed constructor's composition under the simulated reviewer. It was checked in `--simulate` and again in the record path before the write. It was never written.

## Recorded action (real UTC)

Script: `.claude/review-notes/issue-5d-reference-alternatives-ACCEPT.py`, final sha `7a959255012bb8c4bf85ad962ecafb90109c906d1e03a7a8120efb8d515f4764` (after the two verifier fixes below; neither touches the recording path). Logs: `.claude/_sp/rar/rec/`. Each run went through `run.py`, which writes `NAME.log` (stdout and stderr) and `NAME.exit` (the process exit code).

| Action | Log | Result |
|---|---|---|
| `--simulate` (in memory, nothing written; 19:00:01Z–19:00:37Z) | `simulate.log` | EXIT 0; simulated bytes `f5721870…`; every check passes at the placeholder time. (An earlier `--simulate` exited 1 on `acceptance.lifts differs`. The lift appends its own record, and `_kept` had not allowed for it. `_kept` was fixed before the record run, and nothing was written.) |
| `record-reference-alternatives` (19:00:56Z–19:02:03Z) | `record.log` | **EXIT 1 after a successful write**, explained below. Wrote `cc994e1b…`; resolved time **2026-10-01T19:01:31Z**. |
| `--verify .claude/_sp/rar/rec/prior-oracle.json` (19:05:02Z–19:05:44Z) | `verify.log` | EXIT 0. Every check is True, including the 13 new resolutions naming the Owner and this decision, the DELTA byte for byte, and the reload. |
| `--simulate` on the final script (19:44:10Z) | `simulate2.log` | EXIT 1: `… is not the prior`. Expected: after the write, `--simulate` refuses to run over the live file. |
| the final script's `--simulate` body over the saved prior (`simulate_saved.py`, 19:44:26Z–19:45:25Z) | `simulate_saved.log` | EXIT 0; simulated bytes `f5721870…`; every `_precheck` check is True; the oracle is unchanged at `cc994e1b…`. This is the post-fix evidence for the pinned script bytes. |
| actual vs simulated (`sim_diff.py`) | `sim_diff.log` | EXIT 0 |
| cleared findings (`cleared.py`) | `cleared.log` | EXIT 0 |
| Equipment class-eligibility `--verify` | `hist_ece.log` | EXIT 1: `AssertionError: drifted` in `_state`. Expected refusal: its chain no longer composes the file. |
| reference-routes constructor, check mode (no args) | `hist_repl.log` | EXIT 1: `AssertionError: accepted changed`. Expected refusal: its input pin is the prior file. |

**The record run's exit 1.** The pre-write check passed, the native action wrote once, and the post-write `_state()` confirmed the bytes equal the re-composed native action. The post-write `_check` then failed on one line: `1440 resolutions verbatim, in order False`.

That check sliced the first 1440 resolutions by position. The loader returns resolutions in canonical `resolution_id` order, not append order. So on the reloaded file the 13 new resolutions interleave with the 1440, and a positional slice cannot isolate them. In the pre-write check the same line read True, because that check ran on the in-memory composition, which is in append order.

This was a defect in the new, then-unpinned ACCEPT script's verifier, not in the recording. The check now splits by resolution id: "1440 resolutions verbatim, canonical order" and "13 new resolutions are the reviewed PROPOSAL's, canonical order". The file was **not re-recorded**. `record.log` is kept unaltered as evidence. `--verify` over the saved prior then passed every check.

**A second verifier defect in the same family**, found by the focused pytest. `test_the_committed_oracle_records_reference_alternatives` runs `_check` over the replayed prior, not the saved file. There it failed at `24 batches, identities and approvals unchanged`.

The replay holds batches and their records in append (recorded) order. The loader holds them in canonical `batch_id` order. The replay serializes to the same bytes (`5f37fb08…`), but the in-memory tuples differ in order (`probe_batches.log`). `_check` compared those tuples directly.

The fix: `_check` now normalizes both sides once to their as-loaded form (`_canonical`: serialize, then load). That covers every comparison in it: batches, approvals, the lift prefix and the resolution split. Over the replayed prior, every check then passed (`probe_test2.log`). `--verify` over the saved prior passed again (`verify2.log`, EXIT 0, every line True). The rerun test passed (`pytest2.log`). Black, Ruff and `mypy --strict` on the script all exit 0 (`black2`/`ruff2`/`mypy2.log`). Again, nothing was re-recorded.

Before the write, the prior bytes were copied to `.claude/_sp/rar/rec/prior-oracle.json` (scratch, sha `5f37fb08…`, verified). `RECORDED_AT` and `RECORDED_SHA256["recorded"]` were pinned after the write from the values the run printed and read back. Black, Ruff and `mypy --strict` were rerun on the script and all exited 0.

**Recording shape.**
- **One native write.** The prior is lifted 16→17 by `resolve_references(lift_to=…)`. That appends `5d-lift-schema-16-to-17` to `acceptance.lifts` and the 13 reviewed resolutions (#4, #7–12, #17–20, #22, #40), with `reviewer` / `authorized_by` = `Ravenlok (Owner)`, `authorization_reference` = the verbatim statement, and `resolved_at` = the UTC clock read once.
- No batch, span, unit or earlier resolution was re-accepted, re-keyed or dropped.
- **Prior.** The oracle is untracked, so after the write `5f37fb08…` exists as the saved scratch copy and as the replay `EQUIPMENT_CLASS_ELIGIBILITY.composed(…)` (`equipment_class_eligibility_recorded()`), which is sha-asserted. `--verify` and the tests use it.

**Actual vs simulated** (`sim_diff.log`, leaf walk over the two payloads): 52 differing leaves, all on `acceptance.reference_resolution_records`. That is the 13 new records × 4 fields. Non-metadata diffs: `[]`.

| Field | Simulated | Recorded |
|---|---|---|
| `reviewer`, `authorized_by` | `SIMULATION - not an Owner approval` | `Ravenlok (Owner)` |
| `authorization_reference` | `SIMULATION ONLY: in-memory composition check; records no acceptance` | the verbatim statement |
| `resolved_at` | `2026-10-01T00:00:00Z` | `2026-10-01T19:01:31Z` |

## Preservation and replay evidence

From `record.log` and `verify.log`:

- **Counts.** 24 batches, 1835 records, 10492 spans and 1476 units are unchanged. Resolutions go from 1440 to 1453.
- **Batches.** The 24 batches, their identities and their approvals are unchanged.
- **Resolutions.** The 1440 prior resolutions are verbatim, and so are their 1440 historical approvals. The 13 new resolutions are exactly the reviewed PROPOSAL's, in canonical order: 132 routes, 197 destinations. Everything else is as lifted; prior items are kept, and 13 resolutions plus 13 approval records are added.
- **Lift.** Exactly one lift is appended: `5d-lift-schema-16-to-17`.
- **Findings.** Compared as multisets against the lifted prior, 46 / 0 / 0 → 33 / 0 / 0. Exactly 13 cleared and nothing new (`cleared.log`): `srd-5.2.1/character-creation:'Character Creation'` ×1, `srd-5.2.1/classes:'Classes'` ×6, `'Fighting Style Feature'` ×4, `'Spellcasting Feature'` ×1 and `srd-5.2.1/feats:'Origin Feats'` ×1.
- **Delta.** It equals the reviewed DELTA byte for byte.
- **Reload.** The recorded file reloads to the same bytes.

The candidate, reader, proposal and native-contract evidence was reused as reviewed and not reconstructed.

## Moved pins (historical checks kept)

| File | Change |
|---|---|
| `tests/ingestion/mechanical/_replacement_chain.py` | Loads `REFERENCE_ALTERNATIVES` (module `reference_alternatives_accept`). `COMMITTED_SHA256` now points to its recorded sha. Adds `equipment_class_eligibility_recorded()` (the replayed prior). Docstring updated. |
| `test_animals_proposal.py` | The live Equipment class-eligibility test becomes the historical `test_the_equipment_class_eligibility_recording_rebuilds` (replay = `5f37fb08…`, `ECE._check` over the lifted Playing the Game replay, 46 / 0). New: `test_the_committed_oracle_records_reference_alternatives` (33 / 0, all `reference `). |
| `test_reference_alternatives_candidate.py` | The `persisted` fixture reads the recorded oracle instead of composing the candidate; the docstring now calls it the Owner-accepted recording, still unpublished. |
| `test_source_release_readiness.py` | 1440 → 1453 resolutions; docstring updated. |
| `src/.../oracles/README.md` | Current state (`cc994e1b…`, schema 17, 1453, 33); the Equipment class-eligibility history entry completed; a new reference-routes entry; Equipment class-eligibility and the constructor's check mode added to the scripts that now refuse, confirmed by `hist_ece.log` and `hist_repl.log`. |
| `docs/decisions/adr-005d-complete-typed-mechanical-authority.md` | The 2026-10-01 amendment is marked ACCEPTED. It records the verbatim statement, its scope (this schema/route reconciliation and these 13 resolutions only; no other decision rewritten), the recording time, the script and this note, and that nothing is published or activated. |

## Gates (raw)

- **ACCEPT script.** Black 0, Ruff 0, `mypy --strict` (`MYPYPATH=src`) 0, before and after pinning.
- **Black `--check` / Ruff** on the ACCEPT script and the four edited test files (`black.log`, `ruff.log`): EXIT 0 (5 files unchanged), EXIT 0.
- **`mypy --strict` over the same five files** (`mypy.log`): EXIT 1, 17 errors. None are in lines this change added: they are in `conftest.py`, `test_character_origins_feats_proposal.py`, the older Animals test (`test_animals_proposal.py:419–431`), and the older reader-test signatures of `test_reference_alternatives_candidate.py`, whose `type: ignore` sits on the wrong line after Black wrapped them. This falls under the standing non-green expanded mypy. `mypy src/` was not rerun: `src/` code is unchanged (only the untracked oracle JSON and the README changed).
- **Focused pytest `pytest.log`** (16 node ids in `pytest.ids`, 28 collected, `-p no:cacheprovider --no-cov`, 19:09:00Z–19:31:31Z): **27 passed, 1 failed in 1346.37s**, EXIT 1. The failure is `test_the_committed_oracle_records_reference_alternatives` at `_check` line 348, the order defect above.
  - **Rerun after the fix** (`pytest2.log`, that one node id, 19:31:48Z–19:36:25Z): **1 passed in 274.48s**, EXIT 0.
  - The other 27 do not call the changed `_check`; they read only the unchanged pins.
  - Tests passed:
    - all 13 reader tests in `test_reference_alternatives_candidate.py`;
    - `test_animals_proposal::test_the_equipment_class_eligibility_recording_rebuilds`;
    - `test_character_origins_feats_acceptance::test_the_recorded_bytes_are_what_the_two_seams_record`;
    - `::test_the_committed_oracle_records_the_owner_acceptance` in gameplay_toolbox, monsters, classes, spell_descriptions, rules_glossary_completion and magic_items;
    - `test_magic_items_proposal::test_accepted_then_resolved_in_memory_preserves_everything`;
    - `test_committed_accepted_authority::test_no_refused_candidate_is_selectable`;
    - `test_source_release_readiness::test_the_replacement_release_has_only_the_two_pilot_authorities` and `::test_publishing_an_unreviewed_projection_is_typed_refused`;
    - `test_checks_actions_rests_proposal::test_once_accepted_the_draft_resolves_through_the_native_seam`;
    - `test_reference_resolution::test_the_accepted_corpus_is_untouched_by_this_capability`.
- **Last writes.** Test files 19:06:38Z–19:08:05Z, before the pytest start. The README (19:09:22Z) and ADR (19:09:36Z) were saved just after the start; no test reads them. The ACCEPT script fix was saved at 19:26:47Z, and the one affected test was rerun after it.
- **LF only.** All eight edited or new files have 0 CR.
- **Not run: the broad suite and services 430.** No `src/` code changed. No green is claimed.
- **Deferred, not green:** pip-audit, expanded mypy and coverage.
- **detect-secrets.** A scoped scan with `PYTHONUTF8=1` over the nine files of `.claude/_sp/rar/rec/bl/files.txt`: the ACCEPT script, this note, the oracle, the README, the ADR and the four edited test files. It used the baseline's own plugins and filters (`bl/scan.log`). The oracle's 1014 findings were scanned, so it was not skipped.
  - **7 new public hashes, every value recovered.** 6 are the ACCEPT script's pins: the constructor, PROPOSAL, DELTA, review, simulated and recorded shas. 1 is the oracle's schema-17 hash `4881e51f…`, as the new lift's `to_hash`.
  - **0 obsolete.** 966 line numbers were refreshed: 963 in the oracle, 3 in `test_animals_proposal.py`.
  - **Scope.** `apply.py` rewrites only the `results` entries of the scanned files. Settings, filters, version and `generated_at` are identical, and keys stay backslash-only.
  - **Baseline.** It went from `63c8358dbffdc7c2ff24166cfbed6d74dea6e86271f267ab712963a69972d1be` to `54df09f121234ed8b4b77683d192179e48441b04a0efdce176dc976e52573ad6` in the working tree only. **Not staged** (no index changes), so the real staged-baseline hook still reads the index copy.
  - This note was rescanned after its final edit. The hook runs are in `.claude/_sp/rar/rec/final-hook.log` and the final report.

## Limits

- Nothing is committed, pushed, merged, published or activated. No shared DB was written. The protected packet, quarantine and index are untouched.
- The release order is scheduled for one bounded Owner pass after the packets, before publication.
- 33 reference findings remain; the partial-publication block stands.
- No other target-contract proposal is accepted.
