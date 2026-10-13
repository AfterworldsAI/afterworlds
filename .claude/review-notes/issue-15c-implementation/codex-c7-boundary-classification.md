# CRD Issue 15c — remaining boundary classification

Reviewed HEAD `00b822471d9658ad34d79de929736558883f342b`. Read the full governing draft; verified SHA-256 `979889e7a42ef8673f1b4f99d3849545b6091025f08a7a7fcd3d37d0bb5f3173`. Reused this task's verified Library Review 2026-09-25 and Prompting 2026-10-05. This note classifies execution boundaries; it does not review or accept C7 facts. No tests, imports, stores, code changes or Git mutations were performed.

**Verdict: bounded correction needed. Most residue is settled implementation. One narrow input-origin decision remains if Claude wants the GameMaster to establish hand occupancy.** Neither a narrative-Turn cap nor anonymous contextual booleans satisfy code-owned eligibility.

## Loading, Light and Nick: specification correction and required implementation

Reject C7 README's proposed “one Loading shot per delivered Turn.” `equipment.md:78` limits each action, Bonus Action or Reaction; `:76,102` distinguish the Attack action, Light's later Bonus Action and Nick's substitution. `issue-draft.md:18,21,22,32` already requires these properties/masteries, code-owned costs and eligibility, explicit mechanical timing and synchronous linked resolution. A new delivery must neither replenish the same actor turn's action budget nor collapse legitimately distinct activations into one.

The minimum coherent contract is an actor-turn identity plus code-validated action/activation identity and source-defined cost, with attacks linked to the activation that grants them. GameMaster selection of an admitted Attack/Bonus Action/Reaction option is already within the accepted selection contract; it is not permission to invent another action grant. Code derives and consumes the available budget, permits additional attacks/activations only with executable source authority, and records consumption across deliveries until the applicable explicit actor edge. Loading is counted within its source-defined activation. Light requires a qualifying prior Light attack in an Attack action on the actor's own turn, a different Light weapon, the same actor turn, its damage-modifier rule, and the appropriate Bonus Action; Nick consumes the same Light extra-attack entitlement within the Attack action, without also granting a second Light extra attack.

Source baselines are `playing-the-game.md:687,695,901`; typed rule shapes already exist at `representation.py:4318,6329,6345`. The currently explicit Nick hold is `attacks.py:575-580,634-638`. This is a bounded action-cost ledger for admitted operations, not an initiative engine or a second ADR-015b pending/action-resolution sequence. Persist completed expenditure, not suspended mechanical interactions. Any actually missing typed source rule still follows the semantic-candidate gate; source prose is not runtime authority. No Owner question is needed to choose table/helper organization or to authorize already-required costs.

**Held:** positive Loading and Light/Nick coverage until this contract is executable; ammunition authority remains separately held for C7 acceptance. This does not authorize general feature/spell execution or reactions whose trigger/eligibility cannot be validated.

## Free hand: no inference from equipped; narrow Owner question only for new GM authority

`equipment.md:70` explicitly requires a free hand to load a one-handed weapon. `holdings.py:103-117` records only `equipped`, not hands or grip; `scene.py:56-60` currently relabels this as `wielded`. Two-Handed and Versatile also consume hand facts (`representation.py:6386-6402`). Counting equipped weapons and a Shield cannot establish occupancy: equipped is not an accepted complete hand assignment, and unrepresented held objects matter.

An explicit, validated hand-state extension is ordinary minimum state representation. However, treating a new GameMaster hand assertion as authoritative fiction truth is not expressly covered by the approved reach/range/area/movement input in `owner-context-decisions-2026-10-12.md:7`. Do not silently stretch that decision.

**[OWNER DECISION]: May the GameMaster supply auditable, operation-specific hand/grip facts from code-generated options for the acting subject and identified held items?**

- **Recommended:** approve the bounded attestation. Code validates holdings, source hand requirements, conflicts with recorded equipment/conditions, and current revisions; a change of grip/held object invalidates affected later assertions. An attestation cannot create ammunition, waive a source requirement or grant an action. Missing/contradictory facts refuse. This covers Ammunition, Two-Handed and Versatile consistently without a general inventory simulator.
- **Alternative:** require explicit authoritative hand state from the existing state-recording path; missing state refuses. This avoids new GM input authority but requires that state to be supplied before affected attacks are usable.

**Held:** the proposed GM-hand-input path, not all ammunition preparation, action accounting or unrelated approved work. Update the accepted-context section and input contract if approved. No automatic `equipped => wielded/free hand` default.

## Last ammunition: ordinary implementation, no Owner decision

`persistence/orm/dnd5e_state.py:152` requires quantity at least one. Source expenditure and the Owner ammunition directive already determine the gameplay result: the last piece is gone. Removing the exhausted live holding through an audited, revision-checked holdings operation is the smallest compatible implementation; no zero-quantity schema is necessary. Retain identity, source/binding, holder, before/after quantity and expenditure in immutable evidence; apply removal, other effects, audit and Turn atomically. A concurrent spend/transfer, blocked delivery or replay must not lose or duplicate stock. Audit references must survive deletion. This is implementation under AC6, not a policy choice, and does not admit post-fight recovery.

## Successive actor edges: settled input boundary; do not claim initiative validation

`owner-context-decisions-2026-10-12.md:21` retains explicit actor edges and rejects automatic round advancement. `boundary-input-contracts.md:105-128` openly records the successive-delivery residue. `coordination.py:80-112` checks begin/end structure and resets uses only on an explicit begin; it does not automatically begin on narrative delivery. A matching end followed by a fresh explicit begin for the same actor is not itself a duplicate or an automatic round scheduler. Selecting the next actor is already delegated to the explicit GM input; requiring another actor between appearances would invent a scheduling policy and can reject legitimate cases.

**Disposition:** contract clarification, not a new blanket Owner question or a patch adding a scheduler. Preserve audited, revision-bound, once-only edges and never present the one-begin-per-delivery guard as proof of source initiative/round legality. Distinguish a replay of the same edge from a fresh explicit GM declaration; only the latter can establish a new actor-turn instance. Code owns resulting expiry, reset and death-save effects. CRD Issue 15c cannot simultaneously disclaim initiative-order management and claim it independently proves every declared next turn is legitimate. If independent schedule validation is desired, that is a new scope decision; it is not required by the presently accepted bounded input contract.

## Bystanders: P1 implementation defects, not new policy

Two representative siblings establish the family: **anonymous contextual assertions substitute for participating subjects and their authoritative state.**

- `models/rpg.py:84-86,128-132` makes nearby enemy/ally eligibility a boolean. `attacks.py:1077-1083` and `creature_attacks.py:270-289,499-505` consume it. Pack Tactics requires a non-Incapacitated ally (`animals.md:355`); close-combat ranged disadvantage requires an enemy who can see the attacker and is not Incapacitated (`playing-the-game.md:1082`). The boolean asserts these state-dependent qualifications as well as geometry. `_load_subjects` (`service.py:636-682`) cannot load or recheck an unnamed contributor. The GM scene's prior read is not a participating-subject commit recheck.
- `saves.py:285-329` checks the saver's own held contributors. Another character's Aura of Protection can change the save (`classes.md:5621-5627`), yet no external aura source is examined. Refusing when the saver itself holds the feature does not cover the sibling case. The same cause affects externally sourced condition/defense effects.

Use identified participating subjects; code checks their effective conditions, senses, applicable grants and source rules, and the approved GM spatial facts establish only the relevant context. Include all contributors actually read in binding/revision/hold validation and the delivered transaction. Discover potentially relevant external effects sufficiently to refuse unsupported contributing mechanics; do not trust an omitted proposal to establish their absence. Supporting general aura execution remains out of scope; refusing a relevant unexecuted aura is expressly required by AC4. Do not block every story simply because an unrelated distant character has a feature. No new GM permission to author mechanics is needed.

## Hidden conditions in the GM scene: backend access allowed; output seam needs correction

The GameMaster-only scene itself is consistent with backend access (`scene.py:9-13,83-97`; `service.py:778-795`; ADR-015 Decision 5). It is appended after the unchanged stable prefix, not placed in the Writer context. `visible_state.py:55-62` filters hidden conditions. No Owner decision is needed to let adjudication inspect authoritative hidden state.

**P1 implementation channel:** `RollProposal.check_label` is unrestricted model text (`models/rpg.py:180`), and `adapter.py:880-905` copies it into a shown/non-roll Writer view and summary. The model generating this label has just received hidden condition names, instance ids and sources. A shown attack labelled with a secret condition is therefore forwarded unchanged; the prompt's “never reveal” instruction (`rpg_adjudication.md:40`) is the only barrier on this path. This is a verified data-flow vulnerability, not an observed model leak or a claim that every shown roll must become hidden. Keep private selection/provenance text separate from a visibility-safe, code-derived public label/projection. Preserve full backend audit and the permitted visible result. Targeted adversarial-label coverage should prove the boundary.

Only the hand-input-origin question above requires a new Owner answer on this review's interpretation. All new semantic facts retain their independent review/native-preview/exact-acceptance gates. #129 stays frozen; #132/#137, CRD Issue 15b/19b, publication/activation, shared-runtime migration, app launch and merge boundaries remain unchanged.
