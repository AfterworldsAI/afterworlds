# CRD Issue 15c — handoff for Codex independent review

- **Branch:** `codex/issue-15c-bounded-d20`.
- **Commit:** local `eb60d9f`, on baseline `e83018c`.
- **Not pushed. No PR opened. Nothing merged.**
- Nothing was migrated, published, activated or launched in any shared runtime.
- `D:\AI\Claude\afterworlds-runtime` was never touched. #129 stays frozen; #132 and #137 are unchanged.

## Update: scope revision and candidate C2

#191 was updated (body `8225e1b6…57a2`) to add creature attacks, bounded Multiattack, and the tool and omitted-source repairs. The semantic packet under review is now **C2** (`candidate-c2/README.md`). C1, item 1 below, is superseded and preserved. The implementation on `eb60d9f` is unchanged; its operations that depend on C2 remain held.

## Two things to review

1. **Semantic candidate C1** (`candidate/README.md`).
   - **What to check:** the content of three hashed parts, the classification rule (`gap-inventory.md`), and the default exclusion of monster stat-block actions.
   - **Why it matters:** this is the blocker. Weapons, the eight masteries, the zero-HP lifecycle, saves, initiative, tool checks and GameMaster-difficulty checks are **held** until Codex reviews C1 and the Owner explicitly accepts it.
   - **Process question, not a semantic one:** should the Owner accept the content first and native minting follow, or should minting come first? The cost is stated in the packet.
2. **The independent implementation on this branch.** Covered by `docs/architecture/issue-15c-bounded-d20.md`, which has the acceptance-criteria map and the Architecture Notes.

## Where to look in the code

| Surface | Files |
| --- | --- |
| Manifest, certification, refusal kinds | `src/afterworlds/pipeline/rpg/capability.py` |
| Check executor: typed numbers; unexecuted contributors refuse | `src/afterworlds/pipeline/rpg/checks.py` |
| Backend path through the executor; legacy announce/consume left for 15b | `pipeline/rpg/adapter.py` |
| Player roll refused before anything pends; over-bound proposals refused; refusal kinds preserved | `pipeline/rpg/service.py` |
| Wiring (adjudication + dice; no pending service); canned fake response | `api/pipeline_wiring.py`, `api/fake_pipeline.py` |
| Setup turns resolve play status before the sheet; binding refusals are typed | `pipeline/orchestrator/service.py` |
| `TurnCharacter.index` (exact binding authority) | `services/dnd5e_state/turn.py` |
| Identity-only proposal fields and the tool schema enums | `models/rpg.py`, `pipeline/rpg/caller.py` |
| Prompt contract v2 | `docs/prompts/rpg_adjudication.md` |
| Dated reconciliations | ADR-015 D7 (forward reference), ADR-015b (status note), the 2b traceability document, the Known Unknowns 5c entry |

**One defect found and fixed during implementation.** Once adjudication was wired, RPG setup turns failed: the sheet resolver ran before play status was known. `test_rpg_setup_turn_does_not_require_completed_character_sheet` caught it. The orchestrator now resolves play status with the session-only resolver first.

## Evidence

All of it was run on `eb60d9f` unless noted.

**Static gates and dependency checks:**
- Black, Ruff and mypy strict (249 files) are clean on `src/` and `tests/`.
- detect-secrets is clean on the staged files. False positives are documented: inline pragmas, plus three audited baseline entries for the candidate JSON digests.
- `pip-audit` reports no known vulnerabilities with CI's documented chromadb `--ignore-vuln` set. No dependency changed.

**Focused diagnostics (not acceptance):**
- `tests/pipeline/rpg/test_bounded_checks.py`: 51 passed.
- `test_adjudication_service.py` with `test_adapter.py`: 54 passed.
- The orchestrator and API suites: 330 passed.
- The E2E on G1 published in a disposable store (`tests/ingestion/mechanical/test_bounded_d20_on_published_release.py`): 8 passed.

**Full suite:**
- Full `pytest -q` with the configured coverage on `eb60d9f`: **no result.**
  - The serial run hit the 2-hour background-task limit and was stopped before it finished.
  - The block-buffered log shows only early progress (about 6%).
  - It is not reported as passed or failed, and it was not rerun for the candidate-only C2 work.
- Exact-head CI (eight shards, collection census, combined coverage) has not run. It needs a push, which waits for review.

## Unresolved boundaries

- **Merge sequencing (consequence, not decided in code).** Adjudication is wired, and prompt v2 tells the GameMaster to propose a mechanic even when it may be unsupported. If this branch merged before C1 is accepted, combat turns and GameMaster-difficulty skill turns in an in-play RPG story would fail visibly as `PIPELINE_ERROR`. AC1 requires that behaviour, but it leaves RPG mode largely unplayable until C1 lands. Merge is separately gated.
- **Armor is conservative.** Any worn non-shield armor refuses the three admitted checks (all Strength (Athletics)). That includes trained wearers, because armor category and the training rule are held on C1-C.
- **Billing for the newly wired pass.** Read-only check, clean: `RPG_ADJUDICATION` has a model tier and settlement line items (`entitlement/policy.py`) and an Anthropic adapter mapping.

- **C1 content and process.** Codex review and Owner acceptance are required, as described in item 1 above.
- **Contributor lists.** These are conservative, code-owned lists of features, traits and feats that bear on ability checks. Codex may want them reviewed as part of C1 rather than accepted as code.
- **State placement still to be built (held work).** Actor-turn/elapsed-time authority, position, timed mastery effects and the per-subject monster/character classification are proposed as an additive 15c table. The 2b document schema would not be bumped. It is recorded here so it can be reviewed before it is built.
