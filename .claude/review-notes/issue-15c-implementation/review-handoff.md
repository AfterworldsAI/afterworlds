# CRD Issue 15c — handoff for Codex independent review

- **Branch:** `codex/issue-15c-bounded-d20`.
- **Commits:** local `eb60d9f` … `246e6ae` and later, on baseline `e83018c`. See `status.md` "Latest".
- **Not pushed. No PR opened. Nothing merged.**
- Nothing was migrated, published, activated or launched in any shared runtime.
- `D:\AI\Claude\afterworlds-runtime` was never touched. #129 stays frozen; #132 and #137 are unchanged.

## Current (13 October 2026): C7 accepted, recorded locally, ammunition executing

**C7 is Owner-accepted**: the exact consolidated packet `4912928f…eb2c` (`../issue-15c-c7-native/owner-acceptance-2026-10-13.md`). The Owner also authorized integration and recording (`owner-c7-integration-2026-10-13.md`). The earlier "C7 integration blocked" note is superseded.

**Integrated.** The reviewed preview commits are now on this branch:

| Preview commit | Branch commit |
| --- | --- |
| `221a8e7` | `db60370` |
| `2d9f694` | `df9c601` |
| `ed23cb7` | `02fb067` |
| `3166f22` | `ddda49b` |

**Recorded (`952ae53`):** `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json`, SHA-256 `2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373`.
- **Identities equal the packet.** The recorded file differs from the accepted preview in its receipt evidence only (next bullet).

  | Item | Value |
  | --- | --- |
  | Oracle | `cb04163b…5ef6e` |
  | Projection | `8446ab6b-be75-5999-8a9b-74fa133c030a` |
  | Payload | `cffcdbfa…eb65a` |
  | Proposals | `1e7b63d3…` (character-origins-feats), `b8c65454…` (equipment) |
  | Schema | `5d-representation-schema-20` / `759dcc1f…` |
- **Evidence and identity checks** (`../issue-15c-c7-recording/`: `record_successor.py`, `owner-acceptance.json`, `recorded-followup.json`):
  - **What differs from the preview:** only `reviewer`, `accepted_at` and `rule`, on the two batches' 643 records and 47 review units. Rows are matched by identity.
  - **Untouched rows:** they keep their order. Canonical evidence order reads `accepted_at`, so the touched rows' position follows the real recording time.
  - **Unchanged:** the C5 successor `23e5d8e0…`, G1 and the predecessor.
  - **Checks that passed:**
    - native validation found nothing;
    - persist, reconstruct and re-identify is clean;
    - the read-only gate passes in a private store copy.
  - **Verify mode:** a write-once rerun rebuilt the file byte for byte, at the same recording time `2026-10-13T09:56:00Z`.
- **Reproducibility.** The pinned preview `d661cc3b…` lives git-ignored in worktree `agent-afb6123d0b7851456`. `build_c7_preview.py --twice` regenerates it byte for byte, so the recording stays reproducible if that worktree goes away.
- **Selection and packaging:**
  - C5 is superseded by digest.
  - Packaging ships the C7 successor.
  - The oracle, packaging, succession, committed-authority and publication tests follow it.
  - `.secrets.baseline` covers the new and changed review files.

**Recertified (`0da06c9`).**
- `CERTIFIED_RELEASE` moves to projection `8446ab6b`; versions are now adapter `15c-d20-3` and manifest `15c-manifest-3`.
- Component evidence was diffed against C5: only `weapon_attack` changed (`463322bf` → `a5fe16ae`), by adding the five typed supplies it now reads. No other governing component moved.

**Ammunition executing (`0da06c9`, `246e6ae`).**
- **Selection:** a held ammunition item is named and checked against its typed supply, the weapon, and the quantity.
- **Expenditure:** one per attack, hit or miss, applied by CAS on the read revision in the Turn's transaction. The last one removes the holding.
- **Preflight:** counts every shot of the turn against the quantity read.
- **Constraints kept:** Loading, free-hand loading and action accounting are unchanged.
- **Flat damage:** the Blowgun's flat damage now executes.
- **Feat categories:** Origin-category eligibility certifies (Skilled under an ASI).
- **Evidence:**
  - all nine weapons fire, hit or miss;
  - incompatible ammunition refuses, including sling versus firearm bullets;
  - CAS, stale-revision, overspend and removal behave;
  - Loading and action-budget refusals roll no dice;
  - end-to-end, a shot expends one, the last arrow is removed, and a failure after expenditure rolls everything back.

**Completed since:** Codex's Bloodied and linked Grappled→Restrained classification is implemented (`10ddbfd`, `ae011bb`). No C5-positive boundary remains. See `status.md` "Latest" and `sibling-audit-creature-silent-drops.md`. pip-audit reports five pre-existing `chromadb` advisories with no fix versions; they need a disposition.

**Still required:**
- Codex review of the roster, traits, clauses and Multiattack implementation;
- Architecture Notes reconciliation;
- the stable final head, full gates via the independent supervisor, and CI.

There is no push, PR or merge, and nothing is published or activated.

## Earlier update: C5 successor recorded, implementation continuing

- **Owner acceptance.** The Owner accepted the exact native C5 packet on 12 October 2026.
- **Recorded successor.** `srd-5-2-1-corpus-8781d4e0-a3b-15c.json` (`23e5d8e0…`), whose identities equal the packet. G1 is superseded by digest.
- **In `3f0ba29`:**
  - the schema-19 test reconciliation;
  - contributing-grant validation;
  - difficulty, tool and Initiative checks.
- **Since then:** the feat-entitlement residues are fixed, and raw C6-r2 is ready for review.
- **Combat/state work** is in progress under the approved input decisions.

## Earlier update: native schema-19 preview, Owner acceptance HELD

`../issue-15c-native/OWNER-ACCEPTANCE-PACKET.md` gives the exact identities: schema `3734ccf7…d18f`, preview `cd9d1d27…20d3`, oracle `000c4c10…6e76`, projection `44f212d5-32dd-5469-8f05-f0d236492347`.
- It supersedes the earlier `aa9fe91e…` preview. Only the schema descriptor changed (a class-name leak in rule text, fixed). Content equality is shown indirectly; the packet has the old→new table and its evidence.
- All replacement acceptances are SIMULATED. Nothing was accepted, recorded, committed, pushed, published or activated.
- Read alongside `../issue-15c-native/correspondence.md`.
- **Open:** Owner acceptance. Landing needs the native successor recording and the schema-18 test fixtures and pins updated, then full gates, CI and Codex review.

## Earlier update: raw candidate C5, ready for Codex review

`candidate-c5/README.md` applies `codex-c4-review.md` (all five findings), `codex-c5-grant-family-addendum.md`, `codex-c5-provisional-linkage.md` and `codex-c5-provisional-roster.md`.

| Part | SHA-256 |
| --- | --- |
| C5-A | `866f2c13…87c9` |
| C5-B | `187c041b…f3f6` |
| C5-C | `bb3761b9…6ad4` |
| Capability | `6037ea70…efe6` |

**State:**
- Uncommitted and unstaged.
- C1 through C4 are byte-preserved.
- No native work, no acceptance, no full-suite rerun.
- Production code and tests are untouched.

## Earlier update: raw candidate C4

`candidate-c4/README.md` applies:
- `codex-c3-review.md` (all five families);
- `codex-grant-trust-review.md` (the grant/selection source facts);
- every finding in `codex-c4-provisional-findings.md`, which reviewed the earlier C4 snapshots.

| Part | SHA-256 |
| --- | --- |
| C4-A | `901083ec…5e62` |
| C4-B | `f679b06c…5c08` |
| C4-C | `2c34a6f0…fb5f` |
| Capability | `2d884ffb…3a8e` |

**State:**
- Uncommitted and unstaged.
- C1, C2 and C3 are byte-preserved.
- No native work, no acceptance, no full-suite rerun.
- Production code and tests are untouched.

## Earlier update: raw candidate C3

`candidate-c3/README.md` corrects the eight findings and the qualification residue in `codex-c2-review.md`.

| Part | SHA-256 |
| --- | --- |
| C3-A | `aaa5a20f…9ff9` |
| C3-B | `bb086082…5524` |
| C3-C | `36be82a0…422b` |

**State:**
- Uncommitted and unstaged.
- C1 and C2 are byte-preserved.
- No native work, no acceptance, no full-suite rerun.
- Production code and tests are untouched in this pass.

## Earlier update: scope revision and candidate C2

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
  - Codex's bounded diagnosis found an external kill after about 85 minutes, shortly after Claude's session ended. The previously stated two-hour-limit cause is not supported; the exact mechanism is unproven.
  - The partial buffered log reaches 7%, without a pytest verdict, exit marker or coverage result. See `codex-bounded-test-diagnosis.md`.
  - It is not reported as passed or failed, and it was not rerun for the candidate-only C2 work.
- Exact-head CI (eight shards, collection census, combined coverage) has not run. It needs a push, which waits for review.

## Unresolved boundaries

- **Merge sequencing (consequence, not decided in code).** Adjudication is wired, and prompt v2 tells the GameMaster to propose a mechanic even when it may be unsupported. If this branch merged before C1 is accepted, combat turns and GameMaster-difficulty skill turns in an in-play RPG story would fail visibly as `PIPELINE_ERROR`. AC1 requires that behaviour, but it leaves RPG mode largely unplayable until C1 lands. Merge is separately gated.
- **Armor is conservative.** Any worn non-shield armor refuses the three admitted checks (all Strength (Athletics)). That includes trained wearers, because armor category and the training rule are held on C1-C.
- **Billing for the newly wired pass.** Read-only check, clean: `RPG_ADJUDICATION` has a model tier and settlement line items (`entitlement/policy.py`) and an Anthropic adapter mapping.

- **C1 content and process.** Codex review and Owner acceptance are required, as described in item 1 above.
- **Contributor lists.** These are conservative, code-owned lists of features, traits and feats that bear on ability checks. Codex may want them reviewed as part of C1 rather than accepted as code.
- **State placement still to be built (held work).** Actor-turn/elapsed-time authority, position, timed mastery effects and the per-subject monster/character classification are proposed as an additive 15c table. The 2b document schema would not be bumped. It is recorded here so it can be reviewed before it is built.
