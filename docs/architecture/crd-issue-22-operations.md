# CRD Issue 22 — Operations, Support and Data Lifecycle: Operations Record and Runbook

**Governs:** [CRD Issue 22 #206](https://github.com/AfterworldsAI/afterworlds/issues/206) revision 7 and its
accepted companions, exact copies in [`crd-issue-22-governing/`](crd-issue-22-governing/README.md):

| Contract | Revision | SHA-256 |
|---|---|---|
| Governing issue (`GITHUB-ISSUE-206-BODY.md`) | 7 | `5a38f82300739f4e030f253ba758aa4a9517e2c03fccb18865404b8840d19b66` |
| Lifecycle ADR amendments (`GITHUB-CRD22-ADR-CONTRACT.md`) | 1 | `eb7d79c7b2f49735996a54d2b9fa2e3b892b95411da933a3e103db6aa5237774` |
| Field/store retention matrix (`GITHUB-CRD22-RETENTION-CONTRACT.md`) | 1 | `c17dfb5ba51c22220f13de582f9ae177b741c58b6a48adb8e8416bdf87800e43` |
| Package and gate contract (`GITHUB-CRD22-PACKAGE-GATE-CONTRACT.md`) | 1 | `56fe900b70c1a289df171d93abcac805244d09a69d2efa371fba18b79c0acaf1` |
| Remote identity/storage prerequisite (`GITHUB-ISSUE-205-BODY.md`) | 1 | `990dae1f7b67bc02c6c738f736bae2f3334b670e273a9dd79adf9d8c106bdb0e` |

**Built on:** prerequisite #205 as merged in PR #207 (`7e72bb1e`), ADR-021 and
[`remote-identity-and-storage.md`](remote-identity-and-storage.md). Engineering selections:
[ADR-022](../decisions/adr-022-operations-support-data-lifecycle.md).

Nothing here authorizes deployment, real-data migration, remote activation, live administration or public
launch. The approved durations are service commitments, not a statutory compliance claim.

## 1. Recorded decisions and scope

| Decision | Recorded effect |
|---|---|
| D1 deployment/admin | Hosted subscriptions run remotely; BYOK users need accounts for Cloud Services only. The Owner is the sole initial full administrator, provisioned only by `python -m afterworlds.remote.bootstrap` (#205). Staff work in a separate staff session (`aw_staff_session`); an ordinary session — the Owner's included — has no staff authority. |
| D2 scope | Story **and** account-wide export/deletion are delivered, remote and local. |
| D3 authority | Administrator actions run through owning services: credit adjustment (entitlement owner), session revocation (#205 identity owner), data-request review/approval/execution/rejection/finalization, anomaly investigation notes, retention expiry. |
| D4 schedule and markets | §5 table. Business location Reno, Nevada, US; initial markets US, Canada, Mexico. Australia, New Zealand, the UK and the EU require a fresh applicability review before entry; nothing here approves them. |

**Administrative primitives not provided (owner recorded):** hosted plan activation/deactivation, Cloud
Services activation/lapse, BYOK licence grant, subscription cancellation, refunds, chargebacks and trial
operations belong to CRD Issue 23's commercial contracts (with CRD Issue 13 as entitlement owner); the
console offers no control that claims to perform them.

## 2. Authority and safe lookup

- Remote: `enforce_access` (#205) resolves the actor from the server session; `/api/admin/*` needs a
  staff session revalidated against the active binding; targets are path parameters. Requester routes
  (`/api/data-requests/*`) bind the subject to the authenticated account — another account's request or
  Story is the same `404` as a missing one. Local: the single local owner; no sign-in, no `/api/admin`.
- Lookup (`GET /api/admin/accounts/{id}`) reads the identity and entitlement owners only:
  `entitlement_state` (`absent` ≠ zero), plan, exact four-place included/top-up/total credits (negatives
  verbatim), hosted availability and reason, Cloud Services status and expiry, BYOK licence state, local
  readiness `unavailable_remotely` (never inferred), `expected_conditions` (negative balance, exhausted,
  inactive hosted, lapsed Cloud Services — not anomalies) and a replay check. Nothing is activated,
  repaired, probed or contacted.

## 3. Ordered history and remediation

- Entitlement history (`GET .../entitlement-history?after_sequence=&limit=`) pages strictly after a
  `global_sequence` cursor, ascending; `total_events` states coverage; `created_at` is display only. Each
  item shows allowlisted typed fields; free-text `detail` is never shown (`has_detail`). Unsupported
  versions and replay/projection mismatches are reported (`replay`), never rebuilt.
- Support stream (`ops_support_events`) has its own `event_order`; it correlates with the ledger only by
  `source_entitlement_event_id` and `idempotency_ref`. It is provenance, not a ledger.
- **Credit adjustment:** preview (`.../credit-adjustments/preview`) shows target, signed deltas, current and
  resulting balances, the stale token `last_entitlement_event_id` and any owner refusal (never-activated
  hosted access). Submit (`.../credit-adjustments`) needs a client-minted `operation_id` for the logical
  action, a 1–280 character reason (control characters and credential-shaped text refused) and the stale
  token. Order: staff revalidated → `requested` event committed (audit failure ⇒ no effect) → stale check →
  `receive_entitlement_event(MANUAL_CREDIT_ADJUSTMENT, adjusted_by=<staff principal>,
  idempotency_key="crd22-support-adjustment:<operation_id>")` → `committed` event with the entitlement
  `event_id`. Deltas with more than four decimals are refused, not rounded. Same `operation_id` + same
  payload ⇒ the same result, applied once; different target/payload/reason ⇒ `409 operation_conflict`.
  Stale ⇒ `409 operation_stale`; never-activated ⇒ `409 operation_precondition_failed`; owner
  concurrency exhaustion ⇒ `503`; a lost response or outcome write ⇒ `503 operation_outcome_unknown`.
  `GET /api/admin/support-operations/{id}` is the status read: it finds the effect by its idempotency key
  and appends the missing outcome. The console never retries automatically.

## 4. Data-request lifecycle

States: `requested` (deletion awaiting the requester's explicit confirmation) → `awaiting_authorization`
(exports start here) → `approved` → `in_progress` → `completed` | `failed`; `rejected` from the first three.
Each transition is an append-only event with `revision` (stale/invalid ⇒ `409`), trusted actor,
`attempt_id` and timestamps. A retry or a resume after restart is a new attempt; failures stay in history.
Remote requests are approved and executed by the Owner administrator (two recorded steps by the same
person allowed); a local owner executes their own (`POST /api/data-requests/{id}/execute`, recorded as
approve then attempt). A duplicate open request for the same subject/kind/scope/Story is refused with the
existing ID. No route sets `completed`: only an executor's verified result does.

**Clocks:** export service clock = verification (the authenticated request, `verified_at`); deletion clock =
explicit scope confirmation (`confirmed_at`, against the displayed `scope_revision`, plus password
re-authentication for a remote account). `export_deadline_at`, `live_deadline_at`, `backup_deadline_at` are
fixed at those triggers; approval waits, retries, restarts and attempts never move them. `overdue` lists
missed deadlines; a completed request keeps `missed_deadlines` (and its receipt `deadlines.*_met`), so a late
completion is never relabelled on time.

**Export:** one read transaction; only player-visible projections (transcript, visible state, setup view);
ZIP of JSON + Markdown with a versioned `manifest.json` (scope, subject, policy version, snapshot boundary
per Story, per-class/per-Story counts, included classes, explicit exclusions, reading note — no import/restore
path). Account exports add the account view (contact address, the only profile field collected), the own
ledger (operator shown as "administrator") and own requests/support actions. Artifacts live in the export
directory (`AFTERWORLDS_EXPORT_DIR`, default `<content db>.exports`, never inside a store, backup or the
public root, not copied by captures), inventoried before any file effect, downloaded only by the
authenticated owner (`Cache-Control: no-store`). Owned-content export needs no credits or Cloud Services.

**Deletion executor** (`operations/deletion.py`), per attempt, each step recorded as a phase event:
`inventory` (durable pre-detachment IDs: Stories — for an account every Story it ever owned, retired
mappings included — Arcs, Chapters, Nodes, Turns via links **and** Turn IDs referenced from Story-scoped
rows, so `SET NULL` orphans are covered) → `fence` (remote: `record_suppression_fenced` with the
**confirmation** time as boundary; local: per-Story turn locks) → `vector_logical` (ADR-018 D11 delete +
count-zero per Story, before any mapping is removed; an unavailable read fails) → `sql_content` (registered
owning-store disposal in FK-safe order through the guarded lifecycle path, then an independent sweep of
every `story_id` table, inventoried Turns/Turn-keyed rows and Arc/Chapter/Node IDs, and `PRAGMA
foreign_key_check`) → `identity` (remote account: the identity owner closes the account, revokes and deletes
sessions and verification operations, removes the principal's address and verifier, keeps the
`hosted_accounts` tombstone; the administrator's own account is refused) → `artifacts` → `rights_evidence`,
`commercial` (remote account) → `physical_compaction` → `backups`. Story deletion never closes the account or
touches its ledger. This is terminal disposal, not gameplay cancellation, rewind, reroll, refund or credit
reversal (15b-33 stays open for continuing Stories).

## 5. Approved schedule (D4) as implemented

| Record or operation | Period / end condition | Trigger | Implementation |
|---|---|---|---|
| Export production | within 7 calendar days | `verified_at` | `export_deadline_at`; `overdue` |
| Hosted export artifact | 7 days from availability | `available_at` | `sweep` removes file, revokes download (`expired`) |
| Failed/partial staging | 24 hours | artifact creation | partial file removed at once on failure; `sweep` at 24 h |
| Live Story/account data | within 7 calendar days | `confirmed_at` | `live_deadline_at`; logical + physical phases |
| Affected backups | 21-day rolling life from original capture; all disposed by 30 days | capture / `confirmed_at` | #205 inventory; `backups` phase; final completion gate; overdue ⇒ failure |
| Admin/request receipts | 24 calendar months after closure | request `closed_at`; support terminal outcome; audit `recorded_at`; investigated anomaly closure | `sweep`; open/uncertain records never expire |
| Closed-account entitlement history | active + 24 calendar months after closure | `hosted_accounts.closed_at` | `expire_subject_history` (whole subject, guarded), `ops_entitlement_expiries` register |
| Content-free routine logs | 30 days | recording | `provider_refusal_log` rows; never-investigated anomaly telemetry |
| Deletion suppression | until every affected backup is disposed and the horizons have passed; annual review | — | `maintenance release-suppression` (verified only); `reviews` |
| BYOK-rights evidence | while enforceable; annual review | — | `ops_rights_evidence`; `reviews` |

Boundary arithmetic (`operations/policy.py`): recorded UTC instants; N calendar days = +N×24 h; a deadline is
met at any instant up to and including it, overdue strictly after; an expiry takes effect at its instant;
calendar months clamp to the month end (31 Jan + 1 = 28/29 Feb; 29 Feb + 24 = 28 Feb), time of day kept.
Policy version: `crd22-matrix-r1` (stored on every record); a later policy is a new version, earlier records
keep theirs.

## 6. Retained-record allowlists (matrix → actual stores)

Operations store = the **control store** remotely (outside the content snapshot), the local content store
locally. A remote content store carries empty copies of the same tables.

| Matrix record | Table | Fields (all allowlisted; "Extra" = recorded addition) |
|---|---|---|
| Support action event | `ops_support_events` (append-only) | `schema_version, operation_id, event_id, event_order, subject_ref, actor_ref, action_code, target_type, target_ref, reason_code, reason_text, hosted_credit_delta, top_up_credit_delta, requested_at, recorded_at, outcome_code, source_entitlement_event_id, idempotency_ref, policy_version, supersedes_event_id` |
| Data request/transition | `ops_data_requests` (header) + `ops_data_request_events` (append-only) | header: `request_id, schema_version, kind, environment, scope, subject_ref, story_refs, requester_ref, requested_at, verified_at, policy_version, export_deadline_at`; events: `event_order, event_id, schema_version, request_id, revision, state, attempt_id, actor_ref, authorization_code, confirmation_ref, scope_revision, reason_code, reason_text, recorded_at, confirmed_at, approved_at, closed_at, live_deadline_at, backup_deadline_at, policy_version, supersedes_event_id` |
| Protected inventory pointer | `ops_request_inventory` (Extra) | `request_id, resource_class, resource_id, recorded_at` — opaque IDs only; owner: lifecycle; purpose: pre-detachment scope and restore re-application; readers O/R; ends with its request record |
| Export manifest / deletion receipt | `ops_receipts` (append-only) + `ops_phase_events` (append-only) + `ops_export_artifacts` | receipts: `receipt_id, request_id, receipt_kind, schema_version, attempt_id, body_json, created_at, policy_version` (body: IDs, counts, classes, exclusion/retained codes, times — never content); phases: `event_order, event_id, request_id, attempt_id, phase_code, outcome_code, counts_json, detail_code, observed_at, deadline_at`; artifacts: `artifact_id, request_id, attempt_id, storage_locator, status, created_at, available_at, expires_at, removed_at, size_bytes` |
| Post-closure receipt access | `ops_receipt_credentials` (Extra) | `request_id, credential_verifier, issued_at` — SHA-256 of a 256-bit credential shown once at remote account-deletion confirmation; ends with the request record |
| Deletion suppression | #205 `deletion_suppressions` | unchanged; recorded only via `record_suppression_fenced` |
| Anomaly/investigation event | `ops_anomaly_events` (append-only) | `event_order, event_id, schema_version, anomaly_id, subject_ref, source_kind, source_id, observed_at, safe_signal_code, investigation_state, actor_ref, note_code, note_text, supersedes_event_id` (`observed_at` of a note is its own time) |
| Entitlement expiry register | `ops_entitlement_expiries` (Extra) | `subject_ref, closed_at, expired_at, event_count, policy_version` — owner: entitlement; purpose: re-expire on restore; ends with the suppression/rights records that need it |
| Perpetual BYOK-rights evidence | `ops_rights_evidence` | `rights_id, subject_ref` (opaque link), `right_kind, status, purchased_at, external_source, external_reference_id, source_event_id, recorded_at, annual_review_at` |
| Lifecycle grant | `lifecycle_disposal_grants` (Extra, both chains) | `table_name, row_key, operation_ref` — exists only inside a disposing transaction |
| Entitlement events | `entitlement_event` (unchanged typed v1 rows) | the matrix's per-kind allowlist; manual `reason` bounded at creation by §3. Hosted/Cloud deactivation `detail` is free text produced only by CRD Issue 13/23 paths (no current producer); it is never shown or exported (`has_detail`). |
| Closed account tombstone | `hosted_accounts` row (#205) | `account_id, status=closed, closed_at, updated_at, policy_version`; principal, sessions and verification operations deleted |

Every append-only table refuses UPDATE always and DELETE unless `operations.lifecycle.dispose_rows` granted
that row in the same transaction; the guarded triggers replace the plain ones on `entitlement_event`,
`provider_refusal_log`, `rpg_roll_audit`, `action_resolution_events` and `identity_audit_events`
(migrations `0046`, `c0002`). Removed classes and retained categories per scope are listed in each preview
and receipt (`operations/deletion.py`).

## 7. Store, backup and physical-copy inventory

| Copy | Disposition |
|---|---|
| Content SQLite rows | registered disposal + sweep (`sql_content`); `secure_delete` on the deleting connection |
| Content SQLite free pages, WAL | offline `compact`: `wal_checkpoint(TRUNCATE)` + `VACUUM` |
| Chroma `story_memory` rows | per-Story delete + count-zero (`vector_logical`) |
| Chroma SQLite free pages, operation log, HNSW segment files | offline `compact`: export remaining records, rebuild in a **fresh subprocess** (Chroma's HNSW writer was observed persisting freed-memory bytes into a new segment), swap contents keeping marker and lock |
| Shared Rules corpus | copied unchanged by the rebuild; never deleted |
| Export artifacts | removed at deletion, 7-day expiry or 24-hour staging cleanup; never captured in backups |
| Backups (#205 inventory) | 21-day life from original capture (copies/restores keep it); deletion final only when every affected backup is disposed (`backup_disposition`) ≤ 30 days from confirmation |
| Captures | refused while any deletion's physical compaction is pending (`storage_cli capture`) |
| Compaction staging (`.<vector>.compact-new/`) and export (`.<vector>.compact-export.json`) | plain copies of every remaining record, owner-only, beside the live vector store; removed when the swap completes. While either exists the app, `storage_cli` and every maintenance command except `compact` refuse to run; rerun `compact` to finish |
| Control store | not restored with content; host-controlled backup is a #205 launch gate |
| Local device files, keyring, user-downloaded exports, provider-held copies | not touched remotely; local physical remnants are `owner_controlled` (local `compact` available) |

## 8. Runbooks

**Staff session.** Bootstrap once (#205). Open `/#staff`, sign in with the Owner's address/password (a
separate staff session, 1 h). An ordinary session gets `403`; a staff session cannot use ordinary routes.

**Safe lookup.** Enter the account ID; read state, expected conditions and replay status. `unavailable`
or `unreadable` is not an all-clear. Lookup never changes anything.

**Credit adjustment.** Enter signed deltas (≤ 4 dp) and a reason → Preview → check target, balances and
refusal → Confirm. "Applied" appears only with the entitlement event ID and refreshed balances. On
"Outcome unknown", press **Check status** (same operation ID); never resubmit with a new ID. `stale`:
re-preview. Corrections are new adjustments with their own reason.

**Data requests.** Queue (`/#staff`): verify the requester is the account owner (the request is
session-bound) and the scope; **Approve**, then **Execute**. Read the result: `completed`; `failed` (phase and
`detail_code` say why; fix and **Retry** — a new attempt within the same deadlines); `in_progress` with
`progress_code` (pending phases). A Story/account in deletion is fenced (`409` for new changes) at once.
**Reject** only out-of-scope or unverifiable requests, with a code and reason. The administrator's own
account cannot be erased while bound. Before executing an account deletion, check the requester's
export requests: executing it removes every service-managed export artifact of the account, so let an
available export be downloaded first (the requester was told to export before closure).

**Artifact delivery/expiry.** The owner downloads while `available`; run retention expiry daily
(console **Run retention expiry** or `python -m afterworlds.operations.maintenance expire`).

**Physical compaction (within the 7-day live deadline).** Stop the app; `python -m
afterworlds.operations.maintenance compact`; restart; `finalize` (or **Re-check completion**). Run it
before any `storage_cli capture` (capture refuses otherwise). If it fails (a typed `failed (...); retry`
line, exit 1) or is interrupted, run it again: it resumes a completed rebuild or discards an incomplete
one, and nothing serves the stores until it finishes. Always restart the app in a new process after compaction:
a process that held deleted text in memory (as the serving app did) can persist it into vector index
files if it writes them later.

**Backup pending / final completion.** A deletion stays `in_progress` (`backups_pending`) until every
affected backup is disposed: `storage_cli due` / `dispose` (#205), then `maintenance finalize`. Past 30
days the phase fails and an `overdue_final_deletion` anomaly is shown: dispose the backup or record the
failure; never relabel it complete.

**Restore.** Stop the app; `storage_cli restore --backup-id` (#205 refuses an expired backup or a rewinding
ledger); `python -m afterworlds.operations.maintenance enforce-restore` (re-applies every active deletion
from the control store's inventories, re-expires expired ledgers and old refusal rows, then compacts);
`storage_cli verify-restore`; start the app. A closed account stays closed. Note: a restore of a backup
captured before a closed account's ledger expiry is refused by #205's ledger-continuity rule (boundary
recorded in ADR-022).

**Suppression release and annual reviews.** `maintenance reviews` lists suppressions and rights evidence
due for annual review. `maintenance release-suppression --suppression-id` releases only when every affected
backup is disposed and the horizons have passed; otherwise it keeps the suppression (exit 2).

**Post-closure status.** The requester keeps the receipt code shown at confirmation; `POST
/api/data-requests/receipt` with request ID and code returns status and receipt. Any mismatch is the same
`404`.

**Anomalies.** `/#staff` → Anomalies: failed/uncertain support actions, failed/blocked/overdue requests,
replay/projection inconsistency, durable delivered-turn settlement failures, unfinished restores. `sources`
shows what was read (`unavailable` ≠ healthy; `commercial_events: not_integrated`). Notes
(Investigating/Close) append history and repair nothing; fix state only through §3 actions.

**Local BYOK.** "Your data" works without an account: request, confirm, **Run now**, download. Nothing is
uploaded; local keys and licence state are not deleted.

## 9. Legal clocks and the applicability gate (separate from service clocks)

The 7-day production and download windows are not a statutory access-response or preservation policy.
Applicable request-response clocks for the initial markets must be determined for the actual launch setup
and run from their legally required start: e.g. Canada's PIPEDA access guidance (normally 30 days from
receipt, limited extensions with notice); Mexico's LFPDPPP ARCO process (20 business days to determine, 15 to
give effect, justified extensions); US state privacy laws by applicability, thresholds and verification
rules. **Status: not determined — an unmet launch prerequisite** (package worksheet). No financial/legal
preservation exception is implemented or active; no record is kept longer than §5 on a financial or legal
basis; a future exception follows the package's exception-record contract and is disclosed in receipts. US,
Canadian and Mexican financial-record duties (and whether a retained entitlement event is tax evidence)
await the Owner's qualified advice. No complete US/Canada/Mexico compliance is claimed.

## 10. Known limits and gates

- CRD Issue 23: account closure with a live hosted subscription or Cloud Services shows `commercial:
  dependency_unavailable` and never completes; payment/webhook/refund/reconciliation events are not
  integrated into anomalies.
- Physical compaction and restore enforcement are offline (app stopped).
- A remote content restore after a closed account's ledger has expired is refused by #205's continuity rule.
- HTTP server access logs (uvicorn, host) record request paths; host log retention is a #205 launch gate.
- Real email processor, TLS/host hardening, control-store backups, sign-in rate limiting and multiworker
  coordination remain #205 launch gates. Public launch remains the Owner's decision.
