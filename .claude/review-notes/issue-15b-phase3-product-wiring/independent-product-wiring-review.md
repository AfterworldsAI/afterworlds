# CRD Issue 15b Phase 3 independent product-wiring consultation

Codex commissioned a separate read-only Claude Code consultation before finalizing the whole
candidate, satisfying #127's product-wiring consultation requirement. This is review evidence,
not Owner acceptance or new design authority.

- Session: `30b897c4-7385-4721-8176-13fe2a7094fd`, Claude Opus 5.5, high effort.
- Started: 2026-10-15 05:09:37 UTC; completed successfully at approximately 05:13 UTC, exit 0.
- Tools restricted to Read, Glob and Grep, with an empty strict MCP configuration. No commands,
  source changes or tests were performed by the advisor.
- Evidence root: `D:\AI\Claude\scratch\AW docs\issue15b-resumption\`.
- Actual public report: `CODEX-PHASE3-INDEPENDENT-ADVISOR-REPORT.md`.
- Invocation and eleven initial production-file hashes: `phase3-advisor-run/launch.json`.
- Applicability receipt: `phase3-advisor-source-check.json`; all eleven hashes matched at collection.

**Verdict: no concrete blocking concern found.** The advisor inspected single-service construction,
thin delegation, story scoping, the shared story guard, canonical-node resolution, access and
settlement, completed replay after access loss, fixed typed error translation, public/generated
DTOs, client resume/refetch behavior and the twelve-file split gate. Codex independently reviewed
these seams and retained final judgment. The consultation did not repeat Phase 2's mechanics review.

Non-blocking observations and dispositions:

- The product's current-interaction scoping makes consumed/non-player-visible pending-roll
  errors service-level codes. A lost-reply roll retry gets a scoped not-found response and refetch.
  This fits the accepted no-replay-ledger boundary; no new replay behavior was added.
- An unresolved resume without an access path remains access-blocked; its ready facts are preserved.
  Completed replay has the separate accepted success-equivalent classification.
- Minimal client controls submit physical raw faces. Aggregate/inline submissions are supported by
  the API; the full dice tray and browser dice remain CRD Issue 19b. IC blocking stays authoritative
  on the server, while the text input remains available for OOC.
- Abandoned sequences can hold rule changes and adoption indefinitely. The candidate surfaces the
  existing Known Unknown and implements no cancellation or expiration policy.
- The in-process guard reuses existing semantics; cross-process integrity remains the unchanged
  Phase 2 revision checks and RPG turn hold.

The advisor ran no tests and made no CI/coverage claim. Required test and exact-head CI evidence is
separate. Earlier engineer statements about two consultations are not supported by invocation
evidence and are not relied upon; this receipt identifies the actual independent consultation.
