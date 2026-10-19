# Remote Identity and Storage Prerequisite for CRD Issue 22

**Status:** Owner-accepted prerequisite contract, revision 1. The Owner accepted the full package and CRD Issue 22 revision 7 and authorized governing publication and implementation to begin after verified publication, subject to the accepted dependency gates. Prepared against main `d3477eeaba42354e0048b69e4efec45b3ad0585f`. Remote activation, public launch and merge remain separate Owner-controlled gates.

## Goal

Establish the authenticated, account-isolated remote foundation for hosted subscriptions, account-based Cloud Services, and CRD Issue 22's support and data-request workflows. Preserve independent local BYOK use and perpetual rights. Every remote request and durable effect must have a trusted actor, account, ownership scope, and storage boundary.

This prerequisite owns remote identity, account ownership, storage and access integration. CRD Issue 22 owns support actions, Story/account export and deletion, retention fulfillment, backup cleanup, and anomaly visibility. CRD Issue 23 owns commercial enrollment and payments. Passing this prerequisite does not claim either successor is complete.

## Background and authority

CRD Issue 22 D1 records the Owner's decision that hosted subscriptions run remotely in production; BYOK users require accounts only for Cloud Services. The Owner is the sole initial full administrator through a controlled authenticated bootstrap. D2 requires Story and account-wide export/deletion. D4 approves the seven-day export and live-deletion deadlines, seven-day hosted export availability, 24-hour failed-artifact cleanup, 21-day rolling backups, and overall 30-day deletion completion. This prerequisite must make those commitments feasible without inventing additional retention policy.

The present app provisions one server-wide local Sojourner ID at app construction and derives it for every caller. Story rows have no account owner; Story lists enumerate all rows and direct lookup uses only the Story ID. Entitlements use a Sojourner ID, while the current account API includes local OS-keychain BYOK credential operations. Retrieval Memory uses a shared Chroma collection gated by Story ID; remote authorization must bind that Story ID to the authenticated account before reads, writes, reindex, or deletion. Story locks live in one app process; RPG turn-lease recovery depends on SQLite and OS sidecar files. The remote deployment must preserve those invariants.

The local-first shell and CRD Issue 21 proofs remain accepted for their original scope. This contract reconciles remote production with them; local success is not proof of multi-account isolation.

## Owner decisions carried forward

1. Hosted subscriptions are remotely accessed in production. Local subscription use may support early testing. A local-only support panel does not satisfy remote account operations.
2. Local BYOK orchestration, owned-content read/export/deletion and perpetual rights work without a cloud account or active Cloud Services. A remote account is required only for Cloud Services.
3. The Owner is the sole initial full administrator. Ordinary registration, profile fields, account IDs and request parameters cannot grant or impersonate that authority. A multi-staff role hierarchy is unnecessary initially.
4. Full remote administrator authority does not include local-device access or raw BYOK-key disclosure. Mutations retain owning-service authority, reason and durable actor provenance.
5. CRD Issue 22's D4 periods constrain store and backup selection. The field-level retention matrix and terminal-deletion ADR exceptions remain part of CRD Issue 22's separate lifecycle package.

## In scope

- Authenticated remote accounts, stable identity mapping, distinct staff actor context, controlled Owner bootstrap, session revocation, and secure account recovery.
- Account authorization across API, services, SQL, Retrieval Memory, files/artifacts, caches, background jobs, and any future socket/stream/gateway path.
- Durable ownership mapping for newly created remote data. Initial remote stores start without implicit imports of local/test data; any explicitly authorized import needs a verified ownership inventory. Unknown ownership is not guessed.
- Remote account, entitlement, session, Story and vector storage plus backup/restore boundaries needed for later CRD Issue 22 operations.
- Production-shaped API/frontend sign-in, sign-out, recovery and failure behavior through the existing app factory, typed errors, versioned backend DTOs, generated contracts and single frontend API client.
- A declared remote worker/store topology preserving transaction, serialization and lease guarantees. Multiworker operation requires a separately reviewed coordination proof.

## Out of scope

- CRD Issue 22's support UI, remediation, export/deletion fulfillment, retention exceptions, receipt lifecycle or anomaly investigation.
- CRD Issue 23's payment, trial, renewal, refund, webhook or reconciliation semantics.
- A multi-staff hierarchy, prescribed identity vendor, social-login policy, new cloud-key custody model, local-device administration or general hosting platform.
- Entitlement arithmetic/event ownership, provider routing, RPG cancellation, narrative-mode scope, Rules Package authority, or changed CRD Issue 21 acceptance.
- A general legacy-account migration/claim or cross-device import/sync product; automatic assignment of singleton data to a remote user; automatic upload; remote local-keychain access; a server-mediated BYOK provider workflow requiring raw keys.
- Publication, real-data migration, remote activation or deployment under this review draft.

## Required behavior

### 1. Trusted identity and lifecycle

Every protected remote request resolves an authenticated active principal from server-validated state, then a stable hosted account and role. Body, query, path, arbitrary header, browser storage or presented Story ID cannot select the acting identity or privilege. Define creation, sign-in, sign-out, expiry, rotation, revocation, account closure and access recovery. Authentication failure, unavailable identity authority, revoked sessions, closed accounts and ambiguous mappings fail closed with safe typed results. Owning services recheck authorization before effects; frontend visibility alone has no authority.

Bootstrap the Owner administrator only through a controlled, auditable server-side operation bound to a verified authenticated Owner principal. Repeated bootstrap is safe for that same principal and cannot provision another administrator through ordinary registration. Administrative requests carry distinct trusted staff context and deliberate hosted target. The Owner's ordinary Sojourner session cannot borrow staff authority simply because it belongs to the same person or browser.

Recovery restores account control only after proof through the accepted identity authority. Account ID, email, support ticket, Story ID or old session alone is insufficient. Recovery rotates or invalidates affected sessions and preserves account ownership, historical provenance, closure/suppression state and bootstrap integrity. Any staff-assisted recovery uses an explicit audited path; it cannot silently reassign an account or promote a principal. Engineering may select the authentication mechanism/vendor, but its trust boundary and recovery procedure must be documented before remote use.

### 2. Ownership and authorization

Define an authoritative hosted-account relation for Story roots, their Arc/Chapter/Node/Turn and Story Bible content, summaries, setup/session state, Character Sheets and RPG state, entitlement projection/events, provider metadata, Retrieval Memory markers/chunks, generated files/exports and account-scoped caches. Account-wide enumeration must remain possible after parent links are detached. Shared Rules Packages and their collections remain shared authority. If a sheet or other object is independently owned, establish its binding and disposition explicitly; do not infer transfer solely from a Story link.

Every Story list/create/get, transcript, visible-state, setup, turn, RPG action, account/entitlement, download and later request/status operation verifies the actor-to-owner relation before any read, mutation, provider call or vector operation. Direct service and job callers receive the same protection. Known or random IDs confer no authority. Cross-account requests return safe denial/no-disclosure and cause no effect. Administrator targeting is explicit, authenticated and action-scoped; it does not weaken ordinary Sojourner checks.

The remote API contract covers HTTP plus any introduced websocket, stream, polling, upload/download, callback, signed artifact or internal job entry point. No product websocket or export artifact endpoint currently exists; any later one inherits the boundary. Caller-chosen file paths or bare transferable IDs cannot authorize downloads. Browser state is presentation state, never account or staff truth.

### 3. Local BYOK separation

Keep local owner identity, local SQLite/Chroma content and OS-keychain credentials usable without remote sign-in. A Cloud Services account governs only hosted resources it actually owns. Linking local content to it requires an explicit consented and verified operation; account creation alone uploads nothing. Cloud Services lapse suspends hosted active use under ADR-013, while owned-content read/export/download and local BYOK use remain available.

Remote account/support views show only source-bound, non-secret license and service metadata; they cannot infer local credential presence/readiness. Raw BYOK keys, validation payloads and keychain contents must not enter remote API requests, SQL, logs, backups, artifacts, telemetry or admin views. The existing local key-write and validation routes cannot simply be published at the remote account path. Remote Cloud Services account support does not promise server-hosted BYOK generation. Any server-mediated BYOK provider path needing key material is a separate governed security/product decision, not an implication of this prerequisite.

### 4. Stores, migration and restore

Document the actual owners and isolation controls for account/authentication/session records, SQL, Chroma, files/artifacts, caches and backups, including authorized readers, secret handling, inventory, restore and expiration. SQLite and embedded Chroma may remain only if the chosen remote topology safely preserves their limits. This issue does not mandate a networked database or Chroma HTTP service. Migrations preserve existing entitlement event IDs and replay order, immutable history, Story/RPG relationships, local BYOK metadata semantics and CRD Issue 21 behavior except for explicit approved remote changes.

Initial remote stores must not implicitly import or reassign the protected local/test stores or CRD Issue 21 proof data. A newly created hosted account owns only its explicitly created hosted records. No general legacy-account migration, claim UI or cross-device import product is required. If a later explicitly authorized deployment needs pre-existing data imported, inventory its Story, sheet, entitlement, vector and file scope first and record verified ownership/provenance and reconciliation/restart behavior before exposing it. A local UUID, database possession, matching email or first login alone does not assign hosted ownership; unknown/conflicting rows remain inaccessible. No real data import or migration is authorized by this draft.

The remote foundation supplies persistent ownership/closure/revocation boundaries and tested restore/fencing hooks that accept authoritative deletion-suppression instructions. CRD Issue 22 later supplies the operational suppression records and deletion/retention orchestration. A disposable suppression fixture proves that a restore stays unavailable until those instructions are enforced, without requiring CRD Issue 22 fulfillment to be complete first. Copied/restored backups keep their original age. The store/backup inventory and these hooks must make the approved 21-day rolling window and overall 30-day deletion limit achievable, including inaccessible/failed inventory. Unverified coverage is a dependency failure, not presumed compliance.

### 5. Concurrency and delayed work

Declare the process/worker topology and prove per-Story turn serialization, RPG action/lease recovery, entitlement idempotency and transaction behavior, and SQL/vector coordination still hold. The current single-worker envelope may be retained if sufficient. Multiple workers, replicas, runners or hosts require a reviewed shared coordination and storage contract before activation; no distributed lock or database technology is prescribed. Startup migration and restore cannot race ordinary writes.

Every delayed job carries trusted account, Story and operation scope and checks current ownership, access, account closure and deletion fences when it executes. Stale jobs, reindex/backfill, provider results and event replay cannot cross accounts or recreate deleted content. Scope caches and generated files the same way. Multi-store partial progress is durable and retryable where needed; no success precedes the owning committed effect. Fencing a deletion is separate from inventing an RPG pending-action cancellation policy.

### 6. API and frontend integration

Integrate through create_app, the existing typed /api error envelope, backend-owned versioned DTOs, generated OpenAPI/TypeScript contracts and one frontend API client. The built app handles sign-in, logout, session expiry/revocation, forbidden access and safe recovery without persisting privileged authority or credentials as browser truth. Protect state-changing web requests against cross-site submission and session fixation as appropriate to the selected transport; use secure remote transport/session handling. Public health/static assets expose no account data. Logs and validation responses redact secrets and avoid revealing another account's existence.

Entitlement changes still flow only through receive_entitlement_event. Narrative data stays with Story/Story Bible services. Vector access requires account-to-Story authorization before the existing Story-ID filter. A mock login or changed UI flag is not remote isolation.

## Testing

Use disposable identities/stores and synthetic accounts. Drive the built API/frontend with two ordinary remote accounts and a separately authenticated Owner administrator. Exercise Story list/create/read, transcript, visible state, setup, turn and RPG actions, account/entitlement views, vector read/write/reindex/delete and the relevant job/file seams. Probe known IDs, forged actor/role/target fields, stale sessions, cross-account files and direct service calls. Prove normal-session denial even for the Owner and full authority only after controlled staff bootstrap.

Test logout, revocation, closure, secure recovery, and restart/response-loss boundaries. Show recovery does not grant staff authority or change Story ownership. Prove local BYOK remains usable without a cloud account and synthetic raw-key markers never reach remote durable/output paths. Preserve entitlement replay/precision and relevant CRD Issue 21 hosted/local behavior at changed seams.

Prove that a fresh remote deployment imports no local/test records or credentials, and rejects unowned/conflicting rows. If an explicitly authorized pre-existing-data import is included in the delivery, exercise its ownership inventory, reconciliation and interruption/restart behavior; do not invent a legacy migration project to satisfy this criterion. Exercise restore and delayed work against revoked/closed/deleted subjects, and backup inventory compatible with CRD Issue 22's deadlines. Prove the configured single-worker topology or separately reviewed multiworker coordination. No real identity account, provider key/call, customer data, payment service or shared runtime is required for default proof.

## Acceptance criteria

1. Accepted authority reconciles remote subscription/Cloud Services accounts with the earlier local-first shell and preserves independent local BYOK and CRD Issue 21 contracts.
2. Production-shaped remote sessions resolve trusted stable account/role context; forged identity, staff, target, and stale/revoked/closed-session inputs fail closed.
3. The Owner is the sole initial full administrator through controlled bootstrap. Normal enrollment/session and recovery cannot grant or borrow staff authority or reassign historical data.
4. SQL, vector, entitlement, session, cache, file/artifact and job paths enforce account ownership. Two-account proof covers reads, writes, enumeration and failure paths while shared Rules Packages remain shared.
5. Local BYOK orchestration and content access work without a cloud account. No raw BYOK key or authoritative local readiness enters remote service paths. Remote Cloud Services accounts do not imply server-hosted BYOK provider execution.
6. Initial remote stores import no local/test data implicitly and never guess ownership. Any separately authorized pre-existing-data import has evidence-backed ownership, reconciliation and recovery; applicable event ordering and Story/RPG/vector provenance are preserved.
7. The remote store/backup/restore inventory and tested ownership/revocation/fence hooks support CRD Issue 22's approved deadlines and authoritative suppression input. CRD Issue 22 owns the later fulfillment/orchestration; this prerequisite has no circular dependency on its completion. Missing foundation coverage remains an unmet dependency.
8. Worker topology preserves turn, RPG lease, entitlement and vector/SQL invariants; more than one writer/process is enabled only with separately reviewed shared-coordination proof.
9. Built remote API/frontend workflows exercise real identity integration, own-Story use, admin/normal separation, expiry/revocation and recovery. Typed errors and generated contracts match.
10. Applicable migration, Python/frontend, generated-contract, security and CI gates pass without weakening audits, tests or secret detection. A local singleton fixture or draft alone is not implementation proof.

## Documentation and Architecture Notes

Record the accepted account/identity/storage contract and exact dependency to CRD Issues 22 and 23. Reconcile Design §8, Construction Readiness, Known Unknowns, the CRD Issue 19 local-first shell decision, ADR-0004 SQLite persistence, ADR-013 entitlements, ADR-018 Retrieval Memory and credential-security records with narrow explicit supersession. Preserve the original local and CRD Issue 21 decisions. Document selected trust boundary, administrator bootstrap/recovery runbooks, ownership map, singleton disposition, worker count, store/backup inventory, restore checks and open launch gates.

An implementation PR's Architecture Notes must state “No drift from design principles” or name authorized drift, authority and residual risk. A mock login, local singleton fixture or documentation-only store plan cannot close remote acceptance.

## Branch and merge

This is the Owner-accepted governing prerequisite. Verify the complete governing issue and companion-contract publication before Claude Code implementation begins. Codex coordinates and reviews; Claude Code engineers. Use a clean isolated checkout from refreshed main, preserve the protected dirty checkout and CRD Issue 21 evidence, and make no direct commits to main. The Owner retains issue acceptance, publication, deployment, launch and merge authority. The Owner authorizes issue-scoped implementation in clean isolation. No real-data migration, shared-runtime operation, deployment, Rules Package activation, merge or public launch is authorized.

## Published governing companions

- [CRD Issue 22 — Operations, Support, and Compliance Minimums](https://github.com/AfterworldsAI/afterworlds/issues/206), accepted revision 7.
- [Accepted lifecycle ADR amendment contract](https://github.com/AfterworldsAI/afterworlds/issues/206#issuecomment-6246562569), revision 1.
- [Accepted field/store retention matrix](https://github.com/AfterworldsAI/afterworlds/issues/206#issuecomment-6246563742), revision 1.
- [Accepted package and gate contract](https://github.com/AfterworldsAI/afterworlds/issues/206#issuecomment-6246567253), revision 1.

These contracts govern the stated boundaries. Remote foundation delivery supplies the ownership/storage/fencing hooks; CRD Issue 22 supplies later operational fulfillment. No circular completion dependency is introduced.
