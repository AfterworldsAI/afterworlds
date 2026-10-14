# CRD Issue 15b — accepted authority landing: record C9, land schema 22, recertify 15c

Stacked on `codex/issue-15b-contest-authority` (#194, accepted at `5d05f473`, unmerged). Group 17's authority landing gate (ADR-015b 15b-37, gate 2).

## What was built

- **C9 successor recorded natively** from the Owner's acceptance of #194 and the native packet: `srd-5-2-1-corpus-8781d4e0-a3b-15b-c9.json`, SHA-256 `01729b532a0ff46047608d9e46d539851ba2c9a32aaa9e0468ae0babb902ec7b`, schema 22 `b073cd4f…414f`, lift `5d-lift-schema-21-to-22`, oracle identity `924321df…ab0c`, projection `3703faf5-8b51-5c3f-b28c-b378b005f7bf`, payload `c7a52d55…2f` (all equal to the accepted packet). The four exact accepted proposals were accepted with native `accept_proposal` on C8 (`ead7fa9d…`, unchanged); nothing was rebuilt. Only `reviewer`, `accepted_at` and `rule` differ from the reviewed SIMULATED preview, only on the four touched batches; the other 20 batches' rows equal C8's. Write-once/idempotent (`record_successor.py`).
- **Selection:** C8 superseded by digest; distributions ship C9 and exclude C8.
- **Recertification:** `CERTIFIED_RELEASE` → `3703faf5-…`. All 14 executable operations certify on the production-selected successor; no governing set or fingerprint moved (C9 types only the 336 creature profiles, certified per subject). The superseded C8 file, loaded and identified natively, refuses every operation with `incompatible_certification`; C8-era template digests are stale on C9.
- **Docs:** Owner receipt and CI evidence copied byte-for-byte; ADR-015b acceptance status note, Group 17 and the combat Action cost marked accepted, gate status; decision record, known_unknowns, 15c traceability, oracles README and review-note READMEs. Pre-acceptance text and the preview simulation are preserved.

## Acceptance coverage

| Requirement (brief / Group 17 gate 2) | Evidence |
| --- | --- |
| Real native recording of the exact accepted successor | `record_successor.py`, `recorded-followup.json`, `record.*.txt` (exit 0, 360 s) |
| Evidence-only delta, keyed by identity, untouched rows preserved | `comparison_with_reviewed_preview`, `untouched_rows_equal_c8_successor` |
| Native checks on the recorded successor | validate 0 findings; persist → reconstruct → re-identify; own gate passes |
| Schema 22 lands with the recording | resolution test: schema 22, lift, 336 skills facts |
| All 14 operations recertified; stale C8 refused | `recert/governing-components.json`; `tests/pipeline/rpg/test_certification.py` |
| S1 stays an in-memory override, #129 frozen | no S1 recording or activation; no #129, migration, Phase 3 or 19b change |

## Test evidence (local, FOCUSED DIAGNOSTICS ONLY; not full-gate evidence)

- `black --check src tests`, `ruff check src tests`: clean. `mypy src/`: no issues (268 files). detect-secrets hook: passes on the staged change.
- Recording and publication modules, run against C9: `test_accepted_release_publication.py` 27 passed (1,472 s).
- Selection/oracle/packaging/succession/committed-authority/schema/creature-skills modules: 118 + 1,049 passed (see below).
- `tests/pipeline/rpg` + `tests/services/dnd5e_state`: 806 passed.
- `test_bounded_d20_on_published_release.py`, `test_srd_state_on_published_release.py`, `tests/ingestion/corpus/test_packaging.py` (wheel/sdist): 26 passed.
- Other committed-authority consumers (succession anchors, lift evidence, publication, readiness, schema legality, equipment catalogue, quarantine): 1,391 passed; models/persistence/orchestrator consumers: 325 passed.
- **Disclosed:** the first combined focused run had 1 failure, a keyword-only `CreatureSkillBonus` call in the new test, since fixed. It also had errors (`NoReferencedTableError: stories`) in ingestion persistence tests whenever `tests/pipeline/rpg` was collected in the same process. That is a pre-existing ORM collection-order hazard: it reproduces with `test_bloodied.py`, unchanged since main. The same nodes pass in their own process. It is not patched here.
- **Not run locally:** the full suite with coverage and pip-audit. There is no dependency change. The four C8→C9 proposal suites do not read committed authority. Final exact-head CI is required.

## Architecture Notes

No drift from design principles. Deliberate choices:
- **Adapter and manifest versions are not bumped.** No adapter code or manifest entry changed, and the versions are recorded but never compared. The certificate's projection distinguishes C8 from C9.
- **Oracles README corrected.** It had been stale since C7 and C8.
- **Branch history is not linear with `5d05f473`.** `03f7139c` replays its docs commit with identical content on top of the preview commits.
- **Graphify not run.** `.local-tools/aw-graphify.ps1` is absent from this worktree.
- **Pre-existing hazard surfaced.** The ORM collection-order hazard above.

Remaining 15b work, decided and ordinary: the contest operation and lifecycle; Owner Decision 15b-36's cutover; the Finesse pre-roll adjustment; the stored knockout decision; 19b consuming the settled API. #129's explicit resume gate is not released. No merge, publication, activation or shared-runtime operation.

## Codex rerun (verify mode)

Copy the git-ignored preview (`srd-…-c9-PREVIEW.json` `3ad7bdcb…` and the four `*-C9-PROPOSAL.json`) into `.claude/review-notes/issue-15b-c9-native/preview/` with hash checks, then:

```
$env:PYTHONPATH = "src"; $env:PYTHONIOENCODING = "utf-8"
venv\Scripts\python.exe .claude/review-notes/issue-15b-c9-recording/record_successor.py --inputs <private copy of c9-native-work/inputs>
```

Verify mode rewrites `recorded-followup.json` with `"mode": "verify"`. Do not commit that diff.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
