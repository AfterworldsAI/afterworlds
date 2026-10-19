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
| Failure | Identity store unreachable → `503 identity_unavailable` on every HTTP identity operation (public auth routes, session discovery, staff session/target/revocation, closure, and request admission) and when a control-authority read fails after admission (Story authorization/listing, suppression admission, owning-service rechecks; content-store faults keep their own error); every credential failure → `401 authentication_failed`; missing/expired/revoked session → `401 authentication_required`; ordinary session on staff route → `403 staff_authority_required` | `api/errors.py` |

Enrollment and recovery answer `202 accepted` identically whether or not the address exists; sign-in
failure is identical for unknown and wrong-password cases and costs the same scrypt work.

## 2. Logical matrix → actual store mapping

All rows below are in the **control store** (`AFTERWORLDS_CONTROL_DATABASE_URL`, chain
`src/afterworlds/migrations/control/`, revision `c0001`) unless marked *content*. "Extra" marks a field or record not named
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
| Object/backup inventory | `backup_inventory`: `backup_id`, `store_id`, `storage_locator`, `class_code`, `original_capture_at`, `copied_from_backup_id`, `policy_version`, `expires_at`, `disposed_at`, `verification_status` | Extra: `copied_from_backup_id` (copy lineage proves lifetime is not renewed). Locator is a server path, never a credential. Extra (#205 backup evidence): `storage_token` (random identity also written into the backup root as `afterworlds-backup.json`), `storage_namespace` (a random namespace, also written into the backup's namespace witness: set at capture, or -- for a copy -- committed as its admission intent before the first physical effect, after which the copy is bound to it; a copy records its planned token when it is claimed, and is proven only on completion, when it inherits the source's verification and clean proof) and `removal_started_at`. Owner: the storage operator's inventory; purpose: prove that a disposal removes -- or finds gone -- this backup object and let an interrupted removal retry honestly; readers: storage commands and operators only, never an API; classification: operational, non-personal, not account data (excluded from export); lifecycle: kept with the inventory row and ending with it under the inventory's existing end conditions -- no separate clock. The in-root identity file is removed last with the backup. A copy's identity file also records `copy_of` (the source's token), `copy_backup_id` (the copy's inventory id), `copy_destination` (its canonical location) and `copy_namespace` (the namespace its witness carries), written by the copy's completion step as evidence that this row's operation stamped this destination beside that witness (intent found anywhere else -- a filesystem copy of the marker, or the path beneath a replaced parent -- proves nothing); same owner, purpose, readers and classification, and they are deleted with the identity file -- no separate clock. A removal in progress moves the backup to a holding directory beside it named only by its token (`.afterworlds-disposing-<token>`, a fixed length whatever the backup's name, so every accepted location stays removable); capture and copy check that name, like the location, against other backups and the public root before any effect; the same holds for the namespace witness `.afterworlds-witness-<token>` beside the backup (outside its tree: `{"storage_token", "namespace", "moved"}`), written only when the backup is admitted -- by capture, or by the one copy step that first committed the copy's namespace to its row (so a retry can never rebind a copy to other media: once a namespace is committed, a missing witness leaves the copy pending, bound to it) -- and never by a disposal or absence retry; `moved` is set by the disposal only when this backup's own tree is seen in its holding directory (a successful, controlled move), before anything in it is deleted -- same owner, purpose, readers and classification as the row; it is the durable proof that the backup's namespace is still the one it was admitted in (an OS device/inode pair is not: it can recur on replacement media), is reserved with the row and covered by the public-root refusal, and is removed by the disposal right after its record (a terminal repeat removes a leftover one carrying the token) -- no separate clock; that directory belongs to the same undisposed backup (reserved against new captures/copies and any public static root) until the recorded disposal, and is removed by the disposal itself -- no separate clock. |
| — (extra record) | `restore_records`: `restore_id`, `backup_id`, `restored_at`, `status`, `verified_at` | Restore gate. Non-personal. |
| — (extra record) | `deployment_marker` / *content* `remote_store_marker`: `content_store_id`, `initialized_at` | Binds one control store to one content store. Non-personal. |
| — (extra record) | `deployment_initialization`: `content_store_id`, `started_at`, `content_target`, `vector_target` | A fresh deployment's in-progress initialization identity; removed when `deployment_marker` is written. Non-personal. |

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
| Content SQLite + `-wal`/`-shm` | Narrative, RPG, entitlement, ownership | App process (O); operator under both store locks | No secrets | `storage_cli capture` inventories first, then copies (online backup API); `restore` → write-ahead `copying` → copied → verified | Backups expire 21 days after original capture (`due`) |
| Control SQLite + journal | Identity, sessions, binding, audit, suppression, inventory | App process; bootstrap/storage operators | Verifiers only | **Not** restored with content; back it up separately under host controls (launch gate) | Session/recovery removal is CRD 22's erasure step |
| Embedded Chroma directory (bound by `afterworlds-deployment.json`, locked by `.afterworlds-serve.lock`) | `story_memory` chunks, Rules corpus | App process; operator under both locks | No secrets | Copied with each capture (required; a snapshot without its bound vector store cannot be restored); replaced with SQL on restore | Per-Story delete + count-zero (ADR-018 D11) |
| Notice outbox directory | Pending enrollment/recovery codes | Operator relay only (files `0600`) | Codes are single-use, 15-minute | Never backed up: startup, `capture` and `restore` refuse an outbox inside, equal to or around the live vector store or the public static root, and capture/restore refuse a vector tree containing a link into it; `due`/`dispose` cleanup deliberately skips these checks so a backup can always be removed. If the outbox cannot be written, the code stays issued (and expires), the request still answers `accepted`, and the operator log records only `notice_outbox_unwritable`, the notice kind and an opaque correlation id | Operator removes delivered notices; replaced by a real processor before launch |
| Turn-lease owner sidecars (`<db>.turn-owners/`), store locks (`<db>.serve.lock`, vector `.afterworlds-serve.lock`) | Process liveness only | App process | None | Not backed up (the vector lock file is excluded from captures) | Process lifetime |
| Browser | HttpOnly session cookie; last Story ID and drafts (cleared at sign-out) | The user | No authority | — | — |

**Deadline support (D4):** `register_backup`/`copy_backup` keep `original_capture_at` and `expires_at`;
`begin_restore` refuses a backup at or past 21 days, disposed, or with unverified coverage;
`backup_disposition` counts every backup that its capture did not prove clean of the suppression
(`clean_suppression_ids`, inherited by copies) until disposed, treats `inaccessible`/`unverified`
entries as incomplete, and reports overdue at the overall 30-day limit from the confirmed request.
Capture refuses while suppressed content remains, so a post-boundary backup is clean only by proof,
never by its timestamp. CRD Issue 22 orchestrates the operations; the hooks prove the clocks.

## 5. Topology

One uvicorn worker process per deployment (Binding Decision 8, ADR-021 D6). `create_app` holds
exclusive OS locks on the content store (`<db>.serve.lock`), the bound vector store and the control store
(`<control>.serve.lock`) for the process lifetime -- a second deployment configured with the same control
store is therefore refused, and a hard-linked content or control file is refused before opening -- and releases them if startup is refused; a second process, a storage command or the
backfill job fails while they are held. Per-Story turn locks, durable RPG leases (and their
owner-process proof), entitlement idempotency and SQL/vector sequencing are therefore unchanged.
Startup migration runs only after the fresh-store, vector-binding and restore-gate checks, inside the
locks. Both Alembic chains ship inside the package (`afterworlds/migrations/content`,
`afterworlds/migrations/control`), so an installed distribution migrates exactly as a checkout does;
a built frontend is served from the configured external `frontend_dist_dir`. The control store is migrated only there too: the storage commands, Rules provisioning,
remote backfill and the bootstrap command open it without any schema change and refuse a missing or
older control schema (start the application once after an upgrade, then run maintenance). A fresh deployment first commits a `deployment_initialization` record (its new
`content_store_id` and the normalized paths of the content and vector stores it proved empty) to
the control store while those stores are still empty, then stamps the still table-less content
store it is creating with that identity (`remote_initialization_provenance`, retired when the
content marker is written); migration, the content marker, the atomically published vector marker and finally
`deployment_marker` (which retires the record in the same transaction) follow. A start interrupted
at any of these boundaries is retried by simply starting again: it resumes that same identity on
those same recorded stores (a retry pointed at any other content or vector store is refused
untouched), accepting only its own partial effects (a store still without tables, or one carrying its stamp or
marker and no user data, and its own vector marker) and refusing anything else untouched -- a path
match and empty user tables are never enough, so an unrelated store copied onto the recorded path is
refused. Only a completed `deployment_marker` counts as a bound deployment,
so maintenance, capture and restore refuse a half-initialized one, and a completed deployment whose
store or vector marker is missing is never re-initialized. A failed start releases both locks and
disposes its engine. (Its embedded-Chroma release reads chromadb's private client registries,
so `chromadb` is pinned exactly to the verified 1.5.9; changing the pin requires a compatibility
review of that cleanup.) An in-process per-account fence orders request effects against closure (and CRD Issue 22
suppression): requests hold it shared; closure takes it exclusive with a bounded wait
(`close_fence_timeout`, 30 s) and returns `409 account_operation_in_progress` without changing
anything if in-flight work does not finish. Work handed to a worker thread -- every synchronous route handler and every Story-locked mutation -- keeps its own counted fence lease (and its Story lock) until the synchronous worker actually finishes, and a cancelled request keeps awaiting the worker so request-owned resources such as its database session are not closed under it, so a cancelled or disconnected request never lets closure, suppression or another same-Story mutation start while its effects can still land. Multiple workers, replicas or hosts are not enabled; they
require a separately reviewed shared-coordination contract.

## 6. Delayed work and owning-service scope

Remote effects run under a trusted `DelayedWorkScope` (account, Story, operation): set by the request
after its session is revalidated under the fence, or explicitly by a job. The orchestrator, RPG action
and Retrieval Memory seams recheck it at every call (`AccessPolicy.check_current`): owner = scope
account, account active, Story unsuppressed. Unscoped, cross-account or mismatched-subject direct
calls are refused before the service runs. The only delayed job is `scripts/retrieval_backfill.py`;
remotely it requires `--account-id`, runs inside both store locks (so only while the app is stopped),
refuses a pending restore, and every write rechecks the scope — a closure or suppression mid-job stops
the remaining writes (exit `3`). Deletion (`--mode delete`) needs only the owning account, because it
enforces a suppression, and no live Story row: it removes orphan chunks whose SQL Story is already
gone while the durable ownership mapping remains (the same is true of local `--mode delete`).

## 7. Runbooks

### Owner administrator bootstrap (once)

1. The Owner enrolls through the app (address verified by code) and can sign in.
2. On the server, with control-store access:
   `python -m afterworlds.remote.bootstrap --contact-address <owner address>`; enter the Owner's
   password at the prompt (never on the command line).
3. Expected: `owner administrator: provisioned`. A re-run prints `already_provisioned`; any other
   principal is refused (exit 1). Each attempt is an `identity_audit_events` row (`owner_admin_bootstrap`), committed before the command reports: a refusal before the identity is proven (malformed address, unknown or unverified principal, wrong password, inactive account) is recorded with `actor_ref = unauthenticated` and a reason code only -- never the address or any credential. If the control store cannot be opened or migrated, or the receipt cannot be committed, the command exits 2 with a fixed message and nothing is provisioned.
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

### Provisioning shared Rules authority (once per deployment, app stopped)

`python -m afterworlds.remote.rules_provisioning` (same environment as the app). It holds both store
locks, requires the content/control/vector pairing, refuses a pending restore, and runs the existing
publication owners: the source corpus release from the pinned, qualified source, then the
committed accepted oracle for that release. From a source checkout the inputs are the checkout's; an
installed distribution has none, so pass `--source-root <dir>` holding the official PDF
(`docs/sources/…`) and the pinned snapshot. That directory only supplies inputs: the candidate built
from it must match a committed accepted oracle shipped with the release, checked before anything is
published, and a missing or tampered input is refused. Output names the package and release; a re-run reports
`corpus reused, authority already_published`. It writes only Rules SQL tables and the Rules corpus
collection — never Story memory, accounts or Story data — and imports nothing local. RPG Stories can
then select the package during setup. The local `reset_corpus_baseline.py` remains refused remotely.

### Backup, restore and fence

1. Stop the app (the commands need the store locks; `due`/`dispose` need only the control lease). Every entry point that knows both stores
   (app startup, storage CLI, Rules provisioning, remote backfill) refuses a control store that is
   physically the content store (same path, symlink or hard link) before opening either.
   The public static root (`frontend_dist_dir`, served unauthenticated at `/`) may not be, contain or
   sit inside the content or control store, the live vector store, the notice outbox or any undisposed
   backup (verified or not): startup refuses before creating any store or mounting, `capture` and
   `restore` refuse a public target, snapshot or live destination, while `due`/`dispose` stay available
   so an unsafely placed backup can still be removed.
   `python -m afterworlds.remote.storage_cli capture --to <dir>` prints the backup ID. It refuses while
   a restore is pending or suppressed content is still present. The backup is inventoried
   (`unverified`, with its token and namespace) before its first filesystem effect and becomes `verified`
   only when both stores are copied; an existing target is refused untouched with nothing recorded. An
   interrupted capture stays inventoried as unverified — dispose it (it is removed only once its witness
   and identity prove it; otherwise it stays incomplete) and capture again to a new directory. Locators are recorded as absolute, symlink-resolved paths (a relative `--to` is fixed
   against the directory it was given in), and a location belongs to at most one undisposed backup:
   capture and copy refuse a location an undisposed backup still holds, including after a disposal
   whose record was lost, until that disposal is recorded. A snapshot holds the content store as `content.sqlite3` and the vectors as `chroma/` (reserved names, whatever the live database is called);
   snapshots captured earlier with the SQL file under the live database's name remain restorable. A target inside (or around) the live vector store is refused before anything is created.
2. `due` and `dispose` need only the control-store lease and binding -- not the live content or vector
   locks or paths -- so backups can still be expired and disposed while a live store is damaged or its
   volume is unavailable (an inaccessible *backup* still stays incomplete). `... storage_cli due` lists backups at/after 21 days; `... storage_cli dispose --backup-id <id>`
   removes the files, then records the disposal -- only for the object carrying the inventoried
   identity -- the root and holding directory as actual directory entries, and the identity and witness as
   actual files, never followed through a link or junction (a redirection, dangling or not, is neither the
   backup nor its absence, and its target is never touched): it records the removal as started, renames the backup beside itself to a fixed-length name
   carrying only its token, and removes the contents with the identity file last. A retry resumes from either (also after
   a partial removal). A missing location counts as removed only when this deployment had started the
   removal and the backup's namespace witness (`.afterworlds-witness-<token>` beside it, outside its
   tree, written only when the backup was admitted) still carries the recorded namespace -- checked before
   every destructive step and again before certifying; a detached, replaced or bind-mounted namespace
   (even replacement media presenting the same OS device/inode pair), a different object at the location, or a backup never proven to exist
   (metadata-only inventory) is marked `inaccessible`, nothing is removed, and the obligation stays
   incomplete. A copy gets its own identity, and inherits the source's verification and clean proof, only when its destination positively carries the source backup's identity; otherwise it is recorded metadata-only, unverified, with no clean claims, and stays incomplete until proven. A copy is one operation, its inventory row: the row (destination, planned token reserving the root and holding directory, the source's lineage and age, no proof) commits before anything at the destination changes, and every retry of the same source and destination completes that same row -- after a lost commit or response, while the destination is unavailable, or once a replaced namespace is back -- never minting a competing reservation or renewing age; until positive evidence is found it stays metadata-only and incomplete. A copy of the marker elsewhere proves nothing. A holding directory is resumed only after a recorded start, and a tokenless one only as the empty shell identity-last deletion leaves. A missing location is certified only when the witness records that this backup's own tree was moved into its holding directory: a recorded start is only an intention, and a rename that failed (a bind-mounted or busy root) never becomes evidence after an unmount. The witness is removed only after the disposal is recorded. Disposing an already
   disposed backup touches nothing but that backup's own leftover witness (its old location may hold a newer backup).
3. Restore: stop the app; `... storage_cli restore --backup-id <id>`. It is refused (exit 1, nothing
   recorded or copied) unless the backup is verified and unexpired, its snapshot holds this
   deployment's vector store, and the live entitlement ledger is a prefix of the snapshot's. The
   restore is recorded `copying` before files change and marked copied only after both stores are
   replaced. If it fails part-way the app stays fenced; run `restore` again (it supersedes the
   unfinished attempt).
   While a restore of a backup is still `copying`, that backup's disposal is refused (`dispose` exits 1;
   nothing changes) until its earliest disposal deadline: its own 21-day expiry, or the 30-day backup
   horizon of any active suppression it is not proven clean of. From that deadline on, `dispose` runs
   normally. The restore stays `copying` and the app stays fenced: disposal neither completes nor
   cancels it, and recovery from that backup is no longer possible (`restore` also refuses an expired
   backup). Once the restore reaches `pending_enforcement`, or is superseded by a restore from another
   backup, disposal works normally at any time. No clock changes: `due` and backup disposition keep
   their 21-day and 30-day rules. Retry or supersede a stuck restore before its deadline; one left
   `copying` past it is an open recovery failure for CRD Issue 22 (#206) fulfillment.
4. Enforce every active deletion suppression (CRD Issue 22 supplies this), then
   `... storage_cli verify-restore --restore-id <id>`. It refuses an unfinished copy; exit `2` lists
   suppressed Stories still present, and an unavailable Chroma read fails rather than counting as zero.
   Only `verified` lets the app start.
5. Revoked sessions, closures and suppressions survive because they live in the control store.
   CRD Issue 22 records suppressions only through `remote.access.record_suppression_fenced`.
6. Verification checks every content table with a `story_id` column and the story-memory chunk count
   for each suppressed Story (account-scope instructions expand to every Story the account ever owned).
   Turns orphaned by `SET NULL` carry no `story_id`; CRD Issue 22 takes the pre-detachment inventory
   (`remote.inventory.account_inventory`) and disposes of them before verification.

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
