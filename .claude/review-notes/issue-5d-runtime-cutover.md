# CRD Issue 5d — actual runtime cutover record (10 October 2026)

**Status: executed and verified.**
- Migration `0037` and the merged production rule-slice consumer were verified against the local
  runtime stores.
- Codex's independent execution review passed.
- **Completion.** The operation itself declared nothing. Afterwards, on 10 October 2026, the
  Owner declared "The 5c/5d restart is complete.", adopting Codex's completed runtime assessment below.
  - #132 and #137 are unchanged (both already closed).
  - Current status is in the
    [restart opening](../../docs/architecture/issue-5c-5d-clean-restart.md).

## Authority and identity

- **Approval.** After Codex described the next step (actual local migration `0037` and cutover
  verification, followed by the completion assessment), the Owner said: *"Let’s proceed to the next
  step."* That authorizes:
  - this bounded operation;
  - no new semantic acceptance;
  - no issue-state change;
  - no completion declaration.
- **Code.**
  - PR #182 merged `2026-10-10T23:24:27Z` at `47b80c0ba2eccd2d3bcc1985bca771ede4446574`, tree
    `1abd7888424b80a0a1deda64eb308ba8ad5bc48e`, identical to the reviewed head `75b540e`.
  - All 11 required CI jobs passed (run 38079785975): 7,300 passed, 17 skipped, 94.146% coverage.
  - See the [final-cutover note](issue-5d-final-cutover.md).
- **Accepted authority, unchanged and not republished or reactivated:**
  - release `1299484e-c72d-509b-bd8d-d0169ee1f8d2` / `5.2.1-corpus.8781d4e0-a3b`;
  - projection `1f0db408-ee07-5e8d-897d-29838d614c53`;
  - empty override set `521a6242-e6bc-5e76-9564-323c4c0deacb`;
  - oracle `def7caa1625458a40c1f635db153268082cf52d5e25c28f57fd29518e44de58c`.
- **Targets:** `D:\AI\Claude\afterworlds-runtime\afterworlds.db`, and
  `D:\AI\Claude\afterworlds-runtime\.chroma_data`, which was never opened.

## Operation

- **Who and what:** Codex ran the reviewed private harness `runtime_cutover.py` (SHA-256
  `15360b34fddba24573e9de0ff4eabab3ec4ced30dca03b21e6e85994c21df136`) in execute mode. It was bound
  to the reviewed non-mutating prepare rehearsal: same harness, head, tree, interpreter, import
  origins and every target file hash.
- **When:** `2026-10-10T23:40:26.367909Z` to `23:41:51.406272Z`.
- **Result:** native exit 0, verdict `EXECUTED_AND_VERIFIED`.
- **Fail-closed preflight:**
  - exact head and tree, and a clean checkout;
  - the venv interpreter and import origins;
  - no `AFTERWORLDS_*` overrides and no competing process;
  - the oracle and the 123 accepted pins;
  - the protected checkout;
  - target bytes equal to the recorded reference.
- **Backup first:** a stable byte copy of the SQLite file and the whole Chroma directory, in the
  private evidence directory (`runtime-cutover/execute-1/backup/`). Nothing was restored or reset.
- **Pre-state:** read from copies.
  - No drift from the smoke's final state.
  - Schema `0036`, both legacy tables empty, the active projection as accepted, no typed overrides.
  - Integrity ok and foreign-key check empty.
- **Migration:** the production `upgrade_to_head` took `0036` → `0037` in 1.33 s.
- **No app, HTTP server, provider call, story, turn, override authoring, activation or publication.**

## Results

| Check | Result |
|---|---|
| Migration delta | Only `rp_overrides` and `rp_mechanical_entities`, both empty, were removed; `alembic_version` moved `0036` → `0037`. Every other schema object and table row is identical. Integrity ok and FK check empty before and after. Chroma is byte-unchanged |
| Production consumer (`_PerTurnContextBuilder` → `ContextBuilderService` → `get_active_rule_slice`, app wiring, not HTTP) | Record `glossary.blinded`: 1 record, 2 components. Component: 1. Whole package: 1,835 records, 4,040 components. Every slice carries the exact supplied request and the exact four-part binding. UUID and slug slices are equal, and the whole-package authority text is deterministic (SHA-256 `60f185cb…`) |
| Replay and native reads | A fresh reader replays the returned binding: 1,835 records, zero overrides. `rule_slice` gives 1,835 records; the active projection is `1f0db408…`; `glossary.blinded` provenance matches the accepted oracle, with official locator `p. 177` |
| Typed fail-closed refusals | Stale recorded binding gives `STALE`. Retired package, and retired projection inside a recorded binding, give `QuarantinedAuthorityError`. Superseded 3fe and 574 give `ABSENT`, plus `OracleLoadError`. The store was unchanged across the refusals |
| Verification writes | Exactly one `rp_override_set_versions` row (`521a6242…`, `entry_count` 0), one `rp_override_set_scopes` row (that set, the accepted package and its release) and zero entries. This is the normal durable retention of the accepted empty override set (ADR-005d Decision 9), committed by the app wiring and permitted in the reviewed brief because no prior retention existed. No override was authored |
| Citations and vectors | Not re-queried. The 10 October smoke's four citation families and ONNX query stand, because their source, authority paths and Chroma payload are unchanged |

**Codex independent execution review: PASS** (`CODEX-EXECUTION-REVIEW.json`, SHA-256
`8935c9b0339bee4e1ac306afe87125fffec942086ca65505ba1dc36b269eca1a`). It covered:
- the raw pre, migrated and final copies, compared independently: the right tables dropped, other
  rows and schema preserved;
- the backup hashes, all exact;
- the 6 Chroma files, byte-unchanged;
- two supplemental app-wired checks, with zero database table delta: a current recorded binding gives
  `RESOLVED`, and an invalid reference gives `INVALID_REFERENCE`;
- the 123 accepted pins, unchanged;
- the protected checkout: HEAD, status (1,196 entries), index, stashes and settings unchanged;
- no app started, no issue-state change, no completion declared.

**Execution receipts** (private, `runtime-cutover/execute-1/`; hashes verified against the review):

| Receipt | SHA-256 |
|---|---|
| `00-preflight.json` | `d1d11d6d415e73d0d20eb9609f64ab867e42dbc4d80b8f2e5c0cef4666525fb5` |
| `01-backup.json` | `2c7e7f824e0c645f4652287e6ecbbce5c531c44e7897eeef1a684a147b6f94de` |
| `02-pre-state.json` | `833bfc1cbe0820fad7188231c1d3c1386637102da631ce93f2d223d73052764c` |
| `03-migrate.json` | `e2a83b749847551818a9a5e900892eea7c50c0d122dc343a33d078a4f9002cad` |
| `04-migrated-state.json` | `8f1bbcf3d23043f61a21c0bd991601689e526ad34f02acfd9432cefb4d1957d2` |
| `05-verify.json` | `9403eaa230f2ff5e063aa40da7c7b1c1e941064f0d3a216a3ee210b6f6ab376a` |
| `06-final-state.json` | `adf1015baf5d3c16b82b83400f46fcc15f71ef5e735d39bea5c8dce60f6427c6` |
| `99-result.json` | `dd51d637009dbc6184210ff2fcadde443834df17f6ce74c3f21bb6d12478c521` |

## Completion assessment (Codex recommendation; adopted by the Owner's declaration of 10 October 2026, "The 5c/5d restart is complete.")

- **Discharged:**
  - CRD Issue 5c's source and release outcomes;
  - the remaining CRD Issue 5d consumer cutover and legacy retirement, now verified against the actual
    runtime.
- **No identified in-scope blocker remains, and no new Owner Decision is needed.** The recommendation
  is that the Owner declare the restart complete and leave #132 and #137 closed.
- **Documented non-goals, not hidden completion claims:**
  - 2b sheet storage;
  - 15c adapter work;
  - gameplay selector policy;
  - the frozen #129/15b/19b work;
  - fact-specific citation liveness;
  - suppress-all;
  - the uninstalled Awakened Plant;
  - the ADR-018 embedded-only exceptions.

## Architecture Notes

No drift from design principles. The operation applied the merged, reviewed migration and verified
the merged consumer; no semantics, authority or policy changed.
