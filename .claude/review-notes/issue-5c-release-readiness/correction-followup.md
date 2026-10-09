# Release-readiness correction: follow-up, 7 October 2026

**Status:** the initial engineer correction is complete and the [Codex bounded static review](codex-bounded-review.md) has no outstanding static finding at the frozen inputs. Codex's full runtime gate `final-pytest-coverage-1` completed non-green (60 failed, 51 errors, 92.47% coverage); its [residue](codex-full-gate-residue-review.md) is corrected below ("Full-gate residue correction"), with focused diagnostics only. Codex completed the residue review and the frozen full test/coverage run `final-pytest-coverage-2`: native 0, 7,397 passed, 141 skipped, 252 warnings, 92.48% coverage. Final secrets content passes with no unbaselined findings; the real unstaged-baseline hook remains native 1 at the Owner publication boundary. Final preservation is checked separately; publication remains held. Local release readiness is not established. Every pytest run by this engineer session is a focused diagnostic (`FOCUSED DIAGNOSTICS ONLY`, with coverage disabled). None of them is an acceptance gate or a full-gate result. This session ran no final local gate on this diff; Codex runs them after its freeze and review. The external `final-pip-audit` runs below are recorded, not interpreted. No changes from this correction were staged, committed, pushed or published; the pre-existing index is preserved.

## Authority

- The Owner authorized a bounded release-readiness correction ([scope](codex-readiness-scope.md)). Only dependency-vulnerability repairs keep the after-restart deferral.
- The 21 September 2026 [Owner Decision](../../../docs/decisions/owner-decision-2026-09-21-5c-5d-clean-restart.md), Step 5 ("Retire superseded work"), already authorizes retiring obsolete artifacts, paths and tests. It forbids inventing approval gates.
  - Earlier follow-up rows said that retiring the `3fe24ff6-4e3` oracle needed a further Owner Decision. Those rows were wrong.
  - They are corrected in place: see [`recorded-followup.md`](../issue-5c-release-order-recording/recorded-followup.md) "Correction, 2026-10-07" and [`typing-followup.md`](typing-followup.md) rows 60–62.
- This correction grants no new acceptance, recording or publication authority.

The following stay immutable and unchanged:

| Item | Value |
|---|---|
| Recorded oracle | `srd-5-2-1-corpus-8781d4e0-a3b.json`, SHA-256 `def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c` |
| Accepted candidate | SHA-256 `8a6a9a9c305f41207190c0deb55875a027019116ce3f825a6a0425a3a115b4bf` |
| Owner approval identities | unchanged |
| Proposal collections | unchanged |

## Comparison rule

The structures inspected in the recurrence audit below follow this rule, with one disclosed Magic exception. This is not a claim about every assertion in every module; no whole-module audit was run.

- **Current:** `built` over the current `source_release_db` is compared with current expectations. In the Magic Equipment test, the current accepted record and edges come from the current accepted representation (`_replacement_chain.current()`).
- **Historical:** `recorded` (`load_proposal(PROPOSAL, expected_identity=IDENTITY)`) is compared only with `prior`, its own historical chain from `_replacement_chain.through(...)`.
- **Disclosed exception, Magic legacy borrowed-span probe:** `GEN.build` cuts the Magic packet from the current release but borrows the Equipment attunement spans it injects from its own historical `GEN.current()`, the chain `prior` is (generator lines 1408–1412 and 1474–1486). The Attunement assertions in `test_each_section_reads_its_subheadings_in_printed_order` (4 spans; 4 × 140 `CONTEXTUAL` claims) are kept and now characterized in a comment as pinning what that legacy generator injects. They are not evidence of current accepted wiring. Current Attunement behavior (exact text, order, disable and replace) is pinned by the persisted-current service tests (`_attunement`, from line 1059), which are unchanged. The historical generator is not rewritten.

Only assertions that enshrined cross-release bytes, counts or tools were retired, and only after their useful lessons were kept. No assertion was weakened to a set or subset check where it had been exact. No skip, exemption or `Any` was added, and no checker was weakened. One narrow `# type: ignore[arg-type]` was added at `test_oracle.py:301`, where the negative test deliberately passes `None` to prove the `TypeError` refusal.

## Defect families and dispositions

### 1. Typing

- **Original 16 strict errors:** closed in three test/helper files. See [`typing-followup.md`](typing-followup.md).
- **105 further consumer errors in seven files:** closed in place. The fixes are `isinstance` narrowing, typed forwarders and the `json_*` helpers, plus removal of 5 unused ignores. Negative raw-state inputs and all assertions are kept.
- **Strict selected-test set:** the original 15 files plus `test_checks_actions_rests_proposal.py`, run through `run.py`, which supplies `MYPYPATH=src`.
  - `mypy-affected-final` exits 0 with "no issues found in 16 source files".
  - The earlier 35 `import-untyped` diagnostics came from an ad-hoc run without source resolution. They were not typing debt ([Codex note](codex-valid-mypy-invocation.md)).
- **Production gate:** `mypy src/`, final gate, not run here. Repo-wide test mypy is **not** a required gate.

### 2. Release fixture expectations

These are the generator-rebuild tests in the converted family, corrected per file under the comparison rule:

- Classes, Glossary, Checks/Actions/Rest, Gameplay Toolbox, Spell Descriptions, Magic Items, Monsters and Animals;
- the Origins, Equipment and Spellcasting acceptance tests;
- the three finite-reference candidates, through `_replacement_chain.py` (+19 lines).

### 3. Selector reachability

The superseded `3fe24ff6-4e3` binding was still selectable by the committed-directory scan.

- `oracle.py` adds `SUPERSEDED_RELEASE_VERSIONS = {"5.2.1-corpus.3fe24ff6-4e3", "5.2.1-corpus.574662e9-0ef"}`.
- `committed_inputs_for` now:
  1. raises `TypeError` on non-`str` identities;
  2. normalizes both identities through `str.__str__`, which closes the `str`-subclass hash bypass in [Codex's finding](codex-selector-refusal-review.md);
  3. raises `OracleLoadError` for a superseded release.
- It refuses rather than returning `None` because the file is still on disk and still matches, the same reasoning as quarantine.
- The artifact files are untouched. They remain historical evidence.

### 4. Stale status prose

- The `publication.py` docstring no longer restates the old "7 batches, 48 records" coverage. It defers to the gate and its tests. This is a docstring-only change (+5 −9).
- The oracles `README.md` records the superseded set and the 2026-10-07 correction.
- The `test_source_release_readiness.py` opening now distinguishes working-tree accepted authority from published or active authority.

### 5. Codex fixture-residue items ([review](codex-fixture-residue-review.md))

- **Origins reference replay:** now representation-only. `relationship_and_reference_violations(candidate_from_accepted_inputs(lifted(...)).representation)` replaces the cross-release corpus fixture. The 29/94/91 and three-citation assertions are kept (`focused-origins-2`, exit 0).
- **Gameplay and Spell Descriptions disjointness:** `test_no_recorded_leaf_or_record_is_an_accepted_one(recorded, prior)` now compares historical with historical. The current scope tests stay on `built` (`focused-gameplay-2` and `focused-spelldesc-2`, both exit 0, on earlier file hashes; see the evidence boundary below).
- **Reference replay retention:** see the table below.
- **Animals current reader order:** `_read` now builds the expected texts independently.
  - For each printed container, it adds the governing *Monsters* rules not yet read, then the animal's own text.
  - This follows the accepted source order, using the [release-order candidate](../issue-5c-release-order-candidate.md)'s reader proof and `issue-5c-release-order-candidate/reports/reader-proof2.json`.
  - Exact list equality, per-component order, single-read deduplication and the disable and override checks are kept.
  - The expectation is not derived from service output. The module docstring was corrected.
- **Animals 4th test:** `test_the_records_are_the_stat_blocks` failed in `focused-animals-records-1` (exit 1) with `['actions', 'giant_owl', 'traits'] != ['giant_owl', 'traits', 'actions']`.
  - The recorded artifact stores components in canonical order. The old print order came from the retired generator build, not from a recorded byte. Spans carry no component and `GEN.LEAVES` is keyed by heading, so print order cannot be recovered.
  - The expectation is now the recorded canonical order, still exact, with a comment. `focused-animals-records-2` exits 0 for this test and the reader-order test.

### 6. Animals historical generator (recorded, not patched)

The legacy Animals generator cannot build over the current release. Its `current()` reads historical IDs, and `probe-generator-identity-2` reports `animals BUILD FAILED KeyError`.

This is obsolete tooling, and the 21 September Decision authorizes retiring it. It is not a reason to rewrite accepted semantics or historical generators.

- Current-path Animals coverage is the current-reader tests over `source_release_db`.
- Historical coverage is the `recorded`/`prior` replay.

## Reference replay retention map

The checks use `_references(inputs) = relationship_and_reference_violations(candidate_from_accepted_inputs(lifted(inputs)).representation)`. This is the effective historical representation with resolutions applied. No corpus is needed and none is rebuilt.

| File | Before | Drafted closure | Remainder | Status |
|---|---|---|---|---|
| Magic Items | 166 | *Carpet of Flying* is in before, not in after | `sorted(rest) == sorted(kept + packet)` (the exact form of the original); packet scopes `== UNRESOLVED_SCOPES`; `len == REMAINING == 315` | restored |
| Gameplay Toolbox | 143 | *Combat Encounters* | `sorted(rest) == sorted(kept + packet)`; `len == 166`; leaf delta `== mine`, 285 | restored |
| Spell Descriptions | 1157 | every `draft.source_text` | `sorted` equality; `len == REMAINING` (1157 − 1046 + 32) | restored |
| Monsters | 315 | 83 drafts | `Counter(rest) == +kept + Counter(packet)`; `len == 317`. The committed oracle also has 317 `reference …` findings. | restored |
| Origins | — | three citations | 29/94/91 | corrected (item 5) |
| Checks/Actions/Rest, Animals | — | — | — | already on the seam, no change |

The packet expectations are static, from `GEN.expected_representation_findings(GEN.<CHUNK>)`. Each generator's `current()` is the same historical chain as the test's `prior`. They are not read back from the result.

A first Magic restoration pinned the packet only by scope counts and a subset check. That was weaker than the original exact sorted equality. It was corrected to the exact form above before review (`focused-magic-exact-1`).

## Recurrence audit: current `built` mixed with historical `prior`

The trigger was the same pattern appearing twice (Gameplay and Spell Descriptions) in the [residue review](codex-fixture-residue-review.md).

| Structure inspected | Disposition | Admission mechanism |
|---|---|---|
| Gameplay `test_no_recorded_leaf_or_record_is_an_accepted_one` | patched | `recorded` and `prior` share `recorded.binding` |
| Spell Descriptions, same test | patched | same |
| Origins corpus-backed reference replay | patched | representation-only seam |
| Magic Items section-order test, line 417 (`built` with `prior` attunement spans) | characterized, assertions kept | **Corrects an earlier "already safe" row.** One historical chain does feed `read_accepted`, but the packet itself is current, so the state is mixed. A comment now labels the Attunement assertions as a legacy borrowed-span probe (see the comparison rule) |
| Magic Items `test_an_item_equipment_sells_is_one_record_in_both_catalogues`, line 1546 (1541 before the residue edit) | patched | **Corrects the same earlier row.** The record and accepted Equipment edges now come from `current().oracle.representation`, not `prior`. `probe-magic-shared-2` shows that the current accepted record equals the prior one for both *Potion of Healing* and *Spell Scroll*, while the current authority carries both catalogue edges (`equipment.adventuring_gear` and the Magic family). So the accepted-edge expectation is now both edges, exactly. The source text, provenance-role, table-shape and packet-edge assertions are unchanged; `prior` is dropped from the signature |
| Magic Items `test_no_recorded_leaf_is_an_accepted_one_but_the_shared_records` | already safe | `(recorded, prior)` |
| Monsters shape and leaf tests | already safe | `built` is compared with current, and `recorded` with `prior`, in separate assertions |
| Animals `test_the_records_are_the_stat_blocks` | already safe | `(recorded, prior)`; `recorded.binding == prior.oracle.binding` (line 205) |
| Classes and Glossary disjointness | already safe | representative split, `(recorded, prior)` |
| Checks/Actions/Rest composition | already safe | `prior.oracle.binding == recorded.binding` asserted (line 751) |
| Unconverted generator tests outside this fixture family that pass | out of scope | — |

The leaf-overlap probe (`probe-leaf-overlap-1`) prints `old 10464 new 10464 shared 10464`. Leaf IDs are shared across the two releases, so binding-mixed disjointness was not vacuous by ID. It was incoherent by state, which is why it was corrected and not only re-labelled.

## Full-gate residue correction ([review](codex-full-gate-residue-review.md))

Codex's root run `final-pytest-coverage-1` **completed non-green**: 60 failed, 51 errors, 111 bad nodes across 25 mechanical-ingestion files, and 92.47% coverage. The Owner authorized correcting every in-scope non-dependency defect. This section is the finite family map. No production code changed. No accepted oracle, proposal, draft or identity byte changed, and nothing was rerecorded. The 25 files are pre-captured in `.claude/_sp/release-readiness-20261007/pre-full-gate-residue` (`pins.json`).

### Three states, kept apart

| State | Source | Compared with |
|---|---|---|
| **Current** | `GEN.build(source_release_db)` over `8781d4e0-a3b`; `_replacement_chain.current()` (the committed oracle) | current expectations, the current identity, `current().oracle.binding` |
| **Historical** | `recorded = load_proposal(PROPOSAL, expected_identity=IDENTITY)` and its own `prior` from `through(...)`, both binding `3fe24ff6-4e3` | each other only, representation-only (`relationship_and_reference_violations` over the effective representation) |
| **Counterfactual** (ESR only) | `current()` with exactly the 13 Equipment/Spell resolutions removed, in memory | the persisted current authority, as the control |

Coverage of a composed historical state is `_covered(inputs)`: span leaves plus unit leaves. The superseded release's physical source is not available, so these are **retired**: counts of uncovered leaves (for example `(10266, 10252)` and `(9442, 9067)`), and `leaf …` findings. Each is replaced by the exact set `_covered(together) - _covered(prior) == mine`, with the batch's leaf count. The recorded span counts are kept, for example `len(recorded.proposed_spans) == 409`.

Span acceptance is **not** retired. An earlier draft of this step removed the `span …: no acceptance record` findings with the source-bound checks, and wrongly said they need the physical source. `accounting.validate_acceptance` reads only the classification ledger and needs no corpus. It is restored natively: see family 2a.

### Family map

| # | Family | Structures | Disposition |
|---|---|---|---|
| 1 | Historical bytes and identities compared with the current build | `test_the_committed_bytes_are_what_the_published_release_derives` in 11 proposal files, renamed `…_are_the_recorded_proposal` (Actions, Conditions, Reference Closure, Movement Closure, Combat Damage Breaking, Core Play Completion, Core Play Dependencies, Foundations, Origins, Equipment, Spellcasting); `test_the_published_release_still_derives_the_accepted_bytes` in 7 acceptance files, renamed `test_the_recorded_bytes_stay_and_the_current_build_emits`; Declared Expectations `…_keep_their_recorded_identity`; Cited Targets `…_are_the_recorded_ones` | **patched.** The recorded SHA, LF, identity and drafts payload are kept exactly (drafts derived on `recorded.binding`). The current build is pinned to `current().oracle.binding`. A successful emit now matches the current build's own render, and the emit refusal assertions are unchanged. The cross-release byte equality is **retired** |
| 2 | Historical `prior` composed with the current `built` | composed-coverage, `recorded_resolutions_still_apply_composed` and `once_accepted_…_native_seam` tests in Reference Closure, Combat Damage Breaking, Core Play Completion, Core Play Dependencies, Foundations, Origins, Equipment and Spellcasting | **patched** to `recorded` plus `prior`, representation-only. Exact reference lists are kept: `CLOSED`, `OUTSTANDING`, `ACCEPTED_UNRESOLVED + NEW`, Origins 29 plus `added`, Equipment 91 plus `added`, Spellcasting 26 `Spells` plus 2 Equipment. Native `accept_proposal`, `resolve_references` and `reference_resolution_violations` assertions are unchanged |
| 2s | Passing siblings of family 2 | `test_no_leaf_is_owned_by_an_accepted_unit` (Origins, Equipment, Spellcasting); Spellcasting record disjointness; CPD `…_beside_the_stat_block_pointers`; Origins `test_the_accepted_authority_gains_no_membership` | **patched.** Both sides are recorded, with `recorded.binding == prior.oracle.binding` asserted. Membership: the production-path read on `prior` (placing the superseded leaves through the current DB) is **retired** and replaced by its sole input, the explicit `CATALOGUE_MEMBER` edge set, asserted empty over the 103 records. A first rewrite that read `current()` failed in `residue-proposals-1`: the current authority makes some of the 103 keys catalogue members. It was replaced, not loosened |
| 2a | Native acceptance in the seven compositions | composed-coverage tests in Combat Damage/Breaking, Core Play Completion, Core Play Dependencies, Foundations, Origins/Feats, Equipment, Spellcasting | **patched.** `_acceptance(inputs)` = sorted `validate_acceptance(candidate_from_accepted_inputs(…).classification)`, lifted as each file's `_references` is. The recorded prior is asserted clean (`== []`). The composition equals exactly one `span …: no acceptance record` per proposed span: 162 / 71 / 66 / 152 / 172 / 409 / 72. No finding is filtered and no approval is fabricated. It is a separate assertion from the reference multiset. The docstrings that retired span acceptance with the physical source are corrected |
| 3 | Current-source reader counts pinned to old UUIDs | Foundations `len(unlike_chunks)` 18 → **21**; Origins `UNLIKE_CHUNKS` 6 → **5**; Equipment 72 → **62**; Foundations and Origins `test_the_accepted_components_read_in_printed_order` (read `prior` over the current DB); Spellcasting `test_a_session_is_the_published_release` | **patched.** Exact printed-order, text and multiplicity assertions are unchanged. The counts are the current release's. They depend on uuid5 chunk IDs, as their comments say, and the comments keep the history. The two printed-order tests read `current()` restricted to the prior record keys (92 and 103). The current authority no longer holds exactly 3 multi-passage components (`play.exploration` `pace_effects` and `travel_pace`, `play.proficiency` `skill_list`), asserted as an exact set, so the multi-passage counts are 97 and 126. Foundations also pins `(97, 32)`. The Spellcasting session is now asserted as current, and `REPLACEMENT.RELEASE` is checked against `recorded.binding` |
| 4 | ESR fixture persisted historical projections to the current DB | `control` and `candidate` fixtures, 51 setup errors | **patched.** The persisted current accepted authority is in a private copy, and an in-memory counterfactual has exactly the 13 resolutions absent. All route, destination, order, disable/replace, membership and refusal assertions are kept. Row 36 (`DEFERRED_GEAR`) now resolves currently, via the later `cited-36-monsters.parts_of_a_stat_block-gear`. Its test is renamed `test_the_deferred_gear_citation_is_not_among_the_thirteen` and asserts that it resolves identically in the candidate and the control |
| 5a | Acceptance files read an empty historical corpus | `test_publication_stays_blocked…` in 11 acceptance files, renamed `test_the_recorded_state_keeps_exactly_its_unresolved_references`; reference-only siblings (e.g. `test_three_targets_stay_unresolved_as_ten_findings`) | **patched** to representation-only `_references`, with exact `UNRESOLVED` lists and the exact `mine` set. Uncovered counts are **retired**. Native refusal is **already safe** on the current release: the existing `test_gate.py` (`test_the_same_projection_claiming_no_unit_is_refused_as_incomplete`) and `test_source_release_readiness.py` (`test_publishing_an_unreviewed_projection_is_typed_refused`) controls. No runtime refusal was added for the Owner's hold, because the current oracle has zero native findings |
| 5b | Useful native checks on old leaf IDs | Foundations passage-order reader; Core Play Completion Breaking Objects, renamed `…_and_the_title_framed` | **patched** to `current()` and the current source. In the current authority, exactly one leaf is multi-owned: `# Character Creation` (catalogue and framing). None is under *Playing the Game*. The 3 Breaking Objects leaves stay solely `combat-damage-breaking/exploration_breaking_objects`. The chapter title is owned solely by `framing-coverage/playing_the_game` |

Out of scope and not touched: unconverted generator tests outside these 25 files, and the Animals historical generator (item 6).

**Typing:** strict mypy over the 25 files (`mypy-residue-pre-1` on the pre-captures, `mypy-residue-post-1` on the edited files) went from 111 errors to 76. Every per-message count fell or stayed the same, and none is new. `mypy-residue-post-2`, after the membership fix, is also 76 with identical per-code counts. No `type: ignore`, `Any`, skip or `pragma` was added (counted per file against the pre-captures). That state was **not** typing clean.

**Typing closure ([review](codex-residue-typing-review.md)).** All 76 errors are fixed over the 26 affected files (pre-captured in `.claude/_sp/release-readiness-20261007/pre-typing-acceptance-1`). The changes:
- `ComponentHandling` is imported from its defining module `models`.
- Annotations replace the ignores that sat on the wrong line of multi-line signatures (`Built`, `Session`, `pytest.CaptureFixture[str]`, `pytest.MonkeyPatch`, `pytest.FixtureRequest`).
- Typed `references`, `key`/`_key`, `where` and `_accepted_inputs`; Conditions `_with` now takes the draft.
- Narrowing: CPD `qualifier is not None` in one comprehension, Foundations `if e.text`, Equipment `isinstance(e, SourceProse)`, a renamed reassigned `view`.
- Typed forwarding for Spellcasting `_record`.
- Cited Targets imports `_service`/`_sliced`/`_request`/`_disable` and `AuthoredProse`/`SourceProse` from their defining modules.

No `Any`, blanket ignore, relaxation or exclusion was added. Every removed ignore was unused or misplaced.

Results:
- `mypy-typing-fix-2`: 26 files, exit **0**.
- Two of the original 16 import edited modules, so the union was checked: `mypy-typing-union-1` and, on the final bytes, `mypy-typing-final-1`, 42 files, exit **0**.

**Runs (focused diagnostics only; coverage disabled; not acceptance or full-gate evidence).** Logs and exits are under `run/`.

| Run | Exit | Files | Result |
|---|---|---|---|
| residue-actions-1 | 0 | Actions proposal and acceptance | 25 passed (the acceptance file changed afterwards; its final hash passed in `residue-acceptance-1`) |
| residue-acceptance-1 | **1** | 11 acceptance files | 2 failed (CPC Breaking Objects, Foundations printed order), 78 passed. Those two files were fixed and re-run in `residue-reanchor-2`; the other nine are unchanged since |
| residue-esr-1 | **1** | ESR candidate | 1 failed, 50 passed (`test_the_deferred_gear_citation_stays_unresolved`, row 36; see family 4) |
| residue-reanchor-1 | **1** | CPC and Foundations acceptance | the same 2 failed, 49 passed; fixed |
| residue-reanchor-2 | 0 | CPC and Foundations acceptance | 18 passed |
| residue-esr-2 | 0 | ESR candidate | 51 passed |
| residue-proposals-2 | 0 | Movement Closure, Conditions Pilot proposals | 52 passed |
| residue-proposals-1 | **1** | Reference Closure, CDB, CPC, CPD, Foundations, Origins, Equipment, Spellcasting proposals; Declared Expectations; Cited Targets | 1 failed, 377 passed (Origins membership; see 2s) |
| residue-origins-1 | 0 | Origins proposal, after the membership fix | 71 passed |
| mypy-residue-pre-1 / -post-1 / -post-2 | 1 / 1 / 1 | strict mypy, 25 files plus `_replacement_chain.py` | 111 / 76 / 76 errors |
| residue-comments-1 | interrupted | six comment-edited files | **not a pass.** Codex stopped it and verified identical executable ASTs and type-comment tags (`.claude/_sp/release-readiness-20261007/codex-comment-rerun-interruption.json`) |
| mypy-typing-start-1 / -fix-1 / -fix-2 | 1 / 1 / **0** | strict mypy, the 26 affected files | 76 / 33 / 0 errors |
| mypy-typing-union-1 | 0 | strict mypy, original 16 plus affected 26 (42) | 0 errors |
| acceptance-native-1 | **2** | — | usage error (no `--check`); nothing ran |
| acceptance-native-2 | 0 | the seven composed tests; Conditions off-by-one and fabricated reference; Equipment suppressed row; CPD typed effects; Foundations two tier-range readers | 13 passed |
| black-typing-final-1 / ruff-typing-final-1 / mypy-typing-final-1 | 0 / 0 / 0 | the 42 files, final bytes | unchanged / all checks passed / 0 errors |

Final-byte limits. Five composition files changed only in their module docstring after `acceptance-native-2`. Splicing each pre-capture's module docstring onto the final code reproduces exactly the hash that ran:

| File | Ran | Final |
|---|---|---|
| CDB | `b3724d6c6d4d` | `3ce1b4d1247c` |
| CPC | `8f7c7aea8570` | `025059b77aa5` |
| CPD | `cfd9031877e7` | `d0373ece9634` |
| Foundations | `65bc315c10e5` | `d03a2c428aa1` |
| Origins | `3ec2b1570e6b` | `003fa5f60802` |

Equipment, Spellcasting and Conditions ran on their final bytes. `mypy-typing-final-1.log` pins the final hashes of all 42 files. The other typing edits are annotation, import or narrowing changes that strict mypy, black and ruff checked on the final bytes, and they were not re-run as whole files. Behavior-touching edits had the node runs above. Earlier focused runs of the 26 files predate this step's bytes. No root run was started. The next one waits for Codex.

## Reachability inventory

| Caller | Kind | Effect of the refusal |
|---|---|---|
| `src/afterworlds/ingestion/mechanical/publication.py:634` (`committed_oracle_for(header.package_uuid, header.release_version)`) | production | A superseded release now raises `OracleLoadError` instead of resolving to retired authority. The current release resolves as before. |
| `committed_oracle_for` → `committed_inputs_for` (`oracle.py`) | production | Single choke point. Admission: `grep COMMITTED_ORACLE_DIR\|load_accepted_inputs(\|glob(` over `src/` and `scripts/` finds the directory enumerated only at `oracle.py:2032`, reached from lines 1979 and 1993. The only other `load_accepted_inputs` call is the explicit-path `load_accepted_oracle` at line 1922, which is not a release selector. `quarantine.py:86` only names a quarantined path. |
| `test_oracle.py` | test | Current success, superseded refusal, subtype refusal and non-`str` `TypeError` |
| `test_accepted_inputs.py`, `test_committed_accepted_authority.py`, `test_packaging.py`, `test_production_release.py`, `test_publication.py`, `test_runtime_production_release.py`, `test_source_release_readiness.py`, `tests/test_quarantine_5c_5d.py` | test | Resolve the current binding or quarantined ones; covered by the final suite |
| `.claude/review-notes/issue-5c-release-order-recording/RECORD.py:413` | historical receipt | `stale = committed_inputs_for(OLD...)` asserts that the old binding resolves to the prior bytes. This change deliberately invalidates that one proof: `RECORD.py --verify` would now stop at line 413. The receipt is **not** rewritten; its past output and hashes stay a record of the state at recording time. The new `test_oracle.py` refusal replaces it. Other native persistence, reader and source-order proofs in that receipt are unaffected. |
| `.claude/review-notes/issue-5d-conditions-1-ACCEPT-generator.py` | historical | Resolves the quarantined `BINDING`, which was already refused. No change. |

## Evidence boundary

- **Interrupted runs:** `focused-magic-1`, `focused-monsters-1`, `focused-animals-1` and `focused-selector-proofs-1` have **no exit** ([Codex audit](codex-interrupted-pilots.md)). Their logs are preserved as captured. They are not passing evidence and were not rerun as whole modules.
- **Pilot drift:** `pilot-classes-glossary` (exit 0) ran Glossary input `d556ed63…`. The settled file is `355d9cc5…` and adds `test_the_recorded_chain_is_the_state_the_proposal_extends` ([boundary](codex-pilot-invalidation.md)). The pilot is evidence for its captured inputs only.
- **Later edits:** `focused-gameplay-2` and `focused-spelldesc-2` passed on earlier hashes. Both files later gained the reference replay; their replay node then passed in `focused-refreplay-siblings-1`. The final suite covers the settled files.
- **Generator probe:** `probe-generator-identity-2` exit 0 only means the reporting probe completed. It catches per-generator exceptions. It found:
  - Classes main differs;
  - class-option-catalogues and Glossary match;
  - Animals fails to build.

  It is not an acceptance gate ([interpretation](codex-generator-probe-interpretation.md)).
- **Typing and acceptance step:**
  - `residue-comments-1` was interrupted. It is not a pass; Codex's AST check stands in for it.
  - `acceptance-native-1` was a usage error.
  - The earlier selected strict 16-file result and the full-root Black/Ruff passes describe an earlier tree. On this tree only the 42 files were checked (`*-typing-final-1`).
  - `mypy src/` (235) is reused: all 242 `src/` files match Codex's `codex-pre-typing-approval-preservation.json` hashes.
- **Historical receipts:** the hashes, counts and statuses in earlier receipts (recording `run/`, `RECORD.py`, the earlier follow-ups) describe their own time. The corrections above supersede their claims only where the correction entries say so.

## Runs, commands and exits

All runs used `venv/Scripts/python.exe .claude/review-notes/issue-5c-release-readiness/run/run.py NAME …`. The command is line 2 of each `run/NAME.log`, and the exit is in `run/NAME.exit`.

| Run | Exit | Command (abridged; full in log) | Result |
|---|---|---|---|
| black-check, ruff-check, focused-typing, focused-typing-2 | 0 / 0 / 0 / 0 | typing increment ([typing-followup](typing-followup.md)) | passed |
| focused-consumers, black-consumers-final, ruff-consumers-fix-2, ruff-consumers-final | 0 / 0 / 0 / 0 | 105-error consumer increment | passed |
| mypy-before | 1 | strict mypy, original set | baseline errors |
| mypy-after-1 / -2 | 1 / 0 | same | 16 closed |
| mypy-consumers / -preedit-copies / -fix-1 / -fix-2 / -final | 1 / 1 / 1 / 0 / 0 | strict mypy, 15 files | 105 closed |
| codex-mypy-checks-valid-invocation | 0 | strict mypy, Checks, `MYPYPATH=src` | clean |
| mypy-before-vs-recording, mypy-compare | 0 / 0 | log comparison | — |
| focused-family-before / -before-2 | 2 / 1 | 14-file fixture sweep before the correction | failure inventory |
| pilot-candidates | 0 | `run_focused_tests.py --check _replacement_chain.py …` (3 candidates) | 63 passed |
| pilot-classes-glossary | 0 | Classes and Glossary files | pre-drift Glossary |
| focused-acceptance-equip-spell-1 | 0 | Equipment and Spellcasting acceptance files | 8 passed |
| codex-selector-subclass-before / -after-1 | 1 / 0 | `codex_selector_probe.py` | bypass, then `{"retired_binding_refused": true, "error_type": "OracleLoadError"}` |
| focused-oracle-subclass-1 | 0 | `--check oracle.py --check test_oracle.py test_oracle.py` | passed |
| mypy-oracle-subclass-1 | 0 | `mypy --strict oracle.py test_oracle.py` | clean |
| focused-origins-1 / -2 | 0 / 0 | `…::test_three_citations_resolve_and_91_findings_stay` | passed |
| focused-checks-1 | 0 | four Checks nodes | passed |
| focused-gameplay-1 / -2 | 0 / 0 | scope and disjointness nodes | passed, earlier hash |
| focused-spelldesc-1 / -2 | 0 / 0 | scope and disjointness nodes | passed, earlier hash |
| probe-generator-identity / -2 | 0 / 0 | probe scripts | see the evidence boundary |
| probe-leaf-overlap-1 | 0 | `leaf_overlap.py` | `old 10464 new 10464 shared 10464` |
| focused-magic-1, focused-monsters-1, focused-animals-1, focused-selector-proofs-1 | **none** | — | interrupted |
| focused-animals-records-1 | **1** | `--check test_animals_proposal.py …::test_the_records_are_the_stat_blocks` | 1 failed (component order) |
| focused-animals-records-2 | 0 | same, plus `…::test_an_animal_reads_itself_with_the_rules_governing_it` | 2 passed |
| focused-magic-refreplay-1 | 0 | `--check test_magic_items_proposal.py …::test_accepted_then_resolved_in_memory_preserves_everything` | 1 passed (scope-count form, superseded) |
| black-magic-exact-1 / ruff-magic-exact-1 | **1** / 0 | `black --check` / `ruff check` Magic | would reformat; then formatted |
| black-magic-exact-2 / ruff-magic-exact-2 | 0 / 0 | same | clean |
| focused-magic-exact-1 | 0 | `--check test_magic_items_proposal.py …::test_accepted_then_resolved_in_memory_preserves_everything` | 1 passed (exact form) |
| focused-refreplay-siblings-1 | 0 | `--check` Gameplay, Spell and Monsters; the three `…::test_accepted_then_resolved_in_memory_preserves_everything` and Monsters `…::test_the_committed_oracle_records_the_owner_acceptance` | 4 passed |
| mypy-affected-final | 0 | `mypy --strict` on 15 + Checks | "no issues found in 16 source files" |
| black-correction-final | 0 | `black --check` on 26 files | unchanged |
| ruff-correction-final | 0 | `ruff check` on the same files | passed |
| secrets-typing-private-copy / -real-hook | 0 / **1** | earlier typing increment | real hook non-green while unstaged |
| probe-magic-shared-1 / -2 | **1** / 0 | `magic_shared_probe.py` (read-only) | `ModuleNotFoundError: tests`, fixed by `sys.path`; then current vs prior shared records and edges |
| black-magic-residue-1 / ruff-magic-residue-1 | 0 / 0 | `black --check` / `ruff check` Magic | clean |
| focused-magic-residue-1 | 0 | `--check test_magic_items_proposal.py …::test_each_section_reads_its_subheadings_in_printed_order …::test_an_item_equipment_sells_is_one_record_in_both_catalogues` | 3 passed (1 + 2 parametrized), 09:45:26Z–09:49:24Z |

| final-pip-audit-1, final-pip-audit-network-2 | 1 / 1 | `-m pip_audit` | **not started by this engineer session.** They began at 09:37:38Z, apparently Codex's final gates. The first is a DNS failure; the second reports `afterworlds` "not found on PyPI". Recorded only; not interpreted here. |

Secrets checks for this correction are listed at the end of this note.

Every Python file in the diff-scope table was last modified before `black-correction-final` and `ruff-correction-final` ran (09:26:03Z). The exception is `test_magic_items_proposal.py` (see the input status below). The restart doc changed later as well, but only in its opening. There is no CR byte in any of them.

## Input and hash status

| Input | SHA-256 | Note |
|---|---|---|
| `test_magic_items_proposal.py` | `0bdd921a…` | Exact replay form restored at 09:36:38Z (`focused-magic-exact-1`, `black-`/`ruff-magic-exact-2`, on hash `e53508e3…`). Residue edit at 09:44:10Z (+18 −7 against `pre-edit-5/test_magic_items_proposal.before-residue-1.py`); re-checked by `black-`/`ruff-magic-residue-1` and `focused-magic-residue-1`. `focused-magic-exact-1` stays valid for its node, which the residue edit did not touch, but it ran on the earlier hash |
| `.secrets.baseline` | `c8b91695…` | Was `7d7738f6…`; 10 rows added, unstaged (see the secrets section) |
| `docs/architecture/issue-5c-5d-clean-restart.md` | `c956cad1…` | opening only (+6 −6 against `pre-edit-2`); the historical body is byte-identical and there is no CR |

The external `final-pip-audit-1` and `final-pip-audit-network-2` runs started at 09:37:38Z. They ran after the exact Magic restoration and before the residue edit and baseline change. They are not evidence for the settled tree.

## Exact diff scope

Each file is diffed against the pre-correction snapshot in `.claude/_sp/release-readiness-20261007/`: `pre-edit-2` for the first block and `pre-edit-3` for the second. All are working-tree only.

| File | ± |
|---|---|
| `src/afterworlds/ingestion/mechanical/oracle.py` | +23 −0 |
| `src/afterworlds/ingestion/mechanical/oracles/README.md` | +13 −4 |
| `docs/architecture/issue-5c-5d-clean-restart.md` (opening only; historical body identical) | +6 −6 |
| `tests/ingestion/mechanical/test_oracle.py` | +59 −0 |
| `test_canonical_ordering.py` | +8 −3 |
| `test_gate.py` | +4 −6 |
| `test_persistence.py` | +3 −3 |
| `test_raw_state_closure.py` | +11 −8 |
| `test_review_round_3_applicability_types.py` | +9 −3 |
| `test_review_units.py` | +11 −3 |
| `test_schema_12_practical_reliability.py` | +14 −8 |
| `test_source_release_readiness.py` | +22 −16 |
| `conftest.py`, `test_accepted_inputs.py`, `test_committed_accepted_authority.py` | unchanged in this correction (typing increment earlier) |
| `src/afterworlds/ingestion/mechanical/publication.py` (docstring) | +5 −9 |
| `_replacement_chain.py` | +19 −0 |
| `test_animals_proposal.py` | +172 −146 |
| `test_character_origins_feats_acceptance.py` | +29 −55 |
| `test_checks_actions_rests_proposal.py` | +64 −53 |
| `test_classes_proposal.py` | +84 −112 |
| `test_equipment_acceptance.py` | +11 −49 |
| `test_final_ten_references_candidate.py` | +33 −11 |
| `test_finite_reference_routes_candidate.py` | +4 −3 |
| `test_gameplay_toolbox_proposal.py` | +79 −49 |
| `test_magic_items_proposal.py` | +115 −68 |
| `test_monsters_proposal.py` | +75 −43 |
| `test_reference_alternatives_candidate.py` | +4 −3 |
| `test_rules_glossary_completion_proposal.py` | +77 −119 |
| `test_spell_descriptions_proposal.py` | +81 −52 |
| `test_spellcasting_acceptance.py` | +11 −50 |

Notes, in addition to the code files above:

- **Notes changed:** `recorded-followup.md` gained a correction bullet. `typing-followup.md` rows 60–62 now carry closed or superseded markers.
- **New notes:** this file and `external-sync-note.md`.
- **Baseline:** `.secrets.baseline` gained exactly 10 rows, additive and unstaged (see the secrets section).
- **Unchanged:** accepted artifacts, oracles, proposals and generators.

## Architecture Notes

No drift from design principles.

- The superseded-release refusal enforces the 21 September Decision at the single resolution choke point. The two retired artifacts are kept as evidence, not deleted.
- The test corrections change expectations only where a test compared states across releases. No accepted semantics, schema, source content, reader retention or supplement behaviour changed.
- One historical receipt proof (`RECORD.py:413`) is knowingly invalidated and disclosed, not rewritten.

## Remaining items

| Item | Class | Owner / next |
|---|---|---|
| Final local gates on the settled tree: Black, Ruff, `mypy src/`, strict mypy (original 16 plus the affected 26; 0 locally in `mypy-typing-final-1`), the full default `pytest` with the 80% coverage threshold, `pip-audit`, and scoped secrets | merge-blocking, required | Codex, after reviewing this diff |
| Real relative secrets hook is exit 1 while `.secrets.baseline` is unstaged | known non-green; not cured by staging | Publication workflow |
| `run/codex-failed-log-classify-1.log` line 8: 2 SHA-1 fingerprint echoes not in the baseline (`secrets-failed-root-recheck-1` exit 1) | scoped secrets non-green for that file; outside the eight authorized rows | Codex scoped secrets review |
| Dependency-vulnerability repairs | deferred until the restart is complete (per the Owner) | Engineer, after the restart |
| Used `type: ignore[index]` at `test_accepted_inputs.py:1216–1217`, which were lines 1212–1213 before edits | non-blocking cleanup | Engineer |
| Legacy Animals generator cannot build current | obsolete tool, retirement authorized; not patched | Retire with superseded tooling |
| Full CI (including frontend and E2E) and fresh final-head review | required before merge | After Owner publication authorization |
| #132/#137 synchronization ([draft](external-sync-note.md)) | external write, not authorized here | Owner and publication workflow |

## Secrets checks (this correction)

The file list has 146 files: the diff-scope files, `recorded-followup.md` and everything under this folder (`.claude/_sp/release-readiness-20261007/correction-secrets-files.txt`). No 35 MB payload was rescanned. These runs read `.secrets.baseline` at SHA-256 `7d7738f6…`. It has since changed by design: see "Baseline rows added" below.

| Run | Exit | Meaning |
|---|---|---|
| secrets-correction-scan, -private-copy, -real-hook | 1 / 1 / 1 | **invalid invocation** (`python.exe` passed twice to `run.py`); preserved as captured |
| secrets-correction-scan-2 | 1 | read-only `SecretsCollection` under the baseline's settings: rows not in the baseline in 3 files |
| secrets-correction-private-copy-2 | 1 | same 10 locations, against a plain private copy |
| secrets-correction-private-additive | 0 | private copy plus 10 inspected rows, `is_secret: false` |
| secrets-correction-private-copy-3 | 3 | no secret found; the hook rewrote line numbers in the private copy |
| secrets-correction-private-copy-4 | **0** | private-copy content check passes |
| secrets-correction-real-hook-2 | **1** | `.secrets.baseline` is unstaged; honestly non-green, not cured by staging |

All 10 hits were inspected and are public SHA-256 digests:

- the recorded oracle SHA `def7caa1…` at `_replacement_chain.py:148` and `test_oracle.py:282`. Its hashed secret, `97e66fb6…`, is already in the baseline for 7 other files.
- binding and content digests in a SQL-parameter dump at `run/focused-family-before-2.log` lines 364 and 876.

No `pragma: allowlist secret` was added.

**Delta re-scan, the final step.** It covers the edited follow-up, the sync note, the opening, the Magic test and every run file newer than the first list (`correction-secrets-delta.txt`, 36 files):

| Run | Exit | Result |
|---|---|---|
| secrets-delta-scan-1 | 0 | 0 hits |
| secrets-delta-private-copy-1 | 0 | passed |
| secrets-delta-real-hook-1 | 1 | `.secrets.baseline` is unstaged |

This paragraph was then added, followed by one follow-up-only re-scan (`secrets-followup-rescan-1`). That run's own log and exit are the only files left uncovered.

## Baseline rows added (residue step)

The 10 inspected rows above were copied into the working-tree `.secrets.baseline` from the private copy (`correction-private-3.baseline`). Only the entries for the three owning files were taken: `run\focused-family-before-2.log` (8 rows), `_replacement_chain.py` (1) and `test_oracle.py` (1).

- The hook's line-number rewrites of 6 existing Animals and Monsters rows in the private copy were **not** taken. Neither were its `generated_at` and `filters_used` differences.
- Every prior row, the key order and all settings are unchanged. This is checked by parsed comparison and by a text diff showing 0 lines removed and 86 added. The format is `indent=2`, LF and a trailing newline.
- The SHA-256 changed from `7d7738f6…` to `c8b91695c9711b7e725c32a7e58df356a36b1819991fe7bcb4dce834e618500c`. The backup is `pre-edit-5/secrets.baseline.before-residue-1`.
- **Known follow-on:** the real baseline keeps 6 Animals and Monsters rows at their old line numbers, which no longer match the current files. The first staged real-hook run will probably rewrite them, possibly with exit 3. That is expected line-number upkeep for the publication workflow, not a regression.
- **Not staged.** The preserved index, including its earlier staged `.secrets.baseline` entry, is unchanged (cached-diff SHA `75bc69ef…`). Unstaged is the publication boundary.

| Run | Exit | Result |
|---|---|---|
| secrets-residue-scan-1 | 0 | read-only scan of the three owning files plus the Magic test: 10 hits, 0 not in the baseline |
| secrets-residue-real-hook-1 | **1** | "Your baseline file (.secrets.baseline) is unstaged." Honestly non-green; the baseline is unchanged by the hook |

Final-gate logs may add further inspected public-digest locations. Those are not covered here.

**Residue delta re-scan, the final step:** `secrets-residue-delta-1`, read-only, over `.claude/_sp/release-readiness-20261007/residue-delta-files.txt`. That list covers this note, the restart doc, the Magic test, `probe-magic-shared-1`/`-2`, `black-`/`ruff-`/`focused-magic-residue-1`, `secrets-residue-scan-1`, `secrets-residue-real-hook-1` and `secrets-followup-rescan-1`, each `.log` and `.exit`. Its result is in its own log and exit, which are the only files it leaves uncovered.

## Secrets check (full-gate residue step)

`secrets-fullgate-residue-delta-1` (exit 1) is the read-only `correction_secrets_scan.py` over 57 files (`fullgate-residue-secrets-files.txt`): the 25 test files edited in this step, this note, the restart doc and every `run/` file newer than `secrets-residue-delta-1`. The files edited in this step have **0 hits**. The 10 hits not in the baseline are all in Codex's own logs, and all were inspected:

- `final-pytest-coverage-1.log` lines 158 and 821: 8 SHA-256 binding and content digests in a SQL-parameter dump.
- `codex-failed-log-classify-1.log` line 8: 2 SHA-1 detect-secrets fingerprints echoed in an `unmatched_fingerprints` assertion.

These are public digests. No baseline row was added for them, because the logs are Codex's and the scoped secrets review is Codex's. No `pragma` was added and `--baseline` was not run. The run log and exit for this scan, and this paragraph, are the only files it does not cover.

## Secrets check (typing and acceptance step)

- **`secrets-failed-root-rows-2`** (exit 0) added the 8 rows Codex inspected for `run/final-pytest-coverage-1.log` to `.secrets.baseline`, each with `is_secret: false`. The classification is in `.claude/_sp/release-readiness-20261007/failed-root-secret-classification.json`: six digests match recorded public oracle JSON, and two are `rp_mech_projections.payload_hash`. The script asserted:
  - its own scan found exactly those 8 (hash, line) locations;
  - every earlier row, the row and key order, and all settings and metadata are unchanged;
  - the file key is in sorted position.

  The result is a pure 66-line insertion. Its backup is `baseline-before-failed-root-rows.baseline`.
- **`secrets-failed-root-rows-1`** (exit 1) is a failed invocation: a path escape in the script. It wrote nothing.
- **`secrets-typing-delta-1`** (exit 0) covered 58 files: the 26 test files, this note, the restart doc and every `run/` file newer than `secrets-fullgate-residue-delta-1`. It found 4 hits, 0 not in the baseline.
- **`secrets-failed-root-recheck-1`** (exit 1): `final-pytest-coverage-1.log` is now covered. `codex-failed-log-classify-1.log` line 8 still has its 2 SHA-1 fingerprint echoes, which are not in the baseline. They are outside the eight authorized rows, so they are left for Codex's scoped review.

No `pragma` was added and `--baseline` was not run. The real hook stays non-green while the baseline is unstaged. This paragraph and the recheck's own log are not covered by these scans.


## Codex scoped evidence update, 7 October 2026

The two detector-fingerprint echoes in the retained failed classification log were inspected and added additively by `codex-review-fingerprint-baseline-1` (native 0). They are the exact SHA-1 values labelled `unmatched_fingerprints` at line 8, not credentials. Its scan/assertions admit only those two locations and preserve every earlier row, key order, setting and generation field. The total increment is now 20 non-secret rows. No failed log was rewritten. Final scoped content/hook checks remain pending after the full gate and final notes settle.

Root `final-black-2` and `final-ruff-2` are native 0. Parent `codex-post-correction-static-pins-2` verifies all final 42-file typing/formatter/linter hashes and unchanged production inputs. The full pytest/coverage run is pending; no focused receipt substitutes for it. Publication remains held.


## Codex final gates, 7 October 2026

See [the final readiness result](codex-final-readiness.md). Full pytest/coverage is native 0: 7,397 passed, 141 skipped, 252 warnings, no failures or errors; 92.48% coverage. All 616 immutable frozen inputs remain unchanged. Root Black/Ruff and final affected-test strict mypy pass; unchanged production typing and accepted proof are reused.

The final scoped check (`final-scoped-secrets-1`) scanned 202 increment files, found 11 already baselined detector hits and **zero unbaselined locations**. The private copy returned native 3 for metadata normalization, then native **0**; only that private copy changed. The real relative hook returned native **1** because `.secrets.baseline` is unstaged. The real baseline bytes/rows and original index remain preserved. This is content-check success and an explicit held publication hook, not an all-green publication claim.

Only dependency-vulnerability repair remains deferred. No increment change was staged, committed, pushed, merged, published or activated.
