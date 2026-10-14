# CRD Issue 15c — final delivery/execution review

**Verdict: bounded correction needed.** Reviewed `b5051d8433ac2be7336daa41f2aae038b9d21c9e`; unchanged at completion. Full governing draft read and SHA-256 verified as `8ad877861b821aa927c38a39227ea58ea150ff8fdb4d7b2a161044d45727426f`. Applied installed Review 2026-09-25 and routing guidance; reused the coordinator's current-task Library verification (Review 2026-09-25 / Prompting 2026-10-05). C7 acceptance is settled, not reopened here.

Authority includes the issue's AC3–6 and accepted spatial/hand decisions, ADR-015's transaction/visibility invariants, the prior delivery and boundary reviews, and current Architecture Notes. Findings below are **MERGE-BLOCKING DEFECT / implementation work** under existing authority, not new semantics or Owner Decisions. The recurring family is incomplete mechanical dependencies; remediation should close these representative siblings together rather than restart narrow patch cycling.

## P1 — retain negative discovery reads through delivery

**Sites:** `src/afterworlds/pipeline/rpg/service.py:833–836` (`_auras`); `src/afterworlds/api/pipeline_wiring.py:370–387` (`_make_rpg_bounded_loader`). Delivery only rechecks `rpg_sheet` and `adj_result.subjects` at `pipeline/orchestrator/service.py:2164–2167`.

Aura discovery reads every character, then drops all characters without an aura before collecting the delivery read set. Turn-bounded-effect discovery similarly drops every character/creature without a matching effect. These absent results are mechanically consumed: they establish that the save has no external contributor, or that the actor edge has no additional effects to expire. If an excluded subject acquires the relevant aura or timed effect after the scan, its changed revision is not checked. A new matching subject also escapes the retained collection. State updates are ordinary CAS operations (`services/dnd5e_state/service.py:222–276`), with no turn-lease prohibition. Coordination CAS does not cover these state edits.

Consequently, a save can deliver against obsolete contributor absence, or an actor edge can deliver while leaving an effect that should have ended. Preserve a sufficiently complete discovery dependency/revision and collection-membership guard, or revalidate the relevant query at delivery against the snapshot. Include transitions from nonmatching to matching and new membership, with atomic Turn/audit/effects refusal. No general encounter engine is required. **Evidence: static source trace; no concurrent-store reproduction run.**

## P1 — movement must invalidate spatial facts about named bystanders

**Sites:** `src/afterworlds/pipeline/rpg/adapter.py:467–485` and `src/afterworlds/pipeline/rpg/attacks.py:1467–1478` (`spatial_subjects`).

The preflight invalidation set includes only an attack's actor and target (or an area's source and targets), excluding `hostiles_within_5_feet`, `allies_within_5_feet_of_target`, and aura proximity dependencies. Identifying and reading bystanders fixed their state dependency, but did not fix their spatial dependency.

**Reproduced through the real adjudication service:** an initially active Fighter pushes creature B 10 feet, ends the Fighter turn, begins a Wolf's turn, then the Wolf bites the Fighter using B as its nearby ally. The sequence is accepted, rolls four dice calls, and grants `animals.wolf/Pack Tactics`. B's earlier proximity fact was invalidated by Push. Explicit actor edges do not refresh spatial assertions already supplied in that proposal batch.

Include every subject whose spatial relationship the operation consumes in invalidation, including named bystanders and discovered aura sources where absence/range matters. A potentially moved contributor must cause pre-dice refusal under the existing bounded contract until refreshed admissible facts exist. Cover Pack Tactics and close-combat/area-aura siblings; preserve actor-edge semantics without adding initiative ordering.

## P2 — Light must distinguish item instances, not weapon source records

**Sites:** `src/afterworlds/pipeline/rpg/economy.py:143,146–162`.

The Attack action use records only the weapon's source record, and Light rejects `record == first[0]`. Two different held Daggers therefore count as the same weapon. The accepted Light rule requires a different weapon, not a different weapon type (`docs/sources/community/dnd-5e-srd-markdown/equipment.md:76`). This also affects Nick's shared Light entitlement.

**Reproduced through the real service:** an actor holds two Daggers with distinct item UUIDs, one in each hand; an ordinary Dagger attack followed by the other Dagger's Light extra attack refuses `invalid_selection` before dice. Retain the first attack's individual item identity alongside the source identity and compare item identities. Preserve durable action/use replay and source validation. Cover distinct same-kind items positively and reuse of the same item negatively, including Nick.

## P1 — the free-hand loading rule cannot depend on a chosen two-hand grip

**Site:** `src/afterworlds/pipeline/rpg/hands.py:104–127`.

The free-hand rule is checked only when the proposal says `hands == 1`. A one-handed ammunition weapon can therefore evade the source requirement by declaring a two-hand grip with zero free hands. The typed predicate is `weapon_is_one_handed`, and the source requires a free hand to load a one-handed weapon (`equipment.md:70`); the GM's grip declaration cannot waive that requirement. The hand contract also states that these operations do not change grip.

**Reproduced through the real service:** a Hand Crossbow with two declared gripping hands and `free_hands=0` is accepted and rolls its attack/damage. The control with one gripping hand and one free hand also succeeds. Existing all-ammunition coverage constructs the bypassing grip for every weapon (`test_weapon_attacks.py:_shot`). Determine the source-required weapon hand classification independently of the declared grip and enforce loading from validated facts; do not interpret an assertion as an implicit grip-change operation. Cover Hand Crossbow/Pistol/Sling and retain legitimate Two-Handed ammunition behavior.

## Evidence and closed concerns

`delivery-review/reproduce_delivery_edges.py` and `delivery-review/reproduction-results.jsonl` contain the bounded reproductions above, using the real accepted test authority and production adjudication service. Interpreter/import identity was verified as this isolated checkout's `venv` / `src/afterworlds`. No store, network, CLI writer, implementation, Git mutation, or broad test suite was used.

Prior delivery findings now have source fixes: holdings membership plus item revisions are checked; read-only/absent coordination snapshots are checked; action/use events are logged and replayable; ammunition consumption is CAS-protected, deletes the exhausted live holding, and audit/effects remain inside the outer delivery transaction. Limited-entry preflight counts aggregate deterministic uses. Public labels are code-derived and hidden Writer views are nulled. These positives do not supersede the missing discovery and spatial dependencies above.

Discarded candidates: an area-save aura-holder exclusion is already caught by that holder's own save-contributor refusal; stale `rpg_sheet.items` inside the optional orchestrator visible-state builder does **not** establish a production API defect because `api/routes/turns.py:233` rebuilds visible state from committed state. Neither is a blocking finding here.

## Claude-ready remediation

Remediate these settled CRD Issue 15c execution defects under #191 and the approved spatial/hand contracts. Retain negative discovery dependencies and membership through delivery; invalidate the spatial facts of moved named/discovered contributors; retain individual weapon identity for Light/Nick; derive free-hand loading requirements from source weapon classification. Preserve C7, current transaction/audit/replay rails, explicit actor-edge semantics, visibility filtering, and CRD Issue 15b/19b boundaries. Demonstrate the stated regressions and relevant safe controls, including zero dice on invalid compositions and full rollback for stale discovery. No new semantic candidate, general inventory/encounter engine, publication, activation, or merge is authorized by this review.
