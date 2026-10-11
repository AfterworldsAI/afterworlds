# CRD Issue 2b — implementation status

**State: implementation in progress. Not review-ready.** Branch `codex/issue2b-character-state`, base `c90a690`.

## Done

- G1 successor natively recorded from the real Owner receipt (commit `dca4af3`). Successor `srd-5-2-1-corpus-8781d4e0-a3b-g1.json`, SHA-256 `2ccbaeba6de75d9787fbdd407e42dc2425fa20d4d26bcc298b681b550bd11258`. Proposal `8a8a737b…5345`, oracle `3e7b27db…`, projection `efab27a9…` unchanged from the reviewed preview. The prior `def7caa1…` is kept byte-for-byte and superseded by digest. Codex checked the recording independently. There is no recording blocker.
- Typed character and creature state, persistence, binding, adoption, shared-change hold, holdings, consumer integration and retirement (commit `10b621a`). Traceability is in `docs/architecture/issue-2b-character-state.md`.
- An in-play character that is not ready fails the turn typed (commit `03ae863`).

## In progress: Codex's first consolidated findings (implementation-review-1)

Order: 7 (adapter check shape), 6 (display), 4 (poison), 1 (lease liveness), 2+3 (typed selections and state parameters), 5 (item authority). Then Advisor items: adoption takes the write lock first, and the shared-change trial runs effective application.

## Remaining after that

Full CI-equivalent gates on the exact head, the three Codex probes run as written, the PR body and a draft PR.

## Advisor contribution

- Hold design: a lease plus activation that takes the write lock first.
- Adoption semantics: held, then revalidated fresh, with no substitution.
- The readiness gate.
- For the review-1 findings:
  - Leases: per-owner OS-lock liveness rather than a store lock.
  - Selections: one typed selection union reused for effect parameters.
  - HP: no reduced-maximum bound.
  - Adapter: validate every proposal before any dice are rolled.
  - The OOC path stays binding-enforcing.
