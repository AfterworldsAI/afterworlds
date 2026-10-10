# CRD Issues 5c/5d — bounded shared publication and activation: preparation

Prepared 10 October 2026 UTC on branch `codex/5c-5d-publication-preparation`, at merged
main `b9ff329a6d3a3fc46a7f835aae658c74d5df731d` (tree `b76316ae…`).

**Status: APPROVED AND EXECUTED LOCALLY on 10 October 2026 UTC; the app has not
been launched.**
- The execution record follows immediately below.
- The sections after it are the preparation exactly as the Owner approved it. They
  are kept as history; the approved bytes are preserved privately as
  `approved-runbook-before-execution.md`, SHA-256 `4c9eb2eb…`.
- Their "pending" and "proposed" wording describes the state before execution.
- **Authority.** The 21 September Owner Decision, CRD Issues 5c/5d,
  ADR-005c (operational reliability) and ADR-005d. This is operational
  preparation, not semantic construction. Nothing accepted changes:
  - oracle `srd-5-2-1-corpus-8781d4e0-a3b.json`, SHA-256 `def7caa1…`;
  - release `1299484e-c72d-509b-bd8d-d0169ee1f8d2` / `5.2.1-corpus.8781d4e0-a3b`;
  - projection `1f0db408-ee07-5e8d-897d-29838d614c53`;
  - 24 batches, 1,835 records, 1,486 recorded resolutions, schema 17.

## Execution record (approved local operation, 10 October 2026 UTC)

**Approval.** Owner, verbatim: "Approved. Create the local stores in
D:\AI\Claude\afterworlds-runtime, publish the accepted 5c release, activate and
verify its 5d projection. Keep the protected checkout untouched and stop before
launching the app." The approval record is `optionB-preflight-1/approval.json`
(`approved_at` `2026-10-10T07:58:12Z`). It names:
- helper `7b634ee3bf6eeccaaec3f5b82ca306fe27b381bd079e1ce86687378436e3a1df`;
- HEAD `b9ff329`;
- the two targets below;
- start state `absent`/`absent`, with directory creation.

**Execution.** Codex ran the reviewed wrapper as the local operator
(`optionB-apply-1/`, `optionB-apply-1.log`), native exit 0, "APPLY COMPLETE".

| Phase (receipt written, UTC) | Result |
|---|---|
| `01-candidate` 07:59:20 | Live `build_source_candidate` identity equals the oracle binding |
| `02-backup` 07:59:20 | Target absence recorded; nothing to back up |
| `03-migrate` 07:59:23 | `D:\AI\Claude\afterworlds-runtime` created; schema `0036` |
| `04-5c` 08:02:11 | `published`, not reused, 162.6 s. Binding equals the oracle on all six coordinates, including `persisted_corpus_digest 3717fa11…` (commit boundary 1) |
| `05-5d` 08:03:33 | `published`, projection `1f0db408-ee07-5e8d-897d-29838d614c53`, zero gate failures, evidence hash `39d4c54a…`, 67.0 s (commit boundary 2, activation included) |
| `06-verify` 08:05:09 | Every required check passed (below) |

`06-verify` was a fresh session, rolled back at the end. It found:
- active `PUBLISHED` `1f0db408-…`;
- the exact four-part binding (package, release, projection, empty override set
  `521a6242-…`) by UUID and by slug;
- a whole-package slice of 1,835 records;
- `glossary.blinded` provenance equal to the oracle, with official locator `p. 177`;
- the four citation families `RESOLVED`;
- 5 production-vector query hits;
- the retired 36b identity quarantined, and 3fe and 574 superseded;
- unrelated tables unchanged.

**Independent review.** `CODEX-LOCAL-EXECUTION-REVIEW.json`, verdict PASS.
- All six receipt hashes are recorded there and rechecked for this note.
- Its inspection of byte copies of the stores, outside SQLAlchemy and Chroma, found:
  - SQLite `integrity_check` ok;
  - one package, release, projection and activation row;
  - 1,835 mechanical records, 24 acceptance batches and 8,583 reference rows;
  - the Chroma `integrity_check` ok, with one collection
    `rules_corpus_1299484ec72d509bbd8dd0169ee1f8d2` (dimension 384) and 11,076
    embeddings.
- Protection checks passed: the original checkout's HEAD, status, index and
  stashes; global and local settings; the existing databases; the 123 immutable
  files; and pristine production paths.

**Not done:** no app launch, and no source, semantic, issue-state, commit or push
change.

**Scope of this record.**
- **Local stores published and activated:**
  - `D:\AI\Claude\afterworlds-runtime\afterworlds.db`;
  - `D:\AI\Claude\afterworlds-runtime\.chroma_data`.
- **No partial publication:** 5c and 5d both committed and were verified.
- **Not claimed:** this does not declare the restart operationally complete, and
  it closes no issue.
- **Not part of this record:** launching the app is a separate authorization,
  only if the Owner requests it; its configuration is below. This record is
  delivered by a documentation-only pull request for Owner review and merge.

## The proposed operation

| | |
|---|---|
| Database | `D:\AI\Claude\afterworlds-runtime\afterworlds.db` (new; the directory `D:\AI\Claude\afterworlds-runtime` is created by the operation) |
| Chroma | `D:\AI\Claude\afterworlds-runtime\.chroma_data` (new) |
| Expected start | Database `absent`, Chroma `absent`, empty target hash set, parent directory absent (`create_parent_directory: true`) |
| Code | Isolated checkout `D:\AI\Claude\quarantine-retirement\afterworlds` at `b9ff329`. Only the reviewed preparation documentation may differ from HEAD; production, migration, configuration and source paths must be pristine |
| Runtime | `D:\AI\Claude\quarantine-retirement\afterworlds\venv\Scripts\python.exe` (Python 3.12.10), chromadb 1.5.9, production ONNX `all-MiniLM-L6-v2` with chromadb's pinned archive hash |
| Helper | `C:\Users\raven\.codex\visualizations\2026\10\09\01a121f3-798d-7fd2-88a4-b8c172155dba\shared-publication-preparation\shared_publication.py`, SHA-256 `7b634ee3bf6eeccaaec3f5b82ca306fe27b381bd079e1ce86687378436e3a1df`. A private wrapper over production seams, not a product CLI |
| Write set | Directory and database created and migrated to `0036`. 5c package and release `1299484e-…`, about 52 MB of SQL. One Chroma collection `rules_corpus_1299484ec72d509bbd8dd0169ee1f8d2` with 11,076 embeddings, about 73 MB. 5d projection `1f0db408-…` and one activation row |

**Why this target.** It keeps runtime state out of the protected original
checkout and needs no exception to that protection.

**What was not chosen, and is kept as evidence:**
- `D:\AI\Claude\afterworlds\afterworlds.db` (schema `0031`): it holds only the
  migration-seeded `retrieval_marker_era_boundary` row and no rules or user data,
  and its `.chroma_data` is absent.
- The old `D:\AI\Claude\.claude\launch.json` is a separate fake-provider
  manual-smoke environment. It stays untouched and is not a target.

## Exact commands (PowerShell)

```
$PY  = 'D:\AI\Claude\quarantine-retirement\afterworlds\venv\Scripts\python.exe'
$E   = 'C:\Users\raven\.codex\visualizations\2026\10\09\01a121f3-798d-7fd2-88a4-b8c172155dba\shared-publication-preparation'
$ARG = @('--repo','D:\AI\Claude\quarantine-retirement\afterworlds',
         '--db','D:\AI\Claude\afterworlds-runtime\afterworlds.db',
         '--chroma','D:\AI\Claude\afterworlds-runtime\.chroma_data')

# 1. Fresh preflight immediately before approval (writes nothing to the target)
& $PY "$E\shared_publication.py" preflight @ARG --run-dir "$E\optionB-preflight-1"

# 2. Owner review: copy optionB-preflight-1\approval-template.json to
#    optionB-preflight-1\approval.json and fill approved_by and approved_at (ISO 8601 UTC).

# 3. Local concurrency check by the executor (Codex): nothing else is writing to
#    D:\AI\Claude\afterworlds-runtime during the run (no other app, script or
#    automation), and no AFTERWORLDS_* variable is set in this shell. There are no
#    deployed consumers to stop; this is first-time provisioning of a local store.

# 4. Apply (only after the Owner approves this exact operation)
& $PY "$E\shared_publication.py" apply --approval "$E\optionB-preflight-1\approval.json" --confirm-no-concurrent-writer @ARG --run-dir "$E\optionB-apply-1"
```

Each run directory must be new. If preflight must be repeated, use
`optionB-preflight-2` and re-approve.

## Phases and commit boundaries

| Phase | What happens | Boundary |
|---|---|---|
| `00-preflight` | **Live checks:** environment overrides absent; Python 3.12, chromadb, model archive hash and a probe embedding; HEAD `b9ff329` with only the reviewed documentation changed and production/migration/config/source paths pristine; oracle digest; official-PDF and pinned-source digests (14 files); output paths confined to the evidence root and not overlapping either target. **Classification:** target SQLite files and any `chroma.sqlite3` are byte-copied with stable hashes and only the copies are opened. An absent or empty Chroma directory is allowed; unknown content, foreign or orphan collections, other packages or releases, and draft or foreign projections or activations stop. An approval template is written **only** when nothing stops. **Reused, not rebuilt:** the source-candidate identity, verified by the dress rehearsal at this HEAD with unchanged inputs | none |
| `01-candidate` | Refuses unless the approval names exactly this helper, checkout, HEAD, changed-document list, Python executable and version, chromadb version and targets; is completed (approver and ISO timestamp); the executor's no-concurrent-writer confirmation is given; and the target hashes still match. Then **builds `build_source_candidate` live** and requires its identity to equal the oracle binding | none |
| `02-backup` | Rechecks hashes and classification against the approval. **For this absent target it records the absence**; there is no prior database to copy. (For an existing store the same phase takes a diagnostic hash-stable copy and a backup-API snapshot with `integrity_check`; that is support for the helper, not a user-migration deliverable.) | none (evidence only) |
| pre-write | Rechecks hashes and classification against the approval **immediately before the first target write**. Then creates `D:\AI\Claude\afterworlds-runtime` (approved by `create_parent_directory`) | first target write |
| `03-migrate` | `upgrade_to_head` → `0036`. For an existing database it asserts unrelated tables are unchanged. Records the post-migration unrelated-table baseline | **non-transactional SQLite DDL** |
| `04-5c` | `finalize_source_release` with a real `PersistentClient` and `resolve_default_embedding_function()`. Internally: persist draft, reindex, read back live Chroma, verify against SQL, digest, gate, then publish or roll back SQL and drop its own collection. A fresh session then asserts all six binding coordinates equal the oracle's | **commit boundary 1** |
| `05-5d` | `committed_inputs_for` → `candidate_from_accepted_inputs` → `identify_projection`, with `1f0db408-…` asserted before any write. Then, in **one session**: `persist_draft` → `record_persisted_state_digest` (flush only) → `publish_from_committed_oracle`. Any outcome other than `PUBLISHED` is explicitly rolled back. No draft is ever committed | **commit boundary 2** (draft, publication and activation, atomically) |
| `06-verify` | Fresh engine and session, rolled back at the end, so no runtime retention row is committed. Required (any miss is a stop): exact active `PUBLISHED` `1f0db408-…`; all four binding coordinates by UUID and by slug `srd-5-2-1-corpus` (package, release, projection, empty override set); a `RESOLVED` whole-package slice of 1,835 records; a `RESOLVED` `glossary.blinded` slice whose record and component span ids equal the committed provenance claims; its bound chunk's locator `page` / `p. 177`, checked against official PDF page 177; the four citation families through `citation_view`; a real-model `diagnostic_query` with hits; retired 36b quarantined and 3fe/574 superseded; unrelated tables equal to the post-migration baseline | none |

## Evidence (private copies only; no shared store touched)

**Inventory** (`store-inventory.json`, Codex). The default
`D:\AI\Claude\afterworlds\afterworlds.db` is at schema `0031` with zero packages
and releases. Its only row is the migration seed. Its `.chroma_data` is absent.

**Migrations.**
- `0031`→`0036` on a copy (`migration-rehearsal.json`): only `alembic_version` and
  `rp_mech_*` changed, plus four new tables, with no row count changes.
- Absent→`0036` (`absent-migrate-check/`): 70 tables, the same single seeded row.
  This is the path this proposal uses.

**Dress rehearsal** (`rehearsal-1/`, exit 0). The publication phases ran on a copy
of the inventory DB plus an absent Chroma directory, with the **production ONNX
model**. It used the first helper revision, retained privately as
`shared_publication-rehearsed.py` (SHA-256 `b7cc7b64…`, the same value the
rehearsal receipts record).

Comparing its 5c and 5d publication functions with the final helper's, the
function bytes differ only in:
- import ordering;
- the error text "own" becoming "its own";
- inlining the identical expected-binding comprehension in 5c;
- renaming the local `expected_outcome` to `expected` in 5d.

Calls, arguments and transaction and commit boundaries are unchanged. The final
helper's other changes are guards and verification.

| Result | Value |
|---|---|
| 5c | `published` in 153 s; binding equals the oracle on all six coordinates, including `persisted_corpus_digest 3717fa11…` |
| 5d | `published` in 68 s with zero gate failures |
| Total | About 5.3 min after preflight |

That rehearsal demonstrates the invocation. It does not rule out every future 5c
success followed by a 5d refusal; that stop state stays explicit below.

**Guard controls with the final helper** (`controls-r2/summary.txt`; all 19
checks pass. `controls/` holds the same set run before the concurrency-flag
rewording, also all passing).

| Control | Result |
|---|---|
| c1 | Strengthened verification passes on the rehearsal store, including probe provenance, the `p. 177` locator and unrelated-table preservation |
| c2 | Preflight of the proposed target: `absent`/`absent`, pins pass; `D:\AI\Claude\afterworlds-runtime` still does not exist afterwards |
| c3 | Foreign package: stop, no template, target unchanged |
| c4 | Unknown Chroma content: stop, no template |
| c5 | Output path overlapping the target, and output outside the evidence root: both refused, nothing created |
| c6 | Uncompleted approval: refused before any write |
| c7 | Wrong target, and missing no-concurrent-writer confirmation: refused before any write |
| c8 | Target drift after approval: refused before any write, drifted bytes untouched |

The first control run is preserved as `controls-attempt1-pin-parse-bug/`. A
status-parsing bug in the helper itself made the pin check refuse the clean
documentation-only tree. It failed closed, and was fixed before the passing run.

**Reused.** Final PR #180 CI run 38028793489 at `4dc9709` (all 11 jobs) on the
identical merge tree.

## Stop conditions (never retried by the helper)

- **Before the first write:**
  - any `AFTERWORLDS_*` override set;
  - Python, chromadb or model mismatch;
  - HEAD, or any production, migration, config or source path, different from the
    pin;
  - oracle or source digest drift;
  - an uncompleted or mismatched approval, or no no-concurrent-writer confirmation;
  - target hashes or classification different from the approval at any of the
    three rechecks;
  - a candidate identity different from the oracle;
  - output-path overlap.
- **During the operation:**
  - a schema other than `0036`, or unrelated data changed by migration;
  - 5c refused, or a committed 5c binding different from the oracle (5d then does
    not run);
  - the accepted candidate not deriving `1f0db408-…`;
  - a projection header in a non-published state;
  - any 5d outcome other than the expected one, including `ABSENT` after the
    internal activation-race re-entry;
  - any verification miss.

## Recovery (no automatic deletes, no downgrade, no live file replacement)

The target is **originally absent**, so there is no old database or Chroma store
to restore. Each failure is handled where it happens.

- **Stop before the first write.** Nothing exists at the target.
- **Failure during migration or a refused 5c.** The created directory holds only
  what this operation wrote; a refused 5c has rolled back SQL and dropped its own
  collection. Stop and report. Returning to the absent start state is a
  deliberate, Owner-approved, offline removal of the operation-created
  `D:\AI\Claude\afterworlds-runtime` directory, never automatic.
- **5c committed, then 5d refused or stopped.**
  - **This is not operational activation.** Mechanical runtime reads answer typed
    `UNPUBLISHED`, and the block and the app-launch hold stay in force.
  - No draft was committed. A new preflight, whose expected state is
    `5c-published` with Chroma `present`, then re-approval and `apply`, re-proves
    5c as verified reuse and reruns 5d.
  - Otherwise, the Owner-approved offline removal above.
  - Never delete 5c rows or the collection piecemeal.
- **Activation committed, verification failed.** There is no supported
  deactivation path. Stop and report, and keep the app-launch hold. The only revert
  is the Owner-approved offline removal of the operation-created directory.
- **Concurrency.** There are no users and no deployed consumers; this is
  first-time provisioning of a local development/runtime store, with no user
  migration or compatibility obligation. The executor still establishes that no
  other app, script or automation writes to the target during the run. The hash
  and classification rechecks detect changes made before the first write, not
  during the run. If concurrent writing is suspected, stop rather than retry.

## App launch: prepared configuration, not part of this approval

No app is launched during preparation or as part of the data-publication
approval. Prepared configuration, for a later, separately authorized launch
after `06-verify` passes, from the same pinned checkout:

```
$env:AFTERWORLDS_DATABASE_URL = "sqlite:///D:/AI/Claude/afterworlds-runtime/afterworlds.db"
$env:AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY = "D:\AI\Claude\afterworlds-runtime\.chroma_data"
# AFTERWORLDS_RETRIEVAL_EMBEDDING_MODEL_ID and AFTERWORLDS_FAKE_PROVIDER stay unset
& 'D:\AI\Claude\quarantine-retirement\afterworlds\venv\Scripts\python.exe' -m uvicorn afterworlds.main:app --app-dir 'D:\AI\Claude\quarantine-retirement\afterworlds\src' --port 8000
```

App startup runs `upgrade_to_head` (a no-op at `0036`) and provisions runtime
rows. Launch from merged main, not the protected checkout's `1388939`.

## Approval request (granted 10 October 2026 UTC; see the execution record)

Approve exactly the operation in "The proposed operation" table:
- its target paths, including creating the directory;
- start state `absent`/`absent`, confirmed by a fresh `optionB-preflight-1`;
- its write set;
- its pins and helper SHA-256;
- the commands above;
- verification, stop conditions and recovery as stated.

Approval covers data publication and activation only, not the app launch.
