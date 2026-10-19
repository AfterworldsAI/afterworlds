# ADR-021 — Remote Identity, Account Ownership and Storage Boundary

**Date:** 2026-10-17
**Status:** Proposed — engineering selections made under the accepted prerequisite #205, pending
Codex review and Owner acceptance. Only #205 and its companion contracts are accepted authority.
**Governing contract:** [Remote Identity and Storage Prerequisite for CRD Issue 22, #205](https://github.com/AfterworldsAI/afterworlds/issues/205),
revision 1, with [CRD Issue 22 #206](https://github.com/AfterworldsAI/afterworlds/issues/206) revision 7
and its accepted companions: [lifecycle ADR amendments](https://github.com/AfterworldsAI/afterworlds/issues/206#issuecomment-6246562569),
[field/store retention matrix](https://github.com/AfterworldsAI/afterworlds/issues/206#issuecomment-6246563742)
and [package/gate contract](https://github.com/AfterworldsAI/afterworlds/issues/206#issuecomment-6246567253).
Exact copies and SHA-256 identities: `docs/architecture/crd-issue-22-governing/`.

This ADR records the **engineering selections** the prerequisite leaves to implementation. It does
not alter the accepted contract; where this ADR and the contract differ, the contract governs.
Operational detail (ownership map, store/backup inventory, runbooks, launch gates) lives in
[`docs/architecture/remote-identity-and-storage.md`](../architecture/remote-identity-and-storage.md).

## Context

The CRD Issue 19 shell provisions one server-wide local Sojourner identity (`sojourner_identity`,
"DoR-A") at app construction and derives it for every caller. That remains correct for the local
BYOK product. Owner Decision D1 (CRD Issue 22) requires hosted subscriptions to run remotely, with
accounts for Cloud Services only, and a sole Owner administrator. A singleton identity cannot prove
per-account isolation.

## Decisions

### D1. Two deployment modes behind one app factory

`AFTERWORLDS_DEPLOYMENT=local` (default) keeps the CRD Issue 19–21 behavior exactly: singleton local
Sojourner, OS-keychain BYOK routes, no sign-in. `AFTERWORLDS_DEPLOYMENT=remote` is the hosted
deployment. Both modes are built by `create_app()`, mount every router and publish one OpenAPI
document; behavior is gated in dependencies, so generated contracts never diverge by mode.

### D2. Identity authority: Afterworlds' own identity service

No external identity vendor is selected (the prerequisite prescribes none and forbids signing up for
paid services). The remote identity authority is the `afterworlds.identity` service over the control
store:

- **Credentials:** contact address + password. The password verifier is stdlib `hashlib.scrypt`
  (n=2^14, r=8, p=1, 16-byte salt, 32-byte key); no new dependency.
- **Enrollment** requires proof of control of the contact address by a single-use verification
  code delivered through the notice transport. Registration responses are identical whether or not
  the address is already enrolled.
- **Sessions** are opaque 256-bit random tokens; only their SHA-256 verifier is stored. Cookies are
  `HttpOnly`, `SameSite=Strict`, `Secure` (configurable only for an explicitly local test server).
  Every sign-in issues a new token (no fixation); tokens are never refreshed in place. Ordinary
  sessions expire after 24 hours, staff sessions after 1 hour.
- **Revocation:** sign-out revokes the presented session server-side; recovery, closure and
  administrator revocation revoke every session of the principal, staff sessions included.
- **Recovery** proves control of the verified contact address with a 256-bit single-use code
  (15-minute expiry, 5 attempts), sets a new verifier and revokes all sessions. It refuses closed
  accounts, never changes ownership, provenance or the administrator binding. Account ID, email
  alone, support ticket, Story ID or an old session is insufficient. Staff-assisted recovery is not
  provided.
- **Closure** (self-service, password re-authentication) sets the account `closed`, revokes all
  sessions and denies every later request; account deletion/erasure remains CRD Issue 22's.
- **Notice transport:** a protocol with one implementation, a restricted operator outbox
  directory. Selecting a real email processor is an open launch gate (package contract
  "Processors and storage"); remote mode refuses to start without a configured transport.

- **Concurrency:** every identity transition that decides on stored state (registration, enrollment,
  sign-in session issuance, recovery, closure, staff revocation, bootstrap) runs under SQLite's write
  lock (`BEGIN IMMEDIATE`); scrypt runs outside it, and sign-in issues a session only if the verifier
  it proved is unchanged. An old-password sign-in racing recovery cannot mint a session, and a
  recovery code is consumed exactly once. Service methods that take an `Actor` revalidate its stored
  session (current, right context, binding active for staff); Actor fields are never trusted.

### D3. Sole Owner administrator and distinct staff context

The only path to staff authority is the server-side bootstrap command
(`python -m afterworlds.identity.bootstrap`), run by an operator with control-store access. It
re-authenticates the Owner principal by password and requires a verified contact address, records a
provisioning operation and an audit event, is idempotent for the same principal, and refuses any
other principal while an active binding exists. No HTTP route, registration field, profile field or
request parameter can create or select a binding.

Staff authority is a separate session context: a separate sign-in endpoint and cookie, rechecked
against the active binding on every request. `/api/admin/*` accepts only staff sessions; an ordinary
session — including the Owner's own — receives `403 staff_authority_required`, and a staff session
is not accepted on ordinary Sojourner routes. Administrative requests name their hosted target in
the path; the actor always comes from the session. Mutations record reason, actor and target in the
control-store audit stream. Staff authority includes neither local-device access nor BYOK key
disclosure.

### D4. Stable subject mapping

Every hosted account has a stable random `account_id`. In remote mode it **is** the entitlement
subject (`sojourner_id`) passed to `EntitlementService`; no new event type or parallel ledger exists.
`app.state.sojourner_id` is not set in remote mode, so a missed caller fails instead of silently
using a shared identity.

### D5. Stores

| Store | Mode | Holds |
|---|---|---|
| Content store (`AFTERWORLDS_DATABASE_URL`, SQLite, main Alembic chain) | both | Narrative, RPG, entitlement events, Retrieval markers, and — remote only — `account_resources` ownership rows and the `remote_store_marker`. |
| Control store (`AFTERWORLDS_CONTROL_DATABASE_URL`, SQLite, separate `alembic_control` chain) | remote | Accounts, principals/verifiers, sessions, verification/recovery operations, administrator binding, identity audit events, deletion suppressions, backup inventory, restore records. |
| Embedded Chroma (`AFTERWORLDS_RETRIEVAL_PERSIST_DIRECTORY`) | both | Story-memory chunks; shared Rules corpus. |
| Notice outbox (`AFTERWORLDS_NOTICE_OUTBOX_DIR`) | remote | Pending verification/recovery notices for the operator relay. |

Ownership rows live in the content store so a Story and its ownership commit in one transaction.
Identity, session, closure and suppression state live in the control store so restoring a content
snapshot can never revive a revoked session, reopen a closed account or resurrect a suppressed
Story. SQLite and embedded Chroma are retained (no networked database is mandated); their limits are
preserved by D6.

### D6. Topology: one writer process

Remote mode retains the single-uvicorn-worker envelope (Binding Decision 8). `create_app()` holds an
exclusive OS lock on the content store **and** on the bound vector store for the process lifetime
(released if startup is refused); a second app process, a storage command or the backfill job fails
while they are held. Per-Story turn locks, RPG lease recovery and entitlement idempotency are
therefore unchanged. Because the writer is one process, an in-process per-account fence
(`AccountFence`) orders effects against closure and suppression: every remote Sojourner request
holds its account's fence shared for its whole handler and revalidates its session under it;
closure (and CRD Issue 22 suppression) take it exclusive with a bounded wait, admitting no new
request meanwhile and changing nothing on timeout. No effect of an admitted request can land after
closure returns. Multiple workers, replicas or hosts remain unauthorized until a separately reviewed
shared-coordination contract exists (the fence would then need a shared equivalent).

### D7. Fresh remote stores and unknown ownership

A remote deployment initializes only an empty content store, or one already carrying the remote
marker that matches its control store. A store with a `sojourner_identity` row, Stories, entitlement
events or no matching marker is refused **before** migration. The vector directory is held to the
same rule: it must be absent/empty (then bound to the deployment by a marker file) or carry this
deployment's marker; an unmarked, foreign or missing vector store is refused untouched and never
adopted. A fresh deployment therefore starts without shared Rules Package data (SQL or vectors).
#205 provides no lock-aware path to provision it remotely, and the local corpus-baseline reset
refuses in remote mode (it would erase every account's Story memory); remote Rules provisioning is
an open activation dependency, so RPG authority is unavailable in a fresh remote deployment until
it is designed and reviewed. No import, claim or reassignment path exists. Rows without
an active ownership mapping are invisible and inaccessible. Account-wide enumeration survives parent
detachment through `account_resources`; Turn IDs are captured by the pre-detachment inventory seam
(`remote.inventory`), and no ordinary path detaches Story children.

### D8. Authorization

- An app-level dependency default-denies every `/api` route in remote mode except an explicit
  public allowlist (health, session status, enrollment, sign-in, recovery); `/api/admin/*` requires a
  staff session. Unsafe methods additionally require the `X-Afterworlds-Request` header, which a
  cross-site form cannot send and a cross-site script cannot send without a CORS preflight the app
  never grants (no CORS middleware).
- Every `/api/stories/{story_id}` route authorizes the actor against the ownership map before any
  read, mutation, provider call or vector operation; a foreign or unknown Story is the same `404`.
  Child identifiers (pending roll, sequence) are resolved only within the authorized Story.
- Remote effects run under a trusted `DelayedWorkScope` (account, Story, operation) carried in a
  context variable that `asyncio.to_thread`/anyio copy into worker threads. The orchestrator, RPG
  action and Retrieval Memory seams recheck it at each call: the scope's account must own the Story,
  be active, and the Story must be unsuppressed. A direct remote call with no scope, another
  account's scope or a mismatched entitlement subject is refused before the service runs.
- Delayed work carries the same explicit scope, rechecked at every write. The only delayed job today
  is `scripts/retrieval_backfill.py`; it runs inside both store locks, refuses a pending restore, and
  a closure or suppression mid-job stops its remaining writes. No product websocket,
  stream, upload/download, export artifact endpoint or account-scoped cache exists. Any later one
  inherits this boundary.

### D9. Local BYOK separation

In remote mode no credential store (keychain or environment) is constructed — the provider
resolver receives a store that holds nothing and refuses writes, so BYOK resolution below HTTP
access selection fails closed — and BYOK readiness is never probed: access-path selection treats BYOK as not runnable on the server. The local key-write,
validation and settings routes return `409 byok_local_only` before reading the body's key. The
account view reports `byok_readiness_source = "unavailable_remotely"` with only source-bound licence
state. Local installations are unchanged and need no account.

### D10. Restore and deletion fencing hooks

The control store accepts authoritative deletion-suppression instructions (the matrix's suppression
record) and keeps a backup inventory with original capture time, which copies and restores
preserve. Every maintenance step records its state before touching files:

- **Capture** refuses while a restore is pending or any suppressed content is still present in
  either store, inventories the backup (`unverified`, original capture time, the suppressions it
  proved absent) before copying, and marks it `verified` only after both stores are copied. Backup
  coverage is proof-based: a backup counts against a suppression unless its capture proved that
  content absent; capture time alone proves nothing.
- **Restore** checks the snapshot's bound vector store and entitlement-ledger continuity, records a
  `copying` restore before touching files (superseding any unfinished one), replaces both stores and
  only then marks it copied. The app refuses to start while any restore is unfinished, and
  verification refuses a restore whose copy did not finish — an absence of suppression targets is
  never evidence of a successful restore.
- **Verification** proves every active suppression holds (no `story_id`-bearing content row, zero
  story-memory chunks; an unavailable read fails).
- **Disposal** removes files, then records; a retry records a verifiably absent path, and an
  unverifiable one is marked `inaccessible`.

Suppressed Stories are also denied by the ownership guard at all times. CRD Issue 22 supplies the
operational suppression records and deletion orchestration; the prerequisite proves the hooks with a
disposable enforcer fixture.

## Consequences

- Local behavior, CRD Issue 21 proofs and their contracts are unchanged.
- Remote launch still needs: a real notice/email processor, actual host/backup configuration,
  abuse/rate protection for sign-in, the legal/financial applicability determination, CRD Issue 22
  fulfillment and CRD Issue 23 payments. These are recorded launch gates, not implemented claims.
- Account-closure erasure, export and suppression creation are CRD Issue 22 operations over these
  hooks.
- **A restore never silently rewinds the entitlement ledger.** `entitlement_event` is append-only
  accounting authority (ADR-013, Invariant 11) kept in the content store. `begin_restore` refuses,
  before anything is copied, unless the live ledger is a prefix of the snapshot's (same
  `global_sequence` order and event IDs); a missing or unreadable live store, a divergent ledger or
  any event recorded after capture refuses the restore. Nothing is carried forward, rebuilt or
  relocated — that would be new accounting semantics.
- **Open Owner decision (not resolved here):** "When a content restore cannot prove that the restored entitlement ledger contains every recorded event (the live store is lost, or events were recorded after capture), what authority and reconciliation accept the restored money/access state before hosted service resumes?" Every hosted turn records a credit
  deduction, so in practice this guard blocks production restore of an older snapshot until the
  question is answered. It touches CRD Issue 23's reconciliation ownership.
- `verify_restore` proves only that no content table with a `story_id` column holds a row for a
  suppressed Story and that its story-memory chunk count is zero. Turns orphaned by `SET NULL`, and
  per-class disposal, belong to CRD Issue 22's enforcer and its pre-detachment inventory.
