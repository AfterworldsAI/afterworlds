# ADR-015: RPG Mode Integration — Adjudication Loop, Bounded d20 Adapter, Dice Rails, and Visible State

**Issue:** CRD Issue 15 — RPG Mode Integration  
**GitHub:** #105  
**Date:** 2026-06-20  
**Status:** Accepted

---

## Context

CRD Issue 15 ships the RPG Adjudication Loop, bounded d20 Rules System Adapter,
deterministic dice rails, `gm_cheating = off` enforcement, and visible-state
payload/DTO for RPG mode. It does not modify the core Sojourn orchestration
pipeline (Planner → Writer → Extractor → Contradiction). RPG mode is a
mode-specific orchestration override layered around an unchanged pipeline core.

Two architectural questions were pre-decided by the owner before implementation
began (Forks A and B). This ADR records those decisions plus eight implementation
decisions made to resolve scope and boundary questions during Issue 15.

---

## Pre-Decided: Fork A — Adjudication Pass Position (A1)

**Decision:** Implement a distinct `RPG_ADJUDICATION` pass that runs after Planner
and before Writer.

**Rationale (owner-decided):** Planner stays mode-agnostic. Writer stays
single-pass. Adjudication facts are available to Writer as a ledger forward, not
as a second Writer pass or a Writer mutation.

**Consequence:** A1 is the implementation target. The `RPG_ADJUDICATION` pass is
a mode-specific orchestration override, not a pipeline edit.

---

## Pre-Decided: Fork B — Sheet Mutation Application Path (B1)

**Decision:** Trust-relevant sheet mutations (HP changes, resource expenditure,
spell-slot use, condition application, and similar) are applied by code from the
resolved adjudication record and the d20 adapter. They are applied inside the 12c
outer transaction, after the provisional Turn row exists. They are outside the
Extractor proposal path — Extractor owns narrative canon proposals; the d20
adapter owns mechanical sheet mutations.

**Rationale (owner-decided):** Sheet mutations from rolls must be deterministic
and auditable. Routing them through Extractor would intermix narrative-canon
proposal semantics with trust-critical numeric state.

**Consequence:** B1 is the implementation target. `ResolvedAdjudicationRecord`
feeds `rpg_roll_audit` rows and `sheet_effects`; it never enters the Extractor
input.

---

## Decision 1: Transaction lifecycle for provisional records, audit rows, and sheet effects

**Decision:** The mechanical state written by the RPG Adjudication Loop lives
entirely inside the existing 12c outer transaction (`session.begin()`). The
sequence inside the transaction is:

1. Adjudication pass runs; all resolved records are provisional in-memory.
2. Writer produces narrative output (receives only the Writer-facing view).
3. Provisional Turn row is created (turn_id now exists).
4. `rpg_roll_audit` rows are written after the provisional turn_id exists.
5. `sheet_effects` are applied to the character sheet via the d20 adapter.
6. On delivery, the outer transaction commits: Turn, audit rows, and sheet
   mutations all persist together.
7. On block (Output Safety, Contradiction, provider refusal, pipeline error):
   the existing 12c rollback removes Turn, audit rows, and sheet mutations
   atomically. No audit rows survive a blocked turn.

`PendingRollRequest` rows (player-roll announce) are written inside the outer
transaction as part of turn creation. They persist for "pending" turns
(disposition `DELIVERED` with a pending-roll Turn shape). They are not written
before the provisional Turn row.

**Rationale:** Using the existing 12c outer transaction removes the need for a
second transaction model. Rollback safety is inherited. A blocked turn leaves no
audit residue.

---

## Decision 2: `RPG_ADJUDICATION` pass identity

**Decision:** `RPG_ADJUDICATION` is a new value in both `PipelinePassId`
(`entitlement/enums.py`) and `PassIdentifier` (`pipeline/_refusal.py`). It uses
Haiku-tier model selection by default (entry in `PASS_TIER_DEFAULTS`). It uses
the same turn-bound `ProviderAdapter` as other passes. It is settled through the
existing structured-output / tool-use machinery (Issues 10/11).

**Rationale:** Reusing the existing structured-output machinery and
`TurnProviderBinding` avoids forking provider resolution or response parsing.
Haiku-tier is appropriate for proposal extraction (short, schema-bounded output).

**Consequence:** `TurnCostPolicy.extract_snapshots` must be extended to include
the adjudication pass token snapshot when present. The cost is charged on
`DELIVERED` turns via the existing credit deduction path.

---

## Decision 3: Roll-authorship invariant — schema-first enforcement

**Decision:** Roll-authorship is enforced structurally before prompt discipline.
`RollProposal` carries no result field, no DC field, no numeric modifier field,
and no advisory numeric field of any kind. `difficulty_reference_note` is a
non-authoritative textual hint only. Any numeric DC is sourced by code from the
rule slice, house-rule overrides, or adapter policy, or is set to `None` /
`outcome = "undetermined"`. A model that author-hallucinates a number cannot
embed it in a `RollProposal` because the schema provides no such field.

**Rationale:** Prompt discipline is a secondary defense. Schema enforcement
prevents structural violations regardless of prompt failures.

---

## Decision 4: `gm_cheating = off` enforcement

**Decision:** When `gm_cheating = off`, `ResolvedAdjudicationRecord` is the
immutable single source of truth for outcome and `sheet_effects`. Writer prose
that contradicts a resolved result changes neither the audited result nor the
applied sheet mutations — in both directions, including climactic moments.
`gm_cheating_at_roll` is snapshotted into `ResolvedAdjudicationRecord` at
resolution time and is immutable thereafter.

Writer output that overstates or understates a resolved outcome is a prose
continuity issue for the Contradiction Checker, not a mechanical-truth violation.
The mechanical truth is already locked in the record.

**Rationale:** `gm_cheating = off` is a player-trust invariant, not a preference.
Code enforcement (not prompt-only) is required.

---

## Decision 5: Hidden-roll handling

**Decision:** Hidden rolls are backend-visible but player-facing nulled.
`ResolvedAdjudicationRecord.visibility = RollVisibility.HIDDEN` flows through
the full audit path (total, dc, outcome, source, sheet_effects all recorded).
`WriterAdjudicationView` for a hidden roll has `total = None`, `dc = None`, and
`player_facing_summary` describing only what the character perceives from the
outcome — never the roll number, target number, mechanical reason, or hidden
actor.

`hidden_modifier_present` on `PendingRollRequest` is internal-only. It must never
appear in `WriterAdjudicationView`, `RpgVisibleState`, player-facing prompts, or
delivered output.

**Rationale:** Hidden rolls exist because the character has no in-world awareness
that a check is occurring. The audit record must be complete; the player-facing
view must be filtered.

---

## Decision 6: Safety-skip predicate interaction

**Decision:** Adding `RPG_ADJUDICATION` as a `PipelinePassId` does NOT change the
`CapabilityProfileAwareSafetyPolicy` skip predicate. The predicate is driven by
eligible Writer routes and `request_risk_signal`, not by pass identity. Confirmed
by source inspection of `pipeline/provider/_routing.py`.

**Rationale:** The Safety skip predicate was designed to be provider- and
pass-count-agnostic. Adding a new pass id that is not a Writer pass does not
affect it.

**Consequence:** The Safety-skip predicate requires no change for Issue 15. If a
future issue requires the adjudication pass to affect Safety routing, that is a
new owner decision requiring a new ADR.

---

## Decision 7: Bounded d20 / no-ingestion-mechanics boundary

**Decision:** Code owns deterministic RPG rails and auditability. The bounded d20
Rules System Adapter is hand-authored and covers d20 semantics only: modifier
assembly from sheet + rule slice + `RuleOverride`s, DC verification from
authoritative sources, degree-of-success calculation, advantage/disadvantage
via `DiceService`, and audit-record construction. Rules ingestion does not
generate executable mechanics. A Rules Package may be ingested and queried
without a compatible adapter, but it cannot be offered as a fully adjudicated
system without one.

The adapter returns `outcome = "undetermined"` when the mechanic is outside the
supported boundary, rather than inventing a result.

**Rationale:** The adapter-specific-mechanics boundary was established during the
RPG dice-handling Known Unknown resolution. Hand-authored adapters prevent
mechanic drift and keep auditability deterministic.

---

## Decision 8: Active mechanical conditions/effects are sheet-owned concrete d20 state (owner decision)

**Decision:** Active conditions and active effects are owned by the concrete d20
character sheet layer, not by `RpgSessionState.combat_context.active_conditions`.

Implementation direction:
- Add active conditions/effects to the concrete `Dnd5eCharacterSheet` layer as a
  typed child DTO / sheet-owned child table (e.g., `Dnd5eActiveCondition`).
- Do not add condition semantics to `RpgCharacterSheetBase`. The base sheet
  stores structure; the active Rules Package and d20 adapter interpret mechanical
  meaning.
- Condition records carry sufficient structured metadata for v1 adjudication and
  visibility: condition/effect identifier, display label, source, visibility,
  duration/expiry policy, applied turn reference, and an optional Rules Package
  mechanical entity reference.
- Temporary conditions (frightened, poisoned, stunned, exhaustion, etc.) that
  survive an app/session restart are stored here. Fictional time, rest events,
  turn counters, or explicit clear effects remove them — not process/session
  lifecycle.
- Permanent or long-lived effects (curses, diseases, lingering injuries) use the
  same sheet-owned path with appropriate duration/expiry metadata.
- `RpgSessionState.combat_context.active_conditions` may be retained as
  non-authoritative combat scaffolding (e.g., initiative-linked duration counters,
  encounter-local views) but must not be the authoritative store.
- `SheetEffect.apply_condition` and `SheetEffect.clear_condition` target this
  sheet-owned child table/DTO.
- If a condition is narratively significant, the Extractor may record a Story
  Bible fact or event through the normal narrative canon path. That does not
  replace the sheet-owned mechanical record.

**Rationale:** Active conditions can survive session restarts (exhaustion carries
across a long rest; curses persist until removed). Owning them on session state
would lose them on process restart. The Issue 2a boundary is preserved: the base
sheet stores structure; the adapter interprets meaning.

---

## Decision 9: `RpgSessionState` extension — play status and session configuration

**Decision:** `RpgSessionState` must carry the fields required for play-status
dispatch and per-session configuration:

- `play_status: Literal["setup", "in_play"]` — drives orchestration dispatch
  (setup path vs. adjudication path)
- `gm_cheating: bool` — snapshotted into `ResolvedAdjudicationRecord` at roll
  time; defaults to `True` per the prompt contract (`gm_cheating = on` is default)
- `tone: Literal["gritty", "balanced", "forgiving", "danger_free"]`
- `session_type: Literal["short_adventure", "campaign", "open_ended"]`
- `genre_flavor: str | None`
- `house_rules: str | None`
- `acceptable_content: str | None`
- `setup_phase: Literal["world_setup", "character_creation", "play_configuration",
  "complete"]` — tracks pre-play progress

These are session-configuration fields established during the pre-play sequence.
`play_status` transitions from `setup` to `in_play` when the character sheet is
adjudicable (`D20RulesSystemAdapter.is_adjudicable(sheet)` returns `True`) and
the pre-play sequence reaches `setup_phase = "complete"`.

**Rationale:** The orchestration override in Phase 5 dispatches on `play_status`
and reads `gm_cheating` at roll time. Without these fields on session state,
the dispatch and `gm_cheating_at_roll` snapshot have no authoritative source.

---

## Decision 10: `BLOCKED_PENDING_ROLL` disposition — supersedes prior scope note

**Decision (owner-accepted correction):** An earlier statement in the Issue 15
specification said that the `PipelineDisposition` set is unchanged by Issue 15.
That statement is superseded for the **pending-roll intercept case only**.

`BLOCKED_PENDING_ROLL` is an accepted disposition within `PipelineDisposition`
for the case where a Sojourner submits a new in-character action while a
`PendingRollRequest` is outstanding.

**What `BLOCKED_PENDING_ROLL` must do:**

- Return a disposition of `BLOCKED_PENDING_ROLL` that surfaces the outstanding
  pending roll to the caller.
- Redirect the Sojourner to supply the requested roll result before new in-character
  narration continues.

**What `BLOCKED_PENDING_ROLL` must NOT do:**

- Run the Planner, RPG adjudication, Writer, Extractor, or sheet-effect application
  for the intercepted action.
- Create a new narrative outcome Turn row or Node.
- Consume, modify, or expire the pending roll request.

**Interaction with OOC/config input:** Out-of-character and configuration inputs
arriving while a pending roll is outstanding may be answered normally (OOC short-
circuit path). The pending roll is preserved and the BLOCKED_PENDING_ROLL
intercept applies only to new in-character narrative actions.

**Rationale:** Allowing new in-character actions to bypass a pending-roll state
would create ambiguous canon (the narrative proceeds before the player's declared
result). Blocking is the correct response. Adding `BLOCKED_PENDING_ROLL` is a
narrow, well-scoped extension of the disposition set with no pipeline ownership
implications.

---

## Consequences

- `PipelinePassId.RPG_ADJUDICATION` is added to `entitlement/enums.py`
- `PassIdentifier.RPG_ADJUDICATION` is added to `pipeline/_refusal.py`
- `PASS_TIER_DEFAULTS[PipelinePassId.RPG_ADJUDICATION] = ModelTier.HAIKU` in
  `entitlement/policy.py`
- `OrchestrationResult` gains `rpg_visible_state: RpgVisibleState | None`; the
  disposition-matrix invariant validator gains an RPG branch
- `Dnd5eCharacterSheet` gains a typed active-condition relationship
  (`Dnd5eActiveCondition` or equivalent child table)
- `RpgSessionState` gains play-status and session-configuration fields (migration)
- `rpg_roll_audit` table added (append-only, raw-SQL UPDATE/DELETE triggers)
- `pending_roll_request` table added
- `RpgVisibleState`, `WriterAdjudicationView`, `ResolvedAdjudicationRecord`,
  `RollProposal`, `AdjudicationProposalOutput`, `DiceResult`, `SheetEffect`,
  `PendingRollRequest` models added
- `DiceService` protocol + `SystemRandomDiceService` added
- `D20RulesSystemAdapter` added
- `RpgAdjudicationPassService` added
- `RpgVisibleStateService` protocol + implementation added
- `docs/prompts/rpg_adjudication.md` added
- RPG OOC protocol replaces 12c placeholder for RPG mode
- `known_unknowns.md` updated: mode-specific OOC partially resolved for RPG;
  pending-roll rewind/cancel added as new deferred item; frontend stack entry
  already resolved
