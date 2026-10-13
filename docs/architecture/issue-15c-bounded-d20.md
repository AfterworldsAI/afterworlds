# CRD Issue 15c — bounded d20 production reachability: traceability

**Governing issue:** #191, as updated with the Owner's context-input decisions of 12 October 2026 (body SHA-256 `9c3d6f3a…6c`).
- **Authority:** the Owner-accepted native C5 successor `srd-5-2-1-corpus-8781d4e0-a3b-15c.json` (SHA-256 `23e5d8e0…4f69`, schema 19), recorded locally with projection identity `44f212d5-32dd-5469-8f05-f0d236492347`. It is not published or activated shared authority: shared migration, publication and activation remain separately gated. It supersedes G1 (`2ccbaeba…1258`, projection `efab27a9-…`) by digest; G1 is preserved.
- **Recording evidence:** `.claude/review-notes/issue-15c-recording/`.

**Status (12 October 2026): partial, in implementation.**
- **Executable**, each certified against the successor:
  - source-fixed-DC checks;
  - difficulty checks (a GameMaster-selected Typical DC);
  - tool checks (tool plus typed activity, the tool held, validated proficiency);
  - Initiative (`undetermined` outcome);
  - weapon attacks against independent targets: damage, responses, temporary HP and zero-HP outcomes; every condition component is applied or explicitly reviewed (`attacks._ATTACK_RULES`), and implied conditions bind (`pipeline/rpg/conditions.py`);
  - actor-turn edges (`begin_turn`/`end_turn`, contract G1): a story-scoped coordination row with a revision and an append-only edge log (`rpg_turn_coordination`, `rpg_turn_edges`, migration 0041), committed with the delivered Turn;
  - death saves, made by `begin_turn` for a dying subject: Stable with a rolled recovery interval, death, and a natural 20's regained Hit Point.
- **Saving throws** are made by the operation that causes them (`pipeline/rpg/saves.py`): validated proficiency, a creature's printed column, conditions including automatic failure, and relevance-aware contributor refusal.
- **One turn, several operations:** each operation reads the state earlier ones left. The preflight checks every operation before any die, with every condition earlier operations could apply. A refusal after dice is a named `PreflightGapError` (`sibling-audit-turn-state-and-conditions.md`).
- **Contributing grants, partial:** ability increases, skill, Expertise, save and tool grants, and the feat selections they depend on, are validated against their exact typed source authority before any number is used (`pipeline/rpg/grants.py`). Weapon proficiency, armor training and Weapon Mastery grants are pending with the attack operations. Corpus and capability work for the held operations is pending.
- **Not yet executable:** weapon masteries, ammunition and the Light extra attack, creature attacks, Multiattack and save effects, stabilizing, the knockout alternative, and Stable-recovery and Short Rest attestations. They refuse as `unsupported_capability`, naming what they wait on. The Owner approved their spatial and timing input origins on 12 October 2026 (`.claude/review-notes/issue-15c-implementation/owner-context-decisions-2026-10-12.md`); implementation is in progress.
- **Refused for a recorded reason:**
  - Gaming Set and Musical Instrument checks: 2b records no tool kind (missing state).
  - Origin and Fighting Style feat eligibility through a category choice: no typed category (missing authority). Raw candidate C6 is under review.
  - Ability increases whose result depends on an unrecorded acquisition order (missing state).

## What is built

| Concern | Where |
| --- | --- |
| Production wiring after Planner and before Writer, for backend shown/hidden dice. No pending-roll service is wired. | `api/pipeline_wiring.py`, `pipeline/orchestrator/service.py` |
| Versioned capability manifest: roster operations, status, inputs, effects, holds, exclusions | `pipeline/rpg/capability.py` |
| Certification. It binds the operation to the exact release (package, release version, projection), the adapter version, the manifest version, and a fingerprint of every governing component's override-aware `component_schema_id`. | `pipeline/rpg/capability.py` (`certify`, `governing_fingerprint`) |
| Typed refusals: unsupported capability, missing state, missing or unpublished authority, stale binding, incompatible certification, invalid selection, player roll | `RefusalKind`, `AdjudicationRefusal`; `_rpg_resolution_failure` in the orchestrator |
| Source-fixed-DC ability checks, from typed authority (see the note below the table) | `pipeline/rpg/checks.py` |
| Identity-only proposal fields (`operation`, `check_identity`). The forced tool schema's enums are generated from the manifest. | `models/rpg.py`, `pipeline/rpg/caller.py` |
| Prompt contract v2. The unsupported-to-narration instruction is replaced by visible refusal; the narratively-impossible rule is kept. | `docs/prompts/rpg_adjudication.md` |
| The authority a turn reads: `TurnCharacter.index`, the exact effective authority of the character's binding | `services/dnd5e_state/turn.py` |
| Setup turns never require character state. Play status is resolved before the sheet. | `OrchestratorService._resolve_rpg_turn` |

The check executor derives each input from typed authority:

- the DC, ability and skill from the typed `ability_check` fact;
- the ability score as base plus capped adjustments;
- the Proficiency Bonus from the typed band, with Expertise doubling;
- Advantage/Disadvantage from typed condition facts.

Anything that could contribute to the roll but is not executed here refuses the check rather than being ignored:

- an active effect;
- a contributing feature, trait or feat;
- an equipped magic item;
- worn armor;
- Exhaustion;
- a contagion;
- a contextual condition fact.

## Acceptance criteria → evidence

| AC | State | Evidence |
| --- | --- | --- |
| 1. Wiring reaches adjudication after Planner and before Writer; nothing bypasses mechanics through narration; setup, OOC and non-mechanical turns are unchanged | Met for the executable scope. A proposal past the per-turn bound now refuses rather than being dropped. | `tests/ingestion/mechanical/test_bounded_d20_on_published_release.py` (production `create_app`); `tests/api/test_fake_provider_product_path.py`; `tests/pipeline/rpg/test_adjudication_service.py` |
| 2. Versioned manifest; certification binds the exact identity; changes invalidate | Met | `test_bounded_checks.py`: `test_the_certificate_binds…`, `…override_of_a_governing_component…`, `…unrelated_override_keeps…`, `…another_projection…` |
| 3. Validation before rolling; exact identities; stable prefix reused | Met | Every proposal is checked before any die (`test_an_unsupported_proposal_refuses_before_any_earlier_one_rolls`). Labels refuse (`test_a_label_only_backend_proposal_is_refused_not_rolled`). The pass renders the turn's single `AssembledContext`. |
| 4. Calculations, targets from authority, roster coverage | **Partial.** Checks are covered. Weapons, masteries, the zero-HP lifecycle, initiative, tools, saves and GameMaster-difficulty checks are **held on C1**. | `test_bounded_checks.py`: band, Expertise, caps, Poisoned, no natural-1/20 special case, contributor refusals |
| 5. Distinguishable failures; no partial application; `undetermined` only where admitted; player roll refused before pending | Met for the executable scope | E2E refusal tests: no Turn and no audit row; `pending_roll_requests` stays empty |
| 6. Independent subjects; commit recheck; atomic delivery-gated effects; holds | The single-subject recheck and holds are unchanged from 2b. Multi-subject application is **held** with the first multi-subject operation (attacks, C1-B and C1-C). | `tests/pipeline/orchestrator/test_rpg_turn_hold.py`; E2E atomicity |
| 7. End-to-end on G1 published in disposable stores | **Partial.** Checks, failure paths, hidden filtering, `gm_cheating = off` and player-roll refusal are covered. Weapons, masteries, the zero-HP lifecycle and multi-subject cases are **held on C1**. | `test_bounded_d20_on_published_release.py` |

## Architecture Notes

### Deviations and boundaries, stated explicitly

- **Semantic candidate C2 (formerly C1) holds most of the roster.** The approved scope is not shrunk: all 38 weapons, the eight masteries and the zero-HP lifecycle stay in the manifest as `HELD` operations. They refuse as missing authority, naming the candidate part they need. Dependent implementation waits for Codex review and Owner acceptance.
- **Scope update (#191 body `8225e1b6…57a2`).** The Owner admitted ordinary monster and animal attacks, bounded Multiattack and their associated saves and effects. The Owner also directed repair of the component-tool addressing and the omitted-source gaps, and individual assessment of conditional creatures. Candidate C2 (`.claude/review-notes/issue-15c-implementation/candidate-c2/`) supersedes C1 accordingly. The manifest's `EXCLUSIONS` entry for monster stat-block actions predates that update and is superseded. Revising it belongs to the held dependent implementation; that code is unchanged here.
- **Merge sequencing (a consequence, not decided in code).** Adjudication is wired, and prompt v2 directs the GameMaster to propose every mechanic. A merge before C2 is accepted would therefore leave combat turns and GameMaster-difficulty skill turns in an in-play RPG story failing visibly as `PIPELINE_ERROR`. AC1 requires that behaviour, but it makes RPG mode largely unplayable until C2 lands. Merge is separately gated.
- **Armor is conservative.** Worn non-shield armor refuses Strength and Dexterity checks even for a trained wearer until C2-C.
- **Classification rule (for Codex to confirm).** The rule:
  - Printed numbers and per-record data must be typed.
  - Universal arithmetic and sequencing are adapter procedure, certified against the components that govern them. That covers the modifier formula, the Advantage mechanics, Expertise doubling and the total ≥ DC comparison.
  - This follows ADR-005d D3 and ADR-015 D7.
- **Contributor lists are conservative and code-owned.**
  - A phrase scan of the pinned source produced a superset. The ability-check subset was then read entry by entry: 11 class features and 3 species traits.
  - It errs toward refusing.
  - Contributors to saves, Initiative and attacks are compiled with those operations.

### Seam with ADR-015b (recorded as #191 requires)

- **What 15c discharges.** 15c discharges only the backend-roll part of ADR-015b supersession item 7. The adjudication and dice services are constructed in `create_app()`. No pending-roll service is wired.
- **Player rolls.** Player-roll configuration refuses before any proposal is checked, so a pending request cannot exist.
- **Legacy code left in place.** The legacy announce/consume methods, and the label-based assembler they use, are left for 15b to retire (ADR-015b Group 9). They are unreachable in production.
- **In-turn instructions.** 15c's in-turn instructions are in-memory and per turn: an operation, an admitted identity and the derived numbers. Nothing in them is persisted beyond the existing delivery-gated `rpg_roll_audit` row. Its `modifiers_json` carries the provenance: operation, identity, DC source, breakdown, Advantage sources and certificate.
- **Planned shape for linked rolls.** When the held weapon work lands, linked attack → damage → mastery rolls resolve synchronously inside one delivered turn. Their instructions take ADR-015b's `RollInstructionSnapshot`/`RollTerm`/`RollPurpose` field shapes, so 15b can adopt them without migration. 15c introduces no persisted pending or sequence model.

### Other reconciliations

- **ADR-015 Decision 7.** Gains a dated forward reference: under ADR-005c Decision 6 and #191, out-of-boundary mechanics refuse, and `undetermined` is reserved for admitted behavior.
- **ADR-015b.** Gains a status note: it was accepted and merged via PR #128, so its `Proposed` header is stale.
- **Stale status lines.** The 2b traceability document and the Known Unknowns 5c entry gain dated, appended status lines. Preserved history is not rewritten.
- **`pipeline_wiring.py` docstrings.** These no longer say RPG adjudication is unwired.

### Invariants

- **Stable prefix.** It is assembled once per turn and reused by the adjudication pass.
- **Safety envelope.** Unchanged.
- **Separate canons.** Story Bible and mechanical state stay separate; no canon is written.
- **Deterministic rails.** Dice are code-generated; hidden rolls are backend-only and scrubbed from the Writer; results are preserved immutably; `gm_cheating` is snapshotted per record.
- **No numeric authoring.** No model-authored number, label or retrieved prose is used as authority.

No other drift from design principles.
