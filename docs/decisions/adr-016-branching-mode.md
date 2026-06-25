# ADR-016: Branching Mode Integration — Typed Output Contract, Code-Owned Affordances, and Persisted Interaction Configuration

**Issue:** CRD Issue 16 — Branching Mode Integration  
**Date:** 2026-06-24  
**Status:** Accepted

---

## Context

CRD Issue 16 ships the Branching Mode typed output contract, code-owned affordance
enforcement, persisted interaction configuration (interaction style, cadence,
length preference, branch count range), the general Branching-mode rejection
disposition, branch-choice resolution, and the Branching Mode OOC configuration
path.

The central invariant:
> The model may author narrative prose and *propose* branch options; it may never
> author the interaction affordances. Interaction style, freeform availability,
> branch-count range, cadence, branch identity, and selection state are
> code-owned from persisted configuration and validated structured output —
> never inferred from, nor made authoritative by, loose Writer prose.

Seven decisions were made during Issue 16. They are recorded here.

---

## Decision 1: Branch-card output = `BranchingWriterService`, not `WriterService` widening

**Decision:** Structured branch-card output for HYBRID and TRUE_CYOA interaction
styles is produced by a new `BranchingWriterService` (forced tool use) modeled on
`RpgAdjudicationPassService`. `WriterService.write()` and `WriterResult` are not
widened. FREEFORM_ONLY interaction style continues to use the prose `WriterService`
unchanged.

**Rationale:** The branch-card output contract is structurally different from the
prose writer contract. Forced tool use enforces the schema-level invariant that
`option_id`, `interaction_style`, `branching_cadence`, `freeform_available`, and
`branch_count_range` are absent from the tool schema — making it impossible for
the model to propose these code-owned fields. Widening `WriterService` or
`WriterResult` would contaminate the freeform prose path with Branching-specific
structure and break the mode-agnostic writer contract.

**Consequence:** The orchestrator routes BRANCHING + HYBRID/TRUE_CYOA narrative
turns through `BranchingWriterService`. The resulting `BranchingPassResult` carries
both the narrative text and the validated branch-option list; it is stored in
`OrchestrationResult.branching_pass_result` so downstream callers (frontend,
entitlement, observability) can inspect the full typed output without re-parsing
prose. A thin `WriterResult` wrapping only the narrative text is derived from
`BranchingPassResult` for downstream Extractor and Contradiction passes.
`PipelinePassId.BRANCHING_WRITER` and `PassIdentifier.BRANCHING_WRITER` are added
to their respective enums.

---

## Decision 2: `INTERACTION_REJECTED` — general Branching-mode non-narrative rejection disposition

**Decision:** `PipelineDisposition.INTERACTION_REJECTED` is the typed disposition
for all deterministic Branching-mode rejections: cases where the orchestrator can
evaluate the input without a narrative LLM call and determine it is definitively
invalid for the current session configuration or branch-card state.

Four typed reasons (`InteractionRejectionReason`):

| Reason | Trigger |
|---|---|
| `INVALID_FOR_INTERACTION_STYLE` | Non-OOC freeform prose in TRUE_CYOA mode |
| `INVALID_BRANCH_SELECTION` | BRANCH_CHOICE references an option_id absent from the current card set, or no card set was presented |
| `MATERIAL_BRANCH_REWRITE` | Trailing annotation materially rewrites the selected branch label's canonical meaning |
| `CANON_OR_GENRE_CONTRADICTION` | Selected action violates Story Bible canon or established genre/world constraints |

**Branch-selection validation is v1 in-scope.** `BranchSelectionValidationService`
runs after BRANCH_CHOICE intent classification and before the Writer (or
`BranchingWriterService`). Validation sequence:

1. **Option-existence check (deterministic):** resolve explicit `opt_N` token,
   positional-numeric phrase, or ordinal word against the presented option set
   from `Node.mode_metadata.branching.branch_options`. No match →
   `INVALID_BRANCH_SELECTION`.
2. **Annotation extraction (deterministic):** trailing text after the selection
   token is captured as `SelectedBranchContext.annotation`.
3. **On ACCEPT:** `SelectedBranchContext` (option_id, action_text, annotation) is
   threaded to the Writer so the narrative can reference the chosen branch.

`MATERIAL_BRANCH_REWRITE` and `CANON_OR_GENRE_CONTRADICTION` are defined in the
typed enum and available for use without changing the rejection surface. Narrow
forced-tool validation for non-trivial annotations is reserved for future
expansion within this issue scope; v1 deterministic validation covers option
existence and annotation extraction.

**Invariants:** INTERACTION_REJECTED is non-billable — no Turn is created, no
Node is created, no canon is mutated, and no full narrative Writer call is made.
OOC intent bypasses the rejection check entirely (OOC is always valid regardless
of interaction style).

**Typed fields:** `OrchestrationResult.interaction_rejection_reason` is typed as
`InteractionRejectionReason` (not a free string). `interaction_rejection_message`
(non-empty human-readable string) is required alongside it. Both are None on all
other dispositions.

**V1 classifier limitation:** The Issue 7 classifier does not receive
`ClassificationHints` about the current interaction style. `branch_choice` is
only emitted for inputs with explicit selection language. A Sojourner who writes
"Cross the bridge" in TRUE_CYOA mode will be rejected as
`INVALID_FOR_INTERACTION_STYLE` because the classifier returns
`in_character_action`. Wiring `ClassificationHints` is a future issue.

**Consequence:** `PipelineDisposition.INTERACTION_REJECTED` added to
`orchestrator/models.py`. `OrchestrationResult.interaction_rejection_reason:
InteractionRejectionReason | None` and `interaction_rejection_message: str | None`
added. `InteractionRejectionReason` enum with four values added to
`models/enums.py`. `BranchSelectionValidationService` added to
`pipeline/branching/selection.py`. `BranchSelectionValidationResult` and
`SelectedBranchContext` models added to `pipeline/branching/models.py`.

---

## Decision 3: Branching setup confirmation = `DELIVERED` turn (full pipeline, creates Node)

**Decision:** Turns during the Branching setup phase (interaction style/cadence
not yet configured; `play_status = "setup"`) route through the standard narrative
pipeline using the prose `WriterService`. No setup-specific disposition is introduced.
Setup turns are ordinary `DELIVERED` turns.

**Rationale:** The setup phase is narrative — the story architect responds to the
Sojourner's world-building inputs. This narrative should be canon-tracked by the
Extractor and contradiction-checked, just like in-play narrative. No special
dispatch is required.

**Consequence:** When `interaction_style is None` (setup not complete or pre-Issue-16
row), the orchestrator uses the prose `WriterService` path. This is the safe default
and satisfies the conservative-backfill rule (never silently freeform_only).

---

## Decision 4: OOC Branching-config updates use forced-tool extraction, transaction-scoped to `OOC_HANDLED`

**Decision:** When a Sojourner uses OOC to change interaction style, cadence, or
other session configuration, the configuration change is extracted via a narrow
forced-tool LLM call (`BranchingOocConfigExtractorService`) and persisted inside
the existing OOC outer transaction that produces `OOC_HANDLED`. The configuration
write commits atomically with the OOC Turn row.

**Rationale:** Forced-tool extraction produces a machine-readable `BranchingConfigUpdate`
that code can validate against `ALLOWED_RANGES_BY_STYLE` before persisting. Prose
confirmation alone would require fragile text-parsing for a structured config change.
Transaction-scoping is the correct architectural boundary per the Issue 12c
outer-transaction contract — decoupling the configuration write from the OOC Turn
persistence would create a two-phase-commit problem.

**Best-effort:** The extraction pass is best-effort. Extractor failure (provider
error, schema mismatch, invalid range) silently skips config persistence without
blocking `OOC_HANDLED` delivery — the Sojourner still receives the OOC prose
response. The next OOC turn may succeed.

**Consequence:** `BranchingOocConfigExtractorService` added to
`pipeline/branching/ooc_config_extractor.py`. `BranchingConfigUpdate` model added
to `pipeline/branching/models.py`. `PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR`
added to `entitlement/enums.py`. `apply_branching_config_update` CRUD helper added
to `persistence/crud/session_state.py`. `OrchestratorService._run_ooc()` wired
with `branching_ooc_config_extractor` constructor param (optional; best-effort).

---

## Decision 5: Persistence = extend `branching_session_states` (no new config table)

**Decision:** The five new configuration fields (`interaction_style`,
`branching_cadence`, `length_preference`, `branch_count_range`, `play_status`)
and seven optional setup-context fields are added to the existing
`branching_session_states` table via Alembic migration 0012. No new
`branching_config` or `branching_interaction_config` table is created.

**Conservative backfill rule:** All new interaction-configuration columns are
nullable with a NULL server default. `play_status` has a `server_default="setup"`
(safe for all existing rows). Existing rows receive `NULL` for `interaction_style`,
`branching_cadence`, `length_preference`, and `branch_count_range` — never
`"freeform_only"`. This preserves the invariant that pre-Issue-16 rows do not
silently gain an interaction contract they were not configured for.

**Rationale:** One persisted session state per story per mode is the correct
granularity. A separate config table adds a join and a new transaction boundary
without adding semantic value. The existing table is the natural home for this
configuration.

**Consequence:** Migration 0012 adds 12 columns to `branching_session_states`.
`BranchingSessionStateORM` is extended. `BranchingSessionState` Pydantic model
gains nullable configuration fields.

---

## Decision 6: `BranchTree`/`BranchNode` graph-traversal activation deferred; v1 ships `SelectedBranchContext` resolution

**Decision:** v1 ships branch-choice resolution via `SelectedBranchContext`
pass-forward and records the selected option on the current Node. `BranchTree`
and `BranchNode` graph-traversal activation (looking up the next node to navigate
to) is deferred to a future issue.

**What IS v1 in-scope:**
- `BranchSelectionValidationService` resolves a BRANCH_CHOICE input to a
  `SelectedBranchContext` (option_id, action_text, annotation).
- `SelectedBranchContext` is threaded from the validation service to the Writer
  so the narrative can reference the chosen branch.
- **Phase G (selection edge):** after the Writer and persistence complete,
  `selected_option_id` and `selection_annotation` are written to
  `Node.mode_metadata.branching` — recording which option was chosen on this
  beat for future graph-traversal lookup.

**What is DEFERRED:**
- `BranchTree` / `BranchNode` activation: they are left structurally present but
  not written to or read by the Issue 16 pipeline.
- `Node.branching_logic` (a `list[UUID]`) is NOT written by Issue 16. Full
  graph-edge realization — building typed labeled-edge entries — is a future
  migration. The intended labeled-edge shape for future implementors is:

```json
{
  "option_id": "opt_1",
  "target_node_id": "<UUID of the next narrative node>"
}
```

**Rationale:** Recording what was selected on a beat (`selected_option_id`) is
needed for observability and future navigation even before the graph traversal
layer exists. Activating `BranchTree`/`BranchNode` requires resolving the
next-node lookup, which is a larger scope than Issue 16's output-contract and
selection-validation mandate.

---

## Decision 7: `BranchingCadence` is a distinct axis from `PacingStage`

**Decision:** `BranchingCadence` (INTERACTIVE / BALANCED / IMMERSIVE) is a new
enum in `models/enums.py`, distinct from the existing `PacingStage` enum
(SETUP / ESCALATION / REVERSAL / CLIMAX / AFTERMATH). They are not merged,
aliased, or conflated.

**Rationale:** `PacingStage` is an internal narrative arc tracker (the five-stage
dramatic arc) — it is structural and the model tracks it invisibly. `BranchingCadence`
is a Sojourner-configured response-density setting. They are orthogonal axes:
a Climax beat can be any cadence; an Interactive cadence can be at any pacing stage.
Collapsing them into a single enum would force a one-to-one mapping that doesn't
exist in the design.

**Consequence:** `BranchingCadence` added to `models/enums.py`. `PacingStage`
unchanged. `BranchingSessionState` carries both independently. The OOC handler
can update `branching_cadence` without affecting `pacing_stage`.

---

## Mode-Specific OOC Handler — Known Unknown Resolution

ADR-015 Decision 11 established the mode-aware OOC handler selection pattern and
noted: "Issues 16 and 17 should follow the same pattern for Branching and Writing
modes."

Issue 16 resolves the Branching OOC handler Known Unknown:
- `docs/prompts/branching_ooc_handler.md` created (Branching-specific OOC instructions).
- `OrchestratorService._run_ooc()` extended: when `story_mode is StoryMode.BRANCHING`,
  uses `self._branching_ooc_handler_prompt` instead of the generic handler.
- `load_branching_ooc_handler_prompt()` loader added.
- `known_unknowns.md` updated to RESOLVED for Branching mode OOC handler.

Writing mode OOC handler (Issue 17) remains OPEN.

---

## Consequences

- `PipelineDisposition.INTERACTION_REJECTED` added to `orchestrator/models.py`
- `PassIdentifier.BRANCHING_WRITER` added to `pipeline/_refusal.py`
- `PipelinePassId.BRANCHING_WRITER` and `PipelinePassId.BRANCHING_OOC_CONFIG_EXTRACTOR`
  added to `entitlement/enums.py`
- `OrchestrationResult.interaction_rejection_reason: InteractionRejectionReason | None`
  and `OrchestrationResult.interaction_rejection_message: str | None` added
- `OrchestrationResult.branching_pass_result: Any | None` added (typed as
  `BranchingPassResult` by callers; `Any` to avoid import cycle with
  `pipeline/branching/models.py`)
- `OrchestrationResult.branching_visible_state: Any | None` added
- `InteractionStyle`, `BranchingCadence`, `LengthPreference`, `BranchCountRange`,
  `BranchingPlayStatus`, `InteractionRejectionReason`, `BranchPresentationState`
  enums added to `models/enums.py`
- `BranchingSessionState` extended with interaction-configuration fields
- `BranchingSessionStateORM` extended with 12 new columns
- Alembic migration 0012 added
- `BranchingNodeMetadata` enriched with typed output-contract fields
  (`interaction_style`, `branching_cadence`, `freeform_available`,
  `branch_count_range`, `branch_options`, `branch_presentation_state`,
  `selected_option_id`, `selection_annotation`)
- `PersistedBranchOption` model added to `models/node.py`
- `pipeline/branching/` package created:
  `__init__.py`, `caller.py`, `config.py`, `models.py`, `service.py`,
  `selection.py`, `ooc_config_extractor.py`, `visible_state.py`
- `BranchSelectionValidationService`, `BranchSelectionValidationResult`,
  `SelectedBranchContext` added to `pipeline/branching/`
- `BranchingConfigUpdate` and `BranchingOocConfigExtractorService` added to
  `pipeline/branching/`
- `BranchingVisibleState` and `BranchingVisibleStateService` added to
  `pipeline/branching/`
- `apply_branching_config_update` CRUD helper added to
  `persistence/crud/session_state.py`
- `docs/prompts/branching_ooc_handler.md` created
- `known_unknowns.md` updated: Branching OOC handler RESOLVED; v1 CYOA
  classifier limitation documented as new Known Unknown (future issue)
- `OrchestratorService` wired with `branching_writer_service`,
  `branching_session_resolver`, `branching_visible_state_service`,
  `branching_selection_service`, and `branching_ooc_config_extractor`
  constructor params
