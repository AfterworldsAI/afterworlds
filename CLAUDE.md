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
4. Pipeline is staged: Planner → Writer → Extractor → Contradiction → Safety
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

## Commit Format

Conventional commits:
`type(scope): description`
Types: feat, fix, refactor, test, docs, chore
Example: `feat(story-bible): implement tiered inclusion policy for events ledger`

## Known Unknowns — Do Not Resolve Silently

These are open decisions. If you encounter them, flag and pause — do not
make a load-bearing choice without explicit approval:

- React vs. Svelte for the frontend (resolve before Issue 19)
- Exact ChromaDB collection schema (resolve before Issue 18)
- Exact FastAPI route shapes (resolve before Issue 18)
- Rolling summary compression trigger N value (start at 10, tune with testing)
- Events Ledger tiered inclusion N value (start at 15, tune with testing)

## Business Model Constraints — Architectural Invariants

There is **one canonical five-pass pipeline** (Planner → Writer → Extractor →
Contradiction → Safety) for all paying access paths. No commercial tier may
remove core continuity functions. A degraded free-tier pipeline is not part
of this product.

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
  pipeline and normal hosted credits. Not a free tier. Not a degraded path.

Additional invariants:

- Extended TTL caching must be enabled by default wherever the provider
  supports it — this is an economic requirement, not a preference
- Stable prompt prefix is assembled once per turn and shared across all passes
  — rebuilding it per pass is an architectural violation
- Entitlement routing governs billing path, credit balance, Cloud Services
  status, and storage/ingestion entitlements — never whether the core
  continuity pipeline exists
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

**Lessons:**

[2026-04-02] Always run `black src/ tests/` (not just `--check`) before committing — Black formatting failures in CI are a recurring pattern, especially for long lines introduced in new test helpers.
[2026-04-02] Pin Black to an exact version (`black==X.Y.Z`) — a loose `>=` bound lets CI and local installs diverge, causing one to reformat files the other considers clean.

<!-- Claude Code appends dated one-line lessons here as they are learned -->
