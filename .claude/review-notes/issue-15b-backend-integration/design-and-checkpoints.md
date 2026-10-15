# CRD Issue 15b Phase 2: design and mandatory advisor checkpoints

Written before implementation, 14 October 2026. #127 ("Notes for Claude Code" item 6) makes these
advisor checkpoints mandatory. The advisor reviewed the full design below (one consultation, then
corrections folded in). It is the engineering record, not new authority.

Baseline: main `f6f39721` (C9, schema 22, 14 certified 15c operations). The #129 candidate is based on
`6487a3a` (the Phase 1 merge), before all of 15c. Its DTOs, enums, event-ledger shape, migrations and the
aggregate-range fix are reusable. Its single-step `consume_roll`, its label-based instruction builder,
its unconditional `submit_decision` rejection and its duplicated resume code are not reused.

## 1. Sequence engine: stored snapshots are authority, replay only checks

15c resolves every operation of a turn synchronously with backend dice:
`RpgAdjudicationPassService._normal` runs a dice-free preflight over all proposals, then resolves them in
order, threading the advanced state, coordination and Cleave/follow-up linkage through the records. Phase 2
keeps that code path and adds a pause point.

- **Dice requests are described.** Every adapter dice call goes through `dice.request(...)`, which carries
  a `RollRequest`: roller subject, `RollPurpose`, label, modifier components, `dc`, natural-face outcomes
  and source references. Ordinary dice services ignore the description, so 15c turns are unchanged.
- **Ownership.** A die is player-rolled iff the story's dice handling is `player_rolls`, the proposal is
  not hidden, and the roller is the acting character. Every other die is a backend AI or hidden roll.
- **When a sequence exists.** A turn becomes a sequence only when its resolution asks for a player
  interaction: a player die, or a player decision. Group 17: "If no participant is player-rolled, both
  checks are backend-generated inside the originating turn's adjudication, as ordinary 15c rolls are."
  All-backend turns stay ordinary 15c turns.
- **Pausing.** A dedicated `PlayerInputRequired` exception is raised by the sequence dice and decision
  source. It is caught explicitly before the two catch-alls in `service._normal` and the preflight
  (advisor item 3). It is an `Exception`, never a `BaseException`.
- **Validate first, purely.** A roll, adjustment or decision submission is validated against the stored
  snapshot only: request identity, status, revision, term ids and counts, ranges, option membership. Only
  then does resolution continue (advisor item 1, AC41).
- **Fold completed operations; re-run only the in-flight one.** Completed operations are folded from
  their persisted records (effects, turn uses, edge, provenance), as `_normal` already threads records.
  Only the dice-free preflight and the single in-flight operation are re-run. The re-run's earlier dice
  come from that operation's own events.
- **Integrity check.** A regenerated instruction or decision must equal the stored snapshot. A mismatch
  is a typed integrity refusal, never a silent replacement.
- **Guards.** Every advancement reloads the actor and every subject and requires each one's revision,
  binding and holdings unchanged (`require_unchanged`, `require_holdings_unchanged`). It also requires the
  discovery snapshot and the coordination revision unchanged. A moved subject refuses typed and changes
  nothing.
- **Deterministic identities (advisor item 2).** Condition, effect and instruction ids minted inside a
  sequence come from `pipeline/rpg/ids.py`, a `uuid5` over the sequence and operation ordinal. Outside a
  sequence they are `uuid4` as today. A reload between steps therefore reproduces the pending view byte for
  byte.
- **Resume never replays.** Final audit rows and sheet effects come from the events only.

Rejected alternative: re-deriving every step through the old label-based assembler. That is #129's
numeric-label authority, which the handoff forbids.

## 2. Persistence

- **Migration `0043_action_resolution_lifecycle`** follows `0042`, keeping the single head. It does not
  transplant #129's occupied 0017/0019 ids. In one revision it:
  - creates `action_resolution_sequences`, with `session_id NOT NULL` and the partial unique index;
  - creates the append-only `action_resolution_events`, with UPDATE/DELETE triggers in the
    `rpg_roll_audit` pattern and a unique `(sequence_id, event_order)`;
  - asserts `pending_roll_requests` is empty before any destructive statement (15b-36), then drops the
    eight legacy columns and adds the six structured ones by direct `ALTER TABLE`;
  - adds the nine nullable audit columns plus `contest_resolution_json` (below).
- **Downgrade.** It restores the eight dropped columns with server defaults, so the round trip works on an
  empty table.
- **`blocking_events`** counts unresolved sequences as well as pending rolls. A binding therefore cannot
  move mid-sequence, for shared rule changes and adoption alike, through the same gate.
- **Retrieval coverage invariant.** The announce turn's `ROLL_REQUEST` marker matches "a pending roll row
  *or* an action-resolution sequence originating from this turn". A knockout decision can be a sequence's
  first interaction (§4).

## 3. Event ledger and audit (checkpoints 15b-34, 15b-35)

- **Tables.** Names follow #129: `action_resolution_events`, plus the kind-discriminated payloads in
  `models/rpg.py`.
- **Events.** One roll event per die, of kind `PLAYER_ROLL`, `AI_ROLL` or `HIDDEN_ROLL`. Adjustments and
  decisions are their own kinds.
- **Effects.** An operation's effects attach to the event whose acceptance completed that operation.
- **`mechanical_provenance`.** It carries the adapter version and the completed operation's record:
  15c provenance, turn uses and edge. Turn accounting therefore also comes from events at delivery.
- **Contest resolution (Group 17 audit checkpoint).** `RollEventPayload.contest_resolution` is a nullable
  typed `ContestResolution`, set only on the contest-completing roll event. The final audit carries it in a
  new nullable `rpg_roll_audit.contest_resolution_json`, set only on the completing roll's row.
  - The nullability sibling check: a nullable source feeds a nullable destination.
  - An all-backend contest has no events. It writes the same column from its record, through the existing
    15c audit write.
  - This extends the Final Audit Projection table in ADR-015b, in this PR.

## 4. Adjustments and decisions (disposition document)

- **Finesse switch.** A Finesse weapon attack's pending player instruction offers the other admitted
  ability as a parameterless pre-roll option. The initial ability is the GameMaster's validated selection,
  shown on the instruction as a visible modifier label, not decided silently.
  - Acceptance rewrites the persisted proposal's ability.
  - It increments `instruction_revision` and writes an `ADJUSTMENT` event.
  - The linked damage reuses the same ability, because `attacks.prepare` derives both from the one
    selection.
  - A stale revision, a non-offered option, a post-roll attempt, a duplicate or a concurrent request
    changes nothing.
- **Knockout decision (advisor item 6).** The disposition says 15c "preselects `knock_out`" and "15b must
  *instead* persist and advance the result-triggered player decision". For the acting character's melee
  weapon attacks, the knockout is therefore always the stored decision, raised when a hit would reduce a
  target from above 0 to 0 Hit Points:
  - **Options.** `knock_out` and `no_knock_out`, each with its typed provisional effects in the snapshot.
  - **Dice handling.** It applies in both modes, so a backend-dice turn can become a decision-only
    sequence.
  - **Refusals.** A GameMaster `knock_out` preselection by the acting character refuses as an invalid
    selection. A hidden melee attack by the acting character refuses before any die, because its decision
    cannot be offered without revealing the hit.
  - **Creature attackers** are unchanged (no knockout selection exists there).
- **Duration.** The Stable-recovery interval (`1d4` hours) is a `DURATION` step: `dc=None`, `undetermined`.
- **Recharge.** A creature's Recharge die needs a purpose. `RollPurpose.RECHARGE` is added to the
  adapter-owned vocabulary as required propagation of 15b-7: the coverage inventory requires every
  supported mechanic to be representable.

## 5. Contests (Group 17)

- **Operation.** A new certified operation `contest`. Its governing set is the check procedure, S1's
  `play.d20_tests/contest`, the economy procedure and the condition records. With no S1 it refuses
  `missing_authority`. A changed S1 refuses `incompatible_certification`.
- **Versions.** Manifest and adapter are bumped to `15b-manifest-5` and `15b-d20-5`. The 14 existing
  fingerprints are unchanged. The historical `s1-on-c9` evidence, which asserts 14 operations, is
  preserved.
- **Participants.** A character uses the 15c check procedure. A creature uses C9: a listed skill with its
  usual ability is the printed total, with nothing added; an atypical ability refuses; an unlisted skill
  or no skill is the ability modifier; a missing fact refuses.
- **Order and snapshots.** The player participant is rolled first. Both snapshots are frozen at creation.
  The backend participant's dice are drawn only when the player's result is accepted.
- **Comparison.** The higher total wins; equality is a tie with no effect.
- **Action cost.** No active turn: no use. Active turn with the initiator active: `glossary.action/action`.
  Initiator not active: refuse. The resisting participant costs nothing.
- **Hidden counterpart.** If the counterpart's existence is hidden, the player's purpose is the ordinary
  check purpose, no counterpart is named, and the Writer sees success or failure.

## 6. Orchestration (checkpoints: resume, node validation, continuation context, failure recovery)

- **Shared delivery core.** `_narrative_persist` keeps the narrative path. The post-Writer delivery core
  is shared by `orchestrate_turn` and `orchestrate_rpg_resume`: marker, commit rechecks, audit, effects,
  turn edges, Output Safety, Extractor and Contradiction.
  - Resume skips the Planner and Input Preflight; `planner_skipped` is carried over from #129.
  - It uses `_synthesize_intent`-style code-owned intent, the originating input and a continuation frame
    with no mechanical facts. The visibility-filtered views come from the bundle.
  - It passes the binding's refusal-buffer hooks, as #129's last fix did.
- **Resume checks.** Before any provider call, the resume checks sequence existence, status, story and the
  current canonical node. Typed backend discrimination is a typed `OrchestrationResult.action_sequence_error`
  code (`ACTION_SEQUENCE_ALREADY_COMPLETED`, …), not a string prefix: the #129 completed-resume thread was
  deferred, not closed. Phase 3 maps it to success-equivalent.
- **Turn hold.** Resume is bracketed by `RpgTurnHold.acquire/finish`, so held shared changes are
  processed after completion.
- **Failure.** A failed final narration rolls back the Turn, the audit rows, the effects and the
  completion. The events and the ready sequence survive. A retry re-reads the same events.
- **Legacy retirement.** The intercept, `player_reported_total`, `consume_player_roll`,
  `chosen_die_range`, `prepare_player_roll_announce` and the label assembler are removed. 15c's
  `PLAYER_ROLL_UNSUPPORTED` refusal and its tests are migrated to the sequence path.

## 7. Delivery order (advisor item 4)

1. Spike: a player-rolled weapon attack and its damage, with a reload between, through to the ready
   bundle.
2. The remaining dice sites, decisions, adjustments and contests.
3. The orchestrator and the migration.
4. Legacy retirement and docs.
