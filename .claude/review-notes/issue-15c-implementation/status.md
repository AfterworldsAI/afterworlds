# CRD Issue 15c — implementation status

- **Branch and head:** `codex/issue-15c-bounded-d20`. Local commits: `eb60d9f` (implementation), `abca92d` (review notes) and a C2 review-notes commit. Baseline `e83018c` = remote main.
- **Not pushed. No PR.** Stopped at the semantic-acceptance gate for Codex review.
- **Scope:** #191 as updated (body SHA-256 `8225e1b6…57a2`). It adds creature attacks, bounded Multiattack and their saves/effects, the tool-addressing and omitted-source repair, and individual conditional-creature assessment. The G1 oracle `2ccbaeba…1258` is unchanged.
- **Process:** Opus 5.5 at medium effort, with the separate Opus 5.5 Advisor consulted on the approach, the candidate scope and completion.

## Successor recorded; implementation continuing (12 October 2026, Owner accepted the exact native C5 packet)

- **Recorded:** `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c.json`.
  - File SHA-256 `23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69`. This is the real recording; the reviewed simulated preview `cd9d1d27…` is preserved unchanged.
  - Oracle identity `000c4c10…6e76`, projection `44f212d5…` and payload hash `ed8e21dc…` equal the accepted packet.
  - Only `reviewer`, `accepted_at` and `rule` differ from the preview, and only on the eleven batches.
  - Evidence: `../issue-15c-recording/` (`record_successor.py`, `owner-acceptance.json`, `recorded-followup.json`).
  - Re-verified (write-once verify mode) after the closed-type fix below: byte-identical, 0 native findings, gate passes.
- **BLOCKED: supersession of G1 by digest.** Adding G1's digest `2ccbaeba…` to `oracle.SUPERSEDED_ORACLE_SHA256` was refused by the session's permission classifier ("Modify Shared Resources"), and it has not been retried.
  - Until that one line lands, the release has two claimants. `committed_oracle_for` / `committed_inputs_for` raise, which breaks every real-authority test and the E2E publish path.
  - Packaging (`MANIFEST.in`, `pyproject.toml`), the oracles README and the oracle-selection tests follow the same supersession and are held with it.
  - **Owner/user action needed.**
- **Schema-19 native contract fix.**
  - Schema-19 nested value objects (`DamageTerm`, `Rider`, ...) joined `_CLOSED_TYPES`, so the structural and version-legality walkers now descend into them.
  - The schema hash is unchanged (`3734ccf7…`) and the accepted successor re-verifies.
- **Observation for Codex:** three `EntrySubject` members (`amulet_wearer`, `rider`, `self_and_allies`) are admitted by the accepted schema but carried by no accepted fact. C5 states them only on unminted prose entries.
- **Test reconciliation (schema 19), focused only:**
  - **Edits:**
    - `_schema_pins` current → 19 and the 18→19 crossing;
    - round 7/9 and schema 12;
    - the literal lift chains;
    - the legality `SCHEMA_19_ONLY` (235 real exemplars, `data/schema_19_exemplars.json`);
    - 21 invariant-closure rows (`data/schema_19_invariant_cases.json`);
    - fact-family exemplars;
    - `bounded_oracle.json` lifted 18→19 as the G1 precedent did (+17/−2);
    - the identity canary, the scoped "19" check and the collision detector.
  - **`fields:` loci:** the schema-19 invariant loci use a `fields:` prefix; the closure test admits it, as schema 5 admitted `component`. Changing it would move the accepted hash.
  - **Results:** 2,207 + 1,920 focused tests passed after the fixes. Not full-suite evidence.
- **Boundary:** `boundary-input-matrix.md` was sent to Codex. Its classification is `codex-combat-state-boundary.md`, relayed; it requires corrections. Combat/position/timing state stays held until the corrected selector and timing contract.

## Native preview (12 October 2026): SIMULATION, Owner semantic acceptance HELD

**The current state is a review-only schema-19 native preview** of the exact C5 source contract, in `../issue-15c-native/`. Start with `OWNER-ACCEPTANCE-PACKET.md` there.

**State:**
- Uncommitted and unstaged.
- Working-tree src changes: `representation.py`, `schema_lift.py` and `projection.py`. These are a pure insertion with 2 replaced lines.
- One test pin file changed, labelled provisional.
- C1–C5, G1, the predecessor and the isolated store are byte-unchanged.

| Item | Identity |
| --- | --- |
| Schema 19 | `3734ccf7d6be7f25e0a0d7c0395121c5525afcb87144f5cf9d6895e03c1cd18f` (lift `5d-lift-schema-18-to-19`) |
| Preview file | `cd9d1d27428a1525955f83091125489e96bbc7bd0977bb9f3ce83933883a20d3` |
| Oracle identity | `000c4c108daf609c26eb9ae9f1197a26eef6fb80a3cb5c788f9e89ba20ad6e76` |
| Projection | `44f212d5-32dd-5469-8f05-f0d236492347` / `ed8e21dc…5188` |

**This supersedes the earlier preview Codex pinned** (`aa9fe91e…` / schema `85896c…` / `0d2ea513…` / `37c56dbd…`).
- **What changed:** only the schema descriptor. A focused test found Python class names in one invariant's rule text; it was reworded, and the schema-numbered invariant ids were renamed. That changed the hash and every identity bound to it.
- **Why the content is believed unchanged:** the earlier bytes were overwritten, so there was no direct diff. Both runs matched G1 identically under `verify_preview`, with the same delta. Per-batch counts are equal, and `reconcile.json` is byte-identical. The packet has the old→new table.

**Codex reports applied:**
- `codex-native-tool-selection-review.md`: `tool_activity` identities; the identical-option collapse was removed.
- `codex-native-proof-review.md`: hard placement failures; identity-level reconciliation; ordered preservation of the 13 untouched batches; possessor agreement; merge inspected, with no conflict.
- `codex-native-ac-mapping-review.md`: the nested Shield relocation wording.
- `codex-native-c5-review.md`: the C5 wording in the correspondence.
- `codex-native-schema-failure-classification.md`: the provisional pin; the scoped `"19"` assertion; full-shape object comparison; the declared context-shared vocabularies.

**Evidence:** focused only; no full suite and no CI. The packet has the list.
- `verify_preview`: 36/36.
- The build is deterministic across two runs.
- The focused identity test file: 1 failed, 56 passed. The failure is the historical schema-18 `bounded_oracle.json` fixture, which is landing work.

**Blockers:**
- Owner semantic acceptance of the exact identities.
- Landing requires the accepted successor to be recorded natively in the same change, because a schema-19 build refuses the schema-18 G1 oracle.
- The other schema-pinning tests and fixtures.
- `.secrets.baseline`, full gates, CI and Codex review.

## Candidate

**C5 is current: a raw candidate (12 October 2026), uncommitted and unstaged.** It applies all of `codex-c4-review.md`, `codex-c5-grant-family-addendum.md`, `codex-c5-provisional-linkage.md` and `codex-c5-provisional-roster.md`. See `candidate-c5/README.md` for family dispositions, conservation, fidelity, grants and holds.

| Part | SHA-256 |
| --- | --- |
| C5-A | `866f2c132b974ec2c895c269c09fc5de554b881be5a94699faa8c1188b9687c9` |
| C5-B | `187c041b8de8edcffe16e2c606b11c071b90b438dc3be2c68cb8a1a3a97df3f6` |
| C5-C | `bb3761b955f06d94665e86eb817f38da16198069fea9c5919fb98d87db476ad4` |
| Capability (not source) | `6037ea70246c24e478d97c5f7938f3d695802bf6b19284c0c883864af9e3efe6` |

**Checks**, from `derive_c5.py`:
- Two runs were byte-identical.
- C1, C2, C3 and final C4 are byte-preserved, checked before and after each run.
- Logical-entry conservation was re-read from the raw files without the parsers: 1,377 entries and 1,512 content lines, with 0 problems. It recovered 135 continuation lines that earlier candidates dropped.
- Untyped clauses are disposed piece by piece: 433 typed, 189 named unsupported engines, 6 with no mechanical consequence, and **0 missing source authority**.
- Source-to-field fidelity, checked without the readers, found 0 failures across 433 pieces (42 with a turn owner) and 83 grant facts.
- Number accounting is non-vacuous: `source_text` is excluded. It found 0 unaccounted.
- All 89 grant vocabulary fields resolve to typed selectors.
- The grant sibling audit is recorded in the README. Pact of the Blade is out of scope and refuses.
- 672 reused accepted payloads validate, with 0 failures.
- The reviewed source key names are pinned.
- The transition is still 11 of 24 batches.

**Grants:** save, weapon, armor, tool and Weapon Mastery entitlement facts have been added. The 12 checks are labelled as source-rule assertions; they are not runtime validation.

**Roster:** Raven Mimicry (DC 10), Green Hag Mimicry and Cube Transparent are now typed observer checks, and Zombie Undead Fortitude is a typed zero-HP save. Runtime grant validation and `checks.py` stay held.

**Before commit:** the C3, C4 and C5 JSON digests need audited `.secrets.baseline` entries.

**C4 (superseded by C5): a raw candidate (12 October 2026), uncommitted and unstaged.** It applies Codex's C3 source/capability contract, the grant trust-boundary finding and every Codex provisional C4 finding (`codex-c4-provisional-findings.md`; all patched; dispositions in the README). See `candidate-c4/README.md` for family dispositions, invariants, coverage, holds and the 11-batch transition.

| Part | SHA-256 |
| --- | --- |
| C4-A | `901083ec3c8c25e9cd95a638a537cf3db41d8277420e07f0fc2b5d023cd15e62` |
| C4-B | `f679b06c7e8e3513b9886716754db78b5a28c8cf254cb09d1e195b4f30765c08` |
| C4-C | `2c34a6f03fc081a0adbe3abf8f9e50f0dcad55e9c07469cf3204ccb36e68fb5f` |
| Capability (not source) | `2d884ffbb254af6849a8bd0b61cc5f2f2c4a84dd568f664e3606fb02cb783a8e` |

**Checks**, from `derive_c4.py`:
- Two runs were byte-identical.
- C1/C2/C3 digests are unchanged, checked before and after each run.
- General invariants, checked on the source parts alone: 0 scope-vocabulary leaks; 0 unaccounted printed numbers; 2 formula references, both resolved; 1 named target residue; 566 reused payloads validate with 0 failures; 29 of 29 gain-level references resolve to G1 `progression_entry` facts.
- Advisor completion review: its three blocking gaps were applied before this gate. Untyped clauses are now verbatim in source. Rider clusters are typed or classified as named mechanics or `missing_source_authority` (105). Applicability notes moved to capability.
- Sweep defect found and fixed: an escaping error had turned the scope sweep's `held` pattern into control characters, so earlier zero-leak results did not cover "held". It is restored, and a full-file sweep of C4-A/B/C is clean. A full control-character scan of the script and notes is clean.
- Advisor final check, applied:
  - every `affects` context is in a closed vocabulary that the rollup consumes, so Inscrutable and Bound refuse through real keys;
  - Swarm is conditional, settled by the source's exceptions rule;
  - all reaction triggers are read and the cluster labels audited;
  - Venomous Snakes keeps its poison in `hit_damage`.
- Housekeeping: git-ignored `__pycache__` directories under `candidate/`, `candidate-c2/` and `candidate-c3/` were deleted. They were bytecode caches from importing earlier scripts; no tracked or digested file changed.

**Grant trust boundary:** 91 grant/selection source facts are proposed, including:
- the multiclass skill grants;
- the background and Human origin-feat grants;
- feat prerequisites;
- the class ASI and Epic Boon feat choices;
- the Primal Knowledge and College of Lore skill grants;
- expertise gains, referenced to G1 `progression_entry`. Runtime validation and the `checks.py` and test corrections are held until native acceptance.

**Before commit:** the C3 and C4 JSON digests need audited `.secrets.baseline` entries.

**C3 (superseded by C4): a raw candidate (12 October 2026), uncommitted and unstaged.** It corrects all eight Codex C2 findings and the qualification residue. See `candidate-c3/README.md` for the per-finding dispositions, coverage, holds and prerequisites.

| Part | SHA-256 |
| --- | --- |
| C3-A | `aaa5a20fa59c8e4d9dbbd10120aa0b91e968cdb1bcd3616cb8b28632c2e49ff9` |
| C3-B | `bb086082b02e879706218a4ad016110d3c6d5b3f9cc095076adec1cc89095524` |
| C3-C | `36be82a04ff2c587af754ed9430dfdfeb9b6053b8073d80add716313069e422b` |

**Checks**, all from `derive_c3.py`:
- Two runs were byte-identical.
- `regressions()` passes for every cited defect and sibling.
- 529 reused-family payloads validate with the accepted `fact_from_payload`, with 0 failures.
- All 429 attack-roll lines across the four source files are parsed.
- The six C1/C2 digests are unchanged, checked before and after each run.

**Before commit:** the C3 JSON digests need audited `.secrets.baseline` entries; this pass may not write that file.

C1 and C2, below, are preserved and superseded.

**C2 (superseded by C3).** C1 is superseded but preserved; its JSON files are byte-identical.

| Part | SHA-256 | Holds |
| --- | --- | --- |
| C2-A | `a15aab18…` | Rules, weapons, all 25 tools, the stat-block conventions |
| C2-B | `0dd7538f…` | All 336 creature records: per-entry classification, section anchoring, block-level rollup |
| C2-C | `a21a5e89…` | Armor and character AC |

See `candidate-c2/README.md`: concordance, classification, assessed creatures, the schema and addressing delta, transition cost, holds, and the surfaced prerequisite.

**Nothing has been accepted. Native minting has not started** (cost stated: 7 of 24 batches).

Codex independent review of C2 is complete: **candidate corrections required before native preparation or acceptance**. See `codex-c2-review.md` for semantic defects, representation correspondence and the bounded correction brief. Claude remains stopped; that brief has not been dispatched.

## Implementation on `eb60d9f` (unchanged by C2)

See `review-handoff.md`. It covers:

- wiring;
- the manifest and certification;
- typed refusals;
- certified fixed-DC checks;
- player-roll refusal;
- the setup-turn ordering fix;
- prompt v2;
- the ADR and status reconciliations.

Every operation that depends on C2 is `HELD` and refuses visibly. The manifest's "monster stat-block actions" exclusion and its record-only tool wording predate the scope update. They are **superseded by #191 as updated** and are to be revised in the dependent implementation once C2 is accepted. That code was not touched, because candidate work is held.

## Evidence

**Gates passed:**
- Black, Ruff and mypy strict are clean.
- detect-secrets is clean, with documented false positives.
- pip-audit is clean with CI's ignore set.

**Focused diagnostics** are green. These are not acceptance:
- 51 bounded-check tests;
- 54 service and adapter tests;
- 330 orchestrator and API tests;
- 8 E2E tests on G1 published in a disposable store.

**Full `pytest -q` on `eb60d9f`: NO RESULT.**
- The serial background task was externally killed after about 85 minutes, shortly after Claude's session ended. The previous two-hour-limit explanation conflicts with the recorded timestamps; the exact kill mechanism is unproven.
- Its log (`gates/pytest-full.log`) holds partial buffered progress through 7%. No pass/fail verdict, exit marker or coverage result is recorded. See `codex-bounded-test-diagnosis.md`; the bounded diagnosis reran no tests.
- Per the dispatch, it was not rerun for candidate-only work.
- Exact-head CI, which has 8 shards, has not run.

**C2 checks:**
- deterministic re-derivation;
- the C1 digests are verified unchanged;
- the two-sided creature census matched 336 of 336;
- the attack count equals the source's 423;
- every A and C fact anchors to an accepted component.

## Open, not yet applied

These are drafts held outside the repo, to be applied after review or a new full run:

- tests for stale-binding and missing-authority messages;
- the setup-turn sheet-skip test;
- a no-settlement-warning assertion;
- a BYOK E2E.

## Exact blockers

1. Codex independent review of the raw C5 packet.
2. A native mint of the reviewed C5 (11 of 24 batches; not prepared), then Owner acceptance of the exact native identity.
3. Vampire Familiar: C5 keeps the source "vampire" qualification on an explicit relation. How the vampire qualification is validated is held; only the Charmed determination refuses. No Owner Decision is requested.
4. A full-suite and CI result for the implementation head.
