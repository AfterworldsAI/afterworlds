# Remote Identity, Ownership and Storage — Operations Record

**Governs:** [Prerequisite #205](https://github.com/AfterworldsAI/afterworlds/issues/205) revision 1, for
[CRD Issue 22 #206](https://github.com/AfterworldsAI/afterworlds/issues/206) revision 7. Engineering
selections: [ADR-021](../decisions/adr-021-remote-identity-and-storage.md). Accepted contract copies:
[`crd-issue-22-governing/`](crd-issue-22-governing/README.md).
**Dependencies:** CRD Issue 22 consumes these hooks for support, export/deletion fulfillment, retention
and anomaly visibility; CRD Issue 23 owns payments, trial and subscription closure. This record claims
neither successor.

Nothing here authorizes deployment, real-data migration, remote activation or public launch.

## 1. Selected trust boundary

| Element | Selection | Code |
|---|---|---|
| Deployment switch | `AFTERWORLDS_DEPLOYMENT=remote`; default `local` keeps CRD Issues 19–21 unchanged | `api/config.py`, `api/app.py` |
| Identity authority | Afterworlds' own identity service over the control store; no external vendor | `remote/identity.py` |
| Credential | Contact address + password; stdlib scrypt verifier (n=2^14, r=8, p=1) | `remote/verifiers.py` |
| Proof of address | Single-use 256-bit code via the notice transport; 15-minute expiry, 5 attempts | `remote/identity.py`, `remote/notices.py` |
| Session | Opaque 256-bit token; SHA-256 verifier stored; `HttpOnly`, `Secure`, `SameSite=Strict` cookie; 24 h ordinary / 1 h staff; new token at every sign-in | `remote/identity.py`, `api/remote_access.py` |
| Contexts | `aw_session` (Sojourner) and `aw_staff_session` (staff) are separate cookies and separate server records; neither resolves as the other | `api/remote_access.py` |
| Request authority | App-level `enforce_access`: default deny outside `PUBLIC_PATHS`; actor only from the server session | `api/remote_access.py` |
| Cross-site submission | Unsafe methods require `X-Afterworlds-Request: 1` (no CORS middleware grants a cross-origin preflight); `SameSite=Strict` | `api/remote_access.py`, `frontend/src/api/client.ts` |
| Transport | The deployment must terminate TLS in front of the single uvicorn process; `Secure` cookies are not sent over plain HTTP except to a loopback test server | launch gate (§8) |
| Failure | Identity store unreachable → `503 identity_unavailable`; every credential failure → `401 authentication_failed`; missing/expired/revoked session → `401 authentication_required`; ordinary session on staff route → `403 staff_authority_required` | `api/errors.py` |

Enrollment and recovery answer `202 accepted` identically whether or not the address exists; sign-in
failure is identical for unknown and wrong-password cases and costs the same scrypt work.

## 2. Logical matrix → actual store mapping

All rows below are in the **control store** (`AFTERWORLDS_CONTROL_DATABASE_URL`, chain
`alembic_control/`, revision `c0001`) unless marked *content*. "Extra" marks a field or record not named
in the accepted matrix, with its owner, purpose and disposition recorded before collection.

| Matrix record | Table / columns | Notes |
|---|---|---|
| Hosted account | `hosted_accounts`: `account_id`, `identity_subject_ref`, `status`, `created_at`, `updated_at`, `closed_at`, `policy_version` | `identity_subject_ref` = principal ref. `account_id` is also the entitlement subject. |
| Account profile/settings | `identity_principals.contact_address` | Only the contact address is collected. No `display_name`, `locale` or setting keys are collected. Export: own address (CRD 22); deletion: removed within 7 days of confirmed erasure. |
| Authentication/session/recovery | `identity_principals`: `principal_ref`, `account_id`, `password_verifier`, `address_verified_at`, `created_at`, `updated_at`; `auth_sessions`: `session_id`, `principal_ref`, `account_id`, `context`, `token_verifier`, `issued_at`, `expires_at`, `revoked_at`, `status_code`; `verification_operations`: `operation_id`, `principal_ref`, `kind`, `code_verifier`, `issued_at`, `expires_at`, `attempts`, `used_at`, `revoked_at` | Extra: `address_verified_at` (proves address control before recovery), `context` (separates staff), `attempts` (limits code guessing), `kind`. Verifiers are restricted to the identity owner, never exported, logged or shown. Revoked at closure; removed with the account (CRD 22). | <!-- pragma: allowlist secret -->
| Sole administrator binding | `admin_bindings`: `binding_id`, `principal_ref`, `role_code`, `provisioned_at`, `provisioning_operation_ref`, `revoked_at`, `reason_code`, `policy_version` | Partial unique index: at most one active binding. No HTTP route writes it. |
| Administrator-action receipt (minimized) | `identity_audit_events` (append-only triggers): `event_order`, `event_id`, `operation_id`, `actor_ref`, `action_code`, `target_ref`, `reason_code`, bounded `reason_text`, `outcome_code`, `recorded_at`, `policy_version` | Codes/opaque refs only; 24 months after closure per D4 (expiry path: CRD 22). |
| Account-owned resource mapping | *content* `account_resources`: `mapping_id`, `account_id`, `resource_type`, `resource_id`, `ownership_revision`, `created_at`, `retired_at`, `source_operation_ref` | Partial unique index: one active owner per resource. Not FK-bound to `stories`, so it survives parent detachment for account-wide enumeration. |
| Deletion suppression | `deletion_suppressions` (all matrix fields) | Authoritative input from CRD 22; outside the content snapshot. |
| Object/backup inventory | `backup_inventory`: `backup_id`, `store_id`, `storage_locator`, `class_code`, `original_capture_at`, `copied_from_backup_id`, `policy_version`, `expires_at`, `disposed_at`, `verification_status` | Extra: `copied_from_backup_id` (copy lineage proves lifetime is not renewed). Locator is a server path, never a credential. |
| — (extra record) | `restore_records`: `restore_id`, `backup_id`, `restored_at`, `status`, `verified_at` | Restore gate. Non-personal. |
| — (extra record) | `deployment_marker` / *content* `remote_store_marker`: `content_store_id`, `initialized_at` | Binds one control store to one content store. Non-personal. |

No record holds a raw password, session token, code, BYOK key, profile JSON or Story content.

## 3. Ownership map and singleton disposition

| Data | Owner relation (remote) |
|---|---|
| Story root | `account_resources` row (`resource_type = story`), written in the Story's own creation transaction |
| Arc / Chapter / Node / Turn, Story Bible (incl. `sb_dynamic_field_history`), Rolling Summaries, mode session/setup state, world/character state | Through the Story root (`story_id`) |
| Character sheets, D&D 5e state, parties, creatures, items, bindings, adoption requests, leases, coordination, pending rolls, action-resolution sequences/events, roll audit | Through the Story root: every table is FK-bound to `stories.story_id`; no independently owned sheet exists today. A future cross-Story sheet needs an explicit binding (not inferred). |
| Retrieval markers and `story_memory` chunks | Through the Story root; guarded before the `story_id` filter |
| Entitlement events / projection | Subject = `account_id` |
| Provider refusal log | `sojourner_id` = `account_id` |
| Shared Rules Packages, corpus, Rules Chroma collection | Shared authority; no account ownership |
| Generated files / exports / signed artifacts | None exist; any later one inherits the Story guard |
| Account-scoped caches | None exist (`story_locks` is an in-process lock registry keyed by Story ID; `rpg_setup._character_schema` caches a static schema) |
| Websocket / stream / upload / callback endpoints | None exist |

**Singleton disposition:** a remote deployment never provisions or reads `sojourner_identity`; it starts
only on an empty content store (or one carrying its own marker). The protected local store, test
stores and CRD Issue 21 proof data are refused before any migration touches them. A Story row without
an active ownership row is invisible and returns 404. No import, claim or reassignment path exists.

## 4. Store and backup inventory

| Store | Holds | Authorized readers | Secret handling | Backup / restore | Expiry hook |
|---|---|---|---|---|---|
| Content SQLite + `-wal`/`-shm` | Narrative, RPG, entitlement, ownership | App process (O); operator under the store lock | No secrets | `storage_cli capture` (online backup API) → inventoried with capture time; `restore` → pending gate | Backups expire 21 days after original capture (`due`) |
| Control SQLite + journal | Identity, sessions, binding, audit, suppression, inventory | App process; bootstrap/storage operators | Verifiers only | **Not** restored with content; back it up separately under host controls (launch gate) | Session/recovery removal is CRD 22's erasure step |
| Embedded Chroma directory | `story_memory` chunks, Rules corpus | App process; operator under lock | No secrets | Copied with each capture; restored with it | Per-Story delete + count-zero (ADR-018 D11) |
| Notice outbox directory | Pending enrollment/recovery codes | Operator relay only (files `0600`) | Codes are single-use, 15-minute | Never backed up | Operator removes delivered notices; replaced by a real processor before launch |
| Turn-lease owner sidecars (`<db>.turn-owners/`), store lock (`<db>.serve.lock`) | Process liveness only | App process | None | Not backed up | Process lifetime |
| Browser | HttpOnly session cookie; last Story ID and drafts (cleared at sign-out) | The user | No authority | — | — |

**Deadline support (D4):** `register_backup`/`copy_backup` keep `original_capture_at` and `expires_at`;
`begin_restore` refuses a backup at or past 21 days, disposed, or with unverified coverage;
`backup_disposition` lists every backup captured at or before a suppression's boundary until disposed,
treats `inaccessible`/`unverified` entries as incomplete, and reports overdue at the overall 30-day limit
from the confirmed request. CRD Issue 22 orchestrates the operations; the hooks prove the clocks.

## 5. Topology

One uvicorn worker process per content store (Binding Decision 8, ADR-021 D6). `create_app` holds an
exclusive OS lock (`<db>.serve.lock`) for the process lifetime and releases it if startup is refused;
a second process or a storage command fails while it is held. Per-Story turn locks, durable RPG leases
(and their owner-process proof), entitlement idempotency and SQL/vector sequencing are therefore
unchanged. Startup migration runs only after the fresh-store and restore-gate checks, inside the lock.
Multiple workers, replicas or hosts are not enabled; they require a separately reviewed
shared-coordination contract.

## 6. Delayed work

Every delayed operation carries a `DelayedWorkScope` (account, Story, operation) rechecked when it runs:
ownership, active account and no suppression (`AccessPolicy.check_delayed_work`). The only delayed job is
`scripts/retrieval_backfill.py`; remotely it requires `--account-id` and exits `3` when refused. Deletion
(`--mode delete`) needs only the owning account, because it enforces a suppression. Retrieval writes
during a turn pass the same guard, so a turn finishing after closure or suppression cannot re-ingest.

## 7. Runbooks

### Owner administrator bootstrap (once)

1. The Owner enrolls through the app (address verified by code) and can sign in.
2. On the server, with control-store access:
   `python -m afterworlds.remote.bootstrap --contact-address <owner address>`; enter the Owner's
   password at the prompt (never on the command line).
3. Expected: `owner administrator: provisioned`. A re-run prints `already_provisioned`; any other
   principal is refused (exit 1). Each attempt is an `identity_audit_events` row.
4. The Owner signs in to staff context via `POST /api/admin/session` (separate from ordinary sign-in).

### Account recovery

Self-service only: `POST /api/auth/recovery` → code to the verified address → `POST
/api/auth/recovery/complete`. All sessions, staff included, are revoked; ownership, closure and the
binding are untouched; closed accounts cannot recover. **Staff-assisted recovery is not provided**: an
account ID, ticket, Story ID or old session is never accepted as proof.

### Session revocation and closure

- Staff: `POST /api/admin/accounts/{account_id}/sessions/revoke` with a reason (audited).
- Owner of the account: `POST /api/account/close` with password; revokes every session and denies the
  account. Erasure/export remain CRD Issue 22's.

### Backup, restore and fence

1. Stop the app. `python -m afterworlds.remote.storage_cli capture --to <dir>` (prints the backup ID).
2. `... storage_cli due` lists backups at/after 21 days; `... storage_cli dispose --backup-id <id>` removes one and records its disposal.
3. Restore: stop the app; `... storage_cli restore --backup-id <id>`. It is refused (exit 1, nothing
   copied) unless the live entitlement ledger is a prefix of the snapshot's; otherwise the app now
   refuses to start until step 4.
4. Enforce every active deletion suppression (CRD Issue 22 supplies this), then
   `... storage_cli verify-restore --restore-id <id>`; exit `2` lists suppressed Stories still present,
   and an unavailable Chroma read fails rather than counting as zero. Only `verified` lets the app start.
5. Revoked sessions, closures and suppressions survive because they live in the control store.
6. `verify-restore` checks every content table with a `story_id` column and the story-memory chunk
   count for each suppressed Story (account-scope instructions expand to every Story the account ever
   owned). Turns orphaned by `SET NULL` carry no `story_id`; CRD Issue 22's enforcer removes them from
   its pre-detachment inventory before verification.

## 8. Open launch gates (not implemented claims)

- TLS termination and host hardening for the remote server; actual host, backup and storage
  locations and disposal controls (package contract: Processors and storage).
- A real notice/email processor replacing the operator outbox.
- Control-store backup and restore under host controls.
- Sign-in abuse/rate protection before public exposure.
- Initial-market financial/privacy applicability (US, Canada, Mexico) before affected exceptions and
  public launch.
- CRD Issue 22 fulfillment (export, deletion, suppression creation, retention expiry, anomalies) and CRD
  Issue 23 payments.
- Multiworker coordination, if ever required.
- **Accepting an unprovable restore (Owner decision):** "When a content restore cannot prove that the restored entitlement ledger contains every recorded event (the live store is lost, or events were recorded after capture), what authority and reconciliation accept the restored money/access state before hosted service resumes?" The foundation guarantee is
  implemented: a restore that would rewind, diverge from or cannot read the live entitlement ledger
  is refused (§7). In practice that blocks restoring an older snapshot of an active hosted store.
