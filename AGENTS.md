# AGENTS.md

Read this file fully before reviewing an Afterworlds PR.

## Role

Review as Codex/review agent, not as primary implementer. Your job is to find correctness, security, maintainability, test, scope, and architecture problems before merge. Prefer high-signal findings over nitpicks.

The authoritative sources are:

1. Current PR diff and tests.
2. The governing CRD issue spec.
3. ADRs in `/docs/decisions/`.
4. `/docs/architecture/construction_readiness.md`.
5. `/docs/architecture/design.md`.
6. `/docs/architecture/known_unknowns.md`.
7. Prompt contracts in `/docs/prompts/`.
8. `CLAUDE.md` and this file.

Do not review from memory when the issue, ADR, or changed code gives the answer.

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

## Context-Process Review

For non-trivial PRs, verify that the implementation process did not create context-degradation risk.

Look for PR evidence that Claude Code:

* used a briefing subagent or equivalent summarized reconnaissance for broad docs/source/Graphify reading;
* kept the main implementation context focused on issue spec, invariant card, plan, target files, failing tests, and current diff;
* consulted advisor after briefing/planning when architecture, ownership, safety, entitlement, provider routing, RPG adjudication, migrations, or Known Unknowns were involved;
* used phase commits or coherent phase boundaries for large issues;
* ran local gates on the final branch head;
* recorded unresolved process or boundary issues in Architecture Notes.

Absence of this evidence is not automatically merge-blocking for small PRs. For large invariant-heavy issues, missing process evidence is review-relevant because it increases the chance of quiet spec drift. Ask for a short clarification before turning process opacity into a blocking finding.

## Graphify Review Preflight

Before reviewing a non-trivial PR, use Graphify when available.

Graphify is a review aid only. It is not an architectural authority and never replaces source, tests, issue specs, ADRs, `AGENTS.md`, `CLAUDE.md`, or architecture docs.

Required sequence:

1. Read `AGENTS.md`, the PR description, and the diff first.
2. Query Graphify before broad manual spelunking.
3. Use narrow review-specific queries for changed-file impact, ownership seams, downstream callers, related tests, and likely sibling defects.
4. Verify Graphify output against source, tests, issue specs, and docs before writing findings.
5. If blocked by sandbox, request approval/escalation once. If still unavailable, stale, or failing, state that and continue normal review.

```powershell
cd D:\AI\Claude\afterworlds\src
graphify query "Summarize changed-file impact, ownership seams, downstream callers, related tests, and architecture risks for this PR."
```

## Review Method

Use this order for substantive reviews:

1. Identify the governing CRD issue and PR scope.
2. Read Architecture Notes and compare them to the diff.
3. Check new/changed migrations, schemas, DTOs, enums, and service interfaces.
4. Check transaction and rollback behavior before style issues.
5. Check tests against acceptance criteria and likely failure modes.
6. Audit sibling structures when one defect suggests a pattern.
7. Classify each finding before commenting.

Finding classes:

* `P0` — unsafe to merge; breaks core functionality, data integrity, security, billing/access, or product safety.
* `P1` — merge-blocking correctness or architecture defect.
* `P2` — should fix before merge unless owner accepts risk.
* `P3` — non-blocking improvement or cleanup.
* `[OWNER DECISION]` — requires owner judgment on scope, semantics, policy, or ownership before code should change.

Do not inflate severity because a comment is interesting.

## Boundary-over-Patch Rule

Distinguish concrete defects from boundary problems.

Trigger this check when:

* the same PR receives repeated review/fix/re-review cycles;
* the same file, function, query path, schema hotspot, or service hotspot is revised across multiple rounds;
* feedback shifts from defects to semantics, ownership, architecture placement, or which issue owns behavior;
* a proposed fix would move behavior into an issue that does not clearly own it;
* the implementation appears to resolve a Known Unknown without owner approval.

When triggered:

1. Stop treating the latest review comment as automatically the next patch.
2. Classify remaining feedback as merge-blocking defect, scope boundary, Known Unknown, owner decision needed, or non-blocking improvement.
3. Surface the boundary explicitly in PR comments or Architecture Notes.
4. Use `[OWNER DECISION]:` for ownership/scope/policy questions.
5. Defer implementation until the owner narrows scope, defers behavior, or defines the missing rule.

Repeated hotspot churn is a coordination signal, not just a coding task.

## Recurring Defect Family Gate

Codex comments are symptoms. First classify the defect family, then check sibling structures before handing fixes to Claude.

A formal sibling audit is not required for every isolated comment. The gate applies only after recurrence:

* the same defect family appears in two or more review rounds;
* the same hotspot file/function/service/DTO/validator/test seam is implicated again;
* the same invariant is violated in multiple places;
* a narrow fix is followed by a sibling defect that should have been checked with it.

When the gate triggers, stop the narrow patch/re-review loop until Claude produces a short sibling-audit note and the owner accepts it or explicitly waives it.

The note must identify:

1. defect family;
2. triggering review comments or rounds;
3. sibling paths, functions, services, DTOs, validators, tests, prompts, or transaction seams searched;
4. disposition for each sibling, using only `patched`, `already safe`, `out of scope`, `Known Unknown`, or `owner decision needed`.

The audit should be lightweight: a PR comment, handoff note, or implementation note is enough. Do not turn the PR body into a remediation diary.

This gate controls scope; it does not expand it. A sibling marked `out of scope`, `Known Unknown`, or `owner decision needed` must not be silently fixed as part of the current PR unless the owner explicitly authorizes that expansion.

When recurrence is concrete and in scope, request one bundled sibling fix. When it shifts into semantics, ownership, architecture placement, or issue boundary, switch to `[OWNER DECISION]:`.

Examples of recurring defect families include fail-open fallback paths, stale metadata authority, missing corrective notes, usage preservation gaps, parser/selection grammar inconsistencies, nondeterministic ordering, missing tie-breakers, rollback gaps, and inconsistent equivalent inputs.

## Comment Rules

* Prefix design, architectural, ethical, policy, scope, or ownership judgments with `[OWNER DECISION]:`.
* Keep ordinary defect comments concrete: observed problem, consequence, and expected correction.
* Cite the changed file/function when possible.
* Avoid style-only comments unless they obscure correctness or maintainability.
* Do not ask for broad refactors outside issue scope.
* Do not suggest resolving Known Unknowns in code.
* If the PR discovers a better architecture than the spec, require ADR/spec revision in the same PR or owner-approved follow-up before merge.

## Tests and CI

Check that tests cover the issue’s required behavior, not merely the happy path.

Call out missing tests for:

* acceptance criteria;
* migration round trips and DB constraints;
* transaction rollback / savepoint behavior;
* typed parser failures and provider refusal paths;
* cache-boundary/stable-prefix identity;
* entitlement settlement and event replay;
* safety/contradiction blocking behavior;
* RPG dice/adjudication invariants;
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
* which issue/ADR/owner decision authorizes it;
* what remains deferred or risky.

If the diff and Architecture Notes disagree, review the disagreement, not just the code. That is usually where the skeleton is politely wearing a hat.

## Terminology

* Use `CRD Issue N` for construction issue references.
* Use `#N` for GitHub issues and PRs.
* Never use bare `Issue N`.
* Use Sojourner, Story Bible, Rules Package, Rules System Adapter, Character Sheet Model, and Mentor/Peer exactly as defined in the architecture docs.
