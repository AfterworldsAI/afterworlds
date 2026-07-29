# CLAUDE.md

Read this file fully at the start of every Claude Code session before taking action.

## Project and Authority

Afterworlds is an interactive storytelling platform built on the Sojourn Story State Machine. Users are **Sojourners**. Modes are RPG, Branching, and Writing.

Implement the governing CRD issue against repository reality. Apply authority in this order:

1. The governing CRD issue and recorded Owner Decisions.
2. Accepted ADRs in `/docs/decisions/`.
3. Architecture and Known Unknowns in `/docs/architecture/`.
4. Prompt contracts in `/docs/prompts/`.
5. This file and other standing repository guidance.

Source code and tests are evidence of the current implementation, not authority to redefine an accepted contract. If authorities conflict or implementation would deviate from them, surface the conflict in Architecture Notes; do not resolve drift silently.

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

Run applicable gates on the exact branch head before pushing. If blocked, say what could not run.

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

## Engineering Discretion

You own ordinary engineering choices, including investigation order, algorithms, internal organization, helper boundaries, tool use, test organization, and commit decomposition. Choose the lowest-complexity repository-native approach that satisfies the governing contract.

Use Graphify, subagents, advisor consultation, invariant cards, context compaction, and phased delivery when they materially improve the work. They are not required unless the governing issue or an accepted ADR explicitly requires them. Read `AGENTS.md` when performing or responding to PR review; it is not mandatory startup reading for ordinary implementation.

Issue- and ADR-specific requirements remain authoritative. This standing guidance does not retroactively remove procedures explicitly required by accepted work already in progress.

Before handoff:

* verify the requested observable behavior and required failure cases;
* verify production entry points and downstream consumers affected by the change;
* run the applicable repository gates on the final branch head;
* report acceptance coverage, test evidence, and any unresolved boundary.

## Boundary, Sibling Audit, and Known Unknown Rules

See `/docs/architecture/known_unknowns.md`. If implementation touches a listed unknown, stop and flag it; do not decide it in code. Surface product semantics, ownership changes, specification contradictions, and materially different architectures rather than deciding them as ordinary implementation details. If a better architecture contradicts the accepted specification or ADR, reconcile the authority in the same PR or obtain an Owner Decision before implementing it.

Trigger a boundary check when repeated review/fix rounds hit the same file, function, query, schema, service hotspot, or invariant, or when feedback shifts from defects to ownership, semantics, placement, issue scope, or architecture.

When triggered:

1. Stop treating the latest comment as automatically the next patch.
2. Classify remaining work: merge-blocking defect, scope boundary, Known Unknown, Owner Decision, or non-blocking improvement.
3. Surface the boundary in PR comments or Architecture Notes.
4. Resume remediation only after boundary or owner residue is resolved or explicitly deferred.

Codex comments are symptoms. Classify the defect family before fixing the quoted line. Run a bounded sibling audit only when two or more review rounds hit the same defect family, hotspot, or invariant, or when a narrow fix is followed by a sibling defect that should have been checked with it.

A sibling-audit note may be a PR comment, handoff note, or implementation note. Name the defect family, trigger, representative sibling structures inspected, regression coverage, and each disposition: `patched`, `already safe`, `out of scope`, `Known Unknown`, or `owner decision needed`.

This audit controls scope; it does not expand it. Do not silently fix `out of scope`, `Known Unknown`, or `owner decision needed` items.

## Repository and PR Rules

* Work on a topic branch; no direct commits to `main`.
* Open a PR for every CRD issue; do not merge without passing CI and Codex review.
* PR descriptions must include what was built, acceptance-criteria coverage, test evidence, and **Architecture Notes**.
* Architecture Notes must say either `No drift from design principles` or describe the deviation and rationale explicitly.
* Use conventional commit prefixes: `feat`, `fix`, `refactor`, `test`, `docs`, or `chore`.
* Use `CRD Issue N` for construction issues and `#N` for GitHub issues/PRs. Never use bare `Issue N`.

## Business and Access Invariants

There is one canonical Sojourn orchestration path across paying access paths. No commercial tier may remove core continuity functions or the safety envelope.

* Hosted access uses included credits plus transparent top-ups. Exhaustion stops or prompts; it never silently degrades quality or drops passes.
* BYOK perpetual license preserves full pipeline parity. BYOK is a first-class path, not a fallback or reduced-function mode.
* Cloud Services are separable from perpetual license rights. Lapse may gate hosted storage/sync/backup/remote access/hosted ingestion, but not owned-work read/export/download.
* Starter Access, if offered, is paid entry access using the same full pipeline and normal hosted credits. It is not a degraded free tier.
* Extended TTL caching is required wherever provider support and adapter verification allow it; cache correctness belongs to provider adapters.
* Entitlement routing governs access path, credits, Cloud Services, and settlement. Provider routing governs model/provider choice. Do not conflate them.
* No dark patterns in top-up, renewal, cancellation, export, or data retention.
