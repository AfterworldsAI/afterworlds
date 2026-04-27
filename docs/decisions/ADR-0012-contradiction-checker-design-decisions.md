# ADR-0012 — Contradiction Checker Design Decisions (CRD Issue 11)

**Status:** Accepted
**Date:** 2026-04-26
**Issue:** CRD Issue 11 — Lightweight Contradiction Checker
**Scope:** Model tier selection; binary verdict model; mode-agnostic contract;
  rules-adjudication scope; writer output rendering order; shared tool-use utility;
  pass isolation (no DB writes, no canon mutations)

---

## Decision 1 — Haiku-Tier Model as v1 Provider

### Context

The Contradiction pass must verify Writer prose against the Story Bible quickly and
cheaply.  Options for model tier:

1. **Haiku-tier** — smallest, fastest, lowest cost; same family as the Extractor
2. **Sonnet-tier** — mid-tier; stronger reasoning but meaningfully higher cost per call
3. **Opus-tier** — most capable; cost and latency prohibitive for a gate pass

### Decision

**Option 1: Haiku-tier (`claude-haiku-4-5-20251001`) as the v1 provider.**

The model identifier is stored in `ContradictionConfig` (default field + env var
`AFTERWORLDS_CONTRADICTION_MODEL`), not in service code.  Operators can override the
model without touching the implementation.

### Rationale

- The Contradiction pass performs a focused, bounded check: does the prose contradict
  explicit Story Bible facts?  This requires recall over a structured context, not
  multi-step reasoning.
- CRD Item 7 explicitly specifies "small and fast LLM call with focused prompt."
- Per-turn cost discipline: the five-pass pipeline adds latency and cost at every
  turn; each pass should use the cheapest tier that is reliably correct for its scope.
- Model upgrades are a configuration change, not a code change.

### Consequences

- v1 has the same model as the Extractor.  If Haiku-tier proves insufficient for
  complex locked-fact scenarios, bumping to Sonnet-tier requires only a config change.

---

## Decision 2 — Binary Verdict Derived from Violations List

### Context

The service must return a verdict indicating whether the Writer output is CLEAR or
BLOCKED.  Options:

1. **LLM-modeled verdict** — include a `verdict` field in the tool schema; the model
   sets it directly.
2. **Derived verdict** — verdict is computed by the service from the violations list
   at construction time; the model never sees or produces a `verdict` field.

### Decision

**Option 2: verdict is derived at construction time.**

```python
verdict = ContradictionVerdict.BLOCKED if report.violations else ContradictionVerdict.CLEAR
```

The `ContradictionResult` includes both the derived verdict and the violations list
so callers can inspect both.

### Rationale

- A flat violations array is the model's natural output.  Adding a redundant `verdict`
  field creates a schema footgun: a model that reports violations but says "CLEAR" is
  a silent correctness failure.
- The mapping is deterministic: one source of truth (the violations list) drives the
  verdict with no ambiguity.
- The tool schema (`report_contradictions`) remains simple and flat — no discriminated
  union needed.

### Consequences

- The model never outputs a `verdict` string.  Callers that need the verdict read
  `ContradictionResult.verdict`.
- Any model behavior that produces an empty violations list when violations exist is
  caught by test coverage, not by a schema field.

---

## Decision 3 — Mode-Agnostic Contract

### Context

Afterworlds supports three narrative modes (RPG, Branching, Writing).  The
Contradiction pass could be mode-specific (different prompts per mode) or
mode-agnostic (single prompt, mode-aware only via the assembled context).

### Decision

**Mode-agnostic: a single `contradiction.md` prompt contract for all modes.**

The Story Bible context injected via `AssembledContext` is already mode-specific
(different cast, facts, and rules per story).  The Contradiction pass checks prose
against the Story Bible regardless of mode.

### Rationale

- Mode specificity lives in the Story Bible, not in the pass.  A single prompt that
  checks "does this prose contradict the Story Bible?" is correct for all modes.
- Maintaining per-mode prompts adds coordination overhead with no accuracy benefit.
- The `pov_tense_shift` category handles mode-specific concerns (e.g., Branching mode
  uses second-person present) through the prompt's worked examples, not through
  mode-branching logic.

### Consequences

- If a mode-specific check is ever needed (e.g., Branching mode allows tense shifts
  that Writing mode forbids), the prompt can be extended with mode-conditional rules
  without changing the service contract.

---

## Decision 4 — Rules-Adjudication Scope Narrowing

### Context

The Rules Package contains gameplay and narrative rules that may overlap with Story
Bible facts.  The Contradiction pass must decide whether to enforce Rules Package
preferences as violations.

### Decision

**The Contradiction pass checks only explicit Story Bible facts.  Rules Package
preferences are out of scope unless they directly encode a Story Bible fact that
is violated by the prose.**

This boundary is documented in `docs/prompts/contradiction.md` under "Scope."

### Rationale

- Rules Package enforcement is a separate concern from factual contradiction checking.
  A rules violation (e.g., "the party should not split up") is not a Story Bible
  contradiction.
- Mixing rules enforcement into the Contradiction pass blurs the gate's signal: a
  BLOCKED verdict should mean "the prose contradicts established fact," not "the prose
  breaks a preference."
- Rules enforcement is deferred to a future pass or a rules-adjudication layer.

### Consequences

- The Contradiction pass will not block prose that violates Rules Package preferences
  but does not contradict any Story Bible fact.
- Rules Package violations that are also Story Bible violations (e.g., a rule that
  encodes a locked fact) are still flagged via `locked_fact_violated`.

---

## Decision 5 — Writer Output Rendering Order (PassForwardLedger vs. Raw Block)

### Context

The Extractor pass (CRD Issue 10) appends the Writer output as a raw block AFTER the
volatile suffix:

```
[stable prefix] [volatile suffix] [WRITER OUTPUT]
```

The Contradiction pass needs the Writer output BEFORE the volatile suffix so the
model sees it in the context of recent turns:

```
[stable prefix] [WRITER OUTPUT] [volatile suffix]
```

Two options:

1. **Raw block appended after volatile suffix** — mirrors the Extractor.
2. **PassForwardLedger insertion** — add writer output to the ledger via
   `PassForwardLedger.add("writer", writer_output)` so it renders as
   `[WRITER OUTPUT]\n{content}` before the volatile suffix, matching the
   ledger's existing render format.

### Decision

**Option 2: PassForwardLedger insertion via a derived context.**

`_derive_context()` creates a new `AssembledContext` with a copied ledger that
includes the Writer output entry.  The caller's original context is never mutated.

### Rationale

- The ledger's `render()` format (`[PASS_NAME.upper() OUTPUT]\n{content}`) is the
  canonical cross-pass communication format.  Using it for the Writer output keeps
  the rendering contract consistent.
- The Contradiction pass's job is to evaluate the Writer output in the context of
  what just happened (volatile suffix = recent turns + current input).  Placing the
  Writer output before the volatile suffix matches that intent.
- The Extractor puts its Writer output after the volatile suffix because it is
  extracting from the prose — it doesn't need the turn history for context.  The
  Contradiction pass is checking consistency, so turn history context matters.

### Consequences

- `_derive_context()` shallow-copies the ledger entries list so isolation is
  guaranteed without deep-cloning frozen Pydantic models.
- If the pipeline ever needs to pass additional intermediate outputs between passes,
  the same ledger mechanism can be extended.

---

## Decision 6 — Shared Tool-Use Parser (`pipeline/_tool_use.py`)

### Context

The Extractor pass (CRD Issue 10) implements `parse_tool_input()` inside
`extractor/caller.py`, keyed to `EXTRACT_TOOL_NAME`.  The Contradiction pass needs
the same logic.  Options:

1. **Fork** — duplicate the parsing logic in `contradiction/caller.py`.
2. **Shared module** — extract a generic `parse_tool_use_block(response, tool_name)`
   into `pipeline/_tool_use.py`; both callers import from it.

### Decision

**Option 2: shared module at `src/afterworlds/pipeline/_tool_use.py`.**

The Extractor's `parse_tool_input()` is refactored to delegate to the shared utility;
Contradiction's `parse_tool_input()` does the same.  Each pass-level function wraps
`ValueError` into its own typed error class (`ExtractorPassError` /
`ContradictionPassError`).

### Rationale

- Deduplication: the parsing logic is identical across passes — only the tool name
  and error type differ.
- Future passes (Safety, Planner) can reuse the same utility without additional forks.
- The refactor is backward-compatible: `extractor/caller.py` still exports
  `parse_tool_input()` with the same signature and behavior.

### Consequences

- `ToolUseBlock` import moves from `extractor/caller.py` to `pipeline/_tool_use.py`.
- The extractor's existing tests continue to pass unchanged.
- PR Architecture Notes: this introduces a shared `pipeline/` utility not present in
  Issues 9 or 10 — the refactor crosses the Issue 10 file boundary but is contained
  to a non-breaking delegation.
