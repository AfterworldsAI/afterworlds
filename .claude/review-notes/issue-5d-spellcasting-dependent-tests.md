# CRD Issue 5d — Spellcasting: live dependencies updated to the recorded state (#132, #137)

## Scope

This is settled dependency maintenance after the Owner recorded the spellcasting batch. It adds no new semantics and no new acceptance.

It updates the live consumers that assumed the 13-batch Equipment artifact, starting from §5 of `issue-5d-spellcasting-accepted-recording-handoff.md`.

What this run did **not** do:
- No re-recording, and no baseline edits.
- No commit, push, merge, publication or activation.
- No shared-DB or Chroma writes.
- No new batch authoring.
- No broad source audit.

Every prefix is still rebuilt natively and verified. No assertion was weakened, and no test coverage was dropped.

## Recorded state relied on (verified this run)

| Item | Value |
|---|---|
| Oracle `srd-5-2-1-corpus-626c83f8-209.json` | `c5971b89…572f` (unchanged by this run) |
| Content | 14 batches, 235 records, 1497 spans, 169 review units, 50 resolutions, 0 resolution violations |
| Spellcasting step times | `accepted_at 2026-09-25T18:05:59Z`, `resolved_at 2026-09-25T18:06:11Z` |
| Prior (Equipment) | 13 batches, 216 records, 49 resolutions, preserved; rebuilt natively and pinned to `08cca0b7…03fb` |
| Twelve-batch replacement prefix | `7b1d6f43…abdd8` |
| `.secrets.baseline` | `4554f802…efb2f`, staged, untouched (1.5.0, 63 files, 1551 results) |

## Changes, per file

**`tests/ingestion/mechanical/test_spellcasting_acceptance.py`** (new, mirrors the Equipment acceptance test)
- **Replay:** the committed bytes equal the native replay by `SC._state(SC.prior())`, and equal the file resolved by `committed_inputs_for`. The recorded times read back as 18:05:59Z and 18:06:11Z.
- **Acceptance:**
  - The batch rule and the proposal identity are recorded.
  - 72 acceptances under the Owner, and 19 new records.
- **Prior preserved:** 13 batches, 216 records and 49 resolutions. The lifts, policy transitions, schema and binding are unchanged.
- **Totals:** 14 batches, 235 records, 1497 spans, 169 review units, 50 resolutions.
- **Resolution:** the one resolution equals the generator's drafts: `srd-5.2.1/spells`, pointing to `spells.attack_rolls`. It carries the Owner's authorization, and there are 0 violations.
- **Publication still blocked:**
  - Prior: 9068 leaf findings and 58 reference findings.
  - Final: 8964 leaf findings and 59 reference findings.
  - The only finding that is not an unresolved reference is `glossary.improvised_weapons`.
- No 64-hex literals.

**`tests/ingestion/mechanical/test_equipment_acceptance.py`**
- **What changed:** it no longer calls `EQ._state` on the appended artifact. It now rebuilds the 13-batch result natively, as `EQ.resolved(EQ.accepted(EQ.prior(), …))` at the recorded times. Its serialized SHA must equal the spellcasting helper's `PRIOR_SHA256`, so no new literal was added.
- **The committed-file check is now two checks:**
  - `COMMITTED` bytes equal the file bytes.
  - The file is the spellcasting replay over the Equipment result: `SC._state(FINAL)` must be `resolved` and equal to the file bytes. `EQ._check_preserved(FINAL, replay)` must hold, meaning every Equipment item is kept and the first 13 batches are equal.
- **Step times:** the committed file keeps the Equipment `accepted_at` (05:47:17Z) and the resolution `resolved_at` (05:47:29Z) for the 43 Equipment resolutions. `_read_back(FINAL, PRIOR)` is kept.
- **Everything else is kept:** the other assertions and the publication counts for the 13-batch state (9068/58).
- `SC` is loaded, and `EQ = SC.EQUIPMENT`.

**`tests/ingestion/mechanical/test_spellcasting_proposal.py`**
- The `prior()` fixture now rebuilds natively through `SC.prior()`.
- It asserts that the serialized SHA equals `ORACLE_SHA256`; line 136 is unchanged.
- The committed oracle must be exactly `SC._state(rebuilt)` (`resolved`, byte-equal to `ORACLE`). `_check_preserved(rebuilt, replay)` must also hold.
- Docstring lines 30–32 and the comment at line 130 were changed line-neutrally.
- `serialize_accepted_inputs` is taken from `SC`, so no import line is added. The baselined lines 128 and 136 have not moved.
- **Trade-off.** `prior()` now goes through `SC._state`, so it asserts the whole current file. It will need the same update on the next append, and it repeats a claim `test_spellcasting_acceptance` already makes. It was chosen because it is the stronger form of the prefix claim.
  - An order-agnostic alternative would survive appends: `EQ._preserved` over the two `accepted_inputs_payload`s, which is the multiset half of `_check_preserved`.
  - That alternative is weaker: it drops the batch-order check.

**`tests/ingestion/mechanical/test_source_release_readiness.py`**
- Changed to "fourteen accepted batches".
- The span sum now ends `+ 409 + 72`.
- One more history clause was added to the docstring.

**`tests/ingestion/mechanical/test_committed_accepted_authority.py`**
- Added `SPELLCASTING_PROPOSAL` next to `EQUIPMENT_PROPOSAL`.
- Its identity was added to the named set in `test_no_refused_candidate_is_selectable`.

**`.claude/review-notes/issue-5d-equipment-ACCEPT.py`** (decision: retargeted, following the REPLACEMENT precedent; below line 90 only)
- **Why:** `--verify`, `accept` and `resolve` all went through `_state()`, which asserted on the appended artifact. `_one` saw two `resolved_at` values.
- **What `_state()` does now:** when the artifact has more than 13 batches, it loads the spellcasting helper. It rebuilds this recording's result through `spellcasting.prior()`, pinned to `08cca0b7…`, and replays the whole file through `spellcasting._state`. It then asserts `_check_preserved` and returns `"appended"`.
- **Output:**
  - `--verify` prints the state and points to `issue-5d-spellcasting-ACCEPT.py --verify`.
  - `accept` refuses: `… is appended, not the prior chain`.
- The module docstring (line 23) now describes this, with the same line count; the baselined lines 83–90 have not moved.
- `--simulate` still asserts that the artifact is the 12-batch prior. It has been stale since the Equipment recording and was one-shot, so it was left as is.

**`.claude/review-notes/issue-5d-source-correction-REPLACEMENT-ACCEPT.py`**
- In the `verify()` docstring and its printed pointer only, the pointer now names `issue-5d-spellcasting-ACCEPT.py --verify`. These lines are below 171.
- The twelve-batch prefix check is unchanged.

**`src/afterworlds/ingestion/mechanical/oracles/README.md`**
- Now says fourteen batches and fifty resolutions.
- The replay pointer paragraph was updated.
- Added a `spellcasting` bullet and a sentence on the fiftieth resolution.
- "Fifty-nine reference findings remain". The breakdown was measured (see `sd_delta.txt`):
  - one "Spells" pointer was resolved;
  - "Equipment" is now ×3;
  - a new Component Pouch bullet was added.

  Both new findings come from `spells.components/component_pouch_and_focus`. The "Equipment" one names the whole part (`sd_eqref.txt`).
- The resolution sentence uses the README's `record/component` notation: `play.d20_tests/attack_ability_modifier`.
- Now says 8 964 uncovered leaves.

**`docs/architecture/issue-5c-5d-clean-restart.md`**
- Appended one paragraph recording spellcasting: 2026-09-25, `c5971b89…572f`, 14 batches, 235 records, 50 resolutions, and the new roles of the three `--verify` scripts.
- The ADR and the dated Owner Decision were not edited.

**Finding (drove the design above).** A loaded artifact holds its batches in canonical (alphabetical) order, not recorded order. `_check_preserved`'s ordered `batches[:n]` check therefore only holds between in-memory replays; on `load_accepted_inputs(ORACLE)` it fails. Every prefix check here compares against the native `_state` replay, and that replay is itself held byte-equal to the committed file.

## Gates (exact; not a full-suite result)

All runs used `rtk proxy venv\Scripts\python.exe … -p no:cacheprovider`. Raw logs are in `.claude/_sp/`.

| Gate | Result | Log |
|---|---|---|
| `issue-5d-spellcasting-ACCEPT.py --verify` | exit 0: resolved `c5971b89…572f`, 14 batches, 235 records, 1497 spans, 169 review units, 50 resolutions, 0 violations, prior preserved True, 18:05:59Z / 18:06:11Z | `sd_verify.txt` |
| `issue-5d-equipment-ACCEPT.py --verify` | exit 0: state appended, prefix verified, points to the spellcasting helper | `sd_verify.txt` |
| `issue-5d-equipment-ACCEPT.py accept` | exit 1, refused as intended: `… is appended, not the prior chain`; artifact unchanged | `sd_verify.txt` |
| `REPLACEMENT-ACCEPT.py --verify` | exit 0: twelve-batch prefix `7b1d6f43…abdd8`, points to the spellcasting helper | `sd_verify.txt` |
| pytest `--no-cov`: spellcasting_acceptance, equipment_acceptance, source_release_readiness, committed_accepted_authority | 45 passed (107 s) | `sd_pytest1.txt` |
| pytest `--no-cov`: spellcasting_proposal | 39 passed (124 s) | `sd_pytest2.txt` |
| pytest `--no-cov`: accepted_inputs, oracle, packaging, equipment_proposal, character_origins_feats_acceptance | 245 passed (198 s) | `sd_pytest3.txt` |
| pytest `--no-cov`: replacement-chain acceptances (actions-pilot, character-creation-foundations, checks-actions-rests, combat-damage-breaking, combat-turn-1) | 39 passed | `sd_pytest4.txt` |
| pytest `--no-cov`: replacement-chain acceptances (conditions-pilot, core-play-completion, core-play-dependencies, damage-and-hit-points, movement-closure, reference-closure) | 41 passed | `sd_pytest5.txt` |
| pytest **with coverage**: spellcasting_acceptance + equipment_acceptance | 10 passed; **exit 1**: `FAIL Required test coverage of 80% not reached. Total coverage: 41.16%`. The repo-wide fail-under applied to a two-file subset, so this is not a suite coverage result | `sd_pytest_cov.txt` |
| black `--check` (7 changed .py files) | exit 0, after `black` reformatted one wrap in `test_equipment_acceptance.py` | `sd_lint.txt` |
| ruff check (same 7 files) | exit 0 | `sd_lint.txt` |
| mypy on the two acceptance tests | exit 1, `import-untyped` only. This is outside the `mypy src/` gate; no `src/` code changed | `sd_lint.txt` |

## Not run

- The full pytest suite, and full-suite coverage.
- `mypy src/`: no `src/` Python changed.
- pip-audit: 31/11 remains deferred and non-green.

## Secrets baseline (no mutation)

- `sc_scan.py` rescanned every file changed here plus the whole §6a scope of the recording handoff (24 files) under the baseline's own settings. Every file reports **0 new, 0 obsolete, 0 moved**. The oracle is at 153/153. See `sd_scan_fullscope.txt` and `sd_scan_after.txt`.
- The detect-secrets hook was run twice over a temporary copy of the baseline for the 9 changed files: exit 0 both times. The copy was deleted, and `.secrets.baseline` is still `4554f802…efb2f`. See `sd_hook.txt`.
- **New concrete scanner findings for a future Owner terminal pass: none.**

## Preserved hashes

| File | SHA-256 |
|---|---|
| Oracle `srd-5-2-1-corpus-626c83f8-209.json` | `c5971b89…572f` |
| `.secrets.baseline` | `4554f802…efb2f` |
| `issue-5d-source-correction-REPLACEMENT-PACKET.md` (denied; untouched, not deleted) | `e462e235…cae1` |
| Spellcasting proposal | `3dbdae69…4af3` (identity `0b7f14ff…1d55`) |
| Spellcasting drafts | `72bcdc5f…fc2a` |
| `issue-5d-spellcasting-ACCEPT.py` (unchanged) | `2bed9d9b…22f6` |

**Changed this run:**

| File | SHA-256 |
|---|---|
| `issue-5d-equipment-ACCEPT.py` | `458dcee7…c312` (was `24d00787…`) |
| `issue-5d-source-correction-REPLACEMENT-ACCEPT.py` | `791ef715…1044` |
| `test_spellcasting_acceptance.py` | `c69f047b…a722` |
| `test_equipment_acceptance.py` | `ff398691…9c21` (untracked; its earlier SHA was not recorded) |
| `test_spellcasting_proposal.py` | `a25cf548…f00d` (untracked; was `e893ff34…e2a0` per the review packet) |
| `test_source_release_readiness.py` | `8c0074aa…ab47` |
| `test_committed_accepted_authority.py` | `c458cacb…f69e` |
| `oracles/README.md` | `d6a860af…ffcf` |
| `issue-5c-5d-clean-restart.md` | `ec6d5f4d…4b22d` |

All of these are LF, with zero `\r` bytes.

## Remaining / boundaries

- **Retirement:** the live dependencies are addressed, so each maintained copy was reviewed.

  | Copy | Disposition |
  |---|---|
  | `.claude/_sp/sc_final_sim.json` (the predicted artifact bytes behind handoff §6c) | **Retired.** It was already absent from `.claude/_sp/` at this run's retirement step; nothing was deleted. Its prediction is confirmed: oracle 153/153, 0 moved. |
  | `issue-5d-spellcasting-accepted-recording-handoff.md` | **Kept.** §5 and §6c are discharged, but Codex reviews completion against it. Codex or the Owner decides its retirement. |
  | `issue-5d-equipment-accepted-recording-handoff.md`, `issue-5d-equipment-dependent-tests.md` | **Kept**, for the same reason. They are the precedent records for this pass. |
  | `issue-5d-equipment-ACCEPT.py`, `REPLACEMENT-ACCEPT.py`, `issue-5d-spellcasting-ACCEPT.py` | **Kept.** All three are live verifiers: the Spellcasting script checks the whole file, the Equipment script checks 13 batches and the replacement script checks 12. |
- **Review packets:** the spellcasting and Equipment packets still read "(UNACCEPTED)". Equipment set no precedent for updating them, so they were not edited here.
- **Equipment `--simulate`:** stale since the Equipment recording (it asserts the 12-batch artifact). It was one-shot and left as is.
- **Other gates:** full suite, full coverage and pip-audit have not run (see Not run). Nothing is committed.
