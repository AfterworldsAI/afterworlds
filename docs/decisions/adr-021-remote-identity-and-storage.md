# ADR-021 — Remote Identity, Account Ownership and Storage Boundary

**Date:** 2026-10-17
**Status:** Accepted authority; implementation delivered under prerequisite #205 (Owner review, merge
and remote activation pending)
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
exclusive OS lock on the content store for the process lifetime; a second app process, or the
restore command while the app runs, fails to start. Per-Story turn locks, RPG lease recovery and
entitlement idempotency are therefore unchanged. Multiple workers, replicas or hosts remain
unauthorized until a separately reviewed shared-coordination contract exists.

### D7. Fresh remote stores and unknown ownership

A remote deployment initializes only an empty content store, or one already carrying the remote
marker that matches its control store. A store with a `sojourner_identity` row, Stories, entitlement
events or no matching marker is refused **before** migration. No import, claim or reassignment
path exists. Rows without an active ownership mapping are invisible and inaccessible.

### D8. Authorization

- An app-level dependency default-denies every `/api` route in remote mode except an explicit
  public allowlist (health, session status, enrollment, sign-in, recovery); `/api/admin/*` requires a
  staff session. Unsafe methods additionally require the `X-Afterworlds-Request` header, which a
  cross-site form cannot send and a cross-site script cannot send without a CORS preflight the app
  never grants (no CORS middleware).
- Every `/api/stories/{story_id}` route authorizes the actor against the ownership map before any
  read, mutation, provider call or vector operation; a foreign or unknown Story is the same `404`.
  Child identifiers (pending roll, sequence) are resolved only within the authorized Story.
- Retrieval Memory reads, writes, reindex and delete pass through an ownership guard that refuses a
  Story without an active mapping to an active account, or under suppression, before the existing
  `story_id` filter.
- Delayed work carries an explicit `DelayedWorkScope` (account, Story, operation) rechecked when it
  executes. The only delayed job today is `scripts/retrieval_backfill.py`; no product websocket,
  stream, upload/download, export artifact endpoint or account-scoped cache exists. Any later one
  inherits this boundary.

### D9. Local BYOK separation

In remote mode no credential store (keychain or environment) is constructed and BYOK readiness is
never probed: access-path selection treats BYOK as not runnable on the server. The local key-write,
validation and settings routes return `409 byok_local_only` before reading the body's key. The
account view reports `byok_readiness_source = "unavailable_remotely"` with only source-bound licence
state. Local installations are unchanged and need no account.

### D10. Restore and deletion fencing hooks

The control store accepts authoritative deletion-suppression instructions (the matrix's suppression
record) and keeps a backup inventory with original capture time, which copies and restores
preserve. A restore is recorded as pending; the app refuses to start until every active suppression
has been enforced against the restored content and Chroma stores and verified (no suppressed Story
row, zero story-memory chunks). Suppressed Stories are also denied by the ownership guard at all
times. CRD Issue 22 supplies the operational suppression records and deletion orchestration; the
prerequisite proves the hooks with a disposable enforcer fixture.

## Consequences

- Local behavior, CRD Issue 21 proofs and their contracts are unchanged.
- Remote launch still needs: a real notice/email processor, actual host/backup configuration,
  abuse/rate protection for sign-in, the legal/financial applicability determination, CRD Issue 22
  fulfillment and CRD Issue 23 payments. These are recorded launch gates, not implemented claims.
- Account-closure erasure, export and suppression creation are CRD Issue 22 operations over these
  hooks.
