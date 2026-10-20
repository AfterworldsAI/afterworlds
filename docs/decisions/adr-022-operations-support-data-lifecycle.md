# ADR-022 — Operations, Support and Data-Lifecycle Engineering Selections

**Date:** 2026-10-19
**Status:** Proposed — engineering selections under the accepted CRD Issue 22 #206 revision 7 and its
companion contracts, pending Codex review and Owner acceptance. Only #206, its companions and the
accepted #205 foundation are authority; where this ADR and a contract differ, the contract governs.
**Operations record and runbook:** [`crd-issue-22-operations.md`](../architecture/crd-issue-22-operations.md).

## Decisions

### D1. Operations store
CRD Issue 22's records (support events, data-request headers/transitions, inventories, phase progress,
receipts, export artifacts, receipt credentials, anomalies, expiry register, BYOK-rights evidence) share one
declarative base (`afterworlds.operations.orm`) and one frozen DDL (`operations.schema`). Remotely they live in
the **control store** (chain `c0002`), so a content restore cannot rewind a request, its inventory or a
receipt (ADR-021 D5); locally in the content store (chain `0046`), the local owner's only store. The remote
content store carries empty copies.

### D2. Guarded lifecycle exception
Every append-only table's DELETE trigger becomes "refuse unless a `lifecycle_disposal_grants` row names this
`rowid`"; UPDATE triggers are unchanged. Only `operations.lifecycle.dispose_rows` writes grants, inside the
deleting transaction, removing them before commit (a test enforces the single writer). This implements the
amendment's "reviewed lifecycle path" without disabling a trigger. Entitlement expiry removes a whole closed
subject (projection and every event) so no partial, wrongly-replaying ledger is left.

### D3. Support remediation
Credit adjustment is `requested` support event → stale check against `last_entitlement_event_id` →
`receive_entitlement_event(MANUAL_CREDIT_ADJUSTMENT)` with idempotency key
`crd22-support-adjustment:<operation_id>` → `committed` event. The status read reconciles a lost outcome from
the idempotency key. Deltas beyond four decimals are refused (the payload validator would otherwise round).

### D4. Request lifecycle and receipts
An immutable header plus append-only transitions with a per-request `revision` (unique), checked under
SQLite's write lock. Remote fulfillment is administrator-approved and administrator-executed; local
fulfillment is executed by the local owner. A remote account-deletion confirmation issues a one-time 256-bit
receipt credential (verifier stored) for the post-closure status route, a public path refusing every
mismatch identically.

### D5. Deletion execution
Inventory first (including Turns referenced from Story-scoped rows); suppression with the confirmation time
as boundary; vectors before ownership mappings; SQL through a registered FK-ordered disposal registry with an
independent verification sweep (a test fails when a Story- or Turn-bearing table is unregistered);
identity-owner erasure keeping only the `hosted_accounts` tombstone; phases recorded per attempt; final
completion only when physical compaction, backups and the commercial dependency are satisfied.

### D6. Physical disposal
Offline compaction with the store locks held: content `VACUUM`, and a vector rebuild whose import runs in a
fresh subprocess. Reason: on the pinned chromadb 1.5.9 a rebuild inside a process that had read deleted text
produced a new HNSW segment file containing that text (freed-memory bytes); the subprocess never held it.
The same effect means a process that ever read deleted text (the app that
served the Story, or a maintenance process that deleted chunks) must not write the vector store after
compaction: compaction runs with the app stopped, and the app is restarted afterwards in a fresh process.
Capture refuses while compaction is pending, because the SQLite backup API and directory copy carry free
pages and orphan segments. This is a narrow addition to #205's capture preconditions.

### D7. Anomalies
Computed from durable sources at read time (support stream, requests, replay check, restores) plus one new
durable signal: a delivered turn's settlement failure is recorded as an anomaly event by the turn routes
after the response is built (the turn stays delivered; nothing retried or charged).

## Consequences and recorded boundaries

- **Restore after ledger expiry (boundary, not resolved):** #205's `check_ledger_continuity` requires the live
  ledger to be a prefix of the snapshot's. Once a closed subject's events expire, restoring a backup captured
  before that expiry is refused. The rule is kept unchanged (no comparison filtering — that would be new
  reconciliation semantics); `enforce-restore` would re-expire such events if a restore were accepted under a
  future Owner decision. Backups live at most 21 days, so the window is narrow.
- **CRD Issue 23 dependency:** a hosted account with live subscription or Cloud Services references cannot
  reach final deletion completion until CRD Issue 23 supplies closure; the phase reads
  `dependency_unavailable`.
- **Offline maintenance:** physical compaction and restore enforcement need the app stopped (single-writer
  topology, ADR-021 D6).
- **Free text already in v1 entitlement payloads:** manual `reason` is bounded at creation; deactivation
  `detail` has no current producer and is never shown or exported.
