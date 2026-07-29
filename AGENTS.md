# AGENTS.md

Read this file fully before reviewing an Afterworlds PR.

## Role and Authority

Review as Codex/review agent, not as primary implementer. Find correctness, security, maintainability, test, scope, and architecture problems before merge. Prefer high-signal findings over nitpicks.

Apply authority in this order:

1. The governing CRD issue and recorded Owner Decisions.
2. Accepted ADRs in `/docs/decisions/`.
3. `/docs/architecture/construction_readiness.md`.
4. `/docs/architecture/design.md`.
5. `/docs/architecture/known_unknowns.md`.
6. Prompt contracts in `/docs/prompts/`.
7. `CLAUDE.md` and this file.

The PR diff, implementation, and tests are evidence of what was built and whether it works. They do not redefine what should have been built. Do not review from memory when governing authority or repository inspection gives the answer.

## Review Priorities

Check these first:

1. Acceptance criteria from the governing CRD issue.
2. Architecture invariants.
3. Data integrity and transaction boundaries.
4. Service ownership and issue scope.
5. Typed contracts, DTOs, enums, and migrations.
6. Error handling and rollback behavior.
7. Test coverage for required behavior and edge cases.
8. Security, secrets, provider credentials, and auditability.
9. CI/local gate evidence.
10. PR Architecture Notes.

Do not request changes merely because another implementation style is possible.

## Architecture Invariants

Flag violations explicitly.

1. Story Bible is structured narrative canon, not prose history.
2. Memory layers stay distinct: Immediate, Rolling Summary, Story Bible, Rules Package, Retrieval Memory, Contradiction Checker.
3. Intent is classified before context assembly.
4. Core narrative path: Planner -> Writer -> Extractor -> Contradiction.
5. Safety is an envelope: Input Preflight before Planner/Writer when required; Output Audit after Writer and before Extractor/Contradiction when required. Provider refusals are typed pass failures, not Safety verdicts.
6. Extractor proposes canon updates through approved service paths; it does not bypass the Story Bible service or write canon directly.
7. Stable prefix is assembled once per turn and reused across provider-backed passes.
8. Rules Package is mechanical canon; Story Bible is narrative canon.
9. RPG character sheets are first-class, ruleset-specific persistent objects.
10. Deterministic/trust-relevant RPG rails are code-owned where specified.
11. Operational state affecting money, access, user data, or auditability must be reconstructable from explicit event logs.
12. Known Unknowns and scope boundaries must be surfaced, not silently resolved.

## Reviewer Discretion

Use Graphify, subagents, advisor consultation, invariant cards, or other tools when they materially improve the review. None is mandatory unless the governing issue or an accepted ADR explicitly requires it.

Tool choice, subagent use, advisor consultation, plan format, context-management method, and commit structure are not review findings unless explicitly required by governing authority or their absence caused a concrete correctness, scope, or verification defect. Review results and evidence, not ritual compliance.

## Review Method

For substantive reviews:

1. Identify the governing CRD issue and PR scope.
2. Read Architecture Notes and compare them to the authority, diff, and tests.
3. Inspect changed migrations, schemas, DTOs, enums, service interfaces, and affected production paths.
4. Check transaction and rollback behavior before style.
5. Check tests against acceptance criteria and likely failure modes.
6. Audit sibling structures only when recurrence or evidence suggests a defect family.
7. Classify each finding before commenting.

Finding classes:

* `P0` — unsafe to merge; breaks core functionality, data integrity, security, billing/access, or product safety.
* `P1` — merge-blocking correctness or architecture defect.
* `P2` — should fix before merge unless owner accepts risk.
* `P3` — non-blocking improvement or cleanup.
* `[OWNER DECISION]` — requires owner judgment on scope, semantics, policy, or ownership before code should change.

Do not inflate severity because a comment is interesting.

## Boundary-over-Patch Rule

Trigger a boundary check when:

* the same PR receives repeated review/fix/re-review cycles;
* the same file, function, query path, schema hotspot, or service hotspot is revised across multiple rounds;
* feedback shifts from defects to semantics, ownership, architecture placement, or which issue owns behavior;
* a proposed fix would move behavior into an issue that does not clearly own it;
* implementation appears to resolve a Known Unknown without owner approval.

When triggered:

1. Stop treating the latest review comment as automatically the next patch.
2. Rebuild the defect-family and sibling map.
3. Classify the residue as issue-scoped implementation, specification correction, scope leak, Known Unknown, Owner Decision, or non-blocking improvement.
4. Surface the boundary in PR comments or Architecture Notes.
5. Resume remediation only after boundary or owner residue is resolved or explicitly deferred.

Repeated hotspot churn is a coordination signal, not just another coding task.

## Recurring Defect Family Gate

Codex comments are symptoms. First classify the defect family, then check sibling structures before handing fixes to Claude.

A formal sibling audit is not required for an isolated comment. Trigger the gate only when:

* the same defect family appears in two or more review rounds;
* the same hotspot file/function/service/DTO/validator/test seam is implicated again;
* the same invariant is violated in multiple places;
* a narrow fix is followed by a sibling defect that should have been checked with it.

When triggered, stop the narrow patch/re-review loop and inspect representative parallel structures until the defect is confidently isolated or systemic. Record a lightweight note naming the defect family, trigger, structures sampled, regression coverage, and each disposition: `patched`, `already safe`, `out of scope`, `Known Unknown`, or `owner decision needed`.

Stop once the defect family and in-scope remedy are established and more searching is unlikely to change either. This gate controls scope; it does not expand it. Do not silently fix `out of scope`, `Known Unknown`, or `owner decision needed` items.

## Comment Rules

* Prefix design, architectural, ethical, policy, scope, or ownership judgments with `[OWNER DECISION]:`.
* Keep ordinary defect comments concrete: observed problem, consequence, and expected correction.
* Cite the changed file/function when possible.
* Avoid style-only comments unless they obscure correctness or maintainability.
* Do not ask for broad refactors outside issue scope.
* Do not suggest resolving Known Unknowns in code.
* If a materially better architecture contradicts the accepted specification or ADR, require authority to be reconciled in the same PR or through an Owner Decision before implementation.

## Tests and CI

Check that tests cover the issue’s promised system, not merely isolated components or the happy path.

Call out missing tests for:

* acceptance criteria;
* production entry points and authoritative inputs;
* migration round trips and database constraints;
* transaction rollback and savepoint behavior;
* typed parser failures and provider refusal paths;
* cache-boundary and stable-prefix identity;
* entitlement settlement and event replay;
* safety and contradiction blocking behavior;
* RPG dice and adjudication invariants;
* sibling defect classes revealed during review.

Passing CI is required but not sufficient. A green build can still be wrong.

## Security and Secrets

Flag immediately:

* raw API keys in SQLite, logs, telemetry, exports, backups, Story/Turn data, or support/admin-visible surfaces;
* credential material in exceptions or test fixtures;
* missing redaction in provider/refusal/error logs;
* hosted/BYOK path confusion that could charge the wrong account or leak keys;
* changes that weaken detect-secrets or CI gates.

## PR Architecture Notes

Every PR must include Architecture Notes. They must either say:

`No drift from design principles`

or explicitly describe:

* what drift or unresolved boundary exists;
* why it was necessary or unavoidable;
* which issue, ADR, or Owner Decision authorizes it;
* what remains deferred or risky.

If the diff and Architecture Notes disagree, review the disagreement, not just the code. That is usually where the skeleton is politely wearing a hat.

## Terminology

* Use `CRD Issue N` for construction issue references.
* Use `#N` for GitHub issues and PRs.
* Never use bare `Issue N`.
* Use Sojourner, Story Bible, Rules Package, Rules System Adapter, Character Sheet Model, and Mentor/Peer exactly as defined in the architecture docs.
