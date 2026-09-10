# CRD Issue 5d — `actions-1` repository hygiene checkpoint

**Scope:** repository maintenance only. This checkpoint records the alignment of the
existing checkout `D:\AI\Claude\afterworlds` with the verified `origin/main` baseline
and the disposition of every local-only item. It contains **no** `actions-1` authoring,
discovery, or semantic content, and it accepts nothing.

**Date:** 2026-09-05
**Checkout:** `D:\AI\Claude\afterworlds` (single worktree; no replacement checkout created)
**Issue:** #137 (CRD Issue 5d)

---

## 1. Verified baseline

`git fetch origin --prune` then:

| Field | Value |
|---|---|
| `origin/main` | `b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d` |
| Brief's expected head | `b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d` |
| Result | **exact match — baseline unchanged since Codex's 2026-09-05 verification** |

`origin/main` has not advanced, so no intervening-change reconciliation was required and
no other accepted authority was substituted.

The prune deleted five stale remote-tracking refs whose upstream branches were removed
after their PRs merged (`feature/issue-5d-conditions-1-accepted-authority`,
`feature/issue-5d-hazards-1-schema5-regeneration`,
`feature/issue-5d-representation-schema-{3,4,5}`). Their commits are all contained in
`origin/main`; nothing unmerged was dropped.

---

## 2. Before / after branch and commit state

| | Before | After |
|---|---|---|
| Current branch | `main` | `feature/issue-5d-actions-1` |
| `HEAD` | `319e61c0e9499d9bed68e7f06efd57beb615da90` | `b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d` |
| local `main` | `319e61c…` — 0 ahead / 54 behind `origin/main` | `b5d386ba…` — 0 ahead / 0 behind |
| Tracked modifications | none | none |
| Untracked files | 55 | 56 (this checkpoint) |
| Worktrees | 1 (`D:/AI/Claude/afterworlds`) | 1 (unchanged) |

**Maintenance performed:** `git merge --ff-only origin/main`.

Local `main` was strictly behind with zero divergence and zero tracked modifications, and
none of the 55 untracked paths existed in the `origin/main` tree, so a fast-forward could
neither refuse nor clobber. No `reset --hard`, no stash, no forced checkout, no file
deletion, and no `git gc` / `git prune` was run at any point (see §4 — reflog reachability
is load-bearing for the retained evidence).

The `actions-1` branch was then created directly from the verified SHA:

```
git switch -c feature/issue-5d-actions-1 b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d
```

---

## 3. Verification of the synchronized tree

```
git rev-parse HEAD                     -> b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d
git diff --quiet origin/main           -> exit 0   (tracked tree identical to baseline)
git status --porcelain -uno            -> empty    (no tracked modifications)
```

### Committed accepted oracle

`src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-36b786d8-fa2.json`

| Identity | Expected | Observed | |
|---|---|---|---|
| Git blob | `6e65533f4a3523aba3d60cfc3c274ab22e66b59a` | `6e65533f4a3523aba3d60cfc3c274ab22e66b59a` | OK |
| Content SHA-256 (LF-normalized) | `0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7` | `0925d796a058ff4e64f9a429c9ad73d3c39f1e74dff7e394bc2957c1587e73f7` | OK |
| `oracle_identity()` | `c794bde48a6fbe6c59e5cc901a30f092524fe0ceecdc60b7ba080f11fd356245` | `c794bde48a6fbe6c59e5cc901a30f092524fe0ceecdc60b7ba080f11fd356245` | OK |
| representation schema | `5d-representation-schema-5` | `5d-representation-schema-5` | OK |
| schema hash | `2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40` | `2803840899363988cc2f67e0d9f310d9baffe394d52ca0919d11388bcd7f4c40` | OK |

The content digest was computed from `git cat-file blob HEAD:<path>`, i.e. from the
LF-normalized stored content, not from platform bytes. `.gitattributes` declares
`* text=auto eol=lf` and `*.json text eol=lf`, and the working-tree file contains
**0** CRLF sequences, so the on-disk raw digest coincides with the LF-normalized digest
here. The blob identity, not a platform digest, remains the pin.

`release_binding` (all six fields match the brief's source-binding table):

| Field | Value |
|---|---|
| `package_uuid` | `4458fa10-4a66-5e0e-9ecc-ea37530ad2b4` |
| `release_version` | `5.2.1-corpus.36b786d8-fa2` |
| `authoritative_source_hash` | `8974902d109d6e63672d7c490bde9ccf052410503d9cfa768237154fbc5e3d87` |
| `transform_config_hash` | `77720c2f3b8c9b88363d48050466fb8e3a26f8476b63145d1b5928ff2581ef3e` |
| `bundle_root_hash` | `03353dfb79790aee7260b9ed96055b7296cd6f70e3e6f97d6cbe0a2484279685` |
| `persisted_corpus_digest` | `c1f547962b7d9096986f0b8e75624f9f8803dfc281c16033e1c2250cad5a929b` |

Totals (all match the brief's two-batch prior):

| Collection | Expected | Observed |
|---|---|---|
| records | 22 | 22 |
| spans | 281 | 281 |
| components | 69 | 69 |
| prose bindings | 20 | 20 |
| relationships | 0 | 0 |
| references | 22 | 22 |
| provenance edges | 281 | 281 |
| acceptance records | 281 | 281 |
| obligations | 22 | 22 |

Succession and anchors read back as expected: `acceptance.batches` = `conditions-1`,
`hazards-1`; `acceptance.lifts` = `5d-lift-schema-3-to-4` then `5d-lift-schema-4-to-5`;
`acceptance.schema_anchors` records `conditions-1` under `5d-representation-schema-3`
(proposal `14587d5b…`) and `hazards-1` under `5d-representation-schema-5`
(proposal `f7ce4491…`). Semantic policy `5d-semantic-policy-1` / `e6363968…`.

**The oracle file was read only. It was not modified, and no acceptance was recorded.**

### Toolchain

| Tool | Version |
|---|---|
| `venv` interpreter | Python 3.12.10 (`venv\Scripts\python.exe`, prefix `D:\AI\Claude\afterworlds\venv`) |
| black | 26.3.1 |
| ruff | 0.15.8 |
| mypy | 1.19.1 |
| pytest | 9.0.3 |
| pip-audit | 2.10.0 |
| detect-secrets | 1.5.0 |

`pyvenv.cfg` points at `C:\Users\raven\AppData\Local\Programs\Python\Python312`, which
exists and reports 3.12.10; `import afterworlds` resolves to the checkout's
`src\afterworlds`. No stale environment path required repair.

### detect-secrets baseline

The committed baseline is the deterministic start-of-session reference; it was **not**
regenerated and remains byte-identical to the baseline commit.

| Field | Value |
|---|---|
| Path | `.secrets.baseline` |
| Git blob (`HEAD`) | `474ed2f15e2508d9cc31a0a4ead1b9afcf5f2cca` |
| Content SHA-256 (LF-normalized) | `c95a0cb6555ad95c8ef8f0e7b27db060d65959600f67b2119ff83c98f15b9b9a` |
| Baselined files | 4 |
| Baselined findings | 129 |

Scope note recorded now so later findings are separable. `.pre-commit-config.yaml` runs
`detect-secrets --baseline .secrets.baseline`, and pre-commit passes only the *changed*
files, so the gate is per-change, not whole-tree. Consistent with that, the committed
baseline covers exactly the four CRD Issue 5d/5c mechanical JSON artifacts that carry
hash literals:

```
.claude\review-notes\issue-5d-hazards-1-schema5-REGEN-PROPOSAL.json               21
src\afterworlds\ingestion\mechanical\oracles\srd-5-2-1-corpus-36b786d8-fa2.json   60
tests\ingestion\mechanical\data\bounded_oracle.json                                7
tests\ingestion\mechanical\data\legacy_conditions_1_unanchored_schema3.json       41
```

A diagnostic whole-tracked-tree scan run during hygiene reports high-entropy hits that
are **not** baselined and that pre-exist unchanged at the verified baseline — chiefly
`frontend/package-lock.json` (293 integrity hashes),
`src/afterworlds/ingestion/corpus/srd_table_inventory.json` (671), and
`src/afterworlds/ingestion/corpus/transform_identity.py` (12). These are outside the
per-change gate scope, are untouched by this work, and are recorded here only so that a
later whole-tree scan is not mistaken for new residue. Scanning was not disabled and no
generated artifact was broadly excluded; new `actions-1` artifacts will be scanned and
their findings individually inspected as they appear.

Baseline paths are stored with Windows separators. A hook invocation that supplies
POSIX-separator paths will not match them; the recorded gate invocation therefore uses
the platform paths git reports.

---

## 4. Local-only material and dispositions

### 4.1 Reachability finding (why "leave in place" is the preservation)

Every untracked blob below is absent from the `origin/main` tree. Each is present in the
local object store and reachable **only through reflog entries of branches that have
since been deleted or rewound** — none is reachable from any current branch,
remote-tracking ref, or stash. The object store is therefore *not* a durable backup for
this material: reflog expiry followed by `gc` would drop it.

Consequences, applied throughout this session:

* the on-disk copies at their original paths are the preservation, so nothing was
  deleted, moved, renamed, or overwritten;
* no `git gc`, `git prune`, or `git reflog expire` was run, and none should be run while
  this material is wanted;
* the path + size + blob table below is the byte-identity record, so any later relocation
  can be proved faithful.

### 4.2 Disposition table

Classification key — **RE** retained review evidence (superseded CRD Issue 5d iterations,
kept as historical proof of the review path); **LT** local tooling; **LR** local runtime
output.

| # | Path | Bytes | Git blob | Class | Disposition |
|---|---|---|---|---|---|
| 1 | `.claude/pr_body_issue_5d_hazards_1.md` | 30588 | `ff9ebf82870c0c939e9792186254f26229f1fcf5` | RE | keep in place, untracked |
| 2 | `.claude/review-notes/accept-run/conditions-1-ACCEPT-rederived-PROPOSAL.json` | 166038 | `742b635364ef04e84d544a72887ab65cfb8fdf9e` | RE | keep in place, untracked |
| 3 | `.claude/review-notes/accept-run/conditions-1-ACCEPT-rederived-audit.json` | 85639 | `5d0315e2bf219080947d1d8c476d9487bcaae5ec` | RE | keep in place, untracked |
| 4 | `.claude/review-notes/issue-5c-operational-reliability-amendment-DRAFT.md` | 17759 | `b7f1e9729ebc0040021bf9d30b29d2541bb43792` | RE | keep in place, untracked |
| 5 | `.claude/review-notes/issue-5d-actions-1-DISCOVERY-KICKOFF.md` | 17258 | `37b28741ac068c870c26ffb93646af8ba98287ed` | RE | keep in place, untracked |
| 6 | `.claude/review-notes/issue-5d-authoring-schema-checkpoint-DRAFT.md` | 47680 | `cfeb489cb38298a6682c86f0a4efabeca1858978` | RE | keep in place, untracked |
| 7 | `.claude/review-notes/issue-5d-batch-actions-1-PROPOSAL.json` | 96613 | `c0a1c04d7371196c2a9c28d6a661fadeed43f2c9` | RE | keep in place, untracked; **not** generator input (see §5) |
| 8 | `.claude/review-notes/issue-5d-batch-actions-1-audit.json` | 43199 | `f3aa37da57a3dfa9a0e545d697c22d5631f3a02d` | RE | keep in place, untracked; **not** generator input |
| 9 | `.claude/review-notes/issue-5d-batch-actions-1-generator.py` | 27550 | `a063b4c0df79065e36a987e0fc60479c8db2a4f2` | RE | keep in place, untracked; **not** generator input |
| 10 | `.claude/review-notes/issue-5d-batch-conditions-1-PROPOSAL.json` | 144197 | `83c28c633e8bbd41e0c7674fb42f6b1e3c4eaaf5` | RE | keep in place, untracked |
| 11 | `.claude/review-notes/issue-5d-batch-conditions-1-audit.json` | 52171 | `688d1d1a150ec58b8b45d17567f21c24a1d2ca18` | RE | keep in place, untracked |
| 12 | `.claude/review-notes/issue-5d-batch-conditions-1-generator.py` | 27800 | `3f79d9db5125d51f4d276487a9694441eae7429b` | RE | keep in place, untracked |
| 13 | `.claude/review-notes/issue-5d-batch-conditions-1-proposal-DRAFT.md` | 38381 | `34ec165ec8c4ae966d4d55d1fb70e32b38181abf` | RE | keep in place, untracked |
| 14 | `.claude/review-notes/issue-5d-batch-conditions-1-schema2-PROPOSAL.json` | 162381 | `bd65e41bd6a5d49d839bf6d535d0cc620c2acbce` | RE | keep in place, untracked; **byte-identical to #22** |
| 15 | `.claude/review-notes/issue-5d-batch-conditions-1-schema2-audit.json` | 55067 | `363fedbb0991d2c9b0c96343c82dd9718db1a061` | RE | keep in place, untracked |
| 16 | `.claude/review-notes/issue-5d-batch-conditions-1-schema2-generator.py` | 42307 | `f586fc4245663d85d84fe4fc81d0b23ff0a78b7c` | RE | keep in place, untracked |
| 17 | `.claude/review-notes/issue-5d-batch-hazards-1-PROPOSAL.json` | 40591 | `644ae30d94194d0b8209e141c706b5e9f1734377` | RE | keep in place, untracked |
| 18 | `.claude/review-notes/issue-5d-batch-hazards-1-audit.json` | 18322 | `1572d9040f6cb16af5fe857e028aca4bdfb9b596` | RE | keep in place, untracked |
| 19 | `.claude/review-notes/issue-5d-batch-hazards-1-generator.py` | 22129 | `8315df252d21b982a851b3e91aeb61a71ea3a67a` | RE | keep in place, untracked |
| 20 | `.claude/review-notes/issue-5d-conditions-1-ACCEPT-generator.py` | 109022 | `a818457f5a59bef8e6e3b4df92abb1e5b888c342` | RE | keep in place, untracked |
| 21 | `.claude/review-notes/issue-5d-conditions-1-residue-schema-decision-CHECKPOINT.md` | 44100 | `b1dd4ab98798c08036e6ea989c5d485bfad11a01` | RE | keep in place, untracked |
| 22 | `.claude/review-notes/issue-5d-conditions-1-schema2-REGEN-PROPOSAL.json` | 162381 | `bd65e41bd6a5d49d839bf6d535d0cc620c2acbce` | RE | keep in place, untracked; **byte-identical to #14** |
| 23 | `.claude/review-notes/issue-5d-conditions-1-schema2-REGEN-audit.json` | 67198 | `8430c0a1155419be05d9d638aac80b4783900f52` | RE | keep in place, untracked |
| 24 | `.claude/review-notes/issue-5d-conditions-1-schema2-REGEN-generator.py` | 53684 | `dc61361d704e62f22a741fcb071dd122da4b0946` | RE | keep in place, untracked |
| 25 | `.claude/review-notes/issue-5d-conditions-1-schema3-REGEN-CHECKPOINT.md` | 12672 | `b751c5485f80c1865e1c7cc4b1f351b63e9a5d09` | RE | keep in place, untracked |
| 26 | `.claude/review-notes/issue-5d-conditions-1-schema3-REGEN-PROPOSAL.json` | 164890 | `97bbc0269ee618d317f0531a79e2c8d4a90f61b2` | RE | keep in place, untracked |
| 27 | `.claude/review-notes/issue-5d-conditions-1-schema3-REGEN-audit.json` | 75160 | `aae10cbb3ff846d2b6a98ca2e66ef69afd87ec1b` | RE | keep in place, untracked |
| 28 | `.claude/review-notes/issue-5d-conditions-1-schema3-REGEN-generator.py` | 80714 | `d16e41f285fdeaf32c7bc65392ca0c1bf607c613` | RE | keep in place, untracked |
| 29 | `.claude/review-notes/issue-5d-conditions-1-schema3-REMEDIATION-CHECKPOINT.md` | 10182 | `671cb145f8d325d02de2a4d34cd8b86b5122358b` | RE | keep in place, untracked |
| 30 | `.claude/review-notes/issue-5d-conditions-1-schema3-REMEDIATION-PROPOSAL.json` | 166038 | `742b635364ef04e84d544a72887ab65cfb8fdf9e` | RE | keep in place, untracked; **byte-identical to #2** |
| 31 | `.claude/review-notes/issue-5d-conditions-1-schema3-REMEDIATION-audit.json` | 85597 | `ed2f9f5b094dab9851d0d2dabc426a28917b2ba8` | RE | keep in place, untracked |
| 32 | `.claude/review-notes/issue-5d-conditions-1-schema3-REMEDIATION-generator.py` | 94982 | `485bc7c03f174ecdeaac1b045328216c2d024c2e` | RE | keep in place, untracked |
| 33 | `.claude/review-notes/issue-5d-conditions-zero-path-CHECKPOINT.md` | 26642 | `80433a723cd3e8c6d5a1a7a99b58f1487f0ca488` | RE | keep in place, untracked |
| 34 | `.claude/review-notes/issue-5d-consolidated-schema-closure-CHECKPOINT.md` | 38080 | `cd076b769f5554465c9758edb08c250385ec48a2` | RE | keep in place, untracked |
| 35 | `.claude/review-notes/issue-5d-hazards-1-obligation-LEDGER.md` | 18499 | `7efdbd4f03a6f1745d79a8d452f1bab99c24480c` | RE | keep in place, untracked |
| 36 | `.claude/review-notes/issue-5d-hazards-1-schema-closure-CHECKPOINT.md` | 23082 | `115463a91be1e1450f4b926264f2333df524addc` | RE | keep in place, untracked |
| 37 | `.claude/review-notes/issue-5d-hazards-1-schema3-REGEN-PROPOSAL.json` | 63714 | `c24b83cf2f40e72a1cd793add78d2de5d0ae0193` | RE | keep in place, untracked |
| 38 | `.claude/review-notes/issue-5d-hazards-1-schema3-REGEN-audit.json` | 24713 | `73f91c6498209b056fb8279e22352644de939272` | RE | keep in place, untracked |
| 39 | `.claude/review-notes/issue-5d-hazards-1-schema3-REGEN-generator.py` | 27930 | `b0b04837ebe37fcd2e641ff859e20d4700fdddb6` | RE | keep in place, untracked |
| 40 | `.claude/review-notes/issue-5d-hazards-1-schema4-REGEN-CHECKPOINT.md` | 22027 | `bba214722531eb94a8059ad24e060b4d5b1e060c` | RE | keep in place, untracked |
| 41 | `.claude/review-notes/issue-5d-hazards-1-schema4-REGEN-PROPOSAL.json` | 86184 | `028f9078c2aed9fb876c37d988d97515e02c6f87` | RE | keep in place, untracked |
| 42 | `.claude/review-notes/issue-5d-hazards-1-schema4-REGEN-audit.json` | 44878 | `d4731e2e30b47f1aab9e1e711014fef3166e07fd` | RE | keep in place, untracked |
| 43 | `.claude/review-notes/issue-5d-hazards-1-schema4-REGEN-generator.py` | 73859 | `278b211b26a09a2e215b862a6bdeeea59c57ed92` | RE | keep in place, untracked |
| 44 | `.claude/review-notes/issue-5d-hazards-1-sibling-AUDIT.md` | 15634 | `660c112e85d53ed6172a594e707bc0d85abc42bf` | RE | keep in place, untracked |
| 45 | `.claude/review-notes/issue-5d-representation-schema-3-CONSOLIDATED-CHECKPOINT.md` | 61962 | `c86d305b07141a6de2cacf02c46f321101d5ae1a` | RE | keep in place, untracked |
| 46 | `.claude/review-notes/issue-5d-representation-schema-3-transport-authority-CHECKPOINT.md` | 35836 | `d9030c5f35bd2c286e688ce89e51102ce4ae4596` | RE | keep in place, untracked |
| 47 | `.claude/review-notes/issue-5d-schema-2-consolidated-decision-CHECKPOINT.md` | 39708 | `1c9ced93e8b54f72b4840c0d8a5e200715d483b1` | RE | keep in place, untracked |
| 48 | `.claude/review-notes/issue-5d-schema-2-crossbatch-matrix.py` | 9179 | `950b456f67c2fc9201f396e50828f43b4c55ba9c` | RE | keep in place, untracked |
| 49 | `.claude/review-notes/issue-5d-schema-2-implementation-manifest-ADDENDUM.md` | 27664 | `36805ba64ab847e7f0ca86b2228747af2d098ace` | RE | keep in place, untracked |
| 50 | `.claude/review-notes/issue-5d-schema-3-fact-scoped-applicability-CHECKPOINT.md` | 18323 | `5a84d161a0325c2f21a00d3fae8ebafcf65ed566` | RE | keep in place, untracked |
| 51 | `.claude/review-notes/issue-5d-schema-closure-threebatch-matrix.py` | 11936 | `7c971a4191b9020c62ea1714ac71f62110f0fd16` | RE | keep in place, untracked |
| 52 | `.claude/review-notes/issue-5d-zero-path-corrected-matrix.py` | 12716 | `e1b11f4b650b57b63eabe5f8d4f62e783a4787e1` | RE | keep in place, untracked |
| 53 | `.claude/statusline-command.sh` | 2492 | `926bdd2efb47e2642750070e8d641a8a0676d6fc` | LT | keep in place, untracked; unreferenced by `.claude/settings.json` or `settings.local.json`. Orphaned developer convenience — not deleted, not committed |
| 54 | `tmp/pdfs/actions-1-source-review.png` | 1019514 | `7e960d892584a533cd6c805ec8c8b34e957fc02f` | LR | keep in place, untracked. Rendered page image from an earlier `actions-1` source review. **Not** added to `.gitignore` (that would hide drift); this session's own scratch goes to the session scratchpad instead |

Three byte-identity duplicate relations are recorded above (#14 = #22, #2 = #30). No
unique blob is at risk from those duplicates.

### 4.3 Ignored local state

Inspected, unchanged, and deliberately not committed: `.claude/settings.local.json`
(contains only `{"outputStyle": "Concise"}` — no credentials), `.local-tools/aw-graphify.ps1`,
`venv/`, `frontend/node_modules/`, `frontend/dist/`, the `__pycache__` / `.mypy_cache` /
`.pytest_cache` / `.ruff_cache` trees, `.coverage`, `afterworlds.db`, and the
`_manual_smoke_r3.*` scratch database and Chroma directory. `.claude/worktrees/` is an
empty directory. No credential material was read or reproduced. No new ignore rules were
added.

### 4.4 Retained unmerged refs (untouched)

Left exactly as found; recorded so their disposition is explicit rather than assumed
disposable. None was pruned, rebased, or merged.

| Branch | Tip | Commits ahead of baseline | Upstream |
|---|---|---|---|
| `feature/issue-13-entitlement` | `c8e378c` | 1 | gone |
| `feature/issue-15b-structured-roll-lifecycle` | `d8233a4` | 21 | `origin/feature/issue-15b-structured-roll-lifecycle` (live) |
| `feature/issue-5d-publication-gate` | `b35386c` | 10 | gone |
| `fix/issue-5c-recorded-evidence-schema` | `31be484` | 14 | gone |
| `fix/issue-5c-release-proof-clean` | `5a6b6f7` | 13 | gone |
| `test/auto-fix-loop-round-2` | `410bdee` | 3 | gone |
| `test/auto-fix-loop-round-3` | `f550e35` | 1 | gone |
| `test/auto-fix-loop-round-4` | `7d03d40` | 1 | gone |
| `test/auto-fix-loop-round-5` | `dd1cf6f` | 1 | gone |
| `test/codex-autofix-loop` | `8e7ea1c` | 1 | gone |

Branches whose commits are fully contained in the verified baseline and which are
therefore merged, not unique: `feature/issue-5d-conditions-1-accepted-authority`,
`feature/issue-5d-hazards-1-schema4-regen`,
`feature/issue-5d-hazards-1-schema5-regeneration`,
`feature/issue-5d-representation-schema-{3,4,5}`, `main`.

### 4.5 Pre-existing stashes (untouched)

Four stashes pre-date this session. They were **not** created by this hygiene pass, are
**not** used as a reconciliation mechanism, and were not applied, dropped, or inspected
beyond their subjects.

| Ref | Commit | Subject |
|---|---|---|
| `stash@{0}` | `821f6021` | On `feature/issue-5d-conditions-schema-closure`: hygiene-pass pre-existing uncommitted fixes (`.claude-pr/CLAUDE.md` deletion + agent frontmatter dash fix) |
| `stash@{1}` | `b39a7d16` | On `feature/issue-60-rp-logical-key-constraints`: CLAUDE.md lessons |
| `stash@{2}` | `09b4cfa1` | WIP on `chore/decommission-auto-fix-loop` |
| `stash@{3}` | `8a5845fb` | On `feature/issue-3-sqlite-persistence`: temp CLAUDE.md edits |

---

## 5. Constraints carried forward into `actions-1`

* Nothing in §4 is generator input. In particular, `issue-5d-batch-actions-1-*` (#7–#9)
  is a historical August artifact predating schema 5; its semantic payload is **not**
  reused. `actions-1` spans are cut from the bound source at run time.
* `conditions-1` and `hazards-1` accepted content is not reopened, regenerated, or altered.
* No `git gc` / `git prune` / `git reflog expire`, for the reason in §4.1.
* Discovery artifacts, when they exist, are authored fresh under `.claude/review-notes/`
  and kept distinct from this maintenance evidence.

---

## 6. Outcome

Hygiene is **complete** with no unresolved risk to unique work and no Owner question
raised. Every routine action taken was reversible; nothing was deleted, and no accepted
authority was rewritten. The checkout's tracked tree is byte-identical to the verified
`origin/main` baseline `b5d386ba5575a6482bb0eca3d6d38a2ec7e8fc5d`, the committed oracle
carries the expected identities and totals, the Python 3.12 toolchain runs, the
`detect-secrets` baseline is established and unmodified, and all 54 local-only items plus
10 retained branches and 4 stashes have explicit dispositions.

`actions-1` discovery proceeds on `feature/issue-5d-actions-1` from that baseline.
