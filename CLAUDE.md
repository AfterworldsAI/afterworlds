# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.
Read it fully at the start of every session before taking any action.

## Project

Afterworlds is an interactive storytelling platform built on the Sojourn Story
State Machine. It lets users inhabit and continue narrative worlds across three
modes: RPG, Branching, and Writing. The target users are called Sojourners.
This is a solo-developer project operated under AfterworldsAI, LLC.

The authoritative design documents are in /docs/architecture/. Read them before
making any architectural decision. If your implementation would deviate from
anything in those documents, flag it in your PR description — do not resolve it
silently.

## Language & Tooling

- **Language:** Python 3.12 only
- **Package management:** pip + virtualenv only — do not introduce Poetry, PDM,
  uv, or any alternative dependency manager
- **Testing:** pytest (minimum 80% coverage on new code)
- **Type checking:** mypy strict mode — zero tolerance
- **Formatting:** Black — zero tolerance
- **Linting:** Ruff — zero tolerance
- **Dependency scanning:** pip-audit (blocking CI gate)
- **Secret scanning:** detect-secrets (pre-commit hook)

## Build & Test Commands

```bash
# Create and activate virtualenv
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy src/

# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Dependency audit
pip-audit
```

## Architecture Principles — Non-Negotiable

These must not be violated. Any code that breaks them is an architectural
violation and must be flagged in the PR, not silently resolved.

1. Story Bible is structurally separate from prose history
2. Six memory layers have distinct roles: Immediate / Rolling Summary /
   Story Bible / Rules Package / Retrieval Memory / Contradiction Checker
3. Intent is classified before context is assembled
4. The Sojourn orchestration path is the **core narrative pipeline**
   (Planner → Writer → Extractor → Contradiction) wrapped by a **safety
   envelope** with conditional execution: Input Safety Preflight runs
   before Planner/Writer when orchestration policy requires it; Output
   Safety Audit runs after Writer and before Extractor/Contradiction when
   provider or risk policy requires it. Provider refusals during any
   provider-backed pass are typed pass failures, not Safety verdicts. The
   ordering is fixed; the safety calls are conditional, not unconditional
   terminal passes.
5. Extractor proposes canon updates — it does not write canon directly
6. Stable prompt prefix is assembled once per turn and shared across all
   passes for caching efficiency

## Repository & PR Rules

- Feature branches per issue: `feature/issue-N-short-description`
- No direct commits to main under any circumstances
- Open a PR for every issue; PRs are not merged without Codex review passing
- No PR merges with failing CI
- Every PR description must include an **Architecture Notes** section:
  either "No drift from design principles" or an explicit description of
  any deviation and rationale
- Scope creep is a review failure — stay within issue boundaries

## Graphify Preflight

Before starting non-trivial implementation work, use Graphify for codebase orientation when it is available in the local environment.

Graphify is a construction aid only. It is not an Afterworlds runtime dependency, not an architectural authority, and not a replacement for the issue spec, ADRs, `CLAUDE.md`, `AGENTS.md`, or architecture docs.

Required preflight for non-trivial implementation work:

1. Read the governing instructions and issue spec first.
2. Refresh or query the Graphify code graph before broad file inspection.
3. Use narrow, task-specific Graphify queries to identify likely files, services, models, tests, and ownership seams.
4. Verify all Graphify output against source files and authoritative docs before making changes.
5. If Graphify is blocked by the sandbox, request approval/escalation to run the Graphify preflight once. If Graphify is still unavailable, stale, or failing after that, state it explicitly and continue with normal source inspection.

Current local code-only Graphify workflow:

```powershell
cd D:\AI\Claude\afterworlds\src
graphify .
graphify cluster-only D:\AI\Claude\afterworlds\src
graphify query "Describe the files, services, models, tests, and ownership seams relevant to this task."
```

## Review-Loop Boundary Check

If repeated review rounds on the same PR begin focusing on the same file, function, 
query path, schema hotspot, or service hotspot, or if feedback shifts from concrete 
defects to questions of ownership, semantics, architectural placement, or which issue 
should own a behavior, treat that as a boundary problem rather than “the next patch.”

When this happens:

- Stop iterative fix/re-review cycling.
- Classify the remaining feedback as:
  - merge-blocking defect,
  - issue-scope boundary problem,
  - Known Unknown,
  - non-blocking improvement.
- Do not resolve boundary or ownership questions unilaterally in code.
- Raise the issue explicitly in the PR description or PR comments under
  **Architecture Notes**.
- Pause for owner decision when the implementation appears to cross issue
  scope, touch a Known Unknown, or require a new ownership rule.

Do not keep patching a hotspot indefinitely just because a reviewer produced
another comment. Repeated churn on the same hotspot is evidence that the PR may
have crossed its intended boundary.

## Commit Format

Conventional commits:  
`type(scope): description`

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Example: `feat(story-bible): implement tiered inclusion policy for events ledger`

## Known Unknowns — Do Not Resolve Silently

See `/docs/architecture/known_unknowns.md`. If implementation touches a listed
unknown, stop and flag it in the PR — do not resolve it unilaterally.

## Business Model Constraints — Architectural Invariants

There is **one canonical Sojourn orchestration path** — the core narrative
pipeline (Planner → Writer → Extractor → Contradiction) plus the safety
envelope (conditional Input Preflight and Output Audit) — across all paying
access paths. No commercial tier may remove core continuity functions or the
safety envelope. A degraded free-tier pipeline is not part of this product.

Access paths and their constraints:

- **Hosted Subscription:** metered subscription with included monthly credits +
  transparent top-ups. When credits are exhausted, the system stops or prompts
  for top-up — it never silently degrades output quality or drops pipeline
  passes.
- **BYOK Perpetual License:** permanent product rights with full pipeline
  parity. First year of Cloud Services included. BYOK is a first-class path —
  not a fallback or reduced-function mode.
- **BYOK Cloud Services Renewal:** optional annual renewal for ongoing hosted
  services (storage, sync, backup, remote access, ingestion processing). The
  perpetual license and the Cloud Services layer must not be collapsed in code
  or entitlement logic.
- **Starter Access (optional):** small paid entry package using the same full
  orchestration path and normal hosted credits. Not a free tier. Not a
  degraded path.

Additional invariants:

- Extended TTL caching must be enabled by default wherever the provider
  supports it — this is an economic requirement, not a preference
- Stable prompt prefix is assembled once per turn and shared across all passes
  — rebuilding it per pass is an architectural violation
- Entitlement routing governs billing path, credit balance, Cloud Services
  status, and storage/ingestion entitlements — never whether the core
  narrative pipeline or the safety envelope exists
- BYOK non-renewal must preserve read/export/download access to owned work;
  user content must never be held hostage as leverage for renewal
- Top-up flows must be transparent and non-manipulative — no dark patterns,
  no concealed overage behavior

## Note-Taking (Self-Improvement Loop)

After each task, log any correction, preference, or pattern learned during
that task. This is how the project accumulates institutional memory across
sessions.

**Trigger conditions — log when:**

- You were corrected on an implementation decision
- You discovered a behavioral pattern not covered by existing rules
- You made an assumption that turned out to be wrong
- You found a better approach than what the spec implied

**Format:** one line, dated, plain language.  
`[YYYY-MM-DD] <lesson learned>`

**Where to log:**

- Project-wide lessons go in the Lessons section below
- Subsystem-specific lessons go in the relevant file in `/context/`
- When three or more related lessons accumulate anywhere, create a new
  context file in `/context/`, add it to the folder tree in the docs,
  and note it below

## Lessons

[2026-04-02] Before committing, run the full local gate sequence on the exact branch head you plan to push: `black src/ tests/ && ruff check src/ tests/ && mypy src/ && pytest -q`. A green Black check alone does not mean the branch is CI-clean.

[2026-04-02] When CI reports a specific file in a formatter or lint failure, verify that the file’s diff is actually staged and included in a pushed commit. A local fix is not complete until `git diff`, `git status`, and the commit contents confirm it was committed.

[2026-04-02] When fixing a reported formatter or lint issue, inspect the files changed in the commit(s) being pushed. If CI complained about a file and that file is absent from the pushed commit summary, assume the fix did not reach GitHub.

[2026-04-02] Pin Black to an exact version in dev dependencies to reduce avoidable CI/local drift, but do not assume version drift is the root cause without proof from the failing file, the actual commit contents, and the current CI run.

[2026-04-07] CRD issue numbers (Issue 4, Issue 8, Issue 18, …) and GitHub issue numbers (#43, #44, #45, …) are different namespaces. Always write "CRD Issue N" for construction-readiness document references and "#N" for GitHub issue/ +PR references. Never use bare "Issue N" — every AI tool reviewed so far conflates the two sequences.

<!-- Claude Code appends dated one-line lessons here as they are learned -->
