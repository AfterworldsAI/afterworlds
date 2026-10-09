# External synchronization note for #132 and #137 — draft, not published

**Draft only.** Nothing here has been posted. It is to be posted through the established publication workflow once the Owner authorizes publication. Live text was read read-only on 7 October 2026 and retrieved to `.claude/_sp/release-readiness-20261007/issue-132.json` and `issue-137.json`:

- #132 (CRD Issue 5c, SRD corpus integrity and reproducible full-corpus ingestion) is CLOSED.
- #137 (CRD Issue 5d, complete typed mechanical authority and deterministic Rules-Package binding) is OPEN.

Neither issue carries a restart banner for the 21 September 2026 restart.

## Proposed banner (both issues)

> **Restart status (21 September 2026 Owner Decision).** CRD Issue 5c and CRD Issue 5d are being delivered through the clean restart in `docs/architecture/issue-5c-5d-clean-restart.md`. Where this issue's historical forensic topology or inherited-product clauses conflict with that Decision, the Decision governs. The operational and practical-reliability amendments stay in force.
>
> **Current state (working tree, not yet published or active).**
> - The Owner accepted the release-order candidate (SHA-256 `8a6a9a9c…`).
> - It was recorded as release `5.2.1-corpus.8781d4e0-a3b`: oracle SHA-256 `def7caa1…`, with 24 batches, 1,835 records, 1,486 reference resolutions and representation schema 17.
> - Committed-authority resolution now refuses the superseded releases `5.2.1-corpus.3fe24ff6-4e3` and `5.2.1-corpus.574662e9-0ef`. Their files are kept as historical evidence.
> - A release-readiness correction (typing, fixture expectations, selector refusal and status prose) is awaiting Codex review and the final local gates.
>
> Dependency-vulnerability repairs remain deferred until the restart is complete. Nothing is published or active until the Owner authorizes it.

## Per issue

- **#132:** add the banner as a comment, not by editing the body. The closed state is not changed by this note. Whether to reopen it or to track remaining work elsewhere is for the Owner.
- **#137:** add the banner as a comment. Link the restart document and the PR once one exists.

## Constraints

- Use `CRD Issue N` and `#N` notation; never a bare "Issue N".
- No secrets, tokens or local absolute paths.
- Do not claim anything is merged, published or active until it is.
