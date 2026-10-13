# CRD Issue 15c — bounded d20 production reachability: traceability

**Governing issue:** #191, as updated with the Owner's context-input decisions of 12 October 2026 (body SHA-256 `8ad87786…727426f`).

**Authority:** the Owner-accepted C8 successor `srd-5-2-1-corpus-8781d4e0-a3b-15c-c8.json`.
- **Identity:** SHA-256 `ead7fa9d…0d0d`, schema 21 (`4499b396…`), recorded locally 13 October 2026, projection `e4f8f4fb-de6c-53c9-98f1-fa7a0159fe42`, oracle identity `70646cd9…`.
- **Preserved and superseded:** it supersedes the C7 successor `…-15c-c7.json` (`2853f30a…f373`, projection `8446ab6b-…`) by digest, which superseded the native C5 successor (`23e5d8e0…4f69`, projection `44f212d5-…`). C7, C5, G1 and the original artifact are all kept byte for byte.
- **Not shared authority:** it is not published or activated. Shared migration, publication and activation remain separately gated.
- **Recording evidence:** `.claude/review-notes/issue-15c-c8-recording/`. For C7 and C5, see `issue-15c-c7-recording/` and `issue-15c-recording/`.

**Status (13 October 2026): implemented for the whole admitted roster, including the Ghast and Ghoul Claw rider exclusions from the accepted C8 creature types and the Owner-approved bounded species input; whole-PR Codex review, the final full pytest and exact-head CI pending.** Every operation below is certified against the C8 successor: adapter `15c-d20-4`, manifest `15c-manifest-4`, and component evidence in `.claude/review-notes/issue-15c-implementation/recert/`. The remaining holds are named under Architecture Notes (C8).

- **Checks:**
  - source-fixed-DC checks;
  - difficulty checks (a GameMaster-selected Typical DC);
  - tool checks, including the Gaming Set and Musical Instrument: the GameMaster selects the kind (`tool_variant`), which must be one of the activity's typed `ToolVariantsFact` kinds and held (`ItemInstance.tool_variant`, migration 0042). Proficiency counts only from a validated `ToolGrant` of that same tool and kind (`ToolGrant.variant`); a grant of another kind is no proficiency, a grant recording no kind refuses `missing_state`, and a kind that is not the tool's refuses at state, holding and grant validation;
  - Initiative.
- **Grants and feats:** contributing grants are validated against their exact typed source before any number is used (`pipeline/rpg/grants.py`). Origin-feat category eligibility is now typed (C7).
- **Saving throws**, made by the operation that causes them (`pipeline/rpg/saves.py`):
  - a creature's own save traits execute when every effect is its own Advantage or Disadvantage under a circumstance code can derive;
  - anything else refuses.
- **Weapon attacks against independent targets:**
  - damage, responses, temporary HP and zero-HP outcomes;
  - masteries, Cleave, and the Light and Nick extra attacks;
  - flat printed damage (the Blowgun);
  - the knockout alternative;
  - **ammunition (C7):** the attack names the held ammunition item. Code checks the item's typed `ammunition_supply` kind and the weapons it serves (sling and firearm bullets are disjoint), plus the quantity. One is expended per attack, hit or miss, by CAS on the holding in the delivered Turn's transaction; the last one removes the holding.
- **Zero-HP lifecycle:** actor-turn edges and death saves; first aid; the OD-15c-2 attestations.
- **Creature attacks** (`pipeline/rpg/creature_attacks.py`, `creature_clauses.py`):
  - every same-entry typed clause is executed or refused before any die;
  - Multiattack, including replacements by another attack entry;
  - save effects and usage limits (`creature_effects.py`);
  - entries are admitted only from the code-owned roster (`roster.py`).
- **Bystanders:** close combat, Pack Tactics and others' auras each name and read their subject.
- **Creature standing traits** apply on both sides of an attack (`attacks.creature_traits`).
- **Bloodied:** a certified universal predicate (`damage.bloodied`).
- **Linked condition:** Restrained "until the grapple ends" is tied to its Grappled instance (`ConditionInstance.lasts_while_instance`).

**Refused for a recorded reason (not counted as coverage):**
- Fighting Style feat eligibility through a category choice: no typed category, since C6-B was withdrawn.
- Ability increases whose result depends on an unrecorded acquisition order.
- Extra Attack (prose-bound) and Reactions.
- Creature entries outside the roster.

**One turn, several operations.**
- Each operation reads the state earlier ones left, including holdings.
- The preflight checks every operation before any die:
  - every condition earlier operations could apply;
  - every lifecycle change;
  - every action, use and ammunition spent.
- A refusal after dice is a named `PreflightGapError`.

**Action accounting (C7 remediation, a behaviour change).** Attacks, first aid, and creature attacks and effects spend the acting subject's own active turn (`pipeline/rpg/economy.py`). An operation proposed without that turn refuses before any die.

What a turn can spend, each from typed authority:
- the turn's one action;
- the Attack action's one attack roll;
- one Bonus Action;
- the Light extra attack;
- Loading's one piece per activation;
- once-per-turn features (Cleave, Multiattack).

Spending is consumed on the coordination document before any die, logged as `use` events, and lasts until the subject's next explicit `begin_turn`.

**Bystanders (C7 remediation).** Every rule that turns on another creature names it (`pipeline/rpg/bystanders.py`). The named subject is read under its own binding and rechecked at commit.

**Residue for Codex:** which named creature is an *enemy* or an *ally* is the GameMaster's identification; no accepted state records allegiance.

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
| 4. Calculations, targets from authority, roster coverage | Met, pending review | `test_bounded_checks.py`, `test_weapon_attacks.py` (all nine ammunition weapons, incompatible ammunition), `test_masteries.py`, `test_zero_hp_lifecycle.py`, `test_creature_attacks.py`, `test_creature_clauses.py`, `test_creature_roster.py` (every C5 entry and Multiattack selection, no remaining boundary), `test_bloodied.py`, `test_linked_conditions.py`, `test_creature_types.py` (Ghast/Ghoul: ordinary non-Humanoid, Elf and non-Elf characters, recorded Elf/Dwarf Humanoids, Undead, familiar typing (familiar combat held, `test_familiar_limits.py`); refusals before any die; the species operation and its once-per-turn rule) |
| 5. Distinguishable failures; no partial application; `undetermined` only where admitted; player roll refused before pending | Met for the executable scope | E2E refusal tests: no Turn and no audit row; `pending_roll_requests` stays empty |
| 6. Independent subjects; commit recheck; atomic delivery-gated effects; holds | Met, pending review | Each subject and its holdings are rechecked at commit (`RpgTurnHold.recheck`, `require_holdings_unchanged`, `test_coordination.py`); subject effects and ammunition CAS commit with the Turn (E2E) |
| 7. End-to-end on the accepted successor published in disposable stores | Met, pending review | `test_bounded_d20_on_published_release.py` on the C8 successor: checks, refusals, hidden filtering, weapon attacks, edges, ammunition expenditure and rollback, a creature's linked grapple, a recorded species honoured by the Ghoul's Elf exception in a later Turn, a species whose creature moved before commit (rollback), an ineligible species |

## Architecture Notes

### CRD Issue 15c: Gaming Set and Musical Instrument kinds (13 October 2026)

**Built.** Each kind is its own proficiency (`equipment.md` "Tools"; the accepted `ToolVariantsFact`, stated per activity option):
- **State:** `ToolGrant.variant` and `ItemInstance.tool_variant` (migration 0042, `dnd5e_item_instances.tool_variant`) keep the exact typed `ToolVariant`. A recorded kind that is not one of the tool component's typed kinds is refused by state validation, by item identity (create, transfer, use and adoption) and by grant validation.
- **GameMaster input:** `tool_variant` selects the kind used; the scene lists held tools with their kind. A kind is required exactly for a tool with kinds.
- **Check:** the selected kind must be held (`missing_state` otherwise). Proficiency counts only from a validated grant of the same tool and kind. A grant of another kind is no proficiency; a grant recording no kind refuses `missing_state` for checks of that tool only, so the character's other checks still run.

**Named boundary (not a refusal).** A tool-choice `ChoiceRecord` (Soldier's Gaming Set, the Bard's three instruments) records the tool, not the kind: the kind lives only on the `ToolGrant`, validated against the tool's typed kinds and the source's typed selector (which admits any kind of that tool). No choice vocabulary for tool kinds was added.

### CRD Issue 15c C8: target creature types and the bounded species input (13 October 2026)

**Authority.** The Owner answered "Accept exact C8" and "Approve bounded species input" (`.claude/review-notes/issue-15c-c8-native/owner-acceptance-2026-10-13.md`; decision packet `codex-c8-owner-decision-packet.md`, `7a29c7cd…`).
- **Integration:** the reviewed schema-21 code (`056d3d4`…`bf3fb2d`) is integrated unchanged.
- **Recording:** the successor is recorded locally (`ead7fa9d…`). Only the acceptance evidence differs from the reviewed SIMULATED preview `a2d96264…`, which is preserved.
- **Further planning correction:** `issue-15c-c8-native/PLANNING-ADDENDUM-target-domain.md` supersedes the RAW-r2 "every non-Undead creature needs species input" wording.

**Ghast and Ghoul Claw.** Their rider save ("If the target is a creature that isn't an Undead or elf"; the Ghast's spares Undead) executes from the target's accepted type (`pipeline/rpg/creature_types.py`).
- **A spared target:** takes the hit's damage, rolls no save and gets no condition. The audit records `{"result": "excluded", "by": …}`.
- **Otherwise:** the save is made as before. The provenance records the type and its basis.

**Where the type comes from.**
- **Characters:** the validated species' `creature_type` fact. The recorded `creature_type` must agree with it.
- **Creatures:** the certified template's fact.
- **Departures:** a stored type that departs is trusted only through a represented source:
  - Find Familiar's named forms, with a choice within Celestial/Fey/Fiend and `summon.source` exactly the spell;
  - a template whose own fact is a choice (Find Steed), with its own summoning source.

**The ordinary domain** (`codex-elf-type-domain-classification.md`). The type is read only when nothing recorded can change it:
- active effects are recorded (`None` refuses);
- every effect is a reviewed mastery effect;
- no effect names an assumed form.

A bare or departing stored type, an unexecuted effect or a form refuses before any die. The visual form's header is never read.

**Elf.**
- **A character:** an Elf exactly when its species is `character_origins.elf`.
- **A non-Humanoid creature:** not an Elf, by the contrapositive of the accepted Elf ⇒ Humanoid. This is code-owned deduction, not a new fact or policy.
- **A Humanoid creature:** decided only by its recorded species. With none recorded, the Ghoul's Claw refuses before any die (the Ghast's does not ask).

**Bounded species input** (`creature_species`, a new certified operation, no dice).
- **Who may record it:** only a creature whose template's own type is fixed Humanoid. `monsters.md`:55 says every Humanoid stat block leaves species open, so all 26 Humanoid templates qualify.
- **What may be recorded:** one of the code-generated options, the accepted species whose own type is Humanoid (all nine).
- **Storage:** a `CreatureSpeciesSelection` (species, template, projection, override set) on the creature's own state document.
  - It is applied as a `creature_species` sheet effect by CAS when the Turn is delivered. A moved revision rolls the whole Turn back.
  - The delivered Turn's audit row records it (Invariant 11).
  - A selection under another template or binding is stale. Reads refuse it, and it may be recorded again.
  - A current selection is never changed.
- **Shared rules:** the state validator applies the same eligibility rule to every write path.
- **Bounds:** it grants no traits, numbers or type change.
- **Visibility:** the selection is GameMaster state. A hidden record reveals nothing to the Writer, and the shown label is only "Species noted". Creatures are not in the player snapshot.
- **Timing:** within one Turn, a Claw is checked before the species has an effect, so it refuses; it needs a later Turn.

**Recertification.** `CERTIFIED_RELEASE` moves to `e4f8f4fb`; the adapter and manifest are now `15c-d20-4` and `15c-manifest-4`.
- **Evidence:** regenerated in `recert/governing-components.json`.
- **What moved:** against C7, only `creature_attack` changed, by exactly the ten type components it now reads (nine species `creature_type` components and `spells.find_familiar/effect`).
- **New operation:** `creature_species` is new, certified over the species components and the shared check procedure.
- **Unchanged:** no other operation's governing set or fingerprint moved.
- **Per subject:** creature templates stay certified per subject.

**C8 execution review corrections** (`codex-c8-execution-review.md`, at `555be9a`):
- **Duplicate species in one turn:** a turn that records one creature's species twice, same or conflicting, refuses in the whole-turn preflight. This happens before any die, even after an otherwise valid rolled operation (`service._species_once`). Independent creatures may each record one.
- **Familiar source limits** (`pipeline/rpg/familiars.py`; Find Familiar: "A familiar can't attack"; at 0 Hit Points it disappears, leaving what it carried; it can be dismissed). The type proof grants none of these. For a creature summoned by any familiar source:
  - its attacks refuse;
  - anything naming it while not recorded present refuses (unrecorded: missing state; pocket dimension or gone: invalid selection);
  - damage to it refuses before any die, on every path. This is `damage.preflight` and `take_damage`, where weapon, creature, Graze and save-effect damage converge.
  - Its death save, first aid and recovery attestations refuse too: its zero-HP consequence is not executed, and the ordinary monster or character path is not that consequence.
  - These are holds, not Familiar-lifecycle coverage. Ordinary creatures are unaffected.
- **Hidden species:** a refused repeat selection no longer names the held species, since a refusal's text can reach the player. The backend audit keeps the exact identity.

**Holds that remain (refused before any die; not coverage, not accepted exclusions):**
- a Humanoid creature with no recorded species, for the Ghoul;
- familiars from Wild Companion (Fey) and Pact of the Chain (extra forms), whose type authority is not represented;
- a familiar attacking, absent, taking damage or on a zero-HP path (above);
- Find Familiar's other Challenge Rating 0 Beast forms;
- the Vampire's mist form (no state records it);
- any target in an assumed form or under a non-mastery active effect: transformations are not executed.

**Sibling audit** (type predicates):
- **Save-effect target clauses** naming creature types or species (`creature_effects`): the roster admits no such entry. They still refuse (`out of scope`, unchanged).
- **The roster harness:** it has no boundaries left. Both Claws prepare and resolve (`test_creature_roster`).

### CRD Issue 15c C7 remediation and completion (13 October 2026)

- **Creature roster, code-owned and fail-closed** (`pipeline/rpg/roster.py`; C5 Owner packet Decision 4).
  - **Why a roster:** some entry mechanics are typed nowhere. Examples: a Balor's no-Reactions, burning, maximum-HP loss, lycanthrope form, Sunlight Sensitivity. Typed facts cannot show those, so the admitted attack and save-effect entries are listed explicitly.
  - **What is admitted:** entries the reviewed C5 capability marks executable, and entries whose every C5 blocker has since been settled by an approved contract and is executed. Those blockers are Pack Tactics, Recharge at turn start, area and range selections, and turn-bounded ends.
  - **Pinning:** `test_creature_roster` regenerates the roster and pins it to `capability.json` (`6037ea70…`). It also runs every C5 entry and Multiattack selection through the adapter preflight.
  - **Positions:**
    - Every admitted entry prepares and resolves in a scenario built from its own typed targeting.
    - Every entry outside the roster refuses.
    - Held: the Ghast and Ghoul Claw target-type exclusion, pending boundary review.
  - **For Codex:** this is a new mechanism implementing an accepted decision. Please review the settled-blocker table.
- **Bloodied is adapter procedure** (Codex classification, `codex-bloodied-linked-conditions-classification.md`).
  - **The predicate:** `2 * current <= maximum - reduction`, over recorded Hit Points, with temporary HP excluded, read from the turn's advanced state.
  - **Certification:** with `glossary.bloodied/bloodied` and `play.damage_and_healing/{bloodied,hit_points,temporary_hit_points}`, in every operation it can affect.
  - **Bounds:** there is no prose parse and no new source fact. An override of the rule refuses as incompatible certification. This confirms the earlier classification rule (universal arithmetic is adapter procedure).
- **Linked conditions, state contract extension** (ADR-015 Decision 8; 2b distinct instances).
  - **The field:** `ConditionInstance.lasts_while_instance` ties a condition to the Grappled instance the same hit applied.
  - **Validation:** the state validator refuses a dangling or malformed link, and `clear_condition` removes the dependants of what it removes.
  - **Bounds:** this is not a general condition engine. Grapple escape and other dependency graphs remain unexecuted.
- **Discovery and spatial dependencies (Codex delivery review).**
  - **Discovery scans:** the aura and turn-bounded-effect scans' absences rest on a story snapshot of every subject's revision, taken before the scans and required unchanged at commit (`turn.require_story_unchanged`).
  - **Spatial facts:** spatial facts about named bystanders and aura holders are invalidated by movement earlier in the turn.
- **Before any die.** Every refusal-capable read an operation could make happens in preflight. A refusal after an operation's own first die is a `PreflightGapError`.
- **Established, not speculative, prerequisites.** A rule needing a condition as a positive prerequisite (Trample) reads the target's established conditions (`conditions.established`). It never reads the preflight's projection of what an earlier operation might apply.
- **Enemy cohorts.** "Each enemy" save effects (the Sphinx roars) take the GameMaster's named enemies in the area as a typed, audited cohort, under the existing bystander contract. No allegiance is derived.
- **Target creature types (held prerequisite).** Ghast and Ghoul Claw's typed rider exclusions (Undead; the Ghoul also excludes elves) need each target's source creature type, which no accepted fact assigns (Codex classification). Raw candidate C8 (`.claude/review-notes/issue-15c-implementation/candidate-c8/`) proposes the 345 source assignments under a schema-21 `creature_type` family. Until its exact native packet is accepted and recorded, the two Claws refuse. That refusal is interim disclosure, not coverage or exclusion. The Ghoul's elf exclusion against creatures has no represented source and is surfaced as an open point.
- **Ammunition holdings.**
  - **Mechanism:** expenditure is an `item_quantity` sheet effect, applied to holdings by CAS at commit (`holdings.spend_item`) and never to state.
  - **Reconstructable:** the delivered-turn audit row records it (Invariant 11).
  - **Depletion:** a zero quantity removes the holding, because the schema keeps `quantity >= 1`.
  - **Excluded:** ammunition recovery after a fight remains excluded; its source rule is preserved, not executed.
- **Supersessions of the notes below:**
  - The "C2 holds most of the roster" and "merge sequencing" bullets describe the state before C5 and C7 were accepted. The roster they held now executes.
  - The monster stat-block `EXCLUSIONS` entry they mention is already gone from the manifest; creature entries outside the roster refuse instead.

### Deviations and boundaries, stated explicitly (history, 12 October)

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
