# CLAUDE.md

Read this file fully at the start of every Claude Code session before taking action.

## Project

Afterworlds is an interactive storytelling platform built on the Sojourn Story State Machine. Users are **Sojourners**. Modes are RPG, Branching, and Writing. Authoritative sources live in `/docs/architecture/`, `/docs/decisions/`, and `/docs/prompts/`. The CRD issue spec governs the current task. If implementation would deviate from these sources, flag it in Architecture Notes; do not resolve drift silently.

## Stack and Local Gates

* Python 3.12 only. Use standard `pip` + `virtualenv`; do not introduce Poetry, PDM, uv, or another dependency manager.
* Black, Ruff, mypy strict, pytest, pip-audit, and detect-secrets are required.
* Minimum coverage on new code: 80% unless the issue specifies otherwise.

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -e ".[dev]"
black src/ tests/
ruff check src/ tests/
mypy src/
pytest -q
pip-audit
```

Run gates on the exact branch head before pushing. If blocked, say what could not run.

## Architecture Invariants

These are non-negotiable. Violations must be surfaced, not quietly patched.

1. Story Bible is structured narrative canon, never prose history.
2. Memory layers stay distinct: Immediate, Rolling Summary, Story Bible, Rules Package, Retrieval Memory, Contradiction Checker.
3. Intent is classified before context assembly.
4. Core narrative path: Planner -> Writer -> Extractor -> Contradiction.
5. Safety is an envelope: Input Preflight before Planner/Writer when required; Output Audit after Writer and before Extractor/Contradiction when required. Provider refusals are typed pass failures, not Safety verdicts.
6. Extractor proposes canon updates through approved service paths; it does not bypass the Story Bible service or write canon directly.
7. Stable prefix is assembled once per turn and reused across provider-backed passes. Rebuilding it per pass is an architectural violation.
8. Rules Package is mechanical canon; Story Bible is narrative canon. Do not cross their persistence or authority models.
9. RPG character sheets are first-class, ruleset-specific persistent objects. Rules meaning belongs to the active Rules Package and adjudication layer.
10. Deterministic/trust-relevant RPG rails are code-owned where specified: dice generation, hidden/backend-visible rolls, roll-result preservation, and `gm_cheating = off` enforcement.
11. Operational state affecting money, access, user data, or auditability must be reconstructable from explicit event logs, not inferred from opaque state.
12. Scope creep and Known Unknowns must be surfaced, not silently resolved.

## Context Discipline

Claude Code context is a build resource. Do not waste it on raw archaeology.

* Use `/context` before large implementation phases. Note major context costs.
* Do not dump broad docs, Graphify output, or large source sweeps into the main implementation thread when a subagent can summarize them.
* Use subagents for reconnaissance: architecture-doc reading, source seam discovery, Graphify orientation, sibling-structure audits, and review triage.
* Keep the main implementation context focused on the issue spec, invariant card, accepted plan, target files, failing tests, and current diff.
* Consult `/advisor` after briefing and planning, not after raw doc ingestion. Advisor is for judgment forks; subagents are for context isolation.
* Prefer manual `/compact` or `/clear` at phase boundaries. Do not wait for auto-compact to fire mid-edit.
* For large issues, use fresh phases rather than one long invariant-heavy pass.

## Compact Instructions

When compacting, preserve these items exactly:

1. CRD issue number, GitHub issue/PR number, branch, and implementation phase.
2. In-scope and out-of-scope boundaries.
3. Owner decisions, ADR decisions, and Known Unknowns touched by the work.
4. Narrow issue-specific invariants; do not replace them with vague summaries.
5. Exact service, DTO, enum, migration, prompt, and test names changed.
6. Files changed and why each file changed.
7. Test commands run and results.
8. Current failing tests, reviewer comments, and unresolved boundary questions.
9. Architecture Notes content that must appear in the PR.

## Graphify Preflight

Use Graphify before non-trivial implementation or review when available. It is an orientation aid only, not an authority and not a runtime dependency.

1. Read governing instructions and the issue/PR first.
2. Refresh or query the graph before broad file inspection.
3. Use narrow, task-specific queries for files, services, models, tests, callers, and ownership seams.
4. Verify Graphify output against source, tests, issue specs, ADRs, and docs.
5. If blocked, request approval/escalation once. If still unavailable, state that and continue with normal source inspection.

```powershell
cd D:\AI\Claude\afterworlds\src
graphify .
graphify cluster-only D:\AI\Claude\afterworlds\src
graphify query "Describe the files, services, models, tests, and ownership seams relevant to this task."
```

## Implementation Workflow

For small fixes, work directly and keep the diff tight. For non-trivial CRD issues, use this sequence:

1. Read `CLAUDE.md`, `AGENTS.md`, the issue spec, relevant ADRs, and Known Unknowns.
2. Run Graphify/subagent briefing before broad manual spelunking.
3. Produce an invariant card: scope, seams, affected services, tests, risks.
4. Make an implementation plan and consult advisor when the issue involves architecture, ownership, routing, entitlement, safety, orchestration, RPG adjudication, migrations, or a Known Unknown.
5. Implement in phases. End each phase with gates, `git diff --stat`, and `git status`.
6. Commit coherent phases with conventional commits.
7. Before PR handoff, verify tests, Architecture Notes, acceptance criteria, and no unrelated drift.

## Repository and PR Rules

* Feature branches: `feature/issue-N-short-description`; no direct commits to `main`.
* Open a PR for every issue; do not merge without passing CI and Codex review.
* PR description must include what was built, acceptance criteria coverage, test coverage summary, and **Architecture Notes**.
* Architecture Notes must say either `No drift from design principles` or describe the deviation/rationale explicitly.
* Conventional commits only: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.
* Use `CRD Issue N` for construction issues and `#N` for GitHub issues/PRs. Never use bare `Issue N`.

## Boundary, Sibling Audit, and Known Unknown Rules

See `/docs/architecture/known_unknowns.md`. If implementation touches a listed unknown, stop and flag it; do not decide it in code. Codex comments are symptoms: classify the defect family, then check sibling structures before handing fixes back.

Trigger a boundary check when repeated review/fix rounds hit the same file, function, query, schema, service hotspot, invariant, or feedback shifts from defects to ownership, semantics, placement, issue scope, or a materially better architecture than the spec.

When triggered:

1. Stop treating the latest comment as automatically the next patch.
2. Classify remaining work: merge-blocking defect, scope boundary, Known Unknown, owner decision needed, or non-blocking improvement.
3. Surface the boundary in PR comments or Architecture Notes.
4. Wait for owner decision when ownership, scope, or Known Unknowns are involved.

A sibling-audit gate is required when two or more review rounds on the same PR hit the same defect family, hotspot, or invariant, or when a narrow fix is followed by a sibling defect that should have been checked with it. Do not produce more one-off patches until the owner accepts or waives a short sibling-audit note.

The sibling-audit note may be a PR comment, handoff note, or implementation note. It must name: defect family; triggering review comments/rounds; searched sibling paths/functions; and each sibling disposition: `patched`, `already safe`, `out of scope`, `Known Unknown`, or `owner decision needed`.

This gate controls scope; it does not expand it. Classify siblings before continuing. Do not silently fix `out of scope`, `Known Unknown`, or `owner decision needed` items without owner approval.

## Business and Access Invariants

There is one canonical Sojourn orchestration path across paying access paths. No commercial tier may remove core continuity functions or the safety envelope.

* Hosted access uses included credits plus transparent top-ups. Exhaustion stops or prompts; it never silently degrades quality or drops passes.
* BYOK perpetual license preserves full pipeline parity. BYOK is a first-class path, not a fallback or reduced-function mode.
* Cloud Services are separable from perpetual license rights. Lapse may gate hosted storage/sync/backup/remote access/hosted ingestion, but not owned-work read/export/download.
* Starter Access, if offered, is paid entry access using the same full pipeline and normal hosted credits. It is not a degraded free tier.
* Extended TTL caching is required wherever provider support and adapter verification allow it; cache correctness belongs to provider adapters.
* Entitlement routing governs access path, credits, Cloud Services, and settlement. Provider routing governs model/provider choice. Do not conflate.
* No dark patterns in top-up, renewal, cancellation, export, or data retention.

## Lessons and Self-Improvement

After each task, append dated one-line lessons when corrected, an assumption fails, a pattern is discovered, or a better approach should persist. Format: `[YYYY-MM-DD] <lesson learned>`. Avoid duplicates. Preserve unless superseded:

* [2026-04-02] Run the full local gate sequence on the exact branch head before pushing; a green formatter alone does not mean CI-clean.
* [2026-04-02] When CI reports a file, verify the fix is staged, committed, and pushed by checking `git diff`, `git status`, and commit contents.
* [2026-04-02] Pin Black exactly in dev dependencies to reduce CI/local drift, but prove drift before blaming it.
* [2026-04-07] CRD issue numbers and GitHub issue/PR numbers are different namespaces; always write `CRD Issue N` or `#N`.
* [2026-07-28] An operator-facing configuration name (env var, flag, path) is only correct if a test reads it through the same code the operator's command runs; documenting one name while `from_env()` reads another is invisible to every unit test that sets the name itself.
* [2026-07-28] When a `try` block owns cross-store compensation, the boundary must open before the *first* mutation of the transactional store, and each compensating action must be armed only across the window in which its resource can exist.

<!-- Claude Code appends dated one-line lessons here as they are learned -->
