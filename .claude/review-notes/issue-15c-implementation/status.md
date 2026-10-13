# CRD Issue 15c — implementation status

- **Branch and head:** `codex/issue-15c-bounded-d20`. Local commits: `eb60d9f` (implementation), `abca92d` (review notes) and a C2 review-notes commit. Baseline `e83018c` = remote main.
- **Not pushed. No PR.** Stopped at the semantic-acceptance gate for Codex review.
- **Scope:** #191 as updated (body SHA-256 `8225e1b6…57a2`). It adds creature attacks, bounded Multiattack and their saves/effects, the tool-addressing and omitted-source repair, and individual conditional-creature assessment. The G1 oracle `2ccbaeba…1258` is unchanged.
- **Process:** Opus 5.5 at medium effort, with the separate Opus 5.5 Advisor consulted on the approach, the candidate scope and completion.

## Latest (14 October 2026): Codex creature correction review (P1, P2)

From `codex-creature-correction-review.md`, adopted by the parent as ordinary implementation:
- **P1, `78e0efa`.** A speculative condition never establishes a positive prerequisite.
  - Trample's "has the Prone condition" now reads `conditions.established()`, which excludes the preflight's `possible:` instances and what they imply.
  - Gore followed by Trample against a standing target refuses before any die. An initially Prone target still executes.
- **P2, this commit.** The Sphinx roars' "each enemy" is a typed, audited cohort.
  - `CreatureSaveEffectSelection.enemies_in_area` holds the GameMaster's bystander identification, read under each subject's binding, never the source. It is also a spatial dependency.
  - An "each enemy" entry's targets must be exactly the named enemies. Any other entry refuses a cohort.
  - The scene lists `enemy_only_effects`; the caller schema and prompt are reconciled.
  - **Controls:** a missing cohort, a non-enemy target, an enemy that is not targeted, the source named as an enemy, and a cohort on a non-enemy entry all refuse.

Ghast and Ghoul stay held behind raw candidate C8.

## Earlier (14 October 2026): raw candidate C8 (target creature types) ready for Codex raw review

**Scope.** Codex's `codex-creature-type-boundary-classification.md` was adopted. Ghast and Ghoul Claw stay promised, held and incomplete; `BOUNDARIES` is an interim disclosure only.

**Candidate.** `candidate-c8/`; nothing is accepted, minted or recorded, and `src` is unchanged.
- **`c8.json`** (`81991739…20cd6`): 345 `creature_type` facts.
  - 336 creature templates: every `creature_size` profile.
    - 328 direct;
    - 7 swarms (I1);
    - Find Steed's `type_choice`.
  - 9 species: "Humanoid", on their existing prose-bound `creature_type` component.
- **Proposed schema-21 delta:** documented in `schema-21-delta.md`, not applied.
- **Forms:**
  - 12 kept (I2);
  - Incubus/Succubus Form uses the other stat block;
  - Vampire held.
- **Held:**
  - Ghoul against non-Undead creatures. A creature's elf status is unrepresented, and an absent tag is not evidence.
  - Vampires.
  - Stored type departures.
  - Form-changing spells.
- **Affected batches:** monsters 235, animals 95, character-origins-feats 9, spell-descriptions 4, magic-items 2. The other 19 batches are untouched.
- **Validation** (`validation.json`):
  - every quote equals its cited line;
  - one fact per record;
  - closed vocabulary;
  - claim spans and one batch per row;
  - interpretation evidence on its cited lines;
  - deterministic across two runs.

**Next gate:** Codex raw review. After that, a SIMULATED native preview and pinned packet in an isolated worktree, then the Owner's exact acceptance. No type-dependent execution before then.

**Delivery:** `codex-delivery-correction-review.md` clears the four delivery findings at `4a39f27`. The six creature-shape and before-dice repairs await independent implementation review.

## Earlier (13–14 October 2026, overnight): Codex execution remediation

**Codex reviews:**
- `codex-c7-recording-final-review.md`: the C7 recording is CLEARED.
- `codex-creature-execution-final-review.md` and `codex-delivery-execution-final-review.md`: six findings in four families, now addressed.

| Family | Fix | Evidence |
| --- | --- | --- |
| Before-dice completeness | `a7160eb`: condition immunity (direct, linked, rider-save, clause Prone) and Bloodied HP are read in `prepare`, and in save-effect `prepare` for each target. A refusal after an operation's own first die is a `PreflightGapError`. | `test_before_dice.py`: Wolf, Purple Worm and Allosaurus with recorded immunity, a Swarm without HP, and the Lion's Roar, each with zero dice; a too-large target's immunity is not consulted. |
| Positive roster coverage | `ed18d22`: Trample (has Prone), the Sphinx roars (the GameMaster's enemies) and Dragon Turtle Steam Breath (underwater clause) execute. | `test_creature_roster` now requires every admitted entry to prepare and resolve in a scenario built from its own typed targeting. |
| Mechanical dependency closure | `f15c175`: spatial subjects include named bystanders and, for save-forcing operations, every aura holder. `4a39f27`: a story snapshot taken before the discovery scans, required unchanged at commit. | Push → Pack Tactics and Push → close combat refuse with zero dice. End to end, an unnamed subject changing, or a subject being added, fails the turn; the negative control without the guard delivered (2 failed). |
| Physical/source identity | `2570029`: Light/Nick compare item instances (two Daggers qualify; the same Dagger refuses); free-hand loading follows the weapon's classification, not the declared grip. | `test_masteries.py`, `test_weapon_attacks.py` (Hand Crossbow, Pistol, Sling, Blowgun) |

**Held, under independent boundary review** (`codex-creature-type-boundary-classification.md`, pending): the Ghast and Ghoul Claw rider saves exclude Undead (and Elf) targets, and no accepted authority types a target's creature type or species.
- **Disposition:** only that target-tag-dependent execution refuses.
- **Not claimed:** this is not an accepted exclusion, and the roster is not claimed complete.

**pip-audit:** the CI command passes unchanged (`codex-dependency-gate-disposition.md`); the earlier "needs disposition" note is superseded.

**Interrupted:** a disposable full end-to-end file run was stopped at the coordinator's direction. It gives no full-file verdict. The final full pytest via the supervisor remains required.

**Focused diagnostics** (not acceptance):

| Run | Result |
| --- | --- |
| RPG suite | 430 passed |
| New end-to-end tests | discovery ×2 and holdings, each passed individually |
| `test_actor_turn_edges_commit_with_the_delivered_turn` | passed |

## Earlier (13 October 2026, end of session): admitted roster executing; awaiting Codex review and final gates

These commits follow the C7 recording report below; all are local, none pushed.

| Commit | Change |
| --- | --- |
| `10ddbfd` | **Bloodied.** A certified universal predicate (`damage.bloodied`). Pins: `weapon_attack` `c300a9ca`, `creature_attack` `a3dcf934`, `creature_save_effect` `e09799e6`. Creature save traits now execute. |
| `ae011bb` | **Linked Grappled→Restrained.** `ConditionInstance.lasts_while_instance`, a state validator, and a cascade on clear. |
| `acf6432` | After the mouther's lethal Bite, first aid on its target refuses before any die. |
| `b5051d8` | Architecture Notes reconciled on the C7 successor; the manifest names the ammunition-recovery exclusion. |
| `9b63bce` | End to end: holdings that move after the read fail the turn at the recheck, with nothing spent. |

Sibling audit: `sibling-audit-creature-silent-drops.md`.

**Focused diagnostics only** (not acceptance or full-gate evidence):

| Run | Result |
| --- | --- |
| RPG suite | 412 passed, in two runs |
| End-to-end file | 15 passed, plus 2 new end-to-end tests passed individually |
| Publication | 27 passed |
| Oracle and selection | 139 passed |
| Committed census | 2 passed |
| State service | 184 passed |
| Model and persistence | 21 passed |

**Repository-wide static gates on `9b63bce`:**
- black, ruff and mypy are clean;
- detect-secrets passes on all 274 changed files.

**pip-audit reports five `chromadb` 1.5.9 advisories.** They are `PYSEC-2026-311` (twice), `-3813`, `-3814` and `-3815`, and none lists a fixed version. The dependency was not changed by CRD Issue 15c, and remediating it is infrastructure work, not absorbed here. It needs a decision by the coordinator or Owner before merge readiness.

**Remaining before merge readiness:**
1. Codex review of the C7 recording and of this implementation (roster, traits, clauses, Multiattack, ammunition, Bloodied, linked conditions).
2. Full pytest on the stable head, via the independent supervisor.
3. The pip-audit disposition.
4. Unchanged CI, then push and PR (no merge).

## Earlier (13 October 2026, C7 recorded): C7 accepted, recorded locally, ammunition executing

**C7 is Owner-accepted**: the exact consolidated packet `4912928f…eb2c` (`../issue-15c-c7-native/owner-acceptance-2026-10-13.md`). The Owner also authorized integration and recording (`owner-c7-integration-2026-10-13.md`). The earlier "C7 integration blocked" note is superseded.

**Integrated.** The reviewed preview commits are now on this branch:

| Preview commit | Branch commit |
| --- | --- |
| `221a8e7` | `db60370` |
| `2d9f694` | `df9c601` |
| `ed23cb7` | `02fb067` |
| `3166f22` | `ddda49b` |

**Recorded (`952ae53`):** `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c-c7.json`, SHA-256 `2853f30a832ca581c9d4169b82d0c360f3d6a2d78f0ad8980de9997eef51f373`.
- **Identities equal the packet.** The recorded file differs from the accepted preview in its receipt evidence only (next bullet).

  | Item | Value |
  | --- | --- |
  | Oracle | `cb04163b…5ef6e` |
  | Projection | `8446ab6b-be75-5999-8a9b-74fa133c030a` |
  | Payload | `cffcdbfa…eb65a` |
  | Proposals | `1e7b63d3…` (character-origins-feats), `b8c65454…` (equipment) |
  | Schema | `5d-representation-schema-20` / `759dcc1f…` |
- **Evidence and identity checks** (`../issue-15c-c7-recording/`: `record_successor.py`, `owner-acceptance.json`, `recorded-followup.json`):
  - **What differs from the preview:** only `reviewer`, `accepted_at` and `rule`, on the two batches' 643 records and 47 review units. Rows are matched by identity.
  - **Untouched rows:** they keep their order. Canonical evidence order reads `accepted_at`, so the touched rows' position follows the real recording time.
  - **Unchanged:** the C5 successor `23e5d8e0…`, G1 and the predecessor.
  - **Checks that passed:**
    - native validation found nothing;
    - persist, reconstruct and re-identify is clean;
    - the read-only gate passes in a private store copy.
  - **Verify mode:** a write-once rerun rebuilt the file byte for byte, at the same recording time `2026-10-13T09:56:00Z`.
- **Reproducibility.** The pinned preview `d661cc3b…` lives git-ignored in worktree `agent-afb6123d0b7851456`. `build_c7_preview.py --twice` regenerates it byte for byte, so the recording stays reproducible if that worktree goes away.
- **Selection and packaging:**
  - C5 is superseded by digest.
  - Packaging ships the C7 successor.
  - The oracle, packaging, succession, committed-authority and publication tests follow it.
  - `.secrets.baseline` covers the new and changed review files.

**Recertified (`0da06c9`).**
- `CERTIFIED_RELEASE` moves to projection `8446ab6b`; versions are now adapter `15c-d20-3` and manifest `15c-manifest-3`.
- Component evidence was diffed against C5: only `weapon_attack` changed (`463322bf` → `a5fe16ae`), by adding the five typed supplies it now reads. No other governing component moved.

**Ammunition executing (`0da06c9`, `246e6ae`).**
- **Selection:** a held ammunition item is named and checked against its typed supply, the weapon, and the quantity.
- **Expenditure:** one per attack, hit or miss, applied by CAS on the read revision in the Turn's transaction. The last one removes the holding.
- **Preflight:** counts every shot of the turn against the quantity read.
- **Constraints kept:** Loading, free-hand loading and action accounting are unchanged.
- **Flat damage:** the Blowgun's flat damage now executes.
- **Feat categories:** Origin-category eligibility certifies (Skilled under an ASI).
- **Evidence:**
  - all nine weapons fire, hit or miss;
  - incompatible ammunition refuses, including sling versus firearm bullets;
  - CAS, stale-revision, overspend and removal behave;
  - Loading and action-budget refusals roll no dice;
  - end-to-end, a shot expends one, the last arrow is removed, and a failure after expenditure rolls everything back.

**In progress:** Codex's Bloodied and linked Grappled→Restrained classification (`codex-bloodied-linked-conditions-classification.md`). Those ten C5-positive shapes stay visibly refused until then.

**Still required:**
- Codex review of the roster, traits, clauses and Multiattack implementation;
- Architecture Notes reconciliation;
- the stable final head, full gates via the independent supervisor, and CI.

There is no push, PR or merge, and nothing is published or activated.

## Earlier (13 October 2026): coverage gaps and C7 integration permission stop (superseded by the authorization above)

**`3741c60`, C5-positive coverage gaps:**
- Flat printed damage is its amount (`damage.fixed_part`).
- Goblin damage under Advantage executes.
- Creature standing traits apply on both sides (`attacks.creature_traits`).
  - **Sibling defect, patched:** a target creature's trait on attacks against it was silently ignored. The Steam Mephit's Blurred Form gave no Disadvantage to weapon or creature attacks against it.
  - Non-Advantage trait effects now refuse instead of being skipped.
  - Blood Frenzy reads the target's recorded HP.
- Optional non-attack uses within a Multiattack are simply not made (Dryad, Erinyes).
- Pummel reads the target's recorded Grappled referent.
- `test_creature_roster` runs every C5 attack/save entry and every Multiattack selection through the adapter preflight.
  - Every C5-positive shape executes, except the named `BOUNDARIES` below.
  - Every entry outside the roster refuses.

**Boundaries for Codex (C5-positive, refused, not counted as coverage):**
- **Bloodied ×7:** the five animal swarms, Swarm of Crawling Claws, and the Berserker's Bloodied Frenzy.
  - `glossary.bloodied` is prose-bound in the accepted authority ("A creature is Bloodied while it has half its Hit Points or fewer remaining", `rules-glossary.md:269`). C5's capability assumed "recorded HP", but no typed threshold or adapter procedure exists.
  - **Options:** a typed Bloodied fact in a future candidate, or an accepted code-owned adapter procedure. Owner or Codex classification is needed.
- **Linked Grappled→Restrained ×3:** the Purple Worm Bite (also its Multiattack) and the Remorhaz Bite. No state contract ends one condition instance with another.

**C7, Owner-accepted 2026-10-13** (`issue-15c-c7-native/owner-acceptance-2026-10-13.md`, packet `4912928f…eb2c`):
- **Blocked.** Integrating the reviewed preview commits into this branch was denied by the session's permission classifier as a shared-resource modification. The commits are `221a8e7`, `2d9f694`, `ed23cb7` and `3166f22`.
- Recording the successor and dependent ammunition execution therefore wait for the human to authorize that integration in this session.
- Nothing was integrated, recorded or executed.

## Latest (13 October 2026; relay pipe stale, so this is the durable report)

Nothing is pushed and there is no PR. No C7 acceptance, recording or execution has occurred.

**Main branch `codex/issue-15c-bounded-d20`, newest first:**

| Commit | Change |
| --- | --- |
| `bd5ef82` | Code-owned creature roster (C5 packet Decision 4) |
| `6526674` | Multiattack replacements |
| `b082262` | Creature clauses execute or refuse |
| `1ecbb87` | Fix to a test that was already red |
| `4b3ff07` | Bystanders |
| `c17aadc` | Public labels |
| `5513bd5` | Hand/grip facts |
| `56d9dec`, `bf401a7` | Action accounting |
| `545c6f4` | Use events, no-write recheck and holdings recheck |
| `fcab52d` | Template certification and fixed-DC scoping |

- **`1ecbb87`:** `test_no_refused_candidate_is_selectable` was red since the C5 recording, which never named its eleven identities. It now passes.
- **`b082262`:** previously, 107 entries that execute ignored their same-entry `Clause*` facts. Now every clause is executed or refused before any die.
  - The ten C5-positive shapes execute:
    - size/charge predicate, where the charge is the OD-15c-1 `moved_straight_toward_target`;
    - Prone;
    - Allosaurus follow-up Bite (`follows_up`, adjacent, `not_triggered` on a miss, no action of its own; adjacency instead of a use key);
    - Chimera Advantage damage;
    - Gibbering Mouther kills a target it reduces to 0;
    - returning weapons and underwater Fire Resistance, which have no effect here.
  - Save effects refuse any clause; no C5-positive save effect prints one.
- **`6526674`:** a replacement by another attack entry is admitted, and each part is certified by its own preparation.
  - Dragon Turtle Bite/Tail/Bite runs through the service turn.
  - Roc Talons refuses by its own part. Spell and save-effect options stay refused.
- **`bd5ef82`, the silent-drop family.**
  - **The defect:** typed facts cannot show untyped entry mechanics. Examples: the Balor's no-Reactions, burning, maximum-HP loss, armor degradation, lycanthrope form, Sunlight/Light Sensitivity, Aura of Authority. Entries with such mechanics executed and dropped them.
  - **The roster:** `roster.EXECUTABLE` admits:
    - entries C5 marks executable;
    - entries whose every C5 blocker has since been settled. Settled means Pack Tactics (bystanders), Recharge at turn start, area/range selections (OD-15c-1) and turn-bounded ends (OD-15c-2), each executed. The test lists them as `SETTLED`.
  - **The pin:** it is pinned to `capability.json` `6037ea70`.
  - **Effect:** every other attack or save-effect entry refuses before any die.
  - **For Codex:** this is a new mechanism, implementing an accepted decision. Please review the settled-blocker table.

**Remaining C5-positive coverage gaps (in progress):** C5 marks these executable; they refuse today.

| Family | Items |
| --- | --- |
| Flat damage printed as `average` only | 17 |
| Rider conditional damage (swarms, goblins) | 9 |
| Berserker and Sahuagin Frenzy circumstances | 2 |
| Steam Mephit Blurred Form | 1 |
| Purple Worm and Remorhaz linked conditions | 2 |
| Dryad and Erinyes Multiattack fit | 2 |
| Glabrezu Pummel's target condition | 1 |
| Pirate Captain: positive Multiattack whose Rapier is non-positive in C5 | 1 |

Three more positive Multiattack selections fail only through these parts.

**C7 preview (`codex/issue-15c-c7-preview`, worktree `agent-afb6123d0b7851456`):**
- Commits `221a8e7`, `2d9f694`, `02f9bc8` (the census fix), `ed23cb7` and `3166f22` (the `codex-c7-native-review` correction).
- **Validator correction:** the relational rule now reads only structurally admitted facts. Three malformed-structure regressions run through `validate_representation`. The schema pins and preview identities are unchanged, so the evidence is reused.
- **`OWNER-PACKET.md` (`4912928f…eb2c`):** one consolidated acceptance including I2.
- **Verification:** the implementing session reran the builder independently; the report was byte-identical.
- **Next gate:** Codex confirmation, then the Owner.

## Earlier (12–13 October 2026, continuation; relay pipe stale, so this is the durable report)

**Local commits since `86c0436` (not pushed, no PR):**

| Commit | Change |
| --- | --- |
| `2904640` | Saving-throw helper and timing contract §G |
| `b58a168` | Fix: turn-state sequencing and condition coverage |
| `729d58a` | Actor-turn edges, coordination row, migration 0041, death save |
| `5e3a7a4` | Knockout, first aid, OD-15c-2 attestations |
| `9e9eb71` | Masteries; fixes a latent hit-audit UUID serialization defect |
| `199cc92` | Cleave and per-turn uses |
| `57976b7` | Ammunition refusal reason |
| `0822771` | Lifecycle preflight |
| `46f8b50` | Production reachability: the GameMaster previously saw no ids; now it gets a GameMaster-only scene block |
| `0c873cc` | Creature attacks |
| `da179a5` | Fix: one hit's damage terms judged as one damage |
| `b33daa5` | Raw candidate C7 packet |
| `f392913` | Bounded Multiattack |
| `c3cb332` | Creature save effects; usage limits and Recharge |

**Raw candidate C7** (`candidate-c7/`, `c7.json` `bf2a269c…fa77`) consolidates C6-r2 with ammunition identity under the Owner's ammunition directive.
- It proposes schema-20 `ammunition_supply`.
- Interpretations I1–I3 are flagged; I2 (firearm ↔ Musket/Pistol) is the weakest and comes with an Owner alternative.
- It raises three residues: Loading/action economy, free hand, depletion.
- **Next gate:** Codex raw review.

**Still open:**
- Implementation: everything executable without new authority or classification is implemented. Ammunition execution waits on C7's acceptance and the Loading, free-hand and depletion residues.
- For classification: action economy (Nick/Light/Loading), bystander contributors, cross-Turn edge manufacture.
- The self-derived fingerprints in `recert/governing-set-changes.md` need independent recert review.

**Full gates:** wait for the stable head after C7 acceptance, recording and execution.

## Current (13 October 2026)

**Commits** (local only, not pushed):
- `3f0ba29`: the successor recording; G1 superseded; schema-19 tests; grant validation; difficulty, tool and Initiative checks.
- A follow-up commit: the feat-entitlement residues, raw C6/C6-r2 and the review notes.

**Focused diagnostics only.** These are separate runs; none is full acceptance and they are not summed:
- 241 passed: selection, packaging, publication and E2E. Some sources changed during this run; the invalidated cases were rerun.
- 137 passed: RPG.
- 345 passed and 1 failed, the failed case then fixed and rerun: the final rerun.
- 86 passed: `test_bounded_checks` after the residue fixes.

**Approved inputs.** The Owner approved bounded GameMaster spatial facts and instance-linked timing attestations (`owner-context-decisions-2026-10-12.md`). Combat/state implementation is in progress under the corrected `boundary-input-contracts.md`.

**Raw candidates.** C6 (`eb014b30…`) is preserved. C6-r2 (`699718ff…`) awaits independent review. Neither is accepted, and dependent semantics stay held.

**Coverage boundary to raise with Codex.** Fighting Style feats (Fighter 1, Paladin/Ranger 2), Savage Attacker (Soldier) and Defense are attack/AC contributors. Until typed and executed, an attack by or against a character holding them refuses.

## Successor recorded; implementation continuing (12 October 2026, Owner accepted the exact native C5 packet)

- **Recorded:** `src/afterworlds/ingestion/mechanical/oracles/srd-5-2-1-corpus-8781d4e0-a3b-15c.json`.
  - File SHA-256 `23e5d8e0fac60e3f5417b3a41e40e6f475366dd385856f38c42104f4dd264f69`. This is the real recording; the reviewed simulated preview `cd9d1d27…` is preserved unchanged.
  - Oracle identity `000c4c10…6e76`, projection `44f212d5…` and payload hash `ed8e21dc…` equal the accepted packet.
  - Only `reviewer`, `accepted_at` and `rule` differ from the preview, and only on the eleven batches.
  - Evidence: `../issue-15c-recording/` (`record_successor.py`, `owner-acceptance.json`, `recorded-followup.json`).
  - Re-verified (write-once verify mode) after the closed-type fix below: byte-identical, 0 native findings, gate passes.
- **Supersession landed (12 October 2026, through the scoped native-edit authorization).** G1's digest `2ccbaeba…` is in `oracle.SUPERSEDED_ORACLE_SHA256`. Packaging ships the successor and excludes G1. The successor is the release's one claimant. Committed in `3f0ba29`.
- **Schema-19 native contract fix.**
  - Schema-19 nested value objects (`DamageTerm`, `Rider`, ...) joined `_CLOSED_TYPES`, so the structural and version-legality walkers now descend into them.
  - The schema hash is unchanged (`3734ccf7…`) and the accepted successor re-verifies.
- **Observation for Codex:** three `EntrySubject` members (`amulet_wearer`, `rider`, `self_and_allies`) are admitted by the accepted schema but carried by no accepted fact. C5 states them only on unminted prose entries.
- **Test reconciliation (schema 19), focused only:**
  - **Edits:**
    - `_schema_pins` current → 19 and the 18→19 crossing;
    - round 7/9 and schema 12;
    - the literal lift chains;
    - the legality `SCHEMA_19_ONLY` (235 real exemplars, `data/schema_19_exemplars.json`);
    - 21 invariant-closure rows (`data/schema_19_invariant_cases.json`);
    - fact-family exemplars;
    - `bounded_oracle.json` lifted 18→19 as the G1 precedent did (+17/−2);
    - the identity canary, the scoped "19" check and the collision detector.
  - **`fields:` loci:** the schema-19 invariant loci use a `fields:` prefix; the closure test admits it, as schema 5 admitted `component`. Changing it would move the accepted hash.
  - **Results:** 2,207 + 1,920 focused tests passed after the fixes. Not full-suite evidence.
- **Boundary:** `boundary-input-matrix.md` was sent to Codex. Its classification is `codex-combat-state-boundary.md`, relayed; it requires corrections. Combat/position/timing state stays held until the corrected selector and timing contract.

## Native preview (12 October 2026): SIMULATION, Owner semantic acceptance HELD

**The current state is a review-only schema-19 native preview** of the exact C5 source contract, in `../issue-15c-native/`. Start with `OWNER-ACCEPTANCE-PACKET.md` there.

**State:**
- Uncommitted and unstaged.
- Working-tree src changes: `representation.py`, `schema_lift.py` and `projection.py`. These are a pure insertion with 2 replaced lines.
- One test pin file changed, labelled provisional.
- C1–C5, G1, the predecessor and the isolated store are byte-unchanged.

| Item | Identity |
| --- | --- |
| Schema 19 | `3734ccf7d6be7f25e0a0d7c0395121c5525afcb87144f5cf9d6895e03c1cd18f` (lift `5d-lift-schema-18-to-19`) |
| Preview file | `cd9d1d27428a1525955f83091125489e96bbc7bd0977bb9f3ce83933883a20d3` |
| Oracle identity | `000c4c108daf609c26eb9ae9f1197a26eef6fb80a3cb5c788f9e89ba20ad6e76` |
| Projection | `44f212d5-32dd-5469-8f05-f0d236492347` / `ed8e21dc…5188` |

**This supersedes the earlier preview Codex pinned** (`aa9fe91e…` / schema `85896c…` / `0d2ea513…` / `37c56dbd…`).
- **What changed:** only the schema descriptor. A focused test found Python class names in one invariant's rule text; it was reworded, and the schema-numbered invariant ids were renamed. That changed the hash and every identity bound to it.
- **Why the content is believed unchanged:** the earlier bytes were overwritten, so there was no direct diff. Both runs matched G1 identically under `verify_preview`, with the same delta. Per-batch counts are equal, and `reconcile.json` is byte-identical. The packet has the old→new table.

**Codex reports applied:**
- `codex-native-tool-selection-review.md`: `tool_activity` identities; the identical-option collapse was removed.
- `codex-native-proof-review.md`: hard placement failures; identity-level reconciliation; ordered preservation of the 13 untouched batches; possessor agreement; merge inspected, with no conflict.
- `codex-native-ac-mapping-review.md`: the nested Shield relocation wording.
- `codex-native-c5-review.md`: the C5 wording in the correspondence.
- `codex-native-schema-failure-classification.md`: the provisional pin; the scoped `"19"` assertion; full-shape object comparison; the declared context-shared vocabularies.

**Evidence:** focused only; no full suite and no CI. The packet has the list.
- `verify_preview`: 36/36.
- The build is deterministic across two runs.
- The focused identity test file: 1 failed, 56 passed. The failure is the historical schema-18 `bounded_oracle.json` fixture, which is landing work.

**Blockers:**
- Owner semantic acceptance of the exact identities.
- Landing requires the accepted successor to be recorded natively in the same change, because a schema-19 build refuses the schema-18 G1 oracle.
- The other schema-pinning tests and fixtures.
- `.secrets.baseline`, full gates, CI and Codex review.

## Candidate

**C5 is current: a raw candidate (12 October 2026), uncommitted and unstaged.** It applies all of `codex-c4-review.md`, `codex-c5-grant-family-addendum.md`, `codex-c5-provisional-linkage.md` and `codex-c5-provisional-roster.md`. See `candidate-c5/README.md` for family dispositions, conservation, fidelity, grants and holds.

| Part | SHA-256 |
| --- | --- |
| C5-A | `866f2c132b974ec2c895c269c09fc5de554b881be5a94699faa8c1188b9687c9` |
| C5-B | `187c041b8de8edcffe16e2c606b11c071b90b438dc3be2c68cb8a1a3a97df3f6` |
| C5-C | `bb3761b955f06d94665e86eb817f38da16198069fea9c5919fb98d87db476ad4` |
| Capability (not source) | `6037ea70246c24e478d97c5f7938f3d695802bf6b19284c0c883864af9e3efe6` |

**Checks**, from `derive_c5.py`:
- Two runs were byte-identical.
- C1, C2, C3 and final C4 are byte-preserved, checked before and after each run.
- Logical-entry conservation was re-read from the raw files without the parsers: 1,377 entries and 1,512 content lines, with 0 problems. It recovered 135 continuation lines that earlier candidates dropped.
- Untyped clauses are disposed piece by piece: 433 typed, 189 named unsupported engines, 6 with no mechanical consequence, and **0 missing source authority**.
- Source-to-field fidelity, checked without the readers, found 0 failures across 433 pieces (42 with a turn owner) and 83 grant facts.
- Number accounting is non-vacuous: `source_text` is excluded. It found 0 unaccounted.
- All 89 grant vocabulary fields resolve to typed selectors.
- The grant sibling audit is recorded in the README. Pact of the Blade is out of scope and refuses.
- 672 reused accepted payloads validate, with 0 failures.
- The reviewed source key names are pinned.
- The transition is still 11 of 24 batches.

**Grants:** save, weapon, armor, tool and Weapon Mastery entitlement facts have been added. The 12 checks are labelled as source-rule assertions; they are not runtime validation.

**Roster:** Raven Mimicry (DC 10), Green Hag Mimicry and Cube Transparent are now typed observer checks, and Zombie Undead Fortitude is a typed zero-HP save. Runtime grant validation and `checks.py` stay held.

**Before commit:** the C3, C4 and C5 JSON digests need audited `.secrets.baseline` entries.

**C4 (superseded by C5): a raw candidate (12 October 2026), uncommitted and unstaged.** It applies Codex's C3 source/capability contract, the grant trust-boundary finding and every Codex provisional C4 finding (`codex-c4-provisional-findings.md`; all patched; dispositions in the README). See `candidate-c4/README.md` for family dispositions, invariants, coverage, holds and the 11-batch transition.

| Part | SHA-256 |
| --- | --- |
| C4-A | `901083ec3c8c25e9cd95a638a537cf3db41d8277420e07f0fc2b5d023cd15e62` |
| C4-B | `f679b06c7e8e3513b9886716754db78b5a28c8cf254cb09d1e195b4f30765c08` |
| C4-C | `2c34a6f03fc081a0adbe3abf8f9e50f0dcad55e9c07469cf3204ccb36e68fb5f` |
| Capability (not source) | `2d884ffbb254af6849a8bd0b61cc5f2f2c4a84dd568f664e3606fb02cb783a8e` |

**Checks**, from `derive_c4.py`:
- Two runs were byte-identical.
- C1/C2/C3 digests are unchanged, checked before and after each run.
- General invariants, checked on the source parts alone: 0 scope-vocabulary leaks; 0 unaccounted printed numbers; 2 formula references, both resolved; 1 named target residue; 566 reused payloads validate with 0 failures; 29 of 29 gain-level references resolve to G1 `progression_entry` facts.
- Advisor completion review: its three blocking gaps were applied before this gate. Untyped clauses are now verbatim in source. Rider clusters are typed or classified as named mechanics or `missing_source_authority` (105). Applicability notes moved to capability.
- Sweep defect found and fixed: an escaping error had turned the scope sweep's `held` pattern into control characters, so earlier zero-leak results did not cover "held". It is restored, and a full-file sweep of C4-A/B/C is clean. A full control-character scan of the script and notes is clean.
- Advisor final check, applied:
  - every `affects` context is in a closed vocabulary that the rollup consumes, so Inscrutable and Bound refuse through real keys;
  - Swarm is conditional, settled by the source's exceptions rule;
  - all reaction triggers are read and the cluster labels audited;
  - Venomous Snakes keeps its poison in `hit_damage`.
- Housekeeping: git-ignored `__pycache__` directories under `candidate/`, `candidate-c2/` and `candidate-c3/` were deleted. They were bytecode caches from importing earlier scripts; no tracked or digested file changed.

**Grant trust boundary:** 91 grant/selection source facts are proposed, including:
- the multiclass skill grants;
- the background and Human origin-feat grants;
- feat prerequisites;
- the class ASI and Epic Boon feat choices;
- the Primal Knowledge and College of Lore skill grants;
- expertise gains, referenced to G1 `progression_entry`. Runtime validation and the `checks.py` and test corrections are held until native acceptance.

**Before commit:** the C3 and C4 JSON digests need audited `.secrets.baseline` entries.

**C3 (superseded by C4): a raw candidate (12 October 2026), uncommitted and unstaged.** It corrects all eight Codex C2 findings and the qualification residue. See `candidate-c3/README.md` for the per-finding dispositions, coverage, holds and prerequisites.

| Part | SHA-256 |
| --- | --- |
| C3-A | `aaa5a20fa59c8e4d9dbbd10120aa0b91e968cdb1bcd3616cb8b28632c2e49ff9` |
| C3-B | `bb086082b02e879706218a4ad016110d3c6d5b3f9cc095076adec1cc89095524` |
| C3-C | `36be82a04ff2c587af754ed9430dfdfeb9b6053b8073d80add716313069e422b` |

**Checks**, all from `derive_c3.py`:
- Two runs were byte-identical.
- `regressions()` passes for every cited defect and sibling.
- 529 reused-family payloads validate with the accepted `fact_from_payload`, with 0 failures.
- All 429 attack-roll lines across the four source files are parsed.
- The six C1/C2 digests are unchanged, checked before and after each run.

**Before commit:** the C3 JSON digests need audited `.secrets.baseline` entries; this pass may not write that file.

C1 and C2, below, are preserved and superseded.

**C2 (superseded by C3).** C1 is superseded but preserved; its JSON files are byte-identical.

| Part | SHA-256 | Holds |
| --- | --- | --- |
| C2-A | `a15aab18…` | Rules, weapons, all 25 tools, the stat-block conventions |
| C2-B | `0dd7538f…` | All 336 creature records: per-entry classification, section anchoring, block-level rollup |
| C2-C | `a21a5e89…` | Armor and character AC |

See `candidate-c2/README.md`: concordance, classification, assessed creatures, the schema and addressing delta, transition cost, holds, and the surfaced prerequisite.

**Nothing has been accepted. Native minting has not started** (cost stated: 7 of 24 batches).

Codex independent review of C2 is complete: **candidate corrections required before native preparation or acceptance**. See `codex-c2-review.md` for semantic defects, representation correspondence and the bounded correction brief. Claude remains stopped; that brief has not been dispatched.

## Implementation on `eb60d9f` (unchanged by C2)

See `review-handoff.md`. It covers:

- wiring;
- the manifest and certification;
- typed refusals;
- certified fixed-DC checks;
- player-roll refusal;
- the setup-turn ordering fix;
- prompt v2;
- the ADR and status reconciliations.

Every operation that depends on C2 is `HELD` and refuses visibly. The manifest's "monster stat-block actions" exclusion and its record-only tool wording predate the scope update. They are **superseded by #191 as updated** and are to be revised in the dependent implementation once C2 is accepted. That code was not touched, because candidate work is held.

## Evidence

**Gates passed:**
- Black, Ruff and mypy strict are clean.
- detect-secrets is clean, with documented false positives.
- pip-audit is clean with CI's ignore set.

**Focused diagnostics** are green. These are not acceptance:
- 51 bounded-check tests;
- 54 service and adapter tests;
- 330 orchestrator and API tests;
- 8 E2E tests on G1 published in a disposable store.

**Full `pytest -q` on `eb60d9f`: NO RESULT.**
- The serial background task was externally killed after about 85 minutes, shortly after Claude's session ended. The previous two-hour-limit explanation conflicts with the recorded timestamps; the exact kill mechanism is unproven.
- Its log (`gates/pytest-full.log`) holds partial buffered progress through 7%. No pass/fail verdict, exit marker or coverage result is recorded. See `codex-bounded-test-diagnosis.md`; the bounded diagnosis reran no tests.
- Per the dispatch, it was not rerun for candidate-only work.
- Exact-head CI, which has 8 shards, has not run.

**C2 checks:**
- deterministic re-derivation;
- the C1 digests are verified unchanged;
- the two-sided creature census matched 336 of 336;
- the attack count equals the source's 423;
- every A and C fact anchors to an accepted component.

## Open, not yet applied

These are drafts held outside the repo, to be applied after review or a new full run:

- tests for stale-binding and missing-authority messages;
- the setup-turn sheet-skip test;
- a no-settlement-warning assertion;
- a BYOK E2E.

## Exact blockers

1. Codex independent review of the raw C5 packet.
2. A native mint of the reviewed C5 (11 of 24 batches; not prepared), then Owner acceptance of the exact native identity.
3. Vampire Familiar: C5 keeps the source "vampire" qualification on an explicit relation. How the vampire qualification is validated is held; only the Charmed determination refuses. No Owner Decision is requested.
4. A full-suite and CI result for the implementation head.
